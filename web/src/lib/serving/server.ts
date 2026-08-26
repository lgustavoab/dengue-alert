import {
  readFile,
} from "node:fs/promises";

import path from "node:path";

import {
  assertNumber,
  assertServingContract,
  assertString,
} from "@/lib/serving/guards";

import {
  servingPaths,
} from "@/lib/serving/paths";

import type {
  HistoricalAnnualContract,
  HistoricalClimateNationalLagsContract,
  HistoricalClimateRegionalLagsContract,
  HistoricalMunicipalityIndexContract,
  HistoricalRiskEpisodeDurationContract,
  HistoricalRiskMunicipalitiesContract,
  HistoricalRiskWeeklyContract,
  HistoricalSeasonalityNationalContract,
  HistoricalSeasonalityRegionalContract,
  HistoricalSpatialMunicipalitiesContract,
  HistoricalSpatialRegionsContract,
  HistoricalSpatialStatesContract,
  HistoricalWeeklyContract,
  PredictionByHorizonContract,
  PredictionModelContract,
  PredictionMunicipalityIndexContract,
  PredictionOverviewContract,
  QualityOverviewContract,
  ServingManifest,
  TemporalCoverageContract,
  TerritoriesContract,
  TerritoryFilterItem,
} from "@/lib/serving/types";

const servingRoot =
  path.join(
    process.cwd(),
    "public",
    "data",
    "serving",
  );

async function readServingJson(
  relativePath: string,
): Promise<unknown> {
  const filePath =
    path.join(
      servingRoot,
      relativePath,
    );

  let content:
    string;

  try {
    content =
      await readFile(
        filePath,
        "utf-8",
      );
  } catch (error) {
    throw new Error(
      `Não foi possível ler o contrato de serving: ${relativePath}`,
      {
        cause:
          error,
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
        cause:
          error,
      },
    );
  }
}

function assertDataObject(
  value:
    Record<
      string,
      unknown
    >,
  contractName:
    string,
): Record<
  string,
  unknown
> {
  if (
    typeof value.data
    !== "object"
    || value.data
    === null
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
  value:
    Record<
      string,
      unknown
    >,
  contractName:
    string,
): unknown[] {
  if (
    !Array.isArray(
      value.data,
    )
  ) {
    throw new TypeError(
      `${contractName} possui bloco data inválido.`,
    );
  }

  return value.data;
}

function assertCountMatchesData(
  value:
    Record<
      string,
      unknown
    >,
  contractName:
    string,
): unknown[] {
  assertNumber(
    value.count,
    `${contractName}.count`,
  );

  const data =
    assertDataArray(
      value,
      contractName,
    );

  if (
    data.length
    !== value.count
  ) {
    throw new Error(
      `${contractName} possui count divergente de data.length.`,
    );
  }

  return data;
}

async function readCountedDataContract(
  relativePath:
    string,
): Promise<
  Record<
    string,
    unknown
  >
> {
  const value =
    await readServingJson(
      relativePath,
    );

  assertServingContract(
    value,
    relativePath,
  );

  assertCountMatchesData(
    value,
    relativePath,
  );

  return value;
}

export async function getServingManifest(): Promise<ServingManifest> {
  const value =
    await readServingJson(
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
  const value =
    await readServingJson(
      servingPaths
        .quality
        .overview,
    );

  assertServingContract(
    value,
    servingPaths
      .quality
      .overview,
  );

  const data =
    assertDataObject(
      value,
      servingPaths
        .quality
        .overview,
    );

  assertNumber(
    data
      .casos_finais_preservados,
    "quality.overview.data.casos_finais_preservados",
  );

  assertNumber(
    data
      .unidades_territoriais,
    "quality.overview.data.unidades_territoriais",
  );

  assertNumber(
    data
      .municipio_semanas,
    "quality.overview.data.municipio_semanas",
  );

  return value as QualityOverviewContract;
}

export async function getTemporalCoverage(): Promise<TemporalCoverageContract> {
  const value =
    await readServingJson(
      servingPaths
        .metadata
        .temporalCoverage,
    );

  assertServingContract(
    value,
    servingPaths
      .metadata
      .temporalCoverage,
  );

  const data =
    assertDataObject(
      value,
      servingPaths
        .metadata
        .temporalCoverage,
    );

  assertString(
    data
      .periodo_historico,
    "metadata.temporal_coverage.data.periodo_historico",
  );

  assertNumber(
    data
      .semanas_nacionais,
    "metadata.temporal_coverage.data.semanas_nacionais",
  );

  return value as TemporalCoverageContract;
}

export async function getTerritories(): Promise<TerritoriesContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .metadata
        .territories,
    );

  return value as TerritoriesContract;
}

