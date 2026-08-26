import {
  NextResponse,
} from "next/server";

import {
  getTerritoryFilterItems,
} from "@/lib/serving/server";

export async function GET() {
  try {
    const items =
      await getTerritoryFilterItems();

    return NextResponse.json(
      {
        schema_version: "1.0",
        count: items.length,
        items,
      },
      {
        headers: {
          "Cache-Control":
            "public, max-age=3600, stale-while-revalidate=86400",
        },
      },
    );
  } catch (error) {
    console.error(
      "Erro ao carregar índice territorial:",
      error,
    );

    return NextResponse.json(
      {
        error:
          "territory_index_unavailable",
      },
      {
        status: 500,
      },
    );
  }
}