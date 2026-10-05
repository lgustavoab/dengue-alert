# Fase 16A — Organização e linguagem da aplicação

Status: planejamento editorial da Fase 16A, com registro das implementações locais de 16B, 16C.1, 16C.2, 16D, 16E.1, 16E.2 e 16F e da revisão integrada 16G ao final; teste com público leigo, dispositivo físico e leitor de tela permanecem pendentes.

## 1. Objetivo e limites desta etapa

Apresentar o Dengue Alert como comunicação de um trabalho acadêmico: explicar a pergunta, o caminho percorrido, os resultados e suas limitações antes de expor métricas e detalhes de implementação.

O público principal é uma pessoa sem formação em epidemiologia ou aprendizado de máquina. O conteúdo técnico continua acessível para banca, pesquisadores e interessados, mas deixa de disputar a atenção inicial com a explicação do estudo.

Esta fase define organização, vocabulário e textos-base. Não modifica componentes, rotas, dados, modelos, cálculos, contratos, filtros, infraestrutura ou o TCC. Não autoriza publicação do TCC, commit, push ou deployment.

## 2. Fontes e método da análise

- Leitura de conteúdo de [TCC_v5.docx](../reports/methodology/TCC_v5.docx), com extração do texto e das 28 tabelas por `python-docx`. Foco em objetivos, fontes, método, resultados, conclusões e limitações. Não foi uma revisão visual da diagramação, das figuras ou da normalização acadêmica.
- Confronto com a documentação científica: definição do alvo (02), desenho experimental (04), persistência (05), Modelo A (06), comparação climática (07), calibração e limiares (08), teste final (10), heterogeneidade (12) e análises históricas (14–19).
- Consulta aos contratos e protocolos de apresentação: histórico e qualidade (23), predição (25 e 33), histórico (31), mapa (35) e runtime (42).
- Conferência dos pontos numéricos divergentes nos relatórios existentes `avaliacao_baseline_persistencia.json`, `avaliacao_modelo_a.json`, `comparacao_modelos_ab.json` e `avaliacao_final_2025.csv`, em `reports/audits`. Nenhum experimento foi reexecutado.
- Aproveitamento da análise anterior da interface, com nova conferência de textos no código da Home, navegação, rodapé, predição, mapa e qualidade. Esta etapa não constitui uma nova validação visual mobile/desktop.

O TCC orienta a narrativa acadêmica. Para os valores exibidos, os contratos científicos e relatórios auditados precisam permanecer rastreáveis. Quando as fontes divergem, registrar a divergência e pedir revisão; não alterar dados para fazê-los coincidir com uma tabela do manuscrito.

## 3. Mensagem central

> Investigamos se o histórico da dengue permite antecipar períodos de risco elevado nos municípios brasileiros, de uma a quatro semanas à frente, e se informações meteorológicas melhoram essa previsão. Os resultados apresentados foram avaliados retrospectivamente, com dados de 2025.

Três contribuições precisam ser percebidas sem a leitura de um painel técnico:

1. **Organização e análise dos dados:** integração de fontes epidemiológicas, populacionais, territoriais e meteorológicas; descrição da dengue entre 2016 e 2025.
2. **Avaliação preditiva:** comparação de métodos, preservação da ordem temporal e teste final em um ano separado do desenvolvimento.
3. **Comunicação dos resultados:** exploração do histórico e comparação entre alertas do modelo e situações observadas, incluindo erros e limitações.

A aplicação não apresenta alertas atuais, previsão da quantidade de casos, diagnóstico individual ou declaração oficial de epidemia. O nome Dengue Alert pode ser mantido, acompanhado de uma identificação acadêmica clara.

### Achados que podem orientar a narrativa

- O modelo apresentou maior Average Precision que a persistência nos quatro horizontes do teste de 2025. Essa comparação não significa superioridade em todas as métricas.
- Identificar risco quando ele ainda não estava presente foi uma tarefa mais difícil que avaliar todas as situações, incluindo a continuidade de períodos já elevados.
- No cenário de antecipação, H1 e H2 tiveram resultados mais favoráveis em conjunto. H2 teve AP e F1 ligeiramente maiores que H1; não dizer que toda métrica piora a cada semana adicional.
- A inclusão das variáveis meteorológicas avaliadas não trouxe ganho preditivo incremental consistente. Isso não demonstra ausência de relação entre clima e dengue.
- O desempenho variou entre contextos municipais. O resultado nacional não é garantia de desempenho para uma cidade específica.

Fontes principais: TCC, seções 6 e 7; documentos 07, 10 e 12.

## 4. Verificação do TCC após a correção das tabelas

Na abertura da Fase 16B, o autor informou que havia corrigido as tabelas do TCC. A releitura do arquivo local confirmou as duas correções numéricas principais. Esta verificação não constitui uma auditoria integral da pesquisa; o manuscrito foi preservado.

| Local | Estado verificado | Evidência e encaminhamento |
| --- | --- | --- |
| Tabela 19, persistência H2/H3/H4 | Corrigida para 0,6466 / 0,5439 / 0,4640 | Valores compatíveis, a quatro casas, com `avaliacao_baseline_persistencia.json` e o documento 06. |
| Tabela 22, Brier H1 | Corrigida para 0,0268 | Valor compatível, a quatro casas, com `avaliacao_final_2025.csv` e o documento 10. |
| Tabelas 19 e 20, AP geral HGB H2 | 0,8910 e 0,8911 | O relatório registra 0,8910502789475433, que arredonda para 0,8911 a quatro casas. A diferença também aparece entre documentos de etapas anteriores. Padronizar a apresentação, sem modificar o valor científico. |
| Capítulo 5, desenvolvimento da aplicação | Contém anotações sobre manter/resumir o capítulo, em vez da descrição final | Para descrever a implementação, usar os protocolos e o código atuais; o texto acadêmico ainda precisa ser concluído pelos autores. |
| Elementos pré-textuais | Indicações como “colocar outros polos”, “?? f.” e link da apresentação em branco | Não disponibilizar automaticamente esta versão como TCC final. Confirmar versão pública, dados acadêmicos e autorização. |

Outra cautela: na avaliação geral H1 de 2025, o F1 da persistência é aproximadamente 0,8239 e o do modelo é 0,8104. Portanto, a frase “o modelo supera a persistência” deve especificar a métrica, por exemplo AP, e não ser apresentada como vitória universal. Fonte: `reports/audits/avaliacao_final_2025.csv`.

Diferenças entre média e mediana, entre desenvolvimento e teste final ou entre cobertura histórica e preditiva não são automaticamente erros. Cada número deve manter seu período, população de referência e definição.

## 5. Arquitetura de informação proposta

Manter as cinco rotas. Alterar os rótulos de apresentação, não os endereços públicos.

| Rota | Rótulo de navegação proposto | Pergunta respondida | Conteúdo inicial |
| --- | --- | --- | --- |
| `/` | Início | O que vocês estudaram e descobriram? | Pergunta, breve método, três achados, limitações e autoria. |
| `/historico` | Histórico | Como a dengue se comportou no período estudado? | Recorte selecionado, casos e evolução; demais temas organizados em seções. |
| `/predicao` | Resultados | O que o modelo indicou e como foi avaliado? | Separação clara entre consulta municipal e avaliação do modelo. |
| `/mapa` | Mapa | Como os resultados se distribuem no território? | Período retrospectivo, semana, antecedência, busca, legenda e resultado municipal. |
| `/dados-qualidade` | Dados e método | De onde vieram os dados e quais são os limites do estudo? | Fontes em linguagem simples, preparação, definição de risco, avaliação e limitações. |

Ordem proposta: Início → Histórico → Resultados → Mapa → Dados e método.

“Resultados” deve ter o título de página “Resultados do modelo” e a indicação “Avaliação retrospectiva de 2025”. Não usar apenas “Previsão” como rótulo sem contexto, pois pode sugerir informação atual.

### Três níveis de leitura

