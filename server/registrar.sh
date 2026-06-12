#!/usr/bin/env bash
# Registra (ou re-registra) o servidor texto-br no Claude Code com o caminho atual.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

claude mcp remove --scope user texto-br 2>/dev/null || true
claude mcp add --scope user texto-br -- node "$DIR/index.js"
echo "Registrado: texto-br -> $DIR/index.js"
claude mcp list | grep texto-br || true
