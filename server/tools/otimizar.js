import Anthropic from '@anthropic-ai/sdk';
import { z } from 'zod';
import { runPython } from './run-python.js';
import { getSection } from '../content/registry.js';

const MODEL = 'claude-opus-4-8';
const MAX_ITERACOES = 4;
const MAX_SEM_MELHORA = 2;

const SYSTEM = `Você é um editor de humanização de textos em português brasileiro. Receberá um texto e um diagnóstico quantitativo (score 0-100 com componentes de ritmo, léxico e estrutura; alvo >= 80). Reescreva o texto corrigindo APENAS o que o diagnóstico aponta:

RITMO:
- Quebre sentenças longas ou uniformes (candidatas apontadas) criando 1-2 sentenças muito curtas de impacto (1-5 palavras).
- Funda sentenças curtas consecutivas com vírgula ou conjunção, criando 1-2 sentenças bem longas (30+ palavras).
- Insira 1-2 orações subordinadas não-canônicas: anteposta ("Quando o servidor caiu, ninguém notou."), intercalada ("O projeto, embora atrasado, saiu.") ou gerúndio inicial.
- Varie inícios de sentença repetidos.

LÉXICO:
- Troque cada ocorrência de vocabulário pivot apontada por uma das alternativas sugeridas, escolhendo a que cabe no contexto (ou corte a expressão).
- Reduza repetições de palavras de conteúdo e trigramas repetidos apontados, com sinônimos ou retomadas naturais.

ESTRUTURA:
- Se parágrafos forem uniformes, misture um parágrafo curto com outros longos.
- Se 3+ parágrafos seguidos abrirem com conectivo lógico, remova ao menos um.

Regras invioláveis:
- Preserve TODO o conteúdo, o sentido e o registro; não acrescente nem remova informação.
- PROIBIDO travessão (—) e meia-risca (–); use vírgula, parênteses, dois-pontos ou ponto.
- Não introduza conectores clichê ("Além disso", "No entanto", "Em conclusão") nem aberturas de IA.
- Mantenha a divisão de parágrafos e o markdown existente.
- Se uma alteração piorar a frase, escolha outra candidata: a otimização nunca degrada o texto.

Responda SOMENTE com o texto reescrito, sem comentários, sem preâmbulo, sem cercas de código.`;

function resumoDiagnostico(resultado) {
  const s = resultado.score;
  const fracos = Object.entries(s.componentes)
    .filter(([, v]) => v < 5)
    .map(([k, v]) => `${k}: ${v}`)
    .join(', ');
  const partes = [
    `score atual: ${s.total}/100 (alvo >= ${s.alvo}) | componentes fracos: ${fracos || 'nenhum'}`,
    '### Ritmo',
    ...resultado.ritmo.diagnostico,
  ];
  if (resultado.ritmo.candidatas_quebra_fusao?.length) {
    partes.push(
      'Candidatas a quebra/fusão: ' +
        resultado.ritmo.candidatas_quebra_fusao
          .slice(0, 8)
          .map((c) => `S${c.indice} (${c.palavras}p) "${c.trecho}"`)
          .join('; ')
    );
  }
  partes.push('### Léxico', ...resultado.lexico.diagnostico);
  if (resultado.lexico.ocorrencias?.length) {
    partes.push(
      'Pivots a trocar: ' +
        resultado.lexico.ocorrencias
          .slice(0, 12)
          .map((o) => `S${o.sentenca} "${o.encontrado}" → ${o.alternativas}`)
          .join('; ')
    );
  }
  return partes.join('\n');
}

