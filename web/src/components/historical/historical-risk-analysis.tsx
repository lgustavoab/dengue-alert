import {
  countMunicipalitiesWithRecurrence,
  countMunicipalitiesWithRisk,
  filterRiskMunicipalities,
  filterRiskWeeklyByScope,
  findMunicipalityRiskSummary,
  getAverageRiskProportion,
  getRiskWeeklyPeak,
  sortRiskMunicipalitiesByProportion,
} from "@/lib/historical-risk-utils";

import {
  pointsToPath,
  scaleSeries,
} from "@/lib/historical-chart-utils";

import {
  formatInteger,
  formatPercent,
} from "@/lib/serving/formatters";

import type {
  HistoricalRiskEpisodeDurationItem,
  HistoricalRiskEpisodeDurationSummary,
  HistoricalRiskMunicipalityItem,
  HistoricalRiskWeeklyItem,
} from "@/lib/serving/types";

import {
  MetricCard,
} from "@/components/ui/metric-card";

import styles from "./historical-risk-analysis.module.css";

type HistoricalRiskAnalysisProps = {
  weeklyData:
  HistoricalRiskWeeklyItem[];

  municipalities:
  HistoricalRiskMunicipalityItem[];

  episodeSummary:
  HistoricalRiskEpisodeDurationSummary;

  episodeDistribution:
  HistoricalRiskEpisodeDurationItem[];

  selectedRegion:
  string;

  selectedUf:
  string;

  selectedMunicipality:
  string | null;
};

const WEEKLY_WIDTH =
  960;

const WEEKLY_HEIGHT =
  300;

const WEEKLY_PADDING = {
  top: 24,
  right: 26,
  bottom: 48,
  left: 54,
};

const EPISODE_WIDTH =
  960;

const EPISODE_HEIGHT =
  280;

const EPISODE_PADDING = {
  top: 24,
  right: 26,
  bottom: 48,
  left: 54,
};

