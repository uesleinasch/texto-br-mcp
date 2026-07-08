# Etapa 4 — configurações do modelo logístico (LOO-CV honesto)

Baselines: pesos manuais 0.853 (baseline-report.json, corpus corrigido) | aditivo E3 (LOO, corpus antigo 30H): 0.858 — histórico

Aditivo E3 no corpus corrigido (rota com contaminação residual documentada): 0.926 (calibrar.separacao_loocv)

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
In-sample: 0.963 | alvo p75 humano (prob): 0.9
Medianas in-sample (prob): humano 0.881 vs IA 0.088
