import type { Metadata } from "next";

import { PageIntro } from "@/components/ui/page-intro";

export const metadata: Metadata = {
  title: "Histórico",
};

export default function HistoricalPage() {
  return (
    <div className="route-page">
      <PageIntro
        eyebrow="Histórico epidemiológico"
        title="Entenda como a dengue se comportou ao longo do tempo."
        description="Esta área reunirá panorama nacional, sazonalidade, distribuição espacial, dinâmica de risco e séries históricas municipais."
        note="Os dados apresentados nesta área representam observações históricas tratadas e validadas. Não são previsões."
      />

      <section className="placeholder-section">
        <span>Próxima etapa</span>
        <h2>Visualizações históricas</h2>
        <p>
          Os componentes analíticos desta área serão conectados aos contratos
          históricos da camada de serving na próxima fase.
        </p>
      </section>
    </div>
  );
}