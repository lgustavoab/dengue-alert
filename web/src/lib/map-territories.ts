import type {
  TerritoryFilterItem,
} from "@/lib/serving/types";

const EXPECTED_TERRITORIES =
  5_571;

const EXPECTED_PREDICTION_TERRITORIES =
  5_569;

export type MapTerritoryIndex = {
  items: TerritoryFilterItem[];
  byCode: Map<string, TerritoryFilterItem>;
  predictionAvailable: number;
  predictionUnavailable: number;
};

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object"
    && value !== null
    && !Array.isArray(value)
  );
}

function readString(
  record: Record<string, unknown>,
  key: string,
): string {
  const value =
    record[key];

  if (
    typeof value !== "string"
    || value.trim().length === 0
  ) {
    throw new Error(
      `Campo territorial inválido: ${key}.`,
    );
  }

  return value;
}

function readInteger(
  record: Record<string, unknown>,
  key: string,
): number {
  const value =
    record[key];

  if (
    typeof value !== "number"
    || !Number.isInteger(value)
  ) {
    throw new Error(
      `Campo territorial inválido: ${key}.`,
    );
  }

  return value;
}

function readBoolean(
  record: Record<string, unknown>,
  key: string,
): boolean {
  const value =
    record[key];

  if (
    typeof value !== "boolean"
  ) {
    throw new Error(
      `Campo territorial inválido: ${key}.`,
    );
  }

  return value;
}

function parseTerritoryItem(
  value: unknown,
): TerritoryFilterItem {
  if (
    !isRecord(value)
  ) {
    throw new Error(
      "Item territorial inválido.",
    );
  }

  const codigoIbge7 =
    readString(
      value,
      "codigoIbge7",
    );

  const codigoUfIbge =
    readString(
      value,
      "codigoUfIbge",
    );

  if (
    !/^\d{7}$/.test(
      codigoIbge7,
    )
  ) {
    throw new Error(
      `Código IBGE municipal inválido: ${codigoIbge7}.`,
    );
  }

  if (
    !/^\d{2}$/.test(
      codigoUfIbge,
    )
  ) {
    throw new Error(
      `Código IBGE da UF inválido: ${codigoUfIbge}.`,
    );
  }

  const anosDisponiveis =
    readInteger(
      value,
      "anosDisponiveis",
    );

  if (
    anosDisponiveis <= 0
  ) {
    throw new Error(
      `Quantidade de anos disponível inválida para ${codigoIbge7}.`,
    );
  }

  return {
    codigoIbge7,

    nomeMunicipio:
      readString(
        value,
        "nomeMunicipio",
      ),

    codigoUfIbge,

    nomeUf:
      readString(
        value,
        "nomeUf",
      ),

    regiao:
      readString(
        value,
        "regiao",
      ),

    anosDisponiveis,

    riscoHistoricoDisponivel:
      readBoolean(
        value,
        "riscoHistoricoDisponivel",
      ),

    predicaoDisponivel:
      readBoolean(
        value,
        "predicaoDisponivel",
      ),
  };
}

export function parseMapTerritoryIndex(
  payload: unknown,
): MapTerritoryIndex {
  if (
    !isRecord(payload)
  ) {
    throw new Error(
      "Índice territorial inválido.",
    );
  }

  if (
    payload.schema_version !== "1.0"
  ) {
    throw new Error(
      "Versão do índice territorial inválida.",
    );
  }

  if (
    payload.count !== EXPECTED_TERRITORIES
  ) {
    throw new Error(
      "Quantidade territorial divergente. "
      + `Esperado: ${EXPECTED_TERRITORIES}; `
      + `obtido: ${String(payload.count)}.`,
    );
  }

  if (
    !Array.isArray(
      payload.items,
    )
    || payload.items.length !== EXPECTED_TERRITORIES
  ) {
    throw new Error(
      "Lista territorial incompatível com o mapa.",
    );
  }

  const items =
    payload.items.map(
      parseTerritoryItem,
    );

  const byCode =
    new Map<
      string,
      TerritoryFilterItem
    >();

  let predictionAvailable =
    0;

  let predictionUnavailable =
    0;

  for (
    const territory
    of items
  ) {
    if (
      byCode.has(
        territory.codigoIbge7,
      )
    ) {
      throw new Error(
        `Código territorial duplicado: ${territory.codigoIbge7}.`,
      );
    }

    byCode.set(
      territory.codigoIbge7,
      territory,
    );

    if (
      territory.predicaoDisponivel
    ) {
      predictionAvailable +=
        1;
    } else {
      predictionUnavailable +=
        1;
    }
  }

  if (
    predictionAvailable
    !== EXPECTED_PREDICTION_TERRITORIES
    || predictionUnavailable
      !== EXPECTED_TERRITORIES
        - EXPECTED_PREDICTION_TERRITORIES
  ) {
    throw new Error(
      "Cobertura territorial preditiva divergente.",
    );
  }

  return {
    items,
    byCode,
    predictionAvailable,
    predictionUnavailable,
  };
}