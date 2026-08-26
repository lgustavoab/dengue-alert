export const servingPaths = {
  manifest: "manifest.json",

  metadata: {
    temporalCoverage: "metadata/temporal_coverage.json",
    territories: "metadata/territories.json",
  },

  quality: {
    overview: "quality/overview.json",
  },

  historical: {
    panoramaAnnual: "historical/panorama/annual.json",
    municipalityIndex: "historical/municipality/index.json",
  },

  prediction: {
    overview: "prediction/evaluation/overview.json",
    model: "prediction/metadata/model.json",
    municipalityIndex: "prediction/municipality/index.json",
  },
} as const;