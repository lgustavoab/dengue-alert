import {
  MetricCard,
} from "@/components/ui/metric-card";
import {
  formatDecimal,
  formatInteger,
} from "@/lib/serving/formatters";
import type {
  HistoricalMunicipalitySeriesContract,
  TerritoryFilterItem,
} from "@/lib/serving/types";

import styles from "./municipality-panorama.module.css";

type MunicipalityPanoramaProps = {
  territory: TerritoryFilterItem;
  series: HistoricalMunicipalitySeriesContract;
  selectedYear: number | null;
};

type AnnualSummary = {
  year: number;
  cases: number;
  population: number;
  incidence: number;
  peakCases: number;
  peakWeek: number;
  zeroFilledWeeks: number;
};

function aggregateAnnual(
  series: HistoricalMunicipalitySeriesContract,
): AnnualSummary[] {
  const summaries =
    new Map<
      number,
      AnnualSummary
    >();

  for (
    let index = 0;
    index < series.count;
    index += 1
  ) {
    const year =
      series.data
        .ano_epidemiologico[
          index
        ];

    const week =
      series.data
        .semana_epidemiologica[
          index
        ];

    const cases =
      series.data
        .casos_provaveis[
          index
        ];

    const population =
      series.data
        .populacao[
          index
        ];

    const zeroFilled =
      series.data
        .zero_preenchido[
          index
        ];

    const current =
      summaries.get(
        year,
      ) ?? {
        year,
        cases: 0,
        population,
        incidence: 0,
        peakCases: 0,
        peakWeek: week,
        zeroFilledWeeks: 0,
      };

    current.cases +=
      cases;

    current.population =
      population;

    if (
      cases
      > current.peakCases
    ) {
      current.peakCases =
        cases;

      current.peakWeek =
        week;
    }

    if (zeroFilled) {
      current.zeroFilledWeeks +=
        1;
    }

    summaries.set(
      year,
      current,
    );
  }

  return [
    ...summaries.values(),
  ]
    .map(
      (summary) => ({
        ...summary,
        incidence:
          summary.population > 0
            ? (
                summary.cases
                / summary.population
              )
              * 100000
            : 0,
      }),
    )
    .sort(
      (a, b) =>
        a.year - b.year,
    );
}

