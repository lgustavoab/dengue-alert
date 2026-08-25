# Contrato de Serving Histórico e de Qualidade

## 1. Objetivo

Este documento define os contratos de dados da etapa:

**13B — Serving histórico e de qualidade**

do projeto Dengue Alert.

O objetivo é estabelecer, antes da implementação, quais artefatos serão
produzidos em:

```text
data/serving/
```

quais fontes científicas alimentarão cada artefato, quais transformações serão
permitidas e quais validações deverão ser executadas.

Este protocolo complementa:

```text
docs/22_protocolo_arquitetura_serving_aplicacao.md
```

e não altera os princípios de arquitetura já congelados.

---

# 2. Escopo desta etapa

A etapa 13B abrangerá três grupos de dados:

```text
metadata
quality
historical
```

A camada:

```text
prediction
```

não faz parte deste contrato.

O serving preditivo será definido posteriormente na etapa:

**13C — Serving preditivo**

---

# 3. Princípio central

A camada de serving não será uma nova camada de análise científica.

Ela deverá transformar artefatos já auditados em contratos apropriados para
consumo pela aplicação.

O fluxo será:

```text
artefato científico auditado
        ↓
gerador de serving
        ↓
validação do contrato
        ↓
data/serving
        ↓
Next.js
```

Sempre que uma estatística já existir em um artefato auditado, ela deverá ser
reutilizada.

O serving não deverá recalcular desnecessariamente resultados científicos já
congelados.

---

# 4. Transformações permitidas

Os geradores de serving poderão realizar operações como:

- selecionar colunas;
- renomear campos quando necessário ao contrato;
- ordenar registros;
- converter tipos;
- serializar datas;
- organizar estruturas JSON;
- remover campos internos desnecessários;
- combinar artefatos auditados por chave conhecida;
- produzir distribuições destinadas à visualização;
- calcular contagens puramente estruturais;
- particionar arquivos para melhorar desempenho.

Essas transformações não deverão alterar o significado científico dos dados.

---

# 5. Transformações não permitidas

A etapa não deverá:

- redefinir incidência;
- recalcular targets;
- recalcular risco elevado;
- recalcular correlações climáticas;
- modificar semanas epidemiológicas;
- recalcular população;
- retreinar modelos;
- modificar thresholds;
- recalibrar probabilidades;
- alterar resultados da avaliação final;
- introduzir regras científicas novas apenas para facilitar o frontend.

Caso uma transformação científica adicional seja realmente necessária, ela
deverá ser tratada fora do serving e auditada antes de seu consumo pela
aplicação.

---

# 6. Estrutura física inicial

A estrutura inicial será:

```text
data/serving/
├── metadata/
├── quality/
└── historical/
    ├── panorama/
    ├── seasonality/
    ├── spatial/
    ├── risk_dynamics/
    ├── municipality/
    └── climate/
```

Os diretórios serão criados pelos scripts quando necessário.

---

# 7. Convenções gerais dos contratos

Todos os contratos JSON deverão seguir as seguintes regras:

- codificação UTF-8;
- chaves em `snake_case`;
- números armazenados como números;
- booleanos armazenados como booleanos;
- datas no padrão ISO `YYYY-MM-DD`;
- ausência de `NaN`;
- ausência de `Infinity`;
- ausência de caminhos absolutos da máquina de desenvolvimento;
- ordem determinística quando a ordem possuir significado;
- códigos territoriais tratados como identificadores;
- ausência de lógica científica implementada no frontend.

Sempre que apropriado, os arquivos deverão possuir:

```text
schema_version
period
source
data
```

ou estrutura semanticamente equivalente.

---

# 8. Versão inicial dos schemas

Os contratos desta etapa utilizarão:

```text
schema_version = "1.0"
```

Mudanças incompatíveis futuras deverão alterar a versão do schema.

Mudanças apenas internas dos scripts que não alterem o contrato não exigem nova
versão.

---

# 9. Determinismo

A geração dos artefatos deverá ser determinística.

