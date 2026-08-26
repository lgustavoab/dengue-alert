import type {
  MunicipalitySvgPath,
} from "@/lib/map-rendering";

import type {
  PredictionMapContract,
} from "@/lib/serving/prediction-map-types";

export type MunicipalityPredictionStatus =
  | "alerta"
  | "sem_alerta"
  | "sem_avaliacao";

export type MunicipalityMapDatum = {
  codigoIbge7: string;
  d: string;
  status: MunicipalityPredictionStatus;
  score: number | null;
  predicao: boolean | null;
};

export type MunicipalityMapJoinSummary = {
  totalTerritories: number;
  evaluatedMunicipalities: number;
  alertCount: number;
  noAlertCount: number;
  withoutEvaluationCount: number;
};

export type MunicipalityMapJoinResult = {
  municipalities: MunicipalityMapDatum[];
  summary: MunicipalityMapJoinSummary;
};

type PredictionRecord = {
  score: number;
  predicao: boolean;
};

function validatePredictionContract(
  prediction: PredictionMapContract,
): void {
  const {
    codigo_ibge_7: municipalityIds,
    score: scores,
    predicao: predictions,
  } = prediction.data;

  if (
    prediction.count !== 5_569
    || municipalityIds.length !== prediction.count
    || scores.length !== prediction.count
    || predictions.length !== prediction.count
  ) {
    throw new Error(
      "Contrato preditivo incompatível com o mapa municipal.",
    );
  }
}

function normalizeMunicipalityId(
  value: string | number,
): string {
  const normalized =
    String(value)
      .trim()
      .padStart(
        7,
        "0",
      );

  if (
    !/^\d{7}$/.test(normalized)
  ) {
    throw new Error(
      `Código IBGE inválido no join cartográfico: ${String(value)}`,
    );
  }

  return normalized;
}

function buildPredictionLookup(
  prediction: PredictionMapContract,
): Map<string, PredictionRecord> {
  validatePredictionContract(
    prediction,
  );

  const lookup =
    new Map<
      string,
      PredictionRecord
    >();

  for (
    let position = 0;
    position < prediction.count;
    position += 1
  ) {
    const codigoIbge7 =
      normalizeMunicipalityId(
        prediction.data.codigo_ibge_7[position],
      );

    const score =
      prediction.data.score[position];

    const predicao =
      prediction.data.predicao[position];

    if (
      !Number.isFinite(score)
      || typeof predicao !== "boolean"
    ) {
      throw new Error(
        `Resultado preditivo inválido para o município ${codigoIbge7}.`,
      );
    }

    if (
      lookup.has(codigoIbge7)
    ) {
      throw new Error(
        `Código IBGE duplicado no contrato preditivo: ${codigoIbge7}.`,
      );
    }

    lookup.set(
      codigoIbge7,
      {
        score,
        predicao,
      },
    );
  }

  return lookup;
}

export function joinMunicipalityPredictions(
  paths: MunicipalitySvgPath[],
  prediction: PredictionMapContract,
): MunicipalityMapJoinResult {
  if (
    paths.length !== 5_571
  ) {
    throw new Error(
      "A malha renderizada deve possuir exatamente 5.571 territórios.",
    );
  }

  const geographyIds =
    new Set<string>();

  for (
    const municipality
    of paths
  ) {
    const codigoIbge7 =
      normalizeMunicipalityId(
        municipality.codigoIbge7,
      );

    if (
      geographyIds.has(codigoIbge7)
    ) {
      throw new Error(
        `Código IBGE duplicado na malha renderizada: ${codigoIbge7}.`,
      );
    }

    geographyIds.add(
      codigoIbge7,
    );
  }

  const predictionLookup =
    buildPredictionLookup(
      prediction,
    );

  for (
    const codigoIbge7
    of predictionLookup.keys()
  ) {
    if (
      !geographyIds.has(codigoIbge7)
    ) {
      throw new Error(
        `Município predito ausente da malha geográfica: ${codigoIbge7}.`,
      );
    }
  }

  let alertCount =
    0;

  let noAlertCount =
    0;

  let withoutEvaluationCount =
    0;

  const municipalities =
    paths.map(
      (municipality): MunicipalityMapDatum => {
        const codigoIbge7 =
          normalizeMunicipalityId(
            municipality.codigoIbge7,
          );

        const predictionRecord =
          predictionLookup.get(
            codigoIbge7,
          );

        if (
          predictionRecord === undefined
        ) {
          withoutEvaluationCount +=
            1;

          return {
            codigoIbge7,
            d:
              municipality.d,
            status:
              "sem_avaliacao",
            score:
              null,
            predicao:
              null,
          };
        }

        if (
          predictionRecord.predicao
        ) {
          alertCount +=
            1;

          return {
            codigoIbge7,
            d:
              municipality.d,
            status:
              "alerta",
            score:
              predictionRecord.score,
            predicao:
              true,
          };
        }

        noAlertCount +=
          1;

        return {
          codigoIbge7,
          d:
            municipality.d,
          status:
            "sem_alerta",
          score:
            predictionRecord.score,
          predicao:
            false,
        };
      },
    );

  if (
    alertCount
      + noAlertCount
      !== prediction.count
    || withoutEvaluationCount
      !== paths.length
        - prediction.count
  ) {
    throw new Error(
      "O join cartográfico não preservou a cobertura preditiva esperada.",
    );
  }

  return {
    municipalities,

    summary: {
      totalTerritories:
        paths.length,

      evaluatedMunicipalities:
        prediction.count,

      alertCount,

      noAlertCount,

      withoutEvaluationCount,
    },
  };
}