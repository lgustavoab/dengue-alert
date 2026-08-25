"""Compara os Modelos A e B do Dengue Alert de forma reproduzível."""

import json
from pathlib import Path

import pandas as pd

from dengue_alert.config.paths import REPORTS_DIR

AUDIT_DIR = REPORTS_DIR / "audits"

MODEL_A_CSV = AUDIT_DIR / "avaliacao_modelo_a.csv"
MODEL_B_CSV = AUDIT_DIR / "avaliacao_modelo_b.csv"

OUTPUT_CSV = AUDIT_DIR / "comparacao_modelos_ab.csv"
OUTPUT_JSON = AUDIT_DIR / "comparacao_modelos_ab.json"

EXPECTED_ROWS = 32
EXPECTED_FOLDS = 4
EXPECTED_HORIZONS = {1, 2, 3, 4}

KEY_COLUMNS = (
    "modelo",
    "horizonte",
    "fold",
    "validacao_ano",
)

COMPARISON_METRICS = (
    "geral_pr_auc_average_precision",
    "geral_recall",
    "geral_f1",
    "geral_balanced_accuracy",
    "geral_brier_score",
    "early_warning_pr_auc_average_precision",
    "early_warning_recall",
    "early_warning_f1",
    "early_warning_balanced_accuracy",
    "early_warning_brier_score",
)


