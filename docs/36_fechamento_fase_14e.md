# Fechamento da Fase 14E — Dashboard Geográfico de Predição

## 1. Identificação da fase

Fase:

`14E — Dashboard Geográfico de Predição`

Branch de desenvolvimento:

`feat/map-dashboard`

Rota principal entregue:

`/mapa`

Natureza da visualização:

`avaliação retrospectiva de 2025`

A Fase 14E teve como objetivo transformar os resultados preditivos retrospectivos do Dengue Alert em uma superfície geográfica nacional, permitindo visualizar a classificação oficial do modelo por município brasileiro, semana epidemiológica e horizonte preditivo.

---

## 2. Resultado final

A implementação funcional da Fase 14E foi concluída.

A aplicação passou a disponibilizar um mapa municipal do Brasil contendo:

- 5.571 territórios geográficos;
- 5.569 municípios com avaliação preditiva;
- 2 territórios sem avaliação preditiva;
- seleção de semana epidemiológica;
- seleção de horizonte H1, H2, H3 ou H4;
- classificação oficial ALERTA / SEM ALERTA;
- estado específico SEM AVALIAÇÃO;
- busca municipal;
- seleção por clique;
- seleção por teclado;
- painel municipal;
- score;
- threshold;
- datas da semana epidemiológica;
- navegação responsiva;
- integração com a URL;
- suporte a desktop, tablet e mobile.

A página permanece explicitamente retrospectiva e não representa alertas operacionais atuais.

---

## 3. Arquitetura geográfica aprovada

A fonte territorial utilizada foi:

`IBGE — Malha Municipal 2024`

Arquivo-fonte:

`data/raw/geography/ibge_municipios_2024/BR_Municipios_2024.shp`

A fonte original possuía:

- 5.573 feições;
- CRS EPSG:4674.

Durante a auditoria foi identificada uma geometria inválida:

`5007802 — Selvíria/MS`

O reparo oficial utiliza:

`make_valid(method="structure", keep_collapsed=False)`

Também são removidas:

- `4300001`;
- `4300002`.

O conjunto territorial final possui:

- 5.571 geometrias;
- 5.571 códigos únicos;
- 0 geometrias inválidas em EPSG:4674;
- 0 geometrias inválidas em EPSG:5880;
- 0 geometrias vazias;
- cobertura topológica válida;
- 0 arestas problemáticas.

---

## 4. Simplificação geográfica

Após benchmark de diferentes estratégias, foi aprovada a combinação:

- Mapshaper 0.7.55;
- Douglas-Peucker;
- intervalo de 100 m;
- `keep-shapes`;
- TopoJSON;
- sem quantização.

A quantização foi descartada por introduzir invalidades adicionais.

Também foram descartados:

- simplificação independente com GeoPandas;
- `simplify_coverage()`;
- `clean`;
- `fix-geometry`;
- tolerâncias mais agressivas;
- distribuição principal dos polígonos originais por UF.

---

## 5. Asset geográfico definitivo

A fonte canônica derivada é:

`data/serving/geography/municipalities.topojson`

Metadados:

`data/serving/geography/metadata.json`

Peso aproximado:

- TopoJSON bruto = 16,27 MiB;
- TopoJSON gzip = 5,64 MiB.

O SHA-256 determinístico observado foi:

`08f602577f536d405e3c9b16a72608c7407e770694d636dadb9f996606ef56db`

Execuções consecutivas do gerador produziram o mesmo resultado byte a byte.

A auditoria versionável está registrada em:

`reports/audits/serving_geography.json`

---

## 6. Geração e sincronização geográfica

O gerador definitivo é:

`scripts/gerar_serving_geography.py`

A sincronização para a aplicação web é realizada por:

`scripts/sync_web_geography.py`

O navegador utiliza:

`/data/serving/geography/municipalities.topojson`

A fonte canônica permanece em `data/serving`.

