# Dengue Alert — Documentação da Fase Exploratória e de Preparação dos Dados

**Projeto:** TCC em Ciência de Dados — Sistema de alerta antecipado de risco de dengue
**Período analisado:** 2016–2025
**Escopo deste documento:** registrar o trabalho realizado **antes da criação e organização do repositório definitivo `dengue-alert`**, consolidando as fontes consultadas, os dados obtidos, as decisões metodológicas, as auditorias realizadas e os artefatos produzidos durante a fase exploratória.

> **Importante:** este documento é um registro retrospectivo da fase de exploração, auditoria e preparação das fontes. Ele não substitui a metodologia final do TCC. Algumas decisões poderão ser refinadas na etapa de modelagem, desde que qualquer alteração seja documentada e reavaliada quanto a vazamento temporal, cobertura geográfica e reprodutibilidade.

---

## 1. Objetivo da fase exploratória

Antes de iniciar a construção definitiva do pipeline, da base de modelagem e da aplicação, foi realizada uma fase extensa de exploração e auditoria das três famílias de dados necessárias ao projeto:

1. **SINAN / Ministério da Saúde** — registros de dengue;
2. **IBGE** — estrutura territorial, população e referências geográficas;
3. **ERA5-Land / Copernicus / ECMWF** — variáveis meteorológicas.

A finalidade desta etapa não foi treinar modelos, mas responder primeiro às seguintes perguntas:

- Os dados epidemiológicos disponíveis são consistentes ao longo de 2016–2025?
- Qual variável temporal representa melhor o início do episódio de dengue?
- Qual município deve ser usado como referência: notificação ou residência?
- Como compatibilizar os códigos municipais do SINAN com os códigos oficiais do IBGE?
- Como representar semanas sem registros de dengue?
- Como obter denominadores populacionais para calcular incidência?
- Como tratar mudanças territoriais ocorridas no período?
- Como obter uma coordenada representativa por unidade territorial?
- Como relacionar municípios a células do ERA5-Land?
- Como converter os dados meteorológicos horários para semanas epidemiológicas locais?
- Há cobertura climática adequada para todas as unidades territoriais?
- Quais exceções precisam ser explicitamente documentadas antes da modelagem?

O produto final desta fase foi um conjunto de **artefatos intermediários auditados**, considerado apto para ser migrado para a arquitetura definitiva do projeto.

---

# 2. Visão geral das fontes

| Fonte | Instituição | Uso no projeto |
|---|---|---|
| SINAN/Dengue | Ministério da Saúde / OpenDataSUS | Casos prováveis de dengue por município de residência e semana epidemiológica |
| Divisão Territorial Brasileira — DTB | IBGE | Referência oficial de códigos e unidades territoriais |
| Estimativas Populacionais e Censo 2022 | IBGE | Denominadores municipais para cálculo de incidência |
| Cadastro de Localidades 2022 | IBGE | Coordenadas representativas das sedes/localidades municipais |
| Malha Municipal Digital 2024 | IBGE | Validação territorial e suporte ao mapeamento espacial para ERA5-Land |
| ERA5-Land | Copernicus Climate Change Service / ECMWF | Temperatura, ponto de orvalho, umidade relativa derivada e precipitação |

---

# 3. SINAN — dados epidemiológicos de dengue

## 3.1 Fonte

Os registros de dengue utilizados na exploração foram obtidos a partir do conjunto público **Sinan/Dengue**, disponibilizado pelo Ministério da Saúde no portal OpenDataSUS.

Fonte oficial:

- OpenDataSUS — Sinan/Dengue:
  https://opendatasus.saude.gov.br/dataset/arboviroses-dengue
- DATASUS — Doenças e Agravos de Notificação — SINAN:
  https://datasus.saude.gov.br/acesso-a-informacao/doencas-e-agravos-de-notificacao-de-2007-em-diante-sinan/

O próprio conjunto informa que o SINAN tem como objetivo coletar, transmitir e disseminar dados produzidos pela vigilância epidemiológica e que a dengue é agravo de notificação compulsória.

Foram utilizados arquivos anuais correspondentes ao período de 2016 a 2025:

```text
DENGBR16.csv
DENGBR17.csv
DENGBR18.csv
DENGBR19.csv
DENGBR20.csv
DENGBR21.csv
DENGBR22.csv
DENGBR23.csv
DENGBR24.csv
DENGBR25.csv
```

Os arquivos brutos foram preservados durante a auditoria e não foram alterados.

## 3.2 Unidade temporal escolhida

Uma das primeiras decisões metodológicas foi definir **qual semana epidemiológica deveria representar o caso**.

Para o TCC, a referência escolhida foi a semana associada aos **primeiros sintomas**, representada principalmente por:

```text
SEM_PRI
```

e, quando necessário para conferência:

```text
DT_SIN_PRI
```

