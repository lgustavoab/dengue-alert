import {
  describe,
  expect,
  it,
} from "vitest";

import {
  countMunicipalitiesWithRecurrence,
  countMunicipalitiesWithRisk,
  filterRiskMunicipalities,
  filterRiskWeeklyByScope,
  findMunicipalityRiskSummary,
  getAverageRiskProportion,
  getRiskWeeklyPeak,
  sortRiskMunicipalitiesByProportion,
} from "@/lib/historical-risk-utils";

import {
  getHistoricalRiskMunicipalities,
  getHistoricalRiskWeekly,
} from "@/lib/serving/server";

describe(
  "historical risk utils",
  () => {
    it(
      "extrai as 418 semanas nacionais de risco",
      async () => {
        const contract =
          await getHistoricalRiskWeekly();

        const rows =
          filterRiskWeeklyByScope(
            contract.data,
            "",
          );

        expect(
          rows,
        ).toHaveLength(
          418,
        );

        expect(
          rows.every(
            (item) =>
              item.escala
                === "nacional"
              && item.grupo
                === "Brasil",
          ),
        ).toBe(
          true,
        );
      },
    );

    it(
      "extrai as 418 semanas de risco do Sudeste",
      async () => {
        const contract =
          await getHistoricalRiskWeekly();

        const rows =
          filterRiskWeeklyByScope(
            contract.data,
            "Sudeste",
          );

        expect(
          rows,
        ).toHaveLength(
          418,
        );

        expect(
          rows.every(
            (item) =>
              item.escala
                === "regional"
              && item.grupo
                === "Sudeste",
          ),
        ).toBe(
          true,
        );
      },
    );

    it(
      "identifica o pico nacional de municípios simultaneamente em risco",
      async () => {
        const contract =
          await getHistoricalRiskWeekly();

        const rows =
          filterRiskWeeklyByScope(
            contract.data,
            "",
          );

        const peak =
          getRiskWeeklyPeak(
            rows,
          );

        expect(
          peak,
        ).not.toBeNull();

        expect(
          peak
            ?.proporcao_unidades_em_risco,
        ).toBeGreaterThan(
          0,
        );

        expect(
          peak
            ?.unidades_em_risco,
        ).toBeGreaterThan(
          0,
        );
      },
    );

    it(
      "localiza Penápolis no resumo municipal de risco",
      async () => {
        const contract =
          await getHistoricalRiskMunicipalities();

        const penapolis =
          findMunicipalityRiskSummary(
            contract.data,
            "3537305",
          );

        expect(
          penapolis,
        ).toBeDefined();

        expect(
          penapolis
            ?.nome_municipio,
        ).toBe(
          "Penápolis",
        );

        expect(
          penapolis
            ?.nome_uf,
        ).toBe(
          "São Paulo",
        );
      },
    );

    it(
      "não encontra Boa Esperança do Norte no resumo de risco",
      async () => {
        const contract =
          await getHistoricalRiskMunicipalities();

        expect(
          findMunicipalityRiskSummary(
            contract.data,
            "5101837",
          ),
        ).toBeNull();
      },
    );

    it(
      "não encontra Fernando de Noronha no resumo de risco",
      async () => {
        const contract =
          await getHistoricalRiskMunicipalities();

        expect(
          findMunicipalityRiskSummary(
            contract.data,
            "2605459",
          ),
        ).toBeNull();
      },
    );

    it(
      "filtra municípios de São Paulo",
      async () => {
        const contract =
          await getHistoricalRiskMunicipalities();

        const rows =
          filterRiskMunicipalities(
            contract.data,
            {
              ufCode:
                "35",
            },
          );

        expect(
          rows.length,
        ).toBeGreaterThan(
          0,
        );

        expect(
          rows.every(
            (item) =>
              item.codigo_uf_ibge
              === "35",
          ),
        ).toBe(
          true,
        );
      },
    );

    it(
      "filtra municípios do Sudeste",
      async () => {
        const contract =
          await getHistoricalRiskMunicipalities();

        const rows =
          filterRiskMunicipalities(
            contract.data,
            {
              region:
                "Sudeste",
            },
          );

        expect(
          rows.length,
        ).toBeGreaterThan(
          0,
        );

        expect(
          rows.every(
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
      "ordena municípios pela proporção de semanas em risco",
      async () => {
        const contract =
          await getHistoricalRiskMunicipalities();

        const rows =
          filterRiskMunicipalities(
            contract.data,
            {
              ufCode:
                "35",
            },
          );

        const sorted =
          sortRiskMunicipalitiesByProportion(
            rows,
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
              .proporcao_semanas_risco,
          ).toBeGreaterThanOrEqual(
            sorted[
              index
            ]
              .proporcao_semanas_risco,
          );
        }
      },
    );

    it(
      "contabiliza municípios que apresentaram risco",
      async () => {
        const contract =
          await getHistoricalRiskMunicipalities();

        const count =
          countMunicipalitiesWithRisk(
            contract.data,
          );

        expect(
          count,
        ).toBeGreaterThan(
          0,
        );

        expect(
          count,
        ).toBeLessThanOrEqual(
          5569,
        );
      },
    );

    it(
      "contabiliza recorrência multianual",
      async () => {
        const contract =
          await getHistoricalRiskMunicipalities();

        const count =
          countMunicipalitiesWithRecurrence(
            contract.data,
          );

        expect(
          count,
        ).toBeGreaterThan(
          0,
        );

        expect(
          count,
        ).toBeLessThanOrEqual(
          5569,
        );
      },
    );

    it(
      "calcula proporção média de semanas em risco",
      async () => {
        const contract =
          await getHistoricalRiskMunicipalities();

        const average =
          getAverageRiskProportion(
            contract.data,
          );

        expect(
          average,
        ).toBeGreaterThanOrEqual(
          0,
        );

        expect(
          average,
        ).toBeLessThanOrEqual(
          1,
        );
      },
    );
  },
);