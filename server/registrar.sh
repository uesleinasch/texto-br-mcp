#!/usr/bin/env bash
# Registra (ou re-registra) o servidor texto-br no Claude Code com o caminho atual.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v claude >/dev/null 2>&1 || { echo "erro: CLI 'claude' não encontrado no PATH." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || echo "aviso: python3 não encontrado; as análises quantitativas vão falhar em runtime." >&2
[ -d "$DIR/node_modules" ] || { echo "erro: dependências ausentes; rode 'npm install' em $DIR primeiro." >&2; exit 1; }

claude mcp remove --scope user texto-br 2>/dev/null || true
claude mcp add --scope user texto-br -- node "$DIR/index.js"
echo "Registrado: texto-br -> $DIR/index.js"
claude mcp list | grep texto-br || true
