import {
  CLIMATE_VARIABLES,
  filterClimateByVariable,
  filterRegionalClimateByVariable,
  getClimateVariableLabel,
  getStrongestObservedMedianAssociation,
  isBoundaryLag,
  type ClimateVariable,
} from "@/lib/historical-climate-utils";

import {
  formatInteger,
} from "@/lib/serving/formatters";

import type {
  HistoricalClimateLagItem,
  HistoricalClimateRegionalLagItem,
} from "@/lib/serving/types";

import styles from "./historical-climate-analysis.module.css";
import { HistoricalDetails } from "./historical-details";
import { HistoricalChartAxes, HistoricalChartFrame, historicalChartViewBox } from "./historical-chart-axes";

type HistoricalClimateAnalysisProps = {
  nationalData:
    HistoricalClimateLagItem[];

  regionalData:
    HistoricalClimateRegionalLagItem[];

  selectedRegion:
    string;

  selectedUf:
    string;

  selectedMunicipality:
    string | null;
};

const CHART_WIDTH =
  960;

const CHART_HEIGHT =
  300;

const PADDING = {
  top: 26,
  right: 28,
  bottom: 52,
  left: 62,
};

function formatCorrelation(
  value: number,
): string {
  return new Intl.NumberFormat(
    "pt-BR",
    {
      minimumFractionDigits:
        3,

      maximumFractionDigits:
        3,
    },
  ).format(
    value,
  );
}

function getCorrelationBounds(
  data: HistoricalClimateLagItem[],
): {
  minimum: number;
  maximum: number;
} {
  const values =
    data.flatMap(
      (item) => [
        item.correlacao_p25,
        item.correlacao_mediana,
        item.correlacao_p75,
        0,
      ],
    );

  const rawMinimum =
    Math.min(
      ...values,
    );

  const rawMaximum =
    Math.max(
      ...values,
    );

  const span =
    Math.max(
      rawMaximum
      - rawMinimum,
      0.05,
    );

  const padding =
    span
    * 0.12;

  return {
    minimum:
      rawMinimum
      - padding,

    maximum:
      rawMaximum
      + padding,
  };
}

function getX(
  index: number,
  count: number,
): number {
  const plotWidth =
    CHART_WIDTH
    - PADDING.left
    - PADDING.right;

  if (
    count <= 1
  ) {
    return (
      PADDING.left
      + plotWidth
      / 2
    );
  }

  return (
    PADDING.left
    + (
      index
      / (
        count
        - 1
      )
    )
    * plotWidth
  );
}

function getY(
  value: number,
  minimum: number,
  maximum: number,
): number {
  const plotHeight =
    CHART_HEIGHT
    - PADDING.top
    - PADDING.bottom;

  return (
    PADDING.top
    + (
      (
        maximum
        - value
      )
      / (
        maximum
        - minimum
      )
    )
    * plotHeight
  );
}

function buildLinePath(
  data: HistoricalClimateLagItem[],
  minimum: number,
  maximum: number,
): string {
  return data
    .map(
      (
        item,
        index,
      ) => {
        const x =
          getX(
            index,
            data.length,
          );

        const y =
          getY(
            item
              .correlacao_mediana,
            minimum,
            maximum,
          );

        return `${index === 0 ? "M" : "L"} ${x} ${y}`;
      },
    )
    .join(
      " ",
    );
}

function buildBandPolygon(
  data: HistoricalClimateLagItem[],
  minimum: number,
  maximum: number,
): string {
  const upper =
    data.map(
      (
        item,
        index,
      ) =>
        `${getX(
          index,
          data.length,
        )},${getY(
          item.correlacao_p75,
          minimum,
          maximum,
        )}`,
    );

  const lower =
    [...data]
      .reverse()
      .map(
        (
          item,
          reverseIndex,
        ) => {
          const originalIndex =
            data.length
            - reverseIndex
            - 1;

          return `${getX(
            originalIndex,
            data.length,
          )},${getY(
            item.correlacao_p25,
            minimum,
            maximum,
          )}`;
        },
      );

  return [
    ...upper,
    ...lower,
  ].join(
    " ",
  );
}

