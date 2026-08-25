"""Inspeciona os principais artefatos intermediários do projeto."""

import pandas as pd
import pyarrow.parquet as pq

from dengue_alert.config.paths import (
    CLIMATE_COMBINATIONS,
    CLIMATE_EXCLUSIONS,
    CLIMATE_SPATIAL_MAPPING,
    DENGUE_WEEKLY_POPULATION,
    EPIDEMIOLOGICAL_CALENDAR,
    ERA5_WEEKLY_COMBINATIONS,
    MUNICIPAL_COORDINATES,
    MUNICIPAL_TIMEZONES,
    MUNICIPALITY_CLIMATE_COMBINATION_MAP,
    POPULATION_2016_2025,
)


PARQUETS = [
    DENGUE_WEEKLY_POPULATION,
    ERA5_WEEKLY_COMBINATIONS,
]

CSVS = [
    EPIDEMIOLOGICAL_CALENDAR,
    POPULATION_2016_2025,
    MUNICIPAL_COORDINATES,
    MUNICIPAL_TIMEZONES,
    CLIMATE_SPATIAL_MAPPING,
    CLIMATE_EXCLUSIONS,
    CLIMATE_COMBINATIONS,
    MUNICIPALITY_CLIMATE_COMBINATION_MAP,
]


def inspecionar_parquet(caminho):
    arquivo = pq.ParquetFile(caminho)

    print("=" * 100)
    print(caminho.name)
    print(f"Linhas: {arquivo.metadata.num_rows:,}")
    print(f"Colunas: {arquivo.metadata.num_columns}")
    print("Esquema:")
    print(arquivo.schema_arrow)


def inspecionar_csv(caminho):
    df = pd.read_csv(caminho)

    print("=" * 100)
    print(caminho.name)
    print(f"Linhas: {len(df):,}")
    print(f"Colunas: {len(df.columns)}")
    print("Colunas e tipos:")
    print(df.dtypes.to_string())


def main():
    print("\nPARQUETS\n")

    for caminho in PARQUETS:
        inspecionar_parquet(caminho)

    print("\nCSVS\n")

    for caminho in CSVS:
        inspecionar_csv(caminho)


if __name__ == "__main__":
    main()