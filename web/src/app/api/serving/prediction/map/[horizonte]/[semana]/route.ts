import {
  NextResponse,
} from "next/server";

import {
  getPredictionMapSlice,
  PredictionMapSelectionError,
  PredictionMapUnavailableError,
} from "@/lib/serving/prediction-map-server";

type RouteContext = {
  params: Promise<{
    horizonte: string;
    semana: string;
  }>;
};

function parseIntegerParameter(
  value: string,
): number {
  if (
    !/^\d+$/.test(
      value,
    )
  ) {
    return Number.NaN;
  }

  return Number(
    value,
  );
}

export async function GET(
  _request: Request,
  context: RouteContext,
) {
  const {
    horizonte,
    semana,
  } = await context.params;

  const parsedHorizon =
    parseIntegerParameter(
      horizonte,
    );

  const parsedWeek =
    parseIntegerParameter(
      semana,
    );

  try {
    const contract =
      await getPredictionMapSlice(
        parsedHorizon,
        parsedWeek,
      );

    return NextResponse.json(
      contract,
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
      instanceof PredictionMapSelectionError
    ) {
      return NextResponse.json(
        {
          error:
            "invalid_prediction_map_selection",
        },
        {
          status: 400,
        },
      );
    }

    if (
      error
      instanceof PredictionMapUnavailableError
    ) {
      return NextResponse.json(
        {
          error:
            "prediction_map_unavailable",
          horizonte:
            parsedHorizon,
          semana:
            parsedWeek,
        },
        {
          status: 404,
        },
      );
    }

    console.error(
      "Erro ao carregar recorte do mapa preditivo:",
      error,
    );

    return NextResponse.json(
      {
        error:
          "prediction_map_slice_unavailable",
      },
      {
        status: 500,
      },
    );
  }
}