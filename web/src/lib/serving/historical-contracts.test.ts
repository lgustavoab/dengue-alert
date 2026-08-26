import {
  describe,
  expect,
  it,
} from "vitest";

import {
  getHistoricalClimateNationalLags,
  getHistoricalClimateRegionalLags,
  getHistoricalRiskEpisodeDuration,
  getHistoricalRiskMunicipalities,
  getHistoricalRiskWeekly,
  getHistoricalSeasonalityNational,
  getHistoricalSeasonalityRegional,
  getHistoricalSpatialMunicipalities,
  getHistoricalSpatialRegions,
  getHistoricalSpatialStates,
  getHistoricalWeekly,
} from "@/lib/serving/server";

const expectedRegions =
  new Set([
    "Centro-Oeste",
    "Nordeste",
    "Norte",
    "Sudeste",
    "Sul",
  ]);

const expectedClimateVariables =
  new Set([
    "precipitacao_total_mm",
    "temperatura_media_c",
    "umidade_relativa_media_pct",
  ]);

const expectedClimateLags =
  new Set([
    0,
    1,
    2,
    3,
    4,
    6,
    8,
  ]);

describe(
  "historical serving contracts",
  () => {
    it(
      "carrega as 522 semanas do panorama epidemiológico nacional",
      async () => {
        const contract =
          await getHistoricalWeekly();

        expect(
          contract.count,
        ).toBe(
          522,
        );

        expect(
          contract.data,
        ).toHaveLength(
          522,
        );

        expect(
          contract.data[0],
        ).toMatchObject({
          ano_epidemiologico:
            2016,

          semana_epidemiologica:
            1,

          data_inicio_semana:
            "2016-01-03",

          data_fim_semana:
            "2016-01-09",

          casos_provaveis:
            42676,
        });
      },
    );

    it(
      "carrega as 53 semanas da sazonalidade nacional",
      async () => {
        const contract =
          await getHistoricalSeasonalityNational();

        expect(
          contract.count,
        ).toBe(
          53,
        );

        expect(
          contract.data.map(
            (item) =>
              item
                .semana_epidemiologica,
          ),
        ).toEqual(
          Array.from(
            {
              length:
                53,
            },
            (
              _,
              index,
            ) =>
              index + 1,
          ),
        );
      },
    );

    it(
      "carrega a sazonalidade das cinco regiões em 265 registros",
      async () => {
        const contract =
          await getHistoricalSeasonalityRegional();

        expect(
          contract.count,
        ).toBe(
          265,
        );

        const regions =
          new Set(
            contract
              .data
              .map(
                (item) =>
                  item.regiao,
              ),
          );

        expect(
          regions,
        ).toEqual(
          expectedRegions,
        );

        for (
          const region
          of expectedRegions
        ) {
          const rows =
            contract
              .data
              .filter(
                (item) =>
                  item.regiao
                  === region,
              );

          expect(
            rows,
          ).toHaveLength(
            53,
          );
        }
      },
    );

    it(
      "carrega os cinco resumos espaciais regionais",
      async () => {
        const contract =
          await getHistoricalSpatialRegions();

        expect(
          contract.count,
        ).toBe(
          5,
        );

        expect(
          new Set(
            contract
              .data
              .map(
                (item) =>
                  item.regiao,
              ),
          ),
        ).toEqual(
          expectedRegions,
        );
      },
    );

    it(
      "carrega as 27 UFs e preserva seus códigos como strings",
      async () => {
        const contract =
          await getHistoricalSpatialStates();

        expect(
          contract.count,
        ).toBe(
          27,
        );

        expect(
          contract.data,
        ).toHaveLength(
          27,
        );

        expect(
          contract
            .data
            .every(
              (item) =>
                /^\d{2}$/.test(
                  item
                    .codigo_uf_ibge,
                ),
            ),
        ).toBe(
          true,
        );
      },
    );

    it(
      "lê corretamente nomes UTF-8 das UFs",
      async () => {
        const contract =
          await getHistoricalSpatialStates();

        const rondonia =
          contract
            .data
            .find(
              (item) =>
                item
                  .codigo_uf_ibge
                === "11",
            );

        expect(
          rondonia,
        ).toBeDefined();

        expect(
          rondonia
            ?.nome_uf,
        ).toBe(
          "Rondônia",
        );
      },
    );

    it(
      "carrega os 5.571 resumos espaciais municipais",
      async () => {
        const contract =
          await getHistoricalSpatialMunicipalities();

        expect(
          contract.count,
        ).toBe(
          5571,
        );

        expect(
          new Set(
            contract
              .data
              .map(
                (item) =>
                  item
                    .codigo_ibge_7,
              ),
          ).size,
        ).toBe(
          5571,
        );
      },
    );

    it(
      "carrega a dinâmica de risco de 5.569 municípios elegíveis",
      async () => {
        const contract =
          await getHistoricalRiskMunicipalities();

        expect(
          contract.count,
        ).toBe(
          5569,
        );

        expect(
          contract.data,
        ).toHaveLength(
          5569,
        );
      },
    );

    it(
      "não inclui Boa Esperança do Norte nem Fernando de Noronha na dinâmica municipal de risco",
      async () => {
        const contract =
          await getHistoricalRiskMunicipalities();

        const codes =
          new Set(
            contract
              .data
              .map(
                (item) =>
                  item
                    .codigo_ibge_7,
              ),
          );

        expect(
          codes.has(
            "5101837",
          ),
        ).toBe(
          false,
        );

        expect(
          codes.has(
            "2605459",
          ),
        ).toBe(
          false,
        );
      },
    );

    it(
      "carrega 2.508 observações da dinâmica semanal de risco",
      async () => {
        const contract =
          await getHistoricalRiskWeekly();

        expect(
          contract.count,
        ).toBe(
          2508,
        );

        expect(
          contract.data,
        ).toHaveLength(
          2508,
        );
      },
    );

    it(
      "mantém 418 semanas de risco para Brasil e cada região",
      async () => {
        const contract =
          await getHistoricalRiskWeekly();

        const expectedGroups =
          [
            {
              escala:
                "nacional",
              grupo:
                "Brasil",
            },
            ...[
              ...expectedRegions,
            ].map(
              (region) => ({
                escala:
                  "regional",
                grupo:
                  region,
              }),
            ),
          ];

        for (
          const expected
          of expectedGroups
        ) {
          const rows =
            contract
              .data
              .filter(
                (item) =>
                  item.escala
                    === expected.escala
                  && item.grupo
                    === expected.grupo,
              );

          expect(
            rows,
          ).toHaveLength(
            418,
          );
        }
      },
    );

    it(
      "preserva o resumo validado da duração dos episódios de risco",
      async () => {
        const contract =
          await getHistoricalRiskEpisodeDuration();

        expect(
          contract.summary,
        ).toMatchObject({
          quantidade_episodios:
            54269,

          semanas_risco:
            414678,

          minimo:
            1,

          p25:
            3,

          mediana:
            4,

          p75:
            9,

          p90:
            19,

          p95:
            26,

          p99:
            41,

          maximo:
            110,
        });
      },
    );

    it(
      "faz a distribuição de duração somar os 54.269 episódios",
      async () => {
        const contract =
          await getHistoricalRiskEpisodeDuration();

        const total =
          contract
            .distribution
            .reduce(
              (
                accumulator,
                item,
              ) =>
                accumulator
                + item.episodios,
              0,
            );

        expect(
          total,
        ).toBe(
          contract
            .summary
            .quantidade_episodios,
        );
      },
    );

    it(
      "carrega 21 combinações nacionais de variável climática e lag",
      async () => {
        const contract =
          await getHistoricalClimateNationalLags();

        expect(
          contract.count,
        ).toBe(
          21,
        );

        expect(
          new Set(
            contract
              .data
              .map(
                (item) =>
                  item
                    .variavel_climatica,
              ),
          ),
        ).toEqual(
          expectedClimateVariables,
        );

        expect(
          new Set(
            contract
              .data
              .map(
                (item) =>
                  item
                    .lag_semanas,
              ),
          ),
        ).toEqual(
          expectedClimateLags,
        );
      },
    );

    it(
      "mantém sete lags por variável climática no contrato nacional",
      async () => {
        const contract =
          await getHistoricalClimateNationalLags();

        for (
          const variable
          of expectedClimateVariables
        ) {
          const rows =
            contract
              .data
              .filter(
                (item) =>
                  item
                    .variavel_climatica
                  === variable,
              );

          expect(
            rows,
          ).toHaveLength(
            7,
          );
        }
      },
    );

    it(
      "carrega 105 combinações climáticas regionais",
      async () => {
        const contract =
          await getHistoricalClimateRegionalLags();

        expect(
          contract.count,
        ).toBe(
          105,
        );

        expect(
          new Set(
            contract
              .data
              .map(
                (item) =>
                  item.regiao,
              ),
          ),
        ).toEqual(
          expectedRegions,
        );
      },
    );

    it(
      "mantém 21 combinações climáticas em cada região",
      async () => {
        const contract =
          await getHistoricalClimateRegionalLags();

        for (
          const region
          of expectedRegions
        ) {
          const rows =
            contract
              .data
              .filter(
                (item) =>
                  item.regiao
                  === region,
              );

          expect(
            rows,
          ).toHaveLength(
            21,
          );

          expect(
            new Set(
              rows.map(
                (item) =>
                  item
                    .variavel_climatica,
              ),
            ),
          ).toEqual(
            expectedClimateVariables,
          );
        }
      },
    );
  },
);