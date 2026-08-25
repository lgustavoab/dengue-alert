# Distribuição Espacial da Dengue — 2016–2025

## 1. Objetivo

Esta etapa analisa a distribuição espacial da dengue no Brasil entre 2016 e
2025.

A análise foi realizada em três escalas:

**macrorregião → unidade federativa → unidade territorial**

O objetivo principal é caracterizar onde a carga epidemiológica esteve
concentrada e demonstrar a diferença entre:

**volume absoluto de casos**

e

**incidência por 100 mil habitantes**

A análise possui caráter descritivo e não modifica o modelo preditivo final.

---

# 2. Base utilizada

Fonte processada:

`data/processed/painel_municipal_semanal_2016_2025.parquet`

Período:

**2016–2025**

A base possui:

- 2.907.593 registros municipais semanais;
- 16.294.913 casos prováveis;
- 55.701 combinações unidade territorial × ano;
- 5.571 unidades territoriais presentes no período completo.

Todas as agregações espaciais preservaram o total epidemiológico original.

Status:

**APROVADO**

---

# 3. Metodologia

Os dados municipais semanais foram inicialmente agregados para:

**unidade territorial × ano**

A partir dessa base foram construídas agregações por:

- macrorregião;
- unidade federativa;
- unidade territorial.

Casos absolutos e incidência foram mantidos como indicadores distintos.

As incidências estaduais e regionais foram recalculadas como:

`casos agregados / população agregada × 100.000`

Incidências municipais não foram somadas para produzir indicadores de níveis
geográficos superiores.

---

# 4. Macrorregiões

No período completo foram registrados:

| Região | Casos | Participação nacional | Incidência média anual/100 mil | Incidência mediana anual/100 mil |
| --- | ---: | ---: | ---: | ---: |
| Norte | 359.242 | 2,20% | 197,54 | 204,64 |
| Nordeste | 1.757.366 | 10,78% | 310,32 | 243,66 |
| Centro-Oeste | 2.309.520 | 14,17% | 1.397,22 | 1.167,23 |
| Sudeste | 9.277.216 | 56,93% | 1.056,22 | 763,69 |
| Sul | 2.591.569 | 15,90% | 846,49 | 467,66 |

O Sudeste concentrou a maior quantidade absoluta de casos.

Entretanto, a maior incidência média e mediana anual foi observada no
Centro-Oeste.

Isso demonstra que maior volume absoluto não é equivalente a maior intensidade
epidemiológica relativa à população.

---

# 5. Ano de maior incidência regional

O ano de maior incidência em todas as cinco macrorregiões foi:

**2024**

O resultado confirma que a excepcionalidade observada nacionalmente em 2024
teve ampla dimensão geográfica.

Entretanto, essa uniformidade regional não significa que todos os estados ou
municípios tenham registrado seus máximos no mesmo ano.

---

# 6. Distribuição por unidade federativa

Foram avaliadas as 27 unidades federativas.

Quando ordenadas pelo número acumulado de casos, os maiores valores foram
observados principalmente em unidades populacionalmente grandes.

Os cinco maiores volumes foram:

| UF | Casos no período | Participação nacional |
| --- | ---: | ---: |
| São Paulo | 4.796.152 | 29,43% |
| Minas Gerais | 3.477.656 | 21,34% |
| Paraná | 1.530.332 | 9,39% |
| Goiás | 1.251.443 | 7,68% |
| Santa Catarina | 624.858 | 3,83% |

São Paulo e Minas Gerais, juntos, concentraram aproximadamente:

**50,77% de todos os casos observados entre 2016 e 2025.**

---

# 7. Incidência por unidade federativa

A ordenação muda significativamente quando utilizada a incidência mediana
anual.

Os maiores valores foram:

| UF | Incidência mediana anual/100 mil |
| --- | ---: |
| Goiás | 1.374,95 |
| Distrito Federal | 937,22 |
| Acre | 848,75 |
| Mato Grosso do Sul | 803,71 |
| Paraná | 727,46 |
| Mato Grosso | 704,36 |
| São Paulo | 601,32 |
| Minas Gerais | 597,05 |
| Espírito Santo | 559,45 |

