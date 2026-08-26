# Protocolo da Fase 14E — Dashboard Geográfico de Predição

## 1. Objetivo

A Fase 14E tem como objetivo construir e validar uma visualização geográfica nacional dos resultados preditivos retrospectivos do projeto Dengue Alert.

A rota principal da fase é:

`/mapa`

A interface permite observar espacialmente, por município brasileiro, como o modelo final classificou cada combinação de:

- semana epidemiológica de referência de 2025;
- horizonte preditivo H1, H2, H3 ou H4.

A visualização é retrospectiva.

Ela não representa:

- risco atual;
- alerta atual;
- situação epidemiológica atual de 2026;
- previsão referente ao dia de acesso.

Ao fechamento técnico da implementação, a rota `/mapa` encontra-se funcional, integrada ao serving preditivo, à malha municipal e à navegação principal da aplicação.

---

## 2. Natureza retrospectiva

Todos os resultados preditivos exibidos no mapa pertencem ao teste final retrospectivo de 2025.

A aplicação comunica que:

- as previsões representam como o sistema teria se comportado em 2025;
- o mapa não representa risco atual;
- o mapa não representa alertas atuais de 2026;
- os resultados fazem parte da avaliação retrospectiva do modelo.

O ano de 2025 não foi utilizado para seleção do modelo nem para otimização dos thresholds.

---

## 3. Semântica científica preservada

O mapa utiliza os mesmos resultados científicos congelados no Dashboard de Predição.

### 3.1. `score`

O `score` representa a probabilidade bruta produzida pelo modelo para ocorrência futura do estado metodologicamente definido de risco elevado.

O `score`:

- não representa número futuro de casos;
- não representa incidência prevista;
- não representa probabilidade de uma quantidade específica de casos;
- não deve ser reinterpretado como previsão de contagem.

### 3.2. `threshold`

O `threshold` corresponde ao limiar de decisão definido durante a validação.

A regra metodológica oficial é:

`score >= threshold`

### 3.3. `predicao`

O campo `predicao` contém a classificação binária oficial produzida pelo pipeline:

- `true` = ALERTA;
- `false` = SEM ALERTA.

O frontend utiliza diretamente o campo oficial `predicao`.

O mapa não reconstrói a classificação a partir de `score` e `threshold` como fonte de decisão.

A relação entre esses campos pode ser utilizada para auditoria, mas não substitui a saída oficial servida.

---

## 4. Horizontes temporais

Os horizontes permanecem definidos como:

- H1 = 1 semana à frente;
- H2 = 2 semanas à frente;
- H3 = 3 semanas à frente;
- H4 = 4 semanas à frente.

H1, H2, H3 e H4 representam distância temporal.

Eles não representam gravidade.

Não são criadas categorias como:

- baixo;
- moderado;
- alto;
- muito alto;
- crítico.

A aplicação não possui thresholds metodológicos para essas categorias.

---

## 5. Thresholds congelados

Os thresholds oficiais permanecem:

- H1 = `0,187687`;
- H2 = `0,190783`;
- H3 = `0,167991`;
- H4 = `0,157138`.

Esses valores foram definidos antes da avaliação final de 2025.

A aplicação não poderá recalcular, otimizar, redefinir ou ajustar esses valores com base no teste final.

---

## 6. Cobertura territorial

A base territorial utilizada pelo projeto contém:

- 5.571 unidades territoriais municipais.

A avaliação preditiva contém:

- 5.569 municípios.

Portanto:

`5.571 geometrias - 5.569 municípios avaliados = 2 territórios sem avaliação preditiva`

Esses dois casos são semanticamente diferentes de:

`SEM ALERTA`

Eles são apresentados como:

`SEM AVALIAÇÃO`

A ausência de observação preditiva nunca é convertida em:

- `score = 0`;
- `predicao = false`;
- `SEM ALERTA`.

---

## 7. Fonte geográfica

A geometria municipal parte da:

`IBGE — Malha Municipal 2024`

Arquivo-fonte:

`data/raw/geography/ibge_municipios_2024/BR_Municipios_2024.shp`

A malha original possui:

- 5.573 feições;
- CRS EPSG:4674.

A fonte original permanece preservada.

A aplicação utiliza somente um asset derivado específico para visualização web.

---

## 8. Preparação territorial

A auditoria da malha original identificou uma geometria inválida:

`5007802 — Selvíria/MS`

Problema identificado:

`Hole lies outside shell`

A preparação oficial utiliza:

`make_valid(method="structure", keep_collapsed=False)`

Também são removidas exatamente duas feições que não fazem parte das 5.571 unidades territoriais adotadas pelo projeto:

- `4300001`;
- `4300002`.

Após a preparação:

- 5.571 municípios;
- 5.571 códigos únicos;
- 0 geometrias inválidas;
- 0 geometrias vazias.

---

## 9. Auditoria das estratégias geográficas

Foram avaliadas diferentes estratégias de simplificação e distribuição da geometria.

Entre elas:

- simplificação individual com GeoPandas;
- `simplify_coverage()`;
- Mapshaper com quantização;
- Mapshaper sem quantização;
- `clean`;
- `fix-geometry`;
- tolerâncias de 50 m a 2.000 m;
- divisão dos polígonos municipais por UF.

As alternativas foram comparadas quanto a:

- quantidade de municípios;
- preservação dos códigos IBGE;
- validade geométrica;
- cobertura topológica;
- arestas problemáticas;
- erro relativo de área;
- preservação de partes e anéis;
- tamanho bruto;
- tamanho gzip;
- viabilidade para carregamento web.

### 9.1. Simplificação individual descartada

A simplificação individual com GeoPandas reduziu o tamanho, porém rompeu a compatibilidade de diversas fronteiras compartilhadas.

Na tolerância de 100 m:

- vértices = 1.237.668;
- redução = 93,08%;
- GeoJSON gzip = 12,57 MiB;
- cobertura válida = não;
- feições com arestas problemáticas = 5.546.

Essa estratégia foi descartada.

### 9.2. `simplify_coverage()` descartado

