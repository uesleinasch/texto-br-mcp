import { z } from 'zod';
import { runPython } from './run-python.js';
import { TIPOS_VALIDOS, TIPOS_ESTRUTURA_GATE, ALVO_ESTRUTURA } from '../knowledge/phases.js';

export function register(server, session) {
  server.registerTool(
    'texto_br_estrutura',
    {
      title: 'Análise macroestrutural (naturalidade estrutural)',
      description:
        'Mede sinais macroestruturais de IA num rascunho: simetria de seções, inflação de ' +
        'subtópicos, parágrafo-lição (kicker uniforme), frases de efeito em sequência e ' +
        `progressão sinalizada. Compõe um score 0-100 de naturalidade estrutural (alvo >= ${ALVO_ESTRUTURA}) ` +
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
        const resultado = await runPython(
          'estrutura.py',
          JSON.stringify({ texto, tipo: tipoEfetivo, gate: TIPOS_ESTRUTURA_GATE, alvo: ALVO_ESTRUTURA })
        );
        if (resultado.erro && !resultado.inaplicavel) {
          return { isError: true, content: [{ type: 'text', text: resultado.erro }] };
        }
        let relatorio = resultado.relatorio;
        if (session) {
          if (tipoEfetivo === session.tipo) {
            // Análise inaplicável (texto curto demais) não tem o que perturbar: não
            // trava o gate. Erro real (não declarado inaplicável) não libera o gate.
            const atingido = resultado.inaplicavel ? true : resultado.atingiu_alvo === true;
            session.registrarEstrutura(atingido, texto);
          } else {
            // Medição com tipo alheio ao da sessão: não conta para o gate da Fase 5.
            relatorio +=
              `\n\n(Nota: esta medição usou o tipo "${tipoEfetivo}", diferente do tipo ` +
              `da sessão ("${session.tipo}"); o resultado não conta para o gate da Fase 5.)`;
          }
        }
        return { content: [{ type: 'text', text: relatorio }] };
      } catch (err) {
        return { isError: true, content: [{ type: 'text', text: err.message }] };
      }
    }
  );
}
