import Link from "next/link";

import { MetricCard } from "@/components/ui/metric-card";
import { formatInteger, formatPeriod } from "@/lib/serving/formatters";

import type {
  ClimateCoverageContract,
  PopulationCoverageContract,
  QualityOverviewContract,
  SinanPipelineContract,
  TerritorialCoverageContract,
} from "@/lib/serving/types";

import styles from "./quality-overview.module.css";

type QualityOverviewProps = {
  overview: QualityOverviewContract;
  sinan: SinanPipelineContract;
  territory: TerritorialCoverageContract;
  population: PopulationCoverageContract;
  climate: ClimateCoverageContract;
};

function SectionHeading({
  id,
  eyebrow,
  title,
  description,
}: {
  id: string;
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className={styles.sectionHeading}>
      <span>{eyebrow}</span>
      <h2 id={id}>{title}</h2>
      <p>{description}</p>
    </div>
  );
}

function Sources({ sources }: { sources: string[] }) {
  return (
    <div className={styles.sources}>
      <strong>Referências técnicas da preparação</strong>
      <p>Estes são identificadores de arquivos do projeto usados na auditoria, não links públicos para download.</p>
      <ul>
        {sources.map((source) => <li key={source}>{source}</li>)}
      </ul>
    </div>
  );
}

function populationTypeLabel(value: string): string {
  const labels: Record<string, string> = {
    estimativa_ibge: "Estimativa IBGE",
    censo_2022: "Censo 2022",
    censo_2022_reutilizado_em_2023: "Censo 2022 reutilizado em 2023",
  };

  return labels[value] ?? value;
}

