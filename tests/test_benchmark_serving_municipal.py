"""Testes do benchmark de serving histórico municipal."""

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

BENCHMARK_SCRIPT = PROJECT_ROOT / "scripts" / "benchmark_serving_municipal.py"

SPEC = importlib.util.spec_from_file_location(
    "benchmark_serving_municipal",
    BENCHMARK_SCRIPT,
)

if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Não foi possível carregar o script: {BENCHMARK_SCRIPT}")

benchmark = importlib.util.module_from_spec(SPEC)

SPEC.loader.exec_module(benchmark)


def test_normalize_value_converts_timestamp_and_missing() -> None:
    """Valores Pandas devem ser convertidos para tipos JSON válidos."""
    timestamp = pd.Timestamp("2025-03-16")

    assert benchmark.normalize_value(timestamp) == "2025-03-16"

    assert benchmark.normalize_value(pd.NA) is None

    assert benchmark.normalize_value(10) == 10


def test_build_compact_payload_preserves_column_alignment() -> None:
    """Payload compacto deve manter todos os arrays com o mesmo tamanho."""
    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": [
                "3537305",
                "3537305",
            ],
            "ano_epidemiologico": [
                2025,
                2025,
            ],
            "semana_epidemiologica": [
                1,
                2,
            ],
            "data_inicio_semana": pd.to_datetime(
                [
                    "2024-12-29",
                    "2025-01-05",
                ]
            ),
            "casos_provaveis": [
                0,
                3,
            ],
            "incidencia_100mil": [
                0.0,
                4.5,
            ],
            "registro_sinan_presente": [
                False,
                True,
            ],
            "zero_preenchido": [
                True,
                False,
            ],
            "populacao": [
                66_000,
                66_000,
            ],
        }
    )

    payload = benchmark.build_compact_payload(
        "3537305",
        dataframe,
    )

    assert payload["schema_version"] == benchmark.SCHEMA_VERSION

    assert payload["codigo_ibge_7"] == "3537305"

    assert payload["count"] == 2

    assert payload["data"]["data_inicio_semana"] == [
        "2024-12-29",
        "2025-01-05",
    ]

    for values in payload["data"].values():
        assert len(values) == payload["count"]


def test_serialize_json_rejects_nan() -> None:
    """JSON do benchmark não pode aceitar NaN."""
    with pytest.raises(
        ValueError,
    ):
        benchmark.serialize_json({"valor": float("nan")})


def test_benchmark_json_compact_is_smaller_than_verbose() -> None:
    """Representação compacta deve ser menor que a verbosa."""
    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": [
                "1111111",
                "1111111",
                "2222222",
                "2222222",
            ],
            "ano_epidemiologico": [
                2024,
                2024,
                2024,
                2024,
            ],
            "semana_epidemiologica": [
                1,
                2,
                1,
                2,
            ],
            "data_inicio_semana": pd.to_datetime(
                [
                    "2023-12-31",
                    "2024-01-07",
                    "2023-12-31",
                    "2024-01-07",
                ]
            ),
            "casos_provaveis": [
                1,
                2,
                3,
                4,
            ],
            "incidencia_100mil": [
                1.0,
                2.0,
                3.0,
                4.0,
            ],
            "registro_sinan_presente": [
                True,
                True,
                True,
                True,
            ],
            "zero_preenchido": [
                False,
                False,
                False,
                False,
            ],
            "populacao": [
                100_000,
                100_000,
                200_000,
                200_000,
            ],
        }
    )

    result = benchmark.benchmark_json(dataframe)

    assert result["rows_per_territory"] == {
        "1111111": 2,
        "2222222": 2,
    }

    assert result["compact"]["total"] < result["verbose"]["total"]

    assert result["compact"]["total_gzip"] > 0

    assert result["verbose"]["total_gzip"] > 0


def test_validate_week_distribution_accepts_expected_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cobertura conhecida deve aceitar uma única exceção territorial."""
    monkeypatch.setattr(
        benchmark,
        "EXPECTED_FULL_WEEKS",
        10,
    )

    monkeypatch.setattr(
        benchmark,
        "BOA_ESPERANCA_NORTE",
        "5101837",
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_BOA_ESPERANCA_WEEKS",
        3,
    )

    benchmark.validate_week_distribution(
        {
            "1100015": 10,
            "3537305": 10,
            "5101837": 3,
        }
    )


def test_validate_week_distribution_rejects_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cobertura temporal inesperada deve interromper o benchmark."""
    monkeypatch.setattr(
        benchmark,
        "EXPECTED_FULL_WEEKS",
        10,
    )

    monkeypatch.setattr(
        benchmark,
        "BOA_ESPERANCA_NORTE",
        "5101837",
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_BOA_ESPERANCA_WEEKS",
        3,
    )

    with pytest.raises(
        ValueError,
        match="Distribuição municipal de semanas inesperada",
    ):
        benchmark.validate_week_distribution(
            {
                "1100015": 9,
                "5101837": 3,
            }
        )


def test_write_benchmark_audit_creates_structured_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auditoria deve registrar medições e decisão arquitetural."""
    output_file = tmp_path / "benchmark_serving_municipal.json"

    monkeypatch.setattr(
        benchmark,
        "OUTPUT_FILE",
        output_file,
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_TERRITORIES",
        2,
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_ROWS",
        4,
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_FULL_WEEKS",
        2,
    )

    monkeypatch.setattr(
        benchmark,
        "BOA_ESPERANCA_NORTE",
        "5101837",
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_BOA_ESPERANCA_WEEKS",
        2,
    )

    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": [
                "1111111",
                "1111111",
                "5101837",
                "5101837",
            ]
        }
    )

    json_results = {
        "verbose": {
            "total": 1_000,
            "total_gzip": 400,
            "min": 450,
            "median": 500,
            "max": 550,
            "median_gzip": 200,
            "max_gzip": 220,
        },
        "compact": {
            "total": 500,
            "total_gzip": 300,
            "min": 200,
            "median": 250,
            "max": 300,
            "median_gzip": 150,
            "max_gzip": 170,
        },
        "rows_per_territory": {
            "1111111": 2,
            "5101837": 2,
        },
    }

    benchmark.write_benchmark_audit(
        dataframe,
        json_results,
        parquet_size=123,
    )

    payload = json.loads(output_file.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "1.0"

    assert payload["status"] == "APROVADO"

    assert payload["painel"]["linhas"] == 4

    assert payload["painel"]["unidades_territoriais"] == 2

    assert payload["json_compacto_por_municipio"]["total_bytes"] == 500

    assert payload["parquet_nacional_reduzido"]["size_bytes"] == 123

    assert payload["decisao"]["formato_inicial"] == "json_compacto_por_municipio"

    assert payload["decisao"]["arquivos_estimados"] == 2

    assert payload["decisao"]["parquet_preservado_como_alternativa"] is True

    assert payload["validacoes"]["excecao_cobertura_temporal"] == {
        "codigo_ibge_7": "5101837",
        "semanas": 2,
    }
