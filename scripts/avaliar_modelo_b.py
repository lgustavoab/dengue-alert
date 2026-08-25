"""Treina e avalia o Modelo B epidemiológico + climático do Dengue Alert."""

import argparse
import gc
import json
from pathlib import Path
from statistics import fmean
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
    DEFAULT_DECISION_THRESHOLD,
    EPIDEMIOLOGICAL_CLIMATE_FEATURES,
    evaluate_model_predictions,
    fit_candidate_model,
    positive_class_probabilities,
    prepare_binary_target,
    prepare_model_matrix,
)

DEVELOPMENT_DATASET = MASTER_PANEL.parent / "dataset_modelagem_2018_2024.parquet"

MODEL_FEATURES = EPIDEMIOLOGICAL_CLIMATE_FEATURES

EXPECTED_ROWS = 2_032_685
EXPECTED_MUNICIPALITIES = 5_569
EXPECTED_FEATURES = 59

SMOKE_HORIZON = 1
SMOKE_FOLD_NAME = "fold_1"
SMOKE_MODEL = ModelName.LOGISTIC_REGRESSION

METRIC_NAMES = (
    "prevalencia",
    "pr_auc_average_precision",
    "roc_auc",
    "recall",
    "precision",
    "f1",
    "balanced_accuracy",
    "brier_score",
)


def parse_args() -> argparse.Namespace:
    """Lê os argumentos de execução."""
    parser = argparse.ArgumentParser(
        description=("Treina e avalia o Modelo B epidemiológico + climático.")
    )

    parser.add_argument(
        "--mode",
        choices=(
            "smoke",
            "full",
        ),
        required=True,
        help=(
            "smoke executa somente H1/fold_1/"
            "logistic_regression; full executa "
            "todas as 32 combinações."
        ),
    )

    return parser.parse_args()


def output_paths(
    mode: str,
) -> tuple[Path, Path]:
    """Define os arquivos de saída conforme o modo."""
    suffix = "_smoke" if mode == "smoke" else ""

    output_dir = REPORTS_DIR / "audits"

    return (
        output_dir / f"avaliacao_modelo_b{suffix}.json",
        output_dir / f"avaliacao_modelo_b{suffix}.csv",
    )


def required_columns() -> list[str]:
    """Retorna somente as colunas necessárias ao Modelo B."""
    columns = [
        MUNICIPALITY_COLUMN,
        YEAR_COLUMN,
        "data_inicio_semana",
        *MODEL_FEATURES,
        *(target_column_for_horizon(horizon) for horizon in DEFAULT_HORIZONS),
    ]

    return list(dict.fromkeys(columns))


def validate_dataset(
    dataframe: pd.DataFrame,
) -> None:
    """Valida o conjunto de desenvolvimento antes do treinamento."""
    if len(MODEL_FEATURES) != EXPECTED_FEATURES:
        raise ValueError(
            "Quantidade inesperada de features do Modelo B. "
            f"Esperado: {EXPECTED_FEATURES}; "
            f"obtido: {len(MODEL_FEATURES)}."
        )

    if len(set(MODEL_FEATURES)) != EXPECTED_FEATURES:
        raise ValueError(
            "O conjunto de features do Modelo B possui colunas duplicadas."
        )

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
            "Período inesperado no dataset. "
            f"Esperado: {sorted(expected_years)}; "
            f"obtido: {sorted(years)}."
        )

    if 2025 in years:
        raise ValueError("O conjunto final de 2025 não pode participar do treinamento.")

    feature_frame = dataframe.loc[
        :,
        list(MODEL_FEATURES),
    ]

    missing_values = int(feature_frame.isna().sum().sum())

    if missing_values:
        raise ValueError(
            f"As features do Modelo B possuem {missing_values:,} valores ausentes."
        )


def flatten_metrics(
    row: dict,
    *,
    prefix: str,
    metrics: dict,
) -> None:
    """Adiciona métricas de uma avaliação à linha tabular."""
    for key in (
        "observacoes",
        "positivos",
        "negativos",
        *METRIC_NAMES,
    ):
        row[f"{prefix}_{key}"] = metrics[key]

    confusion = metrics["matriz_confusao"]

    for key in (
        "tn",
        "fp",
        "fn",
        "tp",
    ):
        row[f"{prefix}_{key}"] = confusion[key]