export function QualityOverview({
  overview,
  sinan,
  territory,
  population,
  climate,
}: QualityOverviewProps) {
  const overviewData = overview.data;
  const sinanData = sinan.data;
  const territoryData = territory.data;
  const populationData = population.data;
  const climateData = climate.data;

  return (
    <div className={styles.dashboard}>
      <nav className={styles.navigation} aria-label="Nesta página: dados e método">
        <a href="#quality-sources-title">Fontes dos dados</a>
        <a href="#quality-method-title">Método e avaliação</a>
        <a href="#quality-detail-title">Detalhes técnicos</a>
      </nav>

      <section className={styles.section} aria-labelledby="quality-sources-title">
        <SectionHeading id="quality-sources-title" eyebrow={`Fontes · ${formatPeriod(overview.period)}`}
          title="Quais dados usamos?"
          description="Reunimos registros de dengue, população e informações meteorológicas para estudar os municípios brasileiros ao longo do tempo." />
        <div className={styles.sourceGrid}>
          <article>
            <span>Registros de dengue</span>
            <h3>Casos notificados — SINAN</h3>
            <p>O Sistema de Informação de Agravos de Notificação reúne as notificações utilizadas no estudo. Após os filtros documentados, organizamos os casos prováveis por município de residência e semana de início dos sintomas.</p>
          </article>
          <article>
            <span>População e território</span>
            <h3>Referências municipais — IBGE</h3>
            <p>Usamos as referências do Instituto Brasileiro de Geografia e Estatística para identificar os territórios e relacionar casos ao tamanho da população. A incidência expressa casos por 100 mil habitantes, permitindo comparar municípios de tamanhos diferentes.</p>
          </article>
          <article>
            <span>Temperatura, umidade e chuva</span>
            <h3>Estimativas meteorológicas — ERA5-Land</h3>
            <p>São dados de reanálise: estimativas meteorológicas organizadas em uma grade espacial. Não são medições de uma estação instalada em cada município. Associamos os municípios a pontos dessa grade para investigar a contribuição do clima.</p>
          </article>
        </div>
      </section>

      <section className={styles.section} aria-labelledby="quality-preparation-title">
        <SectionHeading id="quality-preparation-title" eyebrow="Preparação dos dados"
          title="Como organizamos os dados?"
          description="Cada linha da base representa um município em uma semana, não uma pessoa. SE significa Semana Epidemiológica: a divisão semanal usada para acompanhar os registros ao longo do tempo." />
        <ol className={styles.steps}>
          <li><strong>Selecionamos os registros</strong><p>Aplicamos os critérios do estudo e verificamos município, semana, período e classificação dos registros. As remoções documentadas podem ser consultadas abaixo.</p></li>
          <li><strong>Associamos as fontes</strong><p>Harmonizamos os códigos territoriais e integramos a população de referência e os dados climáticos. As exceções de cobertura continuam identificadas.</p></li>
          <li><strong>Completamos a sequência semanal</strong><p>Incluímos as combinações município-semana ausentes com zero, mantendo a soma dos casos. Esse procedimento é chamado de preenchimento com zero, ou zero-fill.</p></li>
        </ol>
        <div className={styles.keyMetrics}>
          <MetricCard label="Casos prováveis na base final" value={formatInteger(overviewData.casos_finais_preservados)} description="Total após os filtros e a associação territorial, no período estudado." />
          <MetricCard label="Unidades territoriais" value={formatInteger(overviewData.unidades_territoriais)} description="Cobertura da base preparada; não significa que todas tenham avaliação do modelo." />
          <MetricCard label="Municípios em semanas" value={formatInteger(overviewData.municipio_semanas)} description="Quantidade de combinações município-semana da base, não de pessoas nem de municípios únicos." />
        </div>
        <div className={styles.preservationNote}>
          <strong>Uma semana preenchida com zero não comprova ausência de dengue</strong>
          <p>O preenchimento não transforma uma combinação originalmente ausente em uma notificação de zero na fonte, nem comprova ausência de transmissão. Os indicadores de cobertura preservam essa diferença.</p>
        </div>
        <p className={styles.readingNote}>{populationData.observacao_metodologica}</p>
      </section>

      <section className={styles.section} aria-labelledby="quality-risk-title">
        <SectionHeading id="quality-risk-title" eyebrow="Pergunta do modelo"
          title="O que chamamos de risco elevado?"
          description="Neste estudo, é quando a incidência acumulada em quatro semanas supera uma referência histórica do próprio município para aquela época do ano." />
        <p className={styles.readingNote}>Não é um limite nacional fixo de casos, um diagnóstico individual ou uma declaração oficial de epidemia. O modelo tenta estimar esse estado municipal de uma a quatro semanas depois, não o número futuro de casos.</p>
        <details className={styles.details}>
          <summary>Regra técnica do risco e diferença para o alerta</summary>
          <div className={styles.detailsContent}>
            <p>A referência é o percentil 90 (P90) histórico sazonal, uma medida de posição na distribuição histórica usada como referência para valores elevados. Usamos semanas próximas à semana avaliada (janela de ±4 semanas), exclusivamente em anos anteriores, com no mínimo dois anos de histórico e 12 observações válidas.</p>
            <p><code>{"Risco elevado: incidência acumulada em quatro semanas > P90 sazonal"}</code>. A comparação é estrita: igualdade não caracteriza risco elevado. Isso não impõe que 10% das semanas de cada ano tenham risco elevado.</p>
            <p>Essa regra define o estado observado. Já o alerta é a indicação oficial do modelo, emitida quando sua probabilidade estimada atinge ou supera o limite de decisão definido na validação. Uma indicação pode se confirmar ou não; são conceitos diferentes.</p>
          </div>
        </details>
      </section>

      <section className={styles.section} aria-labelledby="quality-method-title">
        <SectionHeading id="quality-method-title" eyebrow="Avaliação do estudo"
          title="Como testamos o modelo?"
          description="Respeitamos a ordem do tempo: desenvolvemos o modelo com anos anteriores e reservamos 2025 para a avaliação final, sem usar seus resultados para escolher o modelo ou o limite de alerta." />
        <ol className={styles.steps}>
          <li><strong>Desenvolvimento — 2018 a 2024</strong><p>Treinamos com o passado e validamos em anos posteriores. Comparamos o histórico epidemiológico com versões que também incluíam clima.</p></li>
          <li><strong>Comparação com uma referência simples</strong><p>A persistência supõe que o estado de risco da semana de referência continuará no futuro. Comparamos o modelo com essa regra para avaliar o que ele acrescenta.</p></li>
          <li><strong>Teste final — 2025</strong><p>Confrontamos a indicação do modelo com o estado observado na semana futura. Também avaliamos a antecipação separadamente, apenas nas situações ainda sem risco elevado na semana de referência.</p></li>
        </ol>
        <p className={styles.readingNote}>O modelo final utiliza o histórico epidemiológico. Acrescentar as variáveis climáticas testadas não trouxe melhora consistente — isso não significa que o clima não tenha relação com dengue.</p>
        <details className={styles.details}>
          <summary>Desenho temporal e configuração do modelo final</summary>
          <div className={styles.detailsContent}>
            <p>As validações usaram treino expansivo: 2018–2020 → 2021; 2018–2021 → 2022; 2018–2022 → 2023; 2018–2023 → 2024. Não houve divisão aleatória entre treino e teste.</p>
            <p>A estratégia final é HistGradientBoostingClassifier com o conjunto epidemiológico do Modelo A, sem variáveis meteorológicas e sem calibração adicional das probabilidades. Os limites de alerta foram definidos no desenvolvimento, antes do teste final.</p>
            <p>Os prazos H1, H2, H3 e H4 correspondem a uma, duas, três e quatro semanas depois, não a níveis de gravidade. Situações sem estado futuro válido no respectivo período são excluídas somente da avaliação daquele prazo.</p>
          </div>
        </details>
        <p className={styles.readingNote}>Consulte os números e a interpretação dos indicadores em <Link href="/predicao">Resultados do modelo</Link>, os dados históricos em <Link href="/historico">Histórico</Link> e a distribuição dos alertas em <Link href="/mapa">Mapa</Link>.</p>
      </section>

      <aside className={styles.interpretation} aria-labelledby="interpretation-title">
        <span>Limites da interpretação</span>
        <h2 id="interpretation-title">O que os resultados não permitem concluir?</h2>
        <ul>
          <li><strong>Não são alertas atuais.</strong> Usamos dados históricos consolidados e avaliação retrospectiva, não uma operação semanal em tempo real.</li>
          <li><strong>O teste final cobre um único ano.</strong> O desempenho em 2025 não garante o mesmo resultado em outros anos.</li>
          <li><strong>O desempenho não é igual em todos os lugares.</strong> Uma métrica nacional não garante a mesma qualidade para cada município.</li>
          <li><strong>Dados ausentes não são ausência de dengue.</strong> Isso vale para semanas preenchidas com zero e lacunas na integração climática.</li>
          <li><strong>Associação não demonstra causalidade.</strong> Os resultados não provam, por si só, que uma condição meteorológica causou um aumento de casos.</li>
        </ul>
        <p>As contagens técnicas abaixo descrevem preparação e cobertura, não alertas, chances individuais de dengue ou novas análises científicas.</p>
      </aside>

      <section className={styles.section} aria-labelledby="quality-detail-title">
        <SectionHeading id="quality-detail-title" eyebrow="Rastreabilidade"
          title="Quer conferir a preparação em detalhe?"
          description="Abra apenas o tema que deseja aprofundar. Os valores mantêm as fontes auditadas, incluindo lacunas, exceções e verificações sem contagem própria." />
        <details className={styles.details}>
          <summary id="quality-overview-title">Indicadores completos da base preparada</summary>
          <div className={styles.detailsContent}>
            <div className="metric-grid">
              <MetricCard label="Registros SINAN brutos" value={formatInteger(overviewData.registros_sinan_brutos)} description="Base inicial antes dos filtros documentados." />
              <MetricCard label="Mantidos após filtros" value={formatInteger(overviewData.registros_sinan_mantidos_apos_filtros)} description="Registros mantidos ao final do funil documentado." />
              <MetricCard label="Casos finais preservados" value={formatInteger(overviewData.casos_finais_preservados)} description="Soma de casos após normalização territorial." />
              <MetricCard label="Unidades territoriais" value={formatInteger(overviewData.unidades_territoriais)} description="Cobertura territorial final da grade analítica." />
              <MetricCard label="Município-semanas" value={formatInteger(overviewData.municipio_semanas)} description="Combinações presentes na grade completa." />
              <MetricCard label="Linhas inseridas por zero-fill" value={formatInteger(overviewData.linhas_zero_fill)} description="Combinações ausentes que foram completadas com zero." />
              <MetricCard label="Unidades com clima" value={formatInteger(overviewData.unidades_com_cobertura_climatica)} description="Unidades com mapeamento climático disponível." />
              <MetricCard label="Município-semanas sem clima" value={formatInteger(overviewData.municipio_semanas_sem_clima)} description="Ausências de integração climática, não de dengue." />
            </div>
            <Sources sources={overview.source} />
          </div>
        </details>

        <details className={styles.details}>
          <summary id="sinan-title">Filtros e verificações dos registros de dengue</summary>
          <div className={styles.detailsContent}>
            <div className={styles.funnel}>
              <div className={styles.funnelEndpoint}>
                <span>Base inicial</span>
                <strong>{formatInteger(sinanData.registros_brutos)}</strong>
              </div>
              <ol aria-labelledby="sinan-title">
                {sinanData.etapas.map((step) => (
                  <li key={step.id}>
                    <div>
                      <strong>{step.label}</strong>
                      {step.field ? <code>{step.field}</code> : null}
                    </div>
                    {step.records_removed === null ? (
                      <span className={styles.validationBadge}>Verificação lógica · sem contagem própria</span>
                    ) : (
                      <span>{formatInteger(step.records_removed)} removidos</span>
                    )}
                    {step.note ? <p>{step.note}</p> : null}
                  </li>
                ))}
              </ol>
              <div className={styles.funnelEndpoint}>
                <span>Registros mantidos após filtros</span>
                <strong>{formatInteger(sinanData.registros_mantidos_apos_filtros)}</strong>
                <small>{formatInteger(sinanData.total_remocoes_documentadas)} remoções documentadas</small>
              </div>
            </div>
            <Sources sources={sinan.source} />
          </div>
        </details>

        <details className={styles.details}>
          <summary id="territory-title">Associação territorial e exceções</summary>
          <div className={styles.detailsContent}>
            <p>A associação usa {territoryData.referencia}; o Distrito Federal e os códigos residuais não municipais são tratados separadamente.</p>
            <div className={styles.factGrid}>
              <article><span>Códigos SINAN iniciais</span><strong>{formatInteger(territoryData.codigos_sinan_iniciais)}</strong></article>
              <article><span>Associados diretamente</span><strong>{formatInteger(territoryData.codigos_associados_diretamente)}</strong></article>
              <article><span>Não associados inicialmente</span><strong>{formatInteger(territoryData.codigos_nao_associados_inicialmente)}</strong><small>{formatInteger(territoryData.casos_nao_associados_inicialmente)} casos</small></article>
              <article><span>Unidades territoriais finais</span><strong>{formatInteger(territoryData.resultado_final.unidades_territoriais)}</strong></article>
            </div>
            <div className={styles.calloutGrid}>
              <article>
                <span>Distrito Federal</span>
                <h3>Consolidação preservada</h3>
                <p>{formatInteger(territoryData.distrito_federal.codigos_subdivisoes)} códigos de subdivisões foram consolidados em {territoryData.distrito_federal.nome_destino} ({territoryData.distrito_federal.codigo_ibge_7_destino}), preservando {formatInteger(territoryData.distrito_federal.casos_preservados)} casos.</p>
              </article>
              <article>
                <span>Resíduos e cobertura original</span>
                <h3>Exceções explícitas</h3>
                <p>{formatInteger(territoryData.residuais_nao_municipais.quantidade_codigos)} códigos residuais não municipais correspondem a {formatInteger(territoryData.residuais_nao_municipais.casos_excluidos)} casos excluídos. A grade final contém {formatInteger(territoryData.resultado_final.unidades_sem_registro_original)} unidades sem registro epidemiológico original.</p>
              </article>
            </div>
            <Sources sources={territory.source} />
          </div>
        </details>

        <details className={styles.details}>
          <summary id="zero-fill-title">Contagens do preenchimento com zero</summary>
          <div className={styles.detailsContent}>
            <div className={styles.zeroFlow} aria-labelledby="zero-fill-title">
              <article><span>Linhas originalmente observadas</span><strong>{formatInteger(sinanData.zero_fill.linhas_observadas)}</strong></article>
              <span aria-hidden="true">→</span>
              <article><span>Linhas inseridas com zero</span><strong>{formatInteger(sinanData.zero_fill.linhas_preenchidas_com_zero)}</strong></article>
              <span aria-hidden="true">→</span>
              <article><span>Grade final</span><strong>{formatInteger(sinanData.zero_fill.linhas_finais)}</strong></article>
            </div>
            <div className={styles.preservationNote}>
              <strong>{formatInteger(sinanData.zero_fill.casos_antes)} casos antes e {formatInteger(sinanData.zero_fill.casos_depois)} depois</strong>
              <p>A soma de casos foi preservada; os zeros identificam combinações completadas na grade, não notificações originalmente registradas com valor zero.</p>
            </div>
          </div>
        </details>

        <details className={styles.details}>
          <summary id="population-title">População por ano e referência utilizada</summary>
          <div className={styles.detailsContent}>
            <div className={styles.factGrid}>
              <article><span>Linhas sem população</span><strong>{formatInteger(populationData.linhas_sem_populacao)}</strong></article>
              <article><span>População não positiva</span><strong>{formatInteger(populationData.linhas_populacao_nao_positiva)}</strong></article>
              <article><span>Ano epidemiológico especial</span><strong>{populationData.referencia_2023.ano_epidemiologico}</strong></article>
              <article><span>Referência populacional usada</span><strong>{populationData.referencia_2023.ano_referencia_populacao}</strong><small>{populationData.referencia_2023.usa_referencia_censo_2022 ? "Censo 2022" : "Outra referência"}</small></article>
            </div>
            <p className={styles.readingNote}>Em telas pequenas, deslize a tabela na horizontal. Com o container em foco, também é possível usar as setas do teclado.</p>
            <div
              className={styles.tableWrapper}
              role="region"
              aria-label="Referência populacional por ano epidemiológico"
              tabIndex={0}
            >
              <table>
                <caption>Referência populacional por ano epidemiológico</caption>
                <thead><tr><th scope="col">Ano epidemiológico</th><th scope="col">Ano de referência</th><th scope="col">Tipo</th><th scope="col">Unidades</th><th scope="col">Ausências</th></tr></thead>
                <tbody>
                  {populationData.por_ano.map((year) => (
                    <tr key={year.ano_epidemiologico}>
                      <th scope="row">{year.ano_epidemiologico}</th>
                      <td>{year.anos_referencia_populacao.join(", ")}</td>
                      <td>{year.tipos_populacao.map(populationTypeLabel).join(", ")}</td>
                      <td>{formatInteger(year.unidades_territoriais)}</td>
                      <td>{formatInteger(year.linhas_sem_populacao)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Sources sources={population.source} />
          </div>
        </details>

        <details className={styles.details}>
          <summary id="climate-title">Cobertura climática e critérios de associação</summary>
          <div className={styles.detailsContent}>
            <div className={styles.factGrid}>
              <article><span>Unidades mapeadas</span><strong>{formatInteger(climateData.unidades_com_mapeamento_climatico)}</strong></article>
              <article><span>Município-semanas com clima</span><strong>{formatInteger(climateData.municipio_semanas_com_clima)}</strong></article>
              <article><span>Município-semanas sem clima</span><strong>{formatInteger(climateData.municipio_semanas_sem_clima)}</strong></article>
              <article><span>Linhas climáticas da fonte</span><strong>{formatInteger(climateData.linhas_climaticas_fonte)}</strong></article>
              <article><span>Pontos de grade distintos</span><strong>{formatInteger(climateData.pontos_grade_distintos)}</strong></article>
              <article><span>Combinações grade × timezone</span><strong>{formatInteger(climateData.combinacoes_grade_timezone)}</strong></article>
            </div>
            <div className={styles.calloutGrid}>
              <article>
                <span>Métodos de seleção da grade</span>
                <h3>Associação espacial documentada</h3>
                <ul>
                  <li>Grade válida mais próxima: {formatInteger(climateData.metodos_selecao_grid.grid_mais_proximo_valido)}</li>
                  <li>Fallback válido que intersecta o município: {formatInteger(climateData.metodos_selecao_grid.fallback_valido_intersecta_municipio)}</li>
                  <li>Fallback insular externo até 15 km: {formatInteger(climateData.metodos_selecao_grid.fallback_insular_externo_ate_15km)}</li>
                </ul>
              </article>
              <article>
                <span>Exceção territorial</span>
                <h3>Código sem cobertura climática</h3>
                <p>{climateData.codigos_excluidos.join(", ")}</p>
                <small>{climateData.observacao}</small>
              </article>
            </div>
            <Sources sources={climate.source} />
          </div>
        </details>
      </section>
    </div>
  );
}
