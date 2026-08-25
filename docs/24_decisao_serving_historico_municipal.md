# 24 — Decisão de arquitetura do serving histórico municipal

## 1. Objetivo

Este documento registra a decisão arquitetural para disponibilização do histórico
semanal municipal na aplicação do projeto Dengue Alert.

A decisão foi tomada após benchmark específico sobre o painel municipal semanal
consolidado de 2016 a 2025, evitando definir o formato de serving apenas por
conveniência de implementação.

O objetivo é permitir que a aplicação consulte o histórico individual de um
município de forma leve, determinística e adequada ao consumo pelo frontend,
sem transferir o painel nacional completo para o navegador.

---

## 2. Fonte avaliada

O benchmark utilizou como fonte:

```text
data/processed/painel_municipal_semanal_2016_2025.parquet
```

Foram avaliadas apenas as nove colunas inicialmente necessárias para a
visualização histórica municipal:

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

O painel avaliado possui:

| Indicador | Valor |
|---|---:|
| Município-semanas | 2.907.593 |
| Unidades territoriais | 5.571 |
| Unidades com 522 semanas | 5.570 |
| Unidades com 53 semanas | 1 |

A única unidade com 53 semanas é:

```text
5101837 — Boa Esperança do Norte / Mato Grosso
```

Sua cobertura inicia em 2025, respeitando sua instalação territorial e evitando
a criação artificial de observações anteriores à existência da unidade.

---

## 3. Alternativas avaliadas

Foram comparadas três estratégias principais:

### 3.1. JSON verboso por município

Cada semana seria representada como um objeto JSON independente, repetindo os
nomes dos campos em todas as observações.

Exemplo conceitual:

```json
{
  "data": [
    {
      "ano_epidemiologico": 2024,
      "semana_epidemiologica": 1,
      "casos_provaveis": 10,
      "incidencia_100mil": 15.2
    }
  ]
}
```

### 3.2. JSON compacto por município

Cada município continua possuindo seu próprio arquivo, mas a estrutura é
colunar. Os nomes dos campos aparecem apenas uma vez e cada campo contém um
array ordenado temporalmente.

Exemplo conceitual:

```json
{
  "schema_version": "1.0",
  "codigo_ibge_7": "3537305",
  "count": 522,
  "data": {
    "ano_epidemiologico": [2016, 2016, 2016],
    "semana_epidemiologica": [1, 2, 3],
    "casos_provaveis": [0, 1, 3],
    "incidencia_100mil": [0.0, 1.5, 4.6]
  }
}
```

### 3.3. Parquet nacional reduzido

Também foi produzido temporariamente um Parquet contendo somente as nove
colunas candidatas ao serving municipal e utilizando compressão Zstandard.

Essa alternativa foi avaliada principalmente como possibilidade de leitura
server-side.

---

## 4. Resultados do benchmark

O benchmark produziu os seguintes resultados:

| Alternativa | Tamanho total | Arquivo municipal mediano | Maior arquivo municipal |
|---|---:|---:|---:|
| JSON verboso | 580,15 MB | 106,23 KB | 114,98 KB |
| JSON verboso — gzip estimado | 23,18 MB | 4,05 KB | 10,59 KB |
| JSON compacto | 131,87 MB | 23,82 KB | 32,57 KB |
| JSON compacto — gzip estimado | 15,46 MB | 2,66 KB | 7,93 KB |
| Parquet nacional Zstandard | 4,91 MB | — | — |

O JSON compacto apresentou redução de:

```text
77,27% sem compressão
33,31% considerando gzip
```

em relação ao JSON verboso.

Os valores estruturados utilizados nesta decisão estão registrados em:

```text
reports/audits/benchmark_serving_municipal.json
```

O benchmark é reproduzido por:

```text
scripts/benchmark_serving_municipal.py
```

---

## 5. Decisão

A estratégia inicial aprovada para o serving histórico municipal é:

> **um arquivo JSON compacto por unidade territorial.**

A estrutura física prevista é:

```text
data/serving/historical/municipality/
├── index.json
└── series/
    ├── 1100015.json
    ├── 1100023.json
    ├── ...
    ├── 5101837.json
    └── 5300108.json
```

Serão produzidos 5.571 arquivos de séries municipais.

Cada arquivo será identificado pelo código IBGE de sete dígitos da unidade
territorial.

---

## 6. Justificativa

Embora o Parquet nacional reduzido tenha apresentado o menor tamanho agregado,
a decisão não deve considerar somente o tamanho total do conjunto.

A unidade real de acesso da aplicação é o município.

Quando o usuário selecionar uma unidade territorial, a aplicação precisa
receber apenas a série histórica daquele município, e não as 2.907.593 linhas
do painel nacional.

