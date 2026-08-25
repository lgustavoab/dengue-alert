# Protocolo da Avaliação Final de 2025

## 1. Objetivo

Este documento define, antes da abertura do conjunto final de teste, o protocolo
da avaliação final do modelo preditivo do projeto Dengue Alert.

O objetivo é medir a capacidade de generalização temporal da estratégia
selecionada durante o desenvolvimento utilizando exclusivamente dados de 2025.

Nenhum resultado de 2025 foi utilizado para selecionar:

- algoritmo;
- conjunto de features;
- uso ou não de meteorologia;
- estratégia de calibração;
- thresholds operacionais.

As decisões anteriores encontram-se congeladas antes desta avaliação.

---

# 2. Separação temporal

O desenvolvimento do modelo utilizou dados anteriores a 2025.

O ano de:

**2025**

constitui o conjunto final de teste.

A avaliação final será realizada apenas uma vez após o congelamento completo da
estratégia de modelagem.

Resultados de 2025 não poderão ser utilizados posteriormente para reajustar o
modelo e produzir uma nova estimativa de desempenho final no mesmo conjunto.

---

# 3. Estratégia final congelada

## Algoritmo

**HistGradientBoostingClassifier**

Configuração:

- `learning_rate = 0.1`;
- `max_iter = 100`;
- `early_stopping = False`;
- `random_state = 42`.

## Conjunto de features

**Modelo A — 23 features epidemiológicas**

O modelo final não utiliza as features meteorológicas avaliadas no Modelo B.

Também não utiliza latitude e longitude como preditores.

## Probabilidades

Serão utilizadas diretamente as probabilidades produzidas pelo
HistGradientBoosting:

**raw**

Nenhuma calibração adicional será aplicada.

---

# 4. Horizontes avaliados

Serão treinados e avaliados quatro modelos independentes:

- H1: risco elevado em +1 semana;
- H2: risco elevado em +2 semanas;
- H3: risco elevado em +3 semanas;
- H4: risco elevado em +4 semanas.

Cada horizonte possui seu próprio target e seu próprio threshold operacional.

---

# 5. Thresholds operacionais congelados

Os thresholds foram definidos exclusivamente com predições OOF de 2021–2024.

| Horizonte | Threshold |
| --- | ---: |
| H1 | **0,187687** |
| H2 | **0,190783** |
| H3 | **0,167991** |
| H4 | **0,157138** |

Esses valores não poderão ser reajustados após a abertura de 2025.

---

# 6. Treinamento definitivo

Para cada horizonte será treinado um HistGradientBoosting utilizando todo o
período de desenvolvimento disponível até o final de 2024.

A base de treinamento será formada apenas por observações cujo target do
respectivo horizonte permaneça integralmente dentro do período de
desenvolvimento.

Isso significa que observações do final de 2024 cujo target futuro atravesse a
fronteira para 2025 não poderão participar do treinamento.

Essa regra impede que informações provenientes do período final de teste sejam
utilizadas indiretamente durante o ajuste do modelo.

---

# 7. Elegibilidade do teste de 2025

Para cada horizonte serão avaliadas somente observações de 2025 cujo target
futuro esteja disponível dentro do próprio período final de teste.

Consequentemente, o número de observações poderá diminuir conforme aumenta o
horizonte.

Observações cujo target avançaria além do final de 2025 não serão avaliadas.

Nenhuma imputação ou inferência de targets futuros será realizada.

---

# 8. Métrica principal

A métrica principal da avaliação final continuará sendo:

**Average Precision (AP)**

A Average Precision mede a qualidade de ranqueamento das probabilidades e é
particularmente apropriada para problemas com classes desbalanceadas.

Ela será calculada separadamente para:

- H1;
- H2;
- H3;
- H4.

---

# 9. Métricas probabilísticas e de ranqueamento

Além da Average Precision, serão registradas:

- ROC-AUC;
- Brier Score.

O Brier Score será calculado sobre as probabilidades raw do modelo.

Nenhuma nova estratégia de calibração será testada utilizando 2025.

---

# 10. Métricas operacionais

Utilizando os thresholds previamente congelados, serão calculadas:

- precision;
- recall;
- F1;
- balanced accuracy;
- true positives;
- false positives;
- true negatives;
- false negatives;
- quantidade de alertas;
- proporção de alertas.

Essas métricas serão calculadas separadamente para cada horizonte.

---

# 11. Avaliação geral

A avaliação geral considerará todas as observações elegíveis do respectivo
horizonte.

Serão registrados:

- número de observações;
- número de positivos;
- prevalência;
- Average Precision;
- ROC-AUC;
- Brier Score;
- precision;
- recall;
- F1;
- balanced accuracy;
- matriz de confusão.

A prevalência de 2025 somente será conhecida e registrada no momento desta
avaliação final.

---

# 12. Avaliação de early warning

A avaliação operacional prioritária será realizada também no subconjunto:

`risco_elevado(t) = False`

Esse subconjunto representa municípios que ainda não estavam em estado de risco
elevado no momento da previsão.

