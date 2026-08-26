import {
  describe,
  expect,
  it,
} from "vitest";

import {
  filterRegionalSeasonality,
  filterStatesByRegion,
  findRegionSummary,
  findStateSummary,
  getRegionalSeasonalityPeak,
  sortRegionsByAverageIncidence,
  sortStatesByAverageIncidence,
} from "@/lib/historical-territorial-utils";

import {
  getHistoricalSeasonalityRegional,
  getHistoricalSpatialRegions,
  getHistoricalSpatialStates,
} from "@/lib/serving/server";

describe(
  "historical territorial utils",
  () => {
    it(
      "localiza o resumo da região Sudeste",
      async () => {
        const contract =
          await getHistoricalSpatialRegions();

        const region =
          findRegionSummary(
            contract.data,
            "Sudeste",
          );

        expect(
          region,
        ).toBeDefined();

        expect(
          region?.regiao,
        ).toBe(
          "Sudeste",
        );

        expect(
          region?.anos_disponiveis,
        ).toBe(
          10,
        );
      },
    );

    it(
      "localiza São Paulo pelo código textual da UF",
      async () => {
        const contract =
          await getHistoricalSpatialStates();

        const state =
          findStateSummary(
            contract.data,
            "35",
          );

        expect(
          state,
        ).toBeDefined();

        expect(
          state?.nome_uf,
        ).toBe(
          "São Paulo",
        );

        expect(
          state?.regiao,
        ).toBe(
          "Sudeste",
        );
      },
    );

    it(
      "mantém somente as quatro UFs do Sudeste",
      async () => {
        const contract =
          await getHistoricalSpatialStates();

        const states =
          filterStatesByRegion(
            contract.data,
            "Sudeste",
          );

        expect(
          states,
        ).toHaveLength(
          4,
        );

        expect(
          new Set(
            states.map(
              (item) =>
                item.nome_uf,
            ),
          ),
        ).toEqual(
          new Set([
            "Espírito Santo",
            "Minas Gerais",
            "Rio de Janeiro",
            "São Paulo",
          ]),
        );
      },
    );

    it(
      "ordena regiões por incidência média anual em ordem decrescente",
      async () => {
        const contract =
          await getHistoricalSpatialRegions();

        const sorted =
          sortRegionsByAverageIncidence(
            contract.data,
          );

        for (
          let index = 1;
          index < sorted.length;
          index += 1
        ) {
          expect(
            sorted[
              index - 1
            ]
              .incidencia_media_anual_100mil,
          ).toBeGreaterThanOrEqual(
            sorted[
              index
            ]
              .incidencia_media_anual_100mil,
          );
        }
      },
    );

    it(
      "ordena UFs por incidência média anual em ordem decrescente",
      async () => {
        const contract =
          await getHistoricalSpatialStates();

        const sudeste =
          filterStatesByRegion(
            contract.data,
            "Sudeste",
          );

        const sorted =
          sortStatesByAverageIncidence(
            sudeste,
          );

        for (
          let index = 1;
          index < sorted.length;
          index += 1
        ) {
          expect(
            sorted[
              index - 1
            ]
              .incidencia_media_anual_100mil,
          ).toBeGreaterThanOrEqual(
            sorted[
              index
            ]
              .incidencia_media_anual_100mil,
          );
        }
      },
    );

    it(
      "extrai as 53 semanas de sazonalidade de uma região",
      async () => {
        const contract =
          await getHistoricalSeasonalityRegional();

        const data =
          filterRegionalSeasonality(
            contract.data,
            "Sudeste",
          );

        expect(
          data,
        ).toHaveLength(
          53,
        );

        expect(
          data.every(
            (item) =>
              item.regiao
              === "Sudeste",
          ),
        ).toBe(
          true,
        );

        expect(
          data[0]
            .semana_epidemiologica,
        ).toBe(
          1,
        );

        expect(
          data[
            data.length - 1
          ]
            .semana_epidemiologica,
        ).toBe(
          53,
        );
      },
    );

    it(
      "identifica o pico da incidência mediana regional",
      async () => {
        const contract =
          await getHistoricalSeasonalityRegional();

        const data =
          filterRegionalSeasonality(
            contract.data,
            "Sudeste",
          );

        const peak =
          getRegionalSeasonalityPeak(
            data,
          );

        expect(
          peak,
        ).not.toBeNull();

        expect(
          peak
            ?.semana_epidemiologica,
        ).toBeGreaterThanOrEqual(
          1,
        );

        expect(
          peak
            ?.semana_epidemiologica,
        ).toBeLessThanOrEqual(
          53,
        );
      },
    );
  },
);