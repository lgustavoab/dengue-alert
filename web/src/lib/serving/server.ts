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
  ClimateCoverageContract,
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
  PopulationCoverageContract,
  QualityOverviewContract,
  ServingManifest,
  TemporalCoverageContract,
  TerritoriesContract,
  TerritorialCoverageContract,
  TerritoryFilterItem,
  SinanPipelineContract,
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

function assertObject(
  value: unknown,
  fieldName: string,
): asserts value is Record<string, unknown> {
  if (
    typeof value !== "object"
    || value === null
    || Array.isArray(value)
  ) {
    throw new TypeError(`${fieldName} deve ser um objeto.`);
  }
}

function assertStringArray(
  value: unknown,
  fieldName: string,
): asserts value is string[] {
  if (
    !Array.isArray(value)
    || !value.every((item) => typeof item === "string")
  ) {
    throw new TypeError(`${fieldName} deve ser uma lista de textos.`);
  }
}

function assertNumberArray(
  value: unknown,
  fieldName: string,
): asserts value is number[] {
  if (!Array.isArray(value)) {
    throw new TypeError(`${fieldName} deve ser uma lista numérica.`);
  }

  value.forEach((item, index) =>
    assertNumber(item, `${fieldName}[${index}]`));
}

function assertQualityBase(
  value: unknown,
  relativePath: string,
): asserts value is Record<string, unknown> {
  assertServingContract(value, relativePath);
  assertString(value.period, `${relativePath}.period`);
  assertStringArray(value.source, `${relativePath}.source`);
}

function assertNumbers(
  value: Record<string, unknown>,
  fields: readonly string[],
  prefix: string,
): void {
  fields.forEach((field) =>
    assertNumber(value[field], `${prefix}.${field}`));
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
  const relativePath = servingPaths.quality.overview;
  const value =
    await readServingJson(
      relativePath,
    );

  assertQualityBase(value, relativePath);

  const data =
    assertDataObject(
      value,
      relativePath,
    );

  assertNumbers(data, [
    "registros_sinan_brutos",
    "registros_sinan_mantidos_apos_filtros",
    "casos_finais_preservados",
    "unidades_territoriais",
    "municipio_semanas",
    "linhas_zero_fill",
    "unidades_com_cobertura_climatica",
    "municipio_semanas_com_clima",
    "municipio_semanas_sem_clima",
  ], `${relativePath}.data`);

  return value as QualityOverviewContract;
}

export async function getSinanPipeline(): Promise<SinanPipelineContract> {
  const relativePath = servingPaths.quality.sinanPipeline;
  const value = await readServingJson(relativePath);
  assertQualityBase(value, relativePath);
  const data = assertDataObject(value, relativePath);
  assertNumbers(data, [
    "registros_brutos",
    "total_remocoes_documentadas",
    "registros_mantidos_apos_filtros",
    "grupos_antes_normalizacao",
    "codigos_sinan_iniciais",
    "casos_finais",
  ], `${relativePath}.data`);

  if (!Array.isArray(data.etapas)) {
    throw new TypeError(`${relativePath}.data.etapas deve ser uma lista.`);
  }

  data.etapas.forEach((step, index) => {
    assertObject(step, `${relativePath}.data.etapas[${index}]`);
    assertString(step.id, `${relativePath}.data.etapas[${index}].id`);
    assertString(step.label, `${relativePath}.data.etapas[${index}].label`);
    assertString(step.operation, `${relativePath}.data.etapas[${index}].operation`);

    if (step.operation !== "validation" && step.operation !== "filter") {
      throw new TypeError(`${relativePath}.data.etapas[${index}].operation é inválida.`);
    }

    if (step.records_removed !== null) {
      assertNumber(step.records_removed, `${relativePath}.data.etapas[${index}].records_removed`);
    }

    if (step.field !== undefined) {
      assertString(step.field, `${relativePath}.data.etapas[${index}].field`);
    }

    if (step.note !== undefined) {
      assertString(step.note, `${relativePath}.data.etapas[${index}].note`);
    }
  });

  assertObject(data.zero_fill, `${relativePath}.data.zero_fill`);
  assertNumbers(data.zero_fill, [
    "linhas_observadas",
    "linhas_finais",
    "linhas_preenchidas_com_zero",
    "casos_antes",
    "casos_depois",
  ], `${relativePath}.data.zero_fill`);

  return value as SinanPipelineContract;
}

