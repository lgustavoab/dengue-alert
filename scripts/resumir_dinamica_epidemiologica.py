"""Resume os principais resultados da dinâmica epidemiológica."""

import pandas as pd

from dengue_alert.config.paths import REPORTS_DIR

EPISODES_INPUT = REPORTS_DIR / "audits" / "episodios_risco_elevado_2018_2025.csv"

MUNICIPAL_INPUT = REPORTS_DIR / "audits" / "dinamica_risco_municipio_2018_2025.csv"

YEAR_REGION_INPUT = REPORTS_DIR / "audits" / "dinamica_risco_ano_regiao_2018_2025.csv"

TOP_N = 15


def main() -> None:
    """Exibe episódios extremos, recorrência e dinâmica regional."""
    episodes = pd.read_csv(
        EPISODES_INPUT,
        parse_dates=[
            "data_inicio",
            "data_fim",
        ],
        dtype={
            "codigo_ibge_7": "string",
        },
    )

    municipal = pd.read_csv(
        MUNICIPAL_INPUT,
        dtype={
            "codigo_ibge_7": "string",
        },
    )

    year_region = pd.read_csv(YEAR_REGION_INPUT)

    print("=" * 144)
    print("RESUMO DA DINÂMICA EPIDEMIOLÓGICA — 2018–2025")
    print("=" * 144)

    print()
    print("=" * 144)
    print(f"TOP {TOP_N} EPISÓDIOS MAIS LONGOS")
    print("=" * 144)

    longest = episodes.sort_values(
        [
            "duracao_semanas",
            "data_inicio",
        ],
        ascending=[
            False,
            True,
        ],
    ).head(TOP_N)

    columns = [
        "nome_municipio_ibge",
        "nome_uf_ibge",
        "regiao",
        "data_inicio",
        "data_fim",
        "duracao_semanas",
        "incidencia_4s_maxima_100mil",
        "margem_maxima_limiar_100mil",
        "atravessa_ano_epidemiologico",
    ]

    print(longest[columns].to_string(index=False))

    print()
    print("=" * 144)
    print("DISTRIBUIÇÃO DA DURAÇÃO DOS EPISÓDIOS")
    print("=" * 144)

    duration = episodes["duracao_semanas"]

    percentiles = duration.quantile(
        [
            0.25,
            0.50,
            0.75,
            0.90,
            0.95,
            0.99,
        ]
    )

    print(f"Mínimo                            : {int(duration.min())}")

    print(f"P25                               : {percentiles.loc[0.25]:.2f}")

    print(f"P50                               : {percentiles.loc[0.50]:.2f}")

    print(f"P75                               : {percentiles.loc[0.75]:.2f}")

    print(f"P90                               : {percentiles.loc[0.90]:.2f}")

    print(f"P95                               : {percentiles.loc[0.95]:.2f}")

    print(f"P99                               : {percentiles.loc[0.99]:.2f}")

    print(f"Máximo                            : {int(duration.max())}")

    print()
    print("=" * 144)
    print("MUNICÍPIOS — RECORRÊNCIA")
    print("=" * 144)

    recurrence = municipal["anos_com_risco"].value_counts().sort_index()

    for years, count in recurrence.items():
        print(
            f"{int(years)} ano(s) com risco"
            f"{' ' * max(1, 24 - len(str(int(years))))}: "
            f"{int(count):,}"
        )

    print()
    print("=" * 144)
    print("ANO × REGIÃO")
    print("=" * 144)

    display = year_region[
        [
            "ano_epidemiologico",
            "regiao",
            "municipios_elegiveis",
            "municipios_com_risco",
            "proporcao_municipios_com_risco",
            "proporcao_semanas_municipais_em_risco",
            "episodios_iniciados",
            "duracao_mediana_episodios_iniciados",
            "duracao_maxima_episodios_iniciados",
        ]
    ].copy()

    display["proporcao_municipios_com_risco"] = display[
        "proporcao_municipios_com_risco"
    ].map(lambda value: f"{value:.2%}")

    display["proporcao_semanas_municipais_em_risco"] = display[
        "proporcao_semanas_municipais_em_risco"
    ].map(lambda value: f"{value:.2%}")

    print(display.to_string(index=False))

    print()
    print("=" * 144)
    print("STATUS: RESUMO CONCLUÍDO")
    print("=" * 144)


if __name__ == "__main__":
    main()
