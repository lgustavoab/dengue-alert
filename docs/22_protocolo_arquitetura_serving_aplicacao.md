# Protocolo de Arquitetura de Serving e Aplicação

## 1. Objetivo

Esta etapa define a arquitetura técnica que conectará os resultados produzidos
pelo pipeline de Ciência de Dados à aplicação web Dengue Alert.

A arquitetura deverá preservar uma separação clara entre:

**processamento científico**

e

**consumo pela aplicação**

O frontend não deverá executar novamente transformações epidemiológicas,
cálculos de targets, engenharia de features, treinamento ou avaliação de
modelos.

Essas responsabilidades permanecem no pipeline Python.

---

# 2. Arquitetura geral

A arquitetura seguirá o fluxo:

```text
fontes brutas
      ↓
pipeline Python
      ↓
dados processados
      ↓
dados de serving
      ↓
Next.js + React + TypeScript
      ↓
interface Dengue Alert
```

O pipeline Python continuará responsável por:

- ingestão;
- limpeza;
- validação;
- integração;
- engenharia de features;
- construção dos targets;
- modelagem;
- avaliação;
- geração de previsões;
- agregações históricas;
- construção dos artefatos de serving.

A aplicação será responsável por:

- leitura dos artefatos publicados;
- filtros;
- interação;
- visualização;
- navegação;
- apresentação dos dados históricos;
- apresentação dos indicadores de qualidade;
- apresentação das previsões.

---

# 3. Princípio de separação de responsabilidades

A aplicação não será responsável por reproduzir o pipeline científico.

Assim:

```text
Python
```

será responsável por transformar dados em informação validada.

Enquanto:

```text
Next.js
```

será responsável por transformar essa informação validada em uma interface
interativa.

O frontend não deverá:

- limpar SINAN;
- agregar ERA5-Land;
- calcular população;
- reconstruir semanas epidemiológicas;
- calcular targets;
- gerar features;
- treinar modelos;
- otimizar thresholds;
- recalcular previsões.

---

# 4. FastAPI

FastAPI não fará parte da primeira versão da aplicação.

Não será criado inicialmente um serviço Python persistente apenas para entregar
dados ao frontend.

A primeira arquitetura utilizará:

**dados preparados offline**

consumidos pela aplicação Next.js.

Uma API Python poderá ser considerada futuramente caso surjam necessidades como:

- atualização contínua;
- previsões sob demanda;
- autenticação complexa;
- múltiplos consumidores externos;
- processamento em tempo real;
- integração com outros sistemas.

Essas necessidades não fazem parte do escopo inicial.

---

# 5. Estrutura do monorepo

A estrutura geral permanecerá:

```text
tcc-dengue/
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── serving/
├── src/
│   └── dengue_alert/
├── scripts/
├── notebooks/
├── models/
├── reports/
├── docs/
├── tests/
└── web/
```

A pasta:

```text
data/serving/
```

será a fronteira entre o pipeline científico e a aplicação.

---

# 6. Camadas de dados

As quatro camadas possuem finalidades diferentes.

## raw

Contém arquivos originais obtidos das fontes externas.

Esses arquivos devem ser preservados sem alterações destrutivas.

## interim

Contém resultados intermediários do pipeline.

São dados úteis durante etapas específicas de transformação ou auditoria.

## processed

Contém conjuntos analíticos consolidados utilizados pela Ciência de Dados.

Exemplo:

```text
data/processed/painel_municipal_semanal_2016_2025.parquet
```

## serving

Contém artefatos preparados especificamente para consumo pela aplicação.

A camada de serving não será uma cópia integral de `processed`.

---

# 7. Princípio da camada de serving

A camada de serving deverá conter somente dados necessários ao produto.

Portanto:

**processed**

representa dados voltados ao pipeline científico.

**serving**

representa dados preparados para consumo eficiente pela aplicação.

O navegador não deverá receber diretamente o painel municipal semanal completo
com aproximadamente:

**2,9 milhões de linhas**

quando a visualização atual necessita apenas de uma pequena fração dessas
informações.

---

# 8. Organização da camada de serving

A estrutura inicial prevista será:

```text
data/serving/
├── metadata/
├── quality/
├── historical/
└── prediction/
```

Cada área possuirá finalidade própria.

---

# 9. Metadata

A área:

```text
data/serving/metadata/
```

armazenará informações compartilhadas por diferentes partes da aplicação.

Exemplos:

- municípios;
- códigos IBGE;
- UFs;
- regiões;
- períodos disponíveis;
- semanas disponíveis;
- versões dos dados;
- versões do modelo;
- metadados metodológicos.

Esses arquivos deverão ser pequenos e apropriados para consulta frequente.

---

# 10. Quality

A área:

```text
data/serving/quality/
```

armazenará indicadores auditados sobre:

- fontes brutas;
- volume dos dados;
- filtros aplicados;
- registros removidos;
- registros preservados;
- inconsistências encontradas;
- cobertura temporal;
- cobertura territorial;
- cobertura populacional;
- cobertura climática;
- normalizações realizadas.

