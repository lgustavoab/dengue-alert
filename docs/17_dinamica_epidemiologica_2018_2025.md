# Dinâmica Epidemiológica do Risco Elevado — 2018–2025

## 1. Objetivo

Esta etapa caracteriza a dinâmica temporal do estado epidemiológico de risco
elevado nos municípios brasileiros.

Diferentemente das análises anteriores, que avaliaram principalmente:

- número de casos;
- incidência;
- sazonalidade;
- distribuição espacial;

esta etapa investiga:

**duração, persistência e recorrência dos períodos de risco elevado.**

A análise utiliza exatamente a definição oficial de risco epidemiológico já
adotada pelo projeto Dengue Alert.

Nenhum novo critério de risco foi criado para esta etapa.

---

# 2. Período analisado

O período epidemiológico analisado foi:

**2018–2025**

Os anos 2016 e 2017 permanecem importantes para o histórico utilizado na
construção dos primeiros limiares sazonais, mas não possuem o mesmo target
retrospectivo elegível utilizado nesta análise.

Assim, não foi criada uma regra alternativa apenas para estender
artificialmente a análise até 2016.

---

# 3. Definição de risco elevado

O estado utilizado foi o target oficial:

`risco_elevado`

definido quando:

`incidencia_4s_100mil > limiar_sazonal_p90`

O limiar corresponde ao percentil 90 da distribuição sazonal histórica
municipal, utilizando somente anos anteriores e a janela epidemiológica
previamente estabelecida pelo projeto.

---

# 4. Definição de episódio

Foi definido como episódio de risco elevado:

**uma sequência máxima de semanas consecutivas, separadas por exatamente sete
dias, nas quais risco_elevado=True para o mesmo município.**

Um episódio pode atravessar a mudança de ano epidemiológico.

Ele somente é encerrado quando:

- ocorre uma semana com risco_elevado=False; ou
- existe uma ruptura real na sequência temporal elegível.

A mudança de ano não encerra artificialmente um episódio.

---

# 5. Elegibilidade dos dados

Foram concatenados os targets de:

- desenvolvimento 2018–2024;
- avaliação final 2025.

Total de observações:

**2.327.895**

Observações com risco definido:

**2.327.842**

Observações sem target elegível:

**53**

Todas as 53 observações sem target pertencem exclusivamente a:

**Boa Esperança do Norte/MT — código IBGE 5101837**

Essas observações não foram convertidas artificialmente para risco=False.

Municípios efetivamente elegíveis:

**5.569**

Cada um possui:

**418 semanas elegíveis**

---

# 6. Semanas em risco elevado

No período foram identificadas:

**414.678 município-semanas em risco elevado**

Essas semanas correspondem ao estado epidemiológico definido pelo limiar
sazonal municipal e não simplesmente à existência de casos de dengue.

---

# 7. Quantidade de episódios

Foram identificados:

**54.269 episódios de risco elevado**

A duração acumulada dos episódios preservou exatamente as:

**414.678 semanas em risco**

validando a reconstrução das sequências temporais.

---

# 8. Distribuição da duração

A duração dos episódios apresentou distribuição fortemente assimétrica.

| Estatística | Duração em semanas |
| --- | ---: |
| Mínimo | 1 |
| P25 | 3 |
| P50 | 4 |
| P75 | 9 |
| P90 | 19 |
| P95 | 26 |
| P99 | 41 |
| Máximo | 110 |

Duração média:

**7,64 semanas**

Duração mediana:

**4 semanas**

A diferença entre média e mediana demonstra a influência de uma cauda de
episódios persistentemente longos.

A maioria dos episódios possui duração relativamente curta, enquanto uma
parcela pequena persiste por muitos meses.

---

# 9. Episódios extremamente longos

O episódio mais longo ocorreu em:

**Florianópolis/SC**

Início:

**27/02/2022**

Fim:

**31/03/2024**

Duração:

**110 semanas**

Outros episódios de longa duração incluíram:

| Município | UF | Duração |
| --- | --- | ---: |
| Porto Alegre | RS | 107 semanas |
| Iguaba Grande | RJ | 100 semanas |
| Campos dos Goytacazes | RJ | 99 semanas |
| Camboriú | SC | 95 semanas |
| Linhares | ES | 94 semanas |
| Itajaí | SC | 94 semanas |
| Gravataí | RS | 93 semanas |
| São Francisco do Sul | SC | 92 semanas |
| Marília | SP | 87 semanas |
| Londrina | PR | 86 semanas |