A semana de notificação não foi adotada como eixo temporal principal porque o objetivo do trabalho é estudar a dinâmica epidemiológica e meteorológica associada ao início dos casos, e não o momento administrativo em que a notificação entrou no sistema.

Portanto, a unidade temporal da série final tornou-se:

```text
ano_epidemiologico × semana_epidemiologica
```

## 3.3 Unidade geográfica escolhida

A referência geográfica adotada foi o **município de residência do caso**, e não o município onde a notificação foi registrada.

Campo principal utilizado:

```text
ID_MN_RESI
```

Essa escolha é coerente com o objetivo de relacionar a ocorrência epidemiológica às condições ambientais do local de residência.

## 3.4 Regra para casos prováveis

Durante a auditoria dos dicionários do SINAN foi observado que os códigos de classificação não são completamente estáveis entre versões históricas e atuais do sistema.

A regra operacional validada para o período estudado foi:

- excluir registros marcados como descartados com `CLASSI_FIN = 5`;
- não remover automaticamente outros códigos de classificação apenas por interpretação histórica;
- excluir `NDUPLIC_N = 2` caso exista registro marcado como duplicado/não contabilizável.

Nas auditorias executadas, não foram encontrados registros com `NDUPLIC_N = 2`.

Também foi constatado que o código `CLASSI_FIN = 5` deixa de aparecer nos arquivos exportados a partir de 2022. O projeto **não atribuiu uma causa a essa mudança sem documentação oficial específica**; apenas registrou a diferença observada.

## 3.5 Primeira versão do processamento e correção

Uma versão inicial do processamento epidemiológico foi considerada inválida.

O problema estava relacionado ao comportamento de máscaras booleanas com `pd.NA` em colunas `StringDtype` do Pandas, o que podia produzir filtragem incorreta.

Essa versão foi descartada.

A versão considerada válida passou a ser o processamento **V2**, implementado durante a fase exploratória.

## 3.6 Funil de preparação dos arquivos SINAN

O conjunto bruto de 2016–2025 totalizou:

**19.336.281 registros.**

A sequência validada do processamento V2 foi:

1. carregar os dez arquivos anuais;
2. verificar duplicidade lógica segundo `NDUPLIC_N`;
3. remover apenas registros com `CLASSI_FIN = 5`;
4. normalizar o município de residência para o código SINAN de seis dígitos;
5. validar `SEM_PRI` no padrão `AAAASS`;
6. extrair ano epidemiológico;
7. extrair semana epidemiológica;
8. manter somente anos entre 2016 e 2025;
9. manter somente semanas epidemiológicas válidas;
10. agregar por município, ano e semana.

Resultados da auditoria:

| Etapa | Quantidade |
|---|---:|
| Registros brutos | 19.336.281 |
| Registros removidos por `CLASSI_FIN = 5` | 3.002.212 |
| Município inválido | 1.149 |
| `SEM_PRI` inválida | 79 |
| Fora do período 2016–2025 | 37.896 |
| Registros mantidos após filtros | 16.294.945 |
| Grupos município × ano × semana antes da normalização territorial final | 723.860 |
| Códigos SINAN de seis dígitos encontrados | 5.621 |

---

# 4. Compatibilização territorial SINAN × IBGE

## 4.1 Referência territorial

Para validar os códigos de município foi utilizada a **Divisão Territorial Brasileira — DTB 2025**, do IBGE.

Fonte oficial:

https://www.ibge.gov.br/geociencias/organizacao-do-territorio/divisao-regional/23701-divisao-territorial-brasileira.html

Arquivo utilizado na exploração:

```text
RELATORIO_DTB_BRASIL_2025_MUNICIPIOS.xls
```

Na base de trabalho, a referência oficial resultou em **5.571 unidades territoriais**, correspondentes a:

- 5.569 municípios;
- Distrito Federal;
- Distrito Estadual de Fernando de Noronha.

O código IBGE oficial possui sete dígitos, enquanto o SINAN trabalha, em diversos campos, com representação municipal de seis dígitos. A compatibilização foi feita preservando ambos os identificadores.

## 4.2 Primeiro cruzamento

Dos 5.621 códigos SINAN distintos encontrados inicialmente:

- **5.561** foram associados diretamente à referência territorial do IBGE;
- **60** não foram associados diretamente;
- esses 60 códigos representavam **22.878 casos**.

A taxa de casos inicialmente não associados foi de aproximadamente:

**0,140399% dos casos.**

## 4.3 Subdivisões do Distrito Federal

A investigação mostrou que 48 dos códigos não encontrados pertenciam a subdivisões internas do Distrito Federal.

Eles representavam:

**22.846 casos.**

Em vez de descartá-los, os registros foram consolidados na unidade territorial oficial de Brasília:

```text
SINAN: 530010
IBGE:  5300108
```

Com isso, os casos foram preservados.

## 4.4 Códigos residuais não municipais

Após o tratamento do Distrito Federal restaram 12 códigos que não correspondiam a municípios oficiais utilizados na referência do projeto.

