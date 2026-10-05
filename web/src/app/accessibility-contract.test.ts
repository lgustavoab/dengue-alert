import { readFile } from "node:fs/promises";
import path from "node:path";

import { describe, expect, it } from "vitest";

const sourceRoot = path.join(process.cwd(), "src");

async function readSource(relativePath: string): Promise<string> {
  return readFile(path.join(sourceRoot, relativePath), "utf-8");
}

function relativeLuminance(hex: string): number {
  const channels = [1, 3, 5].map((offset) =>
    Number.parseInt(hex.slice(offset, offset + 2), 16) / 255,
  );
  const linearChannels = channels.map((channel) =>
    channel <= 0.04045
      ? channel / 12.92
      : ((channel + 0.055) / 1.055) ** 2.4,
  );

  return (
    0.2126 * linearChannels[0] +
    0.7152 * linearChannels[1] +
    0.0722 * linearChannels[2]
  );
}

function contrastRatio(foreground: string, background: string): number {
  const luminances = [
    relativeLuminance(foreground),
    relativeLuminance(background),
  ].sort((left, right) => right - left);

  return (luminances[0] + 0.05) / (luminances[1] + 0.05);
}

describe("contratos proporcionais de acessibilidade", () => {
  it("não impõe largura mínima nem oculta overflow horizontal na raiz", async () => {
    const styles = await readSource("app/globals.css");
    for (const selector of ["html", "body", ".app-shell", ".app-main"]) {
      const block = styles.split(`${selector} {`)[1]?.split("}")[0];
      expect(block).toBeDefined();
      expect(block).not.toMatch(/min-width\s*:\s*\d+(?:px|rem)/);
      expect(block).not.toMatch(/overflow(?:-x)?\s*:\s*(?:hidden|clip)/);
    }
  });

  it("mantém áreas de expansão municipal de pelo menos 44 px no mobile", async () => {
    for (const [file, selectors] of [
      ["components/prediction/prediction-results.module.css", [".technicalDetails summary"]],
      ["components/map/municipality-map.module.css", [".resultDetails summary", ".clearButton"]],
    ] as const) {
      const styles = await readSource(file);
      const mobile = styles.split("@media (max-width: 680px)")[1];
      for (const selector of selectors) {
        const block = mobile?.split(`${selector} {`)[1]?.split("}")[0];
        expect(block).toContain("min-height: 44px;");
      }
    }
  });

  it("mantém o skip link ligado ao main raiz", async () => {
    const layout = await readSource("app/layout.tsx");

    expect(layout).toContain('className="skip-link" href="#main-content"');
    expect(layout).toContain('id="main-content"');
    expect(layout.indexOf("skip-link")).toBeLessThan(
      layout.indexOf("<SiteHeader />"),
    );
  });

  it("evita landmarks main aninhados nos estados compartilhados", async () => {
    for (const relativePath of [
      "components/ui/route-error-state.tsx",
      "components/ui/route-loading-state.tsx",
    ]) {
      const source = await readSource(relativePath);

      expect(source).not.toContain("<main");
      expect(source).not.toContain("</main>");
    }
  });

  it("mantém regiões roláveis nomeadas e acessíveis por teclado", async () => {
    const historical = await readSource(
      "components/historical/annual-panorama.tsx",
    );
    const quality = await readSource(
      "components/quality/quality-overview.tsx",
    );

    expect(historical).toContain('aria-label="Panorama anual da dengue"');
    expect(historical).toContain("tabIndex={0}");
    expect(quality).toContain(
      'aria-label="Referência populacional por ano epidemiológico"',
    );
    expect(quality).toContain("tabIndex={0}");
  });

  it("mantém contraste mínimo do texto secundário nos fundos utilizados", async () => {
    const styles = await readSource("app/globals.css");
    const foregroundMuted = "#5f7077";

    expect(styles).toContain(`--foreground-muted: ${foregroundMuted};`);

    for (const background of ["#ffffff", "#f4f7f8", "#eef3f4"]) {
      expect(contrastRatio(foregroundMuted, background)).toBeGreaterThanOrEqual(
        4.5,
      );
    }
  });
});