Essa camada não conterá necessariamente os registros brutos.

Seu objetivo será apresentar de forma transparente como os dados originais
foram transformados até chegar às bases analíticas utilizadas pelo projeto.

---

# 11. Historical

A área:

```text
data/serving/historical/
```

armazenará agregados necessários ao dashboard histórico.

Ela será alimentada pelos resultados já auditados durante a análise
exploratória histórica.

---

# 12. Prediction

A área:

```text
data/serving/prediction/
```

armazenará os dados necessários à área de previsão.

Ela deverá permitir consultas eficientes por:

- município;
- semana de referência;
- horizonte;
- semana-alvo.

---

# 13. Estratégia de formatos

Não será obrigatório utilizar um único formato para todos os artefatos.

A escolha dependerá:

- do volume;
- do padrão de acesso;
- da necessidade de leitura server-side;
- da necessidade de leitura no cliente.

Dados pequenos e agregados poderão ser publicados como:

**JSON**

Dados tabulares maiores poderão permanecer em formato apropriado para consulta
na camada de servidor da aplicação.

O princípio obrigatório será:

**o cliente não deverá baixar grandes bases desnecessariamente**

---

# 14. Next.js como camada de aplicação

A aplicação será construída inicialmente com:

**Next.js**

**React**

**TypeScript**

O Next.js poderá realizar leitura de artefatos na camada de servidor quando isso
for mais apropriado.

Assim, será possível evitar que grandes conjuntos sejam enviados integralmente
ao browser.

Isso não equivale à introdução de uma API FastAPI.

---

# 15. Área histórica

A aplicação possuirá uma área histórica capaz de explorar os dados observados.

Essa área deverá responder perguntas como:

**Quanto ocorreu?**

**Quando ocorreu?**

**Onde ocorreu?**

**Como o risco se expandiu?**

**Quanto tempo o risco persistiu?**

**Como clima e dengue se associaram historicamente?**

---

# 16. Panorama histórico

A área histórica deverá disponibilizar dados para:

- casos anuais;
- incidência anual;
- anos disponíveis;
- comparação entre anos;
- destaque de anos epidêmicos.

A visualização deverá ser interativa e não simplesmente reproduzir a Figura 01
como imagem.

---

# 17. Sazonalidade

A aplicação deverá disponibilizar dados para análise por:

- semana epidemiológica;
- Brasil;
- região;
- incidência;
- medidas de distribuição quando necessárias.

As visualizações deverão permitir explorar diferenças sazonais entre as regiões.

---

# 18. Distribuição espacial histórica

O dashboard deverá disponibilizar informações territoriais como:

- código IBGE;
- município;
- UF;
- região;
- incidência histórica;
- casos;
- indicadores utilizados no mapa.

A visualização cartográfica deverá permitir interação por município.

---

# 19. Dinâmica epidemiológica

A aplicação poderá mostrar:

- municípios simultaneamente em risco;
- proporção de municípios em risco;
- evolução semanal;
- episódios de risco;
- duração dos episódios;
- recorrência;
- diferenças regionais.

---

# 20. Clima × dengue histórico

A aplicação poderá explorar:

- variável climática;
- lag;
- correlação;
- Brasil;
- região;
- medidas de distribuição.

A visualização deverá preservar a interpretação:

**associação histórica**

e não:

**causalidade**

---

# 21. Dados municipais históricos

A aplicação deverá permitir detalhamento por município sem carregar o painel
nacional completo no navegador.

Uma visão municipal poderá apresentar:

- identificação do município;
- UF;
- região;
- casos históricos;
- incidência;
- semanas epidemiológicas;
- episódios de risco;
- quantidade de semanas em risco;
- duração do maior episódio;
- recorrência histórica;
- informações geográficas básicas.

Os dados deverão ser consultados sob demanda.

---

# 22. Dados e Qualidade

A aplicação possuirá uma área específica denominada:

**Dados e Qualidade**

Seu objetivo será dar transparência ao processo de construção das bases
utilizadas pelo Dengue Alert.

Essa área não terá como objetivo disponibilizar milhões de registros brutos
linha a linha.

Ela apresentará indicadores consolidados e auditados sobre:

- volume original dos dados;
- regras de limpeza;
- registros removidos;
- registros preservados;
- inconsistências encontradas;
- normalização territorial;
- preenchimento temporal;
- cobertura populacional;
- cobertura geográfica;
- disponibilidade climática.

---

# 23. Fontes de dados

A aplicação deverá apresentar de forma clara as principais fontes utilizadas no
projeto.

## SINAN / OpenDataSUS

Fonte epidemiológica utilizada para obtenção dos registros de dengue.

## IBGE

Utilizado para:

- divisão territorial;
- códigos municipais;
- nomes de municípios;
- unidades federativas;
- regiões;
- população municipal;
- coordenadas;
- malha territorial.

## ERA5-Land

