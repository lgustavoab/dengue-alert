"""Testes da seleção operacional de thresholds."""

import pytest

from dengue_alert.evaluation.thresholds import (
    evaluate_threshold,
    select_f1_threshold,
)


def test_select_f1_threshold_finds_expected_cutoff() -> None:
    """A seleção deve encontrar o ponto de maior F1."""
    result = select_f1_threshold(
        y_true=[
            True,
            False,
            True,
            False,
        ],
        y_score=[
            0.9,
            0.8,
            0.7,
            0.1,
        ],
    )

    assert result["threshold"] == pytest.approx(0.7)

    assert result["precision"] == pytest.approx(2 / 3)

    assert result["recall"] == pytest.approx(1.0)

    assert result["f1"] == pytest.approx(0.8)


def test_threshold_tie_uses_highest_cutoff() -> None:
    """Empates de F1 devem favorecer o maior threshold."""
    result = select_f1_threshold(
        y_true=[
            True,
            False,
            False,
            True,
        ],
        y_score=[
            0.9,
            0.8,
            0.7,
            0.6,
        ],
    )

    assert result["threshold"] == pytest.approx(0.9)

    assert result["regra_desempate"] == "maior_threshold"


def test_evaluate_threshold_calculates_confusion_matrix() -> None:
    """A avaliação deve contabilizar corretamente os alertas."""
    result = evaluate_threshold(
        y_true=[
            False,
            True,
            False,
            True,
        ],
        y_score=[
            0.1,
            0.8,
            0.7,
            0.2,
        ],
        threshold=0.5,
    )

    assert result["matriz_confusao"] == {
        "tn": 1,
        "fp": 1,
        "fn": 1,
        "tp": 1,
    }

    assert result["alertas"] == 2

    assert result["proporcao_alertas"] == pytest.approx(0.5)


def test_threshold_selection_requires_both_classes() -> None:
    """A seleção exige observações positivas e negativas."""
    with pytest.raises(
        ValueError,
        match="classes 0 e 1",
    ):
        select_f1_threshold(
            y_true=[
                False,
                False,
                False,
            ],
            y_score=[
                0.1,
                0.2,
                0.3,
            ],
        )


def test_threshold_rejects_invalid_score() -> None:
    """Scores fora do domínio probabilístico devem falhar."""
    with pytest.raises(
        ValueError,
        match=r"\[0, 1\]",
    ):
        select_f1_threshold(
            y_true=[
                False,
                True,
            ],
            y_score=[
                0.2,
                1.1,
            ],
        )
