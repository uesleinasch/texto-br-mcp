---
name: texto-br
description: Escrita profissional em português brasileiro com pipeline de sete fases (coleta, redação, humanização de superfície, humanização profunda, humanização discursiva, análise macroestrutural, entrega). Use quando o usuário pedir para escrever, redigir, criar, produzir, rascunhar ou humanizar textos em pt-BR — artigos de blog, artigos técnicos, textos corporativos, e-mails, capítulos de livro, roteiros de podcast, roteiros de vídeo, textos explicativos, textos gerais, comentários em blog, comentários em Jira ou respostas de chat. Aplica rigorosamente o Acordo Ortográfico de 1990 e produz textos calibrados para serem indistinguíveis de escrita humana por detectores como ZeroGPT, GPTZero, Copyleaks e Originality.ai.
---

# texto-br

Produz textos em português brasileiro de alta qualidade — gramaticalmente impecáveis e estatisticamente indistinguíveis de escrita humana.

Esta skill é um **orquestrador**. As regras operacionais vivem em `references/`. O Claude deve **ler as referências no momento indicado pelo workflow**, não tentar memorizar nem improvisar.

## Quando usar esta skill

Acione quando o usuário:

- Pedir para escrever, redigir, criar, produzir ou rascunhar texto em português (pt-BR)
- Mencionar qualquer um dos 12 tipos suportados (listados em `references/tipos-de-texto.md`)
- Pedir para humanizar, reescrever ou disfarçar um texto gerado por IA
- Solicitar texto que precise passar por detectores de IA

**Não acione** para tradução pura, revisão gramatical sem reescrita, ou documentos que devam ser literalmente formais e impessoais (jurídicos, atas, contratos).

## Referências obrigatórias

Esta skill depende de quatro documentos em `references/`. Cada um cobre uma camada do trabalho. Eles **não são opcionais** — são lidos durante o workflow:

| Arquivo                                | Conteúdo                                                | Quando ler                         |
| -------------------------------------- | ------------------------------------------------------- | ---------------------------------- |
| `references/tipos-de-texto.md`         | Especificação dos 12 tipos, estrutura, tom, armadilhas  | Fase 0 (coleta) e Fase 1 (redação) |
| `references/gramatica-pt-br.md`        | Regras completas do Acordo Ortográfico de 1990          | Fase 1 (redação) sempre            |
| `references/humanizacao-algoritmos.md` | Pipeline de superfície (perplexidade, burstiness, etc.) | Fase 2 (humanização de superfície) |
| `references/camadas-profundas.md`      | Quatro camadas semânticas + matriz de calibração        | Fase 3 (humanização profunda)      |
| `references/humanizacao-discursiva.md` | Hesitação, autorreparo, exemplos idiossincráticos       | Fase 4 (humanização discursiva)    |

## Workflow obrigatório

Execute SEMPRE nas fases abaixo, nesta ordem. Não pule, não combine, não anuncie ao usuário em qual fase está. O resultado entregue é apenas o produto da Fase 6.

---

### Fase 0 — Coleta de contexto

**Leia:** `references/tipos-de-texto.md` (seção "Decisão rápida de tipo")

Identifique três coisas. Se o usuário forneceu, use o que ele disse. Se não forneceu, pergunte de forma objetiva (uma única mensagem, com as três perguntas juntas):

1. **Tipo de texto** — um dos 12 IDs documentados em `tipos-de-texto.md`
2. **Briefing/tema** — o que escrever sobre
3. **Tamanho aproximado** — curto (300-500), médio (600-900), longo (1000-1500), extenso (1800-2500), ou específico do tipo conversacional (chat/comentário)

Opcionalmente, se relevante ao tipo: tom, público-alvo, palavras-chave.

**Defaults se o usuário disser apenas "escreva sobre X":** tipo `geral`, tamanho médio, tom natural.

**Heurística rápida de tipo conversacional vs produção:**

- "Responde esse e-mail" → `email`
- "Comenta nesse ticket" → `comentario-jira`
- "Responde no Slack" → `chat`
- "Escreve um artigo/post sobre" → `blog`
- Em dúvida: perguntar ao usuário.

---

### Fase 1 — Redação

**Leia:**

- `references/tipos-de-texto.md` — seção do tipo identificado (estrutura, tom, armadilhas)
- `references/gramatica-pt-br.md` — sempre, para garantir Acordo Ortográfico de 1990

Escreva o texto seguindo:

