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
    const bin = process.env.TEXTO_BR_PYTHON || 'python3';
    const proc = spawn(bin, [path.join(ANALYSIS_DIR, scriptName)], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: ANALYSIS_DIR, // garante que imports locais (texto_util) resolvam
      env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    });
    proc.stdout.setEncoding('utf8');
    proc.stderr.setEncoding('utf8');
    let stdout = '';
    let stderr = '';
    let stdinFalhou = null;
    const timer = setTimeout(() => {
      proc.kill('SIGKILL');
      reject(new Error(`Análise excedeu o tempo limite de ${TIMEOUT_MS / 1000}s.`));
    }, TIMEOUT_MS);

    // EPIPE se o Python morrer antes de consumir o stdin: registrar e deixar
    // o handler de close reportar com o stderr real (traceback), que é útil —
    // rejeitar aqui esconderia a causa.
    proc.stdin.on('error', (err) => {
      stdinFalhou = err;
    });

    proc.on('error', (err) => {
      clearTimeout(timer);
      reject(
        err.code === 'ENOENT'
          ? new Error(
              `${bin} não encontrado no PATH; as análises quantitativas requerem Python 3 ` +
                '(configure TEXTO_BR_PYTHON se o binário tiver outro nome).'
            )
          : err
      );
    });
    proc.stdout.on('data', (d) => (stdout += d));
    proc.stderr.on('data', (d) => (stderr += d));
    proc.on('close', (code) => {
      clearTimeout(timer);
      if (code !== 0) {
        const detalhe = stderr.slice(0, 300) || stdinFalhou?.message || '';
        return reject(new Error(`Analisador falhou (exit ${code}): ${detalhe}`));
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
