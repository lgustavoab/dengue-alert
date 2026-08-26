import { readFile } from "node:fs/promises";
import path from "node:path";

import type {
  HistoricalMunicipalitySeriesContract,
  HistoricalMunicipalitySeriesData,
  PredictionMunicipalitySeriesContract,
  PredictionMunicipalitySeriesData,
} from "@/lib/serving/types";

const projectRoot = path.resolve(
  process.cwd(),
  "..",
);

const canonicalServingRoot =
  path.join(
    projectRoot,
    "data",
    "serving",
  );

const ibgeCodePattern =
  /^\d{7}$/;

export class MunicipalitySeriesNotFoundError extends Error {
  constructor(
    code: string,
  ) {
    super(
      `Série municipal não encontrada para o código IBGE ${code}.`,
    );

    this.name =
      "MunicipalitySeriesNotFoundError";
  }
}

function assertIbgeCode(
  code: string,
): void {
  if (
    !ibgeCodePattern.test(
      code,
    )
  ) {
    throw new TypeError(
      "Código IBGE inválido. O código deve possuir exatamente 7 dígitos.",
    );
  }
}

function isNodeError(
  error: unknown,
): error is NodeJS.ErrnoException {
  return (
    error instanceof Error
    && "code" in error
  );
}

async function readCanonicalJson(
  filePath: string,
  code: string,
): Promise<unknown> {
  let content: string;

  try {
    content = await readFile(
      filePath,
      "utf-8",
    );
  } catch (error) {
    if (
      isNodeError(
        error,
      )
      && error.code === "ENOENT"
    ) {
      throw new MunicipalitySeriesNotFoundError(
        code,
      );
    }

    throw new Error(
      `Falha ao ler série municipal ${code}.`,
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
      `JSON inválido na série municipal ${code}.`,
      {
        cause: error,
      },
    );
  }
}

function assertBaseContract(
  value: unknown,
  code: string,
): asserts value is Record<
  string,
  unknown
> {
  if (
    typeof value !== "object"
    || value === null
    || Array.isArray(
      value,
    )
  ) {
    throw new TypeError(
      `Série municipal ${code} não possui objeto JSON na raiz.`,
    );
  }

  const record =
    value as Record<
      string,
      unknown
    >;

  if (
    record.schema_version
    !== "1.0"
  ) {
    throw new Error(
      `Série municipal ${code} possui schema_version incompatível.`,
    );
  }

  if (
    record.codigo_ibge_7
    !== code
  ) {
    throw new Error(
      `Código IBGE interno diverge da série solicitada: ${code}.`,
    );
  }

  if (
    typeof record.count
      !== "number"
    || !Number.isInteger(
      record.count,
    )
    || record.count < 0
  ) {
    throw new TypeError(
      `Série municipal ${code} possui count inválido.`,
    );
  }
}

function assertColumnarData(
  data: unknown,
  expectedColumns: readonly string[],
  expectedCount: number,
  code: string,
): asserts data is Record<
  string,
  unknown[]
> {
  if (
    typeof data !== "object"
    || data === null
    || Array.isArray(
      data,
    )
  ) {
    throw new TypeError(
      `Série municipal ${code} possui bloco data inválido.`,
    );
  }

  const record =
    data as Record<
      string,
      unknown
    >;

  for (
    const column
    of expectedColumns
  ) {
    const values =
      record[
        column
      ];

    if (
      !Array.isArray(
        values,
      )
    ) {
      throw new TypeError(
        `Série municipal ${code} possui coluna inválida: ${column}.`,
      );
    }

    if (
      values.length
      !== expectedCount
    ) {
      throw new Error(
        `Série municipal ${code} possui comprimento divergente em ${column}.`,
      );
    }
  }
}

const historicalColumns = [
  "ano_epidemiologico",
  "semana_epidemiologica",
  "data_inicio_semana",
  "casos_provaveis",
  "incidencia_100mil",
  "registro_sinan_presente",
  "zero_preenchido",
  "populacao",
] as const;

const predictionColumns = [
  "ano_epidemiologico",
  "semana_epidemiologica",
  "data_inicio_semana",
  "risco_elevado",
  "target",
  "score",
  "predicao",
] as const;

export async function getHistoricalMunicipalitySeries(
  code: string,
): Promise<HistoricalMunicipalitySeriesContract> {
  assertIbgeCode(
    code,
  );

  const filePath =
    path.join(
      canonicalServingRoot,
      "historical",
      "municipality",
      "series",
      `${code}.json`,
    );

  const value =
    await readCanonicalJson(
      filePath,
      code,
    );

  assertBaseContract(
    value,
    code,
  );

  assertColumnarData(
    value.data,
    historicalColumns,
    value.count as number,
    code,
  );

  return value as unknown as HistoricalMunicipalitySeriesContract;
}

function assertPredictionHorizon(
  value: unknown,
  horizon: string,
  code: string,
): void {
  if (
    typeof value !== "object"
    || value === null
    || Array.isArray(
      value,
    )
  ) {
    throw new TypeError(
      `Série preditiva ${code} possui horizonte ${horizon} inválido.`,
    );
  }

  const record =
    value as Record<
      string,
      unknown
    >;

  if (
    typeof record.count
      !== "number"
    || !Number.isInteger(
      record.count,
    )
    || record.count < 0
  ) {
    throw new TypeError(
      `Série preditiva ${code} possui count inválido em ${horizon}.`,
    );
  }

  if (
    typeof record.threshold
      !== "number"
    || !Number.isFinite(
      record.threshold,
    )
  ) {
    throw new TypeError(
      `Série preditiva ${code} possui threshold inválido em ${horizon}.`,
    );
  }

  assertColumnarData(
    record.data,
    predictionColumns,
    record.count,
    code,
  );
}

export async function getPredictionMunicipalitySeries(
  code: string,
): Promise<PredictionMunicipalitySeriesContract> {
  assertIbgeCode(
    code,
  );

  const filePath =
    path.join(
      canonicalServingRoot,
      "prediction",
      "municipality",
      "series",
      `${code}.json`,
    );

  const value =
    await readCanonicalJson(
      filePath,
      code,
    );

  assertBaseContract(
    value,
    code,
  );

  const horizons =
    value.horizontes;

  if (
    typeof horizons
      !== "object"
    || horizons === null
    || Array.isArray(
      horizons,
    )
  ) {
    throw new TypeError(
      `Série preditiva ${code} possui bloco horizontes inválido.`,
    );
  }

  const horizonRecord =
    horizons as Record<
      string,
      unknown
    >;

  for (
    const horizon
    of [
      "h1",
      "h2",
      "h3",
      "h4",
    ]
  ) {
    assertPredictionHorizon(
      horizonRecord[
        horizon
      ],
      horizon,
      code,
    );
  }

  return value as unknown as PredictionMunicipalitySeriesContract;
}

export type {
  HistoricalMunicipalitySeriesData,
  PredictionMunicipalitySeriesData,
};