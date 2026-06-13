# Fase 5 — Análise macroestrutural (naturalidade estrutural)

**Data:** 2026-06-13
**Status:** aprovado, pronto para plano de implementação

## 1. Contexto e problema

O servidor MCP `texto-br` produz texto pt-BR humanizado por um pipeline. Hoje
ele tem 6 fases (0 contexto → 1 redação → 2 humanização de superfície → 3
profunda → 4 discursiva → 5 entrega) e dois analisadores quantitativos Python
stdlib (`variancia.py` = ritmo sintático, `lexico.py` = perturbação lexical),
compostos num score 0-100 (`score.py`) que serve de objetivo do loop da Fase 2.

Esses analisadores operam em escala **micro** (sentença e parágrafo): burstiness,
uniformidade de parágrafo, sentença de impacto, corrente de conectivos. Eles não
enxergam a **arquitetura do documento**.

Um dos sinais mais fortes de texto gerado por IA é justamente macroestrutural: a
sensação de "estrutura continua muito bem encaixada". Concretamente:

1. **Simetria dos capítulos/seções** — seções de tamanho e forma quase iguais.
2. **Frases de efeito em sequência** — bordões aforismáticos enfileirados.
3. **Parágrafo que sempre fecha uma "lição"** — cada parágrafo aterrissa numa
   moral curta e arredondada.
4. **Excesso de subtópicos** — subtítulos usados onde não eram necessários.
5. **Progressão linear demais** — escada de signposts, intro/conclusão simétricas,
   andaime previsível.

Esses sinais são especialmente relevantes para **posts e capítulos de livro**.

## 2. Objetivo

Criar uma análise **macroestrutural** que:

- Meça os 5 sinais acima com Python stdlib puro e os componha num score 0-100 de
  **naturalidade estrutural** (1 = humano/variado, 0 = encaixado demais).
- Produza um **plano de perturbação** concreto e priorizado: instruções de
  reescrita para o modelo desencaixar a estrutura.
- Viva como uma **nova Fase 5 dedicada** do pipeline (a entrega passa a ser a Fase 6).
- Aja como **gate adaptativo por tipo**: bloqueia a entrega em tipos longos
  (`blog`, `capitulo`, `tecnico`, `explicativo`, `podcast`, `video`) quando o
  score fica abaixo do alvo; advisory (mede mas não bloqueia) nos demais tipos.
- Seja **extensível**: novos detectores entram registrando uma função, sem
  reescrever o núcleo ("podemos adicionar outras verificações no futuro").

### Não-objetivos (fora de escopo v1, YAGNI)

- Loop automático de reescrita via Claude API (estilo `otimizar.js`) para
  estrutura. A perturbação é executada pelo modelo na conversa, guiado pelo plano.
  Fica como adição futura (o registry de detectores e o score já preparam o terreno).
- Detector semântico via LLM-as-judge. O v1 é 100% determinístico stdlib, como o
  resto do projeto. O registry permite acrescentar um detector opcional no futuro.
- Reescrever ou substituir o `score.py` da Fase 2. As duas medições são
  deliberadamente distintas (micro vs. macro) e coexistem.

## 3. Decisões de design

| Decisão | Escolha | Razão |
|---|---|---|
| Posição no pipeline | Nova Fase 5; entrega vira Fase 6 | Casa com "última etapa" + registry extensível |
| Comportamento | Gate adaptativo por tipo | Bloqueia só onde há estrutura a controlar |
| Abordagem | Registry de detectores + score composto calibrado | Espelha `variancia`/`lexico`/`score`; extensível; testável |
| Linguagem | Python stdlib | Mantém a filosofia "stdlib mede, modelo reescreve" |
| Filosofia | Mede + diagnostica + plano de perturbação | O analisador nunca reescreve |

## 4. Arquitetura

Espelha o padrão existente: analisador Python puro + tool JS embrulhando via
`runPython` + reference markdown com o conhecimento curado.

### 4.1 Parsing estrutural

