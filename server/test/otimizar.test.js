import test from 'node:test';
import assert from 'node:assert';
import { otimizarTexto, resumoDiagnostico } from '../tools/otimizar.js';

const analiseBase = (total, extras = {}) => ({
  atingiu_alvo: total >= 80,
  score: { total, alvo: 80, componentes: { burstiness: 10, sem_pivots: 12 }, maximos: { burstiness: 25, sem_pivots: 25 } },
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

test('componentes fracos usam fração do máximo, não corte absoluto', async () => {
  // burstiness 10/25 (40%) é fraco; um binário 3/5 (60%) não é
  const resumo = resumoDiagnostico(
    analiseBase(60, {
      score: {
        total: 60, alvo: 80,
        componentes: { burstiness: 10, alt_binaria: 3 },
        maximos: { burstiness: 25, alt_binaria: 5 },
      },
    })
  );
  assert.match(resumo, /burstiness/);
  assert.doesNotMatch(resumo, /alt_binaria/);
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
