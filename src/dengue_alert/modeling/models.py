"""Modelos candidatos oficiais do Dengue Alert."""

from enum import StrEnum

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42


class ModelName(StrEnum):
    """Identificadores oficiais dos modelos candidatos."""

    LOGISTIC_REGRESSION = "logistic_regression"
    HIST_GRADIENT_BOOSTING = "hist_gradient_boosting"


def build_logistic_regression() -> Pipeline:
    """Constrói a regressão logística com padronização no próprio pipeline."""
    return Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1_000,
                    solver="lbfgs",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def build_hist_gradient_boosting() -> HistGradientBoostingClassifier:
    """Constrói o modelo não linear de gradient boosting."""
    return HistGradientBoostingClassifier(
        learning_rate=0.1,
        max_iter=100,
        early_stopping=False,
        random_state=RANDOM_STATE,
    )


def build_model(
    model_name: ModelName | str,
):
    """Constrói um modelo candidato a partir de seu identificador."""
    try:
        model = ModelName(model_name)
    except ValueError as error:
        valid = ", ".join(item.value for item in ModelName)

        raise ValueError(f"Modelo inválido. Opções disponíveis: {valid}.") from error

    if model is ModelName.LOGISTIC_REGRESSION:
        return build_logistic_regression()

    if model is ModelName.HIST_GRADIENT_BOOSTING:
        return build_hist_gradient_boosting()

    raise RuntimeError(f"Modelo não implementado: {model}.")
