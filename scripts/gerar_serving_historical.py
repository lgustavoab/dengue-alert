"""Gera os contratos de serving histórico do Dengue Alert."""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "1.0"

PERIOD_HISTORICAL = "2016-2025"
PERIOD_RISK = "2018-2025"

AUDITS_DIR = PROJECT_ROOT / "reports" / "audits"
SERVING_DIR = PROJECT_ROOT / "data" / "serving" / "historical"

PANORAMA_ANNUAL_FILE = AUDITS_DIR / "panorama_nacional_anual_2016_2025.csv"

PANORAMA_WEEKLY_FILE = AUDITS_DIR / "panorama_nacional_semanal_2016_2025.csv"

SEASONALITY_NATIONAL_FILE = (
    AUDITS_DIR / "sazonalidade_nacional_semana_epidemiologica_2016_2025.csv"
)

SEASONALITY_REGIONAL_FILE = (
    AUDITS_DIR / "sazonalidade_regional_semana_epidemiologica_2016_2025.csv"
)

SPATIAL_REGIONS_FILE = AUDITS_DIR / "distribuicao_espacial_regiao_periodo_2016_2025.csv"

SPATIAL_STATES_FILE = AUDITS_DIR / "distribuicao_espacial_uf_periodo_2016_2025.csv"

SPATIAL_MUNICIPALITIES_FILE = (
    AUDITS_DIR / "distribuicao_espacial_municipio_periodo_2016_2025.csv"
)

RISK_WEEKLY_FILE = AUDITS_DIR / "serie_risco_semanal_nacional_regional_2018_2025.csv"

RISK_MUNICIPALITIES_FILE = AUDITS_DIR / "dinamica_risco_municipio_2018_2025.csv"

EPISODES_FILE = AUDITS_DIR / "episodios_risco_elevado_2018_2025.csv"

CLIMATE_NATIONAL_FILE = AUDITS_DIR / "associacao_clima_dengue_nacional_2016_2025.csv"

CLIMATE_REGIONAL_FILE = AUDITS_DIR / "associacao_clima_dengue_regional_2016_2025.csv"

EXPECTED_PANORAMA_ANNUAL_ROWS = 10
EXPECTED_PANORAMA_WEEKLY_ROWS = 522

EXPECTED_SEASONALITY_NATIONAL_ROWS = 53
EXPECTED_SEASONALITY_REGIONAL_ROWS = 265

EXPECTED_REGIONS = 5
EXPECTED_STATES = 27
EXPECTED_MUNICIPALITIES = 5_571

EXPECTED_RISK_WEEKLY_ROWS = 2_508
EXPECTED_RISK_MUNICIPALITIES = 5_569
EXPECTED_RISK_UNAVAILABLE_MUNICIPALITIES = 2

EXPECTED_EPISODES = 54_269
EXPECTED_RISK_WEEKS = 414_678
EXPECTED_EPISODE_MIN = 1
EXPECTED_EPISODE_P25 = 3
EXPECTED_EPISODE_MEDIAN = 4
EXPECTED_EPISODE_P75 = 9
EXPECTED_EPISODE_P90 = 19
EXPECTED_EPISODE_P95 = 26
EXPECTED_EPISODE_P99 = 41
EXPECTED_EPISODE_MAX = 110

EXPECTED_CLIMATE_NATIONAL_ROWS = 21
EXPECTED_CLIMATE_REGIONAL_ROWS = 105

REGIONS = [
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul",
]

CLIMATE_VARIABLES = [
    "temperatura_media_c",
    "umidade_relativa_media_pct",
    "precipitacao_total_mm",
]

CLIMATE_LAGS = [
    0,
    1,
    2,
    3,
    4,
    6,
    8,
]


