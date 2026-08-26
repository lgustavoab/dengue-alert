const integerFormatter = new Intl.NumberFormat(
  "pt-BR",
  {
    maximumFractionDigits: 0,
  },
);

const decimalFormatter = new Intl.NumberFormat(
  "pt-BR",
  {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  },
);

const percentFormatter = new Intl.NumberFormat(
  "pt-BR",
  {
    style: "percent",
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  },
);

export function formatInteger(
  value: number,
): string {
  return integerFormatter.format(
    value,
  );
}

export function formatDecimal(
  value: number,
): string {
  return decimalFormatter.format(
    value,
  );
}

export function formatPercent(
  value: number,
): string {
  return percentFormatter.format(
    value,
  );
}

export function formatPeriod(
  period: string,
): string {
  return period.replace(
    "-",
    "–",
  );
}

export function formatHorizonRange(
  horizons: number[],
): string {
  if (horizons.length === 0) {
    return "—";
  }

  const sorted = [
    ...horizons,
  ].sort(
    (a, b) => a - b,
  );

  const first = sorted[0];
  const last = sorted[
    sorted.length - 1
  ];

  if (first === last) {
    return `H${first}`;
  }

  return `H${first}–H${last}`;
}