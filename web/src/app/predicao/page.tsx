import type {
  Metadata,
} from "next";

import {
  Suspense,
} from "react";

import {
  PredictionSelection,
} from "@/components/prediction/prediction-selection";

import {
  PageIntro,
} from "@/components/ui/page-intro";

export const metadata: Metadata = {
  title:
    "Predição",
};

export default function PredictionPage() {
  return (
    <div
      className="route-page"
    >
      <PageIntro
        eyebrow="Avaliação preditiva retrospectiva"
        title="Consulte como o modelo antecipou o risco epidemiológico em 2025."
        description="Selecione um município e uma semana epidemiológica para analisar previsões de risco elevado entre uma e quatro semanas à frente."
        note="Os resultados pertencem ao teste retrospectivo de 2025. Eles não representam alertas atuais de 2026 nem previsão da quantidade futura de casos."
      />

      <Suspense
        fallback={
          <section
            className="placeholder-section"
            aria-busy="true"
          >
            <span>
              Predição
            </span>

            <h2>
              Preparando consulta
            </h2>

            <p>
              Carregando os controles da avaliação retrospectiva.
            </p>
          </section>
        }
      >
        <PredictionSelection />
      </Suspense>
    </div>
  );
}