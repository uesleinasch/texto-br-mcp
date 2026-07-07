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

test('rejeita candidato truncado por max_tokens', async () => {
  const client = fakeClient([
    { stop_reason: 'max_tokens', content: [{ type: 'text', text: 'texto cortado' }] },
  ]);
  const scores = [60]; // só a medição inicial: candidato truncado nem é pontuado
  const pontuar = async () => analiseBase(scores.shift() ?? 60);
  const r = await otimizarTexto({ texto: 'original', client, pontuar, session: null });
  assert.equal(r.melhor.texto, 'original');
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
