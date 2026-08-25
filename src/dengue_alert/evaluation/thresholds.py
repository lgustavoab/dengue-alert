"""Seleção operacional de thresholds do Dengue Alert."""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

TIE_TOLERANCE = 1e-12


def _prepare_threshold_arrays(
    y_true: Sequence,
    y_score: Sequence,
) -> tuple[np.ndarray, np.ndarray]:
    """Valida target e scores usados na seleção de threshold."""
    target = pd.Series(
        y_true,
        dtype="boolean",
    )

    if target.isna().any():
        missing = int(target.isna().sum())

        raise ValueError(f"y_true possui {missing:,} valores ausentes.")

    scores = np.asarray(
        y_score,
        dtype=np.float64,
    )

    if scores.ndim != 1:
        raise ValueError("y_score deve possuir uma dimensão.")

    if len(target) != len(scores):
        raise ValueError("y_true e y_score devem possuir o mesmo comprimento.")

    if len(target) == 0:
        raise ValueError("A seleção de threshold requer pelo menos uma observação.")

    if not np.isfinite(scores).all():
        raise ValueError("y_score possui valores não finitos.")

    if ((scores < 0) | (scores > 1)).any():
        raise ValueError("y_score deve permanecer no intervalo [0, 1].")

    target_array = target.astype("int8").to_numpy()

    classes = np.unique(target_array)

    if not np.array_equal(
        classes,
        np.array(
            [0, 1],
            dtype=classes.dtype,
        ),
    ):
        raise ValueError("A seleção de threshold requer as classes 0 e 1.")

    return (
        target_array,
        scores,
    )


def evaluate_threshold(
    y_true: Sequence,
    y_score: Sequence,
    *,
    threshold: float,
) -> dict:
    """Avalia um threshold binário específico."""
    target, scores = _prepare_threshold_arrays(
        y_true,
        y_score,
    )

    if not 0 <= threshold <= 1:
        raise ValueError("O threshold deve permanecer no intervalo [0, 1].")

    prediction = scores >= threshold

    positives = target == 1

    negatives = target == 0

    true_positive = int((prediction & positives).sum())

    false_positive = int((prediction & negatives).sum())

    false_negative = int((~prediction & positives).sum())

    true_negative = int((~prediction & negatives).sum())

    predicted_positive = true_positive + false_positive

    actual_positive = true_positive + false_negative

    precision = true_positive / predicted_positive if predicted_positive else 0.0

    recall = true_positive / actual_positive if actual_positive else 0.0

    denominator = precision + recall

    f1 = 2 * precision * recall / denominator if denominator else 0.0

    observations = len(target)

    alerts = predicted_positive

    return {
        "threshold": float(threshold),
        "observacoes": observations,
        "positivos": int(positives.sum()),
        "negativos": int(negatives.sum()),
        "alertas": alerts,
        "proporcao_alertas": (alerts / observations),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "matriz_confusao": {
            "tn": true_negative,
            "fp": false_positive,
            "fn": false_negative,
            "tp": true_positive,
        },
    }


def select_f1_threshold(
    y_true: Sequence,
    y_score: Sequence,
) -> dict:
    """Seleciona o threshold que maximiza F1.

    Em caso de empate numérico, escolhe o maior threshold,
    reduzindo a quantidade de alertas sem sacrificar o F1 máximo.
    """
    target, scores = _prepare_threshold_arrays(
        y_true,
        y_score,
    )

    precision, recall, thresholds = precision_recall_curve(
        target,
        scores,
    )

    if len(thresholds) == 0:
        raise ValueError("Não foi possível gerar thresholds candidatos.")

    candidate_precision = precision[:-1]

    candidate_recall = recall[:-1]

    denominator = candidate_precision + candidate_recall

    f1 = np.divide(
        2 * candidate_precision * candidate_recall,
        denominator,
        out=np.zeros_like(denominator),
        where=(denominator > 0),
    )

    maximum_f1 = float(f1.max())

    best_indices = np.flatnonzero(
        np.isclose(
            f1,
            maximum_f1,
            rtol=0.0,
            atol=TIE_TOLERANCE,
        )
    )

    if len(best_indices) == 0:
        raise RuntimeError("Nenhum threshold ótimo foi identificado.")

    best_thresholds = thresholds[best_indices]

    selected_threshold = float(best_thresholds.max())

    result = evaluate_threshold(
        target,
        scores,
        threshold=selected_threshold,
    )

    result["criterio"] = "max_f1"

    result["candidatos"] = len(thresholds)

    result["regra_desempate"] = "maior_threshold"

    return result
