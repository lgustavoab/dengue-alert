# Seleção Operacional, Calibração e Threshold

## 1. Objetivo

Esta etapa definiu a estratégia operacional do modelo preditivo selecionado
durante o período de desenvolvimento do projeto Dengue Alert.

O candidato principal após a comparação experimental foi:

**Modelo A + HistGradientBoostingClassifier**

Características:

- 23 features epidemiológicas;
- sem features climáticas;
- sem latitude ou longitude;
- horizontes H1, H2, H3 e H4;
- probabilidades originalmente produzidas pelo classificador;
- validação temporal expanding-window.

O conjunto final de 2025 permaneceu reservado durante toda esta etapa.

---

## 2. Predições out-of-fold

Para permitir calibração e seleção de thresholds sem utilizar o conjunto final
de teste, foram geradas predições out-of-fold temporais.

O procedimento utilizado foi:

| Fold | Treinamento | Predição OOF |
| --- | --- | --- |
| Fold 1 | 2018–2020 | 2021 |
| Fold 2 | 2018–2021 | 2022 |
| Fold 3 | 2018–2022 | 2023 |
| Fold 4 | 2018–2023 | 2024 |

As predições foram produzidas separadamente para:

- H1: +1 semana;
- H2: +2 semanas;
- H3: +3 semanas;
- H4: +4 semanas.

Foram produzidas:

**4.410.648 predições OOF**

Nenhuma observação de 2025 participou desse processo.

---

## 3. Auditoria de reprodutibilidade das predições OOF

As métricas produzidas a partir das novas predições OOF foram comparadas com os
resultados previamente registrados durante a avaliação do Modelo A.

Foram auditadas:

**16 combinações de horizonte × fold**

A diferença absoluta máxima encontrada foi:

**1,110 × 10⁻¹⁶**

A tolerância previamente estabelecida foi:

**1 × 10⁻¹⁰**

Portanto, as predições OOF reproduziram os resultados originais do modelo
dentro da precisão numérica esperada.

Status:

**APROVADO**

---

# 4. Avaliação de calibração

Foram comparadas três estratégias:

1. `raw`;
2. `sigmoid`;
3. `isotonic`.

`raw` representa a utilização direta das probabilidades produzidas pelo
HistGradientBoosting.

A calibração foi avaliada com backtest temporal progressivo.

### Avaliação de 2022

Calibração:

**2021**

Avaliação:

**2022**

### Avaliação de 2023

Calibração:

**2021–2022**

Avaliação:

**2023**

### Avaliação de 2024

Calibração:

**2021–2023**

Avaliação:

**2024**

A métrica principal para essa decisão foi o:

**Brier Score geral**

---

## 5. Regra de seleção da calibração

Antes da execução foi estabelecida a seguinte regra:

> Um método calibrado somente seria adotado se apresentasse Brier Score menor
> que `raw` nos três anos de backtest e também Brier Score médio inferior.

A regra foi definida previamente para evitar escolha posterior baseada apenas
nos resultados observados.

---

## 6. Resultados da calibração

### H1

| Método | Brier médio | Delta vs raw | Anos melhores que raw |
| --- | ---: | ---: | ---: |
| raw | **0,033412** | 0,000000 | referência |
| sigmoid | 0,033505 | +0,000093 | 0/3 |
| isotonic | 0,033519 | +0,000107 | 2/3 |

Selecionado:

**raw**

### H2

| Método | Brier médio | Delta vs raw | Anos melhores que raw |
| --- | ---: | ---: | ---: |
| raw | **0,059139** | 0,000000 | referência |
| sigmoid | 0,059317 | +0,000178 | 1/3 |
| isotonic | 0,059311 | +0,000172 | 2/3 |

Selecionado:

**raw**

### H3

| Método | Brier médio | Delta vs raw | Anos melhores que raw |
| --- | ---: | ---: | ---: |
| raw | **0,084154** | 0,000000 | referência |
| sigmoid | 0,084461 | +0,000307 | 2/3 |
| isotonic | 0,084404 | +0,000250 | 2/3 |

Selecionado:

**raw**

### H4

| Método | Brier médio | Delta vs raw | Anos melhores que raw |
| --- | ---: | ---: | ---: |
| raw | **0,110771** | 0,000000 | referência |
| sigmoid | 0,111257 | +0,000486 | 2/3 |
| isotonic | 0,111185 | +0,000414 | 2/3 |

