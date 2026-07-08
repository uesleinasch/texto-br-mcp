import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

// Sobe um client+transporte MCP apontando para um TEXTO_BR_STATE_FILE fixo.
function conectar(stateFile, nomeCliente) {
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: nomeCliente, version: '1.0.0' });
  return client.connect(transport).then(() => client);
}

const TEXTO_BOM = `Comecei a meditar num sábado qualquer de 2019, mais por teimosia do que por convicção, e o tédio dos primeiros dias quase me venceu logo de cara. Desisti? Quase. Mas na terceira semana o sono melhorou primeiro, depois veio uma paciência esquisita nas reuniões, dessas que os colegas percebem antes de você mesmo notar qualquer mudança. Não virei outra pessoa. Só parei de correr atrás de um relógio que ninguém me cobrava.`;

// Outro texto humano, também bom (score >= 80), usado para provar que medir um
// rascunho diferente não destrava o gate do rascunho real (hash amarrado ao texto).
const OUTRO_TEXTO_BOM = `Aprendi a consertar minha bicicleta sozinho num domingo chuvoso de outubro, mais por falta de dinheiro do que por vontade de aprender coisa nova. A corrente saltou de novo na primeira tentativa. Um desastre só. Só na quarta vez que a marcha engatou sem travar, e aí, quando finalmente a roda girou lisa, entendi que tinha aprendido mais com aquele erro do que em qualquer vídeo que eu tinha visto antes. Não virei mecânico. Só parei de empurrar a bike até a loja toda vez que ela range.`;

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

