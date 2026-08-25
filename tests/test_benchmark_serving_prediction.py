"""Testes do benchmark de serving preditivo municipal."""

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

BENCHMARK_SCRIPT = PROJECT_ROOT / "scripts" / "benchmark_serving_prediction.py"

SPEC = importlib.util.spec_from_file_location(
    "benchmark_serving_prediction",
    BENCHMARK_SCRIPT,
)

if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Não foi possível carregar o script: {BENCHMARK_SCRIPT}")

benchmark = importlib.util.module_from_spec(SPEC)

SPEC.loader.exec_module(benchmark)


TEST_THRESHOLDS = {
    1: 0.2,
    2: 0.3,
    3: 0.4,
    4: 0.5,
}


def build_test_dataframe() -> pd.DataFrame:
    """Cria conjunto sintético equivalente ao contrato preditivo."""
    return pd.DataFrame(
        {
            "codigo_ibge_7": [
                "1111111",
                "1111111",
                "1111111",
                "1111111",
                "1111111",
                "2222222",
                "2222222",
                "2222222",
                "2222222",
                "2222222",
            ],
            "ano_epidemiologico": [
                2025,
                2025,
                2025,
                2025,
                2025,
                2025,
                2025,
                2025,
                2025,
                2025,
            ],
            "semana_epidemiologica": [
                1,
                2,
                1,
                1,
                1,
                1,
                2,
                1,
                1,
                1,
            ],
            "data_inicio_semana": pd.to_datetime(
                [
                    "2024-12-29",
                    "2025-01-05",
                    "2024-12-29",
                    "2024-12-29",
                    "2024-12-29",
                    "2024-12-29",
                    "2025-01-05",
                    "2024-12-29",
                    "2024-12-29",
                    "2024-12-29",
                ]
            ),
            "risco_elevado": [
                False,
                False,
                False,
                True,
                False,
                False,
                True,
                False,
                False,
                True,
            ],
            "target": [
                False,
                True,
                True,
                False,
                True,
                True,
                False,
                False,
                True,
                False,
            ],
            "horizonte": [
                1,
                1,
                2,
                3,
                4,
                1,
                1,
                2,
                3,
                4,
            ],
            "score": [
                0.10,
                0.25,
                0.35,
                0.10,
                0.60,
                0.21,
                0.05,
                0.20,
                0.45,
                0.49,
            ],
            "threshold": [
                0.2,
                0.2,
                0.3,
                0.4,
                0.5,
                0.2,
                0.2,
                0.3,
                0.4,
                0.5,
            ],
            "predicao": [
                False,
                True,
                True,
                False,
                True,
                True,
                False,
                False,
                True,
                False,
            ],
        }
    )


