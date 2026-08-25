"""Gera a Figura 01 — panorama nacional de casos de dengue, 2016–2025."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from dengue_alert.config.paths import REPORTS_DIR

INPUT_FILE = REPORTS_DIR / "audits" / "panorama_nacional_anual_2016_2025.csv"

OUTPUT_FILE = REPORTS_DIR / "figures" / "01_panorama_nacional_casos_2016_2025.png"

EXPECTED_YEARS = list(
    range(
        2016,
        2026,
    )
)

YEAR_COLUMN = "ano_epidemiologico"
CASES_COLUMN = "casos_provaveis"


def format_millions(
    value: float,
    _position: float,
) -> str:
    """Formata o eixo vertical em milhões com vírgula decimal."""
    if value == 0:
        return "0"

    millions = value / 1_000_000

    return (
        f"{millions:.1f}".replace(
            ".",
            ",",
        )
        + " mi"
    )


def format_case_label(
    value: int,
) -> str:
    """Formata rótulos das barras em padrão compacto."""
    if value >= 1_000_000:
        return (
            f"{value / 1_000_000:.2f}".replace(
                ".",
                ",",
            )
            + " mi"
        )

    return (
        f"{value / 1_000:.0f}".replace(
            ".",
            ",",
        )
        + " mil"
    )


def validate_input(
    dataframe: pd.DataFrame,
) -> None:
    """Valida o artefato anual antes da geração da figura."""
    required_columns = {
        YEAR_COLUMN,
        CASES_COLUMN,
    }

    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        raise ValueError(
            "Colunas obrigatórias ausentes: " + ", ".join(sorted(missing_columns))
        )

    if dataframe[YEAR_COLUMN].duplicated().any():
        raise ValueError("Existem anos duplicados no panorama nacional.")

    years = dataframe[YEAR_COLUMN].astype(int).sort_values().tolist()

    if years != EXPECTED_YEARS:
        raise ValueError(
            f"Período inesperado. Esperado: {EXPECTED_YEARS}; obtido: {years}."
        )

    if dataframe[CASES_COLUMN].isna().any():
        raise ValueError("Existem valores ausentes de casos.")

    if dataframe[CASES_COLUMN].lt(0).any():
        raise ValueError("Existem valores negativos de casos.")


def calculate_reduction(
    dataframe: pd.DataFrame,
    *,
    previous_year: int,
    current_year: int,
) -> float:
    """Calcula a redução percentual entre dois anos."""
    previous_cases = int(
        dataframe.loc[
            dataframe[YEAR_COLUMN].eq(previous_year),
            CASES_COLUMN,
        ].iloc[0]
    )

    current_cases = int(
        dataframe.loc[
            dataframe[YEAR_COLUMN].eq(current_year),
            CASES_COLUMN,
        ].iloc[0]
    )

    if previous_cases <= 0:
        raise ValueError("O ano de referência possui casos menores ou iguais a zero.")

    return (1 - (current_cases / previous_cases)) * 100


def generate_figure(
    dataframe: pd.DataFrame,
    output_file: Path,
) -> None:
    """Gera e salva a figura do panorama nacional."""
    dataframe = dataframe.sort_values(YEAR_COLUMN).reset_index(drop=True)

    years = dataframe[YEAR_COLUMN].astype(int)

    cases = dataframe[CASES_COLUMN].astype(int)

    peak_index = cases.idxmax()

    peak_year = int(
        dataframe.loc[
            peak_index,
            YEAR_COLUMN,
        ]
    )

    peak_cases = int(
        dataframe.loc[
            peak_index,
            CASES_COLUMN,
        ]
    )

    reduction_2025 = calculate_reduction(
        dataframe,
        previous_year=2024,
        current_year=2025,
    )

    fig, ax = plt.subplots(
        figsize=(
            11,
            6.5,
        ),
        constrained_layout=True,
    )

    bars = ax.bar(
        years.astype(str),
        cases,
        width=0.72,
    )

    peak_bar = bars[peak_index]

    peak_bar.set_hatch("///")

    ax.set_title(
        "Casos prováveis de dengue no Brasil — 2016–2025",
        fontsize=16,
        fontweight="bold",
        pad=18,
    )

    ax.text(
        0,
        1.015,
        ("Série anual consolidada a partir do painel epidemiológico municipal"),
        transform=ax.transAxes,
        fontsize=10,
        va="bottom",
    )

    ax.set_xlabel(
        "Ano epidemiológico",
        fontsize=11,
        labelpad=10,
    )

    ax.set_ylabel(
        "Casos prováveis",
        fontsize=11,
        labelpad=10,
    )

    ax.yaxis.set_major_formatter(FuncFormatter(format_millions))

    ax.set_ylim(
        bottom=0,
        top=peak_cases * 1.18,
    )

    ax.grid(
        axis="y",
        alpha=0.22,
        linewidth=0.8,
    )

    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)

    ax.spines["right"].set_visible(False)

    for bar, value in zip(
        bars,
        cases,
        strict=True,
    ):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + peak_cases * 0.012,
            format_case_label(int(value)),
            ha="center",
            va="bottom",
            fontsize=8.5,
            rotation=0,
        )

    ax.annotate(
        (f"Maior valor da série\n{peak_year}: {peak_cases:,} casos").replace(
            ",",
            ".",
        ),
        xy=(
            peak_index,
            peak_cases,
        ),
        xytext=(
            peak_index - 1.3,
            peak_cases * 1.105,
        ),
        textcoords="data",
        arrowprops={
            "arrowstyle": "->",
        },
        fontsize=10,
        ha="right",
        va="center",
    )

    year_2025_index = int(dataframe.index[dataframe[YEAR_COLUMN].eq(2025)][0])

    cases_2025 = int(
        dataframe.loc[
            year_2025_index,
            CASES_COLUMN,
        ]
    )

    ax.annotate(
        (f"2025: redução de {reduction_2025:.1f}% em relação a 2024").replace(
            ".",
            ",",
        ),
        xy=(
            year_2025_index,
            cases_2025,
        ),
        xytext=(
            year_2025_index - 1.2,
            peak_cases * 0.48,
        ),
        arrowprops={
            "arrowstyle": "->",
        },
        fontsize=9.5,
        ha="center",
        va="center",
    )

    fig.text(
        0.01,
        0.005,
        ("Fonte: elaboração própria a partir de SINAN/OpenDataSUS e IBGE."),
        fontsize=8.5,
        ha="left",
    )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.savefig(
        output_file,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)


def main() -> None:
    """Executa a geração da Figura 01."""
    print("=" * 92)

    print("FIGURA 01 — PANORAMA NACIONAL DE CASOS DE DENGUE")

    print("=" * 92)

    dataframe = pd.read_csv(INPUT_FILE)

    validate_input(dataframe)

    peak_row = dataframe.loc[dataframe[CASES_COLUMN].idxmax()]

    reduction_2025 = calculate_reduction(
        dataframe,
        previous_year=2024,
        current_year=2025,
    )

    generate_figure(
        dataframe,
        OUTPUT_FILE,
    )

    print()

    print(
        "Período                           : "
        f"{int(dataframe[YEAR_COLUMN].min())}"
        "–"
        f"{int(dataframe[YEAR_COLUMN].max())}"
    )

    print(f"Anos representados                : {len(dataframe):,}")

    print(f"Total de casos no período         : {int(dataframe[CASES_COLUMN].sum()):,}")

    print(f"Ano de maior número de casos      : {int(peak_row[YEAR_COLUMN])}")

    print(f"Casos no maior ano                : {int(peak_row[CASES_COLUMN]):,}")

    print(f"Redução 2025 × 2024               : {reduction_2025:.2f}%")

    print()

    print(f"Arquivo gerado                    : {OUTPUT_FILE}")

    print()

    print("STATUS: FIGURA GERADA")


if __name__ == "__main__":
    main()