Uma nova execução sobre as mesmas fontes deverá produzir o mesmo conteúdo
científico.

Não deverão ser inseridos automaticamente nos arquivos campos voláteis como:

```text
generated_at
current_time
execution_uuid
```

quando eles não forem necessários ao produto.

Isso evita alterações artificiais no conteúdo a cada execução.

---

# 10. Proveniência

Cada contrato deverá possuir rastreabilidade até suas fontes.

A proveniência poderá ser registrada como:

```json
{
  "source": [
    "reports/audits/exemplo.json"
  ]
}
```

Os caminhos deverão ser relativos à raiz do projeto.

Caminhos locais como:

```text
C:\Users\...
```

não deverão aparecer nos arquivos de serving.

---

# 11. Metadata — territórios

Será produzido:

```text
data/serving/metadata/territories.json
```

Fonte principal:

```text
reports/audits/distribuicao_espacial_municipio_periodo_2016_2025.csv
```

Granularidade:

**uma linha por unidade territorial**

Quantidade esperada:

**5.571 unidades**

Campos mínimos:

```text
codigo_ibge_7
nome_municipio
codigo_uf_ibge
nome_uf
regiao
anos_disponiveis
```

O campo:

```text
codigo_ibge_7
```

deverá ser serializado como string.

---

# 12. Metadata — cobertura temporal

Será produzido:

```text
data/serving/metadata/temporal_coverage.json
```

Fontes:

```text
reports/audits/panorama_nacional_2016_2025.json
reports/audits/auditoria_painel_mestre.json
```

O contrato deverá informar ao menos:

```text
periodo_historico
anos
semanas_nacionais
anos_com_53_semanas
```

Período histórico:

```text
2016-2025
```

Anos com 53 semanas:

```text
2020
2025
```

---

# 13. Quality — visão geral

Será produzido:

```text
data/serving/quality/overview.json
```

Esse arquivo será utilizado pelos principais cards da área:

**Dados e Qualidade**

Fontes:

```text
reports/audits/auditoria_funil_sinan_2016_2025.json
reports/audits/auditoria_painel_mestre.json
reports/audits/auditoria_chaves_painel_mestre.json
```

Campos previstos:

```text
registros_sinan_brutos
registros_sinan_mantidos_apos_filtros
casos_finais_preservados
unidades_territoriais
municipio_semanas
linhas_zero_fill
unidades_com_cobertura_climatica
municipio_semanas_com_clima
municipio_semanas_sem_clima
```

Valores esperados principais:

```text
registros_sinan_brutos                    19.336.281
registros_sinan_mantidos_apos_filtros    16.294.945
casos_finais_preservados                 16.294.913
unidades_territoriais                     5.571
municipio_semanas                         2.907.593
linhas_zero_fill                          2.186.284
unidades_com_cobertura_climatica          5.570
municipio_semanas_com_clima               2.907.071
municipio_semanas_sem_clima               522
```

Esses valores não deverão ser digitados diretamente no frontend.

---

# 14. Quality — funil SINAN

Será produzido:

```text
data/serving/quality/sinan_pipeline.json
```

Fonte:

```text
reports/audits/auditoria_funil_sinan_2016_2025.json
```

O arquivo de serving deverá ser uma versão apropriada para apresentação do
funil, sem reproduzir necessariamente toda a estrutura interna da auditoria.

O contrato deverá conter:

```text
registros_brutos
etapas
registros_mantidos_apos_filtros
grupos_antes_normalizacao
codigos_sinan_iniciais
casos_finais
```

---

# 15. Funil SINAN

As remoções documentadas são:

| Etapa | Registros |
| --- | ---: |
| `CLASSI_FIN = 5` | 3.002.212 |
| Município inválido | 1.149 |
| `SEM_PRI` inválida | 79 |
| Fora do período | 37.896 |

Total de remoções documentadas:

**3.041.336**

O funil aritmético é:

```text
19.336.281
− 3.041.336
────────────
16.294.945
```

