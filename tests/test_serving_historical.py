"""Testes dos contratos de serving histórico."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SERVING_SCRIPT = PROJECT_ROOT / "scripts" / "gerar_serving_historical.py"

SPEC = importlib.util.spec_from_file_location(
    "gerar_serving_historical",
    SERVING_SCRIPT,
)

if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Não foi possível carregar o script: {SERVING_SCRIPT}")

serving = importlib.util.module_from_spec(SPEC)

SPEC.loader.exec_module(serving)


def test_json_scalar_converts_numpy_and_missing_values() -> None:
    """Escalares NumPy e valores ausentes devem ser serializáveis."""
    assert serving.json_scalar(np.int64(10)) == 10

    assert serving.json_scalar(np.float64(2.5)) == 2.5

    assert serving.json_scalar(pd.NA) is None

    timestamp = pd.Timestamp("2025-03-16")

    assert serving.json_scalar(timestamp) == timestamp.isoformat()


def test_normalize_identifiers_preserves_codes_as_strings() -> None:
    """Códigos territoriais devem manter largura e tipo estáveis."""
    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": [
                "123456",
                "7654321",
            ],
            "codigo_uf_ibge": [
                "1",
                "35",
            ],
        }
    )

    result = serving.normalize_identifiers(dataframe)

    assert result["codigo_ibge_7"].tolist() == [
        "0123456",
        "7654321",
    ]

    assert result["codigo_uf_ibge"].tolist() == [
        "01",
        "35",
    ]


def test_build_panorama_annual_orders_years(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Panorama anual deve permanecer ordenado de 2016 a 2025."""
    dataframe = pd.DataFrame(
        {
            "ano_epidemiologico": list(
                reversed(
                    range(
                        2016,
                        2026,
                    )
                )
            ),
            "casos_provaveis": [1] * 10,
            "incidencia_anual_100mil": [1.0] * 10,
        }
    )

    monkeypatch.setattr(
        serving,
        "load_csv",
        lambda *args, **kwargs: dataframe.copy(),
    )

    contract = serving.build_panorama_annual()

    years = [row["ano_epidemiologico"] for row in contract["data"]]

    assert contract["count"] == 10

    assert years == list(
        range(
            2016,
            2026,
        )
    )


def test_build_seasonality_regional_uses_stable_region_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sazonalidade regional deve obedecer à ordem definida de regiões."""
    dataframe = pd.DataFrame(
        {
            "regiao": [
                "Sul",
                "Norte",
                "Sul",
                "Norte",
            ],
            "semana_epidemiologica": [
                2,
                2,
                1,
                1,
            ],
            "incidencia_media_100mil": [
                4.0,
                2.0,
                3.0,
                1.0,
            ],
            "incidencia_mediana_100mil": [
                4.0,
                2.0,
                3.0,
                1.0,
            ],
            "incidencia_q25_100mil": [
                3.0,
                1.0,
                2.0,
                0.5,
            ],
            "incidencia_q75_100mil": [
                5.0,
                3.0,
                4.0,
                1.5,
            ],
        }
    )

    monkeypatch.setattr(
        serving,
        "REGIONS",
        [
            "Norte",
            "Sul",
        ],
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_SEASONALITY_REGIONAL_ROWS",
        4,
    )

    monkeypatch.setattr(
        serving,
        "load_csv",
        lambda *args, **kwargs: dataframe.copy(),
    )

    contract = serving.build_seasonality_regional()

    order = [
        (
            row["regiao"],
            row["semana_epidemiologica"],
        )
        for row in contract["data"]
    ]

    assert order == [
        (
            "Norte",
            1,
        ),
        (
            "Norte",
            2,
        ),
        (
            "Sul",
            1,
        ),
        (
            "Sul",
            2,
        ),
    ]


def test_build_spatial_municipalities_normalizes_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Serving espacial deve normalizar códigos e nomes territoriais."""
    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": [
                "123456",
                "7654321",
            ],
            "nome_municipio_ibge": [
                "Município A",
                "Município B",
            ],
            "codigo_uf_ibge": [
                "1",
                "35",
            ],
            "nome_uf_ibge": [
                "Estado A",
                "São Paulo",
            ],
            "regiao": [
                "Norte",
                "Sudeste",
            ],
            "casos_periodo": [
                100,
                200,
            ],
            "incidencia_mediana_anual_100mil": [
                50.0,
                100.0,
            ],
        }
    )

    monkeypatch.setattr(
        serving,
        "REGIONS",
        [
            "Norte",
            "Sudeste",
        ],
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_MUNICIPALITIES",
        2,
    )

    monkeypatch.setattr(
        serving,
        "load_csv",
        lambda *args, **kwargs: dataframe.copy(),
    )

    contract = serving.build_spatial_municipalities()

    first = contract["data"][0]

    second = contract["data"][1]

    assert contract["count"] == 2

    assert first["codigo_ibge_7"] == "0123456"

    assert first["codigo_uf_ibge"] == "01"

    assert first["nome_municipio"] == "Município A"

    assert first["nome_uf"] == "Estado A"

    assert second["codigo_ibge_7"] == "7654321"