- A estrutura e tom específicos do tipo escolhido (formato de e-mail, estrutura de podcast, abertura de blog, etc.)
- As regras gramaticais de pt-BR conforme AO1990 (acentuação, hifenização, crase, porquês, concordância, regência)
- **A regra inegociável de pontuação: zero travessões (—) e zero meias-riscas (–) em qualquer hipótese.** Use vírgulas, parênteses, dois-pontos, ponto final ou ponto e vírgula conforme contexto. Detalhes em `gramatica-pt-br.md` → seção "Pontuação" e `humanizacao-algoritmos.md` → seção sobre travessões.
- Português brasileiro, sem regionalismos lusitanos

**Salve o rascunho internamente.** Não mostre ao usuário. Não comente. Não anuncie "Fase 1 concluída". O usuário só verá o resultado da Fase 6.

---

### Fase 2 — Humanização de superfície

**Leia:** `references/humanizacao-algoritmos.md` completo

Releia o rascunho da Fase 1 e aplique o pipeline completo de humanização de superfície:

1. **Limpeza Unicode** — remover caracteres invisíveis, normalizar pontuação
2. **Reescrita lexical** — substituir vocabulário pivot (verbos, adjetivos, substantivos, conectores da lista negra)
3. **Reestruturação sintática** — variar drasticamente comprimento de sentenças (alvo burstiness > 0.6)
4. **Quebra de estruturas paralelas** — eliminar tríades automáticas, simetria de parágrafos
5. **Injeção de voz humana** — marcadores de subjetividade, contrações, expressões brasileiras conforme o tipo permitir

**Calibração por tipo:** tipos conversacionais (chat, comentários) recebem humanização **leve**. Tipos de produção longa (blog, capítulo, podcast) recebem humanização **intensa**.

**Critério de saída da Fase 2:** o checklist da seção 11 de `humanizacao-algoritmos.md` deve estar todo verificado. Se algum item falhar, voltar e reaplicar a técnica correspondente.

---

### Fase 3 — Humanização profunda (quatro camadas)

**Leia:** `references/camadas-profundas.md` completo, com atenção especial à **matriz de calibração** (seção 6) para o tipo identificado.

Esta fase é o que distingue humanização superficial bem-feita (que ainda soa "polida demais") de texto verdadeiramente humano. **Pular esta fase é o erro mais comum** — não pule.

Aplicar, na ordem, **conforme intensidade da matriz para o tipo**:

1. **Camada referencial — Aterragem.** Substituir generalizações vagas ("no Brasil", "muitas pessoas", "recentemente") por âncoras concretas. Remover toda meta-referência ao próprio texto ("neste artigo", "como veremos").
2. **Camada sensorial — Detalhe único.** Reduzir empilhamento de atributos sensoriais (3+ consecutivos = corte). Substituir por 1-2 atributos idiossincráticos. Remover verbos sensoriais clichês ("exala", "perfuma", "dança no paladar").
3. **Camada epistêmica — Fricção.** Introduzir marcadores de dúvida, contradição, mudança de ideia (1 a cada 300 palavras). **Atenção à matriz:** em e-mail e texto corporativo formal, essa camada é evitada ou apenas institucional.
4. **Camada posicional — Ângulo.** Garantir que o texto tem dono — posição declarada, paixão específica, referência cultural, irritação genuína. Em corporativo, ângulo institucional ("na nossa visão"). Eliminar equilíbrio performático ("há prós e contras de ambos os lados").
5. **Coerência local vs global.** Fortalecer transições locais com retomada lexical em vez de conectivos previsíveis. Em texto longo (1000+ palavras), permitir uma digressão controlada que sai do trilho e volta.

**Critério de saída da Fase 3:** o checklist da seção 7 de `camadas-profundas.md` deve estar todo verificado **conforme a matriz** para o tipo de texto. Pergunta-síntese: um leitor humano atento sentiria que há "alguém por trás" do texto?

---

### Fase 4 — Humanização discursiva

**Leia:** `references/humanizacao-discursiva.md` completo, com atenção à matriz de calibração (seção 6) para o tipo identificado.

Trabalha a performance do enunciador (como a voz se comporta na página), conforme a intensidade da matriz para o tipo:

1. **Marcadores de hesitação e modalização** — 1 a cada 300-450 palavras, perto das afirmações fortes, sem repetir o mesmo marcador.
2. **Autocorreção/reformulação** — 1 (máximo 2) autorreparo em que a segunda formulação é de fato melhor; sem duplicar fricções da Fase 3.
3. **Referência cultural ou exemplo idiossincrático** — 1 por texto, trabalhando para o argumento, sem clichê Brasil-para-export.
4. **Apartes e endereçamento** — 1-2 apartes curtos, sem informação essencial dentro deles.

