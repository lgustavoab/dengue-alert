import { readFile } from "node:fs/promises";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import type {
  PredictionMunicipalitySeriesContract,
  PredictionMunicipalitySeriesHorizon,
} from "@/lib/serving/types";
import { PredictionResults } from "./prediction-results";
import { PredictionScoreEvolution } from "./prediction-score-evolution";

function horizon({
  prediction = true,
  target = true,
  origin = false,
  score = 0.18769,
  week = 49,
  available = true,
} = {}): PredictionMunicipalitySeriesHorizon {
  return {
    count: available ? 1 : 0,
    threshold: 0.187687,
    data: {
      ano_epidemiologico: available ? [2025] : [],
      semana_epidemiologica: available ? [week] : [],
      data_inicio_semana: available ? ["2025-11-30"] : [],
      risco_elevado: available ? [origin] : [],
      target: available ? [target] : [],
      score: available ? [score] : [],
      predicao: available ? [prediction] : [],
    },
  };
}

function series(point = horizon()): PredictionMunicipalitySeriesContract {
  return {
    schema_version: "1.0",
    codigo_ibge_7: "3537305",
    count: point.count * 4,
    horizontes: { h1: point, h2: point, h3: point, h4: point },
  };
}

function render(data: PredictionMunicipalitySeriesContract, week = 49) {
  return renderToStaticMarkup(createElement(PredictionResults, { series: data, week }));
}

function cards(html: string): string[] {
  return Array.from(html.matchAll(/<article\b[^>]*>([\s\S]*?)<\/article>/g), (match) => match[1]);
}

