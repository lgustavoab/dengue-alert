import {
  describe,
  expect,
  it,
} from "vitest";

import {
  GET as getPredictionMapIndexRoute,
} from "@/app/api/serving/prediction/map/route";

import {
  GET as getPredictionMapSliceRoute,
} from "@/app/api/serving/prediction/map/[horizonte]/[semana]/route";

function buildContext(
  horizon: string,
  week: string,
) {
  return {
    params: Promise.resolve(
      {
        horizonte:
          horizon,
        semana:
          week,
      },
    ),
  };
}

describe(
  "prediction map routes",
  () => {
    it(
      "serve o índice do mapa com cache HTTP",
      async () => {
        const response =
          await getPredictionMapIndexRoute();

        expect(
          response.status,
        ).toBe(
          200,
        );

        expect(
          response.headers.get(
            "Cache-Control",
          ),
        ).toBe(
          "public, max-age=3600, stale-while-revalidate=86400",
        );

        const payload =
          await response.json();

        expect(
          payload.status,
        ).toBe(
          "APROVADO",
        );

        expect(
          payload.arquivos,
        ).toBe(
          202,
        );

        expect(
          payload.municipios,
        ).toBe(
          5_569,
        );
      },
    );

    it(
      "serve H1 SE20 com 5569 municípios e 687 alertas",
      async () => {
        const response =
          await getPredictionMapSliceRoute(
            new Request(
              "http://localhost/api/serving/prediction/map/1/20",
            ),
            buildContext(
              "1",
              "20",
            ),
          );

        expect(
          response.status,
        ).toBe(
          200,
        );

        expect(
          response.headers.get(
            "Cache-Control",
          ),
        ).toBe(
          "public, max-age=3600, stale-while-revalidate=86400",
        );

        const payload =
          await response.json();

        expect(
          payload.horizonte,
        ).toBe(
          1,
        );

        expect(
          payload.semana_epidemiologica,
        ).toBe(
          20,
        );

        expect(
          payload.count,
        ).toBe(
          5_569,
        );

        expect(
          payload.data.predicao.filter(
            Boolean,
          ),
        ).toHaveLength(
          687,
        );
      },
    );

    it(
      "retorna 404 para horizonte temporalmente indisponível",
      async () => {
        const response =
          await getPredictionMapSliceRoute(
            new Request(
              "http://localhost/api/serving/prediction/map/4/50",
            ),
            buildContext(
              "4",
              "50",
            ),
          );

        expect(
          response.status,
        ).toBe(
          404,
        );

        const payload =
          await response.json();

        expect(
          payload.error,
        ).toBe(
          "prediction_map_unavailable",
        );

        expect(
          payload.horizonte,
        ).toBe(
          4,
        );

        expect(
          payload.semana,
        ).toBe(
          50,
        );
      },
    );

    it(
      "retorna 400 para horizonte inválido",
      async () => {
        const response =
          await getPredictionMapSliceRoute(
            new Request(
              "http://localhost/api/serving/prediction/map/5/20",
            ),
            buildContext(
              "5",
              "20",
            ),
          );

        expect(
          response.status,
        ).toBe(
          400,
        );

        const payload =
          await response.json();

        expect(
          payload.error,
        ).toBe(
          "invalid_prediction_map_selection",
        );
      },
    );

    it(
      "retorna 400 para semana não numérica",
      async () => {
        const response =
          await getPredictionMapSliceRoute(
            new Request(
              "http://localhost/api/serving/prediction/map/1/abc",
            ),
            buildContext(
              "1",
              "abc",
            ),
          );

        expect(
          response.status,
        ).toBe(
          400,
        );

        const payload =
          await response.json();

        expect(
          payload.error,
        ).toBe(
          "invalid_prediction_map_selection",
        );
      },
    );

    it(
      "retorna 400 para semana fora do intervalo epidemiológico",
      async () => {
        const response =
          await getPredictionMapSliceRoute(
            new Request(
              "http://localhost/api/serving/prediction/map/1/53",
            ),
            buildContext(
              "1",
              "53",
            ),
          );

        expect(
          response.status,
        ).toBe(
          400,
        );
      },
    );
  },
);