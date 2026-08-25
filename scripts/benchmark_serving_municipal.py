"""Compara formatos candidatos para o serving histórico municipal."""

import gzip
import json
import tempfile
from pathlib import Path
from statistics import median

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT / "data" / "processed" / "painel_municipal_semanal_2016_2025.parquet"
)

OUTPUT_FILE = PROJECT_ROOT / "reports" / "audits" / "benchmark_serving_municipal.json"

COLUMNS = [
    "codigo_ibge_7",
    "ano_epidemiologico",
    "semana_epidemiologica",
    "data_inicio_semana",
    "casos_provaveis",
    "incidencia_100mil",
    "registro_sinan_presente",
    "zero_preenchido",
    "populacao",
]

EXPECTED_ROWS = 2_907_593
EXPECTED_TERRITORIES = 5_571
EXPECTED_FULL_WEEKS = 522

BOA_ESPERANCA_NORTE = "5101837"
EXPECTED_BOA_ESPERANCA_WEEKS = 53

SCHEMA_VERSION = "1.0"


def load_panel() -> pd.DataFrame:
    """Carrega somente as colunas candidatas ao serving municipal."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    dataframe = pd.read_parquet(
        INPUT_FILE,
        columns=COLUMNS,
    )

    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas. "
            f"Esperado: {EXPECTED_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    dataframe["codigo_ibge_7"] = (
        dataframe["codigo_ibge_7"].astype("string").str.strip().str.zfill(7)
    )

    territories = dataframe["codigo_ibge_7"].nunique()

    if territories != EXPECTED_TERRITORIES:
        raise ValueError(
            "Quantidade inesperada de unidades territoriais. "
            f"Esperado: {EXPECTED_TERRITORIES:,}; "
            f"obtido: {territories:,}."
        )

    dataframe = dataframe.sort_values(
        [
            "codigo_ibge_7",
            "data_inicio_semana",
        ],
        kind="stable",
    ).reset_index(drop=True)

    return dataframe


def normalize_value(value):
    """Converte valores Pandas para tipos adequados ao JSON."""
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
) -> dict:
    """Representação com um objeto JSON para cada semana."""
    records = []

    for row in group.itertuples(index=False):
        records.append(
            {
                "ano_epidemiologico": int(row.ano_epidemiologico),
                "semana_epidemiologica": int(row.semana_epidemiologica),
                "data_inicio_semana": normalize_value(row.data_inicio_semana),
                "casos_provaveis": int(row.casos_provaveis),
                "incidencia_100mil": (
                    None
                    if pd.isna(row.incidencia_100mil)
                    else float(row.incidencia_100mil)
                ),
                "registro_sinan_presente": bool(row.registro_sinan_presente),
                "zero_preenchido": bool(row.zero_preenchido),
                "populacao": (None if pd.isna(row.populacao) else int(row.populacao)),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "codigo_ibge_7": code,
        "count": len(records),
        "data": records,
    }


def build_compact_payload(
    code: str,
    group: pd.DataFrame,
) -> dict:
    """Representação colunar compacta para um município."""
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
            "casos_provaveis": group["casos_provaveis"].astype(int).tolist(),
            "incidencia_100mil": [
                (None if pd.isna(value) else float(value))
                for value in group["incidencia_100mil"]
            ],
            "registro_sinan_presente": group["registro_sinan_presente"]
            .astype(bool)
            .tolist(),
            "zero_preenchido": group["zero_preenchido"].astype(bool).tolist(),
            "populacao": [
                (None if pd.isna(value) else int(value)) for value in group["populacao"]
            ],
        },
    }


def serialize_json(
    payload: dict,
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
    """Retorna tamanho da representação comprimida."""
    return len(
        gzip.compress(
            data,
            compresslevel=9,
            mtime=0,
        )
    )


def format_bytes(
    value: float,
) -> str:
    """Formata quantidade de bytes."""
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


def benchmark_json(
    dataframe: pd.DataFrame,
) -> dict:
    """Mede JSON verboso e compacto para todos os municípios."""
    verbose_sizes = []
    verbose_gzip_sizes = []

    compact_sizes = []
    compact_gzip_sizes = []

    rows_per_territory = {}

    for code, group in dataframe.groupby(
        "codigo_ibge_7",
        sort=True,
    ):
        code = str(code)

        rows_per_territory[code] = len(group)

        verbose = serialize_json(
            build_verbose_payload(
                code,
                group,
            )
        )

        compact = serialize_json(
            build_compact_payload(
                code,
                group,
            )
        )

        verbose_sizes.append(len(verbose))

        verbose_gzip_sizes.append(gzip_size(verbose))

        compact_sizes.append(len(compact))

        compact_gzip_sizes.append(gzip_size(compact))

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
        "compact": {
            "total": sum(compact_sizes),
            "total_gzip": sum(compact_gzip_sizes),
            "min": min(compact_sizes),
            "median": median(compact_sizes),
            "max": max(compact_sizes),
            "median_gzip": median(compact_gzip_sizes),
            "max_gzip": max(compact_gzip_sizes),
        },
        "rows_per_territory": rows_per_territory,
    }


def benchmark_parquet(
    dataframe: pd.DataFrame,
) -> int:
    """Mede um único Parquet nacional apenas com as colunas de serving."""
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "municipal_history.parquet"

        dataframe.to_parquet(
            output,
            index=False,
            compression="zstd",
        )

        return output.stat().st_size


def validate_week_distribution(
    rows_per_territory: dict[str, int],
) -> None:
    """Valida a cobertura temporal municipal conhecida."""
    short = {
        code: rows
        for code, rows in rows_per_territory.items()
        if rows != EXPECTED_FULL_WEEKS
    }

    expected_short = {
        BOA_ESPERANCA_NORTE: EXPECTED_BOA_ESPERANCA_WEEKS,
    }

    if short != expected_short:
        raise ValueError(
            f"Distribuição municipal de semanas inesperada. Obtido: {short}"
        )


def write_benchmark_audit(
    dataframe: pd.DataFrame,
    json_results: dict,
    parquet_size: int,
) -> None:
    """Registra de forma estruturada o benchmark arquitetural."""
    verbose = json_results["verbose"]

    compact = json_results["compact"]

    rows_per_territory = json_results["rows_per_territory"]

    row_distribution = pd.Series(rows_per_territory).value_counts().sort_index()

    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "APROVADO",
        "analise": "benchmark do serving historico municipal",
        "fonte": "data/processed/painel_municipal_semanal_2016_2025.parquet",
        "painel": {
            "linhas": len(dataframe),
            "unidades_territoriais": len(rows_per_territory),
            "colunas_avaliadas": COLUMNS,
            "distribuicao_linhas_por_unidade": {
                str(int(rows)): int(territories)
                for rows, territories in row_distribution.items()
            },
        },
        "json_verboso_por_municipio": {
            "total_bytes": int(verbose["total"]),
            "total_gzip_estimado_bytes": int(verbose["total_gzip"]),
            "arquivo_minimo_bytes": int(verbose["min"]),
            "arquivo_mediano_bytes": float(verbose["median"]),
            "arquivo_mediano_gzip_bytes": float(verbose["median_gzip"]),
            "maior_arquivo_bytes": int(verbose["max"]),
            "maior_arquivo_gzip_bytes": int(verbose["max_gzip"]),
        },
        "json_compacto_por_municipio": {
            "total_bytes": int(compact["total"]),
            "total_gzip_estimado_bytes": int(compact["total_gzip"]),
            "arquivo_minimo_bytes": int(compact["min"]),
            "arquivo_mediano_bytes": float(compact["median"]),
            "arquivo_mediano_gzip_bytes": float(compact["median_gzip"]),
            "maior_arquivo_bytes": int(compact["max"]),
            "maior_arquivo_gzip_bytes": int(compact["max_gzip"]),
            "reducao_sem_compressao_vs_verboso": float(
                1 - compact["total"] / verbose["total"]
            ),
            "reducao_gzip_vs_verboso": float(
                1 - compact["total_gzip"] / verbose["total_gzip"]
            ),
        },
        "parquet_nacional_reduzido": {
            "compression": "zstd",
            "size_bytes": int(parquet_size),
        },
        "decisao": {
            "formato_inicial": "json_compacto_por_municipio",
            "arquivos_estimados": EXPECTED_TERRITORIES,
            "estrutura_prevista": (
                "data/serving/historical/municipality/series/{codigo_ibge_7}.json"
            ),
            "motivos": [
                "Cada consulta municipal transfere apenas a serie solicitada.",
                "O arquivo municipal mediano possui payload gzip muito pequeno.",
                (
                    "O formato pode ser consumido diretamente "
                    "pelo frontend sem biblioteca Parquet."
                ),
                "Arquivos estaticos podem utilizar cache do navegador e CDN.",
            ],
            "parquet_preservado_como_alternativa": True,
        },
        "validacoes": {
            "linhas_esperadas": EXPECTED_ROWS,
            "unidades_territoriais_esperadas": EXPECTED_TERRITORIES,
            "semanas_padrao_por_unidade": EXPECTED_FULL_WEEKS,
            "excecao_cobertura_temporal": {
                "codigo_ibge_7": BOA_ESPERANCA_NORTE,
                "semanas": EXPECTED_BOA_ESPERANCA_WEEKS,
            },
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


def print_results(
    dataframe: pd.DataFrame,
    json_results: dict,
    parquet_size: int,
) -> None:
    """Exibe o benchmark consolidado."""
    verbose = json_results["verbose"]

    compact = json_results["compact"]

    rows_per_territory = json_results["rows_per_territory"]

    print("=" * 104)

    print("BENCHMARK — SERVING HISTÓRICO MUNICIPAL")

    print("=" * 104)

    print()

    print(f"Linhas nacionais      : {len(dataframe):,}")

    print(f"Unidades territoriais : {len(rows_per_territory):,}")

    print()

    print("COBERTURA POR MUNICÍPIO")

    counts = pd.Series(rows_per_territory).value_counts().sort_index()

    for rows, territories in counts.items():
        print(f"  {int(rows):>4} semanas : {int(territories):>5,} unidades")

    print()

    print("JSON VERBOSO — 1 arquivo por município")

    print(f"  Total sem compressão : {format_bytes(verbose['total'])}")

    print(f"  Total gzip estimado   : {format_bytes(verbose['total_gzip'])}")

    print(f"  Arquivo mediano       : {format_bytes(verbose['median'])}")

    print(f"  Arquivo mediano gzip  : {format_bytes(verbose['median_gzip'])}")

    print(f"  Maior arquivo         : {format_bytes(verbose['max'])}")

    print(f"  Maior arquivo gzip    : {format_bytes(verbose['max_gzip'])}")

    print()

    print("JSON COMPACTO — 1 arquivo por município")

    print(f"  Total sem compressão : {format_bytes(compact['total'])}")

    print(f"  Total gzip estimado   : {format_bytes(compact['total_gzip'])}")

    print(f"  Arquivo mediano       : {format_bytes(compact['median'])}")

    print(f"  Arquivo mediano gzip  : {format_bytes(compact['median_gzip'])}")

    print(f"  Maior arquivo         : {format_bytes(compact['max'])}")

    print(f"  Maior arquivo gzip    : {format_bytes(compact['max_gzip'])}")

    print()

    reduction = 1 - compact["total"] / verbose["total"]

    gzip_reduction = 1 - compact["total_gzip"] / verbose["total_gzip"]

    print("REDUÇÃO JSON COMPACTO × VERBOSO")

    print(f"  Sem compressão        : {reduction:.2%}")

    print(f"  Com gzip              : {gzip_reduction:.2%}")

    print()

    print("PARQUET NACIONAL REDUZIDO")

    print(f"  9 colunas + Zstandard : {format_bytes(parquet_size)}")

    print()

    print("DECISÃO INICIAL")

    print("  Formato               : JSON compacto por município")

    print(f"  Arquivos estimados    : {EXPECTED_TERRITORIES:,}")

    print()

    print("Observação:")

    print(
        "O Parquet é medido como alternativa de leitura server-side. "
        "Ele não implica que o navegador deverá interpretar Parquet."
    )

    print()

    print("Auditoria estruturada:")

    print(f"  {OUTPUT_FILE.relative_to(PROJECT_ROOT).as_posix()}")

    print()

    print("STATUS: BENCHMARK CONCLUÍDO")


def main() -> None:
    """Executa benchmark dos formatos candidatos."""
    dataframe = load_panel()

    json_results = benchmark_json(dataframe)

    validate_week_distribution(json_results["rows_per_territory"])

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
