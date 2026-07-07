import { test } from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const TEXTO_BOM = `Comecei a meditar num sábado qualquer de 2019, mais por teimosia do que por convicção, e o tédio dos primeiros dias quase me venceu logo de cara. Desisti? Quase. Mas na terceira semana o sono melhorou primeiro, depois veio uma paciência esquisita nas reuniões, dessas que os colegas percebem antes de você mesmo notar qualquer mudança. Não virei outra pessoa. Só parei de correr atrás de um relógio que ninguém me cobrava.`;

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

    // com alvos atingidos, o avanço passa
    const r4 = await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} });
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
    // blog: posiciona direto na Fase 5
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'hábitos', tipo: 'blog', variancia: false },
    });
    const j = await client.callTool({ name: 'texto_br_proxima_fase', arguments: { fase: 5 } });
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

    // chat (advisory): posiciona na Fase 5 e avança sem medir
    await client.callTool({
      name: 'texto_br_start',
      arguments: { briefing: 'oi', tipo: 'chat', variancia: false },
    });
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: { fase: 5 } });
    const chatOk = await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} });
    assert.ok(chatOk.content[0].text.includes('# Fase 6'));
  } finally {
    await client.close();
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
  }
});