Fonte de reanálise meteorológica utilizada para obtenção e derivação de
variáveis climáticas.

A aplicação deverá diferenciar claramente:

**dados epidemiológicos observados**

de

**dados meteorológicos de reanálise**

---

# 24. Funil de preparação do SINAN

A área Dados e Qualidade deverá apresentar o processo de preparação do SINAN de
maneira visual.

O conjunto bruto auditado possui:

**19.336.281 registros**

As principais regras aplicadas foram:

1. remoção das observações segundo a regra de duplicidade;
2. remoção das observações com classificação final não elegível;
3. validação do município de residência;
4. validação da semana epidemiológica;
5. restrição ao período epidemiológico definido;
6. agregação município × semana;
7. normalização territorial.

---

# 25. Filtragem epidemiológica

Durante a preparação foram identificados:

**3.002.212 registros removidos por `CLASSI_FIN = 5`**

Também foram identificados:

**1.149 registros com município inválido**

**79 registros com semana epidemiológica inválida**

**37.896 registros fora do período definido**

Após as regras epidemiológicas foram preservados:

**16.294.945 registros/casos elegíveis antes da normalização territorial**

Os valores apresentados no frontend deverão ser provenientes de artefatos
auditados e não digitados manualmente nos componentes React.

---

# 26. Normalização territorial

O SINAN apresentou inicialmente:

**5.621 códigos municipais de seis dígitos**

A referência territorial adotada possui:

**5.571 unidades territoriais oficiais**

Na comparação inicial foram encontrados:

**60 códigos sem correspondência direta**

correspondendo a:

**22.878 casos**

---

# 27. Distrito Federal

Dos 60 códigos sem correspondência direta:

**48 pertenciam a subdivisões do Distrito Federal**

representando:

**22.846 casos**

Esses registros foram consolidados para:

**Brasília — código IBGE 5300108**

Essa transformação preservou os casos do Distrito Federal.

---

# 28. Códigos não municipais

Após o tratamento do Distrito Federal restaram:

**12 códigos não municipais**

representando:

**32 casos**

Esses registros foram excluídos.

Nenhum deles foi associado arbitrariamente a outro município.

Após a normalização territorial permaneceram:

**16.294.913 casos**

---

# 29. Cobertura territorial epidemiológica inicial

Após a normalização territorial existiam registros observados em:

**5.561 unidades**

A referência territorial continha:

**5.571 unidades**

Portanto:

**10 unidades territoriais não apresentavam registro epidemiológico observado**

Essas unidades não foram removidas do painel histórico.

---

# 30. Zero-fill

A ausência de uma linha município × semana na base original não deverá ser
interpretada como se o arquivo bruto explicitamente informasse zero casos.

O pipeline construiu uma grade epidemiológica temporal completa.

Antes do preenchimento existiam:

**721.309 linhas município-semana observadas**

Após a construção da grade:

**2.907.593 linhas**

Foram acrescentadas:

**2.186.284 combinações preenchidas com zero**

O total de casos permaneceu:

**16.294.913**

---

# 31. Distinção entre zero e ausência de linha original

A aplicação deverá diferenciar conceitualmente:

**registro SINAN presente**

de

**zero preenchido durante a preparação**

O zero-fill representa uma transformação controlada utilizada para construir
uma série temporal municipal completa.

---

# 32. Semanas epidemiológicas

O painel utiliza semanas epidemiológicas no padrão:

**domingo a sábado**

A semana epidemiológica 1 segue a convenção utilizada no projeto e inclui o dia
4 de janeiro.

No período analisado:

**2020 e 2025 possuem 53 semanas epidemiológicas**

Os demais anos possuem:

**52 semanas**

A aplicação deverá utilizar a mesma definição temporal do pipeline.

---

# 33. Mudanças territoriais

A estrutura territorial não é completamente estática durante todo o período.

Um caso relevante é:

**Boa Esperança do Norte/MT — código IBGE 5101837**

instalada oficialmente em:

**01/01/2025**

Essa unidade não recebe artificialmente semanas anteriores à sua existência
territorial.

A aplicação deverá preservar essa diferença de cobertura histórica.

---

# 34. População

A população municipal é utilizada no cálculo de indicadores como:

**incidência por 100 mil habitantes**

Foram utilizadas fontes oficiais do IBGE para os anos disponíveis na série
adotada.

A cobertura utilizada inclui:

- 2016;
- 2017;
- 2018;
- 2019;
- 2020;
- 2021;
- 2022;
- 2024;
- 2025.

---

# 35. População de 2023

Não havia uma estimativa municipal anual equivalente para:

**2023**

dentro da mesma estrutura oficial adotada pelo projeto.

Por isso, foi reutilizada explicitamente:

**a população do Censo 2022**

como referência para 2023.

Essa decisão deverá aparecer de forma transparente na aplicação.

---

# 36. Descontinuidade populacional

Existe uma descontinuidade metodológica entre:

**estimativas anteriores**

e

**Censo 2022**