test('pipeline completo via client MCP: gate, rascunho, voltar fase', async () => {
  const stateFile = path.join(os.tmpdir(), `texto-br-test-${process.pid}.json`);
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: 'teste', version: '1.0.0' });
  await client.connect(transport);

  try {
    // start direto na Fase 1
    const r1 = await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'café', tipo: 'blog', tamanho: 'curto' },
    });
    assert.ok(r1.content[0].text.includes('# Fase 1'));

    // avança para a Fase 2 salvando o rascunho
    const r2 = await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { rascunho: TEXTO_BOM },
    });
    assert.ok(r2.content[0].text.includes('# Fase 2'));

    // gate: sem medições, avanço da Fase 2 é recusado
    const r3 = await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} });
    assert.equal(r3.isError, true);
    assert.ok(r3.content[0].text.includes('Gate da Fase 2'));

    // o score unificado satisfaz o gate numa única chamada
    const rScore = await client.callTool({ name: 'texto_br_score', arguments: { texto: TEXTO_BOM } });
    assert.ok(rScore.content[0].text.includes('ALVO ATINGIDO'));
    const status = await client.callTool({ name: 'texto_br_status', arguments: {} });
    assert.ok(status.content[0].text.includes('variância alvo atingido'));
    assert.ok(status.content[0].text.includes('léxico alvo atingido'));

    // com alvos atingidos, o avanço passa (rascunho = o mesmo texto medido)
    const r4 = await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { rascunho: TEXTO_BOM },
    });
    assert.ok(r4.content[0].text.includes('# Fase 3'));

    // voltar para a Fase 2 via parâmetro fase
    const r5 = await client.callTool({ name: 'texto_br_proxima_fase', arguments: { fase: 2 } });
    assert.ok(r5.content[0].text.includes('# Fase 2'));

    // forcar pula o gate
    const r6 = await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { forcar: true },
    });
    assert.ok(r6.content[0].text.includes('# Fase 3'));

    // Fase 4 -> 5 (análise macroestrutural)
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 4
    const r7 = await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 5
    assert.ok(r7.content[0].text.includes('# Fase 5'));
    assert.ok(r7.content[0].text.includes('macroestrutural'));

    // Fase 5 é gate para blog: forcar avança até a entrega (Fase 6), que aponta os rascunhos
    const r7b = await client.callTool({ name: 'texto_br_proxima_fase', arguments: { forcar: true } });
    assert.ok(r7b.content[0].text.includes('# Fase 6'));
    assert.ok(r7b.content[0].text.includes('Rascunhos salvos'));

    // recupera o rascunho da Fase 1
    const r8 = await client.callTool({ name: 'texto_br_rascunho', arguments: { fase: 1 } });
    assert.equal(r8.content[0].text, TEXTO_BOM);

    // novo start avisa sobre o pipeline abandonado
    const r9 = await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'outro texto', tipo: 'chat' },
    });
    assert.ok(r9.content[0].text.includes('foi abandonado'));
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: gate da Fase 5 — blog bloqueia sem alvo e avança com alvo; chat é advisory', async () => {
  const stateFile = path.join(os.tmpdir(), `texto-br-test-estr-${process.pid}.json`);
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: 'teste-estrutura', version: '1.0.0' });
  await client.connect(transport);

  try {
    // blog: avança até a Fase 5 (goTo só reposiciona para trás; loop
    // quantitativo desligado, então as fases 2-4 não têm gate aqui)
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'hábitos', tipo: 'blog', variancia: false },
    });
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 1 -> 2
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 2 -> 3
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 3 -> 4
    const j = await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 4 -> 5
    assert.ok(j.content[0].text.includes('# Fase 5'));

    // sem medir, o gate bloqueia
    const bloq = await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} });
    assert.equal(bloq.isError, true);
    assert.ok(bloq.content[0].text.includes('Gate da Fase 5'));

    // mede texto encaixado: reprova e segue bloqueado
    const rEstr = await client.callTool({ name: 'texto_br_estrutura', arguments: { texto: ESTR_IA } });
    assert.ok(rEstr.content[0].text.includes('REESCREVER'));
    const bloq2 = await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} });
    assert.equal(bloq2.isError, true);

    // mede texto humano: aprova e avança para a Fase 6
    const rOk = await client.callTool({ name: 'texto_br_estrutura', arguments: { texto: ESTR_HUMANO } });
    assert.ok(rOk.content[0].text.includes('ALVO ATINGIDO'));
    const avanca = await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { rascunho: ESTR_HUMANO },
    });
    assert.ok(avanca.content[0].text.includes('# Fase 6'));

    // checklist da Fase 5 disponível
    const chk = await client.callTool({ name: 'texto_br_checklist', arguments: { fase: 5 } });
    assert.ok(chk.content[0].text.includes('[ ]'));

    // chat (advisory): avança até a Fase 5 e segue sem medir
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'oi', tipo: 'chat', variancia: false },
    });
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 1 -> 2
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 2 -> 3
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 3 -> 4
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 4 -> 5
    const chatOk = await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 5 -> 6
    assert.ok(chatOk.content[0].text.includes('# Fase 6'));
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: gate da Fase 5 diz "não medido" quando nada foi medido', async () => {
  const stateFile = path.join(os.tmpdir(), `texto-br-test-f5-naomedido-${process.pid}.json`);
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: 'teste-f5-naomedido', version: '1.0.0' });
  await client.connect(transport);

  try {
    // blog: avança até a Fase 5 sem nunca chamar texto_br_estrutura
    // (loop quantitativo desligado para não travar nas fases 2-4 aqui)
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'hábitos', tipo: 'blog', variancia: false },
    });
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 1 -> 2
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 2 -> 3
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 3 -> 4
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 4 -> 5

    // estruturaAtingida nunca foi medida (null): o gate deve dizer "não
    // medido", não afirmar "score < 70" como se já tivesse reprovado.
    const r = await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} });
    assert.equal(r.isError, true);
    assert.match(r.content[0].text, /não medido/i);
    assert.doesNotMatch(r.content[0].text, /score < 70/);
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: texto curto não trava o gate da Fase 2 (inaplicável)', async () => {
  const stateFile = path.join(os.tmpdir(), `texto-br-test-inaplicavel-${process.pid}.json`);
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: 'teste-inaplicavel', version: '1.0.0' });
  await client.connect(transport);

  try {
    // sessão tipo chat, loop quantitativo ativo (default)
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'responder um oi', tipo: 'chat' },
    });
    await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { rascunho: 'Oi! Tudo certo por aí?' },
    }); // 1 -> 2

    // mede um texto de 2 sentenças / 5 palavras: análise inaplicável
    const v = await client.callTool({
      name: 'texto_br_variancia',
      arguments: { texto: 'Oi! Tudo certo por aí?' },
    });
    assert.match(v.content[0].text, /não se aplica/i);
    const l = await client.callTool({
      name: 'texto_br_lexico',
      arguments: { texto: 'Oi! Tudo certo por aí?' },
    });
    assert.match(l.content[0].text, /não se aplica/i);

    // o gate deve liberar a saída da Fase 2 sem forçar
    const r = await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { rascunho: 'Oi! Tudo certo por aí?' },
    });
    assert.ok(!r.isError, r.content[0].text);
    assert.ok(r.content[0].text.includes('# Fase 3'));
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: 3+ sentenças mas < 30 palavras não trava o gate via tools separadas (achado Important)', async () => {
  // Caso-limite do achado: 4 sentenças (>= 3, então o antigo corte de
  // variância não pegava) mas só 8 palavras (< 30). Antes da correção,
  // texto_br_variancia analisava normalmente (burstiness baixíssimo,
  // atingiu_alvo: false) enquanto texto_br_lexico já marcava inaplicavel,
  // divergindo entre os dois caminhos oficiais de medição da Fase 2 e
  // travando o gate para sempre pelo caminho das tools separadas.
  const TEXTO_CURTO = 'Oi. Tudo bem? Como você está? Precisamos conversar.';
  const stateFile = path.join(os.tmpdir(), `texto-br-test-inaplicavel-variancia-${process.pid}.json`);
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: 'teste-inaplicavel-variancia', version: '1.0.0' });
  await client.connect(transport);

  try {
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'responder um oi', tipo: 'chat' },
    });
    await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { rascunho: TEXTO_CURTO },
    }); // 1 -> 2

    // texto_br_variancia e texto_br_lexico chamados separadamente (não via
    // texto_br_score): os dois precisam concordar que o texto é inaplicável.
    const v = await client.callTool({
      name: 'texto_br_variancia',
      arguments: { texto: TEXTO_CURTO },
    });
    assert.match(v.content[0].text, /não se aplica/i);
    const l = await client.callTool({
      name: 'texto_br_lexico',
      arguments: { texto: TEXTO_CURTO },
    });
    assert.match(l.content[0].text, /não se aplica/i);

    // o gate deve liberar a saída da Fase 2 sem forçar
    const r = await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { rascunho: TEXTO_CURTO },
    });
    assert.ok(!r.isError, r.content[0].text);
    assert.ok(r.content[0].text.includes('# Fase 3'));
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: gate da Fase 2 ignora medição de texto alheio (hash)', async () => {
  const stateFile = path.join(os.tmpdir(), `texto-br-test-hash-${process.pid}.json`);
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: 'teste-hash', version: '1.0.0' });
  await client.connect(transport);

  try {
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'artigo sobre café', tipo: 'blog' },
    });
    await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { rascunho: TEXTO_BOM },
    }); // 1 -> 2

    // mede OUTRO texto (também bom) — não pode destravar o gate do rascunho real
    await client.callTool({ name: 'texto_br_score', arguments: { texto: OUTRO_TEXTO_BOM } });

    const r = await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { rascunho: TEXTO_BOM },
    });
    assert.equal(r.isError, true, 'gate deveria bloquear: o rascunho nunca foi medido');
    assert.match(r.content[0].text, /não medido|texto diferente/i);
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: proxima_fase não pula fases para frente', async () => {
  const stateFile = path.join(os.tmpdir(), `texto-br-test-nofwd-${process.pid}.json`);
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: 'teste-nofwd', version: '1.0.0' });
  await client.connect(transport);

  try {
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'artigo', tipo: 'blog' },
    });
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: { rascunho: 'x' } }); // 1 -> 2
    const r = await client.callTool({ name: 'texto_br_proxima_fase', arguments: { fase: 6 } });
    assert.equal(r.isError, true);
    assert.match(r.content[0].text, /para trás|fase futura|avançar/i);
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: voltar para a Fase 2 zera os vereditos', async () => {
  const stateFile = path.join(os.tmpdir(), `texto-br-test-zera-${process.pid}.json`);
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: 'teste-zera', version: '1.0.0' });
  await client.connect(transport);

  try {
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'artigo', tipo: 'blog' },
    });
    const rascunho = TEXTO_BOM;
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: { rascunho } }); // 1 -> 2
    await client.callTool({ name: 'texto_br_score', arguments: { texto: rascunho } }); // atinge alvos
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: { rascunho } }); // 2 -> 3
    await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { fase: 2, rascunho },
    }); // volta
    const r = await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { rascunho: 'texto novo reescrito' },
    });
    assert.equal(r.isError, true, 'gate deveria exigir nova medição após voltar');
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: gate fail-closed — medir isca e avançar SEM rascunho não abre o gate', async () => {
  const stateFile = path.join(os.tmpdir(), `texto-br-test-failclosed-${process.pid}.json`);
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: 'teste-failclosed', version: '1.0.0' });
  await client.connect(transport);

  try {
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'artigo sobre café', tipo: 'blog' },
    });
    // avança para a Fase 2 salvando o rascunho na Fase 1 (rascunhos[2] fica vazio)
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: { rascunho: TEXTO_BOM } });

    // seta os flags medindo um texto isca (bom, mas não é o rascunho real)
    await client.callTool({ name: 'texto_br_score', arguments: { texto: OUTRO_TEXTO_BOM } });

    // avança SEM rascunho e sem ter salvo o rascunho real medido na fase atual:
    // fail-closed, o gate não pode abrir
    const r = await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} });
    assert.equal(r.isError, true, 'gate não pode abrir sem rascunho conhecido');
    assert.ok(r.content[0].text.includes('Gate da Fase 2'));
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: caminho feliz — medir o rascunho real e avançar usando o salvo abre o gate', async () => {
  const stateFile = path.join(os.tmpdir(), `texto-br-test-salvo-${process.pid}.json`);
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: 'teste-salvo', version: '1.0.0' });
  await client.connect(transport);

  try {
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'artigo sobre café', tipo: 'blog' },
    });
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: { rascunho: TEXTO_BOM } }); // 1 -> 2
    // uma tentativa de avanço passando o rascunho real salva rascunhos[2] mesmo bloqueando
    const bloq = await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { rascunho: TEXTO_BOM },
    });
    assert.equal(bloq.isError, true); // ainda não medido

    // mede o rascunho real
    await client.callTool({ name: 'texto_br_score', arguments: { texto: TEXTO_BOM } });

    // avança SEM reenviar o rascunho: a sessão usa o rascunho salvo da fase atual
    const r = await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} });
    assert.ok(!r.isError, r.content[0].text);
    assert.ok(r.content[0].text.includes('# Fase 3'));
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: sessão sobrevive a restart do servidor e restore valida o shape do arquivo', async () => {
  const stateFile = path.join(os.tmpdir(), `texto-br-test-restart-${process.pid}.json`);
  try {
    // primeira "janela": inicia a sessão e encerra o transporte (simula restart)
    const client1 = await conectar(stateFile, 'teste-restart-1');
    try {
      await client1.callTool({
        name: 'texto_br_start',
        arguments: { briefing: 'teste restart', tipo: 'blog' },
      });
    } finally {
      await client1.close();
    }

    // segunda "janela": mesmo TEXTO_BR_STATE_FILE, deve restaurar fase/tipo/vereditos
    const client2 = await conectar(stateFile, 'teste-restart-2');
    try {
      const st = await client2.callTool({ name: 'texto_br_status', arguments: {} });
      assert.match(st.content[0].text, /blog/);
      assert.match(st.content[0].text, /estrutural/i); // estruturaAtingida agora aparece no status
    } finally {
      await client2.close();
    }

    // lixo no state file: restore precisa descartar sem crashar o servidor
    fs.writeFileSync(stateFile, '{"rascunhos": null, "currentPhase": "x"}');
    const client3 = await conectar(stateFile, 'teste-restart-3');
    try {
      const st3 = await client3.callTool({ name: 'texto_br_status', arguments: {} });
      assert.match(st3.content[0].text, /[Nn]enhuma escrita em andamento/);
    } finally {
      await client3.close();
    }
  } finally {
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: persist() limpa o state file assim que o pipeline chega à Fase 6', async () => {
  const stateFile = path.join(os.tmpdir(), `texto-br-test-limpa-fase6-${process.pid}.json`);
  try {
    const client = await conectar(stateFile, 'teste-limpa-fase6');
    try {
      await client.callTool({
        name: 'texto_br_start',
        arguments: { briefing: 'artigo', tipo: 'blog', variancia: false },
      });
      await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 1 -> 2
      await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 2 -> 3
      await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 3 -> 4
      await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 4 -> 5
      const r = await client.callTool({ name: 'texto_br_proxima_fase', arguments: { forcar: true } }); // 5 -> 6
      assert.ok(r.content[0].text.includes('# Fase 6'));
      // sem sessão fantasma: o arquivo não deve existir mais no disco
      assert.equal(fs.existsSync(stateFile), false);
    } finally {
      await client.close();
    }
  } finally {
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: restore descarta state file com "rascunhos" como array (shape inválido)', async () => {
  // {"rascunhos": []} tem typeof 'object' e não é null, então passava na
  // validação antiga de restore() como se fosse um dicionário fase -> texto
  // válido. currentPhase aqui é válido de propósito, para isolar que é a
  // forma de "rascunhos" (array em vez de objeto) que precisa invalidar o
  // shape inteiro.
  const stateFile = path.join(os.tmpdir(), `texto-br-test-rascunhos-array-${process.pid}.json`);
  try {
    fs.writeFileSync(stateFile, JSON.stringify({ currentPhase: 2, tipo: 'blog', rascunhos: [] }));
    const client = await conectar(stateFile, 'teste-rascunhos-array');
    try {
      const st = await client.callTool({ name: 'texto_br_status', arguments: {} });
      assert.match(st.content[0].text, /[Nn]enhuma escrita em andamento/);
    } finally {
      await client.close();
    }
  } finally {
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: reposicionar (goTo) salva o rascunho sob a fase de destino, não a de origem', async () => {
  const stateFile = path.join(os.tmpdir(), `texto-br-test-goto-destino-${process.pid}.json`);
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: 'teste-goto-destino', version: '1.0.0' });
  await client.connect(transport);

  try {
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'hábitos', tipo: 'blog', variancia: false },
    });
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: { rascunho: 'R1' } }); // 1 -> 2
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: { rascunho: 'R2' } }); // 2 -> 3 (rascunhos[2] = 'R2')
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: { rascunho: 'R3' } }); // 3 -> 4
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: { rascunho: 'R4' } }); // 4 -> 5 (rascunhos[4] = 'R4', rascunhos[5] nunca escrito)

    // reposiciona da Fase 5 (origem) para a Fase 2 (destino) passando um novo
    // rascunho: precisa ser salvo sob a fase de DESTINO, sobrescrevendo 'R2'.
    const rGoTo = await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { fase: 2, rascunho: 'RASCUNHO_REPOSICIONADO' },
    });
    assert.ok(rGoTo.content[0].text.includes('# Fase 2'));

    const rascunhoFase2 = await client.callTool({ name: 'texto_br_rascunho', arguments: { fase: 2 } });
    assert.equal(rascunhoFase2.content[0].text, 'RASCUNHO_REPOSICIONADO');

    // a fase de origem (5) não pode ganhar esse rascunho por engano
    const rascunhoFase5 = await client.callTool({ name: 'texto_br_rascunho', arguments: { fase: 5 } });
    assert.notEqual(rascunhoFase5.content[0].text, 'RASCUNHO_REPOSICIONADO');
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: reposicionamento inválido para a frente não suja o slot de destino (Minor E2-T6)', async () => {
  // goTo só aceita ir para trás; pedir uma fase à frente da atual lança. O
  // rascunho passado nessa tentativa não pode ser gravado em rascunhos[fase]
  // antes de goTo validar — senão o slot da fase de destino fica sujo mesmo
  // com a chamada terminando em erro (fail-closed, mas não deveria escrever).
  const stateFile = path.join(os.tmpdir(), `texto-br-test-goto-invalido-${process.pid}.json`);
  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile },
  });
  const client = new Client({ name: 'teste-goto-invalido', version: '1.0.0' });
  await client.connect(transport);

  try {
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'hábitos', tipo: 'blog', variancia: false },
    });
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: { rascunho: 'R1' } }); // 1 -> 2

    // da Fase 2, tenta reposicionar para a Fase 4 (à frente): inválido.
    const rInvalido = await client.callTool({
      name: 'texto_br_proxima_fase',
      arguments: { fase: 4, rascunho: 'TEXTO_ISCA' },
    });
    assert.equal(rInvalido.isError, true);
    assert.match(rInvalido.content[0].text, /apenas para trás/);

    // o slot de destino (4) não pode ter sido gravado pela tentativa inválida
    const rascunhoFase4 = await client.callTool({ name: 'texto_br_rascunho', arguments: { fase: 4 } });
    assert.equal(rascunhoFase4.isError, true);
    assert.doesNotMatch(rascunhoFase4.content[0].text, /TEXTO_ISCA/);
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
  }
});