A verificação lógica segundo:

```text
NDUPLIC_N
```

não possui uma quantidade separada de registros removidos documentada.

O serving não deverá inventar esse valor.

---

# 16. Representação de NDUPLIC_N

O contrato de `sinan_pipeline.json` deverá representar a etapa como:

```text
verificação de duplicidade lógica
```

e não como:

```text
X registros removidos
```

Caso o frontend apresente um funil visual, essa etapa poderá aparecer como uma
verificação metodológica sem valor numérico associado.

---

# 17. Quality — normalização territorial

Será produzido:

```text
data/serving/quality/territorial_coverage.json
```

Fontes:

```text
reports/audits/auditoria_funil_sinan_2016_2025.json
reports/audits/auditoria_painel_mestre.json
reports/audits/distribuicao_espacial_2016_2025.json
```

O contrato deverá informar:

```text
codigos_sinan_iniciais
codigos_associados_diretamente
codigos_nao_associados_inicialmente
casos_nao_associados_inicialmente
codigos_df
casos_df_preservados
codigos_residuais
casos_residuais_excluidos
unidades_territoriais_finais
unidades_sem_registro_original
```

---

# 18. Valores territoriais esperados

Os valores principais são:

```text
Códigos SINAN iniciais                         5.621
Associados diretamente                         5.561
Não associados inicialmente                       60
Casos nesses códigos                          22.878

Subdivisões do Distrito Federal                   48
Casos preservados no Distrito Federal         22.846

Códigos residuais não municipais                  12
Casos residuais excluídos                         32

Unidades territoriais finais                   5.571
Unidades sem registro epidemiológico original     10
```

A consolidação do Distrito Federal deverá permanecer explicitamente
documentada.

---

# 19. Quality — zero-fill

A informação de zero-fill poderá fazer parte de:

```text
quality/overview.json
```

e de:

```text
quality/sinan_pipeline.json
```

Os valores são:

```text
linhas_observadas_antes_zero_fill    721.309
linhas_apos_zero_fill              2.907.593
linhas_preenchidas_com_zero        2.186.284
casos_antes                       16.294.913
casos_depois                      16.294.913
```

A aplicação deverá preservar a distinção entre:

**ausência de linha no extrato original**

e

**zero explicitamente inserido na grade analítica**

---

# 20. Quality — população

Será produzido:

```text
data/serving/quality/population_coverage.json
```

Fontes principais:

```text
data/processed/painel_municipal_semanal_2016_2025.parquet
reports/audits/auditoria_painel_mestre.json
```

A leitura do painel será realizada offline pelo gerador de serving.

O frontend não terá acesso direto ao painel mestre.

---

# 21. Contrato de população

O contrato deverá informar:

- anos disponíveis;
- tipo de população utilizado;
- ano de referência populacional;
- quantidade de linhas sem população;
- quantidade de populações não positivas;
- tratamento aplicado a 2023;
- observação sobre a transição para o Censo 2022.

A auditoria final deverá preservar:

```text
linhas sem população      0
populações não positivas  0
```

---

# 22. População de 2023

O serving deverá deixar explícito que:

**2023 utiliza a população do Censo 2022 como referência**

segundo a decisão metodológica já documentada no projeto.

Essa informação deverá ser obtida ou validada contra os campos existentes no
painel processado.

Ela não deverá existir apenas como texto manual no componente React.

---

# 23. Quality — clima

Será produzido:

```text
data/serving/quality/climate_coverage.json
```

Fontes:

```text
reports/audits/auditoria_painel_mestre.json
reports/audits/auditoria_chaves_painel_mestre.json
data/processed/painel_municipal_semanal_2016_2025.parquet
```

O contrato deverá permitir apresentar:

- unidades com cobertura climática;
- linhas com clima;
- linhas sem clima;
- unidade sem clima;
- unidades modeláveis;
- métodos de seleção da grade;
- número de pontos de grade;
- número de combinações grade × timezone.

---

# 24. Valores climáticos estruturados já auditados

