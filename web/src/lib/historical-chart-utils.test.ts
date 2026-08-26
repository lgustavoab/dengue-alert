import {
  describe,
  expect,
  it,
} from "vitest";

import {
  buildBandPolygon,
  filterWeeklyByYear,
  getPeakWeeklyItem,
  getSeasonalityPeak,
  getWeeklyMetricValue,
  pointsToPath,
  scaleSeries,
} from "@/lib/historical-chart-utils";

import type {
  HistoricalSeasonalityNationalItem,
  HistoricalWeeklyItem,
} from "@/lib/serving/types";

function weeklyItem(
  year: number,
  week: number,
  cases: number,
  incidence: number,
): HistoricalWeeklyItem {
  return {
    ano_epidemiologico:
      year,

    semana_epidemiologica:
      week,

    data_inicio_semana:
      `${year}-01-01`,

    data_fim_semana:
      `${year}-01-07`,

    casos_provaveis:
      cases,

    unidades_territoriais:
      5570,

    unidades_territoriais_com_casos:
      1000,

    populacao_nacional:
      200000000,

    incidencia_nacional_100mil:
      incidence,

    proporcao_unidades_com_casos:
      0.5,
  };
}

function seasonalityItem(
  week: number,
  medianIncidence: number,
): HistoricalSeasonalityNationalItem {
  return {
    semana_epidemiologica:
      week,

    anos_disponiveis:
      10,

    casos_media:
      100,

    casos_mediana:
      90,

    casos_minimo:
      10,

    casos_maximo:
      200,

    incidencia_media_100mil:
      medianIncidence + 1,

    incidencia_mediana_100mil:
      medianIncidence,

    incidencia_q25_100mil:
      medianIncidence / 2,

    incidencia_q75_100mil:
      medianIncidence * 1.5,

    incidencia_minima_100mil:
      0,

    incidencia_maxima_100mil:
      medianIncidence * 2,
  };
}

describe(
  "historical chart utils",
  () => {
    it(
      "mantém todas as semanas quando nenhum ano é selecionado",
      () => {
        const data = [
          weeklyItem(
            2023,
            1,
            10,
            1,
          ),
          weeklyItem(
            2024,
            1,
            20,
            2,
          ),
        ];

        expect(
          filterWeeklyByYear(
            data,
            null,
          ),
        ).toEqual(
          data,
        );
      },
    );

    it(
      "filtra semanas pelo ano epidemiológico",
      () => {
        const data = [
          weeklyItem(
            2023,
            1,
            10,
            1,
          ),
          weeklyItem(
            2024,
            1,
            20,
            2,
          ),
          weeklyItem(
            2024,
            2,
            30,
            3,
          ),
        ];

        const filtered =
          filterWeeklyByYear(
            data,
            2024,
          );

        expect(
          filtered,
        ).toHaveLength(
          2,
        );

        expect(
          filtered.every(
            (item) =>
              item
                .ano_epidemiologico
              === 2024,
          ),
        ).toBe(
          true,
        );
      },
    );

    it(
      "escala uma série respeitando os limites do gráfico",
      () => {
        const points =
          scaleSeries(
            [
              0,
              50,
              100,
            ],
            100,
            100,
            {
              top: 10,
              right: 10,
              bottom: 10,
              left: 10,
            },
          );

        expect(
          points,
        ).toHaveLength(
          3,
        );

        expect(
          points[0].x,
        ).toBeCloseTo(
          10,
        );

        expect(
          points[2].x,
        ).toBeCloseTo(
          90,
        );

        expect(
          points[2].y,
        ).toBeCloseTo(
          10,
        );

        expect(
          points[0].y,
        ).toBeCloseTo(
          90,
        );
      },
    );

    it(
      "centraliza uma série com um único ponto",
      () => {
        const points =
          scaleSeries(
            [
              10,
            ],
            100,
            100,
            {
              top: 10,
              right: 10,
              bottom: 10,
              left: 10,
            },
          );

        expect(
          points[0].x,
        ).toBeCloseTo(
          50,
        );
      },
    );

    it(
      "constrói um path SVG a partir dos pontos",
      () => {
        const points =
          scaleSeries(
            [
              10,
              20,
            ],
            100,
            100,
            {
              top: 10,
              right: 10,
              bottom: 10,
              left: 10,
            },
          );

        const path =
          pointsToPath(
            points,
          );

        expect(
          path.startsWith(
            "M ",
          ),
        ).toBe(
          true,
        );

        expect(
          path,
        ).toContain(
          " L ",
        );
      },
    );

    it(
      "constrói a faixa interquartil como polígono",
      () => {
        const polygon =
          buildBandPolygon(
            [
              1,
              2,
              3,
            ],
            [
              4,
              5,
              6,
            ],
            100,
            100,
            {
              top: 10,
              right: 10,
              bottom: 10,
              left: 10,
            },
          );

        expect(
          polygon.length,
        ).toBeGreaterThan(
          0,
        );

        expect(
          polygon.split(
            " ",
          ),
        ).toHaveLength(
          6,
        );
      },
    );

    it(
      "identifica o pico semanal pela métrica selecionada",
      () => {
        const data = [
          weeklyItem(
            2024,
            1,
            100,
            30,
          ),
          weeklyItem(
            2024,
            2,
            200,
            20,
          ),
        ];

        expect(
          getPeakWeeklyItem(
            data,
            "cases",
          )
            ?.semana_epidemiologica,
        ).toBe(
          2,
        );

        expect(
          getPeakWeeklyItem(
            data,
            "incidence",
          )
            ?.semana_epidemiologica,
        ).toBe(
          1,
        );

        expect(
          getWeeklyMetricValue(
            data[0],
            "incidence",
          ),
        ).toBe(
          30,
        );
      },
    );

    it(
      "identifica a semana de maior incidência mediana sazonal",
      () => {
        const data = [
          seasonalityItem(
            1,
            4,
          ),
          seasonalityItem(
            2,
            9,
          ),
          seasonalityItem(
            3,
            6,
          ),
        ];

        expect(
          getSeasonalityPeak(
            data,
          )
            ?.semana_epidemiologica,
        ).toBe(
          2,
        );
      },
    );
  },
);