# `texto_br_otimizar` sem Claude API — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remover toda dependência da Claude API do servidor MCP `texto-br`, convertendo `texto_br_otimizar` numa tool que empacota diagnóstico + roteiro de reescrita para o host executar.

**Architecture:** A tool deixa de reescrever via `@anthropic-ai/sdk` e passa a medir o texto com `score.py` (determinístico) e devolver, numa chamada, o diagnóstico priorizado (`resumoDiagnostico`) + o roteiro de reescrita (ex-`SYSTEM`, agora `ROTEIRO_REESCRITA`). O loop de subida de encosta migra para a guidance da Fase 2 e é dirigido pelo host. O gate da Fase 2 passa a se comportar como o `texto_br_score`: mede o texto de entrada e libera os flags conforme a medição.

**Tech Stack:** Node.js (ESM), `@modelcontextprotocol/sdk`, `zod`, `node:test`, Python (análise via `runPython`).

## Global Constraints

- **Sem dependência da Claude API:** nenhum `import Anthropic`, nenhuma chamada `messages.create`, nenhum uso de `ANTHROPIC_API_KEY`/`TEXTO_BR_MODEL`.
- **Alvo do score:** `ALVO_SCORE` (importado de `../knowledge/phases.js`) = 93.6; nunca hardcodar o número.
- **Regras de conteúdo do domínio (preservadas no roteiro):** proibido travessão (—) e meia-risca (–); proibido conector clichê ("Além disso", "No entanto", "Em conclusão"); preservar conteúdo/sentido/registro; a otimização nunca degrada o texto.
- **Commits:** Conventional Commits em pt-BR; **nunca** adicionar trailer `Co-Authored-By`.
- **Testes:** `cd server && node --test` deve passar após cada task.

---

### Task 1: Núcleo de `otimizar.js` — função pura sem API + roteiro exportado

**Files:**
- Modify: `server/tools/otimizar.js` (reescrita completa)
- Test: `server/test/otimizar.test.js` (reescrita completa)

**Interfaces:**
- Consumes: `resumoDiagnostico(resultado)` (mantido); `runPython`, `getSection`, `ALVO_SCORE` (já importados).
- Produces:
  - `export const ROTEIRO_REESCRITA: string` — o roteiro de reescrita (ex-`SYSTEM`).
  - `export function resumoDiagnostico(resultado): string` — inalterado.
  - `export async function montarPacoteOtimizacao({ texto, pontuar, session }): Promise<{ atingiu_alvo?: boolean, score?: object, diagnostico?: string, relatorio?: string, inaplicavel?: boolean, erro?: string }>` — mede uma vez via `pontuar`, registra o gate conforme a medição (paridade com `texto_br_score`) e retorna o pacote.

- [ ] **Step 1: Reescrever os testes (falham primeiro)**

Substituir todo o conteúdo de `server/test/otimizar.test.js` por:

