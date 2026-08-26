import type {
  Metadata,
} from "next";

import {
  Suspense,
} from "react";

import {
  HistoricalOverview,
} from "@/components/historical/historical-overview";

import {
  HistoricalRiskSection,
} from "@/components/historical/historical-risk-section";

import {
  PageIntro,
} from "@/components/ui/page-intro";

import {
  formatPeriod,
} from "@/lib/serving/formatters";

import {
  getHistoricalAnnual,
  getHistoricalRiskEpisodeDuration,
  getHistoricalRiskMunicipalities,
  getHistoricalRiskWeekly,
  getHistoricalSeasonalityNational,
  getHistoricalSeasonalityRegional,
  getHistoricalSpatialRegions,
  getHistoricalSpatialStates,
  getHistoricalWeekly,
  getQualityOverview,
} from "@/lib/serving/server";

export const metadata: Metadata = {
  title:
    "Histórico",
};

export default async function HistoricalPage() {
  const [
    annual,
    weekly,
    seasonality,
    regionalSeasonality,
    regions,
    states,
    riskWeekly,
    riskMunicipalities,
    riskEpisodeDuration,
    quality,
  ] =
    await Promise.all([
      getHistoricalAnnual(),
      getHistoricalWeekly(),
      getHistoricalSeasonalityNational(),
      getHistoricalSeasonalityRegional(),
      getHistoricalSpatialRegions(),
      getHistoricalSpatialStates(),
      getHistoricalRiskWeekly(),
      getHistoricalRiskMunicipalities(),
      getHistoricalRiskEpisodeDuration(),
      getQualityOverview(),
    ]);

  if (
    annual.data.length
    === 0
  ) {
    throw new Error(
      "Panorama histórico anual sem dados.",
    );
  }

  if (
    weekly.data.length
    === 0
  ) {
    throw new Error(
      "Panorama histórico semanal sem dados.",
    );
  }

  if (
    seasonality.data.length
    === 0
  ) {
    throw new Error(
      "Contrato de sazonalidade nacional sem dados.",
    );
  }

  if (
    regionalSeasonality.data.length
    === 0
  ) {
    throw new Error(
      "Contrato de sazonalidade regional sem dados.",
    );
  }

  if (
    regions.data.length
    === 0
  ) {
    throw new Error(
      "Contrato espacial regional sem dados.",
    );
  }

  if (
    states.data.length
    === 0
  ) {
    throw new Error(
      "Contrato espacial das UFs sem dados.",
    );
  }

  if (
    riskWeekly.data.length
    === 0
  ) {
    throw new Error(
      "Contrato semanal de risco histórico sem dados.",
    );
  }

  if (
    riskMunicipalities.data.length
    === 0
  ) {
    throw new Error(
      "Contrato municipal de risco histórico sem dados.",
    );
  }

  if (
    riskEpisodeDuration.distribution.length
    === 0
  ) {
    throw new Error(
      "Distribuição da duração dos episódios de risco sem dados.",
    );
  }

  return (
    <div
      className="route-page"
    >
      <PageIntro
        eyebrow="Histórico epidemiológico"
        title="Entenda como a dengue se comportou ao longo do tempo."
        description={`Panorama de ${formatPeriod(
          annual.period,
        )}, com evolução epidemiológica, sazonalidade e comparações territoriais produzidas a partir dos contratos históricos validados.`}
        note="Os dados desta área representam observações históricas tratadas e validadas. Não são previsões."
      />

      <Suspense
        fallback={
          <section
            className="placeholder-section"
            aria-busy="true"
          >
            <span>
              Histórico
            </span>

            <h2>
              Preparando visualização
            </h2>

            <p>
              Carregando os controles e indicadores históricos.
            </p>
          </section>
        }
      >
        <HistoricalOverview
          annualData={
            annual.data
          }
          weeklyData={
            weekly.data
          }
          seasonalityData={
            seasonality.data
          }
          regionalSeasonalityData={
            regionalSeasonality.data
          }
          regionsData={
            regions.data
          }
          statesData={
            states.data
          }
          municipalityWeeks={
            quality.data
              .municipio_semanas
          }
        />

        <HistoricalRiskSection
          weeklyData={
            riskWeekly.data
          }
          municipalities={
            riskMunicipalities.data
          }
          episodeSummary={
            riskEpisodeDuration.summary
          }
          episodeDistribution={
            riskEpisodeDuration.distribution
          }
        />
      </Suspense>
    </div>
  );
}