**Critério de saída:** checklist da seção 7 de `humanizacao-discursiva.md`. Em tipos com intensidade 0-1 na matriz (email, corporativo, comentario-jira), esta fase é quase transparente: não force.

---

### Fase 5 — Análise macroestrutural

**Leia:** `references/estrutura-macro.md`, com atenção à matriz de calibração (seção 7) para o tipo identificado.

Trata da arquitetura do documento inteiro (as fases anteriores cuidaram da palavra e da sentença). Texto de IA tende a uma estrutura simétrica demais; desencaixe-a:

1. Rode `texto_br_estrutura` com o rascunho atual: ele mede simetria de seções, inflação de subtópicos, parágrafo-lição (kicker uniforme), frases de efeito em sequência e progressão sinalizada, compondo um score 0-100 (alvo >= 70).
2. Aplique o plano de perturbação devolvido, corrigindo os detectores mais fracos primeiro. Nunca degrade a clareza.
3. Meça de novo. Repita até "ALVO ATINGIDO" ou, no máximo, 3 iterações.

**Critério de saída:** checklist da seção 8 de `estrutura-macro.md`. Em tipos longos (blog, capitulo, tecnico, explicativo, podcast, video) o gate exige o alvo para avançar; nos demais é advisory. Conversacionais quase não têm macroestrutura: não force.

---

### Fase 6 — Entrega

Entregue **apenas** o texto final em Markdown limpo:

- Sem preâmbulos ("Aqui está...", "Segue abaixo...")
- Sem comentários após o texto
- Sem auto-elogios sobre o processo
- Sem anúncios de fases concluídas
- **Apenas o texto**

Se o usuário pedir explicitamente, mostre também o rascunho da Fase 1 (antes da humanização) para comparação. Em qualquer outro caso, mostrar a Fase 1 é violação do workflow.

Nota: esta skill foi encapsulada no servidor MCP em `server/` (tools `texto_br_*`), que é a forma de uso preferencial; este arquivo permanece como documentação do workflow.

---

## Regras absolutas que valem em todas as fases

Independente de tipo, tamanho ou contexto:

1. **Português brasileiro**, sem regionalismos lusitanos
2. **Acordo Ortográfico de 1990** aplicado (consultar `gramatica-pt-br.md` em caso de dúvida)
3. **Zero travessões (—) e zero meias-riscas (–)** — substituir sempre por outra pontuação
4. **Zero caracteres Unicode invisíveis** — varrer e remover (lista em `humanizacao-algoritmos.md` seção 9)
5. **Zero conectores da lista negra** — "Além disso", "No entanto", "Em conclusão", "Vale ressaltar" e a lista completa de `humanizacao-algoritmos.md`
6. **Zero aberturas clichê de IA** — "Em um mundo onde", "Nos dias atuais", "No cenário atual"
7. **Zero meta-referência ao próprio texto** — "neste artigo", "como veremos", "lendo até o fim"
8. **A humanização nunca degrada o texto.** Se a versão pós-humanização for pior que o rascunho original, refazer. O alvo é texto **melhor**, não apenas mais humano.

## Formato de saída padrão

- Markdown limpo
- `#` para título principal (apenas em capítulos de livro)
- `##` para seções, `###` para subseções
- `**negrito**` para destaques moderados (não exagerar)
- `*itálico*` para ênfase ou termos estrangeiros
- Listas com `-` ou `1.`
- Blocos de código com cercas de três acentos graves
- Citações com `>`
- **Sem nenhum travessão em nenhum lugar**

## Critério final de qualidade

Após a Fase 3, antes de entregar, fazer uma última pergunta interna: "Um estrangeiro inteligente que leu sobre o tema em livros, mas nunca viveu esse contexto, conseguiria ter escrito exatamente este texto?"

Se a resposta for sim, voltar à Fase 3 e aplicar as camadas profundas com mais força — especialmente aterragem (Camada 1) e ângulo (Camada 4). Texto humano deixa **biografia mínima**: traços de quem escreveu, mesmo sem identificação explícita.

A meta não é enganar detectores como fim em si. A meta é produzir **texto de qualidade humana**, que coincidentemente passa pelos detectores porque é genuinamente bom.
