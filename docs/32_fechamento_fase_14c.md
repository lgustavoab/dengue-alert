# Fechamento da Fase 14C — Dashboard Histórico

## 1. Objetivo da fase

A Fase 14C teve como objetivo transformar os contratos históricos já produzidos e validados pelo pipeline de Ciência de Dados em um dashboard web interativo, responsivo e metodologicamente consistente.

A implementação foi realizada sobre a fundação Next.js criada na Fase 14A e sobre a camada de integração com os contratos de serving consolidada na Fase 14B.

A área histórica da aplicação passou a disponibilizar análises epidemiológicas, territoriais, de dinâmica histórica de risco e de associação entre clima e dengue.

A implementação mantém separação explícita entre:

- dados históricos observados;
- análises derivadas desses dados;
- risco histórico utilizado para construção e interpretação do alvo;
- previsões produzidas pelo modelo de aprendizado de máquina.

Nenhum resultado histórico é apresentado ao usuário como previsão futura.

---

## 2. Escopo entregue

A rota principal da fase é:

```text
/historico
```

O dashboard histórico passou a suportar os seguintes níveis territoriais:

- Brasil;
- região;
- unidade federativa;
- município.

Os filtros são persistidos na URL quando aplicável, permitindo representar estados como:

```text
/historico?regiao=Sudeste
```

```text
/historico?regiao=Sudeste&uf=35
```

```text
/historico?regiao=Sudeste&uf=35&municipio=3537305
```

O filtro de ano epidemiológico também é utilizado nos recortes para os quais existe série temporal compatível.

A aplicação não reconstrói artificialmente análises para níveis territoriais que não estejam disponíveis nos contratos de serving.

---

## 3. Panorama epidemiológico

A primeira parte da implementação histórica consolidou a visualização da evolução epidemiológica.

Foram implementadas visualizações para:

- panorama anual;
- evolução semanal;
- incidência por 100 mil habitantes;
- sazonalidade epidemiológica nacional;
- sazonalidade epidemiológica regional;
- recortes municipais quando disponíveis.

A interface diferencia explicitamente casos absolutos de incidência.

Também foi adicionada explicação para a sigla:

```text
SE = Semana Epidemiológica
```

A aplicação considera a organização epidemiológica semanal já definida no pipeline de dados, sem reinterpretar datas diretamente no frontend.

---

## 4. Análise territorial

A análise territorial permite comparar diferentes escalas sem criar granularidades inexistentes.

### 4.1 Brasil

No nível nacional são disponibilizados:

- panorama epidemiológico nacional;
- comparação entre regiões;
- sazonalidade nacional;
- evolução temporal nacional;
- indicadores consolidados.

### 4.2 Região

Ao selecionar uma região, são disponibilizados:

- indicadores consolidados da região;
- comparação entre UFs pertencentes à região;
- sazonalidade regional;
- demais análises para as quais existe contrato regional.

### 4.3 Unidade federativa

Ao selecionar uma UF, a aplicação utiliza os indicadores territoriais consolidados disponíveis no serving.

Não é criada artificialmente uma série temporal estadual caso ela não exista nos contratos produzidos pelo pipeline.

### 4.4 Município

No nível municipal, a aplicação consulta a série histórica correspondente sob demanda por meio da Route Handler:

```text
/api/serving/historical/municipality/[codigo]
```

As séries municipais permanecem fora do carregamento global da página, evitando transportar todo o conjunto nacional de aproximadamente 2,9 milhões de município-semanas para o navegador.

---

## 5. Dinâmica histórica de risco

A Fase 14C incorporou uma área específica para interpretação do estado histórico de risco epidemiológico.

Esse risco não corresponde à previsão do modelo.

O estado histórico utilizado pelo projeto foi construído a partir da definição metodológica previamente congelada, baseada na incidência acumulada em quatro semanas e em um limiar sazonal histórico P90.

A interface reforça explicitamente:

> Risco histórico não é previsão.

Foram incorporadas análises de:

- proporção de semanas em risco;
- quantidade de semanas em risco;
- anos com risco;
- recorrência multianual;
- simultaneidade de municípios em risco;
- ranking municipal;
- duração dos episódios históricos de risco.

No agregado nacional, a distribuição de duração dos episódios utiliza os valores produzidos pelo pipeline, incluindo:

- 54.269 episódios;
- mediana de 4 semanas;
- P90 de 19 semanas;
- máximo observado de 110 semanas.

O dashboard não transforma esses valores em estimativas de duração futura.

---

## 6. Disponibilidade territorial do risco histórico

O contrato municipal de risco histórico contém unidades elegíveis segundo a metodologia utilizada para construção do alvo.

Municípios sem histórico elegível continuam disponíveis no panorama epidemiológico quando seus dados epidemiológicos existem.

A ausência de resumo de risco não é interpretada como ausência de dengue.

Ela é apresentada como indisponibilidade metodológica daquele indicador.

Esse comportamento é especialmente importante para unidades com particularidades na série histórica ou na elegibilidade temporal.

