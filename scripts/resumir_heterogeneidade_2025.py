"""Resume os resultados pós-teste de heterogeneidade de 2025."""

import pandas as pd

from dengue_alert.config.paths import REPORTS_DIR

REGION_INPUT = REPORTS_DIR / "audits" / "heterogeneidade_2025_regiao.csv"

POPULATION_INPUT = (
    REPORTS_DIR / "audits" / "heterogeneidade_2025_porte_populacional.csv"
)

PROFILE_INPUT = (
    REPORTS_DIR / "audits" / "heterogeneidade_2025_perfil_epidemiologico.csv"
)

REGION_ORDER = (
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul",
)

POPULATION_ORDER = (
    "Muito pequeno",
    "Pequeno",
    "Médio",
    "Grande",
    "Muito grande",
)

PROFILE_ORDER = (
    "Q1",
    "Q2",
    "Q3",
    "Q4",
)

EXPECTED_HORIZONS = (
    1,
    2,
    3,
    4,
)

DISPLAY_COLUMNS = [
    "grupo",
    "horizonte",
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
    *,
    expected_groups: tuple[str, ...],
    name: str,
) -> None:
    """Valida a estrutura básica de um resultado de heterogeneidade."""
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
        raise ValueError(f"{name}: colunas ausentes: " + ", ".join(missing) + ".")

    groups = set(dataframe["grupo"].unique())

    if groups != set(expected_groups):
        raise ValueError(
            f"{name}: grupos inesperados. "
            f"Esperado: {expected_groups}; "
            f"obtido: {sorted(groups)}."
        )

    horizons = {int(value) for value in dataframe["horizonte"].unique()}

    if horizons != set(EXPECTED_HORIZONS):
        raise ValueError(f"{name}: horizontes inesperados.")

    subsets = set(dataframe["subconjunto"].unique())

    if subsets != {
        "geral",
        "early_warning",
    }:
        raise ValueError(f"{name}: subconjuntos inesperados.")


def prepare_display(
    dataframe: pd.DataFrame,
    *,
    group_order: tuple[str, ...],
) -> pd.DataFrame:
    """Prepara a tabela central de early warning para impressão."""
    output = dataframe.loc[
        dataframe["subconjunto"].eq("early_warning"),
        DISPLAY_COLUMNS,
    ].copy()

    output["grupo"] = pd.Categorical(
        output["grupo"],
        categories=group_order,
        ordered=True,
    )

    output = output.sort_values(
        [
            "horizonte",
            "grupo",
        ]
    ).reset_index(drop=True)

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


def print_dimension(
    *,
    title: str,
    path,
    group_order: tuple[str, ...],
) -> None:
    """Carrega, valida e imprime uma dimensão."""
    dataframe = pd.read_csv(path)

    validate_input(
        dataframe,
        expected_groups=group_order,
        name=title,
    )

    display = prepare_display(
        dataframe,
        group_order=group_order,
    )

    print()
    print("=" * 132)
    print(title)
    print("SUBCONJUNTO: EARLY WARNING")
    print("=" * 132)

    print(
        display.to_string(
            index=False,
        )
    )


def main() -> None:
    """Exibe os principais resultados de heterogeneidade."""
    print("=" * 132)
    print("RESUMO DA HETEROGENEIDADE PÓS-TESTE — 2025")
    print("=" * 132)

    print()
    print("Apenas organização dos resultados já calculados.")

    print("Nenhum score é recalculado.")

    print("Nenhum modelo é treinado.")

    print("Nenhum threshold é alterado.")

    print_dimension(
        title="MACRORREGIÃO",
        path=REGION_INPUT,
        group_order=REGION_ORDER,
    )

    print_dimension(
        title="PORTE POPULACIONAL",
        path=POPULATION_INPUT,
        group_order=POPULATION_ORDER,
    )

    print_dimension(
        title="PERFIL EPIDEMIOLÓGICO HISTÓRICO",
        path=PROFILE_INPUT,
        group_order=PROFILE_ORDER,
    )

    print()
    print("=" * 132)
    print("STATUS: RESUMO CONCLUÍDO")
    print("=" * 132)


if __name__ == "__main__":
    main()
