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
    "Mapa dos resultados",
};

export default function MapPage() {
  return (
    <div
      className="route-page"
    >
      <PageIntro
        eyebrow="Distribuição espacial retrospectiva"
        title="Explore onde o modelo indicou alerta de risco elevado em 2025."
        description="Escolha uma semana de 2025 e consulte o que o modelo indicou para uma a quatro semanas depois. Busque um município ou selecione-o no mapa."
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
              Carregando os resultados e os municípios da avaliação de 2025.
            </p>
          </section>
        }
      >
        <MapFoundation />
      </Suspense>
    </div>
  );
}
