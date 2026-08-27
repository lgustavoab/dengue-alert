# Protocolo de bootstrap seguro do serving

## Objetivo

O bootstrap instala o snapshot científico versionado em ambientes que não
possuem `data/serving`. O fluxo não recalcula ciência e não confia somente em
informações contidas no próprio ZIP.

## Fontes de confiança

Três elementos independentes participam da validação:

1. o descriptor externo versionado, com SHA-256 e tamanho do ZIP;
2. o manifest completo versionado, com caminhos, tamanhos e hashes científicos;
3. o manifest e `SHA256SUMS` internos do ZIP, que devem ser idênticos aos
   controles externos.

O descriptor atual é
`artifacts/serving/serving-v1.0.0-distribution.json`. Ele contém os dados reais
e a URL HTTPS estável do asset `serving-v1.0.0.zip` publicado na GitHub Release
`serving-v1.0.0`.

## Interface

Instalação pela URL registrada no descriptor:

```text
uv run python scripts/bootstrap_serving_snapshot.py
```

Validação e instalação a partir do snapshot local:

```text
uv run python scripts/bootstrap_serving_snapshot.py \
  --archive dist/serving-v1.0.0.zip
```

Somente verificação, sem extração ou promoção:

```text
uv run python scripts/bootstrap_serving_snapshot.py \
  --archive dist/serving-v1.0.0.zip \
  --verify
```

Substituição explícita de serving divergente:

```text
uv run python scripts/bootstrap_serving_snapshot.py \
  --archive dist/serving-v1.0.0.zip \
  --replace
```

Regeneração do subconjunto público após instalação válida:

```text
uv run python scripts/bootstrap_serving_snapshot.py \
  --archive dist/serving-v1.0.0.zip \
  --sync-web
```

Uma URL HTTPS explícita ainda pode ser informada por `--url <URL-HTTPS>`. Essa
opção substitui a URL do descriptor apenas para a execução atual.

`--project-root` e `--destination` permitem validação em workspace isolado. O
sync exige que o destino seja exatamente `<project-root>/data/serving`.

## Fluxo seguro

O bootstrap executa:

```text
descriptor e manifest versionados
  → arquivo local ou download HTTPS temporário
  → tamanho e SHA-256 externos
  → preflight de entradas e tamanhos ZIP
  → hashes internos
  → restauração em staging no mesmo filesystem
  → validação integral restaurada
  → promoção
  → sync web opcional
```

O destino nunca é usado como diretório de extração. Em instalação nova, o
diretório validado é renomeado para o destino. Em substituição explícita, o
serving anterior é primeiro renomeado para backup no mesmo diretório pai; se a
promoção falhar, o backup é restaurado. Essa sequência evita depender de
substituição direta de diretório não vazio, operação limitada no Windows.

## Destino existente

- Ausente: instala normalmente.
- Presente e idêntico: retorna `already-valid` e evita reinstalação.
- Presente e divergente: falha sem alterar arquivos.
- Presente e divergente com `--replace`: restaura, valida e troca com rollback.

`--verify` nunca promove, substitui ou executa os syncs. `--sync-web` é sempre
explícito e apenas delega aos scripts existentes.

## Segurança do ZIP e do download

Antes da escrita são rejeitados:

- caminhos absolutos, drive letters, UNC, barras invertidas e `..`;
- entradas duplicadas, symlinks, diretórios explícitos e arquivos extras;
- manifest ou `SHA256SUMS` ausentes ou divergentes;
- criptografia e métodos de compressão não permitidos;
- contagem, tamanhos individuais ou tamanho total diferentes dos controles;
- qualquer hash científico divergente.

O download usa somente HTTPS, streaming com limite de tamanho e timeout. Status
fora de 2xx, `Content-Length` divergente, redirecionamento final não HTTPS,
arquivo parcial ou hash incorreto interrompem a execução e removem a cópia
temporária.

## Prova em ambiente limpo

A Fase 15C.5 validou o fluxo em um segundo workspace sem `data/serving`, sem
`dist` e sem cópia manual de dados do workspace original. O ZIP foi obtido pela
URL pública da Release, validado integralmente, promovido para `data/serving` e
sincronizado para `web/public/data/serving`. Dependências instaladas pelos
lockfiles, lint, testes, build e smoke test confirmaram a aplicação executável.

Essa prova estabelece a reprodutibilidade do produto: Git, dependências
versionadas, snapshot publicado e bootstrap produzem a aplicação buildável. Ela
não afirma que o pipeline científico bruto inteiro seja reproduzível pelo Git;
`data/raw`, `data/interim` e `data/processed` continuam fora desse escopo.