describe("consulta municipal: alerta e observado no mesmo resultado", () => {
  it("oferece uma região nomeada e focável para rolar o gráfico de probabilidades", () => {
    const html = renderToStaticMarkup(
      createElement(PredictionScoreEvolution, { series: series(), selectedWeek: 49 }),
    );
    expect(html).toMatch(
      /<div[^>]*role="region"[^>]*aria-label="Evolução das probabilidades: semanas de 2025 e probabilidade de risco elevado"[^>]*tabindex="0"/,
    );
    expect(html).toContain('role="img"');
    expect(html).toContain("Semana selecionada");
  });

  it.each([
    [true, true, "ALERTA", "Os registros indicaram risco elevado nessa semana.", "O alerta se confirmou nos dados observados."],
    [true, false, "ALERTA", "Os registros não indicaram risco elevado nessa semana.", "O alerta não se confirmou nos dados observados."],
    [false, true, "SEM ALERTA", "Os registros indicaram risco elevado nessa semana.", "O risco elevado foi observado, mas o modelo não emitiu alerta."],
    [false, false, "SEM ALERTA", "Os registros não indicaram risco elevado nessa semana.", "O modelo não emitiu alerta e os registros não indicaram risco elevado."],
  ] as const)(
    "compara predicao=%s e target=%s sem trocar a classificação",
    (prediction, target, classification, observed, outcome) => {
      const html = render(series(horizon({ prediction, target, score: prediction ? 0.18769 : 0.18768 })));
      const results = cards(html);
      expect(results).toHaveLength(4);

      results.forEach((card, index) => {
        expect(card).toContain(`${index + 1} semana${index === 0 ? "" : "s"} depois</h3>`);
        expect(card).toContain(`H${index + 1}</span>`);
        expect(card).toContain("Previsão do modelo</span>");
        expect(card).toContain("Resultado nos dados reais</dt>");
        expect(card).toContain("Comparação entre previsão e dados reais</span>");
        expect(card).toContain(`>${classification}</strong>`);
        expect(card).toContain(`${observed}</dd>`);
        expect(card).toContain(`${outcome}</strong>`);
      });
    },
  );

  it("explica que a comparação usa registros reais de 2025 com limitações", () => {
    const visible = render(series()).replace(/<details\b[^>]*>[\s\S]*?<\/details>/g, "");
    expect(visible).toContain("comparar a previsão do modelo com os dados reais registrados em 2025");
    expect(visible).toContain("Cada prazo mostra uma semana futura em relação à semana de referência selecionada");
    expect(visible).toContain("Os dados reais são registros de dengue tratados para a pesquisa");
    expect(visible).toContain("sujeitos às limitações das notificações");
    expect(visible).toContain("Sem risco elevado nos registros não significa ausência de casos de dengue");
    expect(visible).toContain("Não são alertas atuais");
  });

  it("mantém H1 confirmado e H2 não confirmado quando ambos emitiram alerta", () => {
    const data = series();
    data.horizontes.h1 = horizon({ prediction: true, target: true, score: 0.356 });
    data.horizontes.h2 = {
      ...horizon({ prediction: true, target: false, score: 0.409 }),
      threshold: 0.1908,
    };
    const results = cards(render(data));
    for (const card of results.slice(0, 2)) {
      expect(card).toContain(">ALERTA</strong>");
      expect(card).toContain("O modelo emitiu um alerta para essa semana futura.");
    }
    expect(results[0]).toContain("Os registros indicaram risco elevado nessa semana.</dd>");
    expect(results[0]).toContain("O alerta se confirmou nos dados observados.</strong>");
    expect(results[1]).toContain("Os registros não indicaram risco elevado nessa semana.</dd>");
    expect(results[1]).toContain("O alerta não se confirmou nos dados observados.</strong>");
    expect(results[1]).toContain("40,9%");
    expect(results[1]).toContain("19,08%");
    expect(results[1]).not.toContain(">SEM ALERTA</strong>");
  });

  it("não reclassifica SEM ALERTA usando percentuais arredondados", () => {
    // 18,8% parece superar 18,77%, mas o score real é menor que o limite.
    const html = render(series(horizon({ prediction: false, target: true, score: 0.18768 })));
    expect(html).toContain("18,8%");
    expect(html).toContain("18,77%");
    for (const card of cards(html)) {
      expect(card).toContain(">SEM ALERTA</strong>");
      expect(card).not.toContain(">ALERTA</strong>");
      expect(card).toContain("O risco elevado foi observado, mas o modelo não emitiu alerta.");
      expect(card).not.toContain("aria-label=\"Probabilidade");
    }
  });

  it("usa predicao como fonte da classificação, sem derivá-la do score", () => {
    // Fixture deliberadamente divergente para detectar recálculo na apresentação;
    // não representa um registro científico real.
    const html = render(series(horizon({ prediction: false, target: true, score: 0.9 })));
    for (const card of cards(html)) {
      expect(card).toContain(">SEM ALERTA</strong>");
      expect(card).not.toContain(">ALERTA</strong>");
      expect(card).toContain("O risco elevado foi observado, mas o modelo não emitiu alerta.");
    }
  });

  it.each([true, false])("mantém visível o estado na origem: risco=%s", (origin) => {
    const html = render(series(horizon({ origin })));
    const beforeCards = html.slice(0, html.indexOf("<article"));
    expect(beforeCards).toContain("Na semana de referência");
    expect(beforeCards).toContain(origin ? "Já havia risco elevado" : "Não havia risco elevado");
    expect(beforeCards).toContain(origin ? "não pertence ao recorte de antecipação" : "quando ele ainda não estava presente");
    expect(beforeCards).not.toContain("<details");
  });

  it("distingue prazos sem avaliação de ausência de alerta", () => {
    const data = series();
    data.horizontes.h2 = horizon({ available: false });
    data.horizontes.h3 = horizon({ available: false });
    data.horizontes.h4 = horizon({ available: false });
    data.count = 1;
    const results = cards(render(data));
    expect(results[0]).toContain("O alerta se confirmou nos dados observados.");
    for (const card of results.slice(1)) {
      expect(card).toContain("Sem avaliação neste prazo");
      expect(card).not.toContain("Previsão do modelo");
      expect(card).not.toContain("Resultado nos dados reais");
      expect(card).not.toContain("Comparação entre previsão e dados reais");
      expect(card).not.toContain(">SEM ALERTA</strong>");
      expect(card).not.toContain("<details");
    }
  });

  it("não reutiliza resultados de outra semana", () => {
    const html = render(series(), 50);
    expect(html).not.toContain("O alerta se confirmou nos dados observados.");
    expect(html).not.toContain("Resultado nos dados reais");
    expect(cards(html).every((card) => card.includes("Sem avaliação neste prazo"))).toBe(true);
  });

  it("deixa valores técnicos sob demanda e ressalvas essenciais visíveis", () => {
    const html = render(series());
    const details = Array.from(html.matchAll(/<details\b([^>]*)>([\s\S]*?)<\/details>/g));
    expect(details).toHaveLength(4);
    for (const [, attributes, content] of details) {
      expect(attributes).not.toMatch(/\bopen\b/);
      expect(content).toContain("<summary>Como o alerta foi definido</summary>");
      expect(content).toContain("Probabilidade estimada pelo modelo");
      expect(content).toContain("Limite para emitir alerta");
    }
    const visible = html.replace(/<details\b[^>]*>[\s\S]*?<\/details>/g, "");
    expect(visible).not.toContain("18,8%");
    expect(visible).toContain("Sem alerta não significa ausência de dengue nem garantia de segurança");
    expect(visible).toContain("quatro semanas (casos por 100 mil habitantes)");
    expect(visible).toContain("não equivale a uma declaração oficial de epidemia");
    expect(visible).toContain("Não são alertas atuais");
  });

  it("preserva UTF-8 nos textos da consulta", async () => {
    for (const file of ["prediction-results.tsx", "prediction-retrospective.tsx", "prediction-selection.tsx"]) {
      const source = await readFile(new URL(file, import.meta.url), "utf8");
      expect(source).not.toMatch(/Ã|Â|�|â€/);
    }
  });
});
