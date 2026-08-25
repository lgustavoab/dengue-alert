"""Gera contratos globais do serving preditivo retrospectivo."""

import json
from math import isclose
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PREDICTIONS_FILE = (
    PROJECT_ROOT / "data" / "processed" / "predicoes_avaliacao_final_2025.parquet"
)

EVALUATION_JSON = PROJECT_ROOT / "reports" / "audits" / "avaliacao_final_2025.json"

EVALUATION_CSV = PROJECT_ROOT / "reports" / "audits" / "avaliacao_final_2025.csv"

OUTPUT_ROOT = PROJECT_ROOT / "data" / "serving" / "prediction"

MODEL_METADATA_FILE = OUTPUT_ROOT / "metadata" / "model.json"

EVALUATION_OVERVIEW_FILE = OUTPUT_ROOT / "evaluation" / "overview.json"

EVALUATION_BY_HORIZON_FILE = OUTPUT_ROOT / "evaluation" / "by_horizon.json"

MUNICIPALITY_INDEX_FILE = OUTPUT_ROOT / "municipality" / "index.json"

SCHEMA_VERSION = "1.0"

PREDICTION_COLUMNS = [
    "codigo_ibge_7",
    "nome_municipio_ibge",
    "nome_uf_ibge",
    "ano_epidemiologico",
    "semana_epidemiologica",
    "data_inicio_semana",
    "risco_elevado",
    "target",
    "horizonte",
    "score",
    "threshold",
    "predicao",
]

EXPECTED_ROWS = 1_124_938
EXPECTED_MUNICIPALITIES = 5_569
EXPECTED_YEAR = 2025
EXPECTED_ROWS_PER_MUNICIPALITY = 202

EXPECTED_HORIZONS = [
    1,
    2,
    3,
    4,
]

EXPECTED_ROWS_BY_HORIZON = {
    1: 289_588,
    2: 284_019,
    3: 278_450,
    4: 272_881,
}

EXPECTED_WEEKS_BY_HORIZON = {
    1: 52,
    2: 51,
    3: 50,
    4: 49,
}

EXPECTED_ROWS_PER_MUNICIPALITY_BY_HORIZON = {
    1: 52,
    2: 51,
    3: 50,
    4: 49,
}

EXPECTED_THRESHOLDS = {
    1: 0.187687,
    2: 0.190783,
    3: 0.167991,
    4: 0.157138,
}

EXPECTED_MODEL = "HistGradientBoostingClassifier"
EXPECTED_FEATURES = "Modelo A — 23 epidemiológicas"
EXPECTED_CALIBRATION = "não adotada"
EXPECTED_PROBABILITIES = "raw"
EXPECTED_DEVELOPMENT = "2018-2024"
EXPECTED_FINAL_TEST = "2025"


def load_predictions() -> pd.DataFrame:
    """Carrega o artefato final de predições."""
    if not PREDICTIONS_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {PREDICTIONS_FILE}")

    dataframe = pd.read_parquet(
        PREDICTIONS_FILE,
        columns=PREDICTION_COLUMNS,
    )

    dataframe["codigo_ibge_7"] = (
        dataframe["codigo_ibge_7"].astype("string").str.strip().str.zfill(7)
    )

    dataframe["data_inicio_semana"] = pd.to_datetime(
        dataframe["data_inicio_semana"],
        errors="raise",
    )

    return dataframe


def load_evaluation_json() -> dict[str, Any]:
    """Carrega a auditoria estruturada da avaliação final."""
    if not EVALUATION_JSON.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {EVALUATION_JSON}")

    return json.loads(EVALUATION_JSON.read_text(encoding="utf-8"))


def load_evaluation_csv() -> pd.DataFrame:
    """Carrega métricas tabulares da avaliação final."""
    if not EVALUATION_CSV.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {EVALUATION_CSV}")

    return pd.read_csv(EVALUATION_CSV)