def test_build_municipality_index_marks_risk_availability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Índice deve manter todos os territórios e marcar cobertura de risco."""
    monkeypatch.setattr(
        serving,
        "EXPECTED_MUNICIPALITIES",
        3,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_RISK_MUNICIPALITIES",
        2,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_RISK_UNAVAILABLE_MUNICIPALITIES",
        1,
    )

    spatial_contract = {
        "data": [
            {
                "codigo_ibge_7": "1111111",
                "nome_municipio": "Município A",
                "codigo_uf_ibge": "11",
                "nome_uf": "Estado A",
                "regiao": "Norte",
                "anos_disponiveis": 10,
            },
            {
                "codigo_ibge_7": "2222222",
                "nome_municipio": "Município B",
                "codigo_uf_ibge": "22",
                "nome_uf": "Estado B",
                "regiao": "Nordeste",
                "anos_disponiveis": 10,
            },
            {
                "codigo_ibge_7": "3333333",
                "nome_municipio": "Município C",
                "codigo_uf_ibge": "33",
                "nome_uf": "Estado C",
                "regiao": "Sudeste",
                "anos_disponiveis": 10,
            },
        ]
    }

    risk_contract = {
        "data": [
            {
                "codigo_ibge_7": "1111111",
            },
            {
                "codigo_ibge_7": "3333333",
            },
        ]
    }

    contract = serving.build_municipality_index(
        spatial_contract,
        risk_contract,
    )

    assert contract["count"] == 3

    assert contract["risk_history"] == {
        "available": 2,
        "unavailable": 1,
    }

    unavailable = [
        row for row in contract["data"] if not row["risco_historico_disponivel"]
    ]

    assert len(unavailable) == 1

    assert unavailable[0]["codigo_ibge_7"] == "2222222"


def test_build_municipality_index_rejects_unknown_risk_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Risco não pode conter território inexistente no contrato espacial."""
    monkeypatch.setattr(
        serving,
        "EXPECTED_MUNICIPALITIES",
        1,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_RISK_MUNICIPALITIES",
        1,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_RISK_UNAVAILABLE_MUNICIPALITIES",
        0,
    )

    spatial_contract = {
        "data": [
            {
                "codigo_ibge_7": "1111111",
                "nome_municipio": "Município A",
                "codigo_uf_ibge": "11",
                "nome_uf": "Estado A",
                "regiao": "Norte",
                "anos_disponiveis": 10,
            }
        ]
    }

    risk_contract = {
        "data": [
            {
                "codigo_ibge_7": "9999999",
            }
        ]
    }

    with pytest.raises(
        ValueError,
        match="ausentes no contrato espacial",
    ):
        serving.build_municipality_index(
            spatial_contract,
            risk_contract,
        )


