import { readFileSync, writeFileSync, rmSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

// Estado da sessão com persistência mínima em arquivo temporário: se o
// processo MCP reiniciar no meio de um pipeline, a sessão (metadados +
// rascunhos) é restaurada no startup. O arquivo vive em tmpdir e morre no
// reboot, o que é suficiente para o caso de uso (crash/restart do servidor).

const STATE_FILE =
  process.env.TEXTO_BR_STATE_FILE || path.join(os.tmpdir(), 'texto-br-session.json');

const CAMPOS = [
  'currentPhase',
  'tipo',
  'briefing',
  'tamanho',
  'variancia',
  'startedAt',
  'rascunhos',
  'varianciaAtingida',
  'lexicoAtingido',
];

export const SessionState = {
  currentPhase: null, // null = nenhuma escrita em andamento; 0-5 durante o pipeline
  tipo: null,
  briefing: null,
  tamanho: null,
  variancia: true, // loop quantitativo da Fase 2; false apenas se o usuário pedir
  startedAt: null,
  rascunhos: {}, // fase concluída -> texto salvo ao avançar
  varianciaAtingida: null, // último veredicto de texto_br_variancia(_aplicar)
  lexicoAtingido: null, // último veredicto de texto_br_lexico

  start(briefing, tipo, tamanho, variancia) {
    this.briefing = briefing;
    this.tipo = tipo ?? null;
    this.tamanho = tamanho ?? null;
    this.variancia = typeof variancia === 'boolean' ? variancia : true;
    this.currentPhase = tipo ? 1 : 0;
    this.startedAt = new Date().toISOString();
    this.rascunhos = {};
    this.varianciaAtingida = null;
    this.lexicoAtingido = null;
    this.persist();
  },

  advance() {
    if (this.currentPhase === null) {
      throw new Error('Nenhuma sessão de escrita ativa. Chame texto_br_start primeiro.');
    }
    if (this.currentPhase === 0) {
      throw new Error(
        'Tipo de texto ainda não definido. Chame texto_br_start novamente com o tipo.'
      );
    }
    if (this.currentPhase >= 5) {
      throw new Error('O pipeline já chegou à Fase 5 (entrega). Inicie outra escrita com texto_br_start.');
    }
    this.currentPhase += 1;
    this.persist();
    return this.currentPhase;
  },

  // Reposicionamento explícito (voltar/repetir fase). Válido para 1-5 com tipo definido.
  goTo(fase) {
    if (this.currentPhase === null) {
      throw new Error('Nenhuma sessão de escrita ativa. Chame texto_br_start primeiro.');
    }
    if (!this.tipo) {
      throw new Error('Tipo de texto ainda não definido. Chame texto_br_start novamente com o tipo.');
    }
    if (!Number.isInteger(fase) || fase < 1 || fase > 5) {
      throw new Error('Fase inválida: use um inteiro de 1 a 5.');
    }
    this.currentPhase = fase;
    this.persist();
    return this.currentPhase;
  },

  salvarRascunho(fase, texto) {
    this.rascunhos[fase] = texto;
    this.persist();
  },

  toStatus() {
    return {
      faseAtual: this.currentPhase,
      tipo: this.tipo,
      briefing: this.briefing,
      tamanho: this.tamanho,
      variancia: this.variancia,
      iniciadoEm: this.startedAt,
      rascunhosSalvos: Object.keys(this.rascunhos),
      varianciaAtingida: this.varianciaAtingida,
      lexicoAtingido: this.lexicoAtingido,
    };
  },

  persist() {
    try {
      const dados = Object.fromEntries(CAMPOS.map((c) => [c, this[c]]));
      writeFileSync(STATE_FILE, JSON.stringify(dados), 'utf8');
    } catch (err) {
      console.error('[texto-br] aviso: falha ao persistir sessão:', err.message);
    }
  },

  restore() {
    try {
      const dados = JSON.parse(readFileSync(STATE_FILE, 'utf8'));
      for (const campo of CAMPOS) {
        if (campo in dados) this[campo] = dados[campo];
      }
      if (this.currentPhase !== null) {
        console.error(
          `[texto-br] sessão anterior restaurada (fase ${this.currentPhase}, tipo ${this.tipo})`
        );
      }
    } catch {
      // sem arquivo ou ilegível: começa limpo
    }
  },

  clearPersisted() {
    try {
      rmSync(STATE_FILE, { force: true });
    } catch {
      // best-effort
    }
  },
};
