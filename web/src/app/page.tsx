import { AreaCard } from "@/components/ui/area-card";
import {
  formatHorizonRange,
  formatInteger,
  formatPeriod,
} from "@/lib/serving/formatters";
import {
  getPredictionModel,
  getPredictionOverview,
  getQualityOverview,
  getTemporalCoverage,
} from "@/lib/serving/server";

export default async function Home() {
  const [
    quality,
    temporalCoverage,
    prediction,
    predictionModel,
  ] = await Promise.all([
    getQualityOverview(),
    getTemporalCoverage(),
    getPredictionOverview(),
    getPredictionModel(),
  ]);

  const historicalPeriod = formatPeriod(
    temporalCoverage.data.periodo_historico,
  );

  const horizonRange = formatHorizonRange(
    predictionModel.horizontes.map(
      (item) => item.horizonte,
    ),
  );

  return (
    <>
      <section className="hero">
        <div className="hero__inner">
          <div className="hero__content">
            <span className="eyebrow">
              Dengue Alert
            </span>

            <h1>
              Dados históricos e avaliação preditiva para compreender o risco
              de dengue no Brasil.
            </h1>

            <p>
              Uma aplicação para explorar a evolução epidemiológica municipal,
              entender a qualidade das fontes utilizadas e analisar, em
              painéis e no mapa, resultados retrospectivos de previsão de risco
              elevado.
            </p>

            <div
              className="hero__badges"
              aria-label="Características do projeto"
            >
              <span>
                {historicalPeriod}
              </span>

              <span>
                {formatInteger(
                  quality.data
                    .unidades_territoriais,
                )}{" "}
                unidades territoriais
              </span>

              <span>
                {horizonRange} · horizontes de 1 a 4 semanas
              </span>
            </div>
          </div>

          <aside
            className="hero__panel"
            aria-label="Resumo do projeto"
          >
            <span className="hero__panel-label">
              Cobertura histórica
            </span>

            <strong>
              {formatInteger(
                quality.data
                  .casos_finais_preservados,
              )}
            </strong>

            <p>
              casos preservados após tratamento e normalização dos dados.
            </p>

            <div className="hero__panel-divider" />

            <dl className="hero__stats">
              <div>
                <dt>
                  Município-semanas
                </dt>

                <dd>
                  {formatInteger(
                    quality.data
                      .municipio_semanas,
                  )}
                </dd>
              </div>

              <div>
                <dt>
                  Predições retrospectivas
                </dt>

                <dd>
                  {formatInteger(
                    prediction.linhas,
                  )}
                </dd>
              </div>
            </dl>
          </aside>
        </div>
      </section>

      <section className="content-section">
        <div className="section-heading">
          <span className="eyebrow">
            Áreas da aplicação
          </span>

          <h2>
            Quatro perspectivas complementares
          </h2>

          <p>
            Explore dados observados, transparência das fontes, avaliação
            preditiva e distribuição geográfica em áreas dedicadas.
          </p>
        </div>

        <div className="area-grid">
          <AreaCard
            eyebrow="01"
            title="Histórico"
            description="Explore casos, incidência, sazonalidade, distribuição espacial e séries municipais."
            href="/historico"
            metric={historicalPeriod}
            metricLabel="período epidemiológico"
          />

          <AreaCard
            eyebrow="02"
            title="Dados & Qualidade"
            description="Acompanhe o tratamento das fontes, cobertura territorial, população e dados climáticos."
            href="/dados-qualidade"
            metric={formatInteger(
              quality.data
                .unidades_territoriais,
            )}
            metricLabel="unidades territoriais na base"
          />

          <AreaCard
            eyebrow="03"
            title="Predição"
            description="Analise a avaliação retrospectiva de 2025 para horizontes de uma a quatro semanas."
            href="/predicao"
            metric={horizonRange}
            metricLabel={`${formatInteger(
              prediction.municipios,
            )} municípios avaliados`}
          />

          <AreaCard
            eyebrow="04"
            title="Mapa preditivo"
            description="Visualize geograficamente as classificações oficiais por semana epidemiológica e horizonte no teste retrospectivo de 2025."
            href="/mapa"
            metric={formatInteger(
              prediction.municipios,
            )}
            metricLabel="municípios com avaliação preditiva"
          />
        </div>
      </section>

      <section className="method-section">
        <div className="method-section__content">
          <span className="eyebrow">
            Interpretação responsável
          </span>

          <h2>
            O modelo estima risco, não quantidade futura de casos.
          </h2>

          <p>
            A área preditiva apresenta probabilidades de ocorrência futura de
            estado epidemiológico de risco elevado. Os resultados disponíveis
            correspondem à avaliação retrospectiva de {prediction.ano} e não
            representam alertas operacionais atuais.
          </p>
        </div>
      </section>
    </>
  );
}