function WeeklyRiskChart({
  data,
  region,
}: {
  data:
  HistoricalRiskWeeklyItem[];

  region:
  string;
}) {
  if (
    data.length === 0
  ) {
    return null;
  }

  const values =
    data.map(
      (item) =>
        item
          .proporcao_unidades_em_risco,
    );

  const points =
    scaleSeries(
      values,
      WEEKLY_WIDTH,
      WEEKLY_HEIGHT,
      WEEKLY_PADDING,
      1,
    );

  const linePath =
    pointsToPath(
      points,
    );

  const peak =
    getRiskWeeklyPeak(
      data,
    );

  const peakIndex =
    peak
      ? data.indexOf(
        peak,
      )
      : -1;

  const peakPoint =
    peakIndex >= 0
      ? points[
      peakIndex
      ]
      : null;

  const plotHeight =
    WEEKLY_HEIGHT
    - WEEKLY_PADDING.top
    - WEEKLY_PADDING.bottom;

  const yearLabels =
    data
      .map(
        (
          item,
          index,
        ) => ({
          item,
          index,
        }),
      )
      .filter(
        (
          entry,
          index,
          entries,
        ) =>
          index === 0
          || entry.item
            .ano_epidemiologico
          !== entries[
            index - 1
          ].item
            .ano_epidemiologico,
      );

  return (
    <div
      className={
        styles.subsection
      }
    >
      <div
        className={
          styles.subsectionHeader
        }
      >
        <div>
          <h3>
            Evolução semanal da simultaneidade de risco
          </h3>
        </div>

        <p>
          Proporção das unidades elegíveis classificadas em risco elevado em cada Semana Epidemiológica.
        </p>
      </div>

      {peak ? (
        <div
          className={
            styles.summaryGrid
          }
        >
          <div
            className={
              styles.summaryItem
            }
          >
            <span>
              Semanas avaliadas
            </span>

            <strong>
              {formatInteger(
                data.length,
              )}
            </strong>
          </div>

          <div
            className={
              styles.summaryItem
            }
          >
            <span>
              Maior simultaneidade
            </span>

            <strong>
              {formatPercent(
                peak
                  .proporcao_unidades_em_risco,
              )}
            </strong>
          </div>

          <div
            className={
              styles.summaryItem
            }
          >
            <span>
              Unidades no pico
            </span>

            <strong>
              {formatInteger(
                peak
                  .unidades_em_risco,
              )}
            </strong>
          </div>

          <div
            className={
              styles.summaryItem
            }
          >
            <span>
              Semana do pico
            </span>

            <strong>
              {`${peak.ano_epidemiologico} · SE ${peak.semana_epidemiologica}`}
            </strong>
          </div>
        </div>
      ) : null}

      <div
        className={
          styles.svgWrapper
        }
      >
        <svg
          className={
            styles.svg
          }
          viewBox={`0 0 ${WEEKLY_WIDTH} ${WEEKLY_HEIGHT}`}
          role="img"
          aria-label={
            region
              ? `Proporção semanal de municípios em risco na região ${region}`
              : "Proporção semanal de municípios em risco no Brasil"
          }
        >
          {[
            0,
            0.25,
            0.5,
            0.75,
            1,
          ].map(
            (fraction) => {
              const y =
                WEEKLY_PADDING.top
                + fraction
                * plotHeight;

              return (
                <line
                  key={
                    fraction
                  }
                  className={
                    styles.gridLine
                  }
                  x1={
                    WEEKLY_PADDING.left
                  }
                  x2={
                    WEEKLY_WIDTH
                    - WEEKLY_PADDING.right
                  }
                  y1={
                    y
                  }
                  y2={
                    y
                  }
                />
              );
            },
          )}

          <path
            className={
              styles.line
            }
            d={
              linePath
            }
          />

          {points.map(
            (
              point,
              index,
            ) => {
              const item =
                data[
                index
                ];

              return (
                <circle
                  key={`${item.ano_epidemiologico}-${item.semana_epidemiologica}`}
                  className={
                    styles.point
                  }
                  cx={
                    point.x
                  }
                  cy={
                    point.y
                  }
                  r="2"
                >
                  <title>
                    {`${item.ano_epidemiologico} · Semana Epidemiológica ${item.semana_epidemiologica}: ${formatInteger(
                      item
                        .unidades_em_risco,
                    )} de ${formatInteger(
                      item
                        .unidades_elegiveis,
                    )} unidades em risco (${formatPercent(
                      item
                        .proporcao_unidades_em_risco,
                    )})`}
                  </title>
                </circle>
              );
            },
          )}

          {peakPoint ? (
            <circle
              className={
                styles.peakPoint
              }
              cx={
                peakPoint.x
              }
              cy={
                peakPoint.y
              }
              r="6"
            >
              <title>
                {peak
                  ? `Pico: ${peak.ano_epidemiologico}, Semana Epidemiológica ${peak.semana_epidemiologica}`
                  : ""}
              </title>
            </circle>
          ) : null}

          {yearLabels.map(
            (entry) => {
              const point =
                points[
                entry.index
                ];

              if (
                !point
              ) {
                return null;
              }

              return (
                <text
                  key={
                    entry.item
                      .ano_epidemiologico
                  }
                  className={
                    styles.axisText
                  }
                  x={
                    point.x
                  }
                  y={
                    WEEKLY_HEIGHT
                    - 14
                  }
                  textAnchor="middle"
                >
                  {
                    entry.item
                      .ano_epidemiologico
                  }
                </text>
              );
            },
          )}
        </svg>
      </div>

      <p
        className={
          styles.note
        }
      >
        SE = Semana Epidemiológica. Esta série descreve estados históricos observados segundo a definição de risco do projeto; não representa probabilidades previstas pelo modelo.
      </p>
    </div>
  );
}