def source_path(path: Path) -> str:
    """Retorna caminho relativo à raiz do projeto."""
    return path.relative_to(PROJECT_ROOT).as_posix()


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    """Grava JSON UTF-8, determinístico e sem NaN."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )

    path.write_text(
        text + "\n",
        encoding="utf-8",
    )


def load_csv(
    path: Path,
    *,
    required_columns: set[str],
    dtype: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Carrega CSV e valida as colunas mínimas."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    dataframe = pd.read_csv(
        path,
        dtype=dtype,
    )

    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError(
            f"Colunas ausentes em {path.name}: " + ", ".join(sorted(missing))
        )

    return dataframe


def normalize_identifiers(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Normaliza identificadores territoriais como strings."""
    dataframe = dataframe.copy()

    if "codigo_ibge_7" in dataframe.columns:
        dataframe["codigo_ibge_7"] = (
            dataframe["codigo_ibge_7"].astype("string").str.strip().str.zfill(7)
        )

    if "codigo_uf_ibge" in dataframe.columns:
        dataframe["codigo_uf_ibge"] = (
            dataframe["codigo_uf_ibge"].astype("string").str.strip().str.zfill(2)
        )

    return dataframe


def standardize_display_names(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Padroniza somente nomes territoriais destinados ao serving."""
    rename_map = {}

    if "nome_municipio_ibge" in dataframe.columns:
        rename_map["nome_municipio_ibge"] = "nome_municipio"

    if "nome_uf_ibge" in dataframe.columns:
        rename_map["nome_uf_ibge"] = "nome_uf"

    return dataframe.rename(columns=rename_map)


def json_scalar(
    value: Any,
) -> Any:
    """Converte escalar Pandas/NumPy para tipo JSON nativo."""
    if pd.isna(value):
        return None

    if isinstance(
        value,
        pd.Timestamp,
    ):
        return value.isoformat()

    if isinstance(
        value,
        np.generic,
    ):
        return value.item()

    return value


def dataframe_records(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Converte DataFrame para registros JSON sem tipos NumPy."""
    columns = dataframe.columns.tolist()

    records = []

    for row in dataframe.itertuples(
        index=False,
        name=None,
    ):
        record = {
            column: json_scalar(value)
            for column, value in zip(
                columns,
                row,
                strict=True,
            )
        }

        records.append(record)

    return records


def build_table_contract(
    *,
    dataframe: pd.DataFrame,
    period: str,
    source: Path,
) -> dict[str, Any]:
    """Cria contrato tabular padrão."""
    return {
        "schema_version": SCHEMA_VERSION,
        "period": period,
        "source": [source_path(source)],
        "count": len(dataframe),
        "data": dataframe_records(dataframe),
    }


def validate_row_count(
    dataframe: pd.DataFrame,
    *,
    expected: int,
    label: str,
) -> None:
    """Valida quantidade exata de registros."""
    if len(dataframe) != expected:
        raise ValueError(
            f"{label}: quantidade inesperada de registros. "
            f"Esperado: {expected:,}; "
            f"obtido: {len(dataframe):,}."
        )


def validate_unique_key(
    dataframe: pd.DataFrame,
    *,
    columns: list[str],
    label: str,
) -> None:
    """Valida unicidade de uma chave lógica."""
    duplicates = int(dataframe.duplicated(subset=columns).sum())

    if duplicates:
        raise ValueError(f"{label}: {duplicates:,} chaves duplicadas para {columns}.")


def validate_regions(
    dataframe: pd.DataFrame,
) -> None:
    """Valida domínio das macrorregiões."""
    regions = set(dataframe["regiao"].dropna().astype(str).unique())

    if regions != set(REGIONS):
        raise ValueError(f"Conjunto inesperado de regiões. Obtido: {sorted(regions)}")


def sort_regions(
    dataframe: pd.DataFrame,
    *,
    additional_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Ordena macrorregiões na ordem oficial usada pelo projeto."""
    dataframe = dataframe.copy()

    region_order = {region: index for index, region in enumerate(REGIONS)}

    dataframe["_region_order"] = dataframe["regiao"].map(region_order)

    if dataframe["_region_order"].isna().any():
        raise ValueError("Foi encontrada região sem ordem definida.")

    sort_columns = ["_region_order"]

    if additional_columns:
        sort_columns.extend(additional_columns)

    dataframe = (
        dataframe.sort_values(
            sort_columns,
            kind="stable",
        )
        .drop(columns=["_region_order"])
        .reset_index(drop=True)
    )

    return dataframe


def build_panorama_annual() -> dict[str, Any]:
    """Constrói panorama nacional anual."""
    dataframe = load_csv(
        PANORAMA_ANNUAL_FILE,
        required_columns={
            "ano_epidemiologico",
            "casos_provaveis",
            "incidencia_anual_100mil",
        },
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_PANORAMA_ANNUAL_ROWS,
        label="Panorama anual",
    )

    validate_unique_key(
        dataframe,
        columns=["ano_epidemiologico"],
        label="Panorama anual",
    )

    years = dataframe["ano_epidemiologico"].astype(int).sort_values().tolist()

    if years != list(
        range(
            2016,
            2026,
        )
    ):
        raise ValueError(f"Anos inesperados no panorama anual: {years}")

    dataframe = dataframe.sort_values(
        "ano_epidemiologico",
        kind="stable",
    ).reset_index(drop=True)

    return build_table_contract(
        dataframe=dataframe,
        period=PERIOD_HISTORICAL,
        source=PANORAMA_ANNUAL_FILE,
    )


def build_panorama_weekly() -> dict[str, Any]:
    """Constrói panorama nacional semanal."""
    dataframe = load_csv(
        PANORAMA_WEEKLY_FILE,
        required_columns={
            "ano_epidemiologico",
            "semana_epidemiologica",
            "data_inicio_semana",
            "casos_provaveis",
            "incidencia_nacional_100mil",
        },
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_PANORAMA_WEEKLY_ROWS,
        label="Panorama semanal",
    )

    validate_unique_key(
        dataframe,
        columns=[
            "ano_epidemiologico",
            "semana_epidemiologica",
        ],
        label="Panorama semanal",
    )

    dataframe = dataframe.sort_values(
        [
            "ano_epidemiologico",
            "semana_epidemiologica",
        ],
        kind="stable",
    ).reset_index(drop=True)

    return build_table_contract(
        dataframe=dataframe,
        period=PERIOD_HISTORICAL,
        source=PANORAMA_WEEKLY_FILE,
    )


def build_seasonality_national() -> dict[str, Any]:
    """Constrói sazonalidade nacional."""
    dataframe = load_csv(
        SEASONALITY_NATIONAL_FILE,
        required_columns={
            "semana_epidemiologica",
            "incidencia_media_100mil",
            "incidencia_mediana_100mil",
            "incidencia_q25_100mil",
            "incidencia_q75_100mil",
        },
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_SEASONALITY_NATIONAL_ROWS,
        label="Sazonalidade nacional",
    )

    validate_unique_key(
        dataframe,
        columns=["semana_epidemiologica"],
        label="Sazonalidade nacional",
    )

    weeks = dataframe["semana_epidemiologica"].astype(int).sort_values().tolist()

    if weeks != list(
        range(
            1,
            54,
        )
    ):
        raise ValueError("Semanas inesperadas na sazonalidade nacional.")

    dataframe = dataframe.sort_values(
        "semana_epidemiologica",
        kind="stable",
    ).reset_index(drop=True)

    return build_table_contract(
        dataframe=dataframe,
        period=PERIOD_HISTORICAL,
        source=SEASONALITY_NATIONAL_FILE,
    )


def build_seasonality_regional() -> dict[str, Any]:
    """Constrói sazonalidade regional."""
    dataframe = load_csv(
        SEASONALITY_REGIONAL_FILE,
        required_columns={
            "regiao",
            "semana_epidemiologica",
            "incidencia_media_100mil",
            "incidencia_mediana_100mil",
            "incidencia_q25_100mil",
            "incidencia_q75_100mil",
        },
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_SEASONALITY_REGIONAL_ROWS,
        label="Sazonalidade regional",
    )

    validate_regions(dataframe)

    validate_unique_key(
        dataframe,
        columns=[
            "regiao",
            "semana_epidemiologica",
        ],
        label="Sazonalidade regional",
    )

    dataframe = sort_regions(
        dataframe,
        additional_columns=["semana_epidemiologica"],
    )

    return build_table_contract(
        dataframe=dataframe,
        period=PERIOD_HISTORICAL,
        source=SEASONALITY_REGIONAL_FILE,
    )


def build_spatial_regions() -> dict[str, Any]:
    """Constrói resumo espacial por região."""
    dataframe = load_csv(
        SPATIAL_REGIONS_FILE,
        required_columns={
            "regiao",
            "casos_periodo",
            "incidencia_mediana_anual_100mil",
        },
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_REGIONS,
        label="Espacial por região",
    )

    validate_regions(dataframe)

    validate_unique_key(
        dataframe,
        columns=["regiao"],
        label="Espacial por região",
    )

    dataframe = sort_regions(dataframe)

    return build_table_contract(
        dataframe=dataframe,
        period=PERIOD_HISTORICAL,
        source=SPATIAL_REGIONS_FILE,
    )


def build_spatial_states() -> dict[str, Any]:
    """Constrói resumo espacial por UF."""
    dataframe = load_csv(
        SPATIAL_STATES_FILE,
        required_columns={
            "codigo_uf_ibge",
            "nome_uf_ibge",
            "regiao",
            "casos_periodo",
            "incidencia_mediana_anual_100mil",
        },
        dtype={
            "codigo_uf_ibge": "string",
        },
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_STATES,
        label="Espacial por UF",
    )

    validate_regions(dataframe)

    dataframe = normalize_identifiers(dataframe)

    dataframe = standardize_display_names(dataframe)

    validate_unique_key(
        dataframe,
        columns=["codigo_uf_ibge"],
        label="Espacial por UF",
    )

    dataframe = dataframe.sort_values(
        "codigo_uf_ibge",
        kind="stable",
    ).reset_index(drop=True)

    return build_table_contract(
        dataframe=dataframe,
        period=PERIOD_HISTORICAL,
        source=SPATIAL_STATES_FILE,
    )


def build_spatial_municipalities() -> dict[str, Any]:
    """Constrói resumo espacial municipal."""
    dataframe = load_csv(
        SPATIAL_MUNICIPALITIES_FILE,
        required_columns={
            "codigo_ibge_7",
            "nome_municipio_ibge",
            "codigo_uf_ibge",
            "nome_uf_ibge",
            "regiao",
            "casos_periodo",
            "incidencia_mediana_anual_100mil",
        },
        dtype={
            "codigo_ibge_7": "string",
            "codigo_uf_ibge": "string",
        },
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_MUNICIPALITIES,
        label="Espacial municipal",
    )

    validate_regions(dataframe)

    dataframe = normalize_identifiers(dataframe)

    dataframe = standardize_display_names(dataframe)

    validate_unique_key(
        dataframe,
        columns=["codigo_ibge_7"],
        label="Espacial municipal",
    )

    dataframe = dataframe.sort_values(
        "codigo_ibge_7",
        kind="stable",
    ).reset_index(drop=True)

    return build_table_contract(
        dataframe=dataframe,
        period=PERIOD_HISTORICAL,
        source=SPATIAL_MUNICIPALITIES_FILE,
    )


def build_risk_weekly() -> dict[str, Any]:
    """Constrói série nacional e regional do risco elevado."""
    dataframe = load_csv(
        RISK_WEEKLY_FILE,
        required_columns={
            "escala",
            "grupo",
            "ano_epidemiologico",
            "semana_epidemiologica",
            "data_inicio_semana",
            "unidades_elegiveis",
            "unidades_em_risco",
            "proporcao_unidades_em_risco",
        },
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_RISK_WEEKLY_ROWS,
        label="Risco semanal",
    )

    validate_unique_key(
        dataframe,
        columns=[
            "escala",
            "grupo",
            "ano_epidemiologico",
            "semana_epidemiologica",
        ],
        label="Risco semanal",
    )

    dataframe = dataframe.sort_values(
        [
            "escala",
            "grupo",
            "ano_epidemiologico",
            "semana_epidemiologica",
        ],
        kind="stable",
    ).reset_index(drop=True)

    return build_table_contract(
        dataframe=dataframe,
        period=PERIOD_RISK,
        source=RISK_WEEKLY_FILE,
    )


def build_risk_municipalities() -> dict[str, Any]:
    """Constrói resumo municipal da dinâmica de risco."""
    dataframe = load_csv(
        RISK_MUNICIPALITIES_FILE,
        required_columns={
            "codigo_ibge_7",
            "nome_municipio_ibge",
            "codigo_uf_ibge",
            "nome_uf_ibge",
            "regiao",
            "semanas_risco",
            "episodios",
            "duracao_maxima_episodio",
        },
        dtype={
            "codigo_ibge_7": "string",
            "codigo_uf_ibge": "string",
        },
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_RISK_MUNICIPALITIES,
        label="Risco municipal",
    )

    validate_regions(dataframe)

    dataframe = normalize_identifiers(dataframe)

    dataframe = standardize_display_names(dataframe)

    validate_unique_key(
        dataframe,
        columns=["codigo_ibge_7"],
        label="Risco municipal",
    )

    dataframe = dataframe.sort_values(
        "codigo_ibge_7",
        kind="stable",
    ).reset_index(drop=True)

    return build_table_contract(
        dataframe=dataframe,
        period=PERIOD_RISK,
        source=RISK_MUNICIPALITIES_FILE,
    )


def build_municipality_index(
    spatial_contract: dict[str, Any],
    risk_contract: dict[str, Any],
) -> dict[str, Any]:
    """Constrói índice municipal compartilhado para navegação histórica."""
    spatial = pd.DataFrame(spatial_contract["data"])

    risk = pd.DataFrame(risk_contract["data"])

    required_spatial_columns = {
        "codigo_ibge_7",
        "nome_municipio",
        "codigo_uf_ibge",
        "nome_uf",
        "regiao",
        "anos_disponiveis",
    }

    missing = required_spatial_columns - set(spatial.columns)

    if missing:
        raise ValueError(
            "Colunas ausentes no contrato espacial municipal: "
            + ", ".join(sorted(missing))
        )

    if "codigo_ibge_7" not in risk.columns:
        raise ValueError("O contrato municipal de risco não possui codigo_ibge_7.")

    spatial_codes = set(spatial["codigo_ibge_7"].astype(str))

    risk_codes = set(risk["codigo_ibge_7"].astype(str))

    if not risk_codes.issubset(spatial_codes):
        extra_codes = sorted(risk_codes - spatial_codes)

        raise ValueError(
            "Existem unidades do contrato de risco ausentes "
            f"no contrato espacial: {extra_codes}"
        )

    dataframe = spatial[
        [
            "codigo_ibge_7",
            "nome_municipio",
            "codigo_uf_ibge",
            "nome_uf",
            "regiao",
            "anos_disponiveis",
        ]
    ].copy()

    dataframe["risco_historico_disponivel"] = dataframe["codigo_ibge_7"].isin(
        risk_codes
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_MUNICIPALITIES,
        label="Índice municipal",
    )

    validate_unique_key(
        dataframe,
        columns=["codigo_ibge_7"],
        label="Índice municipal",
    )

    risk_available = int(dataframe["risco_historico_disponivel"].sum())

    risk_unavailable = int((~dataframe["risco_historico_disponivel"]).sum())

    if risk_available != EXPECTED_RISK_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de unidades com histórico "
            "de risco disponível. "
            f"Esperado: {EXPECTED_RISK_MUNICIPALITIES:,}; "
            f"obtido: {risk_available:,}."
        )

    if risk_unavailable != EXPECTED_RISK_UNAVAILABLE_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de unidades sem histórico "
            "de risco disponível. "
            f"Esperado: {EXPECTED_RISK_UNAVAILABLE_MUNICIPALITIES}; "
            f"obtido: {risk_unavailable}."
        )

    dataframe = dataframe.sort_values(
        "codigo_ibge_7",
        kind="stable",
    ).reset_index(drop=True)

    return {
        "schema_version": SCHEMA_VERSION,
        "period": PERIOD_HISTORICAL,
        "source": [
            source_path(SPATIAL_MUNICIPALITIES_FILE),
            source_path(RISK_MUNICIPALITIES_FILE),
        ],
        "count": len(dataframe),
        "risk_history": {
            "available": risk_available,
            "unavailable": risk_unavailable,
        },
        "data": dataframe_records(dataframe),
    }


def build_episode_duration() -> dict[str, Any]:
    """Constrói resumo e distribuição da duração dos episódios."""
    dataframe = load_csv(
        EPISODES_FILE,
        required_columns={"duracao_semanas"},
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_EPISODES,
        label="Episódios de risco",
    )

    duration = dataframe["duracao_semanas"]

    if duration.isna().any():
        raise ValueError("Existem durações de episódio ausentes.")

    total_risk_weeks = int(duration.sum())

    if total_risk_weeks != EXPECTED_RISK_WEEKS:
        raise ValueError(
            "Total de semanas em risco divergente. "
            f"Esperado: {EXPECTED_RISK_WEEKS:,}; "
            f"obtido: {total_risk_weeks:,}."
        )

    summary = {
        "quantidade_episodios": len(duration),
        "semanas_risco": total_risk_weeks,
        "minimo": int(duration.min()),
        "media": float(duration.mean()),
        "p25": float(duration.quantile(0.25)),
        "mediana": float(duration.quantile(0.50)),
        "p75": float(duration.quantile(0.75)),
        "p90": float(duration.quantile(0.90)),
        "p95": float(duration.quantile(0.95)),
        "p99": float(duration.quantile(0.99)),
        "maximo": int(duration.max()),
    }

    expected_quantiles = {
        "minimo": EXPECTED_EPISODE_MIN,
        "p25": EXPECTED_EPISODE_P25,
        "mediana": EXPECTED_EPISODE_MEDIAN,
        "p75": EXPECTED_EPISODE_P75,
        "p90": EXPECTED_EPISODE_P90,
        "p95": EXPECTED_EPISODE_P95,
        "p99": EXPECTED_EPISODE_P99,
        "maximo": EXPECTED_EPISODE_MAX,
    }

    for key, expected in expected_quantiles.items():
        if not np.isclose(
            summary[key],
            expected,
        ):
            raise ValueError(
                f"Estatística inesperada para {key}. "
                f"Esperado: {expected}; "
                f"obtido: {summary[key]}."
            )

    frequency = duration.value_counts().sort_index()

    distribution = [
        {
            "duracao_semanas": int(weeks),
            "episodios": int(count),
        }
        for weeks, count in frequency.items()
    ]

    if sum(row["episodios"] for row in distribution) != EXPECTED_EPISODES:
        raise ValueError("Distribuição dos episódios não preservou a quantidade total.")

    return {
        "schema_version": SCHEMA_VERSION,
        "period": PERIOD_RISK,
        "source": [source_path(EPISODES_FILE)],
        "summary": summary,
        "distribution": distribution,
    }


def validate_climate_structure(
    dataframe: pd.DataFrame,
    *,
    regional: bool,
) -> None:
    """Valida variáveis e lags dos contratos climáticos."""
    variables = set(dataframe["variavel_climatica"].unique())

    if variables != set(CLIMATE_VARIABLES):
        raise ValueError("Conjunto inesperado de variáveis climáticas.")

    lags = set(dataframe["lag_semanas"].astype(int).unique())

    if lags != set(CLIMATE_LAGS):
        raise ValueError("Conjunto inesperado de lags climáticos.")

    key = [
        "variavel_climatica",
        "lag_semanas",
    ]

    if regional:
        validate_regions(dataframe)

        key.insert(
            0,
            "regiao",
        )

    validate_unique_key(
        dataframe,
        columns=key,
        label="Clima regional" if regional else "Clima nacional",
    )


def build_climate_national() -> dict[str, Any]:
    """Constrói associações climáticas nacionais por lag."""
    dataframe = load_csv(
        CLIMATE_NATIONAL_FILE,
        required_columns={
            "variavel_climatica",
            "lag_semanas",
            "municipios_correlacao_valida",
            "correlacao_mediana",
            "correlacao_p25",
            "correlacao_p75",
        },
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_CLIMATE_NATIONAL_ROWS,
        label="Clima nacional",
    )

    validate_climate_structure(
        dataframe,
        regional=False,
    )

    variable_order = {
        variable: index for index, variable in enumerate(CLIMATE_VARIABLES)
    }

    dataframe["_variable_order"] = dataframe["variavel_climatica"].map(variable_order)

    dataframe = (
        dataframe.sort_values(
            [
                "_variable_order",
                "lag_semanas",
            ],
            kind="stable",
        )
        .drop(columns=["_variable_order"])
        .reset_index(drop=True)
    )

    return build_table_contract(
        dataframe=dataframe,
        period=PERIOD_HISTORICAL,
        source=CLIMATE_NATIONAL_FILE,
    )


def build_climate_regional() -> dict[str, Any]:
    """Constrói associações climáticas regionais por lag."""
    dataframe = load_csv(
        CLIMATE_REGIONAL_FILE,
        required_columns={
            "regiao",
            "variavel_climatica",
            "lag_semanas",
            "municipios_correlacao_valida",
            "correlacao_mediana",
            "correlacao_p25",
            "correlacao_p75",
        },
    )

    validate_row_count(
        dataframe,
        expected=EXPECTED_CLIMATE_REGIONAL_ROWS,
        label="Clima regional",
    )

    validate_climate_structure(
        dataframe,
        regional=True,
    )

    region_order = {region: index for index, region in enumerate(REGIONS)}

    variable_order = {
        variable: index for index, variable in enumerate(CLIMATE_VARIABLES)
    }

    dataframe["_region_order"] = dataframe["regiao"].map(region_order)

    dataframe["_variable_order"] = dataframe["variavel_climatica"].map(variable_order)

    dataframe = (
        dataframe.sort_values(
            [
                "_region_order",
                "_variable_order",
                "lag_semanas",
            ],
            kind="stable",
        )
        .drop(
            columns=[
                "_region_order",
                "_variable_order",
            ]
        )
        .reset_index(drop=True)
    )

    return build_table_contract(
        dataframe=dataframe,
        period=PERIOD_HISTORICAL,
        source=CLIMATE_REGIONAL_FILE,
    )


def validate_cross_contracts(
    contracts: dict[Path, dict[str, Any]],
) -> None:
    """Valida invariantes entre os contratos históricos."""
    annual = contracts[SERVING_DIR / "panorama" / "annual.json"]

    weekly = contracts[SERVING_DIR / "panorama" / "weekly.json"]

    municipalities = contracts[SERVING_DIR / "spatial" / "municipalities.json"]

    risk_municipalities = contracts[
        SERVING_DIR / "risk_dynamics" / "municipalities.json"
    ]

    municipality_index = contracts[SERVING_DIR / "municipality" / "index.json"]

    episode_duration = contracts[
        SERVING_DIR / "risk_dynamics" / "episode_duration.json"
    ]

    climate_national = contracts[SERVING_DIR / "climate" / "national_lags.json"]

    climate_regional = contracts[SERVING_DIR / "climate" / "regional_lags.json"]

    annual_cases = sum(int(row["casos_provaveis"]) for row in annual["data"])

    weekly_cases = sum(int(row["casos_provaveis"]) for row in weekly["data"])

    if annual_cases != 16_294_913:
        raise ValueError("Panorama anual não preservou o total de casos.")

    if weekly_cases != 16_294_913:
        raise ValueError("Panorama semanal não preservou o total de casos.")

    if municipalities["count"] != EXPECTED_MUNICIPALITIES:
        raise ValueError("Cobertura municipal espacial divergente.")

    if risk_municipalities["count"] != EXPECTED_RISK_MUNICIPALITIES:
        raise ValueError("Cobertura municipal de risco divergente.")

    if municipality_index["count"] != EXPECTED_MUNICIPALITIES:
        raise ValueError("Cobertura do índice municipal divergente.")

    if municipality_index["risk_history"]["available"] != EXPECTED_RISK_MUNICIPALITIES:
        raise ValueError("Cobertura de risco no índice municipal divergente.")

    if (
        municipality_index["risk_history"]["unavailable"]
        != EXPECTED_RISK_UNAVAILABLE_MUNICIPALITIES
    ):
        raise ValueError("Ausências de risco no índice municipal divergentes.")

    if episode_duration["summary"]["quantidade_episodios"] != EXPECTED_EPISODES:
        raise ValueError("Quantidade de episódios divergente.")

    if episode_duration["summary"]["semanas_risco"] != EXPECTED_RISK_WEEKS:
        raise ValueError("Quantidade de semanas em risco divergente.")

    if climate_national["count"] != EXPECTED_CLIMATE_NATIONAL_ROWS:
        raise ValueError("Contrato climático nacional divergente.")

    if climate_regional["count"] != EXPECTED_CLIMATE_REGIONAL_ROWS:
        raise ValueError("Contrato climático regional divergente.")


def generate_serving() -> list[Path]:
    """Gera todos os contratos históricos desta etapa."""
    spatial_municipalities = build_spatial_municipalities()

    risk_municipalities = build_risk_municipalities()

    municipality_index = build_municipality_index(
        spatial_municipalities,
        risk_municipalities,
    )

    contracts = {
        SERVING_DIR / "panorama" / "annual.json": build_panorama_annual(),
        SERVING_DIR / "panorama" / "weekly.json": build_panorama_weekly(),
        SERVING_DIR / "seasonality" / "national.json": build_seasonality_national(),
        SERVING_DIR / "seasonality" / "regional.json": build_seasonality_regional(),
        SERVING_DIR / "spatial" / "regions.json": build_spatial_regions(),
        SERVING_DIR / "spatial" / "states.json": build_spatial_states(),
        SERVING_DIR / "spatial" / "municipalities.json": spatial_municipalities,
        SERVING_DIR / "risk_dynamics" / "weekly.json": build_risk_weekly(),
        SERVING_DIR / "risk_dynamics" / "municipalities.json": risk_municipalities,
        SERVING_DIR
        / "risk_dynamics"
        / "episode_duration.json": build_episode_duration(),
        SERVING_DIR / "climate" / "national_lags.json": build_climate_national(),
        SERVING_DIR / "climate" / "regional_lags.json": build_climate_regional(),
        SERVING_DIR / "municipality" / "index.json": municipality_index,
    }

    validate_cross_contracts(contracts)

    for path, payload in contracts.items():
        write_json(
            path,
            payload,
        )

    return list(contracts)


def print_summary(
    outputs: list[Path],
) -> None:
    """Exibe resumo da geração dos contratos históricos."""
    print("=" * 108)

    print("SERVING — HISTÓRICO")

    print("=" * 108)

    print()

    print(f"Arquivos gerados: {len(outputs)}")

    print()

    total_size = 0

    for path in outputs:
        size = path.stat().st_size

        total_size += size

        print(f"{source_path(path):<76} {size:>14,} bytes")

    print()

    print(f"Tamanho total: {total_size:,} bytes")

    print()

    print("STATUS: SERVING HISTÓRICO GERADO E VALIDADO")


def main() -> None:
    """Executa a geração do serving histórico."""
    outputs = generate_serving()

    print_summary(outputs)


if __name__ == "__main__":
    main()
