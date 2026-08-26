import type {
  SchemaVersion,
} from "@/lib/serving/types";

export type PredictionMapHorizon =
  1 | 2 | 3 | 4;

export type PredictionMapData = {
  codigo_ibge_7: string[];
  score: number[];
  predicao: boolean[];
};

export type PredictionMapContract = {
  schema_version:
    SchemaVersion;

  ano_epidemiologico:
    number;

  semana_epidemiologica:
    number;

  data_inicio_semana:
    string;

  horizonte:
    PredictionMapHorizon;

  threshold:
    number;

  count:
    number;

  data:
    PredictionMapData;
};

export type PredictionMapIndexHorizon = {
  horizonte:
    PredictionMapHorizon;

  threshold:
    number;

  semanas:
    number[];
};

export type PredictionMapIndexContract = {
  schema_version:
    SchemaVersion;

  status:
    "APROVADO";

  avaliacao:
    "retrospectiva_2025";

  ano_epidemiologico:
    number;

  municipios:
    number;

  predicoes:
    number;

  arquivos:
    number;

  horizontes: {
    h1:
    PredictionMapIndexHorizon;

    h2:
    PredictionMapIndexHorizon;

    h3:
    PredictionMapIndexHorizon;

    h4:
    PredictionMapIndexHorizon;
  };
};