Os valores já disponíveis incluem:

```text
unidades com mapeamento climático     5.570
linhas climáticas                     2.721.186
combinações grade × timezone          5.213
linhas com clima                      2.907.071
linhas sem clima                            522
```

A única unidade histórica totalmente sem clima é:

```text
Fernando de Noronha
codigo_ibge_7 = 2605459
```

---

# 25. Métodos de associação climática

As contagens por:

```text
metodo_selecao_grid
```

poderão ser derivadas diretamente do painel processado ou do artefato de
mapeamento disponível no pipeline.

A derivação deverá ser apenas uma contagem estrutural.

Ela não deverá refazer o processo geográfico de seleção da grade.

---

# 26. Histórico — panorama anual

Será produzido:

```text
data/serving/historical/panorama/annual.json
```

Fonte:

```text
reports/audits/panorama_nacional_anual_2016_2025.csv
```

Granularidade:

**ano epidemiológico**

Quantidade esperada:

**10 registros**

Campos candidatos:

```text
ano_epidemiologico
semanas_epidemiologicas
casos_provaveis
populacao_nacional
incidencia_anual_100mil
media_semanal_casos
pico_semanal_casos
semana_pico
data_inicio_semana_pico
unidades_territoriais
unidades_territoriais_com_casos
proporcao_unidades_com_casos
participacao_casos_periodo
```

O serving deverá reutilizar os valores auditados.

---

# 27. Histórico — panorama semanal

Será produzido:

```text
data/serving/historical/panorama/weekly.json
```

Fonte:

```text
reports/audits/panorama_nacional_semanal_2016_2025.csv
```

Granularidade:

**semana epidemiológica nacional**

Quantidade esperada:

**522 registros**

Campos candidatos:

```text
ano_epidemiologico
semana_epidemiologica
data_inicio_semana
data_fim_semana
casos_provaveis
unidades_territoriais
unidades_territoriais_com_casos
populacao_nacional
incidencia_nacional_100mil
proporcao_unidades_com_casos
```

---

# 28. Histórico — sazonalidade nacional

Será produzido:

```text
data/serving/historical/seasonality/national.json
```

Fonte:

```text
reports/audits/sazonalidade_nacional_semana_epidemiologica_2016_2025.csv
```

Granularidade:

**semana epidemiológica**

Campos:

```text
semana_epidemiologica
anos_disponiveis
casos_media
casos_mediana
casos_minimo
casos_maximo
incidencia_media_100mil
incidencia_mediana_100mil
incidencia_q25_100mil
incidencia_q75_100mil
incidencia_minima_100mil
incidencia_maxima_100mil
```

---

# 29. Histórico — sazonalidade regional

Será produzido:

```text
data/serving/historical/seasonality/regional.json
```

Fonte:

```text
reports/audits/sazonalidade_regional_semana_epidemiologica_2016_2025.csv
```

Chave lógica:

```text
regiao + semana_epidemiologica
```

Regiões esperadas:

```text
Norte
Nordeste
Centro-Oeste
Sudeste
Sul
```

---

# 30. Histórico — distribuição espacial por região

Será produzido:

```text
data/serving/historical/spatial/regions.json
```

Fonte:

```text
reports/audits/distribuicao_espacial_regiao_periodo_2016_2025.csv
```

Quantidade esperada:

**5 registros**

O arquivo será utilizado em comparações agregadas entre macrorregiões.

---

# 31. Histórico — distribuição espacial por UF

Será produzido:

```text
data/serving/historical/spatial/states.json
```

Fonte:

```text
reports/audits/distribuicao_espacial_uf_periodo_2016_2025.csv
```

Quantidade esperada:

**27 registros**

---

# 32. Histórico — distribuição espacial municipal

Será produzido:

```text
data/serving/historical/spatial/municipalities.json
```

Fonte:

```text
reports/audits/distribuicao_espacial_municipio_periodo_2016_2025.csv
```

Quantidade esperada:

**5.571 registros**

