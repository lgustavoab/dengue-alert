# Protocolo da Análise Exploratória Histórica

## 1. Objetivo

Esta etapa tem como objetivo caracterizar o comportamento histórico da dengue
no Brasil entre 2016 e 2025 a partir das bases já tratadas e validadas no
projeto Dengue Alert.

A análise exploratória deverá responder perguntas sobre:

- evolução temporal da dengue;
- sazonalidade epidemiológica;
- distribuição geográfica;
- intensidade e recorrência dos períodos de maior risco;
- diferenças entre regiões, UFs e municípios;
- relações descritivas entre variáveis climáticas e ocorrência de dengue.

A etapa também servirá como base para:

- figuras e tabelas do TCC;
- dashboards históricos da aplicação;
- contextualização dos resultados preditivos;
- seleção de visualizações úteis para o usuário final.

---

# 2. Natureza da análise

Esta etapa é:

**descritiva e exploratória**

Ela não será utilizada para modificar o modelo final já avaliado em 2025.

Portanto, os resultados desta análise não poderão alterar:

- definição do target;
- features utilizadas pelo modelo;
- algoritmo;
- hiperparâmetros;
- calibração;
- thresholds;
- resultados oficiais da avaliação final de 2025.

A análise histórica poderá gerar novas interpretações e visualizações, mas não
será utilizada para reotimizar o modelo final.

---

# 3. Período

O período principal será:

**2016–2025**

Esse intervalo permitirá representar:

- anos de menor circulação;
- anos epidêmicos;
- mudanças de intensidade;
- comportamento sazonal;
- diferenças entre períodos recentes.

Quando determinada análise depender de variáveis ou estruturas disponíveis
somente em parte do período, isso deverá ser indicado explicitamente.

---

# 4. Fontes de dados

A análise utilizará os dados já processados e auditados pelo projeto.

Principais fontes originais:

- SINAN / Ministério da Saúde;
- IBGE;
- ERA5-Land.

A aplicação e os gráficos não utilizarão diretamente os arquivos brutos
originais.

Serão utilizados dados:

**tratados, normalizados, validados e agregados**

principalmente na unidade:

**município × semana epidemiológica**

---

# 5. Base epidemiológica principal

A principal fonte para a análise será:

`data/processed/painel_municipal_semanal_2016_2025.parquet`

O painel contém a estrutura municipal semanal consolidada do projeto.

Variáveis epidemiológicas centrais previstas para análise:

- casos de dengue;
- incidência por 100 mil habitantes;
- incidência acumulada em quatro semanas;
- estado de risco epidemiológico;
- semana epidemiológica;
- ano epidemiológico;
- população;
- município;
- UF.

Outras variáveis poderão ser utilizadas quando já fizerem parte da base
validada e forem necessárias para responder às perguntas definidas neste
protocolo.

---

# 6. Tratamento das unidades territoriais

As análises deverão respeitar as regras territoriais já adotadas no projeto.

Não serão criadas correspondências geográficas novas com base apenas em
semelhança de nomes.

Alterações históricas relevantes de municípios deverão ser explicitadas quando
afetarem a interpretação.

Municípios que não existiam durante todo o período não deverão receber dados
históricos artificiais por imputação territorial.

---

# 7. Panorama nacional

A primeira perspectiva será a evolução nacional da dengue.

Serão produzidas estatísticas como:

- total de casos por ano;
- incidência anual por 100 mil habitantes;
- média semanal de casos;
- máximo semanal de casos;
- semanas de maior atividade epidemiológica;
- quantidade de municípios com registros de casos;
- quantidade de municípios em estado de risco elevado.

A análise buscará identificar:

- anos de maior carga;
- anos de menor carga;
- mudanças bruscas entre anos;
- concentração temporal das grandes ondas.

---

# 8. Série temporal semanal nacional

Será construída uma série agregada por semana epidemiológica.

A série deverá permitir visualizar:

- casos semanais;
- incidência semanal;
- incidência acumulada;
- evolução entre 2016 e 2025.

Quando adequado, poderão ser incluídas médias móveis exclusivamente para
facilitar visualização.

Médias móveis utilizadas em gráficos descritivos não serão confundidas com
features do modelo.

---

# 9. Sazonalidade

A sazonalidade será analisada por semana epidemiológica.

Serão avaliados:

- casos médios por semana do ano;
- incidência média por semana epidemiológica;
- mediana;
- dispersão entre anos;
- período de maior atividade;
- diferenças sazonais entre regiões.

A análise deverá verificar se o período de maior dengue ocorre sempre nas
mesmas semanas ou se existe deslocamento entre anos e regiões.

