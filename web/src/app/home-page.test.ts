import { readFile } from "node:fs/promises";
import path from "node:path";

import { describe, expect, it } from "vitest";

const homePath = path.join(process.cwd(), "src", "app", "page.tsx");
const areaCardPath = path.join(
  process.cwd(),
  "src",
  "components",
  "ui",
  "area-card.tsx",
);

async function readHomeSource(): Promise<string> {
  return readFile(homePath, "utf-8");
}

describe("página inicial", () => {
  it("representa as quatro superfícies atuais da aplicação", async () => {
    const source = await readHomeSource();
    const destinations = Array.from(
      source.matchAll(/href="([^"]+)"/g),
      (match) => match[1],
    );

    expect(source.match(/<AreaCard/g)).toHaveLength(4);
    expect(destinations).toEqual([
      "/historico",
      "/dados-qualidade",
      "/predicao",
      "/mapa",
    ]);

    for (const title of [
      "Histórico",
      "Dados & Qualidade",
      "Predição",
      "Mapa preditivo",
    ]) {
      expect(source).toContain(`title="${title}"`);
    }
  });

  it("remove a narrativa desatualizada e o jargão de sincronização", async () => {
    const source = await readHomeSource();

    expect(source).toContain("Quatro perspectivas complementares");
    expect(source).not.toContain("Três perspectivas complementares");
    expect(source).not.toContain("contratos web sincronizados");
    expect(source).not.toContain("contract_count");
    expect(source).not.toContain("getServingManifest");
  });

  it("mantém o mapa explicitamente retrospectivo e sem alerta atual", async () => {
    const source = await readHomeSource();

    expect(source).toContain("classificações oficiais");
    expect(source).toContain("teste retrospectivo de 2025");
    expect(source).toMatch(/não\s+representam alertas operacionais atuais/);
    expect(source).not.toContain("risco atual de 2026");
  });

  it("mantém um nome acessível específico em cada link de área", async () => {
    const source = await readFile(areaCardPath, "utf-8");

    expect(source).toContain("aria-label={`Explorar ${title}`}");
  });
});