def validate_input_file(
    path: Path,
) -> None:
    """Garante que o arquivo de entrada existe."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")


def validate_dataframe(
    dataframe: pd.DataFrame,
    *,
    name: str,
) -> None:
    """Valida estrutura e cardinalidade dos resultados."""
    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            f"{name}: quantidade inesperada de linhas. "
            f"Esperado: {EXPECTED_ROWS}; "
            f"obtido: {len(dataframe)}."
        )

    required_columns = {
        *KEY_COLUMNS,
        *COMPARISON_METRICS,
    }

    missing = sorted(required_columns - set(dataframe.columns))

    if missing:
        raise ValueError(f"{name}: colunas ausentes: " + ", ".join(missing) + ".")

    duplicates = int(dataframe.duplicated(subset=list(KEY_COLUMNS)).sum())

    if duplicates:
        raise ValueError(f"{name}: existem {duplicates} combinações duplicadas.")

    horizons = set(dataframe["horizonte"].unique())

    if horizons != EXPECTED_HORIZONS:
        raise ValueError(
            f"{name}: horizontes inesperados. "
            f"Esperado: {sorted(EXPECTED_HORIZONS)}; "
            f"obtido: {sorted(horizons)}."
        )

    combinations = dataframe.groupby(
        [
            "modelo",
            "horizonte",
        ],
        observed=True,
    ).size()

    if not (combinations == EXPECTED_FOLDS).all():
        raise ValueError(
            f"{name}: cada combinação modelo × horizonte "
            f"deve possuir {EXPECTED_FOLDS} folds."
        )


def build_paired_comparison(
    model_a: pd.DataFrame,
    model_b: pd.DataFrame,
) -> pd.DataFrame:
    """Cria comparação pareada A × B para cada fold."""
    columns = [
        *KEY_COLUMNS,
        *COMPARISON_METRICS,
    ]

    paired = model_a.loc[
        :,
        columns,
    ].merge(
        model_b.loc[
            :,
            columns,
        ],
        on=list(KEY_COLUMNS),
        how="inner",
        suffixes=(
            "_a",
            "_b",
        ),
        validate="one_to_one",
    )

    if len(paired) != EXPECTED_ROWS:
        raise ValueError(
            f"A comparação pareada não preservou as {EXPECTED_ROWS} execuções."
        )

    for metric in COMPARISON_METRICS:
        paired[f"{metric}_delta_b_menos_a"] = (
            paired[f"{metric}_b"] - paired[f"{metric}_a"]
        )

    return paired.sort_values(
        [
            "modelo",
            "horizonte",
            "validacao_ano",
        ]
    ).reset_index(drop=True)


def count_wins(
    values: pd.Series,
    *,
    higher_is_better: bool,
) -> dict:
    """Conta folds em que B foi melhor, pior ou igual a A."""
    tolerance = 1e-12

    if higher_is_better:
        wins_b = int((values > tolerance).sum())

        wins_a = int((values < -tolerance).sum())
    else:
        wins_b = int((values < -tolerance).sum())

        wins_a = int((values > tolerance).sum())

    ties = len(values) - wins_b - wins_a

    return {
        "modelo_b_melhor": wins_b,
        "modelo_a_melhor": wins_a,
        "empates": int(ties),
    }


def summarize_group(
    group: pd.DataFrame,
) -> dict:
    """Resume um algoritmo e horizonte nos quatro folds."""
    result = {
        "folds": len(group),
    }

    for metric in COMPARISON_METRICS:
        column_a = f"{metric}_a"

        column_b = f"{metric}_b"

        delta_column = f"{metric}_delta_b_menos_a"

        result[f"{metric}_media_a"] = float(group[column_a].mean())

        result[f"{metric}_media_b"] = float(group[column_b].mean())

        result[f"{metric}_delta_medio_b_menos_a"] = float(group[delta_column].mean())

    result["consistencia_ap_geral"] = count_wins(
        group["geral_pr_auc_average_precision_delta_b_menos_a"],
        higher_is_better=True,
    )

    result["consistencia_ap_early_warning"] = count_wins(
        group["early_warning_pr_auc_average_precision_delta_b_menos_a"],
        higher_is_better=True,
    )

    result["consistencia_brier_geral"] = count_wins(
        group["geral_brier_score_delta_b_menos_a"],
        higher_is_better=False,
    )

    return result


def build_summary(
    paired: pd.DataFrame,
) -> list[dict]:
    """Gera o resumo por algoritmo e horizonte."""
    records = []

    grouped = paired.groupby(
        [
            "modelo",
            "horizonte",
        ],
        sort=True,
        observed=True,
    )

    for (
        model_name,
        horizon,
    ), group in grouped:
        record = {
            "modelo": model_name,
            "horizonte": int(horizon),
        }

        record.update(summarize_group(group))

        records.append(record)

    return records


def print_summary(
    summaries: list[dict],
) -> None:
    """Exibe as principais diferenças A × B."""
    print()
    print("=" * 100)
    print("COMPARAÇÃO MODELO A × MODELO B")
    print("=" * 100)

    for record in summaries:
        print()
        print(f"{record['modelo']} — H{record['horizonte']}")

        ap_a = record["geral_pr_auc_average_precision_media_a"]

        ap_b = record["geral_pr_auc_average_precision_media_b"]

        ap_delta = record["geral_pr_auc_average_precision_delta_medio_b_menos_a"]

        early_a = record["early_warning_pr_auc_average_precision_media_a"]

        early_b = record["early_warning_pr_auc_average_precision_media_b"]

        early_delta = record[
            "early_warning_pr_auc_average_precision_delta_medio_b_menos_a"
        ]

        brier_a = record["geral_brier_score_media_a"]

        brier_b = record["geral_brier_score_media_b"]

        brier_delta = record["geral_brier_score_delta_medio_b_menos_a"]

        general_consistency = record["consistencia_ap_geral"]

        early_consistency = record["consistencia_ap_early_warning"]

        print(f"  AP geral A                     : {ap_a:.6f}")

        print(f"  AP geral B                     : {ap_b:.6f}")

        print(f"  Delta AP geral B - A           : {ap_delta:+.6f}")

        print(
            "  Folds com AP geral melhor em B : "
            f"{general_consistency['modelo_b_melhor']}/"
            f"{EXPECTED_FOLDS}"
        )

        print(f"  AP early warning A             : {early_a:.6f}")

        print(f"  AP early warning B             : {early_b:.6f}")

        print(f"  Delta AP early B - A           : {early_delta:+.6f}")

        print(
            "  Folds com AP early melhor em B : "
            f"{early_consistency['modelo_b_melhor']}/"
            f"{EXPECTED_FOLDS}"
        )

        print(f"  Brier geral A                  : {brier_a:.6f}")

        print(f"  Brier geral B                  : {brier_b:.6f}")

        print(f"  Delta Brier B - A              : {brier_delta:+.6f}")


def main() -> None:
    """Executa a comparação reproduzível entre os Modelos A e B."""
    print("=" * 100)
    print("AUDITORIA COMPARATIVA — MODELO A × MODELO B")
    print("=" * 100)

    validate_input_file(MODEL_A_CSV)

    validate_input_file(MODEL_B_CSV)

    model_a = pd.read_csv(MODEL_A_CSV)

    model_b = pd.read_csv(MODEL_B_CSV)

    validate_dataframe(
        model_a,
        name="Modelo A",
    )

    validate_dataframe(
        model_b,
        name="Modelo B",
    )

    paired = build_paired_comparison(
        model_a,
        model_b,
    )

    summaries = build_summary(paired)

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    paired.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8",
    )

    report = {
        "status": "APROVADO",
        "comparacao": "Modelo A versus Modelo B",
        "interpretacao_modelos": {
            "modelo_a": "23 features epidemiológicas",
            "modelo_b": "23 features epidemiológicas + 36 features climáticas",
        },
        "protocolo": {
            "comparacao_pareada": True,
            "chaves": list(KEY_COLUMNS),
            "folds_por_combinacao": EXPECTED_FOLDS,
            "horizontes": sorted(EXPECTED_HORIZONS),
            "teste_final_2025_utilizado": False,
            "delta": "Modelo B - Modelo A",
        },
        "resumo": summaries,
    }

    with OUTPUT_JSON.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print_summary(summaries)

    print()
    print("=" * 100)
    print("RESULTADO")
    print("=" * 100)

    print(f"Execuções pareadas               : {len(paired)}")

    print(f"Combinações algoritmo × horizonte: {len(summaries)}")

    print("Teste final de 2025 utilizado    : NÃO")

    print(f"Comparação CSV                   : {OUTPUT_CSV}")

    print(f"Auditoria JSON                   : {OUTPUT_JSON}")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