A malha preparada não era reconhecida como cobertura topológica válida pela implementação utilizada.

Por esse motivo, `simplify_coverage()` não foi adotado.

### 9.3. Quantização descartada

Os experimentos mostraram que a quantização do TopoJSON introduzia invalidades adicionais.

Na combinação de 100 m com quantização:

- geometrias inválidas = 10;
- arestas problemáticas = 17.

Sem quantização, antes da correção definitiva da origem:

- geometrias inválidas = 1;
- arestas problemáticas = 2.

A quantização foi descartada.

### 9.4. `clean` e `fix-geometry` descartados

Operações adicionais de reparo após a simplificação não melhoraram o resultado.

O reparo territorial oficial passou a ocorrer antes da simplificação.

### 9.5. Tolerância de 250 m descartada

A tolerância de 250 m reduzia ainda mais o payload, porém provocava:

- maior erro de área;
- mais municípios acima de 1% de erro;
- perdas em geometrias multipartes;
- alterações excessivas em territórios pequenos.

A economia adicional não justificava a perda geométrica.

### 9.6. Polígonos originais por UF descartados

O benchmark dos 27 payloads encontrou aproximadamente:

- soma gzip = 125,06 MiB;
- mediana = 2,06 MiB por UF.

Como o TopoJSON nacional aprovado possui aproximadamente:

- 5,64 MiB gzip;

a divisão principal por UF foi descartada.

---

## 10. Estratégia geográfica aprovada

A estratégia definitiva utiliza:

- malha IBGE preparada;
- Mapshaper 0.7.55;
- Douglas-Peucker;
- `interval=100m`;
- `keep-shapes`;
- TopoJSON;
- `no-quantization`.

A versão do Mapshaper é explicitamente fixada em:

`0.7.55`

O fluxo conceitual é:

`malha IBGE → validação das 5.573 feições → validação do CRS → reparo de Selvíria → remoção de 4300001 e 4300002 → 5.571 unidades → Mapshaper 0.7.55 → Douglas-Peucker 100 m → keep-shapes → TopoJSON sem quantização → auditoria geométrica → auditoria de cobertura → promoção do asset`

---

## 11. Asset geográfico canônico

O asset final é produzido em:

`data/serving/geography/`

com:

- `municipalities.topojson`;
- `metadata.json`.

O TopoJSON é o asset geográfico canônico de serving.

A malha bruta do IBGE nunca é enviada diretamente ao navegador.

O asset aprovado apresenta:

- municípios = 5.571;
- códigos únicos = 5.571;
- inválidas em EPSG:4674 = 0;
- inválidas em EPSG:5880 = 0;
- geometrias vazias = 0;
- cobertura topológica = válida;
- arestas problemáticas = 0.

Os tipos geométricos permanecem restritos a:

- Polygon;
- MultiPolygon.

Peso aproximado:

- TopoJSON bruto = 16,27 MiB;
- TopoJSON gzip = 5,64 MiB.

---

## 12. Reprodutibilidade da geometria

O gerador geográfico foi executado repetidamente a partir da mesma fonte e dos mesmos parâmetros.

SHA-256 observado:

`08f602577f536d405e3c9b16a72608c7407e770694d636dadb9f996606ef56db`

A execução consecutiva produziu o mesmo SHA-256.

Isso confirma reprodutibilidade byte a byte para:

- mesma fonte;
- mesma preparação;
- Mapshaper 0.7.55;
- mesmos parâmetros.

O relatório versionável correspondente é:

`reports/audits/serving_geography.json`

---

## 13. Gerador geográfico definitivo

A geração do asset é realizada por:

`scripts/gerar_serving_geography.py`

O script concentra a lógica permanente necessária para:

- leitura da fonte IBGE;
- validação territorial;
- reparo da geometria conhecida;
- remoção das duas feições não adotadas;
- simplificação com Mapshaper;
- exportação TopoJSON;
- validação geométrica;
- validação topológica;
- geração dos metadados;
- promoção somente após aprovação das verificações.

Os scripts exploratórios utilizados durante a decisão arquitetural não fazem parte da solução permanente.

---

## 14. Sincronização da geometria com a aplicação web

A fonte canônica da geometria continua em:

`data/serving/geography/municipalities.topojson`

Para uso pelo navegador, foi implementado:

`scripts/sync_web_geography.py`

O script sincroniza o asset derivado para a área pública da aplicação web.

Destino utilizado pela interface:

`web/public/data/serving/geography/municipalities.topojson`

URL pública:

`/data/serving/geography/municipalities.topojson`

A sincronização da geometria permanece separada da infraestrutura de serving preditivo.

Os contratos nacionais de predição não são copiados para `web/public`.

---

## 15. Separação entre geometria e predição

Geometria e predição são contratos independentes.

A associação é feita por código IBGE municipal.

Conceitualmente:

`CD_MUN da geometria → codigo_ibge_7 do serving preditivo`

Essa arquitetura evita repetir os polígonos em cada semana e horizonte.

A geometria é carregada como estrutura territorial e reutilizada enquanto os recortes preditivos são alterados.

---

## 16. Fonte preditiva nacional

A fonte científica utilizada para o mapa é:

`data/processed/predicoes_avaliacao_final_2025.parquet`

Ela contém:

- 1.124.938 predições retrospectivas;
- 5.569 municípios;
- ano epidemiológico 2025;
- H1, H2, H3 e H4.

As séries municipais existentes não seriam adequadas para pintar simultaneamente o território nacional.

Não seria aceitável executar 5.569 requisições municipais a cada alteração de filtro.

Também não seria adequado transferir as 1.124.938 predições para o navegador de uma única vez.

Foi criado, portanto, um serving específico para consultas nacionais por semana e horizonte.

---

## 17. Benchmark do serving preditivo

O benchmark é executado por:

`scripts/benchmark_serving_prediction_map.py`

Relatório:

`reports/audits/benchmark_serving_prediction_map.json`

Foram comparadas duas representações principais.

### 17.1. Formato verboso

Resultado aproximado:

