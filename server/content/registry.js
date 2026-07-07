import { getFile, knownFiles } from './loader.js';
import { parseNumberedSections, extractH1Block } from './parser.js';
import {
  PHASE_SECTIONS,
  PHASE_SECTIONS_CONVERSACIONAL,
  TIPOS_CONVERSACIONAIS,
  TIPOS_VALIDOS,
  CHECKLISTS,
} from '../knowledge/phases.js';

// Conhecimento estrutural sobre as references: seções numeradas por arquivo,
// índice slug → seção em tipos-de-texto.md, e validação no startup.

const parsed = new Map(); // file → Map<numero, corpo>
const slugIndex = new Map(); // slug → corpo da seção do tipo

export function buildIndexes() {
  for (const file of knownFiles()) {
    parsed.set(file, parseNumberedSections(getFile(file)));
  }
  for (const [, body] of parsed.get('tipos-de-texto')) {
    const m = body.match(/\*\*ID:\*\*\s*`([^`]+)`/);
    if (m) slugIndex.set(m[1], body);
  }
}

// Valida que os checklists (CHECKLISTS de knowledge/phases.js) apontam para
// seções existentes. Exportada para teste com mapa injetado.
export function validaChecklists(mapa = CHECKLISTS, warn = (m) => console.error(`[texto-br] aviso: ${m}`)) {
  for (const [fase, ref] of Object.entries(mapa)) {
    if (!parsed.get(ref.file)?.has(ref.section)) {
      warn(`checklist da fase ${fase}: seção ${ref.section} não encontrada em ${ref.file}.md`);
    }
  }
}

// Valida que tudo o que o workflow espera existe nos .md. Avisa em stderr e
// segue em frente — degradação graciosa, nunca crash por conteúdo ausente.
export function validateAll() {
  const warn = (msg) => console.error(`[texto-br] aviso: ${msg}`);

  for (const mapa of [PHASE_SECTIONS, PHASE_SECTIONS_CONVERSACIONAL]) {
    for (const phase of Object.values(mapa)) {
      for (const ref of phase) {
        if (ref.section.startsWith('type:') || ref.section.startsWith('h1:')) continue;
        if (!parsed.get(ref.file)?.has(ref.section)) {
          warn(`seção ${ref.section} não encontrada em ${ref.file}.md`);
        }
      }
    }
  }

  for (const slug of TIPOS_VALIDOS) {
    if (!slugIndex.has(slug)) warn(`tipo "${slug}" sem seção em tipos-de-texto.md`);
  }

  validaChecklists(CHECKLISTS, warn);

  for (const mapa of [PHASE_SECTIONS, PHASE_SECTIONS_CONVERSACIONAL]) {
    for (const phase of Object.values(mapa)) {
      for (const ref of phase) {
        if (!ref.section.startsWith('h1:')) continue;
        const heading = ref.section.slice(3);
        if (!extractH1Block(getFile(ref.file), heading)) {
          warn(`bloco h1 "${heading}" não encontrado em ${ref.file}.md`);
        }
      }
    }
  }
}

export function getSection(file, sectionNumber) {
  const body = parsed.get(file)?.get(String(sectionNumber));
  if (body) return body;
  // Fallback gracioso: arquivo inteiro com aviso, em vez de erro.
  return (
    `> Aviso: seção ${sectionNumber} não encontrada em ${file}.md; ` +
    `segue o arquivo completo.\n\n${getFile(file)}`
  );
}

export function getTypeSpec(slug) {
  return slugIndex.get(slug) ?? null;
}

export function getH1Block(file, headingText) {
  return extractH1Block(getFile(file), headingText);
}

export function listSections(file) {
  return [...(parsed.get(file)?.keys() ?? [])];
}

// Resolve as entradas de PHASE_SECTIONS de uma fase em texto concatenado,
// interpolando "type:{slug}" com o tipo ativo e "h1:..." com blocos nível 1.
// Tipos conversacionais usam o mapa enxuto quando a fase tem override.
export function composePhaseSections(phase, slug) {
  const conversacional = slug && TIPOS_CONVERSACIONAIS.includes(slug);
  const refs =
    (conversacional ? PHASE_SECTIONS_CONVERSACIONAL[phase] : undefined) ??
    PHASE_SECTIONS[phase] ??
    [];
  const parts = [];
  for (const ref of refs) {
    if (ref.section === 'type:{slug}') {
      if (!slug) continue;
      const spec = getTypeSpec(slug);
      parts.push(spec ?? `> Aviso: especificação do tipo "${slug}" não encontrada.`);
    } else if (ref.section.startsWith('h1:')) {
      const block = getH1Block(ref.file, ref.section.slice(3));
      if (block) parts.push(block);
    } else {
      parts.push(getSection(ref.file, ref.section));
    }
  }
  return parts.join('\n\n---\n\n');
}
