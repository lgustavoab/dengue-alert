"use client";

import {
  useState,
} from "react";

import {
  pointsToPath,
  scaleSeries,
} from "@/lib/historical-chart-utils";

import {
  getPredictionHorizonPoints,
} from "@/lib/prediction-selection-utils";

import type {
  PredictionHorizonKey,
} from "@/lib/prediction-selection-utils";

import {
  PREDICTION_HORIZONS,
} from "@/lib/prediction-selection-utils";

import type {
  PredictionMunicipalitySeriesContract,
} from "@/lib/serving/types";

import styles from "./prediction-score-evolution.module.css";

type PredictionScoreEvolutionProps = {
  series:
    PredictionMunicipalitySeriesContract;

  selectedWeek:
    number;
};

const CHART_WIDTH =
  960;

const CHART_HEIGHT =
  330;

const PADDING = {
  top:
    30,

  right:
    28,

  bottom:
    52,

  left:
    62,
};

const HORIZON_LABELS: Record<
  PredictionHorizonKey,
  string
> = {
  h1:
    "H1 · 1 semana",

  h2:
    "H2 · 2 semanas",

  h3:
    "H3 · 3 semanas",

  h4:
    "H4 · 4 semanas",
};

const percentFormatter =
  new Intl.NumberFormat(
    "pt-BR",
    {
      style:
        "percent",

      minimumFractionDigits:
        1,

      maximumFractionDigits:
        1,
    },
  );

const thresholdFormatter =
  new Intl.NumberFormat(
    "pt-BR",
    {
      style:
        "percent",

      minimumFractionDigits:
        2,

      maximumFractionDigits:
        2,
    },
  );