Comparações ao redor dessa transição deverão ser interpretadas com cautela.

Essa descontinuidade decorre da referência populacional oficial e não de erro do
pipeline.

---

# 37. Integração população × epidemiologia

A integração populacional preservou:

**2.907.593 linhas**

Linhas sem população após a integração:

**0**

A compatibilidade populacional foi validada para todos os anos utilizados.

---

# 38. Cobertura geográfica

A estrutura histórica possui:

**5.571 unidades territoriais**

A malha municipal do IBGE utilizada possui:

**5.573 feições**

Duas feições adicionais correspondem a:

- Área Operacional Lagoa Mirim;
- Área Operacional Lagoa dos Patos.

Essas áreas não possuem correspondência no painel epidemiológico e não são
tratadas como municípios.

Todas as 5.571 unidades do painel epidemiológico possuem geometria disponível.

---

# 39. Geometria municipal

A malha utilizada possui CRS original:

**SIRGAS 2000 — EPSG:4674**

Foi identificada uma geometria inválida:

**Selvíria/MS — código IBGE 5007802**

A geometria foi reparada em memória durante o processamento cartográfico.

O arquivo bruto original não foi alterado.

---

# 40. Reprojeção cartográfica

Para a representação nacional utilizada nas análises, a malha foi reprojetada
para:

**SIRGAS 2000 / Brazil Polyconic — EPSG:5880**

Essa transformação é utilizada para visualização e não altera os códigos
territoriais.

---

# 41. Cobertura climática

A modelagem climática considera:

**5.570 unidades territoriais**

Fernando de Noronha permanece no histórico epidemiológico, porém ficou fora da
modelagem climática adotada.

No painel consolidado existem:

**2.907.071 município-semanas com clima disponível**

e:

**522 município-semanas sem clima disponível**

---

# 42. ERA5-Land

Os dados meteorológicos utilizados são provenientes do:

**ERA5-Land**

A aplicação deverá explicar que essa fonte representa:

**reanálise meteorológica**

e não uma estação meteorológica física instalada em cada município.

As variáveis consolidadas incluem:

- temperatura média;
- temperatura mínima;
- temperatura máxima;
- ponto de orvalho médio;
- umidade relativa média;
- precipitação total.

---

# 43. Associação município × grade climática

O projeto estabeleceu associação entre unidades territoriais e células válidas
da grade ERA5-Land.

O resultado final possui:

**5.486 unidades associadas à célula válida mais próxima**

**82 unidades tratadas por interseção municipal**

**2 unidades insulares externas**

**1 unidade excluída da modelagem climática**

A unidade excluída foi:

**Fernando de Noronha**

---

# 44. Grade climática final

Foram utilizados:

**5.203 pontos de grade ERA5-Land distintos**

Considerando simultaneamente:

**grade + timezone**

foram formadas:

**5.213 combinações**

Essa estrutura foi utilizada para respeitar o tempo civil local durante a
agregação temporal.

---

# 45. Tempo civil local

Os dados horários climáticos foram tratados considerando:

**tempo civil local**

antes da agregação para semanas epidemiológicas.

Isso evita que municípios em fusos horários distintos tenham variáveis
climáticas agregadas de maneira temporalmente incompatível com sua semana
epidemiológica.

---

# 46. Precipitação

O processamento definitivo da precipitação segue a convenção temporal validada
durante a auditoria climática.

A aplicação não deverá sugerir que a precipitação semanal foi produzida por uma
diferença arbitrária entre valores horários acumulados.

O artefato definitivo já incorpora o tratamento validado pelo pipeline.

---

# 47. Análise dos dados brutos

A aplicação poderá apresentar:

**análises sobre os dados brutos**

Isso inclui:

- quantidade recebida;
- estrutura das fontes;
- filtros;
- inconsistências;
- perdas;
- cobertura;
- transformações;
- resultado final.

Entretanto, isso é diferente de disponibilizar:

**os registros brutos completos**

linha a linha no navegador.

---

# 48. O que não será exposto no navegador

A aplicação não deverá enviar ao cliente:

- aproximadamente 19 milhões de registros brutos do SINAN;
- o painel completo com aproximadamente 2,9 milhões de município-semanas;
- arquivos brutos completos do ERA5-Land;
- arquivos intermediários do pipeline;
- conjuntos utilizados exclusivamente para treinamento do modelo.

O navegador receberá somente os dados necessários para a interação atual.

---

# 49. Funil visual de dados

A página Dados e Qualidade poderá apresentar uma visualização semelhante a:

```text
19.336.281
registros brutos SINAN
        ↓
filtros epidemiológicos
        ↓
16.294.945
registros elegíveis
        ↓
normalização territorial
        ↓
16.294.913
casos preservados
        ↓
grade município × semana
        ↓
2.907.593
município-semanas
```

A interface poderá permitir detalhamento das etapas.

---

# 50. Indicadores candidatos de qualidade

A aplicação poderá apresentar cards como:

```text
19.336.281
registros epidemiológicos brutos
```

