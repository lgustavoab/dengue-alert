import type {
  HistoricalRiskMunicipalityItem,
  HistoricalRiskWeeklyItem,
} from "@/lib/serving/types";

export type RiskTerritorialScope = {
  region?: string;
  ufCode?: string;
};

export function filterRiskWeeklyByScope(
  data: HistoricalRiskWeeklyItem[],
  region: string,
): HistoricalRiskWeeklyItem[] {
  const scale =
    region
      ? "regional"
      : "nacional";

  const group =
    region
      ? region
      : "Brasil";

  return data
    .filter(
      (item) =>
        item.escala
          === scale
        && item.grupo
          === group,
    )
    .sort(
      (a, b) => {
        if (
          a.ano_epidemiologico
          !== b.ano_epidemiologico
        ) {
          return (
            a.ano_epidemiologico
            - b.ano_epidemiologico
          );
        }

        return (
          a.semana_epidemiologica
          - b.semana_epidemiologica
        );
      },
    );
}

export function getRiskWeeklyPeak(
  data: HistoricalRiskWeeklyItem[],
): HistoricalRiskWeeklyItem | null {
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
        .proporcao_unidades_em_risco
      > current
        .proporcao_unidades_em_risco
        ? item
        : current,
  );
}

export function findMunicipalityRiskSummary(
  data: HistoricalRiskMunicipalityItem[],
  code: string,
): HistoricalRiskMunicipalityItem | null {
  if (
    !code
  ) {
    return null;
  }

  return data.find(
    (item) =>
      item.codigo_ibge_7
      === code,
  ) ?? null;
}

export function filterRiskMunicipalities(
  data: HistoricalRiskMunicipalityItem[],
  scope: RiskTerritorialScope,
): HistoricalRiskMunicipalityItem[] {
  return data.filter(
    (item) => {
      if (
        scope.region
        && item.regiao
        !== scope.region
      ) {
        return false;
      }

      if (
        scope.ufCode
        && item.codigo_uf_ibge
        !== scope.ufCode
      ) {
        return false;
      }

      return true;
    },
  );
}

export function sortRiskMunicipalitiesByProportion(
  data: HistoricalRiskMunicipalityItem[],
): HistoricalRiskMunicipalityItem[] {
  return [...data].sort(
    (a, b) => {
      const difference =
        b.proporcao_semanas_risco
        - a.proporcao_semanas_risco;

      if (
        difference !== 0
      ) {
        return difference;
      }

      return (
        b.semanas_risco
        - a.semanas_risco
      );
    },
  );
}

export function countMunicipalitiesWithRecurrence(
  data: HistoricalRiskMunicipalityItem[],
): number {
  return data.filter(
    (item) =>
      item.recorrencia_multianual,
  ).length;
}

export function countMunicipalitiesWithRisk(
  data: HistoricalRiskMunicipalityItem[],
): number {
  return data.filter(
    (item) =>
      item.semanas_risco
      > 0,
  ).length;
}

export function getAverageRiskProportion(
  data: HistoricalRiskMunicipalityItem[],
): number {
  if (
    data.length === 0
  ) {
    return 0;
  }

  const total =
    data.reduce(
      (
        accumulator,
        item,
      ) =>
        accumulator
        + item
          .proporcao_semanas_risco,
      0,
    );

  return (
    total
    / data.length
  );
}