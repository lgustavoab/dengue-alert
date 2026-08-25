import { readFile } from "node:fs/promises";
import path from "node:path";

import {
  assertNumber,
  assertServingContract,
  assertString,
} from "@/lib/serving/guards";
import { servingPaths } from "@/lib/serving/paths";
import type {
  HistoricalAnnualContract,
  PredictionModelContract,
  PredictionOverviewContract,
  QualityOverviewContract,
  ServingManifest,
  TemporalCoverageContract,
} from "@/lib/serving/types";

const servingRoot = path.join(
  process.cwd(),
  "public",
  "data",
  "serving",
);

async function readServingJson(
  relativePath: string,
): Promise<unknown> {
  const filePath = path.join(
    servingRoot,
    relativePath,
  );

  let content: string;

  try {
    content = await readFile(
      filePath,
      "utf-8",
    );
  } catch (error) {
    throw new Error(
      `Não foi possível ler o contrato de serving: ${relativePath}`,
      {
        cause: error,
      },
    );
  }

  try {
    return JSON.parse(
      content,
    ) as unknown;
  } catch (error) {
    throw new Error(
      `JSON inválido no serving: ${relativePath}`,
      {
        cause: error,
      },
    );
  }
}

export async function getServingManifest(): Promise<ServingManifest> {
  const value = await readServingJson(
    servingPaths.manifest,
  );

  assertServingContract(
    value,
    servingPaths.manifest,
  );

  assertNumber(
    value.contract_count,
    "manifest.contract_count",
  );

  assertNumber(
    value.total_size_bytes,
    "manifest.total_size_bytes",
  );

  return value as ServingManifest;
}

export async function getQualityOverview(): Promise<QualityOverviewContract> {
  const value = await readServingJson(
    servingPaths.quality.overview,
  );

  assertServingContract(
    value,
    servingPaths.quality.overview,
  );

  if (
    typeof value.data !== "object"
    || value.data === null
    || Array.isArray(
      value.data,
    )
  ) {
    throw new TypeError(
      "quality/overview.json possui bloco data inválido.",
    );
  }

  const data = value.data as Record<
    string,
    unknown
  >;

  assertNumber(
    data.casos_finais_preservados,
    "quality.overview.data.casos_finais_preservados",
  );

  assertNumber(
    data.unidades_territoriais,
    "quality.overview.data.unidades_territoriais",
  );

  assertNumber(
    data.municipio_semanas,
    "quality.overview.data.municipio_semanas",
  );

  return value as QualityOverviewContract;
}

export async function getTemporalCoverage(): Promise<TemporalCoverageContract> {
  const value = await readServingJson(
    servingPaths.metadata.temporalCoverage,
  );

  assertServingContract(
    value,
    servingPaths.metadata.temporalCoverage,
  );

  if (
    typeof value.data !== "object"
    || value.data === null
    || Array.isArray(
      value.data,
    )
  ) {
    throw new TypeError(
      "metadata/temporal_coverage.json possui bloco data inválido.",
    );
  }

  const data = value.data as Record<
    string,
    unknown
  >;

  assertString(
    data.periodo_historico,
    "metadata.temporal_coverage.data.periodo_historico",
  );

  assertNumber(
    data.semanas_nacionais,
    "metadata.temporal_coverage.data.semanas_nacionais",
  );

  return value as TemporalCoverageContract;
}

export async function getPredictionOverview(): Promise<PredictionOverviewContract> {
  const value = await readServingJson(
    servingPaths.prediction.overview,
  );

  assertServingContract(
    value,
    servingPaths.prediction.overview,
  );

  assertNumber(
    value.ano,
    "prediction.overview.ano",
  );

  assertNumber(
    value.linhas,
    "prediction.overview.linhas",
  );

  assertNumber(
    value.municipios,
    "prediction.overview.municipios",
  );

  return value as PredictionOverviewContract;
}

export async function getPredictionModel(): Promise<PredictionModelContract> {
  const value = await readServingJson(
    servingPaths.prediction.model,
  );

  assertServingContract(
    value,
    servingPaths.prediction.model,
  );

  assertNumber(
    value.ano_referencia,
    "prediction.model.ano_referencia",
  );

  if (
    typeof value.retrospectivo
    !== "boolean"
  ) {
    throw new TypeError(
      "prediction/model.json possui campo retrospectivo inválido.",
    );
  }

  return value as PredictionModelContract;
}

export async function getHistoricalAnnual(): Promise<HistoricalAnnualContract> {
  const value = await readServingJson(
    servingPaths.historical.panoramaAnnual,
  );

  assertServingContract(
    value,
    servingPaths.historical.panoramaAnnual,
  );

  assertNumber(
    value.count,
    "historical.panorama.annual.count",
  );

  if (!Array.isArray(value.data)) {
    throw new TypeError(
      "historical/panorama/annual.json possui data inválido.",
    );
  }

  return value as HistoricalAnnualContract;
}