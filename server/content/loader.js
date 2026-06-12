import { readFile } from 'node:fs/promises';
import path from 'node:path';

const FILES = [
  'tipos-de-texto',
  'gramatica-pt-br',
  'humanizacao-algoritmos',
  'camadas-profundas',
  'humanizacao-discursiva',
];

const cache = new Map();

export async function loadAll(referencesDir) {
  for (const name of FILES) {
    const filePath = path.join(referencesDir, `${name}.md`);
    cache.set(name, await readFile(filePath, 'utf8'));
  }
}

export function getFile(name) {
  if (!cache.has(name)) {
    throw new Error(`Reference desconhecida: ${name}. Disponíveis: ${FILES.join(', ')}`);
  }
  return cache.get(name);
}

export function knownFiles() {
  return [...FILES];
}
