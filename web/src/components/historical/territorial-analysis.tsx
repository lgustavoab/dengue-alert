import {
  buildBandPolygon,
  pointsToPath,
  scaleSeries,
} from "@/lib/historical-chart-utils";

import {
  filterRegionalSeasonality,
  filterStatesByRegion,
  findRegionSummary,
  findStateSummary,
  getRegionalSeasonalityPeak,
  sortRegionsByAverageIncidence,
  sortStatesByAverageIncidence,
} from "@/lib/historical-territorial-utils";

import {
  formatDecimal,
  formatInteger,
  formatPercent,
} from "@/lib/serving/formatters";

import type {
  HistoricalSeasonalityRegionalItem,
  HistoricalSpatialRegionItem,
  HistoricalSpatialStateItem,
} from "@/lib/serving/types";

import {
  MetricCard,
} from "@/components/ui/metric-card";

import styles from "./territorial-analysis.module.css";
import { HistoricalChartAxes, HistoricalChartFrame, historicalChartViewBox } from "./historical-chart-axes";

type TerritorialAnalysisProps = {
  regions:
    HistoricalSpatialRegionItem[];

  states:
    HistoricalSpatialStateItem[];

  regionalSeasonality:
    HistoricalSeasonalityRegionalItem[];

  selectedRegion:
    string;

  selectedUf:
    string;
};

const CHART_WIDTH =
  960;

const CHART_HEIGHT =
  300;

const PADDING = {
  top: 24,
  right: 26,
  bottom: 48,
  left: 54,
};

