import {
  NextResponse,
} from "next/server";

import {
  getPredictionMapIndex,
} from "@/lib/serving/prediction-map-server";

export async function GET() {
  try {
    const index =
      await getPredictionMapIndex();

    return NextResponse.json(
      index,
      {
        headers: {
          "Cache-Control":
            "public, max-age=3600, stale-while-revalidate=86400",
        },
      },
    );
  } catch (error) {
    console.error(
      "Erro ao carregar índice do mapa preditivo:",
      error,
    );

    return NextResponse.json(
      {
        error:
          "prediction_map_index_unavailable",
      },
      {
        status: 500,
      },
    );
  }
}