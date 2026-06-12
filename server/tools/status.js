import { PHASE_GUIDANCE } from '../knowledge/phases.js';

export function register(server, session) {
  server.registerTool(
    'texto_br_status',
    {
      title: 'Estado do pipeline texto-br',
      description:
        'Mostra o estado atual do pipeline de escrita: fase, tipo, briefing e tamanho. ' +
        'Use ao retomar uma conversa para saber de onde continuar.',
      inputSchema: {},
    },
    async () => {
      const status = session.toStatus();
      if (status.faseAtual === null) {
        return {
          content: [
            {
              type: 'text',
              text: 'Nenhuma escrita em andamento. Use texto_br_start para iniciar.',
            },
          ],
        };
      }
      const faseNome = PHASE_GUIDANCE[status.faseAtual]?.name ?? 'desconhecida';
      const variancia = status.variancia ? 'ativado (default)' : 'desativado';
      const veredicto = (v) =>
        v === true ? 'alvo atingido' : v === false ? 'não atingido' : 'não medido';
      const text = [
        `Fase atual: ${status.faseAtual} (${faseNome})`,
        `Tipo: ${status.tipo ?? 'não definido'}`,
        `Briefing: ${status.briefing}`,
        `Tamanho: ${status.tamanho ?? 'medio (default)'}`,
        `Loop quantitativo (variância + léxico): ${variancia}`,
        `Vereditos: variância ${veredicto(status.varianciaAtingida)} | léxico ${veredicto(status.lexicoAtingido)}`,
        `Rascunhos salvos: ${status.rascunhosSalvos.length ? 'fases ' + status.rascunhosSalvos.join(', ') : 'nenhum'}`,
        `Iniciado em: ${status.iniciadoEm}`,
      ].join('\n');
      return { content: [{ type: 'text', text }] };
    }
  );
}
