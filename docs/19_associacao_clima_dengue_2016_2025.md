# Associação Descritiva entre Clima e Dengue — 2016–2025

## 1. Objetivo

Esta etapa investiga associações temporais entre condições meteorológicas e a
incidência de dengue nos municípios brasileiros.

A pergunta exploratória é:

**Existe uma defasagem temporal identificável entre alterações meteorológicas e
a incidência de dengue observada posteriormente?**

A análise possui caráter exclusivamente:

**descritivo e associativo**

e não será utilizada como evidência causal.

---

# 2. Protocolo previamente congelado

Antes da execução dos cálculos foi criado o protocolo:

`docs/18_protocolo_clima_dengue_2016_2025.md`

O protocolo congelou previamente:

- variáveis meteorológicas;
- desfecho epidemiológico;
- métrica de associação;
- conjunto de defasagens;
- regra de agregação;
- interpretação dos resultados.

As escolhas não foram modificadas após a observação das correlações.

---

# 3. Base utilizada

Foi utilizado o painel mestre:

`data/processed/painel_municipal_semanal_2016_2025.parquet`

Período:

**2016–2025**

Linhas totais:

**2.907.593**

Linhas com clima disponível:

**2.907.071**

Linhas sem clima:

**522**

Unidades territoriais com cobertura climática:

**5.570**

Fernando de Noronha permaneceu no painel histórico geral, mas não participou
desta análise em razão da ausência de cobertura ERA5-Land adotada pelo projeto.

---

# 4. Variável epidemiológica

O desfecho utilizado foi:

`incidencia_100mil`

correspondente à incidência semanal municipal de dengue por 100 mil habitantes.

A incidência foi utilizada em vez dos casos absolutos para reduzir a influência
direta das diferenças de tamanho populacional entre os municípios.

---

# 5. Variáveis meteorológicas

Foram analisadas:

`temperatura_media_c`

`umidade_relativa_media_pct`

`precipitacao_total_mm`

Essas três variáveis foram definidas antes da execução dos cálculos.

---

# 6. Defasagens

Foram avaliados os lags:

**0, 1, 2, 3, 4, 6 e 8 semanas**

A interpretação é:

`clima em t-k × incidência em t`

Assim, por exemplo, lag 4 compara as condições meteorológicas observadas quatro
semanas antes com a incidência da semana atual.

A continuidade temporal foi verificada explicitamente.

Uma linha anterior somente foi utilizada como lag quando sua distância temporal
correspondia exatamente à quantidade esperada de semanas.

---

# 7. Métrica de associação

Foi utilizada a:

**correlação de Spearman**

calculada separadamente para cada:

**unidade territorial × variável meteorológica × lag**

Não foi calculada uma única correlação utilizando indiscriminadamente todos os
municípios brasileiros.

O resumo nacional e regional foi obtido posteriormente a partir da distribuição
das correlações municipais.

---

# 8. Quantidade de associações

Com:

**5.570 unidades territoriais**

**3 variáveis**

e

**7 lags**

foram produzidas:

**116.970 combinações municipais**

antes da avaliação da validade matemática das correlações.

---

# 9. Correlações municipais sem definição

Foram identificadas:

**210 combinações sem correlação de Spearman válida**

correspondentes exatamente a:

**10 unidades territoriais × 3 variáveis × 7 lags**

Os territórios foram:

- Arroio do Padre/RS;
- Campestre da Serra/RS;
- Coqueiro Baixo/RS;
- Itapuca/RS;
- Muitos Capões/RS;
- Santo Expedito do Sul/RS;
- Calmon/SC;
- Macieira/SC;
- Ponte Alta do Norte/SC;
- Urupema/SC.

Cada território possuía aproximadamente a série temporal completa.

A correlação não foi artificialmente substituída por zero.

A ausência de correlação válida ocorre quando não existe variabilidade
suficiente em uma das séries necessárias ao cálculo de Spearman.

Assim, cada combinação variável × lag apresentou:

**5.560 correlações municipais válidas**

em escala nacional.

---

# 10. Resultado nacional — temperatura

A temperatura média apresentou:

| Lag | Correlação mediana |
| ---: | ---: |
| 0 | 0,0025 |
| 1 | 0,0276 |
| 2 | 0,0509 |
| 3 | 0,0738 |
| 4 | 0,0958 |
| 6 | 0,1368 |
| 8 | 0,1676 |

