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
      ? "Alerta confirmado"
      : "Alerta não confirmado"
    : point.target
      ? "Risco elevado não identificado"
      : "Sem alerta e sem risco elevado observado";

  return (
    <div className={styles.comparison}>
      <dl className={styles.observed}>
        <dt>O que foi observado nessa semana futura</dt>
        <dd>
          {point.target ? "Risco elevado observado" : "Sem risco elevado observado"}
        </dd>
      </dl>
      <div className={`${styles.result} ${matches ? styles.match : styles.mismatch}`}>
        <span>Comparação com o observado</span>
        <strong>{outcome}</strong>
      </div>
    </div>
  );
}
