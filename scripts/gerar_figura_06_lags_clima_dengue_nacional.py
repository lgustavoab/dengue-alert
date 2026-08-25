"""Gera a Figura 06 — perfil nacional de lags entre clima e dengue."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "audits"
    / "associacao_clima_dengue_nacional_2016_2025.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT / "reports" / "figures" / "06_lags_clima_dengue_nacional_2016_2025.png"
)

VARIABLE_COLUMN = "variavel_climatica"
LAG_COLUMN = "lag_semanas"
CORRELATION_COLUMN = "correlacao_mediana"
VALID_MUNICIPALITIES_COLUMN = "municipios_correlacao_valida"

EXPECTED_LAGS = [
    0,
    1,
    2,
    3,
    4,
    6,
    8,
]

VARIABLES = {
    "temperatura_media_c": "Temperatura média",
    "umidade_relativa_media_pct": "Umidade relativa",
    "precipitacao_total_mm": "Precipitação total",
}

EXPECTED_ROWS = len(EXPECTED_LAGS) * len(VARIABLES)

EXPECTED_VALID_MUNICIPALITIES = 5_560


def format_decimal_br(
    value: float,
) -> str:
    """Formata valores decimais com vírgula."""
    return f"{value:.3f}".replace(
        ".",
        ",",
    )


def load_data() -> pd.DataFrame:
    """Carrega e valida o resumo nacional clima × dengue."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    dataframe = pd.read_csv(INPUT_FILE)

    required_columns = {
        VARIABLE_COLUMN,
        LAG_COLUMN,
        CORRELATION_COLUMN,
        VALID_MUNICIPALITIES_COLUMN,
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

    variables = set(dataframe[VARIABLE_COLUMN].unique())

    if variables != set(VARIABLES):
        raise ValueError("Conjunto inesperado de variáveis climáticas.")

    for variable in VARIABLES:
        subset = dataframe.loc[dataframe[VARIABLE_COLUMN].eq(variable)]

        lags = subset[LAG_COLUMN].astype(int).sort_values().tolist()

        if lags != EXPECTED_LAGS:
            raise ValueError(f"Lags inesperados para {variable}: {lags}.")

    if (
        not dataframe[VALID_MUNICIPALITIES_COLUMN]
        .eq(EXPECTED_VALID_MUNICIPALITIES)
        .all()
    ):
        raise ValueError("Quantidade inesperada de municípios com correlação válida.")

    values = dataframe[CORRELATION_COLUMN].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    if not np.isfinite(values).all():
        raise ValueError("Existem correlações medianas não finitas.")

    return dataframe


def identify_peaks(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Identifica maior associação mediana em magnitude por variável."""
    candidates = dataframe.copy()

    candidates["magnitude_correlacao"] = candidates[CORRELATION_COLUMN].abs()

    peaks = (
        candidates.sort_values(
            [
                VARIABLE_COLUMN,
                "magnitude_correlacao",
                LAG_COLUMN,
            ],
            ascending=[
                True,
                False,
                True,
            ],
        )
        .drop_duplicates(
            subset=[VARIABLE_COLUMN],
            keep="first",
        )
        .reset_index(drop=True)
    )

    return peaks


def generate_figure(
    dataframe: pd.DataFrame,
    peaks: pd.DataFrame,
) -> None:
    """Gera o perfil nacional das associações por lag."""
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(
            13,
            7.5,
        )
    )

    for variable, label in VARIABLES.items():
        subset = dataframe.loc[dataframe[VARIABLE_COLUMN].eq(variable)].sort_values(
            LAG_COLUMN
        )

        ax.plot(
            subset[LAG_COLUMN],
            subset[CORRELATION_COLUMN],
            marker="o",
            linewidth=2.2,
            markersize=6,
            label=label,
        )

    ax.axhline(
        0,
        linewidth=0.9,
        alpha=0.45,
    )

    annotation_offsets = {
        "temperatura_media_c": (
            -115,
            45,
        ),
        "umidade_relativa_media_pct": (
            -15,
            55,
        ),
        "precipitacao_total_mm": (
            25,
            -55,
        ),
    }

    for row in peaks.itertuples(index=False):
        variable = getattr(
            row,
            VARIABLE_COLUMN,
        )

        lag = int(
            getattr(
                row,
                LAG_COLUMN,
            )
        )

        correlation = float(
            getattr(
                row,
                CORRELATION_COLUMN,
            )
        )

        label = VARIABLES[variable]

        offset = annotation_offsets[variable]

        ax.annotate(
            (
                f"{label}\n"
                f"maior associação observada: "
                f"lag {lag}\n"
                f"ρ = {format_decimal_br(correlation)}"
            ),
            xy=(
                lag,
                correlation,
            ),
            xytext=offset,
            textcoords="offset points",
            arrowprops={
                "arrowstyle": "->",
            },
            fontsize=9,
            ha="center",
        )

    max_correlation = float(dataframe[CORRELATION_COLUMN].max())

    min_correlation = float(dataframe[CORRELATION_COLUMN].min())

    lower_limit = min(
        -0.015,
        min_correlation - 0.02,
    )

    upper_limit = max_correlation + 0.065

    ax.set_ylim(
        lower_limit,
        upper_limit,
    )

    ax.set_xticks(EXPECTED_LAGS)

    ax.set_xlabel(
        "Defasagem climática (semanas)",
        fontsize=11,
        labelpad=10,
    )

    ax.set_ylabel(
        "Correlação de Spearman mediana municipal",
        fontsize=11,
        labelpad=10,
    )

    ax.set_title(
        ("Associação temporal entre clima e dengue no Brasil — 2016–2025"),
        fontsize=18,
        fontweight="bold",
        pad=32,
    )

    ax.text(
        0,
        1.015,
        (
            "Clima observado em t−k comparado à incidência "
            "municipal de dengue observada em t"
        ),
        transform=ax.transAxes,
        fontsize=10.5,
        va="bottom",
    )

    ax.grid(
        alpha=0.22,
        linewidth=0.8,
    )

    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)

    ax.spines["right"].set_visible(False)

    ax.legend(
        loc="upper left",
        frameon=False,
        fontsize=10,
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
        0.035,
        (
            "Nota: correlação não implica causalidade. "
            "As maiores associações indicadas referem-se apenas "
            "aos lags pré-especificados de 0 a 8 semanas."
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
    peaks: pd.DataFrame,
) -> None:
    """Exibe auditoria resumida da Figura 06."""
    print("=" * 112)

    print("FIGURA 06 — PERFIL NACIONAL CLIMA × DENGUE")

    print("=" * 112)

    print()

    print(f"Variáveis representadas           : {len(VARIABLES)}")

    print(f"Lags representados                : {EXPECTED_LAGS}")

    print(f"Municípios válidos por combinação : {EXPECTED_VALID_MUNICIPALITIES:,}")

    print()

    print("MAIOR ASSOCIAÇÃO MEDIANA EM MAGNITUDE")

    for row in peaks.itertuples(index=False):
        variable = getattr(
            row,
            VARIABLE_COLUMN,
        )

        lag = int(
            getattr(
                row,
                LAG_COLUMN,
            )
        )

        correlation = float(
            getattr(
                row,
                CORRELATION_COLUMN,
            )
        )

        print(f"  {VARIABLES[variable]:<20} : lag {lag} | ρ = {correlation:.6f}")

    print()

    print("INTERVALO DAS CORRELAÇÕES MEDIANAS")

    print(
        f"Mínimo                            : {dataframe[CORRELATION_COLUMN].min():.6f}"
    )

    print(
        f"Máximo                            : {dataframe[CORRELATION_COLUMN].max():.6f}"
    )

    print()

    print(f"Arquivo gerado                    : {OUTPUT_FILE}")

    print()

    print("STATUS: FIGURA GERADA")


def main() -> None:
    """Executa a geração da Figura 06."""
    dataframe = load_data()

    peaks = identify_peaks(dataframe)

    generate_figure(
        dataframe,
        peaks,
    )

    print_summary(
        dataframe,
        peaks,
    )


if __name__ == "__main__":
    main()
