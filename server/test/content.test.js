import { test, before } from 'node:test';
import assert from 'node:assert/strict';
import { loadAll } from '../content/loader.js';
import {
  buildIndexes,
  validateAll,
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
  for (const fase of [1, 2, 3, 4]) {
    const producao = composePhaseSections(fase, 'blog');
    const conversacional = composePhaseSections(fase, 'chat');
    assert.ok(
      conversacional.length < producao.length,
      `fase ${fase}: payload de chat (${conversacional.length}) deveria ser menor que o de blog (${producao.length})`
    );
    assert.ok(!conversacional.includes('> Aviso:'), `fase ${fase} conversacional com seção ausente`);
  }
  // fases sem override herdam o mapa cheio
  assert.equal(composePhaseSections(5, 'chat'), composePhaseSections(5, 'blog'));
});

test('checklists apontam para seções existentes', () => {
  for (const [fase, ref] of Object.entries(CHECKLISTS)) {
    const corpo = getSection(ref.file, ref.section);
    assert.ok(!corpo.startsWith('> Aviso:'), `checklist da fase ${fase} ausente em ${ref.file}`);
    assert.ok(corpo.includes('[ ]'), `checklist da fase ${fase} sem itens [ ]`);
  }
});
