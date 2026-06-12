---
type: reference
parent_skill: texto-br
sources: Atlassian Jira documentation, Lullabot Jira best practices, Slack official guidelines, Mode Analytics Slack handbook, Grammarly professional writing, analysis of high-engagement blog comments
scope: Especificações operacionais por tipo de texto, incluindo formatos conversacionais para interação no mundo real
---

# Tipos de Texto — Referência Operacional

Especificação detalhada dos 12 tipos de texto suportados pela skill `texto-br`. Cada tipo inclui: contexto de uso, estrutura, tamanho típico, registro de formalidade, marcadores estilísticos específicos, exemplos comentados, e armadilhas comuns.

A skill consulta este documento para calibrar voz, estrutura e formato — depois aplica humanização (`humanizacao-algoritmos.md`) e correção gramatical (`gramatica-pt-br.md`).

## Sumário

**Tipos de produção (conteúdo autoral):**

1. [Artigo para blog](#1-artigo-para-blog) — `blog`
2. [Artigo técnico](#2-artigo-técnico) — `tecnico`
3. [Texto corporativo](#3-texto-corporativo) — `corporativo`
4. [E-mail corporativo](#4-e-mail-corporativo) — `email`
5. [Capítulo de livro](#5-capítulo-de-livro) — `capitulo`
6. [Roteiro de podcast](#6-roteiro-de-podcast) — `podcast`
7. [Roteiro de vídeo](#7-roteiro-de-vídeo) — `video`
8. [Texto explicativo](#8-texto-explicativo) — `explicativo`
9. [Texto geral](#9-texto-geral) — `geral`

**Tipos conversacionais (interação no mundo real):** 10. [Comentário em blog](#10-comentário-em-blog) — `comentario-blog` 11. [Comentário no Jira](#11-comentário-no-jira) — `comentario-jira` 12. [Resposta de chat](#12-resposta-de-chat) — `chat`

---

## Princípios gerais aplicáveis a todos os tipos

Antes de mergulhar nas especificações, alguns invariantes:

**Sobre formalidade.** Cada tipo tem uma faixa esperada de formalidade (1 = bate-papo de amigo, 5 = documento jurídico). Sair da faixa quebra o registro e estraga o resultado mesmo com gramática perfeita.

**Sobre tamanho.** Comprimento errado é tão problemático quanto tom errado. Comentário de blog de 1500 palavras é ruim. Capítulo de livro de 300 palavras também é ruim.

**Sobre estrutura.** Cada tipo tem uma estrutura esperada pelo leitor. Quebrar essa estrutura sem motivo confunde. Quebrar com motivo (e habilidade) cria efeito.

**Sobre voz.** Quanto mais informal e conversacional o tipo, mais voz pessoal cabe. Quanto mais formal, mais a voz se dilui em institucionalidade.

**Sobre humanização.** Tipos conversacionais (chat, comentários) já tendem a parecer humanos por natureza — a humanização é mais leve. Tipos de produção (artigos longos) precisam de mais trabalho ativo de humanização porque LLMs são muito treinados nesse formato.

---

## 1. Artigo para Blog

**ID:** `blog`
**Formalidade:** 2-3 (informal a meio-formal)
**Tamanho típico:** 600-1500 palavras
**Tempo de leitura alvo:** 4-8 minutos

### Contexto de uso

Artigo de blog é leitura voluntária. O leitor escolheu clicar e pode sair a qualquer momento. Tudo conspira contra você: notificações, outras abas, pressa, ceticismo. O texto precisa ganhar atenção a cada parágrafo.

### Estrutura recomendada

```
# Título (curto, com promessa concreta ou tensão)

[Lead — primeira frase ou parágrafo que prende: pergunta,
afirmação contraintuitiva, cena, dado específico]

[Desenvolvimento em 2-5 seções com ## H2]

[Cada seção pode ter ### H3 se necessário]

[Fechamento — reflexão, CTA, ou volta à imagem inicial]
```

### Marcadores estilísticos

- **Pronome:** "você" direto, frequente
- **Perguntas retóricas:** 2-4 ao longo do texto
- **Frases curtas de impacto:** misturadas com longas
- **Listas:** apenas quando agregam clareza, não por moda
- **Subtítulos:** funcionais, não meramente decorativos
- **Citações:** ocasionais, sempre com fonte
- **Bold:** para destacar termos-chave em parágrafos longos

### Aberturas que funcionam

- Pergunta direta: "Você já se pegou refrescando o e-mail às 23h sem motivo?"
- Cena específica: "Era um sábado de manhã quando percebi que o problema não era o app."
- Afirmação contraintuitiva: "Trabalhar menos pode ser a coisa mais produtiva que você faz hoje."
- Anedota: "Conheço um designer que ganha bem por uma coisa só: ele atende o telefone."
- Dado específico: "47% das pessoas que começam uma rotina de exercícios desistem em 90 dias. Tem motivo."

### Aberturas a evitar

Toda fórmula de IA: "Em um mundo onde", "Nos dias atuais", "No cenário contemporâneo", "Na era digital", "É de conhecimento geral", "Sabe-se que", "Cada vez mais", "Atualmente vivemos".

### Fechamentos que funcionam

- CTA específico e factível: "Tenta isso amanhã: durante 25 minutos, sem celular."
- Pergunta deixada em aberto para o leitor pensar
- Volta à imagem da abertura, agora com outro sentido
- Frase curta que sintetiza tudo: "É isso."

### Armadilhas

- Listas com 3 itens em todo lugar (tríades clichês de IA)
- Conectores no início de cada parágrafo
- Conclusão começando com "Em resumo" ou "Por todo o exposto"
- Densidade alta de adjetivos pivot ("robusto", "fundamental", "crucial")

### Exemplo de abertura humanizada

> # Por que sua to-do list não funciona (e o que fazer no lugar)
>
> Tem uma cena que se repete. Domingo à noite, eu pego o caderno, listo 17 coisas para fazer na segunda. Segunda chega, faço quatro. Algumas das quatro nem estavam na lista. As outras 13 vão pro caderno da semana seguinte.
>
> Já viveu isso?
>
> Acontece com quase todo mundo. E não é falha de disciplina. É falha de design.

---

## 2. Artigo Técnico

**ID:** `tecnico`
**Formalidade:** 3-4
**Tamanho típico:** 800-2000 palavras
**Tempo de leitura alvo:** 6-15 minutos

### Contexto de uso

O leitor de artigo técnico tem motivo concreto: resolver um problema, aprender ferramenta, decidir entre alternativas. Tolera densidade maior que blog comum, mas pune jargão sem explicação e conclusões sem evidência.

### Estrutura recomendada

````
# Título técnico claro (problema + abordagem ou apenas conceito)

[Lead — problema concreto, contexto técnico, motivação]

## Contexto / Problema
[O quê e por quê]

## Solução / Abordagem
[Como, com detalhes técnicos]

```código
exemplo de código quando aplicável
```

## Exemplo prático / Implementação

[Mão na massa]

## Considerações / Limitações

[Quando não funciona, trade-offs]

## Conclusão

[Síntese curta, próximos passos]

````

### Marcadores estilísticos

- **Vocabulário técnico correto:** explicado na primeira ocorrência
- **Código:** em blocos com linguagem especificada
- **Diagramas:** quando ajudam (descrever em ASCII se necessário)
- **Referências:** links para docs oficiais, papers, RFCs
- **Versionamento:** indicar versão de ferramentas/libs
- **Pronome:** "nós" (do autor + leitor explorando juntos) ou "você"

### Aberturas que funcionam

- Problema concreto que motivou o artigo: "Na semana passada, nosso pipeline de CI quebrou por causa de um detalhe do Docker que eu não conhecia."
- Pergunta técnica específica: "Por que `useEffect` roda duas vezes em desenvolvimento?"
- Definição clara seguida de contexto: "PostgreSQL VACUUM é mais que limpeza — é parte central do MVCC. E entender isso muda como você modela escrita pesada."

### Armadilhas técnicas

- "Mergulhar em" qualquer coisa
- Listas de "5 benefícios" sem nuance
- Generalizações sem fonte ("Estudos mostram que...")
- Código sem contexto (de onde vem, o que faz)
- Conclusão genérica tipo "espero que esse artigo tenha ajudado"

### Tom específico

Confiante mas não arrogante. Reconhecer trade-offs. Mostrar pensamento, não só resultado. "Tentei X primeiro, deu errado por causa de Y, então fui pra Z."

---

## 3. Texto Corporativo

**ID:** `corporativo`
**Formalidade:** 4
**Tamanho típico:** 300-1200 palavras
**Tempo de leitura alvo:** 3-8 minutos

### Contexto de uso

Comunicação interna ou externa de empresa: posicionamento sobre tema, anúncio de mudança, relatório, posicionamento institucional. Lê quem precisa, não quem quer. Brevidade e clareza são moeda forte.

### Estrutura recomendada

```

[Título objetivo ou linha de assunto]

[Parágrafo de abertura: contexto + pergunta/problema/anúncio
em 2-4 frases]

[Desenvolvimento em parágrafos curtos, cada um com uma ideia]

[Fechamento: próximo passo concreto, prazo se aplicável,
contato para dúvidas]

```

### Marcadores estilísticos

- **Voz:** terceira pessoa institucional ("a empresa", "a equipe") ou primeira do plural ("entendemos", "vamos")
- **Parágrafos curtos:** 2-4 frases cada
- **Sem floreio:** ir direto ao ponto
- **Dados concretos:** números, datas, nomes específicos
- **Tom:** profissional mas humano, evitar tom legalista

### Jargão corporativo a evitar

`sinergia`, `alavancar`, `robusto`, `holístico`, `mindset`, `deliverable`, `stakeholders` (use "partes envolvidas" ou seja específico: "clientes", "investidores", "fornecedores"), `roadmap`, `pipeline` (fora de tech), `disruptivo`, `transformacional`, `nos próximos passos`, `dado o exposto`.

### O que substitui

Em texto corporativo, palavras simples soam mais profissionais que palavras importadas:
- "sinergia" → "trabalho conjunto", "combinação de forças"
- "alavancar" → "usar a favor", "aproveitar"
- "robusto" → "sólido", "completo"
- "stakeholders" → "clientes e parceiros" (seja específico)
- "deliverable" → "entrega", "produto final"

### Armadilhas

- Tom legalista quando não precisa
- Frases longas com cinco subordinadas
- Tríades simétricas em todo lugar
- "Reforçamos nosso compromisso" e variações
- Encerramento "agradecemos a compreensão" automático

### Exemplo

> ## Mudança no horário do escritório a partir de janeiro
>
> A partir de 6 de janeiro, o escritório passa a funcionar das 9h às 18h, com almoço entre 12h e 13h. A decisão veio de uma pesquisa com 78% de adesão entre os colaboradores.
>
> O que muda na prática:
>
> - Horário de entrada: até 9h30 (havia tolerância até 10h)
> - Almoço fixo: 12h às 13h (era flexível)
> - Saída: 18h (era 19h)
>
> Quem precisar de exceção pode falar com o gestor direto. Dúvidas sobre o impacto em benefícios: financeiro@empresa.com.

---

## 4. E-mail Corporativo

**ID:** `email`
**Formalidade:** 3-4
**Tamanho típico:** 50-300 palavras
**Tempo de leitura alvo:** 30-90 segundos

### Contexto de uso

E-mail é assíncrono e arquivado. Quem lê pode ser uma pessoa ou uma cadeia inteira. Pode ser lido no celular entre reuniões. Tem que ser claro à primeira passada.

### Estrutura fixa

```

Assunto: [Linha objetiva, com palavra-chave de ação se houver]

Olá [Nome], (ou "Prezado(a) [Nome]," para formal)

[Parágrafo 1: contexto + pedido/informação principal,
direto, sem rodeio]

[Parágrafo 2-3: detalhes necessários, se houver]

[CTA explícito ou próximo passo, se aplicável]

[Despedida cordial],
[Seu nome]

```

### Linha de assunto

A linha de assunto é metade do trabalho. Não usar:
- "Olá" / "Oi" / sem assunto
- Frases muito longas
- "Importante!" / "Urgente!" (a menos que seja de verdade)

Usar:
- Ação esperada: "Aprovação necessária — proposta cliente X"
- Tópico + contexto: "Reunião quinta — agenda preliminar"
- Pergunta direta: "Podemos remarcar a call de sexta?"

### Tom por hierarquia

- **Para chefe direto ou cliente:** "Olá Maria,", profissional + cordial
- **Para par:** "Oi João,", mais leve
- **Para subordinado:** "Olá time,", clareza máxima
- **Primeiro contato externo:** "Prezado(a) [Nome],", formal
- **Resposta em thread:** pode pular saudação após a primeira

### Aberturas que funcionam

- Direto: "Estou enviando os arquivos discutidos na reunião de ontem."
- Contexto + pedido: "Como combinamos, segue minha proposta para o projeto X. Pode me dar retorno até quinta?"
- Resposta a pedido: "Sobre o que você perguntou sobre as métricas de Q3:"

### Aberturas a evitar

- "Espero que esteja bem" (a menos que seja genuíno)
- "Conforme combinado anteriormente" (formal demais para muitos contextos)
- "Venho por meio desta" (rebuscado)
- "Salve!" / "E aí!" (informal demais para corporativo)

### Despedidas

- **Padrão profissional:** "Atenciosamente,"
- **Mais cordial:** "Abraço," (com pessoas próximas) / "Um abraço,"
- **Final de cadeia operacional:** "Obrigado!" / "Valeu!"
- **Formal externo:** "Cordialmente,"
- **Evitar:** "Att.", "Abs", abreviações em geral

### Armadilhas

- Pedir várias coisas no mesmo e-mail (cada e-mail = uma ação)
- E-mail longo sem parágrafo (parede de texto)
- Tom passivo-agressivo ("conforme já mencionado anteriormente")
- Cópia oculta ou cópia desnecessária
- Anexo prometido sem anexar

### Exemplo

> **Assunto:** Aprovação para contratar fornecedor de design — Q1 2026
>
> Olá Pedro,
>
> Como discutimos na última 1:1, preciso da sua aprovação para fechar com a Estúdio Z para o redesign da landing page.
>
> Orçamento: R$ 18.500, dentro do que combinamos para Q1.
> Prazo: 6 semanas a partir do início.
> Justificativa: trabalharam com a marca em 2023, conhecem o tom.
>
> Posso fechar até sexta-feira (12/12)? Eles seguram o slot até lá.
>
> Atenciosamente,
> Carla

---

## 5. Capítulo de Livro

**ID:** `capitulo`
**Formalidade:** varia (depende do gênero)
**Tamanho típico:** 1500-5000 palavras
**Tempo de leitura alvo:** 10-30 minutos

### Contexto de uso

Capítulo é unidade de fôlego. Lê-se com tempo e atenção, geralmente em sequência. Pode ser ficção (narrativa, personagem, cena) ou não-ficção (argumento desenvolvido, exemplos longos, anedotas).

### Estrutura — Ficção

```

# Capítulo X — [Título evocativo]

[Cena de abertura: ancorar tempo, lugar, personagem em movimento]

[Desenvolvimento: ação + reflexão + diálogo, alternados]

[Pico de tensão ou momento de revelação]

[Fechamento: gancho para o próximo capítulo]

```

### Estrutura — Não-ficção

```

# Capítulo X — [Título com promessa intelectual]

[Abertura: anedota, cena ou pergunta provocativa]

[Desenvolvimento do argumento em movimento dialético:
tese → exemplo → contraponto → síntese]

[Momento "aha": insight central do capítulo]

[Fechamento: ponte para o próximo, ou síntese aberta]

```

### Marcadores estilísticos

- **Descrição sensorial:** vista, som, tato, olfato, paladar — humanos lembram experiências sensoriais
- **Diálogos com aspas duplas:** "Você vem?", perguntou ela. (NUNCA travessões)
- **Ritmo variado:** parágrafos longos para imersão, curtos para impacto
- **Voz narrativa:** consistente em primeira, terceira ou segunda pessoa
- **Tempo verbal:** consistente (pretérito perfeito é o mais comum em narrativa)
- **Especificidade:** detalhes concretos no lugar de generalidades

### Aberturas que funcionam (ficção)

- Em movimento: "Ela já estava na porta quando o telefone tocou."
- Diálogo: "'Esquece o que eu disse ontem', ele falou, sem olhar."
- Sensação: "O cheiro de café queimado dominava a casa."
- Reflexão curta: "Tem decisões que a gente toma e só percebe depois."

### Aberturas que funcionam (não-ficção)

- Anedota: "Em 1973, três pesquisadores em Stanford fizeram um experimento simples."
- Pergunta provocativa: "Por que algumas pessoas conseguem terminar o que começam?"
- Imagem-conceito: "Imagine uma cidade onde ninguém olha para o relógio."
- Citação seguida de tensão: "'O futuro já chegou', escreveu Gibson. 'Só que está mal distribuído.'"

### Armadilhas

- Descrições genéricas ("a sala era grande e bem iluminada")
- Diálogos que soam expositivos ("Como você sabe, João, somos irmãos.")
- Adjetivos empilhados ("um homem alto, forte, sério, calado")
- Resumos em vez de cenas
- Filtro do narrador ("ela viu que...", "ele percebeu que...") — preferir mostrar direto
- Travessões para diálogo (são clichê de IA mesmo na ficção brasileira recente)

---

## 6. Roteiro de Podcast

**ID:** `podcast`
**Formalidade:** 1-2 (linguagem falada)
**Tamanho típico:** 800-3000 palavras (5-25 min de áudio)
**Tempo de leitura alvo:** N/A (é roteiro, não leitura)

### Contexto de uso

Texto que vai ser **falado**, não lido. Tudo muda. Frases longas com subordinadas viram emaranhado na voz. Termos técnicos sem contexto soam estranhos. Repetições viram úteis para reforço.

### Estrutura recomendada

```

[VINHETA DE ABERTURA — 5s]

[HOST]: [Saudação curta, gancho do episódio em 30s]

Exemplo: "Oi, gente. Bem-vindos ao [Podcast]. Hoje a gente
vai conversar sobre [tema], e o motivo é que [provocação]."

[BLOCO 1: Subtema A]
[Desenvolvimento, com pausas marcadas, ritmo oral]

[INTERVALO / MERCHAN] (opcional)

[BLOCO 2: Subtema B]

[BLOCO 3: Convidado ou aprofundamento]

[ENCERRAMENTO]
[HOST]: "Por hoje é isso. [Recapitulação rápida].
[CTA: seguir no Spotify, mandar áudio, etc.].
A gente se vê semana que vem."

[VINHETA DE FECHAMENTO — 5s]

```

### Marcadores estilísticos

- **Linguagem falada pura:** "a gente" (não "nós"), contrações ("tá", "pra"), "né", "tipo"
- **Frases curtas:** quase sempre, mais fáceis de gravar e ouvir
- **Repetições intencionais:** para reforçar pontos no áudio
- **Marcações entre colchetes:** `[PAUSA]`, `[RISO]`, `[SFX: efeito sonoro]`, `[TROCA DE TOM]`, `[ENERGIA ALTA]`, `[VOZ BAIXA]`
- **Tags de quem fala:** `[HOST]`, `[CO-HOST]`, `[CONVIDADO]`, `[GUEST: Nome]`
- **Quebra para ad libitum:** marcar onde é improviso `[AD LIBITUM]`

### Vocabulário oral brasileiro

Em podcast, palavras escritas ficam estranhas faladas. Trocar:
- "Posteriormente" → "depois"
- "Anteriormente" → "antes"
- "Atualmente" → "hoje em dia", "agora"
- "Subsequentemente" → "em seguida", "depois disso"
- "Adicionalmente" → "e mais", "outra coisa"
- "Consequentemente" → "aí", "por isso"

### Aberturas que funcionam

- "Oi, gente, sejam bem-vindos. Hoje a gente tem um tema diferente."
- "Tudo bem? Hoje vou contar uma história que mudou meu jeito de pensar sobre..."
- "Pega aí, porque o episódio de hoje é denso." (sinaliza tema sério)

### Armadilhas

- Frases de linha escrita ("Vale ressaltar que...") — quase impossíveis de falar bem
- Termos técnicos sem definição ("vamos falar de PMF" — defina antes)
- Longos blocos sem marcação de pausa (gravar fica truncado)
- Tríades retóricas previsíveis ("primeiro... segundo... terceiro...") — entediante no áudio
- Linguagem rebuscada ("paradigma", "intricado") — soa pernóstico falado

### Exemplo

> [VINHETA — 5s]
>
> [HOST]: Oi, gente. Sejam bem-vindos ao [Podcast]. Eu sou a Carla.
>
> [PAUSA CURTA]
>
> Hoje a gente vai falar de uma coisa meio chata, mas que é importante. [TROCA DE TOM, energia mais baixa] Decisões de carreira que a gente toma por inércia.
>
> Sabe quando você tá num emprego, não tá ruim, mas também não tá bom? E aí você fica. Cinco anos depois, continua lá.
>
> [PAUSA]
>
> É sobre isso.

---

## 7. Roteiro de Vídeo

**ID:** `video`
**Formalidade:** 1-2
**Tamanho típico:** 300-1500 palavras (1-10 min de vídeo)
**Tempo de leitura alvo:** N/A

### Contexto de uso

Vídeo curto (YouTube, Reels, Shorts, TikTok) ou médio (YouTube long-form). Retenção é métrica central. Primeiros 5 segundos definem se a pessoa continua ou não.

### Estrutura recomendada

```

[HOOK — 0 a 5s]
[CENA: descrição visual]
[NARRAÇÃO: frase impactante, pergunta, ou ação inesperada]

[INTRO — 5 a 15s]
[CENA: estabelece quem fala, contexto]
[NARRAÇÃO: o que o vídeo vai entregar, em uma frase]

[BLOCO 1 — Ponto principal]
[CENA: A-roll (apresentador) + B-ROLL: descrição]
[NARRAÇÃO]

[BLOCO 2 — Aprofundamento ou contraponto]
[CORTE]
[B-ROLL: imagem ilustrativa]
[NARRAÇÃO]

[GANCHO MEIO — opcional, 30-50% do vídeo]
"Mas tem uma coisa que muda isso..."

[BLOCO 3 — Payoff]

[CTA — call to action]
"Se gostou, [inscreve/segue/comenta]."

[OUTRO — sting de fechamento]

```

### Marcadores estilísticos

- **Indicações visuais entre colchetes:** `[CORTE]`, `[CLOSE]`, `[ZOOM IN]`, `[B-ROLL: descrição]`, `[CENA EXTERNA]`, `[TEXTO NA TELA: ...]`
- **Narração direta:** "olha só", "presta atenção", "você vai ver que"
- **Frases curtas:** ritmo acelerado, edição rápida
- **Repetição de palavra-chave:** ajuda na retenção e algoritmo
- **Ganchos a cada 30s:** "mas tem uma coisa", "e aqui que fica interessante", "espera, antes de ir embora..."

### Hooks que funcionam

- Pergunta direta: "Você sabia que [fato inesperado]?"
- Afirmação contraintuitiva: "Tudo que te ensinaram sobre [X] está errado."
- Promessa concreta: "Em três minutos eu vou te mostrar como [resultado]."
- Cena chocante seguida de contexto: "[Cena de algo dando errado]. Isso aconteceu comigo semana passada."
- Lista numerada: "Cinco erros que estão acabando com sua [coisa]."

### CTAs por plataforma

- **YouTube:** "Inscreve no canal" / "Deixa o like se gostou" / "Comenta o que achou"
- **Instagram Reels:** "Salva pra ver depois" / "Compartilha com alguém"
- **TikTok:** "Segue pra mais" / "Comenta com [palavra]"

### Armadilhas

- Hook longo ou genérico ("Hoje vou falar sobre...")
- Narração que descreve o que está na tela ("Aqui vocês podem ver...")
- Bloco final demorado sem CTA claro
- Tom muito polido — vídeos cruamente humanos performam melhor

---

## 8. Texto Explicativo

**ID:** `explicativo`
**Formalidade:** 2-3
**Tamanho típico:** 500-1500 palavras
**Tempo de leitura alvo:** 4-10 minutos

### Contexto de uso

Texto que assume zero conhecimento prévio. Pode ser para leigo absoluto (Wikipedia) ou para alguém com base mas sem o tópico específico. Objetivo: leitor sai sabendo.

### Estrutura recomendada

```

# [O tópico, definido de forma clara]

[Lead: o que é + por que importa, em 2-4 frases]

## O que é (definição)

[Definição clara, sem circular]

## Por que importa

[Implicações práticas]

## Como funciona (mecanismo)

[Explicação progressiva, do simples ao complexo]

## Exemplo concreto

[Caso real ou ilustrativo]

## Quando aplicar (ou não)

[Limites e contextos]

## Recapitulação

[Pontos principais em 3-5 linhas]

```

### Técnicas didáticas

- **Analogias acessíveis:** "É como X, mas no caso de Y"
- **Do concreto ao abstrato:** começar com exemplo, depois generalizar
- **Definir antes de usar:** todo termo técnico explicado na primeira ocorrência
- **Quebra de conhecimento:** "Antes de entrar nisso, precisamos lembrar que..."
- **Sinalização explícita:** "Resumindo até aqui:", "Vamos por partes:"
- **Verificação compreensiva:** "Se isso ficou claro, o próximo ponto vem fácil."

### Armadilhas

- Pular passos (assumir que o leitor sabe)
- Excesso de jargão técnico
- Definição circular ("X é o processo de fazer X")
- Exemplos hipotéticos demais (preferir reais)
- Conclusão abstrata sem aterragem prática

---

## 9. Texto Geral

**ID:** `geral`
**Formalidade:** varia
**Tamanho típico:** varia
**Tempo de leitura alvo:** varia

### Contexto de uso

Default quando nenhum dos tipos específicos cabe. Adaptado pelo briefing do usuário. Pode ser descrição de produto, bio profissional, texto para palestra, post de redes sociais (longo), texto de apresentação, etc.

### Princípios

Identificar:
1. **Propósito:** informar? convencer? entreter? agradecer?
2. **Público:** quem lê? o que já sabe?
3. **Tom:** formal? casual? técnico?
4. **Tamanho:** definir antes de começar
5. **Formato:** texto corrido? listas? estrutura clássica?

Aplicar princípios gerais da skill (gramática AO1990, humanização) e adaptar conforme briefing.

---

# Tipos conversacionais

Os três tipos a seguir são diferentes em natureza. Não são produção de conteúdo autoral — são **respostas a outras pessoas em contexto real**. A humanização opera de modo diferente: o texto já é curto, contextual e em diálogo, então parece humano naturalmente. O risco maior é o oposto: **soar artificial pelo excesso de cuidado**.

Regras gerais para tipos conversacionais:

- **Brevidade vence:** quanto mais curto, melhor (dentro do que o contexto pede)
- **Contexto é tudo:** depende do que veio antes
- **Voz pessoal aceita:** primeira pessoa frequente
- **Pode quebrar regras formais:** "Mas..." no início, frases incompletas, etc.
- **Imperfeição é assinatura humana:** uma pequena hesitação ou reformulação ajuda
- **Sem floreio:** ninguém abre comentário com "Em um mundo onde"

---

## 10. Comentário em Blog

**ID:** `comentario-blog`
**Formalidade:** 2-3
**Tamanho típico:** 30-200 palavras
**Tempo de leitura alvo:** 15-60 segundos

### Contexto de uso

Comentário em blog é resposta a um artigo (ou a outro comentário). Quem comenta:
- Quer ser lido pelo autor
- Quer engajar com outros leitores
- Não quer parecer spammer

Bom comentário gera resposta. Comentário ruim ("Ótimo post!") morre na seção.

### Tipos de comentário valioso

**1. Acréscimo:** trazer perspectiva, dado ou exemplo que o artigo não cobriu.
> "Boa análise. Acrescento que no setor de educação isso aparece de forma ainda mais aguda — em 2022 vi uma escola implementar exatamente esse modelo, e o que travou foi o middle management, não os professores."

**2. Discordância respeitosa:** apontar onde concorda e onde diverge.
> "Concordo com a primeira parte. Onde discordo é na conclusão: minha experiência sugere que esse efeito só aparece em times maiores que 15 pessoas. Em times pequenos a dinâmica é outra."

**3. Pergunta de aprofundamento:** mostrar interesse genuíno com pergunta específica.
> "Curiosa sobre o ponto 3. Você chegou a testar essa abordagem em contexto B2B? Imagino que o ciclo mais longo de venda mudaria as métricas."

**4. Compartilhamento de experiência:** trazer caso pessoal relevante.
> "Passei por algo parecido em 2020. No nosso caso o que funcionou foi o oposto do que você sugere — mais reuniões, não menos. Mas reuniões curtas e com pauta única."

**5. Recurso adicional:** apontar livro, artigo, ferramenta relevante (sem ser spam).
> "Tópico interessante. Se for útil, o livro 'X' do Y aprofunda exatamente esse ponto sobre Z, com vários estudos de caso."

### Estrutura recomendada

Comentários têm formato simples:

```

[Reconhecimento curto OU entrada direta]
[Contribuição principal (1-3 frases)]
[Opcional: pergunta ou fechamento]

```

OU mais direto:

```

[Sua contribuição central, sem preâmbulo]

```

### Marcadores estilísticos

- **Voz:** primeira pessoa frequente ("acho", "minha experiência")
- **Tom:** conversacional, igualitário
- **Brevidade:** ir ao ponto rapidamente
- **Específico:** dado, número ou exemplo concreto vale mais que opinião abstrata
- **Sem CTA óbvio:** não tentar vender nada

### Aberturas que funcionam

- "Boa análise. Acrescento que..."
- "Concordo com X, mas no Y minha experiência foi diferente:"
- "Pergunta: você chegou a testar..."
- "Curioso. No meu time isso apareceu como..."
- (Sem preâmbulo) "O ponto 3 me fez pensar em..."

### Aberturas a evitar

- "Excelente artigo! Parabéns!" (vazio, soa spam)
- "Em um mundo onde..." (artificial em comentário)
- "Gostaria de parabenizar..." (formal demais)
- "Quero compartilhar..." (sem necessidade — só compartilha)
- "Como podemos observar..." (não é ensaio)

### Armadilhas

- **Longo demais:** comentário de 500 palavras compete com o artigo
- **Spam disfarçado:** terminar com "leia meu blog em..."
- **Concordar com tudo:** soa bajulação
- **Discordar com agressividade:** mata a conversa
- **Ego-mostrar:** comentário virar showcase pessoal
- **Resposta de IA pura:** estrutura tipo "1. ... 2. ... 3. ..." em comentário casual

### Calibração por tipo de blog

- **Blog técnico:** dado, código, link para benchmark, exemplo de implementação
- **Blog de opinião:** experiência pessoal, contraponto, pergunta
- **Blog corporativo:** mais formal, sem coloquialismo excessivo
- **Newsletter pessoal:** mais íntimo, pode ser caloroso

### Exemplo cru → humanizado

❌ Versão IA crua:
> "Excelente artigo sobre produtividade! Você apresentou três pontos cruciais que são fundamentais para qualquer profissional. Em particular, a importância da priorização ressoou comigo. Vale ressaltar que, no entanto, é importante considerar também o contexto de cada equipe. Adicionalmente, gostaria de compartilhar que tenho aplicado essas técnicas em meu trabalho com resultados robustos. Obrigado pelo conteúdo!"

✅ Humanizado:
> "Boa, gostei especialmente da parte sobre priorização. Uma coisa que aprendi quebrando a cara: priorizar funciona em time pequeno. Em time de 20+ pessoas, você prioriza X, mas alguém na ponta da cadeia já tinha priorizado Y três sprints atrás e ninguém sabia. Aí entra outra camada de problema. Por curiosidade, você já viu modelos para esse tipo de coordenação em escala?"

---

## 11. Comentário no Jira

**ID:** `comentario-jira`
**Formalidade:** 3
**Tamanho típico:** 20-150 palavras
**Tempo de leitura alvo:** 20-60 segundos

### Contexto de uso

Comentário em Jira é **registro de trabalho assíncrono**. Quem lê:
- Outros membros do time (dev, QA, PM, design)
- Gestor que entra no ticket meses depois
- Auditoria ou compliance
- Você mesmo, daqui a 3 meses, sem lembrar do contexto

Bom comentário no Jira economiza reuniões e desbloqueia trabalho. Comentário ruim cria ruído e perdas de tempo.

### Quando comentar (tipologia)

**1. Atualização de status:** "Onde está o trabalho agora"
> "Em desenvolvimento. Frontend pronto, falta integração com API que deve ficar pronta amanhã."

**2. Bloqueio:** "Por que parou e o que destrava"
> "Bloqueado. Aguardando definição do @João sobre como tratar o caso de usuário sem CPF cadastrado. Sem isso não consigo escrever o validador."

**3. Decisão técnica:** "Escolhemos X em vez de Y por causa de Z"
> "Decidimos usar Redis em vez de Memcached para esse cache. Razão: já temos Redis em produção e o volume não justifica adicionar nova dependência."

**4. Pergunta:** "Preciso de clarificação"
> "@Maria, no requisito 3 está escrito 'usuário pode editar', mas isso vale para usuário comum ou só admin? Tem impacto direto na implementação do middleware."

**5. Pedido de ação:** "Você (mencionado) precisa fazer X"
> "@Pedro, pode dar uma olhada no PR #487 quando puder? Está bloqueando o deploy de quinta."

**6. Resultado de testes:** "Testei e isso aconteceu"
> "Testei em staging. Funciona para os 12 casos do acceptance criteria. Encontrei edge case: quando o usuário tem 0 transações, a tela quebra. Vou abrir bug separado."

**7. Reportagem de bug com contexto:** "Reproduz assim"
> "Bug reproduz consistentemente:
> 1. Login com user@test.com
> 2. Ir em /dashboard
> 3. Clicar em 'exportar'
> Resultado: erro 500. Esperado: download do CSV.
> Aconteceu em Chrome 121 e Safari 17, em prod e staging."

**8. Encerramento:** "Pronto, terminei"
> "Concluído. PR mergeado em #487. Deploy feito. QA pode validar em staging."

### Estrutura típica

```

[Status/Tipo se útil] [Conteúdo direto] [@menção se precisa de alguém] [Próximo passo se aplicável]

```

Quase sempre uma ou duas frases. Comentário em Jira longo é geralmente comentário ruim — provavelmente devia ser uma página de Confluence ou uma issue separada.

### Marcadores estilísticos

- **Tom:** profissional, mas não rebuscado
- **Direto:** zero floreio
- **@menções:** sempre quando precisa que alguém aja
- **Especificidade:** versão, ambiente, browser, ID do PR, hash do commit
- **Voz:** primeira pessoa OK, primeira plural ("definimos", "decidimos") quando coletivo
- **Bullet/numerado:** sim quando lista passos de reprodução ou checklist
- **Markdown leve:** `código` para nomes de variáveis/comandos, **negrito** para palavras-chave

### Aberturas que funcionam

- Status direto: "Concluído.", "Em andamento.", "Bloqueado por X."
- Ação: "@Pedro, pode revisar..."
- Decisão: "Decidimos por X. Razão:"
- Resultado: "Testei. Funciona. Edge case:"
- Pergunta: "@Maria, dúvida no requisito 3:"

### Aberturas a evitar

- "Olá time, gostaria de compartilhar..." (Jira não é e-mail)
- "Conforme combinado anteriormente..." (formal demais)
- "Em uma análise mais detalhada, podemos observar..." (não é relatório)
- Saudações genéricas ("Bom dia!", "Pessoal!") — Jira não tem horário

### Armadilhas

- **Excesso de contexto repetido:** o ticket já tem o contexto
- **Comentário que devia ser issue:** se requer trabalho novo, abre issue
- **Vagueza:** "está com problema" vs "retorna 500 quando body é vazio"
- **Sem @menção quando precisa:** ninguém recebe notificação
- **Conversa interpessoal:** "vamos almoçar?" não vai aqui
- **Tom passivo-agressivo:** "como já mencionei" — Jira é histórico, evite cobrança disfarçada

### Exemplo comparativo

❌ Versão IA crua:
> "Olá equipe, gostaria de compartilhar uma atualização importante sobre o desenvolvimento desta funcionalidade. Conforme discutido anteriormente, estávamos enfrentando alguns desafios significativos relacionados à integração da API. No entanto, após uma análise robusta e meticulosa, conseguimos identificar três pontos cruciais que estavam causando o problema. Implementei as correções necessárias e os testes iniciais demonstraram resultados muito positivos. Adicionalmente, gostaria de mencionar que a documentação foi atualizada de acordo. Por favor, deixem-me saber se há mais alguma coisa que precise ser feita."

✅ Humanizado para Jira:
> "Resolvido. Problema era no parser do JSON quando o campo `metadata` vinha null. Corrigi em #487. Testei os 4 cenários do AC + o null case que estava quebrando. Doc atualizada. @QA pode validar?"

---

## 12. Resposta de Chat

**ID:** `chat`
**Formalidade:** 1-3 (varia muito por contexto)
**Tamanho típico:** 5-100 palavras
**Tempo de leitura alvo:** 5-30 segundos

### Contexto de uso

Resposta em Slack, Teams, Discord, WhatsApp profissional, Telegram, ou DM em geral. Diferença essencial: **é diálogo em tempo real ou near-real-time**. A pessoa do outro lado está esperando — não em horizonte de "quando puder", mas em "agora" ou "logo".

### Tipos de resposta

**1. Resposta a pergunta direta:**
> Pergunta: "Conseguimos liberar o deploy hoje?"
> Resposta: "Sim, falta só o ok do QA. Tô esperando."

**2. Reconhecimento + ação:**
> "Recebi. Olho hoje à tarde e te dou retorno até 17h."

**3. Pergunta de volta:**
> "Pode ser. Você prefere terça de manhã ou quarta à tarde?"

**4. Atualização rápida:**
> "Update: build verde, pode mergear."

**5. Resposta em thread (mais formal):**
> Pode ser mais elaborada — uma frase de contexto + resposta + próximo passo.

**6. Reação rápida com emoji:** 👍, ✅, 🙏, ❤️
- Substitui resposta textual quando reconhecer é suficiente
- Atalho válido em culturas de chat estabelecidas

**7. "Aviso de espera":**
> "Vi sua msg. Tô em call agora, te respondo em ~30min."

### Estrutura típica

Geralmente UMA frase. No máximo duas ou três. Se a resposta vai precisar de mais que isso, considerar:
- Mudar para thread
- Marcar reunião curta
- Mandar e-mail
- Criar issue/ticket

### Marcadores estilísticos

- **Voz:** primeira pessoa, sempre
- **Contrações OK:** "tô", "pra" (em chat informal entre pares)
- **Pontuação minimalista:** ponto final pode soar seco em chat
- **Emoji moderado:** ajuda a transmitir tom (mas não exagerar)
- **Sem floreio:** zero saudação se já está em conversa ativa
- **Tags com @:** quando precisa puxar alguém pra conversa

### Calibração por destinatário

**Com chefe direto/cliente externo:**
> Mais cordial, com saudação se for primeiro contato do dia, pontuação completa.
> "Oi Pedro, bom dia! Recebi o doc, dou retorno até o fim do dia."

**Com par (mesmo nível):**
> Direto, contrações OK, emoji OK.
> "Recebi, olho hoje 👍"

**Em canal público vs DM:**
> Canal público: um pouco mais cuidadoso, qualquer pessoa pode ler.
> DM: pode ser mais íntimo, depende da relação.

**Cross-cultural ou empresa grande:**
> Mais conservador. Evitar gírias regionais, manter pontuação completa, ser mais explícito.

### Tom segundo situação

**Boa notícia:** energia OK, "🎉" ou exclamação, "boa!", "show!"
> "Cliente aprovou! 🎉 Manda a próxima fatura."

**Notícia neutra:** direto e objetivo
> "Reunião remarcada para quinta às 14h."

**Notícia ruim:** sem dramatização, com próximo passo
> "API caiu em prod. Tô investigando agora. Aviso quando voltar."

**Discordância:** suave + razão
> "Hm, eu iria por um caminho diferente. Posso explicar em call rápida?"

**Confronto necessário:** privado (DM), específico, sem ataque pessoal
> "Pedro, sobre o que aconteceu na reunião — posso te ligar 5 min?"

### Aberturas que funcionam

- Direto: "Sim", "Não", "Pode ser", "Não sei"
- Reconhecimento: "Recebi", "Vi", "Tô vendo"
- Contexto: "Estou em call, te falo em 30min"
- Pergunta de volta: "Que horas?"
- Confirmação: "Fechado.", "Combinado.", "Tá certo."

### Aberturas a evitar

- "Bom dia, espero que esteja bem" se já está conversando há horas
- "Como posso te ajudar?" — chatbot
- "Excelente pergunta!" — chatbot
- Frases longas iniciando com conectivos formais ("Conforme") em chat informal
- Emoji em excesso (uma resposta com 4 emojis soa artificial)

### Armadilhas

- **Wall of text:** chat não suporta parede de texto — quebra ou move pra outro canal
- **Múltiplas mensagens curtas em sequência:** "Oi", "Pedro", "Tem um minuto?", "Preciso te perguntar uma coisa" — quatro notificações onde uma resolvia
- **Esperar resposta imediata:** chat profissional é semi-síncrono, não síncrono total
- **Esquecer @menção:** em canal público sem @, ninguém é notificado
- **Tom inconsistente com a relação:** muito formal com par próximo soa frio; muito casual com cliente novo soa desrespeitoso
- **Hyper-corrigir gramática:** "vc" e "tbm" são aceitáveis em DM informal entre pares
- **Auto-citação para parecer organizado:** estrutura tipo "Em primeiro lugar... Em segundo lugar... Em terceiro lugar..." em chat é desastre

### Resposta de IA crua vs humanizada

❌ IA crua (resposta a "conseguimos liberar hoje?"):
> "Olá! Excelente pergunta. Após uma análise minuciosa da situação atual, posso confirmar que sim, conseguiremos liberar o deploy hoje. No entanto, é importante destacar que ainda estamos aguardando a validação final do QA, que é crucial para garantir a qualidade da entrega. Assim que recebermos o ok da equipe de qualidade, estaremos prontos para prosseguir com o deploy. Vale ressaltar que esse processo segue nosso protocolo padrão. Por favor, me avise se precisar de mais alguma informação!"

✅ Humanizado:
> "Dá sim. Tô esperando só o ok do QA — devia sair em uma hora. Aviso aqui assim que sair."

### Chat técnico (Slack de eng)

Tem cultura própria:
- Code snippets em blocos de código (3 acentos graves)
- Emojis técnicos: 🚀 (deploy), 🐛 (bug), 🔥 (incident), 🟢🟡🔴 (status)
- Threads para discussão longa
- Stand-up rápido em formato fixo (ontem/hoje/blockers)
- Permite mais informalidade, gírias técnicas ("LGTM", "merge time", "rollback now")

### Chat de cliente (suporte/vendas)

Mais formal e cuidadoso:
- Sempre uma saudação no primeiro contato do dia
- Pontuação completa
- Sem gírias
- Confirmar entendimento explícito
- Encerrar com pergunta aberta ou compromisso claro

---

# Tabela-resumo de calibração

| Tipo | ID | Formalidade | Tamanho | Voz pessoal | Humanização |
|---|---|---|---|---|---|
| Artigo blog | `blog` | 2-3 | 600-1500 | alta | intensa |
| Artigo técnico | `tecnico` | 3-4 | 800-2000 | média | intensa |
| Texto corporativo | `corporativo` | 4 | 300-1200 | baixa | intensa |
| E-mail | `email` | 3-4 | 50-300 | baixa-média | média |
| Capítulo livro | `capitulo` | varia | 1500-5000 | varia | intensa |
| Roteiro podcast | `podcast` | 1-2 | 800-3000 | altíssima | leve |
| Roteiro vídeo | `video` | 1-2 | 300-1500 | altíssima | leve |
| Texto explicativo | `explicativo` | 2-3 | 500-1500 | média | média |
| Texto geral | `geral` | varia | varia | varia | adaptar |
| **Comentário blog** | `comentario-blog` | 2-3 | 30-200 | alta | leve |
| **Comentário Jira** | `comentario-jira` | 3 | 20-150 | média | mínima |
| **Resposta chat** | `chat` | 1-3 | 5-100 | alta | mínima |

---

# Notas finais sobre tipos conversacionais

**Por que humanização mínima nos conversacionais?**

Tipos conversacionais já têm 3 fatores que naturalmente os afastam do padrão de IA:

1. **Brevidade extrema** — detectores precisam de texto longo para extrair features estilométricas confiáveis. Mensagem de 12 palavras tem pouca superfície de ataque.
2. **Contexto incorporado** — referência ao que veio antes ("isso", "ele", "aquilo de ontem") quebra coesão padrão de LLM.
3. **Tom oral/informal** — contrações, fragmentos, pontuação solta — todos contra-padrões do LLM.

**O risco real:** sobre-engenheirar. Aplicar burstiness extrema, vocabulário rebuscado e estrutura formal em chat é exatamente o oposto do que faz parecer humano. Para conversacionais, **menos é mais**.

**Regra prática:** se ao ler em voz alta o comentário/chat/Jira soa como algo que você diria para um colega, está bom. Se soa como ensaio escolar, refazer mais cru.

---

# Apêndice: Decisão rápida de tipo

Se o usuário não especificou:

```

É resposta a alguma coisa que veio antes?
├── Sim, em ticket de trabalho → comentario-jira
├── Sim, em chat (Slack/Teams/WhatsApp) → chat
├── Sim, em artigo de blog (público) → comentario-blog
└── Não, é produção autoral
├── Para áudio falado → podcast
├── Para vídeo → video
├── Para livro → capitulo
├── Para e-mail → email
├── Para blog do usuário → blog ou tecnico (se técnico)
├── Para comunicação empresa → corporativo
├── Para ensinar algo → explicativo
└── Não está claro → geral

```

Se ainda não estiver claro, perguntar: "É para postar/enviar onde? E é resposta a alguma coisa ou conteúdo do zero?"
