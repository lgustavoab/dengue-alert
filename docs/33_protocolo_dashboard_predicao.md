# Protocolo da Fase 14D — Dashboard de Predição

## 1. Objetivo

A Fase 14D tem como objetivo construir a interface de apresentação das previsões produzidas pelo modelo final do projeto Dengue Alert.

A página deverá permitir consultar, por município e semana de referência de 2025, a probabilidade estimada de ocorrência futura do estado de risco elevado nos horizontes de uma a quatro semanas.

A implementação deverá preservar integralmente a semântica científica dos contratos de serving e do protocolo experimental já congelado.

A rota principal da fase é:

```text
/predicao
```

---

## 2. Natureza retrospectiva dos resultados

Os resultados disponíveis pertencem ao teste final retrospectivo de 2025.

Portanto, a aplicação não deverá utilizar expressões como:

```text
risco atual
alerta atual
previsão de hoje
situação atual de 2026
```

A interface deverá comunicar explicitamente que:

> As previsões apresentadas foram produzidas retrospectivamente para 2025 e são utilizadas para avaliar como o sistema teria se comportado naquele período.

Os resultados não representam alertas operacionais atuais.

---

## 3. Modelo final

O modelo final utilizado é:

```text
HistGradientBoostingClassifier
```

O conjunto de atributos corresponde ao Modelo A, composto por variáveis epidemiológicas.

As probabilidades utilizadas são as probabilidades brutas produzidas pelo modelo.

Não foi adotada calibração adicional.

O desenvolvimento do modelo utilizou o período:

```text
2018–2024
```

O teste final foi realizado exclusivamente em:

```text
2025
```

Os dados de 2025 não foram utilizados para selecionar o modelo final ou redefinir os thresholds.

---

## 4. Semântica dos campos de predição

Os contratos de serving estabelecem a seguinte semântica:

### `score`

Probabilidade bruta produzida pelo modelo para ocorrência futura do estado de risco elevado.

O `score` não representa número previsto de casos de dengue.

### `threshold`

Limiar de decisão definido durante a validação do modelo.

A decisão binária é calculada por:

```text
score >= threshold
```

### `predicao`

Resultado binário da aplicação do threshold:

```text
true  = ALERTA
false = SEM ALERTA
```

### `risco_elevado`

Estado observado de risco elevado na semana de origem.

Ele representa a situação epidemiológica observada no momento utilizado como referência para a previsão.

### `target`

Estado futuro realmente observado no horizonte correspondente.

Esse campo permite comparar retrospectivamente:

```text
o que o modelo previu
versus
o que realmente ocorreu
```

### `early_warning`

O cenário de alerta antecipado corresponde a:

```text
risco_elevado == false
AND
predicao == true
```

Ou seja, o município ainda não estava em estado de risco elevado na semana de referência, mas o modelo emitiu alerta para uma semana futura.

---

## 5. Horizontes H1–H4

A interface deverá explicar de forma permanente o significado dos horizontes.

```text
H1 = 1 semana à frente
H2 = 2 semanas à frente
H3 = 3 semanas à frente
H4 = 4 semanas à frente
```

H1, H2, H3 e H4 não são categorias de gravidade.

Eles representam apenas a distância temporal entre a semana de referência e a semana futura avaliada.

---

## 6. Thresholds congelados

Cada horizonte possui seu próprio limiar de alerta.

Os thresholds oficiais são:

```text
H1 = 0,187687
H2 = 0,190783
H3 = 0,167991
H4 = 0,157138
```

Em formato percentual:

```text
H1 = 18,7687%
H2 = 19,0783%
H3 = 16,7991%
H4 = 15,7138%
```

Esses valores permanecerão congelados na aplicação.

O frontend não poderá recalcular, otimizar ou redefinir thresholds com base nos resultados de 2025.

---

## 7. Regra oficial de alerta

A classificação oficial do sistema permanece binária:

```text
ALERTA
SEM ALERTA
```

Exemplo conceitual:

```text
H1 · 1 semana à frente

Probabilidade prevista
31,4%

Limiar de alerta
18,77%

31,4% >= 18,77%

ALERTA
```

A aplicação deverá explicar que o limiar de alerta é o valor mínimo de probabilidade necessário para que aquele horizonte seja classificado como ALERTA.

---

## 8. Ausência de categorias artificiais

O experimento científico não definiu categorias como:

```text
Baixo
Moderado
Alto
Crítico
```

Essas faixas não deverão ser inventadas pelo frontend.

A intensidade da probabilidade poderá ser utilizada visualmente para diferenciar previsões, mas a decisão metodológica continuará sendo apenas:

```text
ALERTA / SEM ALERTA
```

Exemplo:

