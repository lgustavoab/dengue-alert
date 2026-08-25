"""Analisa a distribuição espacial da dengue no Brasil entre 2016 e 2025."""

import json

import numpy as np
import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR

REGION_ANNUAL_OUTPUT = (
    REPORTS_DIR / "audits" / "distribuicao_espacial_regiao_anual_2016_2025.csv"
)

REGION_PERIOD_OUTPUT = (
    REPORTS_DIR / "audits" / "distribuicao_espacial_regiao_periodo_2016_2025.csv"
)

UF_ANNUAL_OUTPUT = (
    REPORTS_DIR / "audits" / "distribuicao_espacial_uf_anual_2016_2025.csv"
)

UF_PERIOD_OUTPUT = (
    REPORTS_DIR / "audits" / "distribuicao_espacial_uf_periodo_2016_2025.csv"
)

MUNICIPAL_ANNUAL_OUTPUT = (
    REPORTS_DIR / "audits" / "distribuicao_espacial_municipio_anual_2016_2025.csv"
)

MUNICIPAL_PERIOD_OUTPUT = (
    REPORTS_DIR / "audits" / "distribuicao_espacial_municipio_periodo_2016_2025.csv"
)

AUDIT_OUTPUT = REPORTS_DIR / "audits" / "distribuicao_espacial_2016_2025.json"


EXPECTED_ROWS = 2_907_593
EXPECTED_CASES = 16_294_913
EXPECTED_YEARS = tuple(range(2016, 2026))
EXPECTED_REGIONS = 5
EXPECTED_UFS = 27

EXPECTED_TERRITORIES_BY_YEAR = {year: 5_570 for year in EXPECTED_YEARS}

EXPECTED_TERRITORIES_BY_YEAR[2025] = 5_571

EXPECTED_MUNICIPAL_ANNUAL_ROWS = sum(EXPECTED_TERRITORIES_BY_YEAR.values())

EXPECTED_PERIOD_TERRITORIES = 5_571

YEAR_COLUMN = "ano_epidemiologico"
WEEK_COLUMN = "semana_epidemiologica"
TERRITORY_COLUMN = "codigo_ibge_7"
MUNICIPALITY_NAME_COLUMN = "nome_municipio_ibge"
UF_CODE_COLUMN = "codigo_uf_ibge"
UF_NAME_COLUMN = "nome_uf_ibge"
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
    MUNICIPALITY_NAME_COLUMN,
    UF_CODE_COLUMN,
    UF_NAME_COLUMN,
    YEAR_COLUMN,
    WEEK_COLUMN,
    CASES_COLUMN,
    POPULATION_COLUMN,
]


def validate_input(dataframe: pd.DataFrame) -> None:
    """Valida o painel mestre antes da análise espacial."""
    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas. "
            f"Esperado: {EXPECTED_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    total_cases = int(dataframe[CASES_COLUMN].sum())

    if total_cases != EXPECTED_CASES:
        raise ValueError(
            "Total epidemiológico inesperado. "
            f"Esperado: {EXPECTED_CASES:,}; "
            f"obtido: {total_cases:,}."
        )

    years = tuple(sorted(int(value) for value in dataframe[YEAR_COLUMN].unique()))

    if years != EXPECTED_YEARS:
        raise ValueError(f"Período inesperado: {years}.")

    missing = dataframe[REQUIRED_COLUMNS].isna().sum()

    missing = missing.loc[missing.gt(0)]

    if not missing.empty:
        raise ValueError(
            f"Existem valores ausentes em colunas obrigatórias: {missing.to_dict()}."
        )

    if dataframe.duplicated(
        subset=[
            TERRITORY_COLUMN,
            YEAR_COLUMN,
            WEEK_COLUMN,
        ]
    ).any():
        raise ValueError("Existem registros território-ano-semana duplicados.")

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

    population_variation = dataframe.groupby(
        [
            YEAR_COLUMN,
            TERRITORY_COLUMN,
        ],
        observed=True,
    )[POPULATION_COLUMN].nunique()

    if (population_variation > 1).any():
        affected = int((population_variation > 1).sum())

        raise ValueError(
            "Foram encontradas "
            f"{affected:,} combinações território-ano "
            "com mais de uma população."
        )

    name_mapping = dataframe.groupby(
        TERRITORY_COLUMN,
        observed=True,
    ).agg(
        nomes=(
            MUNICIPALITY_NAME_COLUMN,
            "nunique",
        ),
        codigos_uf=(
            UF_CODE_COLUMN,
            "nunique",
        ),
        nomes_uf=(
            UF_NAME_COLUMN,
            "nunique",
        ),
    )

    inconsistent = name_mapping.loc[
        (name_mapping["nomes"] != 1)
        | (name_mapping["codigos_uf"] != 1)
        | (name_mapping["nomes_uf"] != 1)
    ]

    if not inconsistent.empty:
        raise ValueError(
            "Existem códigos territoriais associados a mais de um nome ou UF."
        )


