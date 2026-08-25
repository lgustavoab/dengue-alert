"""Audita a reprodutibilidade das predições OOF do modelo finalista."""

import json
from math import isclose

import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.modeling.models import ModelName
from dengue_alert.modeling.training import (
    CURRENT_RISK_COLUMN,
    DEFAULT_DECISION_THRESHOLD,
    evaluate_model_predictions,
)

OOF_INPUT = MASTER_PANEL.parent / "predicoes_oof_modelo_a_hgb_2021_2024.parquet"

MODEL_A_RESULTS = REPORTS_DIR / "audits" / "avaliacao_modelo_a.csv"

AUDIT_OUTPUT = REPORTS_DIR / "audits" / "auditoria_reprodutibilidade_oof.json"

FINALIST_MODEL = ModelName.HIST_GRADIENT_BOOSTING.value

EXPECTED_OOF_ROWS = 4_410_648
EXPECTED_COMBINATIONS = 16

TOLERANCE = 1e-10

METRICS = (
    "pr_auc_average_precision",
    "roc_auc",
    "recall",
    "precision",
    "f1",
    "balanced_accuracy",
    "brier_score",
)


def validate_inputs(
    oof: pd.DataFrame,
    reference: pd.DataFrame,
) -> None:
    """Valida a estrutura mínima das duas fontes."""
    if len(oof) != EXPECTED_OOF_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas OOF. "
            f"Esperado: {EXPECTED_OOF_ROWS:,}; "
            f"obtido: {len(oof):,}."
        )

    if 2025 in set(oof["validacao_ano"].unique()):
        raise ValueError(
            "O teste final de 2025 apareceu indevidamente nas predições OOF."
        )

    finalist_reference = reference.loc[reference["modelo"].eq(FINALIST_MODEL)]

    if len(finalist_reference) != EXPECTED_COMBINATIONS:
        raise ValueError(
            "Quantidade inesperada de resultados "
            "de referência do modelo finalista. "
            f"Esperado: {EXPECTED_COMBINATIONS}; "
            f"obtido: {len(finalist_reference)}."
        )


def compare_metric(
    *,
    obtained: float | None,
    expected: float | None,
    metric_name: str,
    horizon: int,
    fold_name: str,
) -> float | None:
    """Compara uma métrica OOF com seu resultado de referência."""
    if obtained is None or expected is None:
        if obtained is expected:
            return None

        raise ValueError(
            f"H{horizon} / {fold_name} / {metric_name}: "
            "divergência envolvendo valor ausente."
        )

    difference = float(obtained - expected)

    if not isclose(
        obtained,
        expected,
        rel_tol=0.0,
        abs_tol=TOLERANCE,
    ):
        raise ValueError(
            f"H{horizon} / {fold_name} / {metric_name}: "
            "resultado OOF não reproduz a referência. "
            f"OOF={obtained:.12f}; "
            f"referência={expected:.12f}; "
            f"diferença={difference:+.12e}."
        )

    return difference


def main() -> None:
    """Executa a auditoria de reprodutibilidade OOF."""
    print("=" * 96)
    print("AUDITORIA DE REPRODUTIBILIDADE — PREDIÇÕES OOF DO MODELO FINALISTA")
    print("=" * 96)

    print()
    print("Carregando predições OOF...")

    oof = pd.read_parquet(OOF_INPUT)

    print("Carregando resultados do Modelo A...")

    reference = pd.read_csv(MODEL_A_RESULTS)

    validate_inputs(
        oof,
        reference,
    )

    reference = reference.loc[reference["modelo"].eq(FINALIST_MODEL)].copy()

    records = []

    maximum_absolute_difference = 0.0

    grouped = oof.groupby(
        [
            "horizonte",
            "fold",
        ],
        sort=True,
        observed=True,
    )

    for (
        horizon,
        fold_name,
    ), subset in grouped:
        horizon = int(horizon)

        print()
        print(f"H{horizon} / {fold_name}")

        evaluation = evaluate_model_predictions(
            y_true=subset["target"],
            y_score=subset["score"],
            current_risk=subset[CURRENT_RISK_COLUMN],
            threshold=(DEFAULT_DECISION_THRESHOLD),
        )

        expected_rows = reference.loc[
            reference["horizonte"].eq(horizon) & reference["fold"].eq(fold_name)
        ]

        if len(expected_rows) != 1:
            raise ValueError(
                f"H{horizon} / {fold_name}: "
                "não foi encontrada exatamente uma "
                "linha de referência."
            )

        expected = expected_rows.iloc[0]

        record = {
            "horizonte": horizon,
            "fold": fold_name,
            "validacao_ano": int(subset["validacao_ano"].iloc[0]),
            "linhas": len(subset),
        }

        for evaluation_name, prefix in (
            (
                "avaliacao_geral",
                "geral",
            ),
            (
                "early_warning",
                "early_warning",
            ),
        ):
            metrics = evaluation[evaluation_name]

            for metric in METRICS:
                obtained = metrics[metric]

                expected_value = expected[f"{prefix}_{metric}"]

                if pd.isna(expected_value):
                    expected_value = None
                else:
                    expected_value = float(expected_value)

                difference = compare_metric(
                    obtained=obtained,
                    expected=expected_value,
                    metric_name=(f"{prefix}_{metric}"),
                    horizon=horizon,
                    fold_name=fold_name,
                )

                record[f"{prefix}_{metric}_diferenca"] = difference

                if difference is not None:
                    maximum_absolute_difference = max(
                        maximum_absolute_difference,
                        abs(difference),
                    )

        records.append(record)

        print(
            "  AP geral                       : "
            f"{evaluation['avaliacao_geral']['pr_auc_average_precision']:.6f}"
        )

        print(
            "  Brier geral                    : "
            f"{evaluation['avaliacao_geral']['brier_score']:.6f}"
        )

        print(
            "  AP early warning               : "
            f"{evaluation['early_warning']['pr_auc_average_precision']:.6f}"
        )

        print(f"  Diferença máxima até aqui      : {maximum_absolute_difference:.3e}")

    if len(records) != EXPECTED_COMBINATIONS:
        raise ValueError(
            "Quantidade inesperada de combinações auditadas. "
            f"Esperado: {EXPECTED_COMBINATIONS}; "
            f"obtido: {len(records)}."
        )

    report = {
        "status": "APROVADO",
        "modelo": FINALIST_MODEL,
        "conjunto_features": "Modelo A — epidemiológico",
        "threshold": DEFAULT_DECISION_THRESHOLD,
        "tolerancia_absoluta": TOLERANCE,
        "predicoes_oof": len(oof),
        "combinacoes_auditadas": len(records),
        "diferenca_absoluta_maxima": maximum_absolute_difference,
        "teste_final_2025_utilizado": False,
        "resultados": records,
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
    print("=" * 96)
    print("RESULTADO")
    print("=" * 96)

    print(f"Predições OOF                    : {len(oof):,}")

    print(f"Combinações auditadas            : {len(records)}")

    print(f"Tolerância absoluta              : {TOLERANCE:.1e}")

    print(f"Diferença absoluta máxima        : {maximum_absolute_difference:.3e}")

    print("Teste final de 2025 utilizado    : NÃO")

    print(f"Auditoria JSON                   : {AUDIT_OUTPUT}")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
