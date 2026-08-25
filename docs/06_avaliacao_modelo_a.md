# Avaliação do Modelo A — Features Epidemiológicas

## 1. Objetivo

Este documento registra os resultados experimentais do Modelo A do projeto
Dengue Alert.

O Modelo A utiliza exclusivamente informações epidemiológicas e temporais
derivadas do histórico municipal de dengue.

Seu objetivo é estabelecer o desempenho preditivo obtido sem o uso de variáveis
meteorológicas.

Esses resultados serão posteriormente comparados ao Modelo B, que adicionará
informações climáticas mantendo o mesmo desenho experimental.

---

## 2. Features utilizadas

O Modelo A utiliza 23 features:

1. `incidencia_100mil`;
2. `incidencia_100mil_lag_1`;
3. `incidencia_100mil_lag_2`;
4. `incidencia_100mil_lag_3`;
5. `incidencia_100mil_lag_4`;
6. `incidencia_100mil_lag_5`;
7. `incidencia_100mil_lag_6`;
8. `incidencia_100mil_lag_7`;
9. `incidencia_100mil_lag_8`;
10. `incidencia_media_2s`;
11. `incidencia_media_4s`;
12. `incidencia_media_8s`;
13. `incidencia_4s_100mil`;
14. `incidencia_4s_lag_1`;
15. `incidencia_4s_lag_4`;
16. `delta_incidencia_4s_1s`;
17. `delta_incidencia_4s_4s`;
18. `limiar_sazonal_p90`;
19. `margem_limiar_p90`;
20. `risco_elevado`;
21. `semana_sin`;
22. `semana_cos`;
23. `log_populacao`.

Nenhuma variável climática ou espacial foi utilizada nesta etapa.

---

## 3. Algoritmos avaliados

Foram avaliados dois algoritmos.

### 3.1 Regressão Logística

A regressão logística foi utilizada como modelo linear de referência.

As features foram padronizadas utilizando `StandardScaler` dentro do próprio
pipeline de modelagem.

A padronização é ajustada exclusivamente nos dados de treinamento de cada fold.

### 3.2 HistGradientBoostingClassifier

O segundo candidato foi o `HistGradientBoostingClassifier`, utilizado para
capturar relações não lineares entre as variáveis epidemiológicas.

Configuração inicial:

- `learning_rate = 0.1`;
- `max_iter = 100`;
- `early_stopping = False`;
- `random_state = 42`.

O `early_stopping` foi desativado para impedir que o algoritmo crie uma
separação interna aleatória de validação, preservando o desenho temporal
explicitamente definido no projeto.

---

## 4. Desenho experimental

Foram utilizados exclusivamente os dados de desenvolvimento de:

**2018–2024**

O teste final de 2025 permaneceu completamente fora desta etapa.

Foram utilizados quatro folds temporais expanding-window:

| Fold | Treinamento | Validação |
| --- | --- | --- |
| Fold 1 | 2018–2020 | 2021 |
| Fold 2 | 2018–2021 | 2022 |
| Fold 3 | 2018–2022 | 2023 |
| Fold 4 | 2018–2023 | 2024 |

Foram avaliados quatro horizontes:

- H1: +1 semana;
- H2: +2 semanas;
- H3: +3 semanas;
- H4: +4 semanas.

Com dois algoritmos, quatro horizontes e quatro folds, foram realizadas:

**32 execuções de treinamento e validação**

---

## 5. Métricas

A métrica principal utilizada para comparação entre os modelos foi:

**Average Precision (AP)**

A AP foi utilizada como operacionalização da área sob a curva
Precision–Recall.

Também foram calculadas:

- ROC-AUC;
- recall;
- precision;
- F1;
- balanced accuracy;
- Brier Score.

As métricas binárias foram calculadas inicialmente com threshold fixo de:

**0,50**

Esse threshold não foi otimizado a partir dos resultados desta etapa.

---

## 6. Resultado geral

As médias da Average Precision nos quatro folds foram:

| Horizonte | Persistência | Regressão Logística | HistGradientBoosting |
| --- | ---: | ---: | ---: |
| H1 | 0,7849 | 0,9274 | **0,9527** |
| H2 | 0,6466 | 0,8472 | **0,8910** |
| H3 | 0,5439 | 0,7600 | **0,8145** |
| H4 | 0,4640 | 0,6508 | **0,7109** |

O desempenho diminuiu à medida que o horizonte de previsão aumentou.

Esse comportamento era esperado, pois prever o estado epidemiológico com maior
antecedência aumenta a incerteza do problema.

Mesmo assim, os dois modelos de machine learning superaram o baseline de
persistência em todos os horizontes.

O HistGradientBoosting apresentou a maior AP média em H1, H2, H3 e H4.

---

## 7. Resultado por horizonte

### 7.1 H1

Average Precision por ano de validação:

| Validação | Regressão Logística | HistGradientBoosting |
| --- | ---: | ---: |
| 2021 | 0,8897 | **0,9281** |
| 2022 | 0,9342 | **0,9565** |
| 2023 | 0,9234 | **0,9497** |
| 2024 | 0,9624 | **0,9763** |

Em H1, os dois modelos apresentaram desempenho elevado.

O HistGradientBoosting superou a regressão logística nos quatro anos de
validação.

---

### 7.2 H2

| Validação | Regressão Logística | HistGradientBoosting |
| --- | ---: | ---: |
| 2021 | 0,7728 | **0,8384** |
| 2022 | 0,8599 | **0,8983** |
| 2023 | 0,8375 | **0,8844** |
| 2024 | 0,9185 | **0,9431** |

