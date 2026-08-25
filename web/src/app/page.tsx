import { AreaCard } from "@/components/ui/area-card";

export default function Home() {
  return (
    <>
      <section className="hero">
        <div className="hero__inner">
          <div className="hero__content">
            <span className="eyebrow">Dengue Alert</span>

            <h1>
              Dados históricos e avaliação preditiva para compreender o risco
              de dengue no Brasil.
            </h1>

            <p>
              Uma aplicação para explorar a evolução epidemiológica municipal,
              entender a qualidade das fontes utilizadas e analisar resultados
              retrospectivos de previsão de risco elevado.
            </p>

            <div className="hero__badges" aria-label="Características do projeto">
              <span>2016–2025</span>
              <span>5.571 unidades territoriais</span>
              <span>Horizontes de 1 a 4 semanas</span>
            </div>
          </div>

          <aside className="hero__panel" aria-label="Resumo do projeto">
            <span className="hero__panel-label">Cobertura histórica</span>

            <strong>16.294.913</strong>

            <p>casos preservados após tratamento e normalização dos dados.</p>

            <div className="hero__panel-divider" />

            <dl className="hero__stats">
              <div>
                <dt>Município-semanas</dt>
                <dd>2.907.593</dd>
              </div>

              <div>
                <dt>Predições retrospectivas</dt>
                <dd>1.124.938</dd>
              </div>
            </dl>
          </aside>
        </div>
      </section>

      <section className="content-section">
        <div className="section-heading">
          <span className="eyebrow">Áreas da aplicação</span>

          <h2>Três perspectivas complementares</h2>

          <p>
            O sistema separa explicitamente dados observados, transparência das
            fontes e resultados de modelagem.
          </p>
        </div>

        <div className="area-grid">
          <AreaCard
            eyebrow="01"
            title="Histórico"
            description="Explore casos, incidência, sazonalidade, distribuição espacial e séries municipais."
            href="/historico"
            metric="2016–2025"
            metricLabel="período epidemiológico"
          />

          <AreaCard
            eyebrow="02"
            title="Dados & Qualidade"
            description="Acompanhe o tratamento das fontes, cobertura territorial, população e dados climáticos."
            href="/dados-qualidade"
            metric="11.164"
            metricLabel="contratos JSON validados"
          />

          <AreaCard
            eyebrow="03"
            title="Predição"
            description="Analise a avaliação retrospectiva de risco elevado para horizontes de uma a quatro semanas."
            href="/predicao"
            metric="H1–H4"
            metricLabel="horizontes avaliados"
          />
        </div>
      </section>

      <section className="method-section">
        <div className="method-section__content">
          <span className="eyebrow">Interpretação responsável</span>

          <h2>O modelo estima risco, não quantidade futura de casos.</h2>

          <p>
            A área preditiva apresenta probabilidades de ocorrência futura de
            estado epidemiológico de risco elevado. Os resultados disponíveis
            correspondem à avaliação retrospectiva de 2025 e não representam
            alertas operacionais atuais.
          </p>
        </div>
      </section>
    </>
  );
}