```text
Município A
score = 21%
ALERTA

Município B
score = 48%
ALERTA

Município C
score = 82%
ALERTA
```

Os três municípios possuem a mesma classe binária, porém probabilidades diferentes.

---

## 9. Cobertura da avaliação retrospectiva

O contrato global de avaliação contém:

```text
1.124.938 previsões
5.569 municípios
ano de avaliação = 2025
status = APROVADO
```

A distribuição por horizonte é:

| Horizonte | Município-semanas | Semanas de origem |
| --- | ---: | ---: |
| H1 | 289.588 | 52 |
| H2 | 284.019 | 51 |
| H3 | 278.450 | 50 |
| H4 | 272.881 | 49 |

A redução do número de semanas ocorre porque horizontes mais longos necessitam de observação futura disponível dentro do período de avaliação.

---

## 10. Frequência de alertas gerais

No teste retrospectivo de 2025, o modelo produziu:

| Horizonte | Predições positivas | Proporção aproximada |
| --- | ---: | ---: |
| H1 | 44.500 | 15,37% |
| H2 | 46.975 | 16,54% |
| H3 | 55.358 | 19,88% |
| H4 | 70.312 | 25,77% |

Portanto, a maioria das município-semanas não foi classificada como ALERTA.

A aplicação não deverá pressupor que thresholds abaixo de 20% impliquem automaticamente grande maioria de municípios alertados.

---

## 11. Alertas antecipados

O recorte de maior interesse operacional é o cenário de `early_warning`.

Nesse cenário, o município ainda não estava em risco elevado na semana de origem.

Os contratos registram:

| Horizonte | Observações elegíveis | Alertas antecipados | Proporção |
| --- | ---: | ---: | ---: |
| H1 | 252.867 | 10.440 | 4,13% |
| H2 | 248.006 | 15.083 | 6,08% |
| H3 | 243.247 | 21.766 | 8,95% |
| H4 | 238.547 | 36.367 | 15,25% |

Essa análise demonstra que o sistema de alerta antecipado representa um subconjunto específico das previsões positivas.

---

## 12. Baseline de persistência

A avaliação inclui uma baseline de persistência.

Essa baseline assume que o estado futuro continuará igual ao estado observado na semana de origem.

No cenário de `early_warning`, a persistência apresenta:

```text
recall = 0
F1 = 0
```

nos quatro horizontes.

Isso ocorre porque uma estratégia baseada exclusivamente em persistir o estado atual não consegue antecipar uma nova entrada em risco quando o município ainda está fora do estado de risco elevado.

Essa comparação é relevante para demonstrar o valor da abordagem preditiva utilizada pelo projeto.

---

## 13. Desempenho por horizonte

O desempenho do modelo diminui conforme aumenta a distância temporal da previsão.

Por exemplo:

```text
H1
PR-AUC ≈ 0,922
ROC-AUC ≈ 0,976
```

Enquanto em:

```text
H4
PR-AUC ≈ 0,546
ROC-AUC ≈ 0,841
```

Essa redução é esperada, pois previsões mais distantes envolvem maior incerteza.

A futura interface de desempenho deverá permitir compreender essa diferença sem sugerir que todos os horizontes possuem a mesma capacidade preditiva.

---

## 14. Série municipal

Cada município possui um contrato individual de predição.

Estrutura conceitual:

```text
municipality/series/{codigo_ibge_7}.json
```

O contrato contém:

```text
schema_version
codigo_ibge_7
count
horizontes
```

Cada horizonte contém:

```text
count
threshold
data
```

Os dados de cada horizonte contêm:

```text
ano_epidemiologico
semana_epidemiologica
data_inicio_semana
risco_elevado
target
score
predicao
```

---

## 15. Penápolis como referência de validação

O município de Penápolis, código IBGE:

```text
3537305
```

possui:

```text
H1 = 52 observações
H2 = 51 observações
H3 = 50 observações
H4 = 49 observações
```

Os thresholds do contrato municipal são idênticos aos thresholds globais congelados.

Penápolis será utilizado como um dos cenários de regressão durante o desenvolvimento do Dashboard de Predição.

---

## 16. Contratos globais utilizados

A camada de serving da predição contém:

```text
prediction/
├── evaluation/
│   ├── overview.json
│   └── by_horizon.json
├── metadata/
│   └── model.json
└── municipality/
    ├── index.json
    └── series/
```

Os contratos globais fornecem:

- metadados do modelo;
- thresholds;
- semântica;
- restrições de interpretação;
- cobertura da avaliação;
- métricas por horizonte;
- avaliação de early warning;
- comparação com baseline;
- índice dos municípios disponíveis.

---

## 17. Integração frontend

A Fase 14D.1 adicionou suporte tipado ao contrato:

```text
prediction/evaluation/by_horizon.json
```

