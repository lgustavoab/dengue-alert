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
  },
);