Campos candidatos:

```text
codigo_ibge_7
nome_municipio
codigo_uf_ibge
nome_uf
regiao
anos_disponiveis
anos_com_casos
casos_periodo
populacao_media
incidencia_media_anual_100mil
incidencia_mediana_anual_100mil
incidencia_maxima_anual_100mil
ano_maior_incidencia
incidencia_ano_pico_100mil
participacao_casos_periodo
```

Este arquivo poderá alimentar o mapa histórico e os resumos municipais.

---

# 33. Histórico espacial anual

As fontes anuais existentes são:

```text
reports/audits/distribuicao_espacial_regiao_anual_2016_2025.csv
reports/audits/distribuicao_espacial_uf_anual_2016_2025.csv
reports/audits/distribuicao_espacial_municipio_anual_2016_2025.csv
```

Os contratos anuais serão gerados caso sejam necessários às interações do
dashboard.

Inicialmente deverão ser preparados pelo gerador, mas o formato físico poderá
ser particionado para evitar payloads desnecessários.

---

# 34. Histórico — risco semanal

Será produzido:

```text
data/serving/historical/risk_dynamics/weekly.json
```

Fonte:

```text
reports/audits/serie_risco_semanal_nacional_regional_2018_2025.csv
```

A fonte possui granularidade:

```text
escala + grupo + semana
```

Campos:

```text
escala
grupo
ano_epidemiologico
semana_epidemiologica
data_inicio_semana
unidades_elegiveis
unidades_em_risco
proporcao_unidades_em_risco
incidencia_4s_media_100mil
incidencia_4s_mediana_100mil
limiar_p90_mediano_100mil
```

O serving não recalculará o estado `risco_elevado`.

---

# 35. Histórico — resumo municipal de risco

Será produzido:

```text
data/serving/historical/risk_dynamics/municipalities.json
```

Fonte:

```text
reports/audits/dinamica_risco_municipio_2018_2025.csv
```

Quantidade esperada:

**5.569 municípios elegíveis**

Campos candidatos:

```text
codigo_ibge_7
nome_municipio
codigo_uf_ibge
nome_uf
regiao
observacoes_elegiveis
anos_elegiveis
semanas_risco
proporcao_semanas_risco
anos_com_risco
primeira_semana_risco
ultima_semana_risco
episodios
duracao_media_episodio
duracao_mediana_episodio
duracao_maxima_episodio
episodios_multianuais
recorrencia_multianual
```

---

# 36. Histórico — distribuição da duração dos episódios

Não será necessário enviar ao navegador o arquivo completo:

```text
reports/audits/episodios_risco_elevado_2018_2025.csv
```

com todos os episódios individuais apenas para reproduzir o gráfico de duração.

Será produzido:

```text
data/serving/historical/risk_dynamics/episode_duration.json
```

Fonte:

```text
reports/audits/episodios_risco_elevado_2018_2025.csv
```

O contrato deverá conter:

```text
summary
distribution
```

---

# 37. Resumo dos episódios

O bloco:

```text
summary
```

deverá conter ao menos:

```text
quantidade_episodios
media
p25
mediana
p75
p90
p95
p99
maximo
```

Valores de referência:

```text
episódios   54.269
média       7,64
p25         3
mediana     4
p75         9
p90         19
p95         26
p99         41
máximo      110
```

---

# 38. Distribuição dos episódios

O bloco:

```text
distribution
```

deverá possuir a frequência observada por duração.

Exemplo lógico:

```json
[
  {
    "duracao_semanas": 1,
    "episodios": 100
  },
  {
    "duracao_semanas": 2,
    "episodios": 200
  }
]
```

Os números acima são apenas exemplos de schema.

As contagens reais deverão ser calculadas pelo gerador a partir do CSV de
episódios.

Essa operação é uma agregação destinada exclusivamente à visualização e não
altera a definição científica de episódio.

---

# 39. Histórico — clima nacional

Será produzido:

```text
data/serving/historical/climate/national_lags.json
```