- total bruto = 78,55 MiB;
- total gzip = 13,47 MiB;
- arquivo mediano bruto = 397,70 KiB;
- arquivo mediano gzip = 68,38 KiB;
- maior arquivo gzip = 74,44 KiB.

### 17.2. Formato colunar

Resultado aproximado:

- total bruto = 38,86 MiB;
- total gzip = 11,71 MiB;
- arquivo mediano bruto = 196,52 KiB;
- arquivo mediano gzip = 59,61 KiB;
- maior arquivo gzip = 65,32 KiB.

Redução do formato colunar:

- bruto = 50,53%;
- gzip = 13,05%.

O formato colunar foi aprovado.

---

## 18. Serving preditivo definitivo

O gerador oficial é:

`scripts/gerar_serving_prediction_map.py`

O destino canônico é:

`data/serving/prediction/map/`

Estrutura:

- `index.json`;
- `h1/se01.json` até `h1/se52.json`;
- `h2/se01.json` até `h2/se51.json`;
- `h3/se01.json` até `h3/se50.json`;
- `h4/se01.json` até `h4/se49.json`.

Quantidade total:

- 202 contratos semana × horizonte;
- 1 `index.json`.

---

## 19. Contrato colunar aprovado

Cada recorte semana × horizonte possui estrutura equivalente a:

`schema_version`

`ano_epidemiologico`

`semana_epidemiologica`

`data_inicio_semana`

`horizonte`

`threshold`

`count`

e:

`data.codigo_ibge_7`

`data.score`

`data.predicao`

Os arrays são alinhados por posição.

Um código, score e predicao no mesmo índice pertencem ao mesmo município.

Os códigos municipais permanecem ordenados deterministicamente.

---

## 20. Campos do contrato nacional

O contrato nacional contém somente os campos necessários para a visualização espacial:

- `codigo_ibge_7`;
- `score`;
- `predicao`.

Não são duplicados nesse contrato:

- `target`;
- `risco_elevado`;
- `casos`;
- `incidência`.

Esses campos continuam disponíveis nas séries municipais quando necessários em outras superfícies da aplicação.

---

## 21. Cobertura temporal

A cobertura oficial do serving é:

- H1 = SE01 até SE52;
- H2 = SE01 até SE51;
- H3 = SE01 até SE50;
- H4 = SE01 até SE49.

Quantidade:

- H1 = 52 arquivos;
- H2 = 51 arquivos;
- H3 = 50 arquivos;
- H4 = 49 arquivos.

Total:

`202`

Nas semanas finais:

- SE49 → H1, H2, H3 e H4;
- SE50 → H1, H2 e H3;
- SE51 → H1 e H2;
- SE52 → H1.

A disponibilidade é obtida a partir das semanas registradas no `index.json`.

A interface não fabrica combinações ausentes.

---

## 22. Horizonte indisponível

Quando um horizonte não existe para determinada semana, a combinação não é interpretada como resultado epidemiológico.

Por exemplo:

`SE50 + H4`

não pode produzir:

- 0%;
- score 0;
- SEM ALERTA.

Na interface, os horizontes disponíveis são ajustados à semana selecionada.

Uma seleção incompatível recebida pela URL é normalizada de forma determinística.

Exemplo:

`/mapa?semana=52&horizonte=4`

é normalizado para:

`/mapa?semana=52&horizonte=1`

---

## 23. Índice preditivo

O arquivo:

`data/serving/prediction/map/index.json`

funciona como contrato de descoberta da cobertura temporal.

Ele registra:

- `schema_version`;
- status;
- natureza retrospectiva;
- ano epidemiológico;
- quantidade de municípios;
- quantidade total de predições;
- quantidade de arquivos;
- thresholds;
- semanas disponíveis por horizonte.

---

## 24. Serving HTTP

Foram implementadas as Route Handlers:

- `GET /api/serving/prediction/map`;
- `GET /api/serving/prediction/map/[horizonte]/[semana]`.

Exemplos:

- `/api/serving/prediction/map`;
- `/api/serving/prediction/map/1/20`;
- `/api/serving/prediction/map/4/49`.

Os valores aceitos para horizonte são:

- 1;
- 2;
- 3;
- 4.

As rotas leem diretamente:

`data/serving/prediction/map`

no ambiente server-side do Next.js.

Os 202 contratos não são copiados para `web/public`.

---

## 25. Cache HTTP

As Route Handlers utilizam:

`Cache-Control: public, max-age=3600, stale-while-revalidate=86400`

Como os resultados são retrospectivos e imutáveis durante a execução normal da aplicação, o cache reduz leituras e transferências redundantes.

---

## 26. Tratamento de erros HTTP

A API diferencia diferentes situações.

### 26.1. Seleção inválida

Exemplos:

- H5;
- SE53;
- semana não numérica.

Resposta:

- HTTP 400;
- `invalid_prediction_map_selection`.

### 26.2. Combinação temporal indisponível

Exemplo:

- H4 / SE50.

Resposta:

- HTTP 404;
- `prediction_map_unavailable`.

### 26.3. Erro interno

Resposta:

- HTTP 500;
- `prediction_map_slice_unavailable`.

---

## 27. Tipagem TypeScript

Foram criados tipos específicos em:

`web/src/lib/serving/prediction-map-types.ts`

Entre eles:

- `PredictionMapHorizon`;
- `PredictionMapData`;
- `PredictionMapContract`;
- `PredictionMapIndexHorizon`;
- `PredictionMapIndexContract`.

A tipagem mantém a nova superfície isolada e explícita.

---

## 28. Reader server-side

A leitura e validação dos contratos é realizada por:

`web/src/lib/serving/prediction-map-server.ts`

O reader valida:

- horizonte;
- semana epidemiológica;
- disponibilidade temporal;
- `schema_version`;
- ano epidemiológico;
- data de início da semana;
- threshold;
- quantidade de municípios;
- quantidade de elementos dos arrays;
- formato dos códigos IBGE;
- unicidade dos códigos;
- ordenação dos códigos;
- scores finitos;
- scores no intervalo `[0, 1]`;
- booleanos de predição;
- consistência entre score, threshold e predicao;
- estrutura do índice;
- cobertura temporal H1–H4.

