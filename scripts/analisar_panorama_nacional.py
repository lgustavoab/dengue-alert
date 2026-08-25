"""Gera o panorama epidemiológico nacional da dengue entre 2016 e 2025."""

import json

import numpy as np
import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR

ANNUAL_OUTPUT = REPORTS_DIR / "audits" / "panorama_nacional_anual_2016_2025.csv"

WEEKLY_OUTPUT = REPORTS_DIR / "audits" / "panorama_nacional_semanal_2016_2025.csv"

AUDIT_OUTPUT = REPORTS_DIR / "audits" / "panorama_nacional_2016_2025.json"

EXPECTED_ROWS = 2_907_593
EXPECTED_CASES = 16_294_913

EXPECTED_YEARS = tuple(
    range(
        2016,
        2026,
    )
)

EXPECTED_WEEKS_BY_YEAR = {year: 52 for year in EXPECTED_YEARS}

EXPECTED_WEEKS_BY_YEAR[2020] = 53

EXPECTED_WEEKS_BY_YEAR[2025] = 53

EXPECTED_TERRITORIES_BY_YEAR = {year: 5_570 for year in EXPECTED_YEARS}

EXPECTED_TERRITORIES_BY_YEAR[2025] = 5_571

EXPECTED_TOTAL_WEEKS = sum(EXPECTED_WEEKS_BY_YEAR.values())

YEAR_COLUMN = "ano_epidemiologico"
WEEK_COLUMN = "semana_epidemiologica"
TERRITORY_COLUMN = "codigo_ibge_7"
CASES_COLUMN = "casos_provaveis"
POPULATION_COLUMN = "populacao"
INCIDENCE_COLUMN = "incidencia_100mil"

REQUIRED_COLUMNS = [
    TERRITORY_COLUMN,
    YEAR_COLUMN,
    WEEK_COLUMN,
    "data_inicio_semana",
    "data_fim_semana",
    CASES_COLUMN,
    POPULATION_COLUMN,
    INCIDENCE_COLUMN,
]


def validate_master(
    dataframe: pd.DataFrame,
) -> float:
    """Valida o painel mestre antes da análise nacional."""
    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas no painel mestre. "
            f"Esperado: {EXPECTED_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    years = tuple(sorted(int(value) for value in dataframe[YEAR_COLUMN].unique()))

    if years != EXPECTED_YEARS:
        raise ValueError(
            "Período epidemiológico inesperado. "
            f"Esperado: {EXPECTED_YEARS}; "
            f"obtido: {years}."
        )

    missing = dataframe[REQUIRED_COLUMNS].isna().sum()

    missing = missing.loc[missing.gt(0)]

    if not missing.empty:
        raise ValueError(
            f"Existem valores ausentes em colunas obrigatórias: {missing.to_dict()}."
        )

    duplicates = int(
        dataframe.duplicated(
            subset=[
                TERRITORY_COLUMN,
                YEAR_COLUMN,
                WEEK_COLUMN,
            ]
        ).sum()
    )

    if duplicates:
        raise ValueError(
            f"Foram encontradas {duplicates:,} linhas territoriais semanais duplicadas."
        )

    total_cases = int(dataframe[CASES_COLUMN].sum())

    if total_cases != EXPECTED_CASES:
        raise ValueError(
            "Total epidemiológico inesperado. "
            f"Esperado: {EXPECTED_CASES:,}; "
            f"obtido: {total_cases:,}."
        )

    cases = dataframe[CASES_COLUMN].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    population = dataframe[POPULATION_COLUMN].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    incidence = dataframe[INCIDENCE_COLUMN].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    if not np.isfinite(cases).all():
        raise ValueError("Existem valores de casos não finitos.")

    if not np.isfinite(population).all():
        raise ValueError("Existem valores populacionais não finitos.")

    if not np.isfinite(incidence).all():
        raise ValueError("Existem valores de incidência não finitos.")

    if (cases < 0).any():
        raise ValueError("Existem valores negativos de casos.")

    if (population <= 0).any():
        raise ValueError("Existem populações menores ou iguais a zero.")

    if (incidence < 0).any():
        raise ValueError("Existem valores negativos de incidência.")

    expected_incidence = cases / population * 100_000

    maximum_difference = float(np.max(np.abs(expected_incidence - incidence)))

    if not np.allclose(
        expected_incidence,
        incidence,
        rtol=1e-10,
        atol=1e-8,
    ):
        raise ValueError(
            "A incidência municipal não é reproduzida "
            "a partir de casos e população. "
            f"Maior diferença absoluta: {maximum_difference:.12f}."
        )

    for year in EXPECTED_YEARS:
        year_data = dataframe.loc[dataframe[YEAR_COLUMN].eq(year)]

        weeks = int(year_data[WEEK_COLUMN].nunique())

        expected_weeks = EXPECTED_WEEKS_BY_YEAR[year]

        if weeks != expected_weeks:
            raise ValueError(
                f"{year}: quantidade inesperada de semanas. "
                f"Esperado: {expected_weeks}; "
                f"obtido: {weeks}."
            )

        territories = int(year_data[TERRITORY_COLUMN].nunique())

        expected_territories = EXPECTED_TERRITORIES_BY_YEAR[year]

        if territories != expected_territories:
            raise ValueError(
                f"{year}: quantidade inesperada de unidades territoriais. "
                f"Esperado: {expected_territories:,}; "
                f"obtido: {territories:,}."
            )

        expected_rows = expected_weeks * expected_territories

        if len(year_data) != expected_rows:
            raise ValueError(
                f"{year}: grade territorial semanal incompleta. "
                f"Esperado: {expected_rows:,}; "
                f"obtido: {len(year_data):,}."
            )

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

    return maximum_difference


