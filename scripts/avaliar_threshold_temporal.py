"""Avalia thresholds operacionais com backtest temporal progressivo."""

import json
from statistics import fmean

import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.evaluation.thresholds import (
    evaluate_threshold,
    select_f1_threshold,
)
from dengue_alert.modeling.training import (
    CURRENT_RISK_COLUMN,
    DEFAULT_DECISION_THRESHOLD,
)

OOF_INPUT = MASTER_PANEL.parent / "predicoes_oof_modelo_a_hgb_2021_2024.parquet"

CSV_OUTPUT = REPORTS_DIR / "audits" / "avaliacao_threshold_temporal.csv"

JSON_OUTPUT = REPORTS_DIR / "audits" / "avaliacao_threshold_temporal.json"

EXPECTED_ROWS = 4_410_648
EXPECTED_HORIZONS = (1, 2, 3, 4)
EXPECTED_OOF_YEARS = (2021, 2022, 2023, 2024)
EVALUATION_YEARS = (2022, 2023, 2024)


def validate_oof(
    dataframe: pd.DataFrame,
) -> None:
    """Valida a base OOF usada no backtest de threshold."""
    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            "Quantidade inesperada de predições OOF. "
            f"Esperado: {EXPECTED_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    required_columns = {
        "horizonte",
        "validacao_ano",
        "target",
        "score",
        CURRENT_RISK_COLUMN,
    }

    missing = sorted(required_columns - set(dataframe.columns))

    if missing:
        raise ValueError("Colunas OOF ausentes: " + ", ".join(missing) + ".")

    horizons = tuple(sorted(int(value) for value in dataframe["horizonte"].unique()))

    if horizons != EXPECTED_HORIZONS:
        raise ValueError(
            "Horizontes inesperados. "
            f"Esperado: {EXPECTED_HORIZONS}; "
            f"obtido: {horizons}."
        )

    years = tuple(sorted(int(value) for value in dataframe["validacao_ano"].unique()))

    if years != EXPECTED_OOF_YEARS:
        raise ValueError(
            f"Anos OOF inesperados. Esperado: {EXPECTED_OOF_YEARS}; obtido: {years}."
        )

    if 2025 in years:
        raise ValueError(
            "O teste final de 2025 não pode participar da seleção de threshold."
        )

    if dataframe["target"].isna().any():
        raise ValueError("Existem targets OOF ausentes.")

    if dataframe["score"].isna().any():
        raise ValueError("Existem scores OOF ausentes.")

    if dataframe[CURRENT_RISK_COLUMN].isna().any():
        raise ValueError("Existem estados atuais de risco ausentes.")