function EpisodeDurationChart({
  summary,
  distribution,
}: {
  summary:
  HistoricalRiskEpisodeDurationSummary;

  distribution:
  HistoricalRiskEpisodeDurationItem[];
}) {
  if (
    distribution.length === 0
  ) {
    return null;
  }

  const maxEpisodes =
    Math.max(
      ...distribution.map(
        (item) =>
          item.episodios,
      ),
      1,
    );

  const plotWidth =
    EPISODE_WIDTH
    - EPISODE_PADDING.left
    - EPISODE_PADDING.right;

  const plotHeight =
    EPISODE_HEIGHT
    - EPISODE_PADDING.top
    - EPISODE_PADDING.bottom;

  const slotWidth =
    plotWidth
    / distribution.length;

  const labelDurations = [
    ...new Set([
      summary.minimo,
      summary.mediana,
      summary.p90,
      summary.maximo,
    ]),
  ];

  return (
    <div
      className={
        styles.subsection
      }
    >
      <div
        className={
          styles.subsectionHeader
        }
      >
        <div>
          <h3>
            Duração dos episódios históricos de risco
          </h3>
        </div>

        <p>
          Distribuição nacional da quantidade de episódios segundo sua duração contínua em semanas.
        </p>
      </div>

      <div
        className={
          styles.summaryGrid
        }
      >
        <div
          className={
            styles.summaryItem
          }
        >
          <span>
            Episódios
          </span>

          <strong>
            {formatInteger(
              summary
                .quantidade_episodios,
            )}
          </strong>
        </div>

        <div
          className={
            styles.summaryItem
          }
        >
          <span>
            Duração mediana
          </span>

          <strong>
            {`${formatInteger(
              summary.mediana,
            )} semanas`}
          </strong>
        </div>

        <div
          className={
            styles.summaryItem
          }
        >
          <span>
            Percentil 90
          </span>

          <strong>
            {`${formatInteger(
              summary.p90,
            )} semanas`}
          </strong>
        </div>

        <div
          className={
            styles.summaryItem
          }
        >
          <span>
            Maior duração
          </span>

          <strong>
            {`${formatInteger(
              summary.maximo,
            )} semanas`}
          </strong>
        </div>
      </div>

      <div
        className={
          styles.svgWrapper
        }
      >
        <svg
          className={
            styles.svg
          }
          viewBox={`0 0 ${EPISODE_WIDTH} ${EPISODE_HEIGHT}`}
          role="img"
          aria-label="Distribuição nacional da duração dos episódios históricos de risco"
        >
          {[
            0,
            0.25,
            0.5,
            0.75,
            1,
          ].map(
            (fraction) => {
              const y =
                EPISODE_PADDING.top
                + fraction
                * plotHeight;

              return (
                <line
                  key={
                    fraction
                  }
                  className={
                    styles.gridLine
                  }
                  x1={
                    EPISODE_PADDING.left
                  }
                  x2={
                    EPISODE_WIDTH
                    - EPISODE_PADDING.right
                  }
                  y1={
                    y
                  }
                  y2={
                    y
                  }
                />
              );
            },
          )}

          {distribution.map(
            (
              item,
              index,
            ) => {
              const height =
                (
                  item.episodios
                  / maxEpisodes
                )
                * plotHeight;

              const x =
                EPISODE_PADDING.left
                + index
                * slotWidth;

              const y =
                EPISODE_PADDING.top
                + plotHeight
                - height;

              return (
                <rect
                  key={
                    item
                      .duracao_semanas
                  }
                  className={
                    styles.bar
                  }
                  x={
                    x
                  }
                  y={
                    y
                  }
                  width={
                    Math.max(
                      slotWidth
                      * 0.82,
                      1,
                    )
                  }
                  height={
                    height
                  }
                >
                  <title>
                    {`${item.duracao_semanas} semana${item.duracao_semanas === 1 ? "" : "s"}: ${formatInteger(
                      item.episodios,
                    )} episódios`}
                  </title>
                </rect>
              );
            },
          )}

          {labelDurations.map(
            (duration) => {
              const index =
                distribution.findIndex(
                  (item) =>
                    item
                      .duracao_semanas
                    === duration,
                );

              if (
                index < 0
              ) {
                return null;
              }

              const x =
                EPISODE_PADDING.left
                + index
                * slotWidth
                + slotWidth
                / 2;

              return (
                <text
                  key={
                    duration
                  }
                  className={
                    styles.axisText
                  }
                  x={
                    x
                  }
                  y={
                    EPISODE_HEIGHT
                    - 14
                  }
                  textAnchor="middle"
                >
                  {duration}
                </text>
              );
            },
          )}
        </svg>
      </div>

      <p
        className={
          styles.note
        }
      >
        O eixo horizontal representa a duração do episódio em semanas. A mediana e os percentis descrevem a distribuição histórica nacional e não um prazo previsto para episódios futuros.
      </p>
    </div>
  );
}

