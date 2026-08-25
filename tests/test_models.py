"""Testes dos modelos candidatos."""

import numpy as np
import pytest
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.pipeline import Pipeline

from dengue_alert.modeling.models import (
    ModelName,
    build_model,
)


def make_training_data() -> tuple[np.ndarray, np.ndarray]:
    """Cria pequeno conjunto binário sintético."""
    x = np.array(
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
        dtype="float64",
    )

    y = np.array(
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
        dtype="int8",
    )

    return x, y


def test_logistic_regression_is_pipeline() -> None:
    """Regressão logística deve incorporar scaling no pipeline."""
    model = build_model(ModelName.LOGISTIC_REGRESSION)

    assert isinstance(
        model,
        Pipeline,
    )

    assert list(model.named_steps) == [
        "scaler",
        "classifier",
    ]


def test_hist_gradient_boosting_is_created() -> None:
    """Gradient boosting deve ser construído com a configuração esperada."""
    model = build_model(ModelName.HIST_GRADIENT_BOOSTING)

    assert isinstance(
        model,
        HistGradientBoostingClassifier,
    )

    assert model.learning_rate == pytest.approx(0.1)

    assert model.max_iter == 100

    assert model.early_stopping is False


@pytest.mark.parametrize(
    "model_name",
    list(ModelName),
)
def test_candidate_models_fit_and_predict_probabilities(
    model_name: ModelName,
) -> None:
    """Todos os modelos oficiais devem treinar e produzir probabilidades."""
    x, y = make_training_data()

    model = build_model(model_name)

    model.fit(
        x,
        y,
    )

    probability = model.predict_proba(x)[:, 1]

    prediction = model.predict(x)

    assert probability.shape == (len(x),)

    assert prediction.shape == (len(x),)

    assert np.isfinite(probability).all()

    assert ((probability >= 0) & (probability <= 1)).all()


def test_unknown_model_is_rejected() -> None:
    """Identificadores desconhecidos devem falhar explicitamente."""
    with pytest.raises(
        ValueError,
        match="Modelo inválido",
    ):
        build_model("modelo_inexistente")
