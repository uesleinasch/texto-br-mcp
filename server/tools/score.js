import { z } from 'zod';
import { runPython } from './run-python.js';
import { getSection } from '../content/registry.js';
import { ALVO_SCORE } from '../knowledge/phases.js';

export function register(server, session) {
  server.registerTool(
    'texto_br_score',
    {
      title: 'Score de humanidade (0-100)',
      description:
        'Função objetivo unificada da Fase 2: compõe ritmo sintático (burstiness, sequências, ' +
        'ordem não-canônica), léxico (pivots, diversidade, trigramas) e estrutura (parágrafos, ' +
        'impacto, conectivos) num score 0-100 (probabilidade de texto humano × 100, modelo ' +
        'calibrado no corpus) com contribuição por sinal e diagnósticos. ' +
        'Alvo >= ' + ALVO_SCORE + '; atingir o alvo satisfaz o gate da Fase 2 numa única chamada (substitui ' +
        'chamar texto_br_variancia e texto_br_lexico separadamente).',
      inputSchema: {
        texto: z.string().min(1).describe('Rascunho completo a pontuar (markdown ou texto puro)'),
      },
    },
    async ({ texto }) => {
      try {
        const secao10 = getSection('humanizacao-algoritmos', 10);
        const resultado = await runPython('score.py', JSON.stringify({ texto, secao10 }));
        if (resultado.inaplicavel) {
          // Análise inaplicável (texto curto): não há o que medir, não trava o
          // gate. O veredicto vale para este texto curto (hash dele).
          if (session) {
            session.registrarVariancia(true, texto);
            session.registrarLexico(true, texto);
          }
          return { content: [{ type: 'text', text: resultado.relatorio }] };
        }
        if (resultado.erro) {
          return { isError: true, content: [{ type: 'text', text: resultado.erro }] };
        }
        if (session) {
          session.registrarVariancia(
            resultado.ritmo.atingiu_alvo === true || resultado.atingiu_alvo === true,
            texto
          );
          session.registrarLexico(
            resultado.lexico.atingiu_alvo === true || resultado.atingiu_alvo === true,
            texto
          );
        }
        return { content: [{ type: 'text', text: resultado.relatorio }] };
      } catch (err) {
        return { isError: true, content: [{ type: 'text', text: err.message }] };
      }
    }
  );
}
