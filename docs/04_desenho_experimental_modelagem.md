# Desenho Experimental da Modelagem

## 1. Objetivo

Esta etapa define previamente o protocolo experimental utilizado para
treinamento e avaliação dos modelos preditivos do projeto Dengue Alert.

O objetivo principal é estimar o risco epidemiológico elevado de dengue em um
município com horizontes de:

- +1 semana;
- +2 semanas;
- +3 semanas;
- +4 semanas.

O alvo epidemiológico utilizado foi definido previamente e permanece congelado
durante toda a etapa de modelagem.

A avaliação final de 2025 permanece reservada e não deve ser utilizada para
seleção de modelos, features, hiperparâmetros, limiares de decisão ou qualquer
outra escolha metodológica.

---

## 2. Origem temporal da previsão

Para cada município e semana epidemiológica `t`, assume-se que a previsão é
realizada ao final da semana `t`.

Portanto, podem ser utilizadas apenas informações disponíveis até essa semana,
incluindo:

- histórico epidemiológico até `t`;
- estado epidemiológico atual em `t`;
- variáveis meteorológicas observadas até `t`;
- características sazonais e populacionais conhecidas em `t`.

Nenhuma informação de `t+1`, `t+2`, `t+3` ou `t+4` pode ser utilizada como
variável preditora.

Os targets futuros são:

- `target_h1`: risco elevado em `t+1`;
- `target_h2`: risco elevado em `t+2`;
- `target_h3`: risco elevado em `t+3`;
- `target_h4`: risco elevado em `t+4`.

---

## 3. Partições temporais

### 3.1 Desenvolvimento

O período de desenvolvimento compreende:

**2018–2024**

Este período pode ser utilizado para:

- treinamento;
- validação temporal;
- comparação entre algoritmos;
- seleção de hiperparâmetros;
- escolha de limiar de decisão;
- análise de importância das features;
- comparação entre conjuntos de variáveis.

### 3.2 Teste final

O ano de:

**2025**

constitui o conjunto de teste final.

Até o encerramento da seleção dos modelos, não devem ser examinados:

- prevalência dos targets de 2025;
- métricas de desempenho em 2025;
- erros dos modelos em 2025;
- municípios com melhor ou pior desempenho;
- distribuições de resultados condicionadas aos targets de 2025.

A estrutura e a completude das features podem ser auditadas sem examinar os
desfechos.

---

## 4. Validação temporal

Será utilizada validação temporal com janela de treinamento expansiva.

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

Esse procedimento preserva a ordem temporal e impede que observações futuras
participem do treinamento de previsões referentes ao passado.

Não será utilizado train/test split aleatório.

---

## 5. Horizontes

Cada horizonte será tratado como um problema preditivo próprio:

- H1;
- H2;
- H3;
- H4.

As últimas semanas de cada partição que não possuem target futuro válido para
determinado horizonte serão excluídas exclusivamente da avaliação desse
horizonte.

Os modelos não poderão atravessar fronteiras temporais para buscar targets em
outra partição.

---

## 6. Baseline obrigatório

O principal baseline será o de persistência epidemiológica:

> o estado de risco elevado observado na semana atual é utilizado como previsão
> do estado futuro.

Formalmente:

`predicao_h(t) = risco_elevado(t)`

para:

- H1;
- H2;
- H3;
- H4.

Esse baseline é obrigatório devido à persistência temporal já identificada no
alvo epidemiológico.

Qualquer modelo proposto deverá ser comparado diretamente com esse baseline.

---

## 7. Conjuntos de features

### Modelo A — Epidemiológico

Utiliza somente o conjunto de features epidemiológicas previamente definido.

Inclui:

- incidência atual;
- lags epidemiológicos;
- médias móveis;
- incidência acumulada de quatro semanas;
- tendências recentes;
- limiar sazonal P90;
- distância em relação ao limiar;
- estado atual de risco;
- sazonalidade;
- população transformada.

### Modelo B — Epidemiológico + Clima

Utiliza todas as features do Modelo A e adiciona:

- temperatura média;
- umidade relativa;
- precipitação;
- lags climáticos de 0 a 8 semanas;
- médias móveis climáticas;
- precipitação acumulada.

A comparação direta entre A e B será utilizada para investigar se as
informações meteorológicas acrescentam capacidade preditiva além do histórico
epidemiológico.

### Modelo C — Epidemiológico + Clima + Espaço

