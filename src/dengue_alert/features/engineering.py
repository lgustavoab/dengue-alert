"""Constrói as features preditivas do projeto Dengue Alert."""

from collections.abc import Iterable
from math import pi

import numpy as np
import pandas as pd

from dengue_alert.features.targets import (
    TARGET_COLUMN,
    THRESHOLD_COLUMN,
)

EPIDEMIOLOGICAL_LAGS = tuple(range(1, 9))
CLIMATE_LAGS = tuple(range(9))
ROLLING_WINDOWS = (2, 4, 8)

CLIMATE_SOURCE_COLUMNS = (
    "temperatura_media_c",
    "umidade_relativa_media_pct",
    "precipitacao_total_mm",
)

IDENTIFICATION_COLUMNS = (
    "codigo_ibge_7",
    "ano_epidemiologico",
    "semana_epidemiologica",
    "data_inicio_semana",
)

EPIDEMIOLOGICAL_FEATURES = (
    "incidencia_100mil",
    *(f"incidencia_100mil_lag_{lag}" for lag in EPIDEMIOLOGICAL_LAGS),
    "incidencia_media_2s",
    "incidencia_media_4s",
    "incidencia_media_8s",
    "incidencia_4s_100mil",
    "incidencia_4s_lag_1",
    "incidencia_4s_lag_4",
    "delta_incidencia_4s_1s",
    "delta_incidencia_4s_4s",
    THRESHOLD_COLUMN,
    "margem_limiar_p90",
    TARGET_COLUMN,
    "semana_sin",
    "semana_cos",
    "log_populacao",
)

CLIMATE_FEATURES = (
    *(f"temperatura_media_c_lag_{lag}" for lag in CLIMATE_LAGS),
    *(f"umidade_relativa_media_pct_lag_{lag}" for lag in CLIMATE_LAGS),
    *(f"precipitacao_total_mm_lag_{lag}" for lag in CLIMATE_LAGS),
    "temperatura_media_media_2s",
    "temperatura_media_media_4s",
    "temperatura_media_media_8s",
    "umidade_relativa_media_2s",
    "umidade_relativa_media_4s",
    "umidade_relativa_media_8s",
    "precipitacao_acumulada_2s",
    "precipitacao_acumulada_4s",
    "precipitacao_acumulada_8s",
)

SPATIAL_FEATURES = (
    "latitude_sede",
    "longitude_sede",
)

EPIDEMIOLOGICAL_CLIMATE_FEATURES = (
    *EPIDEMIOLOGICAL_FEATURES,
    *CLIMATE_FEATURES,
)

EPIDEMIOLOGICAL_CLIMATE_SPATIAL_FEATURES = (
    *EPIDEMIOLOGICAL_FEATURES,
    *CLIMATE_FEATURES,
    *SPATIAL_FEATURES,
)


def require_columns(
    dataframe: pd.DataFrame,
    required_columns: Iterable[str],
) -> None:
    """Falha explicitamente quando colunas obrigatórias não estão disponíveis."""
    missing = sorted(set(required_columns) - set(dataframe.columns))

    if missing:
        raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(missing))


def validate_unique_weekly_keys(
    dataframe: pd.DataFrame,
) -> None:
    """Valida unicidade por município e semana epidemiológica."""
    key = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "semana_epidemiologica",
    ]

    duplicates = int(dataframe.duplicated(key).sum())

    if duplicates:
        raise ValueError(
            f"Foram encontradas {duplicates:,} chaves município-semana duplicadas."
        )


def validate_weekly_continuity(
    dataframe: pd.DataFrame,
) -> None:
    """Impede que lags por posição atravessem lacunas temporais."""
    grouped = dataframe.groupby(
        "codigo_ibge_7",
        observed=True,
        sort=False,
    )

    previous_date = grouped["data_inicio_semana"].shift(1)

    gap_days = (dataframe["data_inicio_semana"] - previous_date).dt.days

    invalid = previous_date.notna() & gap_days.ne(7)

    if invalid.any():
        examples = dataframe.loc[
            invalid,
            [
                "codigo_ibge_7",
                "data_inicio_semana",
            ],
        ].head(5)

        raise ValueError(
            "Foram encontradas lacunas temporais "
            "dentro de séries municipais. "
            "Lags por posição não podem ser "
            "calculados com segurança. Exemplos: "
            f"{examples.to_dict(orient='records')}"
        )


