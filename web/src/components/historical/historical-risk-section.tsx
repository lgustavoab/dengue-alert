"use client";

import {
  useSearchParams,
} from "next/navigation";

import {
  HistoricalRiskAnalysis,
} from "@/components/historical/historical-risk-analysis";

import type {
  HistoricalRiskEpisodeDurationItem,
  HistoricalRiskEpisodeDurationSummary,
  HistoricalRiskMunicipalityItem,
  HistoricalRiskWeeklyItem,
} from "@/lib/serving/types";

type HistoricalRiskSectionProps = {
  weeklyData:
    HistoricalRiskWeeklyItem[];

  municipalities:
    HistoricalRiskMunicipalityItem[];

  episodeSummary:
    HistoricalRiskEpisodeDurationSummary;

  episodeDistribution:
    HistoricalRiskEpisodeDurationItem[];
};

export function HistoricalRiskSection({
  weeklyData,
  municipalities,
  episodeSummary,
  episodeDistribution,
}: HistoricalRiskSectionProps) {
  const searchParams =
    useSearchParams();

  const selectedRegion =
    searchParams.get(
      "regiao",
    ) ?? "";

  const selectedUf =
    searchParams.get(
      "uf",
    ) ?? "";

  const selectedMunicipality =
    searchParams.get(
      "municipio",
    );

  return (
    <HistoricalRiskAnalysis
      weeklyData={
        weeklyData
      }
      municipalities={
        municipalities
      }
      episodeSummary={
        episodeSummary
      }
      episodeDistribution={
        episodeDistribution
      }
      selectedRegion={
        selectedRegion
      }
      selectedUf={
        selectedUf
      }
      selectedMunicipality={
        selectedMunicipality
      }
    />
  );
}