Selecionado:

**raw**

---

## 7. Decisão sobre calibração

Nenhum método calibrado satisfez a regra previamente estabelecida.

Portanto, a estratégia final utiliza:

**probabilidades raw do HistGradientBoosting**

Essa decisão não significa que as probabilidades sejam perfeitamente
calibradas.

Significa apenas que as técnicas `sigmoid` e `isotonic` avaliadas não
demonstraram benefício temporal consistente suficiente para substituir as
probabilidades originais.

---

# 8. Seleção operacional de threshold

O threshold de `0,50`, utilizado inicialmente nas comparações de modelos, não
foi considerado automaticamente adequado para o sistema de alerta.

A seleção operacional foi realizada no subconjunto:

`risco_elevado(t) = False`

Esse subconjunto representa situações em que o município ainda não estava em
risco elevado na semana em que a previsão foi realizada.

O critério definido previamente foi:

**maximizar o F1 no subconjunto de early warning**

Em caso de empate numérico entre thresholds com mesmo F1, foi adotado:

**o maior threshold**

O objetivo da regra de desempate foi reduzir alertas sem sacrificar o F1
máximo obtido.

---

## 9. Backtest temporal dos thresholds

Antes da definição final dos thresholds foi realizado um backtest temporal
progressivo.

### Avaliação em 2022

Seleção do threshold:

**OOF 2021**

Aplicação:

**OOF 2022**

### Avaliação em 2023

Seleção:

**OOF 2021–2022**

Aplicação:

**OOF 2023**

### Avaliação em 2024

Seleção:

**OOF 2021–2023**

Aplicação:

**OOF 2024**

Foram realizadas:

**12 avaliações temporais**

correspondentes a:

**4 horizontes × 3 anos**

---

## 10. Resultados do backtest operacional

### H1

- threshold médio: 0,182294;
- faixa: 0,174670–0,197508;
- F1 médio: 0,373162;
- precision média: 0,345123;
- recall médio: 0,411017;
- proporção média de alertas: 4,75%;
- F1 médio com threshold 0,50: 0,173387;
- ganho médio de F1: +0,199775;
- anos superiores a 0,50: 3/3.

### H2

- threshold médio: 0,200268;
- faixa: 0,191824–0,217157;
- F1 médio: 0,380581;
- precision média: 0,390196;
- recall médio: 0,374415;
- proporção média de alertas: 6,70%;
- F1 médio com threshold 0,50: 0,189745;
- ganho médio de F1: +0,190835;
- anos superiores a 0,50: 3/3.

### H3

- threshold médio: 0,174257;
- faixa: 0,167690–0,184759;
- F1 médio: 0,356897;
- precision média: 0,343488;
- recall médio: 0,375462;
- proporção média de alertas: 10,55%;
- F1 médio com threshold 0,50: 0,184139;
- ganho médio de F1: +0,172758;
- anos superiores a 0,50: 3/3.

### H4

- threshold médio: 0,160546;
- faixa: 0,157138–0,167352;
- F1 médio: 0,336575;
- precision média: 0,283476;
- recall médio: 0,418567;
- proporção média de alertas: 17,59%;
- F1 médio com threshold 0,50: 0,103866;
- ganho médio de F1: +0,232709;
- anos superiores a 0,50: 3/3.

---

## 11. Interpretação do backtest

O procedimento de seleção de threshold apresentou melhoria de F1 em relação ao
threshold fixo de 0,50 nos três anos avaliados e nos quatro horizontes.

Além disso, os thresholds permaneceram em faixas relativamente próximas entre
os diferentes períodos temporais.

Isso indica estabilidade suficiente para utilizar a regra como procedimento de
seleção operacional.

Horizontes mais longos apresentaram maior proporção de alertas.

Esse comportamento é compatível com a maior dificuldade de antecipação em
horizontes mais distantes e com o compromisso entre precision e recall
produzido pela maximização do F1.

---

# 12. Thresholds operacionais finais

Após a aprovação do procedimento no backtest temporal, os thresholds finais
foram calculados utilizando todas as predições OOF de desenvolvimento entre
2021 e 2024.

A seleção permaneceu restrita ao subconjunto de early warning.

