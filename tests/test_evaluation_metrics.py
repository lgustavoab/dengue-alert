"""Testes das métricas oficiais de avaliação."""

import pytest

from dengue_alert.evaluation.metrics import (
    evaluate_binary_predictions,
)


def test_perfect_predictions_have_perfect_metrics() -> None:
    """Predições perfeitas devem produzir métricas ideais."""
    result = evaluate_binary_predictions(
        y_true=[
            False,
            False,
            True,
            True,
        ],
        y_score=[
            0.0,
            0.1,
            0.9,
            1.0,
        ],
        y_pred=[
            False,
            False,
            True,
            True,
        ],
    )

    assert result["pr_auc_average_precision"] == pytest.approx(1.0)

    assert result["roc_auc"] == pytest.approx(1.0)

    assert result["recall"] == pytest.approx(1.0)

    assert result["precision"] == pytest.approx(1.0)

    assert result["f1"] == pytest.approx(1.0)

    assert result["balanced_accuracy"] == pytest.approx(1.0)

    assert result["brier_score"] < 0.01


def test_confusion_matrix_is_calculated() -> None:
    """A matriz de confusão deve refletir as classificações."""
    result = evaluate_binary_predictions(
        y_true=[
            False,
            False,
            True,
            True,
        ],
        y_score=[
            0.2,
            0.8,
            0.3,
            0.9,
        ],
        y_pred=[
            False,
            True,
            False,
            True,
        ],
    )

    assert result["matriz_confusao"] == {
        "tn": 1,
        "fp": 1,
        "fn": 1,
        "tp": 1,
    }


def test_roc_auc_is_none_with_single_class() -> None:
    """Métricas dependentes de duas classes não devem ser calculadas."""
    result = evaluate_binary_predictions(
        y_true=[
            False,
            False,
            False,
        ],
        y_score=[
            0.0,
            0.0,
            0.0,
        ],
        y_pred=[
            False,
            False,
            False,
        ],
    )

    assert result["roc_auc"] is None

    assert result["pr_auc_average_precision"] is None

    assert result["balanced_accuracy"] is None


def test_missing_target_is_rejected() -> None:
    """Targets ausentes devem impedir a avaliação."""
    with pytest.raises(
        ValueError,
        match="y_true",
    ):
        evaluate_binary_predictions(
            y_true=[
                True,
                None,
            ],
            y_score=[
                1.0,
                0.0,
            ],
            y_pred=[
                True,
                False,
            ],
        )


def test_invalid_probability_is_rejected() -> None:
    """Scores probabilísticos devem permanecer entre zero e um."""
    with pytest.raises(
        ValueError,
        match=r"\[0, 1\]",
    ):
        evaluate_binary_predictions(
            y_true=[
                False,
                True,
            ],
            y_score=[
                0.0,
                1.2,
            ],
            y_pred=[
                False,
                True,
            ],
        )