Foram adicionados tipos para:

- matriz de confusão;
- métricas de avaliação;
- métricas de early warning;
- modelo final;
- baseline de persistência;
- avaliação por horizonte;
- contrato completo `PredictionByHorizonContract`.

Também foi criado o reader:

```text
getPredictionByHorizon()
```

---

## 18. Testes dos contratos de predição

Foi criada uma suíte específica:

```text
web/src/lib/serving/prediction-contracts.test.ts
```

Ela valida, entre outros pontos:

- avaliação retrospectiva aprovada;
- ano de referência 2025;
- número total de previsões;
- número de municípios;
- thresholds congelados;
- semanas disponíveis por horizonte;
- modelo final;
- ausência de calibração;
- semântica de `score`;
- semântica de `predicao`;
- semântica de `target`;
- restrição contra faixas artificiais;
- métricas H1;
- alertas antecipados;
- comportamento da baseline;
- índice municipal;
- disponibilidade de Penápolis.

Ao final da Fase 14D.1:

```text
Test Files  9 passed
Tests       93 passed
```

O ESLint terminou sem erros ou warnings.

O build de produção do Next.js também foi aprovado.

---

## 19. Estrutura planejada do Dashboard de Predição

A implementação seguirá as seguintes subfases:

### 14D.1 — Contratos e semântica

Concluída neste protocolo.

### 14D.2 — Seleção da previsão

Implementar:

- seleção de município;
- seleção da semana de referência;
- persistência dos filtros na URL;
- carregamento da série municipal sob demanda.

### 14D.3 — Resultado H1–H4

Implementar:

- quatro horizontes;
- score;
- threshold;
- ALERTA / SEM ALERTA;
- explicações de H1–H4;
- explicação do threshold;
- explicação da probabilidade.

### 14D.4 — Avaliação retrospectiva municipal

Implementar:

- comparação previsão × target;
- estado observado na origem;
- evolução dos scores ao longo de 2025;
- interpretação retrospectiva.

### 14D.5 — Desempenho do modelo

Implementar:

- métricas por horizonte;
- early warning;
- comparação com baseline de persistência;
- explicações acessíveis das métricas selecionadas.

### 14D.6 — UX e qualidade

Realizar:

- responsividade;
- acessibilidade;
- estados de loading e erro;
- regressão;
- testes;
- lint;
- build.

### 14D.7 — Fechamento

Registrar:

- decisões;
- limitações;
- evidências;
- testes;
- documentação final da fase.

---

## 20. Regras de interface

A interface deverá respeitar as seguintes regras:

1. sempre indicar que os resultados são retrospectivos de 2025;

2. explicar H1, H2, H3 e H4 em linguagem acessível;

3. utilizar "Limiar de alerta" como expressão principal e, quando útil, apresentar "threshold" entre parênteses;

4. explicar que `score` corresponde à probabilidade estimada de risco elevado;

5. nunca interpretar `score` como número previsto de casos;

6. manter ALERTA / SEM ALERTA como classificação oficial;

7. não criar faixas baixo/moderado/alto/crítico;

8. diferenciar visualmente probabilidade e decisão;

9. permitir comparação entre previsão e estado futuro observado;

10. separar semanticamente o Dashboard Histórico do Dashboard de Predição;

11. preservar os thresholds congelados;

12. não recalcular métricas ou decisões metodológicas no frontend quando os contratos já fornecerem o resultado oficial.

---

## 21. Critérios de aceite da Fase 14D.1

A subfase é considerada concluída porque:

- [x] os contratos globais de predição foram inventariados;
- [x] a série municipal foi inspecionada;
- [x] a semântica de `score` foi confirmada;
- [x] a semântica de `predicao` foi confirmada;
- [x] a semântica de `risco_elevado` foi confirmada;
- [x] a semântica de `target` foi confirmada;
- [x] os thresholds H1–H4 foram confirmados;
- [x] a natureza retrospectiva de 2025 foi confirmada;
- [x] as restrições de interpretação foram confirmadas;
- [x] a avaliação por horizonte foi incorporada ao frontend;
- [x] o contrato `by_horizon.json` foi tipado;
- [x] foi criado reader dedicado;
- [x] foi criada suíte específica de testes;
- [x] 93 testes foram aprovados;
- [x] o lint foi aprovado;
- [x] o build de produção foi aprovado.

---

## 22. Encerramento

A Fase 14D.1 estabelece o contrato científico, semântico e técnico do Dashboard de Predição.

A partir deste ponto, a interface poderá ser construída sem reinterpretar os resultados do modelo ou criar categorias não validadas.

A próxima etapa é a Fase 14D.2, dedicada à seleção do município, semana de referência e carregamento da série retrospectiva correspondente.