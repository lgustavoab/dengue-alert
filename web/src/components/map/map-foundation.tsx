"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  formatMapWeekOptionLabel,
} from "@/lib/map-week-dates";

import { FilterBar } from "@/components/filters/filter-bar";
import { MunicipalityMap } from "@/components/map/municipality-map";
import { SelectFilter } from "@/components/filters/select-filter";
import {
  DEFAULT_MAP_HORIZON,
  DEFAULT_MAP_WEEK,
  formatMapWeekLabel,
  getAvailableMapHorizons,
  getMapHorizonLabel,
  normalizeMapSelection,
} from "@/lib/map-selection-utils";
import {
  buildPredictionMapSliceUrl,
  createMapSliceErrorState,
  createMapSliceLoadingState,
  resolveCurrentMapSliceState,
} from "@/lib/map-slice-state";
import type {
  MapSliceState,
} from "@/lib/map-slice-state";
import type {
  PredictionMapContract,
  PredictionMapHorizon,
  PredictionMapIndexContract,
} from "@/lib/serving/prediction-map-types";

import styles from "./map-foundation.module.css";

type LoadingStatus = "loading" | "ready" | "error";

type GeographyMetadata = {
  schema_version: "1.0";
  status: "APROVADO";
  preparation: {
    territories: number;
  };
  web_geometry: {
    format: string;
    file: string;
    size_bytes: number;
    gzip_size_bytes: number;
    sha256: string;
  };
};

type FoundationState = {
  status: LoadingStatus;
  index: PredictionMapIndexContract | null;
  geography: GeographyMetadata | null;
  error: string | null;
};

function validateIndex(payload: PredictionMapIndexContract): void {
  if (
    payload.schema_version !== "1.0"
    || payload.status !== "APROVADO"
    || payload.avaliacao !== "retrospectiva_2025"
    || payload.ano_epidemiologico !== 2025
    || payload.municipios !== 5_569
    || payload.predicoes !== 1_124_938
    || payload.arquivos !== 202
  ) {
    throw new Error("Índice preditivo do mapa inválido.");
  }
}

function validateGeography(payload: GeographyMetadata): void {
  if (
    payload.schema_version !== "1.0"
    || payload.status !== "APROVADO"
    || payload.preparation.territories !== 5_571
    || payload.web_geometry.format !== "TopoJSON"
    || payload.web_geometry.file !== "municipalities.topojson"
    || !Number.isInteger(payload.web_geometry.size_bytes)
    || payload.web_geometry.size_bytes <= 0
    || !Number.isInteger(payload.web_geometry.gzip_size_bytes)
    || payload.web_geometry.gzip_size_bytes <= 0
    || typeof payload.web_geometry.sha256 !== "string"
    || payload.web_geometry.sha256.length !== 64
  ) {
    throw new Error("Metadata geográfica inválida.");
  }
}

function validateSlice(
  payload: PredictionMapContract,
  expectedWeek: number,
  expectedHorizon: PredictionMapHorizon,
): void {
  if (
    payload.schema_version !== "1.0"
    || payload.ano_epidemiologico !== 2025
    || payload.semana_epidemiologica !== expectedWeek
    || payload.horizonte !== expectedHorizon
    || payload.count !== 5_569
    || payload.data.codigo_ibge_7.length !== payload.count
    || payload.data.score.length !== payload.count
    || payload.data.predicao.length !== payload.count
  ) {
    throw new Error("Contrato preditivo nacional inválido.");
  }
}

function isPredictionMapHorizon(
  value: number,
): value is PredictionMapHorizon {
  return value === 1 || value === 2 || value === 3 || value === 4;
}

