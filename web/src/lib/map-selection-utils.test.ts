import {
  describe,
  expect,
  it,
} from "vitest";

import {
  DEFAULT_MAP_HORIZON,
  DEFAULT_MAP_WEEK,
  formatMapWeekLabel,
  getAvailableMapHorizons,
  getMapHorizonLabel,
  normalizeMapSelection,
} from "@/lib/map-selection-utils";

import type {
  PredictionMapIndexContract,
} from "@/lib/serving/prediction-map-types";

const index:
PredictionMapIndexContract = {
  schema_version:
    "1.0",

  status:
    "APROVADO",

  avaliacao:
    "retrospectiva_2025",

  ano_epidemiologico:
    2025,

  municipios:
    5_569,

  predicoes:
    1_124_938,

  arquivos:
    202,

  horizontes: {
    h1: {
      horizonte:
        1,

      threshold:
        0.187687,

      semanas:
        Array.from(
          {
            length:
              52,
          },
          (
            _item,
            position,
          ) =>
            position + 1,
        ),
    },

    h2: {
      horizonte:
        2,

      threshold:
        0.190783,

      semanas:
        Array.from(
          {
            length:
              51,
          },
          (
            _item,
            position,
          ) =>
            position + 1,
        ),
    },

    h3: {
      horizonte:
        3,

      threshold:
        0.167991,

      semanas:
        Array.from(
          {
            length:
              50,
          },
          (
            _item,
            position,
          ) =>
            position + 1,
        ),
    },

    h4: {
      horizonte:
        4,

      threshold:
        0.157138,

      semanas:
        Array.from(
          {
            length:
              49,
          },
          (
            _item,
            position,
          ) =>
            position + 1,
        ),
    },
  },
};

describe(
  "map selection utils",
  () => {
    it(
      "usa SE49 e H1 como seleção padrão",
      () => {
        const selection =
          normalizeMapSelection(
            index,
            null,
            null,
          );

        expect(
          selection,
        ).toEqual(
          {
            week:
              DEFAULT_MAP_WEEK,

            horizon:
              DEFAULT_MAP_HORIZON,

            normalized:
              true,
          },
        );
      },
    );

    it(
      "preserva seleção válida",
      () => {
        const selection =
          normalizeMapSelection(
            index,
            "20",
            "4",
          );

        expect(
          selection,
        ).toEqual(
          {
            week:
              20,

            horizon:
              4,

            normalized:
              false,
          },
        );
      },
    );

    it(
      "normaliza semana inválida para SE49",
      () => {
        const selection =
          normalizeMapSelection(
            index,
            "abc",
            "2",
          );

        expect(
          selection.week,
        ).toBe(
          49,
        );

        expect(
          selection.horizon,
        ).toBe(
          2,
        );

        expect(
          selection.normalized,
        ).toBe(
          true,
        );
      },
    );

    it(
      "normaliza horizonte inválido para H1",
      () => {
        const selection =
          normalizeMapSelection(
            index,
            "20",
            "9",
          );

        expect(
          selection.week,
        ).toBe(
          20,
        );

        expect(
          selection.horizon,
        ).toBe(
          1,
        );
      },
    );

    it(
      "preserva SE52 e normaliza H4 para H1",
      () => {
        const selection =
          normalizeMapSelection(
            index,
            "52",
            "4",
          );

        expect(
          selection.week,
        ).toBe(
          52,
        );

        expect(
          selection.horizon,
        ).toBe(
          1,
        );

        expect(
          selection.normalized,
        ).toBe(
          true,
        );
      },
    );

    it(
      "preserva H3 na última semana disponível para H3",
      () => {
        const selection =
          normalizeMapSelection(
            index,
            "50",
            "3",
          );

        expect(
          selection.week,
        ).toBe(
          50,
        );

        expect(
          selection.horizon,
        ).toBe(
          3,
        );

        expect(
          selection.normalized,
        ).toBe(
          false,
        );
      },
    );

    it(
      "expõe todos os horizontes disponíveis na SE49",
      () => {
        expect(
          getAvailableMapHorizons(
            index,
            49,
          ),
        ).toEqual(
          [
            1,
            2,
            3,
            4,
          ],
        );
      },
    );

    it(
      "reduz progressivamente os horizontes no fim do ano",
      () => {
        expect(
          getAvailableMapHorizons(
            index,
            50,
          ),
        ).toEqual(
          [
            1,
            2,
            3,
          ],
        );

        expect(
          getAvailableMapHorizons(
            index,
            51,
          ),
        ).toEqual(
          [
            1,
            2,
          ],
        );

        expect(
          getAvailableMapHorizons(
            index,
            52,
          ),
        ).toEqual(
          [
            1,
          ],
        );
      },
    );

    it(
      "formata semana epidemiológica com dois dígitos",
      () => {
        expect(
          formatMapWeekLabel(
            1,
          ),
        ).toBe(
          "SE01",
        );

        expect(
          formatMapWeekLabel(
            49,
          ),
        ).toBe(
          "SE49",
        );
      },
    );

    it(
      "descreve H1-H4 como horizontes temporais",
      () => {
        expect(
          getMapHorizonLabel(
            1,
          ),
        ).toBe(
          "H1 · 1 semana à frente",
        );

        expect(
          getMapHorizonLabel(
            4,
          ),
        ).toBe(
          "H4 · 4 semanas à frente",
        );
      },
    );
  },
);