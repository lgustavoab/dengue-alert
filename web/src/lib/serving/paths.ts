export const servingPaths = {
  manifest: "manifest.json",

  metadata: {
    temporalCoverage: "metadata/temporal_coverage.json",
  },

  quality: {
    overview: "quality/overview.json",
  },

  historical: {
    panoramaAnnual: "historical/panorama/annual.json",
  },

  prediction: {
    overview: "prediction/evaluation/overview.json",
    model: "prediction/metadata/model.json",
  },
} as const;