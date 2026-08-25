"""Gera os contratos de serving de metadata e qualidade do Dengue Alert."""

import json
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = "1.0"
HISTORICAL_PERIOD = "2016-2025"

FUNNEL_AUDIT_FILE = (
    PROJECT_ROOT / "reports" / "audits" / "auditoria_funil_sinan_2016_2025.json"
)

MASTER_AUDIT_FILE = PROJECT_ROOT / "reports" / "audits" / "auditoria_painel_mestre.json"

KEYS_AUDIT_FILE = (
    PROJECT_ROOT / "reports" / "audits" / "auditoria_chaves_painel_mestre.json"
)

PANORAMA_AUDIT_FILE = (
    PROJECT_ROOT / "reports" / "audits" / "panorama_nacional_2016_2025.json"
)

SPATIAL_MUNICIPAL_FILE = (
    PROJECT_ROOT
    / "reports"
    / "audits"
    / "distribuicao_espacial_municipio_periodo_2016_2025.csv"
)

MASTER_PANEL_FILE = (
    PROJECT_ROOT / "data" / "processed" / "painel_municipal_semanal_2016_2025.parquet"
)

SERVING_ROOT = PROJECT_ROOT / "data" / "serving"

METADATA_DIR = SERVING_ROOT / "metadata"

QUALITY_DIR = SERVING_ROOT / "quality"

EXPECTED_TERRITORIES = 5_571
EXPECTED_CLIMATE_TERRITORIES = 5_570
EXPECTED_PANEL_ROWS = 2_907_593
EXPECTED_CLIMATE_ROWS_AVAILABLE = 2_907_071
EXPECTED_CLIMATE_ROWS_UNAVAILABLE = 522
EXPECTED_CASES = 16_294_913
EXPECTED_RAW_SINAN_RECORDS = 19_336_281
EXPECTED_FILTERED_SINAN_RECORDS = 16_294_945
EXPECTED_ZERO_FILLED_ROWS = 2_186_284
EXPECTED_CLIMATE_COMBOS = 5_213
EXPECTED_CLIMATE_GRID_POINTS = 5_203