export function register(server, session) {
  server.registerTool(
    'texto_br_otimizar',
    {
      title: 'Otimizar humanização (via Claude API)',
      description:
        'Otimiza um rascunho automaticamente contra o score de humanidade (texto_br_score): ' +
        'subida de encosta garantida por código que mede, reescreve via Claude API (ritmo, ' +
        'léxico e estrutura) e remede, REJEITANDO iterações que piorem o score ' +
        '(anti-degradação). Para em alvo atingido (>= 80), convergência ou 4 iterações. ' +
        'Requer ANTHROPIC_API_KEY no ambiente do servidor; sem credencial, use texto_br_score ' +
        'e reescreva manualmente.',
      inputSchema: {
        texto: z.string().min(1).describe('Rascunho completo a otimizar (markdown ou texto puro)'),
      },
    },
    async ({ texto }) => {
      const SEM_CREDENCIAL =
        'Credencial da Anthropic ausente ou inválida no ambiente do servidor ' +
        '(defina ANTHROPIC_API_KEY). Alternativa: use texto_br_score e faça a ' +
        'reescrita manualmente seguindo o diagnóstico.';

      let client;
      try {
        client = new Anthropic();
      } catch {
        return { isError: true, content: [{ type: 'text', text: SEM_CREDENCIAL }] };
      }

      try {
        const secao10 = getSection('humanizacao-algoritmos', 10);
        const pontuar = (t) => runPython('score.py', JSON.stringify({ texto: t, secao10 }));

        let melhor = { texto, analise: await pontuar(texto) };
        if (melhor.analise.erro) {
          return { isError: true, content: [{ type: 'text', text: melhor.analise.erro }] };
        }

        let iteracoes = 0;
        let semMelhora = 0;
        const trajetoria = [melhor.analise.score.total];

        while (
          !melhor.analise.atingiu_alvo &&
          iteracoes < MAX_ITERACOES &&
          semMelhora < MAX_SEM_MELHORA
        ) {
          iteracoes += 1;
          const resposta = await client.messages.create({
            model: MODEL,
            max_tokens: 16000,
            thinking: { type: 'adaptive' },
            system: SYSTEM,
            messages: [
              {
                role: 'user',
                content: `## Diagnóstico\n${resumoDiagnostico(melhor.analise)}\n\n## Texto\n${melhor.texto}`,
              },
            ],
          });
          const bloco = resposta.content.find((b) => b.type === 'text');
          if (!bloco?.text?.trim()) {
            semMelhora += 1;
            continue;
          }
          const candidato = bloco.text.trim();
          const analise = await pontuar(candidato);
          if (analise.erro) {
            semMelhora += 1;
            continue;
          }
          trajetoria.push(analise.score.total);
          // Anti-degradação: só aceita a iteração se o score subir
          if (analise.score.total > melhor.analise.score.total) {
            melhor = { texto: candidato, analise };
            semMelhora = 0;
          } else {
            semMelhora += 1;
          }
        }

        if (session) {
          session.varianciaAtingida =
            melhor.analise.ritmo.atingiu_alvo === true || melhor.analise.atingiu_alvo === true;
          session.lexicoAtingido =
            melhor.analise.lexico.atingiu_alvo === true || melhor.analise.atingiu_alvo === true;
          session.persist();
        }

        const cabecalho = melhor.analise.atingiu_alvo
          ? `Otimização concluída em ${iteracoes} iteração(ões); alvo atingido.`
          : `Otimização parou (${iteracoes} iteração(ões), convergência ou limite); segue a melhor versão encontrada (revise os pontos restantes manualmente).`;

        const text = [
          cabecalho,
          `Trajetória do score: ${trajetoria.join(' → ')}`,
          '## Texto otimizado',
          melhor.texto,
          melhor.analise.relatorio,
        ].join('\n\n');
        return { content: [{ type: 'text', text }] };
      } catch (err) {
        const semAuth =
          err instanceof Anthropic.AuthenticationError ||
          /authentication|api.?key|x-api-key/i.test(err.message ?? '');
        if (semAuth) {
          return { isError: true, content: [{ type: 'text', text: SEM_CREDENCIAL }] };
        }
        return { isError: true, content: [{ type: 'text', text: err.message }] };
      }
    }
  );
}
