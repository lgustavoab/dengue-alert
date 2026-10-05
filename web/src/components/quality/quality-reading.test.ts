import { readFile } from "node:fs/promises";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeAll, describe, expect, it } from "vitest";
import { getClimateCoverage, getPopulationCoverage, getQualityOverview, getSinanPipeline, getTerritorialCoverage } from "@/lib/serving/server";
import { formatInteger } from "@/lib/serving/formatters";
import { QualityOverview } from "./quality-overview";

async function loadData() {
  const [overview, sinan, territory, population, climate] = await Promise.all([
    getQualityOverview(), getSinanPipeline(), getTerritorialCoverage(),
    getPopulationCoverage(), getClimateCoverage(),
  ]);
  return { overview, sinan, territory, population, climate };
}
let data: Awaited<ReturnType<typeof loadData>>;
beforeAll(async () => { data = await loadData(); });
function render(props = data) {
  return renderToStaticMarkup(createElement(QualityOverview, props));
}
function visible(html: string) {
  return html.replace(/<details\b[^>]*>[\s\S]*?<\/details>/g, "");
}

describe("leitura didática de dados e método", () => {
  it("organiza a leitura pelas cinco perguntas principais", () => {
    const html = visible(render());
    for (const title of ["Quais dados usamos?", "Como organizamos os dados?", "O que chamamos de risco elevado?", "Como testamos o modelo?", "O que os resultados não permitem concluir?"]) {
      expect(html).toContain(title);
    }
    for (const anchor of ["quality-sources-title", "quality-method-title", "quality-detail-title"]) {
      expect(html).toContain(`href="#${anchor}"`);
      expect(html).toContain(`id="${anchor}"`);
    }
  });
  it("explica o papel das fontes antes de campos técnicos", () => {
    const html = visible(render());
    expect(html).toContain("Casos notificados — SINAN");
    expect(html).toContain("Referências municipais — IBGE");
    expect(html).toContain("Estimativas meteorológicas — ERA5-Land");
    expect(html).toContain("Não são medições de uma estação instalada em cada município");
    expect(html).toContain("casos por 100 mil habitantes");
    expect(html).not.toContain("CLASSI_FIN");
    expect(html).not.toContain("NDUPLIC_N");
  });
  it("mantém o significado de município-semana e o limite do zero-fill visíveis", () => {
    const html = visible(render());
    expect(html).toContain("um município em uma semana, não uma pessoa");
    expect(html).toContain("Uma semana preenchida com zero não comprova ausência de dengue");
    expect(html).toContain("nem comprova ausência de transmissão");
    expect(html).toContain("Semana Epidemiológica");
  });
  it("não esconde a mudança da referência populacional", () => {
    expect(visible(render())).toContain(data.population.data.observacao_metodologica);
  });
  it("preserva todas as contagens gerais, deixando só três indicadores principais", () => {
    const html = render();
    for (const value of Object.values(data.overview.data)) expect(html).toContain(formatInteger(value));
    expect(visible(html).match(/class="metric-card"/g)).toHaveLength(3);
    expect(html.match(/<details\b/g)).toHaveLength(8);
    expect(html).not.toMatch(/<details[^>]*\bopen(?:=|>)/);
  });
  it("preserva filtros, campos e verificação sem contagem, sem transformá-la em zero", () => {
    const html = render();
    for (const step of data.sinan.data.etapas) {
      expect(html).toContain(step.label);
      if (step.field) expect(html).toContain(step.field);
      if (step.records_removed !== null) expect(html).toContain(`${formatInteger(step.records_removed)} removidos`);
    }
    expect(html).toContain("Verificação lógica · sem contagem própria");
    expect(html).toContain(formatInteger(data.sinan.data.total_remocoes_documentadas));
  });
  it("preserva as contagens de zero-fill e os totais de casos antes e depois", () => {
    const html = render();
    for (const value of Object.values(data.sinan.data.zero_fill)) expect(html).toContain(formatInteger(value));
    expect(html).toContain(`${formatInteger(data.sinan.data.zero_fill.casos_antes)} casos antes e ${formatInteger(data.sinan.data.zero_fill.casos_depois)} depois`);
  });
  it("mantém referência territorial, Distrito Federal e resíduos explícitos", () => {
    const html = render();
    const territory = data.territory.data;
    expect(html).toContain(territory.referencia);
    expect(html).toContain(territory.distrito_federal.codigo_ibge_7_destino);
    expect(html).toContain(formatInteger(territory.distrito_federal.casos_preservados));
    expect(html).toContain(formatInteger(territory.residuais_nao_municipais.casos_excluidos));
  });
  it("preserva a tabela populacional acessível e suas referências anuais", () => {
    const html = render();
    expect(html).toContain('role="region" aria-label="Referência populacional por ano epidemiológico" tabindex="0"');
    expect(html).toContain("<caption>Referência populacional por ano epidemiológico</caption>");
    for (const year of data.population.data.por_ano) {
      expect(html).toContain(`<th scope="row">${year.ano_epidemiologico}</th>`);
      expect(html).toContain(year.anos_referencia_populacao.join(", "));
    }
  });
  it("mantém lacunas e critérios climáticos sem atribuir ausência de dengue", () => {
    const html = render();
    expect(html).toContain(formatInteger(data.climate.data.municipio_semanas_sem_clima));
    for (const code of data.climate.data.codigos_excluidos) expect(html).toContain(code);
    for (const count of Object.values(data.climate.data.metodos_selecao_grid)) expect(html).toContain(formatInteger(count));
    expect(visible(html)).toContain("lacunas na integração climática");
    expect(visible(html)).toContain("não significa que o clima não tenha relação com dengue");
  });
  it("distingue risco observado, alerta e desenvolvimento do teste final", () => {
    const html = render();
    expect(html).toContain("incidência acumulada em quatro semanas &gt; P90 sazonal");
    expect(html).toContain("igualdade não caracteriza risco elevado");
    expect(html).toContain("no mínimo dois anos de histórico e 12 observações válidas");
    expect(html).toContain("atinge ou supera o limite");
    expect(visible(html)).toContain("Desenvolvimento — 2018 a 2024");
    expect(visible(html)).toContain("Teste final — 2025");
    expect(visible(html)).toContain("apenas nas situações ainda sem risco elevado");
    expect(visible(html)).toContain("um único ano");
    expect(visible(html)).toContain("Uma métrica nacional não garante");
  });
  it("mantém rastreabilidade sem inventar links públicos para arquivos internos", () => {
    const html = render();
    for (const contract of Object.values(data)) {
      for (const source of contract.source) expect(html).toContain(source);
    }
    expect(html).toContain("não links públicos para download");
    expect(visible(html)).not.toContain("reports/audits/");
    expect(html).not.toMatch(/href="(?:reports|data)\//);
    expect(html).toContain('href="/predicao"');
  });
  it("usa props para os números e não modifica os contratos", () => {
    const before = JSON.stringify(data);
    const changed = { ...data, overview: { ...data.overview, data: { ...data.overview.data, casos_finais_preservados: 123456789 } } };
    expect(visible(render(changed))).toContain("123.456.789");
    render();
    expect(JSON.stringify(data)).toBe(before);
  });
  it("preserva UTF-8 e carregamento paralelo sem introduzir chamadas HTTP", async () => {
    const component = await readFile(new URL("./quality-overview.tsx", import.meta.url), "utf8");
    const page = await readFile(new URL("../../app/dados-qualidade/page.tsx", import.meta.url), "utf8");
    for (const source of [component, page]) {
      expect(source).not.toMatch(/Ã[©£ª\u00ad³¡]|Â[·\u00a0]|�|â€/);
      expect(source).not.toContain('"use client"');
      expect(source).not.toContain("fetch(");
    }
    expect(page).toContain("Promise.all(");
    expect(page).toContain('title="Dados e método"');
  });
});
