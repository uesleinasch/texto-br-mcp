import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { register as registerStart } from './tools/start.js';
import { register as registerProximaFase } from './tools/proxima-fase.js';
import { register as registerTipo } from './tools/tipo.js';
import { register as registerGramatica } from './tools/gramatica.js';
import { register as registerChecklist } from './tools/checklist.js';
import { register as registerStatus } from './tools/status.js';
import { register as registerVariancia } from './tools/variancia.js';
import { register as registerLexico } from './tools/lexico.js';
import { register as registerEstrutura } from './tools/estrutura.js';
import { register as registerScore } from './tools/score.js';
import { register as registerOtimizar } from './tools/otimizar.js';
import { register as registerRascunho } from './tools/rascunho.js';
import { ALVO_SCORE } from './knowledge/phases.js';

// As regras citadas abaixo são um resumo; a lista autoritativa, injetada na
// Fase 1, é REGRAS_ABSOLUTAS em knowledge/phases.js — mantenha as duas em sincronia.
const INSTRUCTIONS = `Este servidor fornece o workflow "texto-br": escrita profissional em português brasileiro com pipeline de 7 fases (0 coleta de contexto, 1 redação, 2 humanização de superfície, 3 humanização profunda, 4 humanização discursiva, 5 análise macroestrutural, 6 entrega), calibrado para produzir texto gramaticalmente impecável (AO1990) e indistinguível de escrita humana por detectores de IA.

SEMPRE que o usuário pedir para escrever, redigir, criar, produzir, rascunhar ou humanizar texto em pt-BR (artigos, e-mails, textos corporativos, capítulos, roteiros de podcast/vídeo, comentários em blog ou Jira, respostas de chat), use este workflow:

1. Chame texto_br_start(briefing, tipo?, tamanho?). Com o tipo definido, ele retorna o material das Fases 0-1; execute a redação do rascunho COM ESSE MATERIAL e salve-o internamente, sem mostrar ao usuário. Sem tipo, ele retorna o guia de decisão; identifique o tipo (perguntando se necessário) e chame texto_br_start de novo. O loop quantitativo da Fase 2 (injeção de variância sintática via texto_br_variancia + perturbação lexical controlada via texto_br_lexico, com reescrita guiada até ambos os alvos) vem ATIVADO por default; não pergunte sobre ele e desative com variancia: false apenas se o usuário pedir.
2. Chame texto_br_proxima_fase ao concluir cada fase, SEMPRE passando o texto atual no parâmetro "rascunho" (fica salvo na sessão para comparação posterior). Ele retorna a guidance e as referências da fase seguinte (2: humanização de superfície; 3: humanização profunda; 4: humanização discursiva, com hesitação, autorreparo e exemplos idiossincráticos calibrados por tipo; 5: análise macroestrutural, com texto_br_estrutura e plano de perturbação; 6: entrega). Sair da Fase 2 com o loop quantitativo ativo exige os dois alvos atingidos; sair da Fase 5 em tipos longos (blog, capitulo, tecnico, explicativo, podcast, video) exige o alvo de naturalidade estrutural (gates; use "forcar": true só a pedido do usuário). Para refazer uma fase, use o parâmetro "fase" (ex.: fase: 2). Aplique cada fase integralmente antes de avançar. Não pule fases, não as combine, não anuncie ao usuário em qual fase está.
3. Na Fase 6, entregue APENAS o texto final em Markdown limpo, sem preâmbulos nem comentários.

Tools de consulta pontual: texto_br_tipo(id) para a especificação de um tipo; texto_br_gramatica(secao) para dúvidas gramaticais (seções 1-18); texto_br_checklist(fase) para os critérios de saída das fases 2, 3, 4 e 5; texto_br_score(texto) para o score de humanidade 0-100 (probabilidade de o texto ser humano × 100, modelo logístico calibrado no corpus sobre ritmo + léxico + estrutura micro; alvo >= ${ALVO_SCORE}, satisfaz o gate da Fase 2 numa chamada); texto_br_estrutura(texto) para o score de naturalidade estrutural 0-100 (macro: simetria de seções, inflação de subtópicos, kicker uniforme, frases de efeito em sequência, progressão sinalizada; alvo >= 70) com plano de perturbação, usado na Fase 5; texto_br_otimizar(texto) para otimizar automaticamente contra o score via Claude API (subida de encosta com anti-degradação; requer ANTHROPIC_API_KEY no servidor); texto_br_variancia(texto) e texto_br_lexico(texto) para os diagnósticos individuais de ritmo e previsibilidade lexical; texto_br_status() para retomar o estado após pausa.

Regras absolutas em todas as fases: português brasileiro com AO1990; ZERO travessões (—) e meias-riscas (–); zero conectores clichê ("Além disso", "No entanto", "Em conclusão"); zero aberturas de IA ("Em um mundo onde", "Nos dias atuais"); zero meta-referência ao próprio texto; zero caracteres Unicode invisíveis. A humanização nunca pode degradar o texto.

NÃO use este workflow para tradução pura, revisão gramatical sem reescrita, ou documentos que devam ser literalmente formais e impessoais (jurídicos, atas, contratos).`;

export function createServer(session) {
  const server = new McpServer(
    { name: 'texto-br', version: '1.0.0' },
    { instructions: INSTRUCTIONS }
  );

  registerStart(server, session);
  registerProximaFase(server, session);
  registerTipo(server);
  registerGramatica(server);
  registerChecklist(server);
  registerStatus(server, session);
  registerVariancia(server, session);
  registerLexico(server, session);
  registerEstrutura(server, session);
  registerScore(server, session);
  registerOtimizar(server, session);
  registerRascunho(server, session);

  return server;
}
