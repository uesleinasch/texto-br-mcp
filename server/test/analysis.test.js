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

test('lexico: seção 10 vazia é erro real, não aprovação silenciosa', async () => {
  const r = await runPython('lexico.py', JSON.stringify({ texto: TEXTO_VARIADO, secao10: '' }));
  assert.ok(r.erro, 'deveria retornar erro');
  assert.ok(!r.inaplicavel, 'erro real, não inaplicabilidade');
  assert.notEqual(r.atingiu_alvo, true);
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

test('score: separa texto humano (>= alvo calibrado) de texto LLM (< alvo)', async () => {
  const secao10 = getSection('humanizacao-algoritmos', 10);
  const bom = await runPython('score.py', JSON.stringify({ texto: TEXTO_VARIADO, secao10 }));
  assert.ok(bom.score.total >= bom.score.alvo, `texto bom pontuou ${bom.score.total} (alvo ${bom.score.alvo})`);
  assert.equal(bom.atingiu_alvo, true);

  const ruim = await runPython('score.py', JSON.stringify({ texto: TEXTO_PIVOT, secao10 }));
  assert.ok(ruim.score.total < ruim.score.alvo, `texto pivot pontuou ${ruim.score.total} (alvo ${ruim.score.alvo})`);
  assert.equal(ruim.atingiu_alvo, false);
  assert.ok(ruim.relatorio.includes('| Sinal | Valor (0-1) | Contribuição |'));

  // separação relativa: o texto bom deve pontuar bem acima do texto ruim,
  // independente de onde o ALVO calibrado esteja hoje (evita magic number
  // que descasa do score.ALVO real após recalibrações futuras, cf. Etapa 3)
  assert.ok(bom.score.total > ruim.score.total + 20,
    `separação insuficiente: bom ${bom.score.total} vs ruim ${ruim.score.total}`);
});

test('analisadores ignoram código e headings de markdown', async () => {
  const md = `# Título\n\n${TEXTO_VARIADO}\n\n\`\`\`\ncodigo. ignorado. aqui. sempre. mesmo. tamanho. fixo.\n\`\`\`\n`;
  const r = await runPython('variancia.py', md);
  assert.equal(r.atingiu_alvo, true);
});

// --- Análise macroestrutural (estrutura.py) ---

const ESTR_IA = `# Hábitos que transformam

## Entendendo o problema

A rotina molda quem somos ao longo dos anos, e as pequenas escolhas diárias se acumulam em direções que ninguém planeja de antemão. Os estudos sobre comportamento mostram esse padrão com clareza. No fim, somos o que repetimos todo santo dia.

Quem ignora os próprios hábitos acaba refém deles sem perceber o quanto. A consciência é o primeiro movimento de qualquer mudança real. Afinal, ninguém conserta o que não enxerga.

## Aplicando a mudança

Comece pequeno e seja consistente com o processo, porque a ambição exagerada costuma cobrar um preço alto logo nos primeiros dias. A constância vence a intensidade em quase tudo que importa. No fundo, é a repetição que constrói.

Ajuste o ambiente para que o bom comportamento seja o caminho mais fácil de seguir. Um gatilho visível vale mais que toda a força de vontade do mundo. É isso que sustenta o hábito.

## Construindo o futuro

O amanhã se constrói no gesto repetido de hoje, mesmo quando esse gesto parece pequeno demais para significar alguma coisa. Cada dia é um tijolo na parede que você ergue sem ver. No fim das contas, é tudo uma questão de paciência.

A identidade segue o comportamento, e não o contrário, como muitos imaginam no começo. Você vira aquilo que pratica com regularidade. A verdade é que mudamos devagar.`;

const ESTR_HUMANO = `# O sábado em que parei de correr

Comecei a meditar num sábado qualquer de 2019, mais por teimosia do que por convicção, e o tédio dos primeiros dias quase me venceu. A cadeira rangia. Eu olhava o relógio do micro-ondas a cada dois minutos achando que tinha passado meia hora.

## O que mudou (e o que não mudou)

Na terceira semana o sono melhorou. Não foi epifania nenhuma, foi só uma noite em que dormi sem rolar na cama, e aí outra, e aí virou hábito sem eu perceber direito quando.

Os colegas notaram antes de mim. Diziam que eu tinha ficado mais paciente nas reuniões intermináveis de quarta, aquelas que não levam a lugar nenhum e que eu detestava com todas as forças.

Hoje ainda perco a paciência no trânsito. Meditar não me fez santo. Só me deu uns segundos a mais entre o estímulo e a besteira que eu ia falar, e às vezes esses segundos bastam, às vezes não bastam coisa nenhuma e eu xingo igual.`;

test('estrutura: texto IA-encaixado reprova com plano de perturbação', async () => {
  const r = await runPython('estrutura.py', JSON.stringify({ texto: ESTR_IA, tipo: 'blog' }));
  assert.equal(r.atingiu_alvo, false, JSON.stringify(r.score));
  assert.ok(r.score.total < 70, `pontuou ${r.score.total}`);
  assert.ok(r.relatorio.includes('Plano de perturbação'));
});

test('estrutura: simetria detecta seções gêmeas e títulos paralelos', async () => {
  const r = await runPython('estrutura.py', JSON.stringify({ texto: ESTR_IA, tipo: 'blog' }));
  const sim = r.detectores.find((d) => d.id === 'simetria_secoes');
  assert.ok(sim.aplicavel);
  assert.ok(sim.subscore < 0.5, `subscore ${sim.subscore}`);
  assert.ok(sim.perturbacoes.length >= 1);
});

test('estrutura: kicker uniforme detectado em ESTR_IA', async () => {
  const r = await runPython('estrutura.py', JSON.stringify({ texto: ESTR_IA, tipo: 'blog' }));
  const k = r.detectores.find((d) => d.id === 'kicker_uniforme');
  assert.ok(k.aplicavel);
  assert.ok(k.subscore < 0.6, `subscore ${k.subscore}`);
});

test('estrutura: texto humano-variado passa', async () => {
  const r = await runPython('estrutura.py', JSON.stringify({ texto: ESTR_HUMANO, tipo: 'blog' }));
  assert.ok(r.score.total >= 70, `pontuou ${r.score.total}`);
  assert.equal(r.atingiu_alvo, true);
});

test('estrutura: texto curto demais retorna erro', async () => {
  const r = await runPython('estrutura.py', JSON.stringify({ texto: 'Uma frase só.', tipo: 'blog' }));
  assert.ok(r.erro);
});

test('estrutura: inflação de subtópicos detecta seções finas', async () => {
  const md = `# Guia\n\n## A\n\nUma linha curta só aqui.\n\n## B\n\nOutra linha curta aqui.\n\n## C\n\nMais uma curtíssima.\n\n## D\n\nE a última bem curta.`;
  const r = await runPython('estrutura.py', JSON.stringify({ texto: md, tipo: 'blog' }));
  const inf = r.detectores.find((d) => d.id === 'inflacao_subtopicos');
  assert.ok(inf.aplicavel);
  assert.ok(inf.subscore < 0.6, `subscore ${inf.subscore}`);
});

test('estrutura: frases de efeito em sequência', async () => {
  const md = `# T\n\nA vida é curta.\n\nO tempo não volta.\n\nCada dia conta.\n\nFaça valer.\n\nAgora desenvolvo um parágrafo de verdade, com mais de uma sentença e alguma respiração, para não ser bordão. Ele segue por aqui sem pressa.`;
  const r = await runPython('estrutura.py', JSON.stringify({ texto: md, tipo: 'blog' }));
  const f = r.detectores.find((d) => d.id === 'frases_efeito');
  assert.ok(f.aplicavel);
  assert.ok(f.subscore < 0.6, `subscore ${f.subscore}`);
});

test('estrutura: progressão sinalizada (escada de signposts)', async () => {
  const md = `# Plano\n\n## Primeiro passo\n\nPara começar, organize a mesa de trabalho com calma e atenção aos detalhes do dia.\n\n## Em seguida\n\nDepois, defina as três prioridades do dia com calma e atenção aos detalhes.\n\n## Em terceiro lugar\n\nAgora que tudo está pronto, execute a primeira tarefa sem pressa nenhuma.\n\n## Por fim\n\nFinalmente, revise tudo o que foi feito com calma e atenção aos detalhes restantes.`;
  const r = await runPython('estrutura.py', JSON.stringify({ texto: md, tipo: 'blog' }));
  const p = r.detectores.find((d) => d.id === 'progressao_sinalizada');
  assert.ok(p.aplicavel);
  assert.ok(p.subscore < 0.6, `subscore ${p.subscore}`);
});

// --- Robustez da ponte Node↔Python ---

test('runPython: acentuação intacta em saída grande (fronteira de chunk)', async () => {
  // texto longo com acentos por toda parte força múltiplos chunks de stdout
  const frase = 'A canção do coração não é solução para a aflição. ';
  const r = await runPython('variancia.py', frase.repeat(400));
  assert.ok(!/�/.test(JSON.stringify(r)), 'saída contém U+FFFD (corrupção UTF-8)');
});

test('runPython: binário inexistente dá mensagem amigável', async () => {
  process.env.TEXTO_BR_PYTHON = '/caminho/inexistente-python';
  try {
    await assert.rejects(
      () => runPython('variancia.py', 'Um texto qualquer para o teste.'),
      /não encontrado|Python 3/
    );
  } finally {
    delete process.env.TEXTO_BR_PYTHON;
  }
});
