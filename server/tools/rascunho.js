import { z } from 'zod';

export function register(server, session) {
  server.registerTool(
    'texto_br_rascunho',
    {
      title: 'Recuperar rascunho salvo',
      description:
        'Retorna o rascunho salvo ao concluir uma fase (via parâmetro "rascunho" de ' +
        'texto_br_proxima_fase). Útil na Fase 5 quando o usuário pede para comparar o texto ' +
        'final com o rascunho original da Fase 1.',
      inputSchema: {
        fase: z
          .number()
          .int()
          .min(1)
          .max(5)
          .describe('Fase cujo rascunho recuperar (1 = redação original)'),
      },
    },
    async ({ fase }) => {
      const texto = session.rascunhos?.[fase];
      if (!texto) {
        const salvos = Object.keys(session.rascunhos ?? {});
        return {
          isError: true,
          content: [
            {
              type: 'text',
              text: salvos.length
                ? `Nenhum rascunho salvo para a fase ${fase}. Fases com rascunho: ${salvos.join(', ')}.`
                : 'Nenhum rascunho salvo nesta sessão.',
            },
          ],
        };
      }
      return { content: [{ type: 'text', text: texto }] };
    }
  );
}
