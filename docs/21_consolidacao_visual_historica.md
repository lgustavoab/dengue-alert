# Consolidação Visual da Análise Histórica

## 1. Objetivo

Esta etapa consolida visualmente os principais resultados obtidos durante a
análise exploratória histórica do projeto Dengue Alert.

As figuras foram produzidas após a conclusão das análises de:

- panorama nacional;
- sazonalidade epidemiológica;
- distribuição espacial;
- dinâmica do risco elevado;
- associações temporais entre clima e dengue.

O conjunto visual foi definido previamente no protocolo:

`docs/20_protocolo_consolidacao_visual_historica.md`

O objetivo não foi produzir o maior número possível de gráficos, mas selecionar
um conjunto reduzido de figuras capazes de responder às principais perguntas
históricas do projeto.

---

# 2. Conjunto final de figuras

Foram produzidas sete figuras principais.

| Figura | Tema | Pergunta principal |
| --- | --- | --- |
| 01 | Panorama nacional | Quanto ocorreu? |
| 02 | Sazonalidade regional | Quando ocorre? |
| 03 | Distribuição espacial municipal | Onde ocorre? |
| 04 | Municípios simultaneamente em risco | Como o risco se expande e retrai? |
| 05 | Duração dos episódios | Quanto tempo o risco persiste? |
| 06 | Clima × dengue nacional | Existe associação temporal defasada? |
| 07 | Clima × dengue regional | O padrão climático é igual em todo o Brasil? |

A sequência visual adotada foi:

**quanto → quando → onde → como persiste → como se relaciona ao clima**

---

# 3. Figura 01 — panorama nacional

Arquivo:

`reports/figures/01_panorama_nacional_casos_2016_2025.png`

A figura apresenta o número anual de casos prováveis de dengue entre 2016 e
2025.

O gráfico permite visualizar:

- anos de maior atividade;
- contraste entre períodos epidêmicos e anos de menor ocorrência;
- excepcionalidade de 2024;
- redução observada em 2025.

O maior valor da série foi:

**2024 — 6.564.894 casos prováveis**

A redução de 2025 em relação a 2024 foi de aproximadamente:

**74,97%**

A figura utiliza casos absolutos porque sua finalidade é representar carga
epidemiológica nacional ao longo dos anos.

Não foi utilizado eixo duplo para misturar casos e incidência.

---

# 4. Figura 02 — sazonalidade regional

Arquivo:

`reports/figures/02_sazonalidade_regional_2016_2025.png`

A figura apresenta a incidência média semanal por 100 mil habitantes segundo as
cinco macrorregiões brasileiras.

Também inclui:

**média nacional**

e

**intervalo interquartil nacional**

Os picos médios identificados foram:

| Região | Semana epidemiológica de pico |
| --- | ---: |
| Norte | 7 |
| Centro-Oeste | 11 |
| Sudeste | 15 |
| Sul | 15 |
| Nordeste | 16 |
| Brasil | 15 |

O gráfico evidencia que a sazonalidade não é uniforme no país.

O Norte apresenta atividade mais precoce, enquanto o Nordeste apresenta pico
mais tardio.

Centro-Oeste, Sudeste e Sul apresentam maior intensidade média no período
central do primeiro semestre.

---

# 5. Figura 03 — distribuição espacial municipal

Arquivo:

`reports/figures/03_mapa_incidencia_mediana_municipal_2016_2025.png`

A figura apresenta um mapa coroplético municipal do Brasil utilizando:

**incidência mediana anual por 100 mil habitantes entre 2016 e 2025**

A escolha da mediana reduz a influência de um único ano epidêmico extremo.

Foram representadas:

**5.571 unidades territoriais**

A malha municipal oficial do IBGE 2024 possui:

**5.573 feições**

As duas feições adicionais correspondem a:

- Área Operacional Lagoa Mirim;
- Área Operacional Lagoa dos Patos.

Essas áreas não possuem correspondência na base epidemiológica municipal e
foram removidas por conciliação de chaves.

Nenhuma unidade presente na base epidemiológica ficou sem geometria.

---

# 6. Tratamento da geometria

A malha municipal utilizada possui CRS original:

**SIRGAS 2000 — EPSG:4674**

Para a visualização nacional, os dados foram reprojetados para:

**SIRGAS 2000 / Brazil Polyconic — EPSG:5880**

Foi identificada uma geometria inválida:

**Selvíria/MS — código IBGE 5007802**

A geometria foi reparada em memória utilizando procedimento de validação
geométrica.

O arquivo original da malha não foi alterado.

---

# 7. Classes do mapa

A distribuição da incidência mediana municipal apresentou forte assimetria.

