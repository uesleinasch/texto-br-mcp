// Conhecimento curado do workflow texto-br. Toda evolução do pipeline
// (guidance de fase, quais seções cada fase consome) acontece neste arquivo.

export const TIPOS_VALIDOS = [
  'blog',
  'tecnico',
  'corporativo',
  'email',
  'capitulo',
  'podcast',
  'video',
  'explicativo',
  'geral',
  'comentario-blog',
  'comentario-jira',
  'chat',
];

export const TAMANHOS = {
  curto: '300-500 palavras',
  medio: '600-900 palavras',
  longo: '1000-1500 palavras',
  extenso: '1800-2500 palavras',
  conversacional: 'dimensão natural de chat/comentário',
};

// Alvo do score de naturalidade estrutural da Fase 5 (0-100). Fonte única:
// estrutura.js injeta este valor no payload do script Python, que só cai no
// próprio ALVO_PADRAO (analysis/estrutura.py) em uso standalone (sem payload).
export const ALVO_ESTRUTURA = 70;

// Alvo do score de humanidade da Fase 2 (0-100). Fonte única do lado JS,
// espelho de score.ALVO (Python, congelado pela calibração) — o teste de
// paridade em test/alvo-paridade.test.js trava a igualdade.
export const ALVO_SCORE = 93.6;

export const REGRAS_ABSOLUTAS = `## Regras absolutas (valem em todas as fases)

1. Português brasileiro, sem regionalismos lusitanos.
2. Acordo Ortográfico de 1990 aplicado (use texto_br_gramatica(secao) em caso de dúvida).
3. Zero travessões (—) e zero meias-riscas (–): substitua sempre por vírgulas, parênteses, dois-pontos, ponto final ou ponto e vírgula.
4. Zero caracteres Unicode invisíveis.
5. Zero conectores da lista negra ("Além disso", "No entanto", "Em conclusão", "Vale ressaltar" e demais conectores pivot).
6. Zero aberturas clichê de IA ("Em um mundo onde", "Nos dias atuais", "No cenário atual").
7. Zero meta-referência ao próprio texto ("neste artigo", "como veremos", "lendo até o fim").
8. A humanização nunca degrada o texto: se a versão pós-humanização ficar pior que o rascunho, refaça. O alvo é texto melhor, não apenas mais humano.

## Formato de saída padrão

Markdown limpo; "#" para título principal apenas em capítulos de livro; "##" para seções e "###" para subseções; negrito moderado; itálico para ênfase ou termos estrangeiros; listas com "-" ou "1."; código em cercas; citações com ">". Nenhum travessão em nenhum lugar.`;

