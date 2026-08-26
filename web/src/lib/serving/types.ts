export type SchemaVersion =
  "1.0";

export type ServingManifestFile = {
  path: string;
  size_bytes: number;
  sha256: string;
};

export type ServingManifest = {
  schema_version:
  SchemaVersion;
  status: "APROVADO";
  source: string;
  destination: string;
  contract_count: number;
  total_size_bytes: number;
  excluded: string[];
  files:
  ServingManifestFile[];
};

export type QualityOverviewContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  data: {
    registros_sinan_brutos:
    number;

    registros_sinan_mantidos_apos_filtros:
    number;

    casos_finais_preservados:
    number;

    unidades_territoriais:
    number;

    municipio_semanas:
    number;

    linhas_zero_fill:
    number;

    unidades_com_cobertura_climatica:
    number;

    municipio_semanas_com_clima:
    number;

    municipio_semanas_sem_clima:
    number;
  };
};

export type TemporalCoverageContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  data: {
    periodo_historico:
    string;

    anos:
    number[];

    semanas_nacionais:
    number;

    anos_com_53_semanas:
    number[];

    regra_semana_epidemiologica:
    string;
  };
};

export type TerritoryItem = {
  codigo_ibge_7:
  string;

  nome_municipio:
  string;

  codigo_uf_ibge:
  string;

  nome_uf:
  string;

  regiao:
  string;

  anos_disponiveis:
  number;
};

export type TerritoriesContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data:
  TerritoryItem[];
};

export type HistoricalMunicipalityIndexItem =
  TerritoryItem & {
    risco_historico_disponivel:
    boolean;
  };

export type HistoricalMunicipalityIndexContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;

  risk_history: {
    available:
    number;

    unavailable:
    number;
  };

  data:
  HistoricalMunicipalityIndexItem[];
};

export type HistoricalAnnualItem = {
  ano_epidemiologico:
  number;

  semanas_epidemiologicas:
  number;

  casos_provaveis:
  number;

  populacao_nacional:
  number;

  incidencia_anual_100mil:
  number;

  media_semanal_casos:
  number;

  pico_semanal_casos:
  number;

  semana_pico:
  number;

  data_inicio_semana_pico:
  string;

  unidades_territoriais:
  number;

  unidades_territoriais_com_casos:
  number;

  proporcao_unidades_com_casos:
  number;

  participacao_casos_periodo:
  number;
};

export type HistoricalAnnualContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data:
  HistoricalAnnualItem[];
};

export type HistoricalWeeklyItem = {
  ano_epidemiologico:
  number;

  semana_epidemiologica:
  number;

  data_inicio_semana:
  string;

  data_fim_semana:
  string;

  casos_provaveis:
  number;

  unidades_territoriais:
  number;

  unidades_territoriais_com_casos:
  number;

  populacao_nacional:
  number;

  incidencia_nacional_100mil:
  number;

  proporcao_unidades_com_casos:
  number;
};

export type HistoricalWeeklyContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data:
  HistoricalWeeklyItem[];
};

export type HistoricalSeasonalityNationalItem = {
  semana_epidemiologica:
  number;

  anos_disponiveis:
  number;

  casos_media:
  number;

  casos_mediana:
  number;

  casos_minimo:
  number;

  casos_maximo:
  number;

  incidencia_media_100mil:
  number;

  incidencia_mediana_100mil:
  number;

  incidencia_q25_100mil:
  number;

  incidencia_q75_100mil:
  number;

  incidencia_minima_100mil:
  number;

  incidencia_maxima_100mil:
  number;
};

export type HistoricalSeasonalityNationalContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data:
  HistoricalSeasonalityNationalItem[];
};

