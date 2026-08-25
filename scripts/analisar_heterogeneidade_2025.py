"""Analisa heterogeneidade pós-teste das predições finais de 2025."""

import json

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.modeling.splits import MUNICIPALITY_COLUMN, YEAR_COLUMN
from dengue_alert.modeling.training import CURRENT_RISK_COLUMN

PREDICTIONS_INPUT = MASTER_PANEL.parent / "predicoes_avaliacao_final_2025.parquet"

FINAL_TEST_INPUT = MASTER_PANEL.parent / "dataset_teste_final_2025.parquet"

PROFILE_INPUT = (
    MASTER_PANEL.parent / "perfil_epidemiologico_municipios_2018_2024.parquet"
)

REGION_OUTPUT = REPORTS_DIR / "audits" / "heterogeneidade_2025_regiao.csv"

UF_OUTPUT = REPORTS_DIR / "audits" / "heterogeneidade_2025_uf.csv"

POPULATION_OUTPUT = (
    REPORTS_DIR / "audits" / "heterogeneidade_2025_porte_populacional.csv"
)

PROFILE_OUTPUT = (
    REPORTS_DIR / "audits" / "heterogeneidade_2025_perfil_epidemiologico.csv"
)

AUDIT_OUTPUT = REPORTS_DIR / "audits" / "heterogeneidade_2025.json"


EXPECTED_PREDICTION_ROWS = 1_124_938
EXPECTED_FINAL_TEST_ROWS = 295_210
EXPECTED_PROFILE_MUNICIPALITIES = 5_569
EXPECTED_ELIGIBLE_MUNICIPALITIES = 5_569
EXPECTED_HORIZONS = (1, 2, 3, 4)

FROZEN_THRESHOLDS = {
    1: 0.187687,
    2: 0.190783,
    3: 0.167991,
    4: 0.157138,
}

PROFILE_COLUMN = "quartil_epidemiologico"

REGION_BY_IBGE_PREFIX = {
    "11": "Norte",
    "12": "Norte",
    "13": "Norte",
    "14": "Norte",
    "15": "Norte",
    "16": "Norte",
    "17": "Norte",
    "21": "Nordeste",
    "22": "Nordeste",
    "23": "Nordeste",
    "24": "Nordeste",
    "25": "Nordeste",
    "26": "Nordeste",
    "27": "Nordeste",
    "28": "Nordeste",
    "29": "Nordeste",
    "31": "Sudeste",
    "32": "Sudeste",
    "33": "Sudeste",
    "35": "Sudeste",
    "41": "Sul",
    "42": "Sul",
    "43": "Sul",
    "50": "Centro-Oeste",
    "51": "Centro-Oeste",
    "52": "Centro-Oeste",
    "53": "Centro-Oeste",
}

REGION_ORDER = (
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul",
)

POPULATION_LABELS = (
    "Muito pequeno",
    "Pequeno",
    "Médio",
    "Grande",
    "Muito grande",
)

PROFILE_LABELS = (
    "Q1",
    "Q2",
    "Q3",
    "Q4",
)