```text
16.294.913
casos preservados
```

```text
5.571
unidades territoriais históricas
```

```text
2.907.593
município-semanas
```

```text
2.186.284
zeros preenchidos
```

```text
5.570
unidades com cobertura climática
```

```text
2.907.071
município-semanas com clima
```

```text
522
município-semanas sem clima
```

Todos esses valores deverão vir de contratos de serving produzidos pelo Python.

---

# 51. Serving de qualidade

A estrutura candidata será:

```text
data/serving/quality/
├── overview.json
├── sinan_pipeline.json
├── territorial_coverage.json
├── population_coverage.json
└── climate_coverage.json
```

Os nomes poderão ser refinados durante a implementação.

O princípio obrigatório será:

**os valores exibidos no frontend não serão duplicados manualmente nos
componentes React**

---

# 52. Serving histórico

A estrutura candidata será:

```text
data/serving/historical/
├── panorama/
├── seasonality/
├── spatial/
├── risk_dynamics/
├── municipality/
└── climate/
```

Os diretórios deverão conter somente os dados necessários para cada
visualização.

---

# 53. Serving preditivo

A estrutura candidata poderá ser:

```text
data/serving/prediction/
├── metadata/
├── 2025/
└── municipality/
```

A organização definitiva será escolhida de acordo com o padrão de consulta.

Ela deverá permitir acesso por:

- município;
- semana;
- horizonte.

---

# 54. Área de previsão

A área preditiva será conceitualmente separada da área histórica.

Ela deverá permitir selecionar, quando aplicável:

- município;
- semana de referência;
- horizonte.

Horizontes disponíveis:

**+1 semana**

**+2 semanas**

**+3 semanas**

**+4 semanas**

---

# 55. O que o modelo prevê

O modelo final não prevê diretamente:

**quantidade futura de casos de dengue**

O modelo prevê:

**probabilidade de estado futuro de risco epidemiológico elevado**

Portanto a aplicação não deverá apresentar valores como:

```text
casos previstos
```

ou:

```text
número esperado de casos
```

a menos que um modelo específico de regressão seja criado futuramente.

Esse modelo não faz parte do escopo atual.

---

# 56. Definição de risco elevado

O estado epidemiológico utilizado pelo modelo segue a definição congelada no
pipeline.

O risco elevado utiliza:

**incidência acumulada em quatro semanas**

comparada ao:

**percentil 90 sazonal histórico do município**

O cálculo utiliza uma janela sazonal histórica segundo as regras metodológicas
já congeladas.

O frontend não recalculará esse target.

---

# 57. Horizonte de previsão

O sistema trabalhará com quatro horizontes:

| Horizonte | Interpretação |
| --- | --- |
| H1 | risco em +1 semana |
| H2 | risco em +2 semanas |
| H3 | risco em +3 semanas |
| H4 | risco em +4 semanas |

Cada horizonte possui sua própria probabilidade e threshold operacional.

---

# 58. Thresholds operacionais

Os thresholds finais congelados são:

| Horizonte | Threshold |
| --- | ---: |
| H1 | 0,187687 |
| H2 | 0,190783 |
| H3 | 0,167991 |
| H4 | 0,157138 |

Nenhum threshold será recalculado ou otimizado pelo frontend.

---

# 59. Estado de alerta

A decisão operacional atualmente congelada é:

**alerta**

ou:

**sem alerta**

segundo o threshold específico do horizonte.

A aplicação poderá mostrar simultaneamente:

- probabilidade prevista;
- threshold;
- estado de alerta.

---

# 60. Escalas visuais adicionais

Uma classificação visual como:

- baixo;
- moderado;
- alto;
- crítico;

não será inventada automaticamente durante o frontend.

Caso uma escala adicional seja desejada, deverá existir antes:

- uma regra formal;
- justificativa;
- documentação;
- validação.

Até lá, a informação científica principal permanecerá:

**probabilidade prevista + threshold + alerta**

---

# 61. Previsão retrospectiva

A avaliação final disponível corresponde ao ano:

**2025**

A aplicação deverá deixar explícito quando os resultados apresentados forem:

**previsões retrospectivas**

Ela não deverá apresentar resultados de 2025 como se fossem alertas atuais de
2026.

---

# 62. Semana de referência e semana-alvo

A interface deverá diferenciar:

**semana de referência**

da:

**semana-alvo**

Por exemplo:

```text
Semana de referência: SE 20/2025
Horizonte: H3
Semana-alvo: SE 23/2025
```

Essa distinção deverá ser visível para evitar interpretação equivocada.

---

# 63. Previsto × observado

Quando os dados observados estiverem disponíveis retrospectivamente, a
aplicação poderá mostrar:

- probabilidade prevista;
- estado de alerta previsto;
- estado futuro observado;
- acerto ou erro da classificação.

O estado observado nunca deverá ser apresentado como se tivesse sido usado na
geração da previsão.

---

# 64. Mapa preditivo

