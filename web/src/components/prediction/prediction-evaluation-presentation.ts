import type { PredictionHorizonKey } from "@/lib/prediction-selection-utils";

export const evaluationTimeLabels: Record<PredictionHorizonKey, string> = {
  h1: "1 semana depois",
  h2: "2 semanas depois",
  h3: "3 semanas depois",
  h4: "4 semanas depois",
};

const integerFormatter = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });
const percentFormatter = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});
const thresholdFormatter = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const scoreFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 4,
  maximumFractionDigits: 4,
});

export const formatEvaluationInteger = (value: number | null): string =>
  value === null ? "—" : integerFormatter.format(value);
export const formatEvaluationPercent = (value: number | null): string =>
  value === null ? "—" : percentFormatter.format(value);
export const formatEvaluationThreshold = (value: number): string => thresholdFormatter.format(value);
export const formatEvaluationScore = (value: number): string => scoreFormatter.format(value);
