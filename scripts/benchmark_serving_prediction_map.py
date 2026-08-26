"""Compara formatos candidatos para o serving nacional do mapa preditivo."""

from __future__ import annotations

import gzip
import json
from math import isclose
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT / "data" / "processed" / "predicoes_avaliacao_final_2025.parquet"
)

OUTPUT_FILE = (
    PROJECT_ROOT / "reports" / "audits" / "benchmark_serving_prediction_map.json"
)

SCHEMA_VERSION = "1.0"

COLUMNS = [
    "codigo_ibge_7",
    "ano_epidemiologico",
    "semana_epidemiologica",
    "data_inicio_semana",
    "horizonte",
    "score",
    "threshold",
    "predicao",
]

EXPECTED_ROWS = 1_124_938
EXPECTED_MUNICIPALITIES = 5_569
EXPECTED_YEAR = 2025

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

EXPECTED_THRESHOLDS = {
    1: 0.187687,
    2: 0.190783,
    3: 0.167991,
    4: 0.157138,
}

EXPECTED_MAP_FILES = sum(EXPECTED_WEEKS_BY_HORIZON.values())

SAMPLE_KEYS = [
    (1, 20),
    (4, 20),
    (1, 49),
]


def load_predictions() -> pd.DataFrame:
    """Carrega somente os campos necessários ao benchmark."""
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
    """Valida invariantes congeladas da avaliação retrospectiva."""
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
            "Valores ausentes encontrados: "
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
        raise ValueError(f"Horizontes inesperados: {sorted(horizons)}")

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
        raise ValueError("Foram encontrados scores fora de [0, 1].")

    calculated_prediction = dataframe["score"] >= dataframe["threshold"]

    divergent = int((dataframe["predicao"].astype(bool) != calculated_prediction).sum())

    if divergent:
        raise ValueError(
            "Foram encontradas predições divergentes "
            "da regra score >= threshold: "
            f"{divergent:,}."
        )


def validate_horizons(
    dataframe: pd.DataFrame,
) -> None:
    """Valida cobertura temporal e threshold dos horizontes."""
    for horizon in EXPECTED_HORIZONS:
        subset = dataframe[dataframe["horizonte"] == horizon]

        expected_rows = EXPECTED_ROWS_BY_HORIZON[horizon]

        if len(subset) != expected_rows:
            raise ValueError(
                f"H{horizon}: linhas inesperadas. "
                f"Esperado: {expected_rows:,}; "
                f"obtido: {len(subset):,}."
            )

        municipalities = int(subset["codigo_ibge_7"].nunique())

        if municipalities != EXPECTED_MUNICIPALITIES:
            raise ValueError(f"H{horizon}: quantidade inesperada de municípios.")

        weeks = sorted(subset["semana_epidemiologica"].astype(int).unique().tolist())

        expected_week_count = EXPECTED_WEEKS_BY_HORIZON[horizon]

        expected_weeks = list(
            range(
                1,
                expected_week_count + 1,
            )
        )

        if weeks != expected_weeks:
            raise ValueError(f"H{horizon}: semanas inesperadas. Obtido: {weeks}")

        thresholds = subset["threshold"].astype(float).drop_duplicates().tolist()

        if len(thresholds) != 1:
            raise ValueError(f"H{horizon}: mais de um threshold.")

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


def serialize_json(
    payload: dict[str, Any],
) -> bytes:
    """Serializa JSON compacto e sem valores não finitos."""
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


