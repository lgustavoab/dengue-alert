import { readFile } from "node:fs/promises";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeAll, describe, expect, it } from "vitest";

import { PREDICTION_HORIZONS } from "@/lib/prediction-selection-utils";
import { getPredictionByHorizon } from "@/lib/serving/server";
import type { PredictionByHorizonContract } from "@/lib/serving/types";
import { PredictionPerformance } from "./prediction-performance";
import {
  formatEvaluationInteger,
  formatEvaluationPercent,
  formatEvaluationScore,
} from "./prediction-evaluation-presentation";

let evaluation: PredictionByHorizonContract;

beforeAll(async () => {
  evaluation = await getPredictionByHorizon();
});

function render(data = evaluation) {
  return renderToStaticMarkup(createElement(PredictionPerformance, { evaluation: data }));
}

function visibleContent(html: string) {
  return html.replace(/<details\b[^>]*>[\s\S]*?<\/details>/g, "");
}

function articles(html: string) {
  return Array.from(html.matchAll(/<article\b[^>]*>([\s\S]*?)<\/article>/g), (match) => match[1]);
}

function tables(html: string) {
  return Array.from(html.matchAll(/<table\b[^>]*>([\s\S]*?)<\/table>/g), (match) => match[1]);
}

function rowCells(table: string, label: string) {
  const row = Array.from(table.matchAll(/<tr>([\s\S]*?)<\/tr>/g), (match) => match[1])
    .find((content) => content.includes(`>${label}</th>`));
  expect(row, label).toBeDefined();
  return Array.from(row!.matchAll(/<td>(.*?)<\/td>/g), (match) => match[1]);
}