def test_build_episode_duration_preserves_summary_and_distribution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Distribuição de episódios deve preservar quantidade e semanas."""
    dataframe = pd.DataFrame(
        {
            "duracao_semanas": [
                1,
                1,
                1,
                1,
            ]
        }
    )

    monkeypatch.setattr(
        serving,
        "load_csv",
        lambda *args, **kwargs: dataframe.copy(),
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_EPISODES",
        4,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_RISK_WEEKS",
        4,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_EPISODE_MIN",
        1,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_EPISODE_P25",
        1,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_EPISODE_MEDIAN",
        1,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_EPISODE_P75",
        1,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_EPISODE_P90",
        1,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_EPISODE_P95",
        1,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_EPISODE_P99",
        1,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_EPISODE_MAX",
        1,
    )

    contract = serving.build_episode_duration()

    summary = contract["summary"]

    assert summary["quantidade_episodios"] == 4

    assert summary["semanas_risco"] == 4

    assert summary["mediana"] == 1.0

    assert summary["maximo"] == 1

    assert contract["distribution"] == [
        {
            "duracao_semanas": 1,
            "episodios": 4,
        }
    ]


def test_build_climate_national_preserves_variable_and_lag_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contrato climático nacional deve usar ordem determinística."""
    dataframe = pd.DataFrame(
        {
            "variavel_climatica": [
                "precipitacao",
                "temperatura",
                "precipitacao",
                "temperatura",
            ],
            "lag_semanas": [
                1,
                1,
                0,
                0,
            ],
            "municipios_correlacao_valida": [
                10,
                10,
                10,
                10,
            ],
            "correlacao_mediana": [
                0.4,
                0.2,
                0.3,
                0.1,
            ],
            "correlacao_p25": [
                0.2,
                0.1,
                0.1,
                0.0,
            ],
            "correlacao_p75": [
                0.5,
                0.3,
                0.4,
                0.2,
            ],
        }
    )

    monkeypatch.setattr(
        serving,
        "CLIMATE_VARIABLES",
        [
            "temperatura",
            "precipitacao",
        ],
    )

    monkeypatch.setattr(
        serving,
        "CLIMATE_LAGS",
        [
            0,
            1,
        ],
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CLIMATE_NATIONAL_ROWS",
        4,
    )

    monkeypatch.setattr(
        serving,
        "load_csv",
        lambda *args, **kwargs: dataframe.copy(),
    )

    contract = serving.build_climate_national()

    order = [
        (
            row["variavel_climatica"],
            row["lag_semanas"],
        )
        for row in contract["data"]
    ]

    assert order == [
        (
            "temperatura",
            0,
        ),
        (
            "temperatura",
            1,
        ),
        (
            "precipitacao",
            0,
        ),
        (
            "precipitacao",
            1,
        ),
    ]