function ClimateVariableChart({
  data,
  variable,
  scopeLabel,
}: {
  data:
    HistoricalClimateLagItem[];

  variable:
    ClimateVariable;

  scopeLabel:
    string;
}) {
  if (
    data.length === 0
  ) {
    return null;
  }

  const strongest =
    getStrongestObservedMedianAssociation(
      data,
    );

  const {
    minimum,
    maximum,
  } =
    getCorrelationBounds(
      data,
    );

  const linePath =
    buildLinePath(
      data,
      minimum,
      maximum,
    );

  const bandPolygon =
    buildBandPolygon(
      data,
      minimum,
      maximum,
    );

  const zeroY =
    getY(
      0,
      minimum,
      maximum,
    );

  const plotHeight =
    CHART_HEIGHT
    - PADDING.top
    - PADDING.bottom;

  const strongestIndex =
    strongest
      ? data.indexOf(
          strongest,
        )
      : -1;

  const strongestX =
    strongestIndex >= 0
      ? getX(
          strongestIndex,
          data.length,
        )
      : null;

  const strongestY =
    strongest
      ? getY(
          strongest
            .correlacao_mediana,
          minimum,
          maximum,
        )
      : null;

  const validMunicipalities =
    strongest
      ?.municipios_correlacao_valida
    ?? data[0]
      .municipios_correlacao_valida;

  const totalMunicipalities =
    strongest
      ?.municipios_total
    ?? data[0]
      .municipios_total;

  const boundary =
    strongest
      ? isBoundaryLag(
          strongest
            .lag_semanas,
        )
      : false;

  return (
    <article
      className={
        styles.chartCard
      }
    >
      <div
        className={
          styles.chartHeader
        }
      >
        <div
          className={
            styles.chartHeaderContent
          }
        >
          <h3>
            {
              getClimateVariableLabel(
                variable,
              )
            }
          </h3>

          <p>
            Correlação mediana entre os municípios para cada deslocamento temporal analisado.
          </p>
        </div>

        {strongest ? (
          <div
            className={
              styles.summary
            }
          >
            <span>
              Maior associação observada
            </span>

            <strong>
              {formatCorrelation(
                strongest
                  .correlacao_mediana,
              )}
            </strong>

            <small>
              clima {strongest.lag_semanas} semana{strongest.lag_semanas === 1 ? "" : "s"} antes
            </small>
          </div>
        ) : null}
      </div>

      <HistoricalChartFrame label={`${getClimateVariableLabel(variable)}: semanas de diferença e correlação municipal`}>
        <svg
          className={
            styles.svg
          }
          viewBox={historicalChartViewBox(CHART_WIDTH, CHART_HEIGHT)}
          role="img"
          aria-label={`${getClimateVariableLabel(
            variable,
          )}: associação histórica com dengue em ${scopeLabel}`}
        >
          <HistoricalChartAxes width={CHART_WIDTH} height={CHART_HEIGHT} padding={PADDING} minimum={minimum} maximum={maximum} format="correlation" xLabel="Clima observado quantas semanas antes? (lag)" yLabel="Correlação de Spearman (sem unidade)" />
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

          <line
            className={
              styles.zeroLine
            }
            x1={
              PADDING.left
            }
            x2={
              CHART_WIDTH
              - PADDING.right
            }
            y1={
              zeroY
            }
            y2={
              zeroY
            }
          />

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

          {data.map(
            (
              item,
              index,
            ) => {
              const x =
                getX(
                  index,
                  data.length,
                );

              const y =
                getY(
                  item
                    .correlacao_mediana,
                  minimum,
                  maximum,
                );

              return (
                <circle
                  key={
                    item
                      .lag_semanas
                  }
                  className={
                    styles.point
                  }
                  cx={
                    x
                  }
                  cy={
                    y
                  }
                  r="4"
                >
                  <title>
                    {`Lag ${item.lag_semanas}: correlação mediana ${formatCorrelation(
                      item
                        .correlacao_mediana,
                    )}; Q25 ${formatCorrelation(
                      item
                        .correlacao_p25,
                    )}; Q75 ${formatCorrelation(
                      item
                        .correlacao_p75,
                    )}`}
                  </title>
                </circle>
              );
            },
          )}

          {strongestX !== null
          && strongestY !== null ? (
            <circle
              className={
                styles.strongestPoint
              }
              cx={
                strongestX
              }
              cy={
                strongestY
              }
              r="7"
            >
              <title>
                {strongest
                  ? `Maior associação observada na janela: lag ${strongest.lag_semanas}, correlação mediana ${formatCorrelation(
                      strongest
                        .correlacao_mediana,
                    )}`
                  : ""}
              </title>
            </circle>
          ) : null}

          {data.map(
            (
              item,
              index,
            ) => (
              <text
                key={`label-${item.lag_semanas}`}
                className={
                  styles.axisText
                }
                x={
                  getX(
                    index,
                    data.length,
                  )
                }
                y={
                  CHART_HEIGHT
                  - 16
                }
                textAnchor="middle"
              >
                {item.lag_semanas}
              </text>
            ),
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

          Correlação mediana
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

          Metade central das correlações (Q25–Q75)
        </span>
      </div>

      <p
        className={
          styles.coverage
        }
      >
        Cobertura no ponto destacado: {formatInteger(
          validMunicipalities,
        )} de {formatInteger(
          totalMunicipalities,
        )} municípios com correlação válida.
      </p>

      {boundary ? (
        <p
          className={
            styles.warning
          }
        >
          O maior valor observado ocorre no lag 8, que é o limite da janela analisada. Portanto, este resultado não permite concluir que oito semanas seja o deslocamento temporal de associação máxima real.
        </p>
      ) : null}
    </article>
  );
}

export function HistoricalClimateAnalysis({
  nationalData,
  regionalData,
  selectedRegion,
  selectedUf,
  selectedMunicipality,
}: HistoricalClimateAnalysisProps) {
  if (
    selectedMunicipality
  ) {
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
              Clima e dengue
            </span>

            <h2>
              Associação climática municipal
            </h2>
          </div>
        </div>

        <div
          className={
            styles.unavailable
          }
        >
          Esta visualização não disponibiliza associações climáticas individuais por município. Para explorar os resumos das correlações municipais, selecione Brasil ou uma região. Isso não significa ausência de relação entre clima e dengue neste município.
        </div>
      </section>
    );
  }

  if (
    selectedUf
  ) {
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
              Clima e dengue
            </span>

            <h2>
              Associação climática estadual
            </h2>
          </div>
        </div>

        <div
          className={
            styles.unavailable
          }
        >
          Esta visualização disponibiliza resumos para Brasil e regiões, não para estados. Selecione Brasil ou uma região para explorá-los. A ausência de um resumo estadual não significa ausência de relação entre clima e dengue.
        </div>
      </section>
    );
  }

  const scopeLabel =
    selectedRegion
      || "Brasil";

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
            Clima e dengue
          </span>

          <h2>
            O que observamos sobre o clima? · {scopeLabel}
          </h2>
        </div>

        <p>
          Análise exploratória de 2016–2025: comparamos temperatura, umidade e chuva com a incidência semanal de dengue (casos por 100 mil habitantes). O filtro de ano não muda esta seção.
        </p>
      </div>

      <div
        className={
          styles.explanationGrid
        }
      >
        <div
          className={
            styles.explanation
          }
        >
          <strong>
            O clima veio antes ou na mesma semana?
          </strong>{" "}
          Comparamos o clima da mesma semana e de semanas anteriores. Quatro semanas de diferença, por exemplo, compara o clima de quatro semanas antes com a incidência da semana analisada. Essa diferença de tempo é chamada de lag.
        </div>

        <div
          className={
            styles.explanation
          }
        >
          <strong>
            Correlação não implica causalidade.
          </strong>{" "}
          Uma associação histórica não demonstra que determinada condição climática seja, isoladamente, a causa de um aumento da dengue.
        </div>
      </div>

      <p className={styles.coverage}>Os gráficos resumem correlações calculadas separadamente em cada município. Não são uma única correlação de uma série agregada do Brasil ou da região, nem medem a contribuição do clima para o desempenho do modelo.</p>

      <HistoricalDetails title="Explorar os gráficos de temperatura, umidade e chuva">
        <p>A correlação de Spearman varia de −1 a 1. Valores positivos indicam que as duas medidas tenderam a crescer juntas; negativos, que tenderam a variar em sentidos opostos. Valores próximos de zero indicam associação fraca nessa medida, não ausência de qualquer relação.</p>
        <p>A linha mostra a mediana (valor central) das correlações municipais. A faixa entre Q25 e Q75 reúne a metade central dessas correlações. O eixo horizontal mostra quantas semanas antes o clima foi observado.</p>
        <p>Foram comparadas apenas as diferenças de 0, 1, 2, 3, 4, 6 e 8 semanas. O ponto destacado é a maior associação observada nessa janela, não um prazo ótimo definitivo.</p>
      <div
        className={
          styles.chartGrid
        }
      >
        {CLIMATE_VARIABLES.map(
          (variable) => {
            const data =
              selectedRegion
                ? filterRegionalClimateByVariable(
                    regionalData,
                    selectedRegion,
                    variable,
                  )
                : filterClimateByVariable(
                    nationalData,
                    variable,
                  );

            return (
              <ClimateVariableChart
                key={
                  variable
                }
                data={
                  data
                }
                variable={
                  variable
                }
                scopeLabel={
                  scopeLabel
                }
              />
            );
          },
        )}
      </div>
      </HistoricalDetails>

      <p
        className={
          styles.coverage
        }
      >
        Os valores apresentados resumem associações históricas entre municípios para os lags disponíveis no protocolo. Eles não são previsões, coeficientes causais nem evidência de que uma variável climática determine sozinha o comportamento epidemiológico.
      </p>
    </section>
  );
}
