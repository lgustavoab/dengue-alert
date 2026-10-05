import { readFile } from "node:fs/promises";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeAll, describe, expect, it, vi } from "vitest";

import {
  getHistoricalAnnual, getHistoricalWeekly, getHistoricalSeasonalityNational,
  getHistoricalSeasonalityRegional, getHistoricalSpatialRegions, getHistoricalSpatialStates,
  getHistoricalRiskWeekly, getHistoricalRiskMunicipalities, getHistoricalRiskEpisodeDuration,
  getHistoricalClimateNationalLags, getHistoricalClimateRegionalLags, getTerritoryFilterItems,
} from "@/lib/serving/server";
import { getHistoricalMunicipalitySeries } from "@/lib/serving/series-server";
import { formatDecimal, formatInteger } from "@/lib/serving/formatters";
import { HistoricalOverview } from "./historical-overview";
import { HistoricalRiskAnalysis } from "./historical-risk-analysis";
import { HistoricalClimateAnalysis } from "./historical-climate-analysis";
import { MunicipalityPanorama } from "./municipality-panorama";

let query = "";
vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(query),
  usePathname: () => "/historico",
  useRouter: () => ({ replace: vi.fn() }),
}));

async function loadContracts() {
  const [annual, weekly, seasonality, regionalSeasonality, regions, states, riskWeekly,
    riskMunicipalities, episodes, climate, regionalClimate, territories, municipality] = await Promise.all([
    getHistoricalAnnual(), getHistoricalWeekly(), getHistoricalSeasonalityNational(),
    getHistoricalSeasonalityRegional(), getHistoricalSpatialRegions(), getHistoricalSpatialStates(),
    getHistoricalRiskWeekly(), getHistoricalRiskMunicipalities(), getHistoricalRiskEpisodeDuration(),
    getHistoricalClimateNationalLags(), getHistoricalClimateRegionalLags(), getTerritoryFilterItems(),
    getHistoricalMunicipalitySeries("3537305"),
  ]);
  return { annual, weekly, seasonality, regionalSeasonality, regions, states, riskWeekly,
    riskMunicipalities, episodes, climate, regionalClimate, territories, municipality };
}

let data: Awaited<ReturnType<typeof loadContracts>>;
beforeAll(async () => { data = await loadContracts(); });

function overview(parameters = "") {
  query = parameters;
  return renderToStaticMarkup(createElement(HistoricalOverview, {
    annualData: data.annual.data, weeklyData: data.weekly.data,
    seasonalityData: data.seasonality.data, regionalSeasonalityData: data.regionalSeasonality.data,
    regionsData: data.regions.data, statesData: data.states.data, municipalityWeeks: 123456,
  }));
}

function risk(selectedRegion = "", selectedUf = "", selectedMunicipality: string | null = null) {
  return renderToStaticMarkup(createElement(HistoricalRiskAnalysis, {
    weeklyData: data.riskWeekly.data, municipalities: data.riskMunicipalities.data,
    episodeSummary: data.episodes.summary, episodeDistribution: data.episodes.distribution,
    selectedRegion, selectedUf, selectedMunicipality,
  }));
}

function climate(selectedRegion = "", selectedUf = "", selectedMunicipality: string | null = null) {
  return renderToStaticMarkup(createElement(HistoricalClimateAnalysis, {
    nationalData: data.climate.data, regionalData: data.regionalClimate.data,
    selectedRegion, selectedUf, selectedMunicipality,
  }));
}

function visible(html: string) {
  return html.replace(/<details\b[^>]*>[\s\S]*?<\/details>/g, "");
}

function municipal(selectedYear: number | null) {
  const territory = data.territories.find((item) => item.codigoIbge7 === "3537305")!;
  return renderToStaticMarkup(createElement(MunicipalityPanorama, { territory, series: data.municipality, selectedYear }));
}

