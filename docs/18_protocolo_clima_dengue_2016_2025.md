# Protocolo de Análise Descritiva Clima × Dengue — 2016–2025

## 1. Objetivo

Esta etapa investiga associações temporais entre condições meteorológicas e a
atividade epidemiológica de dengue nos municípios brasileiros.

A pergunta exploratória é:

**Existe uma defasagem temporal identificável entre variações meteorológicas e
a incidência de dengue observada posteriormente?**

A análise possui caráter descritivo e associativo.

Não será utilizada para estabelecer causalidade nem para modificar o modelo
preditivo final.

---

# 2. Relação com a hipótese original

A hipótese original do projeto previa investigar se alterações em:

- temperatura;
- precipitação;
- umidade;

poderiam apresentar associação temporal com a ocorrência posterior de dengue.

Também estavam previstas comparações entre a semana atual e variáveis
meteorológicas defasadas em algumas semanas.

Esta etapa formaliza essa investigação sobre a base nacional já auditada.

---

# 3. Base de análise

Será utilizado o painel mestre:

`data/processed/painel_municipal_semanal_2016_2025.parquet`

Período:

**2016–2025**

Unidade analítica:

**unidade territorial × semana epidemiológica**

A análise será limitada às observações com disponibilidade climática válida.

Fernando de Noronha permanece no painel histórico geral, mas não participa das
análises clima × dengue por ausência de cobertura ERA5-Land no mapeamento
adotado pelo projeto.

---

# 4. Variável epidemiológica

O desfecho principal será:

`incidencia_100mil`

correspondente à incidência semanal municipal de dengue por 100 mil
habitantes.

A incidência será utilizada em vez do número absoluto de casos para reduzir a
influência direta das grandes diferenças populacionais entre municípios.

---

# 5. Variáveis meteorológicas

Serão analisadas três variáveis principais:

`temperatura_media_c`

`umidade_relativa_media_pct`

`precipitacao_total_mm`

A escolha mantém o foco nas variáveis meteorológicas centrais definidas na
hipótese original do projeto.

O ponto de orvalho permanece disponível no painel mestre, mas não será
incluído nesta análise principal para evitar ampliar posteriormente o conjunto
de variáveis em função dos resultados observados.

---

# 6. Defasagens temporais

Serão avaliadas as seguintes defasagens:

**0, 1, 2, 3, 4, 6 e 8 semanas**

A interpretação de uma defasagem `k` será:

**clima observado na semana t-k × incidência observada na semana t**

Assim:

- lag 0 compara clima e incidência da mesma semana;
- lag 1 compara o clima da semana anterior com a incidência atual;
- lag 2 compara clima de duas semanas antes;
- e assim sucessivamente.

Nenhuma defasagem superior a oito semanas será adicionada após a observação dos
resultados desta análise.

---

# 7. Continuidade temporal

As defasagens serão construídas dentro de cada unidade territorial.

O deslocamento somente será considerado válido quando a observação climática
corresponder exatamente à semana esperada.

A simples posição anterior de uma linha no arquivo não será considerada
suficiente caso exista ruptura temporal.

Essa regra impede que semanas não consecutivas sejam tratadas como uma
defasagem válida.

---

# 8. Métrica de associação

A métrica principal será a:

**correlação de Spearman**

A escolha é adequada à natureza exploratória da análise porque não exige
relação linear estrita e é menos sensível a valores extremos do que a
correlação de Pearson.

A correlação será calculada separadamente para cada:

**unidade territorial × variável meteorológica × defasagem**

Não será utilizada uma única correlação obtida pelo empilhamento indiscriminado
de todos os municípios brasileiros.

---

# 9. Resumo nacional

Para cada variável e defasagem, as correlações municipais serão resumidas por:

- número de municípios válidos;
- média;
- mediana;
- percentil 25;
- percentil 75;
- percentil 10;
- percentil 90;
- proporção de correlações positivas;
- proporção de correlações negativas.

A mediana das correlações municipais será utilizada como principal medida
descritiva nacional.

---

# 10. Resumo regional

O mesmo procedimento será realizado separadamente para:

