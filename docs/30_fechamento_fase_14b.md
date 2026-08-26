# 30 — Fechamento da Fase 14B — Integração Web com a camada Serving

## 1. Objetivo

A Fase 14B teve como objetivo integrar a aplicação web do projeto Dengue Alert à camada de dados `serving`, estabelecendo uma interface tipada, validada e adequada para consumo pelo frontend em Next.js.

A etapa também introduziu a consulta sob demanda das séries municipais históricas e preditivas, evitando a publicação direta de aproximadamente 199 MB de arquivos municipais no diretório público da aplicação.

Ao final da fase, a aplicação passou a consumir dados reais produzidos pelo pipeline Python, com contratos explícitos, endpoints internos, filtros territoriais e testes automatizados em TypeScript.

---

## 2. Arquitetura adotada

A arquitetura consolidada nesta fase mantém a separação:

```text
Pipeline Python
      ↓
data/serving
      ↓
Camada de integração Next.js
      ↓
Aplicação React / TypeScript
```

Os arquivos de `data/serving` permanecem como fonte canônica dos dados destinados à aplicação.

Os contratos globais e índices compactos podem ser sincronizados para:

```text
web/public/data/serving
```

As séries municipais, entretanto, permanecem fora do diretório público e são consultadas individualmente por meio de Route Handlers internos do Next.js.

Essa decisão evita a duplicação integral das séries municipais no frontend e permite carregar somente o território solicitado pelo usuário.

---

## 3. Sincronização dos contratos globais

Foi implementado:

```text
scripts/sync_web_serving.py
```

O processo trabalha com uma lista explícita de contratos permitidos para sincronização.

A sincronização utiliza:

- validação JSON estrita;
- `schema_version = 1.0`;
- rejeição de `NaN` e `Infinity`;
- cálculo SHA-256;
- diretório temporário de staging;
- promoção segura;
- backup durante a substituição;
- geração de manifesto.

O manifesto é salvo em:

```text
web/public/data/serving/manifest.json
```

Na etapa validada, foram sincronizados:

```text
24 contratos serving
≈ 12,45 MB
```

As séries municipais não fazem parte dessa sincronização inicial.

Volumes aproximados das séries excluídas:

```text
Histórico municipal   ≈ 131,88 MB
Predição municipal    ≈  67,11 MB
Total                 ≈ 198,99 MB
```

---

## 4. Camada TypeScript para contratos serving

Foi criada uma camada específica em:

```text
web/src/lib/serving/
```

Entre os arquivos principais estão:

```text
paths.ts
types.ts
guards.ts
server.ts
series-server.ts
formatters.ts
```

Essa camada centraliza:

- caminhos dos contratos;
- tipos TypeScript;
- validações estruturais;
- leitura server-side;
- integração dos índices territoriais;
- leitura das séries municipais;
- formatadores utilizados na interface.

O objetivo é impedir que componentes React conheçam diretamente detalhes da organização física dos arquivos de dados.

---

## 5. Índice territorial integrado

A aplicação utiliza os contratos:

```text
metadata/territories.json
historical/municipality/index.json
prediction/municipality/index.json
```

A integração produz uma coleção única de territórios utilizada pelos filtros da aplicação.

Para cada unidade territorial são disponibilizados:

```text
codigoIbge7
nomeMunicipio
codigoUfIbge
nomeUf
regiao
anosDisponiveis
riscoHistoricoDisponivel
predicaoDisponivel
```

O índice integrado contém:

```text
5.571 unidades territoriais
```

Distribuição por região:

```text
Centro-Oeste   468
Nordeste     1.794
Norte          450
Sudeste      1.668
Sul          1.191
```

Também estão representadas as 27 UFs.

---

## 6. Correção do contrato do código da UF

Durante os testes automatizados da camada TypeScript foi identificada uma divergência entre o tipo declarado e o contrato real.

O contrato real fornece:

```json
"codigo_uf_ibge": "35"
```

ou seja, o código da UF é um identificador textual.

Inicialmente a tipagem TypeScript considerava:

```ts
codigoUfIbge: number;
```

A inconsistência foi detectada automaticamente por um teste de integração.

A tipagem foi então corrigida para:

```ts
codigoUfIbge: string;
```

Foi adicionada uma regressão específica garantindo que todos os códigos de UF permaneçam strings de dois dígitos.

Essa representação também é semanticamente mais adequada, pois o código da UF é um identificador territorial e não uma medida numérica.

---

## 7. Consulta municipal sob demanda

As séries municipais canônicas permanecem em:

```text
data/serving/historical/municipality/series/
data/serving/prediction/municipality/series/
```

Foi criada uma camada server-side responsável pela leitura segura desses contratos:

