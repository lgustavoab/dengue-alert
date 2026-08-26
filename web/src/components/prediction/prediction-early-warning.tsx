import type {
  PredictionByHorizonContract,
  PredictionEvaluationHorizon,
} from "@/lib/serving/types";

import styles from "./prediction-early-warning.module.css";

type PredictionEarlyWarningProps = {
  evaluation:
    PredictionByHorizonContract;
};

const HORIZON_KEYS = [
  "h1",
  "h2",
  "h3",
  "h4",
] as const;

type HorizonKey =
  (typeof HORIZON_KEYS)[number];

const HORIZON_PRESENTATION: Record<
  HorizonKey,
  {
    label: string;
    distance: string;
  }
> = {
  h1: {
    label:
      "H1",

    distance:
      "1 semana à frente",
  },

  h2: {
    label:
      "H2",

    distance:
      "2 semanas à frente",
  },

  h3: {
    label:
      "H3",

    distance:
      "3 semanas à frente",
  },

  h4: {
    label:
      "H4",

    distance:
      "4 semanas à frente",
  },
};

const integerFormatter =
  new Intl.NumberFormat(
    "pt-BR",
  );

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

function formatNullableInteger(
  value: number | null,
): string {
  return value === null
    ? "—"
    : integerFormatter.format(
        value,
      );
}

function formatNullablePercent(
  value: number | null,
): string {
  return value === null
    ? "—"
    : percentFormatter.format(
        value,
      );
}

function EarlyWarningCard({
  horizonKey,
  horizon,
}: {
  horizonKey:
    HorizonKey;

  horizon:
    PredictionEvaluationHorizon;
}) {
  const presentation =
    HORIZON_PRESENTATION[
      horizonKey
    ];

  const model =
    horizon
      .modelo_final
      .early_warning;

  const persistence =
    horizon
      .baseline_persistencia
      .early_warning;

  return (
    <article
      className={
        styles.card
      }
    >
      <div
        className={
          styles.cardHeader
        }
      >
        <div>
          <strong
            className={
              styles.horizon
            }
          >
            {
              presentation.label
            }
          </strong>

          <span
            className={
              styles.distance
            }
          >
            {
              presentation.distance
            }
          </span>
        </div>
      </div>

      <div
        className={
          styles.contextGrid
        }
      >
        <div
          className={
            styles.contextItem
          }
        >
          <span>
            Observações elegíveis
          </span>

          <strong>
            {
              integerFormatter.format(
                model.observacoes,
              )
            }
          </strong>
        </div>

        <div
          className={
            styles.contextItem
          }
        >
          <span>
            Novas entradas em risco observadas
          </span>

          <strong>
            {
              integerFormatter.format(
                model.positivos,
              )
            }
          </strong>
        </div>

        <div
          className={
            styles.contextItem
          }
        >
          <span>
            Alertas antecipados emitidos
          </span>

          <strong>
            {
              formatNullableInteger(
                model.alertas,
              )
            }
          </strong>
        </div>

        <div
          className={
            styles.contextItem
          }
        >
          <span>
            Proporção de alertas
          </span>

          <strong>
            {
              formatNullablePercent(
                model
                  .proporcao_alertas,
              )
            }
          </strong>
        </div>
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
          <span>
            Métrica
          </span>

          <strong>
            Modelo
          </strong>

          <strong>
            Persistência
          </strong>
        </div>

        <div
          className={
            styles.comparisonRow
          }
        >
          <span>
            Recall
          </span>

          <strong>
            {
              percentFormatter.format(
                model.recall,
              )
            }
          </strong>

          <strong>
            {
              percentFormatter.format(
                persistence.recall,
              )
            }
          </strong>
        </div>

        <div
          className={
            styles.comparisonRow
          }
        >
          <span>
            Precisão
          </span>

          <strong>
            {
              percentFormatter.format(
                model.precision,
              )
            }
          </strong>

          <strong>
            {
              percentFormatter.format(
                persistence.precision,
              )
            }
          </strong>
        </div>

        <div
          className={
            styles.comparisonRow
          }
        >
          <span>
            F1
          </span>

          <strong>
            {
              percentFormatter.format(
                model.f1,
              )
            }
          </strong>

          <strong>
            {
              percentFormatter.format(
                persistence.f1,
              )
            }
          </strong>
        </div>

        <div
          className={
            styles.comparisonRow
          }
        >
          <span>
            Alertas emitidos
          </span>

          <strong>
            {
              formatNullableInteger(
                model.alertas,
              )
            }
          </strong>

          <strong>
            {
              formatNullableInteger(
                persistence.alertas,
              )
            }
          </strong>
        </div>
      </div>
    </article>
  );
}

export function PredictionEarlyWarning({
  evaluation,
}: PredictionEarlyWarningProps) {
  return (
    <section
      className={
        styles.section
      }
      aria-labelledby="prediction-early-warning-title"
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
            Alerta antecipado
          </span>

          <h2
            id="prediction-early-warning-title"
          >
            Capacidade de antecipar novas entradas em risco
          </h2>
        </div>

        <p>
          Este recorte considera semanas em que o município ainda não estava em estado de risco elevado. O objetivo é avaliar se o modelo conseguiu identificar antecipadamente municípios que entrariam em risco no horizonte futuro.
        </p>
      </div>

      <div
        className={
          styles.explanation
        }
      >
        <div>
          <strong>
            O que significa “observação elegível”?
          </strong>

          <p>
            É uma observação município-semana cuja semana de referência ainda estava fora do estado de risco elevado.
          </p>
        </div>

        <div>
          <strong>
            O que significa “alerta antecipado”?
          </strong>

          <p>
            Dentro desse recorte, ocorre quando o modelo classifica o horizonte futuro como ALERTA antes de o município já estar em risco na semana de referência.
          </p>
        </div>

        <div>
          <strong>
            Por que comparar com persistência?
          </strong>

          <p>
            A baseline de persistência simplesmente mantém para o futuro o estado observado na semana atual. Por isso, quando a origem ainda está fora do risco, ela não consegue antecipar uma nova entrada.
          </p>
        </div>
      </div>

      <div
        className={
          styles.grid
        }
      >
        {HORIZON_KEYS.map(
          (horizonKey) => (
            <EarlyWarningCard
              key={
                horizonKey
              }
              horizonKey={
                horizonKey
              }
              horizon={
                evaluation
                  .horizontes[
                    horizonKey
                  ]
              }
            />
          ),
        )}
      </div>

      <p
        className={
          styles.note
        }
      >
        Recall indica qual proporção das novas entradas em risco foi identificada antecipadamente. Precisão indica, entre os alertas emitidos, quantos corresponderam a uma entrada em risco observada. F1 sintetiza o equilíbrio entre essas duas métricas.
      </p>
    </section>
  );
}