---

## 29. Testes do serving preditivo

A suíte:

`web/src/lib/serving/prediction-map-server.test.ts`

verifica, entre outros pontos:

- índice retrospectivo de 2025;
- 202 recortes;
- 5.569 municípios;
- 1.124.938 predições;
- thresholds congelados;
- 52 semanas em H1;
- 51 semanas em H2;
- 50 semanas em H3;
- 49 semanas em H4;
- H1/SE20 com 687 alertas;
- H1/SE49 com 1.013 alertas;
- H4/SE20 com 1.223 alertas;
- rejeição de H4/SE50;
- rejeição de horizonte inválido;
- rejeição de semana epidemiológica inválida.

Também existe:

`web/src/lib/serving/prediction-map-route.test.ts`

para validar as Route Handlers e seus códigos HTTP.

---

## 30. Fundação da rota `/mapa`

A Fase 14E.3 estabeleceu a rota:

`/mapa`

A página possui:

- estado de semana epidemiológica;
- estado de horizonte;
- leitura do índice preditivo;
- normalização dos parâmetros;
- estados de carregamento;
- estados de erro;
- carregamento sob demanda do recorte nacional.

A política padrão adotada é:

- semana padrão = SE49;
- horizonte padrão = H1.

A escolha de SE49 permite iniciar em uma semana na qual H1, H2, H3 e H4 coexistem.

---

## 31. Política de URL

Os filtros temporais são representados na URL.

Estrutura:

`/mapa?semana=49&horizonte=1`

A normalização segue regras determinísticas.

Exemplos:

- semana inválida → SE49;
- horizonte inválido → H1;
- semana válida com horizonte indisponível → mantém a semana e normaliza o horizonte para H1.

Exemplos:

- SE50/H4 → SE50/H1;
- SE52/H4 → SE52/H1;
- SE49/H4 → permanece SE49/H4.

A seleção municipal é um estado de interação da interface.

Ela não é atualmente persistida como parâmetro da URL.

Essa decisão mantém o recorte temporal compartilhável e evita ampliar desnecessariamente a complexidade da fase.

---

## 32. Datas das semanas epidemiológicas

A interface passou a exibir o intervalo de datas correspondente à semana epidemiológica.

A âncora validada para 2025 é:

- SE01 inicia em 29/12/2024;
- SE49 inicia em 30/11/2025;
- SE52 inicia em 21/12/2025.

Exemplo de exibição:

`SE49 · 30/11 a 06/12/2025`

No painel municipal, o recorte apresenta:

- semana;
- horizonte;
- intervalo de datas;
- significado temporal do horizonte.

A função correspondente é implementada em:

`web/src/lib/map-week-dates.ts`

e possui testes próprios.

---

## 33. Biblioteca de renderização adotada

A solução cartográfica aprovada utiliza:

- `d3-geo` 3.1.1;
- `topojson-client` 3.1.0.

Tipos utilizados no desenvolvimento:

- `@types/d3-geo` 3.1.1;
- `@types/topojson-client` 3.1.5.

A aplicação não utiliza:

- mapas externos;
- tiles;
- Google Maps;
- Mapbox;
- Leaflet;
- servidor cartográfico dedicado.

A escolha preserva o princípio de menor complexidade.

---

## 34. Renderização geográfica

O TopoJSON é carregado e convertido para a estrutura necessária à renderização.

A lógica principal fica em:

- `web/src/lib/map-geography.ts`;
- `web/src/lib/map-rendering.ts`.

A renderização utiliza:

- SVG;
- `geoMercator`;
- `fitExtent`;
- `geoPath`.

A área lógica utilizada é:

- largura = 960;
- altura = 720.

São produzidos exatamente:

`5.571 paths SVG`

Cada path preserva o código IBGE municipal.

A geometria não é carregada novamente a cada mudança de semana ou horizonte.

---

## 35. Validação da malha no frontend

`web/src/lib/map-geography.test.ts`

valida a estrutura geográfica utilizada pelo frontend.

Entre os invariantes:

- exatamente 5.571 municípios;
- códigos IBGE únicos;
- códigos com sete dígitos;
- apenas Polygon ou MultiPolygon;
- rejeição de estruturas incompatíveis.

`web/src/lib/map-rendering.test.ts`

verifica:

- dimensões válidas;
- exatamente 5.571 paths;
- paths não vazios;
- ausência de valores numéricos inválidos;
- preservação de códigos municipais reais;
- determinismo da renderização para a mesma geometria.

---

## 36. Integração geografia × predição

A integração é implementada em:

`web/src/lib/map-prediction.ts`

A associação utiliza exclusivamente o código IBGE.

A lógica preserva:

- geometria;
- score;
- predicao oficial;
- estado sem avaliação.

O frontend não calcula novamente `predicao`.

O teste oficial H1/SE49 produz:

- ALERTA = 1.013;
- SEM ALERTA = 4.556;
- SEM AVALIAÇÃO = 2.

Fechamento:

`1.013 + 4.556 + 2 = 5.571`

Esse fechamento é protegido por testes automatizados.

---

## 37. Classificação visual

A classificação visual principal é:

- ALERTA;
- SEM ALERTA;
- SEM AVALIAÇÃO.

Não existe gradação de severidade criada a partir do score.

O mapa utiliza diferenciação visual entre os três estados, acompanhada de legenda textual.

Os dois territórios sem avaliação permanecem visualmente distintos de SEM ALERTA.

---

## 38. Legenda

A legenda apresenta:

- ALERTA;
- SEM ALERTA;
- SEM AVALIAÇÃO.

Quando o recorte está carregado, também são exibidas as quantidades correspondentes.

No recorte H1/SE49:

- ALERTA = 1.013;
- SEM ALERTA = 4.556;
- SEM AVALIAÇÃO = 2.

A legenda reflete exclusivamente estados metodologicamente existentes.

---

## 39. Identidade territorial

A identificação municipal utiliza:

`GET /api/serving/territories`

A validação do contrato utilizada pelo mapa é implementada em:

`web/src/lib/map-territories.ts`

O índice contém:

- 5.571 territórios;
- códigos IBGE;
- nome do município;
- UF;
- região;
- disponibilidade histórica;
- disponibilidade preditiva.

Entre os invariantes:

- 5.571 registros;
- 5.571 códigos únicos;
- 5.569 com predição disponível;
- 2 sem predição disponível.

---

## 40. Interação por hover

No desktop, passar o cursor sobre um município apresenta identificação contextual.

O cartão de hover inclui:

- município;
- UF;
- região;
- classificação quando disponível.

A interação utiliza delegação de eventos no SVG.

Não são criados 5.571 handlers React individuais.

Isso reduz o custo estrutural do componente.

---

## 41. Seleção municipal por clique

Ao clicar em um município:

- o código IBGE é identificado;
- o território é selecionado;
- o polígono recebe destaque visual;
- o painel municipal é preenchido.

A seleção permanece ativa quando a semana ou o horizonte são alterados.

Dessa forma:

- a geometria permanece;
- o município permanece selecionado;
- somente o recorte preditivo é atualizado.

---

## 42. Painel municipal

O painel exibe:

- município;
- UF;
- região;
- código IBGE;
- resultado preditivo oficial;
- semana epidemiológica;
- horizonte;
- intervalo de datas;
- significado temporal do horizonte;
- score;
- threshold;
- interpretação metodológica.

Exemplo de estrutura:

`Município selecionado`

`Penápolis · São Paulo`

`Sudeste · Código IBGE 3537305`

`Resultado preditivo`

`ALERTA ou SEM ALERTA`

`Recorte`

`SE49 · H1`

`30/11 a 06/12/2025`

`H1 · 1 semana à frente`

`Probabilidade de risco elevado`

`Limiar de alerta`

O painel não interpreta o score como quantidade futura de casos.

---

## 43. Município sem avaliação

Quando um território não possui resultado preditivo, o painel apresenta:

`Sem avaliação preditiva`

com explicação de que o território está presente na malha geográfica, mas não possui resultado no conjunto retrospectivo de avaliação.

Esse estado nunca é convertido em SEM ALERTA.

---

## 44. Busca municipal

Para melhorar a acessibilidade e a usabilidade em municípios de pequena área, foi criada uma busca municipal.

Lógica:

`web/src/lib/map-territory-search.ts`

A busca permite pesquisar por:

- nome do município;
- código IBGE.

A normalização ignora diferenças de acentuação.

Exemplo:

`penapolis`

encontra:

`Penápolis`

A busca também encontra:

`3537305`

como código IBGE de Penápolis.

---

## 45. Ordenação dos resultados da busca

A busca prioriza correspondências segundo uma estratégia determinística.

Entre as prioridades:

- código IBGE exato;
- nome exato;
- nome iniciado pela consulta;
- código iniciado pela consulta;
- nome contendo a consulta.

O limite padrão é de:

`8 resultados`

A lógica é protegida por:

`web/src/lib/map-territory-search.test.ts`

---

## 46. Busca acessível integrada

A interface implementa comportamento de combobox/listbox.

São suportados:

- clique;
- touch;
- ArrowDown;
- ArrowUp;
- Home;
- End;
- Enter;
- Escape.

A opção ativa é informada por atributos ARIA.

A busca oferece uma alternativa de teclado sem transformar os 5.571 polígonos em elementos focáveis.

Essa decisão evita:

`5.571 tab stops`

e preserva uma navegação razoável por teclado.

---

## 47. Persistência da seleção durante filtros

Quando um município é selecionado por:

- clique no mapa;
- busca municipal;

a seleção permanece enquanto o usuário altera:

- semana epidemiológica;
- horizonte.

O componente reaproveita o mesmo código IBGE para obter o novo resultado do recorte.

O município não precisa ser selecionado novamente após cada alteração.

---

## 48. Estado de atualização

Quando o usuário muda semana ou horizonte:

- a geometria permanece visível;
- o recorte preditivo anterior deixa de ser tratado como atual;
- a interface informa que a classificação está sendo atualizada;
- o novo contrato é carregado;
- o join é refeito;
- o mapa recebe a nova classificação.

A geometria nacional não é solicitada novamente.

---

## 49. Responsividade

A página foi validada em:

- desktop;
- tablet;
- mobile.

Em telas menores:

- a busca continua disponível;
- os resultados da busca permanecem utilizáveis;
- o painel municipal passa para organização adequada à largura;
- os cards de detalhe são reorganizados;
- o mapa permanece dentro da largura da página;
- não é exigida precisão de toque sobre pequenos municípios graças à busca.

---

## 50. Comportamento em dispositivos touch

Em dispositivos sem hover:

- o cartão de hover é ocultado;
- efeitos visuais de hover deixam de ser necessários;
- a seleção continua disponível por toque;
- a busca oferece mecanismo alternativo mais preciso.

---

## 51. Preferência por movimento reduzido

O CSS considera:

`prefers-reduced-motion: reduce`

Quando essa preferência está ativa, transições visuais não essenciais são removidas.

---

## 52. Acessibilidade textual

O mapa não depende exclusivamente de cor.

A interface fornece informação textual em:

- legenda;
- busca;
- painel municipal;
- resultado preditivo;
- estado sem avaliação;
- controles de semana;
- controles de horizonte;
- textos metodológicos;
- estados de carregamento;
- estados de erro.

O SVG possui descrição contextual e orienta o uso da busca para seleção via teclado.

---

## 53. Navegação principal

A página `/mapa` foi adicionada à navegação principal.

A estrutura possui:

- Início → `/`;
- Histórico → `/historico`;
- Dados & Qualidade → `/dados-qualidade`;
- Predição → `/predicao`;
- Mapa → `/mapa`.

Todas as rotas internas são absolutas.

Isso evita erros de navegação relativa, como:

`/dados-qualidade/mapa`

O comportamento é protegido por:

`web/src/lib/constants/navigation.test.ts`

---

## 54. Responsividade da navegação principal

Em larguras menores, a navegação principal permite rolagem horizontal.

Os itens permanecem em uma única linha utilizável sem exigir alteração arquitetural do header.

A adição de Mapa foi validada em desktop e em larguras menores.

---

## 55. Informação metodológica permanente

A página mantém explicações de que:

- H1 = 1 semana à frente;
- H2 = 2 semanas à frente;
- H3 = 3 semanas à frente;
- H4 = 4 semanas à frente.

Também comunica que:

- os thresholds foram definidos durante validação;
- o score representa probabilidade do estado futuro de risco elevado;
- o score não representa número futuro de casos;
- o resultado é retrospectivo de 2025;
- H1–H4 não representam níveis de severidade.

---

## 56. Relação com o Dashboard de Predição

A rota `/predicao` permanece responsável pela análise detalhada do comportamento preditivo por município.

A rota `/mapa` tem foco em:

- distribuição espacial nacional;
- semana epidemiológica;
- horizonte;
- ALERTA;
- SEM ALERTA;
- SEM AVALIAÇÃO.

As duas superfícies são complementares.

O mapa não duplica integralmente o Dashboard de Predição.

---

## 57. Dados climáticos

O mapa utiliza os resultados do modelo final selecionado.

A conclusão metodológica permanece:

`as variáveis climáticas avaliadas separadamente não produziram ganho preditivo relevante sob a representação e protocolo utilizados`

Essa conclusão não significa que o clima não tenha influência sobre dengue.

A distinção deve ser preservada em qualquer documentação ou interface futura.

---

## 58. Dependências frontend adicionadas

A Fase 14E adicionou:

### Dependências

- `d3-geo` `^3.1.1`;
- `topojson-client` `^3.1.0`.

### Dependências de desenvolvimento

- `@types/d3-geo` `^3.1.1`;
- `@types/topojson-client` `^3.1.5`.

Não foram adicionadas bibliotecas cartográficas de maior complexidade.

---

## 59. Artefatos permanentes da fase

Entre os principais artefatos criados estão:

### Scripts

- `scripts/benchmark_serving_prediction_map.py`;
- `scripts/gerar_serving_geography.py`;
- `scripts/gerar_serving_prediction_map.py`;
- `scripts/sync_web_geography.py`.

### Relatórios de auditoria

- `reports/audits/benchmark_serving_prediction_map.json`;
- `reports/audits/serving_geography.json`.

### Serving preditivo

- `web/src/lib/serving/prediction-map-types.ts`;
- `web/src/lib/serving/prediction-map-server.ts`;
- `web/src/lib/serving/prediction-map-server.test.ts`;
- `web/src/lib/serving/prediction-map-route.test.ts`.

### Route Handlers

- `web/src/app/api/serving/prediction/map/route.ts`;
- `web/src/app/api/serving/prediction/map/[horizonte]/[semana]/route.ts`.

### Página do mapa

- `web/src/app/mapa/`.

### Componentes

- `web/src/components/map/`.

### Geografia frontend

- `web/src/lib/map-geography.ts`;
- `web/src/lib/map-geography.test.ts`;
- `web/src/lib/map-rendering.ts`;
- `web/src/lib/map-rendering.test.ts`.

### Integração preditiva

- `web/src/lib/map-prediction.ts`;
- `web/src/lib/map-prediction.test.ts`.

### Seleção temporal

- `web/src/lib/map-selection-utils.ts`;
- `web/src/lib/map-selection-utils.test.ts`;
- `web/src/lib/map-selection-gaps.test.ts`.

### Identidade territorial

- `web/src/lib/map-territories.ts`;
- `web/src/lib/map-territories.test.ts`.

### Busca municipal

- `web/src/lib/map-territory-search.ts`;
- `web/src/lib/map-territory-search.test.ts`.

### Datas epidemiológicas

- `web/src/lib/map-week-dates.ts`;
- `web/src/lib/map-week-dates.test.ts`.

### Navegação

- `web/src/lib/constants/navigation.ts`;
- `web/src/lib/constants/navigation.test.ts`.

---

## 60. Organização executada da Fase 14E

A fase foi organizada em:

- 14E.1 — Auditoria geoespacial e decisão arquitetural;
- 14E.2 — Contrato espacial e preditivo de serving;
- 14E.3 — Fundação da rota `/mapa`;
- 14E.4 — Mapa municipal do Brasil;
- 14E.5 — Integração semana + H1/H2/H3/H4;
- 14E.6 — Interação e painel municipal;
- 14E.7 — Responsividade, acessibilidade e regressão;
- 14E.8 — Fechamento da fase.

---

## 61. 14E.1 — Auditoria geoespacial e decisão arquitetural

Status:

`CONCLUÍDA`

Entregas:

- auditoria da malha oficial;
- identificação e tratamento de Selvíria;
- avaliação das alternativas de simplificação;
- avaliação de quantização;
- avaliação de `clean`;
- avaliação de `fix-geometry`;
- avaliação de tolerâncias;
- benchmark por UF;
- seleção da estratégia Mapshaper 100 m sem quantização;
- validação topológica;
- gerador definitivo;
- teste de determinismo por SHA-256.

---

## 62. 14E.2 — Contrato espacial e preditivo de serving

Status:

`CONCLUÍDA`

Entregas:

- benchmark verboso × colunar;
- seleção do formato colunar;
- 202 contratos semana × horizonte;
- `index.json`;
- reader TypeScript;
- validações server-side;
- Route Handlers;
- cache HTTP;
- tratamento de erros;
- testes automatizados;
- build de produção aprovado.

---

## 63. 14E.3 — Fundação da rota `/mapa`

Status:

`CONCLUÍDA`

Entregas:

- criação da rota `/mapa`;
- carregamento do índice;
- seleção de semana;
- seleção de horizonte;
- política de URL;
- normalização de parâmetros;
- SE49/H1 como recorte inicial;
- estados de carregamento;
- estados de erro;
- disponibilidade real dos horizontes derivada do índice;
- testes de seleção.

