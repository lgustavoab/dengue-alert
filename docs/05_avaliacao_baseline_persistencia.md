# Avaliação do Baseline de Persistência

## 1. Objetivo

Este documento registra a primeira avaliação experimental da etapa de
modelagem do projeto Dengue Alert.

O objetivo foi estabelecer uma referência mínima de desempenho que deverá ser
superada ou complementada pelos modelos preditivos posteriores.

O baseline utilizado é o de persistência epidemiológica:

> o estado de risco elevado observado na semana atual é utilizado como previsão
> do estado de risco no horizonte futuro.

Formalmente:

`predicao_h(t) = risco_elevado(t)`

para os horizontes:

- H1: +1 semana;
- H2: +2 semanas;
- H3: +3 semanas;
- H4: +4 semanas.

---

## 2. Dados utilizados

A avaliação utilizou exclusivamente o período de desenvolvimento:

**2018–2024**

Foram considerados:

- 2.032.685 registros município-semana;
- 5.569 municípios;
- quatro folds temporais expanding-window;
- quatro horizontes de previsão.

O teste final de 2025 não foi utilizado.

---

## 3. Validação temporal

O baseline foi avaliado nos quatro folds previamente definidos:

### Fold 1

Treino:

**2018–2020**

Validação:

**2021**

### Fold 2

Treino:

**2018–2021**

Validação:

**2022**

### Fold 3

Treino:

**2018–2022**

Validação:

**2023**

### Fold 4

Treino:

**2018–2023**

Validação:

**2024**

Como o baseline de persistência não possui parâmetros treináveis, o período de
treino não é utilizado para ajuste de modelo. Entretanto, as mesmas partições
foram mantidas para garantir comparabilidade posterior com os modelos de
machine learning.

---

## 4. Avaliação geral

A avaliação geral considera todas as semanas de validação com target futuro
disponível.

Os resultados médios dos quatro folds foram:

| Horizonte | AP | Recall | F1 | Balanced Accuracy |
| --- | ---: | ---: | ---: | ---: |
| H1 | 0,7849 | 0,8683 | 0,8712 | 0,9180 |
| H2 | 0,6466 | 0,7691 | 0,7748 | 0,8562 |
| H3 | 0,5439 | 0,6851 | 0,6925 | 0,8037 |
| H4 | 0,4640 | 0,6109 | 0,6190 | 0,7571 |

O desempenho diminui progressivamente conforme aumenta o horizonte de previsão.

Esse comportamento é compatível com a persistência temporal previamente
observada no alvo epidemiológico: quanto menor o horizonte, maior a
probabilidade de o estado observado na semana atual permanecer válido no
futuro próximo.

---

## 5. Resultados por fold

### H1

| Validação | AP | Recall |
| --- | ---: | ---: |
| 2021 | 0,7246 | 0,8352 |
| 2022 | 0,7892 | 0,8715 |
| 2023 | 0,7734 | 0,8603 |
| 2024 | 0,8523 | 0,9064 |

### H2

| Validação | AP | Recall |
| --- | ---: | ---: |
| 2021 | 0,5508 | 0,7104 |
| 2022 | 0,6513 | 0,7729 |
| 2023 | 0,6281 | 0,7548 |
| 2024 | 0,7561 | 0,8384 |

### H3

| Validação | AP | Recall |
| --- | ---: | ---: |
| 2021 | 0,4234 | 0,6042 |
| 2022 | 0,5489 | 0,6888 |
| 2023 | 0,5223 | 0,6669 |
| 2024 | 0,6809 | 0,7804 |

### H4

| Validação | AP | Recall |
| --- | ---: | ---: |
| 2021 | 0,3278 | 0,5110 |
| 2022 | 0,4683 | 0,6131 |
| 2023 | 0,4403 | 0,5895 |
| 2024 | 0,6195 | 0,7301 |

Os resultados mostram variação relevante entre os anos de validação.

Essa variabilidade reforça a decisão metodológica de avaliar os modelos em
múltiplos folds temporais e evitar selecionar uma solução com base no melhor
resultado obtido em apenas um ano.

---

## 6. Avaliação de early warning

A avaliação secundária de early warning considera apenas observações em que:

`risco_elevado(t) = False`

Nesse subconjunto, o objetivo é medir a capacidade de antecipar uma futura
entrada no estado de risco elevado.

Como o baseline utiliza exclusivamente o estado atual como previsão, todas as
observações desse subconjunto recebem:

`predicao = False`

e:

`score = 0`

Consequentemente, o baseline não consegue antecipar nenhuma entrada futura em
risco.

Os resultados médios foram:

| Horizonte | Prevalência futura | AP | Recall |
| --- | ---: | ---: | ---: |
| H1 | 0,0333 | 0,0333 | 0,0000 |
| H2 | 0,0587 | 0,0587 | 0,0000 |
| H3 | 0,0806 | 0,0806 | 0,0000 |
| H4 | 0,1001 | 0,1001 | 0,0000 |

O valor de Average Precision coincide com a prevalência do evento porque todas
as observações recebem o mesmo score.

---

## 7. Interpretação

O baseline demonstra que o estado epidemiológico atual contém grande poder
preditivo sobre o futuro próximo.

Em H1, a persistência apresenta desempenho particularmente elevado, com AP
média de 0,7849 e recall médio de 0,8683.

Entretanto, esse desempenho geral não significa capacidade de antecipação.

Quando a análise é restrita às semanas em que o município ainda não está em
estado de risco elevado, o recall do baseline é zero em todos os horizontes.

Isso evidencia a diferença entre duas tarefas:

1. prever a continuidade de um estado elevado já existente;
2. antecipar a entrada futura em um novo estado de risco elevado.

A segunda tarefa representa o componente mais relevante para um sistema de
alerta antecipado.

---

## 8. Critério para os modelos seguintes

Os modelos de machine learning deverão ser comparados com o baseline em duas
perspectivas complementares.

### Avaliação geral

O objetivo será verificar se os modelos conseguem superar ou manter o forte
desempenho da persistência na previsão do estado futuro.

### Early warning

O objetivo será verificar se os modelos conseguem identificar antecipadamente
semanas que entrarão em risco elevado quando o município ainda se encontra em
estado normal.

Um modelo que apenas reproduza a persistência epidemiológica pode apresentar
bom desempenho geral, mas não necessariamente fornecer valor adicional como
sistema de alerta antecipado.

---

## 9. Arquivos de evidência

A execução completa foi registrada em:

- `reports/audits/avaliacao_baseline_persistencia.json`;
- `reports/audits/avaliacao_baseline_persistencia.csv`.

Foram avaliadas 16 combinações de fold e horizonte:

**4 folds × 4 horizontes**

O processamento foi concluído com status:

**APROVADO**

---

## 10. Proteção do teste final

O conjunto de teste final de 2025 permaneceu completamente fora desta análise.

Nenhuma métrica, prevalência ou resultado baseado nos targets de 2025 foi
consultado.

A seleção dos modelos continuará sendo realizada exclusivamente com os dados do
período de desenvolvimento.