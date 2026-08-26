"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  usePathname,
  useRouter,
  useSearchParams,
} from "next/navigation";

import {
  TerritorialFilters,
} from "@/components/filters/territorial-filters";
import {
  AnnualPanorama,
} from "@/components/historical/annual-panorama";
import {
  MunicipalityPanorama,
} from "@/components/historical/municipality-panorama";
import {
  MetricCard,
} from "@/components/ui/metric-card";
import {
  formatDecimal,
  formatInteger,
} from "@/lib/serving/formatters";
import type {
  HistoricalAnnualItem,
  HistoricalMunicipalitySeriesContract,
  TerritoryFilterItem,
} from "@/lib/serving/types";

type HistoricalOverviewProps = {
  annualData: HistoricalAnnualItem[];
  municipalityWeeks: number;
};

type TerritoryResponse = {
  schema_version: "1.0";
  count: number;
  items: TerritoryFilterItem[];
};

type LoadingStatus =
  | "idle"
  | "loading"
  | "ready"
  | "error";

type TerritoriesState = {
  status: LoadingStatus;
  items: TerritoryFilterItem[];
  error: string | null;
};

type MunicipalitySeriesState = {
  code: string | null;
  status: LoadingStatus;
  data:
  | HistoricalMunicipalitySeriesContract
  | null;
  error: string | null;
};