A associação mediana nacional aumentou progressivamente com a defasagem dentro
do intervalo previamente analisado.

A maior magnitude entre os lags testados ocorreu em:

**lag 8 — correlação mediana 0,1676**

Entretanto, a temperatura apresentou grande heterogeneidade territorial.

No lag 8:

- P25: aproximadamente -0,0016;
- P75: aproximadamente 0,2758;
- correlações positivas: 74,75%.

Assim, o padrão positivo não foi uniforme entre os municípios.

---

# 11. Resultado nacional — umidade relativa

A umidade apresentou associação positiva já na semana contemporânea.

| Lag | Correlação mediana |
| ---: | ---: |
| 0 | 0,1217 |
| 1 | 0,1331 |
| 2 | 0,1375 |
| 3 | 0,1426 |
| 4 | 0,1483 |
| 6 | 0,1473 |
| 8 | 0,1342 |

A maior associação mediana entre os lags avaliados ocorreu em:

**lag 4 — 0,1483**

No lag 4:

- P25: 0,0712;
- P75: 0,2363;
- 93,33% dos municípios apresentaram correlação positiva.

O perfil nacional sugere crescimento da associação até aproximadamente quatro
semanas e posterior redução dentro do intervalo estudado.

---

# 12. Resultado nacional — precipitação

A precipitação apresentou aumento consistente da associação mediana conforme a
defasagem.

| Lag | Correlação mediana |
| ---: | ---: |
| 0 | 0,0560 |
| 1 | 0,0731 |
| 2 | 0,0897 |
| 3 | 0,1063 |
| 4 | 0,1258 |
| 6 | 0,1505 |
| 8 | 0,1613 |

A maior associação observada ocorreu em:

**lag 8 — 0,1613**

No lag 8:

- P25: 0,0818;
- P75: 0,2384;
- 95,43% das correlações municipais foram positivas.

Entre os lags avaliados, a associação da precipitação apresentou comportamento
claramente defasado em escala nacional.

---

# 13. Limite da interpretação do lag 8

Temperatura e precipitação apresentaram suas maiores associações nacionais no:

**lag máximo previamente testado — 8 semanas**

Portanto, os resultados permitem afirmar apenas:

**entre as defasagens pré-especificadas, o lag 8 apresentou a maior associação
mediana observada.**

Não é possível afirmar que oito semanas representem necessariamente:

- a defasagem biológica ideal;
- o verdadeiro máximo da associação;
- um intervalo causal.

Defasagens superiores não foram acrescentadas após a observação dos resultados,
preservando o protocolo previamente congelado.

---

# 14. Heterogeneidade regional

A análise regional mostrou que o perfil nacional não representa igualmente
todas as partes do Brasil.

As maiores associações medianas por região e variável foram:

| Região | Variável | Lag | Correlação mediana |
| --- | --- | ---: | ---: |
| Norte | Precipitação | 6 | 0,1782 |
| Norte | Temperatura | 3 | -0,1163 |
| Norte | Umidade | 3 | 0,1791 |
| Nordeste | Precipitação | 8 | 0,1657 |
| Nordeste | Temperatura | 0 | -0,0960 |
| Nordeste | Umidade | 3 | 0,1815 |
| Centro-Oeste | Precipitação | 8 | 0,2943 |
| Centro-Oeste | Temperatura | 0 | -0,0947 |
| Centro-Oeste | Umidade | 6 | 0,3097 |
| Sudeste | Precipitação | 8 | 0,2008 |
| Sudeste | Temperatura | 8 | 0,2763 |
| Sudeste | Umidade | 6 | 0,1674 |
| Sul | Precipitação | 6 | 0,0463 |
| Sul | Temperatura | 8 | 0,2410 |
| Sul | Umidade | 0 | 0,0639 |

O lag indicado corresponde à maior magnitude da correlação mediana entre os
lags pré-especificados.

---

# 15. Norte

No Norte, precipitação e umidade apresentaram associações predominantemente
positivas.

Precipitação atingiu a maior mediana em:

**lag 6 — 0,1782**

Umidade atingiu:

**lag 3 — 0,1791**

A temperatura apresentou comportamento diferente.

A associação mediana permaneceu negativa em todos os lags avaliados:

- lag 0: -0,1131;
- lag 3: -0,1163;
- lag 8: -0,0807.

A maior magnitude ocorreu no lag 3.

Esse resultado demonstra que o comportamento nacional positivo da temperatura
não representa adequadamente a região Norte.

---

# 16. Nordeste

O Nordeste também apresentou precipitação e umidade predominantemente
positivas.

Precipitação:

**lag 8 — 0,1657**

Umidade:

**lag 3 — 0,1815**

A temperatura apresentou associação negativa nos lags iniciais.

No lag 0:

**-0,0960**

A correlação aproximou-se gradualmente de zero conforme aumentou a defasagem,
atingindo:

**-0,0082 no lag 8**

Portanto, o Nordeste também difere do perfil positivo observado em outras
regiões.

---

# 17. Centro-Oeste

O Centro-Oeste apresentou algumas das associações climáticas medianas mais
elevadas desta análise.

Precipitação:

**lag 8 — 0,2943**

Umidade:

**lag 6 — 0,3097**

No lag 8 da precipitação:

**99,79% das correlações municipais foram positivas**

e, no lag 6 da umidade:

**99,57% foram positivas**

A temperatura apresentou associação negativa nos lags iniciais:

**lag 0 — -0,0947**

mas se aproximou de zero e tornou-se positiva em lags mais longos:

- lag 6: 0,0201;
- lag 8: 0,0562.

O resultado demonstra forte diferença entre as variáveis meteorológicas dentro
da própria região.

---

# 18. Sudeste

O Sudeste apresentou crescimento progressivo das associações de temperatura e
precipitação conforme a defasagem.

Temperatura:

- lag 0: 0,0974;
- lag 4: 0,2083;
- lag 6: 0,2491;
- lag 8: 0,2763.

Precipitação:

- lag 0: 0,0146;
- lag 4: 0,1298;
- lag 6: 0,1715;
- lag 8: 0,2008.

A umidade atingiu maior mediana em:

**lag 6 — 0,1674**

No lag 8 da temperatura:

**99,88% dos municípios apresentaram correlação positiva**

O Sudeste, portanto, contribui de maneira importante para o padrão positivo
nacional observado em temperatura com lags mais longos.

---

# 19. Sul

O Sul apresentou um perfil bastante distinto.

A temperatura cresceu consistentemente com a defasagem:

- lag 0: 0,0422;
- lag 2: 0,1024;
- lag 4: 0,1538;
- lag 6: 0,2059;
- lag 8: 0,2410.

Entretanto, a precipitação apresentou associações medianas muito menores.

Seu máximo ocorreu em:

**lag 6 — 0,0463**

A umidade apresentou maior mediana no:

**lag 0 — 0,0639**

e diminuiu com a defasagem até:

**0,0142 no lag 8**

Assim, no Sul, temperatura apresentou padrão muito mais evidente do que
precipitação ou umidade.

---

# 20. Implicação da heterogeneidade regional

Os resultados demonstram que não existe um único perfil clima × dengue
igualmente representativo de todo o país.

Em particular:

- Norte e Nordeste apresentaram temperatura mediana negativa nos lags curtos;
- Centro-Oeste apresentou associações elevadas de precipitação e umidade;
- Sudeste apresentou associações crescentes de temperatura e precipitação;
- Sul apresentou forte contraste entre temperatura e as demais variáveis.

Assim, uma estatística nacional isolada pode esconder comportamentos regionais
substancialmente diferentes.

---

# 21. Magnitude das correlações

Mesmo nos melhores resultados nacionais, as correlações medianas permaneceram
de magnitude modesta.

Os máximos nacionais ficaram aproximadamente entre:

**0,15 e 0,17**

As associações regionais mais altas ficaram próximas de:

**0,30**

Portanto, os resultados não sustentam a ideia de uma relação simples,
determinística ou uniforme entre uma única variável meteorológica e dengue.

---

# 22. Associação não equivale a causalidade

As associações observadas podem refletir simultaneamente:

- sazonalidade compartilhada;
- temperatura;
- disponibilidade hídrica;
- umidade;
- dinâmica vetorial;
- circulação viral;
- imunidade populacional;
- mobilidade;
- urbanização;
- diferenças de vigilância;
- fatores ambientais não observados.

