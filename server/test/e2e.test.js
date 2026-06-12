import { test } from 'node:test';
import assert from 'node:assert/strict';
import os from 'node:os';
import path from 'node:path';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const TEXTO_BOM = `Comecei a meditar num sábado qualquer de 2019, mais por teimosia do que por convicção, e o tédio dos primeiros dias quase me venceu logo de cara. Desisti? Quase. Mas na terceira semana o sono melhorou primeiro, depois veio uma paciência esquisita nas reuniões, dessas que os colegas percebem antes de você mesmo notar qualquer mudança. Não virei outra pessoa. Só parei de correr atrás de um relógio que ninguém me cobrava.`;

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

    // segue até a entrega, que aponta os rascunhos salvos
    await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 4
    const r7 = await client.callTool({ name: 'texto_br_proxima_fase', arguments: {} }); // 5
    assert.ok(r7.content[0].text.includes('# Fase 5'));
    assert.ok(r7.content[0].text.includes('Rascunhos salvos'));

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