def build_record(
    *,
    model_name: ModelName,
    horizon: int,
    split,
    train_rows: int,
    train_positives: int,
    training_seconds: float,
    prediction_seconds: float,
    evaluation: dict,
) -> dict:
    """Transforma uma execução em registro tabular."""
    general = evaluation["avaliacao_geral"]

    early_warning = evaluation["early_warning"]

    record = {
        "modelo": model_name.value,
        "horizonte": horizon,
        "fold": split.fold.name,
        "treino_inicio": split.fold.train_start_year,
        "treino_fim": split.fold.train_end_year,
        "validacao_ano": split.fold.validation_year,
        "linhas_treino": train_rows,
        "positivos_treino": train_positives,
        "prevalencia_treino": (train_positives / train_rows),
        "linhas_validacao": general["observacoes"],
        "threshold": evaluation["threshold"],
        "tempo_treinamento_segundos": training_seconds,
        "tempo_predicao_segundos": prediction_seconds,
    }

    flatten_metrics(
        record,
        prefix="geral",
        metrics=general,
    )

    flatten_metrics(
        record,
        prefix="early_warning",
        metrics=early_warning,
    )

    return record


def serialize_value(
    value,
):
    """Converte valores NumPy/Pandas para tipos serializáveis."""
    if hasattr(
        value,
        "item",
    ):
        return value.item()

    return value


def summarize_records(
    records: list[dict],
) -> list[dict]:
    """Calcula médias dos folds para cada modelo e horizonte."""
    summaries = []

    combinations = sorted(
        {
            (
                record["modelo"],
                record["horizonte"],
            )
            for record in records
        }
    )

    for model_name, horizon in combinations:
        selected = [
            record
            for record in records
            if (record["modelo"] == model_name and record["horizonte"] == horizon)
        ]

        summary = {
            "modelo": model_name,
            "horizonte": horizon,
            "folds": len(selected),
        }

        for prefix in (
            "geral",
            "early_warning",
        ):
            for metric in METRIC_NAMES:
                key = f"{prefix}_{metric}"

                values = [record[key] for record in selected if record[key] is not None]

                summary[key] = float(fmean(values)) if values else None

        summaries.append(summary)

    return summaries


def write_outputs(
    *,
    mode: str,
    records: list[dict],
    elapsed_seconds: float,
    status: str,
) -> None:
    """Persiste os resultados disponíveis até o momento."""
    json_output, csv_output = output_paths(mode)

    json_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summaries = summarize_records(records) if records else []

    report = {
        "status": status,
        "modo": mode,
        "modelo_conceitual": "Modelo B — epidemiológico + climático",
        "features": {
            "quantidade": len(MODEL_FEATURES),
            "colunas": list(MODEL_FEATURES),
        },
        "protocolo": {
            "periodo_desenvolvimento": "2018-2024",
            "teste_final_2025_utilizado": False,
            "threshold_metricas_binarias": DEFAULT_DECISION_THRESHOLD,
            "metrica_principal": "Average Precision (AP)",
        },
        "execucoes": [
            {key: serialize_value(value) for key, value in record.items()}
            for record in records
        ],
        "resumo_medio_folds": summaries,
        "tempo_total_segundos": elapsed_seconds,
    }

    with json_output.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    pd.DataFrame(records).to_csv(
        csv_output,
        index=False,
        encoding="utf-8",
    )


def selected_models(
    mode: str,
) -> tuple[ModelName, ...]:
    """Define os modelos executados em cada modo."""
    if mode == "smoke":
        return (SMOKE_MODEL,)

    return tuple(ModelName)


def selected_horizons(
    mode: str,
) -> tuple[int, ...]:
    """Define os horizontes executados em cada modo."""
    if mode == "smoke":
        return (SMOKE_HORIZON,)

    return tuple(DEFAULT_HORIZONS)


def should_run_split(
    *,
    mode: str,
    fold_name: str,
) -> bool:
    """Filtra o fold no modo smoke."""
    if mode == "full":
        return True

    return fold_name == SMOKE_FOLD_NAME


