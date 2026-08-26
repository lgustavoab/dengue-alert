import {
  feature,
} from "topojson-client";

const EXPECTED_MUNICIPALITIES =
  5_571;

type TopologyInput =
  Parameters<
    typeof feature
  >[0];

type GeographyObject =
  Parameters<
    typeof feature
  >[1];

export type ParsedMunicipalityGeography = {
  objectName:
  string;

  featureCollection:
  Extract<
    ReturnType<typeof feature>,
    {
      type: "FeatureCollection";
    }
  >;

  municipalityIds:
  string[];
};

function normalizeMunicipalityId(
  value: string | number | undefined,
): string {
  if (
    value === undefined
  ) {
    throw new Error(
      "Geometria municipal sem ID.",
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
      `Código IBGE municipal inválido: ${String(value)}`,
    );
  }

  return normalized;
}

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object"
    && value !== null
    && !Array.isArray(
      value,
    )
  );
}

function validateTopologyStructure(
  payload: unknown,
): TopologyInput {
  if (
    !isRecord(
      payload,
    )
    || payload.type
    !== "Topology"
  ) {
    throw new Error(
      "Asset geográfico não possui type=Topology.",
    );
  }

  if (
    !isRecord(
      payload.objects,
    )
  ) {
    throw new Error(
      "TopoJSON não possui objects válido.",
    );
  }

  if (
    !Array.isArray(
      payload.arcs,
    )
    || payload.arcs.length
    === 0
  ) {
    throw new Error(
      "TopoJSON não possui arcs válidos.",
    );
  }

  return (
    payload as unknown as TopologyInput
  );
}

function getMunicipalityObject(
  topology: TopologyInput,
): {
  objectName:
  string;

  object:
  GeographyObject;
} {
  const objectNames =
    Object.keys(
      topology.objects,
    );

  if (
    objectNames.length
    !== 1
  ) {
    throw new Error(
      "O TopoJSON municipal deve possuir exatamente um objeto geográfico.",
    );
  }

  const objectName =
    objectNames[0];

  const object =
    topology.objects[
    objectName
    ];

  if (
    object === undefined
  ) {
    throw new Error(
      "Objeto geográfico municipal ausente.",
    );
  }

  if (
    object.type
    !== "GeometryCollection"
  ) {
    throw new Error(
      "O objeto municipal deve ser uma GeometryCollection.",
    );
  }

  if (
    object.geometries.length
    !== EXPECTED_MUNICIPALITIES
  ) {
    throw new Error(
      "Quantidade de geometrias municipais divergente. "
      + `Esperado: ${EXPECTED_MUNICIPALITIES}; `
      + `obtido: ${object.geometries.length}.`,
    );
  }

  return {
    objectName,
    object,
  };
}

export function parseMunicipalityTopology(
  payload: unknown,
): ParsedMunicipalityGeography {
  const topology =
    validateTopologyStructure(
      payload,
    );

  const {
    objectName,
    object,
  } =
    getMunicipalityObject(
      topology,
    );

  const converted =
    feature(
      topology,
      object,
    );

  if (
    converted.type
    !== "FeatureCollection"
  ) {
    throw new Error(
      "Conversão TopoJSON não produziu uma FeatureCollection.",
    );
  }

  if (
    converted.features.length
    !== EXPECTED_MUNICIPALITIES
  ) {
    throw new Error(
      "Quantidade de features convertidas divergente.",
    );
  }

  const municipalityIds =
    converted.features.map(
      (municipality) =>
        normalizeMunicipalityId(
          municipality.id,
        ),
    );

  const uniqueIds =
    new Set(
      municipalityIds,
    );

  if (
    uniqueIds.size
    !== EXPECTED_MUNICIPALITIES
  ) {
    throw new Error(
      "A malha convertida possui códigos IBGE municipais duplicados.",
    );
  }

  for (
    const municipality
    of converted.features
  ) {
    if (
      municipality.geometry
      === null
    ) {
      throw new Error(
        "A malha convertida possui geometria municipal nula.",
      );
    }

    if (
      municipality.geometry.type
      !== "Polygon"
      && municipality.geometry.type
      !== "MultiPolygon"
    ) {
      throw new Error(
        "A malha convertida possui tipo geométrico inesperado: "
        + municipality.geometry.type,
      );
    }

    municipality.id =
      normalizeMunicipalityId(
        municipality.id,
      );
  }

  return {
    objectName,

    featureCollection:
      converted,

    municipalityIds,
  };
}