- Norte;
- Nordeste;
- Centro-Oeste;
- Sudeste;
- Sul.

Isso permitirá verificar se o perfil das associações temporais apresenta
heterogeneidade geográfica.

Diferenças regionais serão tratadas como resultados descritivos e não como
efeitos causais da localização.

---

# 11. Interpretação da defasagem

Para cada variável climática será identificado o lag que apresentar a maior
magnitude da correlação mediana municipal dentro dos valores previamente
definidos.

Esse resultado será denominado:

**defasagem de maior associação descritiva**

e não:

**tempo causal entre clima e dengue**

A direção da correlação também será preservada.

---

# 12. Correlação não implica causalidade

Uma associação temporal entre clima e incidência pode refletir simultaneamente
diversos fenômenos, incluindo:

- sazonalidade;
- diferenças territoriais;
- circulação viral;
- imunidade populacional;
- mobilidade humana;
- urbanização;
- vigilância epidemiológica;
- condições ambientais não observadas.

Portanto, esta etapa não será utilizada para afirmar que uma variável
meteorológica isoladamente causa aumento ou redução da dengue.

---

# 13. Sazonalidade

Temperatura, chuva, umidade e dengue apresentam componentes sazonais.

Consequentemente, uma associação encontrada nesta etapa pode refletir, em
parte, sazonalidades coincidentes.

Os resultados serão descritos explicitamente como associações temporais
observadas.

Não será feita inferência causal a partir das correlações.

---

# 14. Relação com a modelagem

Esta etapa ocorre após o congelamento e a avaliação final do modelo.

Se determinada variável ou defasagem apresentar associação elevada nesta
análise, esse resultado não será utilizado para:

- acrescentar nova feature;
- remover feature existente;
- alterar a janela de lag;
- modificar hiperparâmetros;
- recalibrar probabilidades;
- modificar thresholds;
- retreinar o modelo final.

A análise possui finalidade exclusivamente exploratória e interpretativa.

---

# 15. Relação com o resultado do Modelo B

A existência de associação descritiva entre clima e dengue não implica
necessariamente ganho preditivo incremental.

Uma variável pode apresentar associação com a dengue e ainda assim fornecer
pouca informação adicional quando o modelo já conhece o histórico
epidemiológico recente.

Por isso, esta análise será interpretada separadamente da comparação já
realizada entre:

**Modelo A — histórico epidemiológico**

e

**Modelo B — histórico epidemiológico + meteorologia**

---

# 16. Artefatos previstos

A análise deverá produzir, no mínimo:

`reports/audits/associacao_clima_dengue_municipios_2016_2025.csv`

Contendo as correlações por município, variável e lag.

`reports/audits/associacao_clima_dengue_nacional_2016_2025.csv`

Contendo o resumo nacional.

`reports/audits/associacao_clima_dengue_regional_2016_2025.csv`

Contendo o resumo por macrorregião.

`reports/audits/associacao_clima_dengue_2016_2025.json`

Contendo a auditoria consolidada.

---

# 17. Visualizações futuras

As visualizações candidatas incluem:

**Perfil de lag por variável**

Eixo X:

defasagem em semanas

Eixo Y:

correlação mediana municipal

Podendo comparar temperatura, umidade e precipitação.

Também poderão existir perfis separados por região.

As visualizações destinadas à aplicação web deverão ser responsivas e adaptar
a organização das séries e controles a desktop, tablet e dispositivos móveis.

---

# 18. Limitações

A análise de correlação:

- não demonstra causalidade;
- não controla todos os fatores de confusão;
- pode refletir sazonalidade compartilhada;
- não captura necessariamente relações não monotônicas;
- resume relações heterogêneas entre municípios;
- não substitui a avaliação preditiva realizada anteriormente.

---

# 19. Regra de congelamento

Após o início do cálculo das associações, não serão alterados em função dos
resultados:

- as três variáveis meteorológicas principais;
- as defasagens selecionadas;
- a correlação de Spearman;
- o desfecho epidemiológico;
- a regra de resumo municipal.

Qualquer análise adicional será explicitamente identificada como análise
secundária.

Status do protocolo:

**CONGELADO ANTES DA EXECUÇÃO**