Eles representavam apenas **32 casos** e foram excluídos sem tentativa de atribuição especulativa a outro município:

| Código | Casos |
|---|---:|
| 110000 | 8 |
| 520000 | 5 |
| 330000 | 3 |
| 410000 | 3 |
| 520100 | 3 |
| 290000 | 2 |
| 350000 | 2 |
| 520950 | 2 |
| 310000 | 1 |
| 335050 | 1 |
| 520720 | 1 |
| 521510 | 1 |

## 4.5 Resultado da normalização territorial

Após o tratamento territorial:

- linhas agregadas: **721.309**;
- códigos SINAN representados: **5.561**;
- casos preservados: **16.294.913**;
- códigos sem correspondência no IBGE: **0**;
- unidades IBGE sem qualquer registro de dengue no período: **10**.

As dez unidades oficiais sem registro de dengue na série observada foram:

- Calmon — SC;
- Macieira — SC;
- Ponte Alta do Norte — SC;
- Urupema — SC;
- Arroio do Padre — RS;
- Campestre da Serra — RS;
- Coqueiro Baixo — RS;
- Itapuca — RS;
- Muitos Capões — RS;
- Santo Expedito do Sul — RS.

A ausência de registros não foi interpretada como prova de ausência de infecções; apenas como ausência de casos representados no extrato utilizado.

---

# 5. Calendário epidemiológico e preenchimento de semanas sem registros

## 5.1 Calendário epidemiológico

Foi construído um calendário epidemiológico explícito para 2016–2025.

A regra adotada foi compatível com semanas epidemiológicas de domingo a sábado, com a semana 1 definida de forma a conter o dia 4 de janeiro.

Quantidade de semanas no período:

- 2020: 53 semanas;
- 2025: 53 semanas;
- demais anos: 52 semanas.

Total:

**522 semanas epidemiológicas.**

Foi gerado o artefato:

```text
calendario_epidemiologico_2016_2025.csv
```

## 5.2 Zero-fill

A série original contém apenas combinações em que há registro epidemiológico.

Para modelagem temporal, isso criaria um problema: ausência de linha poderia significar tanto “nenhum caso registrado” quanto “combinação inexistente”.

Por isso foi construído um painel explícito município × semana, preenchendo com zero as semanas válidas sem registro de caso.

Resultado:

| Indicador | Quantidade |
|---|---:|
| Linhas antes do zero-fill | 721.309 |
| Linhas depois do zero-fill | 2.907.593 |
| Linhas preenchidas com zero | 2.186.284 |
| Casos antes | 16.294.913 |
| Casos depois | 16.294.913 |

A soma de casos foi preservada integralmente.

Foi mantida informação para distinguir:

- semana originalmente presente no SINAN;
- semana criada por preenchimento;
- valor de casos.

Assim, `0` significa:

> nenhum caso provável representado no extrato para aquela unidade territorial e semana.

Não significa necessariamente ausência real de transmissão.

## 5.3 Boa Esperança do Norte — MT

Foi necessário respeitar a existência histórica das unidades territoriais.

Boa Esperança do Norte — MT:

```text
IBGE: 5101837
SINAN: 510183
```

passou a existir oficialmente em 2025 para a finalidade adotada no projeto.

Por isso, **não foram criadas semanas artificiais para 2016–2024**.

Na base epidemiológica consolidada, a unidade possui apenas as **53 semanas de 2025**.

Essa regra é importante porque o painel mestre definitivo deverá usar a epidemiologia como referência para a existência histórica de cada unidade, evitando criar retrospectivamente observações de municípios que ainda não existiam.

---

# 6. IBGE — população

## 6.1 Objetivo

O número absoluto de casos não permite comparar adequadamente municípios de tamanhos muito diferentes.

Por isso foi necessário obter a população de cada município por ano e calcular:

```text
incidência = casos / população × 100.000
```

## 6.2 Fontes

Foram utilizadas publicações oficiais anuais do IBGE e o Censo Demográfico 2022.

Fonte principal das estimativas populacionais:

https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html

Durante a auditoria foram trabalhados dados para:

- 2016;
- 2017;
- 2018;
- 2019;
- 2020;
- 2021;
- 2022 — Censo Demográfico;
- 2024;
- 2025.

Não foi encontrada uma publicação anual equivalente para 2023 com a mesma natureza necessária ao painel.

## 6.3 Regra adotada para 2023

Para 2023, foi decidido **reutilizar explicitamente a população do Censo 2022**.

Não foi feita interpolação.

O artefato final registra:

- população;
- tipo de população;
- ano de referência da população;
- arquivo-fonte.

Isso permite que 2023 seja identificado como uma decisão metodológica transparente, e não confundido com uma estimativa oficial anual inexistente na série utilizada.

## 6.4 Auditorias de população

Somatórios nacionais registrados durante a exploração:

