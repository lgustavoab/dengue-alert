import type { MunicipalityMapDatum } from "@/lib/map-prediction";
import type { MapSliceStatus } from "@/lib/map-slice-state";
import type { PredictionMapContract, PredictionMapHorizon } from "@/lib/serving/prediction-map-types";
import { formatMapWeekDateRange } from "@/lib/map-week-dates";

import styles from "./municipality-map.module.css";

export function formatMapAdvanceLabel(horizon: PredictionMapHorizon): string {
  return `${horizon} ${horizon === 1 ? "semana" : "semanas"} depois · H${horizon}`;
}

export function MunicipalityMapResult({ prediction, municipality, status }: {
  prediction: PredictionMapContract | null;
  municipality: MunicipalityMapDatum | null;
  status: MapSliceStatus;
}) {
  if (status === "loading") {
    return <div className={styles.selectionLoading} role="status">Carregando o resultado para a semana e o prazo selecionados…</div>;
  }

  if (status === "error") {
    return <div className={styles.selectionUnavailable} role="status">O resultado deste município não pôde ser carregado. Isso não significa “Sem alerta” nem “Sem avaliação”. Use “Tentar novamente” acima; sua seleção será mantida.</div>;
  }

  if (prediction === null || municipality === null) return null;

  const withoutEvaluation = municipality.status === "sem_avaliacao";
  const alert = municipality.status === "alerta";
  const label = withoutEvaluation ? "SEM AVALIAÇÃO PREDITIVA" : alert ? "ALERTA" : "SEM ALERTA";
  const badge = withoutEvaluation ? styles.withoutEvaluationBadge : alert ? styles.alertBadge : styles.noAlertBadge;
  const explanation = withoutEvaluation
    ? "Este território aparece no mapa, mas não tem resultado na avaliação de 2025. Não é possível classificá-lo como Alerta ou Sem alerta."
    : alert
      ? "O modelo indicou risco elevado para a semana futura selecionada. É uma indicação do modelo, não a confirmação de que esse risco ocorreu."
      : "O modelo não indicou alerta para a semana futura selecionada. Isso não significa ausência de dengue nem garante que não houve risco elevado.";
  const percentage = (value: number) => new Intl.NumberFormat("pt-BR", {
    style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2,
  }).format(value);

  return <>
    <div className={styles.detailGrid}>
      <div className={styles.detailPrimary}>
        <span>O que o modelo indicou</span>
        <strong className={`${styles.statusBadge} ${badge}`}>{label}</strong>
        <p>{explanation}</p>
      </div>
      <div className={styles.detailItem}>
        <span>Semana de referência de 2025</span>
        <strong>SE{String(prediction.semana_epidemiologica).padStart(2, "0")}</strong>
        <small>{formatMapWeekDateRange(prediction.semana_epidemiologica)}</small>
        <span>Resultado consultado</span>
        <strong>{formatMapAdvanceLabel(prediction.horizonte)}</strong>
      </div>
    </div>
    <div className={styles.interpretation}>
      <strong>Como ler este resultado</strong>
      <p>Avaliação retrospectiva de 2025, não um alerta atual. O mapa mostra a indicação do modelo, não o risco observado nem a quantidade futura de casos. Não representa a chance individual de uma pessoa contrair dengue.</p>
    </div>
    {!withoutEvaluation && municipality.score !== null ? (
      <details className={styles.resultDetails}>
        <summary>Como o alerta foi definido</summary>
        <p>A probabilidade estimada se refere ao risco elevado do município na semana futura. O limite de alerta foi definido durante a validação do estudo; a classificação exibida é o resultado oficial, sem novo cálculo na interface.</p>
        <dl className={styles.numericDetails}>
          <div><dt>Probabilidade estimada de risco elevado</dt><dd>{percentage(municipality.score)}</dd></div>
          <div><dt>Limite de alerta (limiar)</dt><dd>{percentage(prediction.threshold)}</dd></div>
        </dl>
      </details>
    ) : null}
  </>;
}