test('e2e: texto_br_lexico retorna isError quando a análise dá erro real (não inaplicável)', async () => {
  // Stub de "python3" que ignora o texto de entrada e sempre devolve um erro
  // real (sem "inaplicavel"), simulando a seção 10 não carregada/parseável.
  // Exercita a camada do TOOL (isError), não só o script Python (já coberto
  // em analysis.test.js).
  const stateFile = path.join(os.tmpdir(), `texto-br-test-lexico-erro-${process.pid}.json`);
  const stubDir = fs.mkdtempSync(path.join(os.tmpdir(), 'texto-br-lexico-stub-'));
  const stubPath = path.join(stubDir, 'python-stub.js');
  fs.writeFileSync(
    stubPath,
    [
      '#!/usr/bin/env node',
      'process.stdin.resume();',
      "process.stdin.on('end', () => {",
      "  process.stdout.write(JSON.stringify({ erro: 'Tabelas de vocabulário pivot indisponíveis (stub de teste).' }));",
      '});',
      '',
    ].join('\n'),
    { mode: 0o755 }
  );

  const transport = new StdioClientTransport({
    command: 'node',
    args: [new URL('../index.js', import.meta.url).pathname],
    env: { PATH: process.env.PATH, TEXTO_BR_STATE_FILE: stateFile, TEXTO_BR_PYTHON: stubPath },
  });
  const client = new Client({ name: 'teste-lexico-erro', version: '1.0.0' });
  await client.connect(transport);

  try {
    const r = await client.callTool({
      name: 'texto_br_lexico',
      arguments: { texto: TEXTO_BOM },
    });
    assert.equal(r.isError, true);
    assert.match(r.content[0].text, /Tabelas de vocabulário pivot/);
  } finally {
    await client.close();
    fs.rmSync(stateFile, { force: true });
    fs.rmSync(stubDir, { recursive: true, force: true });
  }
});