1. **Essencial, sempre visível:** pergunta da seção, resultado principal, período, território, unidade e ressalva indispensável.
2. **Explicação, próxima ao resultado:** “Como interpretar”, definição do indicador, exemplo e comparação com o observado.
3. **Detalhe técnico, sob demanda:** métricas completas, fórmulas, parâmetros, campos originais, procedimentos e rastreabilidade.

Não esconder em acordeões: natureza retrospectiva, diferença entre alerta e observado, significado de “sem alerta”, falha de carregamento, ausência de avaliação e limites centrais do estudo. A melhoria não consiste em trocar longos blocos por uma sequência igualmente longa de acordeões abertos.

Explicações essenciais não podem depender de hover. Links e controles de expansão precisam funcionar com teclado e toque. Não é necessário criar um seletor global “leigo/especialista”, que duplicaria conteúdo e estado.

## 6. Organização por página

### 6.1 Início

Sequência recomendada:

1. Identificação acadêmica e pergunta do estudo.
2. Resumo do que foi feito, em três etapas curtas.
3. Principais achados, com limites na mesma leitura.
4. Links “Explorar o histórico”, “Consultar resultados de 2025” e “Entender os dados e o método”.
5. Autores, instituição e orientação, com referência ao trabalho quando houver versão pública aprovada.

Retirar do protagonismo “município-semanas”, total de predições e nomes de algoritmos. Esses números permanecem na metodologia. Não substituir por grandes números de “acerto” sem definição.

Evitar estética ou linguagem de venda: cadastro, planos, promessas de proteção, métricas de vaidade ou chamadas que afirmem impacto operacional não demonstrado.

### 6.2 Histórico

Organizar os temas por perguntas: “Como os casos variaram?”, “Em que épocas aumentaram?”, “Como variaram entre lugares?”, “Quanto duraram os períodos de risco?” e “O que observamos sobre o clima?”.

Mostrar primeiro a evolução correspondente ao recorte disponível. Tabelas extensas e métricas complementares ficam em expansão local. Manter casos e incidência claramente diferentes, inclusive no eixo e no título dos gráficos.

Não forçar todos os temas a responder aos mesmos filtros: cada seção deve declarar o seu escopo. Em especial:

- A UF dispõe de resumo consolidado, não de série semanal ou sazonal estadual no contrato atual.
- A consulta municipal carrega sua série sob demanda.
- A sazonalidade resume diferentes anos; não deve parecer uma curva do ano selecionado.
- A série semanal de risco existe para Brasil e regiões; há resumos municipais, não equivalência automática entre todas as escalas.
- A associação climática exibida é nacional/regional e resume correlações municipais; não é uma única correlação calculada sobre uma série nacional agregada.
- O histórico geral começa em 2016; a análise de risco começa em 2018 por exigir histórico anterior.

Quando um filtro não se aplicar, explicar o motivo junto à seção. Não produzir uma nova agregação científica para preencher uma lacuna da interface.

### 6.3 Resultados do modelo

Separar, dentro da mesma rota, “Consultar um município” e “Avaliar o modelo”. Podem ser seções com navegação local; não há exigência de abas complexas.

Na consulta municipal:

- Selecionar município e semana de referência; deixar claro que são dados de 2025.
- Mostrar “1 semana depois”, “2 semanas depois”, “3 semanas depois” e “4 semanas depois”, com H1–H4 secundários.
- Aproximar, em cada resultado, “O que o modelo indicou” e “O que foi observado”. Evitar obrigar a pessoa a memorizar quatro cards antes de encontrar a comparação.
- Exibir também o estado observado na origem, necessário para distinguir continuidade e antecipação.
- Manter probabilidade e limiar acessíveis em “Como o alerta foi definido”; a decisão principal continua vindo de `predicao`.
- A evolução dos escores ao longo do ano permanece como aprofundamento.

Na avaliação do modelo:

- Explicar primeiro a diferença entre “todas as situações avaliadas” e “situações sem risco elevado na origem”.
- Dar destaque à capacidade de antecipação, acompanhada de alertas não confirmados e situações não identificadas.
- Manter comparação com a persistência e todas as métricas em uma tabela técnica acessível.
- Não confundir métricas nacionais com a qualidade da previsão individual selecionada.
- Se houver exemplos guiados, incluir acerto, alerta não confirmado e risco não identificado. Selecioná-los com evidência nos contratos, sem inventar nem escolher apenas sucessos.

### 6.4 Mapa

O mapa apresenta resultados do modelo em 2025, não risco atual. Manter esse contexto junto aos filtros e à legenda.

Priorizar semana, antecedência, busca municipal e legenda. Aproximar o painel do município da área de interação. Especificações como tamanho do asset, compressão e implementação geográfica não pertencem ao conteúdo principal; podem permanecer na documentação técnica.

Preservar ALERTA, SEM ALERTA e ausência de avaliação como estados distintos. Falha HTTP é um quarto estado de interface, não uma classe epidemiológica. Não usar intensidade de cor para inventar faixas baixo/médio/alto/crítico.

A busca municipal continua sendo uma alternativa essencial à seleção de polígonos pequenos. Reduzir textos e organizar o painel não resolve, por si só, peso da geometria ou interação cartográfica; uma troca de biblioteca ou infraestrutura não faz parte deste plano editorial.

### 6.5 Dados e método

Começar por: “Quais dados usamos?”, “Como os organizamos?”, “O que chamamos de risco elevado?”, “Como testamos o modelo?” e “O que os resultados não permitem concluir?”.

SINAN, IBGE e ERA5-Land devem ser apresentados pelo papel que cumprem, antes de siglas e campos originais. Explicar ERA5-Land como estimativa meteorológica em grade, não estação instalada em cada município.

Manter visíveis as limitações sobre dados consolidados, teste em um único ano e desigualdade de desempenho. A explicação de semanas preenchidas com zero deve acompanhar esse assunto: preenchimento não comprova ausência de transmissão nem registro explícito de zero na fonte.

Funil detalhado, códigos originais, critérios de elegibilidade, exceções territoriais, uso de população e rastreabilidade ficam em subseções técnicas. Caminhos de arquivos não devem aparecer como supostos links públicos quando não forem acessíveis no site.

## 7. Textos-base para implementação futura

São propostas para revisão, não conteúdo já publicado.

### Identificação

> Dengue Alert — um estudo acadêmico sobre dengue no Brasil.

### Título da Home

> É possível antecipar períodos de risco elevado de dengue?

### Introdução

> Analisamos dados de dengue de 2016 a 2025 e testamos modelos para identificar risco elevado de uma a quatro semanas à frente. Também investigamos se temperatura, chuva e umidade ajudavam nessa tarefa. Aqui você pode conhecer o estudo, explorar os dados e comparar os alertas do modelo com o que foi observado em 2025.

### Aviso curto, próximo à introdução

> Este site apresenta resultados de uma pesquisa. Não fornece alertas atuais nem estima o risco individual de uma pessoa ter dengue.

### Como o estudo foi feito

1. **Reunimos os dados:** organizamos registros de dengue e informações de população, território e clima.
2. **Comparamos modelos:** desenvolvemos e selecionamos a estratégia com dados de 2018 a 2024.
3. **Testamos em outro período:** avaliamos os resultados em 2025, sem usar esse ano para escolher o modelo ou ajustar seus limites de alerta.

Os dados de 2016 e 2017 também forneceram histórico para definir as primeiras referências sazonais. A avaliação usou dados históricos consolidados, não uma reprodução completa dos atrasos de informação de uma operação real.

### Três achados, sem promessa comercial

**Foi possível antecipar parte das situações de risco.** O modelo identificou situações futuras em que o município ainda não apresentava risco elevado. Também deixou de identificar algumas situações e produziu alertas que não se confirmaram.

**A antecedência faz diferença.** Os resultados de antecipação foram mais favoráveis em uma e duas semanas. Prever períodos mais distantes trouxe maiores dificuldades no cenário estudado.

**Adicionar clima não trouxe melhora consistente.** As variáveis meteorológicas testadas não melhoraram de forma consistente a previsão obtida com o histórico epidemiológico. Isso não significa que o clima não tenha relação com a dengue.

### Definição curta de risco elevado

