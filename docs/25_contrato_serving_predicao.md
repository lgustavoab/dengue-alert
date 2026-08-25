# 25 — Contrato de serving das predições retrospectivas

## 1. Objetivo

Este documento define a semântica e os contratos iniciais da camada de serving
dos resultados preditivos do projeto Dengue Alert.

O serving preditivo deve transformar os resultados finais já congelados do
modelo em artefatos adequados ao consumo pela aplicação.

Esta etapa não realiza novo treinamento, nova seleção de modelo, recalibração,
otimização de thresholds ou qualquer uso adicional de 2025 para ajuste do
modelo.

A fonte preditiva é exclusivamente o resultado final já aprovado da avaliação
retrospectiva de 2025.

---

## 2. Fonte principal

O artefato final de predições é:

```text
data/processed/predicoes_avaliacao_final_2025.parquet
```

O arquivo possui:

```text
1.124.938 linhas
5.569 municípios
4 horizontes preditivos
0 chaves duplicadas
0 valores ausentes
```

As evidências consolidadas da avaliação estão registradas em:

```text
reports/audits/avaliacao_final_2025.json
reports/audits/avaliacao_final_2025.csv
```

---

## 3. Modelo final

O modelo final utilizado nas predições é:

```text
Algoritmo:
HistGradientBoostingClassifier

Conjunto de features:
Modelo A — 23 epidemiológicas

Calibração adicional:
não adotada

Probabilidades:
raw
```

A ausência de calibração adicional significa que o campo `score` corresponde à
probabilidade bruta produzida pelo modelo final.

Nenhuma transformação de calibração deve ser aplicada novamente na camada de
serving.

---

## 4. Protocolo temporal

O protocolo final está congelado como:

```text
Desenvolvimento:
2018–2024

Teste final:
2025

Thresholds congelados antes do teste final:
sim

Teste final utilizado na seleção do modelo:
não
```

Portanto, 2025 representa uma avaliação final retrospectiva fora do período de
desenvolvimento.

A camada de serving não pode utilizar os resultados de 2025 para reajustar o
modelo ou seus thresholds.

---

## 5. O que o modelo prevê

O modelo não prevê o número futuro de casos de dengue.

O objetivo preditivo é estimar a probabilidade de um município apresentar
**estado de risco epidemiológico elevado em uma semana futura**.

Assim:

```text
score
```

representa a probabilidade produzida pelo modelo para o estado futuro definido
pelo target de risco elevado.

A interface não deverá apresentar `score` como:

```text
casos previstos
número esperado de casos
incidência prevista
quantidade prevista de pessoas infectadas
```

Essas interpretações não fazem parte do modelo desenvolvido.

---

## 6. Horizontes preditivos

São utilizados quatro horizontes:

```text
H1 = +1 semana
H2 = +2 semanas
H3 = +3 semanas
H4 = +4 semanas
```

Cada horizonte possui seu próprio modelo operacional equivalente e seu próprio
threshold congelado.

---

## 7. Thresholds congelados

Os thresholds oficiais são:

| Horizonte | Threshold |
|---|---:|
| H1 | 0.187687 |
| H2 | 0.190783 |
| H3 | 0.167991 |
| H4 | 0.157138 |

Esses valores foram definidos durante o desenvolvimento e permaneceram
congelados antes da abertura do teste final de 2025.

O serving não deve procurar novos thresholds.

---

## 8. Regra da classificação binária

O campo final:

```text
predicao
```

obedece exatamente à regra:

```text
predicao = score >= threshold
```

A auditoria das 1.124.938 linhas confirmou:

```text
divergências entre predicao e score >= threshold = 0
```

Portanto, o campo `predicao` existente no artefato final é a classificação
binária oficial.

O serving poderá preservar diretamente esse valor.

---

## 9. Domínio das probabilidades

A auditoria final confirmou:

```text
score < 0 = 0
score > 1 = 0
```

Portanto, os scores estão contidos no intervalo:

```text
0 <= score <= 1
```

Na interface, o valor poderá ser apresentado como probabilidade percentual,
desde que a transformação seja exclusivamente de apresentação:

```text
score × 100
```

Exemplo:

```text
score = 0.347

apresentação:
34,7%
```

O valor persistido no serving deve permanecer na escala original de 0 a 1.

---

## 10. Campos do artefato final

O Parquet final contém os seguintes campos:

```text
codigo_ibge_7
nome_municipio_ibge
nome_uf_ibge
ano_epidemiologico
semana_epidemiologica
data_inicio_semana
risco_elevado
target
horizonte
score
threshold
predicao
```

---

## 11. Semântica dos campos

### `codigo_ibge_7`

Identificador territorial principal.

Deve ser tratado como string de sete dígitos.

Esse campo é a chave territorial da aplicação.

Nomes de municípios não são identificadores únicos, pois municípios diferentes
podem possuir o mesmo nome em UFs distintas.

---

### `nome_municipio_ibge`

Nome oficial da unidade territorial associado ao código IBGE.

É um campo de apresentação.

---

### `nome_uf_ibge`

Nome da unidade federativa.

