import type {
  Metadata,
} from "next";

import {
  Suspense,
} from "react";

import {
  HistoricalClimateSection,
} from "@/components/historical/historical-climate-section";

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
  getHistoricalClimateNationalLags,
  getHistoricalClimateRegionalLags,
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

import reading from "@/components/historical/historical-reading.module.css";

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
    climateNational,
    climateRegional,
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
      getHistoricalClimateNationalLags(),
      getHistoricalClimateRegionalLags(),
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
    riskEpisodeDuration
      .distribution
      .length
    === 0
  ) {
    throw new Error(
      "Distribuição da duração dos episódios de risco sem dados.",
    );
  }

  if (
    climateNational.data.length
    === 0
  ) {
    throw new Error(
      "Contrato nacional de clima e dengue sem dados.",
    );
  }

  if (
    climateRegional.data.length
    === 0
  ) {
    throw new Error(
      "Contrato regional de clima e dengue sem dados.",
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
        )}. Explore como os casos variaram, compare lugares e conheça as análises de períodos de risco e de clima realizadas no estudo.`}
        note="São dados históricos organizados para a pesquisa, não previsões nem alertas atuais."
      />

      <nav className={reading.navigation} aria-label="Temas do histórico">
        <a href="#historical-cases">Casos e lugares</a>
        <a href="#historical-risk">Períodos de risco</a>
        <a href="#historical-climate">Clima e dengue</a>
      </nav>

      <p className={reading.scope}>
        Escolha um território para explorar os dados disponíveis. O filtro de ano muda a evolução de casos do Brasil ou do município; sazonalidade, comparações territoriais, risco e clima resumem seus períodos completos. Cada seção explica seu alcance.
      </p>

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
        <div id="historical-cases" className={reading.anchor}>
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
        </div>

        <div id="historical-risk" className={reading.anchor}>
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
        </div>

        <div id="historical-climate" className={reading.anchor}>
        <HistoricalClimateSection
          nationalData={
            climateNational.data
          }
          regionalData={
            climateRegional.data
          }
        />
        </div>
      </Suspense>
    </div>
  );
}