| Ano | População usada |
|---|---:|
| 2016 | 206.081.432 |
| 2017 | 207.660.929 |
| 2018 | 208.494.900 |
| 2019 | 210.147.125 |
| 2020 | 211.755.692 |
| 2021 | 213.317.639 |
| 2022 | 203.078.668 |
| 2024 | 212.583.750 |
| 2025 | 213.421.037 |

A forte diferença 2021 → 2022 foi tratada como **descontinuidade de fonte/metodologia associada ao Censo 2022**, e não como evidência de uma queda populacional real dessa magnitude.

Para 2024 foi preservada, na exploração, a versão originalmente selecionada da estimativa publicada no DOU:

```text
estimativa_dou_2024.xls
```

em vez de trocar silenciosamente a fonte por revisões posteriores.

## 6.5 Integração população × dengue

A população foi associada ao painel epidemiológico.

Resultado:

- linhas antes: **2.907.593**;
- linhas depois: **2.907.593**;
- casos antes: **16.294.913**;
- casos depois: **16.294.913**;
- linhas sem população: **0**;
- anos com compatibilidade validada: **10/10**.

Foi produzido o artefato intermediário:

```text
dengue_semanal_2016_2025_com_populacao.parquet
```

Esse arquivo passou a ser a principal base epidemiológica preparada para a integração com clima.

---

# 7. IBGE — coordenadas e localidades

## 7.1 Fonte

Foi utilizado o arquivo geoespacial oficial do IBGE:

```text
BR_localidades_2022.gpkg
```

Sistema de referência espacial:

```text
SIRGAS 2000 — EPSG:4674
```

O arquivo continha:

**96.163 localidades.**

O objetivo não era usar todas as localidades, mas obter uma coordenada representativa para cada unidade municipal.

## 7.2 Seleção das cidades

A categoria `Cidade` continha:

- 5.596 linhas;
- 5.570 municípios distintos.

Foram identificadas 26 duplicações relacionadas a capitais; as coordenadas dessas duplicações eram equivalentes para a finalidade do projeto.

Fernando de Noronha exigiu tratamento específico por sua natureza territorial.

Após a normalização foi criado um conjunto final com:

**5.571 coordenadas territoriais.**

Cobertura:

**5.571 / 5.571 unidades.**

Artefato produzido:

```text
coordenadas_municipais_ibge_2025.csv
```

As coordenadas representam a **sede/localidade municipal usada como proxy espacial**. Elas não representam o centro de massa da população nem a média climática de toda a área territorial.

---

# 8. IBGE — Malha Municipal Digital 2024

## 8.1 Fonte

Para verificações territoriais e suporte à seleção de células climáticas foi utilizada a Malha Municipal Digital 2024 do IBGE.

Fonte oficial:

https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html

Arquivo principal trabalhado:

```text
BR_Municipios_2024.shp
```

Sistema de referência:

```text
SIRGAS 2000 — EPSG:4674
```

## 8.2 Auditoria da malha

A malha continha:

**5.573 feições.**

Duas feições não eram municípios/unidades territoriais de interesse para o painel:

- Lagoa Mirim;
- Lagoa dos Patos.

Após a exclusão dessas áreas operacionais:

**5.571 unidades territoriais.**

Foi detectada uma geometria inválida:

```text
Selvíria — MS
IBGE 5007802
```

Essa ocorrência foi registrada durante a auditoria geoespacial.

Boa Esperança do Norte já estava presente na malha 2024 utilizada.

---

# 9. ERA5-Land — dados meteorológicos

## 9.1 Fonte

Os dados meteorológicos foram obtidos do **ERA5-Land**, produzido no ecossistema ECMWF e disponibilizado pelo **Copernicus Climate Change Service — Climate Data Store (CDS)**.

Fonte oficial do ERA5-Land:

https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land

Fonte utilizada para séries temporais:

https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries

O ERA5-Land fornece reanálise climática horária em grade regular de aproximadamente:

```text
0,1° × 0,1°
```

com resolução nativa informada pelo provedor em torno de:

```text
9 km
```

A série temporal utilizada é apropriada para recuperação de longas séries em pontos de grade.

## 9.2 Variáveis selecionadas

Foram selecionadas três variáveis meteorológicas básicas:

```text
2m temperature
2m dewpoint temperature
total precipitation
```

A partir delas foram produzidas as variáveis semanais:

- temperatura média;
- temperatura mínima;
- temperatura máxima;
- ponto de orvalho médio;
- umidade relativa média;
- precipitação total.

Unidades originais relevantes:

- temperatura: Kelvin;
- ponto de orvalho: Kelvin;
- precipitação: metros de água.

Conversões:

```text
°C = K - 273,15
mm = m × 1000
```

---

# 10. Piloto meteorológico e correção da precipitação

Antes do processamento nacional foi realizado um teste com Penápolis — SP:

```text
IBGE: 3537305
latitude aproximada:  -21.419399
longitude aproximada: -50.076599
```