> Neste estudo, chamamos de risco elevado a situação em que a incidência acumulada em quatro semanas supera uma referência histórica do próprio município para aquela época do ano. Essa definição não equivale a uma declaração oficial de epidemia.

No detalhe metodológico, manter P90 sazonal, janela de ±4 semanas em anos anteriores, exigência de histórico válido e operador estrito `>`. Não confundir essa regra observada com o limiar de decisão do modelo, que usa `>=`.

### Contexto da página de resultados

> Os resultados abaixo foram produzidos para avaliar o modelo com dados de 2025. A semana escolhida é o ponto de partida da previsão; a comparação mostra o estado observado uma, duas, três ou quatro semanas depois.

### Rótulos de estado

- **Alerta do modelo:** o modelo indicou risco elevado para a semana futura selecionada. Não é confirmação do que ocorreu.
- **Sem alerta do modelo:** o resultado ficou abaixo do limite de alerta adotado no estudo. Não significa ausência de dengue ou garantia de segurança.
- **Sem avaliação para este recorte:** não há resultado preditivo disponível; não interpretar como sem alerta.
- **Não foi possível carregar o resultado:** falha de carregamento, com opção de nova tentativa. Não mostrar dados anteriores como se fossem do novo recorte.

As classes canônicas continuam inalteradas; essas frases são explicações públicas.

### Exemplo de explicação de métricas

Para H1, no subconjunto de 2025 em que não havia risco elevado na origem:

> Entre as situações que apresentaram risco elevado uma semana depois, o modelo identificou aproximadamente 45 em cada 100. Entre os alertas emitidos nesse cenário, aproximadamente 27 em cada 100 se confirmaram.

Base: recall 0,447541 e precision 0,273755; 2.858 situações corretamente alertadas, 6.386 situações futuras positivas e 10.440 alertas emitidos. São combinações município–semana, não pessoas nem municípios únicos. As duas frases têm denominadores diferentes e devem aparecer juntas. Não apresentar esses percentuais como “acurácia geral”.

Na implementação, os valores devem continuar derivados dos campos existentes do contrato e de formatadores de apresentação, não de uma nova análise ou de texto numérico duplicado que possa ficar desatualizado.

## 8. Vocabulário de interface

| Termo técnico | Apresentação recomendada | Cuidado obrigatório |
| --- | --- | --- |
| Predição | Resultado do modelo / o que o modelo indicou | Explicitar teste retrospectivo de 2025. |
| Horizonte H1–H4 | 1, 2, 3 ou 4 semanas depois | Distância temporal, não gravidade; resultado em `t+h`, não ocorrência em qualquer ponto do intervalo. |
| Semana epidemiológica / SE | Semana de referência, com número e datas | Usar calendário/datas dos contratos, não semana ISO inferida. |
| Score | Probabilidade estimada pelo modelo | Não é risco pessoal, número de casos ou certeza; são probabilidades sem calibração adicional. |
| Threshold | Limite para emitir alerta | Explicação técnica acessível; não presumir limite de 50%. |
| `predicao` | Alerta / sem alerta do modelo | Fonte da classificação; não recalcular usando percentuais arredondados. |
| `target` | Estado observado na semana futura | Observado segundo a definição da pesquisa, não diagnóstico individual. |
| `risco_elevado` na origem | Estado observado na semana de referência | Diferente da previsão futura. |
| Incidência | Casos por 100 mil habitantes | Informar se semanal, anual ou acumulada em quatro semanas. |
| Casos | Casos prováveis incluídos no estudo | Não transformar em casos confirmados ou pessoas únicas. |
| Município-semana | Um município em uma semana | Contagem de observações, não de municípios distintos. |
| P90 | Referência histórica sazonal | Não representa 90% de chance nem exatamente 10% de semanas futuras em risco. |
| Sazonalidade | Como a dengue varia ao longo do ano | Resumo de vários anos, não uma previsão. |
| Lag | Clima observado algumas semanas antes | Maior associação entre intervalos testados não prova atraso causal ótimo. |
| Correlação | Associação observada nos dados | Não demonstra causalidade. |
| Early warning | Avaliação da antecipação do risco | Restringir ao subconjunto sem risco na origem e separar alerta de confirmação. |
| Baseline de persistência | Comparação simples: o estado continua igual | No subconjunto sem risco atual, sempre prevê ausência de risco; não confundir com comparação clínica. |
| Recall | Situações de risco identificadas pelo modelo | Denominador: situações realmente positivas no recorte. |
| Precision | Alertas que se confirmaram | Denominador: alertas emitidos no recorte. |
| AP / campo `pr_auc_average_precision` | Average Precision (AP), em detalhes técnicos | Mede ordenação ao longo de limiares; 0,92 não significa 92% de acerto. Não renomear o campo do contrato. |
| F1, ROC-AUC e Brier | Manter nomes com definição no detalhe | Não substituir por um genérico “índice de confiança”. |
| Contratos serving / assets | Dados preparados para a aplicação | Nomes de arquivos e estrutura interna ficam na documentação técnica. |
| Classificação oficial | Classificação do modelo neste estudo | Evitar sugerir que se trata de alerta oficial de uma autoridade sanitária. |

Não eliminar siglas da metodologia; introduzi-las depois da explicação. Substituir palavras isoladas não basta quando a estrutura continua mostrando dezenas de indicadores simultaneamente.

## 9. Limites técnicos e científicos preservados

- Cinco rotas existentes; sem backend novo, CMS, biblioteca de gráficos ou serviço pago para executar este plano.
- Runtime compacto é uma forma de distribuir os mesmos contratos, não uma nova fonte científica. Não alterar `data/serving`, snapshots, classificações ou limiares.
- Nenhum modelo é treinado ou executado em tempo real por estas mudanças de apresentação.
- Metadados de geração de arquivos não são data de atualização epidemiológica. Mostrar o período efetivo dos dados.
- Cobertura histórica e preditiva são diferentes: 5.571 unidades históricas/geográficas e 5.569 com avaliação preditiva. Explicar as exceções territoriais; não chamar tudo indistintamente de “todos os municípios”.
- Fernando de Noronha e Boa Esperança do Norte permanecem sem avaliação preditiva nos contratos atuais; o DF não deve ser omitido por simplificação textual.
- Preservar seleção municipal, parâmetros de URL, acessibilidade, carregamento sob demanda, retry e estados de indisponibilidade. Reorganizar conteúdo não autoriza alterar sua lógica.
- A troca dos rótulos deve alcançar headings, legendas, mensagens vazias, títulos e nomes acessíveis, não apenas o texto visual principal.
- Tabelas extensas podem ter rolagem interna, mas não causar overflow horizontal global.
- Não inventar novos indicadores, categorias de gravidade, recomendações médicas ou alegações de eficácia em operação real.

## 10. Identidade acadêmica e pendências

O TCC identifica a UNIVESP, o curso de Ciência de Dados, o ano de 2026 e a orientação de Aline Martins Nascimento Belchior. Apresenta sete autores: Caio Henrique Granado; Ducilene da Costa; Jose Olavo Bernardo Freire; Luis Gustavo de Almeida Barbeiro; Mayara Aparecida de Queiroz; Tiago Trombini; William Cesar Frutuoso Figueredo.

Antes da publicação dessa identificação, confirmar grafia e acentuação dos nomes, polos, forma de crédito e situação final do trabalho. Há diferença de acentuação de José entre elementos do próprio manuscrito; não normalizar nomes por suposição.

Proposta de rodapé, sujeita a essa confirmação: “Trabalho de Conclusão de Curso em Ciência de Dados — UNIVESP, 2026.” Autoria completa pode ficar na Home ou em Dados e método, sem repetir sete nomes em toda navegação.

O arquivo local não deve ser automaticamente copiado para `public`, enviado ao GitHub ou disponibilizado para download. A versão pública deve ser escolhida e autorizada separadamente.

## 11. Encaminhamento das próximas fases

