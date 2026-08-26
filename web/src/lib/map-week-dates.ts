const MILLISECONDS_PER_DAY =
  24 * 60 * 60 * 1_000;

const DAYS_PER_WEEK =
  7;

const EPIDEMIOLOGICAL_WEEK_ONE_START_2025 =
  "2024-12-29";

function parseIsoDate(
  value: string,
): Date {
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(
      value,
    )
  ) {
    throw new Error(
      `Data epidemiológica inválida: ${value}.`,
    );
  }

  const date =
    new Date(
      `${value}T00:00:00Z`,
    );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    throw new Error(
      `Data epidemiológica inválida: ${value}.`,
    );
  }

  return date;
}

function addDays(
  date: Date,
  days: number,
): Date {
  return new Date(
    date.getTime()
    + days
      * MILLISECONDS_PER_DAY,
  );
}

function formatDate(
  date: Date,
): string {
  return new Intl.DateTimeFormat(
    "pt-BR",
    {
      day:
        "2-digit",

      month:
        "2-digit",

      year:
        "numeric",

      timeZone:
        "UTC",
    },
  ).format(
    date,
  );
}

export type EpidemiologicalWeekDateRange = {
  week:
    number;

  start:
    Date;

  end:
    Date;

  startIso:
    string;

  endIso:
    string;
};

function formatIsoDate(
  date: Date,
): string {
  return date
    .toISOString()
    .slice(
      0,
      10,
    );
}

export function getEpidemiologicalWeekDateRange(
  week: number,
): EpidemiologicalWeekDateRange {
  if (
    !Number.isInteger(
      week,
    )
    || week < 1
    || week > 52
  ) {
    throw new Error(
      `Semana epidemiológica inválida: ${String(week)}.`,
    );
  }

  const weekOneStart =
    parseIsoDate(
      EPIDEMIOLOGICAL_WEEK_ONE_START_2025,
    );

  const start =
    addDays(
      weekOneStart,
      (
        week - 1
      )
        * DAYS_PER_WEEK,
    );

  const end =
    addDays(
      start,
      DAYS_PER_WEEK - 1,
    );

  return {
    week,
    start,
    end,
    startIso:
      formatIsoDate(
        start,
      ),

    endIso:
      formatIsoDate(
        end,
      ),
  };
}

export function formatMapWeekDateRange(
  week: number,
): string {
  const {
    start,
    end,
  } =
    getEpidemiologicalWeekDateRange(
      week,
    );

  const sameYear =
    start.getUTCFullYear()
    === end.getUTCFullYear();

  if (
    sameYear
  ) {
    const startShort =
      new Intl.DateTimeFormat(
        "pt-BR",
        {
          day:
            "2-digit",

          month:
            "2-digit",

          timeZone:
            "UTC",
        },
      ).format(
        start,
      );

    return (
      `${startShort} a ${formatDate(end)}`
    );
  }

  return (
    `${formatDate(start)} a ${formatDate(end)}`
  );
}

export function formatMapWeekOptionLabel(
  week: number,
): string {
  const weekLabel =
    String(
      week,
    ).padStart(
      2,
      "0",
    );

  return (
    `SE${weekLabel} · ${formatMapWeekDateRange(week)}`
  );
}