describe("leitura guiada do histórico", () => {
  it("identifica tempo, quantidade e unidades nos eixos dos gráficos nacionais", () => {
    const html = overview();
    expect(html.match(/data-chart-axis="x-title"/g)).toHaveLength(4);
    expect(html.match(/data-chart-axis="y-title"/g)).toHaveLength(4);
    expect(html).toContain("Tempo — ano epidemiológico");
    expect(html).toContain("Casos prováveis por semana");
    expect(html).toContain("Casos prováveis no ano");
    expect(html).toContain("Incidência anual (casos por 100 mil habitantes)");
    expect(html).toContain("Incidência semanal (casos por 100 mil habitantes)");
    expect(overview("ano=2024")).toContain("Tempo — Semana Epidemiológica (SE) de 2024");
  });

  it("explicita percentual, episódios e correlação sem trocar suas escalas", () => {
    const riskHtml = risk();
    expect(riskHtml).toContain("Municípios em risco (% dos elegíveis)");
    expect(riskHtml).toContain('data-axis-value="1">100,0%');
    expect(riskHtml).toContain("Duração do episódio (semanas consecutivas)");
    expect(riskHtml).toContain("Quantidade de episódios");
    const climateHtml = climate();
    expect(climateHtml).toContain("Correlação de Spearman (sem unidade)");
    expect(climateHtml).toContain("Clima observado quantas semanas antes? (lag)");
    expect(climateHtml).toMatch(/data-axis-value="-/);
    expect(municipal(2024)).toContain("Eixo X: Semana Epidemiológica (SE) de 2024. Eixo Y: casos prováveis por semana, de 0 a");
  });

  it("prioriza evolução semanal e distingue casos de incidência", () => {
    const html = overview();
    expect(html.indexOf("Como os casos variaram ao longo das semanas?")).toBeLessThan(html.indexOf("Como os casos variaram entre os anos?"));
    expect(visible(html)).toContain("Gráfico de casos prováveis por semana · Brasil");
    expect(visible(html)).toContain("incidência expressa essa quantidade por 100 mil habitantes");
    expect(visible(html)).toContain("Em que épocas a incidência aumentou?");
    expect(html).toContain("Como os casos variaram entre lugares?");
  });

  it("retira cobertura e tabela extensa da leitura inicial, preservando valores anuais", () => {
    const html = overview();
    expect(visible(html)).not.toContain("123.456");
    expect(html).toContain("123.456 município-semanas");
    expect(html).toContain("não representa pessoas nem municípios distintos");
    expect(visible(html)).not.toContain("<table");
    expect(html).toContain("Consultar a tabela anual completa");
    expect(html).toContain('aria-label="Panorama anual da dengue" tabindex="0"');
    for (const item of data.annual.data) {
      expect(html).toContain(`<td>${formatInteger(item.casos_provaveis)}</td>`);
      expect(html).toContain(`<td>${formatDecimal(item.incidencia_anual_100mil)}</td>`);
    }
  });

  it("ano muda a evolução, mas sazonalidade e comparação declaram período completo", () => {
    const html = visible(overview("ano=2024"));
    expect(html).toContain("Como os casos variaram em 2024?");
    expect(html).toContain("Como foi o ano de 2024 no Brasil?");
    expect(html).toContain("não muda quando um único ano é selecionado");
    expect(html).toContain("mesmo quando um ano é selecionado");
    expect(html).toContain("mediana: o valor central");
  });

  it("região mostra resumo e sazonalidade regionais, sem curva semanal de casos inventada", () => {
    const html = overview("regiao=Sudeste");
    expect(html).toContain("Como os casos variaram entre lugares? · Sudeste");
    expect(html).toContain("Em que épocas a incidência aumentou? · Sudeste");
    expect(html).toContain("Não há uma curva semanal de casos da região");
    expect(html).not.toContain("Como os casos variaram ao longo das semanas?");
  });

  it("UF conserva resumo consolidado e informa ausência de série semanal ou sazonal", () => {
    const html = overview("regiao=Sudeste&uf=35");
    expect(html).toContain("São Paulo");
    expect(html).toContain("não uma série semanal ou sazonalidade específica por estado");
    expect(html).not.toContain("Em que épocas a incidência aumentou?");
    expect(html).not.toContain("Como os casos variaram ao longo das semanas?");
  });

  it("risco conserva definição observada e período diferente do histórico geral", () => {
    const html = risk();
    expect(visible(html)).toContain("2018–2025");
    expect(visible(html)).toContain("O filtro de ano não muda esta seção");
    expect(visible(html)).toContain("Risco histórico não é previsão");
    expect(visible(html)).toContain("não equivale a uma declaração oficial de epidemia");
    expect(html).toContain("percentil 90 (P90) sazonal");
    expect(html).toContain("estritamente maior");
    expect(html).toContain("não é o limiar usado para emitir um alerta");
  });

  it("mantém duração central em destaque e resumo completo sob demanda", () => {
    const html = risk();
    expect(visible(html)).toContain(`A duração mediana foi de ${formatInteger(data.episodes.summary.mediana)} semanas`);
    expect(visible(html)).toContain("A maior duração não representa um episódio típico");
    expect(visible(html)).not.toContain("Maior duração");
    expect(html).toContain(`${formatInteger(data.episodes.summary.maximo)} semanas`);
    expect(html).toContain("Comparar a frequência de risco entre municípios");
  });

  it.each([["Sudeste", ""], ["Sudeste", "35"]])("risco %s/%s não reutiliza duração nacional como territorial", (region, uf) => {
    const html = risk(region, uf);
    expect(html).not.toContain("Quanto duraram os períodos de risco?");
    expect(visible(html)).toContain("disponível apenas para o Brasil completo");
    if (uf) {
      expect(html).not.toContain("Quantos municípios estiveram em risco ao mesmo tempo?");
      expect(visible(html)).toContain("não para estados");
    } else {
      expect(html).toContain('aria-label="Proporção semanal de municípios em risco na região Sudeste"');
    }
  });

  it("risco municipal não se confunde com série semanal nem situação atual", () => {
    const html = visible(risk("Sudeste", "35", "3537305"));
    expect(html).toContain("Penápolis");
    expect(html).toContain("não somente o ano selecionado");
    expect(html).toContain("Não é a situação atual");
    expect(html).toContain("Não há curva semanal de risco");
    expect(html).not.toContain("Quanto duraram os períodos de risco?");
  });

  it("risco municipal apresenta o denominador oficial sem destacar métricas complementares", () => {
    const summary = data.riskMunicipalities.data.find((item) => item.codigo_ibge_7 === "3537305")!;
    const html = risk("Sudeste", "35", "3537305");
    expect(visible(html)).toContain(`${formatInteger(summary.semanas_risco)} de ${formatInteger(summary.observacoes_elegiveis)} semanas com histórico suficiente`);
    expect(visible(html)).not.toContain("Risco em mais de um ano");
    expect(html).toContain(`Risco em mais de um ano: ${summary.recorrencia_multianual ? "Sim" : "Não"}`);
  });

  it("ausência de risco municipal disponível não vira ausência de risco", () => {
    expect(visible(risk("Centro-Oeste", "51", "5101837"))).toContain("Ausência de avaliação não significa ausência de risco");
  });

  it("clima declara correlações municipais, não causalidade ou desempenho preditivo", () => {
    const html = climate();
    expect(visible(html)).toContain("2016–2025");
    expect(visible(html)).toContain("calculadas separadamente em cada município");
    expect(visible(html)).toContain("Não são uma única correlação");
    expect(visible(html)).toContain("Correlação não implica causalidade");
    expect(visible(html)).toContain("nem medem a contribuição do clima para o desempenho do modelo");
    expect(visible(html)).not.toContain("<svg");
    expect(html).toContain("não um prazo ótimo definitivo");
    expect(html).toContain("A correlação de Spearman varia de −1 a 1");
    expect(html).toContain("é o limite da janela analisada");
  });

  it.each([["Sudeste", "35", null], ["Sudeste", "35", "3537305"]])("clima indisponível %s/%s/%s não simula associação local", (region, uf, code) => {
    const html = climate(region, uf, code);
    expect(html).not.toContain("<svg");
    expect(html).toContain("não significa ausência de relação entre clima e dengue");
    expect(html.toLocaleLowerCase("pt-BR")).toContain("selecione brasil ou uma região");
  });

  it("consulta anual municipal explica unidade, cobertura e preenchimento com zero", () => {
    const html = municipal(null);
    expect(visible(html)).toContain("Como os casos variaram? · Penápolis");
    expect(visible(html)).toContain("casos por 100 mil habitantes");
    expect(visible(html)).not.toContain("Semanas disponíveis");
    expect(html).toContain(`${formatInteger(data.municipality.count)} semanas`);
    expect(html).toContain("não comprovam ausência de transmissão");
    expect(html).toContain("Incidência anual (por 100 mil habitantes)");
  });

  it("valores municipais semanais são consultáveis por toque e teclado sem hover", () => {
    const html = municipal(2024);
    expect(html).toContain("Consultar valores semanais e cobertura");
    expect(html).toContain('aria-label="Gráfico semanal de Penápolis" tabindex="0"');
    expect(html).toContain('aria-label="Valores da série municipal" tabindex="0"');
    const table = html.match(/<table[\s\S]*?<\/table>/)![0];
    const indices = data.municipality.data.ano_epidemiologico.flatMap((year, index) => year === 2024 ? [index] : []);
    expect(table.match(/<tbody>[\s\S]*?<\/tbody>/)![0].match(/<tr>/g)).toHaveLength(indices.length);
    for (const index of indices) {
      expect(table).toContain(`<td>SE ${data.municipality.data.semana_epidemiologica[index]}</td><td>${formatInteger(data.municipality.data.casos_provaveis[index])}</td><td>${data.municipality.data.zero_preenchido[index] ? "Sim" : "Não"}</td>`);
    }
  });

  it("expansões começam fechadas e navegação local mantém os três temas", async () => {
    for (const html of [overview(), risk(), climate(), municipal(2024)]) {
      expect(html).toContain("<summary>");
      expect(html).not.toMatch(/<details[^>]*\bopen(?:\s|=|>)/);
    }
    const page = await readFile(new URL("../../app/historico/page.tsx", import.meta.url), "utf8");
    for (const id of ["historical-cases", "historical-risk", "historical-climate"]) {
      expect(page).toContain(`href="#${id}"`);
      expect(page).toContain(`id="${id}"`);
    }
    expect(page).not.toContain("contratos históricos validados");
  });

  it("textos desta etapa permanecem UTF-8 sem corrupção real", async () => {
    const paths = ["annual-panorama.tsx", "weekly-evolution.tsx", "historical-overview.tsx",
      "seasonality-chart.tsx", "territorial-analysis.tsx", "municipality-panorama.tsx",
      "historical-risk-analysis.tsx", "historical-climate-analysis.tsx", "historical-details.tsx", "historical-chart-axes.tsx",
      "../../app/historico/page.tsx"];
    for (const path of paths) {
      const source = await readFile(new URL(path, import.meta.url), "utf8");
      for (const marker of ["\u00c3", "\u00c2", "\ufffd", "\u00e2\u20ac"]) {
        expect(source, path).not.toContain(marker);
      }
    }
  });
});