export async function getHistoricalMunicipalityIndex(): Promise<HistoricalMunicipalityIndexContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .historical
        .municipalityIndex,
    );

  if (
    typeof value
      .risk_history
    !== "object"
    || value
      .risk_history
    === null
    || Array.isArray(
      value
        .risk_history,
    )
  ) {
    throw new TypeError(
      "historical/municipality/index.json possui risk_history inválido.",
    );
  }

  return value as HistoricalMunicipalityIndexContract;
}

export async function getPredictionMunicipalityIndex(): Promise<PredictionMunicipalityIndexContract> {
  const value =
    await readServingJson(
      servingPaths
        .prediction
        .municipalityIndex,
    );

  assertServingContract(
    value,
    servingPaths
      .prediction
      .municipalityIndex,
  );

  assertNumber(
    value.count,
    "prediction.municipality.index.count",
  );

  if (
    !Array.isArray(
      value.items,
    )
  ) {
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
  ] =
    await Promise.all([
      getTerritories(),
      getHistoricalMunicipalityIndex(),
      getPredictionMunicipalityIndex(),
    ]);

  const historicalRiskByCode =
    new Map(
      historicalIndex
        .data
        .map(
          (item) => [
            item
              .codigo_ibge_7,

            item
              .risco_historico_disponivel,
          ],
        ),
    );

  const predictionCodes =
    new Set(
      predictionIndex
        .items
        .map(
          (item) =>
            item
              .codigo_ibge_7,
        ),
    );

  return territories
    .data
    .map(
      (
        territory,
      ) => ({
        codigoIbge7:
          territory
            .codigo_ibge_7,

        nomeMunicipio:
          territory
            .nome_municipio,

        codigoUfIbge:
          territory
            .codigo_uf_ibge,

        nomeUf:
          territory
            .nome_uf,

        regiao:
          territory
            .regiao,

        anosDisponiveis:
          territory
            .anos_disponiveis,

        riscoHistoricoDisponivel:
          historicalRiskByCode
            .get(
              territory
                .codigo_ibge_7,
            )
          ?? false,

        predicaoDisponivel:
          predictionCodes
            .has(
              territory
                .codigo_ibge_7,
            ),
      }),
    );
}

export async function getPredictionByHorizon(): Promise<PredictionByHorizonContract> {
  const value =
    await readServingJson(
      servingPaths
        .prediction
        .byHorizon,
    );

  assertServingContract(
    value,
    servingPaths
      .prediction
      .byHorizon,
  );

  if (
    typeof value
      .horizontes
    !== "object"
    || value
      .horizontes
    === null
    || Array.isArray(
      value
        .horizontes,
    )
  ) {
    throw new TypeError(
      "prediction/evaluation/by_horizon.json possui horizontes inválidos.",
    );
  }

  const horizons =
    value.horizontes as Record<
      string,
      unknown
    >;

  for (
    const key
    of [
      "h1",
      "h2",
      "h3",
      "h4",
    ] as const
  ) {
    const horizon =
      horizons[
      key
      ];

    if (
      typeof horizon
      !== "object"
      || horizon
      === null
      || Array.isArray(
        horizon,
      )
    ) {
      throw new TypeError(
        `prediction/evaluation/by_horizon.json possui ${key} inválido.`,
      );
    }

    const record =
      horizon as Record<
        string,
        unknown
      >;

    assertNumber(
      record.horizonte,
      `prediction.by_horizon.${key}.horizonte`,
    );

    assertNumber(
      record
        .threshold_modelo,
      `prediction.by_horizon.${key}.threshold_modelo`,
    );
  }

  return value as PredictionByHorizonContract;
}

