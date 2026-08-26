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
  FilterBar,
} from "@/components/filters/filter-bar";

import {
  MunicipalityCombobox,
} from "@/components/filters/municipality-combobox";

import {
  SelectFilter,
} from "@/components/filters/select-filter";

import {
  filterPredictionTerritories,
  formatPredictionDate,
  formatPredictionWeekLabel,
  getAvailableHorizonsForWeek,
  getPredictionReferenceWeeks,
} from "@/lib/prediction-selection-utils";

import type {
  PredictionMunicipalitySeriesContract,
  TerritoryFilterItem,
} from "@/lib/serving/types";

import styles from "./prediction-selection.module.css";

type LoadingStatus =
  | "idle"
  | "loading"
  | "ready"
  | "error";

type TerritoryResponse = {
  schema_version:
    "1.0";

  count:
    number;

  items:
    TerritoryFilterItem[];
};

type TerritoriesState = {
  status:
    LoadingStatus;

  items:
    TerritoryFilterItem[];

  error:
    string | null;
};

type PredictionSeriesState = {
  code:
    string | null;

  status:
    LoadingStatus;

  data:
    PredictionMunicipalitySeriesContract
    | null;

  error:
    string | null;
};

export function PredictionSelection() {
  const router =
    useRouter();

  const pathname =
    usePathname();

  const searchParams =
    useSearchParams();

  const [
    territoriesState,
    setTerritoriesState,
  ] =
    useState<TerritoriesState>({
      status:
        "loading",

      items:
        [],

      error:
        null,
    });

  const [
    seriesState,
    setSeriesState,
  ] =
    useState<PredictionSeriesState>({
      code:
        null,

      status:
        "idle",

      data:
        null,

      error:
        null,
    });

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

  const weekParameter =
    searchParams.get(
      "semana",
    );

  const rawWeek =
    weekParameter === null
      ? null
      : Number(
          weekParameter,
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
          ]
          of Object.entries(
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
          }
          else {
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
            scroll:
              false,
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

          if (
            !response.ok
          ) {
            throw new Error(
              `HTTP ${response.status}`,
            );
          }

          const payload:
            TerritoryResponse =
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
            status:
              "ready",

            items:
              payload.items,

            error:
              null,
          });
        }
        catch (error) {
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
            status:
              "error",

            items:
              [],

            error:
              "Não foi possível carregar os municípios disponíveis para predição.",
          });
        }
      }

      void loadTerritories();

      return () =>
        controller.abort();
    },
    [],
  );

  const territories =
    useMemo(
      () =>
        filterPredictionTerritories(
          territoriesState.items,
        ),
      [
        territoriesState.items,
      ],
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
        selectedMunicipality,
        territories,
      ],
    );

  const regionOptions =
    useMemo(
      () => {
        const regions =
          [
            ...new Set(
              territories.map(
                (item) =>
                  item.regiao,
              ),
            ),
          ].sort(
            (a, b) =>
              a.localeCompare(
                b,
                "pt-BR",
              ),
          );

        return [
          {
            value:
              "",

            label:
              "Todas as regiões",
          },

          ...regions.map(
            (region) => ({
              value:
                region,

              label:
                region,
            }),
          ),
        ];
      },
      [
        territories,
      ],
    );

  const ufItems =
    useMemo(
      () => {
        const filtered =
          selectedRegion
            ? territories.filter(
                (item) =>
                  item.regiao
                  === selectedRegion,
              )
            : territories;

        const byCode =
          new Map<
            string,
            TerritoryFilterItem
          >();

        for (
          const item
          of filtered
        ) {
          if (
            !byCode.has(
              item.codigoUfIbge,
            )
          ) {
            byCode.set(
              item.codigoUfIbge,
              item,
            );
          }
        }

        return [
          ...byCode.values(),
        ].sort(
          (a, b) =>
            a.nomeUf.localeCompare(
              b.nomeUf,
              "pt-BR",
            ),
        );
      },
      [
        selectedRegion,
        territories,
      ],
    );

  const ufOptions =
    useMemo(
      () => [
        {
          value:
            "",

          label:
            "Todas as UFs",
        },

        ...ufItems.map(
          (item) => ({
            value:
              item.codigoUfIbge,

            label:
              item.nomeUf,
          }),
        ),
      ],
      [
        ufItems,
      ],
    );

  const municipalityItems =
    useMemo(
      () =>
        territories.filter(
          (item) => {
            if (
              selectedRegion
              && item.regiao
              !== selectedRegion
            ) {
              return false;
            }

            if (
              selectedUf
              && item.codigoUfIbge
              !== selectedUf
            ) {
              return false;
            }

            return true;
          },
        ),
      [
        selectedRegion,
        selectedUf,
        territories,
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

      if (
        !selectedTerritory
      ) {
        replaceParameters({
          municipio:
            null,

          semana:
            null,
        });

        return;
      }

      if (
        selectedRegion
        !== selectedTerritory.regiao
        || selectedUf
        !== selectedTerritory
          .codigoUfIbge
      ) {
        replaceParameters({
          regiao:
            selectedTerritory.regiao,

          uf:
            selectedTerritory
              .codigoUfIbge,
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
              `/api/serving/prediction/municipality/${selectedMunicipality}`,
              {
                signal:
                  controller.signal,
              },
            );

          if (
            !response.ok
          ) {
            throw new Error(
              `HTTP ${response.status}`,
            );
          }

          const payload:
            PredictionMunicipalitySeriesContract =
            await response.json();

          if (
            payload.schema_version
            !== "1.0"
            || payload.codigo_ibge_7
            !== selectedMunicipality
          ) {
            throw new Error(
              "Contrato preditivo municipal inválido.",
            );
          }

          setSeriesState({
            code:
              selectedMunicipality,

            status:
              "ready",

            data:
              payload,

            error:
              null,
          });
        }
        catch (error) {
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

          setSeriesState({
            code:
              selectedMunicipality,

            status:
              "error",

            data:
              null,

            error:
              "Não foi possível carregar a avaliação retrospectiva deste município.",
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
    && seriesState.code
    === selectedMunicipality
      ? seriesState.data
      : null;

  const seriesStatus:
    LoadingStatus =
    selectedMunicipality === null
      ? "idle"
      : seriesState.code
        === selectedMunicipality
        ? seriesState.status
        : "loading";

  const seriesError =
    selectedMunicipality
    && seriesState.code
    === selectedMunicipality
      ? seriesState.error
      : null;

  const referenceWeeks =
    useMemo(
      () =>
        municipalitySeries
          ? getPredictionReferenceWeeks(
              municipalitySeries,
            )
          : [],
      [
        municipalitySeries,
      ],
    );

  const selectedWeek =
    rawWeek !== null
    && Number.isInteger(
      rawWeek,
    )
    && referenceWeeks.some(
      (item) =>
        item.week
        === rawWeek,
    )
      ? rawWeek
      : null;

  useEffect(
    () => {
      if (
        !selectedMunicipality
        && weekParameter
        !== null
      ) {
        replaceParameters({
          semana:
            null,
        });

        return;
      }

      if (
        municipalitySeries
        && weekParameter
        !== null
        && selectedWeek
        === null
      ) {
        replaceParameters({
          semana:
            null,
        });
      }
    },
    [
      municipalitySeries,
      replaceParameters,
      selectedMunicipality,
      selectedWeek,
      weekParameter,
    ],
  );

  const weekOptions =
    useMemo(
      () => [
        {
          value:
            "",

          label:
            municipalitySeries
              ? "Selecione uma semana"
              : "Selecione um município primeiro",
        },

        ...referenceWeeks.map(
          (week) => ({
            value:
              String(
                week.week,
              ),

            label:
              formatPredictionWeekLabel(
                week,
              ),
          }),
        ),
      ],
      [
        municipalitySeries,
        referenceWeeks,
      ],
    );

  const selectedReferenceWeek =
    selectedWeek === null
      ? null
      : referenceWeeks.find(
          (item) =>
            item.week
            === selectedWeek,
        ) ?? null;

  const availableHorizons =
    municipalitySeries
    && selectedWeek !== null
      ? getAvailableHorizonsForWeek(
          municipalitySeries,
          selectedWeek,
        )
      : [];

  function handleRegionChange(
    value: string,
  ) {
    replaceParameters({
      regiao:
        value || null,

      uf:
        null,

      municipio:
        null,

      semana:
        null,
    });
  }

  function handleUfChange(
    value: string,
  ) {
    if (
      !value
    ) {
      replaceParameters({
        uf:
          null,

        municipio:
          null,

        semana:
          null,
      });

      return;
    }

    const territory =
      territories.find(
        (item) =>
          item.codigoUfIbge
          === value,
      );

    replaceParameters({
      regiao:
        territory
          ?.regiao
        ?? selectedRegion
        ?? null,

      uf:
        value,

      municipio:
        null,

      semana:
        null,
    });
  }

  function handleMunicipalityChange(
    value: string | null,
  ) {
    if (
      value === null
    ) {
      replaceParameters({
        municipio:
          null,

        semana:
          null,
      });

      return;
    }

    const territory =
      territories.find(
        (item) =>
          item.codigoIbge7
          === value,
      );

    if (
      !territory
    ) {
      return;
    }

    replaceParameters({
      regiao:
        territory.regiao,

      uf:
        territory.codigoUfIbge,

      municipio:
        territory.codigoIbge7,

      semana:
        null,
    });
  }

  function handleWeekChange(
    value: string,
  ) {
    replaceParameters({
      semana:
        value || null,
    });
  }

  function handleReset() {
    replaceParameters({
      regiao:
        null,

      uf:
        null,

      municipio:
        null,

      semana:
        null,
    });
  }

  const filtersDisabled =
    territoriesState.status
    === "loading"
    || territoriesState.status
    === "error";

  const hasActiveFilters =
    Boolean(
      selectedRegion
      || selectedUf
      || selectedMunicipality
      || selectedWeek,
    );

  return (
    <>
      <FilterBar
        title="Consulta retrospectiva"
        description="Selecione o município e a semana epidemiológica de referência para consultar como o modelo avaliou os horizontes futuros de 2025."
        hasActiveFilters={
          hasActiveFilters
        }
        onReset={
          handleReset
        }
      >
        <div
          className={
            styles.regionControl
          }
        >
          <SelectFilter
            id="prediction-region"
            label="Região"
            value={
              selectedRegion
            }
            options={
              regionOptions
            }
            disabled={
              filtersDisabled
            }
            onChange={
              handleRegionChange
            }
          />
        </div>

        <div
          className={
            styles.ufControl
          }
        >
          <SelectFilter
            id="prediction-state"
            label="UF"
            value={
              selectedUf
            }
            options={
              ufOptions
            }
            disabled={
              filtersDisabled
            }
            onChange={
              handleUfChange
            }
          />
        </div>

        <div
          className={
            styles.municipalityControl
          }
        >
          <MunicipalityCombobox
            items={
              municipalityItems
            }
            selectedCode={
              selectedMunicipality
            }
            disabled={
              filtersDisabled
            }
            onChange={
              handleMunicipalityChange
            }
          />
        </div>

        <div
          className={
            styles.weekControl
          }
        >
          <SelectFilter
            id="prediction-week"
            label="Semana de referência"
            value={
              selectedWeek === null
                ? ""
                : String(
                    selectedWeek,
                  )
            }
            options={
              weekOptions
            }
            disabled={
              !selectedMunicipality
              || seriesStatus
              !== "ready"
            }
            onChange={
              handleWeekChange
            }
          />
        </div>
      </FilterBar>

      {territoriesState.status
      === "loading" ? (
        <p
          className={
            styles.status
          }
        >
          Carregando municípios com avaliação preditiva disponível…
        </p>
      ) : null}

      {territoriesState.error ? (
        <p
          className={
            styles.error
          }
        >
          {
            territoriesState.error
          }
        </p>
      ) : null}

      {seriesStatus
      === "loading" ? (
        <p
          className={
            styles.status
          }
        >
          Carregando a série retrospectiva do município selecionado…
        </p>
      ) : null}

      {seriesError ? (
        <p
          className={
            styles.error
          }
        >
          {
            seriesError
          }
        </p>
      ) : null}

      {!selectedMunicipality ? (
        <section
          className={
            styles.context
          }
        >
          <span
            className={
              styles.contextEyebrow
            }
          >
            Seleção necessária
          </span>

          <h2>
            Escolha um município
          </h2>

          <p>
            A avaliação preditiva é municipal. Depois da seleção, a aplicação carregará somente a série correspondente e permitirá escolher uma semana epidemiológica de 2025.
          </p>
        </section>
      ) : null}

      {selectedTerritory
      && seriesStatus
      === "ready"
      && selectedWeek
      === null ? (
        <section
          className={
            styles.context
          }
        >
          <span
            className={
              styles.contextEyebrow
            }
          >
            Município selecionado
          </span>

          <h2>
            {selectedTerritory.nomeMunicipio} — {selectedTerritory.nomeUf}
          </h2>

          <p>
            Agora selecione uma semana epidemiológica de referência para consultar os horizontes disponíveis.
          </p>

          <p
            className={
              styles.note
            }
          >
            As semanas finais de 2025 possuem menos horizontes disponíveis porque previsões de duas, três ou quatro semanas à frente exigiriam observações fora da janela retrospectiva utilizada na avaliação.
          </p>
        </section>
      ) : null}

      {selectedTerritory
      && selectedReferenceWeek
      && municipalitySeries ? (
        <section
          className={
            styles.context
          }
        >
          <span
            className={
              styles.contextEyebrow
            }
          >
            Consulta pronta
          </span>

          <h2>
            {selectedTerritory.nomeMunicipio} — {selectedTerritory.nomeUf}
          </h2>

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
                Semana epidemiológica
              </span>

              <strong>
                SE {String(
                  selectedReferenceWeek.week,
                ).padStart(
                  2,
                  "0",
                )}/{selectedReferenceWeek.year}
              </strong>
            </div>

            <div
              className={
                styles.summaryItem
              }
            >
              <span>
                Início da semana
              </span>

              <strong>
                {formatPredictionDate(
                  selectedReferenceWeek.startDate,
                )}
              </strong>
            </div>

            <div
              className={
                styles.summaryItem
              }
            >
              <span>
                Horizontes disponíveis
              </span>

              <strong>
                {availableHorizons
                  .map(
                    (horizon) =>
                      horizon.toUpperCase(),
                  )
                  .join(
                    ", ",
                  )}
              </strong>
            </div>
          </div>

          <p
            className={
              styles.note
            }
          >
            Esta é uma consulta retrospectiva de 2025. Os resultados que serão exibidos representam como o modelo teria avaliado os horizontes futuros a partir desta semana de referência, e não um alerta atual.
          </p>
        </section>
      ) : null}
    </>
  );
}