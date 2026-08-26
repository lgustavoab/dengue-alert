# 31 — Protocolo do Dashboard Histórico da Aplicação Web

## 1. Objetivo

Este documento define a arquitetura analítica e os contratos de dados utilizados pela área Histórico da aplicação web do projeto Dengue Alert.

A Fase 14C tem como objetivo transformar a rota:

```text
/historico
```

em uma área analítica completa para exploração dos dados epidemiológicos históricos, da sazonalidade, da distribuição territorial, da dinâmica histórica de risco elevado e da relação exploratória entre clima e dengue.

A aplicação deve consumir exclusivamente contratos previamente preparados e validados pelo pipeline científico.

---

## 2. Princípio arquitetural

O fluxo adotado permanece:

```text
dados brutos
    ↓
pipeline científico Python
    ↓
data/serving
    ↓
camada TypeScript
    ↓
componentes React
```

A aplicação web não deve:

- recalcular a metodologia científica;
- redefinir o alvo de risco;
- recalcular thresholds;
- reconstruir agregações metodológicas a partir dos registros brutos;
- inferir resultados inexistentes nos contratos serving.

A aplicação pode realizar operações exclusivamente apresentacionais, como:

- filtrar registros já agregados;
- selecionar um território;
- selecionar um ano;
- selecionar uma variável;
- selecionar um horizonte ou lag;
- ordenar dados;
- calcular valores simples derivados de um contrato já validado para fins de exibição.

---

## 3. Período histórico

O período epidemiológico consolidado da aplicação é:

```text
2016–2025
```

A série nacional possui:

```text
522 semanas epidemiológicas
```

Os anos:

```text
2020
2025
```

possuem 53 semanas epidemiológicas no calendário adotado pelo projeto.

---

## 4. Contratos históricos disponíveis

Os contratos serving históricos utilizados na aplicação estão organizados em:

```text
data/serving/historical/
```

Os principais contratos globais são:

```text
historical/
├── panorama/
│   ├── annual.json
│   └── weekly.json
├── seasonality/
│   ├── national.json
│   └── regional.json
├── spatial/
│   ├── regions.json
│   ├── states.json
│   └── municipalities.json
├── risk_dynamics/
│   ├── weekly.json
│   ├── municipalities.json
│   └── episode_duration.json
├── climate/
│   ├── national_lags.json
│   └── regional_lags.json
└── municipality/
    ├── index.json
    └── series/
```

As séries individuais em:

```text
historical/municipality/series/
```

permanecem fora da sincronização pública em massa e são consultadas sob demanda por código IBGE.

---

## 5. Panorama epidemiológico

### 5.1 Panorama anual

Contrato:

```text
historical/panorama/annual.json
```

Quantidade esperada:

```text
10 registros
```

Um registro por ano epidemiológico entre 2016 e 2025.

O contrato permite apresentar:

- casos prováveis;
- incidência anual por 100 mil habitantes;
- população nacional;
- média semanal de casos;
- pico semanal;
- semana epidemiológica do pico;
- unidades territoriais com casos;
- participação do ano no total do período.

---

### 5.2 Panorama semanal

Contrato:

```text
historical/panorama/weekly.json
```

Quantidade esperada:

```text
522 registros
```

O contrato permite apresentar a evolução temporal nacional com:

- ano epidemiológico;
- semana epidemiológica;
- data de início;
- data de fim;
- casos prováveis;
- incidência nacional;
- unidades territoriais com casos;
- proporção de unidades com casos.

A série semanal nacional deve ser apresentada como dado histórico observado.

Ela não representa previsão.

---

## 6. Sazonalidade

### 6.1 Sazonalidade nacional

Contrato:

```text
historical/seasonality/national.json
```

Quantidade:

```text
53 semanas epidemiológicas
```

Para cada semana são fornecidos:

- anos disponíveis;
- média de casos;
- mediana de casos;
- mínimo;
- máximo;
- incidência média;
- incidência mediana;
- Q25;
- Q75;
- incidência mínima;
- incidência máxima.

A visualização deve deixar claro que esses valores resumem diferentes anos epidemiológicos.

---

### 6.2 Sazonalidade regional

Contrato:

```text
historical/seasonality/regional.json
```

Quantidade:

```text
265 registros
```

Estrutura:

```text
5 regiões × 53 semanas epidemiológicas
```

Regiões:

```text
Centro-Oeste
Nordeste
Norte
Sudeste
Sul
```

Quando uma região estiver selecionada, a aplicação pode utilizar diretamente a série regional correspondente.

Não é necessário reconstruir a sazonalidade regional a partir das séries municipais.

---

## 7. Análise espacial

### 7.1 Regiões

Contrato:

```text
historical/spatial/regions.json
```

