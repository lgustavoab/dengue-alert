import type { Metadata } from "next";

import { PageIntro } from "@/components/ui/page-intro";
import { QualityOverview } from "@/components/quality/quality-overview";
import {
  getClimateCoverage,
  getPopulationCoverage,
  getQualityOverview,
  getSinanPipeline,
  getTerritorialCoverage,
} from "@/lib/serving/server";

export const metadata: Metadata = {
  title: "Dados & Qualidade",
};

export default async function DataQualityPage() {
  const [overview, sinan, territory, population, climate] = await Promise.all([
    getQualityOverview(),
    getSinanPipeline(),
    getTerritorialCoverage(),
    getPopulationCoverage(),
    getClimateCoverage(),
  ]);

  return (
    <div className="route-page">
      <PageIntro
        eyebrow="Transparência dos dados"
        title="Dados & Qualidade"
        description="Veja como os dados epidemiológicos foram filtrados, normalizados territorialmente e integrados às referências populacionais e climáticas antes das análises."
        note="Os indicadores desta área vêm de contratos auditados e descrevem preparação e cobertura dos dados. Não são alertas nem resultados preditivos."
      />

      <QualityOverview overview={overview} sinan={sinan} territory={territory} population={population} climate={climate} />
    </div>
  );
}