| Etapa | Entrega | Critério principal de aceite |
| --- | --- | --- |
| 16A — esta etapa | Organização, vocabulário e textos-base com rastreabilidade | Revisão humana da proposta; divergências do manuscrito registradas, não propagadas. |
| 16B — apresentação do estudo | Home, identificação acadêmica e narrativa central | O visitante entende pergunta, método, achados e limites sem conhecer H1, AP ou serving. |
| 16C.1 — consulta municipal | Aproximação entre previsão, origem e observado | É possível distinguir alerta confirmado, não confirmado e ausência de avaliação; filtros preservados. |
| 16C.2 — avaliação do modelo | Explicação das métricas e do cenário de antecipação | Avaliação geral não é confundida com antecipação; denominadores e comparação com persistência explícitos. |
| 16D — histórico | Temas por pergunta, explicações e detalhe sob demanda | Gráficos mantêm período, unidade, recorte e limitações de filtro corretos. |
| 16E.1 — mapa | Linguagem e hierarquia do painel | Contexto retrospectivo, legenda, busca e estados de falha preservados; sem categorias artificiais. |
| 16E.2 — dados e método | Conteúdo didático com rastreabilidade técnica acessível | A simplificação não esconde limitações nem confunde dados ausentes com zero. |
| 16F — responsividade e acessibilidade | Validação real em desktop/mobile, teclado e toque | Sem clipping global; leitura e interação não dependem de hover ou somente cor. |
| 16G — revisão integrada | Regressões, validação técnica e revisão de compreensão | Ciência e contratos inalterados; cinco páginas consistentes e fluxo completo verificado. |

Em cada implementação futura: escopo pequeno, revisão de diff, testes proporcionais e validação visual real. Os testes científicos existentes não devem ser enfraquecidos para acomodar uma simplificação de texto. Commit, push e deploy dependem de autorização própria.

### Roteiro de revisão com pessoas não especialistas

Pedir que uma pessoa, sem explicação prévia do autor, responda:

1. Qual foi a pergunta da pesquisa?
2. Esses resultados são de hoje ou de um período passado?
3. O que significa “alerta do modelo”? Ele pode não se confirmar?
4. O que muda entre uma e quatro semanas?
5. “Sem alerta” significa que não houve dengue?
6. O clima não teve relação com dengue, ou não melhorou o modelo testado?
7. Onde estão as fontes, os limites e os resultados completos?

Essas perguntas são critérios propostos para as próximas fases, não resultados de um teste com usuários já realizado.

## 12. Estado de entrega

16A entregue como proposta documental. O TCC foi atualizado pelo autor antes da Fase 16B; esta revisão apenas conferiu suas tabelas. A implementação local da Fase 16B é acompanhada no diff dos arquivos `web/`.

A revisão editorial restante do TCC é um trabalho separado. Os dados pré-textuais e o capítulo da aplicação ainda precisam de decisão dos autores antes de tratar a versão v5 como publicação acadêmica final.

### Fase 16C.1 — consulta municipal implementada localmente

A consulta de `/predicao` reúne o alerta e o estado futuro observado no mesmo card, com prazos de uma a quatro semanas em destaque e H1–H4 como identificação secundária. O estado na semana de referência fica visível antes dos cards, distinguindo o recorte de antecipação das situações em que já havia risco elevado. Probabilidades, limites e evolução anual permanecem acessíveis em expansões nativas; ressalvas essenciais e ausência de avaliação permanecem visíveis. A classificação continua vindo de `predicao`, sem recálculo na interface. Filtros, URLs, contratos e dados não foram alterados.

Validação local: lint, build e 234 testes em 31 arquivos aprovados, incluindo 12 novas verificações de apresentação. No navegador, dados reais de Penápolis confirmaram as quatro combinações de alerta/observado, troca de semana, SE52 com apenas H1 avaliado, expansão por teclado e troca de horizonte no gráfico. Em desktop, `scrollWidth = clientWidth = 1265 px`; em viewport de 390 × 844 px, ambas as larguras foram 375 px, com cards em uma coluna e sem overflow global. Uma sessão limpa não registrou erros de console.

Pendência para a Fase 16F: em viewport de 320 × 740 px, a barra vertical deixa 305 px úteis, mas o `body` já possuía `min-width: 320px` antes desta implementação. O documento mede 320 px nesse cenário. Essa limitação global não foi corrigida nesta etapa; não declarar validação completa para todas as larguras mobile. A navegação superior mantém a rolagem horizontal existente.

A Fase 16C.1 foi entregue para revisão humana, sem commit, push ou deployment. A continuidade na Fase 16C.2 está registrada a seguir.

### Fase 16C.2 — avaliação do modelo implementada localmente

A rota `/predicao` oferece navegação local entre consulta municipal e avaliação nacional. Seu rótulo no menu passa a ser “Resultados”, sem alteração do endereço ou das regras de navegação. A avaliação distingue todas as situações avaliadas do recorte sem risco elevado na semana de referência, com explicação de que uma situação é um município em uma semana, não uma pessoa ou um município único.

Os quatro cards de antecipação mostram recall e precisão com seus denominadores em linguagem simples, acompanhados das contagens oficiais de alertas não confirmados e riscos não identificados. Não há recálculo de métricas ou agregação nova. A seção permanece independente dos filtros municipais. A comparação H1 entre recall geral e antecipação é formatada diretamente dos campos existentes, não escrita como valores numéricos duplicados.

Uma expansão nativa, fechada inicialmente, reúne quatro tabelas semânticas com todas as métricas, matrizes de confusão e comparação modelo/persistência nos dois cenários. AP é apresentada como Average Precision, não como taxa de acerto ou área trapezoidal. Brier, F1, ROC-AUC, prevalência e acurácia balanceada têm definições próximas às tabelas. Campos nulos de alertas/proporção permanecem “—”, sem conversão para zero. Limites científicos, período retrospectivo e ausência de garantia municipal permanecem visíveis na leitura principal.

Validação local: lint, build e 245 testes em 32 arquivos aprovados, incluindo 11 novos testes de apresentação e atualização do teste do rótulo de navegação. As regressões conferem denominadores, erros, todos os valores das tabelas nos quatro prazos e dois cenários, campos nulos, leitura dos props, UTF-8 e estrutura acessível.

No navegador: navegação Início–Resultados e links locais funcionando; filtros de Penápolis preservados; troca da SE34 para SE52 atualiza a consulta sem mudar a avaliação nacional. Expansão técnica funciona com Enter. Em desktop, `scrollWidth = clientWidth = 1265 px`. Em viewport de 390 × 844 px, ambas são 375 px, inclusive com as tabelas abertas; cards ficam em uma coluna e headings/parágrafos não ultrapassam a largura disponível. Cada container de tabela tem 319 px úteis e conteúdo de 700 px, com rolagem interna; ArrowRight avançou o primeiro container em 40 px sem ampliar o documento. Nenhum erro de console foi registrado. A pendência global de 320 px da Fase 16F permanece, sem ampliação do escopo.

Dados, contratos, classificações, cálculos e infraestrutura não foram alterados. As skills de Next.js e React orientaram a manutenção dos componentes de avaliação no servidor e o uso de controles HTML nativos, sem dependências novas. A verificação visual foi feita com o navegador disponível no ambiente.

Esta implementação aguarda revisão humana. A próxima etapa é a Fase 16D, dedicada ao histórico. Não houve commit, push ou deployment; o TCC e as alterações locais anteriores foram preservados.

### Fase 16D — Histórico implementado localmente

A rota `/historico` passou a organizar a leitura por perguntas sobre evolução semanal e anual, épocas de aumento, diferenças entre lugares, repetição/duração dos períodos de risco e associação com clima. A introdução explica o caráter histórico, sem jargão de contratos, e três links locais permitem navegar entre casos/lugares, risco e clima. A evolução semanal nacional vem antes da comparação anual.

Casos, incidência por 100 mil habitantes, Semana Epidemiológica, mediana, faixa Q25–Q75, percentil e diferença temporal do clima têm explicações próximas às visualizações. Cobertura, tabela anual, ranking municipal de risco, indicadores completos de duração e gráficos climáticos ficam em expansões HTML nativas, fechadas inicialmente. Os avisos sobre ausência de previsão atual, definição de risco, não causalidade e limites territoriais continuam visíveis. O resultado central de duração usa a mediana do contrato, sem destacar o máximo como comportamento típico.