Goiás ocupa posição de destaque tanto em volume absoluto quanto em intensidade
epidemiológica.

Outras UFs apresentam posições muito diferentes dependendo da métrica
utilizada.

---

# 8. Casos absolutos e incidência não são equivalentes

A comparação entre as UFs demonstra por que rankings epidemiológicos devem
sempre informar qual indicador está sendo utilizado.

São Paulo apresenta o maior volume acumulado de casos.

Entretanto, Goiás apresenta incidência mediana anual substancialmente maior.

Assim:

**casos absolutos representam carga total**

enquanto:

**incidência representa intensidade relativa à população**

Os dois indicadores respondem a perguntas distintas.

---

# 9. Municípios com maior carga absoluta

Os municípios/unidades territoriais com maior número acumulado de casos foram:

| Município | UF | Casos no período |
| --- | --- | ---: |
| São Paulo | SP | 777.309 |
| Brasília | DF | 526.076 |
| Belo Horizonte | MG | 513.450 |
| Goiânia | GO | 344.495 |
| Campinas | SP | 227.301 |
| Rio de Janeiro | RJ | 200.960 |
| São José do Rio Preto | SP | 200.250 |
| Joinville | SC | 171.879 |
| Aparecida de Goiânia | GO | 167.230 |
| Londrina | PR | 162.494 |

Esses valores representam carga absoluta e devem ser interpretados considerando
as grandes diferenças populacionais entre municípios.

---

# 10. Contraste municipal entre carga e intensidade

A diferença entre casos absolutos e incidência também aparece claramente no
nível municipal.

A cidade de São Paulo registrou:

**777.309 casos**

e incidência mediana anual de:

**116,26 por 100 mil habitantes**

São José do Rio Preto registrou:

**200.250 casos**

e incidência mediana anual de:

**3.922,39 por 100 mil habitantes**

Assim, São Paulo apresentou maior carga absoluta, enquanto São José do Rio
Preto apresentou intensidade relativa muito maior dentro do período
analisado.

---

# 11. Critério para ranking municipal de incidência

Municípios muito pequenos podem apresentar taxas de incidência extremamente
elevadas a partir de poucos casos.

Para reduzir rankings dominados por grande instabilidade de pequenas
populações, foi definido previamente um critério específico para o ranking
comparativo de incidência.

Foram considerados apenas municípios com:

**10 anos disponíveis**

e

**população média de pelo menos 20.000 habitantes**

A métrica utilizada foi:

**incidência mediana anual por 100 mil habitantes**

Após o filtro permaneceram:

**1.762 municípios**

Esse filtro é utilizado exclusivamente para o ranking comparativo.

Municípios fora desse critério permanecem integralmente:

- no painel histórico;
- nas análises espaciais completas;
- nos futuros mapas.

---

# 12. Municípios com maior incidência mediana anual

Os 15 maiores resultados dentro do critério definido foram:

| Município | UF | Incidência mediana anual/100 mil |
| --- | --- | ---: |
| São José do Rio Preto | SP | 3.922,39 |
| Votuporanga | SP | 3.514,57 |
| Presidente Prudente | SP | 3.056,19 |
| Aparecida de Goiânia | GO | 3.048,77 |
| Bady Bassitt | SP | 3.022,74 |
| Guararapes | SP | 2.866,99 |
| Foz do Iguaçu | PR | 2.647,67 |
| Ibiporã | PR | 2.563,94 |
| Andradina | SP | 2.513,85 |
| Birigui | SP | 2.408,71 |
| Tanabi | SP | 2.291,11 |
| Itambacuri | MG | 2.283,40 |
| Jataí | GO | 2.282,58 |
| Santa Fé do Sul | SP | 2.217,69 |
| Mirandópolis | SP | 2.192,79 |

---

# 13. Concentração de municípios paulistas

Entre os 15 municípios com maior incidência mediana anual no ranking estável:

**10 pertencem ao estado de São Paulo**

