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
  it("oferece caminhos para as quatro áreas do estudo", async () => {
    const source = await readHomeSource();
    const destinations = Array.from(
      source.matchAll(/href="([^"]+)"/g),
      (match) => match[1],
    );

    expect(source.match(/<AreaCard/g)).toHaveLength(4);
    expect(destinations).toEqual([
      "/predicao",
      "/dados-qualidade",
      "/historico",
      "/predicao",
      "/mapa",
      "/dados-qualidade",
      "/dados-qualidade",
    ]);

    for (const title of [
      "Histórico",
      "Resultados do modelo",
      "Mapa",
      "Dados e método",
    ]) {
      expect(source).toContain(`title="${title}"`);
    }
  });

  it("apresenta pergunta, método, achados e autoria acadêmica", async () => {
    const source = await readHomeSource();

    expect(source).toContain("É possível antecipar períodos de risco elevado de dengue?");
    expect(source).toContain("Como fizemos o estudo");
    expect(source).toContain("O que encontramos");
    expect(source).toContain("alertas que não se");
    expect(source).toContain("não trouxe melhora consistente");
    expect(source).toContain("Universidade");
    expect(source).toContain("Orientação: Aline Martins");
    expect(source).toContain("<li>José Olavo Bernardo Freire</li>");
  });

  it("distingue pesquisa retrospectiva de alertas atuais", async () => {
    const source = await readHomeSource();

    expect(source).toContain("avaliadas retrospectivamente em {prediction.ano}");
    expect(source).toMatch(/não\s+representam alertas operacionais atuais/);
    expect(source).toContain("não representam alertas operacionais atuais nem risco individual");
    expect(source).toContain("Não equivale a uma declaração oficial de");
  });

  it("mantém um nome acessível específico em cada link de área", async () => {
    const source = await readFile(areaCardPath, "utf-8");

    expect(source).toContain("aria-label={`Explorar ${title}`}");
  });
});