```js
import test from 'node:test';
import assert from 'node:assert';
import { montarPacoteOtimizacao, resumoDiagnostico } from '../tools/otimizar.js';

const analiseBase = (total, extras = {}) => ({
  atingiu_alvo: total >= 80,
  score: {
    total,
    alvo: 80,
    componentes: { burstiness: 1.5, sem_pivots: 2.1 },
    sinais: { burstiness: 0.6, sem_pivots: 0.85 },
  },
  ritmo: { atingiu_alvo: false, diagnostico: [], candidatas_quebra_fusao: [] },
  lexico: { atingiu_alvo: false, diagnostico: [], ocorrencias: [] },
  relatorio: 'relatório',
  ...extras,
});

const fakeSession = () => {
  const chamadas = { variancia: [], lexico: [] };
  return {
    chamadas,
    registrarVariancia: (a, t) => chamadas.variancia.push({ a, t }),
    registrarLexico: (a, t) => chamadas.lexico.push({ a, t }),
  };
};

test('abaixo do alvo: devolve diagnóstico priorizado e atingiu_alvo false', async () => {
  const pontuar = async () => analiseBase(60);
  const pacote = await montarPacoteOtimizacao({ texto: 'x', pontuar, session: null });
  assert.equal(pacote.atingiu_alvo, false);
  assert.match(pacote.diagnostico, /score atual: 60\/100/);
  assert.equal(pacote.relatorio, 'relatório');
  assert.equal(pacote.erro, undefined);
});

test('no alvo: atingiu_alvo true', async () => {
  const pontuar = async () => analiseBase(90);
  const pacote = await montarPacoteOtimizacao({ texto: 'x', pontuar, session: null });
  assert.equal(pacote.atingiu_alvo, true);
});

test('libera o gate conforme a medição, gravando o texto de entrada (paridade com score)', async () => {
  const session = fakeSession();
  const pontuar = async () => analiseBase(90);
  await montarPacoteOtimizacao({ texto: 'entrada', pontuar, session });
  assert.equal(session.chamadas.variancia[0].a, true);
  assert.equal(session.chamadas.lexico[0].a, true);
  assert.equal(session.chamadas.variancia[0].t, 'entrada');
  assert.equal(session.chamadas.lexico[0].t, 'entrada');
});

test('abaixo do alvo NÃO libera o gate', async () => {
  const session = fakeSession();
  const pontuar = async () => analiseBase(60);
  await montarPacoteOtimizacao({ texto: 'entrada', pontuar, session });
  assert.equal(session.chamadas.variancia[0].a, false);
  assert.equal(session.chamadas.lexico[0].a, false);
});

test('inaplicável: libera ambos os flags e não erra', async () => {
  const session = fakeSession();
  const pontuar = async () => ({ inaplicavel: true, relatorio: 'texto curto demais' });
  const pacote = await montarPacoteOtimizacao({ texto: 'Oi.', pontuar, session });
  assert.equal(pacote.inaplicavel, true);
  assert.equal(pacote.relatorio, 'texto curto demais');
  assert.equal(session.chamadas.variancia[0].a, true);
  assert.equal(session.chamadas.lexico[0].a, true);
  assert.equal(session.chamadas.variancia[0].t, 'Oi.');
});

test('erro de medição: propaga erro sem tocar no gate', async () => {
  const session = fakeSession();
  const pontuar = async () => ({ erro: 'falha ao medir' });
  const pacote = await montarPacoteOtimizacao({ texto: 'x', pontuar, session });
  assert.equal(pacote.erro, 'falha ao medir');
  assert.equal(session.chamadas.variancia.length, 0);
  assert.equal(session.chamadas.lexico.length, 0);
});

test('componentes fracos são os de contribuição negativa, ordenados da mais negativa, com o sinal 0-1 junto', async () => {
  const resumo = resumoDiagnostico(
    analiseBase(60, {
      score: {
        total: 60, alvo: 80,
        componentes: { burstiness: -2.5, sem_pivots: 0.8, zipf: -0.3 },
        sinais: { burstiness: 0.2, sem_pivots: 0.9, zipf: 0.5 },
      },
    })
  );
  assert.match(resumo, /burstiness: -2\.5 \(sinal 0\.2\)/);
  assert.match(resumo, /zipf: -0\.3 \(sinal 0\.5\)/);
  assert.doesNotMatch(resumo, /sem_pivots/);
  assert.ok(resumo.indexOf('burstiness') < resumo.indexOf('zipf'));
});
```

- [ ] **Step 2: Rodar os testes e ver falhar**

Run: `cd server && node --test test/otimizar.test.js`
Expected: FAIL — `montarPacoteOtimizacao` não é exportada (ainda existe `otimizarTexto`).

- [ ] **Step 3: Reescrever `server/tools/otimizar.js`**

Substituir todo o conteúdo por:

