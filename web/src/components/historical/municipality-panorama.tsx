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
import reading from "./historical-reading.module.css";
import dashboard from "./historical-dashboard.module.css";
import { HistoricalDetails } from "./historical-details";

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
        className={reading.keyMetrics}
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
              Como os casos variaram? · {territory.nomeMunicipio}
              {" — "}
              {territory.nomeUf}
            </h2>
          </div>

          <p>
            {selectedYear
            === null
              ? "Cada barra mostra o total de casos prováveis de um ano. Escolha um ano no filtro para consultar suas semanas. Incidência, nos indicadores, expressa casos por 100 mil habitantes."
              : `Cada barra mostra os casos prováveis de uma semana de ${selectedYear}. SE significa Semana Epidemiológica. A incidência anual, nos indicadores, expressa casos por 100 mil habitantes.`}
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
            role="region"
            aria-label={`Gráfico semanal de ${territory.nomeMunicipio}`}
            tabIndex={0}
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
              Eixo X: Semana Epidemiológica (SE) de {selectedYear}. Eixo Y: casos prováveis por semana, de 0 a {formatInteger(maxWeeklyCases)}.
              {" "}Em telas pequenas, deslize este gráfico na horizontal. Os valores de cada semana também estão na tabela abaixo, acessível por toque e teclado.
            </p>
          </div>
        )}

        <HistoricalDetails title={selectedYear === null ? "Consultar valores anuais e cobertura" : "Consultar valores semanais e cobertura"}>
          <p>A série municipal completa contém {formatInteger(series.count)} semanas. Esse total descreve a cobertura de todos os anos disponíveis, não somente do ano selecionado.</p>
          {selectedSummary ? <p>População utilizada em {selectedSummary.year}: {formatInteger(selectedSummary.population)} habitantes.</p> : null}
          <p>Semanas preenchidas com zero no tratamento dos dados não comprovam ausência de transmissão nem um registro explícito de zero na fonte.</p>
          <div className={dashboard.tableWrapper} role="region" aria-label="Valores da série municipal" tabIndex={0}>
            <table className={dashboard.table}>
              <thead>
                <tr>
                  <th>{selectedYear === null ? "Ano" : "Semana Epidemiológica"}</th>
                  <th>Casos prováveis</th>
                  {selectedYear === null ? <><th>Incidência anual (por 100 mil habitantes)</th><th>População utilizada</th><th>Semanas preenchidas com zero</th></> : <th>Preenchida com zero</th>}
                </tr>
              </thead>
              <tbody>
                {selectedYear === null ? annual.map((item) => (
                  <tr key={item.year}><td>{item.year}</td><td>{formatInteger(item.cases)}</td><td>{formatDecimal(item.incidence)}</td><td>{formatInteger(item.population)}</td><td>{formatInteger(item.zeroFilledWeeks)}</td></tr>
                )) : weeklyIndices.map((index) => (
                  <tr key={index}><td>SE {series.data.semana_epidemiologica[index]}</td><td>{formatInteger(series.data.casos_provaveis[index])}</td><td>{series.data.zero_preenchido[index] ? "Sim" : "Não"}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </HistoricalDetails>
      </section>
    </>
  );
}
