#!/usr/bin/env node
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { loadAll } from './content/loader.js';
import { buildIndexes, validateAll } from './content/registry.js';
import { SessionState } from './session/state.js';
import { createServer } from './server.js';

process.on('uncaughtException', (err) => {
  console.error('[texto-br] erro fatal:', err);
  process.exit(1);
});

process.on('unhandledRejection', (err) => {
  console.error('[texto-br] erro fatal (promise):', err);
  process.exit(1);
});

const referencesDir = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..',
  'references'
);

await loadAll(referencesDir);
buildIndexes();
validateAll();
SessionState.restore();

const server = createServer(SessionState);
await server.connect(new StdioServerTransport());
console.error('[texto-br] servidor MCP iniciado (stdio)');