```js
import { z } from 'zod';
import { runPython } from './run-python.js';
import { getSection } from '../content/registry.js';
import { ALVO_SCORE } from '../knowledge/phases.js';

// Roteiro de reescrita entregue ao HOST (antes era o system prompt de uma
// chamada de API). O host aplica estas técnicas guiado pelo diagnóstico.
export const ROTEIRO_REESCRITA = `Reescreva o texto corrigindo APENAS o que o diagnóstico aponta (score 0-100 = probabilidade de texto humano × 100; alvo >= ${ALVO_SCORE}):

RITMO:
- Quebre sentenças longas ou uniformes (candidatas apontadas) criando 1-2 sentenças muito curtas de impacto (1-5 palavras).
- Funda sentenças curtas consecutivas com vírgula ou conjunção, criando 1-2 sentenças bem longas (30+ palavras).
- Insira 1-2 orações subordinadas não-canônicas: anteposta ("Quando o servidor caiu, ninguém notou."), intercalada ("O projeto, embora atrasado, saiu.") ou gerúndio inicial.
- Varie inícios de sentença repetidos.

LÉXICO:
- Troque cada ocorrência de vocabulário pivot apontada por uma das alternativas sugeridas, escolhendo a que cabe no contexto (ou corte a expressão).
- Reduza repetições de palavras de conteúdo e trigramas repetidos apontados, com sinônimos ou retomadas naturais.

ESTRUTURA:
- Se parágrafos forem uniformes, misture um parágrafo curto com outros longos.
- Se 3+ parágrafos seguidos abrirem com conectivo lógico, remova ao menos um.