O ganho do modelo não linear permaneceu consistente em H2.

---

### 7.3 H3

| Validação | Regressão Logística | HistGradientBoosting |
| --- | ---: | ---: |
| 2021 | 0,6503 | **0,7311** |
| 2022 | 0,7763 | **0,8249** |
| 2023 | 0,7446 | **0,8030** |
| 2024 | 0,8687 | **0,8989** |

Mesmo com três semanas de antecedência, o HistGradientBoosting continuou
apresentando desempenho superior em todos os folds.

---

### 7.4 H4

| Validação | Regressão Logística | HistGradientBoosting |
| --- | ---: | ---: |
| 2021 | 0,5059 | **0,5934** |
| 2022 | 0,6669 | **0,7190** |
| 2023 | 0,6274 | **0,6944** |
| 2024 | 0,8030 | **0,8368** |

H4 representa o cenário mais difícil entre os horizontes avaliados.

Ainda assim, o HistGradientBoosting manteve vantagem consistente em todos os
anos.

---

## 8. Avaliação de early warning

A análise de early warning considera apenas observações em que:

`risco_elevado(t) = False`

Nesse subconjunto, o município ainda não se encontra em estado de risco elevado
na semana utilizada para realizar a previsão.

O objetivo é avaliar se o modelo consegue antecipar uma futura entrada em
risco.

As médias de Average Precision foram:

| Horizonte | Baseline | Regressão Logística | HistGradientBoosting |
| --- | ---: | ---: | ---: |
| H1 | 0,0333 | 0,2144 | **0,2909** |
| H2 | 0,0587 | 0,2350 | **0,3103** |
| H3 | 0,0806 | 0,2262 | **0,3003** |
| H4 | 0,1001 | 0,1906 | **0,2624** |

A diferença em relação ao baseline de persistência é especialmente importante.

O baseline não possui capacidade de ordenar os municípios do subconjunto de
early warning, pois todos recebem score igual a zero.

Os modelos epidemiológicos, por outro lado, apresentaram Average Precision
substancialmente superior à prevalência do evento.

---

## 9. Recall de early warning com threshold 0,50

Com threshold fixo de 0,50, os recalls médios foram:

| Horizonte | Baseline | Regressão Logística | HistGradientBoosting |
| --- | ---: | ---: | ---: |
| H1 | 0,0000 | 0,0579 | **0,0969** |
| H2 | 0,0000 | 0,0573 | **0,1087** |
| H3 | 0,0000 | 0,0472 | **0,1045** |
| H4 | 0,0000 | 0,0195 | **0,0528** |

Esses valores não devem ser interpretados ainda como desempenho operacional
definitivo do sistema de alerta.

O threshold de 0,50 foi mantido apenas como referência inicial e não foi
otimizado.

A métrica principal desta fase permanece sendo Average Precision, que avalia a
capacidade de ranqueamento do risco sem depender da escolha de threshold.

---

## 10. Comparação entre os algoritmos

O HistGradientBoosting apresentou desempenho superior à regressão logística de
forma consistente.

A vantagem foi observada:

- nos quatro horizontes;
- nos quatro anos de validação;
- na avaliação geral;
- na avaliação de early warning.

Além da maior Average Precision, o HistGradientBoosting apresentou Brier Score
inferior ao da regressão logística em todas as combinações avaliadas, indicando
melhor qualidade das probabilidades produzidas nesta configuração inicial.

Isso sugere que relações não lineares entre histórico de incidência, tendência
recente, posição em relação ao limiar sazonal e demais variáveis
epidemiológicas possuem importância relevante para o problema.

---

## 11. Interpretação

Os resultados mostram que informações epidemiológicas disponíveis até a semana
`t` possuem forte capacidade de prever o estado de risco das semanas futuras.

Parte importante desse desempenho é explicada pela persistência temporal dos
episódios de dengue.

Entretanto, os resultados de early warning mostram que os modelos conseguem
extrair informação adicional antes que o município já esteja classificado como
risco elevado.

Essa distinção é central para o objetivo do projeto.

Um sistema de alerta antecipado precisa fornecer informação adicional antes do
evento, e não apenas identificar que um estado elevado já existente tende a
continuar.

O Modelo A apresenta evidência inicial dessa capacidade.

---

## 12. Papel do Modelo A no experimento

O Modelo A passa a funcionar como referência epidemiológica para a próxima
etapa.

O Modelo B utilizará:

**features epidemiológicas + features meteorológicas**

mantendo constantes:

- definição do target;
- horizontes H1–H4;
- folds temporais;
- algoritmos;
- métricas;
- threshold inicial de 0,50;
- período de desenvolvimento.

Dessa forma, a comparação entre Modelo A e Modelo B permitirá avaliar
diretamente se as informações meteorológicas acrescentam poder preditivo além
do histórico epidemiológico.

---

## 13. Teste final de 2025

O conjunto de 2025 não foi utilizado em nenhuma etapa desta avaliação.

Durante a execução completa foram utilizados exclusivamente:

**2018–2024**

Foram concluídas 32 execuções de treinamento e validação, e o processamento
terminou com status:

**APROVADO**

O teste final de 2025 continuará preservado até que a estratégia de modelagem
seja completamente definida no período de desenvolvimento.

---

## 14. Evidências geradas

Os resultados completos estão registrados em:

- `reports/audits/avaliacao_modelo_a.json`;
- `reports/audits/avaliacao_modelo_a.csv`.

O script responsável pela execução é:

- `scripts/avaliar_modelo_a.py`.

O tempo total registrado para as 32 execuções foi de aproximadamente:

**188,48 segundos**