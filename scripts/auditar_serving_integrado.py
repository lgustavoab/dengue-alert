"""Audita de forma integrada toda a camada de serving da aplicação."""

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SERVING_ROOT = PROJECT_ROOT / "data" / "serving"

AUDIT_FILE = PROJECT_ROOT / "reports" / "audits" / "auditoria_serving_integrado.json"

SCHEMA_VERSION = "1.0"

EXPECTED_TOTAL_JSON_FILES = 11_164

EXPECTED_HISTORICAL_MUNICIPALITIES = 5_571
EXPECTED_HISTORICAL_ROWS = 2_907_593
EXPECTED_HISTORICAL_CASES = 16_294_913

EXPECTED_PREDICTION_MUNICIPALITIES = 5_569
EXPECTED_PREDICTION_ROWS = 1_124_938
EXPECTED_PREDICTIONS_PER_MUNICIPALITY = 202

EXPECTED_PREDICTION_HORIZON_COUNTS = {
    "h1": 52,
    "h2": 51,
    "h3": 50,
    "h4": 49,
}

EXPECTED_PREDICTION_THRESHOLDS = {
    "h1": 0.187687,
    "h2": 0.190783,
    "h3": 0.167991,
    "h4": 0.157138,
}

BOA_ESPERANCA_NORTE = "5101837"
FERNANDO_DE_NORONHA = "2605459"

EXPECTED_NON_PREDICTIVE_CODES = {
    BOA_ESPERANCA_NORTE,
    FERNANDO_DE_NORONHA,
}

HISTORICAL_INDEX_FILE = SERVING_ROOT / "historical" / "municipality" / "index.json"

HISTORICAL_SERIES_DIR = SERVING_ROOT / "historical" / "municipality" / "series"

PREDICTION_INDEX_FILE = SERVING_ROOT / "prediction" / "municipality" / "index.json"

PREDICTION_SERIES_DIR = SERVING_ROOT / "prediction" / "municipality" / "series"

REQUIRED_FILES = [
    SERVING_ROOT / "metadata" / "territories.json",
    SERVING_ROOT / "metadata" / "temporal_coverage.json",
    SERVING_ROOT / "quality" / "overview.json",
    SERVING_ROOT / "quality" / "sinan_pipeline.json",
    SERVING_ROOT / "quality" / "territorial_coverage.json",
    SERVING_ROOT / "quality" / "population_coverage.json",
    SERVING_ROOT / "quality" / "climate_coverage.json",
    HISTORICAL_INDEX_FILE,
    PREDICTION_INDEX_FILE,
    SERVING_ROOT / "prediction" / "metadata" / "model.json",
    SERVING_ROOT / "prediction" / "evaluation" / "overview.json",
    SERVING_ROOT / "prediction" / "evaluation" / "by_horizon.json",
]


def reject_nonfinite_constant(
    value: str,
) -> None:
    """Rejeita NaN e Infinity durante leitura JSON."""
    raise ValueError(f"Constante JSON não permitida: {value}")


def load_json_strict(
    path: Path,
) -> dict[str, Any]:
    """Carrega JSON rejeitando valores numéricos não finitos."""
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_nonfinite_constant,
        )
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"JSON inválido: {path}") from error

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError(f"Contrato JSON não é objeto: {path}")

    return payload


def validate_required_files() -> None:
    """Confirma presença dos contratos essenciais."""
    missing = [path for path in REQUIRED_FILES if not path.exists()]

    if missing:
        relative = [path.relative_to(PROJECT_ROOT).as_posix() for path in missing]

        raise FileNotFoundError(
            "Contratos obrigatórios ausentes: " + ", ".join(relative)
        )


def validate_all_json_contracts() -> dict[str, Any]:
    """Valida sintaxe, finitude e schema dos JSONs de serving."""
    json_files = sorted(SERVING_ROOT.rglob("*.json"))

    if len(json_files) != EXPECTED_TOTAL_JSON_FILES:
        raise ValueError(
            "Quantidade inesperada de contratos JSON no serving. "
            f"Esperado: {EXPECTED_TOTAL_JSON_FILES:,}; "
            f"obtido: {len(json_files):,}."
        )

    total_size = 0

    for path in json_files:
        payload = load_json_strict(path)

        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                "schema_version ausente ou divergente em: "
                + path.relative_to(PROJECT_ROOT).as_posix()
            )

        total_size += path.stat().st_size

    return {
        "files": len(json_files),
        "total_size_bytes": total_size,
    }


