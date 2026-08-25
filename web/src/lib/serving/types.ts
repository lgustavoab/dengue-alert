export type SchemaVersion = "1.0";

export type ServingManifestFile = {
  path: string;
  size_bytes: number;
  sha256: string;
};

export type ServingManifest = {
  schema_version: SchemaVersion;
  status: "APROVADO";
  source: string;
  destination: string;
  contract_count: number;
  total_size_bytes: number;
  excluded: string[];
  files: ServingManifestFile[];
};

export type QualityOverviewContract = {
  schema_version: SchemaVersion;
  period: string;
  source: string[];
  data: {
    registros_sinan_brutos: number;
    registros_sinan_mantidos_apos_filtros: number;
    casos_finais_preservados: number;
    unidades_territoriais: number;
    municipio_semanas: number;
    linhas_zero_fill: number;
    unidades_com_cobertura_climatica: number;
    municipio_semanas_com_clima: number;
    municipio_semanas_sem_clima: number;
  };
};

export type TemporalCoverageContract = {
  schema_version: SchemaVersion;
  period: string;
  source: string[];
  data: {
    periodo_historico: string;
    anos: number[];
    semanas_nacionais: number;
    anos_com_53_semanas: number[];
    regra_semana_epidemiologica: string;
  };
};

export type PredictionHorizonOverview = {
  linhas: number;
  municipios: number;
  semanas_origem: number;
  data_inicio_min: string;
  data_inicio_max: string;
  threshold: number;
  target_positivos: number;
  predicoes_positivas: number;
  early_warning_elegiveis: number;
  early_warning_alertas: number;
  score_min: number;
  score_max: number;
};

export type PredictionOverviewContract = {
  schema_version: SchemaVersion;
  status: "APROVADO";
  avaliacao: string;
  ano: number;
  linhas: number;
  municipios: number;
  horizontes: {
    h1: PredictionHorizonOverview;
    h2: PredictionHorizonOverview;
    h3: PredictionHorizonOverview;
    h4: PredictionHorizonOverview;
  };
};

export type PredictionModelHorizon = {
  horizonte: number;
  semanas_a_frente: number;
  threshold: number;
};

export type PredictionModelContract = {
  schema_version: SchemaVersion;
  status: "APROVADO";
  tipo: string;
  ano_referencia: number;
  retrospectivo: boolean;
  modelo: {
    algoritmo: string;
    features: string;
    calibracao: string;
    probabilidades: string;
  };
  protocolo: {
    desenvolvimento: string;
    teste_final: string;
    thresholds_congelados: boolean;
    teste_final_utilizado_na_selecao: boolean;
  };
  horizontes: PredictionModelHorizon[];
  semantica: {
    predicao: string;
    risco_elevado: string;
    target: string;
    early_warning: string;
  };
  restricoes_interpretacao: string[];
};

export type HistoricalAnnualItem = {
  ano_epidemiologico: number;
  semanas_epidemiologicas: number;
  casos_provaveis: number;
  populacao_nacional: number;
  incidencia_anual_100mil: number;
  media_semanal_casos: number;
  pico_semanal_casos: number;
  semana_pico: number;
  data_inicio_semana_pico: string;
  unidades_territoriais: number;
  unidades_territoriais_com_casos: number;
  proporcao_unidades_com_casos: number;
  participacao_casos_periodo: number;
};

export type HistoricalAnnualContract = {
  schema_version: SchemaVersion;
  period: string;
  source: string[];
  count: number;
  data: HistoricalAnnualItem[];
};