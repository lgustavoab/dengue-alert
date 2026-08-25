# Avaliação do Modelo B e Comparação do Valor Preditivo do Clima

## 1. Objetivo

Este documento registra a avaliação do Modelo B do projeto Dengue Alert e sua
comparação direta com o Modelo A.

O objetivo principal desta etapa foi responder à seguinte questão experimental:

> A inclusão de variáveis meteorológicas acrescenta poder preditivo além das
> informações epidemiológicas já disponíveis?

Para tornar essa comparação válida, os Modelos A e B utilizaram exatamente o
mesmo desenho experimental.

A única diferença entre eles foi o conjunto de features utilizado.

---

## 2. Definição dos modelos

### 2.1 Modelo A

O Modelo A utiliza:

- 23 features epidemiológicas e temporais.

Essas variáveis representam:

- incidência atual;
- lags de incidência;
- médias móveis;
- incidência acumulada;
- tendências recentes;
- relação com o limiar sazonal;
- estado atual de risco;
- sazonalidade;
- população.

### 2.2 Modelo B

O Modelo B mantém todas as 23 features epidemiológicas do Modelo A e acrescenta
36 features meteorológicas.

Total:

**59 features**

As variáveis climáticas representam:

- temperatura média;
- umidade relativa;
- precipitação;
- lags climáticos de 0 a 8 semanas;
- médias móveis de temperatura;
- médias móveis de umidade;
- precipitação acumulada em diferentes janelas.

Nenhuma variável espacial de latitude ou longitude foi incluída nesta etapa.

---

## 3. Desenho experimental

A comparação foi realizada exclusivamente no conjunto de desenvolvimento:

**2018–2024**

O conjunto final de 2025 permaneceu completamente fora da análise.

Foram mantidos os mesmos quatro folds temporais:

| Fold | Treinamento | Validação |
| --- | --- | --- |
| Fold 1 | 2018–2020 | 2021 |
| Fold 2 | 2018–2021 | 2022 |
| Fold 3 | 2018–2022 | 2023 |
| Fold 4 | 2018–2023 | 2024 |

Também foram mantidos os quatro horizontes:

- H1: +1 semana;
- H2: +2 semanas;
- H3: +3 semanas;
- H4: +4 semanas.

Os algoritmos utilizados foram os mesmos do Modelo A:

- Logistic Regression;
- HistGradientBoostingClassifier.

O threshold inicial das métricas binárias permaneceu fixo em:

**0,50**

A métrica principal continuou sendo:

**Average Precision (AP)**

---

## 4. Execução do Modelo B

Foram realizadas:

**32 execuções**

correspondentes a:

**4 horizontes × 4 folds × 2 algoritmos**

A execução completa foi concluída com status:

**APROVADO**

O conjunto final de 2025 não foi utilizado.

---

## 5. Comparação pareada A × B

A comparação foi realizada de forma pareada.

Cada resultado do Modelo A foi comparado com o resultado correspondente do
Modelo B utilizando exatamente a mesma combinação de:

- algoritmo;
- horizonte;
- fold;
- ano de validação.

Foram comparadas:

**32 execuções pareadas**

e:

**8 combinações algoritmo × horizonte**

O delta utilizado foi definido como:

`Delta = Modelo B - Modelo A`

Portanto:

- delta positivo em AP representa vantagem do Modelo B;
- delta negativo em AP representa vantagem do Modelo A;
- para Brier Score, valores menores são melhores.

---

# 6. HistGradientBoosting

## 6.1 Average Precision geral

| Horizonte | Modelo A | Modelo B | Delta B − A | Folds com B melhor |
| --- | ---: | ---: | ---: | ---: |
| H1 | 0,952669 | 0,952875 | +0,000207 | 3/4 |
| H2 | 0,891050 | 0,891434 | +0,000384 | 2/4 |
| H3 | 0,814459 | 0,814948 | +0,000489 | 3/4 |
| H4 | 0,710913 | 0,710883 | −0,000030 | 2/4 |

A inclusão das variáveis climáticas produziu pequenas diferenças positivas em
H1, H2 e H3.

Entretanto, os ganhos foram inferiores a 0,0005 de Average Precision.

