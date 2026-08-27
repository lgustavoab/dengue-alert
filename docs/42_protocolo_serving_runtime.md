# Protocolo do serving runtime compacto

## 1. Relação entre canônico e runtime

`data/serving` permanece a fonte científica canônica do Dengue Alert. O diretório não é substituído, reserializado ou incluído diretamente no Git. A versão canônica publicada continua sendo `serving-v1.0.0`.

`serving-runtime-v1.0.0` é uma derivação operacional reproduzível. Ela reduz a cardinalidade dos arquivos municipais para diminuir o trabalho de file tracing e empacotamento serverless, sem mudar os contratos científicos ou HTTP.

O runtime nunca contém:

- `historical/municipality/series/*.json`;
- `prediction/municipality/series/*.json`.

## 2. Estrutura

```text
serving-runtime-v1.0.0/
├── manifest.json
├── SHA256SUMS
├── historical/
│   ├── municipalities.ndjson
│   └── municipalities.index.json
├── prediction/
│   ├── municipalities.ndjson
│   ├── municipalities.index.json
│   └── map/
│       ├── index.json
│       └── h1...h4/se*.json
├── geography/
├── metadata/
├── quality/
└── demais contratos públicos explicitamente permitidos
```

Os 202 slices do mapa e seu índice permanecem como arquivos individuais. Os 24 contratos JSON sincronizados para o frontend e os dois arquivos geográficos também são copiados byte a byte por allowlist explícita.

## 3. Formato municipal

Cada pack usa o formato `ndjson-offset-v1`:

```text
[payload JSON canônico][LF]
[payload JSON canônico][LF]
...
```

O payload entre `offset` e `offset + length` é exatamente o arquivo UTF-8 canônico. A quebra de linha externa é apenas o separador do pack e não pertence ao payload.

O índice técnico registra, para cada `codigo_ibge_7`:

- `offset` em bytes;
- `length` em bytes;
- SHA-256 do payload.

Também registra tamanho e SHA-256 do pack, versão, encoding, formato e quantidade de entradas. O índice não contém valores científicos e não é uma segunda fonte de verdade.

## 4. Integridade e determinismo

O gerador:

1. ordena os códigos IBGE lexicalmente;
2. rejeita nomes inesperados, duplicatas e payloads vazios;
3. valida `schema_version` e o código interno;
4. copia os bytes sem `JSON.parse` seguido de reserialização;
5. valida offsets, comprimentos, ausência de overlap e limites;
6. relê todos os ranges e compara com os 11.140 arquivos municipais;
7. valida os 203 arquivos do mapa contra uma allowlist fechada;
8. calcula SHA-256 por payload, arquivo, pack, manifest e archive;
9. reconfirma o fingerprint completo do canônico ao final.

O ZIP usa ordem fixa, timestamp normalizado, modo Unix `0644` e compressão Deflate nível 9. Nas mesmas condições, os bytes e o SHA-256 devem ser reproduzíveis.

## 5. Geração local

Executar a partir da raiz do repositório:

```text
uv run python scripts/package_serving_runtime.py
```

Saídas ignoradas pelo Git:

```text
dist/serving-runtime-v1.0.0/
dist/serving-runtime-v1.0.0.zip
dist/serving-runtime-v1.0.0.zip.sha256
```

Manifest técnico pequeno e versionável:

```text
artifacts/serving/serving-runtime-v1.0.0.json
```

O gerador recusa sobrescrita dos artefatos existentes. Uma nova derivação deve usar um destino vazio ou uma nova versão explícita.

## 6. Leitura no Next.js

O leitor em `web/src/lib/serving/runtime-pack-server.ts`:

1. prefere o runtime quando `manifest.json` está disponível;
2. carrega e valida somente o índice em memória;
3. localiza o range do município;
4. abre o pack em modo de leitura;
5. lê somente `length` bytes na posição `offset`;
6. fecha o file handle em `finally`;
7. valida o SHA-256 do payload;
8. decodifica UTF-8 em modo estrito;
9. executa `JSON.parse` somente no payload municipal;
10. passa o objeto pelos validadores científicos já existentes.

O pack completo nunca é carregado por requisição.

## 7. Desenvolvimento local

Quando o runtime não existe, a camada municipal e o mapa usam o `data/serving` canônico local. Isso preserva `corepack pnpm dev`.

O fallback canônico é deliberadamente excluído do output file tracing. Em produção, os includes apontam somente para os packs/índices do runtime, mapa e três contratos territoriais necessários.

A variável opcional `DENGUE_SERVING_RUNTIME_ROOT` permite apontar testes controlados para uma fixture de runtime. Ela não é necessária no uso normal.

## 8. Build Vercel

O fluxo alvo é:

```text
Vercel
→ bootstrap de serving-runtime-v1.0.0
→ aproximadamente 235 arquivos extraídos
→ reconstrução dos 27 assets públicos
→ next build
```

Durante a Fase 15C.7c, o wrapper aceita somente um archive local explícito por `DENGUE_SERVING_RUNTIME_ARCHIVE` ou um runtime já instalado e validado. Não existe URL remota fictícia e o snapshot canônico de 11.369 arquivos não é baixado pelo novo `build:vercel`.

A ativação remota depende de uma futura Release separada, descriptor com URL HTTPS, tamanho e SHA-256, e autorização explícita em subfase posterior.

## 9. Git e distribuição futura

O Git versiona somente:

- gerador e bootstrap;
- leitor TypeScript;
- testes;
- manifest técnico pequeno;
- configuração de tracing;
- este protocolo.

Packs, árvore extraída e ZIP permanecem em `dist/`, já ignorado. A futura distribuição deverá usar outra Release e outro asset, por exemplo `serving-runtime-v1.0.0.zip`, sem alterar a Release canônica `serving-v1.0.0`.
