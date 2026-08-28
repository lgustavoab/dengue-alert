import { readFile } from "node:fs/promises";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { routeStateConfig } from "@/lib/route-state-config";

const appRoot = path.join(process.cwd(), "src", "app");

const phaseFiles = [
  "app/error.tsx",
  "app/historico/error.tsx",
  "app/historico/loading.tsx",
  "app/dados-qualidade/error.tsx",
  "app/dados-qualidade/loading.tsx",
  "app/predicao/error.tsx",
  "app/predicao/loading.tsx",
  "app/mapa/error.tsx",
  "components/ui/route-error-state.tsx",
  "components/ui/route-loading-state.tsx",
  "components/ui/route-state.module.css",
  "lib/route-state-config.ts",
  "lib/route-state-config.test.ts",
] as const;

async function readSource(relativePath: string): Promise<string> {
  return readFile(path.join(process.cwd(), "src", relativePath), "utf-8");
}

describe("resiliência das rotas principais", () => {
  it("mantém configuração pública para as cinco superfícies", () => {
    expect(Object.keys(routeStateConfig)).toEqual([
      "home",
      "historical",
      "quality",
      "prediction",
      "map",
    ]);
  });

  it("não expõe detalhes técnicos nas mensagens públicas", () => {
    const publicMessages = Object.values(routeStateConfig)
      .flatMap((config) => Object.values(config))
      .join(" ");

    for (const forbidden of [
      "stack",
      "digest",
      "exception",
      ".json",
      "filesystem",
      "data/serving",
      "web/public",
    ]) {
      expect(publicMessages.toLowerCase()).not.toContain(forbidden);
    }
  });

  it("possui error boundary Client Component nas cinco rotas", async () => {
    const errorFiles = [
      "error.tsx",
      "historico/error.tsx",
      "dados-qualidade/error.tsx",
      "predicao/error.tsx",
      "mapa/error.tsx",
    ];

    for (const relativePath of errorFiles) {
      const source = await readFile(path.join(appRoot, relativePath), "utf-8");

      expect(source).toContain('"use client"');
      expect(source).toContain("RouteErrorState");
      expect(source).toContain("reset: () => void");
      expect(source).toContain("onRetry={reset}");
      expect(source).not.toContain("retry: () => void");
      expect(source).not.toContain("onRetry={retry}");
      expect(source).not.toContain("error.message");
      expect(source).not.toContain("error.digest");
    }
  });

  it("mantém os arquivos da fase em UTF-8 sem mojibake", async () => {
    const mojibakeMarkers = [
      String.fromCodePoint(0x00c3),
      String.fromCodePoint(0x00c2),
      String.fromCodePoint(0xfffd),
      String.fromCodePoint(0x00e2, 0x20ac),
    ];

    for (const relativePath of phaseFiles) {
      const source = await readSource(relativePath);

      for (const marker of mojibakeMarkers) {
        expect(source).not.toContain(marker);
      }
    }

    const errorState = await readSource("components/ui/route-error-state.tsx");
    expect(errorState).toContain("retorne à página inicial");
    expect(errorState).toContain("Voltar ao início");
  });

  it("limita loading server-side às três rotas assíncronas segmentadas", async () => {
    const loadingFiles = [
      "historico/loading.tsx",
      "dados-qualidade/loading.tsx",
      "predicao/loading.tsx",
    ];

    for (const relativePath of loadingFiles) {
      const source = await readFile(path.join(appRoot, relativePath), "utf-8");
      expect(source).toContain("RouteLoadingState");
      expect(source).not.toMatch(/\b\d{1,3}(?:[.,]\d{3})+\b/);
    }

    await expect(readFile(path.join(appRoot, "mapa", "loading.tsx"), "utf-8"))
      .rejects.toThrow();
  });

  it("mantém retry técnico sem alterar filtros ou regras científicas", async () => {
    const source = await readSource("components/ui/route-error-state.tsx");

    expect(source).toContain("onClick={onRetry}");
    expect(source).not.toContain("searchParams");
    expect(source).not.toContain("router.replace");
    expect(source).not.toContain("predicao");
    expect(source).not.toContain("threshold");
  });

  it("mantém o erro inicial do mapa separado do erro de recorte", async () => {
    const routeError = await readFile(path.join(appRoot, "mapa", "error.tsx"), "utf-8");
    const sliceSource = await readSource("components/map/map-foundation.tsx");

    expect(routeError).toContain("routeStateConfig.map");
    expect(routeError).not.toContain("createMapSliceErrorState");
    expect(sliceSource).toContain("createMapSliceErrorState");
    expect(sliceSource).toContain("Tentar novamente");
  });
});
