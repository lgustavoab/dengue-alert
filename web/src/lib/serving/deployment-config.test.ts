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
    expect(nextConfig).not.toHaveProperty(
      "outputFileTracingRoot",
    );
    expect(nextConfig.outputFileTracingIncludes).toEqual({
      "/api/serving/territories": [
        "public/data/serving/metadata/territories.json",
        "public/data/serving/historical/municipality/index.json",
        "public/data/serving/prediction/municipality/index.json",
      ],
      "/api/serving/historical/municipality/*": [
        ".runtime/serving/historical/municipalities.ndjson",
        ".runtime/serving/historical/municipalities.index.json",
      ],
      "/api/serving/prediction/municipality/*": [
        ".runtime/serving/prediction/municipalities.ndjson",
        ".runtime/serving/prediction/municipalities.index.json",
      ],
      "/api/serving/prediction/map": [
        ".runtime/serving/prediction/map/index.json",
      ],
      "/api/serving/prediction/map/*/*": [
        ".runtime/serving/prediction/map/h*/se*.json",
      ],
    });
    expect(nextConfig.outputFileTracingExcludes).toEqual({
      "/api/serving/territories": [
        "public/data/serving/**/*",
      ],
      "/api/serving/historical/municipality/*": [
        ".runtime/serving/**/*",
      ],
      "/api/serving/prediction/municipality/*": [
        ".runtime/serving/**/*",
      ],
      "/api/serving/prediction/map": [
        ".runtime/serving/**/*",
      ],
      "/api/serving/prediction/map/*/*": [
        ".runtime/serving/**/*",
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
      "../",
    );
  });

  it("mantém artefatos locais fora do upload da Vercel", () => {
    const uploadRules = new Set(
      readFileSync(
        path.join(process.cwd(), "..", ".vercelignore"),
        "utf-8",
      )
        .split(/\r?\n/u)
        .filter(Boolean),
    );

    expect([...uploadRules]).toEqual(expect.arrayContaining([
      "/.venv/",
      "/SINAN/",
      "/data/",
      "/web/.next/",
      "/web/node_modules/",
      "/web/public/data/serving/",
      "/web/.runtime/",
      "/.gitattributes",
      "/.python-version",
      "/README.md",
      "/pyproject.toml",
      "/uv.lock",
      "/scripts/*",
      "!/scripts/bootstrap_serving_runtime.py",
      "!/scripts/package_serving_runtime.py",
      "!/scripts/package_serving_snapshot.py",
      "!/scripts/sync_web_serving.py",
      "!/scripts/sync_web_geography.py",
      "/artifacts/serving/*",
      "!/artifacts/serving/serving-runtime-v1.0.0-distribution.json",
      "!/artifacts/serving/serving-runtime-v1.0.0.json",
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
    ).toContain(
      '".runtime"',
    );
    expect(
      wrapper,
    ).toContain(
      '"--destination"',
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

  it("exclui artefatos gerados da detecção de fontes do Tailwind", () => {
    const globalStyles = readFileSync(
      path.join(process.cwd(), "src", "app", "globals.css"),
      "utf-8",
    );

    expect(globalStyles).toContain(
      '@source not "../../.runtime";',
    );
    expect(globalStyles).toContain(
      '@source not "../../public/data/serving";',
    );
  });
});
