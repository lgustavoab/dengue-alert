"use client";

import {
  useEffect,
  useId,
  useMemo,
  useState,
} from "react";

import type {
  ChangeEvent as ReactChangeEvent,
  KeyboardEvent as ReactKeyboardEvent,
  MouseEvent as ReactMouseEvent,
  PointerEvent as ReactPointerEvent,
} from "react";

import {
  parseMunicipalityTopology,
} from "@/lib/map-geography";

import {
  joinMunicipalityPredictions,
} from "@/lib/map-prediction";

import type {
  MunicipalityMapDatum,
  MunicipalityPredictionStatus,
} from "@/lib/map-prediction";

import {
  MAP_VIEWBOX_HEIGHT,
  MAP_VIEWBOX_WIDTH,
  buildMunicipalitySvgPaths,
} from "@/lib/map-rendering";

import type {
  MunicipalitySvgPath,
} from "@/lib/map-rendering";

import {
  getMapHorizonLabel,
} from "@/lib/map-selection-utils";

import {
  parseMapTerritoryIndex,
} from "@/lib/map-territories";

import type {
  MapTerritoryIndex,
} from "@/lib/map-territories";

import {
  formatMapTerritorySearchLabel,
  searchMapTerritories,
} from "@/lib/map-territory-search";

import {
  formatMapWeekDateRange,
} from "@/lib/map-week-dates";

import type {
  PredictionMapContract,
} from "@/lib/serving/prediction-map-types";

import type {
  TerritoryFilterItem,
} from "@/lib/serving/types";

import styles from "./municipality-map.module.css";

type GeometryState =
  | {
      status: "loading";
      paths: null;
      error: null;
    }
  | {
      status: "ready";
      paths: MunicipalitySvgPath[];
      error: null;
    }
  | {
      status: "error";
      paths: null;
      error: string;
    };

type TerritoryState =
  | {
      status: "loading";
      index: null;
      error: null;
    }
  | {
      status: "ready";
      index: MapTerritoryIndex;
      error: null;
    }
  | {
      status: "error";
      index: null;
      error: string;
    };

type MunicipalityMapProps = {
  prediction: PredictionMapContract | null;
};

const GEOGRAPHY_URL =
  "/data/serving/geography/municipalities.topojson";

const TERRITORIES_URL =
  "/api/serving/territories";

function getMunicipalityClassName(
  status: MunicipalityPredictionStatus,
): string {
  if (
    status === "alerta"
  ) {
    return `${styles.municipality} ${styles.alert}`;
  }

  if (
    status === "sem_alerta"
  ) {
    return `${styles.municipality} ${styles.noAlert}`;
  }

  return `${styles.municipality} ${styles.withoutEvaluation}`;
}

function getStatusLabel(
  status: MunicipalityPredictionStatus,
): string {
  if (
    status === "alerta"
  ) {
    return "ALERTA";
  }

  if (
    status === "sem_alerta"
  ) {
    return "SEM ALERTA";
  }

  return "SEM AVALIAÇÃO PREDITIVA";
}

function getStatusBadgeClassName(
  status: MunicipalityPredictionStatus,
): string {
  if (
    status === "alerta"
  ) {
    return `${styles.statusBadge} ${styles.alertBadge}`;
  }

  if (
    status === "sem_alerta"
  ) {
    return `${styles.statusBadge} ${styles.noAlertBadge}`;
  }

  return `${styles.statusBadge} ${styles.withoutEvaluationBadge}`;
}

