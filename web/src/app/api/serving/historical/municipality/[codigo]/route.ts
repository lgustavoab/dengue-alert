import {
  NextResponse,
} from "next/server";

import {
  getHistoricalMunicipalitySeries,
  MunicipalitySeriesNotFoundError,
} from "@/lib/serving/series-server";

type RouteContext = {
  params: Promise<{
    codigo: string;
  }>;
};

export async function GET(
  _request: Request,
  context: RouteContext,
) {
  const {
    codigo,
  } = await context.params;

  try {
    const series =
      await getHistoricalMunicipalitySeries(
        codigo,
      );

    return NextResponse.json(
      series,
      {
        headers: {
          "Cache-Control":
            "public, max-age=3600, stale-while-revalidate=86400",
        },
      },
    );
  } catch (error) {
    if (
      error
      instanceof MunicipalitySeriesNotFoundError
    ) {
      return NextResponse.json(
        {
          error:
            "municipality_series_not_found",
          codigo_ibge_7:
            codigo,
        },
        {
          status: 404,
        },
      );
    }

    if (
      error instanceof TypeError
    ) {
      return NextResponse.json(
        {
          error:
            "invalid_municipality_code",
        },
        {
          status: 400,
        },
      );
    }

    console.error(
      "Erro ao carregar série histórica municipal:",
      error,
    );

    return NextResponse.json(
      {
        error:
          "municipality_series_unavailable",
      },
      {
        status: 500,
      },
    );
  }
}