function MunicipalityRanking({
  data,
}: {
  data:
  HistoricalRiskMunicipalityItem[];
}) {
  const ranked =
    sortRiskMunicipalitiesByProportion(
      data,
    ).slice(
      0,
      10,
    );

  if (
    ranked.length === 0
  ) {
    return null;
  }

  const maxProportion =
    Math.max(
      ...ranked.map(
        (item) =>
          item
            .proporcao_semanas_risco,
      ),
      Number.EPSILON,
    );

  return (
    <div
      className={
        styles.subsection
      }
    >
      <div
        className={
          styles.subsectionHeader
        }
      >
        <div>
          <h3>
            Maior frequência histórica de risco
          </h3>
        </div>

        <p>
          Dez municípios com maior proporção de observações elegíveis classificadas em risco no recorte territorial.
        </p>
      </div>

      <div
        className={
          styles.ranking
        }
      >
        {ranked.map(
          (item) => {
            const width =
              (
                item
                  .proporcao_semanas_risco
                / maxProportion
              )
              * 100;

            return (
              <div
                key={
                  item
                    .codigo_ibge_7
                }
                className={
                  styles.rankingRow
                }
              >
                <span
                  className={
                    styles.rankingName
                  }
                  title={`${item.nome_municipio} — ${item.nome_uf}`}
                >
                  {item.nome_municipio}
                </span>

                <div
                  className={
                    styles.rankingTrack
                  }
                >
                  <div
                    className={
                      styles.rankingBar
                    }
                    style={{
                      width: `${Math.max(
                        width,
                        1,
                      )}%`,
                    }}
                  />
                </div>

                <strong
                  className={
                    styles.rankingValue
                  }
                >
                  {formatPercent(
                    item
                      .proporcao_semanas_risco,
                  )}
                </strong>
              </div>
            );
          },
        )}
      </div>

      <p
        className={
          styles.note
        }
      >
        Este ranking descreve frequência histórica dentro do período elegível. Ele não representa um ranking de risco atual nem uma previsão.
      </p>
    </div>
  );
}

