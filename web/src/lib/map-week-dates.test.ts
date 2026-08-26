import {
  describe,
  expect,
  it,
} from "vitest";

import {
  formatMapWeekDateRange,
  formatMapWeekOptionLabel,
  getEpidemiologicalWeekDateRange,
} from "@/lib/map-week-dates";

describe(
  "map week dates",
  () => {
    it(
      "representa corretamente a SE01 de 2025",
      () => {
        const range =
          getEpidemiologicalWeekDateRange(
            1,
          );

        expect(
          range.startIso,
        ).toBe(
          "2024-12-29",
        );

        expect(
          range.endIso,
        ).toBe(
          "2025-01-04",
        );
      },
    );

    it(
      "representa corretamente a SE49 confirmada pelo serving",
      () => {
        const range =
          getEpidemiologicalWeekDateRange(
            49,
          );

        expect(
          range.startIso,
        ).toBe(
          "2025-11-30",
        );

        expect(
          range.endIso,
        ).toBe(
          "2025-12-06",
        );
      },
    );

    it(
      "representa corretamente a SE52",
      () => {
        const range =
          getEpidemiologicalWeekDateRange(
            52,
          );

        expect(
          range.startIso,
        ).toBe(
          "2025-12-21",
        );

        expect(
          range.endIso,
        ).toBe(
          "2025-12-27",
        );
      },
    );

    it(
      "formata o intervalo para leitura humana",
      () => {
        expect(
          formatMapWeekDateRange(
            49,
          ),
        ).toBe(
          "30/11 a 06/12/2025",
        );
      },
    );

    it(
      "formata a opção completa do filtro",
      () => {
        expect(
          formatMapWeekOptionLabel(
            49,
          ),
        ).toBe(
          "SE49 · 30/11 a 06/12/2025",
        );
      },
    );

    it(
      "rejeita semanas fora do intervalo",
      () => {
        expect(
          () =>
            getEpidemiologicalWeekDateRange(
              0,
            ),
        ).toThrow(
          "Semana epidemiológica inválida",
        );

        expect(
          () =>
            getEpidemiologicalWeekDateRange(
              53,
            ),
        ).toThrow(
          "Semana epidemiológica inválida",
        );
      },
    );
  },
);