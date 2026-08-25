"""Gera a Figura 05 — distribuição da duração dos episódios de risco."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT / "reports" / "audits" / "episodios_risco_elevado_2018_2025.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT / "reports" / "figures" / "05_duracao_episodios_risco_2018_2025.png"
)

DURATION_COLUMN = "duracao_semanas"

EXPECTED_EPISODES = 54_269
EXPECTED_TOTAL_RISK_WEEKS = 414_678
EXPECTED_MINIMUM = 1
EXPECTED_MEDIAN = 4
EXPECTED_P90 = 19
EXPECTED_P95 = 26
EXPECTED_P99 = 41
EXPECTED_MAXIMUM = 110


def load_data() -> pd.DataFrame:
    """Carrega e valida os episódios históricos."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    dataframe = pd.read_csv(INPUT_FILE)

    if DURATION_COLUMN not in dataframe.columns:
        raise ValueError(f"Coluna obrigatória ausente: {DURATION_COLUMN}")

    if len(dataframe) != EXPECTED_EPISODES:
        raise ValueError(
            "Quantidade inesperada de episódios. "
            f"Esperado: {EXPECTED_EPISODES:,}; "
            f"obtido: {len(dataframe):,}."
        )

    duration = dataframe[DURATION_COLUMN]

    if duration.isna().any():
        raise ValueError("Existem durações ausentes.")

    if not np.isfinite(
        duration.to_numpy(
            dtype=np.float64,
            copy=False,
        )
    ).all():
        raise ValueError("Existem durações não finitas.")

    if duration.lt(1).any():
        raise ValueError("Existem episódios com duração inferior a uma semana.")

    total_weeks = int(duration.sum())

    if total_weeks != EXPECTED_TOTAL_RISK_WEEKS:
        raise ValueError(
            "A duração acumulada não preservou "
            "o total de semanas em risco. "
            f"Esperado: {EXPECTED_TOTAL_RISK_WEEKS:,}; "
            f"obtido: {total_weeks:,}."
        )

    return dataframe


def calculate_statistics(
    dataframe: pd.DataFrame,
) -> dict[str, float]:
    """Calcula estatísticas descritivas da duração."""
    duration = dataframe[DURATION_COLUMN]

    statistics = {
        "min": float(duration.min()),
        "p25": float(duration.quantile(0.25)),
        "p50": float(duration.quantile(0.50)),
        "p75": float(duration.quantile(0.75)),
        "p90": float(duration.quantile(0.90)),
        "p95": float(duration.quantile(0.95)),
        "p99": float(duration.quantile(0.99)),
        "max": float(duration.max()),
        "mean": float(duration.mean()),
    }

    expected = {
        "min": EXPECTED_MINIMUM,
        "p50": EXPECTED_MEDIAN,
        "p90": EXPECTED_P90,
        "p95": EXPECTED_P95,
        "p99": EXPECTED_P99,
        "max": EXPECTED_MAXIMUM,
    }

    for key, expected_value in expected.items():
        if not np.isclose(
            statistics[key],
            expected_value,
        ):
            raise ValueError(
                f"Valor inesperado para {key}. "
                f"Esperado: {expected_value}; "
                f"obtido: {statistics[key]}."
            )

    return statistics


