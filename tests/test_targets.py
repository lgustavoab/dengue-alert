"""Testes da construção do alvo preditivo."""

import pandas as pd
import pytest

from dengue_alert.features.targets import (
    THRESHOLD_COLUMN,
    add_risk_label,
    build_horizon_targets,
    calculate_four_week_incidence,
    calculate_seasonal_p90_threshold,
    seasonal_week_window,
)


def test_seasonal_week_window_wraps_52_week_year() -> None:
    """A janela sazonal deve circular corretamente entre fim e início do ano."""
    weeks = seasonal_week_window(
        target_week=1,
        weeks_in_source_year=52,
        radius=4,
    )

    assert weeks == [
        1,
        2,
        3,
        4,
        5,
        49,
        50,
        51,
        52,
    ]


def test_seasonal_week_53_maps_to_52_week_source_year() -> None:
    """SE53 deve usar a vizinhança da última semana disponível em ano de 52."""
    weeks = seasonal_week_window(
        target_week=53,
        weeks_in_source_year=52,
        radius=4,
    )

    assert weeks == [
        1,
        2,
        3,
        4,
        48,
        49,
        50,
        51,
        52,
    ]


def test_four_week_incidence_uses_last_four_weeks() -> None:
    """A incidência móvel deve acumular exatamente quatro semanas."""
    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": ["1234567"] * 5,
            "data_inicio_semana": pd.date_range(
                "2024-01-07",
                periods=5,
                freq="7D",
            ),
            "casos_provaveis": [1, 2, 3, 4, 5],
            "populacao": [100_000] * 5,
        }
    )

    result = calculate_four_week_incidence(dataframe)

    assert result["casos_4s"].iloc[:3].isna().all()
    assert result.loc[3, "casos_4s"] == 10
    assert result.loc[4, "casos_4s"] == 14
    assert result.loc[3, "incidencia_4s_100mil"] == pytest.approx(10)
    assert result.loc[4, "incidencia_4s_100mil"] == pytest.approx(14)


def test_risk_label_uses_strict_greater_than() -> None:
    """Incidência igual ao limiar não deve ser classificada como elevada."""
    dataframe = pd.DataFrame(
        {
            "incidencia_4s_100mil": [10.0, 11.0],
            THRESHOLD_COLUMN: [10.0, 10.0],
        }
    )

    result = add_risk_label(dataframe)

    assert result["risco_elevado"].tolist() == [
        False,
        True,
    ]


def test_seasonal_threshold_uses_only_prior_years() -> None:
    """O valor do próprio ano-alvo não pode contaminar seu limiar histórico."""
    rows = []

    for year, incidence in [
        (2016, 1.0),
        (2017, 3.0),
        (2018, 999.0),
    ]:
        for week in range(1, 53):
            rows.append(
                {
                    "codigo_ibge_7": "1234567",
                    "ano_epidemiologico": year,
                    "semana_epidemiologica": week,
                    "incidencia_4s_100mil": incidence,
                }
            )

    dataframe = pd.DataFrame(rows)

    result = calculate_seasonal_p90_threshold(dataframe)

    row = result.loc[
        (result["ano_epidemiologico"] == 2018) & (result["semana_epidemiologica"] == 20)
    ].iloc[0]

    assert row[THRESHOLD_COLUMN] == 3.0
    assert row["observacoes_historicas_sazonais"] == 18


def test_horizon_targets_do_not_cross_partition_boundary() -> None:
    """Targets de desenvolvimento não podem utilizar outcomes do ano de teste."""
    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": ["1234567"] * 5,
            "ano_epidemiologico": [
                2024,
                2024,
                2024,
                2025,
                2025,
            ],
            "semana_epidemiologica": [
                50,
                51,
                52,
                1,
                2,
            ],
            "data_inicio_semana": pd.to_datetime(
                [
                    "2024-12-15",
                    "2024-12-22",
                    "2024-12-29",
                    "2025-01-05",
                    "2025-01-12",
                ]
            ),
            "risco_elevado": pd.Series(
                [
                    False,
                    True,
                    False,
                    True,
                    True,
                ],
                dtype="boolean",
            ),
        }
    )

    result = build_horizon_targets(
        dataframe,
        start_year=2024,
        end_year=2024,
        horizons=(1, 2),
    )

    assert len(result) == 3

    assert result["target_h1"].tolist() == [
        True,
        False,
        pd.NA,
    ]

    assert result["target_h2"].tolist() == [
        False,
        pd.NA,
        pd.NA,
    ]


def test_horizon_target_requires_weekly_continuity() -> None:
    """Um salto temporal não pode ser interpretado como horizonte de uma semana."""
    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": [
                "1234567",
                "1234567",
            ],
            "ano_epidemiologico": [
                2024,
                2024,
            ],
            "semana_epidemiologica": [
                1,
                3,
            ],
            "data_inicio_semana": pd.to_datetime(
                [
                    "2024-01-07",
                    "2024-01-21",
                ]
            ),
            "risco_elevado": pd.Series(
                [
                    False,
                    True,
                ],
                dtype="boolean",
            ),
        }
    )

    result = build_horizon_targets(
        dataframe,
        start_year=2024,
        end_year=2024,
        horizons=(1,),
    )

    assert result["target_h1"].isna().all()
