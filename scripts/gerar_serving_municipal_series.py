"""Gera as séries históricas municipais para a camada de serving."""

import json
import shutil
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT / "data" / "processed" / "painel_municipal_semanal_2016_2025.parquet"
)

OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "serving" / "historical" / "municipality" / "series"
)

STAGING_DIR = OUTPUT_DIR.parent / "series.__staging__"

SCHEMA_VERSION = "1.0"

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

DATA_COLUMNS = [
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
EXPECTED_CASES = 16_294_913

EXPECTED_FULL_WEEKS = 522

BOA_ESPERANCA_NORTE = "5101837"
EXPECTED_BOA_ESPERANCA_WEEKS = 53


def load_panel() -> pd.DataFrame:
    """Carrega e normaliza as colunas necessárias ao serving municipal."""
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


def validate_panel(
    dataframe: pd.DataFrame,
) -> None:
    """Valida invariantes nacionais antes da geração dos arquivos."""
    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            "Quantidade inesperada de município-semanas. "
            f"Esperado: {EXPECTED_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    territories = int(dataframe["codigo_ibge_7"].nunique())

    if territories != EXPECTED_TERRITORIES:
        raise ValueError(
            "Quantidade inesperada de unidades territoriais. "
            f"Esperado: {EXPECTED_TERRITORIES:,}; "
            f"obtido: {territories:,}."
        )

    cases = int(dataframe["casos_provaveis"].sum())

    if cases != EXPECTED_CASES:
        raise ValueError(
            "Total nacional de casos divergente. "
            f"Esperado: {EXPECTED_CASES:,}; "
            f"obtido: {cases:,}."
        )

    duplicate_count = int(
        dataframe.duplicated(
            subset=[
                "codigo_ibge_7",
                "ano_epidemiologico",
                "semana_epidemiologica",
            ]
        ).sum()
    )

    if duplicate_count:
        raise ValueError(
            "Foram encontradas chaves município-semana duplicadas: "
            f"{duplicate_count:,}."
        )

    required_non_null = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "semana_epidemiologica",
        "data_inicio_semana",
        "casos_provaveis",
        "registro_sinan_presente",
        "zero_preenchido",
        "populacao",
    ]

    missing = dataframe[required_non_null].isna().sum()

    missing = missing[missing > 0]

    if not missing.empty:
        raise ValueError(
            "Foram encontrados valores ausentes em colunas "
            "obrigatórias: "
            + ", ".join(f"{column}={int(count)}" for column, count in missing.items())
        )

    invalid_codes = ~dataframe["codigo_ibge_7"].str.fullmatch(r"\d{7}")

    if invalid_codes.any():
        raise ValueError("Foram encontrados códigos IBGE inválidos.")


def validate_week_distribution(
    dataframe: pd.DataFrame,
) -> dict[str, int]:
    """Valida a quantidade de semanas disponível por território."""
    rows_per_territory = (
        dataframe.groupby(
            "codigo_ibge_7",
            sort=True,
        )
        .size()
        .astype(int)
        .to_dict()
    )

    short = {
        str(code): int(rows)
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

    return {str(code): int(rows) for code, rows in rows_per_territory.items()}


def nullable_float(
    value: Any,
) -> float | None:
    """Converte valor numérico opcional para JSON."""
    if pd.isna(value):
        return None

    return float(value)


def nullable_int(
    value: Any,
) -> int | None:
    """Converte inteiro opcional para JSON."""
    if pd.isna(value):
        return None

    return int(value)


def build_payload(
    code: str,
    group: pd.DataFrame,
) -> dict[str, Any]:
    """Constrói o contrato colunar compacto de um território."""
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
                value.date().isoformat() for value in group["data_inicio_semana"]
            ],
            "casos_provaveis": group["casos_provaveis"].astype(int).tolist(),
            "incidencia_100mil": [
                nullable_float(value) for value in group["incidencia_100mil"]
            ],
            "registro_sinan_presente": group["registro_sinan_presente"]
            .astype(bool)
            .tolist(),
            "zero_preenchido": group["zero_preenchido"].astype(bool).tolist(),
            "populacao": [nullable_int(value) for value in group["populacao"]],
        },
    }


def validate_payload(
    payload: dict[str, Any],
) -> None:
    """Valida estrutura e alinhamento interno de um arquivo municipal."""
    code = payload["codigo_ibge_7"]

    if (
        not isinstance(
            code,
            str,
        )
        or len(code) != 7
        or not code.isdigit()
    ):
        raise ValueError(f"Código IBGE inválido no payload: {code!r}")

    count = payload["count"]

    data = payload["data"]

    if set(data) != set(DATA_COLUMNS):
        raise ValueError(f"Contrato municipal {code} possui colunas inesperadas.")

    for column, values in data.items():
        if len(values) != count:
            raise ValueError(
                f"Contrato municipal {code}: coluna {column} "
                f"possui {len(values)} valores, mas count={count}."
            )

    dates = data["data_inicio_semana"]

    if dates != sorted(dates):
        raise ValueError(f"Série municipal {code} não está em ordem cronológica.")

    cases = data["casos_provaveis"]

    if any(value < 0 for value in cases):
        raise ValueError(f"Série municipal {code} contém casos negativos.")


