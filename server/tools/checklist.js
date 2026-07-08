import { z } from 'zod';
import { CHECKLISTS } from '../knowledge/phases.js';
import { getSection } from '../content/registry.js';

export function register(server) {
  server.registerTool(
    'texto_br_checklist',
    {
      title: 'Checklist de verificação de fase',
      description:
        'Retorna o checklist de saída de uma fase: fase 2 (verificação final de superfície), ' +
        'fase 3 (camadas profundas), fase 4 (humanização discursiva) ou fase 5 (naturalidade ' +
        'estrutural). Todo item deve estar verificado antes de avançar.',
      inputSchema: {
        fase: z
          .union([z.literal(2), z.literal(3), z.literal(4), z.literal(5)])
          .describe('Fase cujo checklist verificar (2, 3, 4 ou 5)'),
      },
    },
    async ({ fase }) => {
      const ref = CHECKLISTS[fase];
      const secao = getSection(ref.file, ref.section);
      if (!secao) {
        return {
          isError: true,
          content: [
            {
              type: 'text',
              text: `Checklist não encontrado (${ref.file} §${ref.section}); verifique as references.`,
            },
          ],
        };
      }
      return { content: [{ type: 'text', text: secao }] };
    }
  );
}
