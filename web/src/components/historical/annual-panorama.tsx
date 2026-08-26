import {
  scaleSeries,
  pointsToPath,
} from "@/lib/historical-chart-utils";

import {
  formatDecimal,
  formatInteger,
  formatPercent,
} from "@/lib/serving/formatters";

import type {
  HistoricalAnnualItem,
} from "@/lib/serving/types";

import styles from "./historical-dashboard.module.css";

type AnnualPanoramaProps = {
  data: HistoricalAnnualItem[];
};

const CHART_WIDTH =
  900;

const CHART_HEIGHT =
  280;

const PADDING = {
  top: 20,
  right: 24,
  bottom: 44,
  left: 56,
};

export function AnnualPanorama({
  data,
}: AnnualPanoramaProps) {
  if (
    data.length === 0
  ) {
    return null;
  }

  const maxCases =
    Math.max(
      ...data.map(
        (item) =>
          item
            .casos_provaveis,
      ),
      1,
    );

  const maxIncidence =
    Math.max(
      ...data.map(
        (item) =>
          item
            .incidencia_anual_100mil,
      ),
      1,
    );

  const incidencePoints =
    scaleSeries(
      data.map(
        (item) =>
          item
            .incidencia_anual_100mil,
      ),
      CHART_WIDTH,
      CHART_HEIGHT,
      PADDING,
      maxIncidence,
    );

  const incidencePath =
    pointsToPath(
      incidencePoints,
    );

  const plotWidth =
    CHART_WIDTH
    - PADDING.left
    - PADDING.right;

  const plotHeight =
    CHART_HEIGHT
    - PADDING.top
    - PADDING.bottom;

  const slotWidth =
    plotWidth
    / data.length;

  const barWidth =
    Math.min(
      54,
      slotWidth * 0.58,
    );

  const isSingleYear =
    data.length === 1;

  const firstYear =
    data[0]
      .ano_epidemiologico;

  const lastYear =
    data[
      data.length - 1
    ]
      .ano_epidemiologico;

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
            Evolução anual
          </span>

          <h2>
            {isSingleYear
              ? `Panorama epidemiológico de ${firstYear}`
              : "Casos e incidência por ano epidemiológico"}
          </h2>
        </div>

        <p>
          {isSingleYear
            ? `Indicadores nacionais do ano epidemiológico de ${firstYear}.`
            : `Comparação nacional entre ${firstYear} e ${lastYear}. Casos e incidência são apresentados separadamente para evitar confundir volume absoluto com risco populacional.`}
        </p>
      </div>

      <div
        className={
          styles.chartGrid
        }
      >
        <article
          className={
            styles.chartCard
          }
        >
          <div
            className={
              styles.chartCardHeader
            }
          >
            <h3>
              Casos prováveis
            </h3>

            <p>
              Volume nacional registrado em cada ano.
            </p>
          </div>

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
                isSingleYear
                  ? `Casos prováveis de dengue em ${firstYear}`
                  : `Casos prováveis de dengue entre ${firstYear} e ${lastYear}`
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

              {data.map(
                (
                  item,
                  index,
                ) => {
                  const height =
                    (
                      item
                        .casos_provaveis
                      / maxCases
                    )
                    * plotHeight;

                  const x =
                    PADDING.left
                    + index
                    * slotWidth
                    + (
                      slotWidth
                      - barWidth
                    )
                    / 2;

                  const y =
                    PADDING.top
                    + plotHeight
                    - height;

                  return (
                    <g
                      key={
                        item
                          .ano_epidemiologico
                      }
                    >
                      <rect
                        className={
                          styles.bar
                        }
                        x={
                          x
                        }
                        y={
                          y
                        }
                        width={
                          barWidth
                        }
                        height={
                          Math.max(
                            height,
                            2,
                          )
                        }
                        rx="5"
                      >
                        <title>
                          {`${item.ano_epidemiologico}: ${formatInteger(
                            item.casos_provaveis,
                          )} casos`}
                        </title>
                      </rect>

                      <text
                        className={
                          styles.axisText
                        }
                        x={
                          x
                          + barWidth
                          / 2
                        }
                        y={
                          CHART_HEIGHT
                          - 14
                        }
                        textAnchor="middle"
                      >
                        {
                          item
                            .ano_epidemiologico
                        }
                      </text>
                    </g>
                  );
                },
              )}
            </svg>
          </div>
        </article>

        <article
          className={
            styles.chartCard
          }
        >
          <div
            className={
              styles.chartCardHeader
            }
          >
            <h3>
              Incidência anual
            </h3>

            <p>
              Casos por 100 mil habitantes.
            </p>
          </div>

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
              aria-label="Incidência anual de dengue por 100 mil habitantes"
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
                  incidencePath
                }
              />

              {incidencePoints.map(
                (
                  point,
                  index,
                ) => {
                  const item =
                    data[
                      index
                    ];

                  return (
                    <g
                      key={
                        item
                          .ano_epidemiologico
                      }
                    >
                      <circle
                        className={
                          styles.point
                        }
                        cx={
                          point.x
                        }
                        cy={
                          point.y
                        }
                        r="5"
                      >
                        <title>
                          {`${item.ano_epidemiologico}: ${formatDecimal(
                            item.incidencia_anual_100mil,
                          )} por 100 mil`}
                        </title>
                      </circle>

                      <text
                        className={
                          styles.axisText
                        }
                        x={
                          point.x
                        }
                        y={
                          CHART_HEIGHT
                          - 14
                        }
                        textAnchor="middle"
                      >
                        {
                          item
                            .ano_epidemiologico
                        }
                      </text>
                    </g>
                  );
                },
              )}
            </svg>
          </div>
        </article>
      </div>

      <div
        className={
          styles.tableWrapper
        }
      >
        <table
          className={
            styles.table
          }
        >
          <thead>
            <tr>
              <th>
                Ano
              </th>

              <th>
                Casos
              </th>

              <th>
                Incidência
              </th>

              <th>
                Pico semanal
              </th>

              <th>
                SE do pico
              </th>

              <th>
                Territórios com casos
              </th>
            </tr>
          </thead>

          <tbody>
            {data.map(
              (item) => (
                <tr
                  key={
                    item
                      .ano_epidemiologico
                  }
                >
                  <td>
                    <strong>
                      {
                        item
                          .ano_epidemiologico
                      }
                    </strong>
                  </td>

                  <td>
                    {formatInteger(
                      item
                        .casos_provaveis,
                    )}
                  </td>

                  <td>
                    {formatDecimal(
                      item
                        .incidencia_anual_100mil,
                    )}
                  </td>

                  <td>
                    {formatInteger(
                      item
                        .pico_semanal_casos,
                    )}
                  </td>

                  <td>
                    SE{" "}
                    {
                      item
                        .semana_pico
                    }
                  </td>

                  <td>
                    {formatPercent(
                      item
                        .proporcao_unidades_com_casos,
                    )}
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}