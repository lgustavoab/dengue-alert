import {
  describe,
  expect,
  it,
} from "vitest";

import {
  formatDecimal,
  formatHorizonRange,
  formatInteger,
  formatPercent,
  formatPeriod,
} from "@/lib/serving/formatters";

describe(
  "serving formatters",
  () => {
    it(
      "formata inteiros em pt-BR",
      () => {
        expect(
          formatInteger(
            16294913,
          ),
        ).toBe(
          "16.294.913",
        );
      },
    );

    it(
      "formata decimais com uma casa",
      () => {
        expect(
          formatDecimal(
            3088.1447899945315,
          ),
        ).toBe(
          "3.088,1",
        );
      },
    );

    it(
      "formata proporções como percentual",
      () => {
        expect(
          formatPercent(
            0.9847396768402156,
          ),
        ).toBe(
          "98,5%",
        );
      },
    );

    it(
      "formata período histórico",
      () => {
        expect(
          formatPeriod(
            "2016-2025",
          ),
        ).toBe(
          "2016–2025",
        );
      },
    );

    it(
      "formata intervalo de horizontes",
      () => {
        expect(
          formatHorizonRange(
            [
              4,
              2,
              1,
              3,
            ],
          ),
        ).toBe(
          "H1–H4",
        );
      },
    );

    it(
      "formata horizonte único",
      () => {
        expect(
          formatHorizonRange(
            [
              2,
            ],
          ),
        ).toBe(
          "H2",
        );
      },
    );

    it(
      "representa ausência de horizontes",
      () => {
        expect(
          formatHorizonRange(
            [],
          ),
        ).toBe(
          "—",
        );
      },
    );
  },
);