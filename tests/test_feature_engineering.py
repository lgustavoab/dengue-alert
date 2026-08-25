"""Testes da engenharia de features temporais."""

import numpy as np
import pandas as pd
import pytest

from dengue_alert.features.engineering import (
    CLIMATE_FEATURES,
    EPIDEMIOLOGICAL_FEATURES,
    add_climate_lags,
    add_climate_rollings,
    add_epidemiological_lags,
    add_epidemiological_rollings,
    add_epidemiological_trends,
    add_population_feature,
    add_temporal_features,
    build_model_features,
    prepare_chronological_panel,
)


def make_weekly_dataframe(
    periods: int = 10,
) -> pd.DataFrame:
    """Cria série municipal semanal sintética para testes."""
    dates = pd.date_range(
        "2024-01-07",
        periods=periods,
        freq="7D",
    )

    incidence = [float(value) for value in range(1, periods + 1)]

    incidence_4s = [float(value * 10) for value in range(1, periods + 1)]

    return pd.DataFrame(
        {
            "codigo_ibge_7": ["1234567"] * periods,
            "ano_epidemiologico": [2024] * periods,
            "semana_epidemiologica": list(range(1, periods + 1)),
            "data_inicio_semana": dates,
            "incidencia_100mil": incidence,
            "incidencia_4s_100mil": incidence_4s,
            "limiar_sazonal_p90": [50.0] * periods,
            "risco_elevado": pd.Series(
                [False] * periods,
                dtype="boolean",
            ),
            "populacao": [100_000] * periods,
            "temperatura_media_c": [20.0 + value for value in range(periods)],
            "umidade_relativa_media_pct": [60.0 + value for value in range(periods)],
            "precipitacao_total_mm": [float(value) for value in range(periods)],
            "latitude_sede": [-21.0] * periods,
            "longitude_sede": [-50.0] * periods,
        }
    )


def test_prepare_panel_rejects_weekly_gap() -> None:
    """Uma lacuna temporal deve impedir lags por posição."""
    dataframe = make_weekly_dataframe(periods=4)

    dataframe.loc[
        2,
        "data_inicio_semana",
    ] = pd.Timestamp("2024-01-28")

    with pytest.raises(
        ValueError,
        match="lacunas temporais",
    ):
        prepare_chronological_panel(dataframe)


def test_epidemiological_lags_use_only_past() -> None:
    """Lags epidemiológicos devem apontar exclusivamente para semanas anteriores."""
    dataframe = make_weekly_dataframe()

    result = add_epidemiological_lags(dataframe)

    assert pd.isna(
        result.loc[
            0,
            "incidencia_100mil_lag_1",
        ]
    )

    assert (
        result.loc[
            4,
            "incidencia_100mil_lag_1",
        ]
        == 4.0
    )

    assert (
        result.loc[
            8,
            "incidencia_100mil_lag_8",
        ]
        == 1.0
    )


def test_epidemiological_rollings_end_at_current_week() -> None:
    """Médias móveis devem utilizar somente semana atual e passado."""
    dataframe = make_weekly_dataframe()

    result = add_epidemiological_rollings(dataframe)

    assert result.loc[
        1,
        "incidencia_media_2s",
    ] == pytest.approx(1.5)

    assert result.loc[
        3,
        "incidencia_media_4s",
    ] == pytest.approx(2.5)

    assert result.loc[
        7,
        "incidencia_media_8s",
    ] == pytest.approx(4.5)


def test_epidemiological_trends_are_retrospective() -> None:
    """Deltas epidemiológicos devem comparar a semana atual apenas com o passado."""
    dataframe = make_weekly_dataframe()

    result = add_epidemiological_trends(dataframe)

    assert (
        result.loc[
            4,
            "incidencia_4s_lag_1",
        ]
        == 40.0
    )

    assert (
        result.loc[
            4,
            "incidencia_4s_lag_4",
        ]
        == 10.0
    )

    assert (
        result.loc[
            4,
            "delta_incidencia_4s_1s",
        ]
        == 10.0
    )

    assert (
        result.loc[
            4,
            "delta_incidencia_4s_4s",
        ]
        == 40.0
    )

    assert (
        result.loc[
            4,
            "margem_limiar_p90",
        ]
        == 0.0
    )


def test_climate_lags_include_current_as_lag_zero() -> None:
    """Lag zero climático deve representar a própria semana t."""
    dataframe = make_weekly_dataframe()

    result = add_climate_lags(dataframe)

    assert (
        result.loc[
            5,
            "temperatura_media_c_lag_0",
        ]
        == 25.0
    )

    assert (
        result.loc[
            5,
            "temperatura_media_c_lag_1",
        ]
        == 24.0
    )

    assert (
        result.loc[
            8,
            "precipitacao_total_mm_lag_8",
        ]
        == 0.0
    )


def test_climate_rollings_use_mean_and_precipitation_sum() -> None:
    """Temperatura e umidade usam média; precipitação usa soma."""
    dataframe = make_weekly_dataframe()

    result = add_climate_rollings(dataframe)

    assert result.loc[
        3,
        "temperatura_media_media_4s",
    ] == pytest.approx(21.5)

    assert result.loc[
        3,
        "umidade_relativa_media_4s",
    ] == pytest.approx(61.5)

    assert result.loc[
        3,
        "precipitacao_acumulada_4s",
    ] == pytest.approx(6.0)


def test_future_change_does_not_modify_past_features() -> None:
    """Alterar uma semana futura não pode modificar features de uma semana passada."""
    dataframe = make_weekly_dataframe()

    original = build_model_features(dataframe)

    modified = dataframe.copy()

    modified.loc[
        9,
        "incidencia_100mil",
    ] = 999_999.0

    modified.loc[
        9,
        "temperatura_media_c",
    ] = 999.0

    modified.loc[
        9,
        "umidade_relativa_media_pct",
    ] = 99.0

    modified.loc[
        9,
        "precipitacao_total_mm",
    ] = 999_999.0

    changed = build_model_features(modified)

    feature_columns = [
        *EPIDEMIOLOGICAL_FEATURES,
        *CLIMATE_FEATURES,
    ]

    pd.testing.assert_series_equal(
        original.loc[
            8,
            feature_columns,
        ],
        changed.loc[
            8,
            feature_columns,
        ],
        check_names=False,
    )


def test_temporal_features_are_cyclic() -> None:
    """SE1 e SE53 devem permanecer próximas na representação circular."""
    dataframe = pd.DataFrame(
        {
            "semana_epidemiologica": [
                1,
                53,
            ]
        }
    )

    result = add_temporal_features(dataframe)

    distance = np.sqrt(
        (result.loc[0, "semana_sin"] - result.loc[1, "semana_sin"]) ** 2
        + (result.loc[0, "semana_cos"] - result.loc[1, "semana_cos"]) ** 2
    )

    assert distance < 0.13


def test_population_feature_uses_log1p() -> None:
    """População deve ser transformada por log1p."""
    dataframe = pd.DataFrame(
        {
            "populacao": [
                100_000,
            ]
        }
    )

    result = add_population_feature(dataframe)

    assert result.loc[
        0,
        "log_populacao",
    ] == pytest.approx(np.log1p(100_000))


def test_build_model_features_creates_official_sets() -> None:
    """Pipeline completo deve produzir todos os conjuntos oficiais de features."""
    dataframe = make_weekly_dataframe()

    result = build_model_features(dataframe)

    for column in EPIDEMIOLOGICAL_FEATURES:
        assert column in result.columns

    for column in CLIMATE_FEATURES:
        assert column in result.columns
