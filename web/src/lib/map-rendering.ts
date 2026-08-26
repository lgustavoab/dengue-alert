import {
  geoMercator,
  geoPath,
} from "d3-geo";

import type {
  ParsedMunicipalityGeography,
} from "@/lib/map-geography";

export const MAP_VIEWBOX_WIDTH =
  960;

export const MAP_VIEWBOX_HEIGHT =
  720;

export const MAP_VIEWBOX_PADDING =
  24;

export type MunicipalitySvgPath = {
  codigoIbge7:
    string;

  d:
    string;
};

type MunicipalityFeatureCollection =
  ParsedMunicipalityGeography[
    "featureCollection"
  ];

function validateDimensions(
  width: number,
  height: number,
  padding: number,
): void {
  if (
    !Number.isFinite(
      width,
    )
    || !Number.isFinite(
      height,
    )
    || !Number.isFinite(
      padding,
    )
    || width <= 0
    || height <= 0
    || padding < 0
    || padding * 2 >= width
    || padding * 2 >= height
  ) {
    throw new Error(
      "Dimensões inválidas para renderização cartográfica.",
    );
  }
}

function normalizeFeatureId(
  value: string | number | undefined,
): string {
  if (
    value === undefined
  ) {
    throw new Error(
      "Feature municipal sem código IBGE.",
    );
  }

  const normalized =
    String(
      value,
    )
      .trim()
      .padStart(
        7,
        "0",
      );

  if (
    !/^\d{7}$/.test(
      normalized,
    )
  ) {
    throw new Error(
      `Código IBGE inválido durante renderização: ${String(value)}`,
    );
  }

  return normalized;
}

export function buildMunicipalitySvgPaths(
  featureCollection: MunicipalityFeatureCollection,
  width = MAP_VIEWBOX_WIDTH,
  height = MAP_VIEWBOX_HEIGHT,
  padding = MAP_VIEWBOX_PADDING,
): MunicipalitySvgPath[] {
  validateDimensions(
    width,
    height,
    padding,
  );

  if (
    featureCollection.type
    !== "FeatureCollection"
    || featureCollection.features.length
    !== 5_571
  ) {
    throw new Error(
      "FeatureCollection municipal incompatível com a malha aprovada.",
    );
  }

  const projection =
    geoMercator();

  projection.fitExtent(
    [
      [
        padding,
        padding,
      ],
      [
        width - padding,
        height - padding,
      ],
    ],
    featureCollection,
  );

  const pathGenerator =
    geoPath(
      projection,
    );

  const paths =
    featureCollection.features.map(
      (municipality) => {
        const codigoIbge7 =
          normalizeFeatureId(
            municipality.id,
          );

        const d =
          pathGenerator(
            municipality,
          );

        if (
          typeof d !== "string"
          || d.length === 0
        ) {
          throw new Error(
            `Path SVG vazio para o município ${codigoIbge7}.`,
          );
        }

        if (
          /NaN|Infinity/.test(
            d,
          )
        ) {
          throw new Error(
            `Path SVG inválido para o município ${codigoIbge7}.`,
          );
        }

        return {
          codigoIbge7,
          d,
        };
      },
    );

  const uniqueIds =
    new Set(
      paths.map(
        (item) =>
          item.codigoIbge7,
      ),
    );

  if (
    paths.length
    !== 5_571
    || uniqueIds.size
    !== 5_571
  ) {
    throw new Error(
      "Renderização não preservou os 5.571 municípios únicos.",
    );
  }

  return paths;
}