def add_region(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Adiciona a macrorregião oficial a partir do código da UF."""
    output = dataframe.copy()

    uf_code = output[UF_CODE_COLUMN].astype(str).str.zfill(2)

    output["regiao"] = uf_code.map(REGION_BY_UF_CODE)

    if output["regiao"].isna().any():
        unknown = sorted(
            {str(value) for value in uf_code.loc[output["regiao"].isna()].unique()}
        )

        raise ValueError("Códigos de UF sem macrorregião: " + ", ".join(unknown) + ".")

    regions = set(output["regiao"].unique())

    if regions != set(REGION_ORDER):
        raise ValueError("Conjunto inesperado de macrorregiões.")

    if output[UF_CODE_COLUMN].nunique() != EXPECTED_UFS:
        raise ValueError("Quantidade inesperada de UFs.")

    return output


def build_municipal_annual(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega o painel semanal para unidade territorial × ano."""
    annual = dataframe.groupby(
        [
            YEAR_COLUMN,
            TERRITORY_COLUMN,
            MUNICIPALITY_NAME_COLUMN,
            UF_CODE_COLUMN,
            UF_NAME_COLUMN,
            "regiao",
        ],
        as_index=False,
        observed=True,
    ).agg(
        casos_provaveis=(
            CASES_COLUMN,
            "sum",
        ),
        populacao=(
            POPULATION_COLUMN,
            "first",
        ),
        semanas_epidemiologicas=(
            WEEK_COLUMN,
            "nunique",
        ),
    )

    annual["incidencia_anual_100mil"] = (
        annual["casos_provaveis"] / annual["populacao"] * 100_000
    )

    annual["teve_casos"] = annual["casos_provaveis"].gt(0)

    return annual.sort_values(
        [
            YEAR_COLUMN,
            UF_CODE_COLUMN,
            TERRITORY_COLUMN,
        ]
    ).reset_index(drop=True)


def add_national_share(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Adiciona participação no total nacional do respectivo ano."""
    national = dataframe.groupby(
        YEAR_COLUMN,
        as_index=False,
        observed=True,
    ).agg(
        casos_nacionais=(
            "casos_provaveis",
            "sum",
        )
    )

    output = dataframe.merge(
        national,
        on=YEAR_COLUMN,
        how="left",
        validate="many_to_one",
    )

    output["participacao_casos_nacional_ano"] = (
        output["casos_provaveis"] / output["casos_nacionais"]
    )

    return output.drop(columns=["casos_nacionais"])


def build_region_annual(
    municipal: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega os indicadores anuais por macrorregião."""
    region = municipal.groupby(
        [
            YEAR_COLUMN,
            "regiao",
        ],
        as_index=False,
        observed=True,
    ).agg(
        casos_provaveis=(
            "casos_provaveis",
            "sum",
        ),
        populacao_regional=(
            "populacao",
            "sum",
        ),
        unidades_territoriais=(
            TERRITORY_COLUMN,
            "nunique",
        ),
        unidades_territoriais_com_casos=(
            "teve_casos",
            "sum",
        ),
    )

    region["incidencia_anual_100mil"] = (
        region["casos_provaveis"] / region["populacao_regional"] * 100_000
    )

    region["proporcao_unidades_com_casos"] = (
        region["unidades_territoriais_com_casos"] / region["unidades_territoriais"]
    )

    region = add_national_share(region)

    region["regiao"] = pd.Categorical(
        region["regiao"],
        categories=REGION_ORDER,
        ordered=True,
    )

    return region.sort_values(
        [
            YEAR_COLUMN,
            "regiao",
        ]
    ).reset_index(drop=True)


def build_uf_annual(
    municipal: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega os indicadores anuais por unidade federativa."""
    uf = municipal.groupby(
        [
            YEAR_COLUMN,
            UF_CODE_COLUMN,
            UF_NAME_COLUMN,
            "regiao",
        ],
        as_index=False,
        observed=True,
    ).agg(
        casos_provaveis=(
            "casos_provaveis",
            "sum",
        ),
        populacao_uf=(
            "populacao",
            "sum",
        ),
        unidades_territoriais=(
            TERRITORY_COLUMN,
            "nunique",
        ),
        unidades_territoriais_com_casos=(
            "teve_casos",
            "sum",
        ),
    )

    uf["incidencia_anual_100mil"] = uf["casos_provaveis"] / uf["populacao_uf"] * 100_000

    uf["proporcao_unidades_com_casos"] = (
        uf["unidades_territoriais_com_casos"] / uf["unidades_territoriais"]
    )

    uf = add_national_share(uf)

    return uf.sort_values(
        [
            YEAR_COLUMN,
            UF_CODE_COLUMN,
        ]
    ).reset_index(drop=True)


def build_period_summary(
    annual: pd.DataFrame,
    *,
    group_columns: list[str],
    population_column: str,
) -> pd.DataFrame:
    """Resume 2016–2025 sem somar incidências anuais."""
    summary = annual.groupby(
        group_columns,
        as_index=False,
        observed=True,
    ).agg(
        anos_disponiveis=(
            YEAR_COLUMN,
            "nunique",
        ),
        anos_com_casos=(
            "casos_provaveis",
            lambda series: int(series.gt(0).sum()),
        ),
        casos_periodo=(
            "casos_provaveis",
            "sum",
        ),
        populacao_media=(
            population_column,
            "mean",
        ),
        incidencia_media_anual_100mil=(
            "incidencia_anual_100mil",
            "mean",
        ),
        incidencia_mediana_anual_100mil=(
            "incidencia_anual_100mil",
            "median",
        ),
        incidencia_maxima_anual_100mil=(
            "incidencia_anual_100mil",
            "max",
        ),
    )

    sort_columns = [
        *group_columns,
        "incidencia_anual_100mil",
        YEAR_COLUMN,
    ]

    ascending = [
        *(True for _ in group_columns),
        False,
        True,
    ]

    peak = (
        annual.sort_values(
            sort_columns,
            ascending=ascending,
        )
        .drop_duplicates(
            subset=group_columns,
            keep="first",
        )[
            [
                *group_columns,
                YEAR_COLUMN,
                "incidencia_anual_100mil",
            ]
        ]
        .rename(
            columns={
                YEAR_COLUMN: "ano_maior_incidencia",
                "incidencia_anual_100mil": "incidencia_ano_pico_100mil",
            }
        )
    )

    summary = summary.merge(
        peak,
        on=group_columns,
        how="left",
        validate="one_to_one",
    )

    summary["participacao_casos_periodo"] = summary["casos_periodo"] / EXPECTED_CASES

    return summary


def validate_outputs(
    municipal_annual: pd.DataFrame,
    region_annual: pd.DataFrame,
    uf_annual: pd.DataFrame,
    municipal_period: pd.DataFrame,
    region_period: pd.DataFrame,
    uf_period: pd.DataFrame,
) -> None:
    """Valida integridade das agregações espaciais."""
    if len(municipal_annual) != EXPECTED_MUNICIPAL_ANNUAL_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas territoriais anuais. "
            f"Esperado: {EXPECTED_MUNICIPAL_ANNUAL_ROWS:,}; "
            f"obtido: {len(municipal_annual):,}."
        )

    if len(region_annual) != (EXPECTED_REGIONS * len(EXPECTED_YEARS)):
        raise ValueError("Quantidade inesperada de linhas região × ano.")

    if len(uf_annual) != (EXPECTED_UFS * len(EXPECTED_YEARS)):
        raise ValueError("Quantidade inesperada de linhas UF × ano.")

    if len(region_period) != EXPECTED_REGIONS:
        raise ValueError("Quantidade inesperada de regiões no resumo do período.")

    if len(uf_period) != EXPECTED_UFS:
        raise ValueError("Quantidade inesperada de UFs no resumo do período.")

    if len(municipal_period) != EXPECTED_PERIOD_TERRITORIES:
        raise ValueError(
            "Quantidade inesperada de unidades territoriais no resumo do período."
        )

    for name, dataframe in {
        "municipal": municipal_annual,
        "regional": region_annual,
        "uf": uf_annual,
    }.items():
        total = int(dataframe["casos_provaveis"].sum())

        if total != EXPECTED_CASES:
            raise ValueError(f"A agregação {name} não preservou os casos.")

    for year in EXPECTED_YEARS:
        municipal_year = municipal_annual.loc[municipal_annual[YEAR_COLUMN].eq(year)]

        expected = EXPECTED_TERRITORIES_BY_YEAR[year]

        if len(municipal_year) != expected:
            raise ValueError(
                f"{year}: quantidade inesperada de unidades territoriais anuais."
            )

        if municipal_year[TERRITORY_COLUMN].nunique() != expected:
            raise ValueError(f"{year}: códigos territoriais duplicados ou ausentes.")

    if municipal_annual.duplicated(
        subset=[
            YEAR_COLUMN,
            TERRITORY_COLUMN,
        ]
    ).any():
        raise ValueError("Existem unidades territoriais anuais duplicadas.")

    incidence_columns = {
        "municipal": municipal_annual["incidencia_anual_100mil"],
        "regional": region_annual["incidencia_anual_100mil"],
        "uf": uf_annual["incidencia_anual_100mil"],
    }

    for name, series in incidence_columns.items():
        values = series.to_numpy(
            dtype=np.float64,
            copy=False,
        )

        if not np.isfinite(values).all():
            raise ValueError(f"Existem incidências não finitas em {name}.")

        if (values < 0).any():
            raise ValueError(f"Existem incidências negativas em {name}.")


def main() -> None:
    """Executa a análise espacial descritiva."""
    print("=" * 108)
    print("DISTRIBUIÇÃO ESPACIAL DA DENGUE — 2016–2025")
    print("=" * 108)

    print()
    print("Carregando painel mestre...")

    dataframe = pd.read_parquet(
        MASTER_PANEL,
        columns=REQUIRED_COLUMNS,
    )

    validate_input(dataframe)

    dataframe = add_region(dataframe)

    municipal_annual = build_municipal_annual(dataframe)

    region_annual = build_region_annual(municipal_annual)

    uf_annual = build_uf_annual(municipal_annual)

    region_period = build_period_summary(
        region_annual,
        group_columns=[
            "regiao",
        ],
        population_column="populacao_regional",
    )

    uf_period = build_period_summary(
        uf_annual,
        group_columns=[
            UF_CODE_COLUMN,
            UF_NAME_COLUMN,
            "regiao",
        ],
        population_column="populacao_uf",
    )

    municipal_period = build_period_summary(
        municipal_annual,
        group_columns=[
            TERRITORY_COLUMN,
            MUNICIPALITY_NAME_COLUMN,
            UF_CODE_COLUMN,
            UF_NAME_COLUMN,
            "regiao",
        ],
        population_column="populacao",
    )

    validate_outputs(
        municipal_annual,
        region_annual,
        uf_annual,
        municipal_period,
        region_period,
        uf_period,
    )

    REGION_ANNUAL_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    region_annual.to_csv(
        REGION_ANNUAL_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    region_period.to_csv(
        REGION_PERIOD_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    uf_annual.to_csv(
        UF_ANNUAL_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    uf_period.to_csv(
        UF_PERIOD_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    municipal_annual.to_csv(
        MUNICIPAL_ANNUAL_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    municipal_period.to_csv(
        MUNICIPAL_PERIOD_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    years_available_distribution = (
        municipal_period["anos_disponiveis"].value_counts().sort_index()
    )

    audit = {
        "status": "APROVADO",
        "analise": "distribuição espacial da dengue",
        "periodo": "2016-2025",
        "painel": {
            "linhas": len(dataframe),
            "casos_provaveis": int(dataframe[CASES_COLUMN].sum()),
        },
        "agregacoes": {
            "regiao": {
                "grupos": len(region_period),
                "linhas_anuais": len(region_annual),
            },
            "uf": {
                "grupos": len(uf_period),
                "linhas_anuais": len(uf_annual),
            },
            "unidade_territorial": {
                "grupos_periodo": len(municipal_period),
                "linhas_anuais": len(municipal_annual),
                "anos_disponiveis": {
                    str(int(years)): int(count)
                    for years, count in years_available_distribution.items()
                },
            },
        },
        "validacoes": {
            "casos_preservados_regiao": True,
            "casos_preservados_uf": True,
            "casos_preservados_unidade_territorial": True,
            "incidencias_recalculadas": True,
            "incidencias_somadas": False,
            "duplicidades_unidade_ano": 0,
        },
        "observacoes_metodologicas": [
            (
                "Casos absolutos e incidência por 100 mil "
                "são mantidos como indicadores distintos."
            ),
            (
                "Incidências regionais e estaduais são "
                "recalculadas a partir de casos e população agregados."
            ),
            ("A incidência do período não é obtida pela soma das incidências anuais."),
            (
                "O resumo 2016-2025 utiliza média, mediana e máximo "
                "das incidências anuais para caracterização."
            ),
            (
                "Unidades territoriais com menos anos disponíveis "
                "permanecem explicitamente identificadas."
            ),
        ],
        "artefatos": {
            "regiao_anual": str(REGION_ANNUAL_OUTPUT),
            "regiao_periodo": str(REGION_PERIOD_OUTPUT),
            "uf_anual": str(UF_ANNUAL_OUTPUT),
            "uf_periodo": str(UF_PERIOD_OUTPUT),
            "municipio_anual": str(MUNICIPAL_ANNUAL_OUTPUT),
            "municipio_periodo": str(MUNICIPAL_PERIOD_OUTPUT),
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

    display = region_period[
        [
            "regiao",
            "casos_periodo",
            "participacao_casos_periodo",
            "incidencia_media_anual_100mil",
            "incidencia_mediana_anual_100mil",
            "ano_maior_incidencia",
        ]
    ].copy()

    display["participacao_casos_periodo"] = display["participacao_casos_periodo"].map(
        lambda value: f"{value:.2%}"
    )

    display["incidencia_media_anual_100mil"] = display[
        "incidencia_media_anual_100mil"
    ].map(lambda value: f"{value:.2f}")

    display["incidencia_mediana_anual_100mil"] = display[
        "incidencia_mediana_anual_100mil"
    ].map(lambda value: f"{value:.2f}")

    print()
    print(f"Linhas do painel                  : {len(dataframe):,}")

    print(f"Casos preservados                 : {int(dataframe[CASES_COLUMN].sum()):,}")

    print(f"Linhas territoriais anuais        : {len(municipal_annual):,}")

    print(f"Unidades territoriais no período  : {len(municipal_period):,}")

    print()
    print("=" * 108)
    print("RESUMO POR MACRORREGIÃO — 2016–2025")
    print("=" * 108)

    print(
        display.to_string(
            index=False,
        )
    )

    print()
    print("Arquivos gerados:")

    print(f"  Região anual                     : {REGION_ANNUAL_OUTPUT}")

    print(f"  Região período                   : {REGION_PERIOD_OUTPUT}")

    print(f"  UF anual                         : {UF_ANNUAL_OUTPUT}")

    print(f"  UF período                       : {UF_PERIOD_OUTPUT}")

    print(f"  Unidade territorial anual        : {MUNICIPAL_ANNUAL_OUTPUT}")

    print(f"  Unidade territorial período      : {MUNICIPAL_PERIOD_OUTPUT}")

    print(f"  Auditoria                        : {AUDIT_OUTPUT}")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
