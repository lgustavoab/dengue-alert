import Link from "next/link";

import { AreaCard } from "@/components/ui/area-card";
import { formatPeriod } from "@/lib/serving/formatters";
import {
  getPredictionOverview,
  getTemporalCoverage,
} from "@/lib/serving/server";

export default async function Home() {
  const [temporalCoverage, prediction] = await Promise.all([
    getTemporalCoverage(),
    getPredictionOverview(),
  ]);

  const historicalPeriod = formatPeriod(
    temporalCoverage.data.periodo_historico,
  );

  return (
    <>
      <section className="hero">
        <div className="hero__inner">
          <div className="hero__content">
            <span className="eyebrow">Dengue Alert · estudo acadêmico</span>
            <h1>É possível antecipar períodos de risco elevado de dengue?</h1>
            <p>
              Analisamos dados de dengue de {historicalPeriod} e testamos modelos
              para identificar risco elevado de uma a quatro semanas à frente.
              Também investigamos se temperatura, chuva e umidade ajudavam nessa
              tarefa.
            </p>
            <p className="hero__notice">
              Este site apresenta resultados de uma pesquisa. As previsões
              disponíveis foram avaliadas retrospectivamente em {prediction.ano};
              não representam alertas operacionais atuais nem risco individual.
            </p>
            <div className="hero__actions">
              <Link className="hero__action hero__action--primary" href="/predicao">
                Conhecer os resultados
              </Link>
              <Link className="hero__action" href="/dados-qualidade">
                Entender os dados e o método
              </Link>
            </div>
          </div>

          <aside className="hero__panel" aria-label="Períodos da pesquisa">
            <span className="hero__panel-label">Recorte do estudo</span>
            <dl className="hero__periods">
              <div>
                <dt>Histórico analisado</dt>
                <dd>{historicalPeriod}</dd>
              </div>
              <div>
                <dt>Desenvolvimento dos modelos</dt>
                <dd>2018–2024</dd>
              </div>
              <div>
                <dt>Avaliação em outro período</dt>
                <dd>{prediction.ano}</dd>
              </div>
            </dl>
            <p>
              O ano de {prediction.ano} ficou separado das escolhas feitas
              durante o desenvolvimento do modelo.
            </p>
          </aside>
        </div>
      </section>

      <section className="content-section" aria-labelledby="study-method-title">
        <div className="section-heading">
          <span className="eyebrow">A pesquisa</span>
          <h2 id="study-method-title">Como fizemos o estudo</h2>
          <p>
            Reunimos fontes diferentes, comparamos formas de prever o risco e
            verificamos os resultados em um período posterior.
          </p>
        </div>
        <ol className="study-steps">
          <li>
            <h3>Organizamos os dados</h3>
            <p>
              Combinamos registros de casos prováveis de dengue com dados de
              população, território e clima para estudar os municípios ao longo
              das semanas.
            </p>
          </li>
          <li>
            <h3>Comparamos modelos</h3>
            <p>
              Usamos dados de 2018 a 2024 para comparar estratégias e decidir
              como emitir alertas para uma, duas, três ou quatro semanas depois.
            </p>
          </li>
          <li>
            <h3>Avaliamos em 2025</h3>
            <p>
              Com as escolhas já definidas, comparamos os alertas do modelo com
              o risco elevado observado em {prediction.ano}.
            </p>
          </li>
        </ol>
      </section>

      <section className="content-section content-section--findings" aria-labelledby="study-findings-title">
        <div className="section-heading">
          <span className="eyebrow">Principais achados</span>
          <h2 id="study-findings-title">O que encontramos</h2>
          <p>
            Os resultados ajudam a entender o potencial e as limitações da
            antecipação no cenário estudado.
          </p>
        </div>
        <div className="finding-grid">
          <article>
            <h3>Parte do risco pôde ser antecipada</h3>
            <p>
              O modelo identificou algumas situações futuras antes de o
              município estar em risco elevado. Também houve alertas que não se
              confirmaram e situações que não foram identificadas.
            </p>
          </article>
          <article>
            <h3>Uma ou duas semanas tiveram resultados mais favoráveis</h3>
            <p>
              A antecipação ficou mais difícil nos horizontes mais distantes.
              Cada prazo deve ser interpretado com sua própria avaliação.
            </p>
          </article>
          <article>
            <h3>Adicionar clima não trouxe melhora consistente</h3>
            <p>
              As variáveis meteorológicas testadas não melhoraram de forma
              consistente o modelo baseado no histórico epidemiológico. Isso
              não significa ausência de relação entre clima e dengue.
            </p>
          </article>
        </div>
      </section>

      <section className="content-section" aria-labelledby="study-explore-title">
        <div className="section-heading">
          <span className="eyebrow">Explore o trabalho</span>
          <h2 id="study-explore-title">Escolha por onde começar</h2>
          <p>
            Consulte os dados observados, veja a avaliação do modelo ou entenda
            as fontes e os limites da pesquisa.
          </p>
        </div>
        <div className="area-grid">
          <AreaCard
            eyebrow="01 · Dados observados"
            title="Histórico"
            description="Veja como os casos de dengue variaram ao longo do tempo e entre territórios."
            href="/historico"
          />
          <AreaCard
            eyebrow="02 · Avaliação retrospectiva"
            title="Resultados do modelo"
            description="Compare os alertas para municípios de 2025 com o que foi observado depois."
            href="/predicao"
          />
          <AreaCard
            eyebrow="03 · Distribuição territorial"
            title="Mapa"
            description="Explore no mapa as classificações do modelo para uma semana e um prazo escolhidos."
            href="/mapa"
          />
          <AreaCard
            eyebrow="04 · Transparência"
            title="Dados e método"
            description="Conheça as fontes, o tratamento dos dados e as limitações do estudo."
            href="/dados-qualidade"
          />
        </div>
      </section>

      <section className="method-section" aria-labelledby="study-limits-title">
        <div className="method-section__content">
          <span className="eyebrow">Para interpretar os resultados</span>
          <h2 id="study-limits-title">O que chamamos de risco elevado?</h2>
          <p>
            É uma condição definida nesta pesquisa: a incidência acumulada em
            quatro semanas supera uma referência histórica do próprio município
            para aquela época do ano. Não equivale a uma declaração oficial de
            epidemia. O modelo estima a chance de essa condição ocorrer em uma
            semana futura; não prevê a quantidade de casos.
          </p>
          <p>
            Os dados usados são históricos e consolidados. A avaliação de{" "}
            {prediction.ano} não substitui um sistema de alertas em tempo real,
            e o desempenho pode variar entre municípios.
          </p>
          <Link href="/dados-qualidade">Leia sobre os dados e os limites do estudo →</Link>
        </div>
      </section>

      <section className="content-section academic-section" aria-labelledby="study-authors-title">
        <div className="section-heading">
          <span className="eyebrow">Quem fez o estudo</span>
          <h2 id="study-authors-title">Um trabalho acadêmico da UNIVESP</h2>
          <p>
            Trabalho de Conclusão de Curso em Ciência de Dados da Universidade
            Virtual do Estado de São Paulo, 2026. Orientação: Aline Martins
            Nascimento Belchior.
          </p>
        </div>
        <p className="academic-section__label">Autores</p>
        <ul className="academic-section__authors">
          <li>Caio Henrique Granado</li>
          <li>Ducilene da Costa</li>
          <li>José Olavo Bernardo Freire</li>
          <li>Luis Gustavo de Almeida Barbeiro</li>
          <li>Mayara Aparecida de Queiroz</li>
          <li>Tiago Trombini</li>
          <li>William Cesar Frutuoso Figueredo</li>
        </ul>
      </section>
    </>
  );
}
