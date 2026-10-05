import {
  getPredictionPoint,
  PREDICTION_HORIZONS,
} from "@/lib/prediction-selection-utils";
import type { PredictionHorizonKey } from "@/lib/prediction-selection-utils";
import type { PredictionMunicipalitySeriesContract } from "@/lib/serving/types";

import { PredictionRetrospective } from "./prediction-retrospective";
import styles from "./prediction-results.module.css";

type PredictionResultsProps = {
  series: PredictionMunicipalitySeriesContract;
  week: number;
};

const TIME_LABELS: Record<PredictionHorizonKey, string> = {
  h1: "1 semana depois",
  h2: "2 semanas depois",
  h3: "3 semanas depois",
  h4: "4 semanas depois",
};

const scoreFormatter = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const thresholdFormatter = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function PredictionResults({ series, week }: PredictionResultsProps) {
  const origin = getPredictionPoint(series, "h1", week);

  return (
    <section className={styles.results} aria-labelledby="prediction-results-title">
      <div className={styles.heading}>
        <span className={styles.eyebrow}>Consulta municipal · teste de 2025</span>
        <h2 id="prediction-results-title">O alerta se confirmou?</h2>
        <p>
          Como estamos analisando um período passado, podemos comparar a previsão
          do modelo com os dados reais registrados em 2025. Cada prazo mostra uma
          semana futura em relação à semana de referência selecionada; não são
          níveis de gravidade nem resultados de todo o intervalo.
        </p>
      </div>

      {origin ? (
        <div className={styles.origin}>
          <span>Na semana de referência</span>
          <strong>
            {origin.riskElevated ? "Já havia risco elevado" : "Não havia risco elevado"}
          </strong>
          <p>
            {origin.riskElevated
              ? "O risco elevado já estava presente no ponto de partida. Esta consulta não pertence ao recorte de antecipação do risco."
              : "Este é o cenário usado para avaliar a antecipação: identificar risco futuro quando ele ainda não estava presente no ponto de partida."}
          </p>
        </div>
      ) : null}

      <div className={styles.grid}>
        {PREDICTION_HORIZONS.map((horizon) => {
          const point = getPredictionPoint(series, horizon, week);
          const titleId = `prediction-result-${horizon}-title`;

          return (
            <article
              key={horizon}
              aria-labelledby={titleId}
              className={`${styles.card} ${
                point === null
                  ? styles.unavailableCard
                  : point.prediction
                    ? styles.alertCard
                    : styles.noAlertCard
              }`}
            >
              <div className={styles.cardHeader}>
                <h3 id={titleId}>{TIME_LABELS[horizon]}</h3>
                <span>{horizon.toUpperCase()}</span>
              </div>

              {point === null ? (
                <div className={styles.unavailableContent}>
                  <strong>Sem avaliação neste prazo</strong>
                  <p>
                    Não há observação futura suficiente dentro da janela do teste
                    de 2025 para avaliar este prazo. Isso não significa sem alerta.
                  </p>
                </div>
              ) : (
                <>
                  <div className={styles.indication}>
                    <span>Previsão do modelo</span>
                    <strong className={point.prediction ? styles.alertStatus : styles.noAlertStatus}>
                      {point.prediction ? "ALERTA" : "SEM ALERTA"}
                    </strong>
                    <p>
                      {point.prediction
                        ? "O modelo emitiu um alerta para essa semana futura."
                        : "O modelo não emitiu alerta para essa semana futura."}
                    </p>
                  </div>

                  <PredictionRetrospective point={point} />

                  <details className={styles.technicalDetails}>
                    <summary>Como o alerta foi definido</summary>
                    <dl className={styles.technicalValues}>
                      <div>
                        <dt>Probabilidade estimada pelo modelo</dt>
                        <dd>{scoreFormatter.format(point.score)}</dd>
                      </div>
                      <div>
                        <dt>Limite para emitir alerta</dt>
                        <dd>{thresholdFormatter.format(point.threshold)}</dd>
                      </div>
                    </dl>
                    <p>
                      Quando a probabilidade atinge ou supera o limite desse prazo,
                      o modelo emite ALERTA. O limite foi definido na validação,
                      antes do teste de 2025; não precisa ser 50%.
                    </p>
                    <p>
                      Os percentuais exibidos são arredondados. A classificação
                      apresentada é a fornecida pelo modelo, sem novo cálculo a
                      partir desses percentuais. A probabilidade não representa
                      risco individual nem quantidade futura de casos.
                    </p>
                  </details>
                </>
              )}
            </article>
          );
        })}
      </div>

      <div className={styles.note}>
        <p>
          <strong>Sem alerta não significa ausência de dengue nem garantia de segurança.</strong>
        </p>
        <p>
          Nesta pesquisa, risco elevado significa que a incidência acumulada em
          quatro semanas (casos por 100 mil habitantes) supera uma referência
          histórica do próprio município para aquela época do ano. Essa definição
          não equivale a uma declaração oficial de epidemia.
        </p>
        <p>
          Os dados reais são registros de dengue tratados para a pesquisa e estão
          sujeitos às limitações das notificações. Sem risco elevado nos registros
          não significa ausência de casos de dengue.
        </p>
        <p>
          Estes resultados são retrospectivos, de 2025. Não são alertas atuais nem
          previsão da quantidade de casos.
        </p>
      </div>
    </section>
  );
}