O teste inicial confirmou a recuperação de temperatura e permitiu baixar um intervalo multivariável de janeiro de 2024.

Durante esse piloto foi detectado um problema importante: o cálculo de precipitação estava produzindo incrementos negativos devido a uma interpretação inadequada da variável acumulada.

A investigação da estrutura do produto time-series/ARCO mostrou que, para esse acesso, a precipitação já é disponibilizada de forma adequada para representar o valor horário de cada intervalo.

A regra corrigida passou a ser:

```text
precipitação horária = tp × 1000
```

**sem aplicar diferenciação entre horas consecutivas.**

Pequenos valores negativos podem aparecer por efeitos numéricos/de processamento do produto.

Eles foram tratados de forma explícita, com auditoria de magnitude.

---

# 11. Umidade relativa derivada

O ERA5-Land não precisava fornecer diretamente a umidade relativa para o projeto.

Ela foi derivada a partir de:

- temperatura a 2 m;
- temperatura do ponto de orvalho a 2 m.

Foi utilizada a formulação de Magnus para estimar a umidade relativa horária.

Depois, a variável foi agregada semanalmente.

A auditoria final exigiu:

```text
0% <= umidade_relativa <= 100%
```

Não foram encontradas violações no produto semanal aprovado.

---

# 12. Conversão de UTC para horário civil local

O ERA5-Land é temporalmente referenciado em UTC.

Entretanto, uma semana epidemiológica deve ser compatível com o calendário civil do município.

Por isso, os timestamps climáticos foram convertidos para o **fuso horário IANA da unidade territorial antes da agregação semanal**.

Foi criado o artefato:

```text
fusos_horarios_municipios_ibge_2025.csv
```

Cobertura:

**5.571 unidades territoriais.**

Foram identificados 16 fusos IANA no conjunto territorial completo; após a exclusão climática de Fernando de Noronha, o conjunto modelável utilizou 15.

## 12.1 Horário de verão histórico

O período 2016–2025 inclui anos em que algumas regiões brasileiras ainda apresentavam horário de verão.

Por isso, não foi assumido que toda semana possui exatamente 168 horas.

Em fusos historicamente afetados, uma semana local pode conter:

```text
167 horas
168 horas
169 horas
```

Os valores esperados foram derivados a partir dos limites locais timezone-aware.

Os fusos em que foram observadas semanas com 167/169 horas foram:

- `America/Sao_Paulo`;
- `America/Cuiaba`;
- `America/Campo_Grande`.

Isso evitou classificar corretamente como incompleta uma semana alterada por transição de horário de verão.

---

# 13. Regra de fronteira temporal dos dados meteorológicos

Também foi necessário registrar a semântica temporal diferente entre variáveis instantâneas e precipitação.

Para temperatura e ponto de orvalho, o valor com timestamp `t` representa a condição naquele instante.

A agregação foi tratada no intervalo:

```text
[start, end)
```

Para precipitação, o valor horário com timestamp `t` representa o intervalo horário que termina em `t`.

A regra foi tratada como:

```text
(start, end]
```

Essa distinção foi mantida para alinhar corretamente os valores climáticos aos limites das semanas epidemiológicas.

---

# 14. Mapeamento município → célula ERA5-Land

## 14.1 Princípio

A estratégia climática utiliza a célula ERA5-Land associada à **sede municipal como proxy**, e não uma média espacial de toda a área do município.

A escolha foi documentada para que o TCC não confunda:

> clima no ponto representativo da sede

com:

> clima médio de toda a extensão territorial municipal.

## 14.2 Regra de seleção validada

A regra final foi fechada em quatro etapas:

1. usar a célula ERA5 geometricamente mais próxima da sede, se válida;
2. se a célula mais próxima não for válida, procurar a célula ERA5 válida mais próxima cuja célula de 0,1° intercepte o próprio território da unidade;
3. se nenhuma célula válida intercepte o território, permitir fallback externo para unidade insular quando a célula terrestre válida mais próxima estiver a até **15 km**;
4. acima desse limite, excluir a unidade da modelagem climática.

O limite de 15 km foi uma **decisão metodológica do projeto tomada após a análise das exceções**, e não um limite oficial do ERA5-Land.

## 14.3 Casos insulares

A regra permitiu manter duas unidades por fallback externo dentro de 15 km:

- Itaparica;
- Madre de Deus.

Fernando de Noronha não possuía cobertura ERA5-Land terrestre suficientemente próxima dentro do critério adotado.

Distância aproximada encontrada:

**368,88 km.**

Por isso Fernando de Noronha foi explicitamente marcado como:

```text
modelavel_era5_land = False
```

e excluído apenas da modelagem que exige clima.

Ele foi mantido na auditoria epidemiológica, populacional e territorial.

---

# 15. Resultado do mapeamento espacial ERA5-Land

Resultado final:

