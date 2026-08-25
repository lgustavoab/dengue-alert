# 27 — Fechamento da arquitetura de serving da aplicação

## 1. Objetivo

Este documento registra o fechamento técnico da camada de **serving** do projeto Dengue Alert.

A camada de serving foi criada para estabelecer uma fronteira clara entre o pipeline científico executado em Python e a futura aplicação web.

Seu objetivo é disponibilizar contratos compactos, estáveis, validados e adequados ao consumo pelo frontend, sem exigir que o navegador carregue diretamente bases analíticas extensas, arquivos Parquet de modelagem ou registros brutos das fontes originais.

A arquitetura consolidada segue o fluxo:

```text
fontes oficiais
    ↓
pipeline científico em Python
    ↓
dados processados e artefatos de modelagem
    ↓
data/serving
    ↓
aplicação web
```

A aplicação web deverá consumir somente os contratos destinados ao produto, preservando a separação entre processamento científico e apresentação.

---

## 2. Princípios arquiteturais consolidados

A arquitetura de serving foi definida segundo os seguintes princípios:

| Princípio | Decisão |
|---|---|
| Processamento científico | Executado offline em Python |
| Aplicação | Next.js + React + TypeScript |
| API dedicada inicial | Não necessária |
| Comunicação inicial | Contratos estáticos em JSON |
| Dados brutos no navegador | Não |
| Grandes bases processadas no navegador | Não |
| Histórico | Dados observados e agregados |
| Predição | Resultados retrospectivos da avaliação final de 2025 |
| Série municipal | Carregamento sob demanda |
| Identificador territorial | `codigo_ibge_7` |
| Formato principal para frontend | JSON |
| Dados tabulares extensos | Permanecem no pipeline Python |
| Responsividade | Obrigatória no frontend |

A ausência inicial de uma API não impede sua adoção futura. A arquitetura foi estruturada de forma que uma camada de API possa posteriormente utilizar os mesmos contratos ou suas fontes processadas sem modificar a lógica científica já consolidada.

---

## 3. Estrutura consolidada

A camada foi organizada sob:

```text
data/serving/
├── metadata/
├── quality/
├── historical/
└── prediction/
```

Os domínios possuem responsabilidades diferentes.

### 3.1 Metadata

Contém informações necessárias para interpretação dos demais contratos, incluindo cobertura territorial e temporal.

### 3.2 Quality

Contém indicadores consolidados sobre preparação, cobertura e qualidade das fontes utilizadas no projeto.

Essa área permite que a aplicação apresente transparência metodológica sem expor registros brutos individualmente.

### 3.3 Historical

Contém dados observados e agregados utilizados pelas áreas históricas e analíticas da aplicação.

O histórico não representa previsão.

### 3.4 Prediction

Contém exclusivamente os resultados da avaliação final retrospectiva do modelo em 2025.

Esses arquivos não representam alertas operacionais em tempo real.

---

## 4. Contratos históricos

A camada histórica preserva o universo territorial consolidado do projeto.

A auditoria integrada confirmou:

| Indicador | Resultado |
|---|---:|
| Unidades territoriais | 5.571 |
| Município-semanas | 2.907.593 |
| Casos preservados | 16.294.913 |
| Período principal | 2016–2025 |

As séries municipais são armazenadas individualmente:

```text
data/serving/historical/municipality/series/{codigo_ibge_7}.json
```

Foram gerados:

```text
5.571 arquivos municipais
```

A maior parte das unidades possui 522 semanas.

Boa Esperança do Norte/MT possui somente 53 semanas, correspondentes a 2025, pois sua existência territorial no conjunto adotado começa nesse período.

O índice histórico utiliza o contrato:

```text
data/serving/historical/municipality/index.json
```

Nesse contrato, a coleção territorial encontra-se em:

```json
{
  "data": []
}
```

Essa estrutura é válida e permanece preservada.

---

## 5. Contratos preditivos

A camada preditiva representa a avaliação final retrospectiva realizada sobre 2025.

O modelo consolidado é:

```text
HistGradientBoostingClassifier
Modelo A — 23 variáveis epidemiológicas
Probabilidades brutas
Sem calibração adicional
```

O problema modelado é a probabilidade de ocorrência futura de **estado epidemiológico de risco elevado**, e não a quantidade futura de casos de dengue.

Os horizontes consolidados são:

