"use client";

import {
  useSearchParams,
} from "next/navigation";

import {
  HistoricalClimateAnalysis,
} from "@/components/historical/historical-climate-analysis";

import type {
  HistoricalClimateLagItem,
  HistoricalClimateRegionalLagItem,
} from "@/lib/serving/types";

type HistoricalClimateSectionProps = {
  nationalData:
    HistoricalClimateLagItem[];

  regionalData:
    HistoricalClimateRegionalLagItem[];
};

export function HistoricalClimateSection({
  nationalData,
  regionalData,
}: HistoricalClimateSectionProps) {
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
    <HistoricalClimateAnalysis
      nationalData={
        nationalData
      }
      regionalData={
        regionalData
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