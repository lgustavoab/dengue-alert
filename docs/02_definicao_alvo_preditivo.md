# Definição do Alvo Preditivo — Dengue Alert

## 1. Objetivo

O projeto Dengue Alert tem como objetivo desenvolver modelos capazes de antecipar
situações de risco epidemiológico elevado de dengue em municípios brasileiros.

A unidade de análise é o par:

- município;
- semana epidemiológica.

O problema preditivo será tratado como uma tarefa de classificação binária em
múltiplos horizontes temporais.

Para cada semana de referência `t`, o modelo deverá estimar a probabilidade de o
município apresentar risco epidemiológico elevado em:

- `t + 1` semana;
- `t + 2` semanas;
- `t + 3` semanas;
- `t + 4` semanas.

O objetivo não é prever diretamente o número absoluto de casos, mas identificar
antecipadamente semanas em que a incidência de dengue se encontra em nível
anormalmente elevado em relação ao comportamento histórico do próprio município.

---

## 2. Princípios utilizados para definir o alvo

A definição do alvo buscou atender aos seguintes critérios:

1. considerar diferenças populacionais entre municípios;
2. respeitar diferenças históricas próprias de cada município;
3. considerar a forte sazonalidade da dengue;
4. evitar um limite nacional arbitrário de casos ou incidência;
5. utilizar apenas informações historicamente disponíveis antes da semana avaliada;
6. produzir quantidade suficiente de eventos positivos para permitir modelagem;
7. manter interpretação epidemiológica clara;
8. impedir o uso de dados de 2025 durante a escolha metodológica do alvo.

Por esse motivo, a variável básica utilizada foi a incidência acumulada de dengue
em quatro semanas.

A incidência é calculada por:

\[
Incidência_{4s} =
\frac{Casos\ prováveis\ acumulados\ nas\ últimas\ 4\ semanas}
{População\ municipal}
\times 100.000
\]

A janela de quatro semanas reduz parte da volatilidade existente nas contagens
semanais, especialmente em municípios pequenos, sem eliminar completamente a
dinâmica temporal da doença.

---

## 3. Período utilizado para escolha do alvo

Toda a análise metodológica para definição do alvo foi realizada exclusivamente
com dados até 2024.

Período de desenvolvimento utilizado na investigação:

- 2016 a 2024.

Ano reservado para avaliação final:

- 2025.

Os dados de 2025 não participaram:

- da comparação entre definições candidatas;
- da escolha do percentil;
- da escolha da janela histórica;
- da decisão entre baseline móvel e baseline sazonal.

Dessa forma, o ano de 2025 permaneceu intocado durante a definição metodológica
do problema preditivo.

Depois que a regra do alvo foi congelada, ela poderá ser aplicada a 2025 para
construir os rótulos necessários à avaliação final.

---

## 4. Alternativas avaliadas

Foram investigadas duas formas principais de definir uma situação de incidência
anormalmente elevada.

### 4.1. Baseline histórico móvel

A primeira abordagem comparou a incidência acumulada das quatro semanas atuais
com os percentis da distribuição das 104 semanas anteriores do próprio município.

A regra experimental foi:

\[
Incidência_{4s}(t) >
P_q\left(Incidência_{4s}\ das\ 104\ semanas\ anteriores\right)
\]

Foram avaliados:

- P75;
- P80;
- P90.

O cálculo utilizou `shift(1)` antes da janela móvel, garantindo que a própria semana
avaliada não participasse da construção de seu limiar histórico.

Os resultados demonstraram que a prevalência dos eventos variava entre anos,
indicando que a definição não produzia mecanicamente uma proporção fixa de
positivos.

Entretanto, essa estratégia possui uma limitação importante para o objetivo do
projeto.

Durante períodos epidêmicos prolongados, semanas de incidência elevada passam a
integrar progressivamente as 104 semanas utilizadas como referência. Isso pode
elevar o próprio limiar histórico e fazer com que o baseline se adapte rapidamente
a uma epidemia em andamento.

---

## 5. Baseline histórico sazonal

A segunda abordagem considerou explicitamente a sazonalidade da dengue.

Para cada município, ano e semana epidemiológica, a incidência atual foi comparada
com observações de períodos equivalentes em anos anteriores.

A janela sazonal utilizada foi de:

- semana epidemiológica de referência ± 4 semanas.

Assim, para uma semana de referência, são consideradas semanas epidemiologicamente
próximas do mesmo período do ano.

O cálculo considera corretamente a transição entre início e fim do ano e a
existência de anos epidemiológicos com 52 ou 53 semanas.

Somente anos anteriores ao ano da observação atual são utilizados.

