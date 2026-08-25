"""Gera séries municipais do serving preditivo retrospectivo."""

import json
import shutil
from math import isclose
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT / "data" / "processed" / "predicoes_avaliacao_final_2025.parquet"
)

OUTPUT_DIR = (
    PROJECT_ROOT / "data" / "serving" / "prediction" / "municipality" / "series"
)

STAGING_DIR = OUTPUT_DIR.parent / "series.__staging__"

BACKUP_DIR = OUTPUT_DIR.parent / "series.__backup__"

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

DATA_COLUMNS = [
    "ano_epidemiologico",
    "semana_epidemiologica",
    "data_inicio_semana",
    "risco_elevado",
    "target",
    "score",
    "predicao",
]

EXPECTED_ROWS = 1_124_938
EXPECTED_MUNICIPALITIES = 5_569
EXPECTED_ROWS_PER_MUNICIPALITY = 202
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

EXPECTED_TARGET_POSITIVES = {
    1: 36_582,
    2: 35_737,
    3: 34_849,
    4: 33_889,
}

EXPECTED_POSITIVE_PREDICTIONS = {
    1: 44_500,
    2: 46_975,
    3: 55_358,
    4: 70_312,
}

EXPECTED_EARLY_WARNING_ALERTS = {
    1: 10_440,
    2: 15_083,
    3: 21_766,
    4: 36_367,
}


def load_predictions() -> pd.DataFrame:
    """Carrega somente as colunas necessárias às séries municipais."""
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
    """Valida invariantes gerais do artefato final."""
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
    """Valida cobertura, thresholds e resultados por horizonte."""
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

        target_positives = int(subset["target"].astype(bool).sum())

        if target_positives != EXPECTED_TARGET_POSITIVES[horizon]:
            raise ValueError(f"H{horizon}: quantidade divergente de targets positivos.")

        positive_predictions = int(subset["predicao"].astype(bool).sum())

        if positive_predictions != EXPECTED_POSITIVE_PREDICTIONS[horizon]:
            raise ValueError(
                f"H{horizon}: quantidade divergente de predições positivas."
            )

        early_warning = ~subset["risco_elevado"].astype(bool) & subset[
            "predicao"
        ].astype(bool)

        early_warning_alerts = int(early_warning.sum())

        if early_warning_alerts != EXPECTED_EARLY_WARNING_ALERTS[horizon]:
            raise ValueError(
                f"H{horizon}: quantidade divergente de alertas early warning."
            )


def validate_municipality_distribution(
    dataframe: pd.DataFrame,
) -> None:
    """Valida quantidade total e por horizonte de cada município."""
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