function formatPercentage(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "percent",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatInteger(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

function formatMebibytes(value: number): string {
  return `${(value / 1024 ** 2).toFixed(2)} MiB`;
}

export function MapFoundation() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [foundationState, setFoundationState] = useState<FoundationState>({
    status: "loading",
    index: null,
    geography: null,
    error: null,
  });

  const [sliceState, setSliceState] = useState<MapSliceState>({
    week: null,
    horizon: null,
    status: "loading",
    data: null,
    error: null,
  });

  const [
    sliceRequestVersion,
    setSliceRequestVersion,
  ] = useState(
    0,
  );

  useEffect(() => {
    const controller = new AbortController();

    async function loadFoundation() {
      try {
        const [indexResponse, geographyResponse] = await Promise.all([
          fetch("/api/serving/prediction/map", {
            signal: controller.signal,
          }),
          fetch("/data/serving/geography/metadata.json", {
            signal: controller.signal,
          }),
        ]);

        if (!indexResponse.ok) {
          throw new Error(`Índice preditivo: HTTP ${indexResponse.status}`);
        }

        if (!geographyResponse.ok) {
          throw new Error(
            `Metadata geográfica: HTTP ${geographyResponse.status}`,
          );
        }

        const index: PredictionMapIndexContract = await indexResponse.json();
        const geography: GeographyMetadata = await geographyResponse.json();

        validateIndex(index);
        validateGeography(geography);

        setFoundationState({
          status: "ready",
          index,
          geography,
          error: null,
        });
      } catch (error) {
        if (
          error instanceof DOMException
          && error.name === "AbortError"
        ) {
          return;
        }

        console.error(error);

        setFoundationState({
          status: "error",
          index: null,
          geography: null,
          error: "Não foi possível preparar a infraestrutura do mapa preditivo.",
        });
      }
    }

    void loadFoundation();

    return () => controller.abort();
  }, []);

  const selection = useMemo(() => {
    if (foundationState.index === null) {
      return {
        week: DEFAULT_MAP_WEEK,
        horizon: DEFAULT_MAP_HORIZON,
        normalized: false,
      };
    }

    return normalizeMapSelection(
      foundationState.index,
      searchParams.get("semana"),
      searchParams.get("horizonte"),
    );
  }, [foundationState.index, searchParams]);

  const replaceSelection = useCallback(
    (week: number, horizon: PredictionMapHorizon) => {
      const parameters = new URLSearchParams(searchParams.toString());

      parameters.set("semana", String(week));
      parameters.set("horizonte", String(horizon));

      router.replace(`${pathname}?${parameters.toString()}`, {
        scroll: false,
      });
    },
    [pathname, router, searchParams],
  );

  useEffect(() => {
    if (
      foundationState.index === null
      || !selection.normalized
    ) {
      return;
    }

    replaceSelection(selection.week, selection.horizon);
  }, [
    foundationState.index,
    replaceSelection,
    selection.horizon,
    selection.normalized,
    selection.week,
  ]);

  useEffect(() => {
    if (foundationState.index === null) {
      return;
    }

    const controller = new AbortController();

    async function loadSlice() {
      try {
        const response = await fetch(
          buildPredictionMapSliceUrl(
            selection.week,
            selection.horizon,
          ),
          {
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          throw new Error(`Recorte preditivo: HTTP ${response.status}`);
        }

        const payload: PredictionMapContract = await response.json();

        validateSlice(
          payload,
          selection.week,
          selection.horizon,
        );

        setSliceState({
          week: selection.week,
          horizon: selection.horizon,
          status: "ready",
          data: payload,
          error: null,
        });
      } catch (error) {
        if (
          error instanceof DOMException
          && error.name === "AbortError"
        ) {
          return;
        }

        console.error(error);

        setSliceState(
          createMapSliceErrorState(
            selection.week,
            selection.horizon,
            "Não foi possível carregar o recorte preditivo selecionado.",
          ),
        );
      }
    }

    void loadSlice();

    return () => controller.abort();
  }, [
    foundationState.index,
    selection.horizon,
    selection.week,
    sliceRequestVersion,
  ]);

  const availableHorizons = useMemo(
    () =>
      foundationState.index
        ? getAvailableMapHorizons(
          foundationState.index,
          selection.week,
        )
        : [],
    [foundationState.index, selection.week],
  );

  const weekOptions = useMemo(
    () =>
      Array.from(
        { length: 52 },
        (_item, position) => {
          const week = position + 1;

          return {
            value: String(week),
            label: formatMapWeekOptionLabel(week),
          };
        },
      ),
    [],
  );

  const horizonOptions = useMemo(
    () =>
      availableHorizons.map((horizon) => ({
        value: String(horizon),
        label: getMapHorizonLabel(horizon),
      })),
    [availableHorizons],
  );

  function handleWeekChange(value: string) {
    if (foundationState.index === null) {
      return;
    }

    const week = Number(value);

    if (
      !Number.isInteger(week)
      || week < 1
      || week > 52
    ) {
      return;
    }

    const horizons = getAvailableMapHorizons(
      foundationState.index,
      week,
    );

    const horizon = horizons.includes(selection.horizon)
      ? selection.horizon
      : DEFAULT_MAP_HORIZON;

    replaceSelection(
      week,
      horizon,
    );
  }

  function handleHorizonChange(value: string) {
    const parsedHorizon = Number(value);

    if (
      !isPredictionMapHorizon(parsedHorizon)
      || !availableHorizons.includes(parsedHorizon)
    ) {
      return;
    }

    replaceSelection(
      selection.week,
      parsedHorizon,
    );
  }

  function handleReset() {
    replaceSelection(
      DEFAULT_MAP_WEEK,
      DEFAULT_MAP_HORIZON,
    );
  }

  function handleSliceRetry() {
    setSliceState(
      createMapSliceLoadingState(
        selection.week,
        selection.horizon,
      ),
    );

    setSliceRequestVersion(
      (version) =>
        version + 1,
    );
  }

  if (foundationState.status === "loading") {
    return (
      <section
        className={styles.statusCard}
        aria-busy="true"
      >
        <span className={styles.eyebrow}>
          Infraestrutura do mapa
        </span>

        <h2>
          Preparando contratos
        </h2>

        <p>
          Validando a cobertura temporal, os metadados geográficos e a
          disponibilidade da avaliação retrospectiva.
        </p>
      </section>
    );
  }

  if (
    foundationState.status === "error"
    || foundationState.index === null
    || foundationState.geography === null
  ) {
    return (
      <section
        className={styles.statusCard}
        role="alert"
      >
        <span className={styles.eyebrow}>
          Mapa indisponível
        </span>

        <h2>
          Não foi possível preparar a visualização
        </h2>

        <p>
          {foundationState.error}
        </p>
      </section>
    );
  }

  const geography = foundationState.geography;

  const currentSliceState =
    resolveCurrentMapSliceState(
      sliceState,
      selection.week,
      selection.horizon,
    );

  const alertCount =
    currentSliceState.data
      ?.data
      .predicao
      .filter(Boolean)
      .length
    ?? null;

  const noAlertCount =
    alertCount === null
      ? null
      : currentSliceState.data
        ? currentSliceState.data.count - alertCount
        : null;

  const withoutPrediction =
    currentSliceState.status
    === "ready"
      ? geography.preparation.territories
        - foundationState.index.municipios
      : null;

  return (
    <div className={styles.foundation}>
      <FilterBar
        title="Recorte espacial"
        description="Escolha a semana epidemiológica de referência e quantas semanas à frente deseja consultar."
        hasActiveFilters={
          selection.week !== DEFAULT_MAP_WEEK
          || selection.horizon !== DEFAULT_MAP_HORIZON
        }
        onReset={handleReset}
      >
        <SelectFilter
          id="map-week"
          label="Semana epidemiológica"
          value={String(selection.week)}
          options={weekOptions}
          onChange={handleWeekChange}
        />

        <SelectFilter
          id="map-horizon"
          label="Horizonte"
          value={String(selection.horizon)}
          options={horizonOptions}
          onChange={handleHorizonChange}
        />
      </FilterBar>

      <section
        className={styles.summary}
        aria-label="Resumo do recorte selecionado"
      >
        <article className={styles.summaryCard}>
          <span>
            Seleção
          </span>

          <strong>
            {formatMapWeekLabel(selection.week)}
            {" · "}
            H{selection.horizon}
          </strong>

          <p>
            {getMapHorizonLabel(selection.horizon)}
          </p>
        </article>

        <article className={styles.summaryCard}>
          <span>
            ALERTA
          </span>

          <strong>
            {alertCount === null
              ? "—"
              : formatInteger(alertCount)}
          </strong>

          <p>
            Municípios classificados com o resultado preditivo oficial de
            alerta.
          </p>
        </article>

        <article className={styles.summaryCard}>
          <span>
            SEM ALERTA
          </span>

          <strong>
            {noAlertCount === null
              ? "—"
              : formatInteger(noAlertCount)}
          </strong>

          <p>
            Municípios avaliados sem classificação de alerta no recorte.
          </p>
        </article>

        <article className={styles.summaryCard}>
          <span>
            Sem avaliação preditiva
          </span>

          <strong>
            {withoutPrediction === null
              ? "—"
              : formatInteger(withoutPrediction)}
          </strong>

          <p>
            Territórios presentes na malha geográfica e ausentes da avaliação
            final.
          </p>
        </article>
      </section>

      {currentSliceState.status
      === "error" ? (
        <section
          className={
            styles.sliceError
          }
          role="alert"
        >
          <div>
            <span>
              Recorte temporariamente indisponível
            </span>

            <strong>
              Falha ao carregar {formatMapWeekLabel(
                selection.week,
              )} · H{selection.horizon}
            </strong>

            <p>
              {currentSliceState.error} Nenhuma classificação epidemiológica foi inferida para esta falha.
            </p>
          </div>

          <button
            type="button"
            className={
              styles.retryButton
            }
            onClick={
              handleSliceRetry
            }
          >
            Tentar novamente
          </button>
        </section>
      ) : null}

      <section className={styles.workspace}>
        <div className={styles.workspaceHeader}>
          <div>
            <span className={styles.eyebrow}>
              Mapa municipal do Brasil
            </span>

            <h2>
              {formatMapWeekLabel(selection.week)}
              {" · "}
              H{selection.horizon}
            </h2>

<p>
  A malha municipal do Brasil apresenta a classificação preditiva
  retrospectiva do recorte selecionado, distinguindo municípios em
  ALERTA, SEM ALERTA e territórios sem avaliação preditiva.
</p>
          </div>

          {currentSliceState.data ? (
            <div className={styles.threshold}>
              <span>
                Limiar de alerta
              </span>

              <strong>
                {formatPercentage(
                  currentSliceState.data.threshold,
                )}
              </strong>
            </div>
          ) : null}
        </div>

        <MunicipalityMap
          prediction={
            currentSliceState.data
          }
          predictionStatus={
            currentSliceState.status
          }
        />

        <div className={styles.infrastructure}>
          <div>
            <span>
              Territórios da malha
            </span>

            <strong>
              {formatInteger(
                geography.preparation.territories,
              )}
            </strong>
          </div>

          <div>
            <span>
              Municípios avaliados
            </span>

            <strong>
              {formatInteger(
                foundationState.index.municipios,
              )}
            </strong>
          </div>

          <div>
            <span>
              Asset geográfico
            </span>

            <strong>
              {formatMebibytes(
                geography.web_geometry.size_bytes,
              )}
            </strong>
          </div>

          <div>
            <span>
              Transferência gzip
            </span>

            <strong>
              {formatMebibytes(
                geography.web_geometry.gzip_size_bytes,
              )}
            </strong>
          </div>
        </div>
      </section>

      <section className={styles.methodNote}>
        <strong>
          Como interpretar
        </strong>

        <p>
          H1 a H4 representam distância temporal, não gravidade. ALERTA
          corresponde à classificação binária oficial produzida pelo modelo
          quando o score atinge ou supera o limiar definido durante a validação.
        </p>

        <p>
          A probabilidade se refere ao estado futuro metodologicamente definido
          de risco elevado e não à quantidade futura de casos de dengue.
        </p>
      </section>
    </div>
  );
}