---

## 7. Clima e dengue

A Fase 14C também incorporou os resultados da análise exploratória de associação entre clima e dengue.

As variáveis representadas são:

```text
temperatura_media_c
umidade_relativa_media_pct
precipitacao_total_mm
```

Na interface, elas são apresentadas como:

- Temperatura média;
- Umidade relativa média;
- Precipitação total.

Os deslocamentos temporais avaliados são:

```text
0, 1, 2, 3, 4, 6 e 8 semanas
```

A medida principal apresentada nos gráficos é a correlação mediana entre municípios.

Também é apresentada a faixa interquartil Q25–Q75.

---

## 8. Interpretação dos lags climáticos

A interface inclui explicação explícita sobre o significado de lag.

Por exemplo:

> Lag 4 compara a condição climática observada quatro semanas antes com o indicador epidemiológico posterior.

A aplicação utiliza a expressão:

```text
maior associação observada
```

em vez de termos como:

```text
melhor lag
lag ideal
lag ótimo
```

Essa decisão evita atribuir caráter causal ou de otimização a uma análise correlacional.

Quando a maior associação observada ocorre no lag 8, a interface também informa que esse valor corresponde ao limite da janela analisada.

Portanto, o dashboard não conclui que oito semanas seja necessariamente o verdadeiro deslocamento de associação máxima.

---

## 9. Correlação e causalidade

A visualização climática contém ressalva explícita de que:

> Correlação não implica causalidade.

As associações apresentadas descrevem relações históricas entre variáveis climáticas e epidemiológicas.

Elas não demonstram que temperatura, umidade ou precipitação sejam, isoladamente, causas de aumentos posteriores de dengue.

Essa interpretação é consistente com a conclusão obtida durante a avaliação dos modelos: na representação e no protocolo avaliados pelo projeto, as variáveis climáticas não apresentaram ganho preditivo relevante em relação ao histórico epidemiológico utilizado pelo Modelo A.

Essa conclusão não significa ausência de influência climática sobre a dengue.

---

## 10. Disponibilidade territorial das análises climáticas

Os contratos históricos de clima disponibilizam resultados para:

- Brasil;
- cinco regiões brasileiras.

Não existem contratos equivalentes de correlação para:

- unidades federativas;
- municípios.

Por esse motivo, ao selecionar UF ou município, a aplicação informa explicitamente a indisponibilidade dessa análise.

Nenhuma correlação estadual ou municipal é calculada artificialmente pelo frontend.

---

## 11. Componentes implementados

Entre os principais componentes e utilitários desenvolvidos durante a Fase 14C estão:

```text
web/src/components/historical/
├── annual-panorama.tsx
├── weekly-evolution.tsx
├── seasonality-chart.tsx
├── territorial-analysis.tsx
├── municipality-panorama.tsx
├── historical-risk-analysis.tsx
├── historical-risk-section.tsx
├── historical-climate-analysis.tsx
├── historical-climate-section.tsx
└── historical-overview.tsx
```

Utilitários específicos:

```text
web/src/lib/
├── historical-chart-utils.ts
├── historical-territorial-utils.ts
├── historical-risk-utils.ts
└── historical-climate-utils.ts
```

A implementação permanece sem dependência externa de biblioteca de gráficos.

As visualizações foram construídas com SVG responsivo.

---

## 12. Contratos históricos utilizados

A área histórica consome contratos produzidos previamente pelo pipeline e sincronizados para a camada web.

Entre eles estão contratos de:

- panorama anual;
- panorama semanal;
- sazonalidade nacional;
- sazonalidade regional;
- indicadores espaciais por região;
- indicadores espaciais por UF;
- indicadores espaciais municipais;
- dinâmica semanal de risco;
- resumo municipal de risco;
- duração dos episódios de risco;
- associações climáticas nacionais;
- associações climáticas regionais;
- índice territorial;
- séries municipais.

A aplicação não acessa diretamente os arquivos brutos do SINAN, IBGE ou ERA5-Land.

---

## 13. Separação entre Histórico e Predição

Uma decisão arquitetural central da Fase 14C foi preservar a separação semântica entre:

```text
Histórico
```

e:

```text
Predição
```

A rota `/historico` contém exclusivamente dados observados ou análises retrospectivas.

A probabilidade de risco futuro produzida pelo modelo pertence à rota:

```text
/predicao
```

O modelo final não prevê número futuro de casos.

Ele estima a probabilidade de ocorrência do estado de risco elevado nos horizontes H1, H2, H3 e H4.

Essa semântica não é antecipada nem misturada às visualizações históricas.

---

## 14. Responsividade

Os componentes históricos foram desenvolvidos para funcionamento em:

- desktop;
- tablet;
- dispositivos móveis.

Foram incluídos:

- media queries específicas;
- grids adaptáveis;
- controle de overflow;
- SVGs com `viewBox`;
- reorganização de cards em telas menores;
- campos de filtros capazes de reduzir sua largura;
- tratamento de textos e nomes territoriais maiores.