def extract_index_codes(
    path: Path,
) -> tuple[dict[str, Any], set[str], int]:
    """Extrai códigos territoriais dos diferentes contratos de índice."""
    payload = load_json_strict(path)

    if isinstance(
        payload.get("items"),
        list,
    ):
        collection_key = "items"

    elif isinstance(
        payload.get("data"),
        list,
    ):
        collection_key = "data"

    else:
        raise TypeError(
            f"Índice sem coleção territorial válida ('items' ou 'data'): {path}"
        )

    items = payload[collection_key]

    codes = set()

    for item in items:
        if not isinstance(
            item,
            dict,
        ):
            raise TypeError(f"Item inválido no índice: {path}")

        code = item.get("codigo_ibge_7")

        if (
            not isinstance(
                code,
                str,
            )
            or len(code) != 7
            or not code.isdigit()
        ):
            raise ValueError(f"Código IBGE inválido no índice: {path}")

        if code in codes:
            raise ValueError(f"Código duplicado no índice {path}: {code}")

        codes.add(code)

    actual_count = len(codes)

    declared_count = payload.get("count")

    if declared_count is not None and declared_count != actual_count:
        raise ValueError(
            f"Count divergente no índice: {path}. "
            f"Declarado: {declared_count}; "
            f"obtido: {actual_count}."
        )

    if len(items) != actual_count:
        raise ValueError(f"Quantidade de itens e códigos únicos diverge: {path}")

    return (
        payload,
        codes,
        actual_count,
    )


def validate_historical_series(
    expected_codes: set[str],
) -> dict[str, Any]:
    """Valida todas as séries históricas municipais."""
    files = sorted(HISTORICAL_SERIES_DIR.glob("*.json"))

    if len(files) != EXPECTED_HISTORICAL_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de séries históricas. "
            f"Esperado: {EXPECTED_HISTORICAL_MUNICIPALITIES:,}; "
            f"obtido: {len(files):,}."
        )

    file_codes = {path.stem for path in files}

    if file_codes != expected_codes:
        raise ValueError(
            "Índice histórico e arquivos históricos possuem "
            "universos territoriais diferentes."
        )

    total_rows = 0
    total_cases = 0

    temporal_distribution: dict[int, int] = {}

    for path in files:
        payload = load_json_strict(path)

        code = payload.get("codigo_ibge_7")

        if code != path.stem:
            raise ValueError(f"Código interno divergente do nome do arquivo: {path}")

        count = payload.get("count")

        if not isinstance(
            count,
            int,
        ):
            raise TypeError(f"Count histórico inválido: {path}")

        data = payload.get("data")

        if not isinstance(
            data,
            dict,
        ):
            raise TypeError(f"Bloco data histórico inválido: {path}")

        for field, values in data.items():
            if not isinstance(
                values,
                list,
            ):
                raise TypeError(f"Array histórico inválido: {path}/{field}")

            if len(values) != count:
                raise ValueError(f"Array histórico desalinhado: {path}/{field}")

        cases = data.get("casos_provaveis")

        if not isinstance(
            cases,
            list,
        ):
            raise TypeError(f"casos_provaveis ausente: {path}")

        total_rows += count

        total_cases += sum(int(value) for value in cases)

        temporal_distribution[count] = (
            temporal_distribution.get(
                count,
                0,
            )
            + 1
        )

    if total_rows != EXPECTED_HISTORICAL_ROWS:
        raise ValueError(
            "Total de município-semanas histórico divergente. "
            f"Esperado: {EXPECTED_HISTORICAL_ROWS:,}; "
            f"obtido: {total_rows:,}."
        )

    if total_cases != EXPECTED_HISTORICAL_CASES:
        raise ValueError(
            "Total de casos histórico divergente. "
            f"Esperado: {EXPECTED_HISTORICAL_CASES:,}; "
            f"obtido: {total_cases:,}."
        )

    expected_distribution = {
        53: 1,
        522: 5_570,
    }

    if temporal_distribution != expected_distribution:
        raise ValueError(
            f"Distribuição temporal histórica divergente: {temporal_distribution}"
        )

    return {
        "files": len(files),
        "rows": total_rows,
        "cases": total_cases,
        "temporal_distribution": {
            str(weeks): territories
            for weeks, territories in sorted(temporal_distribution.items())
        },
    }


