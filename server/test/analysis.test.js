import { test, before } from 'node:test';
import assert from 'node:assert/strict';
import { runPython } from '../tools/run-python.js';
import { loadAll } from '../content/loader.js';
import { buildIndexes, getSection } from '../content/registry.js';

const TEXTO_UNIFORME = `A meditação diária traz benefícios comprovados para a saúde. A prática regular melhora bastante a qualidade do sono. A redução da ansiedade é outro efeito muito documentado. A rotina dos praticantes ganha foco e concentração maiores. A ciência acompanha esses resultados com atenção crescente hoje. A comunidade médica reconhece o valor da técnica nova.`;

const TEXTO_VARIADO = `Comecei a meditar num sábado qualquer de 2019, mais por teimosia do que por convicção, e o tédio dos primeiros dias quase me venceu logo de cara. Desisti? Quase. Mas na terceira semana o sono melhorou primeiro, depois veio uma paciência esquisita nas reuniões, dessas que os colegas percebem antes de você mesmo notar qualquer mudança. Não virei outra pessoa. Só parei de correr atrás de um relógio que ninguém me cobrava.`;

const TEXTO_PIVOT = `Nos dias atuais, é fundamental ressaltar que a meditação desempenha um papel crucial no panorama da saúde. Além disso, estudos robustos evidenciam benefícios significativos para o sono dos praticantes. A jornada proporciona insights valiosos sobre o mindset de cada um durante o processo.`;

before(async () => {
  await loadAll(new URL('../../references/', import.meta.url).pathname);
  buildIndexes();
});

test('variancia: texto uniforme reprova com diagnóstico', async () => {
  const r = await runPython('variancia.py', TEXTO_UNIFORME);
  assert.equal(r.atingiu_alvo, false);
  assert.ok(r.metricas.burstiness < 0.5);
  assert.ok(r.diagnostico.some((d) => d.startsWith('INTERVIR')));
  assert.ok(r.relatorio.includes('REESCREVER'));
});

test('variancia: texto variado atinge o alvo', async () => {
  const r = await runPython('variancia.py', TEXTO_VARIADO);
  assert.equal(r.atingiu_alvo, true, JSON.stringify(r.diagnostico));
  assert.ok(r.metricas.burstiness >= 0.7);
  assert.ok(r.metricas.nao_canonicas >= 0);
});

test('lexico: parseia as 6 categorias da seção 10 e detecta pivots', async () => {
  const secao10 = getSection('humanizacao-algoritmos', 10);
  const r = await runPython('lexico.py', JSON.stringify({ texto: TEXTO_PIVOT, secao10 }));
  const categorias = Object.keys(r.metricas.tabelas_carregadas);
  for (const c of ['verbos', 'adjetivos', 'substantivos', 'conectores', 'aberturas', 'fechamentos']) {
    assert.ok(categorias.includes(c), `categoria ${c} não parseada`);
  }
  assert.equal(r.atingiu_alvo, false);
  assert.ok(r.metricas.ocorrencias_pivot >= 10);
  assert.ok(r.ocorrencias.some((o) => o.categoria === 'aberturas'));
});

test('lexico: texto limpo atinge o alvo', async () => {
  const secao10 = getSection('humanizacao-algoritmos', 10);
  const r = await runPython('lexico.py', JSON.stringify({ texto: TEXTO_VARIADO, secao10 }));
  assert.equal(r.atingiu_alvo, true, JSON.stringify(r.ocorrencias));
});

test('score: separa texto humano (>= 80) de texto LLM (< 80)', async () => {
  const secao10 = getSection('humanizacao-algoritmos', 10);
  const bom = await runPython('score.py', JSON.stringify({ texto: TEXTO_VARIADO, secao10 }));
  assert.ok(bom.score.total >= 80, `texto bom pontuou ${bom.score.total}`);
  assert.equal(bom.atingiu_alvo, true);

  const ruim = await runPython('score.py', JSON.stringify({ texto: TEXTO_PIVOT, secao10 }));
  assert.ok(ruim.score.total < 80, `texto pivot pontuou ${ruim.score.total}`);
  assert.equal(ruim.atingiu_alvo, false);
  assert.ok(ruim.relatorio.includes('| Componente | Pontos |'));
});

test('analisadores ignoram código e headings de markdown', async () => {
  const md = `# Título\n\n${TEXTO_VARIADO}\n\n\`\`\`\ncodigo. ignorado. aqui. sempre. mesmo. tamanho. fixo.\n\`\`\`\n`;
  const r = await runPython('variancia.py', md);
  assert.equal(r.atingiu_alvo, true);
});
