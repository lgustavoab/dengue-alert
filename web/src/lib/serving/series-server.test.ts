import {
  describe,
  expect,
  it,
} from "vitest";

import {
  getHistoricalMunicipalitySeries,
  getPredictionMunicipalitySeries,
  MunicipalitySeriesNotFoundError,
} from "@/lib/serving/series-server";

describe(
  "historical municipality series",
  () => {
    it(
      "carrega Penápolis com 522 semanas",
      async () => {
        const series =
          await getHistoricalMunicipalitySeries(
            "3537305",
          );

        expect(
          series.schema_version,
        ).toBe(
          "1.0",
        );

        expect(
          series.codigo_ibge_7,
        ).toBe(
          "3537305",
        );

        expect(
          series.count,
        ).toBe(
          522,
        );

        expect(
          series.data
            .ano_epidemiologico,
        ).toHaveLength(
          522,
        );

        expect(
          series.data
            .semana_epidemiologica,
        ).toHaveLength(
          522,
        );

        expect(
          series.data
            .casos_provaveis,
        ).toHaveLength(
          522,
        );

        expect(
          series.data
            .incidencia_100mil,
        ).toHaveLength(
          522,
        );
      },
    );

    it(
      "preserva os primeiros registros conhecidos de Penápolis",
      async () => {
        const series =
          await getHistoricalMunicipalitySeries(
            "3537305",
          );

        expect(
          series.data
            .ano_epidemiologico
            .slice(
              0,
              3,
            ),
        ).toEqual(
          [
            2016,
            2016,
            2016,
          ],
        );

        expect(
          series.data
            .semana_epidemiologica
            .slice(
              0,
              3,
            ),
        ).toEqual(
          [
            1,
            2,
            3,
          ],
        );

        expect(
          series.data
            .casos_provaveis
            .slice(
              0,
              3,
            ),
        ).toEqual(
          [
            3,
            3,
            0,
          ],
        );
      },
    );

    it(
      "carrega Boa Esperança do Norte somente em 2025",
      async () => {
        const series =
          await getHistoricalMunicipalitySeries(
            "5101837",
          );

        expect(
          series.count,
        ).toBe(
          53,
        );

        expect(
          new Set(
            series.data
              .ano_epidemiologico,
          ),
        ).toEqual(
          new Set([
            2025,
          ]),
        );
      },
    );

    it(
      "mantém Fernando de Noronha com 522 semanas epidemiológicas",
      async () => {
        const series =
          await getHistoricalMunicipalitySeries(
            "2605459",
          );

        expect(
          series.count,
        ).toBe(
          522,
        );
      },
    );

    it(
      "rejeita código IBGE estruturalmente inválido",
      async () => {
        await expect(
          getHistoricalMunicipalitySeries(
            "abc",
          ),
        ).rejects.toBeInstanceOf(
          TypeError,
        );
      },
    );

    it(
      "rejeita código IBGE com quantidade incorreta de dígitos",
      async () => {
        await expect(
          getHistoricalMunicipalitySeries(
            "353730",
          ),
        ).rejects.toBeInstanceOf(
          TypeError,
        );
      },
    );
  },
);

describe(
  "prediction municipality series",
  () => {
    it(
      "carrega Penápolis com 202 predições retrospectivas",
      async () => {
        const series =
          await getPredictionMunicipalitySeries(
            "3537305",
          );

        expect(
          series.codigo_ibge_7,
        ).toBe(
          "3537305",
        );

        expect(
          series.count,
        ).toBe(
          202,
        );

        expect(
          series.horizontes
            .h1.count,
        ).toBe(
          52,
        );

        expect(
          series.horizontes
            .h2.count,
        ).toBe(
          51,
        );

        expect(
          series.horizontes
            .h3.count,
        ).toBe(
          50,
        );

        expect(
          series.horizontes
            .h4.count,
        ).toBe(
          49,
        );
      },
    );

    it(
      "preserva os thresholds congelados",
      async () => {
        const series =
          await getPredictionMunicipalitySeries(
            "3537305",
          );

        expect(
          series.horizontes
            .h1.threshold,
        ).toBe(
          0.187687,
        );

        expect(
          series.horizontes
            .h2.threshold,
        ).toBe(
          0.190783,
        );

        expect(
          series.horizontes
            .h3.threshold,
        ).toBe(
          0.167991,
        );

        expect(
          series.horizontes
            .h4.threshold,
        ).toBe(
          0.157138,
        );
      },
    );

    it(
      "não encontra predição para Boa Esperança do Norte",
      async () => {
        await expect(
          getPredictionMunicipalitySeries(
            "5101837",
          ),
        ).rejects.toBeInstanceOf(
          MunicipalitySeriesNotFoundError,
        );
      },
    );

    it(
      "não encontra predição para Fernando de Noronha",
      async () => {
        await expect(
          getPredictionMunicipalitySeries(
            "2605459",
          ),
        ).rejects.toBeInstanceOf(
          MunicipalitySeriesNotFoundError,
        );
      },
    );

    it(
      "rejeita código preditivo estruturalmente inválido",
      async () => {
        await expect(
          getPredictionMunicipalitySeries(
            "../test",
          ),
        ).rejects.toBeInstanceOf(
          TypeError,
        );
      },
    );
  },
);