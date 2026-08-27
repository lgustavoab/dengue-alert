import {
  readFileSync,
} from "node:fs";
import path from "node:path";

import {
  describe,
  expect,
  it,
} from "vitest";

import nextConfig from "../../../next.config";

describe("configuração de deployment do serving", () => {
  it("mantém o tracing explícito e restrito por rota", () => {
    expect(nextConfig.outputFileTracingRoot).toBe(path.join(process.cwd(), ".."));
    expect(nextConfig.outputFileTracingIncludes).toEqual({
      "/api/serving/territories": [
        "public/data/serving/metadata/territories.json",
        "public/data/serving/historical/municipality/index.json",
        "public/data/serving/prediction/municipality/index.json",
      ],
      "/api/serving/historical/municipality/*": [
        "../dist/serving-runtime-v1.0.0/historical/municipalities.ndjson",
        "../dist/serving-runtime-v1.0.0/historical/municipalities.index.json",
      ],
      "/api/serving/prediction/municipality/*": [
        "../dist/serving-runtime-v1.0.0/prediction/municipalities.ndjson",
        "../dist/serving-runtime-v1.0.0/prediction/municipalities.index.json",
      ],
      "/api/serving/prediction/map": [
        "../dist/serving-runtime-v1.0.0/prediction/map/index.json",
      ],
      "/api/serving/prediction/map/*/*": [
        "../dist/serving-runtime-v1.0.0/prediction/map/h*/se*.json",
      ],
    });
    expect(nextConfig.outputFileTracingExcludes).toEqual({
      "/api/serving/territories": [
        "public/data/serving/**/*",
      ],
      "/api/serving/historical/municipality/*": [
        "../data/serving/**/*",
        "../dist/serving-runtime-v1.0.0/**/*",
      ],
      "/api/serving/prediction/municipality/*": [
        "../data/serving/**/*",
        "../dist/serving-runtime-v1.0.0/**/*",
      ],
      "/api/serving/prediction/map": [
        "../data/serving/prediction/map/**/*",
        "../dist/serving-runtime-v1.0.0/**/*",
      ],
      "/api/serving/prediction/map/*/*": [
        "../data/serving/prediction/map/**/*",
        "../dist/serving-runtime-v1.0.0/**/*",
      ],
    });
    expect(nextConfig).not.toHaveProperty("output");

    const serializedIncludes = JSON.stringify(
      nextConfig.outputFileTracingIncludes,
    );

    expect(serializedIncludes).not.toContain(
      "municipality/series",
    );
    expect(serializedIncludes).not.toContain(
      "../data/serving/historical",
    );
    expect(serializedIncludes).not.toContain(
      "../data/serving/prediction/municipality",
    );
  });

  it("mantém artefatos locais fora do upload da Vercel", () => {
    const ignoredPaths = new Set(
      readFileSync(
        path.join(process.cwd(), "..", ".vercelignore"),
        "utf-8",
      )
        .split(/\r?\n/u)
        .filter(Boolean),
    );

    expect([...ignoredPaths]).toEqual(expect.arrayContaining([
      "/.venv/",
      "/SINAN/",
      "/data/",
      "/web/.next/",
      "/web/node_modules/",
      "/web/public/data/serving/",
    ]));
  });

  it("prepara o build Vercel somente com o runtime compacto", () => {
    const packageJson = JSON.parse(
      readFileSync(
        path.join(process.cwd(), "package.json"),
        "utf-8",
      ),
    ) as {
      scripts: Record<
        string,
        string
      >;
    };
    const wrapper = readFileSync(
      path.join(
        process.cwd(),
        "scripts",
        "bootstrap-serving-for-build.mjs",
      ),
      "utf-8",
    );

    expect(
      packageJson.scripts[
        "build:vercel"
      ],
    ).toBe(
      "node scripts/bootstrap-serving-for-build.mjs && next build",
    );
    expect(
      wrapper,
    ).toContain(
      "bootstrap_serving_runtime.py",
    );
    expect(
      wrapper,
    ).toContain(
      "DENGUE_SERVING_RUNTIME_ARCHIVE",
    );
    expect(
      wrapper,
    ).not.toContain(
      "bootstrap_serving_snapshot.py",
    );
    expect(
      wrapper,
    ).not.toContain(
      "serving-v1.0.0.zip",
    );
  });
});
