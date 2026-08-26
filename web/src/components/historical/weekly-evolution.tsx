"use client";

import {
  useMemo,
  useState,
} from "react";

import {
  filterWeeklyByYear,
  getPeakWeeklyItem,
  getWeeklyMetricValue,
  pointsToPath,
  scaleSeries,
  type WeeklyMetric,
} from "@/lib/historical-chart-utils";

import {
  formatDecimal,
  formatInteger,
} from "@/lib/serving/formatters";

import type {
  HistoricalWeeklyItem,
} from "@/lib/serving/types";

import styles from "./historical-dashboard.module.css";

type WeeklyEvolutionProps = {
  data:
    HistoricalWeeklyItem[];

  selectedYear:
    number | null;
};

const CHART_WIDTH =
  960;

const CHART_HEIGHT =
  320;

const PADDING = {
  top: 28,
  right: 26,
  bottom: 50,
  left: 58,
};

export function WeeklyEvolution({
  data,
  selectedYear,
}: WeeklyEvolutionProps) {
  const [
    metric,
    setMetric,
  ] =
    useState<WeeklyMetric>(
      "cases",
    );

  const filtered =
    useMemo(
      () =>
        filterWeeklyByYear(
          data,
          selectedYear,
        ),
      [
        data,
        selectedYear,
      ],
    );

  if (
    filtered.length
    === 0
  ) {
    return null;
  }

  const values =
    filtered.map(
      (item) =>
        getWeeklyMetricValue(
          item,
          metric,
        ),
    );

  const points =
    scaleSeries(
      values,
      CHART_WIDTH,
      CHART_HEIGHT,
      PADDING,
    );

  const path =
    pointsToPath(
      points,
    );

  const peak =
    getPeakWeeklyItem(
      filtered,
      metric,
    );

  const plotHeight =
    CHART_HEIGHT
    - PADDING.top
    - PADDING.bottom;

  const first =
    filtered[0];

  const last =
    filtered[
      filtered.length - 1
    ];

  const xLabels =
    selectedYear === null
      ? filtered
          .map(
            (
              item,
              index,
            ) => ({
              item,
              index,
            }),
          )
          .filter(
            (
              entry,
              index,
              entries,
            ) =>
              index === 0
              || entry.item
                .ano_epidemiologico
              !== entries[
                index - 1
              ].item
                .ano_epidemiologico,
          )
          .map(
            (entry) => ({
              index:
                entry.index,

              label:
                String(
                  entry.item
                    .ano_epidemiologico,
                ),
            }),
          )
      : [
          1,
          13,
          26,
          39,
          53,
        ]
          .map(
            (week) => {
              const index =
                filtered.findIndex(
                  (item) =>
                    item
                      .semana_epidemiologica
                    === week,
                );

              return {
                index,
                label:
                  `SE ${week}`,
              };
            },
          )
          .filter(
            (entry) =>
              entry.index
              >= 0,
          );

  const peakValue =
    peak
      ? getWeeklyMetricValue(
          peak,
          metric,
        )
      : 0;

  const peakIndex =
    peak
      ? filtered.indexOf(
          peak,
        )
      : -1;

  const peakPoint =
    peakIndex >= 0
      ? points[
          peakIndex
        ]
      : null;

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
            Evolução semanal
          </span>

          <h2>
            {selectedYear
              === null
                ? "522 semanas de histórico epidemiológico"
                : `Comportamento semanal em ${selectedYear}`}
          </h2>
        </div>

        <p>
          Série nacional observada. SE significa Semana Epidemiológica. Use o controle abaixo para alternar entre volume absoluto de casos e incidência por 100 mil habitantes.
        </p>
      </div>

      <div
        className={
          styles.controls
        }
      >
        <div
          className={
            styles.metricToggle
          }
          aria-label="Métrica do gráfico semanal"
        >
          <button
            type="button"
            className={`${styles.metricButton} ${
              metric === "cases"
                ? styles.metricButtonActive
                : ""
            }`}
            aria-pressed={
              metric
              === "cases"
            }
            onClick={() =>
              setMetric(
                "cases",
              )
            }
          >
            Casos
          </button>

          <button
            type="button"
            className={`${styles.metricButton} ${
              metric === "incidence"
                ? styles.metricButtonActive
                : ""
            }`}
            aria-pressed={
              metric
              === "incidence"
            }
            onClick={() =>
              setMetric(
                "incidence",
              )
            }
          >
            Incidência
          </button>
        </div>
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
            Semanas exibidas
          </span>

          <strong>
            {formatInteger(
              filtered.length,
            )}
          </strong>
        </div>

        <div
          className={
            styles.summaryItem
          }
        >
          <span>
            Pico do recorte
          </span>

          <strong>
            {metric === "cases"
              ? formatInteger(
                  peakValue,
                )
              : `${formatDecimal(
                  peakValue,
                )} / 100 mil`}
          </strong>
        </div>

        <div
          className={
            styles.summaryItem
          }
        >
          <span>
            Semana do pico
          </span>

          <strong>
            {peak
              ? `${peak.ano_epidemiologico} · SE ${peak.semana_epidemiologica}`
              : "—"}
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
            styles.svgWrapper
          }
        >
          <svg
            className={
              styles.svg
            }
            viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
            role="img"
            aria-label={
              selectedYear
                === null
                ? "Evolução semanal nacional da dengue entre 2016 e 2025"
                : `Evolução semanal nacional da dengue em ${selectedYear}`
            }
          >
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

            <path
              className={
                styles.line
              }
              d={
                path
              }
            />

            {selectedYear !== null
              ? points.map(
                  (
                    point,
                    index,
                  ) => {
                    const item =
                      filtered[
                        index
                      ];

                    return (
                      <circle
                        key={`${item.ano_epidemiologico}-${item.semana_epidemiologica}`}
                        className={
                          styles.point
                        }
                        cx={
                          point.x
                        }
                        cy={
                          point.y
                        }
                        r="3.2"
                      >
                        <title>
                          {metric === "cases"
                            ? `Semana Epidemiológica ${item.semana_epidemiologica}: ${formatInteger(
                                item.casos_provaveis,
                              )} casos`
                            : `Semana Epidemiológica ${item.semana_epidemiologica}: ${formatDecimal(
                                item.incidencia_nacional_100mil,
                              )} por 100 mil`}
                        </title>
                      </circle>
                    );
                  },
                )
              : null}

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
                    ? `Pico: ${peak.ano_epidemiologico}, Semana Epidemiológica ${peak.semana_epidemiologica}`
                    : ""}
                </title>
              </circle>
            ) : null}

            {xLabels.map(
              (entry) => {
                const point =
                  points[
                    entry.index
                  ];

                if (
                  !point
                ) {
                  return null;
                }

                return (
                  <text
                    key={`${entry.label}-${entry.index}`}
                    className={
                      styles.axisTextSmall
                    }
                    x={
                      point.x
                    }
                    y={
                      CHART_HEIGHT
                      - 16
                    }
                    textAnchor="middle"
                  >
                    {
                      entry.label
                    }
                  </text>
                );
              },
            )}
          </svg>
        </div>
      </div>

      <p
        className={
          styles.note
        }
      >
        SE = Semana Epidemiológica. Período exibido: {first.data_inicio_semana} a {last.data_fim_semana}. A linha representa observações históricas tratadas e não uma previsão.
      </p>
    </section>
  );
}