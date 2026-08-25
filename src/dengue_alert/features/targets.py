"""Constrói o alvo epidemiológico e seus horizontes preditivos."""

from collections.abc import Iterable

import pandas as pd

ROLLING_CASE_WEEKS = 4
SEASONAL_RADIUS_WEEKS = 4
MINIMUM_PRIOR_YEARS = 2
MINIMUM_HISTORICAL_OBSERVATIONS = 12
TARGET_QUANTILE = 0.90
DEFAULT_HORIZONS = (1, 2, 3, 4)

TARGET_COLUMN = "risco_elevado"
THRESHOLD_COLUMN = "limiar_sazonal_p90"
HISTORICAL_COUNT_COLUMN = "observacoes_historicas_sazonais"


def _require_columns(
    dataframe: pd.DataFrame,
    required_columns: Iterable[str],
) -> None:
    """Falha explicitamente quando colunas obrigatórias não estão disponíveis."""
    missing = sorted(set(required_columns) - set(dataframe.columns))

    if missing:
        raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(missing))


def _validate_unique_weekly_keys(
    dataframe: pd.DataFrame,
) -> None:
    """Valida unicidade por município e semana epidemiológica."""
    key = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "semana_epidemiologica",
    ]

    duplicated = int(dataframe.duplicated(key).sum())

    if duplicated:
        raise ValueError(
            f"Foram encontradas {duplicated:,} chaves município-semana duplicadas."
        )


def normalize_ibge_code(series: pd.Series) -> pd.Series:
    """Normaliza códigos IBGE como texto de sete dígitos."""
    return series.astype("string").str.strip().str.zfill(7)


def calculate_four_week_incidence(
    dataframe: pd.DataFrame,
    rolling_weeks: int = ROLLING_CASE_WEEKS,
) -> pd.DataFrame:
    """Calcula casos e incidência acumulados nas semanas mais recentes."""
    _require_columns(
        dataframe,
        [
            "codigo_ibge_7",
            "data_inicio_semana",
            "casos_provaveis",
            "populacao",
        ],
    )

    if rolling_weeks < 1:
        raise ValueError("A janela móvel deve possuir pelo menos uma semana.")

    result = dataframe.copy()

    result["data_inicio_semana"] = pd.to_datetime(result["data_inicio_semana"])

    result = result.sort_values(
        [
            "codigo_ibge_7",
            "data_inicio_semana",
        ]
    ).reset_index(drop=True)

    invalid_population = result["populacao"].notna() & result["populacao"].le(0)

    if invalid_population.any():
        raise ValueError("A população deve ser positiva para calcular incidência.")

    result["casos_4s"] = result.groupby(
        "codigo_ibge_7",
        observed=True,
        sort=False,
    )["casos_provaveis"].transform(
        lambda series: series.rolling(
            window=rolling_weeks,
            min_periods=rolling_weeks,
        ).sum()
    )

    result["incidencia_4s_100mil"] = result["casos_4s"] / result["populacao"] * 100_000

    return result


def seasonal_week_window(
    target_week: int,
    weeks_in_source_year: int,
    radius: int = SEASONAL_RADIUS_WEEKS,
) -> list[int]:
    """Retorna semanas sazonais vizinhas com transição circular entre anos."""
    if target_week < 1:
        raise ValueError("A semana-alvo deve ser maior ou igual a 1.")

    if weeks_in_source_year < 1:
        raise ValueError("O ano histórico deve possuir pelo menos uma semana.")

    if radius < 0:
        raise ValueError("O raio sazonal não pode ser negativo.")

    center_week = min(
        target_week,
        weeks_in_source_year,
    )

    return sorted(
        {
            ((center_week - 1 + offset) % weeks_in_source_year) + 1
            for offset in range(-radius, radius + 1)
        }
    )


def calculate_seasonal_p90_threshold(
    dataframe: pd.DataFrame,
    *,
    quantile: float = TARGET_QUANTILE,
    radius: int = SEASONAL_RADIUS_WEEKS,
    minimum_prior_years: int = MINIMUM_PRIOR_YEARS,
    minimum_historical_observations: int = (MINIMUM_HISTORICAL_OBSERVATIONS),
) -> pd.DataFrame:
    """Calcula o limiar sazonal usando exclusivamente anos anteriores."""
    _require_columns(
        dataframe,
        [
            "codigo_ibge_7",
            "ano_epidemiologico",
            "semana_epidemiologica",
            "incidencia_4s_100mil",
        ],
    )

    if not 0 < quantile < 1:
        raise ValueError("O quantil deve estar estritamente entre 0 e 1.")

    if minimum_prior_years < 1:
        raise ValueError("O mínimo de anos anteriores deve ser pelo menos 1.")

    if minimum_historical_observations < 1:
        raise ValueError("O mínimo de observações históricas deve ser pelo menos 1.")

    result = dataframe.copy()

    result[THRESHOLD_COLUMN] = float("nan")
    result[HISTORICAL_COUNT_COLUMN] = float("nan")

    weeks_per_year = (
        result.groupby(
            "ano_epidemiologico",
            observed=True,
        )["semana_epidemiologica"]
        .max()
        .astype(int)
        .to_dict()
    )

    lookup: dict[tuple[int, int], pd.DataFrame] = {}

    for (year, week), group in result.groupby(
        [
            "ano_epidemiologico",
            "semana_epidemiologica",
        ],
        observed=True,
    ):
        lookup[(int(year), int(week))] = (
            group[
                [
                    "codigo_ibge_7",
                    "incidencia_4s_100mil",
                ]
            ]
            .dropna(subset=["incidencia_4s_100mil"])
            .copy()
        )

    years = sorted(int(year) for year in result["ano_epidemiologico"].unique())

    for target_year in years:
        prior_years = [year for year in years if year < target_year]

        if len(prior_years) < minimum_prior_years:
            continue

        target_weeks = sorted(
            int(week)
            for week in result.loc[
                result["ano_epidemiologico"] == target_year,
                "semana_epidemiologica",
            ].unique()
        )

        for target_week in target_weeks:
            historical_parts = []

            for source_year in prior_years:
                source_weeks = seasonal_week_window(
                    target_week=target_week,
                    weeks_in_source_year=(weeks_per_year[source_year]),
                    radius=radius,
                )

                for source_week in source_weeks:
                    part = lookup.get(
                        (
                            source_year,
                            source_week,
                        )
                    )

                    if part is not None and not part.empty:
                        historical_parts.append(part)

            if not historical_parts:
                continue

            historical = pd.concat(
                historical_parts,
                ignore_index=True,
            )

            grouped = historical.groupby(
                "codigo_ibge_7",
                observed=True,
            )["incidencia_4s_100mil"]

            counts = grouped.count()
            threshold = grouped.quantile(quantile)

            valid_codes = counts.loc[counts >= minimum_historical_observations].index

            counts = counts.loc[counts.index.intersection(valid_codes)]

            threshold = threshold.loc[threshold.index.intersection(valid_codes)]

            target_mask = (result["ano_epidemiologico"] == target_year) & (
                result["semana_epidemiologica"] == target_week
            )

            target_codes = result.loc[
                target_mask,
                "codigo_ibge_7",
            ]

            result.loc[
                target_mask,
                THRESHOLD_COLUMN,
            ] = target_codes.map(threshold)

            result.loc[
                target_mask,
                HISTORICAL_COUNT_COLUMN,
            ] = target_codes.map(counts)

    return result