Quantidade:

```text
5 registros
```

Campos disponíveis incluem:

- casos no período;
- população média;
- incidência média anual;
- incidência mediana anual;
- incidência máxima anual;
- ano da maior incidência;
- incidência no ano de pico;
- participação nos casos do período.

---

### 7.2 Unidades federativas

Contrato:

```text
historical/spatial/states.json
```

Quantidade:

```text
27 registros
```

O código da UF é tratado como identificador textual de dois dígitos.

Exemplo:

```text
São Paulo → "35"
```

A aplicação não deve converter esse identificador em medida numérica.

---

### 7.3 Municípios e unidades territoriais

Contrato:

```text
historical/spatial/municipalities.json
```

Quantidade:

```text
5.571 unidades territoriais
```

O contrato contém resumos espaciais consolidados por unidade territorial.

Ele pode ser utilizado em:

- rankings;
- tabelas;
- mapas;
- comparação territorial;
- seleção de territórios.

A série temporal detalhada de um município permanece no contrato individual consultado sob demanda.

---

## 8. Níveis territoriais da interface

A interface histórica trabalha com a hierarquia:

```text
Brasil
  ↓
Região
  ↓
UF
  ↓
Município
```

Nem todos os gráficos precisam estar disponíveis em todos os níveis.

A existência de um filtro territorial não autoriza a aplicação a inventar uma agregação inexistente.

---

## 9. Comportamento por nível territorial

### 9.1 Brasil

No recorte Brasil podem ser utilizados:

- panorama anual;
- panorama semanal;
- sazonalidade nacional;
- comparação entre regiões;
- dinâmica nacional de risco;
- clima nacional;
- duração global de episódios.

---

### 9.2 Região

No recorte regional podem ser utilizados diretamente:

- resumo espacial da região;
- sazonalidade regional;
- dinâmica regional de risco;
- clima regional;
- UFs e municípios pertencentes à região.

---

### 9.3 UF

No recorte por UF existe resumo espacial consolidado.

O contrato atual não fornece uma série temporal semanal ou sazonal específica por UF.

Portanto, a seleção isolada de uma UF não deve gerar artificialmente uma série temporal estadual.

A interface pode apresentar:

- resumo consolidado da UF;
- municípios pertencentes à UF;
- comparação municipal dentro da UF.

---

### 9.4 Município

Ao selecionar um município, a série histórica é consultada sob demanda:

```text
GET /api/serving/historical/municipality/{codigo}
```

O contrato permite apresentar:

- casos semanais;
- incidência semanal;
- população utilizada;
- semanas com registro SINAN;
- semanas preenchidas com zero;
- totais anuais derivados da série.

A dinâmica histórica de risco municipal pode ser combinada com o contrato:

```text
historical/risk_dynamics/municipalities.json
```

quando o município possuir histórico de risco disponível.

---

## 10. Dinâmica histórica de risco

O risco histórico utilizado na aplicação é o mesmo alvo metodológico definido e congelado no pipeline científico.

A aplicação não recalcula esse alvo.

---

### 10.1 Série semanal de risco

Contrato:

```text
historical/risk_dynamics/weekly.json
```

Quantidade:

```text
2.508 registros
```

Estrutura:

```text
Brasil         418 semanas
Centro-Oeste   418 semanas
Nordeste       418 semanas
Norte          418 semanas
Sudeste        418 semanas
Sul            418 semanas
```

O período elegível para a análise de risco começa posteriormente ao início da série epidemiológica porque o alvo depende de histórico anterior.

Campos principais:

- escala;
- grupo;
- ano epidemiológico;
- semana epidemiológica;
- unidades elegíveis;
- unidades em risco;
- proporção de unidades em risco;
- incidência acumulada de quatro semanas;
- limiar P90 mediano.

---

### 10.2 Dinâmica municipal de risco

Contrato:

```text
historical/risk_dynamics/municipalities.json
```

Quantidade:

```text
5.569 unidades
```

Campos disponíveis incluem:

- observações elegíveis;
- anos elegíveis;
- semanas em risco;
- proporção de semanas em risco;
- anos com risco;
- primeira semana de risco;
- última semana de risco;
- quantidade de episódios;
- duração média;
- duração mediana;
- duração máxima;
- episódios multianuais;
- recorrência multianual.

Boa Esperança do Norte/MT e Fernando de Noronha/PE não possuem histórico de risco disponível no contrato consolidado.

---

## 11. Duração dos episódios de risco

Contrato:

```text
historical/risk_dynamics/episode_duration.json
```

Resumo consolidado:

```text
episódios             54.269
semanas em risco     414.678
mínimo                     1
média                    7,64
P25                         3
mediana                     4
P75                         9
P90                        19
P95                        26
P99                        41
máximo                    110
```

