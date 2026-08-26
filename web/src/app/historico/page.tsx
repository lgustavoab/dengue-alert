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
  PageIntro,
} from "@/components/ui/page-intro";
import {
  formatPeriod,
} from "@/lib/serving/formatters";
import {
  getHistoricalAnnual,
  getQualityOverview,
} from "@/lib/serving/server";

export const metadata: Metadata = {
  title: "Histórico",
};

export default async function HistoricalPage() {
  const [
    annual,
    quality,
  ] = await Promise.all([
    getHistoricalAnnual(),
    getQualityOverview(),
  ]);

  if (
    annual.data.length === 0
  ) {
    throw new Error(
      "Panorama histórico anual sem dados.",
    );
  }

  return (
    <div className="route-page">
      <PageIntro
        eyebrow="Histórico epidemiológico"
        title="Entenda como a dengue se comportou ao longo do tempo."
        description={`Panorama nacional de ${formatPeriod(
          annual.period,
        )}, com casos prováveis, incidência, picos epidemiológicos e cobertura territorial.`}
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
          municipalityWeeks={
            quality.data
              .municipio_semanas
          }
        />
      </Suspense>
    </div>
  );
}