def validate_predictions(
    dataframe: pd.DataFrame,
) -> None:
    """Valida invariantes do artefato final de predições."""
    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            "Quantidade inesperada de predições. "
            f"Esperado: {EXPECTED_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    municipalities = int(dataframe["codigo_ibge_7"].nunique())

    if municipalities != EXPECTED_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de municípios. "
            f"Esperado: {EXPECTED_MUNICIPALITIES:,}; "
            f"obtido: {municipalities:,}."
        )

    if dataframe.isna().any().any():
        missing = dataframe.isna().sum()
        missing = missing[missing > 0]

        raise ValueError(
            "Foram encontrados valores ausentes: "
            + ", ".join(f"{column}={int(count)}" for column, count in missing.items())
        )

    invalid_codes = ~dataframe["codigo_ibge_7"].str.fullmatch(r"\d{7}")

    if invalid_codes.any():
        raise ValueError("Foram encontrados códigos IBGE inválidos.")

    years = set(dataframe["ano_epidemiologico"].astype(int).unique().tolist())

    if years != {EXPECTED_YEAR}:
        raise ValueError(f"Ano epidemiológico inesperado: {sorted(years)}")

    horizons = set(dataframe["horizonte"].astype(int).unique().tolist())

    if horizons != set(EXPECTED_HORIZONS):
        raise ValueError(f"Conjunto inesperado de horizontes: {sorted(horizons)}")

    duplicate_count = int(
        dataframe.duplicated(
            subset=[
                "codigo_ibge_7",
                "ano_epidemiologico",
                "semana_epidemiologica",
                "horizonte",
            ]
        ).sum()
    )

    if duplicate_count:
        raise ValueError(
            f"Foram encontradas chaves preditivas duplicadas: {duplicate_count:,}."
        )

    invalid_score = (dataframe["score"] < 0) | (dataframe["score"] > 1)

    if invalid_score.any():
        raise ValueError("Foram encontrados scores fora do intervalo [0, 1].")

    calculated_prediction = dataframe["score"] >= dataframe["threshold"]

    divergent_predictions = int(
        (dataframe["predicao"].astype(bool) != calculated_prediction).sum()
    )

    if divergent_predictions:
        raise ValueError(
            "Foram encontradas predições divergentes da regra "
            "score >= threshold: "
            f"{divergent_predictions:,}."
        )


