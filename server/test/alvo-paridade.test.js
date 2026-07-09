import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { ALVO_SCORE } from '../knowledge/phases.js';

const ANALYSIS = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'analysis');

test('ALVO_SCORE (JS) é idêntico a score.ALVO (Python) — fonte única de verdade', () => {
  const r = spawnSync('python3', ['-c', 'import score; print(score.ALVO)'], {
    cwd: ANALYSIS,
    encoding: 'utf8',
  });
  assert.equal(r.status, 0, r.stderr);
  assert.equal(ALVO_SCORE, parseFloat(r.stdout.trim()));
});
