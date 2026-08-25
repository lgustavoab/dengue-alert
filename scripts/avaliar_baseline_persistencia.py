"""Avalia o baseline de persistência nos folds temporais do Dengue Alert."""

import json
from statistics import fmean
from time import perf_counter

import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.evaluation.metrics import evaluate_binary_predictions
from dengue_alert.features.targets import DEFAULT_HORIZONS
from dengue_alert.modeling.baselines import persistence_predictions
from dengue_alert.modeling.splits import (
    DEFAULT_TEMPORAL_FOLDS,
    MUNICIPALITY_COLUMN,
    YEAR_COLUMN,
    iter_temporal_fold_masks,
    target_column_for_horizon,
)

DEVELOPMENT_DATASET = MASTER_PANEL.parent / "dataset_modelagem_2018_2024.parquet"

JSON_OUTPUT = REPORTS_DIR / "audits" / "avaliacao_baseline_persistencia.json"

CSV_OUTPUT = REPORTS_DIR / "audits" / "avaliacao_baseline_persistencia.csv"

CURRENT_RISK_COLUMN = "risco_elevado"

EXPECTED_ROWS = 2_032_685
EXPECTED_MUNICIPALITIES = 5_569
EXPECTED_COMBINATIONS = 16

METRIC_COLUMNS = (
    "pr_auc_average_precision",
    "roc_auc",
    "recall",
    "precision",
    "f1",
    "balanced_accuracy",
    "brier_score",
)


def validate_dataset(
    dataframe: pd.DataFrame,
) -> None:
    """Valida a estrutura mínima necessária à avaliação."""
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

    if dataframe[CURRENT_RISK_COLUMN].isna().any():
        missing = int(dataframe[CURRENT_RISK_COLUMN].isna().sum())

        raise ValueError(
            "O dataset de desenvolvimento possui "
            f"{missing:,} estados atuais de risco ausentes."
        )

    years = set(dataframe[YEAR_COLUMN].unique())

    expected_years = set(range(2018, 2025))

    if years != expected_years:
        raise ValueError(
            "Período inesperado no dataset. "
            f"Esperado: {sorted(expected_years)}; "
            f"obtido: {sorted(years)}."
        )


def evaluate_persistence_subset(
    dataframe: pd.DataFrame,
    *,
    mask: pd.Series,
    target_column: str,
) -> dict:
    """Avalia persistência em um subconjunto previamente definido."""
    subset = dataframe.loc[mask]

    if subset.empty:
        raise ValueError("O subconjunto de avaliação está vazio.")

    score, prediction = persistence_predictions(subset[CURRENT_RISK_COLUMN])

    return evaluate_binary_predictions(
        y_true=subset[target_column],
        y_score=score,
        y_pred=prediction,
    )


def evaluate_early_warning(
    dataframe: pd.DataFrame,
    *,
    validation_mask: pd.Series,
    target_column: str,
) -> dict:
    """Avalia antecipação quando o risco atual ainda é normal."""
    early_warning_mask = validation_mask & dataframe[CURRENT_RISK_COLUMN].eq(False)

    subset = dataframe.loc[early_warning_mask]

    if subset.empty:
        raise ValueError("O subconjunto de early warning está vazio.")

    score, prediction = persistence_predictions(subset[CURRENT_RISK_COLUMN])

    if not score.eq(0.0).all():
        raise ValueError(
            "O baseline de persistência deveria "
            "produzir score zero em todo o "
            "subconjunto de early warning."
        )

    if prediction.any():
        raise ValueError(
            "O baseline de persistência deveria "
            "produzir somente previsões negativas "
            "no subconjunto de early warning."
        )

    return evaluate_binary_predictions(
        y_true=subset[target_column],
        y_score=score,
        y_pred=prediction,
    )


def flatten_result(
    *,
    horizon: int,
    fold_name: str,
    train_start_year: int,
    train_end_year: int,
    validation_year: int,
    train_rows: int,
    validation_rows: int,
    general: dict,
    early_warning: dict,
) -> dict:
    """Transforma uma avaliação em uma linha tabular."""
    row = {
        "horizonte": horizon,
        "fold": fold_name,
        "treino_inicio": train_start_year,
        "treino_fim": train_end_year,
        "validacao_ano": validation_year,
        "linhas_treino": train_rows,
        "linhas_validacao": validation_rows,
        "geral_observacoes": general["observacoes"],
        "geral_positivos": general["positivos"],
        "geral_prevalencia": general["prevalencia"],
        "early_warning_observacoes": early_warning["observacoes"],
        "early_warning_positivos": early_warning["positivos"],
        "early_warning_prevalencia": early_warning["prevalencia"],
    }

    for metric in METRIC_COLUMNS:
        row[f"geral_{metric}"] = general[metric]

        row[f"early_warning_{metric}"] = early_warning[metric]

    return row


def summarize_horizon(
    records: list[dict],
    *,
    horizon: int,
    evaluation_key: str,
) -> dict:
    """Resume as métricas dos quatro folds de um horizonte."""
    selected = [record for record in records if record["horizonte"] == horizon]

    if len(selected) != len(DEFAULT_TEMPORAL_FOLDS):
        raise ValueError(f"H{horizon}: quantidade inesperada de folds na agregação.")

    summary = {
        "folds": len(selected),
    }

    for metric in (
        "prevalencia",
        *METRIC_COLUMNS,
    ):
        key = f"{evaluation_key}_{metric}"

        values = [record[key] for record in selected if record[key] is not None]

        summary[metric] = float(fmean(values)) if values else None

    return summary