def validate_horizons(
    dataframe: pd.DataFrame,
) -> None:
    """Valida cobertura temporal e thresholds por horizonte."""
    for horizon in EXPECTED_HORIZONS:
        subset = dataframe[dataframe["horizonte"] == horizon]

        expected_rows = EXPECTED_ROWS_BY_HORIZON[horizon]

        if len(subset) != expected_rows:
            raise ValueError(
                f"H{horizon}: quantidade de linhas inesperada. "
                f"Esperado: {expected_rows:,}; "
                f"obtido: {len(subset):,}."
            )

        municipalities = int(subset["codigo_ibge_7"].nunique())

        if municipalities != EXPECTED_MUNICIPALITIES:
            raise ValueError(f"H{horizon}: quantidade de municípios divergente.")

        weeks = int(subset["semana_epidemiologica"].nunique())

        expected_weeks = EXPECTED_WEEKS_BY_HORIZON[horizon]

        if weeks != expected_weeks:
            raise ValueError(
                f"H{horizon}: quantidade de semanas inesperada. "
                f"Esperado: {expected_weeks}; "
                f"obtido: {weeks}."
            )

        thresholds = subset["threshold"].drop_duplicates().tolist()

        if len(thresholds) != 1:
            raise ValueError(f"H{horizon}: mais de um threshold encontrado.")

        threshold = float(thresholds[0])

        expected_threshold = EXPECTED_THRESHOLDS[horizon]

        if not isclose(
            threshold,
            expected_threshold,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(
                f"H{horizon}: threshold divergente. "
                f"Esperado: {expected_threshold}; "
                f"obtido: {threshold}."
            )


def validate_municipality_distribution(
    dataframe: pd.DataFrame,
) -> None:
    """Valida distribuição das predições por município."""
    total_counts = (
        dataframe.groupby(
            "codigo_ibge_7",
            sort=True,
        )
        .size()
        .astype(int)
    )

    invalid_total = total_counts[total_counts != EXPECTED_ROWS_PER_MUNICIPALITY]

    if not invalid_total.empty:
        raise ValueError(
            "Foram encontrados municípios com quantidade inesperada de predições."
        )

    by_horizon = (
        dataframe.groupby(
            [
                "codigo_ibge_7",
                "horizonte",
            ],
            sort=True,
        )
        .size()
        .astype(int)
    )

    for horizon, expected_count in EXPECTED_ROWS_PER_MUNICIPALITY_BY_HORIZON.items():
        counts = by_horizon.xs(
            horizon,
            level="horizonte",
        )

        invalid = counts[counts != expected_count]

        if not invalid.empty:
            raise ValueError(
                f"H{horizon}: municípios com quantidade inesperada de observações."
            )


def validate_evaluation_audit(
    audit: dict[str, Any],
) -> None:
    """Valida metadados congelados da avaliação final."""
    model = audit.get(
        "modelo_final",
        {},
    )

    protocol = audit.get(
        "protocolo",
        {},
    )

    predictions = audit.get(
        "predicoes",
        {},
    )

    if model.get("algoritmo") != EXPECTED_MODEL:
        raise ValueError("Algoritmo final divergente da configuração congelada.")

    if model.get("features") != EXPECTED_FEATURES:
        raise ValueError("Conjunto de features divergente da configuração congelada.")

    if model.get("calibracao") != EXPECTED_CALIBRATION:
        raise ValueError("Configuração de calibração divergente.")

    if model.get("probabilidades") != EXPECTED_PROBABILITIES:
        raise ValueError("Tipo de probabilidade divergente.")

    thresholds = model.get(
        "thresholds",
        {},
    )

    for horizon, expected in EXPECTED_THRESHOLDS.items():
        key = f"h{horizon}"

        if key not in thresholds:
            raise ValueError(f"Threshold ausente na auditoria: {key}.")

        if not isclose(
            float(thresholds[key]),
            expected,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(f"Threshold divergente na auditoria para {key}.")

    if protocol.get("desenvolvimento") != EXPECTED_DEVELOPMENT:
        raise ValueError("Período de desenvolvimento divergente.")

    if protocol.get("teste_final") != EXPECTED_FINAL_TEST:
        raise ValueError("Período de teste final divergente.")

    if protocol.get("thresholds_congelados") is not True:
        raise ValueError("A auditoria não confirma thresholds congelados.")

    if protocol.get("teste_final_utilizado_na_selecao") is not False:
        raise ValueError(
            "A auditoria indica uso indevido do teste final na seleção do modelo."
        )

    if (
        int(
            predictions.get(
                "linhas",
                -1,
            )
        )
        != EXPECTED_ROWS
    ):
        raise ValueError("Quantidade de linhas divergente na auditoria final.")

    if (
        int(
            predictions.get(
                "duplicadas",
                -1,
            )
        )
        != 0
    ):
        raise ValueError("A auditoria final registra predições duplicadas.")


def nullable_int(
    value: Any,
) -> int | None:
    """Converte número opcional para int JSON."""
    if pd.isna(value):
        return None

    return int(value)


def nullable_float(
    value: Any,
) -> float | None:
    """Converte número opcional para float JSON."""
    if pd.isna(value):
        return None

    return float(value)


def build_metric_block(
    row: pd.Series,
    prefix: str,
) -> dict[str, Any]:
    """Converte métricas prefixadas para contrato JSON."""
    return {
        "observacoes": nullable_int(row[f"{prefix}_observacoes"]),
        "positivos": nullable_int(row[f"{prefix}_positivos"]),
        "negativos": nullable_int(row[f"{prefix}_negativos"]),
        "prevalencia": nullable_float(row[f"{prefix}_prevalencia"]),
        "pr_auc_average_precision": nullable_float(
            row[f"{prefix}_pr_auc_average_precision"]
        ),
        "roc_auc": nullable_float(row[f"{prefix}_roc_auc"]),
        "recall": nullable_float(row[f"{prefix}_recall"]),
        "precision": nullable_float(row[f"{prefix}_precision"]),
        "f1": nullable_float(row[f"{prefix}_f1"]),
        "balanced_accuracy": nullable_float(row[f"{prefix}_balanced_accuracy"]),
        "brier_score": nullable_float(row[f"{prefix}_brier_score"]),
        "matriz_confusao": {
            "tn": nullable_int(row[f"{prefix}_matriz_confusao_tn"]),
            "fp": nullable_int(row[f"{prefix}_matriz_confusao_fp"]),
            "fn": nullable_int(row[f"{prefix}_matriz_confusao_fn"]),
            "tp": nullable_int(row[f"{prefix}_matriz_confusao_tp"]),
        },
    }


def build_model_metadata(
    audit: dict[str, Any],
) -> dict[str, Any]:
    """Cria metadata global do modelo final."""
    model = audit["modelo_final"]
    protocol = audit["protocolo"]

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "APROVADO",
        "tipo": "modelo_preditivo_retrospectivo",
        "ano_referencia": EXPECTED_YEAR,
        "retrospectivo": True,
        "modelo": {
            "algoritmo": model["algoritmo"],
            "features": model["features"],
            "calibracao": model["calibracao"],
            "probabilidades": model["probabilidades"],
        },
        "protocolo": {
            "desenvolvimento": protocol["desenvolvimento"],
            "teste_final": protocol["teste_final"],
            "thresholds_congelados": protocol["thresholds_congelados"],
            "teste_final_utilizado_na_selecao": protocol[
                "teste_final_utilizado_na_selecao"
            ],
        },
        "horizontes": [
            {
                "horizonte": horizon,
                "semanas_a_frente": horizon,
                "threshold": EXPECTED_THRESHOLDS[horizon],
            }
            for horizon in EXPECTED_HORIZONS
        ],
        "semantica": {
            "score": (
                "probabilidade bruta produzida pelo modelo "
                "para estado futuro de risco elevado"
            ),
            "predicao": "score >= threshold",
            "risco_elevado": ("estado observado de risco elevado na semana de origem"),
            "target": ("estado futuro observado utilizado na avaliação retrospectiva"),
            "early_warning": ("risco_elevado == false AND predicao == true"),
        },
        "restricoes_interpretacao": [
            ("score não representa número previsto de casos de dengue"),
            ("os resultados pertencem ao teste retrospectivo de 2025"),
            ("os resultados não representam alertas atuais de 2026"),
            ("não existem faixas metodológicas baixo/moderado/alto/crítico"),
        ],
    }


def build_evaluation_overview(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """Cria visão geral da avaliação retrospectiva."""
    horizons = {}

    for horizon in EXPECTED_HORIZONS:
        subset = dataframe[dataframe["horizonte"] == horizon].sort_values(
            [
                "codigo_ibge_7",
                "data_inicio_semana",
            ],
            kind="stable",
        )

        eligible = ~subset["risco_elevado"].astype(bool)

        early_warning = eligible & subset["predicao"].astype(bool)

        horizons[f"h{horizon}"] = {
            "linhas": len(subset),
            "municipios": int(subset["codigo_ibge_7"].nunique()),
            "semanas_origem": int(subset["semana_epidemiologica"].nunique()),
            "data_inicio_min": (subset["data_inicio_semana"].min().date().isoformat()),
            "data_inicio_max": (subset["data_inicio_semana"].max().date().isoformat()),
            "threshold": EXPECTED_THRESHOLDS[horizon],
            "target_positivos": int(subset["target"].astype(bool).sum()),
            "predicoes_positivas": int(subset["predicao"].astype(bool).sum()),
            "early_warning_elegiveis": int(eligible.sum()),
            "early_warning_alertas": int(early_warning.sum()),
            "score_min": float(subset["score"].min()),
            "score_max": float(subset["score"].max()),
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "APROVADO",
        "avaliacao": "teste_final_retrospectivo_2025",
        "ano": EXPECTED_YEAR,
        "linhas": len(dataframe),
        "municipios": int(dataframe["codigo_ibge_7"].nunique()),
        "horizontes": horizons,
    }


def build_evaluation_by_horizon(
    evaluation: pd.DataFrame,
) -> dict[str, Any]:
    """Estrutura métricas finais do modelo e baseline."""
    required_models = {
        "hist_gradient_boosting",
        "persistence",
    }

    models = set(evaluation["modelo"].astype(str).unique().tolist())

    if models != required_models:
        raise ValueError(
            f"Conjunto inesperado de modelos na avaliação: {sorted(models)}"
        )

    horizons = {}

    for horizon in EXPECTED_HORIZONS:
        subset = evaluation[evaluation["horizonte"] == horizon]

        model_rows = subset[subset["modelo"] == "hist_gradient_boosting"]

        persistence_rows = subset[subset["modelo"] == "persistence"]

        if len(model_rows) != 1:
            raise ValueError(f"H{horizon}: linha do modelo final ausente ou duplicada.")

        if len(persistence_rows) != 1:
            raise ValueError(f"H{horizon}: linha do baseline ausente ou duplicada.")

        model_row = model_rows.iloc[0]
        persistence_row = persistence_rows.iloc[0]

        model_threshold = float(model_row["threshold"])

        if not isclose(
            model_threshold,
            EXPECTED_THRESHOLDS[horizon],
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(f"H{horizon}: threshold da avaliação divergente.")

        model_early_warning = build_metric_block(
            model_row,
            "early_warning",
        )

        model_early_warning["alertas"] = nullable_int(
            model_row["early_warning_alertas"]
        )

        model_early_warning["proporcao_alertas"] = nullable_float(
            model_row["early_warning_proporcao_alertas"]
        )

        persistence_early_warning = build_metric_block(
            persistence_row,
            "early_warning",
        )

        persistence_early_warning["alertas"] = nullable_int(
            persistence_row["early_warning_alertas"]
        )

        persistence_early_warning["proporcao_alertas"] = nullable_float(
            persistence_row["early_warning_proporcao_alertas"]
        )

        horizons[f"h{horizon}"] = {
            "horizonte": horizon,
            "threshold_modelo": model_threshold,
            "modelo_final": {
                "nome": "hist_gradient_boosting",
                "linhas_treino": nullable_int(model_row["linhas_treino"]),
                "linhas_teste": nullable_int(model_row["linhas_teste"]),
                "geral": build_metric_block(
                    model_row,
                    "geral",
                ),
                "early_warning": model_early_warning,
            },
            "baseline_persistencia": {
                "nome": "persistence",
                "threshold": nullable_float(persistence_row["threshold"]),
                "linhas_teste": nullable_int(persistence_row["linhas_teste"]),
                "geral": build_metric_block(
                    persistence_row,
                    "geral",
                ),
                "early_warning": persistence_early_warning,
            },
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "APROVADO",
        "avaliacao": "teste_final_retrospectivo_2025",
        "horizontes": horizons,
    }


def build_municipality_index(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """Cria índice dos municípios com predições retrospectivas."""
    items = []

    grouped = dataframe.groupby(
        "codigo_ibge_7",
        sort=True,
    )

    for code, group in grouped:
        municipality_names = (
            group["nome_municipio_ibge"].astype(str).drop_duplicates().tolist()
        )

        state_names = group["nome_uf_ibge"].astype(str).drop_duplicates().tolist()

        if len(municipality_names) != 1:
            raise ValueError(f"{code}: mais de um nome municipal encontrado.")

        if len(state_names) != 1:
            raise ValueError(f"{code}: mais de uma UF encontrada.")

        horizon_counts = group.groupby("horizonte").size().astype(int).to_dict()

        item = {
            "codigo_ibge_7": str(code),
            "nome_municipio_ibge": municipality_names[0],
            "nome_uf_ibge": state_names[0],
            "predicoes": len(group),
            "horizontes": {
                f"h{horizon}": int(
                    horizon_counts.get(
                        horizon,
                        0,
                    )
                )
                for horizon in EXPECTED_HORIZONS
            },
        }

        items.append(item)

    if len(items) != EXPECTED_MUNICIPALITIES:
        raise ValueError("Quantidade inesperada de itens no índice municipal.")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "APROVADO",
        "count": len(items),
        "items": items,
    }


def validate_cross_contracts(
    overview: dict[str, Any],
    evaluation_by_horizon: dict[str, Any],
    municipality_index: dict[str, Any],
) -> None:
    """Valida consistência entre contratos gerados."""
    if overview["linhas"] != EXPECTED_ROWS:
        raise ValueError("Overview possui quantidade de linhas divergente.")

    if overview["municipios"] != EXPECTED_MUNICIPALITIES:
        raise ValueError("Overview possui quantidade de municípios divergente.")

    if municipality_index["count"] != EXPECTED_MUNICIPALITIES:
        raise ValueError("Índice possui quantidade de municípios divergente.")

    total_index_predictions = sum(
        int(item["predicoes"]) for item in municipality_index["items"]
    )

    if total_index_predictions != EXPECTED_ROWS:
        raise ValueError("Total de predições do índice não fecha com o artefato final.")

    for horizon in EXPECTED_HORIZONS:
        key = f"h{horizon}"

        overview_horizon = overview["horizontes"][key]

        evaluation_horizon = evaluation_by_horizon["horizontes"][key]

        general = evaluation_horizon["modelo_final"]["geral"]

        early_warning = evaluation_horizon["modelo_final"]["early_warning"]

        if overview_horizon["linhas"] != general["observacoes"]:
            raise ValueError(f"{key}: linhas divergentes entre overview e avaliação.")

        if overview_horizon["target_positivos"] != general["positivos"]:
            raise ValueError(
                f"{key}: positivos divergentes entre overview e avaliação."
            )

        if overview_horizon["early_warning_elegiveis"] != early_warning["observacoes"]:
            raise ValueError(f"{key}: elegibilidade early warning divergente.")

        if overview_horizon["early_warning_alertas"] != early_warning["alertas"]:
            raise ValueError(f"{key}: quantidade de alertas early warning divergente.")

        if not isclose(
            float(evaluation_horizon["threshold_modelo"]),
            EXPECTED_THRESHOLDS[horizon],
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(f"{key}: threshold divergente no contrato de avaliação.")


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    """Escreve JSON determinístico e compatível com frontend."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def generate_contracts(
    dataframe: pd.DataFrame,
    audit: dict[str, Any],
    evaluation: pd.DataFrame,
) -> dict[str, Any]:
    """Gera e grava todos os contratos globais preditivos."""
    model_metadata = build_model_metadata(audit)

    evaluation_overview = build_evaluation_overview(dataframe)

    evaluation_by_horizon = build_evaluation_by_horizon(evaluation)

    municipality_index = build_municipality_index(dataframe)

    validate_cross_contracts(
        evaluation_overview,
        evaluation_by_horizon,
        municipality_index,
    )

    outputs = {
        MODEL_METADATA_FILE: model_metadata,
        EVALUATION_OVERVIEW_FILE: evaluation_overview,
        EVALUATION_BY_HORIZON_FILE: evaluation_by_horizon,
        MUNICIPALITY_INDEX_FILE: municipality_index,
    }

    for path, payload in outputs.items():
        write_json(
            path,
            payload,
        )

    return {
        "files": len(outputs),
        "municipalities": municipality_index["count"],
        "predictions": evaluation_overview["linhas"],
        "paths": [path for path in outputs],
    }


def print_summary(
    result: dict[str, Any],
) -> None:
    """Exibe resumo da geração."""
    print("=" * 108)

    print("SERVING — CONTRATOS GLOBAIS DE PREDIÇÃO")

    print("=" * 108)

    print()

    print(f"Arquivos gerados : {result['files']}")

    print(f"Municípios       : {result['municipalities']:,}")

    print(f"Predições        : {result['predictions']:,}")

    print()

    print("ARQUIVOS")

    for path in result["paths"]:
        print("  " + path.relative_to(PROJECT_ROOT).as_posix())

    print()

    print("STATUS: CONTRATOS GLOBAIS PREDITIVOS GERADOS E VALIDADOS")


def main() -> None:
    """Executa a geração dos contratos globais preditivos."""
    dataframe = load_predictions()

    audit = load_evaluation_json()

    evaluation = load_evaluation_csv()

    validate_predictions(dataframe)

    validate_horizons(dataframe)

    validate_municipality_distribution(dataframe)

    validate_evaluation_audit(audit)

    result = generate_contracts(
        dataframe,
        audit,
        evaluation,
    )

    print_summary(result)


if __name__ == "__main__":
    main()