Com JSON compacto, um município típico possui aproximadamente:

```text
23,82 KB sem compressão
2,66 KB com gzip
```

Mesmo o maior arquivo observado no benchmark apresentou aproximadamente:

```text
32,57 KB sem compressão
7,93 KB com gzip
```

Esses valores são suficientemente pequenos para carregamento sob demanda em
desktop, tablet e dispositivos móveis.

Além disso, o JSON pode ser consumido diretamente pelo frontend sem necessidade
de biblioteca específica para leitura de Parquet.

Arquivos estáticos também permitem utilização direta de mecanismos de cache do
navegador, CDN e infraestrutura de hospedagem estática.

---

## 7. Por que o Parquet não foi escolhido inicialmente

O resultado de 4,91 MB do Parquet nacional demonstra que o formato continua
sendo tecnicamente muito eficiente para armazenamento e processamento.

Entretanto, seu melhor caso de uso neste projeto seria uma arquitetura com
consulta server-side, na qual uma camada de servidor abriria o arquivo e
retornaria somente o município solicitado.

Essa abordagem introduziria uma camada adicional de execução no serving.

Na arquitetura inicial do Dengue Alert, essa complexidade não é necessária para
atender ao volume observado.

Portanto, o Parquet permanece registrado como alternativa válida para evolução
futura, especialmente caso a aplicação passe a exigir consultas dinâmicas mais
complexas ou uma API dedicada.

---

## 8. Contrato municipal previsto

Cada arquivo municipal deverá possuir estrutura equivalente a:

```json
{
  "schema_version": "1.0",
  "codigo_ibge_7": "3537305",
  "count": 522,
  "data": {
    "ano_epidemiologico": [],
    "semana_epidemiologica": [],
    "data_inicio_semana": [],
    "casos_provaveis": [],
    "incidencia_100mil": [],
    "registro_sinan_presente": [],
    "zero_preenchido": [],
    "populacao": []
  }
}
```

Todos os arrays de `data` deverão possuir exatamente o mesmo comprimento
informado por `count`.

A ordenação será cronológica e determinística.

Códigos IBGE serão armazenados como strings.

Datas serão serializadas em formato ISO.

O JSON não poderá conter `NaN` ou `Infinity`.

---

## 9. Relação com o índice municipal

O arquivo já definido:

```text
data/serving/historical/municipality/index.json
```

continua sendo o ponto de entrada para localização das unidades territoriais.

O índice contém as 5.571 unidades disponíveis no histórico espacial e registra
se existe histórico de risco elevado para cada uma.

A ausência de histórico de risco não implica ausência de série epidemiológica
municipal.

Portanto, a disponibilidade da série histórica e a disponibilidade do histórico
do target de risco são conceitos distintos no serving.

---

## 10. Separação entre histórico e predição

Os arquivos definidos neste documento pertencem exclusivamente à camada
histórica da aplicação.

Eles não representam previsão futura.

A série municipal poderá ser utilizada para apresentar casos observados,
incidência, histórico temporal e indicadores de qualidade relacionados ao
painel consolidado.

Os resultados preditivos terão contratos próprios em:

```text
data/serving/prediction/
```

Essa separação evita que valores históricos observados sejam confundidos com
probabilidades previstas pelo modelo.

---

## 11. Reprodutibilidade

A decisão arquitetural é sustentada por artefatos reproduzíveis:

```text
scripts/benchmark_serving_municipal.py
reports/audits/benchmark_serving_municipal.json
```

O benchmark valida:

```text
2.907.593 município-semanas
5.571 unidades territoriais
5.570 unidades com 522 semanas
1 unidade com 53 semanas
```

A exceção temporal conhecida é:

```text
5101837 — Boa Esperança do Norte / Mato Grosso
```

com 53 semanas em 2025.

---

## 12. Decisão congelada para a implementação inicial

Para a primeira arquitetura de serving da aplicação, fica definido:

```text
Formato:
JSON compacto colunar

Granularidade física:
1 arquivo por unidade territorial

Quantidade esperada:
5.571 arquivos

Diretório:
data/serving/historical/municipality/series/

Identificador:
codigo_ibge_7

Carregamento:
sob demanda por município

Consumo:
direto pelo frontend

Compressão de transporte:
compatível com gzip/Brotli da infraestrutura web

Alternativa futura:
Parquet com leitura server-side
```

A estratégia poderá ser reavaliada caso medições reais da aplicação indiquem
gargalos de deploy, quantidade de arquivos, cache, hospedagem ou tempo de
consulta.

Até que exista evidência nesse sentido, o JSON compacto por município é o
contrato físico aprovado para a implementação inicial.