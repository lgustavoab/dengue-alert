"""Resume os resultados pós-teste de heterogeneidade por UF."""

import pandas as pd

from dengue_alert.config.paths import REPORTS_DIR

UF_INPUT = REPORTS_DIR / "audits" / "heterogeneidade_2025_uf.csv"

EXPECTED_UFS = 27
EXPECTED_HORIZONS = {
    1,
    2,
    3,
    4,
}
EXPECTED_SUBSETS = {
    "geral",
    "early_warning",
}

DISPLAY_COLUMNS = [
    "grupo",
    "municipios",
    "positivos",
    "prevalencia",
    "average_precision",
    "brier_score",
    "precision",
    "recall",
    "f1",
    "proporcao_alertas",
]


def validate_input(
    dataframe: pd.DataFrame,
) -> None:
    """Valida o resultado previamente calculado por UF."""
    required_columns = {
        "grupo",
        "horizonte",
        "subconjunto",
        "municipios",
        "positivos",
        "prevalencia",
        "average_precision",
        "brier_score",
        "precision",
        "recall",
        "f1",
        "proporcao_alertas",
    }

    missing = sorted(required_columns - set(dataframe.columns))

    if missing:
        raise ValueError("Colunas ausentes: " + ", ".join(missing) + ".")

    ufs = set(dataframe["grupo"].unique())

    if len(ufs) != EXPECTED_UFS:
        raise ValueError(
            "Quantidade inesperada de UFs. "
            f"Esperado: {EXPECTED_UFS}; "
            f"obtido: {len(ufs)}."
        )

    horizons = {int(value) for value in dataframe["horizonte"].unique()}

    if horizons != EXPECTED_HORIZONS:
        raise ValueError("Horizontes inesperados.")

    subsets = set(dataframe["subconjunto"].unique())

    if subsets != EXPECTED_SUBSETS:
        raise ValueError("Subconjuntos inesperados.")

    expected_rows = EXPECTED_UFS * len(EXPECTED_HORIZONS) * len(EXPECTED_SUBSETS)

    if len(dataframe) != expected_rows:
        raise ValueError(
            "Quantidade inesperada de resultados. "
            f"Esperado: {expected_rows}; "
            f"obtido: {len(dataframe)}."
        )


def format_display(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Formata a tabela sem modificar os resultados originais."""
    output = dataframe.loc[
        :,
        DISPLAY_COLUMNS,
    ].copy()

    output["prevalencia"] = output["prevalencia"].map(lambda value: f"{value:.2%}")

    output["average_precision"] = output["average_precision"].map(
        lambda value: "N/A" if pd.isna(value) else f"{value:.4f}"
    )

    output["brier_score"] = output["brier_score"].map(lambda value: f"{value:.4f}")

    for column in (
        "precision",
        "recall",
        "f1",
    ):
        output[column] = output[column].map(lambda value: f"{value:.4f}")

    output["proporcao_alertas"] = output["proporcao_alertas"].map(
        lambda value: f"{value:.2%}"
    )

    return output


def main() -> None:
    """Exibe as 27 UFs por horizonte no subconjunto de early warning."""
    print("=" * 132)
    print("HETEROGENEIDADE POR UF — 2025")
    print("SUBCONJUNTO: EARLY WARNING")
    print("=" * 132)

    dataframe = pd.read_csv(UF_INPUT)

    validate_input(dataframe)

    early = dataframe.loc[dataframe["subconjunto"].eq("early_warning")].copy()

    for horizon in sorted(EXPECTED_HORIZONS):
        subset = early.loc[early["horizonte"].eq(horizon)].sort_values("grupo")

        print()
        print("=" * 132)
        print(f"HORIZONTE H{horizon}")
        print("=" * 132)

        display = format_display(subset)

        print(
            display.to_string(
                index=False,
            )
        )

    print()
    print("=" * 132)
    print("OBSERVAÇÃO")
    print("=" * 132)

    print("As UFs estão ordenadas alfabeticamente, e não por desempenho.")

    print(
        "A quantidade de positivos deve ser considerada na interpretação das métricas."
    )

    print("Nenhuma UF foi excluída ou selecionada com base nos resultados.")

    print()
    print("STATUS: RESUMO CONCLUÍDO")


if __name__ == "__main__":
    main()