A cópia em `web/public` é apenas um asset derivado para entrega ao navegador.

---

## 7. Arquitetura do serving preditivo

A fonte científica utilizada pelo mapa é:

`data/processed/predicoes_avaliacao_final_2025.parquet`

Ela contém:

- 1.124.938 predições;
- 5.569 municípios;
- ano epidemiológico 2025;
- horizontes H1, H2, H3 e H4.

Foi descartada a estratégia de carregar as séries municipais individualmente para compor o mapa nacional.

Também foi descartada a transferência integral de todas as predições para o navegador.

A solução aprovada utiliza contratos nacionais por:

`semana epidemiológica × horizonte`

---

## 8. Benchmark do serving preditivo

O benchmark é realizado por:

`scripts/benchmark_serving_prediction_map.py`

Relatório:

`reports/audits/benchmark_serving_prediction_map.json`

Foram avaliadas representações verbosa e colunar.

O formato colunar foi aprovado.

Resultados aproximados do formato colunar:

- total bruto = 38,86 MiB;
- total gzip = 11,71 MiB;
- arquivo mediano bruto = 196,52 KiB;
- arquivo mediano gzip = 59,61 KiB;
- maior arquivo gzip = 65,32 KiB.

Em relação ao formato verboso, a redução observada foi aproximadamente:

- 50,53% no tamanho bruto;
- 13,05% no tamanho gzip.

---

## 9. Serving preditivo definitivo

O gerador oficial é:

`scripts/gerar_serving_prediction_map.py`

Destino canônico:

`data/serving/prediction/map/`

A estrutura contém:

- 52 contratos para H1;
- 51 contratos para H2;
- 50 contratos para H3;
- 49 contratos para H4.

Total:

`202 contratos semana × horizonte`

Além de:

`index.json`

O índice funciona como fonte de verdade da disponibilidade temporal.

---

## 10. Cobertura temporal definitiva

A cobertura oficial é:

- H1 = SE01 até SE52;
- H2 = SE01 até SE51;
- H3 = SE01 até SE50;
- H4 = SE01 até SE49.

Nas semanas finais:

- SE49 → H1, H2, H3, H4;
- SE50 → H1, H2, H3;
- SE51 → H1, H2;
- SE52 → H1.

A aplicação consulta a disponibilidade registrada no índice.

Combinações inexistentes nunca são convertidas em SEM ALERTA.

---

## 11. Contrato científico preservado

O frontend preserva a semântica científica definida anteriormente no projeto.

### `score`

Representa a probabilidade estimada do estado futuro metodologicamente definido de risco elevado.

Não representa:

- quantidade futura de casos;
- incidência futura prevista;
- probabilidade de uma quantidade específica de casos.

### `threshold`

É o limiar definido durante a validação.

Thresholds congelados:

- H1 = 0,187687;
- H2 = 0,190783;
- H3 = 0,167991;
- H4 = 0,157138.

### `predicao`

É a decisão oficial já produzida pelo pipeline:

- `true` = ALERTA;
- `false` = SEM ALERTA.

O frontend utiliza diretamente `predicao`.

Ele não recalcula a classificação a partir do score como fonte oficial.

---

## 12. Horizontes

Os horizontes possuem significado exclusivamente temporal:

- H1 = 1 semana à frente;
- H2 = 2 semanas à frente;
- H3 = 3 semanas à frente;
- H4 = 4 semanas à frente.

Eles não representam severidade.

Não foram introduzidas categorias artificiais como:

- baixo;
- moderado;
- alto;
- crítico.

---

## 13. Route Handlers

Foram implementadas:

`GET /api/serving/prediction/map`

e:

`GET /api/serving/prediction/map/[horizonte]/[semana]`

As rotas leem diretamente os contratos presentes em:

`data/serving/prediction/map`

Os contratos preditivos nacionais não são copiados para `web/public`.

A API diferencia:

