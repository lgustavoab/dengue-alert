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
      <strong>Proveniência do contrato</strong>
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
      <section className={styles.section} aria-labelledby="quality-overview-title">
        <SectionHeading
          id="quality-overview-title"
          eyebrow={`Visão geral · ${formatPeriod(overview.period)}`}
          title="Rastreabilidade da base analítica"
          description="Indicadores estruturais consolidados antes das análises históricas e preditivas. Todos os valores vêm do contrato de visão geral auditado."
        />
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
      </section>

      <section className={styles.section} aria-labelledby="sinan-title">
        <SectionHeading
          id="sinan-title"
          eyebrow="Preparação epidemiológica"
          title="Funil documentado do SINAN"
          description="O fluxo distingue filtros com remoção quantificada de verificações metodológicas sem contagem própria."
        />
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
      </section>

      <section className={styles.section} aria-labelledby="territory-title">
        <SectionHeading
          id="territory-title"
          eyebrow="Normalização territorial"
          title="Da codificação SINAN à referência territorial"
          description={`A associação usa ${territoryData.referencia} e documenta separadamente o Distrito Federal e os resíduos não municipais.`}
        />
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
      </section>

      <section className={styles.section} aria-labelledby="zero-fill-title">
        <SectionHeading
          id="zero-fill-title"
          eyebrow="Completude da grade"
          title="Zero-fill sem alteração da soma de casos"
          description="O preenchimento completa combinações município-semana ausentes na grade analítica. Ele não transforma ausência original em registro explicitamente observado no SINAN."
        />
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
      </section>

      <section className={styles.section} aria-labelledby="population-title">
        <SectionHeading
          id="population-title"
          eyebrow="Cobertura populacional"
          title="Referências anuais e continuidade metodológica"
          description={populationData.observacao_metodologica}
        />
        <div className={styles.factGrid}>
          <article><span>Linhas sem população</span><strong>{formatInteger(populationData.linhas_sem_populacao)}</strong></article>
          <article><span>População não positiva</span><strong>{formatInteger(populationData.linhas_populacao_nao_positiva)}</strong></article>
          <article><span>Ano epidemiológico especial</span><strong>{populationData.referencia_2023.ano_epidemiologico}</strong></article>
          <article><span>Referência populacional usada</span><strong>{populationData.referencia_2023.ano_referencia_populacao}</strong><small>{populationData.referencia_2023.usa_referencia_censo_2022 ? "Censo 2022" : "Outra referência"}</small></article>
        </div>
        <div
          className={styles.tableWrapper}
          role="region"
          aria-label="Referência populacional por ano epidemiológico"
          tabIndex={0}
        >
          <table>
            <caption>Referência populacional por ano epidemiológico</caption>
            <thead><tr><th>Ano epidemiológico</th><th>Ano de referência</th><th>Tipo</th><th>Unidades</th><th>Ausências</th></tr></thead>
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
      </section>

      <section className={styles.section} aria-labelledby="climate-title">
        <SectionHeading
          id="climate-title"
          eyebrow="Cobertura climática"
          title="Disponibilidade e integração do ERA5-Land"
          description="A cobertura climática descreve disponibilidade e integração de dados. Ausência climática não significa ausência de dengue nem permite concluir falta de influência do clima."
        />
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
      </section>

      <aside className={styles.interpretation} aria-labelledby="interpretation-title">
        <span>Como interpretar</span>
        <h2 id="interpretation-title">Indicadores de preparação, não resultados epidemiológicos</h2>
        <p>Esta área descreve rastreabilidade, cobertura e exceções dos dados preparados. Os valores são derivados dos contratos auditados, não representam alertas, classificações preditivas ou uma nova análise científica.</p>
      </aside>
    </div>
  );
}