Em H4, o desempenho médio do Modelo B foi ligeiramente inferior ao Modelo A.

Dessa forma, a avaliação geral mostra desempenho praticamente equivalente
entre os dois conjuntos de features.

---

## 6.2 Average Precision de early warning

| Horizonte | Modelo A | Modelo B | Delta B − A | Folds com B melhor |
| --- | ---: | ---: | ---: | ---: |
| H1 | 0,290844 | 0,287594 | −0,003250 | 1/4 |
| H2 | 0,310261 | 0,309468 | −0,000793 | 1/4 |
| H3 | 0,300303 | 0,300140 | −0,000163 | 1/4 |
| H4 | 0,262359 | 0,261607 | −0,000752 | 2/4 |

Na avaliação de early warning, o Modelo B apresentou AP média inferior ao
Modelo A em todos os quatro horizontes.

Em H1, H2 e H3, o Modelo B superou o Modelo A em apenas um dos quatro folds.

Em H4 houve dois folds favoráveis para cada modelo, mas a média permaneceu
ligeiramente favorável ao Modelo A.

Portanto, não foi observada evidência descritiva de ganho consistente de
antecipação decorrente da inclusão das variáveis meteorológicas.

---

## 6.3 Brier Score

| Horizonte | Modelo A | Modelo B | Delta B − A |
| --- | ---: | ---: | ---: |
| H1 | 0,029175 | 0,029274 | +0,000099 |
| H2 | 0,051639 | 0,051752 | +0,000113 |
| H3 | 0,073433 | 0,073496 | +0,000064 |
| H4 | 0,096601 | 0,096730 | +0,000129 |

Como valores menores de Brier Score representam melhor qualidade das
probabilidades, o Modelo A apresentou resultado ligeiramente melhor nos quatro
horizontes.

As diferenças são pequenas, mas não indicam vantagem de calibração decorrente
da inclusão do clima.

---

# 7. Logistic Regression

## 7.1 Average Precision geral

| Horizonte | Modelo A | Modelo B | Delta B − A | Folds com B melhor |
| --- | ---: | ---: | ---: | ---: |
| H1 | 0,927433 | 0,926477 | −0,000955 | 1/4 |
| H2 | 0,847174 | 0,844779 | −0,002395 | 1/4 |
| H3 | 0,759968 | 0,756797 | −0,003170 | 1/4 |
| H4 | 0,650806 | 0,647164 | −0,003642 | 1/4 |

Para a regressão logística, o Modelo B apresentou desempenho médio inferior ao
Modelo A nos quatro horizontes.

Em cada horizonte, apenas um dos quatro folds apresentou AP geral superior com
a inclusão do clima.

A diferença tornou-se progressivamente maior em horizontes mais longos.

---

## 7.2 Average Precision de early warning

| Horizonte | Modelo A | Modelo B | Delta B − A | Folds com B melhor |
| --- | ---: | ---: | ---: | ---: |
| H1 | 0,214382 | 0,206114 | −0,008269 | 1/4 |
| H2 | 0,235061 | 0,224840 | −0,010221 | 1/4 |
| H3 | 0,226231 | 0,215719 | −0,010513 | 1/4 |
| H4 | 0,190559 | 0,179132 | −0,011427 | 1/4 |

A redução de desempenho foi mais clara na avaliação de early warning.

A inclusão das 36 features meteorológicas reduziu a AP média em todos os
horizontes.

Apenas um dos quatro folds apresentou vantagem para o Modelo B em cada
horizonte.

---

## 7.3 Brier Score

| Horizonte | Modelo A | Modelo B | Delta B − A |
| --- | ---: | ---: | ---: |
| H1 | 0,036618 | 0,036679 | +0,000061 |
| H2 | 0,062449 | 0,062673 | +0,000224 |
| H3 | 0,084316 | 0,084618 | +0,000302 |
| H4 | 0,106148 | 0,106582 | +0,000434 |

O Brier Score também foi ligeiramente pior no Modelo B nos quatro horizontes.

---

# 8. Interpretação do valor incremental do clima

Os resultados não demonstraram ganho preditivo incremental relevante com a
inclusão das variáveis meteorológicas.

No HistGradientBoosting, a AP geral aumentou ligeiramente em H1, H2 e H3, mas
as diferenças foram inferiores a 0,0005.

