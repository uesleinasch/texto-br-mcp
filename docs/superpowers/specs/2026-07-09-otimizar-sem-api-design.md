# Design: `texto_br_otimizar` sem dependência da Claude API

**Data:** 2026-07-09
**Status:** aprovado

## Problema

O servidor MCP `texto-br` exige `ANTHROPIC_API_KEY` no ambiente para que a tool
`texto_br_otimizar` funcione. Essa tool (`server/tools/otimizar.js`) importa o
`@anthropic-ai/sdk` e roda um loop de subida de encosta que **reescreve** o texto
chamando `client.messages.create(...)` — ou seja, o servidor abre uma segunda
conexão com a API da Anthropic.

Isso é arquiteturalmente redundante e contraria a premissa de um MCP:

- O host MCP (o Claude Code que chamou a tool) **já é** um modelo capaz de reescrever.
- Exige credencial e custo separados, quebrando a portabilidade.
- Duplica o raciocínio que o host já faria.

Todas as outras tools (`score`, `variancia`, `lexico`, `estrutura`, ...) são
medição determinística em Python e **não** tocam a API. Apenas `otimizar` depende
dela. A "via manual" já documentada na Fase 2 (`phases.js`) — `texto_br_score` →
host reescreve → remede — é o loop idiomático dirigido pelo host, e já produz
texto no alvo (o loop dirigido pelo host atingiu 94.1 ≥ 93.6 num uso real).

## Objetivo

Eliminar toda dependência da Claude API do servidor, tornando o loop de
humanização **dirigido pelo host** a via única — sem perder a ergonomia de
"uma chamada me dá tudo para agir".

## Decisão de design

Abordagem escolhida: **converter `texto_br_otimizar` numa tool sem API**. A tool
deixa de reescrever; passa a devolver, numa única chamada, o diagnóstico
consolidado + o roteiro de reescrita, e o **host** executa a reescrita.

Alternativas descartadas:

- **Remover a tool + SDK** (só a via manual sobra): funcional, mas joga fora o
  roteiro de reescrita consolidado, que é conhecimento útil hoje preso no
  `SYSTEM` prompt.
- **Manter o loop via `claude` CLI headless**: ainda invoca um segundo modelo,
  mais lento e frágil (spawn de processo, dependência do CLI), e não resolve a
  redundância conceitual.

## Contrato novo da tool

`texto_br_otimizar(texto)` mede o texto com `score.py` (determinístico, já
existe) e retorna um **pacote acionável** de texto:

1. **Cabeçalho**: score atual `/100` e se atingiu o alvo (`>= ALVO_SCORE`).
2. **Diagnóstico priorizado**: o `resumoDiagnostico` já existente (componentes
   fracos ordenados da contribuição mais negativa + candidatas de quebra/fusão +
   pivots a trocar).
3. **Roteiro de reescrita**: exatamente o conteúdo que hoje é o `SYSTEM` prompt
   (técnicas de RITMO / LÉXICO / ESTRUTURA + regras invioláveis: zero travessão,
   zero conector clichê, preservar conteúdo, nunca degradar). Passa a ser
   entregue ao **host** em vez de a um segundo modelo.
4. **Instrução de loop**: reescreva APENAS os pontos apontados seguindo o
   roteiro → `texto_br_score` no texto reescrito → repita até "ALVO ATINGIDO"
   (máx. ~3 iterações); se o score cair, descarte a reescrita e volte à versão
   anterior.

Casos especiais:

- **Texto já no alvo** (`atingiu_alvo`): retorna "nada a reescrever" com o score,
  sem roteiro.
- **Texto curto demais** (`inaplicavel`): mesmo comportamento do `texto_br_score`
  (informa e libera o gate).

Semântica resultante: `texto_br_otimizar` = **`texto_br_score` + roteiro de
reescrita quando o texto ainda não passou.**

## Comportamento do gate da Fase 2

Decisão-chave: a nova tool mede o texto **de entrada** e libera os flags do gate
(`session.registrarVariancia` / `session.registrarLexico`) **exatamente como o
`texto_br_score` faz** — em função da medição do texto recebido.

- Remove-se a lógica antiga de "gravar o veredito do texto otimizado" (não existe
  mais texto otimizado produzido pela tool).
- Não há risco de furar o gate: o gate reflete a medição do texto passado,
  idêntico ao `score`. Se o host passa um texto ainda fraco, o gate não é
  liberado; o host reescreve e remede, e aí sim libera.