Os analisadores atuais usam `texto_util.limpar_markdown`, que **apaga** headings e
listas. A análise macroestrutural precisa do oposto: enxergar o outline.

- Adicionar a `texto_util.py` a função `parsear_blocos(texto)`, que devolve a
  lista ordenada de blocos do markdown: `{tipo, nivel, texto}` para
  `heading | paragrafo | lista | codigo | citacao`. A detecção de cercas de código
  reusa a mesma lógica de `limpar_markdown` (cerca fecha só com mesmo caractere e
  comprimento ≥ o de abertura). É genérica e reutilizável por futuras análises.
- Em `estrutura.py`, `montar_outline(blocos)` agrupa os blocos em seções:
  - Se há exatamente um `#` e ele é o primeiro heading, é o título do
    documento/capítulo; o nível de seção é 2.
  - Senão, o nível de seção é o menor nível de heading presente.
  - Cada seção = `{titulo, nivel, palavras_prosa, paragrafos[], subsecoes[]}`;
    subseções são headings mais profundos que o nível de seção dentro da seção.
  - Parágrafos de prosa são tokenizados em sentenças com `dividir_sentencas` e em
    palavras com `contar_palavras` (reuso de `texto_util`).

### 4.2 Detectores (registry)

Cada detector é uma função pura `detector(outline, blocos, tipo) -> dict`:

```python
{
  "id": "simetria_secoes",
  "nome": "Simetria de seções",
  "aplicavel": bool,        # False quando a estrutura-alvo não existe
  "subscore": 0.0-1.0,      # 1 = humano/variado, 0 = encaixado
  "peso": int,              # peso nominal (tipos longos)
  "metricas": {...},        # números crus, para transparência no relatório
  "diagnostico": [str, ...],# linhas em pt-BR
  "perturbacoes": [str, ...]# movimentos concretos de reescrita (só quando fraco)
}
```

O registry é uma lista `DETECTORES = [detector_simetria, detector_subtopicos, ...]`.
Acrescentar verificação futura = adicionar uma função à lista.

#### Detector 1 — Simetria de seções (peso 25)

Aplicável se ≥ 3 seções.

- `cv_tamanho` = `pstdev/mean` das palavras por seção. CV baixo = simétrico.
- Paralelismo de títulos: `frac_mesmo_primeiro_termo`, `frac_gerundio` (1º termo
  termina em `-ndo`), `frac_pergunta` (título termina em `?`), `cv_comprimento_titulos`.
- `uniformidade_subsecoes`: CV do nº de subseções por seção (ou flag "todas iguais ≥ 2").
- **subscore** = média de três componentes 0-1, todos clamp:
  - tamanho: `interp(cv_tamanho, ruim=0.15→0, bom=0.45→1)`
  - títulos: `1 − max(frac_gerundio, frac_pergunta, frac_mesmo_primeiro_termo)` reescalado
    a partir de 0.4 (abaixo disso, sem penalidade) até 0.85 (penalidade máxima)
  - subseções: 0 se todas as seções têm o mesmo nº de subseções ≥ 2; senão
    `interp(cv_subsecoes, ruim=0.1→0, bom=0.5→1)`
- **perturbações**: "Deixe uma seção respirar (corte ~metade) e outra ir fundo
  (dobre)"; "Funda as seções X e Y"; "Reescreva ≥ 2 títulos com forma gramatical
  diferente (pergunta, frase nominal, imperativo)".

#### Detector 2 — Inflação de subtópicos (peso 20)

Aplicável se há ≥ 1 heading de seção/subseção além do título.

- `densidade` = nº de headings (seção + subseção) por 100 palavras de prosa.
- `frac_secoes_finas` = fração de seções/subseções com < 60 palavras de prosa.
- `profundidade` = uso de `###`/`####` (nível ≥ 3) em texto curto.
- **subscore**: penaliza densidade alta (limiar base: começa a penalizar acima de
  1.5 heading/100 palavras, penalidade máxima ≥ 3.5) e `frac_secoes_finas` alta
  (começa em 0.3, máxima em 0.7). Combina por média ponderada.
