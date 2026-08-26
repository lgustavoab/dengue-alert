# 29 — Decisão de consulta das séries municipais na aplicação web

## 1. Objetivo

Este documento define como a aplicação web do Dengue Alert acessará as séries
municipais históricas e preditivas.

A decisão complementa o protocolo de integração definido em:

```text
docs/28_protocolo_integracao_frontend_serving.md
```

---

## 2. Contexto

A camada de serving possui duas coleções municipais de maior volume.

### Histórico

```text
data/serving/historical/municipality/series/
```

Quantidade:

```text
5.571 arquivos
```

Volume aproximado:

```text
131,88 MB
```

### Predição

```text
data/serving/prediction/municipality/series/
```

Quantidade:

```text
5.569 arquivos
```

Volume aproximado:

```text
67,11 MB
```

Total:

```text
11.140 arquivos
198,99 MB
```

Essas coleções não serão copiadas integralmente para:

```text
web/public/data/serving/
```

---

## 3. Decisão

As séries municipais permanecerão na fonte canônica:

```text
data/serving/
```

A aplicação Next.js realizará leitura sob demanda através de Route Handlers
internos.

Exemplo histórico:

```text
GET /api/serving/historical/municipality/3537305
```

O endpoint acima retorna somente a série histórica do município solicitado.

Esse mecanismo não representa uma API científica independente e não substitui
a camada de serving.

Sua função é somente fornecer ao frontend um contrato já produzido e validado
pelo pipeline Python.

---

## 4. Separação de responsabilidades

### Python

Responsável por:

```text
limpeza
normalização
zero-fill
integrações
engenharia de atributos
definição de targets
treinamento
thresholds
avaliação
geração dos contratos de serving
```

### Next.js server

Responsável por:

```text
validar o código IBGE solicitado
localizar o arquivo correspondente
validar estruturalmente o contrato
entregar o JSON solicitado
```

### Frontend

Responsável por:

```text
seleção territorial
filtros
formatação
visualização
estado da interface
```

O frontend não recalcula regras científicas.

---

## 5. Contrato histórico municipal

Formato:

```text
data/serving/historical/municipality/series/{codigo_ibge_7}.json
```

Estrutura:

```text
schema_version
codigo_ibge_7
count
data
```

O bloco `data` utiliza representação columnar:

```text
ano_epidemiologico[]
semana_epidemiologica[]
data_inicio_semana[]
casos_provaveis[]
incidencia_100mil[]
registro_sinan_presente[]
zero_preenchido[]
populacao[]
```

Todos os vetores devem possuir comprimento igual a `count`.

Cobertura normal:

```text
522 semanas
```

Boa Esperança do Norte:

```text
53 semanas
```

por possuir série somente a partir de 2025.

---

## 6. Contrato preditivo municipal

Formato:

```text
data/serving/prediction/municipality/series/{codigo_ibge_7}.json
```

Estrutura:

```text
schema_version
codigo_ibge_7
count
horizontes
```

Horizontes:

```text
h1
h2
h3
h4
```

Cada horizonte contém:

```text
count
threshold
data
```

O bloco `data` contém:

```text
ano_epidemiologico[]
semana_epidemiologica[]
data_inicio_semana[]
risco_elevado[]
target[]
score[]
predicao[]
```

Distribuição nacional esperada por município:

```text
H1 = 52
H2 = 51
H3 = 50
H4 = 49

Total = 202
```

---

## 7. Disponibilidade territorial

O histórico epidemiológico possui:

```text
5.571 unidades territoriais
```

O histórico de risco possui:

```text
5.569 disponíveis
2 indisponíveis
```

Os dois casos indisponíveis para histórico de risco são tratados conforme os
contratos de serving e não devem ser excluídos da consulta epidemiológica.

### Boa Esperança do Norte

```text
codigo_ibge_7 = 5101837
anos_disponiveis = 1
série epidemiológica = disponível
histórico de risco = indisponível
predição = indisponível
```

### Fernando de Noronha

```text
codigo_ibge_7 = 2605459
anos_disponiveis = 10
série epidemiológica = disponível
histórico de risco = indisponível
predição = indisponível
```

A interface deverá diferenciar:

```text
disponibilidade epidemiológica
disponibilidade de risco histórico
disponibilidade preditiva
```

---

## 8. Segurança de caminho

O Route Handler deverá aceitar somente códigos no formato:

```text
^[0-9]{7}$
```

A entrada do usuário nunca será usada diretamente como caminho arbitrário.

Isso impede navegação de diretórios e acesso a arquivos fora da coleção
municipal autorizada.

---

## 9. Validação do contrato

Antes da resposta ao navegador devem ser verificados:

```text
JSON válido
raiz como objeto
schema_version = 1.0
codigo_ibge_7 compatível com a solicitação
count válido
data columnar
comprimento uniforme dos vetores
comprimento igual a count
```

---

## 10. Carregamento sob demanda

O navegador não deverá baixar antecipadamente as 5.571 séries.

Fluxo esperado:

```text
usuário abre Histórico
        ↓
carrega índices territoriais
        ↓
usuário seleciona município
        ↓
GET /api/serving/historical/municipality/{codigo}
        ↓
uma única série é retornada
```

Ao trocar de município, somente a nova série necessária será solicitada.

---

## 11. Filtros territoriais

A página histórica utilizará a hierarquia:

```text
Região
  ↓
UF
  ↓
Município
  ↓
Ano epidemiológico
```

Os parâmetros serão persistidos na URL.

Exemplo:

```text
/historico?regiao=Sudeste&uf=35&municipio=3537305&ano=2024
```

Região e UF também restringirão as opções disponíveis no seletor de município.

---

## 12. Deployment

A implementação inicial pressupõe que:

```text
data/serving/
```

esteja acessível ao runtime do servidor Next.js.

Como `data/serving` não é versionado no Git, a estratégia definitiva de
distribuição desses artefatos deverá ser resolvida antes do deployment final.

Possibilidades futuras incluem:

```text
artefato de build
object storage
volume persistente
snapshot versionado específico para distribuição
```

Nenhuma dessas alternativas é congelada nesta etapa.

A decisão atual diz respeito ao contrato entre aplicação e serving, não à
infraestrutura final de hospedagem.