| Horizonte | Threshold final |
| --- | ---: |
| H1 | **0,187687** |
| H2 | **0,190783** |
| H3 | **0,167991** |
| H4 | **0,157138** |

Esses valores passam a constituir os thresholds congelados para a avaliação
final.

---

## 13. Características dos thresholds finais

### H1

- observações early warning: 898.785;
- positivos: 28.720;
- prevalência: 3,20%;
- precision de seleção: 0,339341;
- recall de seleção: 0,402542;
- F1 de seleção: 0,368249;
- proporção de alertas: 3,79%.

### H2

- observações early warning: 880.738;
- positivos: 49.629;
- prevalência: 5,63%;
- precision de seleção: 0,371967;
- recall de seleção: 0,381853;
- F1 de seleção: 0,376846;
- proporção de alertas: 5,78%.

### H3

- observações early warning: 862.734;
- positivos: 66.703;
- prevalência: 7,73%;
- precision de seleção: 0,325814;
- recall de seleção: 0,378739;
- F1 de seleção: 0,350289;
- proporção de alertas: 8,99%.

### H4

- observações early warning: 844.617;
- positivos: 81.120;
- prevalência: 9,60%;
- precision de seleção: 0,267915;
- recall de seleção: 0,414608;
- F1 de seleção: 0,325497;
- proporção de alertas: 14,86%.

---

## 14. Uso correto das métricas de seleção

As métricas calculadas utilizando o conjunto OOF completo de 2021–2024 não
devem ser interpretadas como estimativas independentes do desempenho final.

Esse conjunto foi utilizado para selecionar os thresholds definitivos.

A estimativa independente de desempenho será obtida exclusivamente no teste
final de 2025.

O backtest progressivo de 2022–2024 permanece como a principal evidência de
que o procedimento de seleção de threshold apresenta capacidade de
generalização temporal dentro do período de desenvolvimento.

---

# 15. Estratégia congelada antes do teste final

Antes da abertura de 2025, ficam definidos:

### Algoritmo

**HistGradientBoostingClassifier**

### Features

**Modelo A — 23 features epidemiológicas**

### Clima

**Não utilizado no modelo final**

### Calibração

**Não adotada**

### Probabilidades

**raw**

### Threshold H1

**0,187687**

### Threshold H2

**0,190783**

### Threshold H3

**0,167991**

### Threshold H4

**0,157138**

### Critério operacional

**máximo F1 no subconjunto de early warning**

Nenhuma dessas decisões poderá ser alterada utilizando resultados do teste
final de 2025.

---

# 16. Proteção do teste final

Durante toda a seleção operacional:

- targets de 2025 não foram utilizados;
- prevalência dos targets de 2025 não foi inspecionada;
- 2025 não participou da seleção de algoritmo;
- 2025 não participou da seleção de features;
- 2025 não participou da avaliação de calibração;
- 2025 não participou da seleção dos thresholds.

O conjunto de 2025 permaneceu completamente reservado.

---

# 17. Evidências geradas

Predições OOF:

- `data/processed/predicoes_oof_modelo_a_hgb_2021_2024.parquet`.

Auditoria da geração OOF:

- `reports/audits/auditoria_predicoes_oof_modelo_a_hgb.json`.

Auditoria de reprodutibilidade:

- `reports/audits/auditoria_reprodutibilidade_oof.json`.

Avaliação de calibração:

- `reports/audits/avaliacao_calibracao_temporal.csv`;
- `reports/audits/avaliacao_calibracao_temporal.json`.

Backtest de threshold:

- `reports/audits/avaliacao_threshold_temporal.csv`;
- `reports/audits/avaliacao_threshold_temporal.json`.

Thresholds finais:

- `reports/audits/thresholds_operacionais_finais.csv`;
- `reports/audits/thresholds_operacionais_finais.json`.

Scripts:

- `scripts/gerar_predicoes_oof_modelo_finalista.py`;
- `scripts/auditar_reprodutibilidade_oof.py`;
- `scripts/avaliar_calibracao_temporal.py`;
- `scripts/avaliar_threshold_temporal.py`;
- `scripts/definir_thresholds_operacionais_finais.py`.

Infraestrutura:

- `src/dengue_alert/evaluation/calibration.py`;
- `src/dengue_alert/evaluation/thresholds.py`.

Status da etapa:

**APROVADO**