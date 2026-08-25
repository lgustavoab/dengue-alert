import type { Metadata } from "next";

import { PageIntro } from "@/components/ui/page-intro";

export const metadata: Metadata = {
  title: "Dados & Qualidade",
};

export default function DataQualityPage() {
  return (
    <div className="route-page">
      <PageIntro
        eyebrow="Transparência dos dados"
        title="Veja como as fontes foram tratadas antes das análises."
        description="Esta área apresentará o funil do SINAN, cobertura territorial, integração populacional, disponibilidade climática e indicadores de qualidade."
        note="A aplicação apresenta indicadores consolidados de qualidade sem expor registros brutos individualmente."
      />

      <section className="placeholder-section">
        <span>Próxima etapa</span>
        <h2>Indicadores de qualidade</h2>
        <p>
          Os contratos de metadata e quality serão conectados a esta área após
          a conclusão da fundação visual.
        </p>
      </section>
    </div>
  );
}