Os principais quantis foram:

| Quantil | Incidência mediana anual/100 mil |
| --- | ---: |
| P25 | 23,90 |
| P50 | 90,87 |
| P75 | 314,25 |
| P90 | 810,93 |
| P95 | 1.175,16 |
| P99 | 2.184,40 |
| Máximo | 3.922,39 |

Por isso, não foi utilizada uma escala linear de zero até o máximo.

As classes cartográficas foram definidas a partir dos quantis:

- até P25;
- P25–P50;
- P50–P75;
- P75–P90;
- P90–P95;
- P95–P99;
- acima de P99.

A distribuição final foi:

| Classe | Unidades |
| --- | ---: |
| ≤ 24 | 1.393 |
| 24–91 | 1.393 |
| 91–314 | 1.392 |
| 314–811 | 836 |
| 811–1.175 | 278 |
| 1.175–2.184 | 223 |
| > 2.184 | 56 |

A representação preserva todos os municípios e evita que os valores extremos
dominem visualmente o restante do país.

---

# 8. Figura 04 — municípios simultaneamente em risco

Arquivo:

`reports/figures/04_municipios_simultaneamente_risco_2018_2025.png`

A figura apresenta semanalmente a quantidade de municípios classificados como
risco elevado.

Período:

**2018–2025**

Municípios elegíveis:

**5.569**

O maior valor observado ocorreu em:

**2024 — semana epidemiológica 12**

com:

**3.121 municípios simultaneamente em risco**

correspondendo a:

**56,04% dos municípios elegíveis**

A figura permite visualizar a expansão e a retração territorial do estado de
risco ao longo das grandes epidemias.

Ela também evidencia que diferentes anos apresentaram amplitudes nacionais
distintas.

---

# 9. Figura 05 — duração dos episódios

Arquivo:

`reports/figures/05_duracao_episodios_risco_2018_2025.png`

Foram representados:

**54.269 episódios de risco elevado**

correspondentes a:

**414.678 município-semanas em risco**

A distribuição possui forte assimetria.

Principais estatísticas:

| Estatística | Duração |
| --- | ---: |
| Média | 7,64 semanas |
| P25 | 3 semanas |
| Mediana | 4 semanas |
| P75 | 9 semanas |
| P90 | 19 semanas |
| P95 | 26 semanas |
| P99 | 41 semanas |
| Máximo | 110 semanas |

Foi utilizada escala logarítmica no eixo vertical para permitir a visualização
simultânea:

**dos episódios típicos**

e

**da cauda de episódios persistentemente longos**

sem excluir observações extremas.

---

# 10. Interpretação da duração

A mediana de quatro semanas descreve melhor o comportamento central da
distribuição do que o episódio máximo.

Os episódios superiores a dezenas de semanas representam uma cauda
relativamente pequena, porém epidemiologicamente relevante.

O episódio máximo de 110 semanas não deve ser interpretado automaticamente como
uma única onda epidemiológica homogênea.

Ele representa uma sequência contínua de semanas em que o município permaneceu
acima do limiar sazonal de risco definido pelo projeto.

---

# 11. Figura 06 — clima × dengue nacional

Arquivo:

`reports/figures/06_lags_clima_dengue_nacional_2016_2025.png`

A figura apresenta a correlação de Spearman mediana municipal entre clima
defasado e incidência semanal de dengue.

Foram avaliados os lags:

**0, 1, 2, 3, 4, 6 e 8 semanas**

As variáveis foram:

- temperatura média;
- umidade relativa média;
- precipitação total.

Os maiores valores observados entre os lags previamente definidos foram:

| Variável | Lag | Spearman mediano |
| --- | ---: | ---: |
| Temperatura média | 8 | 0,1676 |
| Umidade relativa | 4 | 0,1483 |
| Precipitação total | 8 | 0,1613 |

A figura evidencia que as associações não apresentam o mesmo perfil temporal.

Temperatura e precipitação aumentaram progressivamente dentro da janela
analisada, enquanto a umidade apresentou máximo aproximadamente no lag 4.

---

# 12. Limite de interpretação dos lags

Temperatura e precipitação atingiram suas maiores associações no:

**lag máximo previamente avaliado — 8 semanas**

Assim, a figura permite afirmar apenas que:

**o lag 8 foi o maior valor entre as defasagens pré-especificadas**

e não que:

**oito semanas representam necessariamente a defasagem causal ou ótima real**

Defasagens superiores não foram acrescentadas depois da observação dos
resultados.

---

# 13. Figura 07 — heterogeneidade regional clima × dengue

Arquivo:

`reports/figures/07_lags_clima_dengue_regional_2016_2025.png`

