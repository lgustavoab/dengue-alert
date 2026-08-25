"""Audita os folds temporais reais utilizados na modelagem do Dengue Alert."""

import json
from time import perf_counter

import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.features.targets import DEFAULT_HORIZONS
from dengue_alert.modeling.splits import (
    DATE_COLUMN,
    DEFAULT_TEMPORAL_FOLDS,
    MUNICIPALITY_COLUMN,
    YEAR_COLUMN,
    calculate_future_target_year,
    iter_temporal_fold_masks,
    prepare_temporal_panel,
    target_column_for_horizon,
)

DEVELOPMENT_DATASET = MASTER_PANEL.parent / "dataset_modelagem_2018_2024.parquet"

AUDIT_OUTPUT = REPORTS_DIR / "audits" / "auditoria_folds_modelagem.json"

EXPECTED_ROWS = 2_032_685
EXPECTED_MUNICIPALITIES = 5_569
EXPECTED_YEARS = set(range(2018, 2025))

EXPECTED_TARGET_ROWS = {
    1: 2_027_116,
    2: 2_021_547,
    3: 2_015_978,
    4: 2_010_409,
}


def validate_dataset(
    dataframe: pd.DataFrame,
) -> None:
    """Valida a estrutura geral do dataset de desenvolvimento."""
    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas. "
            f"Esperado: {EXPECTED_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    municipalities = int(dataframe[MUNICIPALITY_COLUMN].nunique())

    if municipalities != EXPECTED_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de municípios. "
            f"Esperado: {EXPECTED_MUNICIPALITIES:,}; "
            f"obtido: {municipalities:,}."
        )

    years = set(dataframe[YEAR_COLUMN].unique())

    if years != EXPECTED_YEARS:
        raise ValueError(
            "Período inesperado no dataset. "
            f"Esperado: {sorted(EXPECTED_YEARS)}; "
            f"obtido: {sorted(years)}."
        )

    duplicates = int(
        dataframe.duplicated(
            [
                MUNICIPALITY_COLUMN,
                YEAR_COLUMN,
                "semana_epidemiologica",
            ]
        ).sum()
    )

    if duplicates:
        raise ValueError(f"Foram encontradas {duplicates:,} chaves duplicadas.")


def validate_split(
    dataframe: pd.DataFrame,
    *,
    future_target_year: pd.Series,
    split,
) -> dict:
    """Audita um fold individual."""
    train = dataframe.loc[split.train_mask]

    validation = dataframe.loc[split.validation_mask]

    if train.empty:
        raise ValueError(f"{split.fold.name} H{split.horizon}: treino vazio.")

    if validation.empty:
        raise ValueError(f"{split.fold.name} H{split.horizon}: validação vazia.")

    overlap = split.train_mask & split.validation_mask

    if overlap.any():
        raise ValueError(
            f"{split.fold.name} H{split.horizon}: "
            "há sobreposição entre treino e validação."
        )

    train_year_min = int(train[YEAR_COLUMN].min())

    train_year_max = int(train[YEAR_COLUMN].max())

    if (
        train_year_min != split.fold.train_start_year
        or train_year_max != split.fold.train_end_year
    ):
        raise ValueError(
            f"{split.fold.name} H{split.horizon}: período de treino incorreto."
        )

    validation_years = set(validation[YEAR_COLUMN].unique())

    if validation_years != {split.fold.validation_year}:
        raise ValueError(
            f"{split.fold.name} H{split.horizon}: ano de validação incorreto."
        )

    train_future_year = future_target_year.loc[split.train_mask]

    if (train_future_year > split.fold.train_end_year).any():
        raise ValueError(
            f"{split.fold.name} H{split.horizon}: "
            "target de treino atravessa "
            "a fronteira da validação."
        )

    validation_future_year = future_target_year.loc[split.validation_mask]

    if not validation_future_year.eq(split.fold.validation_year).all():
        raise ValueError(
            f"{split.fold.name} H{split.horizon}: "
            "target de validação sai do "
            "ano de validação."
        )

    train_municipalities = int(train[MUNICIPALITY_COLUMN].nunique())

    validation_municipalities = int(validation[MUNICIPALITY_COLUMN].nunique())

    if train_municipalities != EXPECTED_MUNICIPALITIES:
        raise ValueError(
            f"{split.fold.name} H{split.horizon}: "
            "quantidade inesperada de municípios "
            "no treino."
        )

    if validation_municipalities != EXPECTED_MUNICIPALITIES:
        raise ValueError(
            f"{split.fold.name} H{split.horizon}: "
            "quantidade inesperada de municípios "
            "na validação."
        )

    train_rows_per_municipality = train.groupby(
        MUNICIPALITY_COLUMN,
        observed=True,
    ).size()

    validation_rows_per_municipality = validation.groupby(
        MUNICIPALITY_COLUMN,
        observed=True,
    ).size()

    if train_rows_per_municipality.nunique() != 1:
        raise ValueError(
            f"{split.fold.name} H{split.horizon}: "
            "municípios possuem números diferentes "
            "de observações de treino."
        )

    if validation_rows_per_municipality.nunique() != 1:
        raise ValueError(
            f"{split.fold.name} H{split.horizon}: "
            "municípios possuem números diferentes "
            "de observações de validação."
        )

    return {
        "nome": split.fold.name,
        "horizonte": split.horizon,
        "treino": {
            "ano_inicio": split.fold.train_start_year,
            "ano_fim": split.fold.train_end_year,
            "linhas": len(train),
            "municipios": train_municipalities,
            "linhas_por_municipio": int(train_rows_per_municipality.iloc[0]),
        },
        "validacao": {
            "ano": split.fold.validation_year,
            "linhas": len(validation),
            "municipios": validation_municipalities,
            "linhas_por_municipio": int(validation_rows_per_municipality.iloc[0]),
        },
        "sobreposicao": 0,
        "target_cruza_fronteira": False,
    }