Fonte:

```text
reports/audits/associacao_clima_dengue_nacional_2016_2025.csv
```

Quantidade esperada:

```text
3 variáveis × 7 lags = 21 registros
```

Variáveis:

```text
temperatura_media_c
umidade_relativa_media_pct
precipitacao_total_mm
```

Lags:

```text
0
1
2
3
4
6
8
```

---

# 40. Histórico — clima regional

Será produzido:

```text
data/serving/historical/climate/regional_lags.json
```

Fonte:

```text
reports/audits/associacao_clima_dengue_regional_2016_2025.csv
```

Quantidade esperada:

```text
5 regiões × 3 variáveis × 7 lags = 105 registros
```

O serving deverá preservar as correlações já calculadas.

---

# 41. Clima — interpretação

Os arquivos climáticos deverão transportar apenas resultados da análise
descritiva já congelada.

A aplicação deverá continuar informando que:

**correlação não implica causalidade**

O serving não deverá classificar uma associação como causal.

---

# 42. Índice municipal

Será produzido:

```text
data/serving/historical/municipality/index.json
```

O índice deverá combinar somente informações necessárias para localizar e
apresentar municípios.

Fontes candidatas:

```text
reports/audits/distribuicao_espacial_municipio_periodo_2016_2025.csv
reports/audits/dinamica_risco_municipio_2018_2025.csv
```

A junção deverá utilizar:

```text
codigo_ibge_7
```

como chave.

---

# 43. Série temporal municipal detalhada

A aplicação deverá futuramente permitir consulta do histórico de um município.

A fonte científica será:

```text
data/processed/painel_municipal_semanal_2016_2025.parquet
```

Entretanto, o formato físico definitivo do serving municipal detalhado não será
escolhido apenas por conveniência.

Antes da decisão serão avaliados:

- tamanho total;
- tamanho médio por município;
- quantidade de arquivos;
- custo de leitura server-side;
- payload enviado ao cliente;
- compatibilidade com o deploy do Next.js.

---

# 44. Contrato lógico municipal

Independentemente do formato físico, a série municipal deverá poder fornecer:

```text
codigo_ibge_7
ano_epidemiologico
semana_epidemiologica
data_inicio_semana
casos_provaveis
incidencia_100mil
registro_sinan_presente
zero_preenchido
populacao
```

Campos climáticos poderão ser incluídos somente quando realmente necessários à
experiência da página municipal.

---

# 45. Decisão física municipal

A implementação poderá avaliar alternativas como:

- particionamento por município;
- particionamento por UF;
- formato tabular compacto para leitura server-side;
- outro armazenamento estático adequado ao Next.js.

A decisão será tomada com base em medição.

O navegador não deverá receber toda a série nacional apenas para exibir um
município.

---

# 46. Dados que não serão copiados integralmente para serving

Não deverão ser simplesmente duplicados integralmente:

```text
data/processed/dataset_modelagem_2018_2024.parquet
data/processed/dataset_teste_final_2025.parquet
data/processed/predicoes_oof_modelo_a_hgb_2021_2024.parquet
```

Esses arquivos pertencem à modelagem e não ao dashboard histórico.

O arquivo:

```text
data/processed/painel_municipal_semanal_2016_2025.parquet
```

será utilizado como fonte offline quando necessário, mas não será entregue
integralmente ao browser.

---

# 47. Artefatos grandes de auditoria

Arquivos como:

```text
reports/audits/associacao_clima_dengue_municipios_2016_2025.csv
reports/audits/episodios_risco_elevado_2018_2025.csv
reports/audits/distribuicao_espacial_municipio_anual_2016_2025.csv
```

não deverão ser automaticamente enviados para o frontend.

Quando necessário, deverão ser:

- resumidos;
- selecionados;
- particionados;
- consultados server-side.

---

# 48. Uso das figuras estáticas

Os arquivos:

```text
reports/figures/01_*.png
...
reports/figures/07_*.png
```

não constituem fonte de dados para serving.