Regras invioláveis:
- Preserve TODO o conteúdo, o sentido e o registro; não acrescente nem remova informação.
- PROIBIDO travessão (—) e meia-risca (–); use vírgula, parênteses, dois-pontos ou ponto.
- Não introduza conectores clichê ("Além disso", "No entanto", "Em conclusão") nem aberturas de IA.
- Mantenha a divisão de parágrafos e o markdown existente.
- Se uma alteração piorar a frase, escolha outra candidata: a otimização nunca degrada o texto.
- Após reescrever, meça de novo com texto_br_score; se o score cair, descarte a reescrita e volte à versão anterior.`;

// Resumo do diagnóstico priorizado. Componentes "fracos" são os de contribuição
// NEGATIVA no logit do modelo calibrado: os sinais que puxam o score para "IA"
// (o valor 0-1 correspondente aparece em score.sinais para contexto).
export function resumoDiagnostico(resultado) {
  const s = resultado.score;
  const sinais = s.sinais ?? {};
  const fracos = Object.entries(s.componentes)
    .filter(([, v]) => v < 0)
    .sort(([, a], [, b]) => a - b)
    .map(([k, v]) => `${k}: ${v} (sinal ${sinais[k] ?? '?'})`)
    .join(', ');
  const partes = [
    `score atual: ${s.total}/100 (alvo >= ${s.alvo}) | componentes fracos: ${fracos || 'nenhum'}`,
    '### Ritmo',
    ...resultado.ritmo.diagnostico,
  ];
  if (resultado.ritmo.candidatas_quebra_fusao?.length) {
    partes.push(
      'Candidatas a quebra/fusão: ' +
        resultado.ritmo.candidatas_quebra_fusao
          .slice(0, 8)
          .map((c) => `S${c.indice} (${c.palavras}p) "${c.trecho}"`)
          .join('; ')
    );
  }
  partes.push('### Léxico', ...resultado.lexico.diagnostico);
  if (resultado.lexico.ocorrencias?.length) {
    partes.push(
      'Pivots a trocar: ' +
        resultado.lexico.ocorrencias
          .slice(0, 12)
          .map((o) => `S${o.sentenca} "${o.encontrado}" → ${o.alternativas}`)
          .join('; ')
    );
  }
  return partes.join('\n');
}

// Mede o texto uma vez e monta o pacote acionável (diagnóstico + score) para o
// HOST reescrever. Sem client, sem API, sem loop: o loop de subida de encosta é
// dirigido pelo host (guidance da Fase 2). O gate espelha texto_br_score: mede o
// texto de entrada e libera os flags conforme a medição. Injetável/testável
// (pontuar/session fakes).
export async function montarPacoteOtimizacao({ texto, pontuar, session }) {
  const analise = await pontuar(texto);
  if (analise.inaplicavel) {
    // Texto curto demais para medir (mesmo contrato de texto_br_score): não há o
    // que reescrever, mas também não trava o gate.
    if (session) {
      session.registrarVariancia(true, texto);
      session.registrarLexico(true, texto);
    }
    return { inaplicavel: true, relatorio: analise.relatorio };
  }
  if (analise.erro) return { erro: analise.erro };

  if (session) {
    session.registrarVariancia(
      analise.ritmo.atingiu_alvo === true || analise.atingiu_alvo === true,
      texto
    );
    session.registrarLexico(
      analise.lexico.atingiu_alvo === true || analise.atingiu_alvo === true,
      texto
    );
  }
  return {
    atingiu_alvo: analise.atingiu_alvo === true,
    score: analise.score,
    diagnostico: resumoDiagnostico(analise),
    relatorio: analise.relatorio,
  };
}

export function register(server, session) {
  server.registerTool(
    'texto_br_otimizar',
    {
      title: 'Pacote de otimização (diagnóstico + roteiro de reescrita)',
      description:
        'Empacota numa única chamada o diagnóstico priorizado do score de humanidade ' +
        '(texto_br_score) e o roteiro de reescrita (ritmo, léxico e estrutura + regras ' +
        'invioláveis) para o HOST reescrever o texto. Não chama modelo nenhum nem requer ' +
        `credencial. Mede o texto de entrada; se ainda abaixo do alvo (>= ${ALVO_SCORE}), ` +
        'devolve os pontos a corrigir e como corrigi-los. Reescreva e remeça com ' +
        'texto_br_score, repetindo até o alvo (descarte reescritas que baixem o score).',
      inputSchema: {
        texto: z
          .string()
          .min(1)
          .describe('Rascunho completo a diagnosticar (markdown ou texto puro)'),
      },
    },
    async ({ texto }) => {
      try {
        const secao10 = getSection('humanizacao-algoritmos', 10);
        const pontuar = (t) => runPython('score.py', JSON.stringify({ texto: t, secao10 }));
        const pacote = await montarPacoteOtimizacao({ texto, pontuar, session });

        if (pacote.erro) {
          return { isError: true, content: [{ type: 'text', text: pacote.erro }] };
        }
        if (pacote.inaplicavel) {
          return { content: [{ type: 'text', text: pacote.relatorio }] };
        }
        if (pacote.atingiu_alvo) {
          const text = [
            `Score ${pacote.score.total}/100 — alvo (>= ${pacote.score.alvo}) já atingido. Nada a reescrever.`,
            pacote.relatorio,
          ].join('\n\n');
          return { content: [{ type: 'text', text }] };
        }
        const text = [
          `Score ${pacote.score.total}/100 (alvo >= ${pacote.score.alvo}). Reescreva os pontos abaixo seguindo o roteiro; depois remeça com texto_br_score e repita até o alvo. Se o score cair, descarte a reescrita e volte à versão anterior.`,
          '## Diagnóstico priorizado',
          pacote.diagnostico,
          '## Roteiro de reescrita',
          ROTEIRO_REESCRITA,
          '## Relatório completo',
          pacote.relatorio,
        ].join('\n\n');
        return { content: [{ type: 'text', text }] };
      } catch (err) {
        return { isError: true, content: [{ type: 'text', text: err.message }] };
      }
    }
  );
}
```

- [ ] **Step 4: Rodar os testes e ver passar**

Run: `cd server && node --test test/otimizar.test.js`
Expected: PASS (7 testes).

- [ ] **Step 5: Rodar a suíte inteira (garantir que nada quebrou)**

