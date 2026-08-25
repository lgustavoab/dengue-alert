"""Compara formatos candidatos para o serving preditivo municipal."""

import gzip
import json
import tempfile
from math import isclose
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT / "data" / "processed" / "predicoes_avaliacao_final_2025.parquet"
)

OUTPUT_FILE = PROJECT_ROOT / "reports" / "audits" / "benchmark_serving_prediction.json"

SCHEMA_VERSION = "1.0"

COLUMNS = [
    "codigo_ibge_7",
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

EXPECTED_YEAR = 2025


def load_predictions() -> pd.DataFrame:
    """Carrega somente as colunas candidatas ao serving preditivo."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    dataframe = pd.read_parquet(
        INPUT_FILE,
        columns=COLUMNS,
    )

    dataframe["codigo_ibge_7"] = (
        dataframe["codigo_ibge_7"].astype("string").str.strip().str.zfill(7)
    )

    dataframe["data_inicio_semana"] = pd.to_datetime(
        dataframe["data_inicio_semana"],
        errors="raise",
    )

    return dataframe


def validate_predictions(
    dataframe: pd.DataFrame,
) -> None:
    """Valida as invariantes congeladas da avaliação final."""
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


def validate_horizon_structure(
    dataframe: pd.DataFrame,
) -> None:
    """Valida cobertura e thresholds por horizonte."""
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
) -> dict[str, int]:
    """Valida quantidade total e por horizonte para cada município."""
    rows_per_municipality = (
        dataframe.groupby(
            "codigo_ibge_7",
            sort=True,
        )
        .size()
        .astype(int)
    )

    invalid_total = rows_per_municipality[
        rows_per_municipality != EXPECTED_ROWS_PER_MUNICIPALITY
    ]

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

    for horizon, expected in EXPECTED_ROWS_PER_MUNICIPALITY_BY_HORIZON.items():
        horizon_counts = by_horizon.xs(
            horizon,
            level="horizonte",
        )

        invalid = horizon_counts[horizon_counts != expected]

        if not invalid.empty:
            raise ValueError(
                f"H{horizon}: municípios com quantidade inesperada de observações."
            )

    return {str(code): int(rows) for code, rows in rows_per_municipality.items()}


def normalize_value(
    value: Any,
) -> Any:
    """Converte valores Pandas para tipos JSON nativos."""
    if pd.isna(value):
        return None

    if isinstance(
        value,
        pd.Timestamp,
    ):
        return value.date().isoformat()

    if hasattr(
        value,
        "item",
    ):
        return value.item()

    return value


def build_verbose_payload(
    code: str,
    group: pd.DataFrame,
) -> dict[str, Any]:
    """Cria representação verbosa com um objeto por predição."""
    records = []

    for row in group.itertuples(index=False):
        records.append(
            {
                "ano_epidemiologico": int(row.ano_epidemiologico),
                "semana_epidemiologica": int(row.semana_epidemiologica),
                "data_inicio_semana": normalize_value(row.data_inicio_semana),
                "risco_elevado": bool(row.risco_elevado),
                "target": bool(row.target),
                "horizonte": int(row.horizonte),
                "score": float(row.score),
                "threshold": float(row.threshold),
                "predicao": bool(row.predicao),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "codigo_ibge_7": code,
        "count": len(records),
        "data": records,
    }


def build_compact_flat_payload(
    code: str,
    group: pd.DataFrame,
) -> dict[str, Any]:
    """Cria representação colunar compacta sem separação por horizonte."""
    return {
        "schema_version": SCHEMA_VERSION,
        "codigo_ibge_7": code,
        "count": len(group),
        "data": {
            "ano_epidemiologico": group["ano_epidemiologico"].astype(int).tolist(),
            "semana_epidemiologica": group["semana_epidemiologica"]
            .astype(int)
            .tolist(),
            "data_inicio_semana": [
                normalize_value(value) for value in group["data_inicio_semana"]
            ],
            "risco_elevado": group["risco_elevado"].astype(bool).tolist(),
            "target": group["target"].astype(bool).tolist(),
            "horizonte": group["horizonte"].astype(int).tolist(),
            "score": group["score"].astype(float).tolist(),
            "threshold": group["threshold"].astype(float).tolist(),
            "predicao": group["predicao"].astype(bool).tolist(),
        },
    }


def build_horizon_payload(
    horizon: int,
    group: pd.DataFrame,
) -> dict[str, Any]:
    """Cria bloco compacto para um único horizonte."""
    threshold = EXPECTED_THRESHOLDS[horizon]

    return {
        "count": len(group),
        "threshold": threshold,
        "data": {
            "ano_epidemiologico": group["ano_epidemiologico"].astype(int).tolist(),
            "semana_epidemiologica": group["semana_epidemiologica"]
            .astype(int)
            .tolist(),
            "data_inicio_semana": [
                normalize_value(value) for value in group["data_inicio_semana"]
            ],
            "risco_elevado": group["risco_elevado"].astype(bool).tolist(),
            "target": group["target"].astype(bool).tolist(),
            "score": group["score"].astype(float).tolist(),
            "predicao": group["predicao"].astype(bool).tolist(),
        },
    }


def build_compact_by_horizon_payload(
    code: str,
    group: pd.DataFrame,
) -> dict[str, Any]:
    """Cria representação compacta organizada por horizonte."""
    horizons = {}

    for horizon in EXPECTED_HORIZONS:
        horizon_group = group[group["horizonte"] == horizon]

        horizons[f"h{horizon}"] = build_horizon_payload(
            horizon,
            horizon_group,
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "codigo_ibge_7": code,
        "count": len(group),
        "horizontes": horizons,
    }


def serialize_json(
    payload: dict[str, Any],
) -> bytes:
    """Serializa JSON compacto em UTF-8."""
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(
            ",",
            ":",
        ),
    ).encode("utf-8")


def gzip_size(
    data: bytes,
) -> int:
    """Calcula tamanho gzip determinístico."""
    return len(
        gzip.compress(
            data,
            compresslevel=9,
            mtime=0,
        )
    )


def benchmark_json(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """Mede as três representações JSON por município."""
    verbose_sizes = []
    verbose_gzip_sizes = []

    flat_sizes = []
    flat_gzip_sizes = []

    horizon_sizes = []
    horizon_gzip_sizes = []

    rows_per_municipality = {}

    dataframe = dataframe.sort_values(
        [
            "codigo_ibge_7",
            "horizonte",
            "data_inicio_semana",
        ],
        kind="stable",
    ).reset_index(drop=True)

    for code, group in dataframe.groupby(
        "codigo_ibge_7",
        sort=True,
    ):
        code = str(code)

        rows_per_municipality[code] = len(group)

        verbose = serialize_json(
            build_verbose_payload(
                code,
                group,
            )
        )

        flat = serialize_json(
            build_compact_flat_payload(
                code,
                group,
            )
        )

        by_horizon = serialize_json(
            build_compact_by_horizon_payload(
                code,
                group,
            )
        )

        verbose_sizes.append(len(verbose))

        verbose_gzip_sizes.append(gzip_size(verbose))

        flat_sizes.append(len(flat))

        flat_gzip_sizes.append(gzip_size(flat))

        horizon_sizes.append(len(by_horizon))

        horizon_gzip_sizes.append(gzip_size(by_horizon))

    return {
        "verbose": {
            "total": sum(verbose_sizes),
            "total_gzip": sum(verbose_gzip_sizes),
            "min": min(verbose_sizes),
            "median": median(verbose_sizes),
            "max": max(verbose_sizes),
            "median_gzip": median(verbose_gzip_sizes),
            "max_gzip": max(verbose_gzip_sizes),
        },
        "compact_flat": {
            "total": sum(flat_sizes),
            "total_gzip": sum(flat_gzip_sizes),
            "min": min(flat_sizes),
            "median": median(flat_sizes),
            "max": max(flat_sizes),
            "median_gzip": median(flat_gzip_sizes),
            "max_gzip": max(flat_gzip_sizes),
        },
        "compact_by_horizon": {
            "total": sum(horizon_sizes),
            "total_gzip": sum(horizon_gzip_sizes),
            "min": min(horizon_sizes),
            "median": median(horizon_sizes),
            "max": max(horizon_sizes),
            "median_gzip": median(horizon_gzip_sizes),
            "max_gzip": max(horizon_gzip_sizes),
        },
        "rows_per_municipality": rows_per_municipality,
    }


def benchmark_parquet(
    dataframe: pd.DataFrame,
) -> int:
    """Mede Parquet nacional reduzido com compressão Zstandard."""
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "prediction_serving.parquet"

        dataframe.to_parquet(
            output,
            index=False,
            compression="zstd",
        )

        return output.stat().st_size


def format_bytes(
    value: float,
) -> str:
    """Formata quantidade de bytes para leitura humana."""
    value = float(value)

    if value < 1024:
        return f"{value:.0f} B"

    value /= 1024

    if value < 1024:
        return f"{value:.2f} KB"

    value /= 1024

    if value < 1024:
        return f"{value:.2f} MB"

    value /= 1024

    return f"{value:.2f} GB"


def write_benchmark_audit(
    dataframe: pd.DataFrame,
    json_results: dict[str, Any],
    parquet_size: int,
) -> None:
    """Registra o benchmark preditivo em formato estruturado."""
    verbose = json_results["verbose"]

    flat = json_results["compact_flat"]

    by_horizon = json_results["compact_by_horizon"]

    rows_per_municipality = json_results["rows_per_municipality"]

    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "APROVADO",
        "analise": "benchmark do serving preditivo municipal",
        "fonte": ("data/processed/predicoes_avaliacao_final_2025.parquet"),
        "painel": {
            "linhas": len(dataframe),
            "municipios": len(rows_per_municipality),
            "predicoes_por_municipio": EXPECTED_ROWS_PER_MUNICIPALITY,
            "horizontes": EXPECTED_HORIZONS,
            "colunas_avaliadas": COLUMNS,
        },
        "estrutura_por_horizonte": {
            f"h{horizon}": {
                "linhas": EXPECTED_ROWS_BY_HORIZON[horizon],
                "semanas": EXPECTED_WEEKS_BY_HORIZON[horizon],
                "threshold": EXPECTED_THRESHOLDS[horizon],
            }
            for horizon in EXPECTED_HORIZONS
        },
        "json_verboso_por_municipio": benchmark_metrics(verbose),
        "json_compacto_colunar": benchmark_metrics(flat),
        "json_compacto_por_horizonte": benchmark_metrics(by_horizon),
        "reducoes": {
            "compacto_colunar_vs_verboso": {
                "sem_compressao": float(1 - flat["total"] / verbose["total"]),
                "gzip": float(1 - flat["total_gzip"] / verbose["total_gzip"]),
            },
            "compacto_por_horizonte_vs_verboso": {
                "sem_compressao": float(1 - by_horizon["total"] / verbose["total"]),
                "gzip": float(1 - by_horizon["total_gzip"] / verbose["total_gzip"]),
            },
            "compacto_por_horizonte_vs_colunar": {
                "sem_compressao": float(1 - by_horizon["total"] / flat["total"]),
                "gzip": float(1 - by_horizon["total_gzip"] / flat["total_gzip"]),
            },
        },
        "parquet_nacional_reduzido": {
            "compression": "zstd",
            "size_bytes": int(parquet_size),
        },
        "decisao": {
            "formato_inicial": "json_compacto_por_horizonte",
            "granularidade": "um_arquivo_por_municipio",
            "arquivos_estimados": EXPECTED_MUNICIPALITIES,
            "estrutura_prevista": (
                "data/serving/prediction/municipality/series/{codigo_ibge_7}.json"
            ),
            "motivos": [
                (
                    "O contrato reflete diretamente os quatro "
                    "horizontes H1, H2, H3 e H4."
                ),
                (
                    "Horizonte e threshold não precisam ser "
                    "repetidos em cada observação."
                ),
                (
                    "O tamanho municipal permanece muito pequeno "
                    "mesmo com compressão de transporte."
                ),
                (
                    "A representação por horizonte é menor sem "
                    "compressão que o JSON compacto colunar."
                ),
                (
                    "A diferença de gzip frente ao compacto "
                    "colunar é pequena e não justifica perder "
                    "clareza semântica."
                ),
            ],
            "parquet_preservado_como_alternativa": True,
        },
        "invariantes": {
            "linhas_esperadas": EXPECTED_ROWS,
            "municipios_esperados": EXPECTED_MUNICIPALITIES,
            "predicoes_por_municipio": EXPECTED_ROWS_PER_MUNICIPALITY,
            "ano": EXPECTED_YEAR,
            "thresholds": {
                f"h{horizon}": EXPECTED_THRESHOLDS[horizon]
                for horizon in EXPECTED_HORIZONS
            },
            "regra_predicao": "score >= threshold",
            "scores_intervalo": "[0, 1]",
        },
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def benchmark_metrics(
    metrics: dict[str, Any],
) -> dict[str, Any]:
    """Padroniza métricas de tamanho para auditoria."""
    return {
        "total_bytes": int(metrics["total"]),
        "total_gzip_estimado_bytes": int(metrics["total_gzip"]),
        "arquivo_minimo_bytes": int(metrics["min"]),
        "arquivo_mediano_bytes": float(metrics["median"]),
        "arquivo_mediano_gzip_bytes": float(metrics["median_gzip"]),
        "maior_arquivo_bytes": int(metrics["max"]),
        "maior_arquivo_gzip_bytes": int(metrics["max_gzip"]),
    }


def print_representation(
    title: str,
    metrics: dict[str, Any],
) -> None:
    """Exibe métricas de uma representação JSON."""
    print(title)

    print(f"  Total sem compressão : {format_bytes(metrics['total'])}")

    print(f"  Total gzip estimado   : {format_bytes(metrics['total_gzip'])}")

    print(f"  Arquivo mediano       : {format_bytes(metrics['median'])}")

    print(f"  Arquivo mediano gzip  : {format_bytes(metrics['median_gzip'])}")

    print(f"  Maior arquivo         : {format_bytes(metrics['max'])}")

    print(f"  Maior arquivo gzip    : {format_bytes(metrics['max_gzip'])}")

    print()


def print_results(
    dataframe: pd.DataFrame,
    json_results: dict[str, Any],
    parquet_size: int,
) -> None:
    """Exibe benchmark consolidado."""
    verbose = json_results["verbose"]

    flat = json_results["compact_flat"]

    by_horizon = json_results["compact_by_horizon"]

    print("=" * 108)

    print("BENCHMARK — SERVING PREDITIVO MUNICIPAL")

    print("=" * 108)

    print()

    print(f"Predições              : {len(dataframe):,}")

    print(f"Municípios             : {dataframe['codigo_ibge_7'].nunique():,}")

    print(f"Predições por município: {EXPECTED_ROWS_PER_MUNICIPALITY}")

    print()

    print("COBERTURA POR HORIZONTE")

    for horizon in EXPECTED_HORIZONS:
        print(
            f"  H{horizon} : "
            f"{EXPECTED_ROWS_BY_HORIZON[horizon]:>7,} linhas | "
            f"{EXPECTED_WEEKS_BY_HORIZON[horizon]:>2} semanas | "
            f"threshold {EXPECTED_THRESHOLDS[horizon]:.6f}"
        )

    print()

    print_representation(
        "JSON VERBOSO — 1 arquivo por município",
        verbose,
    )

    print_representation(
        "JSON COMPACTO COLUNAR — 1 arquivo por município",
        flat,
    )

    print_representation(
        "JSON COMPACTO POR HORIZONTE — 1 arquivo por município",
        by_horizon,
    )

    print("REDUÇÕES")

    print(
        "  Colunar × verboso, sem compressão : "
        f"{1 - flat['total'] / verbose['total']:.2%}"
    )

    print(
        "  Colunar × verboso, gzip           : "
        f"{1 - flat['total_gzip'] / verbose['total_gzip']:.2%}"
    )

    print(
        "  Por horizonte × verboso           : "
        f"{1 - by_horizon['total'] / verbose['total']:.2%}"
    )

    print(
        "  Por horizonte × verboso, gzip     : "
        f"{1 - by_horizon['total_gzip'] / verbose['total_gzip']:.2%}"
    )

    print(
        "  Por horizonte × colunar           : "
        f"{1 - by_horizon['total'] / flat['total']:.2%}"
    )

    print(
        "  Por horizonte × colunar, gzip     : "
        f"{1 - by_horizon['total_gzip'] / flat['total_gzip']:.2%}"
    )

    print()

    print("PARQUET NACIONAL REDUZIDO")

    print(f"  10 colunas + Zstandard            : {format_bytes(parquet_size)}")

    print()

    print("Auditoria estruturada:")

    print("  " + OUTPUT_FILE.relative_to(PROJECT_ROOT).as_posix())

    print()

    print("STATUS: BENCHMARK PREDITIVO CONCLUÍDO")


def main() -> None:
    """Executa benchmark dos formatos de serving preditivo."""
    dataframe = load_predictions()

    validate_predictions(dataframe)

    validate_horizon_structure(dataframe)

    validate_municipality_distribution(dataframe)

    json_results = benchmark_json(dataframe)

    parquet_size = benchmark_parquet(dataframe)

    write_benchmark_audit(
        dataframe,
        json_results,
        parquet_size,
    )

    print_results(
        dataframe,
        json_results,
        parquet_size,
    )


if __name__ == "__main__":
    main()
