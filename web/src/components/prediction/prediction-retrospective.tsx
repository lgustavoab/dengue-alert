import {
  predictionMatchesObservedTarget,
} from "@/lib/prediction-selection-utils";
import type { PredictionPoint } from "@/lib/prediction-selection-utils";

import styles from "./prediction-retrospective.module.css";

type PredictionRetrospectiveProps = {
  point: PredictionPoint;
};

export function PredictionRetrospective({ point }: PredictionRetrospectiveProps) {
  const matches = predictionMatchesObservedTarget(point);
  const outcome = point.prediction
    ? point.target
      ? "O alerta se confirmou nos dados observados."
      : "O alerta não se confirmou nos dados observados."
    : point.target
      ? "O risco elevado foi observado, mas o modelo não emitiu alerta."
      : "O modelo não emitiu alerta e os registros não indicaram risco elevado.";

  return (
    <div className={styles.comparison}>
      <dl className={styles.observed}>
        <dt>Resultado nos dados reais</dt>
        <dd>
          {point.target
            ? "Os registros indicaram risco elevado nessa semana."
            : "Os registros não indicaram risco elevado nessa semana."}
        </dd>
      </dl>
      <div className={`${styles.result} ${matches ? styles.match : styles.mismatch}`}>
        <span>Comparação entre previsão e dados reais</span>
        <strong>{outcome}</strong>
      </div>
    </div>
  );
}