function formatPercentage(
  value: number,
): string {
  return new Intl.NumberFormat(
    "pt-BR",
    {
      style: "percent",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  ).format(
    value,
  );
}

function readMunicipalityCode(
  target: EventTarget | null,
): string | null {
  if (
    !(target instanceof Element)
  ) {
    return null;
  }

  const municipality =
    target.closest<SVGPathElement>(
      "path[data-municipality-code]",
    );

  return (
    municipality
      ?.dataset
      .municipalityCode
    ?? null
  );
}

function renderClassifiedMunicipality(
  municipality: MunicipalityMapDatum,
) {
  return (
    <path
      key={
        municipality.codigoIbge7
      }
      d={
        municipality.d
      }
      data-municipality-code={
        municipality.codigoIbge7
      }
      className={
        getMunicipalityClassName(
          municipality.status,
        )
      }
      vectorEffect="non-scaling-stroke"
      aria-hidden="true"
    />
  );
}

function renderNeutralMunicipality(
  municipality: MunicipalitySvgPath,
) {
  return (
    <path
      key={
        municipality.codigoIbge7
      }
      d={
        municipality.d
      }
      data-municipality-code={
        municipality.codigoIbge7
      }
      className={
        `${styles.municipality} ${styles.neutral}`
      }
      vectorEffect="non-scaling-stroke"
      aria-hidden="true"
    />
  );
}

export function MunicipalityMap({
  prediction,
}: MunicipalityMapProps) {
  const searchListboxId =
    useId();

  const searchHelpId =
    useId();

  const [
    geometryState,
    setGeometryState,
  ] =
    useState<GeometryState>({
      status: "loading",
      paths: null,
      error: null,
    });

  const [
    territoryState,
    setTerritoryState,
  ] =
    useState<TerritoryState>({
      status: "loading",
      index: null,
      error: null,
    });

  const [
    hoveredCode,
    setHoveredCode,
  ] =
    useState<string | null>(
      null,
    );

  const [
    selectedCode,
    setSelectedCode,
  ] =
    useState<string | null>(
      null,
    );

  const [
    searchQuery,
    setSearchQuery,
  ] =
    useState(
      "",
    );

  const [
    searchOpen,
    setSearchOpen,
  ] =
    useState(
      false,
    );

  const [
    activeSearchIndex,
    setActiveSearchIndex,
  ] =
    useState(
      -1,
    );

  useEffect(
    () => {
      const controller =
        new AbortController();

      async function loadGeometry() {
        try {
          const response =
            await fetch(
              GEOGRAPHY_URL,
              {
                signal:
                  controller.signal,
              },
            );

          if (
            !response.ok
          ) {
            throw new Error(
              `Geometria municipal: HTTP ${response.status}`,
            );
          }

          const topology:
            unknown =
            await response.json();

          const geography =
            parseMunicipalityTopology(
              topology,
            );

          const paths =
            buildMunicipalitySvgPaths(
              geography.featureCollection,
            );

          setGeometryState({
            status: "ready",
            paths,
            error: null,
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

          setGeometryState({
            status: "error",
            paths: null,
            error:
              "Não foi possível carregar a malha municipal do Brasil.",
          });
        }
      }

      void loadGeometry();

      return () =>
        controller.abort();
    },
    [],
  );

  useEffect(
    () => {
      const controller =
        new AbortController();

      async function loadTerritories() {
        try {
          const response =
            await fetch(
              TERRITORIES_URL,
              {
                signal:
                  controller.signal,
              },
            );

          if (
            !response.ok
          ) {
            throw new Error(
              `Índice territorial: HTTP ${response.status}`,
            );
          }

          const payload:
            unknown =
            await response.json();

          const index =
            parseMapTerritoryIndex(
              payload,
            );

          setTerritoryState({
            status: "ready",
            index,
            error: null,
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

          setTerritoryState({
            status: "error",
            index: null,
            error:
              "Não foi possível carregar a identificação dos municípios.",
          });
        }
      }

      void loadTerritories();

      return () =>
        controller.abort();
    },
    [],
  );

  const joinedPrediction =
    useMemo(
      () => {
        if (
          geometryState.status
          !== "ready"
          || prediction
          === null
        ) {
          return null;
        }

        return joinMunicipalityPredictions(
          geometryState.paths,
          prediction,
        );
      },
      [
        geometryState,
        prediction,
      ],
    );

  const joinedByCode =
    useMemo(
      () => {
        if (
          joinedPrediction
          === null
        ) {
          return new Map<
            string,
            MunicipalityMapDatum
          >();
        }

        return new Map(
          joinedPrediction
            .municipalities
            .map(
              (municipality) => [
                municipality.codigoIbge7,
                municipality,
              ],
            ),
        );
      },
      [
        joinedPrediction,
      ],
    );

  const pathsByCode =
    useMemo(
      () => {
        if (
          geometryState.status
          !== "ready"
        ) {
          return new Map<
            string,
            MunicipalitySvgPath
          >();
        }

        return new Map(
          geometryState
            .paths
            .map(
              (municipality) => [
                municipality.codigoIbge7,
                municipality,
              ],
            ),
        );
      },
      [
        geometryState,
      ],
    );

  const renderedMunicipalities =
    useMemo(
      () => {
        if (
          geometryState.status
          !== "ready"
        ) {
          return null;
        }

        if (
          joinedPrediction
          !== null
        ) {
          return joinedPrediction
            .municipalities
            .map(
              renderClassifiedMunicipality,
            );
        }

        return geometryState
          .paths
          .map(
            renderNeutralMunicipality,
          );
      },
      [
        geometryState,
        joinedPrediction,
      ],
    );

  const searchResults =
    useMemo(
      () => {
        if (
          territoryState.status
          !== "ready"
        ) {
          return [];
        }

        return searchMapTerritories(
          territoryState.index.items,
          searchQuery,
        );
      },
      [
        searchQuery,
        territoryState,
      ],
    );

  const hoveredTerritory:
    TerritoryFilterItem | null =
    territoryState.status
    === "ready"
    && hoveredCode
    !== null
      ? territoryState
        .index
        .byCode
        .get(
          hoveredCode,
        )
        ?? null
      : null;

  const hoveredPrediction =
    hoveredCode
    !== null
      ? joinedByCode.get(
          hoveredCode,
        )
        ?? null
      : null;

  const selectedTerritory:
    TerritoryFilterItem | null =
    territoryState.status
    === "ready"
    && selectedCode
    !== null
      ? territoryState
        .index
        .byCode
        .get(
          selectedCode,
        )
        ?? null
      : null;

  const selectedPrediction =
    selectedCode
    !== null
      ? joinedByCode.get(
          selectedCode,
        )
        ?? null
      : null;

  const selectedPath =
    selectedCode
    !== null
      ? pathsByCode.get(
          selectedCode,
        )
        ?? null
      : null;

  const searchPopupVisible =
    searchOpen
    && searchQuery
      .trim()
      .length > 0;

  const activeSearchResult =
    activeSearchIndex >= 0
      ? searchResults[
        activeSearchIndex
      ]
        ?? null
      : null;

  const activeDescendant =
    searchPopupVisible
    && activeSearchResult
      ? (
        `${searchListboxId}-option-${activeSearchIndex}`
      )
      : undefined;

  function selectMunicipality(
    codigoIbge7: string,
  ) {
    if (
      territoryState.status
      !== "ready"
    ) {
      return;
    }

    const territory =
      territoryState
        .index
        .byCode
        .get(
          codigoIbge7,
        );

    if (
      territory
      === undefined
    ) {
      return;
    }

    setSelectedCode(
      codigoIbge7,
    );

    setSearchQuery(
      territory.nomeMunicipio,
    );

    setSearchOpen(
      false,
    );

    setActiveSearchIndex(
      -1,
    );
  }

  function clearSelection() {
    setSelectedCode(
      null,
    );

    setSearchQuery(
      "",
    );

    setSearchOpen(
      false,
    );

    setActiveSearchIndex(
      -1,
    );
  }

  function handleSearchChange(
    event: ReactChangeEvent<HTMLInputElement>,
  ) {
    const nextQuery =
      event.target.value;

    setSearchQuery(
      nextQuery,
    );

    setSearchOpen(
      nextQuery
        .trim()
        .length > 0,
    );

    setActiveSearchIndex(
      nextQuery
        .trim()
        .length > 0
        ? 0
        : -1,
    );
  }

  function handleSearchFocus() {
    if (
      searchQuery
        .trim()
        .length === 0
    ) {
      return;
    }

    setSearchOpen(
      true,
    );

    if (
      searchResults.length > 0
      && activeSearchIndex < 0
    ) {
      setActiveSearchIndex(
        0,
      );
    }
  }

  function handleSearchKeyDown(
    event: ReactKeyboardEvent<HTMLInputElement>,
  ) {
    if (
      event.key === "Escape"
    ) {
      if (
        searchOpen
      ) {
        event.preventDefault();

        setSearchOpen(
          false,
        );

        setActiveSearchIndex(
          -1,
        );
      }

      return;
    }

    if (
      event.key === "ArrowDown"
    ) {
      if (
        searchResults.length === 0
      ) {
        return;
      }

      event.preventDefault();

      setSearchOpen(
        true,
      );

      setActiveSearchIndex(
        (current) => {
          if (
            current < 0
            || current
            >= searchResults.length - 1
          ) {
            return 0;
          }

          return current + 1;
        },
      );

      return;
    }

    if (
      event.key === "ArrowUp"
    ) {
      if (
        searchResults.length === 0
      ) {
        return;
      }

      event.preventDefault();

      setSearchOpen(
        true,
      );

      setActiveSearchIndex(
        (current) => {
          if (
            current <= 0
          ) {
            return (
              searchResults.length - 1
            );
          }

          return current - 1;
        },
      );

      return;
    }

    if (
      event.key === "Home"
      && searchOpen
      && searchResults.length > 0
    ) {
      event.preventDefault();

      setActiveSearchIndex(
        0,
      );

      return;
    }

    if (
      event.key === "End"
      && searchOpen
      && searchResults.length > 0
    ) {
      event.preventDefault();

      setActiveSearchIndex(
        searchResults.length - 1,
      );

      return;
    }

    if (
      event.key === "Enter"
      && searchOpen
      && searchResults.length > 0
    ) {
      event.preventDefault();

      const result =
        searchResults[
          activeSearchIndex >= 0
            ? activeSearchIndex
            : 0
        ];

      if (
        result
      ) {
        selectMunicipality(
          result.codigoIbge7,
        );
      }
    }
  }

  function handlePointerOver(
    event: ReactPointerEvent<SVGSVGElement>,
  ) {
    if (
      territoryState.status
      !== "ready"
    ) {
      return;
    }

    const codigoIbge7 =
      readMunicipalityCode(
        event.target,
      );

    if (
      codigoIbge7
      === null
    ) {
      return;
    }

    setHoveredCode(
      (current) =>
        current
        === codigoIbge7
          ? current
          : codigoIbge7,
    );
  }

  function handlePointerLeave() {
    setHoveredCode(
      null,
    );
  }

  function handleClick(
    event: ReactMouseEvent<SVGSVGElement>,
  ) {
    if (
      territoryState.status
      !== "ready"
    ) {
      return;
    }

    const codigoIbge7 =
      readMunicipalityCode(
        event.target,
      );

    if (
      codigoIbge7
      === null
    ) {
      return;
    }

    selectMunicipality(
      codigoIbge7,
    );
  }

  if (
    geometryState.status
    === "loading"
  ) {
    return (
      <div
        className={
          styles.status
        }
        aria-busy="true"
      >
        <div
          className={
            styles.statusMarker
          }
          aria-hidden="true"
        >
          BR
        </div>

        <div>
          <strong>
            Carregando malha municipal
          </strong>

          <p>
            Preparando as 5.571 geometrias do Brasil para visualização.
          </p>
        </div>
      </div>
    );
  }

  if (
    geometryState.status
    === "error"
  ) {
    return (
      <div
        className={
          styles.status
        }
        role="alert"
      >
        <div
          className={
            styles.statusMarker
          }
          aria-hidden="true"
        >
          !
        </div>

        <div>
          <strong>
            Malha geográfica indisponível
          </strong>

          <p>
            {geometryState.error}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={
        styles.container
      }
    >
      <section
        className={
          styles.searchSection
        }
      >
        <div
          className={
            styles.searchHeader
          }
        >
          <div>
            <label
              className={
                styles.searchLabel
              }
              htmlFor={
                `${searchListboxId}-input`
              }
            >
              Buscar município
            </label>

            <p
              id={
                searchHelpId
              }
              className={
                styles.searchHint
              }
            >
              Pesquise pelo nome do município ou pelo código IBGE.
            </p>
          </div>

          {territoryState.status
          === "ready" ? (
            <span
              className={
                styles.searchCoverage
              }
            >
              5.571 territórios disponíveis
            </span>
          ) : null}
        </div>

        <div
          className={
            styles.searchControl
          }
        >
          <input
            id={
              `${searchListboxId}-input`
            }
            type="search"
            className={
              styles.searchInput
            }
            value={
              searchQuery
            }
            placeholder="Ex.: Penápolis ou 3537305"
            autoComplete="off"
            spellCheck="false"
            role="combobox"
            aria-autocomplete="list"
            aria-expanded={
              searchPopupVisible
            }
            aria-controls={
              searchPopupVisible
                ? searchListboxId
                : undefined
            }
            aria-activedescendant={
              activeDescendant
            }
            aria-describedby={
              searchHelpId
            }
            disabled={
              territoryState.status
              !== "ready"
            }
            onChange={
              handleSearchChange
            }
            onFocus={
              handleSearchFocus
            }
            onBlur={
              () => {
                setSearchOpen(
                  false,
                );

                setActiveSearchIndex(
                  -1,
                );
              }
            }
            onKeyDown={
              handleSearchKeyDown
            }
          />

          {searchPopupVisible ? (
            <div
              className={
                styles.searchResults
              }
            >
              {searchResults.length > 0 ? (
                <ul
                  id={
                    searchListboxId
                  }
                  className={
                    styles.searchList
                  }
                  role="listbox"
                  aria-label="Municípios encontrados"
                >
                  {searchResults.map(
                    (
                      territory,
                      index,
                    ) => {
                      const isActive =
                        index
                        === activeSearchIndex;

                      const isSelected =
                        territory
                          .codigoIbge7
                        === selectedCode;

                      const className = [
                        styles.searchOption,
                        isActive
                          ? styles.searchOptionActive
                          : "",
                        isSelected
                          ? styles.searchOptionSelected
                          : "",
                      ]
                        .filter(
                          Boolean,
                        )
                        .join(
                          " ",
                        );

                      return (
                        <li
                          id={
                            `${searchListboxId}-option-${index}`
                          }
                          key={
                            territory.codigoIbge7
                          }
                          className={
                            className
                          }
                          role="option"
                          aria-selected={
                            isSelected
                          }
                          onMouseDown={
                            (
                              event,
                            ) => {
                              event.preventDefault();
                            }
                          }
                          onMouseEnter={
                            () => {
                              setActiveSearchIndex(
                                index,
                              );
                            }
                          }
                          onClick={
                            () => {
                              selectMunicipality(
                                territory.codigoIbge7,
                              );
                            }
                          }
                        >
                          <div
                            className={
                              styles.searchOptionText
                            }
                          >
                            <strong>
                              {
                                territory
                                  .nomeMunicipio
                              }
                            </strong>

                            <span>
                              {
                                territory
                                  .nomeUf
                              }
                              {" · "}
                              {
                                territory
                                  .regiao
                              }
                            </span>
                          </div>

                          <div
                            className={
                              styles.searchOptionMeta
                            }
                          >
                            <span>
                              {
                                territory
                                  .codigoIbge7
                              }
                            </span>

                            <small
                              className={
                                territory
                                  .predicaoDisponivel
                                  ? styles.searchAvailability
                                  : `${styles.searchAvailability} ${styles.searchAvailabilityUnavailable}`
                              }
                            >
                              {
                                territory
                                  .predicaoDisponivel
                                  ? "Com avaliação"
                                  : "Sem avaliação"
                              }
                            </small>
                          </div>

                          <span
                            className={
                              styles.srOnly
                            }
                          >
                            {
                              formatMapTerritorySearchLabel(
                                territory,
                              )
                            }
                          </span>
                        </li>
                      );
                    },
                  )}
                </ul>
              ) : (
                <div
                  id={
                    searchListboxId
                  }
                  className={
                    styles.searchEmpty
                  }
                  role="status"
                >
                  Nenhum município encontrado para “
                  {searchQuery.trim()}
                  ”.
                </div>
              )}
            </div>
          ) : null}

          {territoryState.status
          === "loading" ? (
            <div
              className={
                styles.searchLoading
              }
              role="status"
            >
              Carregando índice municipal…
            </div>
          ) : null}
        </div>
      </section>

      <div
        className={
          styles.wrapper
        }
      >
        <svg
          className={
            styles.map
          }
          viewBox={
            `0 0 ${MAP_VIEWBOX_WIDTH} ${MAP_VIEWBOX_HEIGHT}`
          }
          role="img"
          aria-label={
            "Mapa municipal interativo do Brasil. "
            + "Para seleção por teclado, use a busca de município acima."
          }
          preserveAspectRatio="xMidYMid meet"
          onPointerOver={
            handlePointerOver
          }
          onPointerLeave={
            handlePointerLeave
          }
          onClick={
            handleClick
          }
        >
          <g
            className={
              styles.municipalities
            }
          >
            {
              renderedMunicipalities
            }
          </g>

          {selectedPath ? (
            <path
              d={
                selectedPath.d
              }
              className={
                styles.selectedMunicipality
              }
              vectorEffect="non-scaling-stroke"
              aria-hidden="true"
            />
          ) : null}
        </svg>

        {prediction === null ? (
          <div
            className={
              styles.updating
            }
            role="status"
          >
            Atualizando classificação…
          </div>
        ) : null}

        {hoveredTerritory ? (
          <div
            className={
              styles.hoverCard
            }
            aria-hidden="true"
          >
            <strong>
              {
                hoveredTerritory
                  .nomeMunicipio
              }
            </strong>

            <span>
              {
                hoveredTerritory
                  .nomeUf
              }
              {" · "}
              {
                hoveredTerritory
                  .regiao
              }
            </span>

            {prediction === null ? (
              <small>
                Atualizando classificação…
              </small>
            ) : hoveredPrediction ? (
              <small>
                {
                  getStatusLabel(
                    hoveredPrediction.status,
                  )
                }
              </small>
            ) : null}
          </div>
        ) : null}

        <div
          className={
            styles.legend
          }
          aria-label="Legenda do mapa"
        >
          <div
            className={
              styles.legendItem
            }
          >
            <span
              className={
                `${styles.legendSwatch} ${styles.alertSwatch}`
              }
              aria-hidden="true"
            />

            <span>
              ALERTA
            </span>

            {joinedPrediction ? (
              <strong>
                {
                  joinedPrediction
                    .summary
                    .alertCount
                    .toLocaleString(
                      "pt-BR",
                    )
                }
              </strong>
            ) : null}
          </div>

          <div
            className={
              styles.legendItem
            }
          >
            <span
              className={
                `${styles.legendSwatch} ${styles.noAlertSwatch}`
              }
              aria-hidden="true"
            />

            <span>
              SEM ALERTA
            </span>

            {joinedPrediction ? (
              <strong>
                {
                  joinedPrediction
                    .summary
                    .noAlertCount
                    .toLocaleString(
                      "pt-BR",
                    )
                }
              </strong>
            ) : null}
          </div>

          <div
            className={
              styles.legendItem
            }
          >
            <span
              className={
                `${styles.legendSwatch} ${styles.withoutEvaluationSwatch}`
              }
              aria-hidden="true"
            />

            <span>
              SEM AVALIAÇÃO
            </span>

            {joinedPrediction ? (
              <strong>
                {
                  joinedPrediction
                    .summary
                    .withoutEvaluationCount
                    .toLocaleString(
                      "pt-BR",
                    )
                }
              </strong>
            ) : null}
          </div>
        </div>

        <div
          className={
            styles.caption
          }
        >
          <span>
            Malha municipal
          </span>

          <strong>
            5.571 territórios renderizados
          </strong>
        </div>
      </div>

      {territoryState.status
      === "error" ? (
        <section
          className={
            styles.interactionError
          }
          role="alert"
        >
          <strong>
            Identificação municipal indisponível
          </strong>

          <p>
            {
              territoryState.error
            }
          </p>
        </section>
      ) : null}

      {selectedCode === null ? (
        <section
          className={
            styles.emptySelection
          }
        >
          <strong>
            Consulte um município
          </strong>

          <p>
            Busque um município pelo nome ou código IBGE, ou selecione
            diretamente um território no mapa para consultar seus detalhes.
          </p>
        </section>
      ) : null}

      {selectedCode !== null
      && selectedTerritory ? (
        <section
          className={
            styles.selectionPanel
          }
          aria-live="polite"
        >
          <div
            className={
              styles.selectionHeader
            }
          >
            <div>
              <span
                className={
                  styles.selectionEyebrow
                }
              >
                Município selecionado
              </span>

              <h3>
                {
                  selectedTerritory
                    .nomeMunicipio
                }
                {" · "}
                {
                  selectedTerritory
                    .nomeUf
                }
              </h3>

              <p>
                {
                  selectedTerritory
                    .regiao
                }
                {" · Código IBGE "}
                {
                  selectedTerritory
                    .codigoIbge7
                }
              </p>
            </div>

            <button
              type="button"
              className={
                styles.clearButton
              }
              onClick={
                clearSelection
              }
            >
              Limpar seleção
            </button>
          </div>

          {prediction === null ? (
            <div
              className={
                styles.selectionLoading
              }
              role="status"
            >
              Atualizando o resultado preditivo para o novo recorte…
            </div>
          ) : selectedPrediction ? (
            <div
              className={
                styles.detailGrid
              }
            >
              <div
                className={
                  styles.detailPrimary
                }
              >
                <span>
                  Resultado preditivo
                </span>

                <strong
                  className={
                    getStatusBadgeClassName(
                      selectedPrediction.status,
                    )
                  }
                >
                  {
                    getStatusLabel(
                      selectedPrediction.status,
                    )
                  }
                </strong>
              </div>

              <div
                className={
                  styles.detailItem
                }
              >
                <span>
                  Recorte
                </span>

                <strong>
                  SE
                  {
                    String(
                      prediction
                        .semana_epidemiologica,
                    ).padStart(
                      2,
                      "0",
                    )
                  }
                  {" · "}
                  H
                  {
                    prediction
                      .horizonte
                  }
                </strong>

                <small>
                  {
                    formatMapWeekDateRange(
                      prediction
                        .semana_epidemiologica,
                    )
                  }
                </small>

                <small>
                  {
                    getMapHorizonLabel(
                      prediction
                        .horizonte,
                    )
                  }
                </small>
              </div>

              {selectedPrediction
                .status
                !== "sem_avaliacao"
              && selectedPrediction
                .score
                !== null ? (
                <>
                  <div
                    className={
                      styles.detailItem
                    }
                  >
                    <span>
                      Probabilidade de risco elevado
                    </span>

                    <strong>
                      {
                        formatPercentage(
                          selectedPrediction
                            .score,
                        )
                      }
                    </strong>
                  </div>

                  <div
                    className={
                      styles.detailItem
                    }
                  >
                    <span>
                      Limiar de alerta
                    </span>

                    <strong>
                      {
                        formatPercentage(
                          prediction
                            .threshold,
                        )
                      }
                    </strong>
                  </div>
                </>
              ) : (
                <div
                  className={
                    styles.detailUnavailable
                  }
                >
                  <strong>
                    Sem avaliação preditiva
                  </strong>

                  <p>
                    Este território está presente na malha geográfica,
                    mas não possui resultado no conjunto retrospectivo
                    de avaliação.
                  </p>
                </div>
              )}
            </div>
          ) : null}

          <div
            className={
              styles.interpretation
            }
          >
            <strong>
              Interpretação
            </strong>

            <p>
              O valor apresentado é a probabilidade estimada do estado
              futuro metodologicamente definido de risco elevado. Ele
              não representa uma previsão da quantidade futura de casos
              de dengue.
            </p>
          </div>
        </section>
      ) : null}
    </div>
  );
}