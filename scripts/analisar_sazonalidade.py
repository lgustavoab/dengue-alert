"""Analisa a sazonalidade epidemiológica nacional e regional de 2016 a 2025."""

import json

import numpy as np
import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR

NATIONAL_OUTPUT = (
    REPORTS_DIR / "audits" / "sazonalidade_nacional_semana_epidemiologica_2016_2025.csv"
)

REGIONAL_OUTPUT = (
    REPORTS_DIR / "audits" / "sazonalidade_regional_semana_epidemiologica_2016_2025.csv"
)

REGION_YEAR_WEEK_OUTPUT = (
    REPORTS_DIR / "audits" / "serie_semanal_regional_2016_2025.csv"
)

AUDIT_OUTPUT = REPORTS_DIR / "audits" / "sazonalidade_2016_2025.json"

EXPECTED_ROWS = 2_907_593
EXPECTED_CASES = 16_294_913
EXPECTED_YEARS = tuple(range(2016, 2026))
EXPECTED_TOTAL_WEEKS = 522

YEAR_COLUMN = "ano_epidemiologico"
WEEK_COLUMN = "semana_epidemiologica"
TERRITORY_COLUMN = "codigo_ibge_7"
UF_CODE_COLUMN = "codigo_uf_ibge"
CASES_COLUMN = "casos_provaveis"
POPULATION_COLUMN = "populacao"

REGION_BY_UF_CODE = {
    "11": "Norte",
    "12": "Norte",
    "13": "Norte",
    "14": "Norte",
    "15": "Norte",
    "16": "Norte",
    "17": "Norte",
    "21": "Nordeste",
    "22": "Nordeste",
    "23": "Nordeste",
    "24": "Nordeste",
    "25": "Nordeste",
    "26": "Nordeste",
    "27": "Nordeste",
    "28": "Nordeste",
    "29": "Nordeste",
    "31": "Sudeste",
    "32": "Sudeste",
    "33": "Sudeste",
    "35": "Sudeste",
    "41": "Sul",
    "42": "Sul",
    "43": "Sul",
    "50": "Centro-Oeste",
    "51": "Centro-Oeste",
    "52": "Centro-Oeste",
    "53": "Centro-Oeste",
}

REGION_ORDER = (
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul",
)

REQUIRED_COLUMNS = [
    TERRITORY_COLUMN,
    UF_CODE_COLUMN,
    YEAR_COLUMN,
    WEEK_COLUMN,
    CASES_COLUMN,
    POPULATION_COLUMN,
]


def validate_input(dataframe: pd.DataFrame) -> None:
    """Valida o painel antes da análise de sazonalidade."""
    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas. "
            f"Esperado: {EXPECTED_ROWS:,}; obtido: {len(dataframe):,}."
        )

    total_cases = int(dataframe[CASES_COLUMN].sum())

    if total_cases != EXPECTED_CASES:
        raise ValueError(
            "Total de casos inesperado. "
            f"Esperado: {EXPECTED_CASES:,}; obtido: {total_cases:,}."
        )

    years = tuple(sorted(int(value) for value in dataframe[YEAR_COLUMN].unique()))

    if years != EXPECTED_YEARS:
        raise ValueError(f"Período inesperado: {years}.")

    if dataframe[REQUIRED_COLUMNS].isna().any().any():
        raise ValueError("Existem valores ausentes nas colunas obrigatórias.")

    if dataframe.duplicated(
        subset=[
            TERRITORY_COLUMN,
            YEAR_COLUMN,
            WEEK_COLUMN,
        ]
    ).any():
        raise ValueError("Existem linhas território-ano-semana duplicadas.")

    cases = dataframe[CASES_COLUMN].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    population = dataframe[POPULATION_COLUMN].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    if not np.isfinite(cases).all():
        raise ValueError("Existem valores de casos não finitos.")

    if not np.isfinite(population).all():
        raise ValueError("Existem populações não finitas.")

    if (cases < 0).any():
        raise ValueError("Existem valores negativos de casos.")

    if (population <= 0).any():
        raise ValueError("Existem populações menores ou iguais a zero.")


