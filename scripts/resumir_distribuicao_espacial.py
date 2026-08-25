"""Resume os resultados da distribuição espacial de 2016 a 2025."""

import pandas as pd

from dengue_alert.config.paths import REPORTS_DIR

UF_INPUT = REPORTS_DIR / "audits" / "distribuicao_espacial_uf_periodo_2016_2025.csv"

MUNICIPAL_INPUT = (
    REPORTS_DIR / "audits" / "distribuicao_espacial_municipio_periodo_2016_2025.csv"
)

EXPECTED_UFS = 27
EXPECTED_TERRITORIES = 5_571

MIN_YEARS_FOR_STABLE_RANKING = 10
MIN_MEAN_POPULATION = 20_000
TOP_N = 15


def validate_uf(dataframe: pd.DataFrame) -> None:
    """Valida o resumo por UF."""
    if len(dataframe) != EXPECTED_UFS:
        raise ValueError(
            "Quantidade inesperada de UFs. "
            f"Esperado: {EXPECTED_UFS}; "
            f"obtido: {len(dataframe)}."
        )

    required_columns = {
        "codigo_uf_ibge",
        "nome_uf_ibge",
        "regiao",
        "casos_periodo",
        "participacao_casos_periodo",
        "incidencia_media_anual_100mil",
        "incidencia_mediana_anual_100mil",
        "incidencia_maxima_anual_100mil",
        "ano_maior_incidencia",
    }

    missing = sorted(required_columns - set(dataframe.columns))

    if missing:
        raise ValueError(
            "Colunas ausentes no resumo por UF: " + ", ".join(missing) + "."
        )


def validate_municipal(dataframe: pd.DataFrame) -> None:
    """Valida o resumo territorial do período."""
    if len(dataframe) != EXPECTED_TERRITORIES:
        raise ValueError(
            "Quantidade inesperada de unidades territoriais. "
            f"Esperado: {EXPECTED_TERRITORIES:,}; "
            f"obtido: {len(dataframe):,}."
        )

    required_columns = {
        "codigo_ibge_7",
        "nome_municipio_ibge",
        "nome_uf_ibge",
        "regiao",
        "anos_disponiveis",
        "anos_com_casos",
        "casos_periodo",
        "populacao_media",
        "incidencia_media_anual_100mil",
        "incidencia_mediana_anual_100mil",
        "incidencia_maxima_anual_100mil",
        "ano_maior_incidencia",
    }

    missing = sorted(required_columns - set(dataframe.columns))

    if missing:
        raise ValueError(
            "Colunas ausentes no resumo municipal: " + ", ".join(missing) + "."
        )


def format_uf_display(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Formata uma tabela de UF para terminal."""
    output = dataframe[
        [
            "nome_uf_ibge",
            "regiao",
            "casos_periodo",
            "participacao_casos_periodo",
            "incidencia_media_anual_100mil",
            "incidencia_mediana_anual_100mil",
            "ano_maior_incidencia",
        ]
    ].copy()

    output["participacao_casos_periodo"] = output["participacao_casos_periodo"].map(
        lambda value: f"{value:.2%}"
    )

    for column in (
        "incidencia_media_anual_100mil",
        "incidencia_mediana_anual_100mil",
    ):
        output[column] = output[column].map(lambda value: f"{value:.2f}")

    return output


def format_municipal_display(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Formata uma tabela municipal para terminal."""
    output = dataframe[
        [
            "nome_municipio_ibge",
            "nome_uf_ibge",
            "regiao",
            "anos_disponiveis",
            "casos_periodo",
            "populacao_media",
            "incidencia_mediana_anual_100mil",
            "incidencia_maxima_anual_100mil",
            "ano_maior_incidencia",
        ]
    ].copy()

    output["populacao_media"] = output["populacao_media"].round().astype("int64")

    for column in (
        "incidencia_mediana_anual_100mil",
        "incidencia_maxima_anual_100mil",
    ):
        output[column] = output[column].map(lambda value: f"{value:.2f}")

    return output


def main() -> None:
    """Exibe os principais resultados espaciais já calculados."""
    print("=" * 132)
    print("RESUMO DA DISTRIBUIÇÃO ESPACIAL — 2016–2025")
    print("=" * 132)

    uf = pd.read_csv(
        UF_INPUT,
        dtype={
            "codigo_uf_ibge": "string",
        },
    )

    municipal = pd.read_csv(
        MUNICIPAL_INPUT,
        dtype={
            "codigo_ibge_7": "string",
        },
    )

    validate_uf(uf)
    validate_municipal(municipal)

    print()
    print("=" * 132)
    print("UFs — ORDEM POR CASOS ACUMULADOS")
    print("=" * 132)

    uf_cases = uf.sort_values(
        [
            "casos_periodo",
            "nome_uf_ibge",
        ],
        ascending=[
            False,
            True,
        ],
    )

    print(format_uf_display(uf_cases).to_string(index=False))

    print()
    print("=" * 132)
    print("UFs — ORDEM POR INCIDÊNCIA MEDIANA ANUAL")
    print("=" * 132)

    uf_incidence = uf.sort_values(
        [
            "incidencia_mediana_anual_100mil",
            "nome_uf_ibge",
        ],
        ascending=[
            False,
            True,
        ],
    )

    print(format_uf_display(uf_incidence).to_string(index=False))

    print()
    print("=" * 132)
    print(f"TOP {TOP_N} MUNICÍPIOS — CASOS ACUMULADOS")
    print("=" * 132)

    municipal_cases = municipal.sort_values(
        [
            "casos_periodo",
            "nome_municipio_ibge",
        ],
        ascending=[
            False,
            True,
        ],
    ).head(TOP_N)

    print(format_municipal_display(municipal_cases).to_string(index=False))

    stable = municipal.loc[
        municipal["anos_disponiveis"].ge(MIN_YEARS_FOR_STABLE_RANKING)
        & municipal["populacao_media"].ge(MIN_MEAN_POPULATION)
    ].copy()

    print()
    print("=" * 132)
    print("SUPORTE DO RANKING MUNICIPAL DE INCIDÊNCIA")
    print("=" * 132)

    print(f"Critério de anos                  : >= {MIN_YEARS_FOR_STABLE_RANKING}")

    print(f"População média mínima            : {MIN_MEAN_POPULATION:,}")

    print(f"Municípios elegíveis              : {len(stable):,}")

    print()
    print("=" * 132)
    print(f"TOP {TOP_N} MUNICÍPIOS — INCIDÊNCIA MEDIANA ANUAL")
    print("=" * 132)

    municipal_incidence = stable.sort_values(
        [
            "incidencia_mediana_anual_100mil",
            "nome_municipio_ibge",
        ],
        ascending=[
            False,
            True,
        ],
    ).head(TOP_N)

    print(format_municipal_display(municipal_incidence).to_string(index=False))

    print()
    print("=" * 132)
    print("OBSERVAÇÕES")
    print("=" * 132)

    print("Casos absolutos e incidência são rankings distintos.")

    print(
        "O ranking municipal de incidência usa mediana anual, "
        "10 anos disponíveis e população média >= 20 mil."
    )

    print(
        "Municípios fora desse filtro permanecem nos dados completos "
        "e não são excluídos das análises espaciais."
    )

    print()
    print("STATUS: RESUMO CONCLUÍDO")


if __name__ == "__main__":
    main()
