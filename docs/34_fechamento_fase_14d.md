# Fechamento da Fase 14D — Dashboard de Predição

## 1. Objetivo da fase

A Fase 14D teve como objetivo construir o Dashboard de Predição do projeto Dengue Alert a partir dos contratos de serving produzidos e validados nas etapas anteriores.

A rota principal da fase é:

```text
/predicao
```

A interface permite consultar, por município e semana epidemiológica de referência de 2025, como o modelo final avaliou retrospectivamente a probabilidade de ocorrência futura do estado de risco elevado nos horizontes de uma a quatro semanas.

A implementação preserva a semântica científica congelada no protocolo experimental e não transforma a saída do modelo em previsão de número futuro de casos.

---

## 2. Natureza retrospectiva dos resultados

Todos os resultados apresentados pertencem ao teste final retrospectivo de 2025.

A interface comunica explicitamente que:

- os resultados representam como o sistema teria se comportado em 2025;
- os dados não correspondem a alertas operacionais atuais;
- a página não apresenta risco atual de 2026;
- a consulta é utilizada para avaliação retrospectiva do modelo.

Expressões como:

```text
risco atual
alerta atual
previsão de hoje
situação atual de 2026
```

não são utilizadas para descrever as previsões do dashboard.

---

## 3. Modelo e semântica preservados

O modelo final utilizado é:

```text
HistGradientBoostingClassifier
```

O conjunto de atributos corresponde ao Modelo A, composto por variáveis epidemiológicas.

A interface preserva os seguintes significados:

### `score`

Probabilidade bruta produzida pelo modelo para ocorrência futura do estado de risco elevado.

O `score` não representa número previsto de casos de dengue.

### `threshold`

Limiar de decisão definido durante a validação.

A regra oficial é:

```text
score >= threshold
```

### `predicao`

Resultado binário oficial:

```text
true  = ALERTA
false = SEM ALERTA
```

### `risco_elevado`

Estado observado de risco elevado na semana de origem.

### `target`

Estado futuro realmente observado no horizonte correspondente.

### `early_warning`

Cenário em que:

```text
risco_elevado == false
AND
predicao == true
```

Ou seja, o município ainda não estava em estado de risco elevado na semana de referência, mas o modelo emitiu alerta para o horizonte futuro avaliado.

---

## 4. Horizontes H1–H4

A página explica de forma permanente que:

```text
H1 = 1 semana à frente
H2 = 2 semanas à frente
H3 = 3 semanas à frente
H4 = 4 semanas à frente
```

Esses horizontes representam distância temporal.

Eles não representam categorias de gravidade.

A interface não cria classificações artificiais como:

```text
Baixo
Moderado
Alto
Crítico
```

A decisão metodológica permanece exclusivamente:

```text
ALERTA
SEM ALERTA
```

---

## 5. Thresholds congelados

Os thresholds oficiais preservados na aplicação são:

```text
H1 = 0,187687
H2 = 0,190783
H3 = 0,167991
H4 = 0,157138
```

Em formato percentual aproximado exibido ao usuário:

```text
H1 = 18,77%
H2 = 19,08%
H3 = 16,80%
H4 = 15,71%
```

O frontend não recalcula, otimiza ou redefine esses valores com base no teste de 2025.

Também não recalcula a decisão binária quando o contrato já fornece o campo oficial `predicao`.

---

## 6. Seleção da consulta

A consulta retrospectiva foi implementada com filtros para:

- região;
- unidade federativa;
- município;
- semana epidemiológica de referência.

Os filtros são persistidos na URL.

Exemplo:

```text
/predicao?regiao=Sudeste&uf=35&municipio=3537305&semana=49
```

O estado da consulta pode ser recarregado ou compartilhado diretamente pela URL.

A aplicação também normaliza parâmetros inconsistentes.

Foram validados casos em que:

- semana é informada sem município;
- município é informado sem região e UF;
- região e UF contradizem o município;
- município não existe no índice preditivo;
- semana é inválida;
- semana contém valor não numérico.

A interface remove ou corrige parâmetros incompatíveis sem produzir resultado falso.

---

## 7. Carregamento municipal sob demanda

As séries municipais de predição não são carregadas integralmente no navegador.

