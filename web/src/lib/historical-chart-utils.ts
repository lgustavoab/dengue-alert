import type {
  HistoricalSeasonalityNationalItem,
  HistoricalWeeklyItem,
} from "@/lib/serving/types";

export type ChartPadding = {
  top: number;
  right: number;
  bottom: number;
  left: number;
};

export type ChartPoint = {
  index: number;
  value: number;
  x: number;
  y: number;
};

export type WeeklyMetric =
  | "cases"
  | "incidence";

export function scaleSeries(
  values: number[],
  width: number,
  height: number,
  padding: ChartPadding,
  maxValueOverride?: number,
): ChartPoint[] {
  if (values.length === 0) {
    return [];
  }

  const plotWidth =
    Math.max(
      width
        - padding.left
        - padding.right,
      1,
    );

  const plotHeight =
    Math.max(
      height
        - padding.top
        - padding.bottom,
      1,
    );

  const observedMax =
    Math.max(
      ...values,
      0,
    );

  const maxValue =
    Math.max(
      maxValueOverride
        ?? observedMax,
      1,
    );

  return values.map(
    (
      value,
      index,
    ) => {
      const x =
        values.length === 1
          ? padding.left
            + plotWidth / 2
          : padding.left
            + (
              index
              / (
                values.length
                - 1
              )
            )
            * plotWidth;

      const y =
        padding.top
        + (
          1
          - value / maxValue
        )
        * plotHeight;

      return {
        index,
        value,
        x,
        y,
      };
    },
  );
}

export function pointsToPath(
  points: ChartPoint[],
): string {
  if (
    points.length === 0
  ) {
    return "";
  }

  return points
    .map(
      (
        point,
        index,
      ) =>
        `${index === 0 ? "M" : "L"} ${point.x.toFixed(
          2,
        )} ${point.y.toFixed(
          2,
        )}`,
    )
    .join(
      " ",
    );
}

export function buildBandPolygon(
  lowerValues: number[],
  upperValues: number[],
  width: number,
  height: number,
  padding: ChartPadding,
): string {
  if (
    lowerValues.length === 0
    || lowerValues.length
      !== upperValues.length
  ) {
    return "";
  }

  const maxValue =
    Math.max(
      ...upperValues,
      ...lowerValues,
      1,
    );

  const upperPoints =
    scaleSeries(
      upperValues,
      width,
      height,
      padding,
      maxValue,
    );

  const lowerPoints =
    scaleSeries(
      lowerValues,
      width,
      height,
      padding,
      maxValue,
    )
      .reverse();

  return [
    ...upperPoints,
    ...lowerPoints,
  ]
    .map(
      (point) =>
        `${point.x.toFixed(
          2,
        )},${point.y.toFixed(
          2,
        )}`,
    )
    .join(
      " ",
    );
}

export function filterWeeklyByYear(
  data: HistoricalWeeklyItem[],
  selectedYear: number | null,
): HistoricalWeeklyItem[] {
  if (
    selectedYear === null
  ) {
    return data;
  }

  return data.filter(
    (item) =>
      item
        .ano_epidemiologico
      === selectedYear,
  );
}

export function getWeeklyMetricValue(
  item: HistoricalWeeklyItem,
  metric: WeeklyMetric,
): number {
  if (
    metric === "incidence"
  ) {
    return item
      .incidencia_nacional_100mil;
  }

  return item
    .casos_provaveis;
}

export function getPeakWeeklyItem(
  data: HistoricalWeeklyItem[],
  metric: WeeklyMetric,
): HistoricalWeeklyItem | null {
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
      getWeeklyMetricValue(
        item,
        metric,
      )
      > getWeeklyMetricValue(
        current,
        metric,
      )
        ? item
        : current,
  );
}

export function getSeasonalityPeak(
  data: HistoricalSeasonalityNationalItem[],
): HistoricalSeasonalityNationalItem | null {
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