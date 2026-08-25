"""Figura 02 — sazonalidade regional da dengue no Brasil (2016–2025)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDITS_DIR = PROJECT_ROOT / "reports" / "audits"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

REGIONAL_INPUT = (
    AUDITS_DIR / "sazonalidade_regional_semana_epidemiologica_2016_2025.csv"
)
NATIONAL_INPUT = (
    AUDITS_DIR / "sazonalidade_nacional_semana_epidemiologica_2016_2025.csv"
)
OUTPUT_FIGURE = FIGURES_DIR / "02_sazonalidade_regional_2016_2025.png"

REGION_ORDER = [
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul",
]

REGIONAL_REQUIRED_COLUMNS = {
    "regiao",
    "semana_epidemiologica",
    "anos_disponiveis",
    "incidencia_media_100mil",
    "incidencia_mediana_100mil",
    "incidencia_q25_100mil",
    "incidencia_q75_100mil",
}

NATIONAL_REQUIRED_COLUMNS = {
    "semana_epidemiologica",
    "anos_disponiveis",
    "incidencia_media_100mil",
    "incidencia_mediana_100mil",
    "incidencia_q25_100mil",
    "incidencia_q75_100mil",
}


def ensure_required_columns(
    dataframe: pd.DataFrame,
    required_columns: set[str],
    *,
    dataset_name: str,
) -> None:
    """Valida se todas as colunas necessárias estão presentes."""
    missing_columns = sorted(required_columns - set(dataframe.columns))

    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(
            f"{dataset_name} não possui todas as colunas esperadas. Ausentes: {missing}."
        )


def format_decimal_br(value: float) -> str:
    """Formata número decimal em padrão brasileiro."""
    return f"{value:.2f}".replace(".", ",")


def format_axis_thousands(value: float, _: int) -> str:
    """Formata valores do eixo Y em padrão numérico simples."""
    if abs(value - round(value)) < 1e-9:
        return f"{round(value)}"
    return f"{value:.1f}".replace(".", ",")


def load_input_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega e valida os datasets de sazonalidade."""
    if not REGIONAL_INPUT.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {REGIONAL_INPUT}")

    if not NATIONAL_INPUT.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {NATIONAL_INPUT}")

    regional = pd.read_csv(REGIONAL_INPUT)
    national = pd.read_csv(NATIONAL_INPUT)

    ensure_required_columns(
        regional,
        REGIONAL_REQUIRED_COLUMNS,
        dataset_name="Sazonalidade regional",
    )
    ensure_required_columns(
        national,
        NATIONAL_REQUIRED_COLUMNS,
        dataset_name="Sazonalidade nacional",
    )

    regional["semana_epidemiologica"] = regional["semana_epidemiologica"].astype(int)
    national["semana_epidemiologica"] = national["semana_epidemiologica"].astype(int)

    regional = regional.sort_values(
        [
            "regiao",
            "semana_epidemiologica",
        ]
    ).reset_index(drop=True)

    national = national.sort_values("semana_epidemiologica").reset_index(drop=True)

    found_regions = set(regional["regiao"].unique())

    if found_regions != set(REGION_ORDER):
        raise ValueError(
            "As regiões encontradas no arquivo regional não correspondem ao esperado. "
            f"Encontradas: {sorted(found_regions)} | Esperadas: {REGION_ORDER}"
        )

    expected_weeks = set(national["semana_epidemiologica"].unique())

    for region in REGION_ORDER:
        region_weeks = set(
            regional.loc[
                regional["regiao"] == region,
                "semana_epidemiologica",
            ].unique()
        )

        if region_weeks != expected_weeks:
            raise ValueError(
                f"A região {region} não possui a mesma grade semanal da série nacional."
            )

    return regional, national


