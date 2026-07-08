import { z } from 'zod';
import { runPython } from './run-python.js';
import { getSection } from '../content/registry.js';

export function register(server, session) {
  server.registerTool(
    'texto_br_lexico',
    {
      title: 'Análise de perturbação lexical',
      description:
        'Mede a previsibilidade lexical de um rascunho: ocorrências de vocabulário pivot de ' +
        'LLM (verbos, adjetivos, substantivos, conectores, aberturas e fechamentos da seção 10 ' +
        'das references, com alternativas sugeridas), repetições de palavras de conteúdo, ' +
        'diversidade lexical e trigramas repetidos. Alvo: zero ocorrências pivot. As listas são ' +
        'o piso; identifique também palavras previsíveis no contexto do texto. Use no loop ' +
        'quantitativo da Fase 2 junto com texto_br_variancia.',
      inputSchema: {
        texto: z.string().min(1).describe('Rascunho completo a analisar (markdown ou texto puro)'),
      },
    },
    async ({ texto }) => {
      try {
        const secao10 = getSection('humanizacao-algoritmos', 10);
        const resultado = await runPython('lexico.py', JSON.stringify({ texto, secao10 }));
        if (resultado.erro && !resultado.inaplicavel) {
          return { isError: true, content: [{ type: 'text', text: resultado.erro }] };
        }
        if (session) {
          if (resultado.inaplicavel) {
            // Análise inaplicável (texto curto): não há o que medir, não trava o
            // gate. O veredicto vale para este texto curto (hash dele).
            session.registrarLexico(true, texto);
          } else if (!resultado.erro) {
            session.registrarLexico(resultado.atingiu_alvo === true, texto);
          }
        }
        return { content: [{ type: 'text', text: resultado.relatorio }] };
      } catch (err) {
        return { isError: true, content: [{ type: 'text', text: err.message }] };
      }
    }
  );
}
