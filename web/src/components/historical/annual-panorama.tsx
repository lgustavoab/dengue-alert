import {
  formatDecimal,
  formatInteger,
  formatPercent,
} from "@/lib/serving/formatters";
import type {
  HistoricalAnnualItem,
} from "@/lib/serving/types";

type AnnualPanoramaProps = {
  data: HistoricalAnnualItem[];
};

export function AnnualPanorama({
  data,
}: AnnualPanoramaProps) {
  if (data.length === 0) {
    return null;
  }

  const maxCases = Math.max(
    ...data.map(
      (item) =>
        item.casos_provaveis,
    ),
  );

  const isSingleYear =
    data.length === 1;

  const firstYear =
    data[0]
      .ano_epidemiologico;

  const lastYear =
    data[
      data.length - 1
    ].ano_epidemiologico;

  return (
    <section className="historical-section">
      <div className="historical-section__heading">
        <div>
          <span className="eyebrow">
            Evolução anual
          </span>

          <h2>
            {isSingleYear
              ? `Panorama epidemiológico de ${firstYear}`
              : "Casos prováveis por ano epidemiológico"}
          </h2>
        </div>

        <p>
          {isSingleYear
            ? `Detalhamento nacional do ano epidemiológico de ${firstYear}.`
            : `Comparação nacional do volume anual de casos entre ${firstYear} e ${lastYear}.`}
        </p>
      </div>

      <div
        className="annual-chart"
        aria-label={
          isSingleYear
            ? `Casos prováveis de dengue em ${firstYear}`
            : `Casos prováveis de dengue entre ${firstYear} e ${lastYear}`
        }
      >
        {data.map(
          (item) => {
            const proportion =
              maxCases > 0
                ? item
                    .casos_provaveis
                  / maxCases
                : 0;

            return (
              <article
                key={
                  item
                    .ano_epidemiologico
                }
                className="annual-chart__row"
              >
                <div className="annual-chart__year">
                  {
                    item
                      .ano_epidemiologico
                  }
                </div>

                <div className="annual-chart__visual">
                  <div className="annual-chart__track">
                    <div
                      className="annual-chart__bar"
                      style={{
                        width: `${Math.max(
                          proportion
                            * 100,
                          1,
                        )}%`,
                      }}
                    />
                  </div>

                  <strong>
                    {formatInteger(
                      item
                        .casos_provaveis,
                    )}
                  </strong>
                </div>

                <div className="annual-chart__detail">
                  <span>
                    Incidência
                  </span>

                  <strong>
                    {formatDecimal(
                      item
                        .incidencia_anual_100mil,
                    )}
                  </strong>

                  <small>
                    por 100 mil
                  </small>
                </div>
              </article>
            );
          },
        )}
      </div>

      <div className="historical-table-wrapper">
        <table className="historical-table">
          <thead>
            <tr>
              <th>Ano</th>
              <th>Casos</th>
              <th>Incidência</th>
              <th>Pico</th>
              <th>SE do pico</th>
              <th>
                Territórios com casos
              </th>
            </tr>
          </thead>

          <tbody>
            {data.map(
              (item) => (
                <tr
                  key={
                    item
                      .ano_epidemiologico
                  }
                >
                  <td>
                    <strong>
                      {
                        item
                          .ano_epidemiologico
                      }
                    </strong>
                  </td>

                  <td>
                    {formatInteger(
                      item
                        .casos_provaveis,
                    )}
                  </td>

                  <td>
                    {formatDecimal(
                      item
                        .incidencia_anual_100mil,
                    )}
                  </td>

                  <td>
                    {formatInteger(
                      item
                        .pico_semanal_casos,
                    )}
                  </td>

                  <td>
                    SE{" "}
                    {
                      item
                        .semana_pico
                    }
                  </td>

                  <td>
                    {formatPercent(
                      item
                        .proporcao_unidades_com_casos,
                    )}
                  </td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}