| Horizonte | Threshold congelado | Observações |
|---|---:|---:|
| H1 | 0.187687 | 289.588 |
| H2 | 0.190783 | 284.019 |
| H3 | 0.167991 | 278.450 |
| H4 | 0.157138 | 272.881 |

Total:

```text
1.124.938 predições
```

O universo preditivo contém:

```text
5.569 municípios
```

Cada município possui 202 registros distribuídos da seguinte forma:

```text
H1 = 52
H2 = 51
H3 = 50
H4 = 49
```

As séries são armazenadas em:

```text
data/serving/prediction/municipality/series/{codigo_ibge_7}.json
```

O contrato escolhido organiza diretamente os dados por horizonte:

```json
{
  "schema_version": "1.0",
  "codigo_ibge_7": "3537305",
  "count": 202,
  "horizontes": {
    "h1": {
      "count": 52,
      "threshold": 0.187687,
      "data": {}
    },
    "h2": {},
    "h3": {},
    "h4": {}
  }
}
```

O índice preditivo utiliza:

```text
data/serving/prediction/municipality/index.json
```

e sua coleção territorial encontra-se em:

```json
{
  "count": 5569,
  "items": []
}
```

Os índices histórico e preditivo possuem schemas diferentes, mas ambos são contratos válidos e explicitamente suportados pela auditoria integrada.

---

## 6. Relação territorial entre histórico e predição

A auditoria integrada confirmou que o universo preditivo é subconjunto do universo histórico.

```text
Histórico: 5.571
Predição : 5.569
Diferença: 2
```

As duas unidades existentes somente no domínio histórico são:

| Código IBGE | Unidade | Motivo |
|---|---|---|
| `2605459` | Fernando de Noronha/PE | Não integra o universo climático/modelado final |
| `5101837` | Boa Esperança do Norte/MT | Série disponível apenas em 2025, sem histórico anterior suficiente para construção do alvo |

Nenhuma unidade preditiva encontra-se ausente do histórico.

Essa diferença é intencional e não deve ser corrigida artificialmente no frontend.

---

## 7. Semântica dos resultados preditivos

Os campos preditivos devem manter a seguinte interpretação:

| Campo | Significado |
|---|---|
| `risco_elevado` | Estado observado na semana de origem |
| `target` | Estado observado no futuro correspondente ao horizonte |
| `score` | Probabilidade bruta estimada pelo modelo para risco elevado futuro |
| `threshold` | Limiar congelado do horizonte |
| `predicao` | Resultado de `score >= threshold` |

Uma predição positiva não significa necessariamente um novo alerta antecipado.

O conceito de **early warning** ocorre quando:

```text
risco_elevado == false
e
predicao == true
```

Portanto, o frontend deve distinguir visual e semanticamente:

```text
estado atual observado
probabilidade futura
classificação futura
alerta antecipado
```

---

## 8. Restrições de comunicação no produto

A interface não deverá apresentar o `score` como previsão da quantidade futura de casos.

Exemplos inadequados:

```text
"Serão previstos 350 casos."
"O modelo prevê 1.200 casos de dengue."
```

O modelo atual não foi desenvolvido para essa finalidade.

A comunicação correta deve utilizar conceitos como:

```text
probabilidade de risco elevado
classificação de risco elevado futuro
horizonte de 1 a 4 semanas
resultado retrospectivo de 2025
```

Também não deverão ser criadas arbitrariamente categorias como:

```text
baixo
moderado
alto
crítico
```

Os thresholds atualmente congelados definem somente a classificação binária utilizada na avaliação científica.

Caso futuramente sejam criadas faixas visuais adicionais, elas deverão possuir definição metodológica independente e documentada.

---

## 9. Separação entre histórico e predição

A aplicação deverá preservar uma divisão explícita entre dados observados e resultados de modelagem.

### Histórico

Pode apresentar:

- evolução de casos;
- incidência;
- sazonalidade;
- distribuição espacial;
- dinâmica histórica de risco;
- análises climáticas;
- séries municipais.

### Predição

Pode apresentar:

- probabilidade estimada;
- classificação futura;
- horizonte H1 a H4;
- threshold correspondente;
- estado observado da origem;
- target observado retrospectivamente;
- comparação com resultados reais de 2025.

A área preditiva deverá informar claramente que os resultados disponíveis atualmente correspondem à **avaliação retrospectiva de 2025**.

Eles não deverão ser apresentados como alertas atuais de 2026.

---

