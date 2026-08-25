"""Gera a Figura 07 — heterogeneidade regional clima × dengue."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "audits"
    / "associacao_clima_dengue_regional_2016_2025.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT / "reports" / "figures" / "07_lags_clima_dengue_regional_2016_2025.png"
)

REGION_COLUMN = "regiao"
VARIABLE_COLUMN = "variavel_climatica"
LAG_COLUMN = "lag_semanas"
CORRELATION_COLUMN = "correlacao_mediana"

EXPECTED_LAGS = [
    0,
    1,
    2,
    3,
    4,
    6,
    8,
]

REGIONS = [
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul",
]

VARIABLES = {
    "temperatura_media_c": "Temperatura média",
    "umidade_relativa_media_pct": "Umidade relativa",
    "precipitacao_total_mm": "Precipitação total",
}

EXPECTED_ROWS = len(REGIONS) * len(VARIABLES) * len(EXPECTED_LAGS)


def load_data() -> pd.DataFrame:
    """Carrega e valida o resumo regional clima × dengue."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    dataframe = pd.read_csv(INPUT_FILE)

    required_columns = {
        REGION_COLUMN,
        VARIABLE_COLUMN,
        LAG_COLUMN,
        CORRELATION_COLUMN,
        "municipios_correlacao_valida",
        "correlacao_p25",
        "correlacao_p75",
        "proporcao_correlacao_positiva",
    }

    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(sorted(missing)))

    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas. "
            f"Esperado: {EXPECTED_ROWS}; "
            f"obtido: {len(dataframe)}."
        )

    if set(dataframe[REGION_COLUMN].unique()) != set(REGIONS):
        raise ValueError("Conjunto inesperado de macrorregiões.")

    if set(dataframe[VARIABLE_COLUMN].unique()) != set(VARIABLES):
        raise ValueError("Conjunto inesperado de variáveis climáticas.")

    for region in REGIONS:
        for variable in VARIABLES:
            subset = dataframe.loc[
                dataframe[REGION_COLUMN].eq(region)
                & dataframe[VARIABLE_COLUMN].eq(variable)
            ]

            lags = subset[LAG_COLUMN].astype(int).sort_values().tolist()

            if lags != EXPECTED_LAGS:
                raise ValueError(
                    f"Lags inesperados para {region} × {variable}: {lags}."
                )

    correlations = dataframe[CORRELATION_COLUMN].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    if not np.isfinite(correlations).all():
        raise ValueError("Existem correlações não finitas.")

    return dataframe


def identify_peak(
    dataframe: pd.DataFrame,
    *,
    region: str,
    variable: str,
) -> pd.Series:
    """Identifica a maior associação em magnitude."""
    subset = dataframe.loc[
        dataframe[REGION_COLUMN].eq(region) & dataframe[VARIABLE_COLUMN].eq(variable)
    ].copy()

    subset["magnitude"] = subset[CORRELATION_COLUMN].abs()

    return subset.sort_values(
        [
            "magnitude",
            LAG_COLUMN,
        ],
        ascending=[
            False,
            True,
        ],
    ).iloc[0]