def main() -> None:
    """Executa a avaliação real do baseline de persistência."""
    print("=" * 88)
    print("AVALIAÇÃO DO BASELINE DE PERSISTÊNCIA — DENGUE ALERT")
    print("=" * 88)

    start = perf_counter()

    columns = [
        MUNICIPALITY_COLUMN,
        YEAR_COLUMN,
        "semana_epidemiologica",
        "data_inicio_semana",
        CURRENT_RISK_COLUMN,
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

    records = []

    detailed_results = {}

    for horizon in DEFAULT_HORIZONS:
        print()
        print(f"Avaliando H{horizon}...")

        target_column = target_column_for_horizon(horizon)

        horizon_results = []

        for split in iter_temporal_fold_masks(
            dataframe,
            horizon=horizon,
            folds=DEFAULT_TEMPORAL_FOLDS,
        ):
            train_rows = int(split.train_mask.sum())

            validation_rows = int(split.validation_mask.sum())

            general = evaluate_persistence_subset(
                dataframe,
                mask=(split.validation_mask),
                target_column=(target_column),
            )

            early_warning = evaluate_early_warning(
                dataframe,
                validation_mask=(split.validation_mask),
                target_column=(target_column),
            )

            result = {
                "fold": split.fold.name,
                "treino": {
                    "ano_inicio": split.fold.train_start_year,
                    "ano_fim": split.fold.train_end_year,
                    "linhas": train_rows,
                },
                "validacao": {
                    "ano": split.fold.validation_year,
                    "linhas": validation_rows,
                },
                "avaliacao_geral": general,
                "early_warning": early_warning,
            }

            horizon_results.append(result)

            records.append(
                flatten_result(
                    horizon=horizon,
                    fold_name=(split.fold.name),
                    train_start_year=(split.fold.train_start_year),
                    train_end_year=(split.fold.train_end_year),
                    validation_year=(split.fold.validation_year),
                    train_rows=train_rows,
                    validation_rows=(validation_rows),
                    general=general,
                    early_warning=(early_warning),
                )
            )

            general_ap = general["pr_auc_average_precision"]

            early_ap = early_warning["pr_auc_average_precision"]

            print(
                f"  {split.fold.name} | "
                f"val={validation_rows:,} | "
                f"AP geral="
                f"{general_ap:.4f} | "
                f"recall geral="
                f"{general['recall']:.4f} | "
                f"early AP="
                f"{early_ap:.4f} | "
                f"early recall="
                f"{early_warning['recall']:.4f}"
            )

        detailed_results[f"h{horizon}"] = horizon_results

    if len(records) != EXPECTED_COMBINATIONS:
        raise ValueError(
            "Quantidade inesperada de avaliações. "
            f"Esperado: {EXPECTED_COMBINATIONS}; "
            f"obtido: {len(records)}."
        )

    summary = {}

    for horizon in DEFAULT_HORIZONS:
        summary[f"h{horizon}"] = {
            "geral": summarize_horizon(
                records,
                horizon=horizon,
                evaluation_key="geral",
            ),
            "early_warning": summarize_horizon(
                records,
                horizon=horizon,
                evaluation_key=("early_warning"),
            ),
        }

    duration = perf_counter() - start

    report = {
        "status": "APROVADO",
        "baseline": {
            "nome": "persistencia_epidemiologica",
            "regra": "predicao_h(t) = risco_elevado(t)",
            "probabilidade": "score binario 0/1 igual ao estado atual",
        },
        "dataset": {
            "periodo": "2018-2024",
            "linhas": len(dataframe),
            "municipios": int(dataframe[MUNICIPALITY_COLUMN].nunique()),
            "teste_final_2025_utilizado": False,
        },
        "metodologia": {
            "folds": len(DEFAULT_TEMPORAL_FOLDS),
            "horizontes": list(DEFAULT_HORIZONS),
            "combinacoes": len(records),
            "metrica_principal": "Average Precision (AP)",
            "early_warning": "somente risco_elevado(t) = False",
        },
        "resultados": detailed_results,
        "resumo_medio_folds": summary,
        "tempo_execucao_segundos": duration,
    }

    JSON_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with JSON_OUTPUT.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    result_table = pd.DataFrame(records).sort_values(
        [
            "horizonte",
            "validacao_ano",
        ]
    )

    result_table.to_csv(
        CSV_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    print()
    print("=" * 88)
    print("RESUMO MÉDIO DOS FOLDS")
    print("=" * 88)

    for horizon in DEFAULT_HORIZONS:
        horizon_summary = summary[f"h{horizon}"]

        general = horizon_summary["geral"]

        early = horizon_summary["early_warning"]

        print()
        print(f"H{horizon}")

        print(
            "  Geral — AP                     : "
            f"{general['pr_auc_average_precision']:.4f}"
        )

        print(f"  Geral — Recall                 : {general['recall']:.4f}")

        print(f"  Geral — F1                     : {general['f1']:.4f}")

        print(f"  Geral — Balanced Accuracy      : {general['balanced_accuracy']:.4f}")

        print(f"  Early warning — prevalência    : {early['prevalencia']:.4f}")

        print(
            "  Early warning — AP             : "
            f"{early['pr_auc_average_precision']:.4f}"
        )

        print(f"  Early warning — Recall         : {early['recall']:.4f}")

    print()
    print("=" * 88)
    print("RESULTADO")
    print("=" * 88)

    print(f"Combinações avaliadas            : {len(records)}")

    print("Avaliação geral                  : OK")

    print("Avaliação early warning          : OK")

    print("Teste final de 2025 utilizado    : NÃO")

    print(f"Relatório JSON                   : {JSON_OUTPUT}")

    print(f"Resumo CSV                       : {CSV_OUTPUT}")

    print(f"Tempo de execução                : {duration:.2f} s")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