Não são utilizados dados futuros nem observações posteriores à semana cuja
referência histórica está sendo construída.

Foram exigidos:

- mínimo de 2 anos anteriores;
- mínimo de 12 observações históricas válidas.

Também foram avaliados:

- P75;
- P80;
- P90.

---

## 6. Resultados dos candidatos sazonais

A análise sazonal produziu 2.032.685 observações elegíveis no período de 2018 a
2024, abrangendo 5.569 unidades municipais elegíveis para a análise climática.

### P75 sazonal

- eventos positivos: 552.428;
- prevalência: 27,18%;
- municípios com pelo menos um evento: 5.551;
- municípios sem evento: 18.

### P80 sazonal

- eventos positivos: 500.923;
- prevalência: 24,64%;
- municípios com pelo menos um evento: 5.551;
- municípios sem evento: 18.

### P90 sazonal

- eventos positivos: 377.275;
- prevalência: 18,56%;
- municípios com pelo menos um evento: 5.548;
- municípios sem evento: 21.

O P90 apresentou uma classe positiva suficientemente frequente para modelagem,
mas mais seletiva que P75 e P80.

---

## 7. Comportamento temporal do P90 sazonal

A prevalência anual do P90 sazonal foi:

| Ano | Semanas elegíveis | Eventos positivos | Prevalência |
| --- | ---: | ---: | ---: |
| 2018 | 289.588 | 24.755 | 8,55% |
| 2019 | 289.588 | 69.734 | 24,08% |
| 2020 | 295.157 | 41.812 | 14,17% |
| 2021 | 289.588 | 25.248 | 8,72% |
| 2022 | 289.588 | 63.069 | 21,78% |
| 2023 | 289.588 | 54.105 | 18,68% |
| 2024 | 289.588 | 98.560 | 34,03% |

A forte variação entre anos demonstra que o uso do P90 não produz uma classe
positiva artificialmente fixa em 10%.

O limiar corresponde ao histórico sazonal anterior, enquanto a incidência do ano
corrente pode apresentar comportamento substancialmente diferente.

Por isso, anos com maior intensidade epidemiológica podem apresentar uma proporção
muito superior a 10% de semanas classificadas como risco elevado.

---

## 8. Comportamento segundo porte populacional

Para o P90 sazonal, foram observadas as seguintes prevalências:

| Faixa populacional | Linhas | Positivos | Prevalência |
| --- | ---: | ---: | ---: |
| Até 20 mil habitantes | 1.391.973 | 237.759 | 17,08% |
| 20 mil a 100 mil | 522.502 | 108.642 | 20,79% |
| 100 mil a 500 mil | 101.417 | 26.767 | 26,39% |
| Mais de 500 mil | 16.793 | 4.107 | 24,46% |

A diferença entre os grupos não foi artificialmente removida.

A definição já controla parcialmente o porte municipal por utilizar incidência por
100 mil habitantes e um baseline histórico específico de cada município.

Diferenças residuais entre portes serão tratadas como característica a ser
investigada durante a avaliação do modelo.

Por isso, além da avaliação geral, as métricas preditivas deverão posteriormente
ser analisadas também de forma estratificada segundo faixas populacionais.

---

## 9. Comparação com o baseline móvel

Para permitir comparação metodologicamente justa, os dois métodos foram
considerados sobre o período comum elegível de 2018 a 2024.

As prevalências encontradas foram:

| Percentil | Baseline móvel de 104 semanas | Baseline sazonal |
| --- | ---: | ---: |
| P75 | 22,74% | 27,18% |
| P80 | 19,91% | 24,64% |
| P90 | 13,09% | 18,56% |

A maior prevalência do método sazonal não foi considerada isoladamente como
vantagem ou desvantagem.

A escolha foi baseada principalmente em sua interpretação metodológica.

O baseline sazonal compara o período atual com épocas equivalentes dos anos
anteriores. Dessa forma, uma epidemia prolongada não eleva rapidamente seu próprio
limiar de referência apenas porque as semanas imediatamente anteriores também
estavam elevadas.

Essa propriedade é particularmente adequada para um sistema destinado a
identificar períodos anormalmente elevados em relação ao padrão histórico sazonal
de cada município.

---

## 10. Definição escolhida

O alvo oficial do projeto foi definido como:

> Uma semana é considerada de risco epidemiológico elevado de dengue quando a
> incidência acumulada nas quatro semanas mais recentes supera o percentil 90 da
> distribuição histórica sazonal do próprio município, calculada utilizando uma
> janela de ±4 semanas epidemiológicas ao redor da semana avaliada, exclusivamente
> em anos anteriores, com no mínimo dois anos históricos e 12 observações válidas.

