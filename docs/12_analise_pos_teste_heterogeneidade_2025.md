# Análise Pós-Teste de Heterogeneidade em 2025

## 1. Objetivo

Esta etapa investigou se o desempenho do modelo final Dengue Alert foi
homogêneo entre diferentes grupos de municípios brasileiros.

A análise foi realizada após a conclusão da avaliação final independente de
2025.

Portanto, possui natureza:

**secundária, descritiva e pós-teste**

Nenhum resultado desta etapa foi utilizado para modificar:

- algoritmo;
- features;
- hiperparâmetros;
- calibração;
- thresholds;
- definição do target;
- regra de early warning.

Os resultados oficiais da primeira avaliação final de 2025 permaneceram
inalterados.

---

# 2. Predições analisadas

Foram utilizadas exclusivamente as predições produzidas durante a primeira
avaliação final de 2025.

Total:

**1.124.938 predições**

Municípios elegíveis:

**5.569**

Horizontes:

- H1;
- H2;
- H3;
- H4.

Durante esta análise:

- nenhum modelo foi retreinado;
- nenhum score foi recalculado;
- nenhum threshold foi alterado.

Status da auditoria:

**APROVADO**

---

# 3. Dimensões avaliadas

A heterogeneidade foi analisada segundo:

1. macrorregião;
2. unidade federativa;
3. porte populacional;
4. perfil epidemiológico histórico.

Todas as dimensões foram avaliadas:

- no conjunto geral;
- no subconjunto de early warning.

A discussão principal deste documento prioriza o subconjunto de early warning,
pois ele representa situações em que o município ainda não estava em estado de
risco elevado no momento da previsão.

---

# 4. Perfil epidemiológico histórico

O perfil epidemiológico municipal foi construído utilizando exclusivamente o
período de desenvolvimento:

**2018–2024**

A variável utilizada foi:

**incidência semanal média por 100 mil habitantes**

Foram caracterizados:

**5.569 municípios**

Cada município possui:

**365 semanas históricas**

Os pontos de corte nacionais foram:

| Corte | Incidência média semanal |
| --- | ---: |
| P25 | 2,421379 |
| P50 | 9,996535 |
| P75 | 27,689514 |

Distribuição:

| Quartil | Municípios |
| --- | ---: |
| Q1 | 1.393 |
| Q2 | 1.392 |
| Q3 | 1.392 |
| Q4 | 1.392 |

Q1 representa os municípios historicamente associados à menor carga
epidemiológica e Q4 à maior carga.

---

# 5. Heterogeneidade por macrorregião

Os resultados demonstraram diferenças consistentes entre as cinco
macrorregiões.

## Early warning — F1

| Região | H1 | H2 | H3 | H4 |
| --- | ---: | ---: | ---: | ---: |
| Norte | 0,3453 | 0,3502 | 0,3192 | 0,2904 |
| Nordeste | 0,3061 | 0,3244 | 0,2878 | 0,2465 |
| Centro-Oeste | **0,4171** | **0,4029** | **0,3502** | **0,3193** |
| Sudeste | 0,3679 | 0,3624 | 0,3236 | 0,2773 |
| Sul | 0,2902 | 0,2944 | 0,2527 | 0,2213 |

O Centro-Oeste apresentou o maior F1 de early warning nos quatro horizontes.

O Sul apresentou os menores valores médios entre as regiões.

Essas diferenças também foram acompanhadas por diferenças de recall e de
proporção de alertas.

O resultado demonstra heterogeneidade geográfica, mas não estabelece que a
região seja a causa das diferenças observadas.

---

# 6. Heterogeneidade por porte populacional

Os municípios foram divididos em:

- muito pequeno: menos de 20 mil habitantes;
- pequeno: 20 mil a 49.999;
- médio: 50 mil a 99.999;
- grande: 100 mil a 499.999;
- muito grande: 500 mil ou mais.

## Early warning — F1

| Porte | H1 | H2 | H3 | H4 |
| --- | ---: | ---: | ---: | ---: |
| Muito pequeno | 0,3204 | 0,3227 | 0,2807 | 0,2427 |
| Pequeno | 0,3605 | 0,3717 | 0,3308 | 0,2912 |
| Médio | 0,3795 | 0,3914 | 0,3625 | 0,3169 |
| Grande | **0,4283** | **0,4043** | **0,3736** | 0,3314 |
| Muito grande | 0,3964 | 0,3350 | 0,3424 | **0,3333** |

Os municípios muito pequenos apresentaram desempenho sistematicamente inferior
aos grupos de porte médio e grande.

