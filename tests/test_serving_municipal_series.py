"""Testes do serving das séries históricas municipais."""

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SERVING_SCRIPT = PROJECT_ROOT / "scripts" / "gerar_serving_municipal_series.py"

SPEC = importlib.util.spec_from_file_location(
    "gerar_serving_municipal_series",
    SERVING_SCRIPT,
)

if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Não foi possível carregar o script: {SERVING_SCRIPT}")

serving = importlib.util.module_from_spec(SPEC)

SPEC.loader.exec_module(serving)


def build_test_dataframe() -> pd.DataFrame:
    """Cria painel municipal sintético para os testes."""
    return pd.DataFrame(
        {
            "codigo_ibge_7": [
                "1111111",
                "1111111",
                "2222222",
            ],
            "ano_epidemiologico": [
                2025,
                2025,
                2025,
            ],
            "semana_epidemiologica": [
                1,
                2,
                1,
            ],
            "data_inicio_semana": pd.to_datetime(
                [
                    "2024-12-29",
                    "2025-01-05",
                    "2024-12-29",
                ]
            ),
            "casos_provaveis": [
                1,
                2,
                3,
            ],
            "incidencia_100mil": [
                1.0,
                2.0,
                3.0,
            ],
            "registro_sinan_presente": [
                True,
                True,
                True,
            ],
            "zero_preenchido": [
                False,
                False,
                False,
            ],
            "populacao": [
                100_000,
                100_000,
                200_000,
            ],
        }
    )


def test_nullable_values_convert_missing_to_none() -> None:
    """Valores opcionais ausentes devem ser serializados como null."""
    assert serving.nullable_float(pd.NA) is None

    assert serving.nullable_int(pd.NA) is None

    assert serving.nullable_float(1.5) == 1.5

    assert serving.nullable_int(10) == 10


def test_build_payload_preserves_column_alignment() -> None:
    """Contrato municipal deve manter arrays alinhados."""
    dataframe = build_test_dataframe()

    group = dataframe[dataframe["codigo_ibge_7"] == "1111111"]

    payload = serving.build_payload(
        "1111111",
        group,
    )

    assert payload["schema_version"] == serving.SCHEMA_VERSION

    assert payload["codigo_ibge_7"] == "1111111"

    assert payload["count"] == 2

    assert payload["data"]["data_inicio_semana"] == [
        "2024-12-29",
        "2025-01-05",
    ]

    assert payload["data"]["casos_provaveis"] == [
        1,
        2,
    ]

    for values in payload["data"].values():
        assert len(values) == payload["count"]


def test_validate_payload_accepts_valid_contract() -> None:
    """Contrato municipal consistente deve ser aceito."""
    dataframe = build_test_dataframe()

    group = dataframe[dataframe["codigo_ibge_7"] == "1111111"]

    payload = serving.build_payload(
        "1111111",
        group,
    )

    serving.validate_payload(payload)


def test_validate_payload_rejects_misaligned_array() -> None:
    """Arrays municipais não podem possuir comprimentos diferentes."""
    dataframe = build_test_dataframe()

    group = dataframe[dataframe["codigo_ibge_7"] == "1111111"]

    payload = serving.build_payload(
        "1111111",
        group,
    )

    payload["data"]["casos_provaveis"] = [1]

    with pytest.raises(
        ValueError,
        match="possui 1 valores",
    ):
        serving.validate_payload(payload)


def test_validate_payload_rejects_negative_cases() -> None:
    """Série municipal não pode conter quantidade negativa de casos."""
    dataframe = build_test_dataframe()

    group = dataframe[dataframe["codigo_ibge_7"] == "1111111"]

    payload = serving.build_payload(
        "1111111",
        group,
    )

    payload["data"]["casos_provaveis"][0] = -1

    with pytest.raises(
        ValueError,
        match="casos negativos",
    ):
        serving.validate_payload(payload)


