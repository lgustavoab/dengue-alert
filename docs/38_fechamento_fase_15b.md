# Fechamento da Fase 15B — Polimento e consistência

## 1. Objetivo

Alinhar a Home às quatro superfícies do produto, tornar a navegação atual identificável e acessível, corrigir os achados proporcionais de acessibilidade e eliminar inconsistências textuais residuais sem alterar ciência, contratos ou lógica funcional.

## 2. Escopo concluído

- 15B.1 — auditoria de UX e consistência;
- 15B.2 — alinhamento da Home às quatro superfícies;
- 15B.3 — navegação ativa, semântica e comportamento mobile;
- 15B.4 — contraste de microtextos, skip link, landmarks e regiões roláveis;
- 15B.5 — correção da ocorrência conhecida de “contrato serving atual” no Histórico e regressão consolidada;
- 15B.5a — remoção do jargão público residual em Dados & Qualidade e no resumo municipal de risco do Histórico.

## 3. Home

A Home apresenta “Quatro perspectivas complementares” e quatro destinos: Histórico, Dados & Qualidade, Predição e Mapa preditivo. O mapa aponta para `/mapa`, a avaliação permanece explicitamente retrospectiva de 2025 e não foram adicionadas métricas artificiais.

## 4. Navegação

As cinco rotas possuem exatamente um `aria-current="page"`, com correspondência segura de pathname. O rótulo curto “Mapa” permanece no header, enquanto “Mapa preditivo” permanece nos contextos descritivos. Em 390 × 844, o item ativo fica visível dentro da navegação horizontal sem criar overflow global.

## 5. Acessibilidade

O skip link é o primeiro foco relevante e transfere o foco para `#main-content`. A aplicação mantém um único landmark `main`; estados de erro e carregamento preservam `role="alert"` e `role="status"` sem criar `main` aninhado. As regiões roláveis do panorama anual e da referência populacional são focáveis, nomeadas e mantêm o overflow restrito aos próprios wrappers. O token `--foreground-muted: #5f7077` conserva contraste mínimo de 4,5:1 nos três fundos auditados.

## 6. Consistência textual

A frase “O contrato serving atual...” foi substituída por uma explicação orientada ao usuário, preservando a limitação metodológica da visualização estadual. A referência ao “contrato de visão geral auditado” em Dados & Qualidade passou a indicar diretamente que os valores vêm de dados previamente auditados.

No resumo municipal de risco, as referências a “contrato” e “contrato serving” foram substituídas por explicações diretas sobre o período histórico elegível e a disponibilidade do resumo. A varredura final das cinco superfícies não encontrou outro jargão de implementação visível ao usuário. O bloqueio textual da 15B.5 está resolvido.

## 7. Validações

- Ruff: lint aprovado e 125 arquivos formatados corretamente;
- Python: 179 testes aprovados;
- frontend: lint aprovado, 27 Test Files e 202 testes aprovados;
- build: cinco páginas estáticas e cinco Route Handlers geradas;
- navegador: cinco rotas aprovadas em 1280 × 720 e 390 × 844, sem overflow horizontal global nem erros de console;
- UTF-8: 117 arquivos frontend lidos estritamente, sem mojibake real.

## 8. Não regressão

As alterações da Fase 15B não modificaram `score`, `predicao`, thresholds, H1–H4, target, `risco_elevado`, `early_warning`, categorias de severidade, interpretação climática ou o caráter retrospectivo de 2025. Falhas técnicas permanecem distintas dos estados epidemiológicos. O combobox do mapa continua funcional.

## 9. Pendências deliberadas

- 15C — distribuição dos aproximadamente 280 MB decimais de serving canônico, reprodução em clone limpo, assets derivados, CI, deployment e revisão de dependências, incluindo Next.js;
- 15D — README raiz, `web/README` e instruções públicas de instalação, execução e deployment;
- 15E — regressão candidata a release e revisões científica, de produção e da versão candidata.

## 10. Critério de aceite

A regressão técnica, visual e científica está aprovada, a copy pública residual foi corrigida e a regressão textual final passou. A Fase 15B está funcionalmente encerrada e aprovada para encerramento formal.

## 11. Próxima fase

A próxima etapa prevista é a Fase 15C — produção e deployment, mantendo documentação pública e aceite final reservados, respectivamente, às fases 15D e 15E.
