import {
  describe,
  expect,
  it,
} from "vitest";

import {
  filterPredictionTerritories,
  findPredictionReferenceWeek,
  formatPredictionWeekLabel,
  getAvailableHorizonsForWeek,
  getPredictionHorizonPoints,
  getPredictionPoint,
  getPredictionReferenceWeeks,
  predictionMatchesObservedTarget,
  PREDICTION_HORIZONS,
} from "@/lib/prediction-selection-utils";

import {
  getTerritoryFilterItems,
} from "@/lib/serving/server";

import {
  getPredictionMunicipalitySeries,
} from "@/lib/serving/series-server";

describe(
  "prediction selection utils",
  () => {
    it(
      "mantém apenas os 5569 municípios com previsão disponível",
      async () => {
        const territories =
          await getTerritoryFilterItems();

        const predictionTerritories =
          filterPredictionTerritories(
            territories,
          );

        expect(
          predictionTerritories,
        ).toHaveLength(
          5_569,
        );

        expect(
          predictionTerritories.some(
            (item) =>
              item.codigoIbge7
              === "5101837",
          ),
        ).toBe(
          false,
        );

        expect(
          predictionTerritories.some(
            (item) =>
              item.codigoIbge7
              === "2605459",
          ),
        ).toBe(
          false,
        );
      },
    );

    it(
      "mantém Penápolis disponível para consulta preditiva",
      async () => {
        const territories =
          filterPredictionTerritories(
            await getTerritoryFilterItems(),
          );

        const penapolis =
          territories.find(
            (item) =>
              item.codigoIbge7
              === "3537305",
          );

        expect(
          penapolis,
        ).toBeDefined();

        expect(
          penapolis
            ?.predicaoDisponivel,
        ).toBe(
          true,
        );
      },
    );

    it(
      "gera 52 semanas de referência para Penápolis",
      async () => {
        const series =
          await getPredictionMunicipalitySeries(
            "3537305",
          );

        const weeks =
          getPredictionReferenceWeeks(
            series,
          );

        expect(
          weeks,
        ).toHaveLength(
          52,
        );
      },
    );

    it(
      "preserva a primeira e a última semana de referência",
      async () => {
        const series =
          await getPredictionMunicipalitySeries(
            "3537305",
          );

        const weeks =
          getPredictionReferenceWeeks(
            series,
          );

        expect(
          weeks[0],
        ).toEqual(
          {
            year:
              2025,

            week:
              1,

            startDate:
              "2024-12-29",
          },
        );

        expect(
          weeks[
            weeks.length
            - 1
          ],
        ).toEqual(
          {
            year:
              2025,

            week:
              52,

            startDate:
              "2025-12-21",
          },
        );
      },
    );

    it(
      "formata a semana de referência sem alterar a data por timezone",
      async () => {
        const series =
          await getPredictionMunicipalitySeries(
            "3537305",
          );

        const week =
          findPredictionReferenceWeek(
            series,
            1,
          );

        expect(
          week,
        ).not.toBeNull();

        expect(
          formatPredictionWeekLabel(
            week!,
          ),
        ).toBe(
          "SE 01 · 29/12/2024",
        );
      },
    );

    it(
      "mantém os quatro horizontes disponíveis até a SE49",
      async () => {
        const series =
          await getPredictionMunicipalitySeries(
            "3537305",
          );

        expect(
          getAvailableHorizonsForWeek(
            series,
            49,
          ),
        ).toEqual(
          [
            ...PREDICTION_HORIZONS,
          ],
        );
      },
    );

    it(
      "reduz progressivamente os horizontes disponíveis no fim de 2025",
      async () => {
        const series =
          await getPredictionMunicipalitySeries(
            "3537305",
          );

        expect(
          getAvailableHorizonsForWeek(
            series,
            50,
          ),
        ).toEqual(
          [
            "h1",
            "h2",
            "h3",
          ],
        );

        expect(
          getAvailableHorizonsForWeek(
            series,
            51,
          ),
        ).toEqual(
          [
            "h1",
            "h2",
          ],
        );

        expect(
          getAvailableHorizonsForWeek(
            series,
            52,
          ),
        ).toEqual(
          [
            "h1",
          ],
        );
      },
    );

    it(
      "extrai corretamente um ponto de previsão H1",
      async () => {
        const series =
          await getPredictionMunicipalitySeries(
            "3537305",
          );

        const point =
          getPredictionPoint(
            series,
            "h1",
            1,
          );

        expect(
          point,
        ).not.toBeNull();

        expect(
          point?.week,
        ).toBe(
          1,
        );

        expect(
          point?.threshold,
        ).toBeCloseTo(
          0.187687,
          6,
        );

        expect(
          point?.prediction,
        ).toBe(
          true,
        );

        expect(
          point?.target,
        ).toBe(
          true,
        );

        expect(
          point?.riskElevated,
        ).toBe(
          true,
        );
      },
    );

    it(
      "retorna ausência quando o horizonte não possui aquela semana",
      async () => {
        const series =
          await getPredictionMunicipalitySeries(
            "3537305",
          );

        expect(
          getPredictionPoint(
            series,
            "h4",
            50,
          ),
        ).toBeNull();
      },
    );

    it(
      "preserva a regra score maior ou igual ao threshold em toda a série de Penápolis",
      async () => {
        const series =
          await getPredictionMunicipalitySeries(
            "3537305",
          );

        for (
          const horizon
          of PREDICTION_HORIZONS
        ) {
          const weeks =
            series
              .horizontes[
                horizon
              ]
              .data
              .semana_epidemiologica;

          for (
            const week
            of weeks
          ) {
            const point =
              getPredictionPoint(
                series,
                horizon,
                week,
              );

            expect(
              point,
            ).not.toBeNull();

            expect(
              point
                ?.prediction,
            ).toBe(
              (
                point
                  ?.score
                ?? 0
              )
              >= (
                point
                  ?.threshold
                ?? Number.POSITIVE_INFINITY
              ),
            );
          }
        }
      },
    );
    it(
      "extrai a serie completa de cada horizonte preservando a cobertura retrospectiva",
      async () => {
        const series =
          await getPredictionMunicipalitySeries(
            "3537305",
          );

        const expectedLengths = {
          h1:
            52,

          h2:
            51,

          h3:
            50,

          h4:
            49,
        } as const;

        for (
          const horizon
          of PREDICTION_HORIZONS
        ) {
          const points =
            getPredictionHorizonPoints(
              series,
              horizon,
            );

          expect(
            points,
          ).toHaveLength(
            expectedLengths[
              horizon
            ],
          );

          expect(
            points.every(
              (point) =>
                point.horizon
                === horizon,
            ),
          ).toBe(
            true,
          );
        }
      },
    );

    it(
      "compara a previsao binaria com o estado futuro realmente observado",
      async () => {
        const series =
          await getPredictionMunicipalitySeries(
            "3537305",
          );

        const point =
          getPredictionPoint(
            series,
            "h1",
            1,
          );

        expect(
          point,
        ).not.toBeNull();

        expect(
          predictionMatchesObservedTarget(
            point!,
          ),
        ).toBe(
          point!.prediction
          === point!.target,
        );

        expect(
          predictionMatchesObservedTarget({
            ...point!,

            target:
              !point!.prediction,
          }),
        ).toBe(
          false,
        );
      },
    );
  },
);