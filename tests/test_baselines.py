"""Testes dos baselines preditivos."""

import pandas as pd
import pytest

from dengue_alert.modeling.baselines import (
    persistence_predictions,
)


def test_persistence_repeats_current_state() -> None:
    """O baseline deve repetir exatamente o risco atual."""
    current = pd.Series(
        [
            False,
            True,
            True,
            False,
        ],
        dtype="boolean",
    )

    score, prediction = persistence_predictions(current)

    expected_prediction = pd.Series(
        [
            False,
            True,
            True,
            False,
        ],
        dtype="boolean",
    )

    expected_score = pd.Series(
        [
            0.0,
            1.0,
            1.0,
            0.0,
        ],
        dtype="float64",
    )

    pd.testing.assert_series_equal(
        prediction,
        expected_prediction,
    )

    pd.testing.assert_series_equal(
        score,
        expected_score,
    )


def test_persistence_rejects_missing_state() -> None:
    """O baseline não deve aceitar risco atual ausente."""
    with pytest.raises(
        ValueError,
        match="ausentes",
    ):
        persistence_predictions(
            [
                False,
                None,
                True,
            ]
        )