export function HistoricalRiskAnalysis({
  weeklyData,
  municipalities,
  episodeSummary,
  episodeDistribution,
  selectedRegion,
  selectedUf,
  selectedMunicipality,
}: HistoricalRiskAnalysisProps) {
  const municipalitySummary =
    selectedMunicipality
      ? findMunicipalityRiskSummary(
        municipalities,
        selectedMunicipality,
      )
      : null;

  const scopedMunicipalities =
    selectedMunicipality
      ? []
      : filterRiskMunicipalities(
        municipalities,
        {
          region:
            selectedUf
              ? undefined
              : selectedRegion
              || undefined,

          ufCode:
            selectedUf
            || undefined,
        },
      );

  const weeklyScope =
    !selectedMunicipality
      && !selectedUf
      ? filterRiskWeeklyByScope(
        weeklyData,
        selectedRegion,
      )
      : [];

  const municipalityCount =
    scopedMunicipalities.length;

  const municipalitiesWithRisk =
    countMunicipalitiesWithRisk(
      scopedMunicipalities,
    );

  const municipalitiesWithRecurrence =
    countMunicipalitiesWithRecurrence(
      scopedMunicipalities,
    );

  const averageRiskProportion =
    getAverageRiskProportion(
      scopedMunicipalities,
    );

  const selectedStateName =
    selectedUf
      ? municipalities.find(
        (item) =>
          item.codigo_uf_ibge
          === selectedUf,
      )?.nome_uf
      ?? null
      : null;

  const scopeTitle =
    selectedMunicipality
      ? municipalitySummary
        ? `${municipalitySummary.nome_municipio} — ${municipalitySummary.nome_uf}`
        : "Município selecionado"
      : selectedUf
        ? selectedStateName
        ?? "Unidade federativa selecionada"
        : selectedRegion
          ? selectedRegion
          : "Brasil";

  return (
    <section
      className={
        styles.section
      }
    >
      <div
        className={
          styles.heading
        }
      >
        <div
          className={
            styles.headingContent
          }
        >
          <span
            className={
              styles.eyebrow
            }
          >
            Dinâmica histórica de risco
          </span>

          <h2>
            {scopeTitle}
          </h2>
        </div>

        <p>
          Frequência, simultaneidade e persistência dos estados históricos de risco epidemiológico definidos pelo projeto.
        </p>
      </div>

      <div
        className={
          styles.definition
        }
      >
        <strong>
          Risco histórico não é previsão.
        </strong>{" "}
        Nesta seção, uma observação é classificada em risco elevado quando a incidência acumulada em quatro semanas supera o limiar sazonal P90 histórico definido para o município. Os resultados abaixo descrevem estados já observados e são separados da área de Predição do sistema.
      </div>

      {selectedMunicipality ? (
        municipalitySummary ? (
          <>
            <div
              className="metric-grid"
            >
              <MetricCard
                label="Observações elegíveis"
                value={
                  formatInteger(
                    municipalitySummary
                      .observacoes_elegiveis,
                  )
                }
                description={`${formatInteger(
                  municipalitySummary
                    .anos_elegiveis,
                )} anos com histórico elegível.`}
              />

              <MetricCard
                label="Semanas em risco"
                value={
                  formatInteger(
                    municipalitySummary
                      .semanas_risco,
                  )
                }
                description="Semanas historicamente classificadas em risco elevado."
              />

              <MetricCard
                label="Proporção das semanas"
                value={
                  formatPercent(
                    municipalitySummary
                      .proporcao_semanas_risco,
                  )
                }
                description="Parcela das observações elegíveis classificadas em risco."
              />

              <MetricCard
                label="Anos com risco"
                value={
                  formatInteger(
                    municipalitySummary
                      .anos_com_risco,
                  )
                }
                description="Número de anos elegíveis em que houve pelo menos uma semana em risco."
              />

              <MetricCard
                label="Recorrência multianual"
                value={
                  municipalitySummary
                    .recorrencia_multianual
                    ? "Sim"
                    : "Não"
                }
                description="Indica se o município apresentou risco em mais de um ano."
              />
            </div>

            <p
              className={
                styles.note
              }
            >
              O resumo municipal de risco utiliza todo o período histórico elegível do contrato. Por isso, ele não deve ser interpretado como a situação atual do município.
            </p>
          </>
        ) : (
          <div
            className={
              styles.unavailable
            }
          >
            Não existe resumo histórico de risco elegível para este município no contrato serving. Isso pode ocorrer quando a unidade não possui histórico suficiente para a definição do alvo.
          </div>
        )
      ) : (
        <>
          <div
            className="metric-grid"
          >
            <MetricCard
              label="Municípios elegíveis"
              value={
                formatInteger(
                  municipalityCount,
                )
              }
              description="Municípios disponíveis no resumo histórico deste recorte."
            />

            <MetricCard
              label="Com algum risco histórico"
              value={
                formatInteger(
                  municipalitiesWithRisk,
                )
              }
              description="Municípios que apresentaram pelo menos uma semana em risco."
            />

            <MetricCard
              label="Recorrência multianual"
              value={
                formatInteger(
                  municipalitiesWithRecurrence,
                )
              }
              description="Municípios com risco registrado em mais de um ano."
            />

            <MetricCard
              label="Média de semanas em risco"
              value={
                formatPercent(
                  averageRiskProportion,
                )
              }
              description="Média municipal da proporção de observações elegíveis em risco."
            />
          </div>

          {weeklyScope.length
            > 0 ? (
            <WeeklyRiskChart
              data={
                weeklyScope
              }
              region={
                selectedRegion
              }
            />
          ) : null}

          <MunicipalityRanking
            data={
              scopedMunicipalities
            }
          />

          {!selectedRegion
            && !selectedUf ? (
            <EpisodeDurationChart
              summary={
                episodeSummary
              }
              distribution={
                episodeDistribution
              }
            />
          ) : null}

          {selectedUf ? (
            <p
              className={
                styles.note
              }
            >
              O contrato semanal de risco possui séries agregadas para Brasil e regiões, mas não para UFs. Por isso, no recorte estadual são exibidos os resumos municipais disponíveis sem reconstruir artificialmente uma série semanal estadual.
            </p>
          ) : null}
        </>
      )}
    </section>
  );
}