---

# 10. Comparação entre anos

Os anos de 2016 a 2025 serão comparados individualmente.

Serão observados:

- número total de casos;
- incidência;
- pico semanal;
- semana do pico;
- duração aproximada dos períodos de maior atividade;
- número de municípios afetados.

O objetivo é caracterizar a heterogeneidade temporal entre diferentes anos.

---

# 11. Distribuição por macrorregião

Serão avaliadas as cinco macrorregiões:

- Norte;
- Nordeste;
- Centro-Oeste;
- Sudeste;
- Sul.

Para cada região poderão ser calculados:

- casos;
- incidência;
- participação no total nacional;
- evolução anual;
- sazonalidade;
- número de municípios afetados;
- frequência de estado de risco elevado.

A análise buscará identificar diferenças de magnitude e calendário
epidemiológico.

---

# 12. Distribuição por unidade federativa

A análise também será realizada para as 27 unidades federativas.

Serão utilizados indicadores como:

- casos;
- incidência;
- evolução anual;
- sazonalidade;
- quantidade de municípios afetados.

Rankings deverão sempre indicar a métrica utilizada.

Não será apresentado ranking de casos absolutos como equivalente a ranking de
risco epidemiológico, pois estados com populações maiores naturalmente podem
concentrar mais registros.

---

# 13. Distribuição municipal

A análise municipal deverá priorizar indicadores normalizados.

Poderão ser avaliados:

- municípios com maior incidência;
- municípios com maior carga acumulada;
- frequência de semanas em estado de risco elevado;
- recorrência de períodos de alta incidência;
- persistência do risco;
- número de anos com atividade elevada.

Rankings municipais deverão possuir critérios mínimos de suporte quando
necessário para evitar interpretações baseadas em poucas observações.

---

# 14. Distribuição da incidência

A distribuição da incidência municipal será analisada para avaliar:

- assimetria;
- valores extremos;
- diferenças entre anos;
- diferenças entre regiões;
- concentração da carga epidemiológica.

Poderão ser utilizados:

- percentis;
- histogramas;
- boxplots;
- escala logarítmica quando apropriada.

Valores extremos não serão removidos apenas por serem altos.

Qualquer exclusão deverá possuir justificativa epidemiológica ou de qualidade
de dados.

---

# 15. Dinâmica dos períodos de risco

Será analisado o comportamento do estado:

`risco_elevado`

Poderão ser derivados indicadores como:

- quantidade de semanas de risco por município;
- duração de sequências consecutivas de risco;
- quantidade de episódios;
- recorrência entre anos;
- número de municípios simultaneamente em risco.

O objetivo é caracterizar não apenas a ocorrência de dengue, mas a dinâmica
temporal dos períodos de maior risco epidemiológico.

---

# 16. Ondas epidemiológicas

Quando tecnicamente viável, serão descritos períodos contínuos de maior
atividade epidemiológica.

A análise poderá observar:

- início;
- duração;
- pico;
- intensidade;
- número de municípios afetados.

A definição utilizada para uma onda deverá ser registrada antes da
interpretação dos resultados.

Não serão criadas definições diferentes apenas para produzir resultados mais
visualmente favoráveis.

---

# 17. Variáveis climáticas

A análise climática utilizará as variáveis ERA5-Land já integradas ao projeto.

Variáveis principais:

- temperatura do ar a 2 metros;
- umidade relativa derivada;
- precipitação.

A análise climática terá caráter:

**descritivo e associativo**

Não será interpretada como evidência causal.

---

# 18. Clima e dengue

Serão exploradas relações entre condições climáticas e atividade
epidemiológica.

Poderão ser analisados:

- temperatura × incidência;
- umidade × incidência;
- precipitação × incidência;
- diferenças entre níveis de risco;
- relações defasadas entre clima e dengue.

As defasagens deverão ser definidas de forma explícita.

A análise deverá considerar que relações climáticas podem variar entre regiões
e períodos do ano.

---

# 19. Relações defasadas

Poderão ser avaliadas associações entre clima observado em semanas anteriores
e dengue observada posteriormente.

Exemplos de defasagens previstas:

- lag 0;
- lag 1;
- lag 2;
- lag 3;
- lag 4;
- lag 6;
- lag 8.

Essas análises serão exploratórias.

Correlação não será interpretada como causalidade.

Também não será utilizada para alterar as features do modelo final.

---

# 20. Cobertura climática

As análises que utilizarem clima deverão registrar explicitamente:

- quantidade de municípios com dados;
- quantidade de observações válidas;
- eventuais unidades territoriais sem cobertura.