def generate_figure(
    dataframe: pd.DataFrame,
    statistics: dict[str, float],
) -> None:
    """Gera o histograma da duração dos episódios."""
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    duration = dataframe[DURATION_COLUMN]

    bins = np.arange(
        EXPECTED_MINIMUM - 0.5,
        EXPECTED_MAXIMUM + 1.5,
        1,
    )

    fig, ax = plt.subplots(
        figsize=(
            13,
            7.5,
        )
    )

    ax.hist(
        duration,
        bins=bins,
        edgecolor="white",
        linewidth=0.25,
    )

    ax.set_yscale("log")

    reference_lines = [
        (
            "Mediana",
            statistics["p50"],
        ),
        (
            "P90",
            statistics["p90"],
        ),
        (
            "P95",
            statistics["p95"],
        ),
        (
            "P99",
            statistics["p99"],
        ),
    ]

    for label, value in reference_lines:
        ax.axvline(
            value,
            linestyle="--",
            linewidth=1.25,
            alpha=0.8,
        )

        ax.text(
            value + 0.8,
            0.96,
            (f"{label}\n{int(value)} sem."),
            transform=ax.get_xaxis_transform(),
            fontsize=9,
            va="top",
        )

    ax.annotate(
        (f"Maior episódio observado\n{int(statistics['max'])} semanas"),
        xy=(
            statistics["max"],
            1,
        ),
        xytext=(
            -135,
            45,
        ),
        textcoords="offset points",
        arrowprops={
            "arrowstyle": "->",
        },
        fontsize=9.5,
        ha="center",
    )

    ax.set_title(
        ("Duração dos episódios de risco elevado de dengue — 2018–2025"),
        fontsize=18,
        fontweight="bold",
        pad=30,
    )

    ax.text(
        0,
        1.015,
        ("Distribuição dos 54.269 episódios; eixo vertical em escala logarítmica"),
        transform=ax.transAxes,
        fontsize=10.5,
        va="bottom",
    )

    ax.set_xlabel(
        "Duração do episódio (semanas)",
        fontsize=11,
        labelpad=10,
    )

    ax.set_ylabel(
        "Número de episódios (escala logarítmica)",
        fontsize=11,
        labelpad=10,
    )

    ax.set_xlim(
        0.5,
        EXPECTED_MAXIMUM + 2,
    )

    ax.set_xticks(
        [
            1,
            4,
            10,
            20,
            30,
            40,
            50,
            60,
            70,
            80,
            90,
            100,
            110,
        ]
    )

    ax.grid(
        axis="y",
        alpha=0.20,
        linewidth=0.8,
        which="both",
    )

    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)

    ax.spines["right"].set_visible(False)

    statistics_text = (
        "Resumo da distribuição\n"
        f"Média: {statistics['mean']:.2f} semanas\n"
        f"P25: {int(statistics['p25'])} semanas\n"
        f"Mediana: {int(statistics['p50'])} semanas\n"
        f"P75: {int(statistics['p75'])} semanas\n"
        f"P90: {int(statistics['p90'])} semanas\n"
        f"P95: {int(statistics['p95'])} semanas\n"
        f"P99: {int(statistics['p99'])} semanas"
    ).replace(
        ".",
        ",",
    )

    ax.text(
        0.985,
        0.94,
        statistics_text,
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9.5,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": "white",
            "alpha": 0.9,
            "edgecolor": "0.75",
        },
    )

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
            "Nota: um episódio corresponde a uma sequência máxima "
            "de semanas consecutivas com risco_elevado=True."
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
    statistics: dict[str, float],
) -> None:
    """Exibe a auditoria resumida da Figura 05."""
    print("=" * 108)

    print("FIGURA 05 — DURAÇÃO DOS EPISÓDIOS DE RISCO")

    print("=" * 108)

    print()

    print(f"Episódios representados           : {len(dataframe):,}")

    print(
        f"Semanas de risco preservadas      : {int(dataframe[DURATION_COLUMN].sum()):,}"
    )

    print()

    print("DISTRIBUIÇÃO")

    print(f"Mínimo                            : {int(statistics['min'])} semana")

    print(f"Média                             : {statistics['mean']:.2f} semanas")

    print(f"P25                               : {int(statistics['p25'])} semanas")

    print(f"Mediana                           : {int(statistics['p50'])} semanas")

    print(f"P75                               : {int(statistics['p75'])} semanas")

    print(f"P90                               : {int(statistics['p90'])} semanas")

    print(f"P95                               : {int(statistics['p95'])} semanas")

    print(f"P99                               : {int(statistics['p99'])} semanas")

    print(f"Máximo                            : {int(statistics['max'])} semanas")

    print()

    print(f"Arquivo gerado                    : {OUTPUT_FILE}")

    print()

    print("STATUS: FIGURA GERADA")


def main() -> None:
    """Executa a geração da Figura 05."""
    dataframe = load_data()

    statistics = calculate_statistics(dataframe)

    generate_figure(
        dataframe,
        statistics,
    )

    print_summary(
        dataframe,
        statistics,
    )


if __name__ == "__main__":
    main()
