"""Avalia calibração probabilística com backtest temporal progressivo."""

import json
from statistics import fmean

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
)

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.evaluation.calibration import (
    CALIBRATION_METHODS,
    fit_calibrator,
)
from dengue_alert.modeling.training import CURRENT_RISK_COLUMN

OOF_INPUT = MASTER_PANEL.parent / "predicoes_oof_modelo_a_hgb_2021_2024.parquet"

CSV_OUTPUT = REPORTS_DIR / "audits" / "avaliacao_calibracao_temporal.csv"

JSON_OUTPUT = REPORTS_DIR / "audits" / "avaliacao_calibracao_temporal.json"

EXPECTED_ROWS = 4_410_648
EXPECTED_HORIZONS = (1, 2, 3, 4)
EXPECTED_OOF_YEARS = (2021, 2022, 2023, 2024)
EVALUATION_YEARS = (2022, 2023, 2024)

CONSISTENCY_TOLERANCE = 1e-12


def validate_oof(
    dataframe: pd.DataFrame,
) -> None:
    """Valida a base OOF antes do backtest de calibração."""
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
            "Horizontes OOF inesperados. "
            f"Esperado: {EXPECTED_HORIZONS}; "
            f"obtido: {horizons}."
        )

    years = tuple(sorted(int(value) for value in dataframe["validacao_ano"].unique()))

    if years != EXPECTED_OOF_YEARS:
        raise ValueError(
            f"Anos OOF inesperados. Esperado: {EXPECTED_OOF_YEARS}; obtido: {years}."
        )

    if 2025 in years:
        raise ValueError("O teste final de 2025 não pode participar da calibração.")

    if dataframe["target"].isna().any():
        raise ValueError("Existem targets OOF ausentes.")

    if dataframe["score"].isna().any():
        raise ValueError("Existem scores OOF ausentes.")

    scores = dataframe["score"].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    if not np.isfinite(scores).all():
        raise ValueError("Existem scores OOF não finitos.")

    if ((scores < 0) | (scores > 1)).any():
        raise ValueError("Existem scores OOF fora do intervalo [0, 1].")


def evaluate_probabilities(
    *,
    targets,
    scores,
    current_risk,
) -> dict:
    """Avalia qualidade probabilística geral e em early warning."""
    target_array = np.asarray(
        targets,
        dtype=np.int8,
    )

    score_array = np.asarray(
        scores,
        dtype=np.float64,
    )

    current = pd.Series(
        current_risk,
        dtype="boolean",
    )

    if current.isna().any():
        raise ValueError("Existem estados atuais de risco ausentes.")

    current_array = current.astype("bool").to_numpy()

    if (
        len(
            {
                len(target_array),
                len(score_array),
                len(current_array),
            }
        )
        != 1
    ):
        raise ValueError(
            "Target, score e risco atual devem possuir o mesmo comprimento."
        )

    if not np.isfinite(score_array).all():
        raise ValueError("Probabilidades calibradas não finitas.")

    if ((score_array < 0) | (score_array > 1)).any():
        raise ValueError("Probabilidades calibradas fora de [0, 1].")

    positives = int(target_array.sum())

    general_ap = (
        float(
            average_precision_score(
                target_array,
                score_array,
            )
        )
        if positives
        else None
    )

    early_mask = ~current_array

    if not early_mask.any():
        raise ValueError("O subconjunto de early warning está vazio.")

    early_target = target_array[early_mask]

    early_score = score_array[early_mask]

    early_positives = int(early_target.sum())

    early_ap = (
        float(
            average_precision_score(
                early_target,
                early_score,
            )
        )
        if early_positives
        else None
    )

    return {
        "geral_observacoes": len(target_array),
        "geral_positivos": positives,
        "geral_prevalencia": (positives / len(target_array)),
        "geral_brier_score": float(
            brier_score_loss(
                target_array,
                score_array,
            )
        ),
        "geral_average_precision": general_ap,
        "early_warning_observacoes": int(early_mask.sum()),
        "early_warning_positivos": early_positives,
        "early_warning_prevalencia": (early_positives / int(early_mask.sum())),
        "early_warning_brier_score": float(
            brier_score_loss(
                early_target,
                early_score,
            )
        ),
        "early_warning_average_precision": early_ap,
    }


