import { test, before } from 'node:test';
import assert from 'node:assert/strict';
import { loadAll, getFile } from '../content/loader.js';
import { extractH2Block } from '../content/parser.js';
import {
  buildIndexes,
  validateAll,
  validaChecklists,
  composePhaseSections,
  getTypeSpec,
  getSection,
  listSections,
} from '../content/registry.js';
import { TIPOS_VALIDOS, PHASE_GUIDANCE, PHASE_SECTIONS, CHECKLISTS } from '../knowledge/phases.js';

before(async () => {
  await loadAll(new URL('../../references/', import.meta.url).pathname);
  buildIndexes();
});

test('validateAll não emite nenhum aviso (seções e tipos íntegros)', () => {
  const avisos = [];
  const original = console.error;
  console.error = (...args) => avisos.push(args.join(' '));
  try {
    validateAll();
  } finally {
    console.error = original;
  }
  assert.deepEqual(avisos, []);
});

test('todos os 12 tipos têm especificação', () => {
  for (const slug of TIPOS_VALIDOS) {
    const spec = getTypeSpec(slug);
    assert.ok(spec, `tipo ${slug} sem seção`);
    assert.ok(spec.includes(`\`${slug}\``), `tipo ${slug} sem marcador de ID`);
  }
});

test('seções numeradas das references estão completas', () => {
  assert.equal(listSections('gramatica-pt-br').length, 18);
  assert.equal(listSections('humanizacao-algoritmos').length, 12);
  assert.equal(listSections('camadas-profundas').length, 8);
  assert.equal(listSections('humanizacao-discursiva').length, 8);
  assert.equal(listSections('tipos-de-texto').length, 12);
  assert.equal(listSections('estrutura-macro').length, 8);
});

test('estrutura-macro: parseia seções e checklist', () => {
  assert.ok(getSection('estrutura-macro', 2).includes('Simetria de seções'));
  assert.ok(getSection('estrutura-macro', 7).includes('Matriz de calibração'));
  const chk = getSection('estrutura-macro', 8);
  assert.ok(chk.includes('[ ]'), 'checklist da Fase 5 sem itens [ ]');
});

test('toda fase tem guidance e payload coerente', () => {
  for (const fase of Object.keys(PHASE_SECTIONS)) {
    assert.ok(PHASE_GUIDANCE[fase]?.instruction, `fase ${fase} sem guidance`);
    const payload = composePhaseSections(Number(fase), 'blog');
    if (PHASE_SECTIONS[fase].length > 0) {
      assert.ok(payload.length > 100, `payload da fase ${fase} suspeito de vazio`);
      assert.ok(!payload.includes('> Aviso:'), `payload da fase ${fase} com fallback de seção ausente`);
    }
  }
});

test('roteamento adaptativo: payload conversacional é menor que o de produção', () => {
  for (const fase of [1, 2, 3, 4, 5]) {
    const producao = composePhaseSections(fase, 'blog');
    const conversacional = composePhaseSections(fase, 'chat');
    assert.ok(
      conversacional.length < producao.length,
      `fase ${fase}: payload de chat (${conversacional.length}) deveria ser menor que o de blog (${producao.length})`
    );
    assert.ok(!conversacional.includes('> Aviso:'), `fase ${fase} conversacional com seção ausente`);
  }
  // fases sem override herdam o mapa cheio (Fase 6 entrega = vazia para todos)
  assert.equal(composePhaseSections(6, 'chat'), composePhaseSections(6, 'blog'));
});

test('validaChecklists avisa quando uma seção de checklist não existe', () => {
  const avisos = [];
  const orig = console.error;
  console.error = (...args) => avisos.push(args.join(' '));
  try {
    validaChecklists({ 99: { file: 'humanizacao-algoritmos', section: '999' } });
  } finally {
    console.error = orig;
  }
  assert.ok(avisos.some((m) => /999/.test(m) && /humanizacao-algoritmos/.test(m)));
});

test('validaChecklists não avisa para os checklists reais', () => {
  const avisos = [];
  const orig = console.error;
  console.error = (...args) => avisos.push(args.join(' '));
  try {
    validaChecklists();
  } finally {
    console.error = orig;
  }
  assert.deepEqual(avisos, []);
});

test('extractH2Block extrai o bloco de "Princípios gerais" sem engolir a próxima seção', () => {
  const bloco = extractH2Block(getFile('tipos-de-texto'), 'Princípios gerais aplicáveis a todos os tipos');
  assert.ok(bloco, 'bloco não encontrado');
  assert.match(bloco, /Sobre formalidade/);
  assert.ok(!bloco.includes('Artigo para Blog'), 'bloco H2 engoliu a seção seguinte');
});

test('extractH2Block retorna null/undefined para título inexistente', () => {
  const bloco = extractH2Block(getFile('tipos-de-texto'), 'Título que não existe em lugar nenhum');
  assert.ok(bloco === null || bloco === undefined);
});

test('a Fase 1 serve os princípios gerais para o tipo geral e para um tipo conversacional', () => {
  assert.match(composePhaseSections(1, 'geral'), /[Pp]rincípios gerais/);
  assert.match(composePhaseSections(1, 'chat'), /[Pp]rincípios gerais/);
});

test('checklists apontam para seções existentes', () => {
  for (const [fase, ref] of Object.entries(CHECKLISTS)) {
    const corpo = getSection(ref.file, ref.section);
    assert.ok(!corpo.startsWith('> Aviso:'), `checklist da fase ${fase} ausente em ${ref.file}`);
    assert.ok(corpo.includes('[ ]'), `checklist da fase ${fase} sem itens [ ]`);
  }
});
