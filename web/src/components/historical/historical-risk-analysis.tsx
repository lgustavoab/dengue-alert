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
import reading from "./historical-reading.module.css";
import { HistoricalDetails } from "./historical-details";
import { HistoricalChartAxes, HistoricalChartFrame, historicalChartViewBox } from "./historical-chart-axes";

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
            Quantos municípios estiveram em risco ao mesmo tempo?
          </h3>
        </div>

        <p>
          Percentual dos municípios com histórico suficiente que estiveram em risco elevado em cada Semana Epidemiológica. A linha não mostra a quantidade de casos nem uma previsão.
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

      <HistoricalChartFrame label="Risco semanal: ano epidemiológico e percentual de municípios em risco">
        <svg
          className={
            styles.svg
          }
          viewBox={historicalChartViewBox(WEEKLY_WIDTH, WEEKLY_HEIGHT)}
          role="img"
          aria-label={
            region
              ? `Proporção semanal de municípios em risco na região ${region}`
              : "Proporção semanal de municípios em risco no Brasil"
          }
        >
          <HistoricalChartAxes width={WEEKLY_WIDTH} height={WEEKLY_HEIGHT} padding={WEEKLY_PADDING} maximum={1} format="percent" xLabel="Tempo — ano epidemiológico" yLabel="Municípios em risco (% dos elegíveis)" />
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
      </HistoricalChartFrame>

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
            Quanto duraram os períodos de risco?
          </h3>
        </div>

        <p>
          Brasil, 2018–2025. Cada episódio reúne semanas consecutivas em risco elevado no mesmo município. As barras mostram quantos episódios tiveram cada duração.
        </p>
      </div>

      <p className={styles.note}>
        A duração mediana foi de {formatInteger(summary.mediana)} semanas: esse é o valor central das durações ordenadas, não a média. A maior duração não representa um episódio típico.
      </p>

      <HistoricalDetails title="Ver os indicadores completos de duração">
      <p>Percentil 90 (P90) é a duração abaixo da qual, ou igual à qual, ficam aproximadamente 90% dos episódios.</p>
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
      </HistoricalDetails>

      <HistoricalChartFrame label="Duração do risco: semanas consecutivas e quantidade de episódios">
        <svg
          className={
            styles.svg
          }
          viewBox={historicalChartViewBox(EPISODE_WIDTH, EPISODE_HEIGHT)}
          role="img"
          aria-label="Distribuição nacional da duração dos episódios históricos de risco"
        >
          <HistoricalChartAxes width={EPISODE_WIDTH} height={EPISODE_HEIGHT} padding={EPISODE_PADDING} maximum={maxEpisodes} format="integer" xLabel="Duração do episódio (semanas consecutivas)" yLabel="Quantidade de episódios" />
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
      </HistoricalChartFrame>

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
            Como os períodos de risco se repetiram? · {scopeTitle}
          </h2>
        </div>

        <p>
          Análise de 2018–2025. Ela começa depois da série de casos porque a definição de risco exige dados de anos anteriores. O filtro de ano não muda esta seção.
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
        Aqui, risco elevado significa que a incidência acumulada em quatro semanas superou uma referência histórica do próprio município para aquela época do ano. Isso não equivale a uma declaração oficial de epidemia nem ao risco individual de uma pessoa.
      </div>

      <HistoricalDetails title="Como o estudo definiu risco elevado?">
        <p>A referência é o percentil 90 (P90) sazonal, calculado com dados de anos anteriores e uma janela de ±4 semanas em torno da semana analisada. A incidência acumulada em quatro semanas precisa ser estritamente maior que essa referência.</p>
        <p>Uma observação elegível é uma combinação município–semana com histórico suficiente para aplicar essa definição. Não representa uma pessoa. Essa regra observada não é o limiar usado para emitir um alerta do modelo.</p>
      </HistoricalDetails>

      {selectedMunicipality ? (
        municipalitySummary ? (
          <>
            <div
              className={reading.keyMetrics}
            >
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
                description={`${formatInteger(municipalitySummary.semanas_risco)} de ${formatInteger(municipalitySummary.observacoes_elegiveis)} semanas com histórico suficiente, em todo o período.`}
              />

              <MetricCard
                label="Anos com risco"
                value={
                  formatInteger(
                    municipalitySummary
                      .anos_com_risco,
                  )
                }
                description={`Anos com pelo menos uma semana em risco, entre ${formatInteger(municipalitySummary.anos_elegiveis)} anos com histórico suficiente.`}
              />
            </div>

            <HistoricalDetails title="Ver cobertura e recorrência municipal">
              <p>Semanas com histórico suficiente: {formatInteger(municipalitySummary.observacoes_elegiveis)}, em {formatInteger(municipalitySummary.anos_elegiveis)} anos.</p>
              <p>Risco em mais de um ano: {municipalitySummary.recorrencia_multianual ? "Sim" : "Não"}. Esse indicador resume se houve repetição em anos diferentes, não uma previsão de repetição futura.</p>
            </HistoricalDetails>

            <p
              className={
                styles.note
              }
            >
              O resumo municipal de risco utiliza todo o período histórico elegível disponível, não somente o ano selecionado. Não é a situação atual do município. Não há curva semanal de risco nem distribuição de duração individual nesta visualização.
            </p>
          </>
        ) : (
          <div
            className={
              styles.unavailable
            }
          >
            Não há resumo histórico de risco disponível para este município. Pode faltar histórico suficiente para aplicar a definição do estudo. Ausência de avaliação não significa ausência de risco.
          </div>
        )
      ) : (
        <>
          <HistoricalDetails title="Ver o resumo dos municípios deste recorte">
          <div
            className="metric-grid"
          >
            <MetricCard
              label="Municípios com histórico suficiente"
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
              label="Risco em mais de um ano"
              value={
                formatInteger(
                  municipalitiesWithRecurrence,
                )
              }
              description="Municípios com risco registrado em mais de um ano."
            />

            <MetricCard
              label="Percentual médio de semanas em risco"
              value={
                formatPercent(
                  averageRiskProportion,
                )
              }
              description="Média municipal da proporção de observações elegíveis em risco."
            />
          </div>
          </HistoricalDetails>

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

          <HistoricalDetails title="Comparar a frequência de risco entre municípios">
            <MunicipalityRanking data={scopedMunicipalities} />
          </HistoricalDetails>

          {selectedRegion || selectedUf ? (
            <p className={styles.note}>A distribuição da duração dos episódios está disponível apenas para o Brasil completo; não é uma distribuição específica deste território.</p>
          ) : null}

          {selectedUf ? (
            <p
              className={
                styles.note
              }
            >
              A evolução semanal de risco está disponível para Brasil e regiões, não para estados. Aqui são apresentados somente os resumos municipais do estado selecionado.
            </p>
          ) : null}
        </>
      )}
    </section>
  );
}
