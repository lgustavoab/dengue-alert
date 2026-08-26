import {
  describe,
  expect,
  it,
} from "vitest";

import {
  getPredictionMapIndex,
  getPredictionMapSlice,
  PredictionMapSelectionError,
  PredictionMapUnavailableError,
} from "@/lib/serving/prediction-map-server";

describe(
  "prediction map serving",
  () => {
    it(
      "mantém o índice retrospectivo completo de 2025",
      async () => {
        const index =
          await getPredictionMapIndex();

        expect(
          index.status,
        ).toBe(
          "APROVADO",
        );

        expect(
          index.avaliacao,
        ).toBe(
          "retrospectiva_2025",
        );

        expect(
          index.ano_epidemiologico,
        ).toBe(
          2025,
        );

        expect(
          index.municipios,
        ).toBe(
          5_569,
        );

        expect(
          index.predicoes,
        ).toBe(
          1_124_938,
        );

        expect(
          index.arquivos,
        ).toBe(
          202,
        );
      },
    );

    it(
      "preserva cobertura e thresholds H1-H4",
      async () => {
        const index =
          await getPredictionMapIndex();

        expect(
          index.horizontes.h1.semanas,
        ).toHaveLength(
          52,
        );

        expect(
          index.horizontes.h2.semanas,
        ).toHaveLength(
          51,
        );

        expect(
          index.horizontes.h3.semanas,
        ).toHaveLength(
          50,
        );

        expect(
          index.horizontes.h4.semanas,
        ).toHaveLength(
          49,
        );

        expect(
          index.horizontes.h1.threshold,
        ).toBeCloseTo(
          0.187687,
          6,
        );

        expect(
          index.horizontes.h2.threshold,
        ).toBeCloseTo(
          0.190783,
          6,
        );

        expect(
          index.horizontes.h3.threshold,
        ).toBeCloseTo(
          0.167991,
          6,
        );

        expect(
          index.horizontes.h4.threshold,
        ).toBeCloseTo(
          0.157138,
          6,
        );
      },
    );

    it(
      "carrega H1 SE20 com os 5569 municípios e 687 alertas",
      async () => {
        const contract =
          await getPredictionMapSlice(
            1,
            20,
          );

        expect(
          contract.horizonte,
        ).toBe(
          1,
        );

        expect(
          contract.semana_epidemiologica,
        ).toBe(
          20,
        );

        expect(
          contract.count,
        ).toBe(
          5_569,
        );

        expect(
          contract.data.codigo_ibge_7,
        ).toHaveLength(
          5_569,
        );

        expect(
          contract.data.score,
        ).toHaveLength(
          5_569,
        );

        expect(
          contract.data.predicao,
        ).toHaveLength(
          5_569,
        );

        expect(
          contract.data.predicao.filter(
            Boolean,
          ),
        ).toHaveLength(
          687,
        );
      },
    );

    it(
      "preserva as amostras H1 SE49 e H4 SE20 do benchmark",
      async () => {
        const [
          h1se49,
          h4se20,
        ] = await Promise.all(
          [
            getPredictionMapSlice(
              1,
              49,
            ),
            getPredictionMapSlice(
              4,
              20,
            ),
          ],
        );

        expect(
          h1se49.data.predicao.filter(
            Boolean,
          ),
        ).toHaveLength(
          1_013,
        );

        expect(
          h4se20.data.predicao.filter(
            Boolean,
          ),
        ).toHaveLength(
          1_223,
        );
      },
    );

    it(
      "rejeita combinação temporal indisponível",
      async () => {
        await expect(
          getPredictionMapSlice(
            4,
            50,
          ),
        ).rejects.toBeInstanceOf(
          PredictionMapUnavailableError,
        );
      },
    );

    it(
      "rejeita horizonte inválido",
      async () => {
        await expect(
          getPredictionMapSlice(
            5,
            20,
          ),
        ).rejects.toBeInstanceOf(
          PredictionMapSelectionError,
        );
      },
    );

    it(
      "rejeita semana epidemiológica inválida",
      async () => {
        await expect(
          getPredictionMapSlice(
            1,
            53,
          ),
        ).rejects.toBeInstanceOf(
          PredictionMapSelectionError,
        );
      },
    );
  },
);