- seleção inválida;
- combinação temporal indisponível;
- falha interna.

Também utiliza cache HTTP adequado à natureza retrospectiva e imutável dos dados.

---

## 14. Fundação da página `/mapa`

A rota `/mapa` foi criada como nova superfície da aplicação.

Recorte padrão:

- SE49;
- H1.

A escolha de SE49 permite iniciar em uma semana na qual todos os quatro horizontes coexistem.

Os filtros são representados na URL.

Exemplo:

`/mapa?semana=49&horizonte=1`

A normalização é determinística.

Exemplos:

- semana inválida → SE49;
- horizonte inválido → H1;
- SE50/H4 → SE50/H1;
- SE52/H4 → SE52/H1;
- SE49/H4 → permanece SE49/H4.

---

## 15. Datas epidemiológicas

A interface exibe o intervalo correspondente à semana epidemiológica.

Foram validadas as seguintes referências:

- SE01 inicia em 29/12/2024;
- SE49 inicia em 30/11/2025;
- SE52 inicia em 21/12/2025.

Exemplo de apresentação:

`SE49 · 30/11 a 06/12/2025`

A informação aparece tanto nos controles quanto no painel municipal.

---

## 16. Renderização geográfica

Foram adicionadas as dependências:

- `d3-geo` 3.1.1;
- `topojson-client` 3.1.0.

Tipos correspondentes:

- `@types/d3-geo` 3.1.1;
- `@types/topojson-client` 3.1.5.

A solução utiliza:

- TopoJSON;
- SVG;
- `geoMercator`;
- `fitExtent`;
- `geoPath`.

A renderização produz exatamente:

`5.571 paths SVG`

A geometria é carregada uma única vez e reutilizada durante alterações de semana e horizonte.

---

## 17. Integração geografia × predição

A associação é realizada pelo código IBGE municipal.

No recorte oficial H1/SE49:

- ALERTA = 1.013;
- SEM ALERTA = 4.556;
- SEM AVALIAÇÃO = 2.

Fechamento:

`1.013 + 4.556 + 2 = 5.571`

Os dois territórios sem avaliação permanecem separados de SEM ALERTA.

O campo oficial `predicao` é preservado exatamente.

---

## 18. Interação municipal

A interface oferece:

- hover no desktop;
- clique;
- toque;
- destaque do município selecionado;
- painel persistente.

O painel apresenta:

- município;
- UF;
- região;
- código IBGE;
- resultado oficial;
- semana;
- horizonte;
- intervalo da semana;
- score;
- threshold;
- interpretação metodológica.

A seleção permanece ativa quando semana ou horizonte são alterados.

---

## 19. Busca municipal

Foi implementada busca por:

- nome do município;
- código IBGE.

A busca ignora diferenças de acentuação.

Exemplo:

`penapolis`

localiza:

`Penápolis`

Também é possível utilizar:

`3537305`

A busca possui limite padrão de oito resultados.

---

## 20. Acessibilidade da busca

A busca foi integrada como combobox/listbox.

São suportados:

- ArrowDown;
- ArrowUp;
- Home;
- End;
- Enter;
- Escape;
- mouse;
- touch.

Essa abordagem evita transformar os 5.571 polígonos em tab stops.

A seleção por busca utiliza exatamente o mesmo estado municipal utilizado pelo clique no mapa.

---

## 21. Responsividade

A interface foi validada manualmente em:

- desktop;
- tablet;
- mobile.

Foram verificados:

- mapa;
- filtros;
- painel municipal;
- busca;
- sugestões;
- navegação principal;
- estados de seleção;
- ausência de scroll horizontal indevido;
- comportamento em touch.

Em dispositivos sem hover, a interface não depende do cartão de hover para seleção.

---

## 22. Navegação principal

A navegação da aplicação passou a conter:

- Início;
- Histórico;
- Dados & Qualidade;
- Predição;
- Mapa.

