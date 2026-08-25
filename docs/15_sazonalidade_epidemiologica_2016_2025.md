# Sazonalidade Epidemiológica da Dengue — 2016–2025

## 1. Objetivo

Esta etapa analisa a sazonalidade epidemiológica da dengue no Brasil entre
2016 e 2025.

O objetivo é identificar:

- em quais semanas epidemiológicas a atividade tende a ser maior;
- quanto esse calendário varia entre regiões;
- diferenças entre média e mediana ao longo dos anos;
- elementos que poderão ser utilizados posteriormente nos dashboards
  históricos.

A análise possui caráter descritivo e não modifica o modelo preditivo final.

---

# 2. Base utilizada

Fonte processada:

`data/processed/painel_municipal_semanal_2016_2025.parquet`

Período:

**2016–2025**

Foram preservados:

- 2.907.593 registros municipais semanais;
- 522 semanas epidemiológicas nacionais;
- 16.294.913 casos prováveis.

Status da auditoria:

**APROVADO**

---

# 3. Metodologia

A sazonalidade foi analisada agrupando os dados pela semana epidemiológica do
ano.

Foram calculadas estatísticas nacionais e regionais.

Entre elas:

- média de casos;
- mediana de casos;
- mínimo;
- máximo;
- incidência média;
- incidência mediana;
- percentil 25 da incidência;
- percentil 75 da incidência;
- incidência mínima;
- incidência máxima.

A incidência regional foi calculada a partir de:

`casos regionais / população regional × 100.000`

e não pela soma das incidências municipais.

---

# 4. Semana epidemiológica 53

A semana epidemiológica 53 aparece apenas em:

- 2020;
- 2025.

Portanto, possui apenas duas observações na série histórica.

Ela foi preservada nos artefatos, mas não deve ser comparada diretamente às
semanas epidemiológicas 1 a 52, que possuem suporte histórico muito maior.

Para a identificação dos picos regionais foram consideradas somente semanas
com suporte temporal suficiente.

---

# 5. Sazonalidade nacional

O pico sazonal nacional calculado a partir da incidência média ocorreu na:

**semana epidemiológica 15**

Quando utilizada a incidência mediana entre os anos, o pico ocorreu na:

**semana epidemiológica 14**

Assim, o comportamento central da série indica maior atividade nacional
aproximadamente entre as semanas epidemiológicas 14 e 15.

Esse resultado é consistente com a concentração dos picos anuais observada na
etapa anterior, embora cada ano possa apresentar deslocamentos importantes.

---

# 6. Sazonalidade regional

Os resultados demonstraram diferenças importantes entre as cinco
macrorregiões.

| Região | Pico pela incidência média | Pico pela incidência mediana |
| --- | ---: | ---: |
| Norte | 7 | 5 |
| Nordeste | 16 | 20 |
| Centro-Oeste | 11 | 15 |
| Sudeste | 15 | 14 |
| Sul | 15 | 14 |

Esses resultados mostram que a sazonalidade nacional não representa
integralmente o calendário de todas as regiões.

---

# 7. Região Norte

A região Norte apresentou o calendário mais precoce entre as cinco regiões.

Pico pela média:

**SE 7**

Pico pela mediana:

**SE 5**

Esse comportamento ocorre várias semanas antes do pico nacional.

Assim, utilizar apenas a curva sazonal brasileira poderia esconder uma
diferença temporal relevante da região Norte.

---

# 8. Região Nordeste

O Nordeste apresentou comportamento sazonal mais tardio.

Pico pela média:

**SE 16**

Pico pela mediana:

**SE 20**

A mediana posiciona o maior nível típico de incidência aproximadamente cinco a
seis semanas depois do pico nacional.

A diferença entre média e mediana também indica heterogeneidade importante
entre os anos analisados.

---

# 9. Região Centro-Oeste

O Centro-Oeste apresentou:

- pico médio na SE 11;
- pico mediano na SE 15.

A diferença entre os dois indicadores sugere que anos de maior magnitude podem
influenciar consideravelmente a curva média da região.

