"""Define as partições temporais da modelagem do Dengue Alert."""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

import pandas as pd

from dengue_alert.features.targets import DEFAULT_HORIZONS

MUNICIPALITY_COLUMN = "codigo_ibge_7"
YEAR_COLUMN = "ano_epidemiologico"
DATE_COLUMN = "data_inicio_semana"


@dataclass(frozen=True, slots=True)
class TemporalFold:
    """Descreve uma partição temporal de treino e validação."""

    name: str
    train_start_year: int
    train_end_year: int
    validation_year: int


@dataclass(frozen=True, slots=True)
class TemporalFoldMasks:
    """Armazena as máscaras de treino e validação de um fold."""

    fold: TemporalFold
    horizon: int
    train_mask: pd.Series
    validation_mask: pd.Series


DEFAULT_TEMPORAL_FOLDS = (
    TemporalFold(
        name="fold_1",
        train_start_year=2018,
        train_end_year=2020,
        validation_year=2021,
    ),
    TemporalFold(
        name="fold_2",
        train_start_year=2018,
        train_end_year=2021,
        validation_year=2022,
    ),
    TemporalFold(
        name="fold_3",
        train_start_year=2018,
        train_end_year=2022,
        validation_year=2023,
    ),
    TemporalFold(
        name="fold_4",
        train_start_year=2018,
        train_end_year=2023,
        validation_year=2024,
    ),
)


def target_column_for_horizon(
    horizon: int,
) -> str:
    """Retorna o nome da coluna de target de um horizonte."""
    if horizon not in DEFAULT_HORIZONS:
        raise ValueError(
            "Horizonte inválido. "
            f"Esperado um de {tuple(DEFAULT_HORIZONS)}; "
            f"recebido: {horizon}."
        )

    return f"target_h{horizon}"


def require_temporal_columns(
    dataframe: pd.DataFrame,
    *,
    horizon: int,
) -> None:
    """Valida a presença das colunas necessárias aos splits."""
    target_column = target_column_for_horizon(horizon)

    required = {
        MUNICIPALITY_COLUMN,
        YEAR_COLUMN,
        DATE_COLUMN,
        target_column,
    }

    missing = sorted(required - set(dataframe.columns))

    if missing:
        raise ValueError(
            "Colunas obrigatórias ausentes para "
            "a validação temporal: " + ", ".join(missing)
        )


def validate_fold_definition(
    fold: TemporalFold,
) -> None:
    """Valida a coerência temporal da definição de um fold."""
    if fold.train_start_year > fold.train_end_year:
        raise ValueError(
            f"{fold.name}: ano inicial de treino é posterior ao ano final."
        )

    if fold.validation_year <= fold.train_end_year:
        raise ValueError(
            f"{fold.name}: ano de validação deve ser posterior ao período de treino."
        )


def prepare_temporal_panel(
    dataframe: pd.DataFrame,
    *,
    horizon: int,
) -> pd.DataFrame:
    """Prepara e valida o painel utilizado nos folds temporais."""
    require_temporal_columns(
        dataframe,
        horizon=horizon,
    )

    if not dataframe.index.is_unique:
        raise ValueError(
            "O índice do dataframe deve ser único "
            "para preservar o alinhamento das máscaras."
        )

    result = dataframe.copy()

    result[MUNICIPALITY_COLUMN] = (
        result[MUNICIPALITY_COLUMN].astype("string").str.strip().str.zfill(7)
    )

    result[DATE_COLUMN] = pd.to_datetime(result[DATE_COLUMN])

    duplicated = int(
        result.duplicated(
            [
                MUNICIPALITY_COLUMN,
                DATE_COLUMN,
            ]
        ).sum()
    )

    if duplicated:
        raise ValueError(
            f"Foram encontradas {duplicated:,} chaves município-data duplicadas."
        )

    chronological = result.sort_values(
        [
            MUNICIPALITY_COLUMN,
            DATE_COLUMN,
        ]
    )

    previous_date = chronological.groupby(
        MUNICIPALITY_COLUMN,
        observed=True,
        sort=False,
    )[DATE_COLUMN].shift(1)

    gap_days = (chronological[DATE_COLUMN] - previous_date).dt.days

    invalid_gap = previous_date.notna() & gap_days.ne(7)

    if invalid_gap.any():
        examples = chronological.loc[
            invalid_gap,
            [
                MUNICIPALITY_COLUMN,
                DATE_COLUMN,
            ],
        ].head(5)

        raise ValueError(
            "Foram encontradas lacunas temporais "
            "dentro das séries municipais. "
            f"Exemplos: "
            f"{examples.to_dict(orient='records')}"
        )

    return result


def calculate_future_target_year(
    dataframe: pd.DataFrame,
    *,
    horizon: int,
) -> pd.Series:
    """Calcula o ano epidemiológico da observação usada como target futuro."""
    target_column_for_horizon(horizon)

    chronological = dataframe.sort_values(
        [
            MUNICIPALITY_COLUMN,
            DATE_COLUMN,
        ]
    )

    future_year = chronological.groupby(
        MUNICIPALITY_COLUMN,
        observed=True,
        sort=False,
    )[YEAR_COLUMN].shift(-horizon)

    return future_year.reindex(dataframe.index)


def build_fold_masks(
    dataframe: pd.DataFrame,
    *,
    fold: TemporalFold,
    horizon: int,
    future_target_year: pd.Series,
) -> TemporalFoldMasks:
    """Constrói máscaras que respeitam as fronteiras temporais do fold."""
    validate_fold_definition(fold)

    target_column = target_column_for_horizon(horizon)

    if not future_target_year.index.equals(dataframe.index):
        raise ValueError("O ano futuro deve possuir o mesmo índice do dataframe.")

    target_available = dataframe[target_column].notna()

    train_mask = (
        dataframe[YEAR_COLUMN].between(
            fold.train_start_year,
            fold.train_end_year,
            inclusive="both",
        )
        & future_target_year.le(fold.train_end_year)
        & target_available
    )

    validation_mask = (
        dataframe[YEAR_COLUMN].eq(fold.validation_year)
        & future_target_year.eq(fold.validation_year)
        & target_available
    )

    if (train_mask & validation_mask).any():
        raise ValueError(f"{fold.name}: treino e validação possuem linhas sobrepostas.")

    return TemporalFoldMasks(
        fold=fold,
        horizon=horizon,
        train_mask=train_mask,
        validation_mask=validation_mask,
    )


def iter_temporal_fold_masks(
    dataframe: pd.DataFrame,
    *,
    horizon: int,
    folds: Sequence[TemporalFold] = DEFAULT_TEMPORAL_FOLDS,
) -> Iterator[TemporalFoldMasks]:
    """Itera pelos folds expanding-window de um horizonte."""
    prepared = prepare_temporal_panel(
        dataframe,
        horizon=horizon,
    )

    future_target_year = calculate_future_target_year(
        prepared,
        horizon=horizon,
    )

    for fold in folds:
        yield build_fold_masks(
            prepared,
            fold=fold,
            horizon=horizon,
            future_target_year=(future_target_year),
        )
