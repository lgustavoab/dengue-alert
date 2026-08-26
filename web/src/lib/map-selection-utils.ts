import type {
  PredictionMapHorizon,
  PredictionMapIndexContract,
} from "@/lib/serving/prediction-map-types";

export const DEFAULT_MAP_WEEK =
  49;

export const DEFAULT_MAP_HORIZON:
  PredictionMapHorizon =
  1;

export type MapSelection = {
  week:
  number;

  horizon:
  PredictionMapHorizon;

  normalized:
  boolean;
};

function parseIntegerParameter(
  value: string | null,
): number | null {
  if (
    value === null
    || !/^\d+$/.test(
      value,
    )
  ) {
    return null;
  }

  const parsed =
    Number(
      value,
    );

  if (
    !Number.isInteger(
      parsed,
    )
  ) {
    return null;
  }

  return parsed;
}

function isPredictionMapHorizon(
  value: number | null,
): value is PredictionMapHorizon {
  return (
    value !== null
    && [
      1,
      2,
      3,
      4,
    ].includes(
      value,
    )
  );
}

export function getAvailableMapHorizons(
  index: PredictionMapIndexContract,
  week: number,
): PredictionMapHorizon[] {
  if (
    !Number.isInteger(
      week,
    )
    || week < 1
    || week > 52
  ) {
    return [];
  }

  const horizons: Array<{
    key: "h1" | "h2" | "h3" | "h4";
    value: PredictionMapHorizon;
  }> = [
      {
        key: "h1",
        value: 1,
      },
      {
        key: "h2",
        value: 2,
      },
      {
        key: "h3",
        value: 3,
      },
      {
        key: "h4",
        value: 4,
      },
    ];

  return horizons
    .filter(
      ({ key }) =>
        index.horizontes[
          key
        ].semanas.includes(
          week,
        ),
    )
    .map(
      ({ value }) =>
        value,
    );
}

export function normalizeMapSelection(
  index: PredictionMapIndexContract,
  weekParameter: string | null,
  horizonParameter: string | null,
): MapSelection {
  const parsedWeek =
    parseIntegerParameter(
      weekParameter,
    );

  const availableWeeks =
    index.horizontes
      .h1
      .semanas;

  const week =
    parsedWeek !== null
      && availableWeeks.includes(
        parsedWeek,
      )
      ? parsedWeek
      : DEFAULT_MAP_WEEK;

  const parsedHorizon =
    parseIntegerParameter(
      horizonParameter,
    );

  let horizon:
    PredictionMapHorizon =
    isPredictionMapHorizon(
      parsedHorizon,
    )
      ? parsedHorizon
      : DEFAULT_MAP_HORIZON;

  const availableHorizons =
    getAvailableMapHorizons(
      index,
      week,
    );

  if (
    !availableHorizons.includes(
      horizon,
    )
  ) {
    horizon =
      DEFAULT_MAP_HORIZON;
  }

  const normalized =
    weekParameter
    !== String(
      week,
    )
    || horizonParameter
    !== String(
      horizon,
    );

  return {
    week,
    horizon,
    normalized,
  };
}

export function getMapHorizonLabel(
  horizon: PredictionMapHorizon,
): string {
  const weeksAhead: Record<
    PredictionMapHorizon,
    string
  > = {
    1:
      "1 semana à frente",
    2:
      "2 semanas à frente",
    3:
      "3 semanas à frente",
    4:
      "4 semanas à frente",
  };

  return (
    `H${horizon} · `
    + weeksAhead[
    horizon
    ]
  );
}

export function formatMapWeekLabel(
  week: number,
): string {
  return (
    `SE${String(
      week,
    ).padStart(
      2,
      "0",
    )}`
  );
}