A aplicação consulta apenas o município selecionado por meio da Route Handler:

```text
/api/serving/prediction/municipality/[codigo]
```

Esse desenho evita transportar para o cliente todo o conjunto nacional de previsões.

O contrato municipal contém:

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

E o bloco `data` contém:

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

## 8. Cobertura da avaliação retrospectiva

A avaliação global utilizada pela interface contém:

```text
1.124.938 previsões
5.569 municípios
ano de avaliação = 2025
status = APROVADO
```

Distribuição por horizonte:

| Horizonte | Município-semanas | Semanas de origem |
| --- | ---: | ---: |
| H1 | 289.588 | 52 |
| H2 | 284.019 | 51 |
| H3 | 278.450 | 50 |
| H4 | 272.881 | 49 |

A redução da cobertura nos horizontes mais longos decorre da necessidade de existir observação futura correspondente ainda dentro da janela de avaliação de 2025.

---

## 9. Cards de resultado H1–H4

Para cada horizonte, a interface apresenta:

- distância temporal;
- probabilidade estimada de risco elevado;
- limiar de alerta;
- comparação entre `score` e `threshold`;
- classificação oficial `ALERTA` ou `SEM ALERTA`.

A leitura principal segue a lógica:

```text
Probabilidade de risco elevado
Limiar de alerta
score >= threshold
ALERTA
```

ou:

```text
score < threshold
SEM ALERTA
```

Probabilidade e decisão são visualmente diferenciadas.

---

## 10. Tratamento de horizontes indisponíveis

As semanas finais de 2025 possuem menos horizontes disponíveis.

Por exemplo, na semana epidemiológica 52:

```text
H1 = disponível
H2 = indisponível
H3 = indisponível
H4 = indisponível
```

Nesses casos, a aplicação utiliza a mensagem:

```text
Indisponível nesta semana
```

A interface não fabrica:

- probabilidade igual a zero;
- `SEM ALERTA`;
- ponto inexistente no gráfico;
- valor derivado fora do contrato.

---

## 11. Avaliação retrospectiva municipal

A página permite comparar retrospectivamente:

```text
o que o modelo previu
versus
o que realmente ocorreu
```

A interface apresenta:

- decisão do modelo;
- `target` observado no horizonte correspondente;
- estado `risco_elevado` observado na semana de origem;
- interpretação retrospectiva da combinação.

O `target` é tratado como estado futuro observado, e não como "alerta real".

Também é preservada a diferença entre:

```text
estado observado na origem
```

e:

```text
resultado futuro observado
```

---

## 12. Evolução dos scores

Foi implementado gráfico de evolução dos scores ao longo de 2025.

A visualização permite selecionar individualmente:

```text
H1
H2
H3
H4
```

O gráfico apresenta:

- score semanal;
- threshold congelado do horizonte;
- semana selecionada;
- ponto correspondente à semana de referência quando disponível.

O eixo de probabilidade permanece na escala de 0% a 100%.

Não foi aplicado smoothing ou interpolação entre semanas, evitando sugerir valores que não foram produzidos pelo modelo.

Em telas pequenas, o gráfico utiliza rolagem horizontal interna em vez de reduzir artificialmente a legibilidade da série.

---

## 13. Desempenho global do modelo

A página contém seção específica de desempenho global do teste retrospectivo de 2025.

Para cada horizonte são apresentados:

- número de observações;
- prevalência;
- PR-AUC;
- ROC-AUC;
- recall;
- precisão;
- F1;
- acurácia balanceada;
- threshold do modelo.

Exemplos de desempenho:

```text
H1
PR-AUC ≈ 0,922
ROC-AUC ≈ 0,976
```

```text
H4
PR-AUC ≈ 0,546
ROC-AUC ≈ 0,841
```

A interface explica que, de modo geral, a tarefa se torna mais difícil conforme aumenta a antecedência temporal.

Essa seção é global e não representa desempenho específico do município selecionado.

---

## 14. Glossário de métricas

Foram adicionadas explicações acessíveis para métricas selecionadas.

### PR-AUC

Resume o desempenho da relação precisão–recall ao longo dos limiares e é especialmente informativa quando o estado positivo é menos frequente.

