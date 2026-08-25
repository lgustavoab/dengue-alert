"""Calibração probabilística temporal do Dengue Alert."""

from dataclasses import dataclass

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

CALIBRATION_METHODS = (
    "raw",
    "sigmoid",
    "isotonic",
)

PROBABILITY_EPSILON = 1e-6
RANDOM_STATE = 42


def validate_calibration_arrays(
    scores,
    targets,
) -> tuple[np.ndarray, np.ndarray]:
    """Valida scores e targets utilizados na calibração."""
    score_array = np.asarray(
        scores,
        dtype=np.float64,
    )

    target_array = np.asarray(
        targets,
        dtype=np.int8,
    )

    if score_array.ndim != 1:
        raise ValueError("Os scores de calibração devem possuir uma dimensão.")

    if target_array.ndim != 1:
        raise ValueError("Os targets de calibração devem possuir uma dimensão.")

    if len(score_array) != len(target_array):
        raise ValueError("Scores e targets devem possuir o mesmo comprimento.")

    if len(score_array) == 0:
        raise ValueError("A calibração requer pelo menos uma observação.")

    if not np.isfinite(score_array).all():
        raise ValueError("Os scores possuem valores não finitos.")

    if ((score_array < 0) | (score_array > 1)).any():
        raise ValueError("Os scores devem permanecer no intervalo [0, 1].")

    classes = np.unique(target_array)

    if not np.array_equal(
        classes,
        np.array(
            [0, 1],
            dtype=classes.dtype,
        ),
    ):
        raise ValueError("O conjunto de calibração deve conter as classes 0 e 1.")

    return (
        score_array,
        target_array,
    )


def probability_to_logit(
    scores,
) -> np.ndarray:
    """Converte probabilidades em log-odds de forma numericamente segura."""
    score_array = np.asarray(
        scores,
        dtype=np.float64,
    )

    clipped = np.clip(
        score_array,
        PROBABILITY_EPSILON,
        1.0 - PROBABILITY_EPSILON,
    )

    return np.log(clipped / (1.0 - clipped))


@dataclass
class RawCalibrator:
    """Mantém as probabilidades originais sem transformação."""

    def predict(
        self,
        scores,
    ) -> np.ndarray:
        """Retorna os scores originais após validação básica."""
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

        return score_array.copy()


@dataclass
class SigmoidCalibrator:
    """Implementa Platt scaling sobre o logit da probabilidade original."""

    model: LogisticRegression

    def predict(
        self,
        scores,
    ) -> np.ndarray:
        """Aplica a transformação sigmoidal aprendida."""
        logits = probability_to_logit(scores).reshape(
            -1,
            1,
        )

        return self.model.predict_proba(logits)[:, 1]


@dataclass
class IsotonicCalibrator:
    """Aplica regressão isotônica às probabilidades originais."""

    model: IsotonicRegression

    def predict(
        self,
        scores,
    ) -> np.ndarray:
        """Aplica a função isotônica aprendida."""
        score_array = np.asarray(
            scores,
            dtype=np.float64,
        )

        calibrated = self.model.predict(score_array)

        return np.asarray(
            calibrated,
            dtype=np.float64,
        )


def fit_calibrator(
    method: str,
    scores,
    targets,
):
    """Ajusta o método de calibração solicitado."""
    if method not in CALIBRATION_METHODS:
        raise ValueError(
            f"Método de calibração inválido. Opções: {', '.join(CALIBRATION_METHODS)}."
        )

    score_array, target_array = validate_calibration_arrays(
        scores,
        targets,
    )

    if method == "raw":
        return RawCalibrator()

    if method == "sigmoid":
        logits = probability_to_logit(score_array).reshape(
            -1,
            1,
        )

        model = LogisticRegression(
            solver="lbfgs",
            random_state=RANDOM_STATE,
        )

        model.fit(
            logits,
            target_array,
        )

        return SigmoidCalibrator(model=model)

    model = IsotonicRegression(
        out_of_bounds="clip",
    )

    model.fit(
        score_array,
        target_array,
    )

    return IsotonicCalibrator(model=model)
