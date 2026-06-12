import { z } from 'zod';
import { CHECKLISTS } from '../knowledge/phases.js';
import { getSection } from '../content/registry.js';

export function register(server) {
  server.registerTool(
    'texto_br_checklist',
    {
      title: 'Checklist de verificação de fase',
      description:
        'Retorna o checklist de saída de uma fase de humanização: fase 2 (verificação final ' +
        'de superfície), fase 3 (camadas profundas) ou fase 4 (humanização discursiva). ' +
        'Todo item deve estar verificado antes de avançar.',
      inputSchema: {
        fase: z
          .union([z.literal(2), z.literal(3), z.literal(4)])
          .describe('Fase cujo checklist verificar (2, 3 ou 4)'),
      },
    },
    async ({ fase }) => {
      const ref = CHECKLISTS[fase];
      return { content: [{ type: 'text', text: getSection(ref.file, ref.section) }] };
    }
  );
}
