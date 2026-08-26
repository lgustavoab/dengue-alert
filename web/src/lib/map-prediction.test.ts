import {
  readFile,
} from "node:fs/promises";

import path from "node:path";

import {
  describe,
  expect,
  it,
} from "vitest";

import {
  parseMunicipalityTopology,
} from "@/lib/map-geography";

import {
  joinMunicipalityPredictions,
} from "@/lib/map-prediction";

import {
  buildMunicipalitySvgPaths,
} from "@/lib/map-rendering";

import type {
  PredictionMapContract,
} from "@/lib/serving/prediction-map-types";

async function loadOfficialPaths() {
  const projectRoot =
    path.resolve(
      process.cwd(),
      "..",
    );

  const topologyPath =
    path.join(
      projectRoot,
      "data",
      "serving",
      "geography",
      "municipalities.topojson",
    );

  const topology =
    JSON.parse(
      await readFile(
        topologyPath,
        "utf-8",
      ),
    ) as unknown;

  const geography =
    parseMunicipalityTopology(
      topology,
    );

  return buildMunicipalitySvgPaths(
    geography.featureCollection,
  );
}

async function loadOfficialPrediction(): Promise<PredictionMapContract> {
  const projectRoot =
    path.resolve(
      process.cwd(),
      "..",
    );

  const predictionPath =
    path.join(
      projectRoot,
      "data",
      "serving",
      "prediction",
      "map",
      "h1",
      "se49.json",
    );

  return JSON.parse(
    await readFile(
      predictionPath,
      "utf-8",
    ),
  ) as PredictionMapContract;
}

describe(
  "map prediction join",
  () => {
    it(
      "associa a malha oficial à predição oficial SE49 H1",
      async () => {
        const [
          paths,
          prediction,
        ] =
          await Promise.all([
            loadOfficialPaths(),
            loadOfficialPrediction(),
          ]);

        const result =
          joinMunicipalityPredictions(
            paths,
            prediction,
          );

        expect(
          result.municipalities,
        ).toHaveLength(
          5_571,
        );

        expect(
          result.summary,
        ).toEqual({
          totalTerritories:
            5_571,

          evaluatedMunicipalities:
            5_569,

          alertCount:
            1_013,

          noAlertCount:
            4_556,

          withoutEvaluationCount:
            2,
        });
      },
      30_000,
    );

    it(
      "preserva exatamente o predicao oficial sem derivá-lo do score",
      async () => {
        const [
          paths,
          prediction,
        ] =
          await Promise.all([
            loadOfficialPaths(),
            loadOfficialPrediction(),
          ]);

        const result =
          joinMunicipalityPredictions(
            paths,
            prediction,
          );

        const joinedById =
          new Map(
            result.municipalities.map(
              (municipality) => [
                municipality.codigoIbge7,
                municipality,
              ],
            ),
          );

        for (
          let position = 0;
          position < prediction.count;
          position += 1
        ) {
          const codigoIbge7 =
            String(
              prediction.data.codigo_ibge_7[position],
            ).padStart(
              7,
              "0",
            );

          const joined =
            joinedById.get(
              codigoIbge7,
            );

          expect(
            joined,
          ).toBeDefined();

          expect(
            joined?.predicao,
          ).toBe(
            prediction.data.predicao[position],
          );

          expect(
            joined?.score,
          ).toBe(
            prediction.data.score[position],
          );
        }
      },
      30_000,
    );

    it(
      "mantém os dois territórios sem predição fora de SEM ALERTA",
      async () => {
        const [
          paths,
          prediction,
        ] =
          await Promise.all([
            loadOfficialPaths(),
            loadOfficialPrediction(),
          ]);

        const result =
          joinMunicipalityPredictions(
            paths,
            prediction,
          );

        const withoutEvaluation =
          result.municipalities.filter(
            (municipality) =>
              municipality.status
              === "sem_avaliacao",
          );

        expect(
          withoutEvaluation,
        ).toHaveLength(
          2,
        );

        for (
          const municipality
          of withoutEvaluation
        ) {
          expect(
            municipality.predicao,
          ).toBeNull();

          expect(
            municipality.score,
          ).toBeNull();
        }
      },
      30_000,
    );

    it(
      "faz o fechamento exato entre ALERTA, SEM ALERTA e sem avaliação",
      async () => {
        const [
          paths,
          prediction,
        ] =
          await Promise.all([
            loadOfficialPaths(),
            loadOfficialPrediction(),
          ]);

        const result =
          joinMunicipalityPredictions(
            paths,
            prediction,
          );

        const statusCounts =
          result.municipalities.reduce(
            (
              counts,
              municipality,
            ) => {
              counts[
                municipality.status
              ] +=
                1;

              return counts;
            },
            {
              alerta:
                0,

              sem_alerta:
                0,

              sem_avaliacao:
                0,
            },
          );

        expect(
          statusCounts,
        ).toEqual({
          alerta:
            1_013,

          sem_alerta:
            4_556,

          sem_avaliacao:
            2,
        });

        expect(
          statusCounts.alerta
          + statusCounts.sem_alerta
          + statusCounts.sem_avaliacao,
        ).toBe(
          5_571,
        );
      },
      30_000,
    );
  },
);