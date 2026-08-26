import {
  describe,
  expect,
  it,
} from "vitest";

import {
  formatMapTerritorySearchLabel,
  searchMapTerritories,
} from "@/lib/map-territory-search";

import type {
  TerritoryFilterItem,
} from "@/lib/serving/types";

const territories:
TerritoryFilterItem[] = [
  {
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

    anosDisponiveis:
      10,

    riscoHistoricoDisponivel:
      true,

    predicaoDisponivel:
      true,
  },
  {
    codigoIbge7:
      "3550308",

    nomeMunicipio:
      "São Paulo",

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
      true,
  },
  {
    codigoIbge7:
      "5003207",

    nomeMunicipio:
      "Corumbá",

    codigoUfIbge:
      "50",

    nomeUf:
      "Mato Grosso do Sul",

    regiao:
      "Centro-Oeste",

    anosDisponiveis:
      10,

    riscoHistoricoDisponivel:
      true,

    predicaoDisponivel:
      true,
  },
];

describe(
  "map territory search",
  () => {
    it(
      "encontra município ignorando acentos",
      () => {
        const result =
          searchMapTerritories(
            territories,
            "penapolis",
          );

        expect(
          result,
        ).toHaveLength(
          1,
        );

        expect(
          result[0]
            .codigoIbge7,
        ).toBe(
          "3537305",
        );
      },
    );

    it(
      "encontra município pelo código IBGE completo",
      () => {
        const result =
          searchMapTerritories(
            territories,
            "5003207",
          );

        expect(
          result,
        ).toHaveLength(
          1,
        );

        expect(
          result[0]
            .nomeMunicipio,
        ).toBe(
          "Corumbá",
        );
      },
    );

    it(
      "prioriza correspondência exata do nome",
      () => {
        const result =
          searchMapTerritories(
            territories,
            "sao paulo",
          );

        expect(
          result[0]
            .codigoIbge7,
        ).toBe(
          "3550308",
        );
      },
    );

    it(
      "respeita o limite de resultados",
      () => {
        const result =
          searchMapTerritories(
            territories,
            "a",
            2,
          );

        expect(
          result,
        ).toHaveLength(
          2,
        );
      },
    );

    it(
      "gera rótulo acessível com município, UF e código",
      () => {
        expect(
          formatMapTerritorySearchLabel(
            territories[0],
          ),
        ).toBe(
          "Penápolis · São Paulo · 3537305",
        );
      },
    );

    it(
      "retorna vazio para busca sem conteúdo",
      () => {
        expect(
          searchMapTerritories(
            territories,
            "   ",
          ),
        ).toEqual(
          [],
        );
      },
    );
  },
);