def build_common_metadata(
    horizon: int,
    week: int,
    group: pd.DataFrame,
) -> dict[str, Any]:
    """Cria metadados comuns a todos os formatos candidatos."""
    if len(group) != EXPECTED_MUNICIPALITIES:
        raise ValueError(
            f"H{horizon} SE{week:02d}: "
            "quantidade inesperada de municípios. "
            f"Esperado: {EXPECTED_MUNICIPALITIES:,}; "
            f"obtido: {len(group):,}."
        )

    if group["codigo_ibge_7"].duplicated().any():
        raise ValueError(f"H{horizon} SE{week:02d}: códigos municipais duplicados.")

    dates = group["data_inicio_semana"].drop_duplicates().tolist()

    if len(dates) != 1:
        raise ValueError(
            f"H{horizon} SE{week:02d}: mais de uma data de início encontrada."
        )

    thresholds = group["threshold"].astype(float).drop_duplicates().tolist()

    if len(thresholds) != 1:
        raise ValueError(f"H{horizon} SE{week:02d}: mais de um threshold encontrado.")

    threshold = float(thresholds[0])

    expected_threshold = EXPECTED_THRESHOLDS[horizon]

    if not isclose(
        threshold,
        expected_threshold,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError(f"H{horizon} SE{week:02d}: threshold divergente.")

    return {
        "schema_version": SCHEMA_VERSION,
        "ano_epidemiologico": EXPECTED_YEAR,
        "semana_epidemiologica": week,
        "data_inicio_semana": (pd.Timestamp(dates[0]).date().isoformat()),
        "horizonte": horizon,
        "threshold": threshold,
        "count": len(group),
    }


def build_verbose_payload(
    horizon: int,
    week: int,
    group: pd.DataFrame,
) -> dict[str, Any]:
    """Cria formato verboso com um objeto por município."""
    payload = build_common_metadata(
        horizon,
        week,
        group,
    )

    records = []

    for row in group.itertuples(index=False):
        records.append(
            {
                "codigo_ibge_7": str(row.codigo_ibge_7),
                "score": float(row.score),
                "predicao": bool(row.predicao),
            }
        )

    payload["data"] = records

    return payload


def build_columnar_payload(
    horizon: int,
    week: int,
    group: pd.DataFrame,
) -> dict[str, Any]:
    """Cria formato compacto com arrays alinhados."""
    payload = build_common_metadata(
        horizon,
        week,
        group,
    )

    payload["data"] = {
        "codigo_ibge_7": (group["codigo_ibge_7"].astype(str).tolist()),
        "score": (group["score"].astype(float).tolist()),
        "predicao": (group["predicao"].astype(bool).tolist()),
    }

    return payload


def summarize_sizes(
    raw_sizes: list[int],
    gzip_sizes: list[int],
) -> dict[str, Any]:
    """Resume tamanhos de todos os arquivos de um formato."""
    return {
        "arquivos": len(raw_sizes),
        "total_bytes": sum(raw_sizes),
        "total_gzip_bytes": sum(gzip_sizes),
        "min_bytes": min(raw_sizes),
        "median_bytes": median(raw_sizes),
        "max_bytes": max(raw_sizes),
        "min_gzip_bytes": min(gzip_sizes),
        "median_gzip_bytes": median(gzip_sizes),
        "max_gzip_bytes": max(gzip_sizes),
    }


def format_kib(
    value: float,
) -> str:
    """Formata bytes como KiB."""
    return f"{value / 1024:.2f} KiB"


def format_mib(
    value: float,
) -> str:
    """Formata bytes como MiB."""
    return f"{value / 1024**2:.2f} MiB"


def benchmark(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """Executa o benchmark das duas representações candidatas."""
    dataframe = dataframe.sort_values(
        [
            "horizonte",
            "semana_epidemiologica",
            "codigo_ibge_7",
        ],
        kind="stable",
    ).reset_index(drop=True)

    verbose_raw_sizes = []
    verbose_gzip_sizes = []

    columnar_raw_sizes = []
    columnar_gzip_sizes = []

    samples: dict[str, Any] = {}

    processed_files = 0

    print()
    print(f"Iniciando serialização dos {EXPECTED_MAP_FILES} arquivos candidatos...")

    for horizon in EXPECTED_HORIZONS:
        horizon_subset = dataframe[dataframe["horizonte"] == horizon]

        weeks = sorted(
            horizon_subset["semana_epidemiologica"].astype(int).unique().tolist()
        )

        print()
        print(f"H{horizon}: {len(weeks)} semanas")

        for week in weeks:
            group = horizon_subset[
                horizon_subset["semana_epidemiologica"] == week
            ].copy()

            group = group.sort_values(
                "codigo_ibge_7",
                kind="stable",
            ).reset_index(drop=True)

            verbose_bytes = serialize_json(
                build_verbose_payload(
                    horizon,
                    week,
                    group,
                )
            )

            columnar_bytes = serialize_json(
                build_columnar_payload(
                    horizon,
                    week,
                    group,
                )
            )

            verbose_gzip = gzip_size(verbose_bytes)

            columnar_gzip = gzip_size(columnar_bytes)

            verbose_raw_sizes.append(len(verbose_bytes))

            verbose_gzip_sizes.append(verbose_gzip)

            columnar_raw_sizes.append(len(columnar_bytes))

            columnar_gzip_sizes.append(columnar_gzip)

            key = (
                horizon,
                week,
            )

            if key in SAMPLE_KEYS:
                sample_name = f"h{horizon}_se{week:02d}"

                samples[sample_name] = {
                    "horizonte": horizon,
                    "semana_epidemiologica": week,
                    "count": len(group),
                    "alertas": int(group["predicao"].astype(bool).sum()),
                    "score_min": float(group["score"].min()),
                    "score_median": float(group["score"].median()),
                    "score_max": float(group["score"].max()),
                    "verbose_bytes": len(verbose_bytes),
                    "verbose_gzip_bytes": (verbose_gzip),
                    "columnar_bytes": len(columnar_bytes),
                    "columnar_gzip_bytes": (columnar_gzip),
                }

            processed_files += 1

        print(f"  arquivos acumulados: {processed_files}")

    if processed_files != EXPECTED_MAP_FILES:
        raise ValueError(
            "Quantidade inesperada de arquivos lógicos. "
            f"Esperado: {EXPECTED_MAP_FILES}; "
            f"obtido: {processed_files}."
        )

    verbose_summary = summarize_sizes(
        verbose_raw_sizes,
        verbose_gzip_sizes,
    )

    columnar_summary = summarize_sizes(
        columnar_raw_sizes,
        columnar_gzip_sizes,
    )

    raw_reduction = (
        1 - (columnar_summary["total_bytes"] / verbose_summary["total_bytes"])
    ) * 100

    gzip_reduction = (
        1 - (columnar_summary["total_gzip_bytes"] / verbose_summary["total_gzip_bytes"])
    ) * 100

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "BENCHMARK",
        "fonte": str(INPUT_FILE.relative_to(PROJECT_ROOT)).replace(
            "\\",
            "/",
        ),
        "ano_epidemiologico": EXPECTED_YEAR,
        "linhas_fonte": len(dataframe),
        "municipios": int(dataframe["codigo_ibge_7"].nunique()),
        "arquivos_logicos": processed_files,
        "estrutura_temporal": {
            f"h{horizon}": {
                "semanas": (EXPECTED_WEEKS_BY_HORIZON[horizon]),
                "threshold": (EXPECTED_THRESHOLDS[horizon]),
            }
            for horizon in EXPECTED_HORIZONS
        },
        "formatos": {
            "verbose": verbose_summary,
            "columnar": columnar_summary,
        },
        "reducao_columnar_vs_verbose": {
            "raw_pct": raw_reduction,
            "gzip_pct": gzip_reduction,
        },
        "amostras": samples,
    }


def print_report(
    report: dict[str, Any],
) -> None:
    """Imprime o resumo do benchmark."""
    verbose = report["formatos"]["verbose"]

    columnar = report["formatos"]["columnar"]

    reduction = report["reducao_columnar_vs_verbose"]

    print()
    print("=" * 108)
    print("BENCHMARK DO SERVING NACIONAL DO MAPA PREDITIVO")
    print("=" * 108)

    print(f"Linhas da avaliação       : {report['linhas_fonte']:,}")
    print(f"Municípios                : {report['municipios']:,}")
    print(f"Arquivos lógicos          : {report['arquivos_logicos']:,}")

    print()
    print("FORMATO VERBOSO")
    print(f"  total bruto             : {format_mib(verbose['total_bytes'])}")
    print(f"  total gzip              : {format_mib(verbose['total_gzip_bytes'])}")
    print(f"  arquivo mediano bruto   : {format_kib(verbose['median_bytes'])}")
    print(f"  arquivo mediano gzip    : {format_kib(verbose['median_gzip_bytes'])}")
    print(f"  maior arquivo gzip      : {format_kib(verbose['max_gzip_bytes'])}")

    print()
    print("FORMATO COLUNAR")
    print(f"  total bruto             : {format_mib(columnar['total_bytes'])}")
    print(f"  total gzip              : {format_mib(columnar['total_gzip_bytes'])}")
    print(f"  arquivo mediano bruto   : {format_kib(columnar['median_bytes'])}")
    print(f"  arquivo mediano gzip    : {format_kib(columnar['median_gzip_bytes'])}")
    print(f"  maior arquivo gzip      : {format_kib(columnar['max_gzip_bytes'])}")

    print()
    print("REDUÇÃO DO COLUNAR")
    print(f"  bruto                   : {reduction['raw_pct']:.2f}%")
    print(f"  gzip                    : {reduction['gzip_pct']:.2f}%")

    print()
    print("AMOSTRAS")

    for name, sample in report["amostras"].items():
        print()
        print(f"  {name.upper()}")
        print(f"    municípios            : {sample['count']:,}")
        print(f"    alertas               : {sample['alertas']:,}")
        print(f"    score mediano         : {sample['score_median']:.6f}")
        print(f"    verboso gzip          : {format_kib(sample['verbose_gzip_bytes'])}")
        print(
            f"    colunar gzip          : {format_kib(sample['columnar_gzip_bytes'])}"
        )

    print()
    print(f"Relatório                 : {OUTPUT_FILE}")
    print()
    print("STATUS: BENCHMARK CONCLUÍDO")


def main() -> None:
    """Executa o benchmark completo."""
    print("=" * 108)
    print("BENCHMARK DO SERVING NACIONAL DO MAPA PREDITIVO")
    print("=" * 108)

    print()
    print(f"Fonte: {INPUT_FILE}")

    dataframe = load_predictions()

    print()
    print("Validando avaliação final...")

    validate_predictions(dataframe)

    validate_horizons(dataframe)

    print("Validação científica/estrutural: OK")

    report = benchmark(dataframe)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print_report(report)


if __name__ == "__main__":
    main()
