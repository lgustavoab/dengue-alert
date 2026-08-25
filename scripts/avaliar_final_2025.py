"""Executa a avaliação final congelada de 2025 do Dengue Alert."""

import argparse
import json
from time import perf_counter

import numpy as np
import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.evaluation.thresholds import evaluate_threshold
from dengue_alert.modeling.models import ModelName
from dengue_alert.modeling.splits import (
    MUNICIPALITY_COLUMN,
    YEAR_COLUMN,
    target_column_for_horizon,
)
from dengue_alert.modeling.training import (
    CURRENT_RISK_COLUMN,
    EPIDEMIOLOGICAL_FEATURES,
    evaluate_model_predictions,
    fit_candidate_model,
    positive_class_probabilities,
    prepare_binary_target,
    prepare_model_matrix,
)

DEVELOPMENT_DATASET = MASTER_PANEL.parent / "dataset_modelagem_2018_2024.parquet"

FINAL_TEST_DATASET = MASTER_PANEL.parent / "dataset_teste_final_2025.parquet"

PREDICTIONS_OUTPUT = MASTER_PANEL.parent / "predicoes_avaliacao_final_2025.parquet"

CSV_OUTPUT = REPORTS_DIR / "audits" / "avaliacao_final_2025.csv"

JSON_OUTPUT = REPORTS_DIR / "audits" / "avaliacao_final_2025.json"

FINAL_MODEL = ModelName.HIST_GRADIENT_BOOSTING

FINAL_TEST_CONFIRMATION = "OPEN-2025"

EXPECTED_DEVELOPMENT_ROWS = 2_032_685
EXPECTED_FINAL_TEST_ROWS = 295_210

EXPECTED_HORIZONS = (1, 2, 3, 4)

EXPECTED_TRAIN_ROWS = {
    1: 2_027_116,
    2: 2_021_547,
    3: 2_015_978,
    4: 2_010_409,
}

EXPECTED_TEST_ROWS = {
    1: 289_588,
    2: 284_019,
    3: 278_450,
    4: 272_881,
}

FINAL_THRESHOLDS = {
    1: 0.187687,
    2: 0.190783,
    3: 0.167991,
    4: 0.157138,
}


def parse_args() -> argparse.Namespace:
    """Lê os argumentos da avaliação final."""
    parser = argparse.ArgumentParser(
        description=(
            "Executa a avaliação final congelada de 2025. "
            "Sem confirmação explícita, nenhum dado de 2025 é aberto."
        )
    )

    parser.add_argument(
        "--confirm-final-test",
        default=None,
        help=(
            "Confirmação explícita necessária para abrir o teste final. "
            f"Valor exigido: {FINAL_TEST_CONFIRMATION}"
        ),
    )

    return parser.parse_args()


def require_final_test_confirmation(
    confirmation: str | None,
) -> None:
    """Bloqueia qualquer leitura de 2025 sem confirmação explícita."""
    if confirmation != FINAL_TEST_CONFIRMATION:
        print("=" * 100)
        print("AVALIAÇÃO FINAL DE 2025 — BLOQUEADA")
        print("=" * 100)
        print()
        print("O script foi carregado, mas o conjunto final de 2025 NÃO foi aberto.")
        print()
        print(
            "Para executar definitivamente a avaliação final será "
            "necessária confirmação explícita."
        )
        print()
        print(
            "Nenhum target, prevalência, score ou resultado de 2025 foi inspecionado."
        )

        raise SystemExit(0)


def required_columns() -> list[str]:
    """Retorna as colunas necessárias para treinamento e teste."""
    columns = [
        MUNICIPALITY_COLUMN,
        "nome_municipio_ibge",
        "nome_uf_ibge",
        YEAR_COLUMN,
        "semana_epidemiologica",
        "data_inicio_semana",
        CURRENT_RISK_COLUMN,
        *EPIDEMIOLOGICAL_FEATURES,
        *(target_column_for_horizon(horizon) for horizon in EXPECTED_HORIZONS),
    ]

    return list(dict.fromkeys(columns))