export const PHASE_GUIDANCE = {
  0: {
    name: 'Coleta de contexto',
    instruction: `Identifique três coisas. Se o usuário já forneceu, use o que ele disse; se não, pergunte de forma objetiva (uma única mensagem com as perguntas juntas):

1. **Tipo de texto**: um dos IDs válidos (${TIPOS_VALIDOS.join(', ')}).
2. **Briefing/tema**: o que escrever.
3. **Tamanho aproximado**: curto (300-500), medio (600-900), longo (1000-1500), extenso (1800-2500) ou conversacional.

Opcionalmente, se relevante ao tipo: tom, público-alvo, palavras-chave.

Defaults se o usuário disser apenas "escreva sobre X": tipo "geral", tamanho "medio", tom natural.

Heurística rápida: "responde esse e-mail" → email; "comenta nesse ticket" → comentario-jira; "responde no Slack" → chat; "escreve um artigo/post" → blog. Em dúvida, pergunte.

Nota: o loop quantitativo da Fase 2 (injeção de variância sintática + perturbação lexical controlada) vem ATIVADO por default; não pergunte sobre ele. Desative com variancia: false apenas se o usuário pedir explicitamente.

Quando o tipo estiver definido, chame texto_br_start novamente com briefing, tipo e tamanho preenchidos para receber o material da Fase 1.`,
  },
  1: {
    name: 'Redação',
    instruction: `Escreva o rascunho completo seguindo:

- A estrutura, o tom e as armadilhas do tipo (seção do tipo incluída abaixo).
- As regras gramaticais do AO1990 (seções essenciais incluídas abaixo; para sintaxe, concordância, regência ou colocação pronominal, consulte texto_br_gramatica(secao) com a seção 6-15 desejada).
- A regra inegociável de pontuação: zero travessões (—) e zero meias-riscas (–) em qualquer hipótese.
- Português brasileiro, sem regionalismos lusitanos.

Não mostre o rascunho ao usuário, não comente, não anuncie fase concluída. O usuário só verá o resultado da fase de entrega. Ao terminar, chame texto_br_proxima_fase passando o rascunho completo no parâmetro "rascunho" (isso o preserva na sessão para comparação posterior).`,
  },
  2: {
    name: 'Humanização de superfície',
    instruction: `Releia o rascunho da Fase 1 e aplique o pipeline completo de humanização de superfície (material incluído abaixo):

1. Limpeza Unicode (remover invisíveis, normalizar pontuação).
2. Reescrita lexical (substituir vocabulário pivot da lista negra).
3. Reestruturação sintática (variar drasticamente comprimento de sentenças; burstiness >= 0.7).
4. Quebra de estruturas paralelas (eliminar tríades automáticas e simetria de parágrafos).
5. Injeção de voz humana (subjetividade, contrações, expressões brasileiras conforme o tipo permitir).

Calibração: tipos conversacionais (chat, comentários) recebem humanização leve; produção longa (blog, capitulo, podcast) recebe humanização intensa.

Critério de saída: o checklist retornado por texto_br_checklist(2) deve estar todo verificado. Se algum item falhar, reaplique a técnica correspondente. Depois chame texto_br_proxima_fase passando a versão atual em "rascunho".`,
  },
  3: {
    name: 'Humanização profunda (quatro camadas)',
    instruction: `Esta fase distingue humanização superficial bem-feita (que ainda soa "polida demais") de texto verdadeiramente humano. Pular esta fase é o erro mais comum. Aplique, na ordem, conforme a intensidade da matriz de calibração (seção 6, incluída abaixo) para o tipo:

1. Camada referencial (aterragem): âncoras concretas no lugar de generalizações; remover meta-referências.
2. Camada sensorial (detalhe único): 1-2 atributos idiossincráticos; cortar empilhamento sensorial e verbos clichês.
3. Camada epistêmica (fricção): marcadores de dúvida/contradição (1 a cada 300 palavras); em email e corporativo formal, evitar ou manter institucional.
4. Camada posicional (ângulo): o texto precisa ter dono; eliminar equilíbrio performático.
5. Coerência local vs global: retomada lexical em vez de conectivos previsíveis; em texto 1000+ palavras, permitir uma digressão controlada.

Critério de saída: checklist retornado por texto_br_checklist(3) verificado conforme a matriz. Pergunta-síntese: um leitor atento sentiria que há "alguém por trás" do texto? Antes de avançar, pergunta final de qualidade: "um estrangeiro inteligente que leu sobre o tema em livros, mas nunca viveu esse contexto, escreveria exatamente este texto?" Se sim, reaplique aterragem e ângulo com mais força. Depois chame texto_br_proxima_fase().`,
  },
  4: {
    name: 'Humanização discursiva',
    instruction: `Esta fase trabalha a performance do enunciador: não o que o texto diz (isso foi a Fase 3), mas como a voz se comporta na página. Aplique conforme a matriz de calibração (seção 6, incluída abaixo) para o tipo; em tipos com intensidade 0-1, esta fase é quase transparente, não force.

1. **Marcadores de hesitação e modalização**: gradue o compromisso da voz perto das afirmações fortes ("de certa forma", "ao menos aparentemente", "até onde consigo ver"). Dose: 1 a cada 300-450 palavras; nunca dois na mesma sentença; nunca o mesmo marcador duas vezes.
2. **Autocorreção/reformulação (autorreparo)**: deixe 1 (no máximo 2) reformulação à mostra, em que a segunda formulação é de fato mais precisa ("Foi um erro. Ou, sendo mais justo, uma aposta que envelheceu mal."). Não duplique fricções de ideia já inseridas na Fase 3: aqui muda a palavra, não o argumento.
3. **Referência cultural ou exemplo idiossincrático**: 1 por texto, trabalhando para o argumento; detalhe modesto e específico demais para ser estatística (mural de cortiça, terceira queda do servidor), sem kit clichê Brasil-para-export.
4. **Apartes e endereçamento**: 1-2 apartes curtos entre parênteses se o tipo permitir; sem informação essencial dentro deles.

Critério de saída: checklist retornado por texto_br_checklist(4) verificado conforme a matriz. Pergunta-síntese: o texto soa como alguém pensando por escrito, sem tique repetido? Cada técnica é sal, não molho: na dúvida, aplique menos. Depois chame texto_br_proxima_fase().`,
  },
  5: {
    name: 'Análise macroestrutural',
    instruction: `Antes da entrega, desencaixe a macroestrutura. Texto de IA tende a uma arquitetura simétrica demais (seções gêmeas, títulos paralelos, parágrafos que sempre fecham numa "lição", bordões em sequência, subtópicos demais, progressão linear com signposts). As fases anteriores cuidaram da palavra e da sentença; esta cuida do documento inteiro.

1. Chame texto_br_estrutura com o rascunho atual (ele usa o tipo da sessão para calibrar e medir).
2. Aplique o plano de perturbação que ele devolver, corrigindo os detectores mais fracos primeiro. NUNCA degrade a clareza: a assimetria serve ao texto, não o contrário.
3. Meça de novo. Repita até "ALVO ATINGIDO" (score >= ${ALVO_ESTRUTURA}) ou, no máximo, 3 iterações.

Critério de saída: checklist de texto_br_checklist(5) verificado. Em tipos longos (blog, capitulo, tecnico, explicativo, podcast, video) o gate exige o alvo atingido para avançar; nos demais é advisory. Depois chame texto_br_proxima_fase passando a versão atual em "rascunho".`,
  },
  6: {
    name: 'Entrega',
    instruction: `Entregue APENAS o texto final em Markdown limpo:

- Sem preâmbulos ("Aqui está...", "Segue abaixo...").
- Sem comentários após o texto.
- Sem auto-elogios sobre o processo nem anúncios de fases.
- Apenas o texto.

Se o usuário pedir explicitamente, mostre também o rascunho da Fase 1 para comparação. Em qualquer outro caso, mostrar o rascunho é violação do workflow.`,
  },
};

