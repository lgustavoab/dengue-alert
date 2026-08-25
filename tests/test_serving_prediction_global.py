"""Testes dos contratos globais do serving preditivo."""

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SERVING_SCRIPT = PROJECT_ROOT / "scripts" / "gerar_serving_prediction_global.py"

SPEC = importlib.util.spec_from_file_location(
    "gerar_serving_prediction_global",
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

WEEKS_BY_HORIZON = {
    1: 2,
    2: 1,
    3: 1,
    4: 1,
}

GENERAL_POSITIVES = {
    1: 2,
    2: 1,
    3: 1,
    4: 1,
}

EARLY_WARNING_OBSERVATIONS = {
    1: 3,
    2: 2,
    3: 1,
    4: 1,
}

EARLY_WARNING_POSITIVES = {
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
        "EXPECTED_YEAR",
        2025,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_ROWS_PER_MUNICIPALITY",
        5,
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
        "EXPECTED_WEEKS_BY_HORIZON",
        WEEKS_BY_HORIZON.copy(),
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_ROWS_PER_MUNICIPALITY_BY_HORIZON",
        {
            1: 2,
            2: 1,
            3: 1,
            4: 1,
        },
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_THRESHOLDS",
        TEST_THRESHOLDS.copy(),
    )


def build_test_predictions() -> pd.DataFrame:
    """Cria predições sintéticas compatíveis com o contrato."""
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
            "nome_municipio_ibge": [
                "Município A",
                "Município A",
                "Município A",
                "Município A",
                "Município A",
                "Município B",
                "Município B",
                "Município B",
                "Município B",
                "Município B",
            ],
            "nome_uf_ibge": [
                "Estado A",
                "Estado A",
                "Estado A",
                "Estado A",
                "Estado A",
                "Estado B",
                "Estado B",
                "Estado B",
                "Estado B",
                "Estado B",
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


def build_test_audit() -> dict:
    """Cria auditoria sintética do modelo final."""
    return {
        "modelo_final": {
            "algoritmo": serving.EXPECTED_MODEL,
            "features": serving.EXPECTED_FEATURES,
            "calibracao": serving.EXPECTED_CALIBRATION,
            "probabilidades": serving.EXPECTED_PROBABILITIES,
            "thresholds": {
                "h1": 0.2,
                "h2": 0.3,
                "h3": 0.4,
                "h4": 0.5,
            },
        },
        "protocolo": {
            "desenvolvimento": serving.EXPECTED_DEVELOPMENT,
            "teste_final": serving.EXPECTED_FINAL_TEST,
            "thresholds_congelados": True,
            "teste_final_utilizado_na_selecao": False,
        },
        "predicoes": {
            "linhas": 10,
            "duplicadas": 0,
        },
    }


def add_metric_block(
    row: dict,
    prefix: str,
    observations: int,
    positives: int,
) -> None:
    """Adiciona métricas sintéticas com o schema esperado."""
    negatives = observations - positives

    row[f"{prefix}_observacoes"] = observations
    row[f"{prefix}_positivos"] = positives
    row[f"{prefix}_negativos"] = negatives

    row[f"{prefix}_prevalencia"] = positives / observations if observations else 0.0

    row[f"{prefix}_pr_auc_average_precision"] = 0.5

    row[f"{prefix}_roc_auc"] = 0.5
    row[f"{prefix}_recall"] = 0.5
    row[f"{prefix}_precision"] = 0.5
    row[f"{prefix}_f1"] = 0.5
    row[f"{prefix}_balanced_accuracy"] = 0.5
    row[f"{prefix}_brier_score"] = 0.25

    row[f"{prefix}_matriz_confusao_tn"] = negatives

    row[f"{prefix}_matriz_confusao_fp"] = 0

    row[f"{prefix}_matriz_confusao_fn"] = positives

    row[f"{prefix}_matriz_confusao_tp"] = 0


def build_test_evaluation() -> pd.DataFrame:
    """Cria tabela sintética da avaliação final."""
    rows = []

    for horizon in [1, 2, 3, 4]:
        observations = ROWS_BY_HORIZON[horizon]

        positives = GENERAL_POSITIVES[horizon]

        early_observations = EARLY_WARNING_OBSERVATIONS[horizon]

        early_positives = EARLY_WARNING_POSITIVES[horizon]

        early_alerts = EARLY_WARNING_ALERTS[horizon]

        model_row = {
            "modelo": "hist_gradient_boosting",
            "horizonte": horizon,
            "threshold": TEST_THRESHOLDS[horizon],
            "linhas_treino": 100,
            "linhas_teste": observations,
        }

        add_metric_block(
            model_row,
            "geral",
            observations,
            positives,
        )

        add_metric_block(
            model_row,
            "early_warning",
            early_observations,
            early_positives,
        )

        model_row["early_warning_alertas"] = early_alerts

        model_row["early_warning_proporcao_alertas"] = early_alerts / early_observations

        rows.append(model_row)

        persistence_row = {
            "modelo": "persistence",
            "horizonte": horizon,
            "threshold": 0.5,
            "linhas_treino": None,
            "linhas_teste": observations,
        }

        add_metric_block(
            persistence_row,
            "geral",
            observations,
            positives,
        )

        add_metric_block(
            persistence_row,
            "early_warning",
            early_observations,
            early_positives,
        )

        persistence_row["early_warning_alertas"] = 0

        persistence_row["early_warning_proporcao_alertas"] = 0.0

        rows.append(persistence_row)

    return pd.DataFrame(rows)


def test_nullable_helpers_convert_missing_values() -> None:
    """Conversores opcionais devem transformar ausentes em null."""
    assert serving.nullable_int(pd.NA) is None

    assert serving.nullable_float(pd.NA) is None

    assert serving.nullable_int(10) == 10

    assert serving.nullable_float(1.5) == 1.5


def test_validate_predictions_accepts_consistent_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Artefato preditivo consistente deve ser aceito."""
    patch_test_constants(monkeypatch)

    serving.validate_predictions(build_test_predictions())


def test_validate_predictions_rejects_duplicate_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Chave preditiva duplicada deve interromper a geração."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_predictions()

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
    """Score deve permanecer dentro do intervalo [0, 1]."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_predictions()

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

    dataframe = build_test_predictions()

    dataframe.loc[
        0,
        "predicao",
    ] = True

    with pytest.raises(
        ValueError,
        match="divergentes da regra",
    ):
        serving.validate_predictions(dataframe)


def test_validate_horizons_accepts_expected_structure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cobertura temporal e thresholds válidos devem ser aceitos."""
    patch_test_constants(monkeypatch)

    serving.validate_horizons(build_test_predictions())


def test_validate_horizons_rejects_wrong_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Threshold divergente deve interromper a geração."""
    patch_test_constants(monkeypatch)

    dataframe = build_test_predictions()

    dataframe.loc[
        dataframe["horizonte"] == 1,
        "threshold",
    ] = 0.25

    with pytest.raises(
        ValueError,
        match="threshold divergente",
    ):
        serving.validate_horizons(dataframe)


def test_validate_municipality_distribution_accepts_expected_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cada município deve preservar a distribuição por horizonte."""
    patch_test_constants(monkeypatch)

    serving.validate_municipality_distribution(build_test_predictions())


def test_validate_evaluation_audit_accepts_frozen_protocol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auditoria coerente com o protocolo congelado deve ser aceita."""
    patch_test_constants(monkeypatch)

    serving.validate_evaluation_audit(build_test_audit())


def test_validate_evaluation_audit_rejects_final_test_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Teste final não pode ter sido usado na seleção do modelo."""
    patch_test_constants(monkeypatch)

    audit = build_test_audit()

    audit["protocolo"]["teste_final_utilizado_na_selecao"] = True

    with pytest.raises(
        ValueError,
        match="uso indevido do teste final",
    ):
        serving.validate_evaluation_audit(audit)


def test_build_model_metadata_preserves_semantics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Metadata deve deixar explícita a natureza retrospectiva."""
    patch_test_constants(monkeypatch)

    payload = serving.build_model_metadata(build_test_audit())

    assert payload["retrospectivo"] is True

    assert payload["ano_referencia"] == 2025

    assert payload["modelo"]["algoritmo"] == serving.EXPECTED_MODEL

    assert payload["horizontes"][0]["threshold"] == 0.2

    assert payload["semantica"]["predicao"] == "score >= threshold"


def test_build_evaluation_overview_derives_early_warning_correctly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Overview deve distinguir previsão positiva de early warning."""
    patch_test_constants(monkeypatch)

    payload = serving.build_evaluation_overview(build_test_predictions())

    assert payload["linhas"] == 10

    assert payload["municipios"] == 2

    h1 = payload["horizontes"]["h1"]

    assert h1["linhas"] == 4

    assert h1["target_positivos"] == 2

    assert h1["predicoes_positivas"] == 2

    assert h1["early_warning_elegiveis"] == 3

    assert h1["early_warning_alertas"] == 2


def test_build_evaluation_by_horizon_preserves_model_and_baseline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contrato deve separar modelo final e baseline de persistência."""
    patch_test_constants(monkeypatch)

    payload = serving.build_evaluation_by_horizon(build_test_evaluation())

    assert set(payload["horizontes"]) == {
        "h1",
        "h2",
        "h3",
        "h4",
    }

    h1 = payload["horizontes"]["h1"]

    assert h1["threshold_modelo"] == 0.2

    assert h1["modelo_final"]["nome"] == "hist_gradient_boosting"

    assert h1["baseline_persistencia"]["nome"] == "persistence"

    assert h1["modelo_final"]["early_warning"]["alertas"] == 2


def test_build_municipality_index_preserves_identity_and_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Índice municipal deve usar código IBGE e preservar contagens."""
    patch_test_constants(monkeypatch)

    payload = serving.build_municipality_index(build_test_predictions())

    assert payload["count"] == 2

    assert payload["items"][0] == {
        "codigo_ibge_7": "1111111",
        "nome_municipio_ibge": "Município A",
        "nome_uf_ibge": "Estado A",
        "predicoes": 5,
        "horizontes": {
            "h1": 2,
            "h2": 1,
            "h3": 1,
            "h4": 1,
        },
    }


def test_write_json_rejects_nan(
    tmp_path: Path,
) -> None:
    """Contratos JSON não podem conter NaN."""
    output = tmp_path / "invalid.json"

    with pytest.raises(
        ValueError,
    ):
        serving.write_json(
            output,
            {"score": float("nan")},
        )


def test_generate_contracts_writes_four_cross_validated_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Geração deve criar os quatro contratos globais validados."""
    patch_test_constants(monkeypatch)

    metadata_file = tmp_path / "metadata" / "model.json"

    overview_file = tmp_path / "evaluation" / "overview.json"

    by_horizon_file = tmp_path / "evaluation" / "by_horizon.json"

    index_file = tmp_path / "municipality" / "index.json"

    monkeypatch.setattr(
        serving,
        "MODEL_METADATA_FILE",
        metadata_file,
    )

    monkeypatch.setattr(
        serving,
        "EVALUATION_OVERVIEW_FILE",
        overview_file,
    )

    monkeypatch.setattr(
        serving,
        "EVALUATION_BY_HORIZON_FILE",
        by_horizon_file,
    )

    monkeypatch.setattr(
        serving,
        "MUNICIPALITY_INDEX_FILE",
        index_file,
    )

    result = serving.generate_contracts(
        build_test_predictions(),
        build_test_audit(),
        build_test_evaluation(),
    )

    assert result["files"] == 4

    assert result["municipalities"] == 2

    assert result["predictions"] == 10

    for path in (
        metadata_file,
        overview_file,
        by_horizon_file,
        index_file,
    ):
        assert path.exists()

    overview = json.loads(overview_file.read_text(encoding="utf-8"))

    index = json.loads(index_file.read_text(encoding="utf-8"))

    assert overview["linhas"] == 10

    assert overview["horizontes"]["h1"]["early_warning_alertas"] == 2

    assert index["count"] == 2

    assert sum(item["predicoes"] for item in index["items"]) == 10
