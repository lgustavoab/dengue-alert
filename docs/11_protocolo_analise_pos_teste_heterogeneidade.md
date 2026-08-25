# Protocolo da Análise Pós-Teste de Heterogeneidade

## 1. Objetivo

Esta etapa investiga se o desempenho do modelo final varia entre diferentes
grupos de municípios brasileiros.

A análise é realizada após a avaliação final independente de 2025.

Portanto, seus resultados possuem caráter:

**secundário, descritivo e pós-teste**

Nenhum resultado desta etapa poderá ser utilizado para modificar e reavaliar
no mesmo conjunto final:

- algoritmo;
- features;
- hiperparâmetros;
- calibração;
- thresholds;
- definição do target;
- regra de early warning.

Os resultados oficiais da avaliação final de 2025 permanecem aqueles
registrados anteriormente.

---

# 2. Modelo analisado

Será analisada exclusivamente a estratégia final já congelada:

**HistGradientBoostingClassifier**

Features:

**Modelo A — 23 features epidemiológicas**

Probabilidades:

**raw**

Calibração adicional:

**não adotada**

Thresholds operacionais:

| Horizonte | Threshold |
| --- | ---: |
| H1 | 0,187687 |
| H2 | 0,190783 |
| H3 | 0,167991 |
| H4 | 0,157138 |

Nenhum novo treinamento será realizado nesta análise.

---

# 3. Fonte das predições

A análise utilizará diretamente as predições produzidas durante a primeira
avaliação final de 2025:

`data/processed/predicoes_avaliacao_final_2025.parquet`

Esse arquivo contém as probabilidades e classes previstas originalmente.

As predições não serão recalculadas.

---

# 4. Perspectivas de heterogeneidade

Serão avaliadas quatro dimensões previamente definidas:

1. macrorregião brasileira;
2. unidade federativa;
3. porte populacional;
4. perfil epidemiológico histórico.

A análise será realizada separadamente para H1, H2, H3 e H4.

---

# 5. Macrorregião

As unidades federativas serão agrupadas nas cinco macrorregiões oficiais:

- Norte;
- Nordeste;
- Centro-Oeste;
- Sudeste;
- Sul.

O Distrito Federal será considerado integrante do Centro-Oeste.

Essa análise permitirá verificar se a capacidade preditiva apresenta diferenças
geográficas amplas.

---

# 6. Unidade federativa

Também serão produzidas métricas individualizadas para cada UF.

O objetivo é identificar heterogeneidade que possa ficar escondida na
agregação por região.

Resultados com baixa quantidade de eventos positivos deverão ser interpretados
com cautela.

Nenhuma UF será excluída pelo nível de desempenho observado.

---

# 7. Porte populacional

O porte municipal será definido a partir da população utilizada na semana da
previsão.

Os grupos serão fixados previamente como:

| Grupo | População |
| --- | ---: |
| Muito pequeno | menor que 20.000 |
| Pequeno | 20.000 a 49.999 |
| Médio | 50.000 a 99.999 |
| Grande | 100.000 a 499.999 |
| Muito grande | 500.000 ou mais |

Essas faixas serão utilizadas apenas para análise descritiva.

O modelo não será reestimado por porte populacional.

---

# 8. Perfil epidemiológico histórico

Será criada uma caracterização municipal utilizando exclusivamente o período
anterior ao teste final.

Para cada município será calculada a:

**incidência semanal média por 100 mil habitantes entre 2018 e 2024**

Os municípios serão classificados em quartis nacionais:

- Q1 — carga histórica mais baixa;
- Q2;
- Q3;
- Q4 — carga histórica mais alta.

Os quartis serão calculados apenas com dados de 2018–2024.

Nenhuma informação epidemiológica agregada de 2025 será utilizada para definir
esses grupos.

Essa variável será utilizada exclusivamente para análise pós-teste e não será
adicionada ao modelo.

---

# 9. Métricas por grupo

Para cada grupo e horizonte serão registrados:

- número de observações;
- número de municípios;
- número de positivos;
- prevalência;
- Average Precision;
- ROC-AUC;
- Brier Score;
- precision;
- recall;
- F1;
- balanced accuracy;
- quantidade de alertas;
- proporção de alertas;
- true positives;
- false positives;
- true negatives;
- false negatives.

---

# 10. Early warning

Todas as dimensões também serão analisadas no subconjunto:

`risco_elevado(t) = False`

Serão calculadas as mesmas métricas sempre que houver suporte amostral
suficiente.

A análise de early warning continuará sendo particularmente importante porque
representa situações em que o município ainda não estava classificado em risco
elevado no momento da previsão.

---

# 11. Suporte amostral

Métricas de classificação podem ser instáveis em grupos pequenos.

Por esse motivo, cada resultado deverá registrar explicitamente:

- quantidade de observações;
- quantidade de municípios;
- quantidade de positivos;
- quantidade de negativos.

Average Precision e ROC-AUC somente serão interpretadas quando houver suporte
das duas classes necessário para a respectiva métrica.

Resultados de grupos pequenos serão apresentados como descritivos e deverão
ser interpretados com cautela.

Não serão removidos grupos apenas porque apresentaram desempenho ruim.

---

# 12. Comparação entre grupos

A análise buscará responder questões como:

- o desempenho se mantém nas cinco regiões?
- municípios pequenos apresentam comportamento diferente dos maiores?
- regiões de maior carga histórica de dengue apresentam desempenho distinto?
- existem UFs com degradação particularmente relevante?
- o comportamento muda conforme aumenta o horizonte de previsão?

As comparações serão descritivas.

Não serão realizadas afirmações causais a partir dessas diferenças.

---

# 13. Interpretação das diferenças

Uma diferença de desempenho entre grupos não demonstra que a característica
utilizada para formar o grupo seja a causa da diferença.

Por exemplo, desempenho menor em determinado porte populacional pode refletir
simultaneamente:

- menor quantidade absoluta de eventos;
- maior volatilidade das taxas;
- características regionais;
- qualidade das notificações;
- dinâmica epidemiológica distinta.

A análise identificará heterogeneidade, mas não estabelecerá causalidade.

---

# 14. Relação com o teste final

A avaliação global de 2025 permanece a estimativa principal de generalização
temporal.

As análises por grupo servem para decompor esse resultado e investigar onde o
desempenho foi mais ou menos favorável.

Nenhuma média de subgrupos substituirá os resultados gerais já registrados.

---

# 15. Artefatos previstos

Serão gerados resultados em:

`reports/audits/heterogeneidade_2025_regiao.csv`

`reports/audits/heterogeneidade_2025_uf.csv`

`reports/audits/heterogeneidade_2025_porte_populacional.csv`

`reports/audits/heterogeneidade_2025_perfil_epidemiologico.csv`

e uma auditoria consolidada:

`reports/audits/heterogeneidade_2025.json`

A caracterização histórica dos municípios poderá ser persistida em:

`data/processed/perfil_epidemiologico_municipios_2018_2024.parquet`

Esse arquivo permanecerá fora do Git.

---

# 16. Estado metodológico desta etapa

Esta análise ocorre depois da abertura oficial do teste final.

Assim:

- 2025 já é um conjunto observado;
- seus resultados não poderão orientar retreinamento do modelo final;
- thresholds permanecerão congelados;
- análises adicionais serão identificadas como pós-teste;
- o resultado final oficial continuará sendo o registrado na primeira
  avaliação de 2025.

O próximo passo será implementar a análise de heterogeneidade de forma
reprodutível.