A consulta municipal mantém três indicadores principais; população, cobertura e recorrência ficam nos detalhes. O percentual de semanas em risco mostra seu denominador oficial. A tabela municipal usa os valores que já estavam na série e no resumo anual existente, sem novo cálculo científico. É uma alternativa à leitura por hover: a consulta de 2024 inclui suas 52 semanas, com casos e indicação de preenchimento com zero. O aviso explica que esse preenchimento não comprova ausência de transmissão.

Os filtros e seu alcance foram preservados: evolução de casos do Brasil/município responde ao ano; sazonalidade e comparações territoriais usam 2016–2025; risco usa 2018–2025 e não responde ao ano selecionado; duração de episódios é nacional; clima resume correlações municipais de 2016–2025 para Brasil/regiões, não uma correlação única de uma série agregada. A UF continua sem curva semanal/sazonal de casos, e o município continua sem curva semanal de risco ou associação climática individual nesta visualização. Nenhuma lacuna foi preenchida com dados de outro recorte ou agregação nova.

Validação técnica final: lint, build e **264 testes em 33 arquivos** aprovados. Foram adicionados 19 testes de apresentação, utilizando contratos reais e navegação isolada para renderização; eles protegem unidades, escopos, valores das tabelas, denominadores, ausências de dados, expansões fechadas, navegação local e UTF-8. A interação de filtros foi verificada separadamente no navegador. `git diff --check` passou.

Validação no navegador: Início–Histórico, Brasil/2024, alternância casos/incidência, Sudeste, São Paulo e Penápolis/2024 funcionando. O ano foi removido/desabilitado ao selecionar região/UF e reabilitado na consulta municipal. A série municipal retornou HTTP 200, schema 1.0, código 3537305 e 522 semanas; o índice territorial também retornou HTTP 200 com 5.571 itens. O risco municipal permaneceu no período completo ao mudar o ano dos casos.

Desktop: `scrollWidth = clientWidth = 1265 px`. Em viewport 390 × 844, ambas são 375 px; em 360 × 800, ambas são 345 px. Nenhum heading, parágrafo, card ou seção inspecionado ultrapassou a largura útil. Com expansões abertas, a página permaneceu sem overflow global: a tabela anual possui 285 px úteis e conteúdo de 760 px; a tabela municipal possui 279 px úteis e conteúdo de 760 px, com ArrowRight avançando 40 px internamente. O gráfico semanal municipal também mantém rolagem própria. As âncoras de risco e clima ficaram a aproximadamente 160 px do topo, abaixo do header de aproximadamente 139 px no mobile. Nenhum erro de console ou overlay foi registrado. A pendência global de viewport 320 px, já registrada para 16F, não foi ampliada nem ocultada nesta etapa.

As skills de Next.js e React orientaram a manutenção dos carregamentos, componentes e hooks existentes, com controles HTML nativos e sem novas dependências. A orientação de verificação foi aplicada com o navegador disponível, pois a CLI de automação indicada não está instalada. Somente a apresentação histórica, seus testes e este registro foram alterados nesta etapa. Serving, contratos, cálculos, TCC, mapa, qualidade e as alterações anteriores de Home/Resultados foram preservados.

A Fase 16D aguarda revisão humana. Próxima etapa: **16E.1 — Mapa**, dedicada à linguagem e hierarquia do painel, preservando o contexto retrospectivo, as classificações oficiais, a busca e os estados de falha. Não houve commit, push ou deployment.

### Revisão das Fases 16C.2 e 16D — Eixos e interpretação das métricas

Após as observações humanas sobre os prints, esta revisão acrescentou títulos de eixos, unidades e valores graduados aos gráficos SVG históricos: evolução semanal, panorama anual, sazonalidade nacional/regional, proporção semanal de municípios em risco, duração dos episódios e correlações climáticas. Os limites são os mesmos usados nas curvas, faixas e barras existentes, incluindo a escala fixa de 0–100% para o risco e limites com valores negativos nas correlações. Não houve mudança nas coordenadas dos dados, nos cálculos ou nas regras científicas; o espaço adicional do SVG acomoda os rótulos. A consulta semanal municipal recebeu identificação textual dos dois eixos e de sua faixa de casos.

Em telas pequenas, os gráficos SVG têm largura mínima interna de 640 px para não reduzir os números a texto ilegível. A rolagem pertence somente ao container do gráfico, com região nomeada, foco por teclado e orientação visível de swipe/setas. Não foi usado overflow oculto para mascarar defeitos. As tabelas existentes continuam como alternativa de leitura dos valores.

O guia de indicadores de `/predicao`, dentro da expansão já existente, agora explica escala, direção, significado no estudo e exemplos para recall, precisão, AP, ROC-AUC, F1, acurácia balanceada, Brier e prevalência. AP maior e Brier menor são preferíveis; prevalência não recebe julgamento de melhor/pior. Os exemplos reais usam diretamente os campos oficiais de H1/antecipação do Brasil em 2025, com esse contexto explícito e tratamento de alertas nulos. Os demais exemplos são identificados como ilustrativos. Nenhum indicador é apresentado como porcentagem única de acerto ou chance individual de dengue.

A interpretação foi conferida na documentação oficial: [Average Precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html), [ROC-AUC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html) e [Brier score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html). Não foram introduzidos cálculos ou métricas novos no serving.

Validação técnica: lint, build e **272 testes em 34 arquivos** aprovados; `git diff --check` passou. As oito regressões adicionais protegem coordenadas/limites dos eixos, escalas percentual e negativa, rótulos/unidades, acesso à rolagem e exemplos que acompanham os props sem converter ausência em zero.

Validação no navegador integrado, usando o build local: em desktop, `scrollWidth = clientWidth = 1148 px`. Em viewport 390 × 844 px, ambas as larguras foram 375 px; em 360 × 800 px, 345 px, tanto no Histórico quanto em Resultados. Nenhum rótulo inspecionado ultrapassou os limites do próprio SVG. No mobile de 390 px, os containers nacionais dos gráficos têm 287 px úteis e conteúdo de 640 px; ArrowRight avançou 40 px internamente. As tabelas abertas de Resultados têm 319 px úteis e conteúdo de 700 px, sem overflow global. Headings, parágrafos, cards e guia de métricas permaneceram dentro da largura útil. A troca para 2024/incidência atualizou corretamente o eixo temporal e a unidade. A expansão das métricas funciona com Enter e as sessões não registraram erros de console ou overlays.

Arquivos desta revisão: `historical-chart-axes.tsx`, `historical-chart-axes.module.css`, `historical-chart-axes.test.ts`, `weekly-evolution.tsx`, `annual-panorama.tsx`, `seasonality-chart.tsx`, `territorial-analysis.tsx`, `historical-risk-analysis.tsx`, `historical-climate-analysis.tsx`, `municipality-panorama.tsx`, `historical-reading.test.ts`, `prediction-evaluation-details.tsx`, `prediction-performance.module.css`, `prediction-performance.test.ts` e este registro.

As skills de Next.js/React orientaram o reaproveitamento dos componentes existentes e de HTML nativo; as de verificação exigiram conferir renderização real, rolagem e console. Não foram instaladas dependências. A pendência global de 320 px continua reservada à Fase 16F. As alterações anteriores, o TCC, os contratos, os dados e as classificações foram preservados. Esta revisão aguarda aprovação humana; não antecipa a Fase 16E.1 nem envolve commit, push ou deployment.

### Histórico — Adaptação mobile sem rolagem dos gráficos

A pedido da revisão humana, a apresentação mobile substitui a largura mínima de 640 px descrita acima. Até 680 px, cada gráfico SVG cabe inteiro na área disponível, com títulos e unidades em HTML fora do desenho para permitir quebra de linha. Os eixos mostram até três referências temporais e três graduações verticais, com abreviações explicadas de mil/milhão quando aplicáveis. Percentuais e correlações mantêm sua unidade e sinal. No desktop, o SVG, seus rótulos e sua geometria permanecem como na revisão anterior.