def generate_figure(
    dataframe: pd.DataFrame,
) -> None:
    """Gera a comparação regional por variável climática."""
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, axes = plt.subplots(
        nrows=3,
        ncols=1,
        figsize=(
            13,
            13,
        ),
        sharex=True,
        sharey=True,
    )

    for ax, (
        variable,
        variable_label,
    ) in zip(
        axes,
        VARIABLES.items(),
        strict=True,
    ):
        variable_data = dataframe.loc[dataframe[VARIABLE_COLUMN].eq(variable)]

        for region in REGIONS:
            subset = variable_data.loc[
                variable_data[REGION_COLUMN].eq(region)
            ].sort_values(LAG_COLUMN)

            ax.plot(
                subset[LAG_COLUMN],
                subset[CORRELATION_COLUMN],
                marker="o",
                markersize=4.5,
                linewidth=1.8,
                label=region,
            )

        ax.axhline(
            0,
            linewidth=0.8,
            alpha=0.45,
        )

        ax.set_title(
            variable_label,
            fontsize=13,
            fontweight="bold",
            loc="left",
            pad=8,
        )

        ax.grid(
            alpha=0.20,
            linewidth=0.8,
        )

        ax.set_axisbelow(True)

        ax.spines["top"].set_visible(False)

        ax.spines["right"].set_visible(False)

    global_min = float(dataframe[CORRELATION_COLUMN].min())

    global_max = float(dataframe[CORRELATION_COLUMN].max())

    lower_limit = min(
        -0.15,
        global_min - 0.025,
    )

    upper_limit = max(
        0.35,
        global_max + 0.025,
    )

    for ax in axes:
        ax.set_ylim(
            lower_limit,
            upper_limit,
        )

        ax.set_ylabel(
            "Spearman mediano",
            fontsize=10.5,
        )

    axes[-1].set_xticks(EXPECTED_LAGS)

    axes[-1].set_xlabel(
        "Defasagem climática (semanas)",
        fontsize=11,
        labelpad=10,
    )

    axes[0].legend(
        loc="upper left",
        ncol=5,
        frameon=False,
        fontsize=9.5,
        bbox_to_anchor=(
            0,
            1.18,
        ),
    )

    fig.suptitle(
        ("Heterogeneidade regional das associações entre clima e dengue — 2016–2025"),
        fontsize=18,
        fontweight="bold",
        y=0.985,
    )

    fig.text(
        0.125,
        0.955,
        (
            "Correlação de Spearman mediana municipal "
            "segundo região, variável climática e defasagem"
        ),
        fontsize=10.5,
    )

    fig.text(
        0.01,
        0.01,
        ("Fonte: elaboração própria a partir do painel municipal semanal e ERA5-Land."),
        fontsize=9,
        ha="left",
    )

    fig.text(
        0.01,
        0.028,
        (
            "Nota: correlação não implica causalidade. "
            "Os perfis representam associações históricas "
            "dentro dos lags pré-especificados."
        ),
        fontsize=8.5,
        ha="left",
    )

    fig.subplots_adjust(
        top=0.90,
        bottom=0.08,
        hspace=0.22,
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
) -> None:
    """Exibe auditoria resumida da Figura 07."""
    print("=" * 116)

    print("FIGURA 07 — HETEROGENEIDADE REGIONAL CLIMA × DENGUE")

    print("=" * 116)

    print()

    print(f"Regiões representadas             : {len(REGIONS)}")

    print(f"Variáveis representadas           : {len(VARIABLES)}")

    print(f"Lags representados                : {EXPECTED_LAGS}")

    print()

    print("MAIOR ASSOCIAÇÃO EM MAGNITUDE — REGIÃO × VARIÁVEL")

    for region in REGIONS:
        print()

        print(region.upper())

        for variable, label in VARIABLES.items():
            peak = identify_peak(
                dataframe,
                region=region,
                variable=variable,
            )

            print(
                f"  {label:<20} : "
                f"lag {int(peak[LAG_COLUMN])} | "
                f"ρ = {float(peak[CORRELATION_COLUMN]):.6f}"
            )

    print()

    print(
        "Intervalo global das medianas      : "
        f"{dataframe[CORRELATION_COLUMN].min():.6f} "
        "a "
        f"{dataframe[CORRELATION_COLUMN].max():.6f}"
    )

    print()

    print(f"Arquivo gerado                    : {OUTPUT_FILE}")

    print()

    print("STATUS: FIGURA GERADA")


def main() -> None:
    """Executa a geração da Figura 07."""
    dataframe = load_data()

    generate_figure(dataframe)

    print_summary(dataframe)


if __name__ == "__main__":
    main()
