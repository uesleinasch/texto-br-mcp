import Anthropic from '@anthropic-ai/sdk';
import { z } from 'zod';
import { runPython } from './run-python.js';

const MODEL = 'claude-opus-4-8';
const MAX_ITERACOES = 3;

const SYSTEM = `Você é um editor de ritmo sintático de textos em português brasileiro. Receberá um texto e um diagnóstico quantitativo (burstiness = desvio/média dos comprimentos de sentença; alvo >= 0.7). Sua única tarefa é reescrever o texto corrigindo o ritmo, com três operações:

1. QUEBRAR sentenças longas ou uniformes (as candidatas apontadas no diagnóstico) em sentenças menores, criando 1-2 sentenças muito curtas de impacto (1-5 palavras).
2. FUNDIR sentenças curtas consecutivas com vírgula ou conjunção, criando 1-2 sentenças bem longas (30+ palavras).
3. INSERIR 1-2 orações subordinadas não-canônicas: anteposta ("Quando o servidor caiu, ninguém notou."), intercalada ("O projeto, embora atrasado, saiu.") ou gerúndio inicial, reorganizando sentenças existentes.

Regras invioláveis:
- Preserve TODO o conteúdo, o sentido, o registro e o vocabulário; não acrescente nem remova informação. Mexa apenas na estrutura das sentenças apontadas, o mínimo necessário.
- PROIBIDO travessão (—) e meia-risca (–) em qualquer hipótese; use vírgula, parênteses, dois-pontos ou ponto.
- Não introduza conectores clichê ("Além disso", "No entanto", "Em conclusão").
- Mantenha a divisão de parágrafos e qualquer markdown existente.
- Se uma quebra ou fusão piorar a frase, escolha outra candidata: a correção nunca degrada o texto.

Responda SOMENTE com o texto reescrito, sem comentários, sem preâmbulo, sem cercas de código.`;

function resumoDiagnostico(resultado) {
  const m = resultado.metricas;
  const partes = [
    `burstiness atual: ${m.burstiness} (alvo >= 0.7) | comprimentos: [${m.comprimentos.join(', ')}]`,
    ...resultado.diagnostico,
  ];
  if (resultado.candidatas_quebra_fusao?.length) {
    partes.push(
      'Candidatas a quebra/fusão: ' +
        resultado.candidatas_quebra_fusao
          .map((c) => `S${c.indice} (${c.palavras}p) "${c.trecho}"`)
          .join('; ')
    );
  }
  return partes.join('\n');
}

export function register(server, session) {
  server.registerTool(
    'texto_br_variancia_aplicar',
    {
      title: 'Aplicar variância sintática (via Claude API)',
      description:
        'Corrige o ritmo sintático de um rascunho automaticamente: roda um loop garantido por ' +
        'código que mede (texto_br_variancia), reescreve cirurgicamente via Claude API (quebra ' +
        'sentenças longas/uniformes, funde curtas consecutivas, insere subordinadas ' +
        'não-canônicas) e mede de novo, até burstiness >= 0.7 ou 3 iterações. Requer ' +
        'ANTHROPIC_API_KEY no ambiente do servidor; sem credencial, retorna erro e a reescrita ' +
        'deve ser feita manualmente seguindo o diagnóstico de texto_br_variancia.',
      inputSchema: {
        texto: z.string().min(1).describe('Rascunho completo a corrigir (markdown ou texto puro)'),
      },
    },
    async ({ texto }) => {
      const SEM_CREDENCIAL =
        'Credencial da Anthropic ausente ou inválida no ambiente do servidor ' +
        '(defina ANTHROPIC_API_KEY). Alternativa: use texto_br_variancia e faça a ' +
        'reescrita manualmente seguindo o diagnóstico.';

      let client;
      try {
        client = new Anthropic();
      } catch {
        return { isError: true, content: [{ type: 'text', text: SEM_CREDENCIAL }] };
      }

      try {
        let atual = texto;
        let analise = await runPython('variancia.py', atual);
        if (analise.erro) {
          return { isError: true, content: [{ type: 'text', text: analise.erro }] };
        }

        let iteracoes = 0;
        while (!analise.atingiu_alvo && iteracoes < MAX_ITERACOES) {
          iteracoes += 1;
          const resposta = await client.messages.create({
            model: MODEL,
            max_tokens: 16000,
            thinking: { type: 'adaptive' },
            system: SYSTEM,
            messages: [
              {
                role: 'user',
                content: `## Diagnóstico\n${resumoDiagnostico(analise)}\n\n## Texto\n${atual}`,
              },
            ],
          });
          const blocoTexto = resposta.content.find((b) => b.type === 'text');
          if (!blocoTexto?.text?.trim()) {
            throw new Error('A reescrita retornou vazia; mantendo a versão anterior.');
          }
          atual = blocoTexto.text.trim();
          analise = await runPython('variancia.py', atual);
        }

        if (session) {
          session.varianciaAtingida = analise.atingiu_alvo === true;
          session.persist();
        }

        const cabecalho = analise.atingiu_alvo
          ? `Ritmo corrigido em ${iteracoes} iteração(ões); alvo atingido.`
          : `Limite de ${MAX_ITERACOES} iterações atingido sem fechar o alvo; segue a melhor versão (revise os pontos restantes manualmente).`;

        const text = [
          cabecalho,
          '## Texto reescrito',
          atual,
          analise.relatorio,
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
