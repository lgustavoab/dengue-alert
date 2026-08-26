import type {
  TerritoryFilterItem,
} from "@/lib/serving/types";

const DEFAULT_RESULT_LIMIT =
  8;

function normalizeSearchText(
  value: string,
): string {
  return value
    .normalize(
      "NFD",
    )
    .replace(
      /\p{Diacritic}/gu,
      "",
    )
    .trim()
    .toLocaleLowerCase(
      "pt-BR",
    );
}

function getSearchRank(
  territory: TerritoryFilterItem,
  query: string,
): number | null {
  const normalizedName =
    normalizeSearchText(
      territory.nomeMunicipio,
    );

  const normalizedCode =
    normalizeSearchText(
      territory.codigoIbge7,
    );

  if (
    normalizedCode === query
  ) {
    return 0;
  }

  if (
    normalizedName === query
  ) {
    return 1;
  }

  if (
    normalizedName.startsWith(
      query,
    )
  ) {
    return 2;
  }

  if (
    normalizedCode.startsWith(
      query,
    )
  ) {
    return 3;
  }

  if (
    normalizedName.includes(
      query,
    )
  ) {
    return 4;
  }

  return null;
}

export function searchMapTerritories(
  territories: TerritoryFilterItem[],
  query: string,
  limit: number = DEFAULT_RESULT_LIMIT,
): TerritoryFilterItem[] {
  const normalizedQuery =
    normalizeSearchText(
      query,
    );

  if (
    normalizedQuery.length === 0
  ) {
    return [];
  }

  if (
    !Number.isInteger(
      limit,
    )
    || limit <= 0
  ) {
    throw new Error(
      "O limite da busca municipal deve ser um inteiro positivo.",
    );
  }

  return territories
    .map(
      (
        territory,
        position,
      ) => ({
        territory,

        position,

        rank:
          getSearchRank(
            territory,
            normalizedQuery,
          ),
      }),
    )
    .filter(
      (
        result,
      ): result is {
        territory:
          TerritoryFilterItem;

        position:
          number;

        rank:
          number;
      } =>
        result.rank
        !== null,
    )
    .sort(
      (
        left,
        right,
      ) => {
        if (
          left.rank
          !== right.rank
        ) {
          return (
            left.rank
            - right.rank
          );
        }

        return (
          left.position
          - right.position
        );
      },
    )
    .slice(
      0,
      limit,
    )
    .map(
      ({
        territory,
      }) =>
        territory,
    );
}

export function formatMapTerritorySearchLabel(
  territory: TerritoryFilterItem,
): string {
  return (
    `${territory.nomeMunicipio}`
    + ` · ${territory.nomeUf}`
    + ` · ${territory.codigoIbge7}`
  );
}