def serialize_payload(
    payload: dict[str, Any],
) -> str:
    """Serializa contrato municipal em JSON compacto UTF-8."""
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(
                ",",
                ":",
            ),
        )
        + "\n"
    )


def prepare_staging_directory() -> None:
    """Prepara diretório temporário limpo para geração."""
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)

    STAGING_DIR.mkdir(
        parents=True,
        exist_ok=False,
    )


def promote_staging_directory() -> None:
    """Substitui a versão anterior somente após geração válida."""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    STAGING_DIR.replace(OUTPUT_DIR)


def generate_series(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """Gera todos os arquivos municipais em diretório temporário."""
    dataframe = dataframe.sort_values(
        [
            "codigo_ibge_7",
            "data_inicio_semana",
        ],
        kind="stable",
    ).reset_index(drop=True)

    prepare_staging_directory()

    generated_files = 0
    generated_rows = 0
    generated_cases = 0
    sizes = []

    try:
        for code, group in dataframe.groupby(
            "codigo_ibge_7",
            sort=True,
        ):
            code = str(code)

            payload = build_payload(
                code,
                group,
            )

            validate_payload(payload)

            text = serialize_payload(payload)

            output_file = STAGING_DIR / f"{code}.json"

            output_file.write_text(
                text,
                encoding="utf-8",
            )

            generated_files += 1

            generated_rows += int(payload["count"])

            generated_cases += sum(
                int(value) for value in payload["data"]["casos_provaveis"]
            )

            sizes.append(output_file.stat().st_size)

        if generated_files != EXPECTED_TERRITORIES:
            raise ValueError(
                "Quantidade de arquivos municipais divergente. "
                f"Esperado: {EXPECTED_TERRITORIES:,}; "
                f"obtido: {generated_files:,}."
            )

        if generated_rows != EXPECTED_ROWS:
            raise ValueError(
                "Soma das linhas dos arquivos municipais divergente. "
                f"Esperado: {EXPECTED_ROWS:,}; "
                f"obtido: {generated_rows:,}."
            )

        if generated_cases != EXPECTED_CASES:
            raise ValueError(
                "Soma dos casos dos arquivos municipais divergente. "
                f"Esperado: {EXPECTED_CASES:,}; "
                f"obtido: {generated_cases:,}."
            )

        actual_files = list(STAGING_DIR.glob("*.json"))

        if len(actual_files) != EXPECTED_TERRITORIES:
            raise ValueError("Quantidade física de JSONs divergente no staging.")

        promote_staging_directory()

    except Exception:
        if STAGING_DIR.exists():
            shutil.rmtree(STAGING_DIR)

        raise

    return {
        "files": generated_files,
        "rows": generated_rows,
        "cases": generated_cases,
        "total_size": sum(sizes),
        "min_size": min(sizes),
        "median_size": median(sizes),
        "max_size": max(sizes),
    }


def format_bytes(
    value: float,
) -> str:
    """Formata tamanho para exibição."""
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


def print_summary(
    result: dict[str, Any],
    rows_per_territory: dict[str, int],
) -> None:
    """Exibe resumo final da geração."""
    print("=" * 108)

    print("SERVING — SÉRIES HISTÓRICAS MUNICIPAIS")

    print("=" * 108)

    print()

    print(f"Arquivos gerados       : {result['files']:,}")

    print(f"Município-semanas      : {result['rows']:,}")

    print(f"Casos preservados      : {result['cases']:,}")

    print()

    print("COBERTURA TEMPORAL")

    distribution = pd.Series(rows_per_territory).value_counts().sort_index()

    for weeks, territories in distribution.items():
        print(f"  {int(weeks):>4} semanas : {int(territories):>5,} unidades")

    print()

    print("TAMANHO DOS ARQUIVOS")

    print(f"  Total                 : {format_bytes(result['total_size'])}")

    print(f"  Menor arquivo         : {format_bytes(result['min_size'])}")

    print(f"  Arquivo mediano       : {format_bytes(result['median_size'])}")

    print(f"  Maior arquivo         : {format_bytes(result['max_size'])}")

    print()

    print("Exceção temporal:")

    print(f"  {BOA_ESPERANCA_NORTE} — {EXPECTED_BOA_ESPERANCA_WEEKS} semanas")

    print()

    print("Diretório:")

    print("  " + OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix())

    print()

    print("STATUS: SÉRIES MUNICIPAIS GERADAS E VALIDADAS")


def main() -> None:
    """Executa a geração das séries históricas municipais."""
    dataframe = load_panel()

    validate_panel(dataframe)

    rows_per_territory = validate_week_distribution(dataframe)

    result = generate_series(dataframe)

    print_summary(
        result,
        rows_per_territory,
    )


if __name__ == "__main__":
    main()