describe("avaliação do modelo em linguagem acessível", () => {
  it("explica direção e exemplos sem transformar métricas em acerto ou risco individual", () => {
    const guide = render().split("Como ler os indicadores")[1];
    expect(guide).toContain("uma situação é um município em uma semana, não uma pessoa");
    expect(guide).toContain("Brasil em 2025, uma semana");
    expect(guide).toContain("somente nas situações sem risco elevado na origem");
    expect(guide).toContain("0 a 1. Maior é melhor");
    expect(guide).toContain("0 a 1 nesta avaliação binária. Menor é melhor");
    expect(guide).toContain("Não existe “maior é melhor” ou “menor é melhor”");
    expect(guide).toContain("0,5 é a referência de uma ordenação ao acaso");
    expect(guide).toContain("não é a chance de uma pessoa ter dengue");
    expect(guide).toContain("São erros de uma única situação; o Brier do estudo é a média");
    expect(guide.match(/Exemplo ilustrativo:/g)).toHaveLength(4);
    expect(guide.match(/Exemplo real:/g)).toHaveLength(4);
  });

  it("exemplos reais acompanham o contrato de H1 e tratam alerta ausente como não informado", () => {
    const changed = structuredClone(evaluation);
    const metrics = changed.horizontes.h1.modelo_final.early_warning;
    metrics.matriz_confusao.tp = 17;
    metrics.positivos = 31;
    metrics.alertas = 42;
    metrics.pr_auc_average_precision = 0.321;
    let guide = render(changed).split("Como ler os indicadores")[1];
    expect(guide).toContain("houve alerta em 17 de 31 situações");
    expect(guide).toContain("dos 42 alertas, 17 se confirmaram");
    expect(guide).toContain(`AP do modelo: ${formatEvaluationScore(metrics.pr_auc_average_precision)}`);
    metrics.alertas = null;
    guide = render(changed).split("Como ler os indicadores")[1];
    expect(guide).toContain("a quantidade de alertas não está informada neste recorte");
    expect(guide).not.toContain("dos — alertas");
  });

  it("explica escopos, unidades e limites sem depender de expansão", () => {
    const visible = visibleContent(render());
    expect(visible).toContain("Todas as situações avaliadas");
    expect(visible).toContain("Sem risco elevado no ponto de partida");
    expect(visible).toContain("não medem o desempenho da cidade selecionada");
    expect(visible).toContain("não representam pessoas nem municípios distintos");
    expect(visible).toContain("não com qualquer ocorrência ao longo do intervalo");
    expect(visible).toContain("único ano, 2025");
    expect(visible).toContain("não garante o mesmo desempenho em cada município nem em uso atual");
  });

  it.each(PREDICTION_HORIZONS)("apresenta denominadores e erros oficiais de %s", (key) => {
    const index = PREDICTION_HORIZONS.indexOf(key);
    const card = articles(render())[index];
    const metrics = evaluation.horizontes[key].modelo_final.early_warning;
    expect(card).toContain(formatEvaluationPercent(metrics.recall));
    expect(card).toContain(formatEvaluationPercent(metrics.precision));
    expect(card).toContain(`${formatEvaluationInteger(metrics.matriz_confusao.tp)} de ${formatEvaluationInteger(metrics.positivos)} situações identificadas`);
    expect(card).toContain(`${formatEvaluationInteger(metrics.matriz_confusao.tp)} de ${formatEvaluationInteger(metrics.alertas)} alertas confirmados`);
    expect(card).toContain("Alertas não confirmados");
    expect(card).toContain(`${formatEvaluationInteger(metrics.matriz_confusao.fp)}</dd>`);
    expect(card).toContain("Situações de risco não identificadas");
    expect(card).toContain(`${formatEvaluationInteger(metrics.matriz_confusao.fn)}</dd>`);
  });

  it("não confunde recall geral com antecipação, nem AP com porcentagem de acerto", () => {
    const html = render();
    const visible = visibleContent(html);
    expect(visible).toContain("89,8%");
    expect(visible).toContain("44,8%");
    expect(visible).toContain("Não são uma porcentagem única de acerto");
    expect(html).toContain("Average Precision (AP)");
    expect(html).not.toContain("PR-AUC");
    expect(html).toContain("Uma AP de 0,92 não significa 92% de acerto");
    expect(html).toContain("vantagem em AP não significa superioridade em todas as métricas");
  });

  it("mantém todas as métricas dos quatro prazos e dois cenários no detalhe", () => {
    const technicalTables = tables(render());
    expect(technicalTables).toHaveLength(4);
    const metricRows = [
      ["Situações avaliadas", "observacoes", formatEvaluationInteger],
      ["Com risco elevado na semana futura", "positivos", formatEvaluationInteger],
      ["Sem risco elevado na semana futura", "negativos", formatEvaluationInteger],
      ["Prevalência do risco elevado", "prevalencia", formatEvaluationPercent],
      ["Average Precision (AP)", "pr_auc_average_precision", formatEvaluationScore],
      ["ROC-AUC", "roc_auc", formatEvaluationScore],
      ["Recall", "recall", formatEvaluationPercent],
      ["Precisão", "precision", formatEvaluationPercent],
      ["F1", "f1", formatEvaluationPercent],
      ["Acurácia balanceada", "balanced_accuracy", formatEvaluationPercent],
      ["Brier score", "brier_score", formatEvaluationScore],
    ] as const;

    PREDICTION_HORIZONS.forEach((key, index) => {
      const horizon = evaluation.horizontes[key];
      const columns = [horizon.modelo_final.geral, horizon.baseline_persistencia.geral,
        horizon.modelo_final.early_warning, horizon.baseline_persistencia.early_warning];
      for (const [label, field, format] of metricRows) {
        expect(rowCells(technicalTables[index], label)).toEqual(columns.map((m) => format(m[field])));
      }
      for (const [label, field] of [
        ["Alertas confirmados (TP)", "tp"], ["Alertas não confirmados (FP)", "fp"],
        ["Riscos não identificados (FN)", "fn"], ["Sem alerta e sem risco elevado observado (TN)", "tn"],
      ] as const) {
        expect(rowCells(technicalTables[index], label)).toEqual(columns.map((m) => formatEvaluationInteger(m.matriz_confusao[field])));
      }
      expect(rowCells(technicalTables[index], "Alertas emitidos no recorte de antecipação")).toEqual([
        "—", "—", formatEvaluationInteger(horizon.modelo_final.early_warning.alertas),
        formatEvaluationInteger(horizon.baseline_persistencia.early_warning.alertas),
      ]);
      expect(rowCells(technicalTables[index], "Proporção de alertas no recorte de antecipação")).toEqual([
        "—", "—", formatEvaluationPercent(horizon.modelo_final.early_warning.proporcao_alertas),
        formatEvaluationPercent(horizon.baseline_persistencia.early_warning.proporcao_alertas),
      ]);
    });
  });

  it("não transforma campos nulos em zero", () => {
    const data = structuredClone(evaluation);
    data.horizontes.h1.modelo_final.early_warning.alertas = null;
    data.horizontes.h1.modelo_final.early_warning.proporcao_alertas = null;
    expect(articles(render(data))[0]).toContain("Total de alertas não informado");
    expect(rowCells(tables(render(data))[0], "Alertas emitidos no recorte de antecipação")).toEqual(["—", "—", "—", "—"]);
    expect(rowCells(tables(render(data))[0], "Proporção de alertas no recorte de antecipação")).toEqual(["—", "—", "—", "—"]);
  });

  it("lê as métricas dos props, sem números científicos duplicados", () => {
    const data = structuredClone(evaluation);
    data.horizontes.h1.modelo_final.early_warning.recall = 0.125;
    data.horizontes.h1.modelo_final.early_warning.precision = 0.25;
    data.horizontes.h1.modelo_final.early_warning.matriz_confusao.fp = 123;
    const card = articles(render(data))[0];
    expect(card).toContain("12,5%");
    expect(card).toContain("25,0%");
    expect(card).toContain("123</dd>");
    expect(card).not.toContain("44,8%");
    expect(card).not.toContain("27,4%");
  });

  it("oferece detalhe fechado, tabelas semânticas e regiões roláveis por teclado", () => {
    const html = render();
    expect(html.match(/<details\b/g)).toHaveLength(1);
    expect(html).not.toMatch(/<details\b[^>]*\bopen\b/);
    expect(visibleContent(html)).not.toContain("<table");
    expect(html.match(/role="region" aria-labelledby="evaluation-table-h\d-caption" tabindex="0"/g)).toHaveLength(4);
    for (const table of tables(html)) {
      expect(table).toContain('<caption id="evaluation-table-');
      expect(table).toContain('scope="colgroup"');
      expect(table).toContain('scope="row"');
      expect(table).toContain("Modelo · geral");
      expect(table).toContain("Persistência · antecipação");
    }
  });

  it("preserva UTF-8 nas novas explicações", async () => {
    for (const file of ["prediction-performance.tsx", "prediction-early-warning.tsx", "prediction-evaluation-details.tsx", "prediction-evaluation-presentation.ts"]) {
      expect(await readFile(new URL(file, import.meta.url), "utf8")).not.toMatch(/Ã|Â|�|â€/);
    }
  });
});
