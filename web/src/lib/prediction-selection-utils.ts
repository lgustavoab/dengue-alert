import type {
  PredictionMunicipalitySeriesContract,
  TerritoryFilterItem,
} from "@/lib/serving/types";

export const PREDICTION_HORIZONS = [
  "h1",
  "h2",
  "h3",
  "h4",
] as const;

export type PredictionHorizonKey =
  (typeof PREDICTION_HORIZONS)[number];

export type PredictionReferenceWeek = {
  year:
    number;

  week:
    number;

  startDate:
    string;
};

export type PredictionPoint = {
  horizon:
    PredictionHorizonKey;

  threshold:
    number;

  year:
    number;

  week:
    number;

  startDate:
    string;

  riskElevated:
    boolean;

  target:
    boolean;

  score:
    number;

  prediction:
    boolean;
};

export function filterPredictionTerritories(
  items: TerritoryFilterItem[],
): TerritoryFilterItem[] {
  return items.filter(
    (item) =>
      item.predicaoDisponivel,
  );
}

export function getPredictionReferenceWeeks(
  series: PredictionMunicipalitySeriesContract,
): PredictionReferenceWeek[] {
  const data =
    series
      .horizontes
      .h1
      .data;

  return data
    .semana_epidemiologica
    .map(
      (
        week,
        index,
      ) => ({
        year:
          data
            .ano_epidemiologico[
              index
            ],

        week,

        startDate:
          data
            .data_inicio_semana[
              index
            ],
      }),
    );
}

export function findPredictionReferenceWeek(
  series: PredictionMunicipalitySeriesContract,
  week: number,
): PredictionReferenceWeek | null {
  return (
    getPredictionReferenceWeeks(
      series,
    ).find(
      (item) =>
        item.week
        === week,
    )
    ?? null
  );
}

export function getAvailableHorizonsForWeek(
  series: PredictionMunicipalitySeriesContract,
  week: number,
): PredictionHorizonKey[] {
  return PREDICTION_HORIZONS.filter(
    (horizon) =>
      series
        .horizontes[
          horizon
        ]
        .data
        .semana_epidemiologica
        .includes(
          week,
        ),
  );
}

export function getPredictionPoint(
  series: PredictionMunicipalitySeriesContract,
  horizon: PredictionHorizonKey,
  week: number,
): PredictionPoint | null {
  const block =
    series
      .horizontes[
        horizon
      ];

  const data =
    block.data;

  const index =
    data
      .semana_epidemiologica
      .findIndex(
        (item) =>
          item === week,
      );

  if (
    index === -1
  ) {
    return null;
  }

  return {
    horizon,

    threshold:
      block.threshold,

    year:
      data
        .ano_epidemiologico[
          index
        ],

    week:
      data
        .semana_epidemiologica[
          index
        ],

    startDate:
      data
        .data_inicio_semana[
          index
        ],

    riskElevated:
      data
        .risco_elevado[
          index
        ],

    target:
      data
        .target[
          index
        ],

    score:
      data
        .score[
          index
        ],

    prediction:
      data
        .predicao[
          index
        ],
  };
}

export function formatPredictionDate(
  value: string,
): string {
  const [
    year,
    month,
    day,
  ] =
    value.split(
      "-",
    );

  if (
    !year
    || !month
    || !day
  ) {
    return value;
  }

  return `${day}/${month}/${year}`;
}

export function formatPredictionWeekLabel(
  week: PredictionReferenceWeek,
): string {
  return `SE ${String(
    week.week,
  ).padStart(
    2,
    "0",
  )} · ${formatPredictionDate(
    week.startDate,
  )}`;
}