Resultados climáticos não deverão ser apresentados como nacionais sem indicar
a cobertura efetiva da base.

---

# 21. Visualizações previstas

Entre as visualizações candidatas estão:

- linha temporal nacional;
- comparação anual;
- curva sazonal por semana epidemiológica;
- heatmap ano × semana;
- mapas municipais;
- séries por região;
- séries por UF;
- distribuição da incidência;
- duração dos episódios de risco;
- correlações climáticas defasadas.

Nem todas obrigatoriamente entrarão na aplicação final.

A seleção para o dashboard será feita posteriormente com base em utilidade,
clareza e relevância analítica.

---

# 22. Dashboard histórico

A aplicação final deverá possuir uma área dedicada à análise histórica.

Essa área utilizará dados processados, e não os arquivos brutos originais.

Funcionalidades candidatas:

- filtros por período;
- região;
- UF;
- município;
- visualização temporal;
- mapa;
- comparação entre anos;
- sazonalidade;
- indicadores epidemiológicos;
- contexto climático.

O dashboard histórico será separado conceitualmente da área de previsão.

---

# 23. Indicadores principais do dashboard

Indicadores candidatos incluem:

- casos no período;
- incidência por 100 mil habitantes;
- municípios com casos;
- municípios em risco elevado;
- semana de maior atividade;
- variação em relação ao período anterior.

A definição final dos KPIs ocorrerá depois da análise exploratória.

---

# 24. Figuras para o TCC

As figuras deverão ser produzidas por scripts reprodutíveis.

Arquivos destinados ao relatório poderão ser salvos em:

`reports/figures/`

As figuras deverão possuir:

- título claro;
- unidades explícitas;
- eixos identificados;
- período indicado;
- fonte descrita posteriormente no texto do TCC.

---

# 25. Tabelas para o TCC

Resultados consolidados poderão ser salvos em:

`reports/audits/`

ou em artefatos específicos de análise.

As tabelas deverão permitir reprodução automática sempre que possível.

---

# 26. Reprodutibilidade

As análises deverão ser implementadas preferencialmente em scripts Python.

Notebooks poderão ser utilizados para exploração visual, mas resultados
definitivos deverão ser reproduzíveis por scripts sempre que possível.

O processamento não deverá depender de edição manual dos resultados.

---

# 27. Validação

Cada etapa deverá validar, quando aplicável:

- quantidade de linhas;
- período;
- número de municípios;
- presença de valores ausentes;
- valores não finitos;
- duplicidades;
- preservação de totais epidemiológicos;
- cobertura territorial.

Resultados inconsistentes deverão interromper a análise antes da geração dos
artefatos finais.

---

# 28. Ordem de execução

A análise será dividida em:

## 12A — Panorama nacional

- evolução 2016–2025;
- totais anuais;
- incidência;
- série semanal.

## 12B — Sazonalidade

- semana epidemiológica;
- diferenças entre anos;
- diferenças entre regiões.

## 12C — Distribuição espacial

- macrorregião;
- UF;
- município.

## 12D — Dinâmica epidemiológica

- semanas de risco;
- duração;
- recorrência;
- episódios.

## 12E — Clima e dengue

- temperatura;
- umidade;
- precipitação;
- relações defasadas.

## 12F — Consolidação visual

- figuras;
- tabelas;
- seleção de indicadores para dashboard.

---

# 29. Limitações

A análise utilizará dados retrospectivos de vigilância epidemiológica.

Devem ser consideradas limitações como:

- atrasos de notificação;
- revisões posteriores;
- diferenças de capacidade de vigilância;
- mudanças metodológicas;
- mudanças populacionais;
- mudanças territoriais;
- diferenças regionais de cobertura.

Os resultados descritivos não representam necessariamente transmissão em
tempo real.

---

# 30. Relação com o modelo preditivo

A análise histórica complementa, mas não modifica, a avaliação preditiva.

O projeto final deverá permitir responder a duas classes de perguntas:

**O que aconteceu historicamente?**

e

**Qual é o risco de aumento nas próximas semanas?**

A primeira será atendida principalmente pelos dashboards históricos.

A segunda será atendida pelo módulo preditivo já desenvolvido e avaliado.

---

# 31. Estado metodológico

Este protocolo foi definido antes da geração dos resultados da análise
exploratória histórica desta etapa.

As análises poderão ser refinadas tecnicamente quando necessário, mas qualquer
alteração relevante de escopo deverá ser documentada.

O próximo passo será iniciar a análise nacional de 2016–2025.

Status:

**PROTOCOLO DEFINIDO**