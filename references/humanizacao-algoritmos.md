---
type: reference
parent_skill: texto-br
sources: arXiv (StyloAI 2024, Adversarial Paraphrasing NeurIPS 2025, CoPA 2025), GPTZero technical docs, Originality.ai analysis
scope: Algoritmos de humanização de textos gerados por LLM
target_detectors: GPTZero, ZeroGPT, Copyleaks, Originality.ai, Turnitin AI, Winston AI
---

# Algoritmos Profundos de Humanização

Referência técnica para neutralizar a detecção estatística e estilométrica de textos gerados por LLM. Baseada em literatura acadêmica revisada (NeurIPS, arXiv, ACL) e análise pública dos detectores comerciais. Consultada pela skill `texto-br` na Fase 2 do pipeline.

## Sumário

1. [Teoria da detecção](#1-teoria-da-detecção)
2. [Métricas quantitativas alvo](#2-métricas-quantitativas-alvo)
3. [As 31 features estilométricas](#3-as-31-features-estilométricas-stylometric-features)
4. [Algoritmo master de humanização](#4-algoritmo-master-de-humanização)
5. [Engenharia de perplexidade](#5-engenharia-de-perplexidade)
6. [Engenharia de burstiness](#6-engenharia-de-burstiness)
7. [Quebra de estruturas paralelas](#7-quebra-de-estruturas-paralelas)
8. [Injeção de voz humana](#8-injeção-de-voz-humana)
9. [Caracteres invisíveis e watermarks](#9-caracteres-invisíveis-e-watermarks)
10. [Substituições lexicais em pt-BR](#10-substituições-lexicais-em-pt-br)
11. [Algoritmo de verificação final](#11-algoritmo-de-verificação-final)
12. [Apêndices](#12-apêndices)

---

## 1. Teoria da detecção

SEMPRE LEIA: `references/humanização-profunda.md`

### 1.1 Arquitetura típica de um detector moderno

Detectores comerciais combinam **três camadas** de análise. Para "quebrar" a detecção, é preciso enganar as três simultaneamente — atacar só uma deixa as outras intactas.

**Camada 1 — Estatística (probabilística):**
Roda o texto por um LLM proxy (geralmente GPT-2 ou GPT-Neo) e mede a probabilidade que esse modelo atribui a cada token. Texto com tokens muito prováveis → baixa perplexidade → bandeira vermelha. Métricas usadas: perplexidade média, perplexidade por sentença, burstiness, Conditional Probability Curvature (DetectGPT).

**Camada 2 — Estilométrica (linguística):**
Extrai dezenas de features de superfície: distribuição de tamanhos de sentença, type-token ratio, hapax legomenon rate, contagem de stop words, complexidade sintática, polaridade emocional, índices de legibilidade. Treina classificadores rasos (Random Forest, XGBoost) sobre essas features. StyloAI obtém 81-98% de acurácia só com 31 features.

**Camada 3 — Neural (embeddings):**
Roda o texto por um transformer fine-tunado (RoBERTa, DeBERTa, ModernBERT) treinado em pares (humano, IA). Captura padrões que escapam às outras camadas: coesão excessiva, estruturas paralelas, ausência de erros sutis. Modelos como Fast-DetectGPT, RADAR, OpenAI-RoBERTa-Large operam aqui.

### 1.2 Por que detectores convergem

Insight crítico (Adversarial Paraphrasing, NeurIPS 2025): "_Most high-performing detectors converge toward a common distribution that characterizes human-authored text._" Ou seja: se um texto engana um detector calibrado, tende a enganar os outros, porque todos miram a mesma distribuição de "texto humano". Isso significa que **uma humanização bem-feita transfere entre detectores** — não precisa otimizar contra cada um.

### 1.3 O que distingue texto humano (síntese da literatura)

Texto humano tem, em média, todas as propriedades abaixo. Texto de LLM bruto tem o oposto. Humanizar = mover na direção das colunas da direita.

| Dimensão                                          | LLM bruto                            | Humano                                   |
| ------------------------------------------------- | ------------------------------------ | ---------------------------------------- |
| Perplexidade média                                | 20-30                                | 80-100                                   |
| Burstiness (σ/μ do tamanho de sentenças)          | 0.2-0.4                              | 0.6-1.2                                  |
| Type-token ratio (TTR)                            | uniforme, "polido"                   | variável conforme assunto                |
| Hapax legomenon rate                              | baixo                                | alto (vocabulário rico, palavras únicas) |
| Stop word ratio                                   | menor (LLM usa palavras "ricas")     | maior (humanos diluem)                   |
| Distribuição de tamanhos de sentença              | gaussiana estreita em torno de 15-20 | bimodal/cauda longa (3 a 50+)            |
| Contractions / coloquialismos                     | raros                                | frequentes                               |
| Erros tipográficos sutis                          | zero                                 | ocasionais                               |
| Tríades estruturais (3 itens)                     | sobre-representadas                  | naturais e variadas                      |
| Conectores no início de parágrafo                 | quase 100%                           | ~50-60%                                  |
| Auto-referência ("eu acho", "para mim")           | rara                                 | frequente                                |
| Polaridade emocional                              | neutra                               | variada                                  |
| Travessões (—)                                    | sobre-representados                  | raros em pt-BR informal                  |
| Vocabulário pivot ("crucial", "robusto", "delve") | sobre-representado                   | raro                                     |

---

## 2. Métricas quantitativas alvo

Use estes números como referência **operacional**. Após humanizar, o texto deveria estar dentro destas faixas se você estiver atacando todas as camadas.

### 2.1 Targets primários

| Métrica                             | Cálculo                                     | Target humano             | LLM bruto típico     |
| ----------------------------------- | ------------------------------------------- | ------------------------- | -------------------- |
| **Perplexidade média**              | exp(−1/N · Σ log p(tᵢ)) onde p vem de GPT-2 | 60-120                    | 15-35                |
| **Burstiness**                      | σ(comprimentos) / μ(comprimentos)           | 0.6-1.2                   | 0.15-0.40            |
| **Type-Token Ratio (TTR)**          | UniqueWords / TotalWords                    | 0.45-0.65 (textos médios) | 0.35-0.50 (uniforme) |
| **Hapax Legomenon Rate**            | WordsAppearingOnce / TotalWords             | 0.40-0.55                 | 0.25-0.40            |
| **Stop Word Ratio**                 | StopWords / TotalWords                      | 0.42-0.55                 | 0.35-0.45            |
| **Avg Sentence Length**             | TotalWords / TotalSentences                 | 12-22                     | 17-22 (estreito)     |
| **Sentence Length StdDev**          | σ(comprimentos por sentença)                | 8-15                      | 3-6                  |
| **Contraction Count / 1000 words**  | nº contrações                               | 8-20                      | 0-3                  |
| **First-Person Count / 1000 words** | "eu", "minha", "meu", "comigo"              | 5-25 (varia)              | 0-5                  |
| **Question Count / 1000 words**     | interrogações                               | 2-8                       | 0-2                  |
| **Em-dash (—) Count**               | nº de travessões                            | 0-1 / 1000 palavras       | 5-20 / 1000 palavras |

### 2.2 Targets secundários (verificação)

| Métrica                             | Target                           |
| ----------------------------------- | -------------------------------- |
| Paragraphs starting with connector  | < 60%                            |
| Triads (lists with exactly 3 items) | < 30% das listas                 |
| Polarity StdDev                     | > 0.15 (varia ao longo do texto) |
| Syntactic Variety (POS tag entropy) | > 2.5                            |
| Bigram Uniqueness                   | > 0.85                           |

---

## 3. As 31 features estilométricas (StyloAI)

Fonte: Opara, _StyloAI: Distinguishing AI-Generated Content with Stylometric Analysis_ (2024). Detectores Random Forest atingem 98% de acurácia só com elas. Para cada feature, indicamos como o LLM bruto se comporta e como mover para o lado humano.

### 3.1 Lexical (6 features)

| Feature                | Como LLM se comporta               | Direção humana                       | Tática                                 |
| ---------------------- | ---------------------------------- | ------------------------------------ | -------------------------------------- |
| WordCount              | varia                              | varia                                | irrelevante                            |
| UniqueWordCount        | baixo (vocabulário repetitivo)     | alto                                 | injetar sinônimos menos óbvios         |
| CharCount              | varia                              | varia                                | irrelevante                            |
| AvgWordLength          | levemente maior (palavras "ricas") | menor (mais monossílabos funcionais) | usar mais "que", "se", "de", "o", "a"  |
| **TTR**                | uniforme                           | variável                             | quebrar uniformidade lexical           |
| **HapaxLegomenonRate** | baixo                              | alto                                 | trocar repetições por sinônimos únicos |

### 3.2 Syntactic (12 features)

| Feature                         | LLM bruto                           | Direção humana | Tática                                                       |
| ------------------------------- | ----------------------------------- | -------------- | ------------------------------------------------------------ |
| SentenceCount                   | regular                             | varia          | varia                                                        |
| **AvgSentenceLength**           | 17-22 (estreito)                    | distribuído    | misturar frases de 3 a 40+ palavras                          |
| PunctuationCount                | médio                               | alto           | usar mais vírgula, ponto, interrogação                       |
| StopWordCount                   | baixo                               | alto           | não evitar "o", "a", "que", "de", "para"                     |
| AbstractNounCount               | alto                                | menor          | preferir verbos a substantivações                            |
| **ComplexVerbCount**            | alto (verbos "sofisticados")        | menor          | trocar "implementar" por "fazer", "demonstrar" por "mostrar" |
| **SophisticatedAdjectiveCount** | alto (terminações -ivo, -oso, -ico) | variado        | misturar com adjetivos comuns                                |
| AdverbCount                     | baixo                               | médio          | adicionar advérbios em -mente com moderação                  |
| ComplexSentenceCount            | médio-alto                          | varia          | misturar com frases simples curtas                           |
| QuestionCount                   | baixo (0-1)                         | médio (2-8/1k) | injetar perguntas retóricas                                  |
| ExclamationCount                | quase zero                          | variável       | uma ou duas exclamações naturais                             |
| **ContractionCount**            | zero a baixíssimo                   | alto           | usar contrações naturais do português                        |

⚠️ **Português brasileiro tem menos contrações tipográficas que inglês**, mas tem: _dum, duma, dumas, num, numa, numas, pra (informal), pro (informal), prum, pruma, daí, donde, dele, dela, deste, desta, disso, dessa, dele, daquele, naquele, nessa_. Use em registro informal.

### 3.3 Sentiment & Subjectivity (4 features)

| Feature          | LLM bruto                | Direção humana          | Tática                               |
| ---------------- | ------------------------ | ----------------------- | ------------------------------------ |
| EmotionWordCount | baixo                    | médio-alto              | adicionar palavras emotivas naturais |
| Polarity         | próximo de zero (neutro) | varia ao longo do texto | introduzir opiniões locais           |
| Subjectivity     | baixa                    | média-alta              | usar "acho", "parece", "creio"       |
| VaderCompound    | uniforme                 | variável                | variar tom entre seções              |

### 3.4 Readability (2 features)

| Feature           | LLM bruto                              | Direção humana |
| ----------------- | -------------------------------------- | -------------- |
| FleschReadingEase | médio (50-60)                          | varia          |
| GunningFog        | alto (nível universitário consistente) | varia          |

**Tática geral**: alternar entre passagens densas (Gunning Fog alto) e passagens diretas (Flesch alto). Evitar uniformidade no nível de leitura.

### 3.5 Named Entities (4 features)

| Feature                | LLM bruto     | Direção humana | Tática                                               |
| ---------------------- | ------------- | -------------- | ---------------------------------------------------- |
| **FirstPersonCount**   | 0-5/1k        | 5-25/1k        | adicionar "eu", "minha", "para mim" onde couber      |
| **DirectAddressCount** | baixo         | médio          | endereçar o leitor: "você sabe", "olha só", "repare" |
| PersonEntities         | baixo         | varia          | citar pessoas específicas se contextual              |
| DateEntities           | vago, redondo | específico     | "em março de 2019" em vez de "recentemente"          |

### 3.6 Uniqueness (3 features)

| Feature                     | LLM bruto                  | Direção humana | Tática                                   |
| --------------------------- | -------------------------- | -------------- | ---------------------------------------- |
| **Bigram Uniqueness**       | baixo (n-gramas repetidos) | alto           | quebrar colocações típicas de LLM        |
| **Trigram Uniqueness**      | baixo                      | alto           | reescrever sequências de 3+ palavras     |
| SyntaxVariety (POS entropy) | baixo                      | alto           | variar ordem sintática (SVO → OSV, etc.) |

⚠️ **As 4 features mais discriminantes** (Random Forest feature importance, StyloAI): `UniqueWordCount`, `StopWordCount`, `TTR`, `HapaxLegomenonRate`. Atacar essas quatro é prioridade absoluta.

---

## 4. Algoritmo master de humanização

Pipeline de **5 passos sequenciais**. Executar em ordem. Cada passo aceita texto e retorna texto modificado. Não pular, não combinar.

### Passo 0: Limpeza de caracteres invisíveis

Remover **todos** os caracteres Unicode invisíveis que LLMs podem inserir (potenciais watermarks):

```
U+200B (Zero Width Space)
U+200C (Zero Width Non-Joiner)
U+200D (Zero Width Joiner)
U+2060 (Word Joiner)
U+FEFF (Zero Width No-Break Space / BOM)
U+00AD (Soft Hyphen)
U+180E (Mongolian Vowel Separator)
U+202A-U+202E (Bidi controls)
U+2061-U+2064 (Invisible math operators)
```

Normalizar também:

- `—` (U+2014, em-dash) → vírgula, dois-pontos, ponto, ou parêntese conforme contexto
- `–` (U+2013, en-dash) → idem
- `…` (U+2026) → `...` (três pontos comuns) — opcional
- `"` `"` (U+201C, U+201D) → `"` `"` (aspas retas) — opcional, mais comum em contextos técnicos
- `'` `'` (U+2018, U+2019) → `'` — opcional
- Espaços não-quebráveis `U+00A0` → espaço comum `U+0020`

### Passo 1: Reescrita lexical (atacar perplexidade)

Para cada sentença, identificar 1-3 palavras de **alta probabilidade** (que um LLM colocaria com facilidade) e substituir por **sinônimos menos óbvios mas naturais**. Não inflar com vocabulário rebuscado; o objetivo é _quebrar a previsibilidade_, não impressionar.

**Heurística de seleção**:

- Substantivos abstratos genéricos ("aspecto", "questão", "fator") → termos concretos
- Adjetivos pivot de LLM ("robusto", "crucial", "fundamental") → adjetivos comuns ou descrição
- Verbos formais ("realizar", "implementar", "estabelecer") → verbos diretos ("fazer", "montar", "criar")

Exemplo (antes → depois):

> "É fundamental destacar que a implementação robusta de processos é crucial para o sucesso da organização."

→

> "Repara: montar processos sólidos importa muito pra empresa dar certo."

A segunda frase tem perplexidade ~3-4x maior porque "repara", "montar", "sólidos", "importa", "dar certo" não são as escolhas estatisticamente óbvias.

### Passo 2: Reestruturação sintática (atacar burstiness)

Pegar o texto e **reorganizar sentenças** para criar variação extrema de comprimento. Regra prática:

- A cada 3 sentenças, deve haver pelo menos uma curta (≤ 8 palavras) e uma longa (≥ 25 palavras)
- Nenhuma sequência de 4 sentenças consecutivas com tamanhos similares (variação < 30%)
- Pode quebrar sentença longa em duas curtas via ponto. Pode juntar duas curtas em uma longa via vírgula ou conjunção.

**Padrões de ritmo a injetar**:

| Padrão            | Estrutura                                                                           | Efeito                 |
| ----------------- | ----------------------------------------------------------------------------------- | ---------------------- |
| Staccato          | curta. curta. curta.                                                                | quebra previsibilidade |
| Crescendo         | curta. média, com cláusula. longa, com várias cláusulas e desenvolvimento de ideia. | imita pensamento       |
| Inversão          | longa, longa, longa. Curta.                                                         | ênfase em frase final  |
| Pergunta-resposta | "E por que isso? Por preguiça."                                                     | dialógico              |

### Passo 3: Quebra de estruturas paralelas e tríades

LLMs **adoram** estruturar em 3:

- 3 motivos
- 3 exemplos
- 3 itens em lista
- Introdução, desenvolvimento, conclusão simétricos

**Ação**: contar todas as listas e enumerações do texto. Se mais de 30% têm exatamente 3 itens, **ajustar**:

- Algumas listas com 2 itens
- Algumas com 4 ou 5
- Algumas com 7
- Ocasional lista única ("uma coisa importa: X")

Outras quebras:

- Se 3 parágrafos começam com conectivo, remover de pelo menos 1
- Se a estrutura é intro-3 pontos-conclusão simétrica, mesclar dois pontos ou trocar a ordem
- Se todos os subtítulos seguem mesmo padrão, variar formato (alguns com ":", alguns com pergunta, alguns afirmativos)

### Passo 4: Injeção de voz humana

Adicionar marcadores de subjetividade e presença autoral conforme o tipo de texto permite.

**Marcadores de primeira pessoa** (use sparingly):

- "Acho que", "na minha visão", "para mim", "do meu ponto de vista"
- "Já vi isso acontecer", "tenho a impressão", "me parece"

**Endereçamento ao leitor**:

- "Repare", "olha só", "veja bem", "imagina a cena"
- "Você já deve ter percebido", "sabe quando..."

**Hesitações controladas**:

- Parênteses como pensamento paralelo: "A produtividade (e aqui vale a ressalva) depende do contexto."
- Reformulação: "Isso é importante. Ou melhor: isso é fundamental."

**Coloquialismos brasileiros** (apenas em tipos informais — blog, podcast, vídeo):

- "Tem hora que", "vale a pena", "dá pra ver"
- "Aí é que está", "acontece que", "só que"
- "No fim das contas", "no frigir dos ovos"
- "Tipo assim", "meio que" (com moderação)

**Anedotas e especificidades**:

- Trocar generalizações por casos concretos
- "Estudos mostram" → "Em 2019, um experimento de Stanford mostrou"
- "Muitas pessoas" → "Conheço três pessoas que..."

⚠️ Não exagerar. Texto humano não tem opinião em TODA sentença. Em texto corporativo formal, voz humana fica **sutil**: usar "acho" uma única vez, manter terceira pessoa no resto.

### Passo 5: Verificação e ajuste fino

Rodar o checklist da [Seção 11](#11-algoritmo-de-verificação-final). Se alguma métrica está fora do target, reaplicar o passo correspondente naquela parte do texto.

---

## 5. Engenharia de perplexidade

### 5.1 O que é perplexidade

Perplexidade mede quão "surpreso" um modelo de linguagem fica com o próximo token. Formalmente:

```
PP(W) = exp(-1/N · Σᵢ log P(wᵢ | w₁...wᵢ₋₁))
```

Onde P é dado por um modelo de referência (geralmente GPT-2). Texto com tokens muito prováveis para o modelo → P alto → log P pequeno (perto de 0) → PP baixa.

LLMs modernos otimizam justamente para escolher tokens com P alto. Resultado: textos com PP **muito baixa** (15-35), enquanto humanos batem 60-120.

### 5.2 Técnicas para aumentar perplexidade

**Técnica A — Substituição lexical de baixa frequência**
Trocar palavras de alta frequência (top 1000 do português) por sinônimos de média frequência (rank 5000-20000), mantendo naturalidade.

Exemplo:

- "importante" → "decisivo", "valioso", "que pega"
- "rápido" → "ligeiro", "num átimo", "ágil"
- "começar" → "abrir", "estrear", "dar partida"

**Técnica B — Construções idiomáticas**
Expressões fixas têm probabilidade alta DENTRO da expressão, mas a expressão em si pode ser de baixa probabilidade de ser escolhida. Trocar paráfrase neutra por expressão idiomática brasileira:

- "muito difícil" → "osso duro de roer", "bicho de sete cabeças"
- "facilmente" → "numa boa", "sem suar"
- "rapidamente" → "num piscar de olhos", "ligeiro"
- "muito" → "pra caramba", "à beça"

**Técnica C — Inversão sintática**
Português permite ordens não-canônicas que LLMs usam pouco:

- "Isso eu não sabia." (objeto antes do sujeito)
- "Bonita a casa dela." (sujeito posposto)
- "Pouco importa o resultado." (advérbio inicial)

**Técnica D — Quebrar colocações**
Colocações são pares de palavras que aparecem juntas com alta frequência ("ampla discussão", "profundo conhecimento", "grande importância"). LLMs amam colocações. Quebrar:

- "ampla discussão" → "conversa que se estendeu", "debate que cobriu muita coisa"
- "profundo conhecimento" → "saber bem das coisas", "domínio do assunto"

**Técnica E — Pontuação atípica**
Pontos finais em lugares não-óbvios criam quebras de previsibilidade:

- "Funciona. Mais ou menos."
- "Concordamos. Em parte."
- "A ideia é simples. Executar, nem tanto."

### 5.3 Sentenças "calmas" vs "agitadas"

Cada sentença tem sua perplexidade. **Não é necessário** todas terem PP alta — distribuir é melhor. Em texto humano, há sentenças "calmas" (PP baixa, transições normais) intercaladas com "agitadas" (PP alta, escolhas surpreendentes). Burstiness aplicada à perplexidade.

---

## 6. Engenharia de burstiness

### 6.1 Definição operacional

Burstiness = σ(L) / μ(L), onde L é a lista dos comprimentos (em palavras) de cada sentença.

Texto humano: 0.6-1.2.
LLM bruto: 0.2-0.4.

Para mover um texto de 0.3 para 0.8, é preciso **aumentar drasticamente o desvio padrão** sem mexer (muito) na média.

### 6.2 Algoritmo prático

1. **Tokenizar** o texto em sentenças (por `.`, `?`, `!`).
2. **Contar** o comprimento (palavras) de cada sentença → lista L.
3. **Calcular** μ(L) e σ(L). Se σ/μ < 0.5, intervir.
4. **Identificar** sentenças no entorno da média (μ ± 30%) → essas são as candidatas a serem **quebradas** ou **fundidas**.
5. **Quebrar** algumas em 2 ou 3 (criar sentenças muito curtas).
6. **Fundir** outras com vizinhas via vírgula ou conjunção (criar sentenças muito longas).
7. **Recalcular**. Repetir até σ/μ ≥ 0.7.

### 6.3 Padrões de ritmo "humanos"

Padrões observados em corpora de blog e prosa literária brasileira:

```
Padrão 1 (revelação): [longa] [curta-impacto]
Exemplo: "A meditação melhora foco, regula sono, reduz ansiedade, fortalece imunidade e ajuda no relacionamento com colegas e parceiros. Pena que ninguém faz."

Padrão 2 (cascata): [curta] [média] [longa]
Exemplo: "Comecei ontem. Achei tedioso. Mas no terceiro dia, alguma coisa mudou — uma sensação de que o mundo não estava acelerado, só eu é que estava."

Padrão 3 (eco): [curta] [longa] [curta] [longa] [curta]
Exemplo: "Funciona. Funciona porque, no fim, o cérebro aprende a esperar um momento de pausa todos os dias. Funciona. Como qualquer outro hábito, mas sem a recompensa imediata que vicia o restante. Simples."

Padrão 4 (declaração + qualificação): [muito curta] [longa]
Exemplo: "Errei. Não na escolha do tema, mas na execução, na sequência dos parágrafos, na ordem em que apresentei os argumentos centrais."
```

### 6.4 Mistura de tipos de sentença

Variar não só o comprimento, mas o **tipo**:

- Declarativa: "O mercado fechou em alta."
- Interrogativa: "Por que isso importa?"
- Exclamativa: "Que estranho!"
- Imperativa: "Imagine essa cena."
- Optativa: "Tomara que dê certo."
- Fragmento (sem verbo principal): "Difícil de explicar."

---

## 7. Quebra de estruturas paralelas

### 7.1 Tríades

LLMs treinados em texto de alta qualidade incorporam o "regra de três" da retórica clássica. Resultado: tríades em todo lugar.

**Diagnóstico**: contar quantas listas e enumerações têm exatamente 3 itens. Se > 30%, intervir.

**Intervenção**:

- Algumas listas → 2 itens: "duas coisas: X e Y"
- Algumas → 4 ou 5 itens: "quatro fatores: A, B, C e D"
- Algumas → 7 itens (parecem mais "exaustivas"): listar tudo que vier
- Algumas → 1 item: "uma única coisa importa: X"

### 7.2 Estrutura intro-desenvolvimento-conclusão

LLMs estruturam texto como ensaio escolar: 1 parágrafo de introdução, N parágrafos paralelos de desenvolvimento, 1 parágrafo de conclusão.

**Quebras possíveis**:

- Começar in medias res (no meio da ideia): "Não foi assim que tudo começou."
- Final aberto, sem síntese explícita
- Pular a introdução, ir direto ao ponto
- Conclusão como pergunta, não como afirmação

### 7.3 Paralelismo de parágrafos

LLMs frequentemente fazem parágrafos do mesmo tamanho, todos começando com tópico-frase. Quebrar:

- Misturar parágrafos longos com parágrafos de uma linha
- Algum parágrafo começando com diálogo, exclamação, ou conjunção
- Parágrafo de transição muito curto: "Mas voltemos ao ponto."

### 7.4 Coesão excessiva

LLMs colam tudo com conectivos no início de cada parágrafo ("Além disso", "Por outro lado", "Adicionalmente"). Texto humano frequentemente justapõe ideias sem marcador explícito.

**Regra**: nenhuma sequência de 3 parágrafos consecutivos deve começar com conectivo lógico. Se acontece, remover de pelo menos um e deixar a justaposição falar por si.

---

## 8. Injeção de voz humana

### 8.1 Marcadores de subjetividade

Calibrar pela formalidade do tipo de texto:

| Tipo              | Voz pessoal | Marcadores aceitos                                       |
| ----------------- | ----------- | -------------------------------------------------------- |
| Blog informal     | alta        | "acho", "na minha", "para mim", "olha", "repara"         |
| Artigo técnico    | média       | "no nosso experimento", "observamos", "minha leitura é"  |
| Texto corporativo | baixa       | "entendemos", "na nossa visão" (3ª pessoa institucional) |
| E-mail            | baixa-média | "fico à disposição", "me coloco para esclarecer"         |
| Capítulo de livro | varia       | tudo permitido, depende do narrador                      |
| Podcast           | altíssima   | linguagem oral pura, hesitações, "né?", "tipo"           |
| Vídeo             | altíssima   | "olha só", "presta atenção", "você vai ver que"          |
| Explicativo       | média       | "vamos pensar juntos", "imagine que"                     |

### 8.2 Especificidades concretas

Trocar vagueza por concretude:

- "muitas pessoas" → "três colegas meus", "75% dos brasileiros segundo o IBGE"
- "recentemente" → "no mês passado", "em março de 2024"
- "estudos mostram" → "o estudo de Diener (2002) mostrou"
- "em alguns lugares" → "em Curitiba e Florianópolis"

Atenção: **não inventar** dados específicos. Se não souber a fonte exata, deixar vago é melhor que mentir.

### 8.3 Imperfeições naturais

Texto humano tem **pequenas imperfeições** que LLMs corrigem automaticamente. Reinjetar com moderação (uma ou duas, não mais):

- Repetição intencional de palavra para ênfase: "Funciona. Funciona mesmo."
- Frases começadas com "E", "Mas", "Aí", "Só que" (proibido em redação escolar formal, comum em texto real)
- Anacoluto leve (mudança de construção): "O João, eu vi ele ontem."
- Reformulação no meio: "A questão é que — ou melhor, a questão era que..."

### 8.4 Marcadores discursivos brasileiros

Distintivos do português brasileiro escrito informal:

- "Tipo", "tipo assim", "meio que"
- "Sei lá", "vai saber", "vai entender"
- "Né", "né não" (final de frase)
- "Aí", "daí" (conector narrativo)
- "Tá", "tá ligado" (muito informal)
- "Cara", "mano", "véi" (gíria; só em textos muito informais)

⚠️ Calibrar pelo público-alvo. Texto corporativo NÃO leva "tipo assim".

---

## 9. Caracteres invisíveis e watermarks

### 9.1 O problema

LLMs podem inserir caracteres Unicode invisíveis (zero-width, joiners, soft hyphens) que funcionam como **assinatura digital** persistente. Mesmo após parafrasear o texto, esses caracteres podem permanecer se o input do parafraseador for o texto bruto da IA.

Originality.AI confirma: "_ChatGPT does use several Unicode hidden characters a lot (such as the Em Dash)_."

### 9.2 Caracteres a remover

Lista completa de caracteres a varrer e remover:

| Unicode        | Nome                            | Razão                        |
| -------------- | ------------------------------- | ---------------------------- |
| U+200B         | Zero Width Space                | watermark suspeito           |
| U+200C         | Zero Width Non-Joiner           | watermark suspeito           |
| U+200D         | Zero Width Joiner               | watermark suspeito           |
| U+2060         | Word Joiner                     | watermark suspeito           |
| U+FEFF         | Zero Width No-Break Space / BOM | artefato de encoding         |
| U+00AD         | Soft Hyphen                     | invisível, frequente em LLMs |
| U+180E         | Mongolian Vowel Separator       | invisível                    |
| U+202A-E       | Bidi controls                   | invisíveis, podem confundir  |
| U+2061-4       | Invisible math operators        | invisíveis                   |
| U+034F         | Combining Grapheme Joiner       | invisível                    |
| U+115F, U+1160 | Hangul Filler                   | invisíveis                   |
| U+17B4, U+17B5 | Khmer vowel inherent            | invisíveis                   |
| U+3164         | Hangul Filler                   | invisível                    |
| U+FFA0         | Halfwidth Hangul Filler         | invisível                    |

### 9.3 Caracteres a substituir

| Original                                | Substituir por                            | Quando                       |
| --------------------------------------- | ----------------------------------------- | ---------------------------- |
| `—` (U+2014, em-dash)                   | vírgula, dois-pontos, ponto, ou parêntese | sempre (sinal #1 de IA)      |
| `–` (U+2013, en-dash)                   | hífen comum `-` ou outra pontuação        | sempre                       |
| `―` (U+2015, horizontal bar)            | substituição contextual                   | sempre                       |
| `…` (U+2026, ellipsis)                  | `...` três pontos comuns                  | opcional                     |
| `"` `"` (U+201C/D, smart quotes)        | `"` aspas retas                           | em código, opcional em texto |
| `'` `'` (U+2018/9, smart single quotes) | `'` aspas retas simples                   | em código, opcional em texto |
| `′` `″` (U+2032/3, prime marks)         | `'` `"` aspas                             | sempre                       |
| `«` `»` (U+00AB/BB, guillemets)         | aspas duplas comuns                       | em texto pt-BR               |
| `\u00A0` (NBSP)                         | espaço comum                              | sempre                       |
| `\u2007` (Figure Space)                 | espaço comum                              | sempre                       |
| `\u2009` (Thin Space)                   | espaço comum                              | sempre                       |
| `•` (U+2022, bullet)                    | `-` (hífen) ou `*` em markdown            | opcional                     |

### 9.4 Algoritmo de varredura

Em pseudocódigo:

```
def clean(text):
    invisible = ['\u200B', '\u200C', '\u200D', '\u2060', '\uFEFF',
                 '\u00AD', '\u180E', '\u034F',
                 '\u202A', '\u202B', '\u202C', '\u202D', '\u202E',
                 '\u2061', '\u2062', '\u2063', '\u2064']
    for ch in invisible:
        text = text.replace(ch, '')

    text = text.replace('\u2014', ', ')  # contextual: em-dash → vírgula
    text = text.replace('\u2013', '-')   # en-dash → hífen
    text = text.replace('\u2026', '...') # ellipsis
    text = text.replace('\u201C', '"').replace('\u201D', '"')
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u00A0', ' ')   # NBSP
    text = text.replace('\u2007', ' ')
    text = text.replace('\u2009', ' ')

    return text
```

⚠️ A substituição de `—` por `, ` é simplificação. O ideal é análise de contexto (ver Seção 10.3).

---

## 10. Substituições lexicais em pt-BR

### 10.1 Verbos pivot de LLM

| Evitar       | Trocar por                                   |
| ------------ | -------------------------------------------- |
| realizar     | fazer, executar, levar a cabo                |
| implementar  | aplicar, montar, pôr em prática, fazer rodar |
| estabelecer  | criar, definir, montar, fixar                |
| desempenhar  | fazer, exercer, tocar                        |
| utilizar     | usar                                         |
| demonstrar   | mostrar, provar, deixar claro                |
| evidenciar   | mostrar, deixar à mostra, expor              |
| caracterizar | marcar, definir, ter a cara de               |
| viabilizar   | tornar possível, abrir caminho para          |
| alavancar    | usar a favor, puxar                          |
| fomentar     | empurrar, estimular, dar corda a             |
| propiciar    | dar, abrir espaço para                       |
| contemplar   | levar em conta, abranger, cobrir             |
| abordar      | tratar de, falar de, encarar                 |
| explorar     | examinar, ver de perto, investigar           |
| compreender  | abranger, incluir, abarcar                   |
| envolver     | incluir, ter                                 |
| permitir     | deixar                                       |
| possibilitar | permitir, deixar                             |
| garantir     | assegurar, dar certeza                       |
| aprimorar    | melhorar, refinar, aperfeiçoar               |
| ressaltar    | destacar, frisar, lembrar                    |
| salientar    | destacar, lembrar                            |
| destacar     | apontar, marcar                              |
| reforçar     | confirmar, ratificar (com moderação)         |
| corroborar   | confirmar, sustentar                         |
| mensurar     | medir                                        |
| dimensionar  | medir, calcular                              |
| otimizar     | melhorar, ajustar, afinar                    |
| tecer        | fazer, criar, montar                         |
| mergulhar em | entrar em, ir fundo em, encarar              |
| navegar por  | percorrer, atravessar, passar por            |
| desvendar    | descobrir, abrir, esclarecer                 |

### 10.2 Adjetivos pivot

| Evitar                   | Trocar por                                 |
| ------------------------ | ------------------------------------------ |
| robusto                  | sólido, firme, forte, completo             |
| crucial                  | decisivo, central, chave                   |
| pivotal                  | central, decisivo, definidor               |
| fundamental (em excesso) | importante, central, básico                |
| imprescindível           | obrigatório, necessário, sem o qual não dá |
| significativo            | importante, grande, notável                |
| considerável             | grande, expressivo, alto                   |
| substancial              | grande, forte, considerável                |
| relevante                | importante, que pesa                       |
| pertinente               | que cabe, oportuno                         |
| holístico                | completo, abrangente, que pega o todo      |
| sinérgico                | combinado, conjunto                        |
| multifacetado            | de várias facetas, complexo                |
| paradigmático            | exemplar, modelar                          |
| intricado                | complicado, difícil, emaranhado            |
| meticuloso               | cuidadoso, detalhista                      |
| inovador (em excesso)    | novo, diferente, inédito                   |
| disruptivo               | que quebra padrão, que vira a mesa         |
| transformador            | que muda tudo                              |
| revolucionário           | que muda o jogo                            |
| estratégico (em excesso) | calculado, planejado                       |

### 10.3 Substantivos pivot

| Evitar                         | Trocar por                          |
| ------------------------------ | ----------------------------------- |
| panorama                       | cenário, situação, quadro, paisagem |
| paradigma                      | modelo, jeito de pensar, padrão     |
| sinergia                       | encaixe, combinação                 |
| ecossistema (fora de biologia) | conjunto, ambiente, mundo           |
| jornada (fora de viagem)       | trajeto, caminho, processo          |
| insight                        | sacada, descoberta, percepção       |
| mindset                        | mentalidade, jeito de pensar        |
| framework                      | esquema, modelo, jeito              |
| stakeholders                   | partes envolvidas, interessados     |
| deliverables                   | entregas, resultados                |
| outputs                        | saídas, resultados                  |
| momentum                       | impulso, embalo                     |
| roadmap                        | plano, mapa, rota                   |
| tapestry                       | tecido (raro em pt-BR), trama       |
| underpinning                   | base, alicerce                      |
| testament                      | prova, evidência                    |
| beacon                         | farol, sinal                        |
| realm                          | área, domínio, terreno              |
| landscape                      | cenário, paisagem                   |

### 10.4 Conectores pivot

| Evitar                | Trocar por (ou cortar)                         |
| --------------------- | ---------------------------------------------- |
| Além disso            | E, Outra coisa, Some-se, Tem mais              |
| No entanto            | Mas, Só que, Acontece que, Aí é que está       |
| Por outro lado        | Já, Agora, Por outro ângulo                    |
| Em conclusão          | (cortar) No fim das contas, No frigir dos ovos |
| Em suma               | (cortar) Resumindo                             |
| Em resumo             | (cortar) Resumindo                             |
| Vale ressaltar        | (cortar) Repare                                |
| É importante destacar | (cortar) Olha                                  |
| Vale lembrar          | (cortar) Lembrando                             |
| Cabe mencionar        | (cortar) Vale dizer                            |
| Dessa forma           | Assim, Com isso, (cortar)                      |
| Sendo assim           | Então, Aí                                      |
| Por fim               | No fim, (cortar)                               |
| Dito isso             | (cortar) Pois bem                              |
| Posto isso            | (cortar)                                       |
| Ademais               | (cortar) E                                     |
| Outrossim             | (cortar) (arcaísmo)                            |
| Não obstante          | Mas, Mesmo assim                               |
| Em virtude de         | Por causa de, Devido a                         |
| No que tange a        | Sobre, Quanto a                                |
| No que diz respeito a | Sobre, Quanto a                                |
| À luz de              | Considerando, À vista de                       |
| Por conseguinte       | Logo, Portanto, Aí                             |
| Mediante              | Por meio de, Com                               |

### 10.5 Aberturas pivot

LLMs adoram começar texto com frases-clichê. **Sempre cortar e começar de outro jeito**:

| Evitar                         | Alternativa             |
| ------------------------------ | ----------------------- |
| Em um mundo onde...            | (começar pelo concreto) |
| Nos dias atuais...             | (idem)                  |
| No cenário atual/contemporâneo | (idem)                  |
| Na era digital                 | (idem)                  |
| Atualmente, vivemos            | (idem)                  |
| Em meio a                      | (idem)                  |
| Diante do                      | (idem)                  |
| No contexto contemporâneo      | (idem)                  |
| Cada vez mais                  | (idem)                  |
| Não é segredo que              | (idem)                  |
| É de conhecimento geral        | (idem)                  |
| Sabe-se que                    | (idem)                  |

**Boas aberturas humanas**:

- Imagem concreta: "Era um sábado de manhã, e o café tinha esfriado."
- Pergunta direta: "Você já reparou que..."
- Afirmação contraintuitiva: "Trabalhar menos pode produzir mais."
- Anedota: "Conheci um cara, em 2017, que..."
- Dado específico: "47% dos brasileiros..."
- Diálogo: "'Não dá', ele disse."

### 10.6 Fechamentos pivot

| Evitar                 | Alternativa      |
| ---------------------- | ---------------- |
| Em conclusão...        | (cortar a frase) |
| Em suma...             | (idem)           |
| Por todo o exposto     | (idem)           |
| Como vimos             | (idem)           |
| Em síntese             | (idem)           |
| Espero ter contribuído | (cortar)         |
| Espero ter ajudado     | (cortar)         |

**Bons fechamentos humanos**:

- Volta à imagem inicial (mas modificada)
- Pergunta aberta deixada para o leitor
- Anedota final
- Conselho direto: "Comece amanhã."
- Frase curta de impacto: "É isso."

---

## 11. Algoritmo de verificação final

Checklist obrigatório antes de entregar. Cada item é uma verificação. Se falhar, voltar à seção correspondente.

### 11.1 Verificações quantitativas

```
[ ] Avg sentence length entre 12 e 22?
[ ] Sentence length StdDev > 8?
[ ] Burstiness (σ/μ) >= 0.7?
[ ] TTR entre 0.45 e 0.65?
[ ] Hapax legomenon rate > 0.40?
[ ] Stop word ratio > 0.42?
[ ] Pelo menos 1 sentença < 8 palavras a cada 3 parágrafos?
[ ] Pelo menos 1 sentença > 25 palavras a cada 2 parágrafos (em textos longos)?
[ ] Contractions > 5 por 1000 palavras (em texto informal)?
[ ] First person count > 5 por 1000 palavras (em texto pessoal)?
```

### 11.2 Verificações de pontuação/caracteres

```
[ ] Zero ocorrências de — (em-dash, U+2014)?
[ ] Zero ocorrências de – (en-dash, U+2013)?
[ ] Zero caracteres invisíveis (\u200B, \u200C, \u200D, \u2060, \uFEFF, \u00AD)?
[ ] Aspas verificadas (retas ou curvas, mas consistentes)?
[ ] Espaços não-quebráveis (\u00A0) substituídos?
```

### 11.3 Verificações lexicais (lista negra)

```
[ ] Zero ocorrências de: "Além disso", "No entanto", "Por outro lado",
    "Em conclusão", "Em suma", "Em resumo", "Vale ressaltar",
    "É importante destacar", "Vale lembrar", "Cabe mencionar",
    "Dessa forma", "Sendo assim", "Por fim", "Dito isso"?
[ ] Zero aberturas tipo "Em um mundo onde", "Nos dias atuais", "No cenário atual"?
[ ] "Robusto", "crucial", "pivotal", "tecer", "mergulhar em", "desvendar",
    "navegar por", "panorama", "paradigma", "sinergia", "alavancar",
    "fomentar", "plenamente", "meticulosamente" → no máximo UMA ocorrência
    cada, em texto de até 2000 palavras?
```

### 11.4 Verificações estruturais

```
[ ] Listas com exatamente 3 itens são menos de 30% do total de listas?
[ ] Nenhuma sequência de 3 parágrafos consecutivos começa com conectivo lógico?
[ ] Parágrafos têm tamanhos variados (variação > 40% no comprimento)?
[ ] Estrutura intro-desenvolvimento-conclusão não é estritamente simétrica?
[ ] Pelo menos uma pergunta retórica ou inversão sintática em texto de 500+ palavras?
```

### 11.5 Verificações de gramática

```
[ ] Acordo Ortográfico de 1990 aplicado (consultar gramatica-pt-br.md)?
[ ] Acentuação correta (não é só sem acento — é com os acentos certos)?
[ ] Crase verificada onde aplicável?
[ ] Concordância verbal e nominal corretas?
[ ] Regência correta (preferir X a Y, assistir AO filme, chegar AO local)?
[ ] Sem erros artificiais introduzidos pela humanização?
```

### 11.6 Verificação final de qualidade

```
[ ] O texto ainda preserva o significado e os fatos do briefing?
[ ] O tom é adequado ao tipo de texto (não brasileiro coloquial em texto corporativo)?
[ ] Não há gírias ou regionalismos inadequados ao público-alvo?
[ ] A formatação Markdown está limpa (headers, listas, citações)?
[ ] O texto se sustenta como peça de escrita boa, independente de detecção?
```

⚠️ **Critério crítico de qualidade**: humanização não deve **degradar** o texto. Se um leitor humano achar o texto pior depois da humanização, algo está errado. O target ideal é texto **melhor** após humanização — mais natural, mais ritmado, mais vivo.

---

## 12. Apêndices

### Apêndice A: Algoritmo "Contrastive Paraphrase" (Wang et al., 2025)

Insight do paper _Contrastive Paraphrase Attacks on LLM-Generated Text Detectors_ (arXiv:2505.15337):

Em vez de só parafrasear, comparar **duas distribuições** durante a reescrita:

1. P_humano(token) — modelo treinado em texto humano
2. P_LLM(token) — modelo LLM padrão

A cada token, escolher o que maximiza `log P_humano(t) − log P_LLM(t)`, ou seja, o token que é provável para humanos **mas improvável para LLMs**.

Versão simplificada para uso manual: ao escrever, pergunte "qual a palavra que um humano escolheria aqui que um LLM provavelmente NÃO escolheria?" — esse é o vetor humanizador.

### Apêndice B: Algoritmo "Adversarial Paraphrasing" (Chen et al., NeurIPS 2025)

Insight do paper (arXiv:2506.07001):

Durante a reescrita, em cada token, consultar um detector como guia. Escolher entre os top-k tokens propostos pelo parafraseador aquele que minimiza a probabilidade de classificação como "AI" pelo detector.

Resultado reportado: reduz T@1%F (true positive rate at 1% false positive) em 87.88% em média entre detectores.

Versão prática: depois de escrever, passar pelo detector e usar o highlight de sentenças "suspeitas" para reescrever apenas essas. Não reescrever tudo.

### Apêndice C: Cheat Sheet — sequência rápida

Para humanizar um texto em 10 passos (ordem importa):

1. **Limpar** caracteres invisíveis Unicode e travessões.
2. **Substituir** todos os conectores da lista negra ([Seção 10.4](#104-conectores-pivot)).
3. **Trocar** aberturas e fechamentos clichê ([Seções 10.5-10.6](#105-aberturas-pivot)).
4. **Reescrever** verbos, adjetivos e substantivos pivot ([Seções 10.1-10.3](#101-verbos-pivot-de-llm)).
5. **Variar comprimento** de sentenças (alvo burstiness >= 0.7).
6. **Quebrar** tríades e estruturas paralelas.
7. **Injetar** voz humana conforme o tipo de texto.
8. **Adicionar** especificidades concretas (datas, nomes, números reais).
9. **Verificar** gramática e Acordo Ortográfico 1990.
10. **Rodar** checklist da [Seção 11](#11-algoritmo-de-verificação-final).

### Apêndice D: Lista exaustiva de marcadores de IA (compilação)

**Palavras-bandeira (Walter Writes 2026, análise de 100k textos GPT-4)**:
delve, leverage, utilize, harness, streamline, underscore, robust, pivotal, crucial, innovative, seamless, cutting-edge, landscape, realm, tapestry, synergy, testament, underpinnings, furthermore, moreover, consequently, notably, importantly, plethora, myriad, profound, intricate, multifaceted, transformative, paradigm, holistic, navigate, embark, foster, cultivate, mitigate, facilitate, encompass, exemplify, elucidate, ascertain.

**Equivalentes em português brasileiro**:
mergulhar em, alavancar, utilizar, aproveitar, otimizar, sublinhar, robusto, pivotal, crucial, inovador, integrado, ponta, panorama, esfera, tecido, sinergia, prova, alicerces, ademais, outrossim, consequentemente, notavelmente, importante, plétora, miríade, profundo, intricado, multifacetado, transformador, paradigma, holístico, navegar, embarcar, fomentar, cultivar, mitigar, facilitar, abranger, exemplificar, elucidar, certificar.

**Bigramas e expressões fixas reveladoras**:
"é importante ressaltar", "vale a pena observar", "convém destacar", "no que diz respeito", "no que tange", "torna-se evidente", "cumpre observar", "à luz de", "em virtude de", "em decorrência de", "no contexto de", "na medida em que", "diante do exposto", "por todo o exposto", "em última análise".

### Apêndice E: Referências acadêmicas

- Opara, C. (2024). _StyloAI: Distinguishing AI-Generated Content with Stylometric Analysis_. arXiv:2405.10129.
- Chen, Y. et al. (2025). _Adversarial Paraphrasing: A Universal Attack for Humanizing AI-Generated Text_. NeurIPS 2025. arXiv:2506.07001.
- Wang, H. et al. (2025). _Your Language Model Can Secretly Write Like Humans: Contrastive Paraphrase Attacks_. arXiv:2505.15337.
- Mitchell, E. et al. (2023). _DetectGPT: Zero-Shot Machine-Generated Text Detection using Probability Curvature_. ICML 2023.
- Zaitsu, W. & Jin, M. (2023). _Distinguishing ChatGPT-generated and human-written papers through Japanese stylometric analysis_. PLoS ONE.
- Sarvazyan, A.M. et al. (2023). _Overview of AuTexTification at IberLEF 2023_. SEPLN.
- Kumarage, T. et al. (2023). _Stylometric Detection of AI-Generated Text in Twitter Timelines_. arXiv:2303.03697.
- GPTZero Technical Documentation (2023-2025). _Perplexity and Burstiness: Technical Methodology_.
- Originality.AI (2025). _Invisible Text Detector and Hidden Unicode Analysis_.
- Max Planck Institute (2024). _Lexical Imprinting of LLMs on Human Writing_.

---

## Nota de uso

Este documento é referência para a Fase 2 (humanização) da skill `texto-br`. Sempre consultar em conjunto com `gramatica-pt-br.md` para garantir que as substituições preservam a norma culta brasileira.

A humanização nunca deve degradar a qualidade técnica, informacional ou gramatical do texto. Se um leitor humano achar o texto pior depois da humanização, recomeçar.

A meta não é "enganar detectores" como fim em si — é produzir **texto de qualidade humana**, que coincidentemente passa pelos detectores porque é genuinamente bom.
