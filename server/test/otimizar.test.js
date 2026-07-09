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
