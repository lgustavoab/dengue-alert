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
  title: "Dados e método",
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
        eyebrow="Entenda o estudo"
        title="Dados e método"
        description="De onde vieram os dados? Como os preparamos e como avaliamos o modelo? Conheça o caminho da pesquisa, suas escolhas e seus limites."
        note="Este site apresenta um trabalho acadêmico com dados históricos e avaliação retrospectiva de 2025. Não fornece alertas atuais nem estima a chance individual de uma pessoa contrair dengue."
      />

      <QualityOverview overview={overview} sinan={sinan} territory={territory} population={population} climate={climate} />
    </div>
  );
}
