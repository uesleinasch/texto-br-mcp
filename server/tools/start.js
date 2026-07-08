import { z } from 'zod';
import {
  PHASE_GUIDANCE,
  REGRAS_ABSOLUTAS,
  TIPOS_VALIDOS,
  TAMANHOS,
} from '../knowledge/phases.js';
import { composePhaseSections } from '../content/registry.js';

export function register(server, session) {
  server.registerTool(
    'texto_br_start',
    {
      title: 'Iniciar escrita texto-br',
      description:
        'Inicia (ou reinicia) o pipeline de escrita pt-BR. Com tipo definido, retorna o material ' +
        'das Fases 0-1 (especificação do tipo, gramática essencial, regras absolutas). Sem tipo, ' +
        'retorna o guia de decisão rápida; chame novamente quando o tipo estiver definido.',
      inputSchema: {
        briefing: z.string().describe('Tema/briefing do texto a escrever'),
        tipo: z
          .enum(TIPOS_VALIDOS)
          .optional()
          .describe('ID do tipo de texto, se já conhecido'),
        tamanho: z
          .enum(Object.keys(TAMANHOS))
          .optional()
          .describe('Tamanho aproximado desejado'),
        variancia: z
          .boolean()
          .optional()
          .describe(
            'Loop quantitativo da Fase 2 (injeção de variância sintática + perturbação ' +
              'lexical controlada). Ativado por default; passe false apenas se o usuário ' +
              'pedir para desativar.'
          ),
      },
    },
    async ({ briefing, tipo, tamanho, variancia }) => {
      try {
        const anterior =
          session.currentPhase !== null
            ? `Atenção: o pipeline anterior (Fase ${session.currentPhase}, tipo ${session.tipo ?? 'indefinido'}, briefing "${session.briefing}") foi abandonado ao iniciar esta nova escrita.`
            : null;

        let text;
        if (!tipo) {
          const fase0 = PHASE_GUIDANCE[0];
          text = [
            anterior,
            `# Fase 0 — ${fase0.name}`,
            fase0.instruction,
            composePhaseSections(0, null),
          ]
            .filter(Boolean)
            .join('\n\n');
        } else {
          const fase1 = PHASE_GUIDANCE[1];
          const varianciaAtiva = variancia !== false;
          const avisoVariancia = `Loop quantitativo da Fase 2 (variância sintática + perturbação lexical): ${
            varianciaAtiva ? 'ATIVADO (default)' : 'desativado a pedido do usuário'
          }.`;
          text = [
            anterior,
            `# Fase 1 — ${fase1.name}`,
            `Briefing: ${briefing}`,
            `Tipo: ${tipo} | Tamanho: ${tamanho ? `${tamanho} (${TAMANHOS[tamanho]})` : 'medio (default)'}`,
            avisoVariancia,
            fase1.instruction,
            REGRAS_ABSOLUTAS,
            composePhaseSections(1, tipo),
          ]
            .filter(Boolean)
            .join('\n\n');
        }
        // Só muta a sessão depois que a composição deu certo (em ambas as
        // branches): se composePhaseSections lançasse antes disso, a sessão
        // anterior (se houver) permanece intacta em vez de ser sobrescrita
        // por uma chamada que terminou em erro.
        session.start(briefing, tipo, tamanho, variancia);
        return { content: [{ type: 'text', text }] };
      } catch (err) {
        return { isError: true, content: [{ type: 'text', text: err.message }] };
      }
    }
  );
}
