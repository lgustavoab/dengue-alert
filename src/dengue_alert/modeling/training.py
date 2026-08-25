"""Infraestrutura de treinamento e avaliação dos modelos do Dengue Alert."""

from collections.abc import Sequence

import numpy as np
import pandas as pd

from dengue_alert.evaluation.metrics import evaluate_binary_predictions
from dengue_alert.modeling.models import ModelName, build_model

CURRENT_RISK_COLUMN = "risco_elevado"

DEFAULT_DECISION_THRESHOLD = 0.5

EPIDEMIOLOGICAL_FEATURES = (
    "incidencia_100mil",
    "incidencia_100mil_lag_1",
    "incidencia_100mil_lag_2",
    "incidencia_100mil_lag_3",
    "incidencia_100mil_lag_4",
    "incidencia_100mil_lag_5",
    "incidencia_100mil_lag_6",
    "incidencia_100mil_lag_7",
    "incidencia_100mil_lag_8",
    "incidencia_media_2s",
    "incidencia_media_4s",
    "incidencia_media_8s",
    "incidencia_4s_100mil",
    "incidencia_4s_lag_1",
    "incidencia_4s_lag_4",
    "delta_incidencia_4s_1s",
    "delta_incidencia_4s_4s",
    "limiar_sazonal_p90",
    "margem_limiar_p90",
    "risco_elevado",
    "semana_sin",
    "semana_cos",
    "log_populacao",
)

CLIMATE_FEATURES = (
    "temperatura_media_c_lag_0",
    "temperatura_media_c_lag_1",
    "temperatura_media_c_lag_2",
    "temperatura_media_c_lag_3",
    "temperatura_media_c_lag_4",
    "temperatura_media_c_lag_5",
    "temperatura_media_c_lag_6",
    "temperatura_media_c_lag_7",
    "temperatura_media_c_lag_8",
    "umidade_relativa_media_pct_lag_0",
    "umidade_relativa_media_pct_lag_1",
    "umidade_relativa_media_pct_lag_2",
    "umidade_relativa_media_pct_lag_3",
    "umidade_relativa_media_pct_lag_4",
    "umidade_relativa_media_pct_lag_5",
    "umidade_relativa_media_pct_lag_6",
    "umidade_relativa_media_pct_lag_7",
    "umidade_relativa_media_pct_lag_8",
    "precipitacao_total_mm_lag_0",
    "precipitacao_total_mm_lag_1",
    "precipitacao_total_mm_lag_2",
    "precipitacao_total_mm_lag_3",
    "precipitacao_total_mm_lag_4",
    "precipitacao_total_mm_lag_5",
    "precipitacao_total_mm_lag_6",
    "precipitacao_total_mm_lag_7",
    "precipitacao_total_mm_lag_8",
    "temperatura_media_media_2s",
    "temperatura_media_media_4s",
    "temperatura_media_media_8s",
    "umidade_relativa_media_2s",
    "umidade_relativa_media_4s",
    "umidade_relativa_media_8s",
    "precipitacao_acumulada_2s",
    "precipitacao_acumulada_4s",
    "precipitacao_acumulada_8s",
)


EPIDEMIOLOGICAL_CLIMATE_FEATURES = (
    *EPIDEMIOLOGICAL_FEATURES,
    *CLIMATE_FEATURES,
)


def validate_feature_columns(
    dataframe: pd.DataFrame,
    feature_columns: Sequence[str],
) -> None:
    """Valida se todas as features solicitadas existem no dataset."""
    missing = [column for column in feature_columns if column not in dataframe.columns]

    if missing:
        raise ValueError("Features ausentes no dataset: " + ", ".join(missing) + ".")


def prepare_model_matrix(
    dataframe: pd.DataFrame,
    feature_columns: Sequence[str],
) -> np.ndarray:
    """Converte as features para uma matriz numérica float32 validada."""
    validate_feature_columns(
        dataframe,
        feature_columns,
    )

    matrix = dataframe.loc[
        :,
        list(feature_columns),
    ].to_numpy(
        dtype=np.float32,
        copy=True,
    )

    if matrix.ndim != 2:
        raise ValueError("A matriz de features deve possuir duas dimensões.")

    if matrix.shape[1] != len(feature_columns):
        raise ValueError("Quantidade inesperada de colunas na matriz de features.")

    non_finite = int((~np.isfinite(matrix)).sum())

    if non_finite:
        raise ValueError(
            f"A matriz de features possui {non_finite:,} valores não finitos."
        )

    return matrix