- **Calibração**: `tecnico` multiplica o limiar de densidade por ~1.8
  (documentação é legitimamente seccionada).
- **perturbações**: "N subtítulos em M palavras (1 a cada K): funda os finos,
  mantenha só os que marcam viradas reais"; "Rebaixe `###` a parágrafo com frase-guia".

#### Detector 3 — Parágrafo-lição / kicker uniforme (peso 20)

Aplicável se ≥ 4 parágrafos com ≥ 2 sentenças.

- Para cada parágrafo multi-sentença: `razao_fecho` = palavras da última sentença /
  média das anteriores. `flag_kicker` = `razao_fecho < 0.6` **ou** última sentença
  contém marcador da lista `MARCADORES_LICAO` **ou** começa com "E " e é curta (≤ 8 palavras).
- `frac_kicker` = parágrafos com flag / parágrafos elegíveis.
- **subscore**: `interp(frac_kicker, bom=0.4→1, ruim=0.75→0)`. Alguns fechos são
  humanos; o tell é a **uniformidade** (quase todo parágrafo fecha numa moral).
- `MARCADORES_LICAO` (inicial, ajustável): "no fim", "no fim das contas", "no fundo",
  "afinal", "é isso", "talvez seja", "o que importa", "a verdade é", "no final",
  "resta", "moral da história", "e é por isso", "é sobre isso", "se há algo".
- **perturbações**: "M de N parágrafos fecham num bordão. Deixe ~3 terminarem no
  meio do raciocínio, sem moral"; "Mova o fecho de um parágrafo para o início do seguinte".

#### Detector 4 — Frases de efeito em sequência (peso 15)

Aplicável se ≥ 5 parágrafos.

- `paragrafos_bordao` = parágrafos de prosa com 1 só sentença curta (≤ 8 palavras).
- `frac_bordao` = bordões / parágrafos de prosa.
- `agrupamento` = maior corrida de bordões consecutivos (ou adjacentes).
- **subscore**: penaliza `frac_bordao` alto **e** agrupamento. Um bordão isolado é
  humano; vários em sequência é o tell. `subscore = min(interp(frac_bordao,
  bom=0.15→1, ruim=0.45→0), penalidade_agrupamento)` onde agrupamento ≥ 2 reduz forte.
- **perturbações**: "Bordões em sequência (parágrafos X-Y). Funda ao menos um ao
  parágrafo vizinho ou desenvolva-o em 2-3 sentenças".

#### Detector 5 — Progressão sinalizada (peso 20)

Aplicável se ≥ 3 seções **ou** ≥ 6 parágrafos.

- `signposts`: fração de parágrafos/seções que abrem com `SIGNPOSTS_PROGRESSAO`;
  `staircase` = presença de sequência ordinal (primeiro → depois → por fim).
- `aberturas_conectivo`: fração de seções cujo 1º parágrafo abre com conectivo
  lógico (reusa `CONECTIVOS_INICIAIS` de `variancia.py`).
- `simetria_intro_outro`: primeira seção curta de "setup" + última seção curta com
  marcador de fecho (`MARCADORES_LICAO`).
- `titulos_ordinais`: títulos começando com número/ordinal.
- **subscore**: começa em 1.0 e desconta por sinal presente (staircase, aberturas
  em corrente, intro/outro simétricos, títulos ordinais), com piso 0.
- `SIGNPOSTS_PROGRESSAO` (inicial): "primeiro", "segundo", "terceiro", "em seguida",
  "depois", "por fim", "finalmente", "a seguir", "para começar", "em primeiro lugar",
  "em segundo lugar", "por último", "agora que".
- **perturbações**: "Escada de signposts (primeiro/depois/por fim). Remova a
  numeração explícita; deixe a transição implícita"; "A primeira e a última seção
  são gêmeas. Quebre a simetria intro/conclusão".

### 4.3 Score composto e calibração por tipo

Só os detectores `aplicavel=True` entram. Re-normaliza pelos pesos aplicáveis,
para que um texto sem seções não seja punido por "não ter seções":