A figura foi organizada em três painéis:

- temperatura média;
- umidade relativa;
- precipitação total.

Cada painel contém as cinco macrorregiões.

A mesma escala vertical foi preservada entre os painéis para facilitar a
comparação.

O resultado mostra que uma curva climática nacional única não representa
adequadamente todas as regiões brasileiras.

---

# 14. Temperatura por região

A temperatura apresentou comportamentos distintos.

No Norte, a correlação mediana permaneceu negativa durante toda a janela
avaliada.

No Nordeste, começou negativa e se aproximou de zero conforme aumentou o lag.

No Centro-Oeste, também iniciou negativa e tornou-se discretamente positiva nos
lags mais longos.

Sudeste e Sul apresentaram crescimento claro da associação positiva com a
defasagem.

Os maiores valores observados foram aproximadamente:

**Sudeste — lag 8: 0,276**

**Sul — lag 8: 0,241**

---

# 15. Umidade por região

A maior associação de umidade ocorreu no Centro-Oeste.

O perfil da região aumentou até aproximadamente:

**lag 6 — correlação mediana próxima de 0,310**

Norte e Nordeste apresentaram associações positivas intermediárias.

O Sul apresentou perfil distinto, com associação mais alta na semana
contemporânea e redução progressiva conforme a defasagem aumentou.

---

# 16. Precipitação por região

A precipitação apresentou forte crescimento com a defasagem no Centro-Oeste.

O maior valor regional observado foi aproximadamente:

**lag 8 — 0,294**

O Sudeste também apresentou crescimento progressivo.

Norte e Nordeste mostraram associações positivas de menor magnitude.

No Sul, a precipitação apresentou correlações medianas substancialmente menores
do que nas demais regiões.

---

# 17. Associação não implica causalidade

As Figuras 06 e 07 representam associações históricas.

Elas não demonstram que:

- chuva causa diretamente aumento de dengue;
- determinada temperatura produz epidemias;
- a defasagem observada seja necessariamente um mecanismo biológico causal.

Os resultados podem refletir simultaneamente:

- sazonalidade compartilhada;
- dinâmica vetorial;
- circulação viral;
- imunidade populacional;
- mobilidade;
- urbanização;
- diferenças de vigilância;
- fatores ambientais não observados.

Por isso, todas as figuras climáticas mantêm indicação explícita de que:

**correlação não implica causalidade**

---

# 18. Relação entre associação climática e previsão

As figuras climáticas respondem:

**existe associação histórica entre clima e dengue?**

Essa pergunta é diferente de:

**o clima melhora a previsão quando o modelo já conhece o histórico
epidemiológico recente?**

Assim, uma associação visível nas Figuras 06 e 07 não implica necessariamente
ganho preditivo incremental.

A avaliação preditiva permanece separada da análise exploratória histórica.

---

# 19. Padrão técnico das figuras

Todas as figuras foram geradas por scripts reproduzíveis armazenados em:

`scripts/`

As imagens finais foram salvas em:

`reports/figures/`

Formato:

**PNG**

Resolução utilizada:

**300 dpi**

As figuras evitam:

- eixos duplos desnecessários;
- truncamentos enganosos;
- mistura de indicadores incompatíveis;
- elementos puramente decorativos;
- interpretação causal indevida.

---

# 20. Dependências adicionadas

Durante a consolidação visual foram incorporadas ao ambiente de desenvolvimento
bibliotecas necessárias à geração das figuras.

Entre elas:

**Matplotlib**

utilizado para geração dos gráficos estáticos.

Também foram incorporadas dependências geoespaciais para o mapa:

**GeoPandas**

**Pyogrio**

com dependências associadas como:

**Shapely**

e

**PyProj**

As versões exatas permanecem registradas no:

`uv.lock`

---

# 21. Malha municipal

A malha municipal do IBGE utilizada na Figura 03 é um dado bruto externo.

Ela permanece em:

`data/raw/geography/ibge_municipios_2024/`

e não é versionada no Git.

O script da figura verifica explicitamente:

- existência do arquivo;
- quantidade esperada de feições;
- CRS;
- códigos territoriais;
- geometrias inválidas;
- correspondência com os dados epidemiológicos.

Assim, a figura permanece reproduzível quando a malha oficial é disponibilizada
localmente.

---

# 22. Figuras estáticas e dashboard

As sete figuras produzidas destinam-se principalmente a:

- relatório acadêmico;
- apresentação do TCC;
- documentação técnica;
- repositório.

A aplicação web não deverá simplesmente exibir essas imagens como se fossem um
dashboard.

Os mesmos resultados deverão ser transformados em:

**componentes interativos**

com:

- filtros;
- tooltips;
- seleção geográfica;
- seleção temporal;
- detalhamento sob demanda.

---

# 23. Dashboard histórico

A área histórica da aplicação deverá permitir responder às mesmas perguntas
representadas pelas figuras:

**Quanto ocorreu?**

**Quando ocorreu?**

**Onde ocorreu?**

**Quanto tempo o risco persistiu?**

**Como o risco se espalhou territorialmente?**

**Como clima e dengue se associaram historicamente?**

Os dados utilizados pelo frontend deverão ser tabelas agregadas apropriadas à
visualização.

O navegador não deverá carregar diretamente o painel completo com milhões de
registros.

---

# 24. Responsividade

As visualizações do frontend deverão ser desenvolvidas de forma responsiva.

As figuras estáticas desta etapa servem como referência analítica, não como
layout obrigatório da aplicação.

Em desktop poderão existir múltiplos elementos simultaneamente.

Em tablets e dispositivos móveis poderão ser aplicados:

- empilhamento vertical;
- seletores de variável;
- filtros recolhíveis;
- redução do número de séries simultâneas;
- painéis expansíveis;
- tooltips;
- reorganização dos controles.

O mapa deverá possuir comportamento específico para interação por toque e telas
menores.

---

# 25. Relação com o modelo final

A consolidação visual foi realizada depois da avaliação final do modelo.

Nenhuma figura foi utilizada para:

- redefinir targets;
- criar novas features;
- remover features;
- alterar hiperparâmetros;
- modificar thresholds;
- recalibrar probabilidades;
- retreinar o modelo final.

A etapa é exclusivamente:

**exploratória, descritiva e comunicacional**

---

# 26. Validação técnica final

Após a produção das sete figuras foi executada uma validação global do projeto.

Ruff:

`uv run ruff check src scripts tests --fix`

Resultado:

**All checks passed**

Formatação:

`uv run ruff format src scripts tests`

Resultado:

**64 arquivos sem alterações necessárias**

Nova validação Ruff:

`uv run ruff check src scripts tests`

Resultado:

**All checks passed**

Testes:

`uv run pytest`

Resultado:

**69 testes aprovados**

Tempo observado:

aproximadamente:

**9 segundos**

---

# 27. Arquivos finais

Figuras:

`reports/figures/01_panorama_nacional_casos_2016_2025.png`

`reports/figures/02_sazonalidade_regional_2016_2025.png`

`reports/figures/03_mapa_incidencia_mediana_municipal_2016_2025.png`

`reports/figures/04_municipios_simultaneamente_risco_2018_2025.png`

`reports/figures/05_duracao_episodios_risco_2018_2025.png`

`reports/figures/06_lags_clima_dengue_nacional_2016_2025.png`

`reports/figures/07_lags_clima_dengue_regional_2016_2025.png`

Scripts:

`scripts/gerar_figura_01_panorama_nacional.py`

`scripts/gerar_figura_02_sazonalidade_regional.py`

`scripts/gerar_figura_03_mapa_incidencia_municipal.py`

`scripts/gerar_figura_04_municipios_simultaneamente_risco.py`

`scripts/gerar_figura_05_duracao_episodios_risco.py`

`scripts/gerar_figura_06_lags_clima_dengue_nacional.py`

`scripts/gerar_figura_07_lags_clima_dengue_regional.py`

---

# 28. Encerramento da análise exploratória histórica

Com esta etapa, a análise exploratória histórica fica concluída.

As etapas finalizadas são:

**12A — Panorama nacional**

**12B — Sazonalidade epidemiológica**

**12C — Distribuição espacial**

**12D — Dinâmica epidemiológica**

**12E — Associação clima × dengue**

**12F — Consolidação visual**

O conjunto histórico está agora documentado por:

- auditorias reproduzíveis;
- artefatos tabulares;
- documentação metodológica;
- scripts;
- figuras acadêmicas.

---

# 29. Próxima fase

A análise histórica não necessita de novas figuras principais neste momento.

A próxima fase deverá ser tratada separadamente da EDA.

Antes de iniciar o frontend ou qualquer outra nova etapa, deverá ser definido o
escopo técnico seguinte do projeto.

Possibilidades futuras incluem:

- preparação dos dados de serving;
- desenho da arquitetura do dashboard;
- implementação da aplicação web;
- preparação da camada de previsão;
- integração entre histórico e previsão;
- documentação final do produto.

Essas decisões deverão preservar a separação entre:

**análise histórica**

e

**previsão futura**

Status desta etapa:

**APROVADO**

Status da análise exploratória histórica:

**CONCLUÍDA**