def build_horizon_payload(
    horizon: int,
    group: pd.DataFrame,
) -> dict[str, Any]:
    """Cria bloco de uma série municipal para um horizonte."""
    group = group.sort_values(
        [
            "data_inicio_semana",
            "semana_epidemiologica",
        ],
        kind="stable",
    )

    thresholds = group["threshold"].drop_duplicates().tolist()

    if len(thresholds) != 1:
        raise ValueError(f"H{horizon}: bloco municipal possui mais de um threshold.")

    threshold = float(thresholds[0])

    expected_threshold = EXPECTED_THRESHOLDS[horizon]

    if not isclose(
        threshold,
        expected_threshold,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError(f"H{horizon}: threshold municipal divergente.")

    return {
        "count": len(group),
        "threshold": threshold,
        "data": {
            "ano_epidemiologico": (group["ano_epidemiologico"].astype(int).tolist()),
            "semana_epidemiologica": (
                group["semana_epidemiologica"].astype(int).tolist()
            ),
            "data_inicio_semana": [
                value.date().isoformat() for value in group["data_inicio_semana"]
            ],
            "risco_elevado": (group["risco_elevado"].astype(bool).tolist()),
            "target": (group["target"].astype(bool).tolist()),
            "score": (group["score"].astype(float).tolist()),
            "predicao": (group["predicao"].astype(bool).tolist()),
        },
    }


def build_payload(
    code: str,
    group: pd.DataFrame,
) -> dict[str, Any]:
    """Cria contrato completo de um município."""
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


def validate_payload(
    payload: dict[str, Any],
) -> None:
    """Valida contrato municipal antes e depois da serialização."""
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema_version municipal inválido.")

    code = payload.get("codigo_ibge_7")

    if not isinstance(code, str) or len(code) != 7 or not code.isdigit():
        raise ValueError("Código IBGE inválido no payload municipal.")

    if payload.get("count") != EXPECTED_ROWS_PER_MUNICIPALITY:
        raise ValueError(f"{code}: quantidade total de predições inválida.")

    horizons = payload.get("horizontes")

    if not isinstance(
        horizons,
        dict,
    ):
        raise TypeError(f"{code}: bloco de horizontes ausente.")

    expected_keys = {f"h{horizon}" for horizon in EXPECTED_HORIZONS}

    if set(horizons) != expected_keys:
        raise ValueError(f"{code}: conjunto de horizontes inválido.")

    total_count = 0

    for horizon in EXPECTED_HORIZONS:
        key = f"h{horizon}"

        block = horizons[key]

        expected_count = EXPECTED_ROWS_PER_MUNICIPALITY_BY_HORIZON[horizon]

        count = block.get("count")

        if count != expected_count:
            raise ValueError(
                f"{code}/{key}: count inválido. "
                f"Esperado: {expected_count}; "
                f"obtido: {count}."
            )

        total_count += int(count)

        threshold = float(block.get("threshold"))

        if not isclose(
            threshold,
            EXPECTED_THRESHOLDS[horizon],
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(f"{code}/{key}: threshold inválido.")

        data = block.get("data")

        if not isinstance(
            data,
            dict,
        ):
            raise TypeError(f"{code}/{key}: bloco data ausente.")

        if set(data) != set(DATA_COLUMNS):
            raise ValueError(f"{code}/{key}: conjunto de campos inválido.")

        for field, values in data.items():
            if not isinstance(
                values,
                list,
            ):
                raise TypeError(f"{code}/{key}/{field}: valor não é array.")

            if len(values) != expected_count:
                raise ValueError(
                    f"{code}/{key}/{field}: "
                    f"possui {len(values)} valores; "
                    f"esperado: {expected_count}."
                )

        years = data["ano_epidemiologico"]

        if any(int(year) != EXPECTED_YEAR for year in years):
            raise ValueError(f"{code}/{key}: ano epidemiológico inválido.")

        dates = data["data_inicio_semana"]

        if dates != sorted(dates):
            raise ValueError(f"{code}/{key}: datas fora de ordem.")

        scores = data["score"]

        if any((float(score) < 0 or float(score) > 1) for score in scores):
            raise ValueError(f"{code}/{key}: score fora de [0, 1].")

        predictions = data["predicao"]

        calculated_predictions = [float(score) >= threshold for score in scores]

        if predictions != calculated_predictions:
            raise ValueError(f"{code}/{key}: predicao diverge de score >= threshold.")

    if total_count != EXPECTED_ROWS_PER_MUNICIPALITY:
        raise ValueError(f"{code}: soma dos horizontes não fecha.")


def serialize_payload(
    payload: dict[str, Any],
) -> str:
    """Serializa contrato municipal em JSON compacto."""
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
    """Cria staging vazio para a nova geração."""
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)

    STAGING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def promote_staging_directory() -> None:
    """Promove staging mantendo backup temporário da versão anterior."""
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)

    had_previous_output = OUTPUT_DIR.exists()

    if had_previous_output:
        OUTPUT_DIR.replace(BACKUP_DIR)

    try:
        STAGING_DIR.replace(OUTPUT_DIR)
    except Exception:
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)

        if had_previous_output and BACKUP_DIR.exists():
            BACKUP_DIR.replace(OUTPUT_DIR)

        raise

    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)


