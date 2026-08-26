export const servingPaths = {
  manifest: "manifest.json",

  metadata: {
    temporalCoverage:
      "metadata/temporal_coverage.json",
    territories:
      "metadata/territories.json",
  },

  quality: {
    overview:
      "quality/overview.json",
  },

  historical: {
    panoramaAnnual:
      "historical/panorama/annual.json",

    panoramaWeekly:
      "historical/panorama/weekly.json",

    municipalityIndex:
      "historical/municipality/index.json",

    seasonalityNational:
      "historical/seasonality/national.json",

    seasonalityRegional:
      "historical/seasonality/regional.json",

    spatialRegions:
      "historical/spatial/regions.json",

    spatialStates:
      "historical/spatial/states.json",

    spatialMunicipalities:
      "historical/spatial/municipalities.json",

    riskDynamicsWeekly:
      "historical/risk_dynamics/weekly.json",

    riskDynamicsMunicipalities:
      "historical/risk_dynamics/municipalities.json",

    riskEpisodeDuration:
      "historical/risk_dynamics/episode_duration.json",

    climateNationalLags:
      "historical/climate/national_lags.json",

    climateRegionalLags:
      "historical/climate/regional_lags.json",
  },

  prediction: {
    overview:
      "prediction/evaluation/overview.json",

    model:
      "prediction/metadata/model.json",

    municipalityIndex:
      "prediction/municipality/index.json",
  },
} as const;