def validate_predictions(
    dataframe: pd.DataFrame,
) -> None:
    """Valida as predições congeladas da avaliação final."""
    if len(dataframe) != EXPECTED_PREDICTION_ROWS:
        raise ValueError(
            "Quantidade inesperada de predições finais. "
            f"Esperado: {EXPECTED_PREDICTION_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    required_columns = {
        MUNICIPALITY_COLUMN,
        "nome_municipio_ibge",
        "nome_uf_ibge",
        YEAR_COLUMN,
        "semana_epidemiologica",
        "data_inicio_semana",
        CURRENT_RISK_COLUMN,
        "target",
        "horizonte",
        "score",
        "threshold",
        "predicao",
    }

    missing = sorted(required_columns - set(dataframe.columns))

    if missing:
        raise ValueError(
            "Colunas ausentes nas predições finais: " + ", ".join(missing) + "."
        )

    years = {int(value) for value in dataframe[YEAR_COLUMN].unique()}

    if years != {2025}:
        raise ValueError(
            f"As predições devem conter exclusivamente 2025. Obtido: {sorted(years)}."
        )

    horizons = tuple(sorted(int(value) for value in dataframe["horizonte"].unique()))

    if horizons != EXPECTED_HORIZONS:
        raise ValueError(
            "Horizontes inesperados. "
            f"Esperado: {EXPECTED_HORIZONS}; "
            f"obtido: {horizons}."
        )

    municipalities = int(dataframe[MUNICIPALITY_COLUMN].nunique())

    if municipalities != EXPECTED_ELIGIBLE_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de municípios elegíveis. "
            f"Esperado: {EXPECTED_ELIGIBLE_MUNICIPALITIES:,}; "
            f"obtido: {municipalities:,}."
        )

    duplicates = int(
        dataframe.duplicated(
            subset=[
                MUNICIPALITY_COLUMN,
                "data_inicio_semana",
                "horizonte",
            ]
        ).sum()
    )

    if duplicates:
        raise ValueError(f"Foram encontradas {duplicates:,} predições duplicadas.")

    if dataframe["target"].isna().any():
        raise ValueError("Existem targets ausentes nas predições finais.")

    if dataframe["score"].isna().any():
        raise ValueError("Existem scores ausentes nas predições finais.")

    scores = dataframe["score"].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    if not np.isfinite(scores).all():
        raise ValueError("Existem scores não finitos.")

    if ((scores < 0) | (scores > 1)).any():
        raise ValueError("Existem scores fora do intervalo [0, 1].")

    for horizon, frozen_threshold in FROZEN_THRESHOLDS.items():
        subset = dataframe.loc[dataframe["horizonte"].eq(horizon)]

        thresholds = subset["threshold"].unique()

        if len(thresholds) != 1:
            raise ValueError(f"H{horizon}: mais de um threshold encontrado.")

        obtained = float(thresholds[0])

        if not np.isclose(
            obtained,
            frozen_threshold,
            rtol=0.0,
            atol=1e-12,
        ):
            raise ValueError(
                f"H{horizon}: threshold diferente "
                "do valor congelado. "
                f"Esperado: {frozen_threshold:.6f}; "
                f"obtido: {obtained:.6f}."
            )

        expected_prediction = (
            subset["score"].to_numpy(
                dtype=np.float64,
                copy=False,
            )
            >= frozen_threshold
        )

        stored_prediction = subset["predicao"].astype("boolean").astype(bool).to_numpy()

        if not np.array_equal(
            expected_prediction,
            stored_prediction,
        ):
            raise ValueError(
                f"H{horizon}: as classes previstas "
                "não reproduzem o threshold congelado."
            )


def load_population_support() -> pd.DataFrame:
    """Carrega população de 2025 sem acessar os resultados do modelo."""
    support = pd.read_parquet(
        FINAL_TEST_INPUT,
        columns=[
            MUNICIPALITY_COLUMN,
            "data_inicio_semana",
            "populacao",
        ],
    )

    if len(support) != EXPECTED_FINAL_TEST_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas na base de suporte de 2025. "
            f"Esperado: {EXPECTED_FINAL_TEST_ROWS:,}; "
            f"obtido: {len(support):,}."
        )

    duplicates = int(
        support.duplicated(
            subset=[
                MUNICIPALITY_COLUMN,
                "data_inicio_semana",
            ]
        ).sum()
    )

    if duplicates:
        raise ValueError(
            f"A base de suporte populacional possui {duplicates:,} chaves duplicadas."
        )

    if support["populacao"].isna().any():
        raise ValueError("Existem populações ausentes em 2025.")

    population = support["populacao"].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    if not np.isfinite(population).all():
        raise ValueError("Existem populações não finitas.")

    if (population <= 0).any():
        raise ValueError("Existem populações menores ou iguais a zero.")

    return support


def load_historical_profile() -> pd.DataFrame:
    """Carrega o perfil histórico previamente congelado."""
    profile = pd.read_parquet(
        PROFILE_INPUT,
        columns=[
            MUNICIPALITY_COLUMN,
            PROFILE_COLUMN,
        ],
    )

    if len(profile) != EXPECTED_PROFILE_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de perfis históricos. "
            f"Esperado: {EXPECTED_PROFILE_MUNICIPALITIES:,}; "
            f"obtido: {len(profile):,}."
        )

    if profile[MUNICIPALITY_COLUMN].duplicated().any():
        raise ValueError("Existem municípios duplicados no perfil histórico.")

    labels = set(profile[PROFILE_COLUMN].unique())

    if labels != set(PROFILE_LABELS):
        raise ValueError(
            f"Quartis epidemiológicos inesperados. Obtido: {sorted(labels)}."
        )

    return profile


