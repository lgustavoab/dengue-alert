import {
  describe,
  expect,
  it,
} from "vitest";

import {
  navigationItems,
} from "@/lib/constants/navigation";

describe(
  "main navigation",
  () => {
    it(
      "expõe todas as áreas principais da aplicação",
      () => {
        expect(
          navigationItems,
        ).toEqual([
          {
            label:
              "Início",

            href:
              "/",
          },
          {
            label:
              "Histórico",

            href:
              "/historico",
          },
          {
            label:
              "Dados & Qualidade",

            href:
              "/dados-qualidade",
          },
          {
            label:
              "Predição",

            href:
              "/predicao",
          },
          {
            label:
              "Mapa",

            href:
              "/mapa",
          },
        ]);
      },
    );

    it(
      "mantém todas as rotas internas absolutas",
      () => {
        for (
          const item
          of navigationItems
        ) {
          expect(
            item.href.startsWith(
              "/",
            ),
          ).toBe(
            true,
          );
        }
      },
    );

    it(
      "não possui destinos duplicados",
      () => {
        const hrefs =
          navigationItems.map(
            (item) =>
              item.href,
          );

        expect(
          new Set(
            hrefs,
          ).size,
        ).toBe(
          hrefs.length,
        );
      },
    );
  },
);