A área de previsão deverá possuir representação cartográfica municipal.

O mapa poderá mostrar:

- município;
- UF;
- probabilidade;
- horizonte;
- semana de referência;
- semana-alvo;
- alerta.

A seleção de um município deverá permitir abrir detalhes.

---

# 65. Detalhamento municipal da previsão

Ao selecionar um município, poderão ser exibidos:

## Semana de referência

- município;
- UF;
- semana;
- incidência disponível;
- estado epidemiológico atual.

## H1–H4

- probabilidade;
- threshold;
- alerta;
- semana-alvo.

## Avaliação retrospectiva

Quando disponível:

- estado observado;
- comparação previsto × observado.

---

# 66. Explicabilidade

A aplicação poderá apresentar explicabilidade somente quando existir um artefato
produzido e validado pelo pipeline.

O frontend não deverá produzir explicações artificiais com base apenas no valor
da probabilidade.

A ausência de um artefato validado deverá ser tratada como:

**explicabilidade não disponível**

e não preenchida com interpretação inventada.

---

# 67. Modelo final

O modelo principal permanece:

**HistGradientBoostingClassifier**

utilizando o conjunto epidemiológico de features já congelado.

A inclusão do clima não apresentou ganho preditivo incremental relevante na
comparação final.

A aplicação não deverá transformar essa conclusão em:

**o clima não influencia dengue**

A interpretação correta é:

**na representação e protocolo avaliados, as variáveis climáticas não
acrescentaram ganho preditivo relevante além do histórico epidemiológico**

---

# 68. Histórico × previsão

A interface deverá preservar separação clara entre:

**Histórico**

e

**Previsão**

Histórico descreve:

**o que foi observado**

Previsão representa:

**estimativa probabilística de um estado futuro**

Essa separação deverá existir:

- nos textos;
- nos componentes;
- nas rotas;
- nos dados de serving;
- na navegação.

---

# 69. Estrutura candidata de navegação

A aplicação poderá utilizar uma estrutura semelhante a:

```text
/
├── Visão geral
├── Histórico
├── Mapa
├── Previsão
├── Município
├── Dados e Qualidade
└── Metodologia
```

A estrutura poderá ser refinada durante o design sem alterar a separação
conceitual.

---

# 70. Visão geral

A página inicial poderá apresentar:

- objetivo do Dengue Alert;
- cobertura temporal;
- cobertura territorial;
- fontes;
- indicadores históricos principais;
- acesso ao histórico;
- acesso ao mapa;
- acesso à previsão;
- acesso à qualidade dos dados.

A página não deverá apresentar previsões retrospectivas como alertas atuais.

---

# 71. Histórico

A seção histórica poderá conter:

- evolução anual;
- sazonalidade;
- mapa histórico;
- dinâmica do risco;
- duração dos episódios;
- associação clima × dengue.

As sete figuras produzidas anteriormente serão referências analíticas.

Elas não serão simplesmente inseridas como imagens dentro da aplicação.

---

# 72. Município

A visão municipal deverá integrar, quando possível:

- identificação;
- histórico epidemiológico;
- incidência;
- episódios;
- recorrência;
- contexto histórico;
- previsões disponíveis.

A interface deverá deixar visualmente clara a diferença entre:

**observado**

e

**previsto**

---

# 73. Dados e Qualidade na navegação

A página Dados e Qualidade poderá ser estruturada em:

## Fontes

- SINAN/OpenDataSUS;
- IBGE;
- ERA5-Land.

## Funil epidemiológico

- registros brutos;
- filtros;
- registros preservados;
- normalização territorial.

## Cobertura

- temporal;
- territorial;
- populacional;
- climática.

## Transformações

- normalização geográfica;
- zero-fill;
- população;
- clima.

## Auditoria

- consistência;
- completude;
- exceções documentadas;
- cobertura final.

---

# 74. Metodologia

A aplicação deverá possuir uma área capaz de explicar de maneira acessível:

- fontes dos dados;
- período;
- preparação;
- zero-fill;
- população;
- clima;
- definição de risco elevado;
- horizonte de previsão;
- significado das probabilidades;
- thresholds;
- avaliação retrospectiva;
- limitações;
- diferença entre correlação e causalidade.

---

# 75. Responsividade

A aplicação será responsiva desde a primeira implementação.

Não será adotada a estratégia de construir uma interface fixa para desktop e
somente posteriormente tentar adaptá-la para telas menores.

Os componentes deverão considerar desde sua criação:

**desktop**

**tablet**

**mobile**

---

# 76. Dashboard responsivo

Em desktop poderão coexistir:

- gráficos;
- filtros;
- cards;
- mapa;
- painel lateral;
- tabelas resumidas.

Em telas menores poderão ser utilizados:

- empilhamento vertical;
- filtros recolhíveis;
- seletores;
- tabs;
- painéis expansíveis;
- redução controlada da quantidade de séries simultâneas.

---

# 77. Mapa responsivo

Em desktop uma composição possível será:

```text
mapa + painel lateral de detalhes
```

Em dispositivos móveis:

```text
mapa
↓
controles compactos
↓
painel de detalhes
```

A interação deverá funcionar adequadamente por toque.

---

# 78. Dados e Qualidade responsivo

Em desktop poderão coexistir:

- funil;
- cards;
- gráficos;
- explicações.

Em telas menores, esses componentes deverão ser reorganizados verticalmente.

Tabelas extensas deverão ser evitadas quando cards, gráficos ou blocos
expansíveis comunicarem melhor a informação.

---

# 79. Performance

O frontend deverá seguir os princípios:

- enviar somente dados necessários;
- utilizar agregações pré-calculadas;
- evitar processamento científico no browser;
- particionar dados quando necessário;
- realizar leitura server-side quando apropriada;
- evitar grandes payloads;
- evitar transferência repetida de dados idênticos.

---

# 80. Reprodutibilidade

Todos os artefatos de serving deverão possuir scripts reproduzíveis.

O fluxo será:

```text
dados processados
      ↓
scripts Python
      ↓
data/serving
      ↓
aplicação
```

Nenhum indicador importante deverá existir apenas como valor digitado
manualmente no frontend.

---

# 81. Contratos de dados

Cada artefato de serving deverá possuir contrato conhecido.

O contrato deverá considerar:

- schema;
- tipos;
- chave;
- granularidade;
- unidade;
- cobertura;
- valores ausentes;
- domínios permitidos.

Mudanças de schema deverão ser explícitas.

---

# 82. Auditoria dos contratos

Antes da implementação visual definitiva, os artefatos de serving deverão ser
validados quanto a:

- quantidade de linhas;
- colunas;
- tipos;
- chaves;
- duplicidades;
- valores ausentes;
- intervalos permitidos;
- cobertura temporal;
- cobertura territorial;
- consistência entre arquivos.

O frontend não deverá ser usado como primeira linha de detecção de erros nos
dados.

---

# 83. Testes de serving

Os contratos mais importantes deverão possuir testes automatizados quando
apropriado.

Esses testes poderão validar:

- schemas;
- unicidade;
- cobertura;
- thresholds;
- horizontes;
- códigos territoriais;
- intervalos de probabilidade;
- integridade referencial.

---

# 84. Arquivos de serving no Git

A decisão sobre versionamento de cada artefato dependerá de:

- tamanho;
- estabilidade;
- natureza do dado;
- possibilidade de reprodução;
- necessidade para deploy.

Arquivos grandes ou derivados não deverão ser automaticamente adicionados ao Git
apenas por pertencerem à camada de serving.

A política será definida antes da geração definitiva dos artefatos.

---

# 85. Dados brutos no Git

Os dados brutos externos permanecerão fora do versionamento quando já estiverem
cobertos pelas regras atuais do projeto.

Isso inclui grandes bases epidemiológicas, climáticas e geográficas.

Os scripts e contratos necessários para reproduzir as transformações deverão ser
versionados.

---

# 86. Aplicação e dados científicos

O código do frontend não deverá conter cópias manuais de tabelas científicas que
já existam no pipeline.

Exemplo inadequado:

```typescript
const totalCasos = 16294913;
```

quando esse valor puder ser produzido pelo serving.

O correto será consumir um contrato como:

```text
quality/overview.json
```

com o valor produzido pelo pipeline.

---

# 87. Ordem de implementação da Fase 13

A Fase 13 será executada na seguinte ordem.

## 13A — Arquitetura e contratos

Congelamento deste protocolo.

## 13B — Serving histórico e de qualidade

Construção dos artefatos utilizados por:

- Dados e Qualidade;
- dashboard histórico.

## 13C — Serving preditivo

Construção dos artefatos utilizados pela área de previsão.

## 13D — Auditoria dos contratos de serving

Validação independente dos artefatos produzidos.

## 13E — Estrutura inicial do Next.js

Inicialização da aplicação dentro de:

```text
web/
```

## 13F — Dashboard histórico

Construção das visualizações históricas.

## 13G — Dados e Qualidade

Construção do funil, indicadores e componentes de transparência metodológica.

## 13H — Área preditiva

Construção de:

- mapa;
- seleção de município;
- semana;
- H1–H4;
- probabilidades;
- alertas.

## 13I — Integração

Integração entre:

- histórico;
- município;
- qualidade;
- previsão.

## 13J — Responsividade e UX

Validação dos layouts em:

- desktop;
- tablet;
- mobile.

## 13K — Validação final

Testes funcionais e revisão da aplicação.

---

# 88. O que não será feito nesta fase inicial

Não fazem parte do escopo inicial:

- API FastAPI persistente;
- previsão de quantidade futura de casos;
- atualização meteorológica em tempo real;
- previsão operacional em tempo real;
- retreinamento automático;
- recalibração automática;
- alteração de thresholds pelo usuário;
- processamento de milhões de linhas no navegador;
- inferência causal clima × dengue;
- alertas operacionais reais para órgãos públicos;
- envio dos registros brutos completos do SINAN ao navegador;
- exposição linha a linha dos aproximadamente 19 milhões de registros brutos;
- carregamento integral do painel municipal semanal no cliente.

