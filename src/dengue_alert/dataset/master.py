"""Construção do painel municipal semanal integrado."""

from pathlib import Path

import pandas as pd

from dengue_alert.config.paths import (
    CLIMATE_SPATIAL_MAPPING,
    DENGUE_WEEKLY_POPULATION,
    ERA5_WEEKLY_COMBINATIONS,
    MASTER_PANEL,
    MUNICIPALITY_CLIMATE_COMBINATION_MAP,
)

EPIDEMIOLOGICAL_KEY = [
    "codigo_ibge_7",
    "ano_epidemiologico",
    "semana_epidemiologica",
]

CLIMATE_KEY = [
    "combo_id",
    "ano_epidemiologico",
    "semana_epidemiologica",
]


def normalize_ibge_code(series: pd.Series) -> pd.Series:
    """Normaliza códigos IBGE municipais como texto de sete dígitos."""
    return series.astype("string").str.strip().str.zfill(7)


def validate_unique_key(
    dataframe: pd.DataFrame,
    columns: list[str],
    dataset_name: str,
) -> None:
    """Impede a integração quando uma chave esperada como única é duplicada."""
    duplicates = dataframe.duplicated(columns).sum()

    if duplicates:
        raise ValueError(
            f"{dataset_name} contém {duplicates:,} chaves duplicadas em {columns}."
        )


def build_master_panel(
    epidemiology: pd.DataFrame,
    spatial_mapping: pd.DataFrame,
    combination_mapping: pd.DataFrame,
    climate: pd.DataFrame,
) -> pd.DataFrame:
    """Integra epidemiologia, população, mapeamento espacial e clima semanal."""
    epidemiology = epidemiology.copy()
    spatial_mapping = spatial_mapping.copy()
    combination_mapping = combination_mapping.copy()
    climate = climate.copy()

    epidemiology["codigo_ibge_7"] = normalize_ibge_code(epidemiology["codigo_ibge_7"])
    spatial_mapping["codigo_ibge_7"] = normalize_ibge_code(
        spatial_mapping["codigo_ibge_7"]
    )
    combination_mapping["codigo_ibge_7"] = normalize_ibge_code(
        combination_mapping["codigo_ibge_7"]
    )

    combination_mapping["combo_id"] = combination_mapping["combo_id"].astype("Int64")
    climate["combo_id"] = climate["combo_id"].astype("Int64")

    validate_unique_key(
        epidemiology,
        EPIDEMIOLOGICAL_KEY,
        "Base epidemiológica",
    )
    validate_unique_key(
        spatial_mapping,
        ["codigo_ibge_7"],
        "Mapeamento espacial",
    )
    validate_unique_key(
        combination_mapping,
        ["codigo_ibge_7"],
        "Mapeamento município-combo",
    )
    validate_unique_key(
        climate,
        CLIMATE_KEY,
        "Base climática",
    )

    original_rows = len(epidemiology)

    spatial_columns = [
        "codigo_ibge_7",
        "timezone_iana",
        "latitude_sede",
        "longitude_sede",
        "latitude_grid_era5_final",
        "longitude_grid_era5_final",
        "distancia_sede_grid_final_km",
        "metodo_selecao_grid",
        "modelavel_era5_land",
        "motivo_exclusao",
    ]

    panel = epidemiology.merge(
        spatial_mapping[spatial_columns],
        on="codigo_ibge_7",
        how="left",
        validate="many_to_one",
    )

    if panel["modelavel_era5_land"].isna().any():
        missing = sorted(
            panel.loc[
                panel["modelavel_era5_land"].isna(),
                "codigo_ibge_7",
            ].unique()
        )
        raise ValueError(f"Unidades epidemiológicas sem mapeamento espacial: {missing}")

    panel = panel.merge(
        combination_mapping[
            [
                "codigo_ibge_7",
                "combo_id",
            ]
        ],
        on="codigo_ibge_7",
        how="left",
        validate="many_to_one",
    )

    panel["combo_id"] = panel["combo_id"].astype("Int64")

    modelable_without_combo = panel["modelavel_era5_land"] & panel["combo_id"].isna()

    if modelable_without_combo.any():
        missing = sorted(
            panel.loc[
                modelable_without_combo,
                "codigo_ibge_7",
            ].unique()
        )
        raise ValueError(f"Unidades modeláveis sem combo climático: {missing}")

    non_modelable_with_combo = ~panel["modelavel_era5_land"] & panel["combo_id"].notna()

    if non_modelable_with_combo.any():
        invalid = sorted(
            panel.loc[
                non_modelable_with_combo,
                "codigo_ibge_7",
            ].unique()
        )
        raise ValueError(
            f"Unidades não modeláveis associadas a combo climático: {invalid}"
        )

    climate_columns = [
        "combo_id",
        "ano_epidemiologico",
        "semana_epidemiologica",
        "horas_esperadas",
        "temperatura_media_c",
        "temperatura_min_c",
        "temperatura_max_c",
        "ponto_orvalho_medio_c",
        "umidade_relativa_media_pct",
        "precipitacao_total_mm",
    ]

    panel = panel.merge(
        climate[climate_columns],
        on=CLIMATE_KEY,
        how="left",
        validate="many_to_one",
        indicator="_merge_climate",
    )

    panel["clima_disponivel"] = panel["_merge_climate"].eq("both")
    panel = panel.drop(columns="_merge_climate")

    modelable_without_climate = (
        panel["modelavel_era5_land"] & ~panel["clima_disponivel"]
    )

    if modelable_without_climate.any():
        affected = panel.loc[
            modelable_without_climate,
            [
                "codigo_ibge_7",
                "ano_epidemiologico",
                "semana_epidemiologica",
            ],
        ]

        raise ValueError(
            "Existem unidades modeláveis sem dados climáticos. "
            f"Primeiros registros:\n{affected.head().to_string(index=False)}"
        )

    non_modelable_with_climate = (
        ~panel["modelavel_era5_land"] & panel["clima_disponivel"]
    )

    if non_modelable_with_climate.any():
        raise ValueError(
            "Uma unidade marcada como não modelável recebeu dados climáticos."
        )

    if len(panel) != original_rows:
        raise ValueError(
            "A integração alterou a quantidade de linhas epidemiológicas: "
            f"{original_rows:,} -> {len(panel):,}."
        )

    validate_unique_key(
        panel,
        EPIDEMIOLOGICAL_KEY,
        "Painel mestre",
    )

    return panel


