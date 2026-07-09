import { z } from 'zod';
import { runPython } from './run-python.js';
import { getSection } from '../content/registry.js';
import { ALVO_SCORE } from '../knowledge/phases.js';

// Roteiro de reescrita entregue ao HOST (antes era o system prompt de uma
// chamada de API). O host aplica estas técnicas guiado pelo diagnóstico.
export const ROTEIRO_REESCRITA = `Reescreva o texto corrigindo APENAS o que o diagnóstico aponta (score 0-100 = probabilidade de texto humano × 100; alvo >= ${ALVO_SCORE}):

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
- Após reescrever, meça de novo com texto_br_score; se o score cair, descarte a reescrita e volte à versão anterior.`;

// Resumo do diagnóstico priorizado. Componentes "fracos" são os de contribuição
// NEGATIVA no logit do modelo calibrado: os sinais que puxam o score para "IA"
// (o valor 0-1 correspondente aparece em score.sinais para contexto).
export function resumoDiagnostico(resultado) {
  const s = resultado.score;
  const sinais = s.sinais ?? {};
  const fracos = Object.entries(s.componentes)
    .filter(([, v]) => v < 0)
    .sort(([, a], [, b]) => a - b)
    .map(([k, v]) => `${k}: ${v} (sinal ${sinais[k] ?? '?'})`)
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

// Mede o texto uma vez e monta o pacote acionável (diagnóstico + score) para o
// HOST reescrever. Sem client, sem API, sem loop: o loop de subida de encosta é
// dirigido pelo host (guidance da Fase 2). O gate espelha texto_br_score: mede o
// texto de entrada e libera os flags conforme a medição. Injetável/testável
// (pontuar/session fakes).
export async function montarPacoteOtimizacao({ texto, pontuar, session }) {
  const analise = await pontuar(texto);
  if (analise.inaplicavel) {
    // Texto curto demais para medir (mesmo contrato de texto_br_score): não há o
    // que reescrever, mas também não trava o gate.
    if (session) {
      session.registrarVariancia(true, texto);
      session.registrarLexico(true, texto);
    }
    return { inaplicavel: true, relatorio: analise.relatorio };
  }
  if (analise.erro) return { erro: analise.erro };

  if (session) {
    session.registrarVariancia(
      analise.ritmo.atingiu_alvo === true || analise.atingiu_alvo === true,
      texto
    );
    session.registrarLexico(
      analise.lexico.atingiu_alvo === true || analise.atingiu_alvo === true,
      texto
    );
  }
  return {
    atingiu_alvo: analise.atingiu_alvo === true,
    score: analise.score,
    diagnostico: resumoDiagnostico(analise),
    relatorio: analise.relatorio,
  };
}

export function register(server, session) {
  server.registerTool(
    'texto_br_otimizar',
    {
      title: 'Pacote de otimização (diagnóstico + roteiro de reescrita)',
      description:
        'Empacota numa única chamada o diagnóstico priorizado do score de humanidade ' +
        '(texto_br_score) e o roteiro de reescrita (ritmo, léxico e estrutura + regras ' +
        'invioláveis) para o HOST reescrever o texto. Não chama modelo nenhum nem requer ' +
        `credencial. Mede o texto de entrada; se ainda abaixo do alvo (>= ${ALVO_SCORE}), ` +
        'devolve os pontos a corrigir e como corrigi-los. Reescreva e remeça com ' +
        'texto_br_score, repetindo até o alvo (descarte reescritas que baixem o score).',
      inputSchema: {
        texto: z
          .string()
          .min(1)
          .describe('Rascunho completo a diagnosticar (markdown ou texto puro)'),
      },
    },
    async ({ texto }) => {
      try {
        const secao10 = getSection('humanizacao-algoritmos', 10);
        const pontuar = (t) => runPython('score.py', JSON.stringify({ texto: t, secao10 }));
        const pacote = await montarPacoteOtimizacao({ texto, pontuar, session });

        if (pacote.erro) {
          return { isError: true, content: [{ type: 'text', text: pacote.erro }] };
        }
        if (pacote.inaplicavel) {
          return { content: [{ type: 'text', text: pacote.relatorio }] };
        }
        if (pacote.atingiu_alvo) {
          const text = [
            `Score ${pacote.score.total}/100 — alvo (>= ${pacote.score.alvo}) já atingido. Nada a reescrever.`,
            pacote.relatorio,
          ].join('\n\n');
          return { content: [{ type: 'text', text }] };
        }
        const text = [
          `Score ${pacote.score.total}/100 (alvo >= ${pacote.score.alvo}). Reescreva os pontos abaixo seguindo o roteiro; depois remeça com texto_br_score e repita até o alvo. Se o score cair, descarte a reescrita e volte à versão anterior.`,
          '## Diagnóstico priorizado',
          pacote.diagnostico,
          '## Roteiro de reescrita',
          ROTEIRO_REESCRITA,
          '## Relatório completo',
          pacote.relatorio,
        ].join('\n\n');
        return { content: [{ type: 'text', text }] };
      } catch (err) {
        return { isError: true, content: [{ type: 'text', text: err.message }] };
      }
    }
  );
}