### ROC-AUC

Resume a capacidade de discriminar observações positivas e negativas ao longo de diferentes limiares.

### Acurácia balanceada

Considera o desempenho nas duas classes de forma equilibrada, reduzindo a influência do desbalanceamento.

### Comparação entre horizontes

Explica que H1–H4 representam diferentes distâncias temporais e que horizontes mais longos tendem a apresentar maior dificuldade preditiva.

Também são explicados recall, precisão e F1 no contexto de alerta antecipado.

---

## 15. Alerta antecipado

A interface contém uma seção dedicada ao cenário de `early_warning`.

Nesse recorte, a semana de origem ainda está fora do estado de risco elevado.

Os contratos utilizados registram:

| Horizonte | Observações elegíveis | Alertas antecipados | Proporção |
| --- | ---: | ---: | ---: |
| H1 | 252.867 | 10.440 | 4,13% |
| H2 | 248.006 | 15.083 | 6,08% |
| H3 | 243.247 | 21.766 | 8,95% |
| H4 | 238.547 | 36.367 | 15,25% |

A interface também informa a quantidade de novas entradas em risco realmente observadas em cada horizonte.

O objetivo dessa seção é avaliar a capacidade do modelo de sinalizar uma futura entrada em risco quando o município ainda não se encontrava nesse estado na semana de referência.

---

## 16. Comparação com baseline de persistência

O Dashboard de Predição apresenta a comparação entre o modelo final e a baseline de persistência.

A persistência assume que o estado futuro permanecerá igual ao estado observado na origem.

No cenário `early_warning`, a baseline possui:

```text
recall = 0
F1 = 0
```

nos quatro horizontes.

Isso ocorre porque, quando a origem está fora do estado de risco elevado, persistir o estado atual não consegue antecipar uma nova entrada futura em risco.

A interface não inventa quantidade de alertas para a baseline quando o contrato utiliza valor nulo; nesses casos, é apresentado:

```text
—
```

---

## 17. Frequência de alertas gerais

No teste retrospectivo de 2025, o modelo produziu aproximadamente:

| Horizonte | Predições positivas | Proporção |
| --- | ---: | ---: |
| H1 | 44.500 | 15,37% |
| H2 | 46.975 | 16,54% |
| H3 | 55.358 | 19,88% |
| H4 | 70.312 | 25,77% |

A interface não interpreta thresholds inferiores a 20% como indicação automática de que a maioria das município-semanas recebeu alerta.

---

## 18. Penápolis como cenário de regressão

Penápolis foi utilizado como um dos principais cenários de regressão.

Código IBGE:

```text
3537305
```

Cobertura:

```text
H1 = 52 observações
H2 = 51 observações
H3 = 50 observações
H4 = 49 observações
```

Foram utilizados especialmente:

```text
SE49
```

para validar os quatro horizontes disponíveis, e:

```text
SE52
```

para validar o comportamento dos horizontes finais indisponíveis.

---

## 19. Acessibilidade

A Fase 14D incorporou melhorias específicas de acessibilidade.

Foram implementados:

- `role="status"` e `aria-live="polite"` para mensagens dinâmicas de carregamento;
- `role="alert"` para mensagens de erro;
- respeito a `prefers-reduced-motion`;
- indicação explícita ao Next.js de que o `scroll-behavior: smooth` é intencional;
- foco visual no botão de limpeza dos filtros;
- combobox municipal com semântica ARIA;
- `aria-activedescendant` para a opção ativa;
- lista de municípios identificada como `listbox`;
- navegação por teclado no campo Município.

O combobox foi validado com:

```text
ArrowDown
ArrowUp
Enter
Escape
Tab
Shift + Tab
```

Também foi confirmada busca sem acentuação, como:

```text
Penapolis
```

para localizar:

```text
Penápolis — São Paulo
```

---

## 20. Responsividade

A interface foi validada manualmente nos seguintes viewports:

```text
Desktop   1440 × 900
Notebook  1024 × 768
Tablet     768 × 1024
Mobile     390 × 844
```

Foram verificados:

- filtros;
- cards H1–H4;
- avaliação retrospectiva;
- gráfico de scores;
- desempenho global;
- alerta antecipado;
- navegação;
- ausência de overflow horizontal da página;
- rolagem horizontal interna do gráfico quando necessária;
- reorganização de grids e cards em telas menores.

A regressão visual não identificou problema bloqueante.

---

## 21. Estados de loading e erro

A seleção da previsão mantém estados distintos de:

```text
idle
loading
ready
error
```

Foram preservadas mensagens específicas para:

- carregamento do índice territorial;
- falha ao carregar municípios;
- carregamento da série municipal;
- falha ao carregar a avaliação retrospectiva do município.

Os filtros são desabilitados quando o estado da consulta ainda não permite interação válida.

---

## 22. Validação das URLs

Foram validados manualmente os seguintes cenários:

1. `/predicao`;
2. semana sem município;
3. município sem região e UF;
4. região e UF contraditórias em relação ao município;
5. município inexistente;
6. semana inexistente;
7. semana não numérica;
8. semana epidemiológica 52;
9. recarga da página com filtros persistidos;
10. abertura da URL completa em nova aba.

A aplicação normalizou corretamente os parâmetros e não exibiu previsões falsas.

---

## 23. Validação da Route Handler

Foram realizados testes diretos da rota municipal de predição.

### Município válido

```text
/api/serving/prediction/municipality/3537305
```

Resultado:

```text
200 OK
```

### Código estruturalmente inválido

```text
/api/serving/prediction/municipality/123
```

Resultado:

```text
400 Bad Request
```

### Código com sete dígitos sem série disponível

```text
/api/serving/prediction/municipality/9999999
```

Resultado:

```text
404 Not Found
```

A Route Handler distingue corretamente código inválido de série municipal inexistente.

---

## 24. Componentes implementados

Entre os principais componentes da Fase 14D estão:

```text
web/src/components/prediction/
├── prediction-selection.tsx
├── prediction-results.tsx
├── prediction-retrospective.tsx
├── prediction-score-evolution.tsx
├── prediction-performance.tsx
└── prediction-early-warning.tsx
```

Também foram utilizados ou ampliados componentes compartilhados de filtros:

```text
web/src/components/filters/
├── filter-bar.tsx
├── select-filter.tsx
├── municipality-combobox.tsx
└── filters.module.css
```

A rota principal foi integrada em:

```text
web/src/app/predicao/page.tsx
```

---

## 25. Contratos de serving utilizados

A camada de predição consome contratos organizados em:

```text
data/serving/prediction/
├── evaluation/
│   ├── overview.json
│   └── by_horizon.json
├── metadata/
│   └── model.json
└── municipality/
    ├── index.json
    └── series/
        └── {codigo_ibge_7}.json
```

A aplicação utiliza esses contratos como fonte oficial.

O frontend não recalcula resultados metodológicos que já tenham sido produzidos e congelados pelo pipeline.

---

## 26. Testes automatizados

Ao final da Fase 14D, a suíte web apresentou:

```text
Test Files  10 passed (10)
Tests       105 passed (105)
```

As suítes incluem:

- contratos históricos;
- contratos de predição;
- integração com serving;
- acesso às séries municipais;
- formatadores;
- utilitários históricos;
- utilitários territoriais;
- utilitários de clima;
- utilitários de risco histórico;
- utilitários de seleção da predição.

O ESLint terminou sem erros ou warnings.

O build de produção do Next.js também foi aprovado.

---

## 27. Rotas verificadas no build

O build final manteve as principais páginas:

```text
/
/dados-qualidade
/historico
/predicao
```

E as Route Handlers:

```text
/api/serving/territories
/api/serving/historical/municipality/[codigo]
/api/serving/prediction/municipality/[codigo]
```

As páginas principais permanecem compatíveis com prerenderização estática e as séries municipais são carregadas dinamicamente sob demanda.

---

## 28. Commits principais da fase

A implementação foi consolidada incrementalmente nos seguintes commits da branch `feat/prediction-dashboard`:

```text
648d5b0 feat: add prediction dashboard contracts
881b904 feat: add prediction municipality and week selection
c68185d feat: add prediction horizon result cards
85569fb feat: add retrospective prediction evaluation
49adc50 feat: add prediction model performance
75a1ee6 fix: improve prediction dashboard accessibility
```

