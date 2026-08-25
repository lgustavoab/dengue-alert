"""Baselines oficiais da modelagem do Dengue Alert."""

from collections.abc import Sequence

import pandas as pd


def persistence_predictions(
    current_risk: Sequence,
) -> tuple[pd.Series, pd.Series]:
    """Usa o estado de risco atual como previsão do estado futuro."""
    risk = pd.Series(
        current_risk,
        dtype="boolean",
    )

    if risk.isna().any():
        missing = int(risk.isna().sum())

        raise ValueError(
            f"O baseline de persistência recebeu {missing:,} estados atuais ausentes."
        )

    prediction = risk.copy()

    score = risk.astype("float64")

    return score, prediction