As figuras são produtos finais de visualização acadêmica.

Os dados do dashboard deverão vir dos artefatos estruturados que deram origem
às análises.

---

# 49. Nomenclatura de campos

Quando possível, os nomes científicos existentes serão preservados.

Exemplos:

```text
casos_provaveis
incidencia_100mil
ano_epidemiologico
semana_epidemiologica
codigo_ibge_7
```

Renomeações destinadas apenas à apresentação deverão ocorrer preferencialmente
na camada de interface.

O serving deverá evitar nomes ambíguos.

---

# 50. Identificadores territoriais

O identificador primário das unidades territoriais será:

```text
codigo_ibge_7
```

Esse campo deverá ser tratado como:

**string**

na camada de serving e no frontend.

Nomes de municípios não deverão ser utilizados como chave primária.

---

# 51. Regiões

Os valores válidos serão:

```text
Norte
Nordeste
Centro-Oeste
Sudeste
Sul
```

Valores fora desse domínio deverão causar falha de validação quando o contrato
exigir macrorregião.

---

# 52. Valores ausentes

Cada contrato deverá definir explicitamente campos que podem ser nulos.

O gerador não deverá substituir automaticamente ausência por:

```text
0
```

quando zero e ausência possuem significados diferentes.

Essa regra é especialmente importante para:

- clima;
- targets;
- períodos não elegíveis;
- unidades territoriais com cobertura diferente.

---

# 53. Números decimais

Os JSONs utilizarão ponto como separador decimal, conforme a sintaxe JSON.

Exemplo:

```json
{
  "incidencia_100mil": 721.46
}
```

A formatação brasileira com vírgula será responsabilidade da interface.

---

# 54. Ordenação

Os artefatos deverão utilizar ordenação determinística.

Exemplos:

```text
panorama
→ ano

sazonalidade
→ região + semana

territórios
→ codigo_ibge_7

risco semanal
→ escala + grupo + data

clima
→ variável + região + lag
```

---

# 55. Validação estrutural

Cada gerador deverá validar, quando aplicável:

- presença das fontes;
- colunas obrigatórias;
- quantidade esperada de registros;
- chaves duplicadas;
- domínios permitidos;
- valores ausentes inesperados;
- valores não finitos;
- cobertura temporal;
- cobertura territorial.

A geração deverá falhar caso um contrato importante não seja satisfeito.

---

# 56. Validação científica cruzada

Além do schema, deverão ser preservadas invariantes científicas já conhecidas.

Exemplos:

```text
casos finais = 16.294.913

linhas do painel = 2.907.593

unidades históricas = 5.571

unidades climáticas = 5.570

episódios = 54.269

semanas em risco = 414.678

pico nacional de risco = 3.121 municípios
```

Essas invariantes deverão ser verificadas contra as fontes auditadas.

---

# 57. Não duplicação de constantes científicas

Valores científicos não deverão existir simultaneamente como constantes
independentes em vários componentes.

Exemplo inadequado no frontend:

```typescript
const TOTAL_CASES = 16294913;
```

O valor deverá vir de:

```text
data/serving/quality/overview.json
```

produzido pelo pipeline.

---

# 58. Script de geração

A implementação deverá possuir script ou scripts reproduzíveis dentro de:

```text
scripts/
```

A organização poderá ser:

```text
scripts/gerar_serving_quality.py
scripts/gerar_serving_historical.py
```

ou outra divisão tecnicamente justificada.

Os scripts deverão utilizar as convenções já existentes no projeto.

---

# 59. Código reutilizável

Funções que representem contratos, serialização ou validações reutilizáveis
poderão ser implementadas em:

```text
src/dengue_alert/
```

caso isso reduza duplicação entre scripts.

Os scripts deverão permanecer como pontos de entrada do processo.

---

# 60. Testes automatizados

A camada de serving deverá receber testes automatizados.

Os testes deverão verificar ao menos:

- arquivos esperados;
- schemas;
- chaves;
- quantidades principais;
- unicidade territorial;
- anos;
- semanas;
- regiões;
- ausência de `NaN`;
- compatibilidade entre contratos relacionados.

---

# 61. Auditoria independente do serving

Após a geração, será realizada a etapa:

**13D — Auditoria dos contratos de serving**

A auditoria não deverá depender apenas do fato de os scripts terem terminado sem
erro.

Ela deverá verificar os artefatos produzidos de forma independente.

---

# 62. Política de versionamento dos artefatos

Os scripts, contratos e testes deverão ser versionados.

A decisão de adicionar os artefatos gerados em:

```text
data/serving/
```

ao Git dependerá do tamanho final.

Antes de versionar grandes conjuntos derivados, serão avaliados:

- tamanho total;
- reprodutibilidade;
- necessidade no deploy;
- limites do repositório.

Não será feito `git add` indiscriminado de todos os arquivos de serving.

---

# 63. Dados de qualidade no frontend

A página Dados e Qualidade deverá consumir os contratos de `quality/`.

Ela não deverá ler diretamente:

```text
docs/
reports/audits/
data/processed/
```

Essas são fontes do pipeline, não contratos da aplicação.

---

# 64. Dashboard histórico no frontend

O dashboard deverá consumir:

```text
data/serving/historical/
```

e:

```text
data/serving/metadata/
```

A interface não deverá depender diretamente de CSVs de auditoria.

---

# 65. Responsividade e serving

A camada de dados deverá permitir que componentes responsivos recebam somente a
informação necessária.

Uma tela mobile não deverá receber uma base maior apenas porque o desktop possui
mais espaço visual.

A estratégia de carregamento poderá variar conforme a interação.

---

# 66. Primeiro conjunto de artefatos

A primeira implementação da 13B deverá priorizar:

```text
metadata/territories.json
metadata/temporal_coverage.json

quality/overview.json
quality/sinan_pipeline.json
quality/territorial_coverage.json
quality/population_coverage.json
quality/climate_coverage.json

historical/panorama/annual.json
historical/panorama/weekly.json

historical/seasonality/national.json
historical/seasonality/regional.json

historical/spatial/regions.json
historical/spatial/states.json
historical/spatial/municipalities.json

historical/risk_dynamics/weekly.json
historical/risk_dynamics/municipalities.json
historical/risk_dynamics/episode_duration.json

historical/climate/national_lags.json
historical/climate/regional_lags.json

historical/municipality/index.json
```

O serving municipal semanal detalhado será definido após medição do formato
físico mais adequado.

---

# 67. Critério de conclusão da 13B

A etapa 13B será considerada concluída quando:

- os contratos acima estiverem implementados;
- os artefatos forem reproduzíveis;
- Ruff estiver limpo;
- testes automatizados estiverem aprovados;
- os artefatos passarem pelas validações estruturais;
- os principais totais científicos forem preservados;
- tamanhos dos arquivos forem conhecidos;
- a estratégia do histórico municipal detalhado estiver decidida.

---

# 68. Relação com 13C

Nenhum dado preditivo será incorporado silenciosamente aos contratos históricos.

Após o fechamento da 13B será criado contrato específico para:

**13C — Serving preditivo**

Esse contrato tratará:

- previsões de 2025;
- H1–H4;
- probabilidades;
- thresholds;
- alertas;
- semanas-alvo;
- observado retrospectivo.

---

# 69. Relação com 13E

O Next.js somente será iniciado após:

- serving histórico e de qualidade;
- serving preditivo;
- auditoria dos contratos.

Assim, o frontend começará seu desenvolvimento consumindo contratos previamente
definidos.

Isso reduz o risco de construir componentes baseados em estruturas temporárias.

---

# 70. Status

Fase:

**13B — Serving histórico e de qualidade**

Subetapa:

**Contrato de dados**

Status:

**CONGELADO ANTES DA IMPLEMENTAÇÃO DOS GERADORES**

Próximo passo:

**implementar e validar os geradores de serving**