def main() -> None:
    """Executa a auditoria estrutural dos folds temporais."""
    print("=" * 88)
    print("AUDITORIA DOS FOLDS TEMPORAIS — DENGUE ALERT")
    print("=" * 88)

    start = perf_counter()

    columns = [
        MUNICIPALITY_COLUMN,
        YEAR_COLUMN,
        "semana_epidemiologica",
        DATE_COLUMN,
        *(target_column_for_horizon(horizon) for horizon in DEFAULT_HORIZONS),
    ]

    print()
    print("Carregando dataset de desenvolvimento...")

    dataframe = pd.read_parquet(
        DEVELOPMENT_DATASET,
        columns=columns,
    )

    validate_dataset(dataframe)

    print(f"Linhas                           : {len(dataframe):,}")

    print(
        "Municípios                       : "
        f"{dataframe[MUNICIPALITY_COLUMN].nunique():,}"
    )

    print("Período                          : 2018–2024")

    results = {}

    for horizon in DEFAULT_HORIZONS:
        print()
        print(f"Auditando H{horizon}...")

        target_column = target_column_for_horizon(horizon)

        target_rows = int(dataframe[target_column].notna().sum())

        expected_target_rows = EXPECTED_TARGET_ROWS[horizon]

        if target_rows != expected_target_rows:
            raise ValueError(
                f"H{horizon}: quantidade inesperada "
                "de targets disponíveis. "
                f"Esperado: "
                f"{expected_target_rows:,}; "
                f"obtido: {target_rows:,}."
            )

        prepared = prepare_temporal_panel(
            dataframe,
            horizon=horizon,
        )

        future_target_year = calculate_future_target_year(
            prepared,
            horizon=horizon,
        )

        horizon_results = []

        for split in iter_temporal_fold_masks(
            dataframe,
            horizon=horizon,
            folds=DEFAULT_TEMPORAL_FOLDS,
        ):
            audit = validate_split(
                dataframe,
                future_target_year=(future_target_year),
                split=split,
            )

            horizon_results.append(audit)

            print(
                f"  {split.fold.name}: "
                f"treino={audit['treino']['linhas']:,} | "
                f"validação="
                f"{audit['validacao']['linhas']:,}"
            )

        results[f"h{horizon}"] = {
            "targets_disponiveis": target_rows,
            "folds": horizon_results,
        }

    duration = perf_counter() - start

    report = {
        "status": "APROVADO",
        "dataset": {
            "periodo": "2018-2024",
            "linhas": len(dataframe),
            "municipios": int(dataframe[MUNICIPALITY_COLUMN].nunique()),
        },
        "metodologia": {
            "tipo": "expanding-window",
            "quantidade_folds": len(DEFAULT_TEMPORAL_FOLDS),
            "horizontes": list(DEFAULT_HORIZONS),
            "teste_final_2025_utilizado": False,
        },
        "resultados": results,
        "tempo_execucao_segundos": duration,
    }

    AUDIT_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with AUDIT_OUTPUT.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 88)
    print("RESULTADO")
    print("=" * 88)

    print(f"Folds auditados                  : {len(DEFAULT_TEMPORAL_FOLDS)}")

    print(f"Horizontes auditados             : {len(DEFAULT_HORIZONS)}")

    print(
        "Combinações fold × horizonte     : "
        f"{len(DEFAULT_TEMPORAL_FOLDS) * len(DEFAULT_HORIZONS)}"
    )

    print("Sobreposição treino/validação    : 0")

    print("Targets cruzando fronteiras      : 0")

    print("Teste final de 2025 utilizado    : NÃO")

    print(f"Relatório                        : {AUDIT_OUTPUT}")

    print(f"Tempo de execução                : {duration:.2f} s")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