---

## 64. 14E.4 — Mapa municipal do Brasil

Status:

`CONCLUÍDA`

Entregas:

- leitura do TopoJSON;
- sincronização controlada da geometria;
- `d3-geo`;
- `topojson-client`;
- projeção Mercator;
- `fitExtent`;
- `geoPath`;
- SVG;
- 5.571 geometrias;
- 5.571 códigos municipais;
- renderização determinística;
- testes geográficos e de SVG;
- validação visual do mapa nacional.

---

## 65. 14E.5 — Integração temporal e preditiva

Status:

`CONCLUÍDA`

Subetapas:

### 14E.5A — Join geografia × predição

Status:

`CONCLUÍDA`

Validações:

- 5.571 geometrias;
- 5.569 predições;
- 2 territórios sem avaliação;
- join por código IBGE;
- preservação exata de score e predicao.

### 14E.5B — Classificação visual

Status:

`CONCLUÍDA`

Estados:

- ALERTA;
- SEM ALERTA;
- SEM AVALIAÇÃO.

Recorte de referência H1/SE49:

- ALERTA = 1.013;
- SEM ALERTA = 4.556;
- SEM AVALIAÇÃO = 2.

Total:

`5.571`

---

## 66. 14E.6 — Interação e painel municipal

Status:

`CONCLUÍDA`

Subetapas:

### 14E.6A — Identidade territorial

Status:

`CONCLUÍDA`

Entregas:

- parser do índice territorial;
- 5.571 territórios;
- 5.569 com predição;
- 2 sem predição;
- validação por testes.

### 14E.6B — Hover, clique e painel municipal

Status:

`CONCLUÍDA`

Entregas:

- hover;
- clique;
- destaque;
- nome;
- UF;
- região;
- código IBGE;
- resultado oficial;
- score;
- threshold;
- interpretação;
- manutenção da seleção ao trocar filtros.

### 14E.6C — Datas e cobertura temporal

Status:

`CONCLUÍDA`

Entregas:

- intervalo de datas da semana epidemiológica;
- SE01, SE49 e SE52 validadas;
- labels de data;
- cobertura H1–H4 validada;
- regressão da redução progressiva de horizontes;
- normalização das combinações incompatíveis.

---

## 67. 14E.7 — Responsividade, acessibilidade e regressão

Status:

`CONCLUÍDA`

Subetapas:

### 14E.7A — Lógica da busca municipal

Status:

`CONCLUÍDA`

Entregas:

- busca por nome;
- busca sem exigir acento;
- busca por código IBGE;
- ordenação determinística;
- limite de resultados;
- testes automatizados.

### 14E.7B — Busca acessível integrada

Status:

`CONCLUÍDA`

Entregas:

- combobox;
- listbox;
- teclado;
- touch;
- Enter;
- Escape;
- setas;
- Home;
- End;
- seleção pelo mesmo painel utilizado pelo mapa;
- manutenção da seleção durante mudanças de SE/H.

### 14E.7C — Navegação e regressão de rotas

Status:

`CONCLUÍDA`

Entregas:

- inclusão de Mapa na navegação principal;
- rota absoluta `/mapa`;
- testes contra rotas relativas;
- verificação de destinos duplicados.

### 14E.7D — Regressão final desktop/mobile

Status:

`CONCLUÍDA`

Foram validados manualmente:

- recorte inicial;
- filtros temporais;
- redução de horizontes;
- normalização da URL;
- clique municipal;
- painel;
- troca de filtros com município selecionado;
- busca;
- teclado;
- limpeza de seleção;
- hover;
- mobile;
- touch;
- navegação principal;
- linguagem científica.

---

## 68. Regressão automatizada final

Ao final da implementação da Fase 14E, a suíte frontend apresenta:

- Test Files = 21 passed;
- Tests = 168 passed.

O ESLint foi executado sem erros ou warnings pendentes.

Entre as suítes diretamente relacionadas ao mapa estão:

- `prediction-map-server.test.ts`;
- `prediction-map-route.test.ts`;
- `map-geography.test.ts`;
- `map-rendering.test.ts`;
- `map-prediction.test.ts`;
- `map-selection-utils.test.ts`;
- `map-selection-gaps.test.ts`;
- `map-territories.test.ts`;
- `map-territory-search.test.ts`;
- `map-week-dates.test.ts`;
- `navigation.test.ts`.

---

## 69. Build de produção

O build foi executado com:

- Next.js 16.3.2;
- Turbopack.

O processo concluiu com sucesso:

- compilação;
- TypeScript;
- coleta de dados;
- geração das páginas estáticas;
- otimização final.

Entre as rotas reconhecidas estão:

- `/`;
- `/historico`;
- `/dados-qualidade`;
- `/predicao`;
- `/mapa`;
- `/api/serving/territories`;
- `/api/serving/prediction/map`;
- `/api/serving/prediction/map/[horizonte]/[semana]`;
- `/api/serving/prediction/municipality/[codigo]`.

---

## 70. Performance arquitetural

A arquitetura evita dois extremos inadequados:

### Estratégia não adotada 1

Realizar milhares de requisições municipais por recorte.

### Estratégia não adotada 2

Transferir mais de um milhão de predições de uma única vez para o navegador.

A solução adotada utiliza:

- uma geometria nacional reutilizável;
- um contrato preditivo por semana × horizonte;
- payload mediano aproximado de 59,61 KiB gzip;
- cache HTTP;
- join local por código IBGE.

A geometria não é reprocessada ou baixada novamente a cada troca de filtro.

---

## 71. Performance da renderização

A aplicação renderiza:

`5.571 polígonos SVG`

A arquitetura evita:

- 5.571 event handlers React individuais;
- 5.571 elementos focáveis;
- duplicação da geometria;
- recarga de todos os resultados preditivos.

A interação sobre o SVG utiliza delegação de eventos.

A busca textual fornece mecanismo mais adequado para teclado e municípios pequenos.

---

## 72. Limitações conhecidas

A implementação atual possui algumas limitações deliberadas.

