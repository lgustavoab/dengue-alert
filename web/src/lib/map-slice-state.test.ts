import {
  describe,
  expect,
  it,
} from "vitest";

import {
  buildPredictionMapSliceUrl,
  createMapSliceErrorState,
  resolveCurrentMapSliceState,
} from "@/lib/map-slice-state";

import type {
  MapSliceState,
} from "@/lib/map-slice-state";

describe(
  "estado do recorte preditivo do mapa",
  () => {
    it(
      "mantém erro separado de loading e sem resultado epidemiológico",
      () => {
        const state =
          createMapSliceErrorState(
            49,
            1,
            "Não foi possível carregar o recorte preditivo selecionado.",
          );

        const currentState =
          resolveCurrentMapSliceState(
            state,
            49,
            1,
          );

        expect(
          currentState,
        ).toMatchObject({
          week: 49,
          horizon: 1,
          status: "error",
          data: null,
        });

        expect(
          currentState.status,
        ).not.toBe(
          "loading",
        );
      },
    );

    it(
      "não reutiliza dados anteriores para uma nova seleção",
      () => {
        const previousState = {
          week: 49,
          horizon: 1,
          status: "ready",
          data: {
            recorte:
              "anterior",
          },
          error: null,
        } as unknown as MapSliceState;

        const currentState =
          resolveCurrentMapSliceState(
            previousState,
            20,
            4,
          );

        expect(
          currentState,
        ).toEqual({
          week: 20,
          horizon: 4,
          status: "loading",
          data: null,
          error: null,
        });
      },
    );

    it(
      "constrói o retry para a semana e o horizonte correntes",
      () => {
        expect(
          buildPredictionMapSliceUrl(
            20,
            4,
          ),
        ).toBe(
          "/api/serving/prediction/map/4/20",
        );
      },
    );
  },
);