export type HistoricalSeasonalityRegionalItem = {
  regiao:
  string;

  semana_epidemiologica:
  number;

  anos_disponiveis:
  number;

  casos_media:
  number;

  casos_mediana:
  number;

  incidencia_media_100mil:
  number;

  incidencia_mediana_100mil:
  number;

  incidencia_q25_100mil:
  number;

  incidencia_q75_100mil:
  number;

  incidencia_minima_100mil:
  number;

  incidencia_maxima_100mil:
  number;
};

export type HistoricalSeasonalityRegionalContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data:
  HistoricalSeasonalityRegionalItem[];
};

export type HistoricalSpatialRegionItem = {
  regiao:
  string;

  anos_disponiveis:
  number;

  anos_com_casos:
  number;

  casos_periodo:
  number;

  populacao_media:
  number;

  incidencia_media_anual_100mil:
  number;

  incidencia_mediana_anual_100mil:
  number;

  incidencia_maxima_anual_100mil:
  number;

  ano_maior_incidencia:
  number;

  incidencia_ano_pico_100mil:
  number;

  participacao_casos_periodo:
  number;
};

export type HistoricalSpatialRegionsContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data:
  HistoricalSpatialRegionItem[];
};

export type HistoricalSpatialStateItem = {
  codigo_uf_ibge:
  string;

  nome_uf:
  string;

  regiao:
  string;

  anos_disponiveis:
  number;

  anos_com_casos:
  number;

  casos_periodo:
  number;

  populacao_media:
  number;

  incidencia_media_anual_100mil:
  number;

  incidencia_mediana_anual_100mil:
  number;

  incidencia_maxima_anual_100mil:
  number;

  ano_maior_incidencia:
  number;

  incidencia_ano_pico_100mil:
  number;

  participacao_casos_periodo:
  number;
};

export type HistoricalSpatialStatesContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data:
  HistoricalSpatialStateItem[];
};

export type HistoricalSpatialMunicipalityItem = {
  codigo_ibge_7:
  string;

  nome_municipio:
  string;

  codigo_uf_ibge:
  string;

  nome_uf:
  string;

  regiao:
  string;

  anos_disponiveis:
  number;

  anos_com_casos:
  number;

  casos_periodo:
  number;

  populacao_media:
  number;

  incidencia_media_anual_100mil:
  number;

  incidencia_mediana_anual_100mil:
  number;

  incidencia_maxima_anual_100mil:
  number;

  ano_maior_incidencia:
  number;

  incidencia_ano_pico_100mil:
  number;

  participacao_casos_periodo:
  number;
};

export type HistoricalSpatialMunicipalitiesContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data:
  HistoricalSpatialMunicipalityItem[];
};

export type HistoricalRiskWeeklyItem = {
  escala:
  string;

  grupo:
  string;

  ano_epidemiologico:
  number;

  semana_epidemiologica:
  number;

  data_inicio_semana:
  string;

  unidades_elegiveis:
  number;

  unidades_em_risco:
  number;

  proporcao_unidades_em_risco:
  number;

  incidencia_4s_media_100mil:
  number;

  incidencia_4s_mediana_100mil:
  number;

  limiar_p90_mediano_100mil:
  number;
};

export type HistoricalRiskWeeklyContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data:
  HistoricalRiskWeeklyItem[];
};

export type HistoricalRiskMunicipalityItem = {
  codigo_ibge_7:
  string;

  nome_municipio:
  string;

  codigo_uf_ibge:
  string;

  nome_uf:
  string;

  regiao:
  string;

  observacoes_elegiveis:
  number;

  anos_elegiveis:
  number;

  semanas_risco:
  number;

  proporcao_semanas_risco:
  number;

  anos_com_risco:
  number;

  primeira_semana_risco:
  string | null;

  ultima_semana_risco:
  string | null;

  episodios:
  number;

  duracao_media_episodio:
  number | null;

  duracao_mediana_episodio:
  number | null;

  duracao_maxima_episodio:
  number | null;

  episodios_multianuais:
  number;

  recorrencia_multianual:
  boolean;
};

export type HistoricalRiskMunicipalitiesContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data:
  HistoricalRiskMunicipalityItem[];
};

export type HistoricalRiskEpisodeDurationSummary = {
  quantidade_episodios:
  number;

  semanas_risco:
  number;

  minimo:
  number;

  media:
  number;

  p25:
  number;

  mediana:
  number;

  p75:
  number;

  p90:
  number;

  p95:
  number;

  p99:
  number;

  maximo:
  number;
};

export type HistoricalRiskEpisodeDurationItem = {
  duracao_semanas:
  number;

  episodios:
  number;
};

export type HistoricalRiskEpisodeDurationContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];

  summary:
  HistoricalRiskEpisodeDurationSummary;

  distribution:
  HistoricalRiskEpisodeDurationItem[];
};

export type HistoricalClimateLagItem = {
  variavel_climatica:
  string;

  lag_semanas:
  number;

  municipios_total:
  number;

  municipios_correlacao_valida:
  number;

  observacoes_validas_mediana:
  number;

  correlacao_media:
  number;

  correlacao_mediana:
  number;

  correlacao_p10:
  number;

  correlacao_p25:
  number;

  correlacao_p75:
  number;

  correlacao_p90:
  number;

  proporcao_correlacao_positiva:
  number;

  proporcao_correlacao_negativa:
  number;
};

export type HistoricalClimateNationalLagsContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data:
  HistoricalClimateLagItem[];
};

export type HistoricalClimateRegionalLagItem =
  HistoricalClimateLagItem & {
    regiao:
    string;
  };

export type HistoricalClimateRegionalLagsContract = {
  schema_version:
  SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data:
  HistoricalClimateRegionalLagItem[];
};

export type HistoricalMunicipalitySeriesData = {
  ano_epidemiologico:
  number[];

  semana_epidemiologica:
  number[];

  data_inicio_semana:
  string[];

  casos_provaveis:
  number[];

  incidencia_100mil:
  number[];

  registro_sinan_presente:
  boolean[];

  zero_preenchido:
  boolean[];

  populacao:
  number[];
};

export type HistoricalMunicipalitySeriesContract = {
  schema_version:
  SchemaVersion;

  codigo_ibge_7:
  string;

  count:
  number;

  data:
  HistoricalMunicipalitySeriesData;
};

export type PredictionConfusionMatrix = {
  tn:
  number;

  fp:
  number;

  fn:
  number;

  tp:
  number;
};

export type PredictionEvaluationMetrics = {
  observacoes:
  number;

  positivos:
  number;

  negativos:
  number;

  prevalencia:
  number;

  pr_auc_average_precision:
  number;

  roc_auc:
  number;

  recall:
  number;

  precision:
  number;

  f1:
  number;

  balanced_accuracy:
  number;

  brier_score:
  number;

  matriz_confusao:
  PredictionConfusionMatrix;
};

export type PredictionEarlyWarningMetrics =
  PredictionEvaluationMetrics & {
    alertas:
    number | null;

    proporcao_alertas:
    number | null;
  };

export type PredictionFinalModelEvaluation = {
  nome:
  string;

  linhas_treino:
  number;

  linhas_teste:
  number;

  geral:
  PredictionEvaluationMetrics;

  early_warning:
  PredictionEarlyWarningMetrics;
};

export type PredictionPersistenceEvaluation = {
  nome:
  string;

  threshold:
  number;

  linhas_teste:
  number;

  geral:
  PredictionEvaluationMetrics;

  early_warning:
  PredictionEarlyWarningMetrics;
};

export type PredictionEvaluationHorizon = {
  horizonte:
  number;

  threshold_modelo:
  number;

  modelo_final:
  PredictionFinalModelEvaluation;

  baseline_persistencia:
  PredictionPersistenceEvaluation;
};