def validate_base_periods(
    development: pd.DataFrame,
    final_test: pd.DataFrame,
) -> None:
    """Confirma separação completa entre desenvolvimento e teste."""
    if len(development) != EXPECTED_DEVELOPMENT_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas no desenvolvimento. "
            f"Esperado: {EXPECTED_DEVELOPMENT_ROWS:,}; "
            f"obtido: {len(development):,}."
        )

    if len(final_test) != EXPECTED_FINAL_TEST_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas no teste final. "
            f"Esperado: {EXPECTED_FINAL_TEST_ROWS:,}; "
            f"obtido: {len(final_test):,}."
        )

    development_years = {int(value) for value in development[YEAR_COLUMN].unique()}

    if development_years != set(
        range(
            2018,
            2025,
        )
    ):
        raise ValueError(
            "O desenvolvimento deve conter exclusivamente 2018–2024. "
            f"Obtido: {sorted(development_years)}."
        )

    test_years = {int(value) for value in final_test[YEAR_COLUMN].unique()}

    if test_years != {2025}:
        raise ValueError(
            "O teste final deve conter exclusivamente 2025. "
            f"Obtido: {sorted(test_years)}."
        )

    if development[MUNICIPALITY_COLUMN].isna().any():
        raise ValueError("Existem municípios ausentes no desenvolvimento.")

    if final_test[MUNICIPALITY_COLUMN].isna().any():
        raise ValueError("Existem municípios ausentes no teste final.")


def eligible_subset(
    dataframe: pd.DataFrame,
    *,
    target_column: str,
) -> pd.DataFrame:
    """Mantém somente observações com target disponível."""
    return dataframe.loc[dataframe[target_column].notna()].copy()


def validate_horizon_partition(
    *,
    horizon: int,
    train: pd.DataFrame,
    test: pd.DataFrame,
    target_column: str,
) -> None:
    """Audita as partições elegíveis de um horizonte."""
    expected_train = EXPECTED_TRAIN_ROWS[horizon]

    expected_test = EXPECTED_TEST_ROWS[horizon]

    if len(train) != expected_train:
        raise ValueError(
            f"H{horizon}: quantidade inesperada de linhas de treino. "
            f"Esperado: {expected_train:,}; "
            f"obtido: {len(train):,}."
        )

    if len(test) != expected_test:
        raise ValueError(
            f"H{horizon}: quantidade inesperada de linhas de teste. "
            f"Esperado: {expected_test:,}; "
            f"obtido: {len(test):,}."
        )

    if set(train[YEAR_COLUMN].unique()) - set(
        range(
            2018,
            2025,
        )
    ):
        raise ValueError(f"H{horizon}: treino contém ano fora de 2018–2024.")

    if set(test[YEAR_COLUMN].unique()) != {2025}:
        raise ValueError(f"H{horizon}: teste contém ano diferente de 2025.")

    if train[target_column].isna().any():
        raise ValueError(f"H{horizon}: treino elegível contém target ausente.")

    if test[target_column].isna().any():
        raise ValueError(f"H{horizon}: teste elegível contém target ausente.")

    train_keys = set(
        zip(
            train[MUNICIPALITY_COLUMN].astype(str),
            train["data_inicio_semana"].astype(str),
            strict=True,
        )
    )

    test_keys = set(
        zip(
            test[MUNICIPALITY_COLUMN].astype(str),
            test["data_inicio_semana"].astype(str),
            strict=True,
        )
    )

    overlap = train_keys.intersection(test_keys)

    if overlap:
        raise ValueError(
            f"H{horizon}: foram encontradas "
            f"{len(overlap):,} observações sobrepostas "
            "entre treino e teste."
        )


def flatten_metrics(
    metrics: dict,
    *,
    prefix: str,
) -> dict:
    """Converte métricas aninhadas em colunas tabulares."""
    flattened = {}

    for key, value in metrics.items():
        if isinstance(
            value,
            dict,
        ):
            for nested_key, nested_value in value.items():
                flattened[f"{prefix}_{key}_{nested_key}"] = nested_value
        else:
            flattened[f"{prefix}_{key}"] = value

    return flattened