def add_region(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Deriva a macrorregião a partir do código territorial IBGE."""
    output = dataframe.copy()

    ibge_prefix = output[MUNICIPALITY_COLUMN].astype(str).str.zfill(7).str[:2]

    output["regiao"] = ibge_prefix.map(REGION_BY_IBGE_PREFIX)

    if output["regiao"].isna().any():
        missing_prefixes = sorted(set(ibge_prefix.loc[output["regiao"].isna()]))

        raise ValueError(
            "Prefixos IBGE sem macrorregião: " + ", ".join(missing_prefixes) + "."
        )

    return output


def classify_population(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Classifica o porte populacional conforme protocolo congelado."""
    output = dataframe.copy()

    output["porte_populacional"] = pd.cut(
        output["populacao"],
        bins=[
            -np.inf,
            20_000,
            50_000,
            100_000,
            500_000,
            np.inf,
        ],
        labels=POPULATION_LABELS,
        right=False,
        ordered=True,
    )

    if output["porte_populacional"].isna().any():
        raise ValueError("Não foi possível classificar todos os portes populacionais.")

    return output


def enrich_predictions(
    predictions: pd.DataFrame,
    population: pd.DataFrame,
    profile: pd.DataFrame,
) -> pd.DataFrame:
    """Adiciona somente os agrupadores previstos no protocolo."""
    enriched = predictions.merge(
        population,
        on=[
            MUNICIPALITY_COLUMN,
            "data_inicio_semana",
        ],
        how="left",
        validate="many_to_one",
    )

    if enriched["populacao"].isna().any():
        missing = int(enriched["populacao"].isna().sum())

        raise ValueError(f"Foram encontradas {missing:,} predições sem população.")

    enriched = enriched.merge(
        profile,
        on=MUNICIPALITY_COLUMN,
        how="left",
        validate="many_to_one",
    )

    if enriched[PROFILE_COLUMN].isna().any():
        missing_codes = int(
            enriched.loc[
                enriched[PROFILE_COLUMN].isna(),
                MUNICIPALITY_COLUMN,
            ].nunique()
        )

        raise ValueError(
            "Foram encontrados "
            f"{missing_codes:,} municípios elegíveis "
            "sem perfil epidemiológico histórico."
        )

    enriched = add_region(enriched)

    enriched = classify_population(enriched)

    return enriched


def evaluate_group(
    dataframe: pd.DataFrame,
) -> dict:
    """Calcula métricas descritivas de um grupo."""
    observations = len(dataframe)

    if observations == 0:
        raise ValueError("Não é possível avaliar um grupo vazio.")

    target = dataframe["target"].astype("boolean").astype("int8").to_numpy()

    scores = dataframe["score"].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    prediction = dataframe["predicao"].astype("boolean").astype(bool).to_numpy()

    positives = target == 1

    negatives = target == 0

    positive_count = int(positives.sum())

    negative_count = int(negatives.sum())

    true_positive = int((prediction & positives).sum())

    false_positive = int((prediction & negatives).sum())

    false_negative = int((~prediction & positives).sum())

    true_negative = int((~prediction & negatives).sum())

    alerts = true_positive + false_positive

    precision = true_positive / alerts if alerts else 0.0

    recall = true_positive / positive_count if positive_count else 0.0

    f1_denominator = precision + recall

    f1 = 2 * precision * recall / f1_denominator if f1_denominator else 0.0

    specificity = true_negative / negative_count if negative_count else None

    balanced_accuracy = (
        (recall + specificity) / 2
        if (positive_count and negative_count and specificity is not None)
        else None
    )

    average_precision = (
        float(
            average_precision_score(
                target,
                scores,
            )
        )
        if positive_count
        else None
    )

    roc_auc = (
        float(
            roc_auc_score(
                target,
                scores,
            )
        )
        if (positive_count and negative_count)
        else None
    )

    brier = float(
        brier_score_loss(
            target,
            scores,
        )
    )

    return {
        "observacoes": observations,
        "municipios": int(dataframe[MUNICIPALITY_COLUMN].nunique()),
        "positivos": positive_count,
        "negativos": negative_count,
        "prevalencia": (positive_count / observations),
        "average_precision": average_precision,
        "roc_auc": roc_auc,
        "brier_score": brier,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "balanced_accuracy": (
            float(balanced_accuracy) if balanced_accuracy is not None else None
        ),
        "alertas": alerts,
        "proporcao_alertas": (alerts / observations),
        "tn": true_negative,
        "fp": false_positive,
        "fn": false_negative,
        "tp": true_positive,
    }


def analyse_dimension(
    dataframe: pd.DataFrame,
    *,
    dimension: str,
) -> pd.DataFrame:
    """Calcula métricas geral e early warning por agrupamento."""
    records = []

    groups = list(dataframe[dimension].dropna().unique())

    groups = sorted(
        groups,
        key=str,
    )

    for horizon in EXPECTED_HORIZONS:
        horizon_data = dataframe.loc[dataframe["horizonte"].eq(horizon)]

        threshold = FROZEN_THRESHOLDS[horizon]

        for group in groups:
            group_data = horizon_data.loc[horizon_data[dimension].eq(group)]

            if group_data.empty:
                continue

            general = evaluate_group(group_data)

            records.append(
                {
                    "dimensao": dimension,
                    "grupo": str(group),
                    "horizonte": horizon,
                    "subconjunto": "geral",
                    "threshold": threshold,
                    **general,
                }
            )

            current_risk = group_data[CURRENT_RISK_COLUMN].astype("boolean")

            if current_risk.isna().any():
                raise ValueError(
                    f"{dimension}={group}: existem estados atuais de risco ausentes."
                )

            early_data = group_data.loc[~current_risk.astype(bool)]

            if early_data.empty:
                continue

            early = evaluate_group(early_data)

            records.append(
                {
                    "dimensao": dimension,
                    "grupo": str(group),
                    "horizonte": horizon,
                    "subconjunto": "early_warning",
                    "threshold": threshold,
                    **early,
                }
            )

    return pd.DataFrame(records)


def validate_result(
    result: pd.DataFrame,
    *,
    dimension: str,
) -> None:
    """Valida o resultado tabular de uma dimensão."""
    if result.empty:
        raise ValueError(f"A dimensão {dimension} não gerou resultados.")

    if set(result["horizonte"].unique()) != set(EXPECTED_HORIZONS):
        raise ValueError(f"A dimensão {dimension} não contém H1–H4.")

    subsets = set(result["subconjunto"].unique())

    if subsets != {
        "geral",
        "early_warning",
    }:
        raise ValueError(
            f"A dimensão {dimension} não contém as duas perspectivas previstas."
        )

    if (result["observacoes"] <= 0).any():
        raise ValueError(f"A dimensão {dimension} possui resultado sem observações.")

    if (result["municipios"] <= 0).any():
        raise ValueError(f"A dimensão {dimension} possui resultado sem municípios.")


def main() -> None:
    """Executa a análise pós-teste de heterogeneidade."""
    print("=" * 104)
    print("ANÁLISE PÓS-TESTE DE HETEROGENEIDADE — 2025")
    print("=" * 104)

    print()
    print("Carregando predições finais congeladas...")

    predictions = pd.read_parquet(PREDICTIONS_INPUT)

    validate_predictions(predictions)

    print(f"Predições finais                 : {len(predictions):,}")

    print(
        "Municípios elegíveis             : "
        f"{predictions[MUNICIPALITY_COLUMN].nunique():,}"
    )

    print("Horizontes                       : H1, H2, H3, H4")

    print("Scores                           : NÃO recalculados")

    print("Thresholds                       : congelados")

    print("Treinamento                      : NÃO realizado")

    population = load_population_support()

    profile = load_historical_profile()

    print()
    print("Enriquecendo predições com agrupadores...")

    enriched = enrich_predictions(
        predictions,
        population,
        profile,
    )

    dimensions = {
        "regiao": (REGION_OUTPUT),
        "nome_uf_ibge": (UF_OUTPUT),
        "porte_populacional": (POPULATION_OUTPUT),
        PROFILE_COLUMN: (PROFILE_OUTPUT),
    }

    audit_dimensions = {}

    for dimension, output_path in dimensions.items():
        print()
        print("-" * 104)
        print(f"DIMENSÃO: {dimension}")
        print("-" * 104)

        result = analyse_dimension(
            enriched,
            dimension=dimension,
        )

        validate_result(
            result,
            dimension=dimension,
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        result.to_csv(
            output_path,
            index=False,
            encoding="utf-8",
        )

        groups = sorted(result["grupo"].unique())

        audit_dimensions[dimension] = {
            "grupos": list(groups),
            "quantidade_grupos": len(groups),
            "linhas_resultado": len(result),
            "arquivo": str(output_path),
        }

        print(f"Grupos                           : {len(groups)}")

        print(f"Linhas de resultado              : {len(result):,}")

        print(f"Arquivo                          : {output_path}")

    report = {
        "status": "APROVADO",
        "natureza": "análise secundária, descritiva e pós-teste",
        "predicoes": {
            "arquivo": str(PREDICTIONS_INPUT),
            "linhas": len(predictions),
            "municipios": int(predictions[MUNICIPALITY_COLUMN].nunique()),
            "scores_recalculados": False,
            "modelos_retreinados": False,
            "thresholds_alterados": False,
        },
        "agrupadores": {
            "regiao": "macrorregião oficial derivada do código IBGE",
            "uf": "UF presente na predição final",
            "porte_populacional": (
                "<20 mil; 20-49,9 mil; 50-99,9 mil; 100-499,9 mil; >=500 mil"
            ),
            "perfil_epidemiologico": (
                "quartis nacionais da incidência semanal média municipal de 2018-2024"
            ),
        },
        "dimensoes": audit_dimensions,
        "observacao": (
            "Os resultados desta análise não alteram "
            "a avaliação final independente de 2025."
        ),
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
    print("=" * 104)
    print("RESULTADO")
    print("=" * 104)

    print(f"Predições analisadas              : {len(predictions):,}")

    print("Modelos retreinados               : NÃO")

    print("Scores recalculados               : NÃO")

    print("Thresholds alterados              : NÃO")

    print(f"Auditoria JSON                    : {AUDIT_OUTPUT}")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