export async function getPredictionOverview(): Promise<PredictionOverviewContract> {
  const value =
    await readServingJson(
      servingPaths
        .prediction
        .overview,
    );

  assertServingContract(
    value,
    servingPaths
      .prediction
      .overview,
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
  const value =
    await readServingJson(
      servingPaths
        .prediction
        .model,
    );

  assertServingContract(
    value,
    servingPaths
      .prediction
      .model,
  );

  assertNumber(
    value
      .ano_referencia,
    "prediction.model.ano_referencia",
  );

  if (
    typeof value
      .retrospectivo
    !== "boolean"
  ) {
    throw new TypeError(
      "prediction/model.json possui campo retrospectivo inválido.",
    );
  }

  return value as PredictionModelContract;
}

export async function getHistoricalAnnual(): Promise<HistoricalAnnualContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .historical
        .panoramaAnnual,
    );

  return value as HistoricalAnnualContract;
}

export async function getHistoricalWeekly(): Promise<HistoricalWeeklyContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .historical
        .panoramaWeekly,
    );

  return value as HistoricalWeeklyContract;
}

export async function getHistoricalSeasonalityNational(): Promise<HistoricalSeasonalityNationalContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .historical
        .seasonalityNational,
    );

  return value as HistoricalSeasonalityNationalContract;
}

export async function getHistoricalSeasonalityRegional(): Promise<HistoricalSeasonalityRegionalContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .historical
        .seasonalityRegional,
    );

  return value as HistoricalSeasonalityRegionalContract;
}

export async function getHistoricalSpatialRegions(): Promise<HistoricalSpatialRegionsContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .historical
        .spatialRegions,
    );

  return value as HistoricalSpatialRegionsContract;
}

export async function getHistoricalSpatialStates(): Promise<HistoricalSpatialStatesContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .historical
        .spatialStates,
    );

  return value as HistoricalSpatialStatesContract;
}

export async function getHistoricalSpatialMunicipalities(): Promise<HistoricalSpatialMunicipalitiesContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .historical
        .spatialMunicipalities,
    );

  return value as HistoricalSpatialMunicipalitiesContract;
}

export async function getHistoricalRiskWeekly(): Promise<HistoricalRiskWeeklyContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .historical
        .riskDynamicsWeekly,
    );

  return value as HistoricalRiskWeeklyContract;
}

export async function getHistoricalRiskMunicipalities(): Promise<HistoricalRiskMunicipalitiesContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .historical
        .riskDynamicsMunicipalities,
    );

  return value as HistoricalRiskMunicipalitiesContract;
}

export async function getHistoricalRiskEpisodeDuration(): Promise<HistoricalRiskEpisodeDurationContract> {
  const relativePath =
    servingPaths
      .historical
      .riskEpisodeDuration;

  const value =
    await readServingJson(
      relativePath,
    );

  assertServingContract(
    value,
    relativePath,
  );

  if (
    typeof value.summary
    !== "object"
    || value.summary
    === null
    || Array.isArray(
      value.summary,
    )
  ) {
    throw new TypeError(
      `${relativePath} possui summary inválido.`,
    );
  }

  const summary =
    value.summary as Record<
      string,
      unknown
    >;

  assertNumber(
    summary
      .quantidade_episodios,
    `${relativePath}.summary.quantidade_episodios`,
  );

  assertNumber(
    summary
      .semanas_risco,
    `${relativePath}.summary.semanas_risco`,
  );

  assertNumber(
    summary
      .mediana,
    `${relativePath}.summary.mediana`,
  );

  assertNumber(
    summary
      .maximo,
    `${relativePath}.summary.maximo`,
  );

  if (
    !Array.isArray(
      value.distribution,
    )
  ) {
    throw new TypeError(
      `${relativePath} possui distribution inválido.`,
    );
  }

  return value as HistoricalRiskEpisodeDurationContract;
}

export async function getHistoricalClimateNationalLags(): Promise<HistoricalClimateNationalLagsContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .historical
        .climateNationalLags,
    );

  return value as HistoricalClimateNationalLagsContract;
}

export async function getHistoricalClimateRegionalLags(): Promise<HistoricalClimateRegionalLagsContract> {
  const value =
    await readCountedDataContract(
      servingPaths
        .historical
        .climateRegionalLags,
    );

  return value as HistoricalClimateRegionalLagsContract;
}