import { z } from 'zod';
import { PHASE_GUIDANCE, LOOP_QUANTITATIVO_GUIDANCE, TIPOS_ESTRUTURA_GATE } from '../knowledge/phases.js';
import { composePhaseSections } from '../content/registry.js';

export function register(server, session) {
  server.registerTool(
    'texto_br_proxima_fase',
    {
      title: 'Avançar (ou reposicionar) fase do pipeline',
      description:
        'Avança o pipeline de escrita para a próxima fase e retorna a guidance dela junto com ' +
        'as seções de referência necessárias. Sequência: 1 (redação) → 2 (humanização de ' +
        'superfície) → 3 (humanização profunda) → 4 (humanização discursiva) → 5 (análise ' +
        'macroestrutural) → 6 (entrega). SEMPRE passe em "rascunho" o texto produzido na fase ' +
        'que está concluindo. Use "fase" para voltar/repetir uma fase específica. Sair da Fase 2 ' +
        '(loop quantitativo) exige ambos os alvos; sair da Fase 5 em tipos longos exige o alvo ' +
        'de naturalidade estrutural (ou "forcar": true em ambos os casos).',
      inputSchema: {
        rascunho: z
          .string()
          .optional()
          .describe('Texto completo produzido na fase que está sendo concluída (fica salvo na sessão)'),
        fase: z
          .number()
          .int()
          .min(1)
          .max(6)
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
      // Fase de destino do rascunho: ao reposicionar (fase !== undefined), o
      // texto passado é o do destino (para onde a sessão está indo), não o
      // da fase de origem — senão o fallback de hashGate abaixo (que lê
      // session.rascunhos[session.currentPhase] já reposicionado) nunca
      // encontraria o rascunho que acabou de ser salvo.
      const faseParaSalvarRascunho = fase !== undefined ? fase : session.currentPhase;
      if (rascunho && session.currentPhase !== null) {
        session.salvarRascunho(faseParaSalvarRascunho, rascunho);
      }

      let phase;
      try {
        if (fase !== undefined) {
          phase = session.goTo(fase);
        } else {
          // Veredictos só contam se o hash do texto medido bater com o do
          // rascunho que a sessão conhece nesta fase (achado C3): medir um
          // texto alheio ("isca") não pode destravar o gate de outro. O texto
          // de comparação é o rascunho passado nesta chamada (já salvo acima)
          // ou, na ausência dele, o rascunho salvo da fase atual.
          // FAIL-CLOSED: se a sessão não conhece nenhum texto da fase atual
          // (hashGate null), o gate NÃO abre — não há como confirmar que o
          // veredicto se refere ao rascunho real.
          const textoGate = rascunho ?? session.rascunhos?.[session.currentPhase];
          const hashGate = textoGate ? session.hashTexto(textoGate) : null;
          const casaHash = (hash) => hash !== null && hashGate !== null && hash === hashGate;
          const estadoCampo = (atingido, hash) => {
            if (atingido !== true) return atingido === false ? 'não atingido' : 'não medido';
            if (hashGate === null) return 'medido, mas o rascunho não foi informado (passe "rascunho")';
            if (!casaHash(hash)) return 'medido em texto diferente do rascunho atual';
            return 'ALVO ATINGIDO';
          };
          const varianciaOk = session.varianciaAtingida === true && casaHash(session.varianciaHash);
          const lexicoOk = session.lexicoAtingido === true && casaHash(session.lexicoHash);
          // Gate da Fase 2: com o loop quantitativo ativo, só avança com os
          // dois alvos registrados (texto_br_variancia e texto_br_lexico).
          if (session.currentPhase === 2 && session.variancia && !forcar && !(varianciaOk && lexicoOk)) {
            return {
              isError: true,
              content: [
                {
                  type: 'text',
                  text:
                    'Gate da Fase 2: o loop quantitativo ainda não fechou ' +
                    `(variância sintática: ${estadoCampo(session.varianciaAtingida, session.varianciaHash)}; ` +
                    `perturbação lexical: ${estadoCampo(session.lexicoAtingido, session.lexicoHash)}). ` +
                    'Rode texto_br_variancia e texto_br_lexico com o rascunho atual, reescreva ' +
                    'os pontos apontados até ambos retornarem ALVO ATINGIDO, e tente avançar de ' +
                    'novo. Para avançar mesmo assim (a pedido do usuário), use forcar: true.',
                },
              ],
            };
          }
          // Gate da Fase 5: em tipos longos, só avança com o alvo de naturalidade
          // estrutural atingido (texto_br_estrutura). Advisory nos demais tipos.
          const estruturaOk = session.estruturaAtingida === true && casaHash(session.estruturaHash);
          if (
            session.currentPhase === 5 &&
            TIPOS_ESTRUTURA_GATE.includes(session.tipo) &&
            !forcar &&
            !estruturaOk
          ) {
            // Distingue "nunca medido" (null) de "medido e reprovado" (false):
            // só neste último caso o score real ficou abaixo do alvo, então
            // só aqui faz sentido afirmar "score < 70".
            const estado = estadoCampo(session.estruturaAtingida, session.estruturaHash);
            const detalheAlvo =
              session.estruturaAtingida === false
                ? ` (score < 70 para o tipo "${session.tipo}")`
                : ` para o tipo "${session.tipo}"`;
            return {
              isError: true,
              content: [
                {
                  type: 'text',
                  text:
                    'Gate da Fase 5: a naturalidade estrutural ainda não atingiu o alvo' +
                    `${detalheAlvo}; estado: ${estado}. Rode ` +
                    'texto_br_estrutura com o rascunho atual, aplique o plano de perturbação até ' +
                    '"ALVO ATINGIDO" e tente avançar de novo. Para avançar mesmo assim (a pedido ' +
                    'do usuário), use forcar: true.',
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
      if (phase === 6) {
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