def run_backtest(
    dataframe: pd.DataFrame,
) -> list[dict]:
    """Executa calibração progressiva H1–H4 em 2022–2024."""
    records = []

    for horizon in EXPECTED_HORIZONS:
        horizon_data = dataframe.loc[dataframe["horizonte"].eq(horizon)]

        print()
        print("=" * 96)
        print(f"HORIZONTE H{horizon}")
        print("=" * 96)

        for evaluation_year in EVALUATION_YEARS:
            calibration_data = horizon_data.loc[
                horizon_data["validacao_ano"].lt(evaluation_year)
            ]

            evaluation_data = horizon_data.loc[
                horizon_data["validacao_ano"].eq(evaluation_year)
            ]

            if calibration_data.empty:
                raise ValueError(
                    f"H{horizon} / {evaluation_year}: base de calibração vazia."
                )

            if evaluation_data.empty:
                raise ValueError(
                    f"H{horizon} / {evaluation_year}: base de avaliação vazia."
                )

            calibration_years = sorted(
                int(value) for value in calibration_data["validacao_ano"].unique()
            )

            print()
            print(
                f"Avaliação {evaluation_year} | "
                "calibração "
                f"{calibration_years[0]}"
                "–"
                f"{calibration_years[-1]}"
            )

            raw_brier = None

            year_records = []

            for method in CALIBRATION_METHODS:
                calibrator = fit_calibrator(
                    method,
                    calibration_data["score"],
                    calibration_data["target"],
                )

                calibrated_scores = calibrator.predict(evaluation_data["score"])

                metrics = evaluate_probabilities(
                    targets=(evaluation_data["target"]),
                    scores=(calibrated_scores),
                    current_risk=(evaluation_data[CURRENT_RISK_COLUMN]),
                )

                record = {
                    "horizonte": horizon,
                    "ano_avaliacao": evaluation_year,
                    "calibracao_ano_inicio": calibration_years[0],
                    "calibracao_ano_fim": calibration_years[-1],
                    "calibracao_anos": len(calibration_years),
                    "calibracao_observacoes": len(calibration_data),
                    "metodo": method,
                    **metrics,
                }

                if method == "raw":
                    raw_brier = metrics["geral_brier_score"]

                year_records.append(record)

                print(
                    f"  {method:<8} | "
                    "Brier geral="
                    f"{metrics['geral_brier_score']:.6f} | "
                    "AP geral="
                    f"{metrics['geral_average_precision']:.6f} | "
                    "Brier early="
                    f"{metrics['early_warning_brier_score']:.6f} | "
                    "AP early="
                    f"{metrics['early_warning_average_precision']:.6f}"
                )

            if raw_brier is None:
                raise RuntimeError("Resultado raw não encontrado.")

            for record in year_records:
                record["delta_brier_geral_vs_raw"] = (
                    record["geral_brier_score"] - raw_brier
                )

            records.extend(year_records)

    return records


def summarize_and_select(
    records: list[dict],
) -> tuple[list[dict], dict[str, str]]:
    """Resume resultados e seleciona calibração de forma conservadora."""
    dataframe = pd.DataFrame(records)

    summaries = []

    selected_methods = {}

    for horizon in EXPECTED_HORIZONS:
        horizon_data = dataframe.loc[dataframe["horizonte"].eq(horizon)]

        method_summaries = []

        for method in CALIBRATION_METHODS:
            method_data = horizon_data.loc[
                horizon_data["metodo"].eq(method)
            ].sort_values("ano_avaliacao")

            if len(method_data) != len(EVALUATION_YEARS):
                raise ValueError(
                    f"H{horizon} / {method}: quantidade inesperada de anos."
                )

            deltas = method_data["delta_brier_geral_vs_raw"]

            wins = int((deltas < -CONSISTENCY_TOLERANCE).sum())

            losses = int((deltas > CONSISTENCY_TOLERANCE).sum())

            ties = len(deltas) - wins - losses

            mean_brier = float(fmean(method_data["geral_brier_score"]))

            mean_early_brier = float(fmean(method_data["early_warning_brier_score"]))

            mean_delta = float(fmean(deltas))

            eligible = method == "raw" or (
                wins == len(EVALUATION_YEARS) and mean_delta < -CONSISTENCY_TOLERANCE
            )

            summary = {
                "horizonte": horizon,
                "metodo": method,
                "anos_avaliados": len(method_data),
                "brier_geral_medio": mean_brier,
                "brier_early_warning_medio": mean_early_brier,
                "delta_brier_geral_medio_vs_raw": mean_delta,
                "anos_melhor_que_raw": wins,
                "anos_pior_que_raw": losses,
                "anos_empate_com_raw": int(ties),
                "elegivel": eligible,
            }

            summaries.append(summary)

            method_summaries.append(summary)

        calibrated_candidates = [
            summary
            for summary in method_summaries
            if (summary["metodo"] != "raw" and summary["elegivel"])
        ]

        if calibrated_candidates:
            selected = min(
                calibrated_candidates,
                key=lambda item: (
                    item["brier_geral_medio"],
                    item["metodo"],
                ),
            )
        else:
            selected = next(
                summary for summary in method_summaries if summary["metodo"] == "raw"
            )

        selected_methods[f"h{horizon}"] = selected["metodo"]

    return (
        summaries,
        selected_methods,
    )


