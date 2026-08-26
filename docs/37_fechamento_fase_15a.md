# Fechamento da Fase 15A — Auditoria e correções estruturais

## 1. Objetivo

Consolidar as correções estruturais identificadas na auditoria final da aplicação e confirmar que as cinco superfícies principais continuam funcionais, sem alterar os contratos científicos ou de serving.

## 2. Escopo concluído

- 15A.1 — inventário e auditoria;
- 15A.2 — correção do encoding textual do dashboard histórico;
- 15A.3 — tratamento isolado da falha de recorte preditivo do mapa;
- 15A.4 — implementação da superfície Dados & Qualidade;
- 15A.5 — estados de erro e carregamento das rotas;
- 15A.6 — regressão consolidada e fechamento formal.

## 3. Correções realizadas

- remoção de mojibake comprovado no dashboard histórico, com regressão específica de encoding;
- separação entre erro técnico, carregamento e estados epidemiológicos no mapa, sem reutilização silenciosa do recorte anterior;
- substituição do placeholder de `/dados-qualidade` por uma visão baseada nos cinco contratos auditados, preservando as semânticas de `NDUPLIC_N`, zero-fill e cobertura climática;
- correção responsiva da nova superfície;
- inclusão de cinco error boundaries com o contrato oficial `reset` do App Router e de loading states somente nas três rotas assíncronas segmentadas.

## 4. Validações executadas

- Python: Ruff aprovou 87 arquivos no lint e 124 arquivos na verificação de formato; pytest aprovou 179 testes;
- frontend: lint aprovado; 25 Test Files e 185 testes aprovados; build de produção aprovado;
- build: páginas `/`, `/historico`, `/dados-qualidade`, `/predicao` e `/mapa` geradas, além das cinco Route Handlers existentes;
- navegador: as cinco superfícies renderizaram com títulos corretos, sem placeholder indevido, sem erro de console e sem overflow horizontal global nas medições desktop e mobile;
- Git: `git diff --check` previsto como critério final antes do aceite.

## 5. Não regressão científica

A auditoria confirmou que `score`, `predicao`, `threshold`, `target`, `risco_elevado`, `early_warning` e H1–H4 mantêm os significados definidos pelos contratos. A interface continua usando `predicao` como classificação oficial, sem criar categorias de severidade, confundir falha técnica com estado epidemiológico ou atribuir interpretação causal à cobertura climática.

## 6. Estado atual da aplicação

As cinco superfícies principais estão funcionais e cobertas pelas regressões executadas. A Fase 15A está funcionalmente encerrada.

O produto ainda não está pronto para deployment em clone limpo. `data/serving` permanece ignorado pelo Git e contém aproximadamente 280 MB de contratos canônicos, enquanto os assets públicos de serving são derivados. Isso não constitui falha da Fase 15A; o tema está formalmente encaminhado para a Fase 15C.

## 7. Pendências deliberadas

- 15B — atualização da Home, rota ativa e refinamentos de navegação/UX, consistência visual e textual e eventual cobertura adicional de acessibilidade;
- 15C — estratégia de artefatos e deployment, reprodução em clone limpo, CI e revisão de dependências de produção, incluindo Next.js;
- 15D — atualização do README raiz, de `web/README` e das instruções públicas de execução e arquitetura;
- 15E — regressão final, revisão científica, revisão de produção e preparação da versão candidata.

## 8. Critério de aceite

A fase é aceita com regressões Python e frontend aprovadas, build concluído, cinco superfícies funcionais, invariantes científicos preservados, varredura UTF-8 sem mojibake real e diff restrito ao escopo das correções estruturais e deste fechamento.

## 9. Próxima fase

A sequência prevista é a Fase 15B — polimento e consistência. Os bloqueios de produção e clone limpo permanecem reservados à Fase 15C.