def prepare_binary_target(
    values: Sequence,
    *,
    name: str,
) -> np.ndarray:
    """Converte um target binário para int8 e rejeita valores ausentes."""
    series = pd.Series(
        values,
        dtype="boolean",
    )

    if series.isna().any():
        missing = int(series.isna().sum())

        raise ValueError(f"{name} possui {missing:,} valores ausentes.")

    return series.astype("int8").to_numpy()


def validate_training_target(
    target: np.ndarray,
) -> None:
    """Garante que o treinamento contém as duas classes."""
    classes = np.unique(target)

    if not np.array_equal(
        classes,
        np.array(
            [0, 1],
            dtype=classes.dtype,
        ),
    ):
        raise ValueError("O conjunto de treinamento deve conter as classes 0 e 1.")


def fit_candidate_model(
    model_name: ModelName | str,
    x_train: np.ndarray,
    y_train: np.ndarray,
):
    """Treina um dos modelos candidatos oficiais."""
    if x_train.ndim != 2:
        raise ValueError("x_train deve possuir duas dimensões.")

    if y_train.ndim != 1:
        raise ValueError("y_train deve possuir uma dimensão.")

    if len(x_train) != len(y_train):
        raise ValueError(
            "x_train e y_train devem possuir o mesmo número de observações."
        )

    validate_training_target(y_train)

    model = build_model(model_name)

    model.fit(
        x_train,
        y_train,
    )

    return model


def positive_class_probabilities(
    model,
    features: np.ndarray,
) -> np.ndarray:
    """Obtém a probabilidade estimada para a classe positiva."""
    probabilities = np.asarray(
        model.predict_proba(features),
        dtype=np.float64,
    )

    if probabilities.ndim != 2:
        raise ValueError("predict_proba retornou uma estrutura inesperada.")

    if probabilities.shape[1] != 2:
        raise ValueError(
            "O modelo deve produzir probabilidades para exatamente duas classes."
        )

    classes = np.asarray(model.classes_)

    if not np.array_equal(
        classes,
        np.array(
            [0, 1],
            dtype=classes.dtype,
        ),
    ):
        raise ValueError("O modelo treinado deve possuir as classes [0, 1].")

    positive = probabilities[
        :,
        1,
    ]

    if not np.isfinite(positive).all():
        raise ValueError("O modelo produziu probabilidades não finitas.")

    if ((positive < 0) | (positive > 1)).any():
        raise ValueError("O modelo produziu probabilidades fora do intervalo [0, 1].")

    return positive


def predictions_from_scores(
    scores: Sequence,
    *,
    threshold: float = DEFAULT_DECISION_THRESHOLD,
) -> np.ndarray:
    """Transforma probabilidades em classificações por threshold."""
    if not 0 < threshold < 1:
        raise ValueError("O threshold deve estar estritamente entre 0 e 1.")

    score_array = np.asarray(
        scores,
        dtype=np.float64,
    )

    if score_array.ndim != 1:
        raise ValueError("Os scores devem possuir uma dimensão.")

    if not np.isfinite(score_array).all():
        raise ValueError("Os scores possuem valores não finitos.")

    if ((score_array < 0) | (score_array > 1)).any():
        raise ValueError("Os scores devem permanecer no intervalo [0, 1].")

    return score_array >= threshold


def evaluate_model_predictions(
    *,
    y_true: Sequence,
    y_score: Sequence,
    current_risk: Sequence,
    threshold: float = DEFAULT_DECISION_THRESHOLD,
) -> dict:
    """Avalia previsões gerais e no subconjunto de early warning."""
    target = prepare_binary_target(
        y_true,
        name="y_true",
    )

    current = pd.Series(
        current_risk,
        dtype="boolean",
    )

    if current.isna().any():
        missing = int(current.isna().sum())

        raise ValueError(f"current_risk possui {missing:,} valores ausentes.")

    scores = np.asarray(
        y_score,
        dtype=np.float64,
    )

    lengths = {
        len(target),
        len(scores),
        len(current),
    }

    if len(lengths) != 1:
        raise ValueError(
            "y_true, y_score e current_risk devem possuir o mesmo comprimento."
        )

    predictions = predictions_from_scores(
        scores,
        threshold=threshold,
    )

    general = evaluate_binary_predictions(
        y_true=target,
        y_score=scores,
        y_pred=predictions,
    )

    current_array = current.astype("bool").to_numpy()

    early_warning_mask = ~current_array

    early_warning_rows = int(early_warning_mask.sum())

    if early_warning_rows == 0:
        raise ValueError(
            "Não existem observações disponíveis para a avaliação de early warning."
        )

    early_warning = evaluate_binary_predictions(
        y_true=target[early_warning_mask],
        y_score=scores[early_warning_mask],
        y_pred=predictions[early_warning_mask],
    )

    return {
        "threshold": threshold,
        "avaliacao_geral": general,
        "early_warning": early_warning,
    }