## 10. Estratégia de carregamento municipal

As séries municipais não são reunidas em um único JSON nacional.

O padrão adotado é:

```text
index.json
        ↓
seleção do município
        ↓
series/{codigo_ibge_7}.json
```

Esse desenho evita transferências nacionais desnecessárias.

No histórico foram produzidos 5.571 arquivos.

Na predição foram produzidos 5.569 arquivos.

O benchmark realizado antes da implementação confirmou que essa estratégia apresenta tamanho adequado para carregamento sob demanda pelo frontend.

Para as séries preditivas, o conjunto completo possui aproximadamente:

```text
67,11 MB
```

enquanto o arquivo municipal mediano possui aproximadamente:

```text
12,38 KB
```

---

## 11. Auditoria integrada

Foi criado:

```text
scripts/auditar_serving_integrado.py
```

O script percorre de forma integrada os contratos de serving e verifica:

```text
presença dos contratos obrigatórios
validade estrita dos JSONs
ausência de NaN e Infinity
schema_version
compatibilidade índice × séries
totais históricos
totais preditivos
relação territorial histórico × predição
thresholds congelados
regra score >= threshold
quantidade por horizonte
```

O resultado estruturado é gravado em:

```text
reports/audits/auditoria_serving_integrado.json
```

Resultado final:

```text
STATUS: APROVADO
```

A auditoria validou:

| Indicador | Resultado |
|---|---:|
| Contratos JSON | 11.164 |
| Tamanho total | 211,43 MB |
| Séries históricas | 5.571 |
| Município-semanas históricas | 2.907.593 |
| Casos preservados | 16.294.913 |
| Séries preditivas | 5.569 |
| Predições | 1.124.938 |
| H1 | 289.588 |
| H2 | 284.019 |
| H3 | 278.450 |
| H4 | 272.881 |

---

## 12. Validação automatizada

A arquitetura de serving foi acompanhada por testes automatizados ao longo de sua construção.

Após a inclusão dos testes específicos da auditoria integrada, a suíte completa atingiu:

```text
164 passed
```

Os testes incluem validações de:

```text
contratos de metadata e quality
agregados históricos
índices municipais
séries históricas municipais
benchmark histórico
contratos globais de prediction
benchmark preditivo
séries preditivas municipais
staging e promoção segura
JSON estrito
schemas distintos de índices
integridade territorial
auditoria integrada
```

Também foram aplicados Ruff e formatação automatizada sobre `src`, `scripts` e `tests`.

---

## 13. Fronteira entre pipeline e frontend

Com esta fase concluída, o frontend não deverá reproduzir regras científicas já consolidadas em Python.

Responsabilidades do pipeline:

```text
limpeza
normalização
agregação
engenharia de atributos
construção dos alvos
treinamento
avaliação
aplicação dos thresholds
agregações históricas
preparação dos contratos
auditoria
```

Responsabilidades do frontend:

```text
leitura dos contratos
seleção territorial
filtros
navegação
visualizações
mapas
gráficos
tabelas
tooltips
explicações
responsividade
estado da interface
```

O frontend não deverá recalcular o modelo, reconstruir alvos ou reinterpretar thresholds.

---

## 14. Diretrizes para o frontend

A próxima etapa poderá iniciar a aplicação Next.js + React + TypeScript.

O desenvolvimento deverá preservar desde o início:

```text
desktop
tablet
mobile
```

Gráficos, mapas, tabelas, controles e navegação deverão ser responsivos.

A interface deverá separar claramente três áreas conceituais:

```text
Histórico
Dados & Qualidade
Predição
```

Essa divisão acompanha diretamente os contratos já consolidados na camada de serving.

---

## 15. Estado final da Fase 13

A camada de serving encontra-se tecnicamente pronta para consumo pela aplicação.

Foram concluídos:

```text
definição arquitetural
contratos histórico/qualidade
agregados históricos
benchmark de séries históricas
séries municipais históricas
contrato de prediction
benchmark preditivo
contratos globais de prediction
séries municipais preditivas
validação territorial
auditoria integrada
testes automatizados
```

A camada preserva as principais invariantes científicas do projeto e impede que decisões de apresentação do frontend modifiquem silenciosamente o significado dos dados.

Com isso, a **Fase 13 — Arquitetura e Serving da Aplicação** é considerada:

```text
CONCLUÍDA
```

O próximo ciclo do projeto poderá ser dedicado à implementação da aplicação web.