# Humanização macroestrutural

Material da Fase 5 do pipeline texto-br. As fases anteriores tratam da
microestrutura (palavra, sentença, parágrafo). Esta trata da **arquitetura do
documento**: como as seções, os títulos e os fechos se organizam ao longo do
texto inteiro. Um dos sinais mais fortes de texto gerado por IA não está em
nenhuma frase isolada, mas no conjunto: tudo encaixa bem demais.

Princípio: humanizar a macroestrutura é introduzir **assimetria deliberada** sem
perder a clareza. O analisador `texto_br_estrutura` mede; quem reescreve é você.
Aplique o plano de perturbação dos detectores mais fracos primeiro e meça de novo.

## 1. O sinal: estrutura encaixada demais

Texto humano de fôlego é irregular. O autor se empolga numa seção e é seco em
outra, esquece de fechar um raciocínio, repete um assunto que já tinha tratado,
abre com uma cena em vez de uma definição. Texto de IA tende ao oposto: seções
do mesmo tamanho, títulos da mesma forma, cada parágrafo aterrissando numa lição,
bordões em sequência, subtópicos para tudo e uma progressão linear sinalizada
passo a passo. Cada elemento, isolado, é defensável. O problema é a **regularidade**:
a soma denuncia a máquina.

Os cinco detectores abaixo medem essa regularidade. Nenhum é prova isolada; o
score combina os aplicáveis. A meta não é zerar todo padrão (texto sem nenhuma
estrutura vira caos), e sim quebrar a simetria onde ela ficou mecânica.

## 2. Simetria de seções

**Sinal.** Seções de tamanho quase igual; títulos com a mesma forma gramatical
(todos gerúndio: "Entendendo... Aplicando... Construindo..."; todos pergunta;
todos com o mesmo primeiro termo); mesmo número de subseções em cada uma.

**Por que denuncia IA.** O modelo distribui o conteúdo de forma equilibrada por
default. Um humano que escreveu de verdade tem uma seção que importava mais e
ficou maior, e outra que ele despachou em três linhas.

**Perturbação.**
- Deixe uma seção respirar (corte para ~metade) e outra ir fundo (dobre o tamanho).
- Funda seções gêmeas: se duas dizem quase a mesma coisa em tamanho igual, vire uma só.
- Reescreva ao menos dois títulos com forma gramatical diferente (uma pergunta,
  uma frase nominal, um imperativo, um fragmento). Quebre o paralelismo.
- Varie a profundidade: uma seção sem subseções, outra com duas.

## 3. Inflação de subtópicos

**Sinal.** Muitos subtítulos para pouco texto; seções "finas" de duas ou três
linhas; uso de `###`/`####` num texto que não precisava.

**Por que denuncia IA.** Subtítulo é barato para o modelo e dá uma falsa sensação
de organização. Texto humano usa heading quando há virada real de assunto, não a
cada parágrafo.

**Perturbação.**
- Funda subtítulos finos; mantenha heading só onde o assunto realmente vira.
- Rebaixe uma seção fina a um parágrafo com frase-guia em negrito, sem heading próprio.
- Regra de bolso: se a seção cabe num parágrafo, provavelmente não precisava de título.
- Tipos técnicos (documentação) toleram mais seccionamento; blog e capítulo, bem menos.

## 4. Parágrafo-lição (kicker)

**Sinal.** Quase todo parágrafo termina numa frase curta e sentenciosa, uma
moral arredondada: "No fim, somos o que repetimos." "Afinal, ninguém muda sozinho."
"É isso que sustenta tudo." A última sentença é sempre bem mais curta que o corpo.

**Por que denuncia IA.** O modelo gosta de aterrissar cada parágrafo num efeito.
Um ou dois fechos assim são humanos e bons; o tell é a **uniformidade**, todo
parágrafo fechando do mesmo jeito.

**Perturbação.**
- Deixe vários parágrafos terminarem no meio do raciocínio, sem moral no fim.
- Mova o fecho de um parágrafo para o **início** do parágrafo seguinte.
- Onde sobrarem dois kickers próximos, apague um: deixe a ideia sem laço amarrado.

## 5. Frases de efeito em sequência

**Sinal.** Vários parágrafos de uma única frase curta de impacto, enfileirados:
"A vida é curta." / "O tempo não volta." / "Cada dia conta." Bordões em série.

**Por que denuncia IA.** Isolada, a frase de efeito tem força. Em sequência, vira
tique: o texto perde respiração e parece legenda motivacional.

**Perturbação.**
- Funda ao menos um bordão da sequência ao parágrafo vizinho.
- Desenvolva outro em duas ou três sentenças, dando contexto à afirmação.
- Guarde no máximo uma frase de efeito isolada por trecho longo, e onde ela pesar mesmo.

## 6. Progressão sinalizada

**Sinal.** Escada de signposts ("Primeiro... Em seguida... Por fim..."), títulos
ordinais ou numerados, seções abrindo em conectivo lógico ("Portanto...", "Dessa
forma..."), e uma moldura intro/conclusão simétrica (primeira seção curta de
apresentação, última seção curta amarrando a lição).

**Por que denuncia IA.** O modelo anuncia a própria estrutura para parecer
organizado. Texto humano transita por contraste e retomada, não por placa de
sinalização a cada curva.

**Perturbação.**
- Remova a numeração e os "primeiro/depois/por fim" explícitos; deixe a transição
  acontecer pelo conteúdo.
- Abra ao menos uma seção direto no concreto (uma cena, um número, um exemplo),
  sem conectivo de ligação.
- Quebre a moldura intro/conclusão: comece no meio da ação ou termine sem fechar
  o laço com uma síntese.

## 7. Matriz de calibração por tipo

| Tipos | Intensidade | Gate | Alvo |
| --- | --- | --- | --- |
| blog, capitulo, tecnico, explicativo, podcast, video | alta | bloqueia a entrega | 70 |
| geral, corporativo | média | advisory | 70 |
| email, comentario-blog, comentario-jira, chat | baixa | advisory | 70 |

Nos tipos de gate, avançar para a entrega exige o alvo atingido (ou `forcar: true`
a pedido do usuário). `tecnico` tolera mais subtítulos (o detector de inflação
afrouxa o limiar de densidade).

Textos conversacionais quase não têm macroestrutura: a maioria dos detectores não
se aplica e a etapa fica praticamente transparente. Não force estrutura onde não há.

## 8. Checklist de saída da Fase 5

- [ ] As seções têm tamanhos visivelmente diferentes (não há um molde único).
- [ ] Os títulos não compartilham a mesma forma gramatical (não são todos gerúndio/pergunta).
- [ ] Nem todo parágrafo fecha numa "lição"; alguns terminam no meio do raciocínio.
- [ ] Não há sequência de frases de efeito isoladas enfileiradas.
- [ ] Subtítulos aparecem só onde há virada real de assunto, não a cada parágrafo.
- [ ] A progressão não usa escada de signposts nem moldura intro/conclusão simétrica.
- [ ] A assimetria introduzida não virou bagunça: o texto continua claro e navegável.
