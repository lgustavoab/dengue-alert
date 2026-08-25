import type { Metadata } from "next";

import { PageIntro } from "@/components/ui/page-intro";

export const metadata: Metadata = {
  title: "Predição",
};

export default function PredictionPage() {
  return (
    <div className="route-page">
      <PageIntro
        eyebrow="Avaliação preditiva"
        title="Analise a probabilidade futura de risco epidemiológico elevado."
        description="Esta área reunirá os resultados retrospectivos de 2025 para os horizontes H1, H2, H3 e H4, com consulta municipal e comparação com o estado observado."
        note="O score representa probabilidade de risco elevado futuro. Ele não representa previsão da quantidade de casos."
      />

      <section className="placeholder-section">
        <span>Próxima etapa</span>
        <h2>Resultados H1–H4</h2>
        <p>
          Os contratos preditivos serão conectados aqui sem recalcular modelos,
          targets ou thresholds no frontend.
        </p>
      </section>
    </div>
  );
}