import { PREDICTION_HORIZONS } from "@/lib/prediction-selection-utils";
import type { PredictionByHorizonContract } from "@/lib/serving/types";

import {
  evaluationTimeLabels,
  formatEvaluationInteger,
  formatEvaluationPercent,
} from "./prediction-evaluation-presentation";
import styles from "./prediction-early-warning.module.css";

export function PredictionEarlyWarning({ evaluation }: { evaluation: PredictionByHorizonContract }) {
  return (
    <section className={styles.section} aria-labelledby="prediction-early-warning-title">
      <div className={styles.heading}>
        <h3 id="prediction-early-warning-title">O modelo identificou risco antes de ele estar presente?</h3>
        <p>
          Aqui entram apenas as situações sem risco elevado na semana de referência.
          Comparamos os alertas com o estado observado em cada semana futura,
          não com qualquer ocorrência ao longo do intervalo.
        </p>
      </div>

      <p className={styles.guide}>
        Os dois percentuais abaixo respondem a perguntas diferentes: quanto do
        risco observado foi identificado e quantos alertas se confirmaram.
        Não são uma porcentagem única de acerto.
      </p>

      <div className={styles.grid}>
        {PREDICTION_HORIZONS.map((key) => {
          const metrics = evaluation.horizontes[key].modelo_final.early_warning;
          const matrix = metrics.matriz_confusao;
          const titleId = `early-warning-${key}-title`;

          return (
            <article key={key} className={styles.card} aria-labelledby={titleId}>
              <div className={styles.cardHeader}>
                <h4 id={titleId}>{evaluationTimeLabels[key]}</h4>
                <span>{key.toUpperCase()}</span>
              </div>

              <dl className={styles.rates}>
                <div>
                  <dt>Situações de risco identificadas</dt>
                  <dd>
                    <strong>{formatEvaluationPercent(metrics.recall)}</strong>
                    <span>Entre as situações que apresentaram risco elevado na semana futura.</span>
                    <span>
                      {formatEvaluationInteger(matrix.tp)} de {formatEvaluationInteger(metrics.positivos)} situações identificadas.
                    </span>
                  </dd>
                </div>
                <div>
                  <dt>Alertas que se confirmaram</dt>
                  <dd>
                    <strong>{formatEvaluationPercent(metrics.precision)}</strong>
                    <span>Entre os alertas emitidos pelo modelo neste recorte.</span>
                    <span>
                      {metrics.alertas === null
                        ? "Total de alertas não informado."
                        : `${formatEvaluationInteger(matrix.tp)} de ${formatEvaluationInteger(metrics.alertas)} alertas confirmados.`}
                    </span>
                  </dd>
                </div>
              </dl>

              <dl className={styles.errors}>
                <div>
                  <dt>Alertas não confirmados</dt>
                  <dd>{formatEvaluationInteger(matrix.fp)}</dd>
                </div>
                <div>
                  <dt>Situações de risco não identificadas</dt>
                  <dd>{formatEvaluationInteger(matrix.fn)}</dd>
                </div>
              </dl>
              <p className={styles.coverage}>
                {formatEvaluationInteger(metrics.observacoes)} situações avaliadas sem risco elevado na origem.
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
