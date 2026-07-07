# texto-br MCP

Servidor MCP (stdio) que encapsula o workflow texto-br: escrita profissional em português brasileiro com pipeline de 7 fases (0 coleta, 1 redação, 2 humanização de superfície com loop quantitativo, 3 humanização profunda, 4 humanização discursiva, 5 análise macroestrutural, 6 entrega). O conteúdo de domínio vive em `../references/*.md`; o servidor lê e fatia esses arquivos em runtime, servindo a cada fase apenas as seções necessárias.

## Pré-requisitos

- Node.js >= 18
- Python 3 no PATH (`python3`) — usado pelos analisadores quantitativos
- Opcional: `ANTHROPIC_API_KEY` no ambiente — habilita `texto_br_otimizar` (correção automática de ritmo via Claude API; sem a chave, a tool retorna erro amigável e o fluxo manual segue normal)

## Instalação e registro

```bash
cd server
npm install
./registrar.sh            # registra no Claude Code (escopo user) com o caminho atual
```

O registro usa caminho absoluto: **se o repositório for movido, rode `./registrar.sh` de novo**. Para registrar manualmente:

```bash
claude mcp add --scope user texto-br -- node /caminho/absoluto/para/server/index.js
```

Verificação: `claude mcp list` deve mostrar `texto-br ... ✔ Connected`.

## Tools

| Tool | Função |
|---|---|
| `texto_br_start(briefing, tipo?, tamanho?, variancia?)` | Inicia o pipeline; com tipo definido retorna o material das Fases 0-1 |
| `texto_br_proxima_fase(rascunho?, fase?, forcar?, variancia?)` | Avança (ou reposiciona via `fase`); salva `rascunho`; gate quantitativo na saída da Fase 2 e gate macroestrutural na saída da Fase 5 (tipos longos) |
| `texto_br_score(texto)` | Score de humanidade 0-100 (ritmo + léxico + estrutura micro; alvo ≥ 80; satisfaz o gate da Fase 2) |
| `texto_br_estrutura(texto, tipo?)` | Score de naturalidade estrutural 0-100 (macro: simetria, subtópicos, kicker, bordões, progressão; alvo ≥ 70) + plano de perturbação (Fase 5) |
| `texto_br_otimizar(texto)` | Otimiza contra o score via Claude API: subida de encosta com anti-degradação (requer credencial) |
| `texto_br_variancia(texto)` | Mede ritmo sintático (burstiness σ/μ, alvo ≥ 0.7) |
| `texto_br_lexico(texto)` | Mede previsibilidade lexical (vocabulário pivot da seção 10, repetições, diversidade) |
| `texto_br_tipo(id)` / `texto_br_gramatica(secao)` / `texto_br_checklist(fase)` | Consultas pontuais |
| `texto_br_rascunho(fase)` | Recupera rascunho salvo de uma fase |
| `texto_br_status()` | Fase atual, tipo, vereditos do loop, rascunhos salvos |

## Estrutura

```
server/
├── index.js              # bootstrap: carrega references, valida, restaura sessão, conecta stdio
├── server.js             # McpServer + instructions + registro das tools
├── content/              # loader (cache), parser (fatiamento por heading), registry (índices)
├── knowledge/phases.js   # guidance das fases + mapa fase→seções (toda evolução do workflow é aqui)
├── session/state.js      # estado da sessão, persistido em $TMPDIR/texto-br-session-<hash-do-cwd>.json
├── tools/                # uma tool por arquivo + run-python.js (spawn dos analisadores)
├── analysis/             # variancia.py, lexico.py, score.py, estrutura.py, texto_util.py (Python stdlib)
└── test/                 # node --test
```

## Variáveis de ambiente

| Variável | Efeito |
|---|---|
| `ANTHROPIC_API_KEY` | Habilita `texto_br_otimizar` |
| `TEXTO_BR_PYTHON_TIMEOUT_MS` | Timeout dos analisadores Python (default 30000) |

## Desenvolvimento

```bash
npm test          # testes (conteúdo, analisadores, e2e via client MCP)
node index.js     # roda o servidor manualmente (stdio; logs em stderr)
```

A persistência de sessão fica em `os.tmpdir()/texto-br-session-<hash-do-cwd>.json` (sobrevive a restart do servidor, morre no reboot; o hash do `cwd` evita colisão entre janelas em projetos diferentes — mesma pasta ainda compartilha o arquivo). Use `TEXTO_BR_STATE_FILE` para fixar o caminho. Para editar o conteúdo de domínio (tipos, gramática, listas pivot, matrizes), edite os `.md` em `../references/` — o servidor parseia em runtime e o `validateAll()` avisa em stderr se alguma seção esperada sumir.