export function PredictionScoreEvolution({
  series,
  selectedWeek,
}: PredictionScoreEvolutionProps) {
  const [
    horizon,
    setHorizon,
  ] =
    useState<PredictionHorizonKey>(
      "h1",
    );

  const points =
    getPredictionHorizonPoints(
      series,
      horizon,
    );

  const scores =
    points.map(
      (point) =>
        point.score,
    );

  const chartPoints =
    scaleSeries(
      scores,
      CHART_WIDTH,
      CHART_HEIGHT,
      PADDING,
      1,
    );

  const scorePath =
    pointsToPath(
      chartPoints,
    );

  const threshold =
    series
      .horizontes[
        horizon
      ]
      .threshold;

  const plotHeight =
    CHART_HEIGHT
    - PADDING.top
    - PADDING.bottom;

  const plotWidth =
    CHART_WIDTH
    - PADDING.left
    - PADDING.right;

  const thresholdY =
    PADDING.top
    + (
      1
      - threshold
    )
    * plotHeight;

  const selectedIndex =
    points.findIndex(
      (point) =>
        point.week
        === selectedWeek,
    );

  const selectedChartPoint =
    selectedIndex >= 0
      ? chartPoints[
          selectedIndex
        ]
      : null;

  const selectedPoint =
    selectedIndex >= 0
      ? points[
          selectedIndex
        ]
      : null;

  const xWeeks = [
    1,
    13,
    26,
    39,
    points[
      points.length
      - 1
    ]?.week,
  ]
    .filter(
      (
        week,
      ): week is number =>
        typeof week
        === "number",
    )
    .filter(
      (
        week,
        index,
        items,
      ) =>
        items.indexOf(
          week,
        )
        === index,
    );

  const xLabels =
    xWeeks
      .map(
        (week) => {
          const index =
            points.findIndex(
              (point) =>
                point.week
                === week,
            );

          if (
            index === -1
          ) {
            return null;
          }

          return {
            week,

            x:
              chartPoints[
                index
              ].x,
          };
        },
      )
      .filter(
        (
          item,
        ): item is {
          week: number;
          x: number;
        } =>
          item !== null,
      );

  const yLabels = [
    0,
    0.25,
    0.5,
    0.75,
    1,
  ];

  const alerts =
    points.filter(
      (point) =>
        point.prediction,
    ).length;

  return (
    <section
      className={
        styles.section
      }
      aria-labelledby="prediction-score-evolution-title"
    >
      <div
        className={
          styles.heading
        }
      >
        <div>
          <span
            className={
              styles.eyebrow
            }
          >
            Evolução retrospectiva
          </span>

          <h2
            id="prediction-score-evolution-title"
          >
            Probabilidade ao longo de 2025
          </h2>
        </div>

        <p>
          A linha mostra a probabilidade estimada de risco elevado em cada semana de referência. O limiar permanece fixo para o horizonte selecionado.
        </p>
      </div>

      <div
        className={
          styles.controls
        }
        aria-label="Horizonte da evolução das probabilidades"
      >
        {PREDICTION_HORIZONS.map(
          (item) => (
            <button
              key={
                item
              }
              type="button"
              className={`${styles.horizonButton} ${
                horizon
                === item
                  ? styles.horizonButtonActive
                  : ""
              }`}
              aria-pressed={
                horizon
                === item
              }
              onClick={() =>
                setHorizon(
                  item,
                )
              }
            >
              {
                HORIZON_LABELS[
                  item
                ]
              }
            </button>
          ),
        )}
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
            Horizonte
          </span>

          <strong>
            {
              HORIZON_LABELS[
                horizon
              ]
            }
          </strong>
        </div>

        <div
          className={
            styles.summaryItem
          }
        >
          <span>
            Semanas avaliadas
          </span>

          <strong>
            {
              points.length
            }
          </strong>
        </div>

        <div
          className={
            styles.summaryItem
          }
        >
          <span>
            Limiar de alerta
          </span>

          <strong>
            {
              thresholdFormatter.format(
                threshold,
              )
            }
          </strong>
        </div>

        <div
          className={
            styles.summaryItem
          }
        >
          <span>
            Semanas classificadas como alerta
          </span>

          <strong>
            {
              alerts
            }
          </strong>
        </div>
      </div>

      <div
        className={
          styles.chartCard
        }
      >
        <div
          className={
            styles.legend
          }
        >
          <span
            className={
              styles.scoreLegend
            }
          >
            Probabilidade estimada
          </span>

          <span
            className={
              styles.thresholdLegend
            }
          >
            Limiar de alerta
          </span>

          <span
            className={
              styles.selectedLegend
            }
          >
            Semana selecionada
          </span>
        </div>

        <div
          className={
            styles.chartScroll
          }
        >
          <svg
            className={
              styles.chart
            }
            viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
            role="img"
            aria-label={`Evolução da probabilidade de risco elevado em ${HORIZON_LABELS[horizon]}, com limiar de alerta de ${thresholdFormatter.format(threshold)}`}
          >
            {yLabels.map(
              (value) => {
                const y =
                  PADDING.top
                  + (
                    1
                    - value
                  )
                  * plotHeight;

                return (
                  <g
                    key={
                      value
                    }
                  >
                    <line
                      className={
                        styles.gridLine
                      }
                      x1={
                        PADDING.left
                      }
                      y1={
                        y
                      }
                      x2={
                        PADDING.left
                        + plotWidth
                      }
                      y2={
                        y
                      }
                    />

                    <text
                      className={
                        styles.axisLabel
                      }
                      x={
                        PADDING.left
                        - 12
                      }
                      y={
                        y + 4
                      }
                      textAnchor="end"
                    >
                      {
                        `${Math.round(
                          value
                          * 100,
                        )}%`
                      }
                    </text>
                  </g>
                );
              },
            )}

            {xLabels.map(
              (item) => (
                <text
                  key={
                    item.week
                  }
                  className={
                    styles.axisLabel
                  }
                  x={
                    item.x
                  }
                  y={
                    CHART_HEIGHT
                    - 18
                  }
                  textAnchor="middle"
                >
                  {
                    `SE ${item.week}`
                  }
                </text>
              ),
            )}

            <line
              className={
                styles.thresholdLine
              }
              x1={
                PADDING.left
              }
              y1={
                thresholdY
              }
              x2={
                PADDING.left
                + plotWidth
              }
              y2={
                thresholdY
              }
            />

            <text
              className={
                styles.thresholdLabel
              }
              x={
                PADDING.left
                + 8
              }
              y={
                Math.max(
                  thresholdY
                  - 8,
                  14,
                )
              }
            >
              {
                `Limiar ${thresholdFormatter.format(
                  threshold,
                )}`
              }
            </text>

            {selectedChartPoint ? (
              <line
                className={
                  styles.selectedWeekLine
                }
                x1={
                  selectedChartPoint.x
                }
                y1={
                  PADDING.top
                }
                x2={
                  selectedChartPoint.x
                }
                y2={
                  PADDING.top
                  + plotHeight
                }
              />
            ) : null}

            <path
              className={
                styles.scoreLine
              }
              d={
                scorePath
              }
            />

            {chartPoints.map(
              (
                chartPoint,
                index,
              ) => (
                <circle
                  key={
                    points[
                      index
                    ].week
                  }
                  className={
                    points[
                      index
                    ].week
                    === selectedWeek
                      ? styles.selectedPoint
                      : styles.scorePoint
                  }
                  cx={
                    chartPoint.x
                  }
                  cy={
                    chartPoint.y
                  }
                  r={
                    points[
                      index
                    ].week
                    === selectedWeek
                      ? 5
                      : 2.5
                  }
                >
                  <title>
                    {
                      `SE ${points[index].week}: ${percentFormatter.format(points[index].score)} · ${points[index].prediction ? "ALERTA" : "SEM ALERTA"}`
                    }
                  </title>
                </circle>
              ),
            )}
          </svg>
        </div>

        {selectedPoint ? (
          <div
            className={
              styles.selectedWeekSummary
            }
          >
            <span>
              Semana selecionada · SE {
                selectedPoint.week
              }
            </span>

            <strong>
              {
                percentFormatter.format(
                  selectedPoint.score,
                )
              }
              {" · "}
              {
                selectedPoint.prediction
                  ? "ALERTA"
                  : "SEM ALERTA"
              }
            </strong>
          </div>
        ) : (
          <div
            className={
              styles.selectedWeekSummary
            }
          >
            <span>
              Semana selecionada
            </span>

            <strong>
              Indisponível para este horizonte
            </strong>
          </div>
        )}
      </div>

      <p
        className={
          styles.note
        }
      >
        Valores acima ou iguais ao limiar daquele horizonte correspondem à classificação ALERTA. O gráfico representa probabilidades retrospectivas do teste de 2025 e não uma previsão atual.
      </p>
    </section>
  );
}