A versão mobile reutiliza os mesmos caminhos, barras e pontos, com transformação linear apenas das coordenadas de apresentação. Nenhuma observação foi removida ou agregada; a seleção reduz somente rótulos. Os limites mínimo/máximo de cada eixo continuam os mesmos. A adaptação não usa leitura de viewport em hooks nem dependências novas: as duas apresentações compartilham o conteúdo gráfico e a visibilidade é definida pela media query existente. Apenas a apresentação visível participa da leitura acessível.

O gráfico municipal semanal também passou a caber no mobile, sem sua antiga largura mínima de 760 px. Todas as barras permanecem representadas; início, meio e fim recebem rótulos. Foi corrigida uma sobra de 1–2 px provocada pelo texto dos rótulos ocultos, sem esconder overflow. A tabela de detalhes mantém todos os valores e sua rolagem própria, quando necessária.

Validação final: lint, build e **275 testes em 34 arquivos** aprovados; `git diff --check` passou. As regressões verificam a preservação do caminho original nas duas apresentações, as abreviações, as posições das marcações selecionadas, os limites numéricos dos eixos compactos e os três rótulos municipais.

No navegador integrado, desktop apresentou `scrollWidth = clientWidth = 1265 px`. Em viewport 390 × 844 px, o documento mediu 375/375 px; os gráficos nacionais mediram 287/287 px e os climáticos abertos, 253/253 px (scrollWidth/clientWidth), sem rolagem. Em 360 × 800 px, o documento mediu 345/345 px; os gráficos nacionais, 257/257 px, e os climáticos, 223/223 px. Os rótulos inspecionados permaneceram dentro dos próprios SVGs, e os caminhos das curvas foram iguais nas duas versões. A troca para 2024/incidência atualizou os títulos corretamente; a sazonalidade do Sudeste também permaneceu dentro da largura disponível.

Penápolis/2024 manteve suas 52 barras, com rótulos de SE1, SE27 e SE52. Seu container mediu 315/315 px na viewport de 390 px e 285/285 px em 360 px. Com a tabela municipal aberta, somente seu container teve rolagem (249 px úteis e conteúdo de 760 px); o documento permaneceu em 345/345 px. Não foram observados erros de console ou overlays. A navegação horizontal global e a pendência preexistente de 320 px não foram redesenhadas nesta revisão.

Arquivos desta revisão: `historical-chart-axes.tsx`, `historical-chart-axes.module.css`, `historical-chart-axes.test.ts`, `weekly-evolution.tsx`, `annual-panorama.tsx`, `seasonality-chart.tsx`, `territorial-analysis.tsx`, `historical-risk-analysis.tsx`, `historical-climate-analysis.tsx`, `municipality-panorama.tsx`, `municipality-panorama.module.css`, `historical-reading.test.ts` e este registro. As skills de Next.js/React orientaram o compartilhamento das séries e a solução por CSS sem novos carregamentos; a verificação visual foi feita com o navegador disponível, sem instalar a CLI de automação.

Serviços, dados, contratos, cálculos, classificações, TCC e alterações anteriores foram preservados. A adaptação aguarda revisão humana. Não houve commit, push ou deployment; a Fase 16E.1 não foi iniciada.

### Revisão humana — Restauração da versão mobile anterior

A adaptação compacta acima foi revertida após a revisão humana identificar perda de legibilidade. Foram restaurados os gráficos SVG com largura mínima de 640 px e rolagem interna no mobile, além da apresentação municipal semanal anterior, com largura mínima de 760 px. Desktop, eixos, unidades, explicações dos indicadores e alterações anteriores foram preservados.

Lint, build e 272 testes em 34 arquivos passaram. A redução de três testes corresponde à remoção das regressões específicas da apresentação compacta revertida. `git diff --check` passou.

No navegador integrado, desktop mediu 1148/1148 px (scrollWidth/clientWidth). Na viewport mobile de 390 × 844 px, o documento mediu 375/375 px, sem overflow horizontal global; os gráficos nacionais tiveram 287 px disponíveis e conteúdo de 640 px, com rolagem apenas em seus containers. A rolagem por teclado foi confirmada, com deslocamento de 40 px. Não foram observados erros de console.

Dados, serving, contratos, cálculos, TCC e trabalho local anterior não foram alterados nesta reversão. Não houve commit, push ou deployment.

### Fase 16E.1 — Mapa implementado localmente

A rota `/mapa` prioriza semana de referência, prazo de uma a quatro semanas depois, busca municipal e interpretação do resultado. SE e H1–H4 são explicados junto aos filtros, sem alterar seus valores, URLs, disponibilidade ou normalização. A natureza retrospectiva de 2025 permanece na introdução, junto ao mapa e na leitura municipal.

A legenda saiu da sobreposição ao desenho e explica ALERTA, SEM ALERTA e SEM AVALIAÇÃO em texto. Sem alerta não significa ausência de dengue; a ausência de avaliação não recebe score zero. O painel municipal fica ao lado do mapa no desktop e abaixo dele em telas menores, com resultado e contexto temporal antes dos números. Probabilidade e limite de alerta ficam em expansão HTML nativa, fechada inicialmente. Uma segunda expansão conserva cobertura e limite do recorte; tamanho do asset/compressão deixaram a leitura principal. A definição curta de risco elevado segue o texto aprovado neste planejamento e não equivale a declaração oficial de epidemia.

O componente visual `MunicipalityMapResult` isola a apresentação para testes sem alterar seleção, join ou classificação. A decisão continua vindo de `predicao` pelo join existente, não de uma nova comparação de score. Loading e falha retornam antes da apresentação de dados; o erro explica que não é Sem alerta nem Sem avaliação. O retry e a geometria neutra continuam nas estruturas existentes.

Validação técnica final: lint, build e **286 testes em 35 arquivos** passaram, incluindo 14 novas regressões de prazo, classificação oficial, detalhes numéricos, limites interpretativos, loading, falha, ausência e encoding UTF-8. A regressão de encoding procura sequências corrompidas, sem confundir o Ã legítimo de AVALIAÇÃO com mojibake. `git diff --check` passou. Permanecem cinco páginas estáticas e os Route Handlers existentes.

No navegador integrado com o build local, o mapa manteve 5.571 polígonos. Penápolis foi selecionado por busca e Enter; SE49/H1 mostrou Sem alerta, score 0,62% e limite 18,77%. A troca para H2 conservou o município e atualizou score para 1,58% e limite para 19,08%. SE52 normalizou o prazo para H1 e ofereceu apenas esse prazo. Penápolis/SE12/H1 exibiu Alerta com score 99,82%. Fernando de Noronha apareceu como Sem avaliação, sem detalhes de probabilidade. A expansão funcionou por teclado e a navegação Início/Mapa foi conferida.

Desktop apresentou scrollWidth/clientWidth de 1265/1265 px e, na conferência final, 1148/1148 px, conforme o tamanho normal da janela. Em viewport 390 × 844 px, o documento mediu 375/375 px; em 360 × 800 px, 345/345 px, inclusive com detalhes abertos. Headings, parágrafos, cards, seções e SVG inspecionados permaneceram dentro do viewport; não houve erros de console. A pendência global preexistente de 320 px permanece para a Fase 16F. Falha/loading foram validados em testes controlados de apresentação e na suíte existente de estado; não houve interceptação HTTP de falha no navegador nesta etapa.

Arquivos desta etapa: `web/src/app/mapa/page.tsx`; `map-foundation.tsx`, `map-foundation.module.css`, `municipality-map.tsx`, `municipality-map.module.css`, `municipality-map-result.tsx` e `map-reading.test.ts`, em `web/src/components/map/`; e este registro. As skills de Next.js/React orientaram a manutenção dos carregamentos e hooks existentes, a apresentação testável e as expansões nativas. A verificação visual utilizou o navegador integrado disponível, sem instalar dependências.

Serving, contratos, cálculos, geometria, TCC e alterações locais anteriores foram preservados. A Fase 16E.1 aguarda revisão humana; próxima etapa proposta: 16E.2 — Dados e método. Não houve commit, push ou deployment.

### Fase 16E.2 — Dados e método implementado localmente