def validate_prediction_series(
    expected_codes: set[str],
) -> dict[str, Any]:
    """Valida todas as séries preditivas municipais."""
    files = sorted(PREDICTION_SERIES_DIR.glob("*.json"))

    if len(files) != EXPECTED_PREDICTION_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de séries preditivas. "
            f"Esperado: {EXPECTED_PREDICTION_MUNICIPALITIES:,}; "
            f"obtido: {len(files):,}."
        )

    file_codes = {path.stem for path in files}

    if file_codes != expected_codes:
        raise ValueError(
            "Índice preditivo e arquivos preditivos possuem "
            "universos territoriais diferentes."
        )

    total_rows = 0

    rows_by_horizon = {key: 0 for key in EXPECTED_PREDICTION_HORIZON_COUNTS}

    for path in files:
        payload = load_json_strict(path)

        code = payload.get("codigo_ibge_7")

        if code != path.stem:
            raise ValueError(f"Código interno divergente do arquivo: {path}")

        count = payload.get("count")

        if count != EXPECTED_PREDICTIONS_PER_MUNICIPALITY:
            raise ValueError(f"Count preditivo inválido: {path}")

        horizons = payload.get("horizontes")

        if not isinstance(
            horizons,
            dict,
        ):
            raise TypeError(f"Bloco horizontes inválido: {path}")

        if set(horizons) != set(EXPECTED_PREDICTION_HORIZON_COUNTS):
            raise ValueError(f"Conjunto de horizontes inválido: {path}")

        municipality_total = 0

        for key, expected_count in EXPECTED_PREDICTION_HORIZON_COUNTS.items():
            block = horizons[key]

            if not isinstance(
                block,
                dict,
            ):
                raise TypeError(f"Bloco {key} inválido: {path}")

            block_count = block.get("count")

            if block_count != expected_count:
                raise ValueError(f"{path}/{key}: count divergente.")

            threshold = block.get("threshold")

            if threshold != EXPECTED_PREDICTION_THRESHOLDS[key]:
                raise ValueError(f"{path}/{key}: threshold divergente.")

            data = block.get("data")

            if not isinstance(
                data,
                dict,
            ):
                raise TypeError(f"{path}/{key}: bloco data inválido.")

            for field, values in data.items():
                if not isinstance(
                    values,
                    list,
                ):
                    raise TypeError(f"{path}/{key}/{field}: array inválido.")

                if len(values) != expected_count:
                    raise ValueError(f"{path}/{key}/{field}: array desalinhado.")

            scores = data.get("score")

            predictions = data.get("predicao")

            if not isinstance(
                scores,
                list,
            ) or not isinstance(
                predictions,
                list,
            ):
                raise TypeError(f"{path}/{key}: score/predicao ausente.")

            calculated = [float(score) >= float(threshold) for score in scores]

            if calculated != predictions:
                raise ValueError(
                    f"{path}/{key}: predicao divergente de score >= threshold."
                )

            municipality_total += block_count

            rows_by_horizon[key] += block_count

        if municipality_total != EXPECTED_PREDICTIONS_PER_MUNICIPALITY:
            raise ValueError(f"Soma de horizontes divergente: {path}")

        total_rows += municipality_total

    if total_rows != EXPECTED_PREDICTION_ROWS:
        raise ValueError(
            "Total de predições divergente. "
            f"Esperado: {EXPECTED_PREDICTION_ROWS:,}; "
            f"obtido: {total_rows:,}."
        )

    expected_rows_by_horizon = {
        "h1": 289_588,
        "h2": 284_019,
        "h3": 278_450,
        "h4": 272_881,
    }

    if rows_by_horizon != expected_rows_by_horizon:
        raise ValueError("Totais preditivos por horizonte divergentes.")

    return {
        "files": len(files),
        "rows": total_rows,
        "rows_by_horizon": rows_by_horizon,
    }


