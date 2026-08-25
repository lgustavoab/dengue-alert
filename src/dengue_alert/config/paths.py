"""Caminhos centralizados do projeto Dengue Alert."""

from pathlib import Path

# Raiz do projeto:
# tcc-dengue/
PROJECT_ROOT = Path(__file__).resolve().parents[3]


# Diretórios principais
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
MODELS_DIR = PROJECT_ROOT / "models"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"


# Camadas de dados
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SERVING_DATA_DIR = DATA_DIR / "serving"


# Dados intermediários por domínio
EPIDEMIOLOGY_DIR = INTERIM_DATA_DIR / "epidemiology"
POPULATION_DIR = INTERIM_DATA_DIR / "population"
GEOGRAPHY_DIR = INTERIM_DATA_DIR / "geography"
CLIMATE_DIR = INTERIM_DATA_DIR / "climate"


# Artefatos epidemiológicos
DENGUE_WEEKLY_POPULATION = (
    EPIDEMIOLOGY_DIR / "dengue_semanal_2016_2025_com_populacao.parquet"
)

EPIDEMIOLOGICAL_CALENDAR = EPIDEMIOLOGY_DIR / "calendario_epidemiologico_2016_2025.csv"


# População
POPULATION_2016_2025 = POPULATION_DIR / "populacao_ibge_2016_2025_final.csv"


# Geografia
MUNICIPAL_COORDINATES = GEOGRAPHY_DIR / "coordenadas_municipais_ibge_2025.csv"

MUNICIPAL_TIMEZONES = GEOGRAPHY_DIR / "fusos_horarios_municipios_ibge_2025.csv"


# Clima
CLIMATE_SPATIAL_MAPPING = CLIMATE_DIR / "mapeamento_climatico_era5_final.csv"

CLIMATE_EXCLUSIONS = CLIMATE_DIR / "exclusoes_climaticas.csv"

CLIMATE_COMBINATIONS = CLIMATE_DIR / "combinacoes_grid_timezone.csv"

MUNICIPALITY_CLIMATE_COMBINATION_MAP = CLIMATE_DIR / "mapeamento_unidades_combo_id.csv"

ERA5_WEEKLY_COMBINATIONS = CLIMATE_DIR / "era5_semanal_combinacoes_2016_2025.parquet"


# Futuro produto integrado
MASTER_PANEL = PROCESSED_DATA_DIR / "painel_municipal_semanal_2016_2025.parquet"