A distribuição completa por duração também está disponível.

A interface deve evitar sugerir que a duração máxima representa um comportamento típico.

Mediana e intervalos percentílicos devem receber maior destaque interpretativo.

---

## 12. Clima e dengue

A análise climática histórica é exploratória e baseada em correlações municipais resumidas.

Ela não deve ser apresentada como evidência causal.

---

### 12.1 Variáveis climáticas

Variáveis presentes nos contratos:

```text
temperatura_media_c
umidade_relativa_media_pct
precipitacao_total_mm
```

---

### 12.2 Lags

Os lags disponíveis são:

```text
0
1
2
3
4
6
8 semanas
```

Os contratos não testam continuamente todas as defasagens possíveis.

Portanto, o maior valor observado entre os lags disponíveis não deve ser descrito como "lag ótimo" absoluto.

---

### 12.3 Clima nacional

Contrato:

```text
historical/climate/national_lags.json
```

Quantidade:

```text
21 registros
```

Estrutura:

```text
3 variáveis × 7 lags
```

---

### 12.4 Clima regional

Contrato:

```text
historical/climate/regional_lags.json
```

Quantidade:

```text
105 registros
```

Estrutura:

```text
5 regiões × 3 variáveis × 7 lags
```

---

## 13. Interpretação do clima

A aplicação pode apresentar:

- correlação média;
- correlação mediana;
- P10;
- P25;
- P75;
- P90;
- proporção de correlações positivas;
- proporção de correlações negativas;
- quantidade de municípios com correlação válida.

A aplicação não deve afirmar:

```text
"o clima causa dengue"
```

nem:

```text
"o lag X é o verdadeiro melhor lag"
```

A formulação adequada é:

```text
"associação histórica observada na análise exploratória"
```

---

## 14. Histórico versus Predição

As áreas Histórico e Predição permanecem conceitualmente separadas.

### Histórico

Representa:

- observações epidemiológicas;
- resumos espaciais;
- sazonalidade;
- risco histórico observado;
- associações climáticas históricas.

### Predição

Representa:

- avaliação retrospectiva do modelo em 2025;
- score probabilístico;
- classificação após threshold congelado;
- horizontes H1–H4.

Nenhum gráfico histórico deve ser rotulado como previsão.

---

## 15. Responsividade

Todas as visualizações da aplicação devem funcionar em:

```text
desktop
tablet
mobile
```

Requisitos:

- nenhum gráfico pode forçar scroll horizontal da página inteira;
- elementos largos podem utilizar scroll interno quando necessário;
- tooltips não devem depender exclusivamente de hover;
- filtros devem continuar utilizáveis em telas pequenas;
- textos interpretativos devem permanecer legíveis;
- tabelas devem ter comportamento responsivo explícito.

---

## 16. Estado da URL

Os filtros territoriais permanecem persistidos em query parameters.

Exemplo:

```text
/historico?regiao=Sudeste&uf=35&municipio=3537305&ano=2024
```

Filtros adicionais poderão ser persistidos quando fizer sentido analítico, evitando poluir a URL com estados puramente visuais.

---

## 17. Ordem de desenvolvimento

A Fase 14C será executada em:

```text
14C.1  Contratos TypeScript, readers e testes
14C.2  Panorama epidemiológico
14C.3  Análise territorial
14C.4  Dinâmica histórica de risco
14C.5  Clima e dengue
14C.6  Responsividade, UX e regressão
14C.7  Documentação e fechamento
```

---

## 18. Regra de implementação

Antes da criação de um componente visual novo:

1. deve existir contrato serving correspondente;
2. o contrato deve possuir tipo TypeScript;
3. deve existir reader server-side apropriado;
4. o contrato deve possuir teste automatizado;
5. somente depois o componente deve consumir o dado.

A regra mantém o fluxo:

```text
contrato
   ↓
tipo
   ↓
reader
   ↓
teste
   ↓
visualização
```

---

## 19. Resultado esperado da Fase 14C

Ao final da fase, a rota `/historico` deverá funcionar como um dashboard analítico completo capaz de responder, entre outras perguntas:

- como os casos de dengue evoluíram entre 2016 e 2025;
- quais anos apresentaram maior incidência;
- quais semanas epidemiológicas concentram historicamente maior incidência;
- como a sazonalidade varia entre regiões;
- como regiões, UFs e municípios se diferenciam;
- quantos municípios estiveram simultaneamente em risco elevado;
- com que frequência o risco elevado reaparece;
- quanto duram os episódios históricos de risco;
- como temperatura, umidade e precipitação se associaram historicamente à incidência em diferentes defasagens.

Essas respostas devem permanecer estritamente ancoradas nos contratos científicos produzidos pelo pipeline.