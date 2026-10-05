import type { PropsWithChildren } from "react";
import type { ChartPadding } from "@/lib/historical-chart-utils";
import { formatDecimal, formatInteger, formatPercent } from "@/lib/serving/formatters";
import styles from "./historical-chart-axes.module.css";

// Labels get extra space; existing plot coordinates and scales remain unchanged.
export function historicalChartViewBox(width: number, height: number) {
  return `-110 -40 ${width + 130} ${height + 85}`;
}

export function HistoricalChartFrame({ label, children }: PropsWithChildren<{ label: string }>) {
  return <><div className={styles.scroll} role="region" aria-label={label} tabIndex={0}>{children}</div><p className={styles.hint}>Em telas pequenas, deslize o gráfico na horizontal para ler os eixos. Também é possível usar as setas do teclado.</p></>;
}

export function HistoricalChartAxes({ width, height, padding, minimum = 0, maximum, xLabel, yLabel, format = "decimal" }: {
  width: number; height: number; padding: ChartPadding; minimum?: number; maximum: number;
  xLabel: string; yLabel: string; format?: "integer" | "decimal" | "percent" | "correlation";
}) {
  const fractions = format === "integer" && maximum - minimum < 4 ? [0, 1] : [0, 0.25, 0.5, 0.75, 1];
  const label = (value: number) => format === "integer" ? formatInteger(value)
    : format === "percent" ? formatPercent(value)
    : format === "correlation" ? new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 3, maximumFractionDigits: 3 }).format(value)
    : formatDecimal(value);
  const bottom = height - padding.bottom;
  return (
    <g>
      <text x={padding.left} y={-10} className={styles.title} data-chart-axis="y-title">{yLabel}</text>
      {fractions.map((fraction) => {
        const value = maximum - fraction * (maximum - minimum);
        const y = padding.top + fraction * (bottom - padding.top);
        return <text key={fraction} x={padding.left - 12} y={y} textAnchor="end" dominantBaseline="middle" data-chart-axis="y-tick" data-axis-value={value}>{label(value)}</text>;
      })}
      <line x1={padding.left} x2={padding.left} y1={padding.top} y2={bottom} className={styles.line} />
      <line x1={padding.left} x2={width - padding.right} y1={bottom} y2={bottom} className={styles.line} />
      <text x={(padding.left + width - padding.right) / 2} y={height + 25} textAnchor="middle" className={styles.title} data-chart-axis="x-title">{xLabel}</text>
    </g>
  );
}