def load_json(
    path: Path,
) -> dict[str, Any]:
    """Carrega um arquivo JSON e valida sua existência."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(
        data,
        dict,
    ):
        raise TypeError(f"O arquivo não contém um objeto JSON: {path}")

    return data


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    """Serializa JSON determinístico, UTF-8 e sem NaN."""
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


def source_path(
    path: Path,
) -> str:
    """Retorna caminho relativo à raiz usando barras portáveis."""
    return path.relative_to(PROJECT_ROOT).as_posix()


def validate_source_files() -> None:
    """Valida a presença de todas as fontes necessárias."""
    required_files = [
        FUNNEL_AUDIT_FILE,
        MASTER_AUDIT_FILE,
        KEYS_AUDIT_FILE,
        PANORAMA_AUDIT_FILE,
        SPATIAL_MUNICIPAL_FILE,
        MASTER_PANEL_FILE,
    ]

    missing = [str(path) for path in required_files if not path.exists()]

    if missing:
        raise FileNotFoundError(
            "Arquivos obrigatórios ausentes:\n" + "\n".join(missing)
        )


def build_territories() -> dict[str, Any]:
    """Constrói o índice territorial compartilhado."""
    dataframe = pd.read_csv(
        SPATIAL_MUNICIPAL_FILE,
        dtype={
            "codigo_ibge_7": "string",
            "codigo_uf_ibge": "string",
        },
    )

    required_columns = {
        "codigo_ibge_7",
        "nome_municipio_ibge",
        "codigo_uf_ibge",
        "nome_uf_ibge",
        "regiao",
        "anos_disponiveis",
    }

    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError("Colunas territoriais ausentes: " + ", ".join(sorted(missing)))

    if len(dataframe) != EXPECTED_TERRITORIES:
        raise ValueError(
            "Quantidade inesperada de unidades territoriais. "
            f"Esperado: {EXPECTED_TERRITORIES:,}; "
            f"obtido: {len(dataframe):,}."
        )

    if dataframe["codigo_ibge_7"].isna().any():
        raise ValueError("Existem códigos IBGE ausentes.")

    if dataframe["codigo_ibge_7"].duplicated().any():
        raise ValueError("Existem códigos IBGE duplicados.")

    dataframe["codigo_ibge_7"] = dataframe["codigo_ibge_7"].str.strip().str.zfill(7)

    dataframe["codigo_uf_ibge"] = dataframe["codigo_uf_ibge"].str.strip().str.zfill(2)

    dataframe = dataframe.sort_values("codigo_ibge_7")

    data = []

    for row in dataframe.itertuples(index=False):
        data.append(
            {
                "codigo_ibge_7": str(row.codigo_ibge_7),
                "nome_municipio": str(row.nome_municipio_ibge),
                "codigo_uf_ibge": str(row.codigo_uf_ibge),
                "nome_uf": str(row.nome_uf_ibge),
                "regiao": str(row.regiao),
                "anos_disponiveis": int(row.anos_disponiveis),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "period": HISTORICAL_PERIOD,
        "source": [source_path(SPATIAL_MUNICIPAL_FILE)],
        "count": len(data),
        "data": data,
    }


def build_temporal_coverage(
    funnel_audit: dict[str, Any],
    panorama_audit: dict[str, Any],
) -> dict[str, Any]:
    """Constrói metadados de cobertura temporal."""
    years = panorama_audit["painel_mestre"]["anos"]

    weeks = panorama_audit["painel_mestre"]["semanas_nacionais"]

    years_with_53_weeks = funnel_audit["grade_epidemiologica"]["anos_com_53_semanas"]

    if years != list(
        range(
            2016,
            2026,
        )
    ):
        raise ValueError(f"Anos históricos inesperados: {years}")

    if int(weeks) != 522:
        raise ValueError("Quantidade inesperada de semanas nacionais.")

    if years_with_53_weeks != [
        2020,
        2025,
    ]:
        raise ValueError("Anos com 53 semanas divergentes do esperado.")

    return {
        "schema_version": SCHEMA_VERSION,
        "period": HISTORICAL_PERIOD,
        "source": [
            source_path(PANORAMA_AUDIT_FILE),
            source_path(FUNNEL_AUDIT_FILE),
        ],
        "data": {
            "periodo_historico": HISTORICAL_PERIOD,
            "anos": [int(year) for year in years],
            "semanas_nacionais": int(weeks),
            "anos_com_53_semanas": [int(year) for year in years_with_53_weeks],
            "regra_semana_epidemiologica": funnel_audit["grade_epidemiologica"][
                "regra_semana"
            ],
        },
    }


def build_quality_overview(
    funnel_audit: dict[str, Any],
    master_audit: dict[str, Any],
    keys_audit: dict[str, Any],
) -> dict[str, Any]:
    """Constrói os principais indicadores da página de qualidade."""
    data = {
        "registros_sinan_brutos": int(
            funnel_audit["entrada_sinan"]["registros_brutos"]
        ),
        "registros_sinan_mantidos_apos_filtros": int(
            funnel_audit["processamento_v2"]["registros_mantidos_apos_filtros"]
        ),
        "casos_finais_preservados": int(master_audit["painel"]["casos_provaveis"]),
        "unidades_territoriais": int(master_audit["painel"]["municipios"]),
        "municipio_semanas": int(master_audit["painel"]["linhas"]),
        "linhas_zero_fill": int(
            funnel_audit["grade_epidemiologica"]["linhas_preenchidas_com_zero"]
        ),
        "unidades_com_cobertura_climatica": int(
            keys_audit["mapeamento_climatico"]["unidades"]
        ),
        "municipio_semanas_com_clima": int(master_audit["clima"]["linhas_com_clima"]),
        "municipio_semanas_sem_clima": int(master_audit["clima"]["linhas_sem_clima"]),
    }

    expected = {
        "registros_sinan_brutos": EXPECTED_RAW_SINAN_RECORDS,
        "registros_sinan_mantidos_apos_filtros": EXPECTED_FILTERED_SINAN_RECORDS,
        "casos_finais_preservados": EXPECTED_CASES,
        "unidades_territoriais": EXPECTED_TERRITORIES,
        "municipio_semanas": EXPECTED_PANEL_ROWS,
        "linhas_zero_fill": EXPECTED_ZERO_FILLED_ROWS,
        "unidades_com_cobertura_climatica": EXPECTED_CLIMATE_TERRITORIES,
        "municipio_semanas_com_clima": EXPECTED_CLIMATE_ROWS_AVAILABLE,
        "municipio_semanas_sem_clima": EXPECTED_CLIMATE_ROWS_UNAVAILABLE,
    }

    if data != expected:
        raise ValueError(
            "Indicadores de overview divergiram dos valores auditados.\n"
            f"Obtido: {data}\n"
            f"Esperado: {expected}"
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "period": HISTORICAL_PERIOD,
        "source": [
            source_path(FUNNEL_AUDIT_FILE),
            source_path(MASTER_AUDIT_FILE),
            source_path(KEYS_AUDIT_FILE),
        ],
        "data": data,
    }


def build_sinan_pipeline(
    funnel_audit: dict[str, Any],
) -> dict[str, Any]:
    """Constrói o contrato visual do funil SINAN."""
    processing = funnel_audit["processamento_v2"]

    filters = processing["filtros_documentados"]

    steps = [
        {
            "id": "duplicate_check",
            "label": "Verificação de duplicidade lógica",
            "field": processing["duplicidade_logica"]["campo"],
            "operation": "validation",
            "records_removed": None,
            "note": processing["duplicidade_logica"]["observacao"],
        },
        {
            "id": "classi_fin_5",
            "label": "Remoção de classificação final não elegível",
            "field": "CLASSI_FIN",
            "operation": "filter",
            "records_removed": int(filters["classi_fin_5"]["registros_removidos"]),
        },
        {
            "id": "invalid_municipality",
            "label": "Município de residência inválido",
            "operation": "filter",
            "records_removed": int(
                filters["municipio_invalido"]["registros_removidos"]
            ),
        },
        {
            "id": "invalid_sem_pri",
            "label": "Semana epidemiológica inválida",
            "field": "SEM_PRI",
            "operation": "filter",
            "records_removed": int(filters["sem_pri_invalida"]["registros_removidos"]),
        },
        {
            "id": "outside_period",
            "label": "Registro fora do período 2016–2025",
            "operation": "filter",
            "records_removed": int(
                filters["fora_periodo_2016_2025"]["registros_removidos"]
            ),
        },
    ]

    documented_removals = sum(
        int(step["records_removed"])
        for step in steps
        if step["records_removed"] is not None
    )

    raw_records = int(funnel_audit["entrada_sinan"]["registros_brutos"])

    filtered_records = int(processing["registros_mantidos_apos_filtros"])

    if raw_records - documented_removals != filtered_records:
        raise ValueError("O funil aritmético do SINAN não fecha.")

    territorial_result = funnel_audit["resultado_apos_normalizacao_territorial"]

    zero_fill = funnel_audit["grade_epidemiologica"]

    return {
        "schema_version": SCHEMA_VERSION,
        "period": HISTORICAL_PERIOD,
        "source": [source_path(FUNNEL_AUDIT_FILE)],
        "data": {
            "registros_brutos": raw_records,
            "etapas": steps,
            "total_remocoes_documentadas": documented_removals,
            "registros_mantidos_apos_filtros": filtered_records,
            "grupos_antes_normalizacao": int(
                processing["grupos_municipio_ano_semana_antes_normalizacao_territorial"]
            ),
            "codigos_sinan_iniciais": int(processing["codigos_sinan_6_digitos"]),
            "casos_finais": int(territorial_result["casos_preservados"]),
            "zero_fill": {
                "linhas_observadas": int(
                    zero_fill["linhas_observadas_antes_zero_fill"]
                ),
                "linhas_finais": int(zero_fill["linhas_apos_zero_fill"]),
                "linhas_preenchidas_com_zero": int(
                    zero_fill["linhas_preenchidas_com_zero"]
                ),
                "casos_antes": int(zero_fill["casos_antes_zero_fill"]),
                "casos_depois": int(zero_fill["casos_depois_zero_fill"]),
            },
        },
    }


def build_territorial_coverage(
    funnel_audit: dict[str, Any],
    master_audit: dict[str, Any],
) -> dict[str, Any]:
    """Constrói o contrato de cobertura e conciliação territorial."""
    reconciliation = funnel_audit["conciliacao_territorial"]

    first_match = reconciliation["primeiro_cruzamento"]

    federal_district = reconciliation["distrito_federal"]

    residual = reconciliation["codigos_residuais_nao_municipais"]

    final_result = funnel_audit["resultado_apos_normalizacao_territorial"]

    final_territories = int(master_audit["painel"]["municipios"])

    if final_territories != EXPECTED_TERRITORIES:
        raise ValueError("Cobertura territorial final inesperada.")

    return {
        "schema_version": SCHEMA_VERSION,
        "period": HISTORICAL_PERIOD,
        "source": [
            source_path(FUNNEL_AUDIT_FILE),
            source_path(MASTER_AUDIT_FILE),
        ],
        "data": {
            "referencia": reconciliation["referencia"],
            "unidades_territoriais_referencia": int(
                reconciliation["unidades_territoriais_referencia"]
            ),
            "composicao_referencia": reconciliation["composicao_referencia"],
            "codigos_sinan_iniciais": int(first_match["codigos_sinan_distintos"]),
            "codigos_associados_diretamente": int(
                first_match["codigos_associados_diretamente"]
            ),
            "codigos_nao_associados_inicialmente": int(
                first_match["codigos_nao_associados_diretamente"]
            ),
            "casos_nao_associados_inicialmente": int(
                first_match["casos_em_codigos_nao_associados"]
            ),
            "distrito_federal": {
                "codigos_subdivisoes": int(
                    federal_district["codigos_subdivisoes_identificados"]
                ),
                "casos_preservados": int(federal_district["casos_preservados"]),
                "codigo_ibge_7_destino": str(federal_district["codigo_ibge_7_destino"]),
                "nome_destino": federal_district["nome_destino"],
            },
            "residuais_nao_municipais": {
                "quantidade_codigos": int(residual["quantidade_codigos"]),
                "casos_excluidos": int(residual["casos_excluidos"]),
            },
            "resultado_final": {
                "unidades_territoriais": final_territories,
                "unidades_com_registro_original": int(
                    final_result["codigos_sinan_representados"]
                ),
                "unidades_sem_registro_original": int(
                    final_result["unidades_ibge_sem_registro_dengue"]
                ),
                "casos_preservados": int(final_result["casos_preservados"]),
            },
        },
    }


def load_population_panel() -> pd.DataFrame:
    """Carrega apenas as colunas necessárias à auditoria populacional."""
    columns = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "populacao",
        "tipo_populacao",
        "ano_referencia_populacao",
    ]

    return pd.read_parquet(
        MASTER_PANEL_FILE,
        columns=columns,
    )


def build_population_coverage(
    master_audit: dict[str, Any],
) -> dict[str, Any]:
    """Constrói o contrato de cobertura populacional."""
    dataframe = load_population_panel()

    missing_population = int(dataframe["populacao"].isna().sum())

    nonpositive_population = int(dataframe["populacao"].le(0).sum())

    if missing_population != int(master_audit["populacao"]["ausentes"]):
        raise ValueError("Divergência na quantidade de populações ausentes.")

    if nonpositive_population != int(master_audit["populacao"]["nao_positivas"]):
        raise ValueError("Divergência na quantidade de populações não positivas.")

    year_rows = []

    for year, group in dataframe.groupby(
        "ano_epidemiologico",
        sort=True,
    ):
        reference_years = sorted(
            {int(value) for value in group["ano_referencia_populacao"].dropna()}
        )

        population_types = sorted(
            {str(value) for value in group["tipo_populacao"].dropna()}
        )

        territories = int(group["codigo_ibge_7"].nunique())

        year_rows.append(
            {
                "ano_epidemiologico": int(year),
                "anos_referencia_populacao": reference_years,
                "tipos_populacao": population_types,
                "unidades_territoriais": territories,
                "linhas_sem_populacao": int(group["populacao"].isna().sum()),
                "linhas_populacao_nao_positiva": int(group["populacao"].le(0).sum()),
            }
        )

    year_2023 = next(row for row in year_rows if row["ano_epidemiologico"] == 2023)

    uses_2022_reference = year_2023["anos_referencia_populacao"] == [2022]

    if not uses_2022_reference:
        raise ValueError("A referência populacional de 2023 não corresponde a 2022.")

    return {
        "schema_version": SCHEMA_VERSION,
        "period": HISTORICAL_PERIOD,
        "source": [
            source_path(MASTER_PANEL_FILE),
            source_path(MASTER_AUDIT_FILE),
        ],
        "data": {
            "linhas_sem_populacao": missing_population,
            "linhas_populacao_nao_positiva": nonpositive_population,
            "referencia_2023": {
                "ano_epidemiologico": 2023,
                "ano_referencia_populacao": 2022,
                "usa_referencia_censo_2022": uses_2022_reference,
            },
            "observacao_metodologica": (
                "O ano epidemiológico de 2023 utiliza a população "
                "do Censo 2022 como referência. Existe descontinuidade "
                "metodológica entre estimativas anteriores e o Censo 2022."
            ),
            "por_ano": year_rows,
        },
    }


def load_climate_panel() -> pd.DataFrame:
    """Carrega somente colunas necessárias à cobertura climática."""
    columns = [
        "codigo_ibge_7",
        "modelavel_era5_land",
        "metodo_selecao_grid",
        "latitude_grid_era5_final",
        "longitude_grid_era5_final",
        "combo_id",
        "timezone_iana",
        "clima_disponivel",
    ]

    return pd.read_parquet(
        MASTER_PANEL_FILE,
        columns=columns,
    )


def build_climate_coverage(
    master_audit: dict[str, Any],
    keys_audit: dict[str, Any],
) -> dict[str, Any]:
    """Constrói o contrato de cobertura climática."""
    dataframe = load_climate_panel()

    modelable = dataframe.loc[dataframe["modelavel_era5_land"].eq(True)].copy()

    territory_methods = modelable[
        [
            "codigo_ibge_7",
            "metodo_selecao_grid",
        ]
    ].drop_duplicates()

    methods_per_territory = territory_methods.groupby("codigo_ibge_7")[
        "metodo_selecao_grid"
    ].nunique()

    if methods_per_territory.gt(1).any():
        raise ValueError(
            "Uma unidade territorial possui mais de um método de seleção de grade."
        )

    method_counts_series = (
        territory_methods["metodo_selecao_grid"].value_counts(dropna=False).sort_index()
    )

    method_counts = {
        ("ausente" if pd.isna(method) else str(method)): int(count)
        for method, count in method_counts_series.items()
    }

    unique_grid_points = int(
        modelable[
            [
                "latitude_grid_era5_final",
                "longitude_grid_era5_final",
            ]
        ]
        .dropna()
        .drop_duplicates()
        .shape[0]
    )

    unique_combos = int(modelable["combo_id"].dropna().nunique())

    modelable_territories = int(modelable["codigo_ibge_7"].nunique())

    climate_available_rows = int(dataframe["clima_disponivel"].eq(True).sum())

    climate_unavailable_rows = int(dataframe["clima_disponivel"].eq(False).sum())

    if modelable_territories != EXPECTED_CLIMATE_TERRITORIES:
        raise ValueError("Quantidade inesperada de unidades modeláveis.")

    if unique_grid_points != EXPECTED_CLIMATE_GRID_POINTS:
        raise ValueError("Quantidade inesperada de pontos de grade.")

    if unique_combos != EXPECTED_CLIMATE_COMBOS:
        raise ValueError("Quantidade inesperada de combinações grade × timezone.")

    if climate_available_rows != EXPECTED_CLIMATE_ROWS_AVAILABLE:
        raise ValueError("Quantidade inesperada de linhas com clima.")

    if climate_unavailable_rows != EXPECTED_CLIMATE_ROWS_UNAVAILABLE:
        raise ValueError("Quantidade inesperada de linhas sem clima.")

    if unique_combos != int(keys_audit["clima"]["combos"]):
        raise ValueError("Combinações climáticas divergiram da auditoria de chaves.")

    if climate_available_rows != int(master_audit["clima"]["linhas_com_clima"]):
        raise ValueError("Cobertura climática divergiu da auditoria do painel mestre.")

    if climate_unavailable_rows != int(master_audit["clima"]["linhas_sem_clima"]):
        raise ValueError(
            "Ausências climáticas divergiram da auditoria do painel mestre."
        )

    excluded_codes = [
        str(code) for code in keys_audit["cobertura"]["codigos_excluidos"]
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "period": HISTORICAL_PERIOD,
        "source": [
            source_path(MASTER_PANEL_FILE),
            source_path(MASTER_AUDIT_FILE),
            source_path(KEYS_AUDIT_FILE),
        ],
        "data": {
            "unidades_com_mapeamento_climatico": modelable_territories,
            "linhas_climaticas_fonte": int(keys_audit["clima"]["linhas"]),
            "pontos_grade_distintos": unique_grid_points,
            "combinacoes_grade_timezone": unique_combos,
            "municipio_semanas_com_clima": climate_available_rows,
            "municipio_semanas_sem_clima": climate_unavailable_rows,
            "codigos_excluidos": excluded_codes,
            "metodos_selecao_grid": method_counts,
            "observacao": (
                "Os dados climáticos são provenientes do ERA5-Land "
                "e representam reanálise meteorológica, não medições "
                "diretas de estações locais em cada município."
            ),
        },
    }


def validate_cross_contracts(
    territories: dict[str, Any],
    temporal_coverage: dict[str, Any],
    overview: dict[str, Any],
    sinan_pipeline: dict[str, Any],
    territorial_coverage: dict[str, Any],
    population_coverage: dict[str, Any],
    climate_coverage: dict[str, Any],
) -> None:
    """Valida invariantes entre contratos antes da gravação."""
    if territories["count"] != overview["data"]["unidades_territoriais"]:
        raise ValueError("Quantidade territorial divergente entre contratos.")

    if (
        sinan_pipeline["data"]["casos_finais"]
        != overview["data"]["casos_finais_preservados"]
    ):
        raise ValueError("Total de casos divergente entre contratos.")

    if (
        territorial_coverage["data"]["resultado_final"]["casos_preservados"]
        != overview["data"]["casos_finais_preservados"]
    ):
        raise ValueError("Casos territoriais divergentes do overview.")

    if (
        sinan_pipeline["data"]["zero_fill"]["linhas_finais"]
        != overview["data"]["municipio_semanas"]
    ):
        raise ValueError("Quantidade de município-semanas divergente.")

    if (
        climate_coverage["data"]["unidades_com_mapeamento_climatico"]
        != overview["data"]["unidades_com_cobertura_climatica"]
    ):
        raise ValueError("Cobertura climática territorial divergente.")

    if (
        climate_coverage["data"]["municipio_semanas_com_clima"]
        != overview["data"]["municipio_semanas_com_clima"]
    ):
        raise ValueError("Linhas com clima divergentes entre contratos.")

    if (
        climate_coverage["data"]["municipio_semanas_sem_clima"]
        != overview["data"]["municipio_semanas_sem_clima"]
    ):
        raise ValueError("Linhas sem clima divergentes entre contratos.")

    years = temporal_coverage["data"]["anos"]

    population_years = [
        row["ano_epidemiologico"] for row in population_coverage["data"]["por_ano"]
    ]

    if years != population_years:
        raise ValueError("Cobertura temporal populacional divergente.")


def generate_serving() -> list[Path]:
    """Gera todos os contratos de metadata e qualidade."""
    validate_source_files()

    funnel_audit = load_json(FUNNEL_AUDIT_FILE)

    master_audit = load_json(MASTER_AUDIT_FILE)

    keys_audit = load_json(KEYS_AUDIT_FILE)

    panorama_audit = load_json(PANORAMA_AUDIT_FILE)

    territories = build_territories()

    temporal_coverage = build_temporal_coverage(
        funnel_audit,
        panorama_audit,
    )

    overview = build_quality_overview(
        funnel_audit,
        master_audit,
        keys_audit,
    )

    sinan_pipeline = build_sinan_pipeline(funnel_audit)

    territorial_coverage = build_territorial_coverage(
        funnel_audit,
        master_audit,
    )

    population_coverage = build_population_coverage(master_audit)

    climate_coverage = build_climate_coverage(
        master_audit,
        keys_audit,
    )

    validate_cross_contracts(
        territories,
        temporal_coverage,
        overview,
        sinan_pipeline,
        territorial_coverage,
        population_coverage,
        climate_coverage,
    )

    outputs = {
        METADATA_DIR / "territories.json": territories,
        METADATA_DIR / "temporal_coverage.json": temporal_coverage,
        QUALITY_DIR / "overview.json": overview,
        QUALITY_DIR / "sinan_pipeline.json": sinan_pipeline,
        QUALITY_DIR / "territorial_coverage.json": territorial_coverage,
        QUALITY_DIR / "population_coverage.json": population_coverage,
        QUALITY_DIR / "climate_coverage.json": climate_coverage,
    }

    for path, payload in outputs.items():
        write_json(
            path,
            payload,
        )

    return list(outputs)


def print_summary(
    outputs: list[Path],
) -> None:
    """Exibe resumo da geração."""
    print("=" * 100)

    print("SERVING — METADATA E QUALIDADE")

    print("=" * 100)

    print()

    print(f"Arquivos gerados: {len(outputs)}")

    print()

    for path in outputs:
        size = path.stat().st_size

        print(f"{source_path(path):<60} {size:>12,} bytes")

    print()

    total_size = sum(path.stat().st_size for path in outputs)

    print(f"Tamanho total: {total_size:,} bytes")

    print()

    print("STATUS: SERVING DE METADATA E QUALIDADE GERADO E VALIDADO")


def main() -> None:
    """Executa a geração dos contratos."""
    outputs = generate_serving()

    print_summary(outputs)


if __name__ == "__main__":
    main()
