---
type: reference
parent_skill: texto-br
sources: Grosz & Sidner 1986, CoUDA 2024 (arXiv:2404.00681), Align to Structure 2025 (arXiv:2504.03622), Halliday & Hasan 1976
scope: Humanização semântica profunda — quatro camadas estruturais que persistem após humanização de superfície
---

# Camadas Profundas de Humanização

Referência operacional para a humanização em nível semântico — o que fica **depois** que perplexidade, burstiness, travessões e clichês lexicais já foram tratados. Esta é a camada que detectores neurais modernos (Fast-DetectGPT, RADAR) capturam, e que leitores humanos atentos sentem mesmo quando não sabem nomear.

A regra mental que organiza tudo aqui: **texto de IA parece escrito por um estrangeiro inteligente que leu sobre o tema em livros — sabe tudo de forma correta e abstrata, mas nunca pisou ali**. As quatro camadas atacam exatamente esse padrão.

## Quando consultar este documento

- Texto já passou pelas correções de superfície (vocabulário, conectores, burstiness) e ainda soa "polido demais", "panorâmico", "sem dono"
- Detector aponta sentenças como "vague", "generic", "lacks personal context"
- Leitor humano comenta que o texto "parece escrito por consultor de fora"
- Antes de finalizar texto de produção longo (blog, capítulo, podcast, ensaio)

## Quando NÃO aplicar

- Texto curto conversacional (chat, comentário de Jira simples) — o contexto da conversa já faz o trabalho
- Texto formal corporativo/jurídico onde fricção declarada e ângulo individual destroem autoridade
- Quando o texto já foi naturalmente escrito por humano (não há o que aterrar)

---

## Sumário

