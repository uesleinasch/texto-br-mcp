import { z } from 'zod';
import { PHASE_GUIDANCE, LOOP_QUANTITATIVO_GUIDANCE } from '../knowledge/phases.js';
import { composePhaseSections } from '../content/registry.js';

export function register(server, session) {
  server.registerTool(
    'texto_br_proxima_fase',
    {
      title: 'Avançar (ou reposicionar) fase do pipeline',
      description:
        'Avança o pipeline de escrita para a próxima fase e retorna a guidance dela junto com ' +
        'as seções de referência necessárias. Sequência: 1 (redação) → 2 (humanização de ' +
        'superfície) → 3 (humanização profunda) → 4 (humanização discursiva) → 5 (entrega). ' +
        'SEMPRE passe em "rascunho" o texto produzido na fase que está concluindo. Use "fase" ' +
        'para voltar/repetir uma fase específica. Sair da Fase 2 com o loop quantitativo ativo ' +
        'exige ambos os alvos atingidos (ou "forcar": true).',
      inputSchema: {
        rascunho: z
          .string()
          .optional()
          .describe('Texto completo produzido na fase que está sendo concluída (fica salvo na sessão)'),
        fase: z
          .number()
          .int()
          .min(1)
          .max(5)
          .optional()
          .describe('Reposiciona o pipeline nesta fase (ex.: 2 para refazer a humanização de superfície)'),
        forcar: z
          .boolean()
          .optional()
          .describe('Avança da Fase 2 mesmo sem os alvos do loop quantitativo atingidos'),
        variancia: z
          .boolean()
          .optional()
          .describe(
            'Loop quantitativo da Fase 2 (variância sintática + perturbação lexical). ' +
              'Ativado por default; passe false apenas se o usuário pedir para desativar.'
          ),
      },
    },
    async ({ rascunho, fase, forcar, variancia }) => {
      if (typeof variancia === 'boolean') {
        session.variancia = variancia;
        session.persist();
      }
      if (rascunho && session.currentPhase !== null) {
        session.salvarRascunho(session.currentPhase, rascunho);
      }

      let phase;
      try {
        if (fase !== undefined) {
          phase = session.goTo(fase);
        } else {
          // Gate da Fase 2: com o loop quantitativo ativo, só avança com os
          // dois alvos registrados (texto_br_variancia e texto_br_lexico).
          if (
            session.currentPhase === 2 &&
            session.variancia &&
            !forcar &&
            !(session.varianciaAtingida === true && session.lexicoAtingido === true)
          ) {
            const estado = (v) =>
              v === true ? 'ALVO ATINGIDO' : v === false ? 'não atingido' : 'não medido';
            return {
              isError: true,
              content: [
                {
                  type: 'text',
                  text:
                    'Gate da Fase 2: o loop quantitativo ainda não fechou ' +
                    `(variância sintática: ${estado(session.varianciaAtingida)}; ` +
                    `perturbação lexical: ${estado(session.lexicoAtingido)}). ` +
                    'Rode texto_br_variancia e texto_br_lexico com o rascunho atual, reescreva ' +
                    'os pontos apontados até ambos retornarem ALVO ATINGIDO, e tente avançar de ' +
                    'novo. Para avançar mesmo assim (a pedido do usuário), use forcar: true.',
                },
              ],
            };
          }
          phase = session.advance();
        }
      } catch (err) {
        return {
          isError: true,
          content: [{ type: 'text', text: err.message }],
        };
      }

      const guidance = PHASE_GUIDANCE[phase];
      const sections = composePhaseSections(phase, session.tipo);
      const parts = [
        `# Fase ${phase} — ${guidance.name}`,
        `Tipo ativo: ${session.tipo} | Briefing: ${session.briefing}`,
        guidance.instruction,
      ];

      if (phase === 2 && session.variancia) {
        parts.push(LOOP_QUANTITATIVO_GUIDANCE);
      }
      if (phase === 5) {
        const salvos = Object.keys(session.rascunhos);
        parts.push(
          salvos.length
            ? `Rascunhos salvos das fases: ${salvos.join(', ')}. Se o usuário pedir comparação, recupere com texto_br_rascunho(fase).`
            : 'Nenhum rascunho intermediário foi salvo nesta sessão (passe "rascunho" ao avançar de fase nas próximas escritas).'
        );
      }

      parts.push(sections);
      const text = parts.filter(Boolean).join('\n\n');

      return { content: [{ type: 'text', text }] };
    }
  );
}
