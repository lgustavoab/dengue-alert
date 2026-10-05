import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { HistoricalChartAxes, HistoricalChartFrame, historicalChartViewBox } from "./historical-chart-axes";

const geometry = { width: 960, height: 320, padding: { top: 28, right: 26, bottom: 50, left: 58 } };

function ticks(maximum: number, minimum = 0, format: "integer" | "decimal" | "percent" | "correlation" = "decimal") {
  const html = renderToStaticMarkup(createElement(HistoricalChartAxes, {
    ...geometry, maximum, minimum, format, xLabel: "Tempo", yLabel: "Quantidade",
  }));
  return Array.from(html.matchAll(/<text[^>]*y="([^"]+)"[^>]*data-chart-axis="y-tick"[^>]*data-axis-value="([^"]+)"[^>]*>([^<]+)<\/text>/g), (match) => ({ y: Number(match[1]), value: Number(match[2]), label: match[3] }));
}

describe("eixos históricos legíveis", () => {
  it("usa os limites e as coordenadas do gráfico, sem normalizar dados", () => {
    expect(ticks(100)).toEqual([
      { y: 28, value: 100, label: "100,0" }, { y: 88.5, value: 75, label: "75,0" },
      { y: 149, value: 50, label: "50,0" }, { y: 209.5, value: 25, label: "25,0" },
      { y: 270, value: 0, label: "0,0" },
    ]);
  });

  it("apresenta proporções como percentuais e correlações negativas sem perder sinal", () => {
    expect(ticks(1, 0, "percent").map((tick) => tick.label)).toEqual(["100,0%", "75,0%", "50,0%", "25,0%", "0,0%"]);
    expect(ticks(0.2, -0.2, "correlation").map((tick) => tick.label)).toEqual(["0,200", "0,100", "0,000", "-0,100", "-0,200"]);
  });

  it("evita rótulos inteiros repetidos quando há poucos casos", () => {
    expect(ticks(1, 0, "integer")).toEqual([{ y: 28, value: 1, label: "1" }, { y: 270, value: 0, label: "0" }]);
  });

  it("reserva espaço para rótulos e permite rolagem interna por teclado", () => {
    expect(historicalChartViewBox(960, 320)).toBe("-110 -40 1090 405");
    const html = renderToStaticMarkup(createElement(HistoricalChartFrame, { label: "Gráfico semanal" }, createElement("svg")));
    expect(html).toContain('role="region" aria-label="Gráfico semanal" tabindex="0"');
    expect(html).toContain("setas do teclado");
  });
});
