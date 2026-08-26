import {
  getPredictionPoint,
  PREDICTION_HORIZONS,
} from "@/lib/prediction-selection-utils";

import type {
  PredictionHorizonKey,
} from "@/lib/prediction-selection-utils";

import type {
  PredictionMunicipalitySeriesContract,
} from "@/lib/serving/types";

import styles from "./prediction-results.module.css";

type PredictionResultsProps = {
  series:
    PredictionMunicipalitySeriesContract;

  week:
    number;
};

type HorizonPresentation = {
  shortLabel:
    string;

  timeLabel:
    string;
};

const HORIZON_PRESENTATION: Record<
  PredictionHorizonKey,
  HorizonPresentation
> = {
  h1: {
    shortLabel:
      "H1",

    timeLabel:
      "1 semana à frente",
  },

  h2: {
    shortLabel:
      "H2",

    timeLabel:
      "2 semanas à frente",
  },

  h3: {
    shortLabel:
      "H3",

    timeLabel:
      "3 semanas à frente",
  },

  h4: {
    shortLabel:
      "H4",

    timeLabel:
      "4 semanas à frente",
  },
};

const scoreFormatter =
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

function formatScore(
  value: number,
): string {
  return scoreFormatter.format(
    value,
  );
}

function formatThreshold(
  value: number,
): string {
  return thresholdFormatter.format(
    value,
  );
}

export function PredictionResults({
  series,
  week,
}: PredictionResultsProps) {
  return (
    <section
      className={
        styles.results
      }
      aria-labelledby="prediction-results-title"
    >
      <div
        className={
          styles.heading
        }
      >
        <span
          className={
            styles.eyebrow
          }
        >
          Resultado do modelo
        </span>

        <h2
          id="prediction-results-title"
        >
          Previsão por horizonte
        </h2>

        <p>
          Cada horizonte representa uma distância temporal a partir da semana epidemiológica selecionada. A classificação apresentada corresponde ao resultado retrospectivo produzido pelo modelo para 2025.
        </p>
      </div>

      <div
        className={
          styles.grid
        }
      >
        {PREDICTION_HORIZONS.map(
          (horizon) => {
            const presentation =
              HORIZON_PRESENTATION[
                horizon
              ];

            const point =
              getPredictionPoint(
                series,
                horizon,
                week,
              );

            if (
              point === null
            ) {
              return (
                <article
                  key={
                    horizon
                  }
                  className={`${styles.card} ${styles.unavailableCard}`}
                >
                  <div
                    className={
                      styles.cardHeader
                    }
                  >
                    <span
                      className={
                        styles.horizon
                      }
                    >
                      {
                        presentation.shortLabel
                      }
                    </span>

                    <span
                      className={
                        styles.timeLabel
                      }
                    >
                      {
                        presentation.timeLabel
                      }
                    </span>
                  </div>

                  <div
                    className={
                      styles.unavailableContent
                    }
                  >
                    <strong>
                      Indisponível nesta semana
                    </strong>

                    <p>
                      Não existe observação futura suficiente dentro da janela do teste retrospectivo de 2025 para avaliar este horizonte.
                    </p>
                  </div>
                </article>
              );
            }

            const formattedScore =
              formatScore(
                point.score,
              );

            const formattedThreshold =
              formatThreshold(
                point.threshold,
              );

            const statusLabel =
              point.prediction
                ? "ALERTA"
                : "SEM ALERTA";

            const comparisonOperator =
              point.prediction
                ? "≥"
                : "<";

            return (
              <article
                key={
                  horizon
                }
                className={`${styles.card} ${
                  point.prediction
                    ? styles.alertCard
                    : styles.noAlertCard
                }`}
              >
                <div
                  className={
                    styles.cardHeader
                  }
                >
                  <span
                    className={
                      styles.horizon
                    }
                  >
                    {
                      presentation.shortLabel
                    }
                  </span>

                  <span
                    className={
                      styles.timeLabel
                    }
                  >
                    {
                      presentation.timeLabel
                    }
                  </span>
                </div>

                <div
                  className={
                    styles.probability
                  }
                >
                  <span>
                    Probabilidade de risco elevado
                  </span>

                  <strong>
                    {
                      formattedScore
                    }
                  </strong>
                </div>

                <div
                  className={
                    styles.details
                  }
                >
                  <div
                    className={
                      styles.detailItem
                    }
                  >
                    <span>
                      Limiar de alerta
                    </span>

                    <strong>
                      {
                        formattedThreshold
                      }
                    </strong>
                  </div>

                  <div
                    className={
                      styles.comparison
                    }
                    aria-label={`Probabilidade ${formattedScore} ${comparisonOperator === "≥" ? "maior ou igual ao" : "menor que o"} limiar de alerta ${formattedThreshold}`}
                  >
                    <span>
                      {
                        formattedScore
                      }
                    </span>

                    <strong>
                      {
                        comparisonOperator
                      }
                    </strong>

                    <span>
                      {
                        formattedThreshold
                      }
                    </span>
                  </div>
                </div>

                <div
                  className={`${styles.status} ${
                    point.prediction
                      ? styles.alertStatus
                      : styles.noAlertStatus
                  }`}
                >
                  <span>
                    Classificação
                  </span>

                  <strong>
                    {
                      statusLabel
                    }
                  </strong>
                </div>
              </article>
            );
          },
        )}
      </div>

      <div
        className={
          styles.explanation
        }
      >
        <div
          className={
            styles.explanationItem
          }
        >
          <strong>
            H1–H4
          </strong>

          <p>
            H1 representa uma semana à frente; H2, duas semanas; H3, três semanas; e H4, quatro semanas. Os horizontes indicam distância temporal, não níveis de gravidade.
          </p>
        </div>

        <div
          className={
            styles.explanationItem
          }
        >
          <strong>
            Probabilidade de risco elevado
          </strong>

          <p>
            É a probabilidade estimada pelo modelo de ocorrência futura do estado de risco elevado definido pela metodologia. Ela não representa a quantidade futura de casos de dengue.
          </p>
        </div>

        <div
          className={
            styles.explanationItem
          }
        >
          <strong>
            Limiar de alerta
          </strong>

          <p>
            É o valor de corte definido durante a validação do modelo. Cada horizonte possui seu próprio limiar.
          </p>
        </div>

        <div
          className={
            styles.explanationItem
          }
        >
          <strong>
            ALERTA / SEM ALERTA
          </strong>

          <p>
            Quando a probabilidade prevista atinge ou supera o limiar daquele horizonte, o resultado fornecido pelo modelo é ALERTA. Caso contrário, é SEM ALERTA.
          </p>
        </div>
      </div>

      <p
        className={
          styles.retrospectiveNote
        }
      >
        Estes resultados pertencem à avaliação retrospectiva de 2025. Eles não representam alertas atuais de 2026 nem previsão da quantidade futura de casos.
      </p>
    </section>
  );
}