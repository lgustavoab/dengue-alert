import type {
  HistoricalClimateLagItem,
  HistoricalClimateRegionalLagItem,
} from "@/lib/serving/types";

export const CLIMATE_VARIABLES = [
  "temperatura_media_c",
  "umidade_relativa_media_pct",
  "precipitacao_total_mm",
] as const;

export type ClimateVariable =
  (typeof CLIMATE_VARIABLES)[number];

export const CLIMATE_LAGS = [
  0,
  1,
  2,
  3,
  4,
  6,
  8,
] as const;

export const CLIMATE_VARIABLE_LABELS: Record<
  ClimateVariable,
  string
> = {
  temperatura_media_c:
    "Temperatura média",

  umidade_relativa_media_pct:
    "Umidade relativa média",

  precipitacao_total_mm:
    "Precipitação total",
};

export function isClimateVariable(
  value: string,
): value is ClimateVariable {
  return (
    CLIMATE_VARIABLES
      .some(
        (variable) =>
          variable === value,
      )
  );
}

export function filterClimateByVariable(
  data: HistoricalClimateLagItem[],
  variable: ClimateVariable,
): HistoricalClimateLagItem[] {
  return data
    .filter(
      (item) =>
        item
          .variavel_climatica
        === variable,
    )
    .sort(
      (a, b) =>
        a.lag_semanas
        - b.lag_semanas,
    );
}

export function filterRegionalClimate(
  data: HistoricalClimateRegionalLagItem[],
  region: string,
): HistoricalClimateRegionalLagItem[] {
  if (
    !region
  ) {
    return [];
  }

  return data.filter(
    (item) =>
      item.regiao
      === region,
  );
}

export function filterRegionalClimateByVariable(
  data: HistoricalClimateRegionalLagItem[],
  region: string,
  variable: ClimateVariable,
): HistoricalClimateRegionalLagItem[] {
  return data
    .filter(
      (item) =>
        item.regiao
          === region
        && item
          .variavel_climatica
          === variable,
    )
    .sort(
      (a, b) =>
        a.lag_semanas
        - b.lag_semanas,
    );
}

export function getStrongestObservedMedianAssociation<
  T extends HistoricalClimateLagItem,
>(
  data: T[],
): T | null {
  if (
    data.length === 0
  ) {
    return null;
  }

  return data.reduce(
    (
      current,
      item,
    ) =>
      Math.abs(
        item
          .correlacao_mediana,
      )
      > Math.abs(
        current
          .correlacao_mediana,
      )
        ? item
        : current,
  );
}

export function isBoundaryLag(
  lag: number,
  availableLags: readonly number[] =
    CLIMATE_LAGS,
): boolean {
  if (
    availableLags.length
    === 0
  ) {
    return false;
  }

  const maximumLag =
    Math.max(
      ...availableLags,
    );

  return (
    lag
    === maximumLag
  );
}

export function getClimateVariableLabel(
  variable: string,
): string {
  if (
    isClimateVariable(
      variable,
    )
  ) {
    return (
      CLIMATE_VARIABLE_LABELS[
        variable
      ]
    );
  }

  return variable;
}

export function getAvailableClimateLags(
  data: HistoricalClimateLagItem[],
): number[] {
  return [
    ...new Set(
      data.map(
        (item) =>
          item
            .lag_semanas,
      ),
    ),
  ].sort(
    (a, b) =>
      a - b,
  );
}