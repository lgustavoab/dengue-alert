import {
  describe,
  expect,
  it,
} from "vitest";

import {
  parseMapTerritoryIndex,
} from "@/lib/map-territories";

import {
  getTerritoryFilterItems,
} from "@/lib/serving/server";

function createTerritory(
  position: number,
) {
  return {
    codigoIbge7:
      String(
        1_000_000
        + position,
      ),

    nomeMunicipio:
      `Município ${position}`,

    codigoUfIbge:
      "35",

    nomeUf:
      "São Paulo",

    regiao:
      "Sudeste",

    anosDisponiveis:
      10,

    riscoHistoricoDisponivel:
      true,

    predicaoDisponivel:
      position < 5_569,
  };
}

function createPayload() {
  const items =
    Array.from(
      {
        length:
          5_571,
      },
      (
        _item,
        position,
      ) =>
        createTerritory(
          position,
        ),
    );

  return {
    schema_version:
      "1.0",

    count:
      items.length,

    items,
  };
}

describe(
  "map territories",
  () => {
    it(
      "indexa exatamente 5.571 territórios únicos",
      () => {
        const result =
          parseMapTerritoryIndex(
            createPayload(),
          );

        expect(
          result.items,
        ).toHaveLength(
          5_571,
        );

        expect(
          result.byCode.size,
        ).toBe(
          5_571,
        );

        expect(
          result.predictionAvailable,
        ).toBe(
          5_569,
        );

        expect(
          result.predictionUnavailable,
        ).toBe(
          2,
        );
      },
    );

    it(
      "rejeita código municipal duplicado",
      () => {
        const payload =
          createPayload();

        payload.items[1].codigoIbge7 =
          payload.items[0].codigoIbge7;

        expect(
          () =>
            parseMapTerritoryIndex(
              payload,
            ),
        ).toThrow(
          "Código territorial duplicado",
        );
      },
    );

    it(
      "rejeita cobertura preditiva divergente",
      () => {
        const payload =
          createPayload();

        payload.items[5_569]
          .predicaoDisponivel =
          true;

        expect(
          () =>
            parseMapTerritoryIndex(
              payload,
            ),
        ).toThrow(
          "Cobertura territorial preditiva divergente",
        );
      },
    );

    it(
      "rejeita código IBGE municipal fora do formato esperado",
      () => {
        const payload =
          createPayload();

        payload.items[0].codigoIbge7 =
          "123";

        expect(
          () =>
            parseMapTerritoryIndex(
              payload,
            ),
        ).toThrow(
          "Código IBGE municipal inválido",
        );
      },
    );

    it(
      "valida o índice territorial oficial usado pela aplicação",
      async () => {
        const items =
          await getTerritoryFilterItems();

        const result =
          parseMapTerritoryIndex({
            schema_version:
              "1.0",

            count:
              items.length,

            items,
          });

        expect(
          result.items,
        ).toHaveLength(
          5_571,
        );

        expect(
          result.byCode.size,
        ).toBe(
          5_571,
        );

        expect(
          result.predictionAvailable,
        ).toBe(
          5_569,
        );

        expect(
          result.predictionUnavailable,
        ).toBe(
          2,
        );

        const penapolis =
          result.byCode.get(
            "3537305",
          );

        expect(
          penapolis,
        ).toBeDefined();

        expect(
          penapolis?.nomeMunicipio,
        ).toBe(
          "Penápolis",
        );

        expect(
          penapolis?.nomeUf,
        ).toBe(
          "São Paulo",
        );
      },
      30_000,
    );
  },
);