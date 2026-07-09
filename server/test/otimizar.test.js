import test from 'node:test';
import assert from 'node:assert';
import { otimizarTexto, resumoDiagnostico } from '../tools/otimizar.js';

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

const fakeClient = (respostas) => {
  let i = 0;
  return {
    messages: {
      create: async () => {
        const r = respostas[i++];
        if (r instanceof Error) throw r;
        return r;
      },
    },
  };
};

test('descarta candidato truncado por max_tokens mas segue o loop e aceita melhora válida', async () => {
  // Iteração 1 trunca (deve ser descartada, NÃO aceita); iteração 2 traz melhora
  // válida e é aceita. Abortar o loop com break jogaria fora o orçamento de
  // iterações; o correto é descartar o candidato e continuar a subida de encosta.
  const client = fakeClient([
    { stop_reason: 'max_tokens', content: [{ type: 'text', text: 'texto cortado' }] },
    { stop_reason: 'end_turn', content: [{ type: 'text', text: 'versão melhorada e completa' }] },
  ]);
  const scores = [60, 85]; // só medições reais: inicial + candidato válido; o truncado nem é pontuado
  const pontuar = async () => analiseBase(scores.shift() ?? 85);
  const r = await otimizarTexto({ texto: 'original', client, pontuar, session: null });
  assert.equal(r.melhor.texto, 'versão melhorada e completa');
  assert.equal(r.melhor.analise.score.total, 85);
  assert.equal(scores.length, 0); // exatamente 2 pontuações: o candidato truncado nunca foi medido
});

test('todas as respostas truncadas: preserva o original sem abortar por erro', async () => {
  // Loop roda até MAX_SEM_MELHORA sem crashar; nenhum candidato válido → original mantido.
  const client = fakeClient([
    { stop_reason: 'max_tokens', content: [{ type: 'text', text: 'corte 1' }] },
    { stop_reason: 'max_tokens', content: [{ type: 'text', text: 'corte 2' }] },
  ]);
  const scores = [60]; // só a medição inicial: candidatos truncados nunca são pontuados
  const pontuar = async () => analiseBase(scores.shift() ?? 60);
  const r = await otimizarTexto({ texto: 'original', client, pontuar, session: null });
  assert.equal(r.melhor.texto, 'original');
});

test('descarta candidato com comprimento suspeito (< 80%) e segue o loop', async () => {
  const original = 'Este é um texto original razoavelmente longo com bastante conteúdo para o teste.';
  const client = fakeClient([
    { stop_reason: 'end_turn', content: [{ type: 'text', text: 'curto' }] }, // < 80% do original: descartado
    {
      stop_reason: 'end_turn',
      content: [{ type: 'text', text: 'Versão melhorada mantendo praticamente todo o comprimento original do texto aqui.' }],
    },
  ]);
  const scores = [60, 85]; // inicial + candidato de comprimento OK; o curto nunca é pontuado
  const pontuar = async () => analiseBase(scores.shift() ?? 85);
  const r = await otimizarTexto({ texto: original, client, pontuar, session: null });
  assert.match(r.melhor.texto, /Versão melhorada/);
  assert.notEqual(r.melhor.texto, 'curto');
  assert.equal(scores.length, 0); // candidato curto nunca foi medido
});

test('falha de API no meio do loop devolve a melhor versão, não erro', async () => {
  const client = fakeClient([
    { stop_reason: 'end_turn', content: [{ type: 'text', text: 'versão melhorada' }] },
    new Error('overloaded'),
  ]);
  const scores = [60, 75];
  const pontuar = async () => analiseBase(scores.shift() ?? 75);
  const r = await otimizarTexto({ texto: 'original', client, pontuar, session: null });
  assert.equal(r.melhor.texto, 'versão melhorada');
  assert.equal(r.melhor.analise.score.total, 75);
  assert.match(r.aviso ?? '', /falha|erro/i);
});

test('componentes fracos são os de contribuição negativa, ordenados da mais negativa, com o sinal 0-1 junto', async () => {
  // burstiness (-2.5) e zipf (-0.3) puxam para "IA" (fracos); sem_pivots (0.8),
  // com contribuição positiva, não é fraco e não deve aparecer no resumo.
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
  // ordenado da contribuição mais negativa primeiro
  assert.ok(resumo.indexOf('burstiness') < resumo.indexOf('zipf'));
});

test('grava veredito na sessão com o texto da melhor versão (wiring da Task 5)', async () => {
  const chamadas = { variancia: [], lexico: [] };
  const session = {
    registrarVariancia: (atingido, texto) => chamadas.variancia.push({ atingido, texto }),
    registrarLexico: (atingido, texto) => chamadas.lexico.push({ atingido, texto }),
  };
  const client = fakeClient([
    { stop_reason: 'end_turn', content: [{ type: 'text', text: 'versão melhorada aqui' }] },
  ]);
  const scores = [60, 85];
  const pontuar = async () => analiseBase(scores.shift() ?? 85);
  const r = await otimizarTexto({ texto: 'original', client, pontuar, session });

  assert.equal(chamadas.variancia.length, 1);
  assert.equal(chamadas.lexico.length, 1);
  // O hash do gate (gravado pelos registrar* da Task 5) deve bater com o
  // rascunho otimizado, não com o texto de entrada.
  assert.equal(chamadas.variancia[0].texto, r.melhor.texto);
  assert.equal(chamadas.lexico[0].texto, r.melhor.texto);
  assert.equal(chamadas.variancia[0].texto, 'versão melhorada aqui');
  assert.equal(chamadas.variancia[0].atingido, true);
  assert.equal(chamadas.lexico[0].atingido, true);
});

test('texto curto demais (inaplicavel): libera o gate em vez de só devolver erroInicial (achado Minor)', async () => {
  // texto_br_score já libera o gate (registra os dois flags) para texto curto
  // demais para medir; otimizarTexto tratava esse mesmo caso como erroInicial
  // puro, sem registrar nada — inconsistente entre as duas tools para o
  // mesmo texto. client não deveria nem ser chamado: não há o que otimizar.
  const chamadas = { variancia: [], lexico: [] };
  const session = {
    registrarVariancia: (atingido, texto) => chamadas.variancia.push({ atingido, texto }),
    registrarLexico: (atingido, texto) => chamadas.lexico.push({ atingido, texto }),
  };
  const client = fakeClient([]);
  const pontuar = async () => ({ erro: 'Texto curto demais; análise não se aplica.', inaplicavel: true });
  const r = await otimizarTexto({ texto: 'Oi. Tudo bem?', client, pontuar, session });

  assert.equal(chamadas.variancia.length, 1);
  assert.equal(chamadas.lexico.length, 1);
  assert.equal(chamadas.variancia[0].atingido, true);
  assert.equal(chamadas.lexico[0].atingido, true);
  assert.equal(chamadas.variancia[0].texto, 'Oi. Tudo bem?');
  assert.equal(chamadas.lexico[0].texto, 'Oi. Tudo bem?');
  assert.equal(r.erroInicial, undefined);
  assert.match(r.aviso ?? '', /curto demais|não se aplica/i);
});