def patch_test_constants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Adapta as invariantes nacionais ao conjunto sintético."""
    monkeypatch.setattr(
        benchmark,
        "EXPECTED_ROWS",
        10,
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_MUNICIPALITIES",
        2,
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_ROWS_PER_MUNICIPALITY",
        5,
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_HORIZONS",
        [
            1,
            2,
            3,
            4,
        ],
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_ROWS_BY_HORIZON",
        {
            1: 4,
            2: 2,
            3: 2,
            4: 2,
        },
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_WEEKS_BY_HORIZON",
        {
            1: 2,
            2: 1,
            3: 1,
            4: 1,
        },
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_ROWS_PER_MUNICIPALITY_BY_HORIZON",
        {
            1: 2,
            2: 1,
            3: 1,
            4: 1,
        },
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_THRESHOLDS",
        TEST_THRESHOLDS.copy(),
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_YEAR",
        2025,
    )


def test_normalize_value_handles_timestamp_and_missing() -> None:
    """Valores Pandas devem ser convertidos para tipos JSON seguros."""
    assert benchmark.normalize_value(pd.Timestamp("2025-01-05")) == "2025-01-05"

    assert benchmark.normalize_value(pd.NA) is None

    assert benchmark.normalize_value(10) == 10


def test_validate_predictions_accepts_consistent_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Conjunto preditivo consistente deve ser aceito."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_dataframe()

    benchmark.validate_predictions(dataframe)


def test_validate_predictions_rejects_duplicate_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Chave município-semana-horizonte não pode ser duplicada."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_dataframe()

    duplicate = dataframe.iloc[[0]].copy()

    dataframe = pd.concat(
        [
            dataframe,
            duplicate,
        ],
        ignore_index=True,
    )

    monkeypatch.setattr(
        benchmark,
        "EXPECTED_ROWS",
        11,
    )

    with pytest.raises(
        ValueError,
        match="chaves preditivas duplicadas",
    ):
        benchmark.validate_predictions(dataframe)


def test_validate_predictions_rejects_score_outside_probability_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scores devem permanecer no intervalo probabilístico [0, 1]."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_dataframe()

    dataframe.loc[
        0,
        "score",
    ] = 1.1

    with pytest.raises(
        ValueError,
        match=r"fora do intervalo \[0, 1\]",
    ):
        benchmark.validate_predictions(dataframe)


def test_validate_predictions_rejects_prediction_rule_divergence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Predição deve corresponder exatamente a score >= threshold."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_dataframe()

    dataframe.loc[
        0,
        "predicao",
    ] = True

    with pytest.raises(
        ValueError,
        match="divergentes da regra",
    ):
        benchmark.validate_predictions(dataframe)


def test_validate_horizon_structure_accepts_expected_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cobertura e thresholds válidos devem ser aceitos."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_dataframe()

    benchmark.validate_horizon_structure(dataframe)


def test_validate_horizon_structure_rejects_wrong_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Threshold divergente do valor congelado deve interromper o benchmark."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_dataframe()

    dataframe.loc[
        dataframe["horizonte"] == 1,
        "threshold",
    ] = 0.25

    with pytest.raises(
        ValueError,
        match="threshold divergente",
    ):
        benchmark.validate_horizon_structure(dataframe)


def test_validate_municipality_distribution_accepts_expected_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cada município deve possuir a distribuição esperada por horizonte."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_dataframe()

    result = benchmark.validate_municipality_distribution(dataframe)

    assert result == {
        "1111111": 5,
        "2222222": 5,
    }


def test_compact_by_horizon_payload_has_expected_structure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contrato escolhido deve armazenar threshold uma vez por horizonte."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_dataframe()

    group = dataframe[dataframe["codigo_ibge_7"] == "1111111"]

    payload = benchmark.build_compact_by_horizon_payload(
        "1111111",
        group,
    )

    assert payload["schema_version"] == benchmark.SCHEMA_VERSION

    assert payload["codigo_ibge_7"] == "1111111"

    assert payload["count"] == 5

    assert set(payload["horizontes"]) == {
        "h1",
        "h2",
        "h3",
        "h4",
    }

    assert payload["horizontes"]["h1"]["count"] == 2

    assert payload["horizontes"]["h1"]["threshold"] == 0.2

    data = payload["horizontes"]["h1"]["data"]

    assert set(data) == {
        "ano_epidemiologico",
        "semana_epidemiologica",
        "data_inicio_semana",
        "risco_elevado",
        "target",
        "score",
        "predicao",
    }

    assert "horizonte" not in data

    assert "threshold" not in data

    for values in data.values():
        assert len(values) == 2


def test_serialize_json_rejects_nan() -> None:
    """JSON do serving não pode aceitar NaN."""
    with pytest.raises(
        ValueError,
    ):
        benchmark.serialize_json({"score": float("nan")})


def test_benchmark_json_measures_all_candidate_formats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Benchmark deve medir as três representações JSON."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_dataframe()

    result = benchmark.benchmark_json(dataframe)

    assert set(result) == {
        "verbose",
        "compact_flat",
        "compact_by_horizon",
        "rows_per_municipality",
    }

    assert result["rows_per_municipality"] == {
        "1111111": 5,
        "2222222": 5,
    }

    for representation in (
        "verbose",
        "compact_flat",
        "compact_by_horizon",
    ):
        metrics = result[representation]

        assert metrics["total"] > 0

        assert metrics["total_gzip"] > 0

        assert metrics["min"] > 0

        assert metrics["median"] > 0

        assert metrics["max"] > 0

    assert result["verbose"]["total"] > result["compact_flat"]["total"]

    assert result["verbose"]["total"] > result["compact_by_horizon"]["total"]


def test_benchmark_parquet_returns_positive_size() -> None:
    """Representação Parquet reduzida deve produzir artefato válido."""
    dataframe = build_test_dataframe()

    size = benchmark.benchmark_parquet(dataframe)

    assert size > 0


def test_write_benchmark_audit_records_approved_decision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auditoria deve preservar decisão física e invariantes aprovadas."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_dataframe()

    output_file = tmp_path / "benchmark_serving_prediction.json"

    monkeypatch.setattr(
        benchmark,
        "OUTPUT_FILE",
        output_file,
    )

    json_results = benchmark.benchmark_json(dataframe)

    benchmark.write_benchmark_audit(
        dataframe,
        json_results,
        parquet_size=1234,
    )

    payload = json.loads(output_file.read_text(encoding="utf-8"))

    assert payload["status"] == "APROVADO"

    assert payload["painel"]["linhas"] == 10

    assert payload["painel"]["municipios"] == 2

    assert payload["decisao"]["formato_inicial"] == "json_compacto_por_horizonte"

    assert payload["decisao"]["granularidade"] == "um_arquivo_por_municipio"

    assert payload["decisao"]["arquivos_estimados"] == 2

    assert payload["decisao"]["parquet_preservado_como_alternativa"] is True

    assert payload["invariantes"]["linhas_esperadas"] == 10

    assert payload["invariantes"]["municipios_esperados"] == 2

    assert payload["invariantes"]["thresholds"] == {
        "h1": 0.2,
        "h2": 0.3,
        "h3": 0.4,
        "h4": 0.5,
    }

    assert payload["parquet_nacional_reduzido"]["size_bytes"] == 1234
