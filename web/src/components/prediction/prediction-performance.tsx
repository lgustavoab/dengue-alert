import type {
  PredictionByHorizonContract,
  PredictionEvaluationHorizon,
} from "@/lib/serving/types";

import {
  PredictionEarlyWarning,
} from "@/components/prediction/prediction-early-warning";

import styles from "./prediction-performance.module.css";

type PredictionPerformanceProps = {
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

type HorizonPresentation = {
  label:
  string;

  distance:
  string;
};

const HORIZON_PRESENTATION: Record<
  HorizonKey,
  HorizonPresentation
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
    {
      maximumFractionDigits:
        0,
    },
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

const scoreFormatter =
  new Intl.NumberFormat(
    "pt-BR",
    {
      minimumFractionDigits:
        3,

      maximumFractionDigits:
        3,
    },
  );

function PerformanceCard({
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

  const metrics =
    horizon
      .modelo_final
      .geral;

  const metricItems = [
    {
      label:
        "PR-AUC",

      value:
        scoreFormatter.format(
          metrics
            .pr_auc_average_precision,
        ),
    },

    {
      label:
        "ROC-AUC",

      value:
        scoreFormatter.format(
          metrics.roc_auc,
        ),
    },

    {
      label:
        "Recall",

      value:
        percentFormatter.format(
          metrics.recall,
        ),
    },

    {
      label:
        "Precisão",

      value:
        percentFormatter.format(
          metrics.precision,
        ),
    },

    {
      label:
        "F1",

      value:
        percentFormatter.format(
          metrics.f1,
        ),
    },

    {
      label:
        "Acurácia balanceada",

      value:
        percentFormatter.format(
          metrics
            .balanced_accuracy,
        ),
    },
  ];

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

        <div
          className={
            styles.threshold
          }
        >
          <span>
            Limiar aplicado
          </span>

          <strong>
            {
              thresholdFormatter.format(
                horizon
                  .threshold_modelo,
              )
            }
          </strong>
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
            Observações
          </span>

          <strong>
            {
              integerFormatter.format(
                metrics.observacoes,
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
            Prevalência do estado positivo
          </span>

          <strong>
            {
              percentFormatter.format(
                metrics.prevalencia,
              )
            }
          </strong>
        </div>
      </div>

      <div
        className={
          styles.metricsGrid
        }
      >
        {metricItems.map(
          (item) => (
            <div
              key={
                item.label
              }
              className={
                styles.metricItem
              }
            >
              <span>
                {
                  item.label
                }
              </span>

              <strong>
                {
                  item.value
                }
              </strong>
            </div>
          ),
        )}
      </div>
    </article>
  );
}

export function PredictionPerformance({
  evaluation,
}: PredictionPerformanceProps) {
  return (
    <section
      className={
        styles.section
      }
      aria-labelledby="prediction-performance-title"
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
            Desempenho global
          </span>

          <h2
            id="prediction-performance-title"
          >
            Avaliação do modelo no teste retrospectivo de 2025
          </h2>
        </div>

        <p>
          Estas métricas resumem o desempenho global do modelo em todos os municípios incluídos no teste final. Elas não representam o desempenho do município selecionado na consulta acima.
        </p>
      </div>

      <div
        className={
          styles.scopeNote
        }
      >
        <strong>
          Como ler esta seção
        </strong>

        <p>
          Cada horizonte foi avaliado separadamente. H1 corresponde a uma semana à frente e H4 a quatro semanas à frente. Os resultados utilizam os limiares definidos antes do teste final de 2025.
        </p>
      </div>

      <div
        className={
          styles.grid
        }
      >
        {HORIZON_KEYS.map(
          (horizonKey) => (
            <PerformanceCard
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

      <div
        className={
          styles.metricGuide
        }
      >
        <div>
          <strong>
            PR-AUC
          </strong>

          <p>
            Resume a capacidade do modelo de identificar o estado positivo considerando o equilíbrio entre precisão e recall. É especialmente informativa quando a classe positiva é menos frequente.
          </p>
        </div>

        <div>
          <strong>
            ROC-AUC
          </strong>

          <p>
            Mede a capacidade geral de separar observações positivas e negativas ao longo de diferentes limiares. Valores maiores indicam melhor discriminação.
          </p>
        </div>

        <div>
          <strong>
            Acurácia balanceada
          </strong>

          <p>
            Considera o desempenho nas duas classes de forma equilibrada, reduzindo a influência de uma classe mais frequente sobre a leitura da acurácia.
          </p>
        </div>

        <div>
          <strong>
            Comparação entre horizontes
          </strong>

          <p>
            H1 a H4 representam distâncias temporais diferentes. A redução das métricas nos horizontes mais longos indica maior dificuldade preditiva conforme aumenta a antecedência.
          </p>
        </div>
      </div>

      <PredictionEarlyWarning
        evaluation={
          evaluation
        }
      />
    </section>
  );
}