def add_region(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Adiciona macrorregião a partir do código oficial da UF."""
    output = dataframe.copy()

    uf_code = output[UF_CODE_COLUMN].astype(str).str.zfill(2)

    output["regiao"] = uf_code.map(REGION_BY_UF_CODE)

    if output["regiao"].isna().any():
        unknown = sorted(set(uf_code.loc[output["regiao"].isna()]))

        raise ValueError("Códigos de UF sem região: " + ", ".join(unknown) + ".")

    return output


def build_national_year_week(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Constrói a série nacional ano × semana."""
    population_by_year = (
        dataframe[
            [
                YEAR_COLUMN,
                TERRITORY_COLUMN,
                POPULATION_COLUMN,
            ]
        ]
        .drop_duplicates(
            subset=[
                YEAR_COLUMN,
                TERRITORY_COLUMN,
            ]
        )
        .groupby(
            YEAR_COLUMN,
            as_index=False,
            observed=True,
        )
        .agg(
            populacao_nacional=(
                POPULATION_COLUMN,
                "sum",
            )
        )
    )

    weekly = (
        dataframe.groupby(
            [
                YEAR_COLUMN,
                WEEK_COLUMN,
            ],
            as_index=False,
            observed=True,
        )
        .agg(
            casos_provaveis=(
                CASES_COLUMN,
                "sum",
            )
        )
        .merge(
            population_by_year,
            on=YEAR_COLUMN,
            how="left",
            validate="many_to_one",
        )
    )

    weekly["incidencia_nacional_100mil"] = (
        weekly["casos_provaveis"] / weekly["populacao_nacional"] * 100_000
    )

    return weekly


def build_national_seasonality(
    weekly: pd.DataFrame,
) -> pd.DataFrame:
    """Resume a sazonalidade nacional por semana epidemiológica."""
    result = (
        weekly.groupby(
            WEEK_COLUMN,
            as_index=False,
            observed=True,
        )
        .agg(
            anos_disponiveis=(
                YEAR_COLUMN,
                "nunique",
            ),
            casos_media=(
                "casos_provaveis",
                "mean",
            ),
            casos_mediana=(
                "casos_provaveis",
                "median",
            ),
            casos_minimo=(
                "casos_provaveis",
                "min",
            ),
            casos_maximo=(
                "casos_provaveis",
                "max",
            ),
            incidencia_media_100mil=(
                "incidencia_nacional_100mil",
                "mean",
            ),
            incidencia_mediana_100mil=(
                "incidencia_nacional_100mil",
                "median",
            ),
            incidencia_q25_100mil=(
                "incidencia_nacional_100mil",
                lambda series: series.quantile(0.25),
            ),
            incidencia_q75_100mil=(
                "incidencia_nacional_100mil",
                lambda series: series.quantile(0.75),
            ),
            incidencia_minima_100mil=(
                "incidencia_nacional_100mil",
                "min",
            ),
            incidencia_maxima_100mil=(
                "incidencia_nacional_100mil",
                "max",
            ),
        )
        .sort_values(WEEK_COLUMN)
        .reset_index(drop=True)
    )

    return result


def build_region_population(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula população por região e ano sem repetição semanal."""
    territory_year = dataframe[
        [
            YEAR_COLUMN,
            "regiao",
            TERRITORY_COLUMN,
            POPULATION_COLUMN,
        ]
    ].drop_duplicates(
        subset=[
            YEAR_COLUMN,
            TERRITORY_COLUMN,
        ]
    )

    return territory_year.groupby(
        [
            YEAR_COLUMN,
            "regiao",
        ],
        as_index=False,
        observed=True,
    ).agg(
        populacao_regional=(
            POPULATION_COLUMN,
            "sum",
        ),
        unidades_territoriais=(
            TERRITORY_COLUMN,
            "nunique",
        ),
    )


def build_region_year_week(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Constrói a série epidemiológica semanal por região."""
    population = build_region_population(dataframe)

    regional = (
        dataframe.groupby(
            [
                YEAR_COLUMN,
                WEEK_COLUMN,
                "regiao",
            ],
            as_index=False,
            observed=True,
        )
        .agg(
            casos_provaveis=(
                CASES_COLUMN,
                "sum",
            )
        )
        .merge(
            population,
            on=[
                YEAR_COLUMN,
                "regiao",
            ],
            how="left",
            validate="many_to_one",
        )
    )

    regional["incidencia_regional_100mil"] = (
        regional["casos_provaveis"] / regional["populacao_regional"] * 100_000
    )

    regional["regiao"] = pd.Categorical(
        regional["regiao"],
        categories=REGION_ORDER,
        ordered=True,
    )

    return regional.sort_values(
        [
            YEAR_COLUMN,
            WEEK_COLUMN,
            "regiao",
        ]
    ).reset_index(drop=True)


def build_regional_seasonality(
    regional: pd.DataFrame,
) -> pd.DataFrame:
    """Resume a sazonalidade por região e semana epidemiológica."""
    result = regional.groupby(
        [
            "regiao",
            WEEK_COLUMN,
        ],
        as_index=False,
        observed=True,
    ).agg(
        anos_disponiveis=(
            YEAR_COLUMN,
            "nunique",
        ),
        casos_media=(
            "casos_provaveis",
            "mean",
        ),
        casos_mediana=(
            "casos_provaveis",
            "median",
        ),
        incidencia_media_100mil=(
            "incidencia_regional_100mil",
            "mean",
        ),
        incidencia_mediana_100mil=(
            "incidencia_regional_100mil",
            "median",
        ),
        incidencia_q25_100mil=(
            "incidencia_regional_100mil",
            lambda series: series.quantile(0.25),
        ),
        incidencia_q75_100mil=(
            "incidencia_regional_100mil",
            lambda series: series.quantile(0.75),
        ),
        incidencia_minima_100mil=(
            "incidencia_regional_100mil",
            "min",
        ),
        incidencia_maxima_100mil=(
            "incidencia_regional_100mil",
            "max",
        ),
    )

    result["regiao"] = pd.Categorical(
        result["regiao"],
        categories=REGION_ORDER,
        ordered=True,
    )

    return result.sort_values(
        [
            "regiao",
            WEEK_COLUMN,
        ]
    ).reset_index(drop=True)


def validate_outputs(
    national_weekly: pd.DataFrame,
    national_seasonality: pd.DataFrame,
    regional_weekly: pd.DataFrame,
    regional_seasonality: pd.DataFrame,
) -> None:
    """Valida as agregações sazonais."""
    if len(national_weekly) != EXPECTED_TOTAL_WEEKS:
        raise ValueError("Quantidade inesperada de semanas nacionais.")

    if int(national_weekly["casos_provaveis"].sum()) != EXPECTED_CASES:
        raise ValueError("A série nacional não preservou o total de casos.")

    if int(regional_weekly["casos_provaveis"].sum()) != EXPECTED_CASES:
        raise ValueError("A série regional não preservou o total de casos.")

    if len(national_seasonality) != 53:
        raise ValueError("A sazonalidade nacional não possui semanas 1–53.")

    expected_regional_rows = len(REGION_ORDER) * 53

    if len(regional_seasonality) != expected_regional_rows:
        raise ValueError(
            "Quantidade inesperada de linhas na sazonalidade regional. "
            f"Esperado: {expected_regional_rows}; "
            f"obtido: {len(regional_seasonality)}."
        )

    week_53_years = int(
        national_seasonality.loc[
            national_seasonality[WEEK_COLUMN].eq(53),
            "anos_disponiveis",
        ].iloc[0]
    )

    if week_53_years != 2:
        raise ValueError("A semana 53 deveria existir apenas em 2020 e 2025.")


def build_peak_summary(
    national_seasonality: pd.DataFrame,
    regional_seasonality: pd.DataFrame,
) -> dict:
    """Identifica semanas de maior incidência média e mediana."""
    national_mean_peak = national_seasonality.loc[
        national_seasonality["incidencia_media_100mil"].idxmax()
    ]

    national_median_peak = national_seasonality.loc[
        national_seasonality["incidencia_mediana_100mil"].idxmax()
    ]

    regional_peaks = {}

    for region in REGION_ORDER:
        subset = regional_seasonality.loc[
            regional_seasonality["regiao"].eq(region)
            & regional_seasonality["anos_disponiveis"].ge(5)
        ]

        mean_peak = subset.loc[subset["incidencia_media_100mil"].idxmax()]

        median_peak = subset.loc[subset["incidencia_mediana_100mil"].idxmax()]

        regional_peaks[region] = {
            "semana_maior_incidencia_media": int(mean_peak[WEEK_COLUMN]),
            "incidencia_media_100mil": float(mean_peak["incidencia_media_100mil"]),
            "semana_maior_incidencia_mediana": int(median_peak[WEEK_COLUMN]),
            "incidencia_mediana_100mil": float(
                median_peak["incidencia_mediana_100mil"]
            ),
        }

    return {
        "nacional": {
            "semana_maior_incidencia_media": int(national_mean_peak[WEEK_COLUMN]),
            "incidencia_media_100mil": float(
                national_mean_peak["incidencia_media_100mil"]
            ),
            "semana_maior_incidencia_mediana": int(national_median_peak[WEEK_COLUMN]),
            "incidencia_mediana_100mil": float(
                national_median_peak["incidencia_mediana_100mil"]
            ),
        },
        "regioes": regional_peaks,
    }


def main() -> None:
    """Executa a análise descritiva da sazonalidade."""
    print("=" * 104)
    print("SAZONALIDADE EPIDEMIOLÓGICA — 2016–2025")
    print("=" * 104)

    dataframe = pd.read_parquet(
        MASTER_PANEL,
        columns=REQUIRED_COLUMNS,
    )

    validate_input(dataframe)

    dataframe = add_region(dataframe)

    national_weekly = build_national_year_week(dataframe)

    national_seasonality = build_national_seasonality(national_weekly)

    regional_weekly = build_region_year_week(dataframe)

    regional_seasonality = build_regional_seasonality(regional_weekly)

    validate_outputs(
        national_weekly,
        national_seasonality,
        regional_weekly,
        regional_seasonality,
    )

    peaks = build_peak_summary(
        national_seasonality,
        regional_seasonality,
    )

    NATIONAL_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    national_seasonality.to_csv(
        NATIONAL_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    regional_seasonality.to_csv(
        REGIONAL_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    regional_weekly.to_csv(
        REGION_YEAR_WEEK_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    audit = {
        "status": "APROVADO",
        "analise": "sazonalidade epidemiológica nacional e regional",
        "periodo": "2016-2025",
        "linhas_painel": len(dataframe),
        "casos_preservados": int(national_weekly["casos_provaveis"].sum()),
        "semanas_nacionais": len(national_weekly),
        "semanas_sazonais": len(national_seasonality),
        "regioes": list(REGION_ORDER),
        "semana_53": {
            "anos_disponiveis": 2,
            "observacao": "A semana 53 ocorre somente em 2020 e 2025.",
        },
        "picos_sazonais": peaks,
        "observacoes_metodologicas": [
            (
                "Incidências regionais são calculadas a partir "
                "de casos agregados e população regional."
            ),
            (
                "A semana 53 possui apenas dois anos e não deve "
                "ser comparada diretamente às semanas 1-52."
            ),
            (
                "Média e mediana são apresentadas em conjunto "
                "porque 2024 possui magnitude epidemiológica excepcional."
            ),
            ("A análise é descritiva e não modifica o modelo preditivo final."),
        ],
        "artefatos": {
            "sazonalidade_nacional": str(NATIONAL_OUTPUT),
            "sazonalidade_regional": str(REGIONAL_OUTPUT),
            "serie_semanal_regional": str(REGION_YEAR_WEEK_OUTPUT),
            "auditoria": str(AUDIT_OUTPUT),
        },
    }

    with AUDIT_OUTPUT.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            audit,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(f"Linhas do painel                  : {len(dataframe):,}")

    print(
        "Casos preservados                 : "
        f"{int(national_weekly['casos_provaveis'].sum()):,}"
    )

    print(f"Semanas nacionais                 : {len(national_weekly):,}")

    print()
    print("PICO SAZONAL NACIONAL")
    print(
        "Maior incidência média            : "
        f"SE {peaks['nacional']['semana_maior_incidencia_media']}"
    )

    print(
        "Maior incidência mediana          : "
        f"SE {peaks['nacional']['semana_maior_incidencia_mediana']}"
    )

    print()
    print("PICOS REGIONAIS")

    for region in REGION_ORDER:
        result = peaks["regioes"][region]

        print(
            f"{region:<16} "
            f"média=SE "
            f"{result['semana_maior_incidencia_media']:>2} | "
            f"mediana=SE "
            f"{result['semana_maior_incidencia_mediana']:>2}"
        )

    print()
    print(f"Sazonalidade nacional             : {NATIONAL_OUTPUT}")

    print(f"Sazonalidade regional             : {REGIONAL_OUTPUT}")

    print(f"Série semanal regional            : {REGION_YEAR_WEEK_OUTPUT}")

    print(f"Auditoria                         : {AUDIT_OUTPUT}")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
