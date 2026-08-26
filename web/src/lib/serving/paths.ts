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

    sinanPipeline:
      "quality/sinan_pipeline.json",

    territorialCoverage:
      "quality/territorial_coverage.json",

    populationCoverage:
      "quality/population_coverage.json",

    climateCoverage:
      "quality/climate_coverage.json",
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

    byHorizon:
      "prediction/evaluation/by_horizon.json",

    model:
      "prediction/metadata/model.json",

    municipalityIndex:
      "prediction/municipality/index.json",
  },
} as const;