- Caso `inaplicavel`: libera ambos os flags (paridade com `score`).

## Refatoração da função pura

- `otimizarTexto({texto, client, pontuar, session})` (loop com `client`) →
  `montarPacoteOtimizacao({texto, pontuar, session})` — **sem `client`**. Mede
  uma vez via `pontuar`, registra o gate conforme a medição (igual `score`) e
  retorna `{ score, atingiu_alvo, inaplicavel, diagnostico, relatorio }`.
- `resumoDiagnostico(resultado)` permanece **intacto** (reaproveitado como o
  diagnóstico consolidado do pacote).
- A constante `SYSTEM` é renomeada para `ROTEIRO_REESCRITA` e **exportada**,
  entrando no payload de retorno da tool.

## Remoções

- `import Anthropic from '@anthropic-ai/sdk'` e todo uso do client.
- Loop de subida de encosta: `MAX_ITERACOES`, `MAX_SEM_MELHORA`, tratamento de
  `stop_reason === 'max_tokens'`, sanity de comprimento, `try/catch` de falha de
  API, mensagens `SEM_CREDENCIAL`.
- Env `TEXTO_BR_MODEL` (só usada para a chamada de API).
- Dependência `@anthropic-ai/sdk` em `server/package.json` e
  `server/package-lock.json`.

## Testes (`server/test/otimizar.test.js`)

- **Remover** os testes do loop-com-`client` (deixam de ter alvo de teste):
  descarte de candidato truncado por `max_tokens`; todas as respostas truncadas;
  descarte por comprimento suspeito; falha de API no meio do loop; wiring do gate
  com o texto otimizado.
- **Manter** o teste de `resumoDiagnostico` (componentes negativos, ordenação,
  sinal 0-1) — o comportamento não muda.
- **Adicionar** testes de `montarPacoteOtimizacao`:
  - texto abaixo do alvo → pacote com `diagnostico` preenchido e `atingiu_alvo:
    false`;
  - texto no alvo → `atingiu_alvo: true` (o host trata como "nada a reescrever");
  - libera o gate conforme a medição, gravando o **texto de entrada** (paridade
    com `score`);
  - texto `inaplicavel` → libera ambos os flags, sem erro.

## Guidance & docs

- `server/knowledge/phases.js` (`LOOP_QUANTITATIVO_GUIDANCE`): eliminar a
  dicotomia "via automática (API) vs manual". Passa a ser um loop único dirigido
  pelo host: (1) `texto_br_otimizar` devolve diagnóstico priorizado + roteiro num
  passo; (2) host reescreve os pontos apontados; (3) remede com `texto_br_score`
  e repete até o alvo, descartando quedas.
- `server/server.js` (string `instructions` do servidor): descrição de
  `texto_br_otimizar` sem "via Claude API / requer ANTHROPIC_API_KEY".
- `SKILL.md` (linha ~98): reescrever a menção a `texto_br_otimizar` como "atalho
  automático via Claude API".
- `server/README.md` (linhas ~9, ~35, ~72): reescrever a descrição de
  `texto_br_otimizar` e **remover** `ANTHROPIC_API_KEY` da seção/tabela de
  variáveis de ambiente.
- **Fora de escopo**: docs de auditoria histórica em `docs/` (ex.:
  `docs/auditoria-2026-07-07.md`, specs/plans antigos) — são registro do que
  valia na época e não devem ser reescritos.

## Impacto no resultado do texto

Nenhuma mudança no critério de qualidade: `score.py`, o alvo e o gate são
idênticos, e a saída da Fase 2 continua bloqueada por código até o alvo. Muda
apenas **quem** reescreve: o host, com todo o contexto da conversa (briefing,
tipo, fases anteriores), em vez de um segundo modelo isolado — o que tende a
melhorar a fidelidade. A única perda é a garantia *mecânica* de monotonicidade
dentro do loop (vira regra da guidance); o piso do resultado final continua
imposto pelo gate.

## Verificação

- `node --test` em `server/` passa (suíte ajustada).
- Servidor sobe **sem** `ANTHROPIC_API_KEY` e `texto_br_otimizar` responde com o
  pacote (diagnóstico + roteiro), nunca mais com "credencial ausente".
- `grep -rn "ANTHROPIC_API_KEY\|@anthropic-ai/sdk"` em `server/` (fora de
  `node_modules`) e nas docs vivas não retorna nada.
