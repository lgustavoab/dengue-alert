"""Gera predições OOF temporais do modelo finalista do Dengue Alert."""

import gc
import json
from time import perf_counter

import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.features.targets import DEFAULT_HORIZONS
from dengue_alert.modeling.models import ModelName
from dengue_alert.modeling.splits import (
    DEFAULT_TEMPORAL_FOLDS,
    MUNICIPALITY_COLUMN,
    YEAR_COLUMN,
    iter_temporal_fold_masks,
    target_column_for_horizon,
)
from dengue_alert.modeling.training import (
    CURRENT_RISK_COLUMN,
    EPIDEMIOLOGICAL_FEATURES,
    fit_candidate_model,
    positive_class_probabilities,
    prepare_binary_target,
    prepare_model_matrix,
)

DEVELOPMENT_DATASET = MASTER_PANEL.parent / "dataset_modelagem_2018_2024.parquet"

OUTPUT_PARQUET = MASTER_PANEL.parent / "predicoes_oof_modelo_a_hgb_2021_2024.parquet"

AUDIT_OUTPUT = REPORTS_DIR / "audits" / "auditoria_predicoes_oof_modelo_a_hgb.json"

FINALIST_MODEL = ModelName.HIST_GRADIENT_BOOSTING

EXPECTED_ROWS = 2_032_685
EXPECTED_MUNICIPALITIES = 5_569

EXPECTED_VALIDATION_ROWS = {
    1: 284_019,
    2: 278_450,
    3: 272_881,
    4: 267_312,
}


def required_columns() -> list[str]:
    """Retorna somente as colunas necessárias à geração OOF."""
    columns = [
        MUNICIPALITY_COLUMN,
        YEAR_COLUMN,
        "semana_epidemiologica",
        "data_inicio_semana",
        CURRENT_RISK_COLUMN,
        *EPIDEMIOLOGICAL_FEATURES,
        *(target_column_for_horizon(horizon) for horizon in DEFAULT_HORIZONS),
    ]

    return list(dict.fromkeys(columns))


def validate_dataset(
    dataframe: pd.DataFrame,
) -> None:
    """Valida o conjunto de desenvolvimento antes da geração OOF."""
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

    expected_years = set(range(2018, 2025))

    if years != expected_years:
        raise ValueError(
            "Período inesperado. "
            f"Esperado: {sorted(expected_years)}; "
            f"obtido: {sorted(years)}."
        )

    if 2025 in years:
        raise ValueError("O conjunto final de 2025 não pode participar da geração OOF.")


def build_oof_frame(
    validation_subset: pd.DataFrame,
    *,
    target_column: str,
    scores,
    horizon: int,
    fold_name: str,
    train_start_year: int,
    train_end_year: int,
    validation_year: int,
) -> pd.DataFrame:
    """Constrói o bloco OOF de uma combinação fold × horizonte."""
    output = validation_subset.loc[
        :,
        [
            MUNICIPALITY_COLUMN,
            YEAR_COLUMN,
            "semana_epidemiologica",
            "data_inicio_semana",
            CURRENT_RISK_COLUMN,
            target_column,
        ],
    ].copy()

    output = output.rename(
        columns={
            target_column: "target",
        }
    )

    output["score"] = scores
    output["horizonte"] = horizon
    output["fold"] = fold_name
    output["treino_inicio"] = train_start_year
    output["treino_fim"] = train_end_year
    output["validacao_ano"] = validation_year

    return output


def validate_oof_output(
    output: pd.DataFrame,
) -> dict:
    """Audita a estrutura completa das predições OOF."""
    expected_total = sum(
        rows * len(DEFAULT_TEMPORAL_FOLDS) for rows in EXPECTED_VALIDATION_ROWS.values()
    )

    if len(output) != expected_total:
        raise ValueError(
            "Quantidade inesperada de predições OOF. "
            f"Esperado: {expected_total:,}; "
            f"obtido: {len(output):,}."
        )

    if output["score"].isna().any():
        missing = int(output["score"].isna().sum())

        raise ValueError(f"Existem {missing:,} scores OOF ausentes.")

    if (
        not output["score"]
        .between(
            0.0,
            1.0,
            inclusive="both",
        )
        .all()
    ):
        raise ValueError("Existem probabilidades OOF fora do intervalo [0, 1].")

    if output["target"].isna().any():
        missing = int(output["target"].isna().sum())

        raise ValueError(f"Existem {missing:,} targets OOF ausentes.")

    if output["validacao_ano"].min() != 2021:
        raise ValueError("Ano mínimo inesperado nas predições OOF.")

    if output["validacao_ano"].max() != 2024:
        raise ValueError("Ano máximo inesperado nas predições OOF.")

    duplicate_columns = [
        MUNICIPALITY_COLUMN,
        "data_inicio_semana",
        "horizonte",
    ]

    duplicates = int(output.duplicated(subset=duplicate_columns).sum())

    if duplicates:
        raise ValueError(f"Foram encontradas {duplicates:,} predições OOF duplicadas.")

    counts = (
        output.groupby(
            [
                "horizonte",
                "fold",
            ],
            observed=True,
        )
        .size()
        .to_dict()
    )

    for horizon in DEFAULT_HORIZONS:
        expected = EXPECTED_VALIDATION_ROWS[horizon]

        for fold in DEFAULT_TEMPORAL_FOLDS:
            obtained = int(
                counts.get(
                    (
                        horizon,
                        fold.name,
                    ),
                    0,
                )
            )

            if obtained != expected:
                raise ValueError(
                    f"H{horizon} / {fold.name}: "
                    "quantidade inesperada de linhas. "
                    f"Esperado: {expected:,}; "
                    f"obtido: {obtained:,}."
                )

    return {
        "linhas": len(output),
        "horizontes": sorted(int(value) for value in output["horizonte"].unique()),
        "anos_validacao": sorted(
            int(value) for value in output["validacao_ano"].unique()
        ),
        "municipios": int(output[MUNICIPALITY_COLUMN].nunique()),
        "duplicadas": duplicates,
        "score_minimo": float(output["score"].min()),
        "score_maximo": float(output["score"].max()),
    }


