import { z } from 'zod';
import { TIPOS_VALIDOS } from '../knowledge/phases.js';
import { getTypeSpec } from '../content/registry.js';

export function register(server) {
  server.registerTool(
    'texto_br_tipo',
    {
      title: 'Especificação de um tipo de texto',
      description:
        'Retorna a especificação completa de um dos 12 tipos de texto (estrutura, tom, ' +
        'marcadores estilísticos, aberturas, armadilhas). Consulta pontual, fora do fluxo de fases.',
      inputSchema: {
        id: z.enum(TIPOS_VALIDOS).describe('ID do tipo de texto'),
      },
    },
    async ({ id }) => {
      const spec = getTypeSpec(id);
      if (!spec) {
        return {
          isError: true,
          content: [
            { type: 'text', text: `Tipo "${id}" não encontrado em tipos-de-texto.md.` },
          ],
        };
      }
      return { content: [{ type: 'text', text: spec }] };
    }
  );
}