A correlação de Spearman utilizada nesta análise não isola esses mecanismos.

Assim, nenhuma das associações será descrita como evidência causal.

---

# 23. Sazonalidade compartilhada

Dengue e variáveis meteorológicas possuem componentes sazonais importantes.

Parte das correlações pode decorrer do fato de:

**clima e dengue variarem sistematicamente ao longo do calendário**

sem que uma variável meteorológica isolada explique diretamente a ocorrência
posterior da doença.

Esta etapa não removeu explicitamente a sazonalidade antes das correlações.

Consequentemente, os valores devem ser interpretados como:

**associação temporal observada nas séries históricas**

e não como efeito meteorológico isolado.

---

# 24. Relação com o resultado preditivo

Esta análise responde:

**há associação temporal observável entre variáveis climáticas e dengue?**

Essa pergunta é diferente de:

**essas variáveis acrescentam informação preditiva relevante quando o histórico
epidemiológico recente já está disponível?**

Uma variável pode apresentar associação estatística com dengue e ainda fornecer
pouco ganho incremental a um modelo que já conhece a trajetória epidemiológica
recente.

Portanto, associação descritiva e ganho preditivo não devem ser tratados como
sinônimos.

---

# 25. Implicação científica

Os resultados permitem conciliar duas observações aparentemente diferentes:

1. existem associações temporais entre clima e dengue;
2. a informação meteorológica não precisa necessariamente produzir grande ganho
   incremental sobre um modelo epidemiológico forte.

Isso sugere que parte da informação relacionada ao ambiente pode:

- compartilhar sazonalidade com os casos;
- estar parcialmente refletida na própria trajetória epidemiológica;
- apresentar relações regionais heterogêneas;
- não se traduzir diretamente em ganho de previsão fora da amostra.

---

# 26. Relação com o modelo final

Esta etapa foi realizada somente após o congelamento e a avaliação final da
modelagem.

Nenhum resultado foi utilizado para:

- acrescentar lags;
- remover lags;
- escolher novas features;
- alterar hiperparâmetros;
- retreinar modelos;
- recalibrar probabilidades;
- modificar thresholds operacionais.

O modelo final permanece inalterado.

---

# 27. Implicações para o dashboard histórico

A análise clima × dengue pode gerar visualizações históricas como:

**Perfil nacional de defasagem**

Mostrando:

`lag × correlação mediana municipal`

para temperatura, umidade e precipitação.

**Perfil regional**

Permitindo selecionar uma região e observar como o comportamento dos lags se
modifica.

Essas visualizações deverão apresentar mensagens explícitas de que:

**correlação não implica causalidade**

e que os resultados representam associações históricas.

---

# 28. Responsividade

Os gráficos clima × dengue destinados à aplicação deverão ser responsivos.

Em desktop será possível comparar múltiplas curvas simultaneamente.

Em telas menores, a interface poderá utilizar:

- seletor de variável;
- seletor de região;
- uma curva principal por vez;
- tooltips;
- legenda compacta;
- controles reorganizados verticalmente.

O objetivo será preservar legibilidade sem simplesmente reduzir um gráfico
desktop proporcionalmente.

---

# 29. Artefatos

Correlação municipal:

`reports/audits/associacao_clima_dengue_municipios_2016_2025.csv`

Resumo nacional:

`reports/audits/associacao_clima_dengue_nacional_2016_2025.csv`

Resumo regional:

`reports/audits/associacao_clima_dengue_regional_2016_2025.csv`

Auditoria:

`reports/audits/associacao_clima_dengue_2016_2025.json`

Scripts:

`scripts/analisar_associacao_clima_dengue.py`

`scripts/resumir_associacao_clima_dengue.py`

Protocolo:

`docs/18_protocolo_clima_dengue_2016_2025.md`

---

# 30. Próxima etapa

A próxima etapa será:

**12F — consolidação visual da análise exploratória histórica**

Nessa etapa serão selecionados os gráficos e mapas que realmente agregam valor
à apresentação do TCC e à futura aplicação.

A seleção deverá evitar redundância e priorizar visualizações que respondam
diretamente às perguntas:

- quanto ocorreu;
- quando ocorreu;
- onde ocorreu;
- como os episódios se comportaram;
- como clima e dengue se relacionaram temporalmente.

Status desta etapa:

**APROVADO**