---

# 89. Dados brutos × análise dos dados brutos

A aplicação poderá apresentar:

**análises e indicadores derivados dos dados brutos**

mas isso será feito por meio de:

**artefatos agregados de serving**

Assim:

**analisar os dados brutos**

é diferente de:

**entregar os dados brutos completos ao navegador**

A aplicação deverá mostrar de maneira transparente:

- o que foi recebido;
- quais problemas foram encontrados;
- quais regras foram aplicadas;
- o que foi removido;
- o que foi preservado;
- qual cobertura final foi obtida.

---

# 90. Valor acadêmico da área Dados e Qualidade

A seção Dados e Qualidade demonstra que o projeto não consiste apenas na
aplicação de um algoritmo de machine learning sobre uma base previamente pronta.

O trabalho realizado inclui:

- obtenção de dados;
- auditoria;
- limpeza;
- transformação;
- normalização territorial;
- construção de séries temporais;
- integração populacional;
- integração climática;
- engenharia de features;
- construção de targets;
- modelagem;
- avaliação;
- análise histórica;
- visualização;
- serving.

Essa trajetória deverá ser comunicada de forma clara no produto.

---

# 91. Relação entre análise histórica e previsão

A aplicação deverá evitar misturar duas perguntas diferentes.

A análise histórica responde:

**o que aconteceu e quais padrões foram observados?**

A previsão responde:

**qual é a probabilidade de o município entrar ou permanecer em estado de risco
elevado nas próximas semanas?**

Ambas fazem parte do mesmo produto, mas possuem finalidades distintas.

---

# 92. Estado final do modelo

O modelo final já foi congelado e avaliado.

A avaliação final de 2025 já foi aberta.

Nenhuma etapa posterior relacionada a:

- análise histórica;
- clima;
- visualização;
- serving;
- dashboard;
- interface;

poderá ser utilizada para retunar o modelo com base nos resultados finais de
2025.

---

# 93. Resultados finais por horizonte

Os resultados finais permanecem registrados nos artefatos científicos do
projeto.

A aplicação poderá utilizar esses resultados em uma área de metodologia ou
avaliação do modelo.

Eles deverão ser apresentados como:

**avaliação retrospectiva**

e não como desempenho futuro garantido.

---

# 94. Produto final esperado

Ao final da implementação, o Dengue Alert deverá possuir três grandes núcleos.

## Histórico

Permitir exploração dos dados epidemiológicos observados.

## Dados e Qualidade

Explicar de onde vieram os dados e como foram transformados.

## Previsão

Apresentar probabilidades de risco futuro em:

- H1;
- H2;
- H3;
- H4.

---

# 95. Informação mínima de uma previsão

Uma previsão exibida ao usuário deverá informar claramente:

- município;
- semana de referência;
- horizonte;
- semana-alvo;
- probabilidade;
- threshold;
- alerta.

Quando retrospectivo e disponível:

- estado observado.

---

# 96. Linguagem da aplicação

A aplicação deverá evitar afirmações como:

**o município terá uma epidemia**

**o município terá X casos**

**a chuva causará aumento de dengue**

A linguagem deverá refletir a natureza probabilística e observacional do
projeto.

Exemplos adequados:

**probabilidade estimada de risco elevado**

**alerta segundo o threshold do horizonte**

**associação histórica observada**

**previsão retrospectiva**

---

# 97. Transparência metodológica

O usuário deverá conseguir descobrir, sem consultar o código-fonte:

- quais fontes foram utilizadas;
- qual período está coberto;
- como risco elevado é definido;
- o que significa H1–H4;
- o que significa a probabilidade;
- como o alerta é determinado;
- quais limitações existem;
- quando uma previsão é retrospectiva.

---

# 98. Regra de congelamento

Este protocolo será congelado antes da implementação da camada de serving.

Mudanças futuras poderão ocorrer caso exista necessidade técnica real.

Entretanto, elas não deverão alterar silenciosamente os princípios centrais:

- separação entre pipeline científico e frontend;
- separação entre histórico e previsão;
- área própria de Dados e Qualidade;
- ausência inicial de FastAPI;
- uso de camada de serving;
- não envio das bases massivas ao navegador;
- dados científicos produzidos pelo Python;
- previsão de risco e não de número de casos;
- thresholds já congelados;
- responsividade desde o início;
- preservação da reprodutibilidade;
- transparência metodológica.

Qualquer mudança conceitual relevante deverá ser documentada antes de sua
implementação.

---

# 99. Status

Fase:

**13A — Arquitetura e contratos**

Status do protocolo:

**CONGELADO ANTES DA IMPLEMENTAÇÃO DA CAMADA DE SERVING**

Próxima etapa após aprovação e versionamento:

**13B — Serving histórico e de qualidade**