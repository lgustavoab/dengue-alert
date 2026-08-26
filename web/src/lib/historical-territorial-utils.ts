import type {
  HistoricalSeasonalityRegionalItem,
  HistoricalSpatialRegionItem,
  HistoricalSpatialStateItem,
} from "@/lib/serving/types";

export function findRegionSummary(
  data: HistoricalSpatialRegionItem[],
  region: string,
): HistoricalSpatialRegionItem | null {
  if (!region) {
    return null;
  }

  return data.find(
    (item) =>
      item.regiao
      === region,
  ) ?? null;
}

export function findStateSummary(
  data: HistoricalSpatialStateItem[],
  ufCode: string,
): HistoricalSpatialStateItem | null {
  if (!ufCode) {
    return null;
  }

  return data.find(
    (item) =>
      item.codigo_uf_ibge
      === ufCode,
  ) ?? null;
}

export function filterStatesByRegion(
  data: HistoricalSpatialStateItem[],
  region: string,
): HistoricalSpatialStateItem[] {
  if (!region) {
    return [];
  }

  return data.filter(
    (item) =>
      item.regiao
      === region,
  );
}

export function sortStatesByAverageIncidence(
  data: HistoricalSpatialStateItem[],
): HistoricalSpatialStateItem[] {
  return [...data].sort(
    (a, b) =>
      b
        .incidencia_media_anual_100mil
      - a
        .incidencia_media_anual_100mil,
  );
}

export function sortRegionsByAverageIncidence(
  data: HistoricalSpatialRegionItem[],
): HistoricalSpatialRegionItem[] {
  return [...data].sort(
    (a, b) =>
      b
        .incidencia_media_anual_100mil
      - a
        .incidencia_media_anual_100mil,
  );
}

export function filterRegionalSeasonality(
  data: HistoricalSeasonalityRegionalItem[],
  region: string,
): HistoricalSeasonalityRegionalItem[] {
  if (!region) {
    return [];
  }

  return data
    .filter(
      (item) =>
        item.regiao
        === region,
    )
    .sort(
      (a, b) =>
        a
          .semana_epidemiologica
        - b
          .semana_epidemiologica,
    );
}

export function getRegionalSeasonalityPeak(
  data: HistoricalSeasonalityRegionalItem[],
): HistoricalSeasonalityRegionalItem | null {
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
      item
        .incidencia_mediana_100mil
      > current
        .incidencia_mediana_100mil
        ? item
        : current,
  );
}