def build_population_by_year(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Obtém a população nacional sem repetir população a cada semana."""
    territory_year = dataframe[
        [
            YEAR_COLUMN,
            TERRITORY_COLUMN,
            POPULATION_COLUMN,
        ]
    ].drop_duplicates(
        subset=[
            YEAR_COLUMN,
            TERRITORY_COLUMN,
        ]
    )

    population = (
        territory_year.groupby(
            YEAR_COLUMN,
            as_index=False,
            observed=True,
        )
        .agg(
            populacao_nacional=(
                POPULATION_COLUMN,
                "sum",
            ),
            unidades_territoriais=(
                TERRITORY_COLUMN,
                "nunique",
            ),
        )
        .sort_values(YEAR_COLUMN)
        .reset_index(drop=True)
    )

    return population


def validate_week_dates(
    dataframe: pd.DataFrame,
) -> None:
    """Confirma uma única data inicial e final para cada semana."""
    date_counts = dataframe.groupby(
        [
            YEAR_COLUMN,
            WEEK_COLUMN,
        ],
        observed=True,
    ).agg(
        datas_inicio=(
            "data_inicio_semana",
            "nunique",
        ),
        datas_fim=(
            "data_fim_semana",
            "nunique",
        ),
    )

    invalid = date_counts.loc[
        (date_counts["datas_inicio"] != 1) | (date_counts["datas_fim"] != 1)
    ]

    if not invalid.empty:
        raise ValueError(
            "Existem semanas epidemiológicas com datas inicial ou final inconsistentes."
        )


def build_weekly(
    dataframe: pd.DataFrame,
    population_by_year: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega o painel municipal para a escala nacional semanal."""
    working = dataframe.assign(
        unidade_com_casos=(dataframe[CASES_COLUMN].gt(0).astype("int8"))
    )

    weekly = working.groupby(
        [
            YEAR_COLUMN,
            WEEK_COLUMN,
        ],
        as_index=False,
        observed=True,
    ).agg(
        data_inicio_semana=(
            "data_inicio_semana",
            "first",
        ),
        data_fim_semana=(
            "data_fim_semana",
            "first",
        ),
        casos_provaveis=(
            CASES_COLUMN,
            "sum",
        ),
        unidades_territoriais=(
            TERRITORY_COLUMN,
            "nunique",
        ),
        unidades_territoriais_com_casos=(
            "unidade_com_casos",
            "sum",
        ),
    )

    weekly = weekly.merge(
        population_by_year[
            [
                YEAR_COLUMN,
                "populacao_nacional",
            ]
        ],
        on=YEAR_COLUMN,
        how="left",
        validate="many_to_one",
    )

    weekly["incidencia_nacional_100mil"] = (
        weekly["casos_provaveis"] / weekly["populacao_nacional"] * 100_000
    )

    weekly["proporcao_unidades_com_casos"] = (
        weekly["unidades_territoriais_com_casos"] / weekly["unidades_territoriais"]
    )

    return weekly.sort_values(
        [
            YEAR_COLUMN,
            WEEK_COLUMN,
        ]
    ).reset_index(drop=True)


def build_annual(
    dataframe: pd.DataFrame,
    weekly: pd.DataFrame,
    population_by_year: pd.DataFrame,
) -> pd.DataFrame:
    """Constrói os indicadores epidemiológicos nacionais anuais."""
    territory_year = dataframe.groupby(
        [
            YEAR_COLUMN,
            TERRITORY_COLUMN,
        ],
        as_index=False,
        observed=True,
    ).agg(
        casos_anuais=(
            CASES_COLUMN,
            "sum",
        ),
    )

    territory_year["unidade_com_casos"] = (
        territory_year["casos_anuais"].gt(0).astype("int8")
    )

    annual = territory_year.groupby(
        YEAR_COLUMN,
        as_index=False,
        observed=True,
    ).agg(
        casos_provaveis=(
            "casos_anuais",
            "sum",
        ),
        unidades_territoriais_com_casos=(
            "unidade_com_casos",
            "sum",
        ),
    )

    annual = annual.merge(
        population_by_year,
        on=YEAR_COLUMN,
        how="left",
        validate="one_to_one",
    )

    weekly_summary = weekly.groupby(
        YEAR_COLUMN,
        as_index=False,
        observed=True,
    ).agg(
        semanas_epidemiologicas=(
            WEEK_COLUMN,
            "nunique",
        ),
        media_semanal_casos=(
            CASES_COLUMN,
            "mean",
        ),
        pico_semanal_casos=(
            CASES_COLUMN,
            "max",
        ),
    )

    peak = (
        weekly.sort_values(
            [
                YEAR_COLUMN,
                CASES_COLUMN,
                WEEK_COLUMN,
            ],
            ascending=[
                True,
                False,
                True,
            ],
        )
        .drop_duplicates(
            subset=[YEAR_COLUMN],
            keep="first",
        )[
            [
                YEAR_COLUMN,
                WEEK_COLUMN,
                "data_inicio_semana",
            ]
        ]
        .rename(
            columns={
                WEEK_COLUMN: "semana_pico",
                "data_inicio_semana": "data_inicio_semana_pico",
            }
        )
    )

    annual = annual.merge(
        weekly_summary,
        on=YEAR_COLUMN,
        how="left",
        validate="one_to_one",
    )

    annual = annual.merge(
        peak,
        on=YEAR_COLUMN,
        how="left",
        validate="one_to_one",
    )

    annual["incidencia_anual_100mil"] = (
        annual["casos_provaveis"] / annual["populacao_nacional"] * 100_000
    )

    annual["proporcao_unidades_com_casos"] = (
        annual["unidades_territoriais_com_casos"] / annual["unidades_territoriais"]
    )

    annual["participacao_casos_periodo"] = annual["casos_provaveis"] / EXPECTED_CASES

    columns = [
        YEAR_COLUMN,
        "semanas_epidemiologicas",
        "casos_provaveis",
        "populacao_nacional",
        "incidencia_anual_100mil",
        "media_semanal_casos",
        "pico_semanal_casos",
        "semana_pico",
        "data_inicio_semana_pico",
        "unidades_territoriais",
        "unidades_territoriais_com_casos",
        "proporcao_unidades_com_casos",
        "participacao_casos_periodo",
    ]

    return annual[columns].sort_values(YEAR_COLUMN).reset_index(drop=True)


def validate_outputs(
    annual: pd.DataFrame,
    weekly: pd.DataFrame,
) -> None:
    """Valida preservação dos totais nas agregações nacionais."""
    if len(annual) != len(EXPECTED_YEARS):
        raise ValueError("Quantidade inesperada de linhas no resumo anual.")

    if len(weekly) != EXPECTED_TOTAL_WEEKS:
        raise ValueError(
            "Quantidade inesperada de semanas no resumo nacional. "
            f"Esperado: {EXPECTED_TOTAL_WEEKS}; "
            f"obtido: {len(weekly)}."
        )

    annual_cases = int(annual["casos_provaveis"].sum())

    weekly_cases = int(weekly["casos_provaveis"].sum())

    if annual_cases != EXPECTED_CASES:
        raise ValueError("O resumo anual não preservou o total de casos.")

    if weekly_cases != EXPECTED_CASES:
        raise ValueError("O resumo semanal não preservou o total de casos.")

    if weekly.duplicated(
        subset=[
            YEAR_COLUMN,
            WEEK_COLUMN,
        ]
    ).any():
        raise ValueError("O resumo semanal possui semanas duplicadas.")

    for year in EXPECTED_YEARS:
        obtained = int(
            weekly.loc[
                weekly[YEAR_COLUMN].eq(year),
                WEEK_COLUMN,
            ].nunique()
        )

        expected = EXPECTED_WEEKS_BY_YEAR[year]

        if obtained != expected:
            raise ValueError(
                f"{year}: resumo semanal possui "
                f"{obtained} semanas; esperado: {expected}."
            )

    numeric_columns = [
        "incidencia_anual_100mil",
        "media_semanal_casos",
        "pico_semanal_casos",
        "proporcao_unidades_com_casos",
        "participacao_casos_periodo",
    ]

    for column in numeric_columns:
        values = annual[column].to_numpy(
            dtype=np.float64,
            copy=False,
        )

        if not np.isfinite(values).all():
            raise ValueError(f"O resumo anual possui valores não finitos em {column}.")


def build_audit(
    annual: pd.DataFrame,
    weekly: pd.DataFrame,
    maximum_incidence_difference: float,
) -> dict:
    """Monta a auditoria consolidada da análise."""
    cases_by_year = {
        str(int(row[YEAR_COLUMN])): int(row["casos_provaveis"])
        for _, row in annual.iterrows()
    }

    return {
        "status": "APROVADO",
        "analise": "panorama epidemiológico nacional",
        "periodo": "2016-2025",
        "fonte_processada": str(MASTER_PANEL),
        "painel_mestre": {
            "linhas": EXPECTED_ROWS,
            "casos_provaveis": EXPECTED_CASES,
            "anos": list(EXPECTED_YEARS),
            "semanas_nacionais": len(weekly),
        },
        "validacoes": {
            "total_epidemiologico_preservado": True,
            "grade_territorial_semanal_validada": True,
            "duplicidades": 0,
            "incidencia_municipal_reproduzida": True,
            "maior_diferenca_absoluta_incidencia": maximum_incidence_difference,
        },
        "casos_por_ano": cases_by_year,
        "observacoes_metodologicas": [
            (
                "A população nacional é calculada uma única vez "
                "por unidade territorial e ano."
            ),
            (
                "A incidência nacional é calculada como total de casos "
                "dividido pela população nacional, multiplicado por 100 mil."
            ),
            (
                "O estado risco_elevado não faz parte do painel mestre "
                "e não foi reconstruído nesta etapa."
            ),
            (
                "As unidades territoriais incluem a estrutura oficial "
                "preservada pelo painel do projeto."
            ),
        ],
        "artefatos": {
            "anual": str(ANNUAL_OUTPUT),
            "semanal": str(WEEKLY_OUTPUT),
            "auditoria": str(AUDIT_OUTPUT),
        },
    }


def main() -> None:
    """Executa a análise nacional de 2016 a 2025."""
    print("=" * 104)
    print("PANORAMA EPIDEMIOLÓGICO NACIONAL — 2016–2025")
    print("=" * 104)

    print()
    print("Carregando painel mestre...")

    dataframe = pd.read_parquet(
        MASTER_PANEL,
        columns=REQUIRED_COLUMNS,
    )

    maximum_incidence_difference = validate_master(dataframe)

    print(f"Linhas                            : {len(dataframe):,}")

    print(f"Casos prováveis                   : {int(dataframe[CASES_COLUMN].sum()):,}")

    print("Período                           : 2016–2025")

    print("Incidência municipal auditada     : SIM")

    validate_week_dates(dataframe)

    population_by_year = build_population_by_year(dataframe)

    weekly = build_weekly(
        dataframe,
        population_by_year,
    )

    annual = build_annual(
        dataframe,
        weekly,
        population_by_year,
    )

    validate_outputs(
        annual,
        weekly,
    )

    ANNUAL_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    annual.to_csv(
        ANNUAL_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    weekly.to_csv(
        WEEKLY_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    audit = build_audit(
        annual,
        weekly,
        maximum_incidence_difference,
    )

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

    display = annual[
        [
            YEAR_COLUMN,
            "casos_provaveis",
            "populacao_nacional",
            "incidencia_anual_100mil",
            "pico_semanal_casos",
            "semana_pico",
            "unidades_territoriais_com_casos",
        ]
    ].copy()

    display["incidencia_anual_100mil"] = display["incidencia_anual_100mil"].map(
        lambda value: f"{value:.2f}"
    )

    print()
    print("=" * 104)
    print("RESUMO ANUAL")
    print("=" * 104)

    print(
        display.to_string(
            index=False,
        )
    )

    print()
    print("=" * 104)
    print("AUDITORIA")
    print("=" * 104)

    print(f"Linhas do painel                  : {len(dataframe):,}")

    print(f"Semanas nacionais                 : {len(weekly):,}")

    print(f"Casos preservados                 : {int(weekly[CASES_COLUMN].sum()):,}")

    print(f"Maior diferença na incidência     : {maximum_incidence_difference:.12g}")

    print(f"Resumo anual                      : {ANNUAL_OUTPUT}")

    print(f"Resumo semanal                    : {WEEKLY_OUTPUT}")

    print(f"Auditoria                         : {AUDIT_OUTPUT}")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