def main() -> None:
    """Treina o finalista nos folds e gera predições OOF."""
    print("=" * 92)
    print("PREDIÇÕES OOF — MODELO A + HISTGRADIENTBOOSTING")
    print("=" * 92)

    start = perf_counter()

    print()
    print("Carregando dataset de desenvolvimento...")

    dataframe = pd.read_parquet(
        DEVELOPMENT_DATASET,
        columns=required_columns(),
    )

    validate_dataset(dataframe)

    print(f"Linhas                            : {len(dataframe):,}")

    print(
        "Municípios                        : "
        f"{dataframe[MUNICIPALITY_COLUMN].nunique():,}"
    )

    print("Período                           : 2018–2024")

    print(f"Modelo                            : {FINALIST_MODEL.value}")

    print(f"Features                          : {len(EPIDEMIOLOGICAL_FEATURES)}")

    print("Teste final de 2025               : NÃO UTILIZADO")

    oof_blocks = []
    execution_records = []

    for horizon in DEFAULT_HORIZONS:
        target_column = target_column_for_horizon(horizon)

        print()
        print("-" * 92)

        print(f"HORIZONTE H{horizon}")

        print("-" * 92)

        for split in iter_temporal_fold_masks(
            dataframe,
            horizon=horizon,
            folds=DEFAULT_TEMPORAL_FOLDS,
        ):
            train_subset = dataframe.loc[split.train_mask]

            validation_subset = dataframe.loc[split.validation_mask]

            print()
            print(
                f"{split.fold.name} | "
                f"treino "
                f"{split.fold.train_start_year}"
                "–"
                f"{split.fold.train_end_year}"
                " | validação "
                f"{split.fold.validation_year}"
            )

            x_train = prepare_model_matrix(
                train_subset,
                EPIDEMIOLOGICAL_FEATURES,
            )

            y_train = prepare_binary_target(
                train_subset[target_column],
                name=target_column,
            )

            x_validation = prepare_model_matrix(
                validation_subset,
                EPIDEMIOLOGICAL_FEATURES,
            )

            training_start = perf_counter()

            model = fit_candidate_model(
                FINALIST_MODEL,
                x_train,
                y_train,
            )

            training_seconds = perf_counter() - training_start

            prediction_start = perf_counter()

            scores = positive_class_probabilities(
                model,
                x_validation,
            )

            prediction_seconds = perf_counter() - prediction_start

            oof_block = build_oof_frame(
                validation_subset,
                target_column=target_column,
                scores=scores,
                horizon=horizon,
                fold_name=split.fold.name,
                train_start_year=(split.fold.train_start_year),
                train_end_year=(split.fold.train_end_year),
                validation_year=(split.fold.validation_year),
            )

            oof_blocks.append(oof_block)

            execution_records.append(
                {
                    "horizonte": horizon,
                    "fold": split.fold.name,
                    "treino_inicio": split.fold.train_start_year,
                    "treino_fim": split.fold.train_end_year,
                    "validacao_ano": split.fold.validation_year,
                    "linhas_treino": len(train_subset),
                    "linhas_validacao": len(validation_subset),
                    "tempo_treinamento_segundos": training_seconds,
                    "tempo_predicao_segundos": prediction_seconds,
                }
            )

            print(f"  Linhas treino                   : {len(train_subset):,}")

            print(f"  Linhas OOF                      : {len(validation_subset):,}")

            print(f"  Score mínimo                    : {scores.min():.6f}")

            print(f"  Score máximo                    : {scores.max():.6f}")

            print(f"  Tempo treinamento               : {training_seconds:.2f} s")

            print(f"  Tempo predição                  : {prediction_seconds:.2f} s")

            del model
            del scores
            del x_train
            del y_train
            del x_validation
            del train_subset
            del validation_subset

            gc.collect()

    print()
    print("Consolidando predições OOF...")

    output = pd.concat(
        oof_blocks,
        ignore_index=True,
    )

    audit = validate_oof_output(output)

    OUTPUT_PARQUET.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_parquet(
        OUTPUT_PARQUET,
        index=False,
    )

    elapsed = perf_counter() - start

    report = {
        "status": "APROVADO",
        "modelo": {
            "nome": FINALIST_MODEL.value,
            "conjunto_features": "Modelo A — epidemiológico",
            "quantidade_features": len(EPIDEMIOLOGICAL_FEATURES),
        },
        "protocolo": {
            "periodo_treinamento": "2018-2023 conforme fold",
            "periodo_oof": "2021-2024",
            "horizontes": list(DEFAULT_HORIZONS),
            "folds": len(DEFAULT_TEMPORAL_FOLDS),
            "teste_final_2025_utilizado": False,
        },
        "auditoria": audit,
        "execucoes": execution_records,
        "arquivo_oof": str(OUTPUT_PARQUET),
        "tempo_total_segundos": elapsed,
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
    print("=" * 92)
    print("RESULTADO")
    print("=" * 92)

    print(f"Predições OOF                     : {len(output):,}")

    print("Anos OOF                          : 2021–2024")

    print("Horizontes                        : H1, H2, H3, H4")

    print("Teste final de 2025 utilizado     : NÃO")

    print(f"Arquivo Parquet                   : {OUTPUT_PARQUET}")

    print(f"Auditoria JSON                    : {AUDIT_OUTPUT}")

    print(f"Tempo total                       : {elapsed:.2f} s")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