Formalmente:

\[
RiscoElevado(t) =
\begin{cases}
1, & \text{se } Incidência_{4s}(t) > P90_{sazonal}(t) \\
0, & \text{caso contrário}
\end{cases}
\]

A comparação utiliza estritamente o operador `>`.

Assim, quando o limiar histórico é zero, uma semana com incidência igual a zero não
é classificada como risco elevado.

---

## 11. Interpretação do alvo

O alvo representa um estado epidemiológico elevado.

Ele não representa necessariamente:

- o início exato de um surto;
- uma declaração oficial de epidemia;
- um diagnóstico individual;
- um número específico de casos futuros.

Um município pode permanecer classificado como risco elevado durante várias
semanas consecutivas.

Portanto, o modelo deverá responder à seguinte pergunta:

> Qual é a probabilidade de este município apresentar uma situação epidemiológica
> de dengue anormalmente elevada daqui a 1, 2, 3 ou 4 semanas?

Essa formulação é compatível com a aplicação futura do projeto, que deverá
apresentar previsões de risco municipal em múltiplos horizontes.

---

## 12. Diagnóstico de persistência do alvo

Depois da escolha do P90 sazonal, foi realizado um diagnóstico específico dos
episódios consecutivos de risco elevado.

Foram identificados:

- 47.728 episódios;
- 5.548 municípios com pelo menos um episódio;
- duração média de 7,90 semanas;
- duração mediana de 4 semanas;
- P75 de duração igual a 9 semanas;
- P90 de duração igual a 20 semanas;
- duração máxima observada de 110 semanas.

A distribuição das durações foi:

| Duração | Episódios |
| --- | ---: |
| 1 semana | 5.992 |
| 2 semanas | 4.112 |
| 3 semanas | 3.281 |
| 4 semanas | 12.950 |
| 5 a 7 semanas | 6.884 |
| 8 semanas ou mais | 14.509 |

Não foram observadas lacunas temporais na série utilizada para a identificação dos
episódios.

Os episódios mais longos também foram inspecionados individualmente.

O episódio máximo apresentou 110 semanas consecutivas classificadas como risco
elevado.

Essa duração não significa incidência constante ou número constante de casos.

Ela indica apenas que, durante aquele período, a incidência móvel de quatro semanas
permaneceu continuamente acima do P90 sazonal histórico utilizado como referência.

---

## 13. Persistência entre horizontes

A análise demonstrou forte persistência temporal do estado de risco.

| Horizonte | P(futuro elevado \| atual elevado) | P(futuro elevado \| atual normal) | Concordância entre estado atual e futuro |
| --- | ---: | ---: | ---: |
| +1 semana | 87,60% | 2,88% | 95,35% |
| +2 semanas | 78,23% | 5,08% | 91,83% |
| +3 semanas | 70,20% | 6,97% | 88,80% |
| +4 semanas | 63,05% | 8,65% | 86,11% |

Esses resultados demonstram que o estado atual de risco possui forte poder
preditivo por si só.

Consequentemente, uma elevada acurácia global não será suficiente para demonstrar
valor do modelo de aprendizado de máquina.

---

## 14. Baseline obrigatório de persistência

Os modelos preditivos deverão ser comparados contra um baseline simples de
persistência.

Para cada horizonte `h`:

\[
\widehat{RiscoElevado}(t+h) = RiscoElevado(t)
\]

Ou seja, o baseline assume que o estado observado atualmente continuará no
horizonte futuro.

Um modelo de aprendizado de máquina somente será considerado útil se demonstrar
ganho relevante em relação a esse baseline, especialmente na identificação
antecipada de novos estados de risco.

---

## 15. Avaliação geral e avaliação de alerta antecipado

A avaliação será realizada sob duas perspectivas complementares.

### 15.1. Avaliação geral

Considerará todas as observações elegíveis.

Ela medirá a capacidade do modelo de prever corretamente o estado futuro de risco,
independentemente de o município já estar ou não em condição elevada na semana de
referência.

### 15.2. Avaliação de alerta antecipado

Será realizada especificamente sobre observações em que:

\[
RiscoElevado(t) = 0
\]

Nesse subconjunto, o objetivo será avaliar se o modelo consegue antecipar municípios
que ainda estão em situação normal na semana `t`, mas que entrarão em risco elevado
em `t+h`.

Essa análise permite distinguir um sistema genuinamente antecipatório de um modelo
que apenas aprende a persistência de estados já elevados.

---

## 16. Construção dos horizontes preditivos

O alvo contemporâneo é:

```text
risco_elevado