import {
  getPredictionPoint,
  predictionMatchesObservedTarget,
  PREDICTION_HORIZONS,
} from "@/lib/prediction-selection-utils";

import type {
  PredictionHorizonKey,
} from "@/lib/prediction-selection-utils";

import type {
  PredictionMunicipalitySeriesContract,
} from "@/lib/serving/types";

import styles from "./prediction-retrospective.module.css";

type PredictionRetrospectiveProps = {
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

function formatOriginState(
  value: boolean,
): string {
  return value
    ? "Risco elevado"
    : "Sem risco elevado";
}

function formatPrediction(
  value: boolean,
): string {
  return value
    ? "ALERTA"
    : "SEM ALERTA";
}

function formatObservedTarget(
  value: boolean,
): string {
  return value
    ? "Risco elevado observado"
    : "Sem risco elevado observado";
}

export function PredictionRetrospective({
  series,
  week,
}: PredictionRetrospectiveProps) {
  return (
    <section
      className={
        styles.section
      }
      aria-labelledby="prediction-retrospective-title"
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
          Validação retrospectiva
        </span>

        <h2
          id="prediction-retrospective-title"
        >
          Previsão versus estado observado
        </h2>

        <p>
          Como 2025 já pertence ao período de teste concluído, é possível comparar o resultado emitido pelo modelo com o estado epidemiológico que foi realmente observado no horizonte correspondente.
        </p>
      </div>

      <div
        className={
          styles.grid
        }
      >
        {PREDICTION_HORIZONS.map(
          (horizon) => {
            const point =
              getPredictionPoint(
                series,
                horizon,
                week,
              );

            if (
              point === null
            ) {
              return null;
            }

            const presentation =
              HORIZON_PRESENTATION[
                horizon
              ];

            const matches =
              predictionMatchesObservedTarget(
                point,
              );

            return (
              <article
                key={
                  horizon
                }
                className={
                  styles.card
                }
              >
                <div
                  className={
                    styles.cardHeader
                  }
                >
                  <strong
                    className={
                      styles.horizon
                    }
                  >
                    {
                      presentation.shortLabel
                    }
                  </strong>

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

                <dl
                  className={
                    styles.comparisonList
                  }
                >
                  <div
                    className={
                      styles.comparisonItem
                    }
                  >
                    <dt>
                      Estado na semana de referência
                    </dt>

                    <dd>
                      {
                        formatOriginState(
                          point.riskElevated,
                        )
                      }
                    </dd>
                  </div>

                  <div
                    className={
                      styles.comparisonItem
                    }
                  >
                    <dt>
                      O modelo previu
                    </dt>

                    <dd>
                      {
                        formatPrediction(
                          point.prediction,
                        )
                      }
                    </dd>
                  </div>

                  <div
                    className={
                      styles.comparisonItem
                    }
                  >
                    <dt>
                      Estado futuro observado
                    </dt>

                    <dd>
                      {
                        formatObservedTarget(
                          point.target,
                        )
                      }
                    </dd>
                  </div>
                </dl>

                <div
                  className={`${styles.result} ${
                    matches
                      ? styles.match
                      : styles.mismatch
                  }`}
                >
                  <span>
                    Comparação retrospectiva
                  </span>

                  <strong>
                    {matches
                      ? "Previsão e observação coincidiram"
                      : "Previsão e observação não coincidiram"}
                  </strong>
                </div>
              </article>
            );
          },
        )}
      </div>

      <p
        className={
          styles.note
        }
      >
        Esta comparação só é possível porque os resultados pertencem ao teste retrospectivo de 2025. Ela não transforma o sistema em uma previsão de casos e não altera a classificação oficial ALERTA / SEM ALERTA.
      </p>
    </section>
  );
}