A mediana, por ser menos sensível a anos extremos, posiciona o comportamento
central mais próximo do pico nacional.

---

# 10. Regiões Sudeste e Sul

Sudeste e Sul apresentaram praticamente o mesmo calendário sazonal.

Para ambas:

- pico da incidência média: SE 15;
- pico da incidência mediana: SE 14.

Esse comportamento também coincide de forma próxima com o padrão nacional.

---

# 11. Média e mediana

A utilização conjunta de média e mediana é especialmente importante nesta
série.

O período analisado possui anos de magnitudes epidemiológicas muito diferentes,
incluindo o evento excepcional de 2024.

A média pode ser deslocada por anos de atividade muito elevada.

A mediana representa de forma mais robusta o comportamento central entre os
anos.

Assim, diferenças entre média e mediana não devem ser interpretadas como erro,
mas como sinal de heterogeneidade temporal da série.

---

# 12. Interpretação geral

A análise mostra que existe uma sazonalidade epidemiológica nacional clara, mas
ela não é temporalmente uniforme no território brasileiro.

O principal padrão identificado foi:

- Norte: atividade sazonal mais precoce;
- Centro-Oeste: tendência relativamente precoce pela média;
- Sudeste e Sul: comportamento próximo do padrão nacional;
- Nordeste: atividade sazonal mais tardia.

Essas diferenças são epidemiologicamente importantes para a interpretação do
sistema.

Uma mesma semana do ano pode representar momentos distintos do ciclo sazonal em
regiões diferentes.

---

# 13. Implicações para o dashboard histórico

A sazonalidade deverá possuir uma área própria na aplicação histórica.

Visualizações candidatas incluem:

1. curva nacional por semana epidemiológica;
2. comparação entre as cinco regiões;
3. heatmap ano × semana;
4. seleção de região para inspeção individual;
5. comparação entre média e mediana.

No frontend, essas visualizações deverão ser responsivas.

Em telas menores, deverão ser considerados recursos como:

- redução de informações simultâneas;
- seleção de região em vez da exibição obrigatória das cinco curvas;
- tooltip para valores detalhados;
- legenda adaptável;
- rolagem horizontal apenas quando estritamente necessária.

---

# 14. Visualizações para o TCC

A análise indica pelo menos três figuras potencialmente úteis para o relatório:

## Curva sazonal nacional

Semana epidemiológica no eixo X e incidência no eixo Y.

Poderá apresentar:

- mediana;
- intervalo interquartil;
- eventualmente média como referência complementar.

## Heatmap ano × semana

Permitirá mostrar:

- intensidade;
- momento dos picos;
- deslocamento entre anos;
- excepcionalidade de 2024.

## Comparação regional

Permitirá demonstrar visualmente o deslocamento do calendário epidemiológico
entre as cinco regiões.

---

# 15. Limitações

Os resultados representam padrões descritivos observados entre 2016 e 2025.

Eles não implicam que:

- o pico futuro ocorrerá obrigatoriamente na mesma semana;
- todas as UFs de uma região apresentem o mesmo calendário;
- todos os municípios sigam o padrão regional;
- a sazonalidade seja causada exclusivamente por condições climáticas.

Também existe forte heterogeneidade de magnitude entre os anos.

---

# 16. Artefatos

Sazonalidade nacional:

`reports/audits/sazonalidade_nacional_semana_epidemiologica_2016_2025.csv`

Sazonalidade regional:

`reports/audits/sazonalidade_regional_semana_epidemiologica_2016_2025.csv`

Série semanal regional:

`reports/audits/serie_semanal_regional_2016_2025.csv`

Auditoria:

`reports/audits/sazonalidade_2016_2025.json`

Script:

`scripts/analisar_sazonalidade.py`

---

# 17. Próxima etapa

A próxima etapa será a análise da distribuição espacial da dengue.

Serão avaliadas:

- macrorregiões;
- unidades federativas;
- municípios;
- diferenças entre casos absolutos e incidência;
- concentração territorial da carga epidemiológica.

Posteriormente, os resultados espaciais serão utilizados na definição dos
mapas do dashboard histórico.

Status desta etapa:

**APROVADO**