Esses resultados demonstram que episódios persistentes não se restringem a um
único município.

---

# 10. Interpretação dos episódios longos

Um episódio longo deve ser interpretado como:

**persistência do estado risco_elevado segundo a definição sazonal do projeto.**

Isso não demonstra necessariamente que todo o período represente uma única
onda epidemiológica biologicamente homogênea.

O episódio indica apenas que a incidência acumulada em quatro semanas
permaneceu continuamente acima do respectivo limiar sazonal histórico.

Por esse motivo, os termos episódio de risco e onda epidemiológica não serão
tratados como sinônimos automáticos.

---

# 11. Episódios atravessando anos

Foram identificados:

**3.552 episódios que atravessaram a mudança de ano epidemiológico**

Essas sequências foram preservadas como episódios únicos quando as semanas
permaneceram consecutivas e em risco elevado.

Essa regra evita fragmentar artificialmente períodos persistentes apenas pela
mudança de calendário.

---

# 12. Municípios com algum risco

Dos 5.569 municípios elegíveis:

**5.553 apresentaram pelo menos uma semana em risco elevado**

Apenas:

**16 municípios**

não apresentaram risco elevado em nenhum dos oito anos avaliados.

---

# 13. Recorrência multianual

Foram identificados:

**5.466 municípios**

com risco elevado em pelo menos dois anos diferentes.

A distribuição completa foi:

| Anos com risco | Municípios |
| --- | ---: |
| 0 | 16 |
| 1 | 87 |
| 2 | 208 |
| 3 | 451 |
| 4 | 776 |
| 5 | 1.242 |
| 6 | 1.392 |
| 7 | 1.061 |
| 8 | 336 |

O grupo individual mais numeroso foi o de municípios que apresentaram algum
risco elevado em:

**6 dos 8 anos analisados**

com:

**1.392 municípios**

A recorrência é, portanto, uma característica amplamente disseminada.

---

# 14. Pico simultâneo nacional

O maior número de municípios simultaneamente em risco ocorreu em:

**2024 — semana epidemiológica 12**

Data inicial da semana:

**17/03/2024**

Municípios simultaneamente em risco:

**3.121**

Proporção dos municípios elegíveis:

**56,04%**

Assim, em uma única semana, mais da metade dos municípios brasileiros
elegíveis estavam simultaneamente acima de seus próprios limiares sazonais
históricos.

---

# 15. Dinâmica regional em 2024

O caráter excepcional de 2024 também aparece na análise regional.

| Região | Municípios com algum risco | Proporção das município-semanas em risco |
| --- | ---: | ---: |
| Norte | 73,56% | 21,35% |
| Nordeste | 78,58% | 19,48% |
| Centro-Oeste | 82,01% | 28,84% |
| Sudeste | 96,70% | 50,06% |
| Sul | 95,05% | 40,32% |

Sudeste e Sul apresentaram uma expansão particularmente ampla e persistente do
estado de risco.

No Sudeste, aproximadamente metade de todas as combinações município-semana de
2024 ficaram classificadas como risco elevado.

---

# 16. Comparação entre 2024 e 2025

A intensidade dinâmica diminuiu consideravelmente em 2025.

No Sudeste:

| Indicador | 2024 | 2025 |
| --- | ---: | ---: |
| Municípios com risco | 96,70% | 73,02% |
| Município-semanas em risco | 50,06% | 15,32% |

No Sul:

| Indicador | 2024 | 2025 |
| --- | ---: | ---: |
| Municípios com risco | 95,05% | 63,98% |
| Município-semanas em risco | 40,32% | 10,76% |

A redução é compatível com a queda do volume nacional observada anteriormente.

Entretanto, 2025 continuou apresentando atividade epidemiológica importante.

---

# 17. Heterogeneidade regional

A dinâmica não foi uniforme entre as regiões.

Em determinados anos o Centro-Oeste apresentou proporções particularmente
elevadas de municípios em risco.

Em 2022, por exemplo:

**91,86% dos municípios da região tiveram algum risco elevado**