def print_selection(
    summaries: list[dict],
    selected_methods: dict[str, str],
) -> None:
    """Exibe o resultado da regra de seleção."""
    print()
    print("=" * 96)
    print("SELEÇÃO DE CALIBRAÇÃO")
    print("=" * 96)

    for horizon in EXPECTED_HORIZONS:
        print()
        print(f"H{horizon}")

        horizon_summaries = [item for item in summaries if item["horizonte"] == horizon]

        for summary in horizon_summaries:
            print(
                f"  {summary['metodo']:<8} | "
                "Brier médio="
                f"{summary['brier_geral_medio']:.6f} | "
                "delta="
                f"{summary['delta_brier_geral_medio_vs_raw']:+.6f} | "
                "anos melhores="
                f"{summary['anos_melhor_que_raw']}/3 | "
                "elegível="
                f"{'SIM' if summary['elegivel'] else 'NÃO'}"
            )

        print(f"  Método selecionado             : {selected_methods[f'h{horizon}']}")


def main() -> None:
    """Executa o backtest temporal de calibração."""
    print("=" * 96)
    print("BACKTEST TEMPORAL DE CALIBRAÇÃO — MODELO A + HISTGRADIENTBOOSTING")
    print("=" * 96)

    print()
    print("Carregando predições OOF...")

    dataframe = pd.read_parquet(OOF_INPUT)

    validate_oof(dataframe)

    print(f"Predições OOF                    : {len(dataframe):,}")

    print("Período OOF                      : 2021–2024")

    print("Anos avaliados                   : 2022, 2023, 2024")

    print("Métodos                          : " + ", ".join(CALIBRATION_METHODS))

    print("Regra de seleção                 : calibração deve superar raw em 3/3 anos")

    print("Teste final de 2025              : NÃO UTILIZADO")

    records = run_backtest(dataframe)

    summaries, selected_methods = summarize_and_select(records)

    print_selection(
        summaries,
        selected_methods,
    )

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
        "protocolo": {
            "periodo_oof": "2021-2024",
            "anos_avaliacao": list(EVALUATION_YEARS),
            "metodos": list(CALIBRATION_METHODS),
            "metrica_selecao": "Brier Score geral",
            "regra_consistencia": (
                "Método calibrado somente é elegível "
                "se superar raw nos três anos "
                "2022, 2023 e 2024 e possuir "
                "Brier médio menor."
            ),
            "teste_final_2025_utilizado": False,
        },
        "resultados": records,
        "resumo": summaries,
        "metodo_selecionado_por_horizonte": selected_methods,
    }

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
    print("=" * 96)
    print("RESULTADO")
    print("=" * 96)

    print(f"Avaliações realizadas            : {len(records)}")

    print(f"Métodos por horizonte            : {len(CALIBRATION_METHODS)}")

    print("Teste final de 2025 utilizado    : NÃO")

    print(f"Resultados CSV                   : {CSV_OUTPUT}")

    print(f"Auditoria JSON                   : {JSON_OUTPUT}")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