def test_validate_panel_accepts_consistent_panel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Painel sintético consistente deve preservar invariantes nacionais."""
    dataframe = build_test_dataframe()

    monkeypatch.setattr(
        serving,
        "EXPECTED_ROWS",
        3,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_TERRITORIES",
        2,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CASES",
        6,
    )

    serving.validate_panel(dataframe)


def test_validate_panel_rejects_duplicate_municipality_week(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Uma chave município-semana duplicada deve interromper a geração."""
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
        serving,
        "EXPECTED_ROWS",
        4,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_TERRITORIES",
        2,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CASES",
        7,
    )

    with pytest.raises(
        ValueError,
        match="chaves município-semana duplicadas",
    ):
        serving.validate_panel(dataframe)


def test_validate_week_distribution_accepts_expected_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cobertura reduzida deve ocorrer apenas na exceção conhecida."""
    dataframe = build_test_dataframe()

    monkeypatch.setattr(
        serving,
        "EXPECTED_FULL_WEEKS",
        2,
    )

    monkeypatch.setattr(
        serving,
        "BOA_ESPERANCA_NORTE",
        "2222222",
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_BOA_ESPERANCA_WEEKS",
        1,
    )

    result = serving.validate_week_distribution(dataframe)

    assert result == {
        "1111111": 2,
        "2222222": 1,
    }


def test_serialize_payload_rejects_nan() -> None:
    """JSON municipal não pode conter NaN."""
    with pytest.raises(
        ValueError,
    ):
        serving.serialize_payload({"valor": float("nan")})


def test_generate_series_creates_all_expected_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Geração deve produzir arquivos completos e preservar totais."""
    dataframe = build_test_dataframe()

    output_dir = tmp_path / "series"

    staging_dir = tmp_path / "series.__staging__"

    monkeypatch.setattr(
        serving,
        "OUTPUT_DIR",
        output_dir,
    )

    monkeypatch.setattr(
        serving,
        "STAGING_DIR",
        staging_dir,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_TERRITORIES",
        2,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_ROWS",
        3,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CASES",
        6,
    )

    result = serving.generate_series(dataframe)

    assert result["files"] == 2

    assert result["rows"] == 3

    assert result["cases"] == 6

    assert output_dir.exists()

    assert not staging_dir.exists()

    files = sorted(output_dir.glob("*.json"))

    assert [file.name for file in files] == [
        "1111111.json",
        "2222222.json",
    ]

    first_payload = json.loads(
        (output_dir / "1111111.json").read_text(encoding="utf-8")
    )

    second_payload = json.loads(
        (output_dir / "2222222.json").read_text(encoding="utf-8")
    )

    assert first_payload["count"] == 2

    assert second_payload["count"] == 1

    assert sum(first_payload["data"]["casos_provaveis"]) == 3

    assert sum(second_payload["data"]["casos_provaveis"]) == 3


def test_generate_series_cleans_staging_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Falha intermediária não deve deixar staging parcial."""
    dataframe = build_test_dataframe()

    output_dir = tmp_path / "series"

    staging_dir = tmp_path / "series.__staging__"

    output_dir.mkdir(parents=True)

    existing_file = output_dir / "existing.json"

    existing_file.write_text(
        '{"preserved":true}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        serving,
        "OUTPUT_DIR",
        output_dir,
    )

    monkeypatch.setattr(
        serving,
        "STAGING_DIR",
        staging_dir,
    )

    original_validate_payload = serving.validate_payload

    calls = 0

    def fail_on_second_payload(
        payload,
    ) -> None:
        nonlocal calls

        calls += 1

        original_validate_payload(payload)

        if calls == 2:
            raise ValueError("falha sintética")

    monkeypatch.setattr(
        serving,
        "validate_payload",
        fail_on_second_payload,
    )

    with pytest.raises(
        ValueError,
        match="falha sintética",
    ):
        serving.generate_series(dataframe)

    assert not staging_dir.exists()

    assert existing_file.exists()

    assert existing_file.read_text(encoding="utf-8") == '{"preserved":true}\n'
