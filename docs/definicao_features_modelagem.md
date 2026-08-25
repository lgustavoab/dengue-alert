# Definição das Features de Modelagem — Dengue Alert

## 1. Objetivo

Este documento registra a especificação inicial das variáveis preditoras utilizadas
nos modelos do projeto Dengue Alert.

A definição das features ocorre antes do treinamento dos modelos e antes da abertura
dos resultados do conjunto de teste final de 2025.

O objetivo é evitar seleção retrospectiva de variáveis baseada no desempenho do
teste final e manter uma separação clara entre:

- construção dos preditores;
- definição do alvo;
- treinamento;
- validação;
- teste final.

A unidade de observação permanece sendo:

- município;
- semana epidemiológica.

Para uma observação na semana `t`, todas as features devem ser conhecidas em `t`
ou pertencer ao passado.

Nenhuma feature poderá utilizar informação de:

- `t + 1`;
- `t + 2`;
- `t + 3`;
- `t + 4`;
- qualquer outro instante posterior à semana de referência.

---

## 2. Momento da previsão

A previsão será interpretada como realizada ao final de uma semana epidemiológica
já concluída.

Portanto, informações observadas durante a própria semana `t` poderão ser
utilizadas como preditores.

Isso inclui:

- casos registrados na semana `t`;
- incidência da semana `t`;
- temperatura observada na semana `t`;
- umidade observada na semana `t`;
- precipitação observada na semana `t`.

Os horizontes representam então o risco epidemiológico em semanas futuras:

```text
t + 1
t + 2
t + 3
t + 4