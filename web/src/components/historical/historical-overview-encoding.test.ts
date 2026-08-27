import {
  readFile,
} from "node:fs/promises";

import {
  fileURLToPath,
} from "node:url";

import {
  describe,
  expect,
  it,
} from "vitest";

const historicalOverviewPath =
  fileURLToPath(
    new URL(
      "./historical-overview.tsx",
      import.meta.url,
    ),
  );

const territorialAnalysisPath =
  fileURLToPath(
    new URL(
      "./territorial-analysis.tsx",
      import.meta.url,
    ),
  );

const historicalRiskAnalysisPath =
  fileURLToPath(
    new URL(
      "./historical-risk-analysis.tsx",
      import.meta.url,
    ),
  );

const qualityOverviewPath =
  fileURLToPath(
    new URL(
      "../quality/quality-overview.tsx",
      import.meta.url,
    ),
  );

const mojibakeMarkers = [
  "\u00c3",
  "\u00c2",
  "\ufffd",
  "\u00e2\u20ac",
] as const;

describe(
  "encoding do panorama histórico",
  () => {
    it(
      "não contém marcadores conhecidos de mojibake",
      async () => {
        const source =
          await readFile(
            historicalOverviewPath,
            "utf-8",
          );

        for (
          const marker
          of mojibakeMarkers
        ) {
          expect(
            source,
          ).not.toContain(
            marker,
          );
        }
      },
    );

    it(
      "não expõe implementação interna na limitação da análise estadual",
      async () => {
        const source =
          await readFile(
            territorialAnalysisPath,
            "utf-8",
          );

        expect(
          source,
        ).toContain(
          "Os dados disponíveis nesta visualização incluem o resumo histórico consolidado por UF",
        );
        expect(
          source,
        ).not.toContain(
          "O contrato serving atual",
        );
      },
    );

    it(
      "não expõe jargão interno nos textos públicos residuais",
      async () => {
        const publicSources =
          await Promise.all([
            readFile(
              historicalRiskAnalysisPath,
              "utf-8",
            ),
            readFile(
              qualityOverviewPath,
              "utf-8",
            ),
          ]);
        const publicText =
          publicSources.join(
            "\n",
          );

        for (
          const jargon
          of [
            "contrato serving",
            "contratos web sincronizados",
            "contrato de visão geral auditado",
          ]
        ) {
          expect(
            publicText,
          ).not.toContain(
            jargon,
          );
        }
      },
    );
  },
);
