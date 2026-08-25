"""Resume os resultados da associação descritiva clima × dengue."""

import pandas as pd

from dengue_alert.config.paths import REPORTS_DIR

MUNICIPAL_INPUT = (
    REPORTS_DIR / "audits" / "associacao_clima_dengue_municipios_2016_2025.csv"
)

NATIONAL_INPUT = (
    REPORTS_DIR / "audits" / "associacao_clima_dengue_nacional_2016_2025.csv"
)

REGIONAL_INPUT = (
    REPORTS_DIR / "audits" / "associacao_clima_dengue_regional_2016_2025.csv"
)

VARIABLES = [
    "temperatura_media_c",
    "umidade_relativa_media_pct",
    "precipitacao_total_mm",
]

REGION_ORDER = [
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul",
]


def identify_peaks(
    dataframe: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:
    """Identifica maior correlação mediana em magnitude por grupo."""
    output = dataframe.copy()

    output["magnitude_correlacao_mediana"] = output["correlacao_mediana"].abs()

    sort_columns = [
        *group_columns,
        "magnitude_correlacao_mediana",
        "lag_semanas",
    ]

    ascending = [
        *[True] * len(group_columns),
        False,
        True,
    ]

    return (
        output.sort_values(
            sort_columns,
            ascending=ascending,
        )
        .drop_duplicates(
            subset=group_columns,
            keep="first",
        )
        .reset_index(drop=True)
    )


def main() -> None:
    """Exibe heterogeneidade regional e correlações inválidas."""
    municipal = pd.read_csv(
        MUNICIPAL_INPUT,
        dtype={
            "codigo_ibge_7": "string",
            "codigo_uf_ibge": "string",
        },
    )

    national = pd.read_csv(NATIONAL_INPUT)

    regional = pd.read_csv(REGIONAL_INPUT)

    print("=" * 150)
    print("RESUMO DA ASSOCIAÇÃO CLIMA × DENGUE — 2016–2025")
    print("=" * 150)

    print()
    print("=" * 150)
    print("CORRELAÇÕES MUNICIPAIS INVÁLIDAS")
    print("=" * 150)

    invalid = municipal.loc[~municipal["correlacao_valida"].astype(bool)].copy()

    invalid_territories = (
        invalid[
            [
                "codigo_ibge_7",
                "nome_municipio_ibge",
                "nome_uf_ibge",
                "regiao",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            [
                "nome_uf_ibge",
                "nome_municipio_ibge",
            ]
        )
        .reset_index(drop=True)
    )

    print(f"Linhas inválidas                   : {len(invalid):,}")

    print(f"Territórios envolvidos             : {len(invalid_territories):,}")

    print()

    print(invalid_territories.to_string(index=False))

    invalid_counts = (
        invalid.groupby(
            [
                "codigo_ibge_7",
                "nome_municipio_ibge",
            ],
            as_index=False,
            observed=True,
        )
        .agg(
            combinacoes_invalidas=(
                "correlacao_valida",
                "size",
            ),
            observacoes_minimas=(
                "observacoes_validas",
                "min",
            ),
            observacoes_maximas=(
                "observacoes_validas",
                "max",
            ),
        )
        .sort_values(
            [
                "combinacoes_invalidas",
                "codigo_ibge_7",
            ],
            ascending=[
                False,
                True,
            ],
        )
    )

    print()
    print("DETALHE DAS INVALIDAÇÕES")
    print()

    print(invalid_counts.to_string(index=False))

    print()
    print("=" * 150)
    print("DEFASAGENS DE MAIOR ASSOCIAÇÃO — NACIONAL")
    print("=" * 150)

    national_peaks = identify_peaks(
        national,
        [
            "variavel_climatica",
        ],
    )

    print(
        national_peaks[
            [
                "variavel_climatica",
                "lag_semanas",
                "correlacao_mediana",
                "correlacao_p25",
                "correlacao_p75",
                "proporcao_correlacao_positiva",
            ]
        ].to_string(index=False)
    )

    print()
    print("=" * 150)
    print("DEFASAGENS DE MAIOR ASSOCIAÇÃO — REGIÃO × VARIÁVEL")
    print("=" * 150)

    regional_peaks = identify_peaks(
        regional,
        [
            "regiao",
            "variavel_climatica",
        ],
    )

    regional_peaks["regiao"] = pd.Categorical(
        regional_peaks["regiao"],
        categories=REGION_ORDER,
        ordered=True,
    )

    regional_peaks = regional_peaks.sort_values(
        [
            "regiao",
            "variavel_climatica",
        ]
    )

    print(
        regional_peaks[
            [
                "regiao",
                "variavel_climatica",
                "lag_semanas",
                "municipios_correlacao_valida",
                "correlacao_mediana",
                "correlacao_p25",
                "correlacao_p75",
                "proporcao_correlacao_positiva",
            ]
        ].to_string(index=False)
    )

    print()
    print("=" * 150)
    print("PERFIL REGIONAL COMPLETO POR LAG")
    print("=" * 150)

    display = regional[
        [
            "regiao",
            "variavel_climatica",
            "lag_semanas",
            "municipios_correlacao_valida",
            "correlacao_mediana",
            "correlacao_p25",
            "correlacao_p75",
            "proporcao_correlacao_positiva",
        ]
    ].copy()

    display["regiao"] = pd.Categorical(
        display["regiao"],
        categories=REGION_ORDER,
        ordered=True,
    )

    display = display.sort_values(
        [
            "variavel_climatica",
            "regiao",
            "lag_semanas",
        ]
    )

    print(display.to_string(index=False))

    print()
    print("=" * 150)
    print("STATUS: RESUMO CONCLUÍDO")
    print("=" * 150)


if __name__ == "__main__":
    main()