A rota permanece `/dados-qualidade`, com título, metadata e rótulo de navegação “Dados e método”. A leitura principal responde a cinco perguntas: quais dados usamos, como os organizamos, o que chamamos de risco elevado, como testamos o modelo e o que os resultados não permitem concluir. SINAN, IBGE e ERA5-Land são apresentados por seu papel no estudo, antes dos campos técnicos.

As fontes meteorológicas são descritas como reanálise em grade, não estações em cada município. Município-semana, incidência por 100 mil habitantes e SE têm explicações próximas ao conteúdo. A leitura principal destaca apenas três indicadores da base final, vindos dos props oficiais, sem recálculo. O preenchimento com zero não comprova ausência de transmissão nem registro explícito de zero na fonte. A observação oficial sobre Censo 2022/referência de 2023 e descontinuidade metodológica continua visível.

Risco elevado é explicado como incidência acumulada em quatro semanas acima da referência sazonal do próprio município. A expansão técnica mantém P90, janela ±4 semanas em anos anteriores, mínimo de dois anos e 12 observações, operador estrito > e distinção do alerta, cujo limite de decisão usa >=. O desenho temporal distingue desenvolvimento de 2018–2024 e teste final de 2025, persistência, avaliação geral e antecipação. A narrativa e os detalhes foram conferidos nos documentos 02, 04, 10 e 12 e no planejamento já aprovado. Não há nova regra científica nem afirmação de desempenho individual garantido.

O visitante encontra oito expansões HTML nativas, inicialmente fechadas: regra do risco; configuração temporal/modelo final; indicadores completos; funil SINAN; associação territorial; zero-fill; população por ano; cobertura climática. Contagens, campos, exceções, verificações sem contagem própria e referências existentes foram preservados. Identificadores de arquivos internos permanecem na rastreabilidade, explicitamente sem serem apresentados como links públicos. A tabela populacional mantém dez anos, caption, cabeçalhos e container focável, com orientação de rolagem.

Permanecem visíveis os limites de dados consolidados/avaliação retrospectiva, teste final em um único ano, desigualdade de desempenho, ausência de dados diferente de ausência de dengue e associação diferente de causalidade. O modelo final é epidemiológico; falta de melhora consistente com as variáveis climáticas testadas não implica falta de relação entre clima e dengue.

Validação final: lint, build e **300 testes em 36 arquivos** aprovados; `git diff --check` passou. São 14 regressões novas de leitura, contagens, zero-fill, população, território, clima, critérios do risco, separação temporal, rastreabilidade, props e UTF-8. O carregamento paralelo dos cinco contratos no servidor foi mantido, sem novos fetches, componentes client ou dependências. O build conserva cinco páginas estáticas e os Route Handlers existentes.

No navegador integrado, desktop apresentou scrollWidth/clientWidth de 1265/1265 px. As oito expansões abriram por Enter. Em viewport 390 × 844 px, o documento mediu 375/375 px; em 360 × 800 px, 345/345 px, com todos os detalhes abertos. Nenhum heading, parágrafo, seção, card, aside ou summary inspecionado ultrapassou a largura útil. A tabela tem conteúdo de 720 px e containers de 279 px e 249 px, respectivamente: sua rolagem permaneceu interna, com ArrowRight deslocando 40 px. Não foram observados erros de console ou overlays. O link para Resultados foi confirmado na rota `/predicao`. A pendência global preexistente de 320 px permanece para a Fase 16F; a navegação superior conserva seu scroll horizontal intencional.

Arquivos desta etapa: `web/src/app/dados-qualidade/page.tsx`; `web/src/components/quality/quality-overview.tsx`, `quality-overview.module.css` e `quality-reading.test.ts`; `web/src/lib/constants/navigation.ts` e `navigation.test.ts`; e este registro. As skills de Next.js/React orientaram a preservação do carregamento no servidor e das expansões nativas; a validação visual foi feita no navegador integrado disponível, sem instalar a CLI de automação.

Dados, serving, contratos, cálculos, TCC, mapa, histórico, resultados e alterações locais anteriores foram preservados. A Fase 16E.2 aguarda revisão humana; próxima etapa proposta: 16F — Responsividade e acessibilidade. Não houve commit, push ou deployment.

### Fase 16F — Responsividade e acessibilidade: implementação e validação local

O overflow global de 320 px foi reproduzido no navegador: a barra vertical deixava 305 px úteis, mas o body exigia min-width de 320 px, ampliando o documento. Foi removida somente essa restrição. Não foi aplicado overflow-x hidden na raiz. A Home passou a medir scrollWidth/clientWidth de 305/305 px, com títulos e parágrafos dentro da largura disponível.

O gráfico de probabilidades dos Resultados recebeu região nomeada, tabIndex zero e foco visível interno, para não ser cortado pela moldura. ArrowRight avançou 40 px no container, que mede 249 px úteis e 746 px de conteúdo em viewport 320 px, sem ampliar a página. O SVG, suas dimensões e os cálculos não mudaram. Nas expansões municipais “Como o alerta foi definido”, a área mobile era de aproximadamente 19 px nos Resultados e 20 px no Mapa: passou a pelo menos 44 px. “Limpar seleção” no Mapa passou de aproximadamente 35 px para 44 px. Esses ajustes de tamanho são restritos ao breakpoint mobile; não há novo comportamento de seleção.

A matriz real das cinco páginas (Início, Histórico, Dados e método, Resultados e Mapa), com o build local no navegador integrado, apresentou:

| Viewport | scrollWidth/clientWidth em cada página | Overflow global |
| --- | --- | --- |
| 320 × 740 px | 305/305 px | Não |
| 390 × 844 px | 375/375 px | Não |
| 768 × 1024 px | 753/753 px | Não |
| 1280 × 900 px | 1265/1265 px | Não |

Nenhum heading, parágrafo, seção, card, summary, input ou select inspecionado ultrapassou a largura útil. Em 320 px, as oito expansões do Histórico e as oito de Dados e método foram abertas por Enter. Resultados também foi conferido com Penápolis/SE49, evolução de probabilidades e avaliação nacional expandidas. No Mapa, Penápolis foi selecionado com ArrowDown/Enter; a troca de H1 para H2 por teclado manteve a seleção. A geometria conservou 5.571 polígonos e as classificações permaneceram expressas em texto, sem depender somente de cor ou hover.

O skip link recebeu foco visível e Enter transferiu foco para main-content. A navegação horizontal mobile continua intencional: o foco no link Mapa tornou-o visível dentro do container, sem deslocar horizontalmente o documento. O filtro de ano do Histórico mudou para 2025 pelo teclado. Gráficos históricos mantêm o SVG mínimo de 640 px e rolagem própria, conforme a preferência humana; ArrowRight deslocou 40 px. A tabela populacional em 320 px tem 209 px úteis e conteúdo de 720 px, também rolando 40 px internamente. As tabelas dos Resultados mantêm regiões nomeadas por seus captions. Não foram registrados erros de console no percurso final.

Lint, build e **303 testes em 36 arquivos** passaram; git diff --check passou. Foram acrescentadas três regressões focadas: ausência de largura mínima/mascaramento de overflow nos blocos raiz; áreas mobile ajustadas de pelo menos 44 px; renderização da região nomeada e focável do gráfico de probabilidades. Os testes de CSS protegem as declarações locais e não substituem a matriz de navegador. O build mantém cinco páginas estáticas e os Route Handlers existentes.

Arquivos alterados nesta etapa: web/src/app/globals.css; web/src/app/accessibility-contract.test.ts; web/src/components/prediction/prediction-score-evolution.tsx; prediction-score-evolution.module.css; prediction-results.module.css; prediction-results.test.ts, na mesma pasta prediction; web/src/components/map/municipality-map.module.css; e este registro. Todas as alterações anteriores foram preservadas. Nenhum arquivo de data/serving, contrato, cálculo, classificação, loader, TCC ou README foi modificado nesta etapa.

