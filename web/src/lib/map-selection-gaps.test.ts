import {
  readFile,
} from "node:fs/promises";

import path from "node:path";

import {
  beforeAll,
  describe,
  expect,
  it,
} from "vitest";

import {
  getAvailableMapHorizons,
  normalizeMapSelection,
} from "@/lib/map-selection-utils";

import type {
  PredictionMapIndexContract,
} from "@/lib/serving/prediction-map-types";
import {
  getActiveServingRoot,
} from "@/lib/serving/runtime-paths";

let officialIndex:
  PredictionMapIndexContract;

beforeAll(
  async () => {
    const indexPath =
      path.join(
        await getActiveServingRoot(),
        "prediction",
        "map",
        "index.json",
      );

    officialIndex =
      JSON.parse(
        await readFile(
          indexPath,
          "utf-8",
        ),
      ) as PredictionMapIndexContract;
  },
);

describe(
  "map selection official horizon coverage",
  () => {
    it(
      "preserva a cobertura oficial de 202 arquivos",
      () => {
        expect(
          officialIndex.arquivos,
        ).toBe(
          202,
        );

        expect(
          officialIndex.horizontes
            .h1
            .semanas,
        ).toHaveLength(
          52,
        );

        expect(
          officialIndex.horizontes
            .h2
            .semanas,
        ).toHaveLength(
          51,
        );

        expect(
          officialIndex.horizontes
            .h3
            .semanas,
        ).toHaveLength(
          50,
        );

        expect(
          officialIndex.horizontes
            .h4
            .semanas,
        ).toHaveLength(
          49,
        );

        expect(
          officialIndex.horizontes
            .h4
            .semanas,
        ).toContain(
          38,
        );

        expect(
          officialIndex.horizontes
            .h4
            .semanas,
        ).toContain(
          47,
        );

        expect(
          officialIndex.horizontes
            .h4
            .semanas,
        ).toContain(
          49,
        );
      },
    );

    it(
      "mantém H4 disponível até SE49 e indisponível na SE50",
      () => {
        expect(
          getAvailableMapHorizons(
            officialIndex,
            49,
          ),
        ).toEqual([
          1,
          2,
          3,
          4,
        ]);

        expect(
          getAvailableMapHorizons(
            officialIndex,
            50,
          ),
        ).toEqual([
          1,
          2,
          3,
        ]);

        expect(
          normalizeMapSelection(
            officialIndex,
            "50",
            "4",
          ),
        ).toEqual({
          week:
            50,

          horizon:
            1,

          normalized:
            true,
        });
      },
    );

    it(
      "respeita a redução progressiva dos horizontes no fim de 2025",
      () => {
        expect(
          getAvailableMapHorizons(
            officialIndex,
            50,
          ),
        ).toEqual([
          1,
          2,
          3,
        ]);

        expect(
          getAvailableMapHorizons(
            officialIndex,
            51,
          ),
        ).toEqual([
          1,
          2,
        ]);

        expect(
          getAvailableMapHorizons(
            officialIndex,
            52,
          ),
        ).toEqual([
          1,
        ]);

        expect(
          normalizeMapSelection(
            officialIndex,
            "52",
            "4",
          ),
        ).toEqual({
          week:
            52,

          horizon:
            1,

          normalized:
            true,
        });
      },
    );
  },
);