def add_risk_label(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Cria o alvo binário usando comparação estrita com o P90 sazonal."""
    _require_columns(
        dataframe,
        [
            "incidencia_4s_100mil",
            THRESHOLD_COLUMN,
        ],
    )

    result = dataframe.copy()

    eligible = result["incidencia_4s_100mil"].notna() & result[THRESHOLD_COLUMN].notna()

    target = pd.Series(
        pd.NA,
        index=result.index,
        dtype="boolean",
    )

    target.loc[eligible] = (
        result.loc[
            eligible,
            "incidencia_4s_100mil",
        ]
        > result.loc[
            eligible,
            THRESHOLD_COLUMN,
        ]
    ).to_numpy()

    result[TARGET_COLUMN] = target

    return result


def build_epidemiological_target(
    dataframe: pd.DataFrame,
    *,
    modelable_only: bool = True,
) -> pd.DataFrame:
    """Constrói a definição oficial de risco epidemiológico elevado."""
    _require_columns(
        dataframe,
        [
            "codigo_ibge_7",
            "ano_epidemiologico",
            "semana_epidemiologica",
            "data_inicio_semana",
            "casos_provaveis",
            "populacao",
        ],
    )

    result = dataframe.copy()

    if modelable_only:
        _require_columns(
            result,
            ["modelavel_era5_land"],
        )

        result = result.loc[result["modelavel_era5_land"]].copy()

    result["codigo_ibge_7"] = normalize_ibge_code(result["codigo_ibge_7"])

    result["data_inicio_semana"] = pd.to_datetime(result["data_inicio_semana"])

    result = result.sort_values(
        [
            "codigo_ibge_7",
            "data_inicio_semana",
        ]
    ).reset_index(drop=True)

    _validate_unique_weekly_keys(result)

    result = calculate_four_week_incidence(result)

    result = calculate_seasonal_p90_threshold(result)

    result = add_risk_label(result)

    return result


def build_horizon_targets(
    dataframe: pd.DataFrame,
    *,
    start_year: int,
    end_year: int,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
) -> pd.DataFrame:
    """Cria alvos futuros sem permitir cruzamento da partição temporal."""
    _require_columns(
        dataframe,
        [
            "codigo_ibge_7",
            "ano_epidemiologico",
            "semana_epidemiologica",
            "data_inicio_semana",
            TARGET_COLUMN,
        ],
    )

    if start_year > end_year:
        raise ValueError("O ano inicial não pode ser posterior ao ano final.")

    normalized_horizons = tuple(sorted({int(horizon) for horizon in horizons}))

    if not normalized_horizons:
        raise ValueError("Pelo menos um horizonte deve ser informado.")

    if normalized_horizons[0] < 1:
        raise ValueError("Todos os horizontes devem ser inteiros positivos.")

    result = dataframe.loc[
        dataframe["ano_epidemiologico"].between(
            start_year,
            end_year,
            inclusive="both",
        )
    ].copy()

    result["data_inicio_semana"] = pd.to_datetime(result["data_inicio_semana"])

    result = result.sort_values(
        [
            "codigo_ibge_7",
            "data_inicio_semana",
        ]
    ).reset_index(drop=True)

    _validate_unique_weekly_keys(result)

    grouped = result.groupby(
        "codigo_ibge_7",
        observed=True,
        sort=False,
    )

    for horizon in normalized_horizons:
        future_target = grouped[TARGET_COLUMN].shift(-horizon)

        future_date = grouped["data_inicio_semana"].shift(-horizon)

        expected_future_date = result["data_inicio_semana"] + pd.to_timedelta(
            7 * horizon,
            unit="D",
        )

        contiguous = future_date.eq(expected_future_date)

        result[f"target_h{horizon}"] = future_target.where(contiguous).astype("boolean")

    return result