É um campo de apresentação.

---

### `ano_epidemiologico`

Ano epidemiológico da semana utilizada como origem da previsão.

No artefato final:

```text
2025
```

---

### `semana_epidemiologica`

Semana epidemiológica utilizada como origem da previsão.

Não representa diretamente a semana futura do target.

---

### `data_inicio_semana`

Data de início da semana epidemiológica de origem.

Deve ser serializada em formato ISO:

```text
YYYY-MM-DD
```

---

### `risco_elevado`

Estado observado de risco elevado na semana de origem.

Esse campo responde:

> O município já estava em estado de risco elevado no momento em que a previsão
> foi produzida?

Ele não é a previsão futura.

---

### `target`

Estado de risco elevado observado no horizonte futuro correspondente.

Esse é o valor real utilizado para avaliar retrospectivamente a previsão.

Exemplo:

```text
horizonte = 3
```

significa que `target` representa o estado observado três semanas à frente da
semana de origem.

O `target` existe porque 2025 já é um período histórico observado.

Em uma execução realmente prospectiva futura, o target ainda não estaria
disponível no momento da previsão.

---

### `horizonte`

Número de semanas à frente:

```text
1
2
3
4
```

---

### `score`

Probabilidade bruta produzida pelo modelo para o target futuro.

Escala:

```text
0 a 1
```

Não representa número de casos.

---

### `threshold`

Limiar congelado do horizonte.

Existe apenas um threshold por horizonte.

---

### `predicao`

Classificação binária oficial:

```text
score >= threshold
```

Interpretação:

```text
false = modelo não classificou o estado futuro como risco elevado

true = modelo classificou o estado futuro como risco elevado
```

---

## 12. Predição positiva não é necessariamente early warning

O campo:

```text
predicao = true
```

não deve ser automaticamente rotulado como alerta antecipado.

Uma previsão positiva pode ocorrer quando o município já se encontra em estado
de risco elevado na semana de origem.

Para representar um **early warning** no sentido utilizado na avaliação final,
é necessário:

```text
risco_elevado == false
AND
predicao == true
```

Assim, existem dois conceitos distintos:

```text
predição positiva
```

e:

```text
alerta antecipado em situação ainda sem risco elevado
```

Esses conceitos não devem ser misturados na aplicação.

---

## 13. Quantidade de predições por horizonte

A avaliação final possui:

| Horizonte | Linhas | Municípios | Semanas de origem |
|---|---:|---:|---:|
| H1 | 289.588 | 5.569 | 52 |
| H2 | 284.019 | 5.569 | 51 |
| H3 | 278.450 | 5.569 | 50 |
| H4 | 272.881 | 5.569 | 49 |
| **Total** | **1.124.938** | — | — |

A redução das semanas é consequência natural da necessidade de possuir target
observável dentro de 2025.

---

## 14. Cobertura temporal por horizonte

A primeira semana de origem é:

```text
2024-12-29
```

correspondente à primeira semana epidemiológica de 2025.

As últimas datas disponíveis são:

| Horizonte | Última data de origem |
|---|---|
| H1 | 2025-12-21 |
| H2 | 2025-12-14 |
| H3 | 2025-12-07 |
| H4 | 2025-11-30 |

Essa diferença não representa perda de dados.

Ela decorre do deslocamento necessário para observar o target futuro dentro do
período de teste.

---

## 15. Targets positivos observados

A quantidade de targets positivos no teste final é:

| Horizonte | Targets positivos |
|---|---:|
| H1 | 36.582 |
| H2 | 35.737 |
| H3 | 34.849 |
| H4 | 33.889 |

Esses números representam estados futuros observados e não previsões positivas.

---

## 16. Predições positivas

A quantidade total de registros com:

```text
predicao = true
```

é:

| Horizonte | Predições positivas |
|---|---:|
| H1 | 44.500 |
| H2 | 46.975 |
| H3 | 55.358 |
| H4 | 70.312 |

Essas contagens incluem situações em que o município já estava em risco elevado
na semana de origem.

Portanto, não equivalem às contagens de early warning.

---

## 17. Early warning

Na avaliação final, o subconjunto de early warning é definido sobre semanas em
que:

```text
risco_elevado == false
```

Nesse subconjunto, uma previsão positiva representa um alerta antecipado.

As quantidades registradas na avaliação final são:

| Horizonte | Alertas early warning |
|---|---:|
| H1 | 10.440 |
| H2 | 15.083 |
| H3 | 21.766 |
| H4 | 36.367 |

Esses valores devem ser tratados separadamente das predições positivas gerais.

---

## 18. Resultados retrospectivos

A aplicação deve deixar explícito que os resultados preditivos atualmente
disponíveis pertencem ao teste final de:

```text
2025
```

Eles são resultados retrospectivos.

Portanto, a interface não deve utilizar textos como:

```text
risco atual
alerta de hoje
situação atual
previsão vigente
alerta ativo em 2026
```

quando estiver exibindo esse conjunto.

Formulações adequadas incluem:

```text
Avaliação retrospectiva de 2025

Probabilidade estimada pelo modelo no teste de 2025

Resultado retrospectivo

Simulação histórica de alerta antecipado
```

---

## 19. Estados visuais

A aplicação não deve inventar classes como:

```text
baixo
moderado
alto
crítico
```

O modelo final possui:

```text
score contínuo
threshold por horizonte
predicao binária
```

Qualquer classificação ordinal adicional exigiria uma nova definição
metodológica e não faz parte do modelo atualmente aprovado.

---

## 20. Separação entre histórico e predição

Os dados observados historicamente continuam pertencendo a:

```text
data/serving/historical/
```

Os resultados do modelo pertencem a:

```text
data/serving/prediction/
```

Essa separação deve existir tanto na estrutura física quanto na interface.

O usuário precisa conseguir distinguir claramente:

```text
o que foi observado
```

de:

```text
o que o modelo estimou
```

---

## 21. Estrutura inicial do serving preditivo

A camada preditiva deverá possuir, inicialmente:

```text
data/serving/prediction/
├── metadata/
├── evaluation/
└── municipality/
```

A divisão física detalhada será definida após medição dos payloads, seguindo o
mesmo princípio utilizado no serving histórico municipal.

Não será adotado automaticamente um único JSON nacional contendo as 1.124.938
predições.

---

## 22. Metadata preditiva

A área:

```text
prediction/metadata/
```

deverá disponibilizar informações pequenas e globais, incluindo:

```text
modelo final
período de desenvolvimento
período de teste
horizontes
thresholds
semântica do score
natureza retrospectiva
```

Esses dados podem ser carregados pela aplicação sem depender das séries
municipais.

---

## 23. Avaliação

A área:

```text
prediction/evaluation/
```

deverá disponibilizar resultados agregados da avaliação final.

Ela poderá incluir, por horizonte:

```text
PR-AUC
ROC-AUC
recall
precision
F1
balanced accuracy
Brier score
matriz de confusão
métricas do subconjunto early warning
comparação com baseline de persistência
```

O objetivo é permitir que a aplicação mostre não apenas as previsões, mas
também a qualidade observada no teste retrospectivo.

---

## 24. Serving municipal preditivo

A área:

```text
prediction/municipality/
```

deverá permitir a consulta das predições de um município sem transferir o
artefato nacional inteiro para o navegador.

A granularidade física será definida após benchmark específico do artefato de
1.124.938 linhas.

A decisão deverá considerar:

```text
tamanho por município
quantidade de linhas por município
JSON compacto
compressão de transporte
eventual alternativa Parquet server-side
quantidade de arquivos
simplicidade de consumo pelo frontend
```

Nenhum formato físico será escolhido apenas por conveniência antes dessa
medição.

---

## 25. Invariantes obrigatórias

Qualquer gerador do serving preditivo deverá validar pelo menos:

```text
linhas totais = 1.124.938

municípios = 5.569

horizontes = {1, 2, 3, 4}

duplicadas na chave
(codigo_ibge_7, ano_epidemiologico,
 semana_epidemiologica, horizonte)
= 0

score dentro de [0, 1]

predicao == (score >= threshold)

threshold H1 = 0.187687
threshold H2 = 0.190783
threshold H3 = 0.167991
threshold H4 = 0.157138
```

O gerador deverá interromper a execução se alguma dessas invariantes deixar de
ser satisfeita.

---

## 26. Regras de serialização

Os contratos JSON deverão utilizar:

```text
UTF-8
schema_version
snake_case
codigo_ibge_7 como string
datas ISO YYYY-MM-DD
números como tipos numéricos
booleanos como booleanos JSON
sem NaN
sem Infinity
ordenação determinística
```

---

## 27. Princípio de não recalcular a ciência

A camada de serving não deve refazer:

```text
treinamento
seleção de features
seleção de algoritmo
calibração
definição de target
otimização de threshold
avaliação baseada novamente em 2025
```

Ela deve transformar e validar os resultados científicos já congelados.

Derivações puramente semânticas ou de apresentação podem ser permitidas quando
forem determinísticas e explicitamente definidas.

Exemplo:

```text
early_warning =
    risco_elevado == false
    AND
    predicao == true
```

Caso esse campo seja materializado no serving, sua origem derivada deverá ser
documentada.

---

## 28. Decisão congelada nesta etapa

Ficam congelados para a implementação:

```text
Modelo:
HistGradientBoostingClassifier

Features:
Modelo A — 23 epidemiológicas

Probabilidades:
raw

Calibração adicional:
não

Horizontes:
H1, H2, H3 e H4

Thresholds:
H1 0.187687
H2 0.190783
H3 0.167991
H4 0.157138

Período de desenvolvimento:
2018–2024

Teste final:
2025

Uso de 2025 na seleção:
não

Natureza da interface atual:
retrospectiva

Target do modelo:
estado futuro de risco elevado

Saída contínua:
score de probabilidade

Saída operacional:
predicao binária

Faixas baixo/moderado/alto/crítico:
não definidas
```

A próxima etapa será medir a melhor representação física das predições
municipais e, em seguida, implementar os contratos de serving preditivo.