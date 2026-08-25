# Protocolo de Consolidação Visual da Análise Histórica

## 1. Objetivo

Esta etapa consolida visualmente os principais resultados obtidos na análise
exploratória histórica do projeto Dengue Alert.

As análises já concluídas incluem:

- panorama nacional;
- sazonalidade epidemiológica;
- distribuição espacial;
- dinâmica do risco elevado;
- associações temporais entre clima e dengue.

O objetivo desta etapa não é produzir o maior número possível de gráficos.

O objetivo é selecionar um conjunto reduzido de visualizações que responda de
forma clara às principais perguntas exploratórias do projeto.

---

# 2. Princípio de seleção

Cada figura deverá responder a uma pergunta distinta.

Serão evitadas visualizações que:

- apresentem essencialmente a mesma informação;
- existam apenas por efeito estético;
- adicionem complexidade sem ganho interpretativo;
- induzam leitura causal de resultados descritivos;
- misturem indicadores incompatíveis sem explicação.

A seleção das figuras foi definida antes da geração gráfica final.

---

# 3. Separação entre TCC e aplicação

Serão tratados separadamente:

## Figuras estáticas

Destinadas principalmente a:

- relatório do TCC;
- documentação técnica;
- apresentação acadêmica;
- repositório.

Serão armazenadas em:

`reports/figures/`

## Visualizações interativas

Destinadas à aplicação web Dengue Alert.

Não serão simples reproduções das figuras estáticas.

Deverão permitir:

- filtros;
- seleção de período;
- seleção geográfica;
- tooltips;
- detalhamento;
- reorganização responsiva.

---

# 4. Figura 01 — panorama nacional

Pergunta:

**Como o volume de dengue evoluiu entre 2016 e 2025?**

Arquivo previsto:

`reports/figures/01_panorama_nacional_casos_2016_2025.png`

Visualização:

**barras anuais de casos prováveis**

O gráfico deverá destacar especialmente:

- 2016;
- 2019;
- 2022;
- 2023;
- 2024;
- 2025.

O ano de 2024 deverá aparecer como o maior valor da série:

**6.564.894 casos**

A figura deverá permitir perceber que 2025 apresentou forte redução em relação
a 2024, mas permaneceu elevado historicamente.

Não será utilizado eixo duplo para misturar casos e incidência no mesmo gráfico.

---

# 5. Figura 02 — sazonalidade epidemiológica

Pergunta:

**Em quais semanas do ano a atividade epidemiológica tende a se concentrar?**

Arquivo previsto:

`reports/figures/02_sazonalidade_regional_2016_2025.png`

Visualização:

**perfil por semana epidemiológica**

Serão comparadas as cinco macrorregiões:

- Norte;
- Nordeste;
- Centro-Oeste;
- Sudeste;
- Sul.

A figura deverá evidenciar que:

- o padrão nacional se concentra aproximadamente entre SE14 e SE15;
- o Norte apresenta pico mais precoce;
- o Nordeste apresenta pico mais tardio;
- existem diferenças regionais relevantes.

A semana epidemiológica 53 deverá ser tratada com cautela porque não ocorre em
todos os anos.

---

# 6. Figura 03 — distribuição espacial municipal

Pergunta:

**Onde a dengue apresentou maior intensidade histórica?**

Arquivo previsto:

`reports/figures/03_mapa_incidencia_mediana_municipal_2016_2025.png`

Visualização preferencial:

**mapa municipal do Brasil**

Indicador principal:

**incidência mediana anual por 100 mil habitantes entre 2016 e 2025**

A utilização da mediana anual reduz a influência de um único ano extremo.

O mapa deverá representar todos os municípios/unidades territoriais elegíveis,
sem aplicar o filtro de população utilizado exclusivamente no ranking
comparativo.

A geometria municipal deverá utilizar referência territorial oficial do IBGE.

Caso o arquivo de geometria ainda não esteja disponível no projeto definitivo,
sua existência e caminho deverão ser verificados antes da implementação.

---

# 7. Figura 04 — municípios simultaneamente em risco

Pergunta:

**Como o estado de risco elevado se expandiu e retraiu pelo território?**

Arquivo previsto:

`reports/figures/04_municipios_simultaneamente_risco_2018_2025.png`

Visualização:

**série temporal semanal**

Eixo X:

tempo

Eixo Y:

quantidade de municípios simultaneamente em risco elevado

A figura deverá destacar o máximo observado:

**3.121 municípios**

em:

**SE12 de 2024**

correspondendo a:

**56,04% dos municípios elegíveis**

A figura utilizará o target histórico oficial `risco_elevado`.

---

# 8. Figura 05 — duração dos episódios

Pergunta:

**Quanto tempo os episódios de risco elevado normalmente persistem?**

Arquivo previsto:

`reports/figures/05_duracao_episodios_risco_2018_2025.png`

A visualização deverá representar adequadamente uma distribuição fortemente
assimétrica.

Valores de referência:

- P25: 3 semanas;
- mediana: 4 semanas;
- P75: 9 semanas;
- P90: 19 semanas;
- P95: 26 semanas;
- P99: 41 semanas;
- máximo: 110 semanas.

A figura deverá permitir distinguir:

**duração típica**

de

**episódios extremos**

sem ocultar a existência da cauda longa.

---

# 9. Figura 06 — perfil nacional clima × dengue

Pergunta:

**As associações entre clima e dengue apresentam defasagem temporal?**

Arquivo previsto:

`reports/figures/06_lags_clima_dengue_nacional_2016_2025.png`

Eixo X:

**lag em semanas**

Valores:

0, 1, 2, 3, 4, 6 e 8.

Eixo Y:

**correlação de Spearman mediana municipal**

Serão representadas:

- temperatura média;
- umidade relativa média;
- precipitação total.

