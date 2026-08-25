"""Gera a Figura 04 — municípios simultaneamente em risco, 2018–2025."""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "audits"
    / "serie_risco_semanal_nacional_regional_2018_2025.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "figures"
    / "04_municipios_simultaneamente_risco_2018_2025.png"
)

DATE_COLUMN = "data_inicio_semana"
YEAR_COLUMN = "ano_epidemiologico"
WEEK_COLUMN = "semana_epidemiologica"
RISK_COLUMN = "unidades_em_risco"
ELIGIBLE_COLUMN = "unidades_elegiveis"
PROPORTION_COLUMN = "proporcao_unidades_em_risco"

EXPECTED_WEEKS = 418
EXPECTED_ELIGIBLE_MUNICIPALITIES = 5_569

EXPECTED_PEAK_YEAR = 2024
EXPECTED_PEAK_WEEK = 12
EXPECTED_PEAK_MUNICIPALITIES = 3_121


def validate_input(
    dataframe: pd.DataFrame,
) -> None:
    """Valida a série nacional antes da geração da figura."""
    required_columns = {
        "escala",
        "grupo",
        YEAR_COLUMN,
        WEEK_COLUMN,
        DATE_COLUMN,
        ELIGIBLE_COLUMN,
        RISK_COLUMN,
        PROPORTION_COLUMN,
    }

    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(sorted(missing)))

    if len(dataframe) != EXPECTED_WEEKS:
        raise ValueError(
            "Quantidade inesperada de semanas nacionais. "
            f"Esperado: {EXPECTED_WEEKS}; "
            f"obtido: {len(dataframe)}."
        )

    if dataframe[DATE_COLUMN].duplicated().any():
        raise ValueError("Existem semanas nacionais duplicadas.")

    if not dataframe[ELIGIBLE_COLUMN].eq(EXPECTED_ELIGIBLE_MUNICIPALITIES).all():
        raise ValueError(
            "A quantidade de municípios elegíveis não permaneceu constante em 5.569."
        )

    if dataframe[RISK_COLUMN].lt(0).any():
        raise ValueError("Existem quantidades negativas de municípios em risco.")

    if dataframe[RISK_COLUMN].gt(dataframe[ELIGIBLE_COLUMN]).any():
        raise ValueError(
            "Existem semanas com mais municípios em risco do que municípios elegíveis."
        )

    expected_proportion = dataframe[RISK_COLUMN] / dataframe[ELIGIBLE_COLUMN]

    difference = (expected_proportion - dataframe[PROPORTION_COLUMN]).abs()

    if difference.max() > 1e-12:
        raise ValueError(
            "A proporção de municípios em risco não corresponde às contagens."
        )