A rota do mapa é absoluta:

`/mapa`

Foi adicionada regressão automatizada para impedir destinos relativos como:

`mapa`

que poderiam gerar incorretamente caminhos como:

`/dados-qualidade/mapa`

---

## 23. Artefatos principais adicionados

### Scripts

- `scripts/benchmark_serving_prediction_map.py`;
- `scripts/gerar_serving_geography.py`;
- `scripts/gerar_serving_prediction_map.py`;
- `scripts/sync_web_geography.py`.

### Auditorias

- `reports/audits/benchmark_serving_prediction_map.json`;
- `reports/audits/serving_geography.json`.

### Serving

- `web/src/lib/serving/prediction-map-types.ts`;
- `web/src/lib/serving/prediction-map-server.ts`;
- `web/src/lib/serving/prediction-map-server.test.ts`;
- `web/src/lib/serving/prediction-map-route.test.ts`.

### API

- `web/src/app/api/serving/prediction/map/route.ts`;
- `web/src/app/api/serving/prediction/map/[horizonte]/[semana]/route.ts`.

### Página

- `web/src/app/mapa/`.

### Componentes

- `web/src/components/map/`.

### Geografia

- `web/src/lib/map-geography.ts`;
- `web/src/lib/map-geography.test.ts`;
- `web/src/lib/map-rendering.ts`;
- `web/src/lib/map-rendering.test.ts`.

### Predição espacial

- `web/src/lib/map-prediction.ts`;
- `web/src/lib/map-prediction.test.ts`.

### Seleção

- `web/src/lib/map-selection-utils.ts`;
- `web/src/lib/map-selection-utils.test.ts`;
- `web/src/lib/map-selection-gaps.test.ts`.

### Territórios

- `web/src/lib/map-territories.ts`;
- `web/src/lib/map-territories.test.ts`.

### Busca

- `web/src/lib/map-territory-search.ts`;
- `web/src/lib/map-territory-search.test.ts`.

### Datas

- `web/src/lib/map-week-dates.ts`;
- `web/src/lib/map-week-dates.test.ts`.

### Navegação

- `web/src/lib/constants/navigation.ts`;
- `web/src/lib/constants/navigation.test.ts`.

---

## 24. Validação automatizada final

Ao final da implementação, a suíte frontend alcançou:

`21 Test Files passed`

e:

`168 Tests passed`

O ESLint foi executado sem erros ou warnings pendentes.

Os testes cobrem, entre outros pontos:

- contratos preditivos;
- Route Handlers;
- cobertura temporal;
- thresholds;
- malha municipal;
- 5.571 paths;
- determinismo da renderização;
- join geografia × predição;
- preservação de `predicao`;
- fechamento 5.571;
- territórios sem avaliação;
- seleção temporal;
- redução dos horizontes;
- datas epidemiológicas;
- identidade territorial;
- busca municipal;
- navegação absoluta.

---

## 25. Build de produção

O build final foi validado com:

- Next.js 16.3.2;
- Turbopack.

As etapas concluíram com sucesso:

- compilação;
- TypeScript;
- coleta de dados;
- geração estática;
- otimização final.

A rota `/mapa` foi reconhecida corretamente pelo build.

As Route Handlers preditivas também foram reconhecidas como rotas dinâmicas.

---

## 26. Regressão manual final

A regressão funcional final validou:

1. abertura de `/mapa`;
2. recorte padrão SE49/H1;
3. intervalo de datas;
4. contagens da legenda;
5. disponibilidade H1–H4;
6. redução progressiva de horizontes nas semanas finais;
7. normalização de combinações incompatíveis;
8. seleção por clique;
9. persistência da seleção;
10. atualização do município após troca de SE/H;
11. busca por nome;
12. busca sem acento;
13. busca por código IBGE;
14. navegação por teclado;
15. Enter;
16. Escape;
17. limpeza da seleção;
18. hover;
19. comportamento mobile;
20. comportamento touch;
21. navegação principal;
22. preservação da linguagem científica.