export function MunicipalityPanorama({
  territory,
  series,
  selectedYear,
}: MunicipalityPanoramaProps) {
  const annual =
    aggregateAnnual(
      series,
    );

  const selectedSummary =
    selectedYear === null
      ? null
      : annual.find(
          (item) =>
            item.year
            === selectedYear,
        ) ?? null;

  const totalCases =
    annual.reduce(
      (
        total,
        item,
      ) =>
        total + item.cases,
      0,
    );

  const peakAnnual =
    annual.reduce(
      (
        current,
        item,
      ) =>
        item.cases
        > current.cases
          ? item
          : current,
    );

  const latest =
    annual[
      annual.length - 1
    ];

  const weeklyIndices =
    selectedYear === null
      ? []
      : series.data
          .ano_epidemiologico
          .map(
            (year, index) => ({
              year,
              index,
            }),
          )
          .filter(
            (item) =>
              item.year
              === selectedYear,
          )
          .map(
            (item) =>
              item.index,
          );

  const maxWeeklyCases =
    weeklyIndices.length > 0
      ? Math.max(
          ...weeklyIndices.map(
            (index) =>
              series.data
                .casos_provaveis[
                  index
                ],
          ),
        )
      : 0;

  return (
    <>
      <section
        className="metric-grid"
        aria-label={`Indicadores de ${territory.nomeMunicipio}`}
      >
        {selectedSummary ? (
          <>
            <MetricCard
              label={`Casos · ${selectedSummary.year}`}
              value={formatInteger(
                selectedSummary.cases,
              )}
              description={`Total observado em ${territory.nomeMunicipio}.`}
            />

            <MetricCard
              label="Incidência anual"
              value={formatDecimal(
                selectedSummary.incidence,
              )}
              description="Casos por 100 mil habitantes."
            />

            <MetricCard
              label="Pico semanal"
              value={`SE ${selectedSummary.peakWeek}`}
              description={`${formatInteger(
                selectedSummary.peakCases,
              )} casos na semana de maior volume.`}
            />

            <MetricCard
              label="População utilizada"
              value={formatInteger(
                selectedSummary.population,
              )}
              description="População associada ao ano epidemiológico."
            />
          </>
        ) : (
          <>
            <MetricCard
              label="Casos no período"
              value={formatInteger(
                totalCases,
              )}
              description={`${annual.length} anos epidemiológicos disponíveis.`}
            />

            <MetricCard
              label="Maior volume anual"
              value={formatInteger(
                peakAnnual.cases,
              )}
              description={`${peakAnnual.year} · ${formatDecimal(
                peakAnnual.incidence,
              )} por 100 mil habitantes.`}
            />

            <MetricCard
              label={`Ano mais recente · ${latest.year}`}
              value={formatInteger(
                latest.cases,
              )}
              description={`Pico na SE ${latest.peakWeek}.`}
            />

            <MetricCard
              label="Semanas disponíveis"
              value={formatInteger(
                series.count,
              )}
              description="Cobertura epidemiológica da série municipal."
            />
          </>
        )}
      </section>

      <section
        className={
          styles.section
        }
      >
        <div
          className={
            styles.heading
          }
        >
          <div>
            <span className="eyebrow">
              Série municipal
            </span>

            <h2>
              {territory.nomeMunicipio}
              {" — "}
              {territory.nomeUf}
            </h2>
          </div>

          <p>
            {selectedYear
            === null
              ? "Comparação do total anual de casos prováveis ao longo da série disponível."
              : `Distribuição semanal dos casos prováveis no ano epidemiológico de ${selectedYear}.`}
          </p>
        </div>

        {!territory
          .riscoHistoricoDisponivel ? (
          <div
            className={
              styles.notice
            }
          >
            A série epidemiológica deste território está disponível,
            mas o histórico de risco elevado não está disponível para
            este município. Isso não impede a análise dos casos
            observados.
          </div>
        ) : null}

        {selectedYear === null ? (
          <div
            className={
              styles.annualRows
            }
          >
            {(() => {
              const maxCases =
                Math.max(
                  ...annual.map(
                    (item) =>
                      item.cases,
                  ),
                );

              return annual.map(
                (item) => (
                  <div
                    key={
                      item.year
                    }
                    className={
                      styles.annualRow
                    }
                  >
                    <span
                      className={
                        styles.year
                      }
                    >
                      {item.year}
                    </span>

                    <div
                      className={
                        styles.track
                      }
                    >
                      <div
                        className={
                          styles.bar
                        }
                        style={{
                          width: `${Math.max(
                            maxCases
                            > 0
                              ? (
                                  item.cases
                                  / maxCases
                                )
                                * 100
                              : 0,
                            1,
                          )}%`,
                        }}
                      />
                    </div>

                    <strong
                      className={
                        styles.value
                      }
                    >
                      {formatInteger(
                        item.cases,
                      )}
                    </strong>
                  </div>
                ),
              );
            })()}
          </div>
        ) : (
          <div
            className={
              styles.weeklyWrapper
            }
          >
            <div
              className={
                styles.weeklyChart
              }
              aria-label={`Casos semanais em ${selectedYear}`}
            >
              {weeklyIndices.map(
                (index) => {
                  const week =
                    series.data
                      .semana_epidemiologica[
                        index
                      ];

                  const cases =
                    series.data
                      .casos_provaveis[
                        index
                      ];

                  const height =
                    maxWeeklyCases
                    > 0
                      ? (
                          cases
                          / maxWeeklyCases
                        )
                        * 100
                      : 0;

                  return (
                    <div
                      key={`${selectedYear}-${week}`}
                      className={
                        styles.week
                      }
                      title={`SE ${week}: ${formatInteger(
                        cases,
                      )} casos`}
                    >
                      <div
                        className={
                          styles.weekBarArea
                        }
                      >
                        <div
                          className={
                            styles.weekBar
                          }
                          style={{
                            height: `${Math.max(
                              height,
                              cases > 0
                                ? 2
                                : 0,
                            )}%`,
                          }}
                        />
                      </div>

                      <span
                        className={
                          styles.weekLabel
                        }
                      >
                        {week}
                      </span>
                    </div>
                  );
                },
              )}
            </div>

            <p
              className={
                styles.caption
              }
            >
              SE = semana epidemiológica. Passe o cursor sobre uma
              barra para consultar o número de casos daquela semana.
            </p>
          </div>
        )}
      </section>
    </>
  );
}