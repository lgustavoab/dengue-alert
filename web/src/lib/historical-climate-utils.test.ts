import {
  describe,
  expect,
  it,
} from "vitest";

import {
  CLIMATE_LAGS,
  CLIMATE_VARIABLES,
  filterClimateByVariable,
  filterRegionalClimate,
  filterRegionalClimateByVariable,
  getAvailableClimateLags,
  getClimateVariableLabel,
  getStrongestObservedMedianAssociation,
  isBoundaryLag,
} from "@/lib/historical-climate-utils";

import {
  getHistoricalClimateNationalLags,
  getHistoricalClimateRegionalLags,
} from "@/lib/serving/server";

describe(
  "historical climate utils",
  () => {
    it(
      "mantém 21 combinações nacionais de variável e lag",
      async () => {
        const contract =
          await getHistoricalClimateNationalLags();

        expect(
          contract.data,
        ).toHaveLength(
          21,
        );
      },
    );

    it(
      "mantém exatamente as três variáveis climáticas esperadas",
      async () => {
        const contract =
          await getHistoricalClimateNationalLags();

        const variables =
          new Set(
            contract.data.map(
              (item) =>
                item
                  .variavel_climatica,
            ),
          );

        expect(
          variables,
        ).toEqual(
          new Set(
            CLIMATE_VARIABLES,
          ),
        );
      },
    );

    it(
      "mantém os sete lags previstos no protocolo",
      async () => {
        const contract =
          await getHistoricalClimateNationalLags();

        expect(
          getAvailableClimateLags(
            contract.data,
          ),
        ).toEqual(
          [
            ...CLIMATE_LAGS,
          ],
        );
      },
    );

    it(
      "extrai sete observações nacionais para temperatura",
      async () => {
        const contract =
          await getHistoricalClimateNationalLags();

        const temperature =
          filterClimateByVariable(
            contract.data,
            "temperatura_media_c",
          );

        expect(
          temperature,
        ).toHaveLength(
          7,
        );

        expect(
          temperature.map(
            (item) =>
              item
                .lag_semanas,
          ),
        ).toEqual(
          [
            ...CLIMATE_LAGS,
          ],
        );
      },
    );

    it(
      "mantém 105 combinações no contrato regional",
      async () => {
        const contract =
          await getHistoricalClimateRegionalLags();

        expect(
          contract.data,
        ).toHaveLength(
          105,
        );
      },
    );

    it(
      "extrai 21 combinações climáticas do Sudeste",
      async () => {
        const contract =
          await getHistoricalClimateRegionalLags();

        const southeast =
          filterRegionalClimate(
            contract.data,
            "Sudeste",
          );

        expect(
          southeast,
        ).toHaveLength(
          21,
        );

        expect(
          southeast.every(
            (item) =>
              item.regiao
              === "Sudeste",
          ),
        ).toBe(
          true,
        );
      },
    );

    it(
      "extrai sete lags de precipitação no Sudeste",
      async () => {
        const contract =
          await getHistoricalClimateRegionalLags();

        const precipitation =
          filterRegionalClimateByVariable(
            contract.data,
            "Sudeste",
            "precipitacao_total_mm",
          );

        expect(
          precipitation,
        ).toHaveLength(
          7,
        );

        expect(
          precipitation.map(
            (item) =>
              item
                .lag_semanas,
          ),
        ).toEqual(
          [
            ...CLIMATE_LAGS,
          ],
        );
      },
    );

    it(
      "identifica apenas a maior associação observada sem afirmar lag ótimo",
      async () => {
        const contract =
          await getHistoricalClimateNationalLags();

        const humidity =
          filterClimateByVariable(
            contract.data,
            "umidade_relativa_media_pct",
          );

        const strongest =
          getStrongestObservedMedianAssociation(
            humidity,
          );

        expect(
          strongest,
        ).not.toBeNull();

        const maximumAbsoluteCorrelation =
          Math.max(
            ...humidity.map(
              (item) =>
                Math.abs(
                  item
                    .correlacao_mediana,
                ),
            ),
          );

        expect(
          Math.abs(
            strongest
              ?.correlacao_mediana
              ?? 0,
          ),
        ).toBe(
          maximumAbsoluteCorrelation,
        );
      },
    );

    it(
      "reconhece lag 8 como borda da janela analisada",
      () => {
        expect(
          isBoundaryLag(
            8,
          ),
        ).toBe(
          true,
        );

        expect(
          isBoundaryLag(
            4,
          ),
        ).toBe(
          false,
        );
      },
    );

    it(
      "traduz os identificadores técnicos das variáveis",
      () => {
        expect(
          getClimateVariableLabel(
            "temperatura_media_c",
          ),
        ).toBe(
          "Temperatura média",
        );

        expect(
          getClimateVariableLabel(
            "umidade_relativa_media_pct",
          ),
        ).toBe(
          "Umidade relativa média",
        );

        expect(
          getClimateVariableLabel(
            "precipitacao_total_mm",
          ),
        ).toBe(
          "Precipitação total",
        );
      },
    );
  },
);