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

type SyntheticGeometry = {
  type: string;
  id: string;
  arcs: number[][];
};

type SyntheticGeometryCollection = {
  type: string;
  geometries: SyntheticGeometry[];
};

type SyntheticTopology = {
  type: string;
  objects: {
    municipalities: SyntheticGeometryCollection;
    [key: string]: SyntheticGeometryCollection;
  };
  arcs: number[][][];
};

function createSyntheticTopology(): SyntheticTopology {
  return {
    type:
      "Topology",

    objects: {
      municipalities: {
        type:
          "GeometryCollection",

        geometries:
          Array.from(
            {
              length:
                5_571,
            },
            (
              _item,
              position,
            ) => ({
              type:
                "Polygon",

              id:
                String(
                  1_000_000
                  + position,
                ),

              arcs: [
                [
                  position,
                ],
              ],
            }),
          ),
      },
    },

    arcs:
      Array.from(
        {
          length:
            5_571,
        },
        (
          _item,
          position,
        ) => [
            [
              position,
              0,
            ],
            [
              1,
              0,
            ],
            [
              0,
              1,
            ],
            [
              -1,
              0,
            ],
            [
              0,
              -1,
            ],
          ],
      ),
  };
}

describe(
  "map geography",
  () => {
    it(
      "converte uma Topology municipal válida em FeatureCollection",
      () => {
        const geography =
          parseMunicipalityTopology(
            createSyntheticTopology(),
          );

        expect(
          geography.objectName,
        ).toBe(
          "municipalities",
        );

        expect(
          geography.featureCollection.type,
        ).toBe(
          "FeatureCollection",
        );

        expect(
          geography.featureCollection.features,
        ).toHaveLength(
          5_571,
        );

        expect(
          geography.municipalityIds,
        ).toHaveLength(
          5_571,
        );

        expect(
          new Set(
            geography.municipalityIds,
          ).size,
        ).toBe(
          5_571,
        );
      },
    );

    it(
      "normaliza IDs municipais para sete dígitos",
      () => {
        const topology =
          createSyntheticTopology();

        topology.objects
          .municipalities
          .geometries[0]
          .id =
          "123456";

        const geography =
          parseMunicipalityTopology(
            topology,
          );

        expect(
          geography.municipalityIds[0],
        ).toBe(
          "0123456",
        );

        expect(
          geography.featureCollection
            .features[0]
            .id,
        ).toBe(
          "0123456",
        );
      },
    );

    it(
      "rejeita payload que não seja Topology",
      () => {
        expect(
          () =>
            parseMunicipalityTopology(
              {
                type:
                  "FeatureCollection",
              },
            ),
        ).toThrow(
          "type=Topology",
        );
      },
    );

    it(
      "rejeita TopoJSON com mais de um objeto geográfico",
      () => {
        const topology =
          createSyntheticTopology();

        topology.objects =
        {
          ...topology.objects,

          another:
            topology.objects
              .municipalities,
        };

        expect(
          () =>
            parseMunicipalityTopology(
              topology,
            ),
        ).toThrow(
          "exatamente um objeto",
        );
      },
    );

    it(
      "rejeita quantidade territorial divergente",
      () => {
        const topology =
          createSyntheticTopology();

        topology.objects
          .municipalities
          .geometries
          .pop();

        expect(
          () =>
            parseMunicipalityTopology(
              topology,
            ),
        ).toThrow(
          "Quantidade de geometrias municipais divergente",
        );
      },
    );

    it(
      "rejeita códigos municipais duplicados",
      () => {
        const topology =
          createSyntheticTopology();

        topology.objects
          .municipalities
          .geometries[1]
          .id =
          topology.objects
            .municipalities
            .geometries[0]
            .id;

        expect(
          () =>
            parseMunicipalityTopology(
              topology,
            ),
        ).toThrow(
          "códigos IBGE municipais duplicados",
        );
      },
    );

    it(
      "converte o asset geográfico oficial com 5.571 municípios únicos",
      async () => {
        const projectRoot =
          path.resolve(
            process.cwd(),
            "..",
          );

        const topologyPath =
          path.join(
            projectRoot,
            "data",
            "serving",
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

        const geography =
          parseMunicipalityTopology(
            topology,
          );

        expect(
          geography.objectName,
        ).toBe(
          "BR_Municipios_2024_prepared",
        );

        expect(
          geography.featureCollection
            .features,
        ).toHaveLength(
          5_571,
        );

        expect(
          geography.municipalityIds,
        ).toHaveLength(
          5_571,
        );

        expect(
          new Set(
            geography.municipalityIds,
          ).size,
        ).toBe(
          5_571,
        );

        expect(
          geography.municipalityIds,
        ).toContain(
          "2504108",
        );

        expect(
          geography.municipalityIds,
        ).toContain(
          "1707405",
        );

        expect(
          geography.municipalityIds,
        ).toContain(
          "3537305",
        );
      },
      30_000,
    );
  },
);