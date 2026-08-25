# Avaliação Final Independente de 2025

## 1. Objetivo

Este documento registra a primeira avaliação final independente do sistema
preditivo Dengue Alert utilizando exclusivamente o conjunto de teste de 2025.

Antes da abertura desse conjunto já estavam congelados e versionados:

- algoritmo;
- conjunto de features;
- hiperparâmetros;
- estratégia de calibração;
- thresholds operacionais;
- métricas;
- protocolo de avaliação.

Nenhum resultado de 2025 participou dessas decisões.

---

# 2. Estratégia final avaliada

## Algoritmo

**HistGradientBoostingClassifier**

## Features

**Modelo A — 23 features epidemiológicas**

## Variáveis meteorológicas

Não utilizadas no modelo final.

## Calibração

Não adotada.

Foram utilizadas as probabilidades:

**raw**

## Thresholds

| Horizonte | Threshold |
| --- | ---: |
| H1 | 0,187687 |
| H2 | 0,190783 |
| H3 | 0,167991 |
| H4 | 0,157138 |

---

# 3. Separação temporal

Desenvolvimento:

**2018–2024**

Teste final:

**2025**

Para cada horizonte foram excluídas do treinamento observações cujo target
atravessaria a fronteira temporal entre desenvolvimento e teste.

Também foram excluídas da avaliação observações do final de 2025 cujo target
não estivesse disponível dentro do período final.

---

# 4. Auditoria das partições

| Horizonte | Linhas treino | Linhas teste |
| --- | ---: | ---: |
| H1 | 2.027.116 | 289.588 |
| H2 | 2.021.547 | 284.019 |
| H3 | 2.015.978 | 278.450 |
| H4 | 2.010.409 | 272.881 |

Total de predições finais:

**1.124.938**

Predições duplicadas:

**0**

Status da execução:

**APROVADO**

---

# 5. Resultados gerais

| Horizonte | AP modelo | AP persistência | Brier | F1 |
| --- | ---: | ---: | ---: | ---: |
| H1 | **0,922094** | 0,700813 | 0,026753 | 0,810414 |
| H2 | **0,822503** | 0,525659 | 0,045809 | 0,700092 |
| H3 | **0,703513** | 0,402206 | 0,062984 | 0,575388 |
| H4 | **0,546211** | 0,310807 | 0,080826 | 0,460495 |

O modelo superou o baseline de persistência em Average Precision nos quatro
horizontes.

Foi observada redução progressiva da capacidade preditiva conforme aumentou a
antecedência.

O Brier Score também aumentou progressivamente entre H1 e H4, indicando maior
dificuldade na previsão probabilística em horizontes mais distantes.

---

# 6. Avaliação de early warning

O subconjunto de early warning considera somente situações em que:

`risco_elevado(t) = False`

Portanto, representa municípios que ainda não estavam em estado de risco
elevado no momento da previsão.

| Horizonte | AP modelo | AP persistência | Precision | Recall | F1 | Alertas |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H1 | **0,261908** | 0,025254 | 0,273755 | 0,447541 | **0,339712** | 4,13% |
| H2 | **0,268569** | 0,043039 | 0,293377 | 0,414559 | **0,343596** | 6,08% |
| H3 | **0,242606** | 0,057879 | 0,249931 | 0,386391 | **0,303529** | 8,95% |
| H4 | **0,185209** | 0,070711 | 0,193252 | 0,416647 | **0,264037** | 15,25% |

O modelo apresentou capacidade de antecipação acima do baseline em todos os
horizontes.

Os melhores resultados operacionais ocorreram em H1 e H2.

H2 apresentou a maior Average Precision e o maior F1 de early warning no teste
final, embora as diferenças em relação a H1 tenham sido pequenas.

H3 manteve capacidade relevante de antecipação, porém com redução de Average
Precision e F1.

H4 permaneceu superior ao baseline, mas apresentou a menor precision e a maior
proporção de alertas entre os quatro horizontes.

---

# 7. Interpretação do baseline de early warning

No subconjunto de early warning, todos os registros possuem estado atual de
risco igual a falso.

Consequentemente, o baseline de persistência atribui score zero para todas as
observações.

Nesse cenário, sua Average Precision corresponde essencialmente à prevalência
positiva do subconjunto.

A superioridade do modelo sobre essa referência demonstra que as probabilidades
produzidas conseguem ordenar os futuros eventos de risco utilizando informação
disponível antes da entrada no estado elevado.

---

# 8. Comportamento conforme o horizonte

A avaliação final apresentou deterioração progressiva da capacidade geral de
previsão:

- H1: AP 0,922094;
- H2: AP 0,822503;
- H3: AP 0,703513;
- H4: AP 0,546211.

A avaliação de early warning apresentou comportamento semelhante, embora H2
tenha obtido resultado ligeiramente superior a H1:

- H1: AP 0,261908;
- H2: AP 0,268569;
- H3: AP 0,242606;
- H4: AP 0,185209.

Dessa forma, os resultados não indicam uma fronteira absoluta em que a
previsão deixe de funcionar.

Em vez disso, mostram perda progressiva de capacidade à medida que aumenta o
horizonte.

---

# 9. Resposta à questão de antecipação

Os resultados demonstram que o modelo é capaz de identificar risco
epidemiológico futuro antes que o município já esteja classificado em risco
elevado.

A capacidade operacional foi mais favorável nos horizontes de uma e duas
semanas.

Ainda foi identificado sinal preditivo em três e quatro semanas, porém com
redução de desempenho.

Assim, os resultados sustentam que a antecipação é possível, mas sua
confiabilidade diminui conforme aumenta a distância temporal da previsão.

---

# 10. Generalização temporal

O desempenho observado em 2025 foi inferior ao desempenho médio registrado nos
folds de desenvolvimento, principalmente nos horizontes mais longos.

Essa diferença demonstra a importância da existência de um conjunto temporal
independente.

O resultado final não será utilizado para reajustar o modelo.

Possíveis diferenças entre anos, regiões ou padrões epidemiológicos poderão ser
investigadas posteriormente apenas como análises secundárias e descritivas.

---

# 11. Valor das variáveis meteorológicas

A seleção entre Modelo A e Modelo B foi concluída antes da abertura de 2025.

O modelo final utilizou somente as features epidemiológicas.

Portanto, o teste final não foi utilizado para realizar nova comparação ou
seleção envolvendo variáveis climáticas.

A conclusão sobre o valor incremental do clima permanece baseada nos
experimentos temporais realizados no período de desenvolvimento.

---

# 12. Congelamento pós-teste

A partir desta avaliação, 2025 passa a constituir um conjunto de teste já
observado.

Os resultados não poderão ser utilizados para modificar e posteriormente
reavaliar no mesmo conjunto:

- algoritmo;
- features;
- hiperparâmetros;
- calibração;
- thresholds;
- definição do target;
- regra de early warning.

Experimentos posteriores serão identificados explicitamente como análises
exploratórias ou secundárias pós-teste.

Eles não substituirão os resultados registrados neste documento.

---

# 13. Artefatos

Resultados:

- `reports/audits/avaliacao_final_2025.csv`;
- `reports/audits/avaliacao_final_2025.json`.

Predições finais:

- `data/processed/predicoes_avaliacao_final_2025.parquet`.

Script:

- `scripts/avaliar_final_2025.py`.

O arquivo de predições permanece fora do versionamento Git.

Status:

**APROVADO**