function RegionalSeasonality({
  data,
  region,
}: {
  data:
    HistoricalSeasonalityRegionalItem[];

  region:
    string;
}) {
  if (
    data.length === 0
  ) {
    return null;
  }

  const medianValues =
    data.map(
      (item) =>
        item
          .incidencia_mediana_100mil,
    );

  const q25Values =
    data.map(
      (item) =>
        item
          .incidencia_q25_100mil,
    );

  const q75Values =
    data.map(
      (item) =>
        item
          .incidencia_q75_100mil,
    );

  const maxValue =
    Math.max(
      ...q75Values,
      ...medianValues,
      1,
    );

  const medianPoints =
    scaleSeries(
      medianValues,
      CHART_WIDTH,
      CHART_HEIGHT,
      PADDING,
      maxValue,
    );

  const linePath =
    pointsToPath(
      medianPoints,
    );

  const bandPolygon =
    buildBandPolygon(
      q25Values,
      q75Values,
      CHART_WIDTH,
      CHART_HEIGHT,
      PADDING,
    );

  const peak =
    getRegionalSeasonalityPeak(
      data,
    );

  const peakIndex =
    peak
      ? data.indexOf(
          peak,
        )
      : -1;

  const peakPoint =
    peakIndex >= 0
      ? medianPoints[
          peakIndex
        ]
      : null;

  const plotHeight =
    CHART_HEIGHT
    - PADDING.top
    - PADDING.bottom;

  const labelWeeks = [
    1,
    13,
    26,
    39,
    53,
  ];

  return (
    <div
      className={
        styles.seasonality
      }
    >
      <div
        className={
          styles.seasonalityHeader
        }
      >
        <div>
          <h3>
            Em que épocas a incidência aumentou? · {region}
          </h3>
        </div>

        <p>
          Região {region}, 2016–2025. A linha mostra a mediana (valor central) das incidências da mesma semana em diferentes anos, em casos por 100 mil habitantes. A faixa entre Q25 e Q75 reúne a metade central dos valores; não é um intervalo de previsão.
        </p>
      </div>

      <HistoricalChartFrame label={`Sazonalidade de ${region}: semana e incidência por 100 mil habitantes`}>
        <svg
          className={
            styles.svg
          }
          viewBox={historicalChartViewBox(CHART_WIDTH, CHART_HEIGHT)}
          role="img"
          aria-label={`Sazonalidade histórica da região ${region}`}
        >
          <HistoricalChartAxes width={CHART_WIDTH} height={CHART_HEIGHT} padding={PADDING} maximum={maxValue} xLabel="Semana Epidemiológica (SE) — diferentes anos" yLabel="Incidência semanal (casos por 100 mil habitantes)" />
          {[
            0,
            0.25,
            0.5,
            0.75,
            1,
          ].map(
            (fraction) => {
              const y =
                PADDING.top
                + fraction
                * plotHeight;

              return (
                <line
                  key={
                    fraction
                  }
                  className={
                    styles.gridLine
                  }
                  x1={
                    PADDING.left
                  }
                  x2={
                    CHART_WIDTH
                    - PADDING.right
                  }
                  y1={
                    y
                  }
                  y2={
                    y
                  }
                />
              );
            },
          )}

          <polygon
            className={
              styles.band
            }
            points={
              bandPolygon
            }
          />

          <path
            className={
              styles.line
            }
            d={
              linePath
            }
          />

          {medianPoints.map(
            (
              point,
              index,
            ) => {
              const item =
                data[
                  index
                ];

              return (
                <circle
                  key={
                    item
                      .semana_epidemiologica
                  }
                  className={
                    styles.point
                  }
                  cx={
                    point.x
                  }
                  cy={
                    point.y
                  }
                  r="2.8"
                >
                  <title>
                    {`Semana Epidemiológica ${item.semana_epidemiologica}: mediana ${formatDecimal(
                      item.incidencia_mediana_100mil,
                    )}; Q25 ${formatDecimal(
                      item.incidencia_q25_100mil,
                    )}; Q75 ${formatDecimal(
                      item.incidencia_q75_100mil,
                    )}`}
                  </title>
                </circle>
              );
            },
          )}

          {peakPoint ? (
            <circle
              className={
                styles.peakPoint
              }
              cx={
                peakPoint.x
              }
              cy={
                peakPoint.y
              }
              r="6"
            >
              <title>
                {peak
                  ? `Pico da incidência mediana: Semana Epidemiológica ${peak.semana_epidemiologica}`
                  : ""}
              </title>
            </circle>
          ) : null}

          {labelWeeks.map(
            (week) => {
              const index =
                data.findIndex(
                  (item) =>
                    item
                      .semana_epidemiologica
                    === week,
                );

              if (
                index < 0
              ) {
                return null;
              }

              return (
                <text
                  key={
                    week
                  }
                  className={
                    styles.axisText
                  }
                  x={
                    medianPoints[
                      index
                    ].x
                  }
                  y={
                    CHART_HEIGHT
                    - 14
                  }
                  textAnchor="middle"
                >
                  SE {week}
                </text>
              );
            },
          )}
        </svg>
      </HistoricalChartFrame>

      <div
        className={
          styles.legend
        }
      >
        <span
          className={
            styles.legendItem
          }
        >
          <span
            className={
              styles.legendLine
            }
          />

          Incidência mediana
        </span>

        <span
          className={
            styles.legendItem
          }
        >
          <span
            className={
              styles.legendBand
            }
          />

          Metade central dos valores (Q25–Q75)
        </span>
      </div>

      {peak ? (
        <p
          className={
            styles.note
          }
        >
          O maior valor da incidência mediana histórica da região ocorre na Semana Epidemiológica {peak.semana_epidemiologica}, com {formatDecimal(
            peak
              .incidencia_mediana_100mil,
          )} casos por 100 mil habitantes.
        </p>
      ) : null}
    </div>
  );
}

