import { z } from 'zod';
import { runPython } from './run-python.js';

export function register(server, session) {
  server.registerTool(
    'texto_br_variancia',
    {
      title: 'Análise de variância sintática',
      description:
        'Mede o ritmo sintático de um rascunho: burstiness (sigma/mu, alvo >= 0.7), ' +
        'sentenças candidatas a quebra/fusão, sequências uniformes, inícios repetidos e ' +
        'uniformidade de parágrafos. Retorna diagnóstico para reescrita cirúrgica. ' +
        'Use no loop quantitativo da Fase 2: medir → reescrever os pontos apontados → ' +
        'medir de novo, até "ALVO ATINGIDO".',
      inputSchema: {
        texto: z.string().min(1).describe('Rascunho completo a analisar (markdown ou texto puro)'),
      },
    },
    async ({ texto }) => {
      try {
        const resultado = await runPython('variancia.py', texto);
        if (session) {
          if (resultado.inaplicavel) {
            // Análise inaplicável (texto curto): não há o que medir, não trava o
            // gate. O veredicto vale para este texto curto (hash dele).
            session.registrarVariancia(true, texto);
          } else if (!resultado.erro) {
            session.registrarVariancia(resultado.atingiu_alvo === true, texto);
          }
        }
        return { content: [{ type: 'text', text: resultado.relatorio }] };
      } catch (err) {
        return { isError: true, content: [{ type: 'text', text: err.message }] };
      }
    }
  );
}