Modelo exploratório adicional.

Utiliza o conjunto do Modelo B e adiciona:

- latitude da sede municipal;
- longitude da sede municipal.

Esse modelo não substitui a comparação principal entre A e B.

---

## 8. Algoritmos candidatos

Serão avaliadas inicialmente duas famílias de modelos.

### Regressão Logística

Modelo linear probabilístico utilizado como referência estatística e
interpretável.

Será treinado com os mesmos conjuntos A e B para permitir comparação direta.

### HistGradientBoostingClassifier

Modelo não linear baseado em gradient boosting, disponível no Scikit-Learn.

Sua inclusão permite avaliar:

- relações não lineares;
- interações entre variáveis;
- efeitos climáticos potencialmente não lineares.

Também será treinado com os mesmos conjuntos A e B.

Algoritmos adicionais somente serão incluídos caso exista justificativa
metodológica identificada durante o desenvolvimento, sem consulta aos
resultados de 2025.

---

## 9. Pré-processamento

Todo pré-processamento que dependa dos dados deve ser ajustado exclusivamente no
conjunto de treinamento de cada fold.

Isso inclui, quando aplicável:

- imputação;
- padronização;
- normalização;
- seleção de features;
- calibração;
- escolha de hiperparâmetros.

O conjunto de validação nunca poderá participar do ajuste desses
transformadores.

O teste final de 2025 nunca poderá ser utilizado para ajuste.

---

## 10. Métricas principais

A métrica principal para comparação dos modelos será:

**PR-AUC — área sob a curva Precision-Recall**

A escolha se deve à natureza binária e desbalanceada do alvo.

Também serão registradas:

- recall;
- precision;
- F1-score;
- balanced accuracy;
- ROC-AUC;
- Brier score.

A acurácia simples não será utilizada como métrica principal.

---

## 11. Avaliação probabilística e limiar

As métricas independentes de limiar, especialmente PR-AUC e ROC-AUC, serão
utilizadas prioritariamente na comparação entre modelos.

Quando forem necessárias previsões binárias, o limiar de decisão deverá ser
escolhido exclusivamente utilizando dados pertencentes ao período de
desenvolvimento.

Nenhum limiar poderá ser escolhido com base em 2025.

O procedimento utilizado para escolha do limiar será documentado antes da
avaliação final.

---

## 12. Avaliação de early warning

Além da avaliação geral, será realizada uma avaliação secundária de antecipação.

Nessa análise serão consideradas apenas observações em que:

`risco_elevado(t) = False`

O objetivo será verificar se o modelo consegue antecipar a entrada futura em
estado de risco elevado, em vez de apenas reproduzir a persistência de episódios
já em andamento.

Essa avaliação será realizada separadamente para H1, H2, H3 e H4.

---

## 13. Comparações principais

As comparações fundamentais serão:

1. baseline de persistência versus modelos preditivos;
2. Modelo A versus Modelo B;
3. desempenho por horizonte H1–H4;
4. avaliação geral versus avaliação de early warning;
5. regressão logística versus gradient boosting.

O Modelo C espacial será tratado como análise complementar.

---

## 14. Seleção do modelo final

A escolha do modelo final será baseada exclusivamente nos resultados agregados
dos folds temporais de desenvolvimento.

Serão considerados:

- desempenho médio;
- estabilidade entre anos;
- PR-AUC;
- desempenho de early warning;
- calibração;
- complexidade;
- interpretabilidade.

Não será escolhido um modelo apenas pelo melhor resultado isolado em um único
ano.

---

## 15. Avaliação final em 2025

Somente após:

- congelamento do alvo;
- congelamento das features;
- congelamento dos algoritmos;
- congelamento dos hiperparâmetros;
- escolha do modelo;
- definição do limiar de decisão;
- conclusão das análises de desenvolvimento;

o teste final de 2025 poderá ser aberto.

O modelo selecionado será então treinado utilizando o período completo de
desenvolvimento disponível e avaliado uma única vez em 2025.

Os resultados de 2025 serão considerados estimativa final de generalização
temporal e não serão utilizados para novas decisões metodológicas.

---

## 16. Princípio geral

Toda decisão de modelagem deve respeitar a seguinte regra:

> nenhuma informação do futuro pode influenciar uma decisão tomada para o
> passado, e nenhuma informação dos desfechos de 2025 pode influenciar a
> construção ou seleção do modelo final.