export function TerritorialAnalysis({
  regions,
  states,
  regionalSeasonality,
  selectedRegion,
  selectedUf,
}: TerritorialAnalysisProps) {
  const regionSummary =
    findRegionSummary(
      regions,
      selectedRegion,
    );

  const stateSummary =
    findStateSummary(
      states,
      selectedUf,
    );

  const effectiveRegion =
    stateSummary?.regiao
    ?? selectedRegion;

  const statesInRegion =
    sortStatesByAverageIncidence(
      filterStatesByRegion(
        states,
        effectiveRegion,
      ),
    );

  const seasonality =
    filterRegionalSeasonality(
      regionalSeasonality,
      selectedRegion,
    );

  if (
    stateSummary
  ) {
    const maxIncidence =
      Math.max(
        ...statesInRegion.map(
          (item) =>
            item
              .incidencia_media_anual_100mil,
        ),
        1,
      );

    return (
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
          <div
            className={
              styles.headingContent
            }
          >
            <span
              className={
                styles.eyebrow
              }
            >
              Análise territorial · UF
            </span>

            <h2>
              Como os casos variaram entre lugares? · {stateSummary.nome_uf}
            </h2>
          </div>

          <p>
            Resumo do estado no período completo de 2016–2025. Incidência expressa casos por 100 mil habitantes e permite comparar volumes em relação à população. Não é uma medida do risco individual.
          </p>
        </div>

        <div
          className="metric-grid"
        >
          <MetricCard
            label="Casos no período"
            value={
              formatInteger(
                stateSummary
                  .casos_periodo,
              )
            }
            description="Total consolidado no período histórico."
          />

          <MetricCard
            label="Incidência média anual"
            value={
              formatDecimal(
                stateSummary
                  .incidencia_media_anual_100mil,
              )
            }
            description="Casos por 100 mil habitantes."
          />

          <MetricCard
            label="Ano de maior incidência"
            value={
              String(
                stateSummary
                  .ano_maior_incidencia,
              )
            }
            description={`${formatDecimal(
              stateSummary
                .incidencia_ano_pico_100mil,
            )} por 100 mil habitantes.`}
          />

          <MetricCard
            label="Participação nacional"
            value={
              formatPercent(
                stateSummary
                  .participacao_casos_periodo,
              )
            }
            description="Participação nos casos do período nacional."
          />
        </div>

        <div
          className={
            styles.comparison
          }
        >
          <div
            className={
              styles.comparisonHeader
            }
          >
            <h3>
              Comparação dentro da região {stateSummary.regiao}
            </h3>

            <p>
              Estados ordenados pela incidência média anual de 2016–2025, em casos por 100 mil habitantes.
            </p>
          </div>

          <div
            className={
              styles.rows
            }
          >
            {statesInRegion.map(
              (item) => {
                const proportion =
                  item
                    .incidencia_media_anual_100mil
                  / maxIncidence;

                const selected =
                  item
                    .codigo_uf_ibge
                  === selectedUf;

                return (
                  <div
                    key={
                      item
                        .codigo_uf_ibge
                    }
                    className={`${styles.row} ${
                      selected
                        ? styles.selectedRow
                        : ""
                    }`}
                  >
                    <span
                      className={
                        styles.name
                      }
                    >
                      {item.nome_uf}
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
                            proportion
                            * 100,
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
                      {formatDecimal(
                        item
                          .incidencia_media_anual_100mil,
                      )}
                    </strong>
                  </div>
                );
              },
            )}
          </div>
        </div>

        <p
          className={
            styles.note
          }
        >
          Os dados disponíveis nesta visualização incluem o resumo histórico consolidado por UF, mas não uma série semanal ou sazonalidade específica por estado. Por isso, esses gráficos não são apresentados.
        </p>
      </section>
    );
  }

  if (
    regionSummary
  ) {
    const maxIncidence =
      Math.max(
        ...statesInRegion.map(
          (item) =>
            item
              .incidencia_media_anual_100mil,
        ),
        1,
      );

    return (
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
          <div
            className={
              styles.headingContent
            }
          >
            <span
              className={
                styles.eyebrow
              }
            >
              Análise territorial · Região
            </span>

            <h2>
              Como os casos variaram entre lugares? · {regionSummary.regiao}
            </h2>
          </div>

          <p>
            Região {regionSummary.regiao}, 2016–2025. Os indicadores e a comparação entre estados resumem todo o período; a sazonalidade, abaixo, reúne diferentes anos. Não há uma curva semanal de casos da região nesta visualização.
          </p>
        </div>

        <div
          className="metric-grid"
        >
          <MetricCard
            label="Casos no período"
            value={
              formatInteger(
                regionSummary
                  .casos_periodo,
              )
            }
            description="Total consolidado da região."
          />

          <MetricCard
            label="Incidência média anual"
            value={
              formatDecimal(
                regionSummary
                  .incidencia_media_anual_100mil,
              )
            }
            description="Casos por 100 mil habitantes."
          />

          <MetricCard
            label="Ano de maior incidência"
            value={
              String(
                regionSummary
                  .ano_maior_incidencia,
              )
            }
            description={`${formatDecimal(
              regionSummary
                .incidencia_ano_pico_100mil,
            )} por 100 mil habitantes.`}
          />

          <MetricCard
            label="Participação nacional"
            value={
              formatPercent(
                regionSummary
                  .participacao_casos_periodo,
              )
            }
            description="Participação nos casos do período nacional."
          />
        </div>

        <div
          className={
            styles.comparison
          }
        >
          <div
            className={
              styles.comparisonHeader
            }
          >
            <h3>
              UFs da região
            </h3>

            <p>
              Comparação pela incidência média anual de 2016–2025, em casos por 100 mil habitantes.
            </p>
          </div>

          <div
            className={
              styles.rows
            }
          >
            {statesInRegion.map(
              (item) => {
                const proportion =
                  item
                    .incidencia_media_anual_100mil
                  / maxIncidence;

                return (
                  <div
                    key={
                      item
                        .codigo_uf_ibge
                    }
                    className={
                      styles.row
                    }
                  >
                    <span
                      className={
                        styles.name
                      }
                    >
                      {item.nome_uf}
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
                            proportion
                            * 100,
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
                      {formatDecimal(
                        item
                          .incidencia_media_anual_100mil,
                      )}
                    </strong>
                  </div>
                );
              },
            )}
          </div>
        </div>

        <RegionalSeasonality
          data={
            seasonality
          }
          region={
            regionSummary.regiao
          }
        />
      </section>
    );
  }

  const rankedRegions =
    sortRegionsByAverageIncidence(
      regions,
    );

  const maxRegionalIncidence =
    Math.max(
      ...rankedRegions.map(
        (item) =>
          item
            .incidencia_media_anual_100mil,
      ),
      1,
    );

  return (
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
        <div
          className={
            styles.headingContent
          }
        >
          <span
            className={
              styles.eyebrow
            }
          >
            Comparação territorial
          </span>

          <h2>
            Como os casos variaram entre lugares?
          </h2>
        </div>

        <p>
          As cinco regiões, 2016–2025. Comparamos a incidência média anual: casos por 100 mil habitantes, levando em conta a população. Esta comparação usa o período completo, mesmo quando um ano é selecionado, e não mostra o risco individual.
        </p>
      </div>

      <div
        className={
          styles.comparison
        }
      >
        <div
          className={
            styles.rows
          }
        >
          {rankedRegions.map(
            (item) => {
              const proportion =
                item
                  .incidencia_media_anual_100mil
                / maxRegionalIncidence;

              return (
                <div
                  key={
                    item.regiao
                  }
                  className={
                    styles.row
                  }
                >
                  <span
                    className={
                      styles.name
                    }
                  >
                    {item.regiao}
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
                          proportion
                          * 100,
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
                    {formatDecimal(
                      item
                        .incidencia_media_anual_100mil,
                    )}
                  </strong>
                </div>
              );
            },
          )}
        </div>
      </div>

      <p
        className={
          styles.note
        }
      >
        Os valores representam incidência média anual no período histórico e não devem ser interpretados como a situação atual ou como previsão futura.
      </p>
    </section>
  );
}
