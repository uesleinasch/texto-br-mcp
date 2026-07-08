# Relatório de separação baseline (pesos atuais)

- Amostras: 29 humano / 27 IA
- AUC total: **0.853**
- Média do score: humano 65.2 vs IA 53.3 (alvo 93.6)

## Poder discriminativo por componente (AUC univariado)

| Componente | AUC |
| --- | --- |
| burstiness_gb | 0.833 |
| burstiness | 0.832 |
| zipf | 0.765 |
| sentenca_de_impacto | 0.762 |
| razao_compressao | 0.658 |
| burrows_delta | 0.657 |
| yule_k | 0.649 |
| cross_entropy_trigramas | 0.619 |
| sem_pivots | 0.584 |
| autocorrelacao_lag1 | 0.581 |
| ordem_nao_canonica | 0.542 |
| paragrafos_variados | 0.519 |
| sem_inicios_repetidos | 0.503 |
| sem_corrente_de_conectivos | 0.5 |
| diversidade_lexical | 0.483 |
| sem_trigramas_repetidos | 0.481 |
| sem_sequencias_uniformes | 0.475 |
