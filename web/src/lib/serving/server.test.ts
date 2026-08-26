import {
  describe,
  expect,
  it,
} from "vitest";

import {
  getTerritoryFilterItems,
} from "@/lib/serving/server";

describe(
  "territory serving integration",
  () => {
    it(
      "integra as 5.571 unidades territoriais",
      async () => {
        const items =
          await getTerritoryFilterItems();

        expect(
          items,
        ).toHaveLength(
          5571,
        );

        expect(
          new Set(
            items.map(
              (item) =>
                item.codigoIbge7,
            ),
          ).size,
        ).toBe(
          5571,
        );
      },
    );

    it(
      "mantém Penápolis com histórico e predição disponíveis",
      async () => {
        const items =
          await getTerritoryFilterItems();

        const penapolis =
          items.find(
            (item) =>
              item.codigoIbge7
              === "3537305",
          );

        expect(
          penapolis,
        ).toBeDefined();

        expect(
          penapolis,
        ).toMatchObject({
          codigoIbge7:
            "3537305",
          nomeMunicipio:
            "Penápolis",
          codigoUfIbge:
            "35",
          nomeUf:
            "São Paulo",
          regiao:
            "Sudeste",
          anosDisponiveis: 10,
          riscoHistoricoDisponivel:
            true,
          predicaoDisponivel:
            true,
        });
      },
    );

    it(
      "mantém Boa Esperança do Norte apenas com série epidemiológica de um ano",
      async () => {
        const items =
          await getTerritoryFilterItems();

        const territory =
          items.find(
            (item) =>
              item.codigoIbge7
              === "5101837",
          );

        expect(
          territory,
        ).toBeDefined();

        expect(
          territory,
        ).toMatchObject({
          codigoIbge7:
            "5101837",
          nomeMunicipio:
            "Boa Esperança do Norte",
          codigoUfIbge:
            "51",
          nomeUf:
            "Mato Grosso",
          regiao:
            "Centro-Oeste",
          anosDisponiveis: 1,
          riscoHistoricoDisponivel:
            false,
          predicaoDisponivel:
            false,
        });
      },
    );

    it(
      "mantém Fernando de Noronha com histórico epidemiológico e sem risco ou predição",
      async () => {
        const items =
          await getTerritoryFilterItems();

        const territory =
          items.find(
            (item) =>
              item.codigoIbge7
              === "2605459",
          );

        expect(
          territory,
        ).toBeDefined();

        expect(
          territory,
        ).toMatchObject({
          codigoIbge7:
            "2605459",
          nomeMunicipio:
            "Fernando de Noronha",
          codigoUfIbge:
            "26",
          nomeUf:
            "Pernambuco",
          regiao:
            "Nordeste",
          anosDisponiveis: 10,
          riscoHistoricoDisponivel:
            false,
          predicaoDisponivel:
            false,
        });
      },
    );

    it(
      "possui exatamente cinco regiões",
      async () => {
        const items =
          await getTerritoryFilterItems();

        const regions =
          new Set(
            items.map(
              (item) =>
                item.regiao,
            ),
          );

        expect(
          regions,
        ).toEqual(
          new Set([
            "Centro-Oeste",
            "Nordeste",
            "Norte",
            "Sudeste",
            "Sul",
          ]),
        );
      },
    );

    it(
      "possui exatamente 27 UFs",
      async () => {
        const items =
          await getTerritoryFilterItems();

        const states =
          new Set(
            items.map(
              (item) =>
                item.codigoUfIbge,
            ),
          );

        expect(
          states.size,
        ).toBe(
          27,
        );
      },
    );

    it(
      "mantém códigos de UF como identificadores textuais",
      async () => {
        const items =
          await getTerritoryFilterItems();

        expect(
          items.every(
            (item) =>
              typeof item.codigoUfIbge
              === "string",
          ),
        ).toBe(
          true,
        );

        expect(
          items.every(
            (item) =>
              /^\d{2}$/.test(
                item.codigoUfIbge,
              ),
          ),
        ).toBe(
          true,
        );
      },
    );

    it(
      "possui 5.569 territórios com histórico de risco",
      async () => {
        const items =
          await getTerritoryFilterItems();

        const available =
          items.filter(
            (item) =>
              item
                .riscoHistoricoDisponivel,
          );

        expect(
          available,
        ).toHaveLength(
          5569,
        );
      },
    );

    it(
      "possui 5.569 territórios com predição disponível",
      async () => {
        const items =
          await getTerritoryFilterItems();

        const available =
          items.filter(
            (item) =>
              item
                .predicaoDisponivel,
          );

        expect(
          available,
        ).toHaveLength(
          5569,
        );
      },
    );
  },
);