def validate_territorial_relationship(
    historical_codes: set[str],
    prediction_codes: set[str],
) -> dict[str, Any]:
    """Valida relação entre universos histórico e preditivo."""
    if not prediction_codes.issubset(historical_codes):
        unexpected = sorted(prediction_codes - historical_codes)

        raise ValueError(
            f"Há municípios preditivos ausentes do histórico: {unexpected[:10]}"
        )

    historical_only = historical_codes - prediction_codes

    if historical_only != EXPECTED_NON_PREDICTIVE_CODES:
        raise ValueError(
            "Diferença territorial histórico × predição divergente. "
            f"Obtido: {sorted(historical_only)}"
        )

    return {
        "historical": len(historical_codes),
        "prediction": len(prediction_codes),
        "historical_only": sorted(historical_only),
    }


def write_audit(
    payload: dict[str, Any],
) -> None:
    """Grava auditoria integrada em JSON determinístico."""
    AUDIT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    AUDIT_FILE.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def format_bytes(
    value: float,
) -> str:
    """Formata bytes para leitura humana."""
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


def main() -> None:
    """Executa a auditoria integrada do serving."""
    if not SERVING_ROOT.exists():
        raise FileNotFoundError(f"Serving não encontrado: {SERVING_ROOT}")

    validate_required_files()

    json_summary = validate_all_json_contracts()

    (
        _,
        historical_codes,
        historical_index_count,
    ) = extract_index_codes(HISTORICAL_INDEX_FILE)

    (
        _,
        prediction_codes,
        prediction_index_count,
    ) = extract_index_codes(PREDICTION_INDEX_FILE)

    if historical_index_count != EXPECTED_HISTORICAL_MUNICIPALITIES:
        raise ValueError(
            "Quantidade divergente no índice histórico. "
            f"Esperado: {EXPECTED_HISTORICAL_MUNICIPALITIES:,}; "
            f"obtido: {historical_index_count:,}."
        )

    if prediction_index_count != EXPECTED_PREDICTION_MUNICIPALITIES:
        raise ValueError(
            "Quantidade divergente no índice preditivo. "
            f"Esperado: {EXPECTED_PREDICTION_MUNICIPALITIES:,}; "
            f"obtido: {prediction_index_count:,}."
        )

    historical_summary = validate_historical_series(historical_codes)

    prediction_summary = validate_prediction_series(prediction_codes)

    territorial_summary = validate_territorial_relationship(
        historical_codes,
        prediction_codes,
    )

    audit = {
        "schema_version": SCHEMA_VERSION,
        "status": "APROVADO",
        "auditoria": "serving_integrado",
        "serving_root": "data/serving",
        "json": json_summary,
        "historical": historical_summary,
        "prediction": prediction_summary,
        "territorial_relationship": territorial_summary,
        "checks": {
            "required_contracts": True,
            "strict_json": True,
            "no_nan_or_infinity": True,
            "schema_version_consistent": True,
            "historical_index_matches_series": True,
            "prediction_index_matches_series": True,
            "prediction_is_subset_of_historical": True,
            "historical_totals_preserved": True,
            "prediction_totals_preserved": True,
            "prediction_rule_preserved": True,
        },
    }

    write_audit(audit)

    print("=" * 108)

    print("AUDITORIA INTEGRADA — CAMADA DE SERVING")

    print("=" * 108)

    print()

    print(f"Contratos JSON         : {json_summary['files']:,}")

    print(f"Tamanho total JSON     : {format_bytes(json_summary['total_size_bytes'])}")

    print()

    print("HISTÓRICO")

    print(f"  Municípios            : {historical_summary['files']:,}")

    print(f"  Município-semanas     : {historical_summary['rows']:,}")

    print(f"  Casos preservados     : {historical_summary['cases']:,}")

    print()

    print("PREDIÇÃO")

    print(f"  Municípios            : {prediction_summary['files']:,}")

    print(f"  Predições             : {prediction_summary['rows']:,}")

    for key, rows in prediction_summary["rows_by_horizon"].items():
        print(f"  {key.upper():<4}                  : {rows:,}")

    print()

    print("RELAÇÃO TERRITORIAL")

    print(f"  Histórico             : {territorial_summary['historical']:,}")

    print(f"  Predição              : {territorial_summary['prediction']:,}")

    print(
        "  Apenas no histórico   : " + ", ".join(territorial_summary["historical_only"])
    )

    print()

    print("Auditoria:")

    print("  " + AUDIT_FILE.relative_to(PROJECT_ROOT).as_posix())

    print()

    print("STATUS: SERVING INTEGRADO VALIDADO")


if __name__ == "__main__":
    main()