| Situação | Unidades |
|---|---:|
| Unidades territoriais avaliadas | 5.571 |
| Modeláveis no ERA5-Land | 5.570 |
| Excluídas | 1 |
| Célula mais próxima válida | 5.486 |
| Fallback com célula que intercepta o município | 82 |
| Fallback externo insular ≤ 15 km | 2 |
| Exclusão | 1 |

Outros indicadores:

- células ERA5 distintas utilizadas: **5.203**;
- combinações distintas `célula × timezone`: **5.213**;
- maior distância sede → célula final entre unidades modeláveis: aproximadamente **29,10 km**.

A distância máxima pode ser superior a 15 km nos casos em que a célula selecionada satisfaz o critério territorial de interseção. O limite de 15 km foi aplicado especificamente ao fallback externo insular.

Artefatos produzidos:

```text
mapeamento_climatico_era5_final.csv
exclusoes_climaticas.csv
combinacoes_grid_timezone.csv
mapeamento_unidades_combo_id.csv
```

---

# 16. Otimização do processamento nacional do ERA5-Land

Processar todas as unidades individualmente produziria trabalho repetido, pois municípios diferentes podem compartilhar:

- a mesma célula ERA5;
- e o mesmo fuso horário.

Por isso foi criada a entidade:

```text
combo_id = combinação única de célula ERA5 × timezone
```

Resultado:

```text
5.570 unidades modeláveis
        ↓
5.203 células distintas
        ↓
5.213 combinações célula × timezone
```

O processamento climático nacional foi executado uma vez por `combo_id`, e depois cada município seria associado à série correspondente.

Essa estratégia reduziu duplicação de processamento e de armazenamento.

---

# 17. Processamento ERA5-Land nacional 2016–2025

O processamento definitivo da fase exploratória cobriu:

**5.213 combinações × 522 semanas = 2.721.186 linhas.**

Características registradas:

- processamento em 163 lotes;
- lote de 32 combinações;
- leitura vetorizada de ARCO/Zarr geo-chunked;
- período UTC ampliado para acomodar os limites das semanas nos diferentes fusos.

Janela processada:

```text
2016-01-03T02:00Z
até
2026-01-04T05:00Z
```

Artefato climático semanal principal:

```text
era5_semanal_combinacoes_2016_2025.parquet
```

---

# 18. Auditoria da precipitação

Durante o processamento nacional foram registrados:

**5.930.373 valores horários negativos muito pequenos** de precipitação.

Mínimo observado:

```text
-0.000061030732 mm
```

Esses valores foram interpretados como artefatos numéricos/de desagregação do produto e corrigidos no processamento.

Também foi criado um limite de segurança conservador:

```text
tp < -0.01 mm
```

Caso um valor mais negativo que esse aparecesse, o processamento deveria ser interrompido para investigação.

Esse valor não foi tratado como “limite físico oficial”, mas como **gate de segurança do pipeline**.

---

# 19. Auditoria final do ERA5-Land

A fase de aquisição e preparação climática foi encerrada somente após a auditoria nacional.

Resultado:

```text
STATUS: APROVADO
```

Indicadores:

| Verificação | Resultado |
|---|---:|
| Combinações auxiliares | 5.213 |
| Unidades modeláveis | 5.570 |
| Células ERA5 distintas | 5.203 |
| Fusos do conjunto modelável | 15 |
| Linhas no Parquet semanal | 2.721.186 |
| Chaves distintas | 2.721.186 |
| Combinações com 522 semanas | 5.213 |
| Chaves duplicadas | 0 |
| Horas inválidas | 0 |
| Violações de temperatura | 0 |
| Umidade fora de 0–100% | 0 |
| Precipitação semanal negativa | 0 |
| Problemas críticos | 0 |

A partir desse ponto, a coleta/preparação do ERA5-Land foi considerada **fechada e aprovada** para a próxima fase.

---

# 20. Artefatos aprovados ao final da fase exploratória

Os principais artefatos considerados aptos para migração para o projeto definitivo foram:

## Epidemiologia

```text
calendario_epidemiologico_2016_2025.csv
dengue_semanal_2016_2025_com_populacao.parquet
```

## População

```text
populacao_ibge_2016_2025_final.csv
```

## Geografia

```text
coordenadas_municipais_ibge_2025.csv
fusos_horarios_municipios_ibge_2025.csv
```

## Clima

```text
combinacoes_grid_timezone.csv
era5_semanal_combinacoes_2016_2025.parquet
exclusoes_climaticas.csv
mapeamento_climatico_era5_final.csv
mapeamento_unidades_combo_id.csv
```

Os arquivos de diagnóstico, pilotos, benchmarks, lotes intermediários e scripts experimentais foram mantidos no workspace legado como evidência da exploração, mas **não foram considerados parte da camada limpa de dados intermediários do projeto definitivo**.

---

# 21. Estado das bases ao final da exploração

## Epidemiologia + população

```text
2.907.593 linhas
5.571 unidades territoriais
2016–2025
16.294.913 casos prováveis preservados
0 linhas sem população
```