```
total = round( sum(peso_i * subscore_i) / sum(peso_i) * 100 )   # i aplicáveis
```

Calibração por tipo (`CALIBRACAO_ESTRUTURA`):

| Conjunto | Tipos | Gate | Alvo |
|---|---|---|---|
| Gate (tipos longos) | `blog`, `capitulo`, `tecnico`, `explicativo`, `podcast`, `video` | **bloqueia** | 70 |
| Advisory | todos os demais (`geral`, `corporativo`, `email`, `comentario-*`, `chat`) | mede, não bloqueia | 70 (informativo) |

`tecnico` ainda ajusta o limiar de densidade do Detector 2 (×1.8). O conjunto de
gate segue exatamente a lista que o usuário definiu.

### 4.4 Relatório e plano de perturbação

Saída em Markdown, no padrão dos outros analisadores:

- `## Score de naturalidade estrutural` — `Total: X / 100 | alvo >= A | veredicto:
  ALVO ATINGIDO | REESCREVER E MEDIR DE NOVO`.
- Tabela `| Detector | subscore | peso | pts |` (só aplicáveis; inaplicáveis
  listados como "não se aplica").
- `### Diagnóstico` por detector.
- `## Plano de perturbação` — lista priorizada pelas perturbações dos detectores
  mais fracos (subscore mais baixo primeiro), com movimentos concretos.
- `atingiu_alvo` = `total >= alvo` **ou** análise inteira inaplicável (texto sem
  estrutura macro a controlar → nada a desencaixar).

### 4.5 Degradação graciosa

- < 4 parágrafos de prosa → retorna `{"erro": "..."}` (como `variancia.py` faz com
  < 3 sentenças). A Fase 5 vira transparente.
- Texto sem headings (típico de conversacional/curto) → detectores de seção/
  subtópico/progressão ficam `aplicavel=False`; rodam só kicker + sequência.

## 5. Interface (tool MCP)

`texto_br_estrutura(texto, tipo?)`:

- `tipo` opcional, default = `session.tipo` (ou `geral`). Usado para calibração e alvo.
- Chama `runPython('estrutura.py', JSON.stringify({texto, tipo}))`.
- Se `!resultado.erro`, grava `session.estruturaAtingida = resultado.atingiu_alvo === true`
  e `session.persist()` (espelha `variancia.js`/`lexico.js`).
- Retorna `resultado.relatorio`.
- Registrado em `server.js` como `registerEstrutura(server, session)`.

## 6. Integração no pipeline (renumeração 5 → 6)

### Arquivos novos

- `server/analysis/estrutura.py` — parser de outline, detectores, score, relatório.
- `server/tools/estrutura.js` — tool `texto_br_estrutura`.
- `references/estrutura-macro.md` — conhecimento curado: o que cada tell significa
  e por que sinaliza IA; técnicas de perturbação; matriz de calibração por tipo;
  **checklist de saída** (seção numerada, servida via `texto_br_checklist(5)`).

### Arquivos modificados

- `server/analysis/texto_util.py` — adicionar `parsear_blocos(texto)`.
- `server/knowledge/phases.js`:
  - `PHASE_GUIDANCE[5]` = nova guidance macroestrutural; `PHASE_GUIDANCE[6]` =
    texto atual da entrega (movido de `[5]`).
  - `PHASE_SECTIONS[5]` = seções de `estrutura-macro`; `PHASE_SECTIONS[6] = []`
    (remover o antigo `[5] = []`).
  - `PHASE_SECTIONS_CONVERSACIONAL[5]` = payload enxuto (só técnica de kicker +
    matriz de calibração).
  - `CHECKLISTS[5] = { file: 'estrutura-macro', section: <n> }`.
  - Novas constantes: `TIPOS_ESTRUTURA_GATE` e `CALIBRACAO_ESTRUTURA` (esta última
    espelhada no Python; fonte de verdade documentada).
  - Atualizar o comentário de cabeçalho ("...5 entrega" → "...6 entrega").