def main() -> None:
    """Executa o treinamento temporal do Modelo B."""
    args = parse_args()

    mode = args.mode

    print("=" * 88)
    print("MODELO B — FEATURES EPIDEMIOLÓGICAS + CLIMÁTICAS")
    print("=" * 88)

    print()
    print(f"Modo                             : {mode}")

    if mode == "smoke":
        print("Execução                          : H1 / fold_1 / logistic_regression")
    else:
        print("Execução                          : 4 horizontes × 4 folds × 2 modelos")

    print(f"Features                          : {len(MODEL_FEATURES)}")

    print(f"Threshold métricas binárias       : {DEFAULT_DECISION_THRESHOLD:.2f}")

    print("Teste final de 2025               : NÃO UTILIZADO")

    total_start = perf_counter()

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

    print(f"Features epidemiológicas + clima  : {len(MODEL_FEATURES)}")

    records = []

    try:
        for horizon in selected_horizons(mode):
            target_column = target_column_for_horizon(horizon)

            print()
            print("-" * 88)

            print(f"HORIZONTE H{horizon}")

            print("-" * 88)

            for split in iter_temporal_fold_masks(
                dataframe,
                horizon=horizon,
                folds=DEFAULT_TEMPORAL_FOLDS,
            ):
                if not should_run_split(
                    mode=mode,
                    fold_name=(split.fold.name),
                ):
                    continue

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

                print(f"  Linhas treino                   : {len(train_subset):,}")

                print(f"  Linhas validação                : {len(validation_subset):,}")

                x_train = prepare_model_matrix(
                    train_subset,
                    MODEL_FEATURES,
                )

                y_train = prepare_binary_target(
                    train_subset[target_column],
                    name=target_column,
                )

                x_validation = prepare_model_matrix(
                    validation_subset,
                    MODEL_FEATURES,
                )

                y_validation = prepare_binary_target(
                    validation_subset[target_column],
                    name=target_column,
                )

                train_positives = int(y_train.sum())

                for model_name in selected_models(mode):
                    print()
                    print(f"  Modelo                          : {model_name.value}")

                    training_start = perf_counter()

                    model = fit_candidate_model(
                        model_name,
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

                    evaluation = evaluate_model_predictions(
                        y_true=y_validation,
                        y_score=scores,
                        current_risk=(validation_subset[CURRENT_RISK_COLUMN]),
                        threshold=(DEFAULT_DECISION_THRESHOLD),
                    )

                    general = evaluation["avaliacao_geral"]

                    early = evaluation["early_warning"]

                    record = build_record(
                        model_name=model_name,
                        horizon=horizon,
                        split=split,
                        train_rows=(len(train_subset)),
                        train_positives=(train_positives),
                        training_seconds=(training_seconds),
                        prediction_seconds=(prediction_seconds),
                        evaluation=evaluation,
                    )

                    records.append(record)

                    elapsed = perf_counter() - total_start

                    write_outputs(
                        mode=mode,
                        records=records,
                        elapsed_seconds=elapsed,
                        status="EM_ANDAMENTO",
                    )

                    print(
                        "  AP geral                        : "
                        f"{general['pr_auc_average_precision']:.4f}"
                    )

                    print(
                        f"  Recall geral                    : {general['recall']:.4f}"
                    )

                    print(f"  F1 geral                        : {general['f1']:.4f}")

                    print(
                        "  Brier                           : "
                        f"{general['brier_score']:.4f}"
                    )

                    print(
                        "  AP early warning                : "
                        f"{early['pr_auc_average_precision']:.4f}"
                    )

                    print(f"  Recall early warning            : {early['recall']:.4f}")

                    print(
                        f"  Tempo treinamento               : {training_seconds:.2f} s"
                    )

                    print(
                        "  Tempo predição                  : "
                        f"{prediction_seconds:.2f} s"
                    )

                    del model
                    del scores

                    gc.collect()

                del x_train
                del y_train
                del x_validation
                del y_validation
                del train_subset
                del validation_subset

                gc.collect()

        total_seconds = perf_counter() - total_start

        write_outputs(
            mode=mode,
            records=records,
            elapsed_seconds=total_seconds,
            status="APROVADO",
        )

    except Exception:
        elapsed = perf_counter() - total_start

        write_outputs(
            mode=mode,
            records=records,
            elapsed_seconds=elapsed,
            status="INTERROMPIDO",
        )

        raise

    json_output, csv_output = output_paths(mode)

    print()
    print("=" * 88)
    print("RESULTADO")
    print("=" * 88)

    print(f"Execuções concluídas              : {len(records)}")

    print("Teste final de 2025 utilizado     : NÃO")

    print(f"Relatório JSON                    : {json_output}")

    print(f"Resumo CSV                        : {csv_output}")

    print(f"Tempo total                       : {total_seconds:.2f} s")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
