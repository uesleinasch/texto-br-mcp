import { z } from 'zod';
import { runPython } from './run-python.js';
import { TIPOS_VALIDOS } from '../knowledge/phases.js';

export function register(server, session) {
  server.registerTool(
    'texto_br_estrutura',
    {
      title: 'Análise macroestrutural (naturalidade estrutural)',
      description:
        'Mede sinais macroestruturais de IA num rascunho: simetria de seções, inflação de ' +
        'subtópicos, parágrafo-lição (kicker uniforme), frases de efeito em sequência e ' +
        'progressão sinalizada. Compõe um score 0-100 de naturalidade estrutural (alvo >= 70) ' +
        'e devolve um plano de perturbação priorizado. Use na Fase 5: medir → perturbar a ' +
        'estrutura conforme o plano → medir de novo, até "ALVO ATINGIDO". O tipo calibra a ' +
        'análise e o gate (default: tipo da sessão).',
      inputSchema: {
        texto: z.string().min(1).describe('Rascunho completo a analisar (markdown ou texto puro)'),
        tipo: z.enum(TIPOS_VALIDOS).optional().describe('Tipo de texto; default = tipo da sessão'),
      },
    },
    async ({ texto, tipo }) => {
      try {
        const tipoEfetivo = tipo ?? session?.tipo ?? 'geral';
        const resultado = await runPython('estrutura.py', JSON.stringify({ texto, tipo: tipoEfetivo }));
        if (session) {
          // Análise inaplicável (texto curto demais) não tem o que perturbar: não trava
          // o gate. Erro real (não declarado inaplicável) não libera o gate.
          session.estruturaAtingida = resultado.inaplicavel
            ? true
            : resultado.atingiu_alvo === true;
          session.persist();
        }
        return { content: [{ type: 'text', text: resultado.relatorio }] };
      } catch (err) {
        return { isError: true, content: [{ type: 'text', text: err.message }] };
      }
    }
  );
}
