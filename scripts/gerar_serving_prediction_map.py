"""Gera o serving nacional do mapa preditivo retrospectivo de 2025."""

from __future__ import annotations

import json
import shutil
from math import isclose
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT / "data" / "processed" / "predicoes_avaliacao_final_2025.parquet"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "serving" / "prediction" / "map"

STAGING_DIR = OUTPUT_DIR.parent / "map.__staging__"

BACKUP_DIR = OUTPUT_DIR.parent / "map.__backup__"

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

DATA_COLUMNS = [
    "codigo_ibge_7",
    "score",
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

EXPECTED_POSITIVE_PREDICTIONS = {
    1: 44_500,
    2: 46_975,
    3: 55_358,
    4: 70_312,
}

EXPECTED_MAP_FILES = sum(EXPECTED_WEEKS_BY_HORIZON.values())


def load_predictions() -> pd.DataFrame:
    """Carrega somente as colunas necessárias ao mapa."""
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

    duplicates = int(
        dataframe.duplicated(
            subset=[
                "codigo_ibge_7",
                "ano_epidemiologico",
                "semana_epidemiologica",
                "horizonte",
            ]
        ).sum()
    )

    if duplicates:
        raise ValueError(
            f"Foram encontradas chaves preditivas duplicadas: {duplicates:,}."
        )

    invalid_score = (dataframe["score"] < 0) | (dataframe["score"] > 1)

    if invalid_score.any():
        raise ValueError("Foram encontrados scores fora do intervalo [0, 1].")

    calculated_prediction = dataframe["score"] >= dataframe["threshold"]

    divergent = int((dataframe["predicao"].astype(bool) != calculated_prediction).sum())

    if divergent:
        raise ValueError(
            f"Predições divergentes da regra score >= threshold: {divergent:,}."
        )


def validate_horizons(
    dataframe: pd.DataFrame,
) -> None:
    """Valida cobertura e resultados de cada horizonte."""
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

        week_count = int(subset["semana_epidemiologica"].nunique())

        expected_week_count = EXPECTED_WEEKS_BY_HORIZON[horizon]

        if week_count != expected_week_count:
            raise ValueError(
                f"H{horizon}: semanas inesperadas. "
                f"Esperado: {expected_week_count}; "
                f"obtido: {week_count}."
            )

        weeks = sorted(subset["semana_epidemiologica"].astype(int).unique().tolist())

        expected_weeks = list(
            range(
                1,
                expected_week_count + 1,
            )
        )

        if weeks != expected_weeks:
            raise ValueError(f"H{horizon}: conjunto inesperado de semanas.")

        thresholds = subset["threshold"].astype(float).drop_duplicates().tolist()

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
            raise ValueError(f"H{horizon}: threshold divergente.")

        positive_predictions = int(subset["predicao"].astype(bool).sum())

        expected_positives = EXPECTED_POSITIVE_PREDICTIONS[horizon]

        if positive_predictions != expected_positives:
            raise ValueError(
                f"H{horizon}: quantidade divergente de predições positivas."
            )


def build_payload(
    horizon: int,
    week: int,
    group: pd.DataFrame,
) -> dict[str, Any]:
    """Cria o contrato de uma semana e horizonte."""
    if len(group) != EXPECTED_MUNICIPALITIES:
        raise ValueError(
            f"H{horizon}/SE{week:02d}: quantidade inesperada de municípios."
        )

    if group["codigo_ibge_7"].duplicated().any():
        raise ValueError(f"H{horizon}/SE{week:02d}: códigos municipais duplicados.")

    group = group.sort_values(
        "codigo_ibge_7",
        kind="stable",
    ).reset_index(drop=True)

    dates = group["data_inicio_semana"].drop_duplicates().tolist()

    if len(dates) != 1:
        raise ValueError(f"H{horizon}/SE{week:02d}: mais de uma data de início.")

    thresholds = group["threshold"].astype(float).drop_duplicates().tolist()

    if len(thresholds) != 1:
        raise ValueError(f"H{horizon}/SE{week:02d}: mais de um threshold.")

    threshold = float(thresholds[0])

    expected_threshold = EXPECTED_THRESHOLDS[horizon]

    if not isclose(
        threshold,
        expected_threshold,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError(f"H{horizon}/SE{week:02d}: threshold divergente.")

    return {
        "schema_version": SCHEMA_VERSION,
        "ano_epidemiologico": EXPECTED_YEAR,
        "semana_epidemiologica": week,
        "data_inicio_semana": (pd.Timestamp(dates[0]).date().isoformat()),
        "horizonte": horizon,
        "threshold": threshold,
        "count": len(group),
        "data": {
            "codigo_ibge_7": (group["codigo_ibge_7"].astype(str).tolist()),
            "score": (group["score"].astype(float).tolist()),
            "predicao": (group["predicao"].astype(bool).tolist()),
        },
    }


def validate_payload(
    payload: dict[str, Any],
    horizon: int,
    week: int,
) -> None:
    """Valida um contrato antes e após serialização."""
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("schema_version inválido.")

    if payload.get("ano_epidemiologico") != EXPECTED_YEAR:
        raise ValueError("Ano epidemiológico inválido.")

    if payload.get("semana_epidemiologica") != week:
        raise ValueError("Semana epidemiológica inválida.")

    if payload.get("horizonte") != horizon:
        raise ValueError("Horizonte inválido.")

    if payload.get("count") != EXPECTED_MUNICIPALITIES:
        raise ValueError("Count municipal inválido.")

    threshold = float(payload.get("threshold"))

    if not isclose(
        threshold,
        EXPECTED_THRESHOLDS[horizon],
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise ValueError("Threshold inválido.")

    data = payload.get("data")

    if not isinstance(
        data,
        dict,
    ):
        raise TypeError("Bloco data inválido.")

    if set(data) != set(DATA_COLUMNS):
        raise ValueError("Campos inesperados no bloco data.")

    for field in DATA_COLUMNS:
        values = data.get(field)

        if not isinstance(
            values,
            list,
        ):
            raise TypeError(f"{field}: valor não é array.")

        if len(values) != EXPECTED_MUNICIPALITIES:
            raise ValueError(f"{field}: comprimento divergente.")

    codes = data["codigo_ibge_7"]

    if len(set(codes)) != EXPECTED_MUNICIPALITIES:
        raise ValueError("Códigos IBGE duplicados no payload.")

    if codes != sorted(codes):
        raise ValueError("Códigos IBGE fora de ordem.")

    if any(
        not isinstance(
            code,
            str,
        )
        or len(code) != 7
        or not code.isdigit()
        for code in codes
    ):
        raise ValueError("Código IBGE inválido no payload.")

    scores = data["score"]

    if any(
        (
            not isinstance(
                score,
                int | float,
            )
            or isinstance(
                score,
                bool,
            )
            or score < 0
            or score > 1
        )
        for score in scores
    ):
        raise ValueError("Score inválido no payload.")

    predictions = data["predicao"]

    if any(
        not isinstance(
            prediction,
            bool,
        )
        for prediction in predictions
    ):
        raise ValueError("Predição inválida no payload.")


def serialize_payload(
    payload: dict[str, Any],
) -> str:
    """Serializa contrato em JSON determinístico."""
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


def prepare_staging() -> None:
    """Cria staging vazio."""
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)

    STAGING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def write_payload(
    horizon: int,
    week: int,
    payload: dict[str, Any],
) -> Path:
    """Grava um contrato no staging."""
    horizon_dir = STAGING_DIR / f"h{horizon}"

    horizon_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = horizon_dir / f"se{week:02d}.json"

    path.write_text(
        serialize_payload(payload),
        encoding="utf-8",
    )

    return path


def load_json_strict(
    path: Path,
) -> dict[str, Any]:
    """Relê JSON rejeitando NaN e Infinity."""

    def reject_constant(
        value: str,
    ) -> None:
        raise ValueError(f"Constante JSON não permitida: {value}")

    payload = json.loads(
        path.read_text(encoding="utf-8"),
        parse_constant=reject_constant,
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError(f"JSON não possui objeto na raiz: {path}")

    return payload


def build_index() -> dict[str, Any]:
    """Cria o índice do serving nacional do mapa."""
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "APROVADO",
        "avaliacao": "retrospectiva_2025",
        "ano_epidemiologico": EXPECTED_YEAR,
        "municipios": EXPECTED_MUNICIPALITIES,
        "predicoes": EXPECTED_ROWS,
        "arquivos": EXPECTED_MAP_FILES,
        "horizontes": {
            f"h{horizon}": {
                "horizonte": horizon,
                "threshold": (EXPECTED_THRESHOLDS[horizon]),
                "semanas": list(
                    range(
                        1,
                        EXPECTED_WEEKS_BY_HORIZON[horizon] + 1,
                    )
                ),
            }
            for horizon in EXPECTED_HORIZONS
        },
    }


def write_index(
    index: dict[str, Any],
) -> None:
    """Grava o índice no staging."""
    path = STAGING_DIR / "index.json"

    path.write_text(
        json.dumps(
            index,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def validate_staging(
    index: dict[str, Any],
) -> tuple[
    int,
    int,
]:
    """Valida todos os contratos gerados no staging."""
    expected_paths = {
        (f"h{horizon}/se{week:02d}.json")
        for horizon in EXPECTED_HORIZONS
        for week in range(
            1,
            EXPECTED_WEEKS_BY_HORIZON[horizon] + 1,
        )
    }

    generated_paths = {
        path.relative_to(STAGING_DIR).as_posix()
        for path in STAGING_DIR.rglob("se*.json")
    }

    if generated_paths != expected_paths:
        missing = sorted(expected_paths - generated_paths)

        unexpected = sorted(generated_paths - expected_paths)

        raise ValueError(
            "Conjunto de arquivos divergente. "
            f"Ausentes: {missing}; "
            f"inesperados: {unexpected}."
        )

    if index.get("arquivos") != EXPECTED_MAP_FILES:
        raise ValueError("Quantidade divergente no índice.")

    total_size = 0
    positive_predictions = {horizon: 0 for horizon in EXPECTED_HORIZONS}

    for horizon in EXPECTED_HORIZONS:
        for week in range(
            1,
            EXPECTED_WEEKS_BY_HORIZON[horizon] + 1,
        ):
            path = STAGING_DIR / f"h{horizon}" / f"se{week:02d}.json"

            payload = load_json_strict(path)

            validate_payload(
                payload,
                horizon,
                week,
            )

            total_size += path.stat().st_size

            positive_predictions[horizon] += sum(payload["data"]["predicao"])

    for horizon in EXPECTED_HORIZONS:
        expected = EXPECTED_POSITIVE_PREDICTIONS[horizon]

        obtained = positive_predictions[horizon]

        if obtained != expected:
            raise ValueError(
                f"H{horizon}: total de alertas "
                "divergente no staging. "
                f"Esperado: {expected:,}; "
                f"obtido: {obtained:,}."
            )

    persisted_index = load_json_strict(STAGING_DIR / "index.json")

    if persisted_index != index:
        raise ValueError("Índice persistido diverge do índice em memória.")

    return (
        len(generated_paths),
        total_size,
    )


def promote_staging() -> None:
    """Promove staging preservando versão anterior."""
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)

    had_previous = OUTPUT_DIR.exists()

    if had_previous:
        OUTPUT_DIR.replace(BACKUP_DIR)

    try:
        STAGING_DIR.replace(OUTPUT_DIR)
    except Exception:
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)

        if had_previous and BACKUP_DIR.exists():
            BACKUP_DIR.replace(OUTPUT_DIR)

        raise

    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)


def generate() -> tuple[
    int,
    int,
]:
    """Executa a geração completa do serving do mapa."""
    dataframe = load_predictions()

    validate_predictions(dataframe)

    validate_horizons(dataframe)

    dataframe = dataframe.sort_values(
        [
            "horizonte",
            "semana_epidemiologica",
            "codigo_ibge_7",
        ],
        kind="stable",
    ).reset_index(drop=True)

    prepare_staging()

    generated = 0

    try:
        for horizon in EXPECTED_HORIZONS:
            subset = dataframe[dataframe["horizonte"] == horizon]

            weeks = EXPECTED_WEEKS_BY_HORIZON[horizon]

            print(f"H{horizon}: gerando {weeks} semanas...")

            for week in range(
                1,
                weeks + 1,
            ):
                group = subset[subset["semana_epidemiologica"] == week].copy()

                payload = build_payload(
                    horizon,
                    week,
                    group,
                )

                validate_payload(
                    payload,
                    horizon,
                    week,
                )

                path = write_payload(
                    horizon,
                    week,
                    payload,
                )

                persisted = load_json_strict(path)

                validate_payload(
                    persisted,
                    horizon,
                    week,
                )

                generated += 1

        index = build_index()

        write_index(index)

        file_count, total_size = validate_staging(index)

        if generated != file_count:
            raise ValueError("Quantidade gerada diverge da validação final.")

        promote_staging()

    except Exception:
        if STAGING_DIR.exists():
            shutil.rmtree(STAGING_DIR)

        raise

    return (
        file_count,
        total_size,
    )


def format_size(
    value: int,
) -> str:
    """Formata bytes para MiB."""
    return f"{value / 1024**2:.2f} MiB"


def main() -> None:
    """Executa o gerador."""
    print("=" * 108)
    print("SERVING DO MAPA PREDITIVO — AVALIAÇÃO RETROSPECTIVA 2025")
    print("=" * 108)
    print()

    print(f"Fonte       : {INPUT_FILE}")
    print(f"Destino     : {OUTPUT_DIR}")
    print()

    files, total_size = generate()

    print()
    print(f"Arquivos semanais : {files:,}")
    print("Índice             : 1")
    print(f"Municípios         : {EXPECTED_MUNICIPALITIES:,}")
    print(f"Predições          : {EXPECTED_ROWS:,}")
    print(f"Tamanho contratos  : {format_size(total_size)}")
    print()
    print("STATUS: SERVING DO MAPA GERADO E VALIDADO")


if __name__ == "__main__":
    main()
