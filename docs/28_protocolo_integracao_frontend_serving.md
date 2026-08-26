# 28 — Protocolo de integração entre serving e frontend

## 1. Objetivo

Este documento define como a aplicação web do Dengue Alert consumirá a camada de
serving produzida pelo pipeline Python.

A integração deve preservar a separação entre:

```text
pipeline científico
        ↓
data/serving
        ↓
sincronização controlada
        ↓
web/public/data/serving
        ↓
Next.js
```

A camada `data/serving` permanece como fonte canônica dos contratos destinados à
aplicação.

O frontend não deve alterar, reconstruir ou reinterpretar regras científicas
consolidadas pelo pipeline.

---

## 2. Fonte canônica

A fonte oficial dos dados da aplicação permanece:

```text
data/serving/
```

Esse diretório é derivado pelo pipeline Python e não representa código-fonte da
aplicação.

Entre seus domínios estão:

```text
metadata/
quality/
historical/
prediction/
```

---

## 3. Diretório de consumo do frontend

Os contratos estáticos selecionados para consumo direto pela aplicação serão
sincronizados para:

```text
web/public/data/serving/
```

Esse diretório é:

```text
derivado
reproduzível
não canônico
ignorado pelo Git
```

Portanto, alterações manuais dentro dele não devem ser realizadas.

Qualquer atualização deve ser feita a partir de `data/serving` pelo script de
sincronização.

---

## 4. Estratégia inicial

A camada completa de serving possui aproximadamente:

```text
211,43 MB
```

As séries municipais correspondem à maior parte desse volume:

```text
Histórico
5.571 arquivos
131,88 MB

Predição
5.569 arquivos
67,11 MB
```

Total aproximado das séries municipais:

```text
198,99 MB
```

Por esse motivo, a primeira integração do frontend não realizará cópia integral
dessas séries.

A sincronização inicial inclui somente contratos globais, agregados e índices
municipais.

O volume resultante é de aproximadamente:

```text
12,44 MB
```

---

## 5. Contratos sincronizados

### Metadata

```text
metadata/temporal_coverage.json
metadata/territories.json
```

### Quality

```text
quality/climate_coverage.json
quality/overview.json
quality/population_coverage.json
quality/sinan_pipeline.json
quality/territorial_coverage.json
```

### Historical

```text
historical/climate/national_lags.json
historical/climate/regional_lags.json

historical/municipality/index.json

historical/panorama/annual.json
historical/panorama/weekly.json

historical/risk_dynamics/episode_duration.json
historical/risk_dynamics/municipalities.json
historical/risk_dynamics/weekly.json

historical/seasonality/national.json
historical/seasonality/regional.json

historical/spatial/municipalities.json
historical/spatial/regions.json
historical/spatial/states.json
```

### Prediction

```text
prediction/evaluation/by_horizon.json
prediction/evaluation/overview.json
prediction/metadata/model.json
prediction/municipality/index.json
```

Total esperado:

```text
24 contratos
```

---

## 6. Contratos excluídos desta etapa

Não são copiados nesta etapa:

```text
historical/municipality/series/*.json
prediction/municipality/series/*.json
```

Esses conjuntos possuem:

```text
5.571 séries históricas
5.569 séries preditivas
11.140 arquivos no total
```

A política definitiva para consulta municipal será tratada separadamente.

O objetivo é manter carregamento sob demanda sem transferir ou duplicar o
universo nacional inteiro desnecessariamente.

---

## 7. Manifesto da sincronização

O processo de sincronização deverá gerar:

```text
web/public/data/serving/manifest.json
```

O manifesto registrará:

```text
schema_version
status
quantidade de contratos
tamanho total
arquivos sincronizados
tamanho individual
SHA-256
arquivos deliberadamente excluídos
```

Isso permitirá verificar que os assets utilizados pelo frontend correspondem
exatamente aos contratos produzidos pelo pipeline.

---

## 8. Validações obrigatórias

Antes da cópia, cada contrato deve apresentar:

```text
arquivo existente
JSON válido
objeto na raiz
schema_version = 1.0
ausência de NaN
ausência de Infinity
```

Após a cópia devem ser validados:

```text
quantidade de arquivos
caminhos esperados
SHA-256 origem × destino
manifesto
ausência de contratos inesperados
```

---

## 9. Promoção segura

A sincronização deve utilizar:

```text
serving.__staging__
serving.__backup__
```

Fluxo:

```text
1. criar staging limpo
2. validar e copiar contratos
3. validar staging completo
4. mover versão atual para backup
5. promover staging
6. remover backup após sucesso
```

Se a promoção falhar, a versão anterior deverá ser restaurada.

Isso evita que uma sincronização interrompida deixe o frontend com uma camada
de dados parcial.

---

## 10. Regras para o frontend

O frontend poderá:

```text
ler contratos
filtrar informações
selecionar municípios
organizar visualizações
formatar números e datas
controlar estados de interface
```

O frontend não deverá:

```text
refazer limpeza epidemiológica
reconstruir alvos
recalcular modelos
recalcular thresholds
alterar classificações
transformar score em previsão de casos
inventar faixas epidemiológicas não documentadas
```

---

## 11. Separação histórica e preditiva

Os domínios deverão permanecer semanticamente separados.

### Historical

Representa:

```text
dados observados
indicadores históricos
agregações epidemiológicas
sazonalidade
distribuição espacial
dinâmica histórica
relações climáticas
```

### Prediction

Representa:

```text
avaliação retrospectiva de 2025
score de risco elevado futuro
classificação binária futura
horizontes H1 a H4
targets observados retrospectivamente
```

Prediction não representa alerta operacional atual.

---

## 12. Estratégia de carregamento

Os contratos globais serão servidos como arquivos estáticos.

Exemplo:

```text
/data/serving/metadata/temporal_coverage.json
/data/serving/historical/panorama/annual.json
/data/serving/prediction/evaluation/overview.json
```

Cada página deverá solicitar somente os contratos necessários.

A existência de um arquivo em `public` não implica seu carregamento automático
pelo navegador.

Portanto, contratos históricos de alguns megabytes poderão permanecer
disponíveis estaticamente desde que sejam carregados apenas nas áreas que
realmente os utilizam.

---

## 13. Séries municipais

A estratégia para:

```text
historical/municipality/series/{codigo_ibge_7}.json
prediction/municipality/series/{codigo_ibge_7}.json
```

será definida em etapa própria.

Ela deverá garantir:

```text
consulta por código IBGE
carregamento sob demanda
ausência de transferência nacional desnecessária
compatibilidade com deployment
nenhuma alteração da semântica científica
```

---

## 14. Estado da integração

Com este protocolo, a Fase 14B inicia com uma fronteira explícita:

```text
data/serving
    = fonte canônica

scripts/sync_web_serving.py
    = sincronização controlada

web/public/data/serving
    = cópia derivada para consumo web

web/src/lib/serving
    = contratos e loaders TypeScript
```

A implementação TypeScript deverá ser construída sobre essa política.