// Tipos conversacionais recebem payloads enxutos (roteamento adaptativo):
// textos curtos não precisam das seções completas de gramática e humanização.
export const TIPOS_CONVERSACIONAIS = ['email', 'comentario-blog', 'comentario-jira', 'chat'];

// Mapa declarativo: quais seções de quais references cada fase recebe.
// Notações especiais: "type:{slug}" (seção do tipo ativo, resolvida em runtime),
// "h1:Texto" (bloco de heading nível 1 com texto exato) e "h2:Texto" (idem,
// nível 2, até o próximo heading de nível <= 2).
export const PHASE_SECTIONS = {
  0: [{ file: 'tipos-de-texto', section: 'h1:Apêndice: Decisão rápida de tipo' }],
  1: [
    { file: 'tipos-de-texto', section: 'h2:Princípios gerais aplicáveis a todos os tipos' },
    { file: 'tipos-de-texto', section: 'type:{slug}' },
    { file: 'gramatica-pt-br', section: '2' }, // acentuação
    { file: 'gramatica-pt-br', section: '3' }, // hifenização
    { file: 'gramatica-pt-br', section: '4' }, // ortografia
    { file: 'gramatica-pt-br', section: '5' }, // pontuação
    { file: 'gramatica-pt-br', section: '12' }, // crase
    { file: 'gramatica-pt-br', section: '17' }, // erros frequentes
    { file: 'gramatica-pt-br', section: '18' }, // particularidades pt-BR
  ],
  2: [
    { file: 'humanizacao-algoritmos', section: '4' }, // algoritmo master
    { file: 'humanizacao-algoritmos', section: '5' }, // perplexidade
    { file: 'humanizacao-algoritmos', section: '6' }, // burstiness
    { file: 'humanizacao-algoritmos', section: '7' }, // estruturas paralelas
    { file: 'humanizacao-algoritmos', section: '8' }, // voz humana
    { file: 'humanizacao-algoritmos', section: '9' }, // caracteres invisíveis
    { file: 'humanizacao-algoritmos', section: '10' }, // substituições lexicais
    // checklist (seção 11) só via texto_br_checklist(2), para não duplicar payload
  ],
  3: [
    { file: 'camadas-profundas', section: '1' },
    { file: 'camadas-profundas', section: '2' },
    { file: 'camadas-profundas', section: '3' },
    { file: 'camadas-profundas', section: '4' },
    { file: 'camadas-profundas', section: '5' },
    { file: 'camadas-profundas', section: '6' }, // matriz de calibração
    // checklist (seção 7) só via texto_br_checklist(3)
  ],
  4: [
    { file: 'humanizacao-discursiva', section: '2' }, // hesitação/modalização
    { file: 'humanizacao-discursiva', section: '3' }, // autorreparo
    { file: 'humanizacao-discursiva', section: '4' }, // referências/exemplos
    { file: 'humanizacao-discursiva', section: '5' }, // apartes
    { file: 'humanizacao-discursiva', section: '6' }, // matriz de calibração
    // checklist (seção 7) só via texto_br_checklist(4)
    { file: 'humanizacao-discursiva', section: '8' }, // armadilhas
  ],
  5: [
    { file: 'estrutura-macro', section: '1' }, // o sinal
    { file: 'estrutura-macro', section: '2' }, // simetria de seções
    { file: 'estrutura-macro', section: '3' }, // inflação de subtópicos
    { file: 'estrutura-macro', section: '4' }, // parágrafo-lição (kicker)
    { file: 'estrutura-macro', section: '5' }, // frases de efeito em sequência
    { file: 'estrutura-macro', section: '6' }, // progressão sinalizada
    { file: 'estrutura-macro', section: '7' }, // matriz de calibração
    // checklist (seção 8) só via texto_br_checklist(5)
  ],
  6: [],
};

