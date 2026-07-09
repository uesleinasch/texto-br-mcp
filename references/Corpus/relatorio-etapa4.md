# Etapa 4 — configurações do modelo logístico (LOO-CV honesto)

Baselines: pesos manuais 0.853 (baseline-report.json, corpus corrigido) | aditivo E3 (LOO, corpus antigo 30H): 0.858 — histórico

Rota E3 estendida às 17 chaves (prior manual; sinais de referência computados in-sample — contaminada, NÃO comparável 1:1 com o LOO honesto): 0.926 (calibrar.separacao_loocv)

| k | λ | AUC LOO-CV |
| --- | --- | --- |
| 5 | 0.1 | 0.843 |
| 5 | 0.3 | 0.849 |
| 5 | 1.0 | 0.851 |
| 7 | 0.1 | 0.83 |
| 7 | 0.3 | 0.826 |
| 7 | 1.0 | 0.835 |
| 9 | 0.1 | 0.885 |
| 9 | 0.3 | 0.894 |
| 9 | 1.0 | 0.902 ← vencedor |
| 11 | 0.1 | 0.862 |
| 11 | 0.3 | 0.884 |
| 11 | 1.0 | 0.893 |
| 13 | 0.1 | 0.858 |
| 13 | 0.3 | 0.877 |
| 13 | 1.0 | 0.885 |
| 17 | 0.1 | 0.837 |
| 17 | 0.3 | 0.867 |
| 17 | 1.0 | 0.891 |
| 10-antigas | 1.0 | 0.84 |

Chaves do vencedor: burstiness_gb, burstiness, zipf, sentenca_de_impacto, razao_compressao, burrows_delta, yule_k, cross_entropy_trigramas, sem_pivots
In-sample: 0.963 | alvo p75 humano (prob): 0.9 (preciso, 4 casas: 0.9357)
Medianas in-sample (prob): humano 0.881 vs IA 0.088

p75 humano nas probabilidades LOO (honesto): 0.8872 — sob o ALVO in-sample (p75 0.9357), ~6/29 humanos passam out-of-sample; leitura consistente com a política mira-alto, mas o quantil LOO é o número a preferir em recalibrações futuras.

Disclosure de normalização: os clamps p5/p95 de NORMALIZACAO_NOVOS (score.py) vêm do corpus completo agrupando as duas classes (label-free); efeito de 2ª ordem no fit por saturação em 0/1 nas bordas — não recomputados por fold do LOO-CV.

Leitura honesta: o AUC LOO de cada célula é honesto para AQUELA configuração, mas o vencedor é o máximo sobre 18 pontos da grade e o ranking de candidatos foi feito in-sample — juntos, tornam o número do vencedor uma estimativa otimista da generalização do PROCEDIMENTO de auto-seleção (um CV aninhado daria menos). Com n=56, é o preço aceito nesta etapa; o gate deve ler o 0.9x como teto, não como piso.