def test_build_climate_regional_preserves_region_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contrato climático regional deve ordenar região, variável e lag."""
    dataframe = pd.DataFrame(
        {
            "regiao": [
                "Sul",
                "Norte",
                "Sul",
                "Norte",
            ],
            "variavel_climatica": [
                "temperatura",
                "temperatura",
                "temperatura",
                "temperatura",
            ],
            "lag_semanas": [
                1,
                1,
                0,
                0,
            ],
            "municipios_correlacao_valida": [
                10,
                10,
                10,
                10,
            ],
            "correlacao_mediana": [
                0.4,
                0.2,
                0.3,
                0.1,
            ],
            "correlacao_p25": [
                0.2,
                0.1,
                0.1,
                0.0,
            ],
            "correlacao_p75": [
                0.5,
                0.3,
                0.4,
                0.2,
            ],
        }
    )

    monkeypatch.setattr(
        serving,
        "REGIONS",
        [
            "Norte",
            "Sul",
        ],
    )

    monkeypatch.setattr(
        serving,
        "CLIMATE_VARIABLES",
        [
            "temperatura",
        ],
    )

    monkeypatch.setattr(
        serving,
        "CLIMATE_LAGS",
        [
            0,
            1,
        ],
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CLIMATE_REGIONAL_ROWS",
        4,
    )

    monkeypatch.setattr(
        serving,
        "load_csv",
        lambda *args, **kwargs: dataframe.copy(),
    )

    contract = serving.build_climate_regional()

    order = [
        (
            row["regiao"],
            row["lag_semanas"],
        )
        for row in contract["data"]
    ]

    assert order == [
        (
            "Norte",
            0,
        ),
        (
            "Norte",
            1,
        ),
        (
            "Sul",
            0,
        ),
        (
            "Sul",
            1,
        ),
    ]


def test_validate_cross_contracts_accepts_consistent_contracts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validação cruzada deve aceitar contratos mutuamente consistentes."""
    monkeypatch.setattr(
        serving,
        "EXPECTED_MUNICIPALITIES",
        3,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_RISK_MUNICIPALITIES",
        2,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_RISK_UNAVAILABLE_MUNICIPALITIES",
        1,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_EPISODES",
        4,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_RISK_WEEKS",
        4,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CLIMATE_NATIONAL_ROWS",
        2,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CLIMATE_REGIONAL_ROWS",
        4,
    )

    contracts = {
        serving.SERVING_DIR / "panorama" / "annual.json": {
            "data": [
                {
                    "casos_provaveis": 16_294_913,
                }
            ]
        },
        serving.SERVING_DIR / "panorama" / "weekly.json": {
            "data": [
                {
                    "casos_provaveis": 16_294_913,
                }
            ]
        },
        serving.SERVING_DIR / "spatial" / "municipalities.json": {
            "count": 3,
        },
        serving.SERVING_DIR / "risk_dynamics" / "municipalities.json": {
            "count": 2,
        },
        serving.SERVING_DIR / "municipality" / "index.json": {
            "count": 3,
            "risk_history": {
                "available": 2,
                "unavailable": 1,
            },
        },
        serving.SERVING_DIR / "risk_dynamics" / "episode_duration.json": {
            "summary": {
                "quantidade_episodios": 4,
                "semanas_risco": 4,
            }
        },
        serving.SERVING_DIR / "climate" / "national_lags.json": {
            "count": 2,
        },
        serving.SERVING_DIR / "climate" / "regional_lags.json": {
            "count": 4,
        },
    }

    serving.validate_cross_contracts(contracts)


def test_validate_cross_contracts_rejects_wrong_municipality_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validação deve detectar inconsistência na cobertura do índice."""
    monkeypatch.setattr(
        serving,
        "EXPECTED_MUNICIPALITIES",
        3,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_RISK_MUNICIPALITIES",
        2,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_RISK_UNAVAILABLE_MUNICIPALITIES",
        1,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_EPISODES",
        4,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_RISK_WEEKS",
        4,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CLIMATE_NATIONAL_ROWS",
        2,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CLIMATE_REGIONAL_ROWS",
        4,
    )

    contracts = {
        serving.SERVING_DIR / "panorama" / "annual.json": {
            "data": [
                {
                    "casos_provaveis": 16_294_913,
                }
            ]
        },
        serving.SERVING_DIR / "panorama" / "weekly.json": {
            "data": [
                {
                    "casos_provaveis": 16_294_913,
                }
            ]
        },
        serving.SERVING_DIR / "spatial" / "municipalities.json": {
            "count": 3,
        },
        serving.SERVING_DIR / "risk_dynamics" / "municipalities.json": {
            "count": 2,
        },
        serving.SERVING_DIR / "municipality" / "index.json": {
            "count": 3,
            "risk_history": {
                "available": 2,
                "unavailable": 0,
            },
        },
        serving.SERVING_DIR / "risk_dynamics" / "episode_duration.json": {
            "summary": {
                "quantidade_episodios": 4,
                "semanas_risco": 4,
            }
        },
        serving.SERVING_DIR / "climate" / "national_lags.json": {
            "count": 2,
        },
        serving.SERVING_DIR / "climate" / "regional_lags.json": {
            "count": 4,
        },
    }

    with pytest.raises(
        ValueError,
        match="Ausências de risco no índice municipal divergentes",
    ):
        serving.validate_cross_contracts(contracts)
