import {
  readFile,
} from "node:fs/promises";
import path from "node:path";

import type {
  PredictionMapContract,
  PredictionMapHorizon,
  PredictionMapIndexContract,
} from "@/lib/serving/prediction-map-types";
import {
  getActiveServingRoot,
} from "@/lib/serving/runtime-paths";

async function getPredictionMapRoot(): Promise<string> {
  return path.join(
    await getActiveServingRoot(),
    "prediction",
    "map",
  );
}

const expectedYear =
  2025;

const expectedMunicipalities =
  5_569;

const expectedPredictions =
  1_124_938;

const expectedFiles =
  202;

const expectedWeeks: Record<
  PredictionMapHorizon,
  number
> = {
  1: 52,
  2: 51,
  3: 50,
  4: 49,
};

const expectedThresholds: Record<
  PredictionMapHorizon,
  number
> = {
  1: 0.187687,
  2: 0.190783,
  3: 0.167991,
  4: 0.157138,
};

const ibgeCodePattern =
  /^\d{7}$/;

const datePattern =
  /^\d{4}-\d{2}-\d{2}$/;

export class PredictionMapSelectionError
  extends Error {
  constructor(
    message: string,
  ) {
    super(
      message,
    );

    this.name =
      "PredictionMapSelectionError";
  }
}

export class PredictionMapUnavailableError
  extends Error {
  constructor(
    horizon: number,
    week: number,
  ) {
    super(
      `Predição do mapa indisponível para H${horizon} na SE${week}.`,
    );

    this.name =
      "PredictionMapUnavailableError";
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

function assertObject(
  value: unknown,
  label: string,
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
      `${label} deve ser um objeto.`,
    );
  }
}

function assertHorizon(
  value: number,
): asserts value is PredictionMapHorizon {
  if (
    !Number.isInteger(
      value,
    )
    || ![
      1,
      2,
      3,
      4,
    ].includes(
      value,
    )
  ) {
    throw new PredictionMapSelectionError(
      "Horizonte inválido. Use H1, H2, H3 ou H4.",
    );
  }
}

function assertWeek(
  value: number,
): void {
  if (
    !Number.isInteger(
      value,
    )
    || value < 1
    || value > 52
  ) {
    throw new PredictionMapSelectionError(
      "Semana epidemiológica inválida. Use valores entre 1 e 52.",
    );
  }
}

function assertAvailableSelection(
  horizon: PredictionMapHorizon,
  week: number,
): void {
  const maximumWeek =
    expectedWeeks[
      horizon
    ];

  if (
    week > maximumWeek
  ) {
    throw new PredictionMapUnavailableError(
      horizon,
      week,
    );
  }
}

async function readJson(
  filePath: string,
): Promise<unknown> {
  let content: string;

  try {
    content =
      await readFile(
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
      throw error;
    }

    throw new Error(
      `Falha ao ler contrato de mapa: ${filePath}.`,
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
      `JSON inválido no contrato de mapa: ${filePath}.`,
      {
        cause: error,
      },
    );
  }
}

function thresholdMatches(
  obtained: number,
  expected: number,
): boolean {
  return (
    Math.abs(
      obtained
      - expected,
    )
    <= 1e-12
  );
}

function assertNumberArray(
  value: unknown,
  label: string,
  expectedLength: number,
): asserts value is number[] {
  if (
    !Array.isArray(
      value,
    )
    || value.length
      !== expectedLength
  ) {
    throw new TypeError(
      `${label} possui estrutura ou comprimento inválido.`,
    );
  }

  for (
    const item
    of value
  ) {
    if (
      typeof item
        !== "number"
      || !Number.isFinite(
        item,
      )
    ) {
      throw new TypeError(
        `${label} contém valor numérico inválido.`,
      );
    }
  }
}

