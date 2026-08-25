# 26 — Decisão de arquitetura do serving preditivo municipal

## 1. Objetivo

Este documento registra a decisão de arquitetura física para disponibilização
das predições retrospectivas municipais do Dengue Alert.

A semântica preditiva já foi congelada em:

```text
docs/25_contrato_serving_predicao.md
```

A presente decisão trata exclusivamente da representação física dos resultados
para consumo pela aplicação.

Nenhum treinamento, calibração, seleção de modelo, definição de target ou
otimização de threshold é realizado nesta etapa.

---

## 2. Fonte avaliada

O benchmark utilizou:

```text
data/processed/predicoes_avaliacao_final_2025.parquet
```

O artefato possui:

```text
1.124.938 predições
5.569 municípios
202 predições por município
4 horizontes
```

A distribuição é:

| Horizonte | Linhas | Registros por município | Threshold |
|---|---:|---:|---:|
| H1 | 289.588 | 52 | 0.187687 |
| H2 | 284.019 | 51 | 0.190783 |
| H3 | 278.450 | 50 | 0.167991 |
| H4 | 272.881 | 49 | 0.157138 |
| **Total** | **1.124.938** | **202** | — |

---

## 3. Invariantes validadas antes do benchmark

Antes da medição dos formatos, foram verificadas as invariantes científicas e
estruturais do artefato final:

```text
linhas = 1.124.938

municípios = 5.569

horizontes = {1, 2, 3, 4}

ano epidemiológico = 2025

duplicadas na chave preditiva = 0

scores dentro de [0, 1]

predicao == score >= threshold

threshold H1 = 0.187687
threshold H2 = 0.190783
threshold H3 = 0.167991
threshold H4 = 0.157138
```

O benchmark somente foi executado após essas validações.

---

## 4. Alternativas avaliadas

Foram comparadas quatro representações.

### 4.1. JSON verboso por município

Cada predição seria armazenada como um objeto completo.

Campos como:

```text
horizonte
threshold
ano_epidemiologico
```

seriam repetidos em cada registro.

---

### 4.2. JSON compacto colunar

Cada município possuiria um único conjunto de arrays alinhados:

```text
ano_epidemiologico[]
semana_epidemiologica[]
data_inicio_semana[]
risco_elevado[]
target[]
horizonte[]
score[]
threshold[]
predicao[]
```

Essa estratégia reduz significativamente a repetição dos nomes dos campos.

---

### 4.3. JSON compacto organizado por horizonte

Cada município possui um arquivo, mas as predições são separadas internamente
em:

```text
h1
h2
h3
h4
```

Cada horizonte contém seu threshold apenas uma vez e seus próprios arrays
temporais.

Exemplo conceitual:

```json
{
  "schema_version": "1.0",
  "codigo_ibge_7": "3537305",
  "count": 202,
  "horizontes": {
    "h1": {
      "count": 52,
      "threshold": 0.187687,
      "data": {
        "semana_epidemiologica": [],
        "data_inicio_semana": [],
        "risco_elevado": [],
        "target": [],
        "score": [],
        "predicao": []
      }
    },
    "h2": {
      "count": 51,
      "threshold": 0.190783,
      "data": {}
    },
    "h3": {
      "count": 50,
      "threshold": 0.167991,
      "data": {}
    },
    "h4": {
      "count": 49,
      "threshold": 0.157138,
      "data": {}
    }
  }
}
```

---

### 4.4. Parquet nacional reduzido

Também foi avaliado um Parquet nacional contendo somente as dez colunas
necessárias ao serving, com compressão Zstandard.

Essa alternativa representa principalmente uma possível arquitetura futura de
consulta server-side.

---

## 5. Resultados

Os resultados medidos foram:

| Representação | Total | Total gzip estimado | Arquivo mediano | Mediano gzip |
|---|---:|---:|---:|---:|
| JSON verboso | 221,11 MB | 18,64 MB | 40,70 KB | 3,48 KB |
| JSON compacto colunar | 76,02 MB | 13,47 MB | 14,02 KB | 2,52 KB |
| JSON compacto por horizonte | 67,10 MB | 13,94 MB | 12,38 KB | 2,61 KB |
| Parquet nacional Zstd | 7,43 MB | — | — | — |

---

## 6. Reduções observadas

Em relação ao JSON verboso, o JSON compacto colunar reduziu:

```text
65,62% sem compressão
27,75% com gzip
```

O JSON compacto organizado por horizonte reduziu:

```text
69,66% sem compressão
25,20% com gzip
```

Comparando diretamente as duas estratégias compactas, o formato por horizonte
é:

```text
11,74% menor sem compressão
3,53% maior sob gzip
```

---

## 7. Decisão

A estratégia aprovada para a implementação inicial é:

> **JSON compacto organizado por horizonte, com um arquivo por município.**

A estrutura física prevista é:

```text
data/serving/prediction/
├── metadata/
├── evaluation/
└── municipality/
    ├── index.json
    └── series/
        ├── 1100015.json
        ├── 1100023.json
        ├── ...
        └── 5300108.json
```

A área de séries deverá possuir:

```text
5.569 arquivos municipais
```

---

## 8. Justificativa

O JSON compacto colunar apresentou a menor transferência gzip entre as
alternativas JSON:

```text
2,52 KB por município mediano
```

O formato organizado por horizonte apresentou:

```text
2,61 KB por município mediano
```

A diferença é de aproximadamente:

```text
0,09 KB por consulta municipal típica
```

Essa diferença é considerada operacionalmente pequena.

Em contrapartida, o formato por horizonte:

```text
reduz o tamanho não comprimido;
elimina a repetição do horizonte em cada observação;
elimina a repetição do threshold em cada observação;
reflete diretamente H1, H2, H3 e H4;
simplifica a seleção de horizonte na interface;
torna o contrato mais legível e semanticamente explícito.
```