export async function getTerritorialCoverage(): Promise<TerritorialCoverageContract> {
  const relativePath = servingPaths.quality.territorialCoverage;
  const value = await readServingJson(relativePath);
  assertQualityBase(value, relativePath);
  const data = assertDataObject(value, relativePath);
  assertString(data.referencia, `${relativePath}.data.referencia`);
  assertNumbers(data, [
    "unidades_territoriais_referencia",
    "codigos_sinan_iniciais",
    "codigos_associados_diretamente",
    "codigos_nao_associados_inicialmente",
    "casos_nao_associados_inicialmente",
  ], `${relativePath}.data`);

  assertObject(data.composicao_referencia, `${relativePath}.data.composicao_referencia`);
  assertObject(data.distrito_federal, `${relativePath}.data.distrito_federal`);
  assertObject(data.residuais_nao_municipais, `${relativePath}.data.residuais_nao_municipais`);
  assertObject(data.resultado_final, `${relativePath}.data.resultado_final`);

  assertNumbers(data.composicao_referencia, [
    "municipios",
    "distrito_federal",
    "distrito_estadual_fernando_de_noronha",
  ], `${relativePath}.data.composicao_referencia`);
  assertNumbers(data.distrito_federal, [
    "codigos_subdivisoes",
    "casos_preservados",
  ], `${relativePath}.data.distrito_federal`);
  assertString(data.distrito_federal.codigo_ibge_7_destino, `${relativePath}.data.distrito_federal.codigo_ibge_7_destino`);
  assertString(data.distrito_federal.nome_destino, `${relativePath}.data.distrito_federal.nome_destino`);
  assertNumbers(data.residuais_nao_municipais, [
    "quantidade_codigos",
    "casos_excluidos",
  ], `${relativePath}.data.residuais_nao_municipais`);
  assertNumbers(data.resultado_final, [
    "unidades_territoriais",
    "unidades_com_registro_original",
    "unidades_sem_registro_original",
    "casos_preservados",
  ], `${relativePath}.data.resultado_final`);

  return value as TerritorialCoverageContract;
}

export async function getPopulationCoverage(): Promise<PopulationCoverageContract> {
  const relativePath = servingPaths.quality.populationCoverage;
  const value = await readServingJson(relativePath);
  assertQualityBase(value, relativePath);
  const data = assertDataObject(value, relativePath);
  assertNumbers(data, [
    "linhas_sem_populacao",
    "linhas_populacao_nao_positiva",
  ], `${relativePath}.data`);
  assertString(data.observacao_metodologica, `${relativePath}.data.observacao_metodologica`);
  assertObject(data.referencia_2023, `${relativePath}.data.referencia_2023`);
  assertNumbers(data.referencia_2023, [
    "ano_epidemiologico",
    "ano_referencia_populacao",
  ], `${relativePath}.data.referencia_2023`);

  if (typeof data.referencia_2023.usa_referencia_censo_2022 !== "boolean") {
    throw new TypeError(`${relativePath}.data.referencia_2023.usa_referencia_censo_2022 deve ser booleano.`);
  }

  if (!Array.isArray(data.por_ano)) {
    throw new TypeError(`${relativePath}.data.por_ano deve ser uma lista.`);
  }

  data.por_ano.forEach((item, index) => {
    assertObject(item, `${relativePath}.data.por_ano[${index}]`);
    assertNumbers(item, [
      "ano_epidemiologico",
      "unidades_territoriais",
      "linhas_sem_populacao",
      "linhas_populacao_nao_positiva",
    ], `${relativePath}.data.por_ano[${index}]`);
    assertNumberArray(item.anos_referencia_populacao, `${relativePath}.data.por_ano[${index}].anos_referencia_populacao`);
    assertStringArray(item.tipos_populacao, `${relativePath}.data.por_ano[${index}].tipos_populacao`);
  });

  return value as PopulationCoverageContract;
}

export async function getClimateCoverage(): Promise<ClimateCoverageContract> {
  const relativePath = servingPaths.quality.climateCoverage;
  const value = await readServingJson(relativePath);
  assertQualityBase(value, relativePath);
  const data = assertDataObject(value, relativePath);
  assertNumbers(data, [
    "unidades_com_mapeamento_climatico",
    "linhas_climaticas_fonte",
    "pontos_grade_distintos",
    "combinacoes_grade_timezone",
    "municipio_semanas_com_clima",
    "municipio_semanas_sem_clima",
  ], `${relativePath}.data`);
  assertStringArray(data.codigos_excluidos, `${relativePath}.data.codigos_excluidos`);
  assertObject(data.metodos_selecao_grid, `${relativePath}.data.metodos_selecao_grid`);
  assertNumbers(data.metodos_selecao_grid, [
    "fallback_insular_externo_ate_15km",
    "fallback_valido_intersecta_municipio",
    "grid_mais_proximo_valido",
  ], `${relativePath}.data.metodos_selecao_grid`);
  assertString(data.observacao, `${relativePath}.data.observacao`);

  return value as ClimateCoverageContract;
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