Esse padrão representa uma concentração espacial relevante dentro dos dados
analisados.

Entretanto, a análise é descritiva.

O resultado não demonstra que pertencer ao estado de São Paulo seja causa da
maior incidência.

Investigações causais exigiriam considerar simultaneamente fatores como:

- circulação viral;
- clima;
- urbanização;
- mobilidade;
- características demográficas;
- vigilância epidemiológica;
- imunidade populacional.

Esses mecanismos não são isolados nesta etapa.

---

# 14. Heterogeneidade temporal municipal

Embora 2024 tenha sido o ano de maior incidência em todas as macrorregiões, os
máximos municipais não ocorreram necessariamente nesse ano.

Entre os municípios de maior incidência mediana aparecem anos de máximo como:

- 2019;
- 2022;
- 2023;
- 2024;
- 2025.

Esse resultado demonstra heterogeneidade temporal em escala local.

A dinâmica municipal não pode ser completamente representada apenas pelo
comportamento nacional ou regional.

---

# 15. Implicações para os mapas

A análise espacial será utilizada futuramente para construir mapas históricos
da aplicação.

Os mapas deverão permitir alternância entre indicadores como:

**casos absolutos**

e

**incidência por 100 mil habitantes**

Isso evitará que uma única representação cartográfica induza interpretações
equivocadas.

Também deverão existir filtros por:

- período;
- ano;
- região;
- UF;
- município;
- indicador selecionado.

---

# 16. Responsividade do frontend

Os mapas e demais visualizações espaciais da aplicação deverão ser
responsivos.

Em desktop poderão existir simultaneamente:

**mapa + filtros + painel de detalhes**

Em telas menores, a interface deverá priorizar:

**mapa + filtros compactos + painel de detalhes expansível**

A aplicação não deverá simplesmente reduzir proporcionalmente uma visualização
desktop.

Os componentes deverão reorganizar seu layout conforme o espaço disponível.

---

# 17. Limitações

A interpretação espacial deve considerar algumas limitações.

Casos absolutos são fortemente influenciados pelo tamanho populacional.

Incidências podem apresentar grande volatilidade em pequenas populações.

Os dados possuem natureza retrospectiva e dependem da vigilância
epidemiológica.

Diferenças entre territórios não estabelecem causalidade geográfica.

Além disso, algumas unidades territoriais não possuem o mesmo número de anos
históricos em razão de mudanças territoriais ocorridas durante o período.

---

# 18. Relação com a análise preditiva

A análise espacial histórica é independente da avaliação final do modelo.

Ela não foi utilizada para:

- alterar features;
- modificar thresholds;
- retreinar modelos;
- selecionar novos hiperparâmetros.

Seu objetivo é caracterizar os dados históricos e fornecer contexto para a
aplicação Dengue Alert.

---

# 19. Artefatos

Resultados regionais:

`reports/audits/distribuicao_espacial_regiao_anual_2016_2025.csv`

`reports/audits/distribuicao_espacial_regiao_periodo_2016_2025.csv`

Resultados por UF:

`reports/audits/distribuicao_espacial_uf_anual_2016_2025.csv`

`reports/audits/distribuicao_espacial_uf_periodo_2016_2025.csv`

Resultados territoriais:

`reports/audits/distribuicao_espacial_municipio_anual_2016_2025.csv`

`reports/audits/distribuicao_espacial_municipio_periodo_2016_2025.csv`

Auditoria:

`reports/audits/distribuicao_espacial_2016_2025.json`

Scripts:

`scripts/analisar_distribuicao_espacial.py`

`scripts/resumir_distribuicao_espacial.py`

---

# 20. Próxima etapa

A próxima etapa será a análise da dinâmica epidemiológica.

Ela investigará aspectos como:

**persistência, duração e recorrência dos períodos de elevada atividade**

em vez de analisar apenas totais agregados.

Essa etapa permitirá compreender melhor como as ondas de dengue se desenvolvem
ao longo do tempo em diferentes municípios.

Status desta etapa:

**APROVADO**