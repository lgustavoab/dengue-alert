"""Métricas oficiais de avaliação preditiva do Dengue Alert."""

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def _prepare_boolean_series(
    values: Sequence,
    *,
    name: str,
) -> pd.Series:
    """Normaliza uma sequência binária e rejeita valores ausentes."""
    series = pd.Series(
        values,
        dtype="boolean",
    )

    if series.isna().any():
        missing = int(series.isna().sum())

        raise ValueError(f"{name} possui {missing:,} valores ausentes.")

    return series


def _prepare_probability_series(
    values: Sequence,
    *,
    name: str,
) -> pd.Series:
    """Normaliza probabilidades e valida o intervalo [0, 1]."""
    series = pd.Series(
        values,
        dtype="float64",
    )

    if series.isna().any():
        missing = int(series.isna().sum())

        raise ValueError(f"{name} possui {missing:,} valores ausentes.")

    array = series.to_numpy(
        dtype="float64",
        copy=False,
    )

    invalid_finite = int((~np.isfinite(array)).sum())

    if invalid_finite:
        raise ValueError(f"{name} possui {invalid_finite:,} valores não finitos.")

    invalid_range = int(((array < 0) | (array > 1)).sum())

    if invalid_range:
        raise ValueError(
            f"{name} possui {invalid_range:,} valores fora do intervalo [0, 1]."
        )

    return series


def evaluate_binary_predictions(
    y_true: Sequence,
    y_score: Sequence,
    y_pred: Sequence,
) -> dict:
    """Calcula as métricas oficiais para um problema binário.

    A métrica PR-AUC é operacionalizada como Average Precision (AP).
    """
    true = _prepare_boolean_series(
        y_true,
        name="y_true",
    )

    score = _prepare_probability_series(
        y_score,
        name="y_score",
    )

    prediction = _prepare_boolean_series(
        y_pred,
        name="y_pred",
    )

    lengths = {
        len(true),
        len(score),
        len(prediction),
    }

    if len(lengths) != 1:
        raise ValueError("y_true, y_score e y_pred devem possuir o mesmo comprimento.")

    if len(true) == 0:
        raise ValueError("A avaliação requer pelo menos uma observação.")

    true_array = true.astype("int8").to_numpy()

    score_array = score.to_numpy(
        dtype="float64",
        copy=False,
    )

    prediction_array = prediction.astype("int8").to_numpy()

    negatives = int((true_array == 0).sum())

    positives = int((true_array == 1).sum())

    matrix = confusion_matrix(
        true_array,
        prediction_array,
        labels=[0, 1],
    )

    true_negative = int(matrix[0, 0])

    false_positive = int(matrix[0, 1])

    false_negative = int(matrix[1, 0])

    true_positive = int(matrix[1, 1])

    if positives:
        pr_auc = float(
            average_precision_score(
                true_array,
                score_array,
            )
        )
    else:
        pr_auc = None

    if positives and negatives:
        roc_auc = float(
            roc_auc_score(
                true_array,
                score_array,
            )
        )

        balanced_accuracy = float(
            balanced_accuracy_score(
                true_array,
                prediction_array,
            )
        )
    else:
        roc_auc = None
        balanced_accuracy = None

    return {
        "observacoes": len(true),
        "positivos": positives,
        "negativos": negatives,
        "prevalencia": (positives / len(true)),
        "pr_auc_average_precision": pr_auc,
        "roc_auc": roc_auc,
        "recall": float(
            recall_score(
                true_array,
                prediction_array,
                zero_division=0,
            )
        ),
        "precision": float(
            precision_score(
                true_array,
                prediction_array,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                true_array,
                prediction_array,
                zero_division=0,
            )
        ),
        "balanced_accuracy": balanced_accuracy,
        "brier_score": float(
            brier_score_loss(
                true_array,
                score_array,
            )
        ),
        "matriz_confusao": {
            "tn": true_negative,
            "fp": false_positive,
            "fn": false_negative,
            "tp": true_positive,
        },
    }