def prepare_chronological_panel(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Normaliza e ordena o painel antes da engenharia temporal."""
    require_columns(
        dataframe,
        [
            *IDENTIFICATION_COLUMNS,
            "incidencia_100mil",
            "incidencia_4s_100mil",
            THRESHOLD_COLUMN,
            TARGET_COLUMN,
            "populacao",
            *CLIMATE_SOURCE_COLUMNS,
            *SPATIAL_FEATURES,
        ],
    )

    result = dataframe.copy()

    result["codigo_ibge_7"] = (
        result["codigo_ibge_7"].astype("string").str.strip().str.zfill(7)
    )

    result["data_inicio_semana"] = pd.to_datetime(result["data_inicio_semana"])

    result = result.sort_values(
        [
            "codigo_ibge_7",
            "data_inicio_semana",
        ]
    ).reset_index(drop=True)

    validate_unique_weekly_keys(result)
    validate_weekly_continuity(result)

    return result


def add_epidemiological_lags(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Adiciona lags retrospectivos da incidência semanal."""
    result = dataframe.copy()

    grouped = result.groupby(
        "codigo_ibge_7",
        observed=True,
        sort=False,
    )

    for lag in EPIDEMIOLOGICAL_LAGS:
        result[f"incidencia_100mil_lag_{lag}"] = grouped["incidencia_100mil"].shift(lag)

    return result


def add_epidemiological_rollings(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Adiciona médias móveis retrospectivas da incidência."""
    result = dataframe.copy()

    grouped = result.groupby(
        "codigo_ibge_7",
        observed=True,
        sort=False,
    )

    for window in ROLLING_WINDOWS:
        result[f"incidencia_media_{window}s"] = grouped["incidencia_100mil"].transform(
            lambda series, window=window: series.rolling(
                window=window,
                min_periods=window,
            ).mean()
        )

    return result


def add_epidemiological_trends(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Adiciona lags e deltas da incidência acumulada de quatro semanas."""
    result = dataframe.copy()

    grouped = result.groupby(
        "codigo_ibge_7",
        observed=True,
        sort=False,
    )

    result["incidencia_4s_lag_1"] = grouped["incidencia_4s_100mil"].shift(1)

    result["incidencia_4s_lag_4"] = grouped["incidencia_4s_100mil"].shift(4)

    result["delta_incidencia_4s_1s"] = (
        result["incidencia_4s_100mil"] - result["incidencia_4s_lag_1"]
    )

    result["delta_incidencia_4s_4s"] = (
        result["incidencia_4s_100mil"] - result["incidencia_4s_lag_4"]
    )

    result["margem_limiar_p90"] = (
        result["incidencia_4s_100mil"] - result[THRESHOLD_COLUMN]
    )

    return result


def add_climate_lags(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Adiciona valores climáticos contemporâneos e retrospectivos."""
    result = dataframe.copy()

    grouped = result.groupby(
        "codigo_ibge_7",
        observed=True,
        sort=False,
    )

    for column in CLIMATE_SOURCE_COLUMNS:
        for lag in CLIMATE_LAGS:
            feature_name = f"{column}_lag_{lag}"

            if lag == 0:
                result[feature_name] = result[column]
            else:
                result[feature_name] = grouped[column].shift(lag)

    return result


def add_climate_rollings(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Adiciona resumos climáticos móveis terminando na semana atual."""
    result = dataframe.copy()

    grouped = result.groupby(
        "codigo_ibge_7",
        observed=True,
        sort=False,
    )

    for window in ROLLING_WINDOWS:
        result[f"temperatura_media_media_{window}s"] = grouped[
            "temperatura_media_c"
        ].transform(
            lambda series, window=window: series.rolling(
                window=window,
                min_periods=window,
            ).mean()
        )

        result[f"umidade_relativa_media_{window}s"] = grouped[
            "umidade_relativa_media_pct"
        ].transform(
            lambda series, window=window: series.rolling(
                window=window,
                min_periods=window,
            ).mean()
        )

        result[f"precipitacao_acumulada_{window}s"] = grouped[
            "precipitacao_total_mm"
        ].transform(
            lambda series, window=window: series.rolling(
                window=window,
                min_periods=window,
            ).sum()
        )

    return result


def add_temporal_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Representa a semana epidemiológica como variável circular."""
    result = dataframe.copy()

    invalid_week = ~result["semana_epidemiologica"].between(
        1,
        53,
        inclusive="both",
    )

    if invalid_week.any():
        raise ValueError(
            "Foram encontradas semanas epidemiológicas fora do intervalo 1–53."
        )

    angle = 2 * pi * (result["semana_epidemiologica"] - 1) / 53

    result["semana_sin"] = np.sin(angle)
    result["semana_cos"] = np.cos(angle)

    return result


def add_population_feature(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Adiciona transformação logarítmica da população."""
    result = dataframe.copy()

    invalid_population = result["populacao"].isna() | result["populacao"].le(0)

    if invalid_population.any():
        raise ValueError(
            "A população deve estar disponível e ser positiva para todas as linhas."
        )

    result["log_populacao"] = np.log1p(result["populacao"])

    return result


def build_model_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Constrói todas as features da primeira especificação oficial."""
    result = prepare_chronological_panel(dataframe)

    result = add_epidemiological_lags(result)

    result = add_epidemiological_rollings(result)

    result = add_epidemiological_trends(result)

    result = add_climate_lags(result)

    result = add_climate_rollings(result)

    result = add_temporal_features(result)

    result = add_population_feature(result)

    return result
