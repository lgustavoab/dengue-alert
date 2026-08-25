"""Testes da infraestrutura de treinamento e avaliação."""

import numpy as np
import pandas as pd
import pytest

from dengue_alert.modeling.models import ModelName
from dengue_alert.modeling.training import (
    DEFAULT_DECISION_THRESHOLD,
    EPIDEMIOLOGICAL_FEATURES,
    evaluate_model_predictions,
    fit_candidate_model,
    positive_class_probabilities,
    predictions_from_scores,
    prepare_model_matrix,
)


def test_epidemiological_feature_set_has_23_features() -> None:
    """O Modelo A deve utilizar exatamente 23 features epidemiológicas."""
    assert len(EPIDEMIOLOGICAL_FEATURES) == 23

    assert "risco_elevado" in EPIDEMIOLOGICAL_FEATURES

    assert "temperatura_media_c_lag_0" not in EPIDEMIOLOGICAL_FEATURES

    assert "latitude_sede" not in EPIDEMIOLOGICAL_FEATURES


def test_prepare_model_matrix_returns_float32() -> None:
    """A matriz de modelagem deve ser convertida para float32."""
    dataframe = pd.DataFrame(
        {
            "feature_a": [
                1.0,
                2.0,
            ],
            "feature_b": [
                3.0,
                4.0,
            ],
        }
    )

    matrix = prepare_model_matrix(
        dataframe,
        (
            "feature_a",
            "feature_b",
        ),
    )

    assert matrix.shape == (
        2,
        2,
    )

    assert matrix.dtype == np.float32


def test_prepare_model_matrix_rejects_missing_feature() -> None:
    """Features inexistentes devem impedir a preparação da matriz."""
    dataframe = pd.DataFrame(
        {
            "feature_a": [
                1.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="Features ausentes",
    ):
        prepare_model_matrix(
            dataframe,
            (
                "feature_a",
                "feature_b",
            ),
        )


def test_prepare_model_matrix_rejects_non_finite_values() -> None:
    """Valores não finitos não devem chegar ao treinamento."""
    dataframe = pd.DataFrame(
        {
            "feature_a": [
                1.0,
                np.inf,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="não finitos",
    ):
        prepare_model_matrix(
            dataframe,
            ("feature_a",),
        )


def test_predictions_use_fixed_threshold() -> None:
    """Scores devem ser classificados com threshold fixo de 0,5."""
    scores = np.array(
        [
            0.10,
            0.49,
            0.50,
            0.90,
        ]
    )

    predictions = predictions_from_scores(
        scores,
        threshold=(DEFAULT_DECISION_THRESHOLD),
    )

    expected = np.array(
        [
            False,
            False,
            True,
            True,
        ]
    )

    np.testing.assert_array_equal(
        predictions,
        expected,
    )


@pytest.mark.parametrize(
    "model_name",
    list(ModelName),
)
def test_candidate_models_train_and_return_probabilities(
    model_name: ModelName,
) -> None:
    """Os candidatos devem treinar e retornar probabilidades válidas."""
    x_train = np.array(
        [
            [0.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [2.0, 1.0],
            [2.0, 2.0],
            [3.0, 2.0],
            [3.0, 3.0],
        ],
        dtype=np.float32,
    )

    y_train = np.array(
        [
            0,
            0,
            0,
            0,
            1,
            1,
            1,
            1,
        ],
        dtype=np.int8,
    )

    model = fit_candidate_model(
        model_name,
        x_train,
        y_train,
    )

    probabilities = positive_class_probabilities(
        model,
        x_train,
    )

    assert probabilities.shape == (len(x_train),)

    assert np.isfinite(probabilities).all()

    assert ((probabilities >= 0) & (probabilities <= 1)).all()


def test_evaluation_separates_early_warning_subset() -> None:
    """Early warning deve considerar somente risco atual negativo."""
    result = evaluate_model_predictions(
        y_true=[
            False,
            True,
            True,
            False,
            True,
        ],
        y_score=[
            0.10,
            0.80,
            0.70,
            0.20,
            0.60,
        ],
        current_risk=[
            False,
            False,
            True,
            False,
            True,
        ],
    )

    general = result["avaliacao_geral"]

    early = result["early_warning"]

    assert general["observacoes"] == 5

    assert early["observacoes"] == 3

    assert early["positivos"] == 1

    assert early["negativos"] == 2

    assert early["recall"] == pytest.approx(1.0)
