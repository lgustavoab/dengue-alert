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
  PredictionPerformance,
} from "@/components/prediction/prediction-performance";

import {
  PageIntro,
} from "@/components/ui/page-intro";

import {
  getPredictionByHorizon,
} from "@/lib/serving/server";

import styles from "./page.module.css";

export const metadata: Metadata = {
  title:
    "Resultados do modelo",
};

export default async function PredictionPage() {
  const predictionByHorizon =
    await getPredictionByHorizon();

  return (
    <div
      className="route-page"
    >
      <PageIntro
        eyebrow="Avaliação retrospectiva de 2025"
        title="Resultados do modelo"
        description="Compare os alertas com o que foi observado em um município ou conheça os resultados da avaliação nacional do modelo."
        note="Esta página apresenta resultados de pesquisa com dados de 2025. Não fornece alertas atuais nem prevê a quantidade futura de casos."
      />

      <nav className={styles.sectionNavigation} aria-label="Seções dos resultados do modelo">
        <a href="#municipal-consultation">Consultar um município</a>
        <a href="#prediction-performance-title">Avaliar o modelo</a>
      </nav>

      <div id="municipal-consultation" className={styles.consultation}>
        <Suspense
          fallback={
            <section
              className="placeholder-section"
              aria-busy="true"
            >
              <span>
                Consulta municipal
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

      <PredictionPerformance
        evaluation={
          predictionByHorizon
        }
      />
    </div>
  );
}