def early_warning_subset(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Mantém observações sem risco elevado na semana atual."""
    current_risk = dataframe[CURRENT_RISK_COLUMN].astype("boolean")

    if current_risk.isna().any():
        raise ValueError("Existem valores ausentes em risco atual.")

    subset = dataframe.loc[~current_risk.astype(bool)]

    if subset.empty:
        raise ValueError("O subconjunto de early warning está vazio.")

    return subset


def flatten_metrics(
    metrics: dict,
    *,
    prefix: str,
) -> dict:
    """Transforma métricas de threshold em colunas tabulares."""
    confusion = metrics["matriz_confusao"]

    return {
        f"{prefix}_observacoes": metrics["observacoes"],
        f"{prefix}_positivos": metrics["positivos"],
        f"{prefix}_negativos": metrics["negativos"],
        f"{prefix}_alertas": metrics["alertas"],
        f"{prefix}_proporcao_alertas": metrics["proporcao_alertas"],
        f"{prefix}_precision": metrics["precision"],
        f"{prefix}_recall": metrics["recall"],
        f"{prefix}_f1": metrics["f1"],
        f"{prefix}_tn": confusion["tn"],
        f"{prefix}_fp": confusion["fp"],
        f"{prefix}_fn": confusion["fn"],
        f"{prefix}_tp": confusion["tp"],
    }


def run_backtest(
    dataframe: pd.DataFrame,
) -> list[dict]:
    """Executa o backtest temporal dos thresholds operacionais."""
    records = []

    for horizon in EXPECTED_HORIZONS:
        horizon_data = dataframe.loc[dataframe["horizonte"].eq(horizon)]

        print()
        print("=" * 100)
        print(f"HORIZONTE H{horizon}")
        print("=" * 100)

        for evaluation_year in EVALUATION_YEARS:
            selection_data = horizon_data.loc[
                horizon_data["validacao_ano"].lt(evaluation_year)
            ]

            evaluation_data = horizon_data.loc[
                horizon_data["validacao_ano"].eq(evaluation_year)
            ]

            if selection_data.empty:
                raise ValueError(
                    f"H{horizon} / {evaluation_year}: base de seleção vazia."
                )

            if evaluation_data.empty:
                raise ValueError(
                    f"H{horizon} / {evaluation_year}: base de avaliação vazia."
                )

            selection_early = early_warning_subset(selection_data)

            evaluation_early = early_warning_subset(evaluation_data)

            selection_years = sorted(
                int(value) for value in selection_data["validacao_ano"].unique()
            )

            selected = select_f1_threshold(
                selection_early["target"],
                selection_early["score"],
            )

            threshold = selected["threshold"]

            selected_early = evaluate_threshold(
                evaluation_early["target"],
                evaluation_early["score"],
                threshold=threshold,
            )

            selected_general = evaluate_threshold(
                evaluation_data["target"],
                evaluation_data["score"],
                threshold=threshold,
            )

            fixed_early = evaluate_threshold(
                evaluation_early["target"],
                evaluation_early["score"],
                threshold=(DEFAULT_DECISION_THRESHOLD),
            )

            fixed_general = evaluate_threshold(
                evaluation_data["target"],
                evaluation_data["score"],
                threshold=(DEFAULT_DECISION_THRESHOLD),
            )

            record = {
                "horizonte": horizon,
                "ano_avaliacao": evaluation_year,
                "selecao_ano_inicio": selection_years[0],
                "selecao_ano_fim": selection_years[-1],
                "selecao_anos": len(selection_years),
                "selecao_observacoes_early": len(selection_early),
                "selecao_positivos_early": int(selection_early["target"].sum()),
                "threshold_selecionado": threshold,
                "selecao_f1": selected["f1"],
                "selecao_precision": selected["precision"],
                "selecao_recall": selected["recall"],
                "selecao_proporcao_alertas": selected["proporcao_alertas"],
                **flatten_metrics(
                    selected_early,
                    prefix=("selecionado_early"),
                ),
                **flatten_metrics(
                    selected_general,
                    prefix=("selecionado_geral"),
                ),
                **flatten_metrics(
                    fixed_early,
                    prefix=("fixo_05_early"),
                ),
                **flatten_metrics(
                    fixed_general,
                    prefix=("fixo_05_geral"),
                ),
            }

            record["delta_f1_early_vs_05"] = (
                record["selecionado_early_f1"] - record["fixo_05_early_f1"]
            )

            record["delta_recall_early_vs_05"] = (
                record["selecionado_early_recall"] - record["fixo_05_early_recall"]
            )

            record["delta_precision_early_vs_05"] = (
                record["selecionado_early_precision"]
                - record["fixo_05_early_precision"]
            )

            records.append(record)

            print()
            print(
                f"Avaliação {evaluation_year} | "
                "seleção "
                f"{selection_years[0]}"
                "–"
                f"{selection_years[-1]}"
            )

            print(f"  Threshold selecionado           : {threshold:.6f}")

            print(f"  F1 no período de seleção        : {selected['f1']:.6f}")

            print(f"  Early F1 — selecionado          : {selected_early['f1']:.6f}")

            print(
                f"  Early precision — selecionado   : {selected_early['precision']:.6f}"
            )

            print(f"  Early recall — selecionado      : {selected_early['recall']:.6f}")

            print(
                "  Early alertas — selecionado     : "
                f"{selected_early['proporcao_alertas']:.2%}"
            )

            print(f"  Early F1 — threshold 0.50       : {fixed_early['f1']:.6f}")

            print(f"  Early recall — threshold 0.50   : {fixed_early['recall']:.6f}")

            print(
                "  Delta F1 vs 0.50                : "
                f"{record['delta_f1_early_vs_05']:+.6f}"
            )

    return records


def build_summary(
    records: list[dict],
) -> list[dict]:
    """Resume estabilidade e desempenho do threshold por horizonte."""
    dataframe = pd.DataFrame(records)

    summaries = []

    for horizon in EXPECTED_HORIZONS:
        subset = dataframe.loc[dataframe["horizonte"].eq(horizon)].sort_values(
            "ano_avaliacao"
        )

        if len(subset) != len(EVALUATION_YEARS):
            raise ValueError(
                f"H{horizon}: quantidade inesperada de avaliações temporais."
            )

        thresholds = subset["threshold_selecionado"]

        delta_f1 = subset["delta_f1_early_vs_05"]

        summaries.append(
            {
                "horizonte": horizon,
                "avaliacoes": len(subset),
                "threshold_medio": float(fmean(thresholds)),
                "threshold_minimo": float(thresholds.min()),
                "threshold_maximo": float(thresholds.max()),
                "early_f1_medio": float(fmean(subset["selecionado_early_f1"])),
                "early_precision_media": float(
                    fmean(subset["selecionado_early_precision"])
                ),
                "early_recall_medio": float(fmean(subset["selecionado_early_recall"])),
                "early_proporcao_alertas_media": float(
                    fmean(subset["selecionado_early_proporcao_alertas"])
                ),
                "fixo_05_early_f1_medio": float(fmean(subset["fixo_05_early_f1"])),
                "delta_f1_early_medio_vs_05": float(fmean(delta_f1)),
                "anos_f1_melhor_que_05": int((delta_f1 > 0).sum()),
                "anos_f1_pior_que_05": int((delta_f1 < 0).sum()),
            }
        )

    return summaries


def print_summary(
    summaries: list[dict],
) -> None:
    """Exibe o resumo temporal por horizonte."""
    print()
    print("=" * 100)
    print("RESUMO DO BACKTEST OPERACIONAL")
    print("=" * 100)

    for summary in summaries:
        print()
        print(f"H{summary['horizonte']}")

        print(f"  Threshold médio                 : {summary['threshold_medio']:.6f}")

        print(
            "  Faixa de thresholds             : "
            f"{summary['threshold_minimo']:.6f}"
            " – "
            f"{summary['threshold_maximo']:.6f}"
        )

        print(f"  Early F1 médio                  : {summary['early_f1_medio']:.6f}")

        print(
            "  Early precision média           : "
            f"{summary['early_precision_media']:.6f}"
        )

        print(
            f"  Early recall médio              : {summary['early_recall_medio']:.6f}"
        )

        print(
            "  Proporção média de alertas      : "
            f"{summary['early_proporcao_alertas_media']:.2%}"
        )

        print(
            "  F1 médio com threshold 0.50     : "
            f"{summary['fixo_05_early_f1_medio']:.6f}"
        )

        print(
            "  Delta F1 médio vs 0.50          : "
            f"{summary['delta_f1_early_medio_vs_05']:+.6f}"
        )

        print(
            f"  Anos com F1 melhor que 0.50     : {summary['anos_f1_melhor_que_05']}/3"
        )


def main() -> None:
    """Executa a avaliação temporal dos thresholds."""
    print("=" * 100)
    print("BACKTEST TEMPORAL DE THRESHOLD — MODELO A + HISTGRADIENTBOOSTING")
    print("=" * 100)

    print()
    print("Carregando predições OOF...")

    dataframe = pd.read_parquet(OOF_INPUT)

    validate_oof(dataframe)

    print(f"Predições OOF                    : {len(dataframe):,}")

    print("Scores                           : raw")

    print("Critério de seleção              : máximo F1 no subconjunto early warning")

    print("Anos de backtest                 : 2022, 2023, 2024")

    print(
        f"Referência                       : threshold {DEFAULT_DECISION_THRESHOLD:.2f}"
    )

    print("Teste final de 2025              : NÃO UTILIZADO")

    records = run_backtest(dataframe)

    if len(records) != 12:
        raise ValueError(
            "Quantidade inesperada de avaliações. "
            f"Esperado: 12; obtido: {len(records)}."
        )

    summaries = build_summary(records)

    print_summary(summaries)

    CSV_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(records).to_csv(
        CSV_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    report = {
        "status": "APROVADO",
        "modelo": "Modelo A + HistGradientBoosting",
        "probabilidades": "raw",
        "protocolo": {
            "criterio_threshold": "maximizar F1 no subconjunto early warning",
            "regra_desempate": "maior threshold entre empates numéricos",
            "anos_oof": list(EXPECTED_OOF_YEARS),
            "anos_avaliacao": list(EVALUATION_YEARS),
            "threshold_referencia": DEFAULT_DECISION_THRESHOLD,
            "teste_final_2025_utilizado": False,
        },
        "resultados": records,
        "resumo": summaries,
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
    print("RESULTADO")
    print("=" * 100)

    print(f"Avaliações temporais             : {len(records)}")

    print("Horizontes                       : H1, H2, H3, H4")

    print("Teste final de 2025 utilizado    : NÃO")

    print(f"Resultados CSV                   : {CSV_OUTPUT}")

    print(f"Auditoria JSON                   : {JSON_OUTPUT}")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
