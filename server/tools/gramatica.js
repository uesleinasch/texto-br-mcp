import { z } from 'zod';
import { getSection, listSections } from '../content/registry.js';

const TEMAS = `1 alfabeto/AO1990, 2 acentuação, 3 hifenização, 4 ortografia, 5 pontuação,
6 classes gramaticais, 7 sintaxe, 8 concordância verbal, 9 concordância nominal,
10 regência verbal, 11 regência nominal, 12 crase, 13 verbo, 14 pronomes,
15 colocação pronominal, 16 os quatro porquês, 17 erros frequentes, 18 particularidades pt-BR`;

export function register(server) {
  server.registerTool(
    'texto_br_gramatica',
    {
      title: 'Consulta gramatical pt-BR (AO1990)',
      description: `Retorna uma seção da referência de gramática do português brasileiro. Seções: ${TEMAS}.`,
      inputSchema: {
        secao: z.coerce
          .number()
          .int()
          .min(1)
          .max(18)
          .describe('Número da seção de gramática (1-18)'),
      },
    },
    async ({ secao }) => {
      const available = listSections('gramatica-pt-br');
      if (!available.includes(String(secao))) {
        return {
          isError: true,
          content: [
            {
              type: 'text',
              text: `Seção ${secao} indisponível. Seções existentes: ${available.join(', ')}.`,
            },
          ],
        };
      }
      return { content: [{ type: 'text', text: getSection('gramatica-pt-br', secao) }] };
    }
  );
}
