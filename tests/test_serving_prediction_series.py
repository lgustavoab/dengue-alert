"""Testes das séries municipais do serving preditivo."""

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SERVING_SCRIPT = PROJECT_ROOT / "scripts" / "gerar_serving_prediction_series.py"

SPEC = importlib.util.spec_from_file_location(
    "gerar_serving_prediction_series",
    SERVING_SCRIPT,
)

if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Não foi possível carregar o script: {SERVING_SCRIPT}")

serving = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(serving)


TEST_THRESHOLDS = {
    1: 0.2,
    2: 0.3,
    3: 0.4,
    4: 0.5,
}

ROWS_BY_HORIZON = {
    1: 4,
    2: 2,
    3: 2,
    4: 2,
}

ROWS_PER_MUNICIPALITY_BY_HORIZON = {
    1: 2,
    2: 1,
    3: 1,
    4: 1,
}

TARGET_POSITIVES = {
    1: 2,
    2: 1,
    3: 1,
    4: 1,
}

POSITIVE_PREDICTIONS = {
    1: 2,
    2: 1,
    3: 1,
    4: 1,
}

EARLY_WARNING_ALERTS = {
    1: 2,
    2: 1,
    3: 1,
    4: 1,
}


def patch_test_constants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Adapta as invariantes nacionais ao conjunto sintético."""
    monkeypatch.setattr(
        serving,
        "EXPECTED_ROWS",
        10,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_MUNICIPALITIES",
        2,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_ROWS_PER_MUNICIPALITY",
        5,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_YEAR",
        2025,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_HORIZONS",
        [1, 2, 3, 4],
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_ROWS_BY_HORIZON",
        ROWS_BY_HORIZON.copy(),
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_ROWS_PER_MUNICIPALITY_BY_HORIZON",
        ROWS_PER_MUNICIPALITY_BY_HORIZON.copy(),
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_THRESHOLDS",
        TEST_THRESHOLDS.copy(),
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_TARGET_POSITIVES",
        TARGET_POSITIVES.copy(),
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_POSITIVE_PREDICTIONS",
        POSITIVE_PREDICTIONS.copy(),
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_EARLY_WARNING_ALERTS",
        EARLY_WARNING_ALERTS.copy(),
    )


def patch_test_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, Path]:
    """Redireciona output, staging e backup para diretório temporário."""
    output_dir = tmp_path / "municipality" / "series"

    staging_dir = tmp_path / "municipality" / "series.__staging__"

    backup_dir = tmp_path / "municipality" / "series.__backup__"

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
        "BACKUP_DIR",
        backup_dir,
    )

    return (
        output_dir,
        staging_dir,
        backup_dir,
    )


def build_test_dataframe() -> pd.DataFrame:
    """Cria conjunto preditivo municipal sintético."""
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


def build_municipality_payload(
    code: str = "1111111",
) -> dict:
    """Cria payload municipal válido para os testes."""
    dataframe = build_test_dataframe()

    group = dataframe[dataframe["codigo_ibge_7"] == code]

    return serving.build_payload(
        code,
        group,
    )


def test_validate_predictions_accepts_consistent_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Artefato preditivo consistente deve ser aceito."""
    patch_test_constants(monkeypatch)

    serving.validate_predictions(build_test_dataframe())


def test_validate_predictions_rejects_duplicate_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Chave município-semana-horizonte duplicada deve ser rejeitada."""
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
        serving,
        "EXPECTED_ROWS",
        11,
    )

    with pytest.raises(
        ValueError,
        match="chaves preditivas duplicadas",
    ):
        serving.validate_predictions(dataframe)


def test_validate_predictions_rejects_score_outside_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scores devem permanecer dentro de [0, 1]."""
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
        serving.validate_predictions(dataframe)