1. [Camada referencial — Aterragem](#1-camada-referencial--aterragem)
2. [Camada sensorial — Detalhe único](#2-camada-sensorial--detalhe-único)
3. [Camada epistêmica — Fricção](#3-camada-epistêmica--fricção)
4. [Camada posicional — Ângulo](#4-camada-posicional--ângulo)
5. [Coerência local vs global](#5-coerência-local-vs-global)
6. [Matriz de calibração por tipo de texto](#6-matriz-de-calibração-por-tipo-de-texto)
7. [Checklist de verificação](#7-checklist-de-verificação)
8. [Referências](#8-referências)

---

## 1. Camada referencial — Aterragem

**O problema.** LLM, por minimização de risco, prefere o universal ao particular. "No Brasil inteiro", "muitas pessoas", "recentemente", "em algum momento". A generalização protege o modelo de errar e simultaneamente apaga o que faz o texto soar humano: a âncora.

**O princípio.** Toda generalização vaga (lugar, tempo, quantidade, agente) deve ser substituída por **âncora concreta**, mesmo que inventada (ficção) ou plausível (ensaio sem dado exato). Generalizações são dívida do texto: pagar antes de entregar.

### Categorias a aterrar

| Vago                 | Aterrado                                                       |
| -------------------- | -------------------------------------------------------------- |
| no Brasil            | em Belo Horizonte, na minha cidade, na casa da minha avó       |
| muitas pessoas       | três amigos meus, 40% dos brasileiros (IBGE 2022), meu vizinho |
| recentemente         | no mês passado, em março, na quarta-feira                      |
| há algum tempo       | em 2017, há uns 6 anos                                         |
| uma pessoa           | um sujeito de óculos, a senhora do caixa, o motoboy            |
| em algum lugar       | num bar perto do metrô Sé, na esquina da Augusta               |
| de vez em quando     | umas duas vezes por mês, todo segundo domingo                  |
| em algumas situações | quando chove, quando o servidor cai, quando ele bebe           |

### Como aterrar por tipo de texto

- **Ficção, crônica, blog pessoal:** inventar âncora plausível. "A casa da minha avó em Maringá" funciona mesmo que a avó/cidade não existam — o que importa é a textura referencial.
- **Ensaio, explicativo, técnico:** aterrar com dado verificável OU declarar explicitamente o limite ("não tenho número exato, mas..."). Declarar é mais humano que generalizar com falsa autoridade.
- **Corporativo, jurídico:** aterrar institucionalmente — "no nosso setor de logística", "nos clientes do varejo", "no projeto Aurora" — em vez de "na empresa" ou "no mercado".

### Anti-padrão: meta-referência

Auto-referência ao próprio texto é assinatura de blog-IA. Cortar sempre:

- "neste artigo"
- "como veremos"
- "ao longo deste post"
- "lendo este texto até o fim"
- "vou te mostrar a seguir"
- "ao final desta leitura"
- "como discutiremos"

Substituir por âncora externa ou simplesmente remover.

### Exemplo

> ❌ "Tem uma cena que se repete em jantares pelo Brasil inteiro."
>
> ✅ "Tem uma cena que se repete na casa da minha sogra, em Maringá, todo segundo domingo do mês."

### Limite operacional

- Máximo **2 generalizações vagas sobreviventes por 500 palavras** em texto de produção
- **Zero meta-referências** ao próprio texto

---

## 2. Camada sensorial — Detalhe único

**O problema.** LLM tende a empilhar 3-5 atributos sensoriais quando descreve qualquer coisa: "uma taça pequena, gelada, com um líquido amarelo brilhante que perfuma a mesa antes mesmo de ser provado". Cada atributo é correto, todos são esperados — a soma é entrega clara de IA. Humanos escolhem **um** detalhe estranho e deixam o resto implícito.

**O princípio.** Máximo de **2 atributos sensoriais consecutivos** antes de quebrar com outro movimento (ação, reflexão, diálogo, transição). Dos atributos disponíveis, escolher o **mais idiossincrático** — o que só quem viveu a cena conheceria. Cortar os redundantes.

### Como escolher o detalhe único

Entre os atributos possíveis, manter o que:

1. é mais **inesperado** dado o objeto
2. tem origem **memorial específica** (cheiro de algo do passado, cor que lembra outra coisa)
3. envolve um **sentido menos óbvio** (olfato, paladar, tato — não só visão)
4. é **funcionalmente útil** à cena (a frieza importa porque a taça suava)

### Verbos sensoriais clichês — evitar

Templates de marketing/IA que entregam o padrão:

- exala
- perfuma (no sentido de "espalhar aroma")
- dança no paladar
- desperta os sentidos
- envolve em aroma
- encanta o olhar
- conquista pelo aroma
- seduz pelo sabor

Substituir por verbos diretos: "cheira a", "tem gosto de", "lembra cheiro de X", "lembra sabor de X".

### Exemplo

> ❌ "uma taça pequena, gelada, com um líquido amarelo brilhante que perfuma a mesa antes mesmo de ser provado"
>
> ✅ "uma taça pequena, gelada, com um líquido que cheira a casca de limão queimada"

A versão aterrada manteve **dois** atributos (pequena, gelada — funcionais) e substituiu três genéricos por **um** idiossincrático (cheira a casca de limão queimada). O cheiro específico é improvável de ser gerado por LLM e sinaliza memória vivida.

### Limite operacional

- **Zero ocorrências** de empilhamento ≥ 3 atributos sensoriais consecutivos
- Em descrições de cena, ao menos **1 atributo idiossincrático** que não seja genérico

---

## 3. Camada epistêmica — Fricção

**O problema.** LLM apresenta tudo com **confiança uniforme**. Nenhuma frase admite que não sabe, nenhuma se contradiz com a anterior, nenhuma muda de ideia. Isso não é só estranho — é anti-humano. Pensar é se contradizer, hesitar, mudar de ideia.

**O princípio.** Texto humano de qualidade tem **fricção epistêmica**: momentos onde o autor admite o que não sabe, considera o contrário, reformula, muda de posição, ou simplesmente hesita. Injetar de forma controlada — não como ruído gratuito, mas como marca de pensamento real.

### Tipos de fricção epistêmica

| Tipo                        | Exemplo                                             |
| --------------------------- | --------------------------------------------------- |
| Admissão de ignorância      | "Não sei dizer ao certo por quê."                   |
| Contradição contida         | "Funciona. Quase sempre."                           |
| Reformulação mid-frase      | "A questão é — ou melhor, era — outra."             |
| Concessão genuína           | "Pode ser que eu esteja errado."                    |
| Dúvida sobre o próprio dado | "Vi isso num estudo, mas não lembro qual."          |
| Mudança de ideia explícita  | "Achei isso por anos. Mês passado, mudei de ideia." |
| Hesitação operacional       | "Sei lá. Acho que sim, acho que não."               |
| Qualificação posterior      | "Importante, sim. Mas com asterisco."               |

### Anti-padrão: fricção performática

Simulacro de fricção que soa **ainda mais IA**:

- "todos sabemos que é complexo"
- "essa é uma questão multifacetada"
- "como tudo na vida, depende"
- "há prós e contras"

Fricção real é **específica**: o que exatamente não sei, onde mudei de ideia, onde estou inseguro. Genérico não conta.

### Por que funciona contra detectores

Detectores neurais foram treinados em texto de IA com alta confiança e texto humano com hesitação natural. Fricção epistêmica move o texto para a distribuição humana — exatamente o tipo de sinal que Fast-DetectGPT e RADAR capturam pela curvatura de probabilidades.

### Exemplo

> ❌ "É isso que um bom licor faz. Exige curiosidade e uns poucos princípios que dá pra dominar lendo este texto até o fim."
>
> ✅ "É isso que um licor decente faz, quando faz. Porque metade dos licores caseiros que provei ao longo da vida eram bem ruins, e eu não vou fingir que sei a fórmula. Aprendi uns princípios. Eles ajudam."

A versão aterrada acrescentou: admissão de variabilidade ("quando faz"), contradição contida (metade era ruim), admissão de não saber tudo, declaração modesta no fim.

### Limite operacional

- **Ao menos 1 marcador de fricção epistêmica a cada 300 palavras** em texto de produção
- **Zero ocorrências** de fricção performática genérica
- **Não aplicar** em e-mail formal, texto jurídico, comunicação corporativa de autoridade

---

## 4. Camada posicional — Ângulo

**O problema.** Texto de IA é **panorâmico**. Cobre o tema dos vários ângulos, equilibra perspectivas, evita ofender qualquer leitor potencial. Resultado: texto sem dono. Texto humano de qualidade tem **ângulo** — alguém escreveu, com posição, formação, preconceitos, paixões. Você sente, lendo, quem está por trás.

**O princípio.** Todo texto humano deixa traços do autor: geração, região, classe, profissão, gostos, irritações. Não precisa ser explícito — precisa **existir como camada implícita** no que o texto escolhe enfatizar, no que ignora, no tom, nas referências.

### Componentes do ângulo

| Componente                     | Como aparece                                                  |
| ------------------------------ | ------------------------------------------------------------- |
| Posição declarada              | "Eu acho que X é melhor que Y."                               |
| Preconceito assumido           | "Tenho preguiça de discussões abstratas sobre Z."             |
| Paixão por algo específico     | "Vinho do Porto velho, isso sim merece reverência."           |
| Irritação genuína              | "O que me irrita é quando as pessoas misturam X com Y."       |
| Referência cultural específica | "É tipo o que o Caetano fez em Transa, mas no avesso."        |
| Marca geracional               | piada, referência, gíria que data o autor                     |
| Marca regional                 | regionalismo lexical, referência geográfica específica        |
| Marca profissional             | jargão técnico em contexto preciso, frame mental da profissão |

### Calibração por formalidade

- **Texto pessoal** (blog, capítulo, podcast): ângulo individual e mais explícito
- **Texto corporativo/jurídico:** ângulo institucional — a empresa tem ângulo, não o autor. "Na nossa visão, X é o caminho."

### Anti-padrão: equilíbrio performático

Fuga de posição que soa IA:

- "Há prós e contras de ambos os lados."
- "Cada caso é um caso."
- "Depende do contexto."

Texto humano declara posição mesmo quando é "ambíguo": "acho que tende mais pra X, embora não tenha certeza".

### Exemplo

> ❌ "Sobremesa é um terreno difícil para qualquer bebida. Cada bebida tem suas características que podem ou não combinar com diferentes tipos de sobremesa."
>
> ✅ "Sobremesa é terreno traiçoeiro pra qualquer bebida. Vinho doce em geral é uma desgraça com chocolate, por exemplo — não me venham com Porto + brigadeiro, porque eu já provei e não cola."

A versão com ângulo tem: convicção declarada ("uma desgraça"), exemplo específico (Porto + brigadeiro), referência cultural, irritação genuína ("não me venham com"), evidência pessoal ("eu já provei").

### Limite operacional

- **Ao menos 1 marca explícita de ângulo em texto de 500+ palavras** (posição declarada, paixão, irritação)
- Em texto opinativo: várias marcas
- Em texto corporativo: ao menos uma marca **institucional** ("nossa abordagem", "no nosso entendimento")
- **Zero ocorrências** de equilíbrio performático

---

## 5. Coerência local vs global

**Insight (Grosz & Sidner 1986; CoUDA 2024).** Coerência discursiva tem dois níveis. **Global** é a coerência do texto inteiro com seu tema central (organização macro). **Local** é a transição fluida entre frases consecutivas (centramento de atenção, retomada de referentes).

### Comportamento contrastante

**LLMs:**

- Coerência global: excelente. Mantém o tópico, não foge do assunto, conclui voltando ao começo.
- Coerência local: frágil. Transições entre frases seguem padrões de conectivo previsíveis ("Além disso", "Por outro lado") ou justaposição neutra.

**Humanos:**

- Coerência global: menos perfeita. Digredem, voltam, mudam de assunto e retornam. Parágrafos podem mudar de tema antes do esperado.
- Coerência local: mais forte. Cada frase responde sensorialmente, emocionalmente ou logicamente à anterior, mesmo sem conectivo explícito.

### Como inverter o padrão

1. **Permitir digressões pequenas** em textos longos (parágrafo lateral que parece sair do tema e volta)
2. **Fortalecer transições locais** removendo conectivos previsíveis, usando retomada de termo, eco sensorial, ou pergunta retórica
3. **Aceitar** que a estrutura macro do texto não precise ser perfeitamente simétrica

### Exemplo de transição local fortalecida

> ❌ "A meditação reduz o estresse. Além disso, melhora o sono. Por outro lado, exige disciplina."
>
> ✅ "A meditação reduz estresse. Reduz sono ruim também — é o efeito mais imediato que sentei pra observar em mim mesmo. Disciplina, sim. Disciplina é o problema."

A versão aterrada substituiu conectivos por retomada lexical ("reduz... reduz"), introduziu marca de autor ("sentei pra observar em mim mesmo") e usou eco ("Disciplina, sim. Disciplina é o problema") em vez de "Por outro lado".

### Exemplo de digressão controlada

> [parágrafo principal sobre produtividade em home office]
>
> ✅ "...e aqui entra uma coisa que parece besteira mas não é: a luz da janela. Em janeiro, com sol nas costas, eu produzo o dobro. Em julho, com céu cinza paulistano, produzo metade. Anota aí. Voltando ao ponto principal: ..."

A digressão sobre luz/clima parece lateral, mas adiciona textura humana que LLM não geraria de forma natural. O retorno explícito ("Voltando ao ponto principal") sinaliza pensamento real, não roteiro.

### Limite operacional

- Em texto de **1000+ palavras: ao menos 1 digressão controlada** que sai do trilho e volta
- Em texto curto, transições locais fortes substituem digressão

---

## 6. Matriz de calibração por tipo de texto

Nem todas as quatro camadas se aplicam a todos os tipos. Aplicar fora de contexto **prejudica** o resultado. Em e-mail corporativo, fricção epistêmica e ângulo opinativo podem destruir a autoridade da mensagem. Em chat, aterragem referencial é redundante.

| Tipo              | Aterragem        | Detalhe único | Fricção epistêmica | Ângulo posicional  |
| ----------------- | ---------------- | ------------- | ------------------ | ------------------ |
| `blog`            | ★★★              | ★★★           | ★★★                | ★★★                |
| `tecnico`         | ★★★              | ★★            | ★★                 | ★★                 |
| `corporativo`     | ★★               | ★             | ★ (institucional)  | ★★ (institucional) |
| `email`           | ★★               | ★             | ☆ (evitar)         | ★ (institucional)  |
| `capitulo`        | ★★★              | ★★★           | ★★★                | ★★★                |
| `podcast`         | ★★★              | ★★            | ★★★                | ★★★                |
| `video`           | ★★               | ★★            | ★★                 | ★★★                |
| `explicativo`     | ★★★              | ★★            | ★★                 | ★★                 |
| `geral`           | adaptar          | adaptar       | adaptar            | adaptar            |
| `comentario-blog` | ★★               | ★             | ★★                 | ★★★                |
| `comentario-jira` | ★★★ (técnica)    | ☆             | ★ (precisão)       | ★ (técnico)        |
| `chat`            | ★ (contexto faz) | ☆             | ★                  | ★                  |

**Legenda:** ★★★ aplicar com força · ★★ aplicar moderado · ★ aplicar leve · ☆ não aplicar.

### Notas por tipo

- **`blog`, `capitulo`, `podcast`:** as quatro camadas com força máxima — é onde texto de IA mais entrega o padrão e onde humanização profunda mais paga.
- **`tecnico`:** aterragem máxima (citar versão, ferramenta, contexto técnico específico); detalhe único moderado (não é texto sensorial); fricção moderada (admitir trade-offs é humano e correto); ângulo moderado (mostrar opinião técnica é OK).
- **`corporativo`:** aterragem institucional (nome de projeto, área, métrica); detalhe único raro; fricção apenas institucional ("estamos avaliando", "ainda não temos certeza sobre"); ângulo é da empresa, não do autor.
- **`email`:** fricção epistêmica **evitar** — destrói autoridade. Aterragem moderada (citar contexto: "como combinamos na 1:1 de terça"). Detalhe único raro.
- **`comentario-jira`:** aterragem máxima na dimensão técnica (versão, PR, commit, ambiente). As outras camadas quase ausentes — é registro de trabalho, não prosa.
- **`chat`:** já é naturalmente humano por contexto. Aplicar levemente, sem sobre-engenheirar. O risco é o oposto: aplicar humanização profunda em mensagem curta de chat destrói o registro.

**Regra prática.** Quanto **mais informal e longo** o tipo, **mais força** nas quatro camadas. Quanto **mais formal ou conversacional curto**, mais leve.

---

## 7. Checklist de verificação

Antes de entregar texto que passou pelas quatro camadas, conferir:

```
[ ] Generalizações vagas (lugar/tempo/quantidade/agente sem nome)
    são ≤ 2 por 500 palavras?

[ ] Zero meta-referências ao próprio texto ("neste artigo", "como veremos",
    "lendo até o fim")?

[ ] Zero empilhamentos de 3+ atributos sensoriais consecutivos?

[ ] Descrições de cena incluem ao menos 1 atributo idiossincrático
    (não-genérico)?

[ ] Zero verbos sensoriais clichês ("exala", "perfuma", "dança no paladar",
    "desperta os sentidos")?

[ ] Ao menos 1 marcador de fricção epistêmica genuína a cada 300 palavras
    (conforme aplicabilidade do tipo)?

[ ] Zero ocorrências de fricção performática ("todos sabemos que é
    complexo", "depende do contexto", "cada caso é um caso")?

[ ] Ao menos 1 marca de ângulo do autor em texto de 500+ palavras
    (posição, paixão, irritação, referência cultural específica)?

[ ] Zero ocorrências de equilíbrio performático ("há prós e contras
    de ambos os lados")?

[ ] Transições locais fortes (retomada lexical, eco, pergunta) em
    vez de conectivos previsíveis?

[ ] Em texto de 1000+ palavras: ao menos 1 digressão controlada que
    sai do trilho e volta?

[ ] Um leitor humano atento sentiria que há "alguém por trás" do texto?
```

**Critério final.** Se ao reler o texto humanizado você ainda sente que "qualquer estrangeiro inteligente que tivesse lido sobre o tema poderia ter escrito isso", as quatro camadas não foram aplicadas com força suficiente. Texto humano deixa **biografia mínima** — traços de quem escreveu, mesmo sem se identificar.

---

## 8. Referências

- Grosz, B. & Sidner, C. (1986). _Attention, Intentions, and the Structure of Discourse_. Computational Linguistics 12(3). — Fundamento da distinção local/global de coerência discursiva.
- Wu, X. et al. (2024). _CoUDA: Coherence Evaluation via Unified Data Augmentation_. arXiv:2404.00681. — Aplicação contemporânea da teoria de Grosz & Sidner a detecção de coerência em LLMs.
- Liu, H. et al. (2025). _Align to Structure: Aligning Large Language Models with Structural Information_. arXiv:2504.03622. — Mostra que LLMs precisam de alinhamento explícito para igualar estrutura discursiva humana.
- Halliday, M.A.K. & Hasan, R. (1976). _Cohesion in English_. Longman. — Clássico fundamental sobre coesão textual; base teórica do que LLMs ainda não replicam bem.

---

## Nota final

A meta não é "enganar detectores" como fim em si — é produzir **texto de qualidade humana**, que coincidentemente passa pelos detectores porque é genuinamente bom. As quatro camadas existem porque texto verdadeiramente humano não é só **escrito de jeito humano** — é **pensado de jeito humano**: com âncora, com detalhe vivido, com dúvida, com dono.
