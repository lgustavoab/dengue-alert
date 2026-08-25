# Panorama Epidemiológico Nacional da Dengue — 2016–2025

## 1. Objetivo

Esta etapa apresenta uma caracterização nacional da dengue no Brasil entre
2016 e 2025 a partir do painel municipal semanal consolidado e auditado pelo
projeto Dengue Alert.

A análise possui caráter descritivo e faz parte da etapa de análise
exploratória histórica.

Ela não modifica o modelo preditivo final nem os resultados da avaliação
independente de 2025.

---

# 2. Base utilizada

Fonte processada principal:

`data/processed/painel_municipal_semanal_2016_2025.parquet`

Unidade básica:

**unidade territorial × semana epidemiológica**

Período:

**2016–2025**

O painel utilizado possui:

- 2.907.593 linhas;
- 522 semanas epidemiológicas nacionais;
- 16.294.913 casos prováveis de dengue.

A auditoria confirmou preservação integral do total epidemiológico.

Status:

**APROVADO**

---

# 3. Incidência nacional

A incidência nacional não foi obtida pela soma das incidências municipais.

Para cada ano, foi calculada como:

`casos nacionais / população nacional × 100.000`

A população de cada unidade territorial foi contabilizada apenas uma vez por
ano.

A incidência municipal armazenada no painel também foi recalculada a partir de
casos e população durante a auditoria.

Maior diferença absoluta encontrada:

**0**

---

# 4. Resultados anuais

| Ano | Casos prováveis | População | Incidência por 100 mil | Pico semanal | Semana do pico | Unidades com casos |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2016 | 1.486.799 | 206.081.432 | 721,46 | 104.500 | 8 | 4.851 |
| 2017 | 241.528 | 207.660.929 | 116,31 | 9.708 | 16 | 3.761 |
| 2018 | 267.765 | 208.494.900 | 128,43 | 11.791 | 15 | 3.649 |
| 2019 | 1.551.370 | 210.147.125 | 738,23 | 103.636 | 19 | 4.678 |
| 2020 | 948.528 | 211.755.692 | 447,94 | 58.859 | 10 | 4.393 |
| 2021 | 539.980 | 213.317.639 | 253,13 | 27.113 | 14 | 4.109 |
| 2022 | 1.404.899 | 203.078.668 | 691,80 | 103.823 | 18 | 5.017 |
| 2023 | 1.645.946 | 203.078.668 | 810,50 | 110.655 | 15 | 4.992 |
| 2024 | 6.564.894 | 212.583.750 | 3.088,14 | 433.511 | 12 | 5.485 |
| 2025 | 1.643.204 | 213.421.037 | 769,94 | 90.182 | 12 | 5.165 |

---

# 5. Ano de 2024

O ano de 2024 foi claramente excepcional dentro da série analisada.

Foram registrados:

**6.564.894 casos prováveis**

com incidência nacional de:

**3.088,14 casos por 100 mil habitantes**

Esse total corresponde a aproximadamente:

**40,3% de todos os casos observados entre 2016 e 2025**

O número de casos de 2024 foi aproximadamente quatro vezes o observado em
2023.

O maior volume semanal ocorreu na:

**semana epidemiológica 12**

com:

**433.511 casos**

Também houve ampla disseminação territorial, com:

**5.485 unidades territoriais com pelo menos um caso no ano**

---

# 6. Comportamento de 2025

Em 2025 foram registrados:

**1.643.204 casos prováveis**

A incidência nacional foi:

**769,94 por 100 mil habitantes**

O volume foi aproximadamente 75% inferior ao de 2024.

Apesar dessa redução, 2025 não representa um ano de baixa atividade dentro da
série histórica.

O total de casos ficou muito próximo ao observado em 2023 e superior ao de
diversos outros anos de elevada circulação.

O pico ocorreu na:

**semana epidemiológica 12**

com:

**90.182 casos**

---

# 7. Heterogeneidade entre anos

A série demonstra grande variação interanual.

Entre os anos de menor carga estão:

- 2017;
- 2018;
- 2021.

Entre os períodos de maior carga encontram-se:

- 2016;
- 2019;
- 2022;
- 2023;
- 2024;
- 2025.

Entretanto, 2024 possui magnitude muito superior aos demais.

Esse comportamento demonstra que a dengue no Brasil não apresenta intensidade
estável ao longo do período.

---

# 8. Momento dos picos anuais

As semanas de maior quantidade nacional de casos foram:

| Ano | Semana epidemiológica do pico |
| --- | ---: |
| 2016 | 8 |
| 2017 | 16 |
| 2018 | 15 |
| 2019 | 19 |
| 2020 | 10 |
| 2021 | 14 |
| 2022 | 18 |
| 2023 | 15 |
| 2024 | 12 |
| 2025 | 12 |

Os picos encontram-se concentrados principalmente na primeira parte do ano,
mas não ocorrem em uma semana epidemiológica fixa.

Essa variação será investigada com maior profundidade na análise de
sazonalidade.

---

# 9. Disseminação territorial

Também foi observada variação na quantidade de unidades territoriais com
registro de casos ao longo de cada ano.

Em 2017 e 2018, por exemplo, foram observadas:

- 3.761 unidades com casos em 2017;
- 3.649 em 2018.

Em 2024 foram:

**5.485**

Isso indica que os diferentes anos variam não apenas em quantidade de casos,
mas também em extensão territorial da ocorrência registrada.

---

# 10. População de 2023

Para 2023 foi reutilizada a população do Censo 2022 de acordo com a decisão
metodológica já documentada no projeto.

Assim:

**população utilizada em 2023 = 203.078.668**

A utilização desse denominador deve ser considerada na interpretação da
incidência nacional de 2023.

---

# 11. Interpretação

Os resultados demonstram uma série epidemiológica marcada por forte
heterogeneidade temporal.

Existem anos com circulação relativamente reduzida, seguidos por anos com
crescimento expressivo.

O ano de 2024 representa o evento de maior magnitude dentro do período
analisado.

Além da quantidade total de casos, os dados mostram variação:

- na incidência;
- no pico semanal;
- no momento do pico;
- na quantidade de unidades territoriais afetadas.

Esses resultados justificam a análise posterior da sazonalidade e da
distribuição regional.

---

# 12. Relação com o dashboard histórico

O panorama nacional fornece candidatos naturais para a visão geral da
aplicação.

Entre eles:

- casos no período selecionado;
- incidência por 100 mil habitantes;
- evolução temporal;
- pico epidemiológico;
- unidades territoriais com casos;
- comparação entre anos.

As visualizações destinadas à aplicação deverão ser implementadas com layout
responsivo e comportamento adequado para desktop, tablet e dispositivos
móveis.

A escolha definitiva dos componentes ocorrerá após a conclusão das demais
etapas da análise exploratória.

---

# 13. Artefatos

Resumo anual:

`reports/audits/panorama_nacional_anual_2016_2025.csv`

Série semanal:

`reports/audits/panorama_nacional_semanal_2016_2025.csv`

Auditoria:

`reports/audits/panorama_nacional_2016_2025.json`

Script:

`scripts/analisar_panorama_nacional.py`

---

# 14. Próxima etapa

A próxima etapa será a análise de sazonalidade epidemiológica.

Ela investigará:

- comportamento por semana epidemiológica;
- variação do calendário entre anos;
- distribuição dos picos;
- diferenças entre macrorregiões.

Status desta etapa:

**APROVADO**