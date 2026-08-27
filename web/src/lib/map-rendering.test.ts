import {
  readFile,
} from "node:fs/promises";

import path from "node:path";

import {
  describe,
  expect,
  it,
} from "vitest";

import {
  parseMunicipalityTopology,
} from "@/lib/map-geography";

import {
  MAP_VIEWBOX_HEIGHT,
  MAP_VIEWBOX_PADDING,
  MAP_VIEWBOX_WIDTH,
  buildMunicipalitySvgPaths,
} from "@/lib/map-rendering";
import {
  getActiveServingRoot,
} from "@/lib/serving/runtime-paths";

async function loadOfficialGeography() {
  const topologyPath =
    path.join(
      await getActiveServingRoot(),
      "geography",
      "municipalities.topojson",
    );

  const topology =
    JSON.parse(
      await readFile(
        topologyPath,
        "utf-8",
      ),
    ) as unknown;

  return parseMunicipalityTopology(
    topology,
  );
}

describe(
  "map rendering",
  () => {
    it(
      "define um viewBox cartográfico válido",
      () => {
        expect(
          MAP_VIEWBOX_WIDTH,
        ).toBeGreaterThan(
          0,
        );

        expect(
          MAP_VIEWBOX_HEIGHT,
        ).toBeGreaterThan(
          0,
        );

        expect(
          MAP_VIEWBOX_PADDING,
        ).toBeGreaterThanOrEqual(
          0,
        );

        expect(
          MAP_VIEWBOX_PADDING * 2,
        ).toBeLessThan(
          MAP_VIEWBOX_WIDTH,
        );

        expect(
          MAP_VIEWBOX_PADDING * 2,
        ).toBeLessThan(
          MAP_VIEWBOX_HEIGHT,
        );
      },
    );

    it(
      "rejeita dimensões de renderização inválidas",
      async () => {
        const geography =
          await loadOfficialGeography();

        expect(
          () =>
            buildMunicipalitySvgPaths(
              geography.featureCollection,
              0,
              720,
              24,
            ),
        ).toThrow(
          "Dimensões inválidas",
        );

        expect(
          () =>
            buildMunicipalitySvgPaths(
              geography.featureCollection,
              960,
              720,
              500,
            ),
        ).toThrow(
          "Dimensões inválidas",
        );
      },
      30_000,
    );

    it(
      "gera exatamente 5.571 paths SVG para a malha oficial",
      async () => {
        const geography =
          await loadOfficialGeography();

        const paths =
          buildMunicipalitySvgPaths(
            geography.featureCollection,
          );

        expect(
          paths,
        ).toHaveLength(
          5_571,
        );

        expect(
          new Set(
            paths.map(
              (item) =>
                item.codigoIbge7,
            ),
          ).size,
        ).toBe(
          5_571,
        );
      },
      30_000,
    );

    it(
      "gera paths não vazios e sem valores numéricos inválidos",
      async () => {
        const geography =
          await loadOfficialGeography();

        const paths =
          buildMunicipalitySvgPaths(
            geography.featureCollection,
          );

        for (
          const municipality
          of paths
        ) {
          expect(
            municipality.d.length,
          ).toBeGreaterThan(
            0,
          );

          expect(
            municipality.d,
          ).not.toMatch(
            /NaN|Infinity/,
          );
        }
      },
      30_000,
    );

    it(
      "preserva códigos municipais reais durante a projeção",
      async () => {
        const geography =
          await loadOfficialGeography();

        const paths =
          buildMunicipalitySvgPaths(
            geography.featureCollection,
          );

        const ids =
          new Set(
            paths.map(
              (item) =>
                item.codigoIbge7,
            ),
          );

        expect(
          ids.has(
            "3537305",
          ),
        ).toBe(
          true,
        );

        expect(
          ids.has(
            "2504108",
          ),
        ).toBe(
          true,
        );

        expect(
          ids.has(
            "1707405",
          ),
        ).toBe(
          true,
        );
      },
      30_000,
    );

    it(
      "produz resultado determinístico para a mesma malha",
      async () => {
        const geography =
          await loadOfficialGeography();

        const first =
          buildMunicipalitySvgPaths(
            geography.featureCollection,
          );

        const second =
          buildMunicipalitySvgPaths(
            geography.featureCollection,
          );

        expect(
          second,
        ).toEqual(
          first,
        );
      },
      30_000,
    );
  },
);