def build_figure(
    regional: pd.DataFrame,
    national: pd.DataFrame,
) -> None:
    """Gera a figura consolidada de sazonalidade regional."""
    FIGURES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(
        figsize=(14, 8),
    )

    national = national.sort_values("semana_epidemiologica")

    ax.fill_between(
        national["semana_epidemiologica"],
        national["incidencia_q25_100mil"],
        national["incidencia_q75_100mil"],
        alpha=0.18,
        label="Brasil (Q25–Q75)",
    )

    for region in REGION_ORDER:
        subset = regional.loc[regional["regiao"] == region].sort_values(
            "semana_epidemiologica"
        )

        ax.plot(
            subset["semana_epidemiologica"],
            subset["incidencia_media_100mil"],
            linewidth=2.2,
            label=region,
        )

    ax.plot(
        national["semana_epidemiologica"],
        national["incidencia_media_100mil"],
        linestyle="--",
        linewidth=2.8,
        label="Brasil (média)",
    )

    min_week = int(national["semana_epidemiologica"].min())
    max_week = int(national["semana_epidemiologica"].max())

    tick_step = 4
    xticks = list(range(min_week, max_week + 1, tick_step))

    if xticks[-1] != max_week:
        xticks.append(max_week)

    ax.set_xlim(
        min_week,
        max_week,
    )
    ax.set_xticks(xticks)
    ax.set_xlabel("Semana epidemiológica", fontsize=12)
    ax.set_ylabel("Incidência média por 100 mil habitantes", fontsize=12)

    ax.yaxis.set_major_formatter(FuncFormatter(format_axis_thousands))
    ax.grid(
        axis="y",
        alpha=0.3,
    )

    ax.set_title(
        "Sazonalidade regional da dengue no Brasil — 2016–2025",
        fontsize=20,
        fontweight="bold",
        pad=34,
    )

    ax.text(
        0.0,
        1.01,
        (
            "Curvas médias semanais por macrorregião; "
            "a faixa sombreada representa o intervalo interquartil nacional."
        ),
        transform=ax.transAxes,
        fontsize=11,
        va="bottom",
    )

    ax.legend(
        loc="upper left",
        bbox_to_anchor=(0.0, -0.16),
        ncol=3,
        frameon=False,
    )

    fig.text(
        0.01,
        0.01,
        "Fonte: elaboração própria a partir do painel epidemiológico municipal (SINAN/OpenDataSUS e IBGE).",
        fontsize=10,
    )

    fig.savefig(
        OUTPUT_FIGURE,
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)


def print_summary(
    regional: pd.DataFrame,
    national: pd.DataFrame,
) -> None:
    """Imprime resumo executivo da figura gerada."""
    national_peak = national.loc[national["incidencia_media_100mil"].idxmax()]

    print("=" * 92)
    print("FIGURA 02 — SAZONALIDADE REGIONAL DA DENGUE")
    print("=" * 92)
    print()
    print("Período                           : 2016–2025")
    print(
        "Semanas representadas             : "
        f"{national['semana_epidemiologica'].nunique()}"
    )
    print(f"Regiões representadas             : {len(REGION_ORDER)}")
    print("Métrica principal                 : incidência média por 100 mil hab.")
    print(
        "Pico nacional da média            : "
        f"SE {int(national_peak['semana_epidemiologica'])}"
    )
    print(
        "Incidência média no pico nacional : "
        f"{format_decimal_br(float(national_peak['incidencia_media_100mil']))}"
    )
    print()

    print("PICOS REGIONAIS (incidência média)")
    for region in REGION_ORDER:
        subset = regional.loc[regional["regiao"] == region]
        peak_row = subset.loc[subset["incidencia_media_100mil"].idxmax()]

        print(
            f"  {region:<15} : "
            f"SE {int(peak_row['semana_epidemiologica']):>2} | "
            f"{format_decimal_br(float(peak_row['incidencia_media_100mil']))} por 100 mil"
        )

    print()
    print(f"Arquivo gerado                    : {OUTPUT_FIGURE}")
    print()
    print("STATUS: FIGURA GERADA")


def main() -> None:
    """Executa a geração da figura."""
    regional, national = load_input_data()
    build_figure(
        regional,
        national,
    )
    print_summary(
        regional,
        national,
    )


if __name__ == "__main__":
    main()