function assertBooleanArray(
  value: unknown,
  label: string,
  expectedLength: number,
): asserts value is boolean[] {
  if (
    !Array.isArray(
      value,
    )
    || value.length
      !== expectedLength
  ) {
    throw new TypeError(
      `${label} possui estrutura ou comprimento inválido.`,
    );
  }

  for (
    const item
    of value
  ) {
    if (
      typeof item
        !== "boolean"
    ) {
      throw new TypeError(
        `${label} contém valor booleano inválido.`,
      );
    }
  }
}

function assertCodeArray(
  value: unknown,
  expectedLength: number,
): asserts value is string[] {
  if (
    !Array.isArray(
      value,
    )
    || value.length
      !== expectedLength
  ) {
    throw new TypeError(
      "codigo_ibge_7 possui estrutura ou comprimento inválido.",
    );
  }

  let previousCode:
    string | null = null;

  const uniqueCodes =
    new Set<string>();

  for (
    const item
    of value
  ) {
    if (
      typeof item
        !== "string"
      || !ibgeCodePattern.test(
        item,
      )
    ) {
      throw new TypeError(
        "codigo_ibge_7 contém código inválido.",
      );
    }

    if (
      previousCode !== null
      && item <= previousCode
    ) {
      throw new Error(
        "codigo_ibge_7 não está estritamente ordenado.",
      );
    }

    uniqueCodes.add(
      item,
    );

    previousCode =
      item;
  }

  if (
    uniqueCodes.size
    !== expectedLength
  ) {
    throw new Error(
      "codigo_ibge_7 contém códigos duplicados.",
    );
  }
}

function assertPredictionMapContract(
  value: unknown,
  expectedHorizon: PredictionMapHorizon,
  expectedWeek: number,
): asserts value is PredictionMapContract {
  assertObject(
    value,
    "Contrato do mapa",
  );

  if (
    value.schema_version
    !== "1.0"
  ) {
    throw new Error(
      "schema_version incompatível no contrato do mapa.",
    );
  }

  if (
    value.ano_epidemiologico
    !== expectedYear
  ) {
    throw new Error(
      "Ano epidemiológico divergente no contrato do mapa.",
    );
  }

  if (
    value.horizonte
    !== expectedHorizon
  ) {
    throw new Error(
      "Horizonte interno divergente no contrato do mapa.",
    );
  }

  if (
    value.semana_epidemiologica
    !== expectedWeek
  ) {
    throw new Error(
      "Semana interna divergente no contrato do mapa.",
    );
  }

  if (
    typeof value.data_inicio_semana
      !== "string"
    || !datePattern.test(
      value.data_inicio_semana,
    )
  ) {
    throw new TypeError(
      "data_inicio_semana inválida no contrato do mapa.",
    );
  }

  if (
    typeof value.threshold
      !== "number"
    || !Number.isFinite(
      value.threshold,
    )
    || !thresholdMatches(
      value.threshold,
      expectedThresholds[
        expectedHorizon
      ],
    )
  ) {
    throw new Error(
      "Threshold divergente no contrato do mapa.",
    );
  }

  if (
    value.count
    !== expectedMunicipalities
  ) {
    throw new Error(
      "Quantidade municipal divergente no contrato do mapa.",
    );
  }

  assertObject(
    value.data,
    "Bloco data do mapa",
  );

  assertCodeArray(
    value.data.codigo_ibge_7,
    expectedMunicipalities,
  );

  assertNumberArray(
    value.data.score,
    "score",
    expectedMunicipalities,
  );

  assertBooleanArray(
    value.data.predicao,
    "predicao",
    expectedMunicipalities,
  );

  for (
    let index = 0;
    index
      < expectedMunicipalities;
    index += 1
  ) {
    const score =
      value.data.score[
        index
      ];

    const prediction =
      value.data.predicao[
        index
      ];

    if (
      score < 0
      || score > 1
    ) {
      throw new Error(
        "Score fora do intervalo [0, 1] no contrato do mapa.",
      );
    }

    const calculatedPrediction =
      score
      >= value.threshold;

    if (
      prediction
      !== calculatedPrediction
    ) {
      throw new Error(
        "Predição divergente da regra score >= threshold no contrato do mapa.",
      );
    }
  }
}

