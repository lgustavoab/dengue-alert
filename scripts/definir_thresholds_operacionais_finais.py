"""Define os thresholds operacionais finais antes do teste de 2025."""

import json

import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.evaluation.thresholds import select_f1_threshold
from dengue_alert.modeling.training import CURRENT_RISK_COLUMN

OOF_INPUT = MASTER_PANEL.parent / "predicoes_oof_modelo_a_hgb_2021_2024.parquet"

CSV_OUTPUT = REPORTS_DIR / "audits" / "thresholds_operacionais_finais.csv"

JSON_OUTPUT = REPORTS_DIR / "audits" / "thresholds_operacionais_finais.json"

EXPECTED_ROWS = 4_410_648
EXPECTED_HORIZONS = (1, 2, 3, 4)
EXPECTED_YEARS = (2021, 2022, 2023, 2024)


def validate_oof(
    dataframe: pd.DataFrame,
) -> None:
    """Valida a base OOF antes da definição final dos thresholds."""
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

    if years != EXPECTED_YEARS:
        raise ValueError(
            f"Anos OOF inesperados. Esperado: {EXPECTED_YEARS}; obtido: {years}."
        )

    if 2025 in years:
        raise ValueError(
            "O teste final de 2025 não pode participar da definição dos thresholds."
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
    """Seleciona observações ainda sem risco elevado na semana atual."""
    current_risk = dataframe[CURRENT_RISK_COLUMN].astype("boolean")

    if current_risk.isna().any():
        raise ValueError("Existem valores ausentes no risco atual.")

    subset = dataframe.loc[~current_risk.astype(bool)]

    if subset.empty:
        raise ValueError("O subconjunto de early warning está vazio.")

    return subset


def main() -> None:
    """Calcula os thresholds finais H1–H4 usando OOF 2021–2024."""
    print("=" * 100)
    print("DEFINIÇÃO DOS THRESHOLDS OPERACIONAIS FINAIS")
    print("=" * 100)

    print()
    print("Carregando predições OOF...")

    dataframe = pd.read_parquet(OOF_INPUT)

    validate_oof(dataframe)

    print(f"Predições OOF                    : {len(dataframe):,}")

    print("Modelo                           : Modelo A + HistGradientBoosting")

    print("Probabilidades                   : raw")

    print("Período de seleção               : 2021–2024")

    print("Subconjunto                      : early warning")

    print("Critério                         : máximo F1")

    print("Regra de desempate               : maior threshold")

    print("Teste final de 2025              : NÃO UTILIZADO")

    records = []

    for horizon in EXPECTED_HORIZONS:
        horizon_data = dataframe.loc[dataframe["horizonte"].eq(horizon)]

        early_data = early_warning_subset(horizon_data)

        result = select_f1_threshold(
            early_data["target"],
            early_data["score"],
        )

        prevalence = result["positivos"] / result["observacoes"]

        record = {
            "horizonte": horizon,
            "threshold": result["threshold"],
            "periodo_selecao_inicio": 2021,
            "periodo_selecao_fim": 2024,
            "observacoes_early_warning": result["observacoes"],
            "positivos_early_warning": result["positivos"],
            "prevalencia_early_warning": prevalence,
            "alertas": result["alertas"],
            "proporcao_alertas": result["proporcao_alertas"],
            "precision_selecao": result["precision"],
            "recall_selecao": result["recall"],
            "f1_selecao": result["f1"],
            "candidatos_threshold": result["candidatos"],
            "criterio": result["criterio"],
            "regra_desempate": result["regra_desempate"],
        }

        records.append(record)

        print()
        print(f"H{horizon}")

        print(f"  Threshold final                 : {record['threshold']:.6f}")

        print(
            "  Observações early warning       : "
            f"{record['observacoes_early_warning']:,}"
        )

        print(
            f"  Positivos early warning         : {record['positivos_early_warning']:,}"
        )

        print(
            "  Prevalência                     : "
            f"{record['prevalencia_early_warning']:.2%}"
        )

        print(f"  F1 no conjunto de seleção       : {record['f1_selecao']:.6f}")

        print(f"  Precision no conjunto seleção   : {record['precision_selecao']:.6f}")

        print(f"  Recall no conjunto seleção      : {record['recall_selecao']:.6f}")

        print(f"  Proporção de alertas            : {record['proporcao_alertas']:.2%}")

    if len(records) != len(EXPECTED_HORIZONS):
        raise ValueError("Quantidade inesperada de thresholds finais.")

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
        "modelo": {
            "algoritmo": "HistGradientBoostingClassifier",
            "conjunto_features": "Modelo A — 23 features epidemiológicas",
            "probabilidades": "raw",
            "calibracao": "não adotada",
        },
        "protocolo_threshold": {
            "periodo_selecao": "2021-2024 OOF",
            "subconjunto": "early warning — risco_elevado(t) = False",
            "criterio": "maximizar F1",
            "regra_desempate": "maior threshold entre empates numéricos",
            "threshold_especifico_por_horizonte": True,
            "teste_final_2025_utilizado": False,
        },
        "observacao_metodologica": (
            "As métricas calculadas no período 2021-2024 "
            "representam desempenho no conjunto utilizado "
            "para seleção dos thresholds e não constituem "
            "estimativa independente de desempenho final."
        ),
        "thresholds": records,
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

    print(f"Thresholds definidos             : {len(records)}")

    print("Horizontes                       : H1, H2, H3, H4")

    print("Calibração                       : NÃO")

    print("Teste final de 2025 utilizado    : NÃO")

    print(f"Thresholds CSV                   : {CSV_OUTPUT}")

    print(f"Auditoria JSON                   : {JSON_OUTPUT}")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
