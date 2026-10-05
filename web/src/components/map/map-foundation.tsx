"use client";

import Link from "next/link";

import { useCallback, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import {
  formatMapWeekOptionLabel,
} from "@/lib/map-week-dates";

import { FilterBar } from "@/components/filters/filter-bar";
import { MunicipalityMap } from "@/components/map/municipality-map";
import { formatMapAdvanceLabel } from "./municipality-map-result";
import { SelectFilter } from "@/components/filters/select-filter";
import {
  DEFAULT_MAP_HORIZON,
  DEFAULT_MAP_WEEK,
  formatMapWeekLabel,
  getAvailableMapHorizons,
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
          error: "Não foi possível carregar os dados necessários para abrir o mapa.",
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
            "Não foi possível carregar os resultados da semana e do prazo selecionados.",
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
        label: formatMapAdvanceLabel(horizon),
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
          Mapa dos resultados
        </span>

        <h2>
          Carregando o mapa
        </h2>

        <p>
          Preparando os municípios e os resultados da avaliação de 2025.
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
        title="Qual semana de 2025 você quer consultar?"
        description="A semana é o ponto de partida; o prazo indica quantas semanas depois o modelo tentou prever. SE significa Semana Epidemiológica. H1–H4 são prazos, não níveis de gravidade."
        hasActiveFilters={
          selection.week !== DEFAULT_MAP_WEEK
          || selection.horizon !== DEFAULT_MAP_HORIZON
        }
        onReset={handleReset}
      >
        <SelectFilter
          id="map-week"
          label="Semana de referência (SE)"
          value={String(selection.week)}
          options={weekOptions}
          onChange={handleWeekChange}
        />

        <SelectFilter
          id="map-horizon"
          label="Quantas semanas depois?"
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
            {formatMapAdvanceLabel(selection.horizon)} · avaliação de 2025
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
            Municípios em que o modelo indicou risco elevado na semana futura.
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
            Municípios sem alerta do modelo. Não significa ausência de dengue.
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
            Territórios que aparecem no mapa, mas não têm resultado na avaliação.
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
              {currentSliceState.error} A falha não significa “Sem alerta” nem “Sem avaliação”. Os resultados anteriores não são exibidos para esta seleção.
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
              {formatMapAdvanceLabel(selection.horizon)}
            </h2>

            <p>
              Resultados do modelo na avaliação retrospectiva de 2025, não alertas atuais.
              As cores mostram a indicação do modelo para a semana futura,
              não o risco observado. Use a busca para selecionar municípios pequenos.
            </p>
          </div>
        </div>

        <MunicipalityMap
          prediction={
            currentSliceState.data
          }
          predictionStatus={
            currentSliceState.status
          }
        />

        <details className={styles.coverageDetails}>
          <summary>Cobertura da avaliação e limite de alerta</summary>
          <p>
            O mapa reúne {formatInteger(geography.preparation.territories)} territórios;
            {" "}{formatInteger(foundationState.index.municipios)} municípios têm resultados na avaliação.
            A diferença é preservada como “Sem avaliação”, não como “Sem alerta”.
            No fim do ano, só aparecem os prazos disponíveis nos dados do estudo.
          </p>
          {currentSliceState.data ? (
            <p>
              Limite de alerta (limiar) para este prazo: {formatPercentage(currentSliceState.data.threshold)}.
              Ele foi definido durante a validação; a classificação exibida é a decisão oficial do modelo.
            </p>
          ) : null}
        </details>
      </section>

      <section className={styles.methodNote}>
        <strong>O que significa risco elevado neste estudo?</strong>
        <p>
          É quando a incidência acumulada em quatro semanas supera uma referência
          histórica do próprio município para aquela época do ano. Essa definição
          não equivale a uma declaração oficial de epidemia.
        </p>
        <strong>O que este mapa não mostra</strong>
        <p>
          Um alerta pode não se confirmar, e o modelo pode deixar de indicar
          situações de risco elevado. A indicação não é uma previsão do número
          de casos nem da chance individual de contrair dengue.
        </p>
        <p>
          Para comparar a indicação com o que foi observado na semana futura,
          consulte a página <Link href="/predicao">Resultados do modelo</Link>.
        </p>
      </section>
    </div>
  );
}