def validate_generated_directory(
    expected_codes: set[str],
) -> dict[str, Any]:
    """Relê e valida integralmente o staging produzido."""
    files = sorted(STAGING_DIR.glob("*.json"))

    if len(files) != EXPECTED_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de arquivos no staging. "
            f"Esperado: {EXPECTED_MUNICIPALITIES:,}; "
            f"obtido: {len(files):,}."
        )

    file_codes = {path.stem for path in files}

    if file_codes != expected_codes:
        missing = sorted(expected_codes - file_codes)

        unexpected = sorted(file_codes - expected_codes)

        raise ValueError(
            "Conjunto de arquivos municipais divergente. "
            f"Ausentes: {missing[:5]}; "
            f"inesperados: {unexpected[:5]}."
        )

    total_rows = 0

    rows_by_horizon = {horizon: 0 for horizon in EXPECTED_HORIZONS}

    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))

        validate_payload(payload)

        total_rows += int(payload["count"])

        for horizon in EXPECTED_HORIZONS:
            rows_by_horizon[horizon] += int(
                payload["horizontes"][f"h{horizon}"]["count"]
            )

    if total_rows != EXPECTED_ROWS:
        raise ValueError(
            "Total de predições dos arquivos gerados não fecha com o artefato final."
        )

    for horizon in EXPECTED_HORIZONS:
        if rows_by_horizon[horizon] != EXPECTED_ROWS_BY_HORIZON[horizon]:
            raise ValueError(f"H{horizon}: total gerado divergente.")

    return {
        "files": len(files),
        "rows": total_rows,
        "rows_by_horizon": rows_by_horizon,
    }


def generate_series(
    dataframe: pd.DataFrame,
) -> dict[str, Any]:
    """Gera, valida e promove todas as séries municipais."""
    dataframe = dataframe.sort_values(
        [
            "codigo_ibge_7",
            "horizonte",
            "data_inicio_semana",
        ],
        kind="stable",
    ).reset_index(drop=True)

    expected_codes = set(dataframe["codigo_ibge_7"].astype(str).unique().tolist())

    prepare_staging_directory()

    sizes = []

    generated_files = 0

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

            serialized = serialize_payload(payload)

            path = STAGING_DIR / f"{code}.json"

            path.write_text(
                serialized,
                encoding="utf-8",
            )

            sizes.append(path.stat().st_size)

            generated_files += 1

            if generated_files % 1000 == 0:
                print(
                    "Gerados e validados: "
                    f"{generated_files:,} / "
                    f"{EXPECTED_MUNICIPALITIES:,}"
                )

        validation = validate_generated_directory(expected_codes)

        promote_staging_directory()

    except Exception:
        if STAGING_DIR.exists():
            shutil.rmtree(STAGING_DIR)

        raise

    if not sizes:
        raise ValueError("Nenhum arquivo municipal foi gerado.")

    return {
        "files": validation["files"],
        "rows": validation["rows"],
        "rows_by_horizon": validation["rows_by_horizon"],
        "total_size": sum(sizes),
        "min_size": min(sizes),
        "median_size": median(sizes),
        "max_size": max(sizes),
    }


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


def print_summary(
    result: dict[str, Any],
) -> None:
    """Exibe resumo da geração das séries preditivas."""
    print("=" * 108)

    print("SERVING — SÉRIES PREDITIVAS MUNICIPAIS")

    print("=" * 108)

    print()

    print(f"Arquivos gerados       : {result['files']:,}")

    print(f"Predições preservadas  : {result['rows']:,}")

    print()

    print("COBERTURA POR HORIZONTE")

    for horizon in EXPECTED_HORIZONS:
        print(
            f"  H{horizon} : "
            f"{result['rows_by_horizon'][horizon]:>7,} "
            "predições | "
            f"{EXPECTED_ROWS_PER_MUNICIPALITY_BY_HORIZON[horizon]} "
            "por município | "
            f"threshold {EXPECTED_THRESHOLDS[horizon]:.6f}"
        )

    print()

    print("TAMANHO DOS ARQUIVOS")

    print(f"  Total                 : {format_bytes(result['total_size'])}")

    print(f"  Menor arquivo         : {format_bytes(result['min_size'])}")

    print(f"  Arquivo mediano       : {format_bytes(result['median_size'])}")

    print(f"  Maior arquivo         : {format_bytes(result['max_size'])}")

    print()

    print("Diretório:")

    print("  " + OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix())

    print()

    print("STATUS: SÉRIES PREDITIVAS MUNICIPAIS GERADAS E VALIDADAS")


def main() -> None:
    """Executa geração do serving preditivo municipal."""
    dataframe = load_predictions()

    validate_predictions(dataframe)

    validate_horizon_structure(dataframe)

    validate_municipality_distribution(dataframe)

    result = generate_series(dataframe)

    print_summary(result)


if __name__ == "__main__":
    main()