Esses pequenos ganhos não foram acompanhados por melhora na avaliação de early
warning.

Ao contrário, a AP de early warning apresentou redução média nos quatro
horizontes.

Na regressão logística, a inclusão do clima apresentou desempenho inferior
tanto na avaliação geral quanto em early warning.

O Brier Score também apresentou pequena piora no Modelo B para os dois
algoritmos e em todos os horizontes.

---

## 9. O que este resultado não significa

Os resultados não devem ser interpretados como evidência de que temperatura,
umidade ou precipitação não possuem relação com a dinâmica epidemiológica da
dengue.

A análise responde a uma questão mais específica:

> As variáveis meteorológicas utilizadas neste projeto acrescentam informação
> preditiva útil quando o modelo já possui acesso ao histórico epidemiológico
> recente do município?

Dentro do período, features, algoritmos e horizontes avaliados, o ganho
incremental observado foi inexistente ou muito pequeno.

É possível que parte da informação relacionada ao clima já esteja
indiretamente refletida no comportamento recente da incidência epidemiológica.

Também é possível que outras representações climáticas, escalas temporais ou
modelos produzam resultados diferentes.

Essas possibilidades não foram testadas nesta comparação e não devem ser
inferidas a partir dos resultados atuais.

---

# 10. Complexidade versus desempenho

O Modelo A utiliza:

**23 features**

O Modelo B utiliza:

**59 features**

Portanto, o Modelo B adiciona 36 variáveis e aumenta consideravelmente a
dimensionalidade do problema.

Apesar desse aumento de complexidade, não foi observada melhoria consistente na
capacidade de antecipação.

Pelo princípio de parcimônia, quando dois modelos apresentam desempenho
equivalente, deve ser favorecida a solução mais simples, desde que ela atenda
aos objetivos preditivos.

Nesse contexto, os resultados atuais favorecem a utilização das features do
Modelo A.

---

# 11. Algoritmo candidato principal

Entre os algoritmos avaliados, o HistGradientBoosting apresentou desempenho
superior à regressão logística no Modelo A e no Modelo B.

No Modelo A, ele apresentou:

- maior Average Precision geral;
- maior Average Precision de early warning;
- melhor desempenho em todos os horizontes.

A comparação A × B também mostrou que a adição do clima não produz melhoria
relevante sobre essa configuração.

Dessa forma, o candidato principal após esta etapa passa a ser:

**HistGradientBoosting + features epidemiológicas do Modelo A**

Essa seleção permanece restrita ao período de desenvolvimento.

O conjunto final de 2025 continua preservado.

---

# 12. Conclusão da comparação A × B

A comparação experimental indica que:

**o histórico epidemiológico recente é a principal fonte de informação
preditiva entre as variáveis avaliadas para horizontes de uma a quatro
semanas.**

A inclusão das variáveis meteorológicas:

- não produziu ganho consistente de Average Precision geral;
- não melhorou a Average Precision de early warning;
- apresentou Brier Score ligeiramente pior;
- aumentou a complexidade do modelo de 23 para 59 features.

Por esse motivo, o Modelo B não substitui o Modelo A como configuração
preferencial nesta etapa.

O Modelo A com HistGradientBoosting permanece como principal candidato para as
etapas seguintes de desenvolvimento.

---

# 13. Proteção do teste final

Nenhuma informação proveniente do target de 2025 foi utilizada nesta
comparação.

A avaliação A × B foi realizada exclusivamente com os quatro folds temporais
de desenvolvimento entre 2018 e 2024.

O conjunto de 2025 permanece reservado para avaliação final após a definição
completa da estratégia de modelagem.

---

# 14. Evidências geradas

Resultados completos do Modelo B:

- `reports/audits/avaliacao_modelo_b.csv`;
- `reports/audits/avaliacao_modelo_b.json`.

Comparação pareada A × B:

- `reports/audits/comparacao_modelos_ab.csv`;
- `reports/audits/comparacao_modelos_ab.json`.

Scripts utilizados:

- `scripts/avaliar_modelo_b.py`;
- `scripts/comparar_modelos_ab.py`.

A auditoria comparativa foi concluída com status:

**APROVADO**