// Payloads enxutos para tipos conversacionais (fases ausentes herdam o mapa cheio).
// Seções podadas continuam acessíveis sob demanda via texto_br_gramatica etc.
export const PHASE_SECTIONS_CONVERSACIONAL = {
  1: [
    { file: 'tipos-de-texto', section: 'h2:Princípios gerais aplicáveis a todos os tipos' },
    { file: 'tipos-de-texto', section: 'type:{slug}' },
    { file: 'gramatica-pt-br', section: '4' }, // ortografia (porquês, mau/mal, a/há...)
    { file: 'gramatica-pt-br', section: '5' }, // pontuação (regra dos travessões)
    { file: 'gramatica-pt-br', section: '17' }, // erros frequentes
  ],
  2: [
    { file: 'humanizacao-algoritmos', section: '4' }, // algoritmo master
    { file: 'humanizacao-algoritmos', section: '8' }, // voz humana
    { file: 'humanizacao-algoritmos', section: '9' }, // caracteres invisíveis
    { file: 'humanizacao-algoritmos', section: '10' }, // substituições lexicais
  ],
  3: [
    { file: 'camadas-profundas', section: '1' }, // aterragem
    { file: 'camadas-profundas', section: '3' }, // fricção epistêmica
    { file: 'camadas-profundas', section: '6' }, // matriz de calibração
  ],
  4: [
    { file: 'humanizacao-discursiva', section: '2' }, // hesitação
    { file: 'humanizacao-discursiva', section: '3' }, // autorreparo
    { file: 'humanizacao-discursiva', section: '6' }, // matriz de calibração
  ],
  5: [
    { file: 'estrutura-macro', section: '4' }, // parágrafo-lição (kicker)
    { file: 'estrutura-macro', section: '7' }, // matriz de calibração
  ],
};

export const CHECKLISTS = {
  2: { file: 'humanizacao-algoritmos', section: '11' },
  3: { file: 'camadas-profundas', section: '7' },
  4: { file: 'humanizacao-discursiva', section: '7' },
  5: { file: 'estrutura-macro', section: '8' },
};

// Tipos longos onde a Fase 5 (macroestrutura) bloqueia a entrega até o alvo.
// Fonte de verdade replicada em analysis/estrutura.py (TIPOS_GATE).
export const TIPOS_ESTRUTURA_GATE = ['blog', 'capitulo', 'tecnico', 'explicativo', 'podcast', 'video'];

// Loop quantitativo da Fase 2 (variância sintática + perturbação lexical).
// Ativo por default; desligado apenas com variancia: false a pedido do usuário.
export const LOOP_QUANTITATIVO_GUIDANCE = `## Loop quantitativo (ATIVADO)

Depois de aplicar as cinco técnicas de superfície acima, otimize contra o score de humanidade (probabilidade de texto humano × 100; alvo >= ${ALVO_SCORE}):

1. **Via automática (preferencial se disponível)**: chame texto_br_otimizar com o rascunho completo. Ela roda a subida de encosta inteira (medir → reescrever → medir, rejeitando iterações que piorem o score) e devolve o texto otimizado com a trajetória. Se retornar erro de credencial, siga a via manual.
2. **Via manual**: chame texto_br_score com o rascunho e corrija os componentes fracos apontados:
   - **Ritmo (injeção de variância sintática)**: quebre candidatas em sentenças muito curtas (1-5 palavras), funda curtas consecutivas em longas (30+), insira 1-2 subordinadas não-canônicas (anteposta: "Quando X, Y"; intercalada: "O projeto, embora atrasado, saiu"; gerúndio inicial), varie inícios repetidos.
   - **Léxico (perturbação lexical controlada)**: troque cada pivot apontado pela alternativa que cabe no contexto (ou corte). As listas são o PISO: perturbe também palavras previsíveis demais no contexto deste texto (use repetições, diversidade e trigramas como sinal).
   - **Estrutura**: parágrafos uniformes e correntes de conectivos apontados.
3. Reescreva APENAS os pontos apontados e meça de novo. Repita até "ALVO ATINGIDO", com no máximo 3 iterações manuais. Se o score CAIR após uma reescrita, descarte-a e volte à versão anterior: a otimização nunca degrada o texto.`;