function assertIndexHorizon(
  value: unknown,
  expectedHorizon: PredictionMapHorizon,
): void {
  assertObject(
    value,
    `Índice H${expectedHorizon}`,
  );

  if (
    value.horizonte
    !== expectedHorizon
  ) {
    throw new Error(
      `Horizonte divergente no índice H${expectedHorizon}.`,
    );
  }

  if (
    typeof value.threshold
      !== "number"
    || !Number.isFinite(
      value.threshold,
    )
    || !thresholdMatches(
      value.threshold,
      expectedThresholds[
        expectedHorizon
      ],
    )
  ) {
    throw new Error(
      `Threshold divergente no índice H${expectedHorizon}.`,
    );
  }

  const weeks =
    value.semanas;

  if (
    !Array.isArray(
      weeks,
    )
  ) {
    throw new TypeError(
      `Semanas inválidas no índice H${expectedHorizon}.`,
    );
  }

  const expected =
    Array.from(
      {
        length:
          expectedWeeks[
            expectedHorizon
          ],
      },
      (
        _item,
        index,
      ) => index + 1,
    );

  if (
    weeks.length
      !== expected.length
    || weeks.some(
      (
        week,
        index,
      ) =>
        week
        !== expected[
          index
        ],
    )
  ) {
    throw new Error(
      `Cobertura semanal divergente no índice H${expectedHorizon}.`,
    );
  }
}

function assertPredictionMapIndex(
  value: unknown,
): asserts value is PredictionMapIndexContract {
  assertObject(
    value,
    "Índice do mapa preditivo",
  );

  if (
    value.schema_version
    !== "1.0"
    || value.status
      !== "APROVADO"
    || value.avaliacao
      !== "retrospectiva_2025"
    || value.ano_epidemiologico
      !== expectedYear
    || value.municipios
      !== expectedMunicipalities
    || value.predicoes
      !== expectedPredictions
    || value.arquivos
      !== expectedFiles
  ) {
    throw new Error(
      "Metadados divergentes no índice do mapa preditivo.",
    );
  }

  assertObject(
    value.horizontes,
    "Horizontes do índice do mapa",
  );

  assertIndexHorizon(
    value.horizontes.h1,
    1,
  );

  assertIndexHorizon(
    value.horizontes.h2,
    2,
  );

  assertIndexHorizon(
    value.horizontes.h3,
    3,
  );

  assertIndexHorizon(
    value.horizontes.h4,
    4,
  );
}

export async function getPredictionMapIndex():
Promise<PredictionMapIndexContract> {
  const predictionMapRoot =
    await getPredictionMapRoot();
  const filePath =
    path.join(
      predictionMapRoot,
      "index.json",
    );

  const value =
    await readJson(
      filePath,
    );

  assertPredictionMapIndex(
    value,
  );

  return value;
}

export async function getPredictionMapSlice(
  horizon: number,
  week: number,
): Promise<PredictionMapContract> {
  assertHorizon(
    horizon,
  );

  assertWeek(
    week,
  );

  assertAvailableSelection(
    horizon,
    week,
  );

  const predictionMapRoot =
    await getPredictionMapRoot();

  const filePath =
    path.join(
      predictionMapRoot,
      `h${horizon}`,
      `se${String(
        week,
      ).padStart(
        2,
        "0",
      )}.json`,
    );

  let value: unknown;

  try {
    value =
      await readJson(
        filePath,
      );
  } catch (error) {
    if (
      isNodeError(
        error,
      )
      && error.code === "ENOENT"
    ) {
      throw new PredictionMapUnavailableError(
        horizon,
        week,
      );
    }

    throw error;
  }

  assertPredictionMapContract(
    value,
    horizon,
    week,
  );

  return value;
}