e:

**34,16% das município-semanas ficaram em risco**

Em 2024, a maior expansão relativa ocorreu principalmente no Sudeste e no Sul.

Assim, diferentes anos epidêmicos possuem distribuições territoriais distintas.

---

# 18. Duração típica e duração extrema

Os resultados demonstram a importância de distinguir:

**episódio típico**

de

**episódio extremo**

A mediana de quatro semanas descreve melhor a experiência central da
distribuição.

Entretanto, os percentis superiores mostram episódios substancialmente mais
persistentes:

- P90: 19 semanas;
- P95: 26 semanas;
- P99: 41 semanas.

Os episódios superiores a 80 semanas representam eventos extremos da
distribuição e não devem ser utilizados para descrever a duração típica.

---

# 19. Implicações para o dashboard histórico

A dinâmica epidemiológica permite adicionar ao dashboard indicadores que não
aparecem em simples contagens de casos.

Funcionalidades candidatas incluem:

**por município**

- número de episódios;
- semanas totais em risco;
- episódio mais longo;
- anos com algum risco;
- recorrência multianual;
- histórico temporal dos episódios.

**em escala nacional/regional**

- municípios simultaneamente em risco;
- proporção do território em risco;
- evolução semanal;
- comparação entre anos;
- comparação entre regiões.

---

# 20. Visualizações candidatas

Entre as visualizações mais úteis estão:

**Série nacional de municípios simultaneamente em risco**

Permitirá observar expansão e retração territorial das grandes epidemias.

**Timeline municipal de episódios**

Permitirá mostrar em quais períodos determinado município permaneceu acima de
seu limiar sazonal.

**Distribuição da duração dos episódios**

Permitirá demonstrar a assimetria entre episódios típicos e persistentes.

**Comparação anual por região**

Permitirá mostrar a proporção de municípios e de município-semanas em risco.

---

# 21. Responsividade

As visualizações destinadas ao frontend serão desenvolvidas de maneira
responsiva.

Em dispositivos móveis, timelines longas não deverão simplesmente ser
reduzidas proporcionalmente.

Poderão ser utilizados:

- seleção de período;
- zoom temporal;
- filtros compactos;
- painel expansível de detalhes;
- tooltips;
- reorganização vertical dos componentes.

A prioridade será preservar legibilidade e interação em diferentes tamanhos de
tela.

---

# 22. Limitações

O estado de risco elevado é uma definição operacional construída a partir da
incidência histórica municipal.

Ele não representa diretamente:

- transmissão instantânea;
- gravidade clínica;
- hospitalizações;
- mortalidade;
- uma definição oficial de epidemia do Ministério da Saúde.

Além disso, episódios longos representam persistência acima do limiar sazonal
e não devem ser interpretados automaticamente como uma única onda
epidemiológica homogênea.

---

# 23. Relação com o modelo preditivo

Esta análise utiliza o mesmo estado epidemiológico que posteriormente foi
utilizado como base dos targets H1–H4.

Entretanto, a análise é exclusivamente histórica e descritiva.

Nenhum resultado desta etapa foi utilizado para:

- alterar a definição do target;
- modificar features;
- recalibrar probabilidades;
- modificar thresholds operacionais;
- retreinar o modelo final.

---

# 24. Artefatos

Episódios:

`reports/audits/episodios_risco_elevado_2018_2025.csv`

Resumo municipal:

`reports/audits/dinamica_risco_municipio_2018_2025.csv`

Série semanal nacional e regional:

`reports/audits/serie_risco_semanal_nacional_regional_2018_2025.csv`

Resumo ano × região:

`reports/audits/dinamica_risco_ano_regiao_2018_2025.csv`

Auditoria:

`reports/audits/dinamica_epidemiologica_2018_2025.json`

Scripts:

`scripts/analisar_dinamica_epidemiologica.py`

`scripts/resumir_dinamica_epidemiologica.py`

---

# 25. Próxima etapa

A próxima etapa será a análise descritiva de clima e dengue.

Serão avaliadas as relações entre:

- temperatura;
- umidade relativa;
- precipitação;
- atividade epidemiológica;
- defasagens temporais.

Essa análise terá caráter associativo e não será interpretada como evidência de
causalidade.

Status desta etapa:

**APROVADO**