Para esse subconjunto serão registrados:

- observações;
- positivos futuros;
- prevalência;
- Average Precision;
- ROC-AUC;
- Brier Score;
- precision;
- recall;
- F1;
- balanced accuracy;
- matriz de confusão;
- quantidade de alertas;
- proporção de alertas.

Essa avaliação representa diretamente a capacidade de antecipar a entrada
futura em estado de risco elevado.

---

# 13. Baseline de persistência

O modelo final será comparado com o baseline de persistência previamente
definido.

O baseline assume:

> o estado de risco futuro será igual ao estado de risco atual.

A comparação será realizada para H1, H2, H3 e H4.

Serão comparadas principalmente:

- Average Precision;
- recall;
- precision;
- F1;
- balanced accuracy;
- Brier Score.

No subconjunto de early warning, o baseline de persistência não gera alerta
enquanto o município permanece fora do estado atual de risco.

Esse comportamento será preservado e registrado sem modificações.

---

# 14. Comparação entre horizontes

A avaliação final deverá responder como o desempenho varia conforme aumenta a
antecedência.

A interpretação será feita de forma progressiva:

- H1 versus H2;
- H2 versus H3;
- H3 versus H4.

O objetivo não é definir retrospectivamente um horizonte "aceitável" com base
em uma regra criada depois dos resultados.

Os resultados serão apresentados como evidência empírica da perda ou
manutenção da capacidade preditiva à medida que aumenta a antecedência.

---

# 15. Avaliação de heterogeneidade entre municípios

Após a avaliação principal, será realizada uma análise secundária e
estritamente descritiva da heterogeneidade de desempenho.

Essa análise não poderá alterar o modelo ou os thresholds.

Serão consideradas, quando houver tamanho amostral adequado, características
como:

- região geográfica;
- porte populacional;
- unidade federativa;
- perfil epidemiológico histórico.

O objetivo será investigar se o desempenho geral esconde diferenças importantes
entre grupos de municípios.

Essa análise será identificada explicitamente como análise secundária.

---

# 16. Comparação com as conclusões do desenvolvimento

Os resultados de 2025 serão comparados descritivamente com o comportamento
observado durante os folds temporais de desenvolvimento.

A comparação poderá indicar:

- manutenção do desempenho;
- melhora;
- degradação;
- alteração do equilíbrio entre precision e recall.

Não serão criados novos thresholds ou novos modelos para corrigir diferenças
observadas em 2025.

---

# 17. Interpretação do clima

A comparação entre Modelo A e Modelo B já foi realizada no período de
desenvolvimento.

O teste final operacional utilizará somente o Modelo A selecionado.

Portanto, 2025 não será utilizado para realizar nova seleção entre Modelo A e
Modelo B.

A conclusão sobre o valor incremental das features meteorológicas continuará
baseada no experimento temporal previamente realizado.

---

# 18. Artefatos da avaliação final

A execução deverá gerar, no mínimo:

### Resultados tabulares

- `reports/audits/avaliacao_final_2025.csv`;
- `reports/audits/avaliacao_final_2025.json`.

### Predições finais

Um arquivo Parquet contendo, por observação elegível:

- município;
- semana epidemiológica;
- horizonte;
- target real;
- probabilidade prevista;
- threshold aplicado;
- classe prevista;
- risco atual.

O arquivo de predições deverá permanecer em `data/processed/` e não será
versionado no Git.

### Modelos treinados

Os quatro modelos finais poderão posteriormente ser persistidos em `models/`
para uso pela aplicação.

A persistência dos modelos não será necessária para calcular a avaliação
científica inicial.

---

# 19. Proibição de reajuste após o teste

Depois que os resultados finais de 2025 forem conhecidos, não poderão ser
alterados com objetivo de melhorar esses resultados:

- features;
- algoritmo;
- hiperparâmetros;
- calibração;
- thresholds;
- definição do target;
- regra de early warning.

Qualquer experimento adicional realizado depois disso deverá ser identificado
como:

**análise exploratória pós-teste**

e não poderá substituir os resultados do teste final originalmente registrado.

---

# 20. Critério de conclusão da avaliação

A avaliação final será considerada concluída quando:

1. os quatro modelos H1–H4 forem treinados somente com dados elegíveis de
   desenvolvimento;
2. as predições de 2025 forem geradas;
3. todas as métricas previamente definidas forem calculadas;
4. o baseline de persistência for avaliado no mesmo conjunto;
5. os thresholds congelados forem aplicados sem modificação;
6. os resultados forem persistidos;
7. uma auditoria confirmar ausência de vazamento temporal;
8. os resultados forem documentados antes de qualquer experimento posterior.

---

# 21. Estado antes da abertura de 2025

No momento de criação deste protocolo:

- modelo final: congelado;
- features: congeladas;
- hiperparâmetros: congelados;
- calibração: congelada;
- thresholds: congelados;
- protocolo de avaliação: congelado;
- resultados de 2025: ainda não utilizados.

O próximo passo será implementar e auditar o script de avaliação final antes de
sua primeira execução.