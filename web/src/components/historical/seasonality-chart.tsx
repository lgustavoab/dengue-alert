import {
  buildBandPolygon,
  getSeasonalityPeak,
  pointsToPath,
  scaleSeries,
} from "@/lib/historical-chart-utils";

import {
  formatDecimal,
  formatInteger,
} from "@/lib/serving/formatters";

import type {
  HistoricalSeasonalityNationalItem,
} from "@/lib/serving/types";

import styles from "./historical-dashboard.module.css";
import { HistoricalDetails } from "./historical-details";
import { HistoricalChartAxes, HistoricalChartFrame, historicalChartViewBox } from "./historical-chart-axes";

type SeasonalityChartProps = {
  data:
    HistoricalSeasonalityNationalItem[];
};

const CHART_WIDTH =
  960;

const CHART_HEIGHT =
  320;

const PADDING = {
  top: 26,
  right: 26,
  bottom: 50,
  left: 58,
};

export function SeasonalityChart({
  data,
}: SeasonalityChartProps) {
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

  const medianPath =
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
    getSeasonalityPeak(
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

  const yearsAvailable =
    Math.max(
      ...data.map(
        (item) =>
          item
            .anos_disponiveis,
      ),
    );

  const labelWeeks = [
    1,
    13,
    26,
    39,
    53,
  ];

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
            Sazonalidade histórica
          </span>

          <h2>
            Em que épocas a incidência aumentou?
          </h2>
        </div>

        <p>
          Brasil, 2016–2025. A linha mostra a mediana: o valor central das incidências observadas na mesma semana em diferentes anos. A faixa mostra a metade central desses valores. A unidade é casos por 100 mil habitantes.
        </p>
      </div>

      <div
        className={
          styles.summaryGrid
        }
      >
        <div
          className={
            styles.summaryItem
          }
        >
          <span>
            Semanas epidemiológicas
          </span>

          <strong>
            {formatInteger(
              data.length,
            )}
          </strong>
        </div>

        <div
          className={
            styles.summaryItem
          }
        >
          <span>
            Anos considerados
          </span>

          <strong>
            {formatInteger(
              yearsAvailable,
            )}
          </strong>
        </div>

        <div
          className={
            styles.summaryItem
          }
        >
          <span>
            Pico sazonal da mediana
          </span>

          <strong>
            {peak
              ? `SE ${peak.semana_epidemiologica} · ${formatDecimal(
                  peak.incidencia_mediana_100mil,
                )} por 100 mil`
              : "—"}
          </strong>

          {peak ? (
            <span>
              Semana Epidemiológica {peak.semana_epidemiologica}
            </span>
          ) : null}
        </div>
      </div>

      <div
        className={
          styles.chartCard
        }
      >
        <HistoricalChartFrame label="Sazonalidade nacional: semana e incidência por 100 mil habitantes">
          <svg
            className={
              styles.svg
            }
            viewBox={historicalChartViewBox(CHART_WIDTH, CHART_HEIGHT)}
            role="img"
            aria-label="Sazonalidade nacional da incidência de dengue por semana epidemiológica"
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
                styles.lineSecondary
              }
              d={
                medianPath
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
                    ? `Maior incidência mediana: Semana Epidemiológica ${peak.semana_epidemiologica}`
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
                      - 16
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
      </div>

      <p
        className={
          styles.note
        }
      >
        SE = Semana Epidemiológica. A sazonalidade utiliza o conjunto histórico completo e, por isso, não muda quando um único ano é selecionado. Ela resume o comportamento recorrente entre os anos disponíveis.
      </p>
      <HistoricalDetails title="Como interpretar a mediana e a faixa?">
        <p>Mediana não é média: ela divide os valores ordenados ao meio. Q25 e Q75 são os percentis 25 e 75; entre eles fica a metade central das incidências observadas para aquela semana. A faixa não é um intervalo de previsão.</p>
        <p>Nem todas as semanas têm a mesma quantidade de anos disponíveis. A Semana Epidemiológica 53 ocorre apenas em alguns anos.</p>
      </HistoricalDetails>
    </section>
  );
}