export type PredictionByHorizonContract = {
  schema_version:
  SchemaVersion;

  status:
  "APROVADO";

  avaliacao:
  string;

  horizontes: {
    h1:
    PredictionEvaluationHorizon;

    h2:
    PredictionEvaluationHorizon;

    h3:
    PredictionEvaluationHorizon;

    h4:
    PredictionEvaluationHorizon;
  };
};

export type PredictionHorizonOverview = {
  linhas:
  number;

  municipios:
  number;

  semanas_origem:
  number;

  data_inicio_min:
  string;

  data_inicio_max:
  string;

  threshold:
  number;

  target_positivos:
  number;

  predicoes_positivas:
  number;

  early_warning_elegiveis:
  number;

  early_warning_alertas:
  number;

  score_min:
  number;

  score_max:
  number;
};

export type PredictionOverviewContract = {
  schema_version:
  SchemaVersion;

  status:
  "APROVADO";

  avaliacao:
  string;

  ano:
  number;

  linhas:
  number;

  municipios:
  number;

  horizontes: {
    h1:
    PredictionHorizonOverview;

    h2:
    PredictionHorizonOverview;

    h3:
    PredictionHorizonOverview;

    h4:
    PredictionHorizonOverview;
  };
};

export type PredictionModelHorizon = {
  horizonte:
  number;

  semanas_a_frente:
  number;

  threshold:
  number;
};

export type PredictionModelContract = {
  schema_version:
  SchemaVersion;

  status:
  "APROVADO";

  tipo:
  string;

  ano_referencia:
  number;

  retrospectivo:
  boolean;

  modelo: {
    algoritmo:
    string;

    features:
    string;

    calibracao:
    string;

    probabilidades:
    string;
  };

  protocolo: {
    desenvolvimento:
    string;

    teste_final:
    string;

    thresholds_congelados:
    boolean;

    teste_final_utilizado_na_selecao:
    boolean;
  };

  horizontes:
  PredictionModelHorizon[];

  semantica: {
    score:
    string;

    predicao:
    string;

    risco_elevado:
    string;

    target:
    string;

    early_warning:
    string;
  };

  restricoes_interpretacao:
  string[];
};

export type PredictionMunicipalityIndexItem = {
  codigo_ibge_7:
  string;

  nome_municipio_ibge:
  string;

  nome_uf_ibge:
  string;

  predicoes:
  number;

  horizontes: {
    h1:
    number;

    h2:
    number;

    h3:
    number;

    h4:
    number;
  };
};

export type PredictionMunicipalityIndexContract = {
  schema_version:
  SchemaVersion;

  status:
  "APROVADO";

  count:
  number;

  items:
  PredictionMunicipalityIndexItem[];
};

export type PredictionMunicipalitySeriesData = {
  ano_epidemiologico:
  number[];

  semana_epidemiologica:
  number[];

  data_inicio_semana:
  string[];

  risco_elevado:
  boolean[];

  target:
  boolean[];

  score:
  number[];

  predicao:
  boolean[];
};

export type PredictionMunicipalitySeriesHorizon = {
  count:
  number;

  threshold:
  number;

  data:
  PredictionMunicipalitySeriesData;
};

export type PredictionMunicipalitySeriesContract = {
  schema_version:
  SchemaVersion;

  codigo_ibge_7:
  string;

  count:
  number;

  horizontes: {
    h1:
    PredictionMunicipalitySeriesHorizon;

    h2:
    PredictionMunicipalitySeriesHorizon;

    h3:
    PredictionMunicipalitySeriesHorizon;

    h4:
    PredictionMunicipalitySeriesHorizon;
  };
};

export type TerritoryFilterItem = {
  codigoIbge7:
  string;

  nomeMunicipio:
  string;

  codigoUfIbge:
  string;

  nomeUf:
  string;

  regiao:
  string;

  anosDisponiveis:
  number;

  riscoHistoricoDisponivel:
  boolean;

  predicaoDisponivel:
  boolean;
};