def load_national_series() -> pd.DataFrame:
    """Carrega somente a série nacional."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    dataframe = pd.read_csv(
        INPUT_FILE,
        parse_dates=[
            DATE_COLUMN,
        ],
    )

    national = (
        dataframe.loc[
            dataframe["escala"].eq("nacional") & dataframe["grupo"].eq("Brasil")
        ]
        .copy()
        .sort_values(DATE_COLUMN)
        .reset_index(drop=True)
    )

    validate_input(national)

    return national


def validate_peak(
    dataframe: pd.DataFrame,
) -> pd.Series:
    """Valida o máximo nacional previamente auditado."""
    peak_index = dataframe[RISK_COLUMN].idxmax()

    peak = dataframe.loc[peak_index]

    if int(peak[YEAR_COLUMN]) != EXPECTED_PEAK_YEAR:
        raise ValueError("Ano inesperado para o pico nacional.")

    if int(peak[WEEK_COLUMN]) != EXPECTED_PEAK_WEEK:
        raise ValueError("Semana inesperada para o pico nacional.")

    if int(peak[RISK_COLUMN]) != EXPECTED_PEAK_MUNICIPALITIES:
        raise ValueError("Quantidade inesperada no pico nacional.")

    return peak


def generate_figure(
    dataframe: pd.DataFrame,
    peak: pd.Series,
) -> None:
    """Gera a série temporal nacional de municípios em risco."""
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(
            14,
            7.5,
        )
    )

    ax.plot(
        dataframe[DATE_COLUMN],
        dataframe[RISK_COLUMN],
        linewidth=1.8,
    )

    ax.fill_between(
        dataframe[DATE_COLUMN],
        dataframe[RISK_COLUMN],
        alpha=0.15,
    )

    peak_date = peak[DATE_COLUMN]

    peak_municipalities = int(peak[RISK_COLUMN])

    peak_proportion = float(peak[PROPORTION_COLUMN])

    ax.scatter(
        [
            peak_date,
        ],
        [
            peak_municipalities,
        ],
        s=55,
        zorder=4,
    )

    ax.annotate(
        (
            "Pico nacional\n"
            f"SE {int(peak[WEEK_COLUMN])} de "
            f"{int(peak[YEAR_COLUMN])}\n"
            f"{peak_municipalities:,} municípios "
            f"({peak_proportion:.2%})"
        ).replace(
            ",",
            ".",
        ),
        xy=(
            peak_date,
            peak_municipalities,
        ),
        xytext=(
            -115,
            55,
        ),
        textcoords="offset points",
        arrowprops={
            "arrowstyle": "->",
        },
        fontsize=10,
        ha="center",
    )

    for year in range(
        2019,
        2026,
    ):
        date = pd.Timestamp(
            year=year,
            month=1,
            day=1,
        )

        ax.axvline(
            date,
            linewidth=0.6,
            alpha=0.16,
        )

    ax.set_title(
        ("Municípios simultaneamente em risco elevado de dengue — 2018–2025"),
        fontsize=18,
        fontweight="bold",
        pad=30,
    )

    ax.text(
        0,
        1.015,
        ("Quantidade semanal de municípios acima de seus limiares sazonais históricos"),
        transform=ax.transAxes,
        fontsize=10.5,
        va="bottom",
    )

    ax.set_xlabel(
        "Semana epidemiológica",
        fontsize=11,
        labelpad=10,
    )

    ax.set_ylabel(
        "Municípios em risco elevado",
        fontsize=11,
        labelpad=10,
    )

    ax.set_ylim(
        bottom=0,
        top=EXPECTED_ELIGIBLE_MUNICIPALITIES,
    )

    ax.set_xlim(
        dataframe[DATE_COLUMN].min(),
        dataframe[DATE_COLUMN].max(),
    )

    ax.xaxis.set_major_locator(mdates.YearLocator())

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    ax.grid(
        axis="y",
        alpha=0.22,
        linewidth=0.8,
    )

    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)

    ax.spines["right"].set_visible(False)

    fig.text(
        0.01,
        0.01,
        (
            "Fonte: elaboração própria a partir dos targets "
            "históricos do projeto Dengue Alert."
        ),
        fontsize=9,
        ha="left",
    )

    fig.text(
        0.01,
        0.035,
        (
            "Nota: risco elevado corresponde à incidência acumulada "
            "em quatro semanas acima do limiar sazonal P90 municipal."
        ),
        fontsize=8.5,
        ha="left",
    )

    fig.savefig(
        OUTPUT_FILE,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)


def print_summary(
    dataframe: pd.DataFrame,
    peak: pd.Series,
) -> None:
    """Exibe auditoria resumida da figura."""
    print("=" * 108)

    print("FIGURA 04 — MUNICÍPIOS SIMULTANEAMENTE EM RISCO")

    print("=" * 108)

    print()

    print(f"Semanas representadas             : {len(dataframe):,}")

    print(f"Municípios elegíveis              : {EXPECTED_ELIGIBLE_MUNICIPALITIES:,}")

    print(f"Início da série                   : {dataframe[DATE_COLUMN].min().date()}")

    print(f"Fim da série                      : {dataframe[DATE_COLUMN].max().date()}")

    print()

    print("PICO NACIONAL")

    print(f"Ano epidemiológico                : {int(peak[YEAR_COLUMN])}")

    print(f"Semana epidemiológica             : {int(peak[WEEK_COLUMN])}")

    print(f"Data inicial                      : {peak[DATE_COLUMN].date()}")

    print(f"Municípios em risco               : {int(peak[RISK_COLUMN]):,}")

    print(f"Proporção                         : {float(peak[PROPORTION_COLUMN]):.2%}")

    print()

    print(f"Arquivo gerado                    : {OUTPUT_FILE}")

    print()

    print("STATUS: FIGURA GERADA")


def main() -> None:
    """Executa a geração da Figura 04."""
    dataframe = load_national_series()

    peak = validate_peak(dataframe)

    generate_figure(
        dataframe,
        peak,
    )

    print_summary(
        dataframe,
        peak,
    )


if __name__ == "__main__":
    main()
