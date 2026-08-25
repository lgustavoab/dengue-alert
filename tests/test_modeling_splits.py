"""Testes das partições temporais da modelagem."""

import pandas as pd
import pytest

from dengue_alert.modeling.splits import (
    DEFAULT_TEMPORAL_FOLDS,
    TemporalFold,
    calculate_future_target_year,
    iter_temporal_fold_masks,
    prepare_temporal_panel,
    target_column_for_horizon,
)


def make_temporal_dataframe() -> pd.DataFrame:
    """Cria série sintética contínua atravessando uma fronteira anual."""
    dates = pd.date_range(
        "2020-12-06",
        periods=10,
        freq="7D",
    )

    years = [
        2020,
        2020,
        2020,
        2020,
        2021,
        2021,
        2021,
        2021,
        2021,
        2021,
    ]

    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": ["1234567"] * 10,
            "ano_epidemiologico": years,
            "data_inicio_semana": dates,
            "target_h1": pd.Series(
                [True] * 9 + [pd.NA],
                dtype="boolean",
            ),
            "target_h2": pd.Series(
                [True] * 8 + [pd.NA, pd.NA],
                dtype="boolean",
            ),
            "target_h3": pd.Series(
                [True] * 7 + [pd.NA] * 3,
                dtype="boolean",
            ),
            "target_h4": pd.Series(
                [True] * 6 + [pd.NA] * 4,
                dtype="boolean",
            ),
        }
    )

    return dataframe


def test_default_folds_are_expanding_window() -> None:
    """Os folds oficiais devem expandir o treino e avançar a validação."""
    assert len(DEFAULT_TEMPORAL_FOLDS) == 4

    assert DEFAULT_TEMPORAL_FOLDS[0] == TemporalFold(
        name="fold_1",
        train_start_year=2018,
        train_end_year=2020,
        validation_year=2021,
    )

    assert DEFAULT_TEMPORAL_FOLDS[3] == TemporalFold(
        name="fold_4",
        train_start_year=2018,
        train_end_year=2023,
        validation_year=2024,
    )


@pytest.mark.parametrize(
    ("horizon", "expected"),
    [
        (1, "target_h1"),
        (2, "target_h2"),
        (3, "target_h3"),
        (4, "target_h4"),
    ],
)
def test_target_column_for_valid_horizon(
    horizon: int,
    expected: str,
) -> None:
    """Horizontes válidos devem mapear para as colunas oficiais."""
    assert target_column_for_horizon(horizon) == expected


def test_invalid_horizon_is_rejected() -> None:
    """Horizontes fora da especificação oficial devem falhar."""
    with pytest.raises(
        ValueError,
        match="Horizonte inválido",
    ):
        target_column_for_horizon(5)


def test_future_target_year_respects_horizon() -> None:
    """O ano futuro deve corresponder à observação localizada em t+h."""
    dataframe = prepare_temporal_panel(
        make_temporal_dataframe(),
        horizon=2,
    )

    future_year = calculate_future_target_year(
        dataframe,
        horizon=2,
    )

    assert future_year.iloc[0] == 2020

    assert future_year.iloc[2] == 2021

    assert pd.isna(future_year.iloc[-1])


def test_training_excludes_targets_that_enter_validation_year() -> None:
    """O treino não pode usar rótulos localizados no ano de validação."""
    dataframe = make_temporal_dataframe()

    fold = TemporalFold(
        name="teste",
        train_start_year=2020,
        train_end_year=2020,
        validation_year=2021,
    )

    split = next(
        iter_temporal_fold_masks(
            dataframe,
            horizon=2,
            folds=(fold,),
        )
    )

    train = dataframe.loc[split.train_mask]

    assert len(train) == 2

    assert train["data_inicio_semana"].max() == pd.Timestamp("2020-12-13")


def test_validation_excludes_unavailable_future_targets() -> None:
    """A validação deve excluir linhas sem target futuro disponível."""
    dataframe = make_temporal_dataframe()

    fold = TemporalFold(
        name="teste",
        train_start_year=2020,
        train_end_year=2020,
        validation_year=2021,
    )

    split = next(
        iter_temporal_fold_masks(
            dataframe,
            horizon=2,
            folds=(fold,),
        )
    )

    validation = dataframe.loc[split.validation_mask]

    assert len(validation) == 4

    assert validation["data_inicio_semana"].max() == pd.Timestamp("2021-01-24")


def test_train_and_validation_do_not_overlap() -> None:
    """Nenhuma observação pode pertencer simultaneamente aos dois conjuntos."""
    dataframe = make_temporal_dataframe()

    fold = TemporalFold(
        name="teste",
        train_start_year=2020,
        train_end_year=2020,
        validation_year=2021,
    )

    split = next(
        iter_temporal_fold_masks(
            dataframe,
            horizon=1,
            folds=(fold,),
        )
    )

    overlap = split.train_mask & split.validation_mask

    assert not overlap.any()


def test_weekly_gap_is_rejected() -> None:
    """Uma série descontínua não pode gerar splits por posição."""
    dataframe = make_temporal_dataframe()

    dataframe.loc[
        4:,
        "data_inicio_semana",
    ] = dataframe.loc[
        4:,
        "data_inicio_semana",
    ] + pd.Timedelta(days=7)

    with pytest.raises(
        ValueError,
        match="lacunas temporais",
    ):
        prepare_temporal_panel(
            dataframe,
            horizon=1,
        )


def test_invalid_fold_definition_is_rejected() -> None:
    """Validação não pode ocorrer dentro do período de treino."""
    dataframe = make_temporal_dataframe()

    invalid_fold = TemporalFold(
        name="invalido",
        train_start_year=2020,
        train_end_year=2021,
        validation_year=2021,
    )

    with pytest.raises(
        ValueError,
        match="ano de validação",
    ):
        next(
            iter_temporal_fold_masks(
                dataframe,
                horizon=1,
                folds=(invalid_fold,),
            )
        )