def build_prediction_frame(
    test: pd.DataFrame,
    *,
    horizon: int,
    target_column: str,
    scores: np.ndarray,
    threshold: float,
) -> pd.DataFrame:
    """Constrói as predições finais persistidas."""
    output = test.loc[
        :,
        [
            MUNICIPALITY_COLUMN,
            "nome_municipio_ibge",
            "nome_uf_ibge",
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

    output["horizonte"] = horizon

    output["score"] = scores

    output["threshold"] = threshold

    output["predicao"] = scores >= threshold

    return output


def main() -> None:
    """Executa a avaliação final congelada."""
    args = parse_args()

    require_final_test_confirmation(args.confirm_final_test)

    print("=" * 100)
    print("AVALIAÇÃO FINAL DE 2025 — MODELO A + HISTGRADIENTBOOSTING")
    print("=" * 100)

    print()
    print("CONFIRMAÇÃO RECEBIDA: o teste final de 2025 será aberto nesta execução.")

    print()
    print("Carregando desenvolvimento 2018–2024...")

    development = pd.read_parquet(
        DEVELOPMENT_DATASET,
        columns=required_columns(),
    )

    print("Carregando teste final de 2025...")

    final_test = pd.read_parquet(
        FINAL_TEST_DATASET,
        columns=required_columns(),
    )

    validate_base_periods(
        development,
        final_test,
    )

    print()
    print(f"Linhas desenvolvimento           : {len(development):,}")

    print(f"Linhas teste final               : {len(final_test):,}")

    print(f"Modelo                           : {FINAL_MODEL.value}")

    print(f"Features                         : {len(EPIDEMIOLOGICAL_FEATURES)}")

    print("Calibração                       : NÃO — probabilidades raw")

    prediction_blocks = []
    result_records = []
    audit_records = []

    total_start = perf_counter()

    for horizon in EXPECTED_HORIZONS:
        target_column = target_column_for_horizon(horizon)

        threshold = FINAL_THRESHOLDS[horizon]

        train = eligible_subset(
            development,
            target_column=target_column,
        )

        test = eligible_subset(
            final_test,
            target_column=target_column,
        )

        validate_horizon_partition(
            horizon=horizon,
            train=train,
            test=test,
            target_column=target_column,
        )

        print()
        print("-" * 100)

        print(f"HORIZONTE H{horizon}")

        print("-" * 100)

        print(f"Linhas treino                    : {len(train):,}")

        print(f"Linhas teste                     : {len(test):,}")

        print(f"Threshold congelado              : {threshold:.6f}")

        x_train = prepare_model_matrix(
            train,
            EPIDEMIOLOGICAL_FEATURES,
        )

        y_train = prepare_binary_target(
            train[target_column],
            name=target_column,
        )

        x_test = prepare_model_matrix(
            test,
            EPIDEMIOLOGICAL_FEATURES,
        )

        y_test = prepare_binary_target(
            test[target_column],
            name=target_column,
        )

        training_start = perf_counter()

        model = fit_candidate_model(
            FINAL_MODEL,
            x_train,
            y_train,
        )

        training_seconds = perf_counter() - training_start

        prediction_start = perf_counter()

        scores = positive_class_probabilities(
            model,
            x_test,
        )

        prediction_seconds = perf_counter() - prediction_start

        model_evaluation = evaluate_model_predictions(
            y_true=y_test,
            y_score=scores,
            current_risk=test[CURRENT_RISK_COLUMN],
            threshold=threshold,
        )

        persistence_scores = (
            test[CURRENT_RISK_COLUMN]
            .astype("boolean")
            .astype("int8")
            .to_numpy(
                dtype=np.float64,
            )
        )

        baseline_evaluation = evaluate_model_predictions(
            y_true=y_test,
            y_score=persistence_scores,
            current_risk=test[CURRENT_RISK_COLUMN],
            threshold=0.5,
        )

        early_mask = (
            ~test[CURRENT_RISK_COLUMN].astype("boolean").astype(bool).to_numpy()
        )

        operational_early = evaluate_threshold(
            y_true=y_test[early_mask],
            y_score=scores[early_mask],
            threshold=threshold,
        )

        prediction_frame = build_prediction_frame(
            test,
            horizon=horizon,
            target_column=target_column,
            scores=scores,
            threshold=threshold,
        )

        prediction_blocks.append(prediction_frame)

        model_record = {
            "modelo": "hist_gradient_boosting",
            "horizonte": horizon,
            "threshold": threshold,
            "linhas_treino": len(train),
            "linhas_teste": len(test),
            **flatten_metrics(
                model_evaluation["avaliacao_geral"],
                prefix="geral",
            ),
            **flatten_metrics(
                model_evaluation["early_warning"],
                prefix="early_warning",
            ),
            "early_warning_alertas": operational_early["alertas"],
            "early_warning_proporcao_alertas": operational_early["proporcao_alertas"],
        }

        baseline_record = {
            "modelo": "persistence",
            "horizonte": horizon,
            "threshold": 0.5,
            "linhas_treino": None,
            "linhas_teste": len(test),
            **flatten_metrics(
                baseline_evaluation["avaliacao_geral"],
                prefix="geral",
            ),
            **flatten_metrics(
                baseline_evaluation["early_warning"],
                prefix="early_warning",
            ),
        }

        result_records.extend(
            [
                model_record,
                baseline_record,
            ]
        )

        audit_records.append(
            {
                "horizonte": horizon,
                "target": target_column,
                "threshold": threshold,
                "linhas_treino": len(train),
                "linhas_teste": len(test),
                "ano_minimo_treino": int(train[YEAR_COLUMN].min()),
                "ano_maximo_treino": int(train[YEAR_COLUMN].max()),
                "ano_teste": 2025,
                "sobreposicao_treino_teste": 0,
                "tempo_treinamento_segundos": training_seconds,
                "tempo_predicao_segundos": prediction_seconds,
            }
        )

        general = model_evaluation["avaliacao_geral"]

        early = model_evaluation["early_warning"]

        baseline_general = baseline_evaluation["avaliacao_geral"]

        baseline_early = baseline_evaluation["early_warning"]

        print(
            "AP geral modelo                  : "
            f"{general['pr_auc_average_precision']:.6f}"
        )

        print(
            "AP geral persistência            : "
            f"{baseline_general['pr_auc_average_precision']:.6f}"
        )

        print(f"Brier modelo                     : {general['brier_score']:.6f}")

        print(f"F1 geral modelo                  : {general['f1']:.6f}")

        print(
            "AP early warning modelo          : "
            f"{early['pr_auc_average_precision']:.6f}"
        )

        print(
            "AP early warning persistência    : "
            f"{baseline_early['pr_auc_average_precision']:.6f}"
        )

        print(f"Precision early warning          : {early['precision']:.6f}")

        print(f"Recall early warning             : {early['recall']:.6f}")

        print(f"F1 early warning                 : {early['f1']:.6f}")

        print(
            "Proporção de alertas early       : "
            f"{operational_early['proporcao_alertas']:.2%}"
        )

        print(f"Tempo treinamento                : {training_seconds:.2f} s")

        del model
        del x_train
        del y_train
        del x_test
        del y_test
        del scores
        del persistence_scores
        del train
        del test

    predictions = pd.concat(
        prediction_blocks,
        ignore_index=True,
    )

    expected_prediction_rows = sum(EXPECTED_TEST_ROWS.values())

    if len(predictions) != expected_prediction_rows:
        raise ValueError(
            "Quantidade inesperada de predições finais. "
            f"Esperado: {expected_prediction_rows:,}; "
            f"obtido: {len(predictions):,}."
        )

    duplicate_count = int(
        predictions.duplicated(
            subset=[
                MUNICIPALITY_COLUMN,
                "data_inicio_semana",
                "horizonte",
            ]
        ).sum()
    )

    if duplicate_count:
        raise ValueError(
            f"Foram encontradas {duplicate_count:,} predições finais duplicadas."
        )

    if predictions["score"].isna().any():
        raise ValueError("Existem scores finais ausentes.")

    if (
        not predictions["score"]
        .between(
            0.0,
            1.0,
            inclusive="both",
        )
        .all()
    ):
        raise ValueError("Existem probabilidades finais fora de [0, 1].")

    PREDICTIONS_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    predictions.to_parquet(
        PREDICTIONS_OUTPUT,
        index=False,
    )

    CSV_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(result_records).to_csv(
        CSV_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    total_seconds = perf_counter() - total_start

    report = {
        "status": "APROVADO",
        "avaliacao": "teste final independente de 2025",
        "modelo_final": {
            "algoritmo": "HistGradientBoostingClassifier",
            "features": "Modelo A — 23 epidemiológicas",
            "calibracao": "não adotada",
            "probabilidades": "raw",
            "thresholds": {
                f"h{horizon}": threshold
                for horizon, threshold in FINAL_THRESHOLDS.items()
            },
        },
        "protocolo": {
            "desenvolvimento": "2018-2024",
            "teste_final": "2025",
            "thresholds_congelados": True,
            "teste_final_utilizado_na_selecao": False,
        },
        "auditoria_temporal": audit_records,
        "predicoes": {
            "linhas": len(predictions),
            "duplicadas": duplicate_count,
            "arquivo": str(PREDICTIONS_OUTPUT),
        },
        "resultados": result_records,
        "tempo_total_segundos": total_seconds,
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

    print()
    print("=" * 100)
    print("RESULTADO FINAL")
    print("=" * 100)

    print("Modelos avaliados                : 4")

    print("Horizontes                       : H1, H2, H3, H4")

    print(f"Predições finais                 : {len(predictions):,}")

    print(f"Predições duplicadas             : {duplicate_count}")

    print(f"Resultados CSV                   : {CSV_OUTPUT}")

    print(f"Auditoria JSON                   : {JSON_OUTPUT}")

    print(f"Predições Parquet                : {PREDICTIONS_OUTPUT}")

    print(f"Tempo total                      : {total_seconds:.2f} s")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