Run: `cd server && node --test`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add server/tools/otimizar.js server/test/otimizar.test.js
git commit -m "refactor(otimizar): tool sem API — empacota diagnóstico + roteiro para o host"
```

---

### Task 2: Remover a dependência `@anthropic-ai/sdk`

**Files:**
- Modify: `server/package.json`
- Modify: `server/package-lock.json`

**Interfaces:**
- Consumes: Task 1 já removeu todo uso do SDK no código.
- Produces: `package.json` sem `@anthropic-ai/sdk`.

- [ ] **Step 1: Confirmar que nada mais importa o SDK**

Run: `cd server && grep -rn "@anthropic-ai/sdk" --include="*.js" . | grep -v node_modules`
Expected: nenhuma linha.

- [ ] **Step 2: Desinstalar o pacote**

Run: `cd server && npm uninstall @anthropic-ai/sdk`
Expected: `package.json` e `package-lock.json` atualizados; `@anthropic-ai/sdk` removido de `node_modules`.

- [ ] **Step 3: Rodar a suíte**

Run: `cd server && node --test`
Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add server/package.json server/package-lock.json
git commit -m "chore(server): remove dependência @anthropic-ai/sdk"
```

---

### Task 3: Guidance da Fase 2 e instructions do servidor

**Files:**
- Modify: `server/knowledge/phases.js` (`LOOP_QUANTITATIVO_GUIDANCE`, ~linha 249)
- Modify: `server/server.js` (string `instructions`, ~linha 26)

**Interfaces:**
- Consumes: novo contrato de `texto_br_otimizar` da Task 1.
- Produces: guidance sem a dicotomia "via automática vs manual".

- [ ] **Step 1: Reescrever `LOOP_QUANTITATIVO_GUIDANCE` em `server/knowledge/phases.js`**

Substituir a constante (do `export const LOOP_QUANTITATIVO_GUIDANCE = ...` até o backtick de fechamento) por:

```js
export const LOOP_QUANTITATIVO_GUIDANCE = `## Loop quantitativo (ATIVADO)

Depois de aplicar as cinco técnicas de superfície acima, otimize contra o score de humanidade (probabilidade de texto humano × 100; alvo >= ${ALVO_SCORE}). O loop é dirigido por você (o host); nenhuma tool reescreve o texto por você:

1. Chame texto_br_otimizar com o rascunho completo: numa única chamada ele mede o texto e devolve o diagnóstico priorizado (componentes fracos + candidatas de quebra/fusão + pivots a trocar) e o roteiro de reescrita (ritmo, léxico e estrutura + regras invioláveis). Se o texto já atingiu o alvo, ele avisa e não há o que reescrever.
2. Reescreva APENAS os pontos apontados, seguindo o roteiro:
   - **Ritmo (injeção de variância sintática)**: quebre candidatas em sentenças muito curtas (1-5 palavras), funda curtas consecutivas em longas (30+), insira 1-2 subordinadas não-canônicas (anteposta: "Quando X, Y"; intercalada: "O projeto, embora atrasado, saiu"; gerúndio inicial), varie inícios repetidos.
   - **Léxico (perturbação lexical controlada)**: troque cada pivot apontado pela alternativa que cabe no contexto (ou corte). As listas são o PISO: perturbe também palavras previsíveis demais no contexto deste texto (use repetições, diversidade e trigramas como sinal).
   - **Estrutura**: parágrafos uniformes e correntes de conectivos apontados.
3. Meça de novo (texto_br_score, que satisfaz o gate numa chamada, ou texto_br_otimizar). Repita até "ALVO ATINGIDO", com no máximo 3 iterações. Se o score CAIR após uma reescrita, descarte-a e volte à versão anterior: a otimização nunca degrada o texto.`;
```

- [ ] **Step 2: Atualizar a descrição de `texto_br_otimizar` na string `instructions` de `server/server.js`**

Localizar o trecho (dentro da string de instruções, ~linha 26):

`texto_br_otimizar(texto) para otimizar automaticamente contra o score via Claude API (subida de encosta com anti-degradação; requer ANTHROPIC_API_KEY no servidor);`

Substituir por:

`texto_br_otimizar(texto) para receber numa chamada o diagnóstico priorizado do score + o roteiro de reescrita (ritmo, léxico e estrutura) e reescrever você mesmo o rascunho (sem API nem credencial; o loop é dirigido por você);`

- [ ] **Step 3: Verificar que o servidor sobe sem credencial e sem menções à API**

Run: `cd server && grep -rn "ANTHROPIC_API_KEY\|Claude API\|via autom" knowledge/ server.js`
Expected: nenhuma linha.

Run: `cd server && env -u ANTHROPIC_API_KEY node -e "import('./server.js').then(() => console.log('OK: servidor importado sem credencial')).catch(e => { console.error(e); process.exit(1); })"`
Expected: `OK: servidor importado sem credencial` (sem erro de credencial). Se `server.js` iniciar o transporte no import e travar, em vez disso rode `node --check server.js` e confirme a suíte `node --test`.

- [ ] **Step 4: Commit**

```bash
git add server/knowledge/phases.js server/server.js
git commit -m "docs(otimizar): guidance da Fase 2 e instructions sem via-API"
```

---

### Task 4: Documentação viva (SKILL.md e server/README.md)

**Files:**
- Modify: `SKILL.md` (~linha 98)
- Modify: `server/README.md` (~linhas 9, 35, 72)

**Interfaces:**
- Consumes: novo contrato de `texto_br_otimizar`.
- Produces: docs sem referência a `ANTHROPIC_API_KEY`/Claude API para otimizar.

- [ ] **Step 1: Atualizar `SKILL.md` (~linha 98)**

Localizar a frase:

`\`texto_br_otimizar\` é o atalho automático: roda a subida de encosta inteira via Claude API (requer credencial).`

Substituir por:

`\`texto_br_otimizar\` é o atalho de diagnóstico: numa chamada devolve os pontos fracos priorizados e o roteiro de reescrita para você mesmo reescrever (sem API nem credencial).`

- [ ] **Step 2: Atualizar `server/README.md` linha ~9**

Localizar:

`- Opcional: \`ANTHROPIC_API_KEY\` no ambiente — habilita \`texto_br_otimizar\` (correção automática de ritmo via Claude API; sem a chave, a tool retorna erro amigável e o fluxo manual segue normal)`

Remover essa linha inteira (a tool não depende mais de credencial).

- [ ] **Step 3: Atualizar `server/README.md` linha ~35 (tabela de tools)**

Localizar:

`| \`texto_br_otimizar(texto)\` | Otimiza contra o score via Claude API: subida de encosta com anti-degradação (requer credencial) |`

Substituir por:

`| \`texto_br_otimizar(texto)\` | Empacota diagnóstico priorizado + roteiro de reescrita para o host reescrever (sem API) |`

- [ ] **Step 4: Atualizar `server/README.md` linha ~72 (tabela de variáveis de ambiente)**

Localizar e remover a linha:

`| \`ANTHROPIC_API_KEY\` | Habilita \`texto_br_otimizar\` |`

Se a tabela ficar sem linhas de dados úteis, ajustar o texto ao redor para não deixar cabeçalho órfão (manter apenas variáveis que ainda existem, ex.: `TEXTO_BR_*` se houver; caso contrário, remover a tabela e a frase introdutória).

- [ ] **Step 5: Verificação final integrada**

Run: `grep -rn "ANTHROPIC_API_KEY\|@anthropic-ai/sdk" SKILL.md server/ | grep -v node_modules`
Expected: nenhuma linha.

Run: `cd server && node --test`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add SKILL.md server/README.md
git commit -m "docs(otimizar): README e SKILL sem via-API para otimizar"
```

---

## Notas de execução

- Ordem obrigatória: Task 1 antes da Task 2 (o `npm uninstall` só é seguro depois que o código para de importar o SDK).
- Tasks 3 e 4 dependem do contrato definido na Task 1, mas não do estado da Task 2.
- A verificação de que `server.js` importa sem `ANTHROPIC_API_KEY` (Task 3, Step 3) é o teste de aceitação central do objetivo: o servidor funciona por si.
