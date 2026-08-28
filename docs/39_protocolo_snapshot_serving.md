# Protocolo do snapshot científico de serving

## Objetivo

O snapshot preserva e transporta, sem recalcular ou reserializar, o conjunto
canônico `data/serving`. Ele permite que builds e ambientes de produção recebam
exatamente os contratos científicos aprovados, mesmo que esses arquivos não
sejam armazenados no Git.

## Versão inicial e imutabilidade

A versão inicial é `serving-v1.0.0`. O identificador segue versionamento
semântico e não depende de timestamp. Depois de publicada, uma versão não deve
ser substituída: mudanças científicas, contratuais ou de conteúdo exigem uma
nova versão.

O snapshot cobre o período científico de 2016–2025 e a avaliação preditiva
retrospectiva de 2025.

## Fonte autoritativa

`data/serving` é a única fonte autoritativa. O conteúdo de
`web/public/data/serving` continua sendo derivado pelos scripts existentes:

- `scripts/sync_web_serving.py`;
- `scripts/sync_web_geography.py`.

O subconjunto público não é incluído como uma segunda fonte no snapshot.

## Manifest

O arquivo versionado `artifacts/serving/serving-v1.0.0.json` registra:

- versão do schema e do snapshot;
- períodos científico e preditivo;
- contagem e tamanho total;
- caminho POSIX, tamanho e SHA-256 de cada arquivo;
- horizontes H1–H4;
- referência ao contrato que contém os thresholds congelados.

Os thresholds não são copiados para o manifest. A referência a
`data/serving/prediction/metadata/model.json`, também protegida por SHA-256,
evita criar uma segunda fonte metodológica suscetível a divergência.

O manifest não contém timestamps, caminhos absolutos, UUIDs ou URLs de
distribuição. Seus arquivos são ordenados lexicograficamente.

## Estrutura do ZIP

```text
manifest.json
SHA256SUMS
data/
  serving/
    ...
```

`manifest.json` possui exatamente os mesmos bytes do manifest versionado.
`SHA256SUMS` é derivado deterministicamente da lista `files` e cobre somente os
contratos em `data/serving`; ele não tenta incluir a si próprio ou o manifest.

Os contratos são copiados byte a byte. O empacotador não interpreta, formata ou
normaliza JSON e TopoJSON.

## Determinismo e segurança

O ZIP usa ordem lexicográfica, DEFLATE padrão, nível de compressão fixo,
timestamp ZIP fixo e permissões normalizadas de arquivo regular. No mesmo
ambiente Python/zlib, a mesma entrada produz o mesmo ZIP e o mesmo SHA-256. O
manifest e a identidade do conteúdo permanecem determinísticos também entre
plataformas.

O empacotador rejeita:

- caminhos absolutos, `..`, barras incompatíveis e caracteres de controle;
- symlinks;
- caches, arquivos ocultos e temporários;
- formatos diferentes de JSON e TopoJSON;
- arquivos fora da raiz canônica;
- alterações detectadas durante leitura ou empacotamento;
- divergências entre origem, manifest, ZIP e restauração.

A restauração de validação usa diretório temporário vazio, confina cada destino
à sua raiz e nunca sobrescreve `data/serving` original.

## Geração local

Na raiz do projeto:

```text
uv run python scripts/package_serving_snapshot.py
```

O comando cria:

- o manifest pequeno e versionável em `artifacts/serving`;
- o ZIP e seu sidecar SHA-256 em `dist`;
- uma restauração temporária para comparação integral, removida ao final.

O diretório `dist/` já é ignorado pelo Git. O ZIP e seu sidecar não devem ser
adicionados ao repositório.

## Distribuição e bootstrap

O descriptor externo
`artifacts/serving/serving-v1.0.0-distribution.json` registra versão, nome,
tamanho, SHA-256 e a URL HTTPS estável do asset publicado. Ele permanece
separado do manifest interno, portanto a localização de distribuição não altera
a identidade nem os hashes científicos.

A versão está publicada na Release
`https://github.com/lgustavoab/dengue-alert/releases/tag/serving-v1.0.0`. O ZIP
canônico é `serving-v1.0.0.zip`, com 53.427.094 bytes e SHA-256
`68eb1ffc3fc7d3104c8099467d01a0ef1a3cb282f5768af8dd95bc6697d08f4f`.
Essa versão é imutável; qualquer conteúdo diferente exige uma nova versão.

O bootstrap seguro está descrito em `docs/40_protocolo_bootstrap_serving.md`.
Ele usa por padrão a URL HTTPS do descriptor, também aceita arquivo local ou URL
HTTPS explícita, verifica o descriptor antes de abrir o ZIP e somente promove
uma restauração integralmente validada.

## Conteúdo versionado no Git

São versionados apenas:

- o script de empacotamento;
- o script de bootstrap;
- seus testes;
- o manifest JSON completo;
- o descriptor externo com URL HTTPS estável;
- este protocolo técnico.

Permanecem fora do Git o serving canônico, o ZIP, o sidecar de hash, cópias
temporárias e futuras restaurações de validação.
