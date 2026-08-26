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
  HistoricalMunicipalityIndexContract,
  PredictionModelContract,
  PredictionMunicipalityIndexContract,
  PredictionOverviewContract,
  QualityOverviewContract,
  ServingManifest,
  TemporalCoverageContract,
  TerritoriesContract,
  TerritoryFilterItem,
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

function assertDataObject(
  value: Record<string, unknown>,
  contractName: string,
): Record<string, unknown> {
  if (
    typeof value.data !== "object"
    || value.data === null
    || Array.isArray(
      value.data,
    )
  ) {
    throw new TypeError(
      `${contractName} possui bloco data inválido.`,
    );
  }

  return value.data as Record<
    string,
    unknown
  >;
}

function assertDataArray(
  value: Record<string, unknown>,
  contractName: string,
): unknown[] {
  if (!Array.isArray(value.data)) {
    throw new TypeError(
      `${contractName} possui bloco data inválido.`,
    );
  }

  return value.data;
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

  const data = assertDataObject(
    value,
    servingPaths.quality.overview,
  );

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

  const data = assertDataObject(
    value,
    servingPaths.metadata.temporalCoverage,
  );

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

export async function getTerritories(): Promise<TerritoriesContract> {
  const value = await readServingJson(
    servingPaths.metadata.territories,
  );

  assertServingContract(
    value,
    servingPaths.metadata.territories,
  );

  assertNumber(
    value.count,
    "metadata.territories.count",
  );

  const data = assertDataArray(
    value,
    servingPaths.metadata.territories,
  );

  if (
    data.length
    !== value.count
  ) {
    throw new Error(
      "metadata/territories.json possui count divergente de data.length.",
    );
  }

  return value as TerritoriesContract;
}

export async function getHistoricalMunicipalityIndex(): Promise<HistoricalMunicipalityIndexContract> {
  const value = await readServingJson(
    servingPaths.historical
      .municipalityIndex,
  );

  assertServingContract(
    value,
    servingPaths.historical
      .municipalityIndex,
  );

  assertNumber(
    value.count,
    "historical.municipality.index.count",
  );

  const data = assertDataArray(
    value,
    servingPaths.historical
      .municipalityIndex,
  );

  if (
    data.length
    !== value.count
  ) {
    throw new Error(
      "historical/municipality/index.json possui count divergente de data.length.",
    );
  }

  return value as HistoricalMunicipalityIndexContract;
}

export async function getPredictionMunicipalityIndex(): Promise<PredictionMunicipalityIndexContract> {
  const value = await readServingJson(
    servingPaths.prediction
      .municipalityIndex,
  );

  assertServingContract(
    value,
    servingPaths.prediction
      .municipalityIndex,
  );

  assertNumber(
    value.count,
    "prediction.municipality.index.count",
  );

  if (!Array.isArray(value.items)) {
    throw new TypeError(
      "prediction/municipality/index.json possui items inválido.",
    );
  }

  if (
    value.items.length
    !== value.count
  ) {
    throw new Error(
      "prediction/municipality/index.json possui count divergente de items.length.",
    );
  }

  return value as PredictionMunicipalityIndexContract;
}

export async function getTerritoryFilterItems(): Promise<
  TerritoryFilterItem[]
> {
  const [
    territories,
    historicalIndex,
    predictionIndex,
  ] = await Promise.all([
    getTerritories(),
    getHistoricalMunicipalityIndex(),
    getPredictionMunicipalityIndex(),
  ]);

  const historicalRiskByCode =
    new Map(
      historicalIndex.data.map(
        (item) => [
          item.codigo_ibge_7,
          item
            .risco_historico_disponivel,
        ],
      ),
    );

  const predictionCodes =
    new Set(
      predictionIndex.items.map(
        (item) =>
          item.codigo_ibge_7,
      ),
    );

  return territories.data.map(
    (territory) => ({
      codigoIbge7:
        territory.codigo_ibge_7,
      nomeMunicipio:
        territory.nome_municipio,
      codigoUfIbge:
        territory.codigo_uf_ibge,
      nomeUf:
        territory.nome_uf,
      regiao:
        territory.regiao,
      anosDisponiveis:
        territory.anos_disponiveis,
      riscoHistoricoDisponivel:
        historicalRiskByCode.get(
          territory.codigo_ibge_7,
        ) ?? false,
      predicaoDisponivel:
        predictionCodes.has(
          territory.codigo_ibge_7,
        ),
    }),
  );
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
    servingPaths.historical
      .panoramaAnnual,
  );

  assertServingContract(
    value,
    servingPaths.historical
      .panoramaAnnual,
  );

  assertNumber(
    value.count,
    "historical.panorama.annual.count",
  );

  const data = assertDataArray(
    value,
    servingPaths.historical
      .panoramaAnnual,
  );

  if (
    data.length
    !== value.count
  ) {
    throw new Error(
      "historical/panorama/annual.json possui count divergente de data.length.",
    );
  }

  return value as HistoricalAnnualContract;
}