## Clima

```text
2.721.186 linhas semanais por combo
5.213 combos célula × timezone
5.570 unidades territorialmente modeláveis
1 exclusão climática
```

## Exclusão climática

```text
2605459 — Fernando de Noronha
```

## Unidade com existência apenas em 2025

```text
5101837 — Boa Esperança do Norte — MT
53 semanas
```

---

# 22. Validação posterior da migração para a estrutura definitiva

Embora esta etapa já pertença ao início da organização do repositório novo, ela serve como confirmação de que a fase exploratória foi preservada corretamente.

Os dez artefatos aprovados foram **copiados**, e não movidos, para:

```text
data/interim/
```

na nova arquitetura.

Foi calculado SHA-256 para cada arquivo na origem legada e na cópia.

Resultado:

```text
10 / 10 arquivos idênticos
```

Assim, os artefatos do novo projeto são byte a byte iguais aos arquivos aprovados na exploração.

---

# 23. Validação das chaves para a futura integração

Antes de construir o painel mestre, foi realizada uma auditoria das chaves dos artefatos.

Resultado:

```text
STATUS: APROVADO
```

Principais verificações:

| Verificação | Resultado |
|---|---:|
| Linhas epidemiológicas | 2.907.593 |
| Unidades epidemiológicas | 5.571 |
| Duplicidades epidemiológicas | 0 |
| Unidades mapeadas para clima | 5.570 |
| Combinações climáticas | 5.213 |
| Duplicidades climáticas | 0 |
| Linhas epidemiológicas com clima disponível | 2.907.071 |
| Linhas sem clima | 522 |
| Divergência de início da semana | 0 |
| Divergência de fim da semana | 0 |

As 522 linhas sem clima são exatamente as 522 semanas de Fernando de Noronha.

A única unidade com quantidade de semanas diferente de 522 é:

```text
5101837 — Boa Esperança do Norte
53 semanas
```

Isso confirma que a estratégia adequada para o painel mestre é preservar a base epidemiológica como referência e associar o clima por `combo_id + ano + semana`.

---

# 24. Fluxo completo da fase exploratória

De forma resumida, o trabalho realizado antes do repositório definitivo pode ser representado assim:

```text
SINAN 2016–2025
        │
        ├── auditoria de campos
        ├── definição de semana dos primeiros sintomas
        ├── município de residência
        ├── exclusão de descartados
        ├── validação de códigos
        ▼
agregação município × semana
        │
        ▼
IBGE DTB 2025
        │
        ├── normalização SINAN ↔ IBGE
        ├── consolidação do Distrito Federal
        ├── exclusão de 32 registros residuais não municipais
        ▼
série epidemiológica territorial validada
        │
        ├── calendário epidemiológico
        ├── zero-fill
        ▼
painel semanal completo
        │
        ▼
IBGE população 2016–2025
        │
        ├── Censo 2022
        ├── regra explícita para 2023
        ├── cálculo de incidência
        ▼
epidemiologia + população
        │
        ├────────────────────────────────────┐
        │                                    │
        │                                    ▼
        │                           IBGE localidades
        │                                    │
        │                                    ▼
        │                           coordenadas das sedes
        │                                    │
        │                                    ▼
        │                           Malha Municipal 2024
        │                                    │
        │                                    ▼
        │                           mapeamento espacial
        │                                    │
        │                                    ▼
        │                              ERA5-Land
        │                                    │
        │                         temperatura / orvalho /
        │                         precipitação / umidade
        │                                    │
        │                                    ▼
        │                         agregação por semana local
        │                                    │
        └───────────────────┬────────────────┘
                            ▼
              artefatos intermediários auditados
                            │
                            ▼
               prontos para o painel mestre
```

---

# 25. Decisões metodológicas que devem permanecer explícitas

As seguintes escolhas são importantes o suficiente para nunca ficarem escondidas apenas no código:

1. **Semana temporal do caso:** semana dos primeiros sintomas, não semana de notificação.
2. **Geografia do caso:** município de residência.
3. **Casos prováveis:** exclusão validada de `CLASSI_FIN = 5`.
4. **Códigos territoriais:** compatibilização explícita SINAN ↔ IBGE.
5. **Distrito Federal:** subdivisões consolidadas em Brasília.
6. **Zero-fill:** zero representa ausência de caso no extrato, não prova de ausência de transmissão.
7. **População 2023:** reutilização explícita do Censo 2022, sem interpolação.
8. **Boa Esperança do Norte:** sem criação de observações antes de sua existência na estrutura adotada.
9. **Coordenada climática:** célula associada à sede municipal como proxy.
10. **Fernando de Noronha:** mantido nos dados epidemiológicos, mas excluído quando clima ERA5-Land é obrigatório.
11. **ERA5-Land:** agregação climática feita após conversão para horário civil local.
12. **Horário de verão:** semanas de 167/169 horas são válidas quando compatíveis com a transição local.
13. **Precipitação:** não diferenciar novamente a série horária do produto time-series/ARCO.
14. **Umidade relativa:** derivada de temperatura e ponto de orvalho.
15. **Validação temporal futura:** dados de 2025 devem permanecer reservados para avaliação final do modelo, evitando usá-los para otimização.

