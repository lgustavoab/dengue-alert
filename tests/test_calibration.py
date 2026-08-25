"""Testes da calibração probabilística."""

import numpy as np
import pytest

from dengue_alert.evaluation.calibration import (
    CALIBRATION_METHODS,
    fit_calibrator,
    probability_to_logit,
)


def make_calibration_data() -> tuple[np.ndarray, np.ndarray]:
    """Cria uma pequena amostra binária para calibração."""
    scores = np.array(
        [
            0.02,
            0.05,
            0.10,
            0.20,
            0.30,
            0.60,
            0.70,
            0.80,
            0.90,
            0.98,
        ],
        dtype=np.float64,
    )

    targets = np.array(
        [
            0,
            0,
            0,
            0,
            1,
            0,
            1,
            1,
            1,
            1,
        ],
        dtype=np.int8,
    )

    return scores, targets


def test_probability_to_logit_is_finite_at_boundaries() -> None:
    """Probabilidades zero e um devem resultar em logits finitos."""
    logits = probability_to_logit(
        [
            0.0,
            0.5,
            1.0,
        ]
    )

    assert np.isfinite(logits).all()

    assert logits[0] < 0

    assert logits[1] == pytest.approx(0.0)

    assert logits[2] > 0


@pytest.mark.parametrize(
    "method",
    CALIBRATION_METHODS,
)
def test_calibrators_return_valid_probabilities(
    method: str,
) -> None:
    """Todos os métodos devem produzir probabilidades válidas."""
    scores, targets = make_calibration_data()

    calibrator = fit_calibrator(
        method,
        scores,
        targets,
    )

    calibrated = calibrator.predict(scores)

    assert calibrated.shape == (len(scores),)

    assert np.isfinite(calibrated).all()

    assert ((calibrated >= 0) & (calibrated <= 1)).all()


def test_raw_calibration_preserves_scores() -> None:
    """O método raw não deve modificar as probabilidades."""
    scores, targets = make_calibration_data()

    calibrator = fit_calibrator(
        "raw",
        scores,
        targets,
    )

    calibrated = calibrator.predict(scores)

    np.testing.assert_allclose(
        calibrated,
        scores,
    )


def test_unknown_calibration_method_is_rejected() -> None:
    """Métodos desconhecidos devem falhar explicitamente."""
    scores, targets = make_calibration_data()

    with pytest.raises(
        ValueError,
        match="Método de calibração inválido",
    ):
        fit_calibrator(
            "desconhecido",
            scores,
            targets,
        )


def test_calibration_requires_both_classes() -> None:
    """A calibração deve possuir exemplos das duas classes."""
    with pytest.raises(
        ValueError,
        match="classes 0 e 1",
    ):
        fit_calibrator(
            "sigmoid",
            [
                0.1,
                0.2,
                0.3,
            ],
            [
                0,
                0,
                0,
            ],
        )