A implementação incremental permitiu validar cada subfase antes de avançar.

---

## 29. Limitações conhecidas

Ao final da Fase 14D permanecem as seguintes limitações conhecidas:

1. os resultados são exclusivamente retrospectivos para 2025 e não constituem um sistema operacional de alerta em tempo real;

2. o modelo não prevê número futuro de casos de dengue;

3. os horizontes finais do ano possuem cobertura progressivamente menor porque o resultado futuro precisa estar disponível dentro da janela retrospectiva;

4. a série municipal é carregada a partir dos contratos de serving locais durante o desenvolvimento; a estratégia definitiva de disponibilização desses arquivos no deploy permanece para etapa posterior;

5. o modelo utiliza o conjunto de atributos epidemiológicos do Modelo A; a conclusão de que variáveis climáticas não produziram ganho preditivo relevante no protocolo avaliado não deve ser interpretada como ausência de influência do clima sobre a dengue;

6. as probabilidades exibidas são probabilidades brutas do modelo, sem calibração adicional;

7. melhorias adicionais de acessibilidade mais avançada ainda podem ser incorporadas futuramente, especialmente para experiências assistivas mais detalhadas em visualizações gráficas.

Essas limitações não impedem o funcionamento do Dashboard de Predição no escopo definido para a Fase 14D.

---

## 30. Critérios de aceite

A Fase 14D é considerada concluída porque:

- [x] os contratos e a semântica científica foram integrados ao frontend;
- [x] a natureza retrospectiva de 2025 está explicitamente comunicada;
- [x] município e semana de referência podem ser selecionados;
- [x] os filtros são persistidos e normalizados pela URL;
- [x] a série municipal é carregada sob demanda;
- [x] os horizontes H1–H4 são apresentados corretamente;
- [x] `score`, threshold e decisão binária são diferenciados;
- [x] ALERTA / SEM ALERTA permanece a classificação oficial;
- [x] não foram criadas categorias artificiais de gravidade;
- [x] horizontes indisponíveis não recebem valores inventados;
- [x] previsão e `target` podem ser comparados retrospectivamente;
- [x] o estado observado na origem é apresentado separadamente;
- [x] a evolução dos scores de 2025 foi implementada;
- [x] o desempenho global por horizonte foi incorporado;
- [x] PR-AUC, ROC-AUC e acurácia balanceada possuem explicações acessíveis;
- [x] o cenário de `early_warning` foi incorporado;
- [x] a baseline de persistência foi comparada ao modelo;
- [x] a interface foi validada em desktop, notebook, tablet e mobile;
- [x] o combobox municipal possui navegação por teclado;
- [x] estados de loading e erro possuem tratamento acessível;
- [x] URLs inválidas e contraditórias foram testadas;
- [x] respostas 200, 400 e 404 da Route Handler foram validadas;
- [x] 105 testes automatizados foram aprovados;
- [x] o lint terminou limpo;
- [x] o build de produção foi aprovado;
- [x] a regressão manual não identificou problema bloqueante;
- [x] o repositório foi encerrado com working tree limpa após o commit da Fase 14D.6.

---

## 31. Encerramento

A Fase 14D transforma os resultados do modelo final em uma interface retrospectiva, navegável e metodologicamente consistente.

O Dashboard de Predição permite compreender:

- a probabilidade estimada de risco elevado;
- a decisão binária do modelo;
- os thresholds específicos por horizonte;
- a diferença entre previsão e resultado futuro observado;
- a evolução dos scores ao longo de 2025;
- o desempenho global do modelo;
- o comportamento no cenário de alerta antecipado;
- a comparação com uma baseline simples de persistência.

Ao mesmo tempo, a interface preserva as principais restrições científicas do projeto:

- não prevê número futuro de casos;
- não apresenta resultados de 2025 como alerta atual;
- não cria categorias artificiais de gravidade;
- não redefine thresholds;
- não recalcula decisões metodológicas já fornecidas pelos contratos.

Com isso, a Fase 14D é considerada encerrada e o Dashboard de Predição passa a compor a aplicação web do Dengue Alert de forma consistente com o protocolo científico definido anteriormente.