Resultados de referência:

- temperatura: maior associação observada no lag 8;
- umidade: maior associação observada no lag 4;
- precipitação: maior associação observada no lag 8.

A figura deverá conter indicação textual ou legenda de que:

**correlação não implica causalidade**

e que o lag 8 representa apenas o maior valor dentro do intervalo
pré-especificado.

---

# 10. Figura 07 — heterogeneidade regional clima × dengue

Pergunta:

**O perfil das associações climáticas é semelhante em todo o Brasil?**

Arquivo previsto:

`reports/figures/07_lags_clima_dengue_regional_2016_2025.png`

A figura deverá evidenciar diferenças como:

- temperatura negativa nos lags curtos no Norte;
- temperatura negativa nos lags curtos no Nordeste;
- associações elevadas de precipitação e umidade no Centro-Oeste;
- crescimento da associação de temperatura no Sudeste;
- crescimento da associação de temperatura no Sul;
- baixa associação da precipitação no Sul.

A visualização deverá evitar excesso de séries simultâneas.

Poderá utilizar organização por variável ou outra composição que mantenha
legibilidade.

---

# 11. Figuras que não serão priorizadas

Não serão produzidas como figuras principais do TCC apenas por disponibilidade
dos dados:

- ranking gráfico de todos os estados;
- ranking gráfico de municípios por casos;
- ranking gráfico de municípios por incidência;
- gráficos individuais para cada ano;
- gráficos individuais para cada região;
- gráficos individuais para cada variável climática;
- mapas diferentes para todos os anos.

Essas informações poderão existir de forma interativa no dashboard sem ocupar
espaço no conjunto principal de figuras acadêmicas.

---

# 12. Padrão técnico das figuras

As figuras estáticas deverão:

- possuir títulos claros;
- identificar unidades;
- evitar eixos truncados enganosos;
- utilizar separadores numéricos legíveis;
- evitar excesso de elementos decorativos;
- apresentar fontes e legendas legíveis;
- manter consistência visual entre gráficos.

Formato principal:

**PNG**

Resolução destinada ao relatório:

**alta resolução, aproximadamente 300 dpi**

Os scripts responsáveis pelas figuras deverão ser reproduzíveis.

---

# 13. Dashboard — visão histórica

O dashboard histórico não deverá carregar diretamente os 2,9 milhões de
registros no navegador.

Serão utilizadas tabelas processadas e agregadas apropriadas para cada
visualização.

A área histórica deverá permitir responder:

**quanto ocorreu?**

**quando ocorreu?**

**onde ocorreu?**

**quanto tempo o risco persistiu?**

**como clima e dengue se associaram historicamente?**

---

# 14. Dashboard — componentes candidatos

## Panorama histórico

Indicadores:

- casos;
- incidência;
- ano;
- variação temporal.

## Sazonalidade

Filtros:

- Brasil;
- região;
- UF;
- município quando aplicável.

## Mapa histórico

Filtros:

- ano;
- período;
- casos;
- incidência;
- região;
- UF.

## Dinâmica do risco

Indicadores:

- municípios simultaneamente em risco;
- episódios;
- duração;
- recorrência.

## Município

Ao selecionar um município poderão ser apresentados:

- histórico de casos;
- incidência;
- episódios de risco;
- semanas em risco;
- episódio mais longo;
- recorrência.

## Clima × dengue

Filtros:

- variável;
- região;
- lag.

A interface deverá deixar explícito que as associações são históricas e não
causais.

---

# 15. Responsividade

Todas as visualizações destinadas ao frontend deverão ser projetadas de forma
responsiva desde a implementação.

Desktop, tablet e mobile não deverão utilizar apenas uma redução proporcional
do mesmo layout.

Em telas menores poderão ser aplicados:

- empilhamento vertical;
- redução do número de séries simultâneas;
- seletores no lugar de múltiplas legendas;
- filtros recolhíveis;
- tooltips;
- painéis de detalhes expansíveis;
- scroll horizontal apenas quando realmente necessário.

---

# 16. Mapa responsivo

Em desktop:

**mapa + filtros + painel lateral**

poderão coexistir.

Em mobile:

o layout deverá privilegiar:

**mapa**

seguido por:

**filtros compactos**

e:

**detalhes expansíveis**

A interação por toque deverá ser considerada desde o início.

---

# 17. Relação com o modelo preditivo

Esta etapa corresponde à consolidação visual da análise histórica.

Ela não será utilizada para:

- retreinar modelos;
- alterar features;
- modificar targets;
- alterar thresholds;
- recalibrar probabilidades.

A área preditiva da aplicação será desenvolvida separadamente a partir dos
resultados já congelados da modelagem.

---

# 18. Regra de congelamento

As sete figuras principais foram selecionadas antes da geração gráfica final.

Caso alguma figura apresente problema técnico ou baixa legibilidade, sua forma
visual poderá ser ajustada.

Entretanto, não serão adicionadas ou removidas figuras principais apenas porque
determinado resultado pareça mais ou menos favorável à narrativa do trabalho.

---

# 19. Sequência de implementação

A produção seguirá a ordem:

1. panorama nacional;
2. sazonalidade;
3. distribuição espacial;
4. dinâmica territorial do risco;
5. duração dos episódios;
6. associação climática nacional;
7. heterogeneidade climática regional.

Cada figura será validada antes da criação da próxima.

---

# 20. Resultado esperado

Ao final da consolidação visual, o conjunto de figuras deverá permitir
compreender a análise histórica do projeto por meio da sequência:

**quanto → quando → onde → como persiste → como se relaciona ao clima**

sem necessidade de apresentar todas as tabelas produzidas nas auditorias.

Status do protocolo:

**CONGELADO ANTES DA GERAÇÃO DAS FIGURAS**