A regressão foi aprovada.

---

## 27. Limitações conhecidas

### 27.1. Avaliação retrospectiva

A página apresenta resultados de 2025.

Ela não representa alertas operacionais atuais.

### 27.2. Município não persistido na URL

Semana e horizonte são representados na URL.

O município selecionado permanece como estado local da interface.

### 27.3. Ausência de zoom avançado

A fase não implementa:

- pan;
- zoom cartográfico avançado;
- tiles;
- mapa-base;
- satélite;
- serviços externos.

Esses recursos não eram necessários ao objetivo da fase.

### 27.4. SVG nacional único

Os 5.571 territórios são renderizados em um único SVG.

A estratégia foi considerada suficiente para a aplicação acadêmica e para os testes realizados.

### 27.5. Dois territórios sem avaliação

Dois territórios da malha não possuem resultado preditivo.

Essa ausência é mantida explicitamente como SEM AVALIAÇÃO.

---

## 28. Não regressão científica

Mudanças futuras não poderão alterar no frontend:

- score;
- predicao;
- threshold;
- target;
- risco_elevado;
- horizonte;
- cobertura temporal.

Esses valores pertencem ao pipeline científico.

O frontend pode:

- selecionar;
- associar;
- formatar;
- explicar;
- visualizar.

Ele não pode redefinir regras científicas.

---

## 29. Não regressão territorial

Mudanças futuras no asset geográfico deverão preservar ou superar a auditoria atual.

Os seguintes invariantes devem permanecer:

- 5.571 territórios;
- 5.571 códigos únicos;
- 0 geometrias inválidas em EPSG:4674;
- 0 geometrias inválidas em EPSG:5880;
- 0 geometrias vazias;
- cobertura topológica válida;
- 0 arestas problemáticas.

Uma nova estratégia de simplificação somente poderá substituir o asset atual após auditoria equivalente.

---

## 30. Não regressão do mapa

O mapa deve continuar preservando:

`5.571 geometrias`

associadas a:

`5.569 predições`

mais:

`2 territórios sem avaliação`

A ausência de uma predição jamais poderá ser convertida em:

- score zero;
- `predicao = false`;
- SEM ALERTA.

---

## 31. Situação das subfases

Estado final:

- 14E.1 — CONCLUÍDA;
- 14E.2 — CONCLUÍDA;
- 14E.3 — CONCLUÍDA;
- 14E.4 — CONCLUÍDA;
- 14E.5 — CONCLUÍDA;
- 14E.6 — CONCLUÍDA;
- 14E.7 — CONCLUÍDA;
- 14E.8 — FECHAMENTO TÉCNICO CONCLUÍDO.

A Fase 14E não possui novas funcionalidades pendentes.

---

## 32. Conclusão

A Fase 14E transformou os resultados preditivos retrospectivos do Dengue Alert em uma superfície geográfica nacional reproduzível, auditável e compatível com a arquitetura de serving já existente.

A solução final:

- preserva a metodologia científica;
- utiliza a decisão oficial `predicao`;
- mantém separadas geometria e predição;
- evita transferência desnecessária de dados;
- preserva os 5.571 territórios municipais;
- representa corretamente os 5.569 municípios avaliados;
- diferencia os dois territórios sem avaliação;
- suporta H1, H2, H3 e H4 segundo a cobertura real;
- mantém os filtros na URL;
- oferece busca municipal acessível;
- funciona em desktop, tablet e mobile;
- permanece coberta por testes automatizados;
- conclui o build de produção com sucesso.

A implementação funcional do Dashboard Geográfico de Predição está, portanto, encerrada.

A partir deste ponto, qualquer evolução do mapa deverá ser tratada como nova funcionalidade ou nova fase, e não como requisito pendente da Fase 14E.