export function HistoricalOverview({
  annualData,
  municipalityWeeks,
}: HistoricalOverviewProps) {
  const router =
    useRouter();

  const pathname =
    usePathname();

  const searchParams =
    useSearchParams();

  const [
    territoriesState,
    setTerritoriesState,
  ] = useState<TerritoriesState>({
    status: "loading",
    items: [],
    error: null,
  });

  const [
    municipalitySeriesState,
    setMunicipalitySeriesState,
  ] = useState<MunicipalitySeriesState>({
    code: null,
    status: "idle",
    data: null,
    error: null,
  });

  const territories =
    territoriesState.items;

  const selectedRegion =
    searchParams.get(
      "regiao",
    ) ?? "";

  const selectedUf =
    searchParams.get(
      "uf",
    ) ?? "";

  const selectedMunicipality =
    searchParams.get(
      "municipio",
    );

  const yearParameter =
    searchParams.get(
      "ano",
    );

  const rawYear =
    yearParameter === null
      ? null
      : Number(
        yearParameter,
      );

  const replaceParameters =
    useCallback(
      (
        updates: Record<
          string,
          string | null
        >,
      ) => {
        const parameters =
          new URLSearchParams(
            searchParams.toString(),
          );

        for (
          const [
            key,
            value,
          ] of Object.entries(
            updates,
          )
        ) {
          if (
            value === null
            || value === ""
          ) {
            parameters.delete(
              key,
            );
          } else {
            parameters.set(
              key,
              value,
            );
          }
        }

        const query =
          parameters.toString();

        router.replace(
          query
            ? `${pathname}?${query}`
            : pathname,
          {
            scroll: false,
          },
        );
      },
      [
        pathname,
        router,
        searchParams,
      ],
    );

  useEffect(
    () => {
      const controller =
        new AbortController();

      async function loadTerritories() {
        try {
          const response =
            await fetch(
              "/api/serving/territories",
              {
                signal:
                  controller.signal,
              },
            );

          if (!response.ok) {
            throw new Error(
              `HTTP ${response.status}`,
            );
          }

          const payload: TerritoryResponse =
            await response.json();

          if (
            payload.schema_version
            !== "1.0"
            || !Array.isArray(
              payload.items,
            )
            || payload.items.length
            !== payload.count
          ) {
            throw new Error(
              "Contrato territorial inválido.",
            );
          }

          setTerritoriesState({
            status: "ready",
            items: payload.items,
            error: null,
          });
        } catch (error) {
          if (
            error
            instanceof DOMException
            && error.name
            === "AbortError"
          ) {
            return;
          }

          console.error(
            error,
          );

          setTerritoriesState({
            status: "error",
            items: [],
            error:
              "Não foi possível carregar o índice territorial.",
          });
        }
      }

      void loadTerritories();

      return () =>
        controller.abort();
    },
    [],
  );

  const selectedTerritory =
    useMemo(
      () =>
        territories.find(
          (item) =>
            item.codigoIbge7
            === selectedMunicipality,
        ) ?? null,
      [
        territories,
        selectedMunicipality,
      ],
    );

  useEffect(
    () => {
      if (
        territoriesState.status
        !== "ready"
        || !selectedMunicipality
      ) {
        return;
      }

      if (!selectedTerritory) {
        replaceParameters({
          municipio: null,
        });

        return;
      }

      const expectedRegion =
        selectedTerritory.regiao;

      const expectedUf =
        String(
          selectedTerritory
            .codigoUfIbge,
        );

      if (
        selectedRegion
        !== expectedRegion
        || selectedUf
        !== expectedUf
      ) {
        replaceParameters({
          regiao:
            expectedRegion,
          uf:
            expectedUf,
        });
      }
    },
    [
      replaceParameters,
      selectedMunicipality,
      selectedRegion,
      selectedTerritory,
      selectedUf,
      territoriesState.status,
    ],
  );

  useEffect(
    () => {
      if (
        !selectedMunicipality
      ) {
        return;
      }

      const controller =
        new AbortController();

      async function loadSeries() {
        try {
          const response =
            await fetch(
              `/api/serving/historical/municipality/${selectedMunicipality}`,
              {
                signal:
                  controller.signal,
              },
            );

          if (!response.ok) {
            throw new Error(
              `HTTP ${response.status}`,
            );
          }

          const payload: HistoricalMunicipalitySeriesContract =
            await response.json();

          if (
            payload.schema_version
            !== "1.0"
            || payload.codigo_ibge_7
            !== selectedMunicipality
          ) {
            throw new Error(
              "Contrato municipal inválido.",
            );
          }

          setMunicipalitySeriesState({
            code:
              selectedMunicipality,
            status: "ready",
            data: payload,
            error: null,
          });
        } catch (error) {
          if (
            error
            instanceof DOMException
            && error.name
            === "AbortError"
          ) {
            return;
          }

          console.error(
            error,
          );

          setMunicipalitySeriesState({
            code:
              selectedMunicipality,
            status: "error",
            data: null,
            error:
              "Não foi possível carregar a série histórica deste município.",
          });
        }
      }

      void loadSeries();

      return () =>
        controller.abort();
    },
    [
      selectedMunicipality,
    ],
  );

  const municipalitySeries =
    selectedMunicipality
      && municipalitySeriesState.code
      === selectedMunicipality
      ? municipalitySeriesState.data
      : null;

  const seriesStatus:
    LoadingStatus =
    selectedMunicipality === null
      ? "idle"
      : municipalitySeriesState.code
        === selectedMunicipality
        ? municipalitySeriesState.status
        : "loading";

  const seriesError =
    selectedMunicipality
      && municipalitySeriesState.code
      === selectedMunicipality
      ? municipalitySeriesState.error
      : null;

  const nationalYears =
    useMemo(
      () =>
        annualData.map(
          (item) =>
            item
              .ano_epidemiologico,
        ),
      [
        annualData,
      ],
    );

  const municipalityYears =
    useMemo(
      () => {
        if (
          !municipalitySeries
        ) {
          return [];
        }

        return [
          ...new Set(
            municipalitySeries
              .data
              .ano_epidemiologico,
          ),
        ].sort(
          (a, b) =>
            a - b,
        );
      },
      [
        municipalitySeries,
      ],
    );

  const availableYears =
    selectedMunicipality
      ? municipalityYears
      : nationalYears;

  const selectedYear =
    rawYear !== null
      && Number.isInteger(
        rawYear,
      )
      && availableYears.includes(
        rawYear,
      )
      ? rawYear
      : null;

  useEffect(
    () => {
      if (
        rawYear === null
      ) {
        return;
      }

      if (
        selectedMunicipality
        && seriesStatus
        !== "ready"
      ) {
        return;
      }

      if (
        availableYears.length
        > 0
        && !availableYears.includes(
          rawYear,
        )
      ) {
        replaceParameters({
          ano: null,
        });
      }
    },
    [
      availableYears,
      rawYear,
      replaceParameters,
      selectedMunicipality,
      seriesStatus,
    ],
  );

  function handleRegionChange(
    value: string,
  ) {
    replaceParameters({
      regiao:
        value || null,
      uf: null,
      municipio: null,
    });
  }

  function handleUfChange(
    value: string,
  ) {
    replaceParameters({
      uf:
        value || null,
      municipio: null,
    });
  }

  function handleMunicipalityChange(
    code: string | null,
  ) {
    if (code === null) {
      replaceParameters({
        municipio: null,
      });

      return;
    }

    const territory =
      territories.find(
        (item) =>
          item.codigoIbge7
          === code,
      );

    if (!territory) {
      return;
    }

    replaceParameters({
      regiao:
        territory.regiao,
      uf:
        String(
          territory
            .codigoUfIbge,
        ),
      municipio:
        territory.codigoIbge7,
    });
  }

  function handleYearChange(
    year: number | null,
  ) {
    replaceParameters({
      ano:
        year === null
          ? null
          : String(
            year,
          ),
    });
  }

  function handleReset() {
    replaceParameters({
      regiao: null,
      uf: null,
      municipio: null,
      ano: null,
    });
  }

  const filteredAnnualData =
    selectedYear === null
      ? annualData
      : annualData.filter(
        (item) =>
          item
            .ano_epidemiologico
          === selectedYear,
      );

  const nationalPeak =
    filteredAnnualData.reduce(
      (
        current,
        item,
      ) =>
        item.casos_provaveis
          > current.casos_provaveis
          ? item
          : current,
    );

  const nationalLatest =
    filteredAnnualData[
    filteredAnnualData.length - 1
    ];

  const nationalTotalCases =
    filteredAnnualData.reduce(
      (
        total,
        item,
      ) =>
        total
        + item.casos_provaveis,
      0,
    );

  return (
    <>
      <TerritorialFilters
        items={
          territories
        }
        territoriesLoading={
          territoriesState.status
          === "loading"
        }
        territoriesError={
          territoriesState.error
        }
        selectedRegion={
          selectedRegion
        }
        selectedUf={
          selectedUf
        }
        selectedMunicipality={
          selectedMunicipality
        }
        selectedYear={
          selectedYear
        }
        availableYears={
          availableYears
        }
        onRegionChange={
          handleRegionChange
        }
        onUfChange={
          handleUfChange
        }
        onMunicipalityChange={
          handleMunicipalityChange
        }
        onYearChange={
          handleYearChange
        }
        onReset={
          handleReset
        }
      />

      {selectedMunicipality ? (
        <>
          {seriesStatus
            === "loading" ? (
            <section
              className="placeholder-section"
              aria-busy="true"
            >
              <span>
                Série municipal
              </span>

              <h2>
                Carregando município
              </h2>

              <p>
                A série epidemiológica solicitada está sendo carregada sob
                demanda.
              </p>
            </section>
          ) : null}

          {seriesStatus
            === "error"
            && seriesError ? (
            <section
              className="placeholder-section"
            >
              <span>
                Série municipal
              </span>

              <h2>
                Dados indisponíveis
              </h2>

              <p>
                {seriesError}
              </p>
            </section>
          ) : null}

          {seriesStatus
            === "ready"
            && municipalitySeries
            && selectedTerritory ? (
            <MunicipalityPanorama
              territory={
                selectedTerritory
              }
              series={
                municipalitySeries
              }
              selectedYear={
                selectedYear
              }
            />
          ) : null}
        </>
      ) : (
        <>
          <section
            className="metric-grid"
            aria-label="Indicadores do panorama histórico nacional"
          >
            <MetricCard
              label="Casos no recorte"
              value={formatInteger(
                nationalTotalCases,
              )}
              description={
                selectedYear
                  === null
                  ? "Soma nacional dos anos epidemiológicos apresentados."
                  : `Total nacional observado em ${selectedYear}.`
              }
            />

            {selectedYear
              !== null ? (
              <MetricCard
                label="Incidência anual"
                value={formatDecimal(
                  nationalPeak
                    .incidencia_anual_100mil,
                )}
                description="Casos por 100 mil habitantes no ano selecionado."
              />
            ) : (
              <MetricCard
                label="Maior volume anual"
                value={formatInteger(
                  nationalPeak
                    .casos_provaveis,
                )}
                description={`${nationalPeak.ano_epidemiologico} · ${formatDecimal(
                  nationalPeak
                    .incidencia_anual_100mil,
                )} casos por 100 mil habitantes.`}
              />
            )}

            {selectedYear
              !== null ? (
              <MetricCard
                label="Pico semanal"
                value={`SE ${nationalPeak.semana_pico}`}
                description={`${formatInteger(
                  nationalPeak
                    .pico_semanal_casos,
                )} casos na semana de maior volume.`}
              />
            ) : (
              <MetricCard
                label={`Ano mais recente · ${nationalLatest.ano_epidemiologico}`}
                value={formatInteger(
                  nationalLatest
                    .casos_provaveis,
                )}
                description={`Pico na SE ${nationalLatest.semana_pico}.`}
              />
            )}

            <MetricCard
              label="Município-semanas no painel"
              value={formatInteger(
                municipalityWeeks,
              )}
              description="Cobertura total do painel epidemiológico nacional."
            />
          </section>

          <AnnualPanorama
            data={
              filteredAnnualData
            }
          />
        </>
      )}
    </>
  );
}