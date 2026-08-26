import type {
  Metadata,
} from "next";

import {
  Suspense,
} from "react";

import {
  MapFoundation,
} from "@/components/map/map-foundation";

import {
  PageIntro,
} from "@/components/ui/page-intro";

export const metadata: Metadata = {
  title:
    "Mapa preditivo",
};

export default function MapPage() {
  return (
    <div
      className="route-page"
    >
      <PageIntro
        eyebrow="Distribuição espacial retrospectiva"
        title="Explore onde o modelo indicou alerta de risco elevado em 2025."
        description="Selecione a semana epidemiológica e o horizonte preditivo para consultar simultaneamente os resultados dos municípios brasileiros avaliados."
        note="O mapa representa a avaliação retrospectiva de 2025. Os resultados não são alertas atuais de 2026 e não representam previsão da quantidade futura de casos."
      />

      <Suspense
        fallback={
          <section
            className="placeholder-section"
            aria-busy="true"
          >
            <span>
              Mapa preditivo
            </span>

            <h2>
              Preparando visualização
            </h2>

            <p>
              Carregando a cobertura temporal e os contratos da avaliação retrospectiva.
            </p>
          </section>
        }
      >
        <MapFoundation />
      </Suspense>
    </div>
  );
}