As skills de Next.js/React orientaram a manutenção da arquitetura e o uso de atributos HTML sem novos hooks ou dependências; a verificação de navegador exigiu medir o documento e testar os controles reais. A CLI de automação não foi instalada: foi utilizado o navegador integrado disponível. A validação utilizou viewport e teclado/clique, não emulação comprovada de touchscreen nem um leitor de tela real. Swipe/toque em celular físico e leitura assistiva permanecem para conferência humana; este registro não declara conformidade integral com WCAG. Evidências visuais foram salvas temporariamente fora do repositório.

A implementação local da 16F aguarda revisão humana. A próxima etapa proposta é 16G — revisão integrada, sem antecipar publicação. Não houve commit, push ou deployment.

### Fase 16G — Revisão integrada local

Revisão autorizada após a apresentação do escopo: leitura para público leigo, coerência entre as cinco páginas, navegação, fidelidade ao TCC/documentação e regressões funcionais. Não é redesign nem autorização de publicação. Nenhuma nova regressão comprovada exigiu alteração do frontend nesta etapa; somente este registro foi atualizado. O working tree já continha as implementações anteriores e o TCC não versionado, que foram preservados.

#### Conteúdo e fidelidade científica

Foram confrontadas as explicações públicas com os trechos metodológicos, resultados e limitações de reports/methodology/TCC_v5.docx e com os documentos 02, 04, 07, 10, 12 e 19. O DOCX foi lido semanticamente com python-docx, sem modificar o manuscrito; isso não constitui revisão visual da diagramação. As tabelas 22 e 23 conferem com os números apresentados para avaliação geral e antecipação em 2025. A revisão confirmou a distinção entre histórico de 2016–2025, desenvolvimento de 2018–2024 e teste final de 2025; risco observado e alerta do modelo; prazo futuro específico e ocorrência em qualquer momento do intervalo; avaliação nacional e consulta municipal.

A referência histórica sazonal do risco não foi confundida com o limite de decisão do alerta. AP maior e Brier menor são descritos corretamente, sem interpretação como porcentagem geral de acerto ou chance individual de dengue. A falta de melhora consistente com o clima não é apresentada como ausência de associação, e correlação não é apresentada como causalidade. Permanecem claros os limites de dados históricos consolidados, teste final de um único ano, heterogeneidade municipal e ausência de alertas operacionais atuais. A avaliação editorial não comprova compreensão por usuários leigos reais; esse teste permanece pendente.

Permanecem as pendências do manuscrito já registradas: diferença de arredondamento de AP/H2 entre as tabelas 19 e 20, notas de redação no capítulo da aplicação e itens pré-textuais a finalizar pelos autores. O valor de origem 0,8910502789475433 explica a diferença entre 0,8910 e 0,8911; não foi alterado nenhum número para harmonizar a apresentação. Não houve edição do TCC.

#### Navegação e fluxos integrados

No navegador integrado, utilizando o build local, foi percorrido Início → Resultados → Dados e método → Histórico, além do Mapa em ambiente local controlado. O CTA principal leva à avaliação, e a navegação mantém os cinco destinos existentes. A leitura inicial explica o estudo antes dos detalhes técnicos. Expansões foram acionadas por Enter, sem depender exclusivamente de hover.

Penápolis/SE49 nos Resultados apresentou os quatro prazos e a comparação com o observado. Na troca para SE52, H1 permaneceu disponível e H2–H4 passaram a “Sem avaliação neste prazo”, sem classificações antigas ou conversão para Sem alerta. A avaliação nacional continua identificada como independente dos filtros municipais, e as explicações dos indicadores incluem escala, direção e exemplos contextualizados.

No Histórico, Penápolis/2024 apresentou 52 semanas, eixos descritos em texto e total de 197 casos. Risco conserva seu período completo e clima municipal informa a indisponibilidade dessa análise individual, sem inferir ausência de associação. A âncora de risco manteve município, região, UF e ano na URL. Trocar território continua limpando o ano pela regra preexistente; selecionar 2024 após o município funciona normalmente. Links genéricos entre rotas não prometem transportar filtros de uma superfície para outra. Nenhuma dessas regras foi modificada.

#### Falha HTTP e recuperação do mapa

Foi utilizado um proxy HTTP temporário, restrito ao loopback local, com os módulos nativos de Node.js. Ele encaminhou a aplicação de 3101 para 3100 e forçou HTTP 503 somente no pathname /api/serving/prediction/map/2/49. Não foram criados arquivos de teste no repositório, instaladas dependências, alterados assets ou contratos, nem acessada a configuração de produção.

| Verificação | Resultado observado |
| --- | --- |
| SE49/H1 funcionando | 1.013 alertas, 4.556 sem alerta, 2 sem avaliação; Penápolis selecionado |
| Trocar para H2 com a falha ativada | Erro público específico de SE49/H2 e botão Tentar novamente |
| Loading infinito | Ausente; nenhum elemento aria-busy=true ao concluir a falha |
| Contagens durante a falha | ALERTA, SEM ALERTA e sem avaliação preditiva mostraram — |
| Geometria e seleção | 5.571 polígonos mantidos, em estado neutro; Penápolis permaneceu selecionado |
| Dados antigos no painel | Não apareceram classificação, score ou limite de H1 |
| Falha confundida com classificação | Não; texto distingue falha de Sem alerta e Sem avaliação |
| Filtros durante a falha | Semana 49 e horizonte 2 mantidos |
| Remover falha e tentar novamente | Contador da chamada passou de 1 para 2; somente uma foi bloqueada |
| Recuperação | SE49/H2 mantidos, cores e contagens restauradas: 1.064, 4.505 e 2 |
| Painel municipal recuperado | Penápolis: Sem alerta, probabilidade 1,58%, limite 19,08% |

Uma leitura independente da resposta canônica confirmou H2/SE49, threshold 0,190783, score de Penápolis 0,01575865218339143 e predicao=false. A classificação continua vindo de predicao pelo join existente, protegida também pelos testes que deliberadamente usam score e classificação divergentes. O frontend não reclassifica os percentuais arredondados. Após a recuperação, Fernando de Noronha apresentou Sem avaliação preditiva, sem score ou expansão numérica. SE52 normalizou o mapa para H1 e ofereceu somente esse prazo, mantendo o território selecionado.

#### Responsividade, validação técnica e limites

Em viewport 320 × 740 px, Resultados com métricas expandidas, Dados e método com tabela populacional aberta, Histórico municipal e Mapa com detalhes abertos mediram scrollWidth/clientWidth de 305/305 px. Nenhum heading, parágrafo, card ou controle inspecionado ultrapassou a largura útil. A tabela populacional rolou no próprio container de 209 px, com conteúdo de 720 px; o gráfico municipal manteve sua rolagem própria, 245/760 px, conforme a preferência humana pela apresentação anterior. No Mapa, desktop 1280 × 900 px mediu 1265/1265 px. Essas medidas complementam a matriz das cinco páginas já registrada em 16F, sem substituir testes em aparelho físico.

Não houve erros de console inesperados no percurso. O único erro no mapa foi HTTP 503, provocado intencionalmente pelo teste; a mensagem técnica ficou no console, não no painel público. Capturas de falha e recuperação foram salvas temporariamente fora do repositório. Proxy, servidor e tabs de validação foram encerrados ao final, e o override de viewport foi removido.

Lint aprovado; 303 testes em 36 Test Files aprovados; build aprovado, mantendo cinco páginas estáticas e os Route Handlers existentes; git diff --check aprovado. Não há force-dynamic em web/src. Nenhum arquivo de serving, loader, contrato, cálculo, classificação, README ou TCC foi alterado nesta revisão. Não foram adicionados testes novos porque não houve nova implementação: foram executadas as regressões existentes e o cenário HTTP controlado no navegador.

As orientações de Next.js/React conduziram a revisão da arquitetura sem refatoração, e as de documentos orientaram a leitura sem editar o manuscrito. A CLI de navegador não estava disponível; foi usado o navegador integrado, sem instalação de dependências. A revisão técnica local está concluída dentro do escopo testado. Permanecem para revisão humana a compreensão por alguém leigo, toque/swipe em celular físico, leitor de tela real e a decisão sobre versionamento/publicação. Não houve commit, push ou deployment.
