import { readFile } from "node:fs/promises";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { MunicipalityMapDatum } from "@/lib/map-prediction";
import type { MapSliceStatus } from "@/lib/map-slice-state";
import type { PredictionMapContract, PredictionMapHorizon } from "@/lib/serving/prediction-map-types";
import { MunicipalityMapResult, formatMapAdvanceLabel } from "./municipality-map-result";

const prediction: PredictionMapContract = {
  schema_version: "1.0", ano_epidemiologico: 2025,
  semana_epidemiologica: 49, data_inicio_semana: "2025-11-30",
  horizonte: 2, threshold: 0.5, count: 1,
  data: { codigo_ibge_7: ["3537305"], score: [0.25], predicao: [true] },
};
const municipality: MunicipalityMapDatum = {
  codigoIbge7: "3537305", d: "M0,0", status: "alerta", score: 0.25, predicao: true,
};
function result(status: MapSliceStatus = "ready", record = municipality, contract: PredictionMapContract | null = prediction) {
  return renderToStaticMarkup(createElement(MunicipalityMapResult, { status, municipality: record, prediction: contract }));
}
function visible(html: string) {
  return html.replace(/<details\b[^>]*>[\s\S]*?<\/details>/g, "");
}

describe("leitura didática do mapa", () => {
  it.each([1, 2, 3, 4] as PredictionMapHorizon[])("explica H%s como prazo, não gravidade", (horizon) => {
    expect(formatMapAdvanceLabel(horizon)).toBe(`${horizon} ${horizon === 1 ? "semana" : "semanas"} depois · H${horizon}`);
  });
  it("mostra indicação oficial sem reclassificar o score pelo limite", () => {
    const html = result();
    expect(visible(html)).toContain(">ALERTA<");
    expect(visible(html)).not.toContain(">SEM ALERTA<");
    expect(html).toContain("não a confirmação");
    expect(html).toContain("SE49");
    expect(html).toContain("2 semanas depois · H2");
  });
  it("mantém probabilidade e limite sob demanda, diretamente dos props", () => {
    const html = result();
    expect(html).toContain("<summary>Como o alerta foi definido</summary>");
    expect(html).toContain("25,00%");
    expect(html).toContain("50,00%");
    expect(visible(html)).not.toContain("25,00%");
    expect(visible(html)).not.toContain("50,00%");
    expect(result("ready", { ...municipality, score: 0.75 }, { ...prediction, threshold: 0.4 })).toContain("75,00%");
    expect(result("ready", municipality, { ...prediction, threshold: 0.4 })).toContain("40,00%");
  });
  it("não interpreta sem alerta como ausência de dengue", () => {
    const html = result("ready", { ...municipality, status: "sem_alerta", predicao: false, score: 0.9 });
    expect(html).toContain(">SEM ALERTA<");
    expect(html).toContain("não significa ausência de dengue");
  });
  it("não atribui probabilidade zero ao território sem avaliação", () => {
    const html = result("ready", { ...municipality, status: "sem_avaliacao", score: null, predicao: null });
    expect(html).toContain(">SEM AVALIAÇÃO PREDITIVA<");
    expect(html).toContain("não tem resultado");
    expect(html).not.toContain("<details");
    expect(html).not.toContain("0,00%");
  });
  it("falha não exibe classificação nem resultado antigo, mesmo com props anteriores", () => {
    const html = result("error");
    expect(html).toContain("não pôde ser carregado");
    expect(html).toContain("sua seleção será mantida");
    expect(html).not.toContain("statusBadge");
    expect(html).not.toContain("<details");
    expect(html).not.toContain("25,00%");
    expect(html).not.toContain("SE49");
  });
  it("loading não exibe resultado anterior", () => {
    const html = result("loading");
    expect(html).toContain("Carregando o resultado");
    expect(html).not.toContain(">ALERTA<");
    expect(html).not.toContain("25,00%");
  });
  it("não inventa resultado quando o contrato está ausente", () => {
    expect(result("ready", municipality, null)).toBe("");
  });
  it("mantém natureza retrospectiva e limites essenciais fora da expansão", () => {
    const html = visible(result());
    expect(html).toContain("Avaliação retrospectiva de 2025, não um alerta atual");
    expect(html).toContain("não o risco observado");
    expect(html).toContain("Não representa a chance individual");
  });
  it("a integração preserva o retry, dados oficiais e alternativa de busca por teclado", async () => {
    const foundation = await readFile(new URL("./map-foundation.tsx", import.meta.url), "utf8");
    const map = await readFile(new URL("./municipality-map.tsx", import.meta.url), "utf8");
    expect(foundation).toContain("resolveCurrentMapSliceState(");
    expect(foundation).toContain("createMapSliceLoadingState(");
    expect(foundation).toContain("Tentar novamente");
    expect(map).toContain("joinMunicipalityPredictions(");
    expect(map).toContain("handleSearchKeyDown");
    expect(map).toContain("municipality={selectedPrediction}");
    expect(map).toContain("status={predictionStatus}");
    expect(map).toContain("não significa ausência de dengue");
  });
  it("as fontes da superfície do mapa permanecem UTF-8 sem mojibake", async () => {
    for (const filename of ["map-foundation.tsx", "municipality-map.tsx", "municipality-map-result.tsx", "../../app/mapa/page.tsx"]) {
      const source = await readFile(new URL(filename, import.meta.url), "utf8");
      // “Ã” sozinho também ocorre em português correto, como AVALIAÇÃO.
      expect(source).not.toMatch(/Ã[©£ª\u00ad³¡]|Â[·\u00a0]|�|â€/);
    }
  });
});