```text
web/src/lib/serving/series-server.ts
```

A consulta exige código IBGE com exatamente sete dígitos:

```text
^\d{7}$
```

Os contratos são validados antes de serem devolvidos à interface.

São verificados, entre outros aspectos:

- versão do schema;
- código IBGE;
- quantidade declarada de registros;
- presença das colunas obrigatórias;
- comprimento consistente das colunas;
- existência dos quatro horizontes preditivos.

---

## 8. Endpoints internos

Foram criados os seguintes Route Handlers:

```text
GET /api/serving/territories

GET /api/serving/historical/municipality/{codigo}

GET /api/serving/prediction/municipality/{codigo}
```

O endpoint territorial fornece o índice compacto utilizado pelos filtros.

Os endpoints municipais carregam somente a série solicitada.

Exemplo:

```text
/api/serving/historical/municipality/3537305
```

retorna a série histórica de Penápolis/SP.

A resposta utiliza cache HTTP:

```text
Cache-Control:
public, max-age=3600, stale-while-revalidate=86400
```

Códigos municipais inválidos produzem resposta de erro sem permitir acesso arbitrário ao sistema de arquivos.

---

## 9. Casos territoriais especiais

A aplicação preserva as diferenças metodológicas de determinados territórios.

### Penápolis/SP — 3537305

Disponibilidade:

```text
Histórico epidemiológico      disponível
Histórico de risco            disponível
Predição retrospectiva 2025   disponível
```

Série histórica:

```text
522 semanas
2016–2025
```

Predição:

```text
202 registros

H1 = 52
H2 = 51
H3 = 50
H4 = 49
```

### Boa Esperança do Norte/MT — 5101837

A unidade territorial foi instalada em 01/01/2025.

Disponibilidade:

```text
Histórico epidemiológico      disponível
Histórico de risco            indisponível
Predição retrospectiva 2025   indisponível
```

A série possui:

```text
53 semanas
somente 2025
```

Não são criados zeros artificiais anteriores à existência do município.

### Fernando de Noronha/PE — 2605459

Disponibilidade:

```text
Histórico epidemiológico      disponível
Histórico de risco            indisponível
Predição retrospectiva 2025   indisponível
```

A série epidemiológica contém:

```text
522 semanas
```

A ausência de histórico de risco decorre da indisponibilidade da cobertura climática/modelada adotada no projeto e não implica ausência de dados epidemiológicos.

---

## 10. Filtros históricos

A página:

```text
/historico
```

passou a utilizar filtros hierárquicos:

```text
Região
  ↓
UF
  ↓
Município
  ↓
Ano epidemiológico
```

A seleção territorial é persistida na URL.

Exemplo:

```text
/historico?regiao=Sudeste&uf=35&municipio=3537305&ano=2024
```

Isso permite:

- atualização da página sem perda do recorte;
- compartilhamento direto do estado da análise;
- navegação reproduzível;
- evolução futura para outros filtros.

O seletor municipal permite pesquisa por:

- nome;
- nome sem acentuação;
- código IBGE.

Exemplos equivalentes de busca:

```text
Penápolis
Penapolis
3537305
```

---

## 11. Semântica dos filtros territoriais

Região e UF são utilizados inicialmente como filtros de localização do município.

A seleção isolada de Região ou UF não transforma automaticamente o panorama nacional em uma agregação regional ou estadual.

Isso evita apresentar como análise calculada um agregado que ainda não possui contrato específico na camada serving.

A troca efetiva para uma série territorial ocorre quando um município é selecionado.

Futuramente, contratos agregados por UF ou Região poderão ser adicionados de forma explícita.

---

## 12. Panorama municipal histórico

Ao selecionar um município, a aplicação consulta a série histórica sob demanda.

Para o município são derivados indicadores como:

- total de casos no período;
- total anual;
- incidência anual;
- população utilizada;
- semana epidemiológica de pico;
- casos na semana de pico;
- quantidade de semanas disponíveis.

Quando nenhum ano é selecionado, a aplicação apresenta a comparação anual.

Quando um ano epidemiológico é selecionado, a visualização passa para a série semanal daquele ano.

Os valores são derivados exclusivamente do contrato histórico municipal correspondente.

---

## 13. Responsividade

Os filtros e visualizações foram estruturados para funcionar em:

```text
desktop
tablet
mobile
```

O campo de Município recebe prioridade de largura por possuir conteúdo potencialmente maior.

Foi corrigida uma condição em que o combobox municipal podia avançar visualmente sobre o campo de Ano epidemiológico.

A correção utiliza:

```text
min-width: 0
```

nos containers flexíveis e uma distribuição específica de espaço entre:

```text
Região
UF
Município
Ano epidemiológico
```

No mobile os controles passam para disposição vertical.

---

## 14. Testes automatizados do frontend

Foi introduzido:

```text
Vitest 4.1.11
```

A configuração está em:

```text
web/vitest.config.mts
```

Foram criados testes para:

```text
formatters.test.ts
server.test.ts
series-server.test.ts
```

A suíte validada possui:

```text
3 arquivos de teste
27 testes
27 aprovados
```

Distribuição:

```text
Formatadores              7
Integração territorial    9
Séries municipais        11
```

Os testes cobrem, entre outros pontos:

- formatação pt-BR;
- cinco regiões;
- 27 UFs;
- 5.571 unidades territoriais;
- 5.569 unidades com histórico de risco;
- 5.569 unidades com predição;
- código de UF textual;
- Penápolis;
- Boa Esperança do Norte;
- Fernando de Noronha;
- validação de código IBGE;
- ausência de predição quando prevista metodologicamente;
- contagens H1–H4;
- thresholds congelados.

---

## 15. Validação de produção do frontend

Foram executados:

```powershell
corepack pnpm lint
corepack pnpm build
corepack pnpm test
```

Resultado:

```text
ESLint              aprovado
Next.js build       aprovado
TypeScript          aprovado
Vitest              27/27 aprovados
```

Rotas identificadas no build:

```text
○ /
○ /dados-qualidade
○ /historico
○ /predicao

ƒ /api/serving/territories
ƒ /api/serving/historical/municipality/[codigo]
ƒ /api/serving/prediction/municipality/[codigo]
```

As páginas são pré-renderizadas quando possível.

Os endpoints municipais permanecem dinâmicos e são executados sob demanda.

---

## 16. Regressão Python

Após a integração web também foi executada a suíte completa do pipeline Python.

Comandos:

```powershell
uv run ruff check src scripts tests --fix
uv run ruff format src scripts tests
uv run ruff check src scripts tests
uv run pytest
```

Resultados:

```text
Ruff check     aprovado
Ruff format    nenhum arquivo alterado
Pytest         179/179 testes aprovados
```

Isso confirma que a introdução da camada web não alterou os contratos ou comportamentos científicos já validados no pipeline Python.

---

## 17. Decisão sobre FastAPI

A Fase 14B não introduz FastAPI.

O Next.js é utilizado como camada de aplicação e disponibiliza Route Handlers internos suficientes para o estágio atual do projeto.

Essa decisão mantém a arquitetura inicial mais simples:

```text
Python offline
    ↓
serving
    ↓
Next.js
```

FastAPI permanece uma alternativa futura caso sejam necessários:

- serviços independentes;
- atualização online dos dados;
- múltiplos consumidores;
- autenticação centralizada;
- jobs remotos;
- inferência online;
- infraestrutura desacoplada do frontend.

---

## 18. Limitação de deployment ainda aberta

As séries municipais canônicas permanecem fora do Git e fora do diretório público do frontend.

Portanto, um ambiente de produção precisará garantir acesso a:

```text
data/serving
```

pela aplicação Next.js.

As possibilidades futuras incluem:

```text
artefato preparado durante o build
volume persistente
object storage
snapshot de serving
pipeline de deployment dedicado
```

A decisão de infraestrutura não é necessária para o desenvolvimento local da aplicação e permanece deliberadamente aberta para uma etapa posterior.

---

## 19. Resultado da Fase 14B

A Fase 14B é considerada concluída.

Ao final da etapa, o projeto possui:

```text
contratos serving sincronizáveis
camada TypeScript tipada
índice territorial integrado
consulta municipal sob demanda
endpoints internos Next.js
filtros Região → UF → Município → Ano
estado persistido em URL
busca municipal
panorama histórico municipal
tratamento de territórios especiais
layout responsivo
27 testes TypeScript
179 testes Python
build de produção aprovado
```

A aplicação deixou de depender de valores estáticos para a navegação histórica e passou a utilizar diretamente os contratos reais produzidos pelo pipeline científico.

---

## 20. Próxima etapa

A continuidade da Fase 14 deve desenvolver as áreas analíticas da aplicação sobre essa infraestrutura já validada.

Entre os próximos blocos estão:

```text
expansão do dashboard Histórico
visualizações de sazonalidade
visualizações territoriais
indicadores de risco histórico
área Dados & Qualidade
área Predição
visualização das probabilidades H1–H4
interpretação responsável dos resultados
```

A infraestrutura criada na Fase 14B deve ser reutilizada nessas etapas, evitando acesso direto dos componentes aos arquivos canônicos e mantendo a separação entre dados históricos, qualidade e predição.