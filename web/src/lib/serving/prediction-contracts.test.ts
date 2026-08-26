import {
  describe,
  expect,
  it,
} from "vitest";

import {
  getPredictionByHorizon,
  getPredictionModel,
  getPredictionMunicipalityIndex,
  getPredictionOverview,
} from "@/lib/serving/server";

describe(
  "prediction serving contracts",
  () => {
    it(
      "mantém o overview retrospectivo de 2025 aprovado",
      async () => {
        const contract =
          await getPredictionOverview();

        expect(
          contract.status,
        ).toBe(
          "APROVADO",
        );

        expect(
          contract.avaliacao,
        ).toBe(
          "teste_final_retrospectivo_2025",
        );

        expect(
          contract.ano,
        ).toBe(
          2025,
        );

        expect(
          contract.linhas,
        ).toBe(
          1_124_938,
        );

        expect(
          contract.municipios,
        ).toBe(
          5_569,
        );
      },
    );

    it(
      "preserva os thresholds congelados dos quatro horizontes",
      async () => {
        const contract =
          await getPredictionOverview();

        expect(
          contract
            .horizontes
            .h1
            .threshold,
        ).toBeCloseTo(
          0.187687,
          6,
        );

        expect(
          contract
            .horizontes
            .h2
            .threshold,
        ).toBeCloseTo(
          0.190783,
          6,
        );

        expect(
          contract
            .horizontes
            .h3
            .threshold,
        ).toBeCloseTo(
          0.167991,
          6,
        );

        expect(
          contract
            .horizontes
            .h4
            .threshold,
        ).toBeCloseTo(
          0.157138,
          6,
        );
      },
    );

    it(
      "mantém 52, 51, 50 e 49 semanas de origem nos horizontes",
      async () => {
        const contract =
          await getPredictionOverview();

        expect(
          contract
            .horizontes
            .h1
            .semanas_origem,
        ).toBe(
          52,
        );

        expect(
          contract
            .horizontes
            .h2
            .semanas_origem,
        ).toBe(
          51,
        );

        expect(
          contract
            .horizontes
            .h3
            .semanas_origem,
        ).toBe(
          50,
        );

        expect(
          contract
            .horizontes
            .h4
            .semanas_origem,
        ).toBe(
          49,
        );
      },
    );

    it(
      "mantém o modelo final retrospectivo e sem calibração adotada",
      async () => {
        const contract =
          await getPredictionModel();

        expect(
          contract.retrospectivo,
        ).toBe(
          true,
        );

        expect(
          contract
            .ano_referencia,
        ).toBe(
          2025,
        );

        expect(
          contract
            .modelo
            .algoritmo,
        ).toBe(
          "HistGradientBoostingClassifier",
        );

        expect(
          contract
            .modelo
            .probabilidades,
        ).toBe(
          "raw",
        );

        expect(
          contract
            .protocolo
            .thresholds_congelados,
        ).toBe(
          true,
        );

        expect(
          contract
            .protocolo
            .teste_final_utilizado_na_selecao,
        ).toBe(
          false,
        );
      },
    );

    it(
      "mantém a semântica oficial de score, previsão e target",
      async () => {
        const contract =
          await getPredictionModel();

        expect(
          contract
            .semantica
            .predicao,
        ).toBe(
          "score >= threshold",
        );

        expect(
          contract
            .semantica
            .score,
        ).toContain(
          "probabilidade",
        );

        expect(
          contract
            .semantica
            .risco_elevado,
        ).toContain(
          "semana de origem",
        );

        expect(
          contract
            .semantica
            .target,
        ).toContain(
          "estado futuro observado",
        );
      },
    );

    it(
      "mantém explícita a restrição contra faixas artificiais de risco",
      async () => {
        const contract =
          await getPredictionModel();

        expect(
          contract
            .restricoes_interpretacao
            .some(
              (item) =>
                item.includes(
                  "baixo/moderado/alto/crítico",
                ),
            ),
        ).toBe(
          true,
        );
      },
    );

    it(
      "carrega a avaliação por horizonte aprovada",
      async () => {
        const contract =
          await getPredictionByHorizon();

        expect(
          contract.status,
        ).toBe(
          "APROVADO",
        );

        expect(
          contract.avaliacao,
        ).toBe(
          "teste_final_retrospectivo_2025",
        );

        expect(
          contract
            .horizontes
            .h1
            .horizonte,
        ).toBe(
          1,
        );

        expect(
          contract
            .horizontes
            .h4
            .horizonte,
        ).toBe(
          4,
        );
      },
    );

    it(
      "preserva as métricas gerais do modelo final em H1",
      async () => {
        const contract =
          await getPredictionByHorizon();

        const metrics =
          contract
            .horizontes
            .h1
            .modelo_final
            .geral;

        expect(
          metrics
            .observacoes,
        ).toBe(
          289_588,
        );

        expect(
          metrics
            .pr_auc_average_precision,
        ).toBeCloseTo(
          0.9220944722,
          8,
        );

        expect(
          metrics
            .roc_auc,
        ).toBeCloseTo(
          0.9764527270,
          8,
        );

        expect(
          metrics
            .matriz_confusao
            .tp,
        ).toBe(
          32_855,
        );
      },
    );

    it(
      "preserva os alertas antecipados do modelo em H1 e H4",
      async () => {
        const contract =
          await getPredictionByHorizon();

        expect(
          contract
            .horizontes
            .h1
            .modelo_final
            .early_warning
            .alertas,
        ).toBe(
          10_440,
        );

        expect(
          contract
            .horizontes
            .h4
            .modelo_final
            .early_warning
            .alertas,
        ).toBe(
          36_367,
        );
      },
    );

    it(
      "confirma que a persistência não antecipa novas entradas em risco",
      async () => {
        const contract =
          await getPredictionByHorizon();

        for (
          const horizon
          of [
            contract
              .horizontes
              .h1,
            contract
              .horizontes
              .h2,
            contract
              .horizontes
              .h3,
            contract
              .horizontes
              .h4,
          ]
        ) {
          expect(
            horizon
              .baseline_persistencia
              .early_warning
              .recall,
          ).toBe(
            0,
          );

          expect(
            horizon
              .baseline_persistencia
              .early_warning
              .f1,
          ).toBe(
            0,
          );
        }
      },
    );

    it(
      "mantém índice de 5569 municípios com previsão",
      async () => {
        const contract =
          await getPredictionMunicipalityIndex();

        expect(
          contract.count,
        ).toBe(
          5_569,
        );

        expect(
          contract.items,
        ).toHaveLength(
          5_569,
        );
      },
    );

    it(
      "mantém Penápolis disponível nos quatro horizontes",
      async () => {
        const contract =
          await getPredictionMunicipalityIndex();

        const penapolis =
          contract.items.find(
            (item) =>
              item.codigo_ibge_7
              === "3537305",
          );

        expect(
          penapolis,
        ).toBeDefined();

        expect(
          penapolis
            ?.horizontes,
        ).toEqual(
          {
            h1: 52,
            h2: 51,
            h3: 50,
            h4: 49,
          },
        );
      },
    );
  },
);