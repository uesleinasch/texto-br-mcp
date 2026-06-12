import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ANALYSIS_DIR = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..',
  'analysis'
);

const TIMEOUT_MS = Number(process.env.TEXTO_BR_PYTHON_TIMEOUT_MS) || 30000;

// Roda um analisador Python de server/analysis/, escrevendo `input` no stdin
// e devolvendo o JSON parseado do stdout.
export function runPython(scriptName, input) {
  return new Promise((resolve, reject) => {
    const proc = spawn('python3', [path.join(ANALYSIS_DIR, scriptName)], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: ANALYSIS_DIR, // garante que imports locais (texto_util) resolvam
    });
    let stdout = '';
    let stderr = '';
    const timer = setTimeout(() => {
      proc.kill('SIGKILL');
      reject(new Error(`Análise excedeu o tempo limite de ${TIMEOUT_MS / 1000}s.`));
    }, TIMEOUT_MS);

    // EPIPE se o Python morrer antes de consumir o stdin: rejeitar em vez de
    // derrubar o servidor com uncaughtException
    proc.stdin.on('error', (err) => {
      clearTimeout(timer);
      reject(err);
    });

    proc.on('error', (err) => {
      clearTimeout(timer);
      reject(
        err.code === 'ENOENT'
          ? new Error('python3 não encontrado no PATH; as análises quantitativas requerem Python 3.')
          : err
      );
    });
    proc.stdout.on('data', (d) => (stdout += d));
    proc.stderr.on('data', (d) => (stderr += d));
    proc.on('close', (code) => {
      clearTimeout(timer);
      if (code !== 0) {
        return reject(new Error(`Analisador falhou (exit ${code}): ${stderr.slice(0, 300)}`));
      }
      try {
        resolve(JSON.parse(stdout));
      } catch {
        reject(new Error(`Saída inválida do analisador: ${stdout.slice(0, 200)}`));
      }
    });

    proc.stdin.write(input, 'utf8');
    proc.stdin.end();
  });
}