Por essas razões, a clareza estrutural supera a pequena vantagem gzip do formato
colunar único.

---

## 9. Unidade real de acesso

A aplicação não precisa transferir:

```text
1.124.938 predições
```

para apresentar o resultado de um município.

A unidade real de consulta é uma única unidade territorial.

Assim, ao selecionar um município, o frontend deverá carregar apenas:

```text
prediction/municipality/series/{codigo_ibge_7}.json
```

O arquivo municipal mediano possui aproximadamente:

```text
12,38 KB sem compressão
2,61 KB sob gzip
```

Esse tamanho é adequado para carregamento sob demanda inclusive em
dispositivos móveis.

---

## 10. Estrutura municipal aprovada

Cada arquivo terá estrutura equivalente a:

```json
{
  "schema_version": "1.0",
  "codigo_ibge_7": "3537305",
  "count": 202,
  "horizontes": {
    "h1": {
      "count": 52,
      "threshold": 0.187687,
      "data": {
        "ano_epidemiologico": [],
        "semana_epidemiologica": [],
        "data_inicio_semana": [],
        "risco_elevado": [],
        "target": [],
        "score": [],
        "predicao": []
      }
    },
    "h2": {
      "count": 51,
      "threshold": 0.190783,
      "data": {}
    },
    "h3": {
      "count": 50,
      "threshold": 0.167991,
      "data": {}
    },
    "h4": {
      "count": 49,
      "threshold": 0.157138,
      "data": {}
    }
  }
}
```

---

## 11. Threshold no contrato

O threshold pertence ao horizonte, não à observação individual.

Portanto, no formato aprovado:

```text
h1.threshold = 0.187687
h2.threshold = 0.190783
h3.threshold = 0.167991
h4.threshold = 0.157138
```

O campo não será repetido em cada semana.

Isso não altera o resultado científico.

É somente uma normalização física de um valor que já é constante dentro de cada
horizonte.

---

## 12. Campo horizonte

Da mesma forma, o número do horizonte não precisa existir em cada observação.

A própria chave:

```text
h1
h2
h3
h4
```

define o horizonte do bloco.

A retirada do array repetitivo `horizonte[]` é uma transformação de serving e
não modifica a semântica da previsão.

---

## 13. Campos preservados por horizonte

Cada bloco deverá preservar:

```text
ano_epidemiologico
semana_epidemiologica
data_inicio_semana
risco_elevado
target
score
predicao
```

Todos os arrays dentro do mesmo horizonte deverão possuir exatamente o
comprimento indicado por:

```text
count
```

---

## 14. Early warning

O contrato municipal poderá permitir que a interface derive:

```text
early_warning =
    risco_elevado == false
    AND
    predicao == true
```

Esse conceito não deve substituir `predicao`.

São informações diferentes.

O serving inicial não precisa materializar um array adicional caso a derivação
no frontend permaneça simples e determinística.

---

## 15. Target retrospectivo

O campo:

```text
target
```

será preservado porque o serving representa a avaliação retrospectiva de 2025.

Isso permite comparar:

```text
probabilidade estimada
classificação produzida
estado futuro realmente observado
```

Em uma aplicação prospectiva futura, `target` ainda não estaria disponível no
momento da previsão.

---

## 16. Natureza retrospectiva

Os arquivos pertencem exclusivamente à avaliação final de:

```text
2025
```

Eles não representam alertas atuais de 2026.

A aplicação deverá identificar claramente o conteúdo como:

```text
avaliação retrospectiva
resultado histórico do modelo
simulação histórica de alerta antecipado
```

---

## 17. Por que o Parquet não foi escolhido

O Parquet nacional reduzido apresentou:

```text
7,43 MB
```

e continua sendo a representação agregada mais eficiente em armazenamento.

Entretanto, seu uso direto exigiria uma arquitetura de leitura server-side ou
outra camada capaz de filtrar o município solicitado.

Para a aplicação inicial, os arquivos JSON municipais permitem:

```text
consumo direto pelo frontend;
carregamento sob demanda;
cache de arquivos estáticos;
CDN;
ausência de biblioteca Parquet no navegador;
arquitetura mais simples.
```

O Parquet permanece como alternativa válida para evolução futura.

---

## 18. Invariantes do futuro gerador

O gerador das séries preditivas deverá validar:

```text
arquivos = 5.569

linhas totais = 1.124.938

202 predições por município

H1 = 52 observações por município
H2 = 51 observações por município
H3 = 50 observações por município
H4 = 49 observações por município

score dentro de [0, 1]

predicao == score >= threshold

threshold H1 = 0.187687
threshold H2 = 0.190783
threshold H3 = 0.167991
threshold H4 = 0.157138

nenhuma chave preditiva duplicada

todos os arrays alinhados

nenhum NaN

nenhum Infinity
```

---

## 19. Reprodutibilidade

A decisão está sustentada por:

```text
scripts/benchmark_serving_prediction.py
reports/audits/benchmark_serving_prediction.json
```

O benchmark deve permanecer reproduzível a partir do artefato final congelado.

---

## 20. Decisão congelada

Para a implementação inicial:

```text
Formato:
JSON compacto por horizonte

Granularidade:
1 arquivo por município

Quantidade:
5.569 arquivos

Estrutura interna:
h1
h2
h3
h4

Threshold:
armazenado uma vez por horizonte

Carregamento:
sob demanda

Consumo:
direto pelo frontend

Compressão de transporte:
gzip/Brotli conforme infraestrutura web

Parquet:
preservado como alternativa server-side futura
```

Essa decisão poderá ser revista somente se medições reais da aplicação
indicarem problema de deploy, cache, quantidade de arquivos, transferência ou
latência.