- `server/session/state.js`:
  - `estruturaAtingida: null` em defaults e em `CAMPOS`.
  - `advance()`: `>= 5` → `>= 6`; mensagem "Fase 5 (entrega)" → "Fase 6 (entrega)".
  - `goTo()`: limite `1..5` → `1..6`.
  - `start()`: resetar `estruturaAtingida = null`.
- `server/tools/proxima-fase.js`:
  - schema `fase` `max(5)` → `max(6)`.
  - Manter gate da Fase 2. Adicionar **gate da Fase 5**: se `currentPhase === 5` e
    `tipo ∈ TIPOS_ESTRUTURA_GATE` e `!forcar` e `session.estruturaAtingida !== true`
    → bloqueia com mensagem (rode `texto_br_estrutura`, aplique o plano, remeça).
    Advisory para os demais tipos.
  - Mover a nota de "rascunhos salvos" de `phase === 5` para `phase === 6`.
  - Atualizar `description`.
- `server/content/loader.js` — adicionar `'estrutura-macro'` a `FILES`.
- `server/tools/checklist.js` — schema `union(2,3,4)` → incluir `5`; atualizar descrição.
- `server/server.js` — `import`/`registerEstrutura`; atualizar `INSTRUCTIONS`
  ("6 fases" → "7 fases"; Fase 5 = naturalidade estrutural, Fase 6 = entrega;
  acrescentar `texto_br_estrutura` à lista de tools; checklist "2, 3 e 4" → "2-5").
- `server/index.js` — sem mudança lógica (carrega/valida via `loader`/`registry`,
  que já leem as listas atualizadas).
- `server/README.md` e `SKILL.md` — refletir 7 fases e a nova tool/etapa.

## 7. Testes

- `server/test/analysis.test.js`:
  - Fixture "IA-encaixado" (seções simétricas + kicker uniforme + escada de
    signposts) → score baixo, `atingiu_alvo=false`, plano de perturbação não vazio.
  - Fixture "humano-variado" (seções de tamanhos díspares, fechos irregulares) →
    score alto, `atingiu_alvo=true`.
  - Texto sem headings → detectores de seção `aplicavel=False`; score só do que aplica.
  - < 4 parágrafos → `{"erro": ...}`.
  - `parsear_blocos`/`montar_outline`: outline correto para capítulo com `#` + `##`.
- `server/test/content.test.js`: `estrutura-macro.md` parseia; tem as seções
  esperadas + a seção de checklist; `validateAll()` sem avisos novos.
- `server/test/e2e.test.js`: pipeline avança 4 → 5 → 6; gate bloqueia em `blog`
  com `estruturaAtingida` falso; advisory em `chat`; `forcar: true` fura o gate.

## 8. Sequência de implementação sugerida

1. `texto_util.parsear_blocos` + testes do parser.
2. `estrutura.py`: outline + detectores + score + relatório + testes de análise.
3. `references/estrutura-macro.md` (conhecimento + matriz + checklist) + testes de conteúdo.
4. `estrutura.js` (tool) + registro em `server.js` + `loader.js`.
5. Renumeração de fase: `phases.js`, `state.js`, `proxima-fase.js`, `checklist.js`.
6. `INSTRUCTIONS`, `README.md`, `SKILL.md`.
7. `e2e.test.js` + suíte completa verde.

## 9. Riscos e mitigações

- **Proxies heurísticos para sinais semânticos** ("lição", "progressão"): o
  relatório é honesto sobre serem proxies; o gate só atua em tipos longos; limiares
  são iniciais e calibrados contra as fixtures. Falso-bloqueio é contornável com
  `forcar: true`.
- **Renumeração de fase** toca vários arquivos: mitigado pela sequência acima e
  pela suíte e2e cobrindo a transição 5 → 6 e os gates.
- **Divergência entre calibração JS e Python**: `CALIBRACAO_ESTRUTURA` tem fonte de
  verdade documentada em `phases.js`; o Python replica os valores com comentário
  apontando para lá (mesmo padrão de `REGRAS_ABSOLUTAS`/`INSTRUCTIONS`).