def load_master_panel_inputs() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """Carrega os quatro artefatos necessários para construir o painel."""
    epidemiology = pd.read_parquet(DENGUE_WEEKLY_POPULATION)

    spatial_mapping = pd.read_csv(
        CLIMATE_SPATIAL_MAPPING,
        dtype={"codigo_ibge_7": "string"},
        usecols=[
            "codigo_ibge_7",
            "timezone_iana",
            "latitude_sede",
            "longitude_sede",
            "latitude_grid_era5_final",
            "longitude_grid_era5_final",
            "distancia_sede_grid_final_km",
            "metodo_selecao_grid",
            "modelavel_era5_land",
            "motivo_exclusao",
        ],
    )

    combination_mapping = pd.read_csv(
        MUNICIPALITY_CLIMATE_COMBINATION_MAP,
        dtype={"codigo_ibge_7": "string"},
        usecols=[
            "codigo_ibge_7",
            "combo_id",
        ],
    )

    climate = pd.read_parquet(
        ERA5_WEEKLY_COMBINATIONS,
        columns=[
            "combo_id",
            "ano_epidemiologico",
            "semana_epidemiologica",
            "horas_esperadas",
            "temperatura_media_c",
            "temperatura_min_c",
            "temperatura_max_c",
            "ponto_orvalho_medio_c",
            "umidade_relativa_media_pct",
            "precipitacao_total_mm",
        ],
    )

    return (
        epidemiology,
        spatial_mapping,
        combination_mapping,
        climate,
    )

    climate = pd.read_parquet(ERA5_WEEKLY_COMBINATIONS)

    return (
        epidemiology,
        spatial_mapping,
        combination_mapping,
        climate,
    )


def generate_master_panel(
    destination: Path = MASTER_PANEL,
) -> pd.DataFrame:
    """Constrói, valida e grava o painel mestre em Parquet."""
    (
        epidemiology,
        spatial_mapping,
        combination_mapping,
        climate,
    ) = load_master_panel_inputs()

    panel = build_master_panel(
        epidemiology=epidemiology,
        spatial_mapping=spatial_mapping,
        combination_mapping=combination_mapping,
        climate=climate,
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    panel.to_parquet(
        destination,
        index=False,
    )

    return panel