### 72.1. Natureza retrospectiva

O mapa apresenta exclusivamente a avaliação final de 2025.

Ele não constitui sistema operacional em produção para 2026.

### 72.2. Seleção municipal não persistida na URL

Semana e horizonte são persistidos na URL.

O município selecionado permanece como estado local da interface.

Compartilhar ou recarregar a página não restaura automaticamente o município selecionado.

Essa funcionalidade poderá ser avaliada futuramente se houver necessidade real.

### 72.3. Ausência de zoom cartográfico avançado

O mapa não implementa:

- zoom geográfico avançado;
- pan;
- tiles;
- camadas externas;
- mapa base.

Esses recursos não são necessários para o objetivo científico desta fase.

### 72.4. SVG nacional

Os 5.571 municípios são renderizados em um único SVG.

A solução foi considerada suficiente para a aplicação acadêmica e para os testes realizados.

### 72.5. Avaliação preditiva ausente em dois territórios

Dois territórios da malha não possuem avaliação preditiva correspondente.

Essa ausência é preservada explicitamente.

---

## 73. Critérios gerais de aceite

A Fase 14E é considerada tecnicamente aceita porque:

1. `/mapa` representa corretamente os 5.571 territórios;
2. as 5.569 previsões são associadas corretamente aos códigos IBGE;
3. os dois territórios sem avaliação são diferenciados de SEM ALERTA;
4. `predicao` é utilizada como decisão oficial;
5. nenhuma categoria artificial de severidade foi introduzida;
6. H1–H4 são apresentados exclusivamente como horizontes temporais;
7. semanas sem determinado horizonte são tratadas corretamente;
8. o mapa permanece explicitamente retrospectivo de 2025;
9. nenhuma linguagem sugere alerta operacional atual;
10. a geometria não é duplicada nos contratos preditivos;
11. a troca de semana ou horizonte carrega apenas o recorte necessário;
12. semana e horizonte são representados na URL;
13. a interface funciona em desktop, tablet e mobile;
14. existe alternativa de seleção por busca e teclado;
15. a regressão automatizada permanece aprovada;
16. o ESLint permanece aprovado;
17. o build de produção permanece aprovado.

---

## 74. Regra de não regressão científica

Nenhuma decisão futura de frontend poderá alterar:

- thresholds;
- predicao;
- score;
- target;
- risco_elevado;
- horizontes;
- cobertura temporal.

Esses valores pertencem ao pipeline científico e ao serving.

O frontend poderá:

- selecionar;
- associar;
- filtrar;
- formatar;
- explicar;
- visualizar.

O frontend não poderá redefinir regras científicas.

---

## 75. Regra de não regressão territorial

O mapa deverá preservar a correspondência:

- 5.571 geometrias;
- 5.571 códigos únicos.

O asset geográfico aprovado deverá continuar validando:

- 0 geometrias inválidas em EPSG:4674;
- 0 geometrias inválidas em EPSG:5880;
- 0 geometrias vazias;
- cobertura válida;
- 0 arestas problemáticas.

Mudanças futuras de simplificação somente poderão substituir o asset atual após nova auditoria equivalente.

---

## 76. Regra de não regressão do join

A associação geografia × predição deverá preservar:

- 5.571 territórios geográficos;
- 5.569 registros preditivos por recorte;
- 2 territórios sem avaliação.

A ausência de registro preditivo nunca poderá ser interpretada como:

- `predicao = false`;
- score zero;
- SEM ALERTA.

---

## 77. Regra de não regressão da disponibilidade temporal

A cobertura oficial permanece:

- SE01–SE49 → H1, H2, H3, H4;
- SE50 → H1, H2, H3;
- SE51 → H1, H2;
- SE52 → H1.

A interface deverá utilizar o `index.json` como fonte de verdade para disponibilidade.

A cobertura não deverá ser inventada no frontend.

---

## 78. Regra de não regressão de datas

As datas exibidas devem permanecer coerentes com a semana epidemiológica oficial usada nos contratos.

Para 2025:

- SE01 inicia em 29/12/2024;
- SE49 inicia em 30/11/2025;
- SE52 inicia em 21/12/2025.

A formatação visual não poderá alterar o significado do recorte temporal.

---

## 79. Regra de não regressão da acessibilidade

A interface não deverá passar a depender exclusivamente de:

- hover;
- cor;
- clique preciso sobre pequenos polígonos.

A busca municipal deve permanecer como alternativa para:

- teclado;
- touch;
- identificação textual;
- seleção de territórios pequenos.

Não deverão ser criados 5.571 tab stops no mapa.

---

## 80. Estado final da Fase 14E

Ao final deste protocolo:

- 14E.1 — CONCLUÍDA;
- 14E.2 — CONCLUÍDA;
- 14E.3 — CONCLUÍDA;
- 14E.4 — CONCLUÍDA;
- 14E.5 — CONCLUÍDA;
- 14E.6 — CONCLUÍDA;
- 14E.7 — CONCLUÍDA;
- 14E.8 — EM FECHAMENTO DOCUMENTAL.

A implementação funcional do Dashboard Geográfico de Predição está concluída.

Restam apenas as atividades de fechamento documental e Git da fase.

---

## 81. 14E.8 — Fechamento

A Fase 14E.8 deverá registrar definitivamente:

- arquitetura geográfica adotada;
- serving nacional de predição;
- biblioteca de renderização;
- política de filtros;
- política de URL;
- comportamento de seleção;
- busca municipal;
- acessibilidade;
- responsividade;
- testes finais;
- build final;
- limitações conhecidas;
- arquivos versionados;
- commit de fechamento da branch.

O documento separado de fechamento será:

`docs/36_fechamento_fase_14e.md`

Após sua criação e validação, deverão ser executados:

- auditoria Git;
- `git diff --check`;
- ESLint;
- Vitest;
- build de produção;
- revisão do conjunto final de arquivos;
- staging;
- commit da Fase 14E.

Nenhuma nova funcionalidade deverá ser adicionada ao mapa durante o fechamento, salvo correção de regressão comprovada.