O resultado não indica relação estritamente monotônica entre população e
desempenho.

O grupo de municípios muito grandes possui apenas 47 municípios e quantidade
relativamente pequena de eventos positivos, exigindo maior cautela na
interpretação de suas métricas.

Uma hipótese possível para a maior dificuldade nos municípios muito pequenos é
a maior volatilidade das taxas de incidência quando poucos casos representam
grandes alterações por 100 mil habitantes.

Essa hipótese não foi testada causalmente.

---

# 7. Heterogeneidade por perfil epidemiológico histórico

Foi observado um padrão particularmente consistente entre os quartis de carga
histórica.

## Early warning — F1

| Perfil | H1 | H2 | H3 | H4 |
| --- | ---: | ---: | ---: | ---: |
| Q1 | 0,2842 | 0,2944 | 0,2552 | 0,2327 |
| Q2 | 0,3198 | 0,3363 | 0,3095 | 0,2665 |
| Q3 | **0,3772** | **0,3750** | **0,3252** | **0,2798** |
| Q4 | 0,3719 | 0,3611 | 0,3201 | 0,2764 |

O modelo apresentou maior dificuldade em Q1.

Q3 e Q4 apresentaram desempenho consistentemente superior.

Esse resultado também apareceu na Average Precision.

Por exemplo, em H1:

| Perfil | Prevalência | AP |
| --- | ---: | ---: |
| Q1 | 2,74% | 0,1942 |
| Q4 | 2,28% | 0,3085 |

Apesar da prevalência de positivos ser superior em Q1, sua Average Precision
foi substancialmente inferior.

Em H4:

| Perfil | Prevalência | AP |
| --- | ---: | ---: |
| Q1 | 8,05% | 0,1634 |
| Q4 | 6,18% | 0,2002 |

Novamente, a diferença de AP não pode ser explicada simplesmente por uma maior
prevalência positiva em Q4.

Os resultados sugerem que a antecipação foi mais difícil em municípios
historicamente associados a baixa carga epidemiológica de dengue.

---

# 8. Heterogeneidade por unidade federativa

A análise por UF revelou diferenças adicionais que não são completamente
capturadas pelas macrorregiões.

Foram avaliadas:

**27 unidades federativas**

nos quatro horizontes e nos dois subconjuntos.

Total:

**216 resultados**

---

## 8.1 Centro-Oeste

Goiás, Mato Grosso e Mato Grosso do Sul apresentaram desempenho favorável e
relativamente consistente.

### Early warning — F1

| UF | H1 | H2 | H3 | H4 |
| --- | ---: | ---: | ---: | ---: |
| Goiás | 0,4181 | 0,4078 | 0,3496 | 0,3119 |
| Mato Grosso | 0,4115 | 0,3901 | 0,3475 | 0,3242 |
| Mato Grosso do Sul | 0,4274 | 0,4181 | 0,3597 | 0,3354 |

Esse padrão mostra que o desempenho favorável do Centro-Oeste não resultou
apenas de uma única UF isolada.

---

## 8.2 Região Sul

A região Sul apresentou heterogeneidade interna.

### Early warning — F1

| UF | H1 | H2 | H3 | H4 |
| --- | ---: | ---: | ---: | ---: |
| Paraná | 0,3176 | 0,3195 | 0,2887 | 0,2664 |
| Rio Grande do Sul | 0,2776 | 0,2875 | 0,2426 | 0,2133 |
| Santa Catarina | 0,2612 | 0,2553 | 0,2021 | 0,1546 |

Santa Catarina apresentou desempenho particularmente reduzido.

O Rio Grande do Sul também apresentou dificuldade relativamente elevada,
principalmente em recall.

O Paraná teve comportamento mais favorável que os demais estados da região.

Assim, a menor performance agregada do Sul não deve ser interpretada como
comportamento uniforme entre seus três estados.

---

## 8.3 Nordeste

O Nordeste apresentou forte variação entre UFs.

Exemplos em H1:

| UF | F1 |
| --- | ---: |
| Pernambuco | 0,3645 |
| Alagoas | 0,3565 |
| Piauí | 0,2213 |
| Sergipe | 0,1899 |

Em H4:

| UF | F1 |
| --- | ---: |
| Alagoas | 0,3047 |
| Pernambuco | 0,2757 |
| Piauí | 0,2123 |
| Sergipe | 0,1166 |

Portanto, o resultado regional não representa comportamento uniforme entre os
estados.

---

# 9. Unidades federativas com baixo suporte amostral

Algumas UFs possuem poucos municípios ou poucos eventos positivos.