A regressão visual foi realizada nos principais níveis territoriais.

---

## 15. Acessibilidade básica

Foi realizada auditoria estática dos componentes históricos.

Resultado registrado:

```text
Media queries.............: 9
SVG role=img..............: 8
aria-label................: 12
Regras de overflow........: 16
Grids responsivos.........: 17
Avisos nao-previsao.......: 7
Explicacoes de SE.........: 20
Explicacoes de lag........: 2
Ressalvas de causalidade..: 3
```

Nenhum arquivo contendo SVG foi identificado sem `role="img"`.

Os gráficos também possuem descrições acessíveis por `aria-label`.

A acessibilidade completa da aplicação ainda pode receber refinamentos posteriores, especialmente para interação detalhada com pontos de gráficos em dispositivos sem ponteiro.

---

## 16. Testes automatizados

Ao final da Fase 14C, a suíte web apresentou:

```text
Test Files  8 passed (8)
Tests       81 passed (81)
```

As suítes incluem:

- integração com serving;
- validação dos contratos históricos;
- formatação;
- acesso às séries municipais;
- utilitários dos gráficos;
- utilitários territoriais;
- utilitários de risco histórico;
- utilitários de clima.

O ESLint terminou sem erros ou warnings.

O build de produção do Next.js também foi concluído com sucesso.

---

## 17. Rotas verificadas no build

O build final da fase manteve as seguintes rotas:

```text
/
 /dados-qualidade
 /historico
 /predicao
```

Além das Route Handlers:

```text
/api/serving/territories
/api/serving/historical/municipality/[codigo]
/api/serving/prediction/municipality/[codigo]
```

As páginas principais permaneceram compatíveis com prerenderização estática e as séries municipais são consultadas dinamicamente sob demanda.

---

## 18. Regressão final

A regressão da Fase 14C incluiu cenários representativos de:

- Brasil;
- Brasil com ano epidemiológico selecionado;
- região Sudeste;
- São Paulo;
- Penápolis;
- Penápolis com ano selecionado;
- Boa Esperança do Norte;
- Fernando de Noronha.

Também foram verificados os comportamentos responsivos dos principais recortes.

A regressão confirmou:

- funcionamento dos filtros;
- persistência dos filtros na URL;
- ausência de granularidades artificiais;
- separação entre histórico e previsão;
- tratamento de indisponibilidades metodológicas;
- responsividade dos gráficos;
- ausência de regressões detectadas pela suíte automatizada.

---

## 19. Limitações conhecidas

Ao final da fase permanecem como limitações conhecidas:

1. as séries municipais são acessadas a partir do armazenamento local do projeto durante o desenvolvimento; a estratégia definitiva de disponibilização desses arquivos no ambiente de deploy ainda deverá ser definida;

2. não existem séries semanais estaduais específicas no serving atual;

3. não existem correlações clima × dengue específicas para UF ou município;

4. os gráficos SVG utilizam recursos simples de interação e poderão receber melhorias futuras de acessibilidade e tooltips;

5. os componentes históricos maiores poderão ser refatorados em componentes menores futuramente, mas a refatoração não foi realizada no fechamento da fase para evitar introduzir regressões sem benefício funcional imediato.

Essas limitações não impedem o funcionamento do Dashboard Histórico no escopo definido para a Fase 14C.

---

## 20. Critérios de aceite

A Fase 14C é considerada concluída porque:

- [x] o panorama epidemiológico foi implementado;
- [x] a evolução temporal foi implementada;
- [x] a sazonalidade foi implementada;
- [x] os filtros territoriais controlam análises reais;
- [x] o recorte municipal funciona sob demanda;
- [x] a análise territorial foi implementada;
- [x] a dinâmica histórica de risco foi implementada;
- [x] risco histórico e previsão estão semanticamente separados;
- [x] a análise histórica de clima e dengue foi implementada;
- [x] correlação e causalidade são distinguidas na interface;
- [x] limitações de granularidade são respeitadas;
- [x] o dashboard é responsivo;
- [x] foi realizada auditoria estática de acessibilidade e responsividade;
- [x] foram executados 81 testes automatizados com sucesso;
- [x] o lint terminou limpo;
- [x] o build de produção foi aprovado;
- [x] a regressão final não deixou alterações pendentes no repositório.

---

## 21. Encerramento

A Fase 14C transforma os resultados históricos produzidos pelo pipeline científico em uma interface navegável e interpretável sem alterar a semântica dos dados ou produzir análises não sustentadas pelos contratos existentes.

Com isso, a aplicação passa a oferecer uma camada histórica completa que contextualiza:

- evolução da dengue;
- sazonalidade;
- diferenças territoriais;
- recorrência do risco;
- duração de episódios;
- associação histórica com variáveis climáticas.

Essa base fornece o contexto necessário para a próxima etapa da aplicação, dedicada à apresentação e interpretação das previsões produzidas pelo modelo de aprendizado de máquina.