def test_validate_predictions_rejects_prediction_divergence(
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
        serving.validate_predictions(dataframe)


def test_validate_horizon_structure_accepts_expected_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Estrutura e resultados por horizonte válidos devem ser aceitos."""
    patch_test_constants(monkeypatch)

    serving.validate_horizon_structure(build_test_dataframe())


def test_validate_horizon_structure_rejects_wrong_target_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Divergência nos targets positivos deve interromper a geração."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_dataframe()

    dataframe.loc[
        0,
        "target",
    ] = True

    with pytest.raises(
        ValueError,
        match="targets positivos",
    ):
        serving.validate_horizon_structure(dataframe)


def test_validate_municipality_distribution_accepts_expected_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cada município deve preservar 5 registros no conjunto sintético."""
    patch_test_constants(monkeypatch)

    serving.validate_municipality_distribution(build_test_dataframe())


def test_build_payload_uses_compact_horizon_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Payload deve organizar as observações diretamente por horizonte."""
    patch_test_constants(monkeypatch)

    payload = build_municipality_payload()

    assert payload["schema_version"] == serving.SCHEMA_VERSION

    assert payload["codigo_ibge_7"] == "1111111"

    assert payload["count"] == 5

    assert set(payload["horizontes"]) == {
        "h1",
        "h2",
        "h3",
        "h4",
    }

    h1 = payload["horizontes"]["h1"]

    assert h1["count"] == 2

    assert h1["threshold"] == 0.2

    assert set(h1["data"]) == set(serving.DATA_COLUMNS)

    assert "horizonte" not in h1["data"]

    assert "threshold" not in h1["data"]

    assert h1["data"]["data_inicio_semana"] == [
        "2024-12-29",
        "2025-01-05",
    ]


def test_validate_payload_rejects_invalid_data_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Campos estruturais com tipo inválido devem gerar TypeError."""
    patch_test_constants(monkeypatch)

    payload = build_municipality_payload()

    payload["horizontes"]["h1"]["data"] = []

    with pytest.raises(
        TypeError,
        match="bloco data ausente",
    ):
        serving.validate_payload(payload)


def test_serialize_payload_rejects_nan() -> None:
    """JSON municipal não pode conter NaN."""
    with pytest.raises(
        ValueError,
    ):
        serving.serialize_payload({"score": float("nan")})


def test_prepare_staging_directory_removes_previous_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Staging antigo deve ser descartado antes de uma nova geração."""
    (
        _,
        staging_dir,
        _,
    ) = patch_test_directories(
        tmp_path,
        monkeypatch,
    )

    staging_dir.mkdir(parents=True)

    stale_file = staging_dir / "stale.json"

    stale_file.write_text(
        "{}\n",
        encoding="utf-8",
    )

    serving.prepare_staging_directory()

    assert staging_dir.exists()

    assert list(staging_dir.iterdir()) == []


def test_generate_series_writes_and_promotes_all_expected_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Geração deve validar e promover todos os municípios."""
    patch_test_constants(monkeypatch)

    (
        output_dir,
        staging_dir,
        backup_dir,
    ) = patch_test_directories(
        tmp_path,
        monkeypatch,
    )

    result = serving.generate_series(build_test_dataframe())

    assert result["files"] == 2

    assert result["rows"] == 10

    assert result["rows_by_horizon"] == ROWS_BY_HORIZON

    assert output_dir.exists()

    assert not staging_dir.exists()

    assert not backup_dir.exists()

    files = sorted(output_dir.glob("*.json"))

    assert [path.name for path in files] == [
        "1111111.json",
        "2222222.json",
    ]

    payload = json.loads((output_dir / "1111111.json").read_text(encoding="utf-8"))

    assert payload["count"] == 5

    assert payload["horizontes"]["h1"]["count"] == 2

    assert payload["horizontes"]["h4"]["threshold"] == 0.5


def test_validate_generated_directory_rejects_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validação integral deve detectar município ausente no staging."""
    patch_test_constants(monkeypatch)

    (
        _,
        staging_dir,
        _,
    ) = patch_test_directories(
        tmp_path,
        monkeypatch,
    )

    staging_dir.mkdir(parents=True)

    payload = build_municipality_payload("1111111")

    (staging_dir / "1111111.json").write_text(
        serving.serialize_payload(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Quantidade inesperada de arquivos",
    ):
        serving.validate_generated_directory(
            {
                "1111111",
                "2222222",
            }
        )


def test_promote_staging_directory_replaces_previous_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Promoção bem-sucedida deve substituir a versão anterior."""
    (
        output_dir,
        staging_dir,
        backup_dir,
    ) = patch_test_directories(
        tmp_path,
        monkeypatch,
    )

    output_dir.mkdir(parents=True)

    (output_dir / "old.json").write_text(
        '{"version":"old"}\n',
        encoding="utf-8",
    )

    staging_dir.mkdir(parents=True)

    (staging_dir / "new.json").write_text(
        '{"version":"new"}\n',
        encoding="utf-8",
    )

    serving.promote_staging_directory()

    assert output_dir.exists()

    assert not staging_dir.exists()

    assert not backup_dir.exists()

    assert not (output_dir / "old.json").exists()

    assert (output_dir / "new.json").exists()


def test_promote_staging_directory_restores_backup_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Falha na promoção deve restaurar integralmente o output anterior."""
    (
        output_dir,
        staging_dir,
        backup_dir,
    ) = patch_test_directories(
        tmp_path,
        monkeypatch,
    )

    output_dir.mkdir(parents=True)

    old_file = output_dir / "old.json"

    old_file.write_text(
        '{"version":"old"}\n',
        encoding="utf-8",
    )

    staging_dir.mkdir(parents=True)

    (staging_dir / "new.json").write_text(
        '{"version":"new"}\n',
        encoding="utf-8",
    )

    original_replace = Path.replace

    def fail_when_promoting(
        self: Path,
        target: Path,
    ) -> Path:
        if self == staging_dir and Path(target) == output_dir:
            raise OSError("falha sintética na promoção")

        return original_replace(
            self,
            target,
        )

    monkeypatch.setattr(
        Path,
        "replace",
        fail_when_promoting,
    )

    with pytest.raises(
        OSError,
        match="falha sintética na promoção",
    ):
        serving.promote_staging_directory()

    assert output_dir.exists()

    assert old_file.exists()

    assert old_file.read_text(encoding="utf-8") == '{"version":"old"}\n'

    assert staging_dir.exists()

    assert (staging_dir / "new.json").exists()

    assert not backup_dir.exists()