Nesses casos, métricas como Average Precision, precision, recall e F1 podem
apresentar maior variabilidade.

Acre, Amapá e Roraima são exemplos de estados que apresentaram em alguns
horizontes métricas numericamente elevadas, mas com suporte amostral menor.

Esses resultados são apresentados integralmente, mas devem ser interpretados
com maior cautela.

---

# 10. Distrito Federal

No subconjunto de early warning, o Distrito Federal não apresentou evento
positivo elegível em nenhum dos quatro horizontes.

Consequentemente:

- a Average Precision não é definida;
- precision = 0;
- recall = 0;
- F1 = 0.

Esses valores não devem ser interpretados como evidência de incapacidade do
modelo no Distrito Federal.

Não houve suporte positivo suficiente nesse subconjunto para avaliar a
capacidade de antecipação.

---

# 11. Trade-off operacional entre UFs

O threshold nacional congelado apresentou comportamentos operacionais
diferentes entre estados.

Por exemplo, São Paulo em H4 apresentou:

- precision: 0,2006;
- recall: 0,5686;
- F1: 0,2966;
- proporção de alertas: 24,60%.

Isso indica que, em alguns grupos, o modelo recupera uma proporção maior de
eventos futuros ao custo de maior quantidade de alertas.

Essas diferenças não serão utilizadas para criar thresholds específicos por
UF, pois isso constituiria otimização posterior ao teste.

---

# 12. Interpretação geral

A análise demonstra que o modelo possui capacidade de generalização em escala
nacional, mas seu desempenho não é completamente homogêneo entre municípios.

Os padrões mais consistentes observados foram:

1. desempenho mais favorável no Centro-Oeste;
2. maior dificuldade média na região Sul;
3. desempenho inferior em municípios muito pequenos;
4. maior dificuldade em municípios com baixa carga epidemiológica histórica;
5. heterogeneidade relevante entre UFs pertencentes à mesma região.

Essas diferenças devem ser consideradas na interpretação operacional do
sistema.

Elas não estabelecem relações causais.

---

# 13. Limitações da análise

A análise apresenta algumas limitações importantes.

Primeiro, os grupos possuem diferentes prevalências de eventos positivos.

A Average Precision deve ser interpretada considerando essa diferença.

Segundo, alguns grupos possuem baixo suporte amostral.

Terceiro, as dimensões avaliadas são correlacionadas.

Por exemplo, determinada região pode possuir maior proporção de municípios
pequenos ou determinado perfil epidemiológico.

Portanto, os resultados não permitem atribuir causalmente diferenças de
desempenho a uma única característica.

---

# 14. Relação com o resultado final

A avaliação global de 2025 permanece a estimativa principal da capacidade de
generalização temporal do modelo.

Esta análise apenas decompõe o resultado segundo características previamente
definidas.

Nenhuma métrica por grupo substitui os resultados nacionais registrados na
avaliação final independente.

---

# 15. Conclusão

O modelo Dengue Alert apresentou capacidade de antecipação em escala nacional,
mas com heterogeneidade de desempenho entre diferentes contextos municipais.

Os resultados sugerem maior robustez em municípios de porte médio e grande e
em locais historicamente associados a maior carga epidemiológica.

Municípios muito pequenos e municípios de menor carga histórica apresentaram
maior dificuldade de antecipação.

Também foram identificadas diferenças geográficas relevantes, tanto entre
macrorregiões quanto entre unidades federativas.

Esses resultados reforçam a necessidade de apresentar o sistema como ferramenta
de apoio epidemiológico, acompanhada de métricas de incerteza e contexto local,
e não como mecanismo de decisão automática.

---

# 16. Artefatos

Perfil epidemiológico histórico:

- `data/processed/perfil_epidemiologico_municipios_2018_2024.parquet`;
- `reports/audits/auditoria_perfil_epidemiologico_2018_2024.json`.

Heterogeneidade:

- `reports/audits/heterogeneidade_2025_regiao.csv`;
- `reports/audits/heterogeneidade_2025_uf.csv`;
- `reports/audits/heterogeneidade_2025_porte_populacional.csv`;
- `reports/audits/heterogeneidade_2025_perfil_epidemiologico.csv`;
- `reports/audits/heterogeneidade_2025.json`.

Scripts:

- `scripts/criar_perfil_epidemiologico_historico.py`;
- `scripts/analisar_heterogeneidade_2025.py`;
- `scripts/resumir_heterogeneidade_2025.py`;
- `scripts/resumir_heterogeneidade_uf_2025.py`.

Status da etapa:

**APROVADO**