---

# 26. Limitações conhecidas antes da modelagem

## 26.1 SINAN é uma base retrospectiva

O conjunto consolidado utilizado no projeto não simula automaticamente a situação operacional de dados disponíveis em tempo real.

Registros podem sofrer:

- atraso de notificação;
- atualização;
- encerramento posterior;
- revisão de classificação.

Portanto, previsões construídas sobre o histórico consolidado devem inicialmente ser descritas como **avaliação retrospectiva de capacidade preditiva**.

Qualquer afirmação de sistema operacional em tempo real exigiria simular ou medir a latência de disponibilidade dos dados.

## 26.2 ERA5-Land não é estação meteorológica municipal

ERA5-Land é um produto de reanálise em grade.

O projeto utiliza uma célula representativa próxima à sede, e não medições de uma estação específica nem média espacial de todo o município.

Essa aproximação deve ser considerada na interpretação dos resultados.

## 26.3 Mudanças populacionais e territoriais

A série atravessa:

- diferentes estimativas populacionais;
- Censo 2022;
- mudanças metodológicas;
- criação/instalação de unidade territorial.

Por isso, população e território não devem ser tratados como atributos estáticos sem ano de referência.

---

# 27. Próxima etapa após esta documentação

A fase exploratória encerrou a pergunta:

> **“As fontes podem ser compatibilizadas de forma tecnicamente consistente?”**

A resposta obtida pelas auditorias foi positiva.

O passo seguinte do projeto definitivo é construir o:

```text
painel_municipal_semanal_2016_2025.parquet
```

integrando:

```text
epidemiologia + população
          │
          ▼
mapeamento município → combo ERA5
          │
          ▼
clima semanal
```

A integração deverá preservar as **2.907.593 linhas epidemiológicas** na camada ampla e identificar explicitamente disponibilidade climática.

A expectativa já validada pelas chaves é:

```text
2.907.593 linhas epidemiológicas
-      522 linhas de Fernando de Noronha sem ERA5-Land
-----------------------------------------------------
2.907.071 linhas com cobertura climática
```

A base de modelagem poderá ser derivada posteriormente, sem apagar a unidade excluída da camada histórica/auditável.

---

# 28. Referências oficiais principais

## Ministério da Saúde

**OpenDataSUS — Sinan/Dengue**
https://opendatasus.saude.gov.br/dataset/arboviroses-dengue

**DATASUS — Doenças e Agravos de Notificação (SINAN)**
https://datasus.saude.gov.br/acesso-a-informacao/doencas-e-agravos-de-notificacao-de-2007-em-diante-sinan/

## IBGE

**Divisão Territorial Brasileira — DTB**
https://www.ibge.gov.br/geociencias/organizacao-do-territorio/divisao-regional/23701-divisao-territorial-brasileira.html

**Estimativas da População**
https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html

**Malhas Territoriais**
https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html

## Copernicus / ECMWF

**ERA5-Land hourly data from 1950 to present**
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land

**ERA5 Land hourly time-series data from 1950 to present**
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries

**DOI do ERA5-Land**
https://doi.org/10.24381/cds.e2161bac

---

# 29. Conclusão

A fase exploratória não consistiu apenas em baixar três conjuntos de dados e uni-los.

Foi necessário construir uma cadeia de validações para garantir que epidemiologia, população, território e clima compartilhassem uma interpretação coerente de:

- município;
- existência histórica;
- semana epidemiológica;
- população;
- coordenada;
- fuso horário;
- célula climática;
- intervalo temporal.

Ao final dessa fase:

- os registros de dengue foram filtrados e agregados de forma auditada;
- os códigos SINAN foram conciliados com a referência territorial do IBGE;
- semanas ausentes foram explicitadas sem alterar o total de casos;
- a população foi integrada com cobertura completa;
- as coordenadas municipais foram normalizadas;
- a malha territorial foi auditada;
- o mapeamento município → ERA5-Land foi validado;
- a meteorologia foi convertida de horário UTC para semanas epidemiológicas locais;
- as exceções territoriais e climáticas foram documentadas;
- o processamento nacional ERA5-Land foi concluído e aprovado;
- os artefatos finais da exploração foram preservados para migração ao projeto definitivo.

Assim, o repositório definitivo não começou com dados brutos desconhecidos, mas com um conjunto de **artefatos intermediários previamente investigados, auditados e documentados**, permitindo que a próxima etapa se concentre na integração mestre, engenharia de atributos, modelagem, validação temporal e desenvolvimento da aplicação.

---

*Documento elaborado como registro técnico retrospectivo da fase exploratória do projeto Dengue Alert.*
