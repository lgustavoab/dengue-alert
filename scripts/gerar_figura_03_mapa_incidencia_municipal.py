"""Gera a Figura 03 — mapa da incidência histórica municipal de dengue."""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SHAPEFILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "geography"
    / "ibge_municipios_2024"
    / "BR_Municipios_2024.shp"
)

DATA_FILE = (
    PROJECT_ROOT
    / "reports"
    / "audits"
    / "distribuicao_espacial_municipio_periodo_2016_2025.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "figures"
    / "03_mapa_incidencia_mediana_municipal_2016_2025.png"
)

GEOGRAPHIC_CRS = 4674
PLOT_CRS = 5880

GEOMETRY_CODE_COLUMN = "CD_MUN"
DATA_CODE_COLUMN = "codigo_ibge_7"
INCIDENCE_COLUMN = "incidencia_mediana_anual_100mil"

EXPECTED_GEOMETRIES = 5_573
EXPECTED_DATA_TERRITORIES = 5_571

EXPECTED_EXTRA_GEOMETRIES = {
    "4300001",
    "4300002",
}

QUANTILES = [
    0.25,
    0.50,
    0.75,
    0.90,
    0.95,
    0.99,
]


def format_decimal_br(
    value: float,
) -> str:
    """Formata decimal com separadores brasileiros."""
    text = f"{value:,.0f}"

    return (
        text.replace(
            ",",
            "X",
        )
        .replace(
            ".",
            ",",
        )
        .replace(
            "X",
            ".",
        )
    )


def load_data() -> pd.DataFrame:
    """Carrega e valida os indicadores epidemiológicos municipais."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Arquivo epidemiológico não encontrado: {DATA_FILE}")

    dataframe = pd.read_csv(
        DATA_FILE,
        dtype={
            DATA_CODE_COLUMN: "string",
        },
    )

    required_columns = {
        DATA_CODE_COLUMN,
        "nome_municipio_ibge",
        "codigo_uf_ibge",
        "nome_uf_ibge",
        "regiao",
        "anos_disponiveis",
        INCIDENCE_COLUMN,
    }

    missing = required_columns - set(dataframe.columns)

    if missing:
        raise ValueError(
            "Colunas epidemiológicas ausentes: " + ", ".join(sorted(missing))
        )

    if len(dataframe) != EXPECTED_DATA_TERRITORIES:
        raise ValueError(
            "Quantidade inesperada de unidades territoriais. "
            f"Esperado: {EXPECTED_DATA_TERRITORIES:,}; "
            f"obtido: {len(dataframe):,}."
        )

    if dataframe[DATA_CODE_COLUMN].duplicated().any():
        raise ValueError("Existem códigos territoriais duplicados.")

    if dataframe[INCIDENCE_COLUMN].isna().any():
        raise ValueError("Existem incidências medianas ausentes.")

    values = dataframe[INCIDENCE_COLUMN].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    if not np.isfinite(values).all():
        raise ValueError("Existem incidências não finitas.")

    if (values < 0).any():
        raise ValueError("Existem incidências negativas.")

    return dataframe


def load_geometry() -> tuple[gpd.GeoDataFrame, int]:
    """Carrega e audita a malha municipal oficial."""
    if not SHAPEFILE.exists():
        raise FileNotFoundError(f"Shapefile não encontrado: {SHAPEFILE}")

    geometry = gpd.read_file(SHAPEFILE)

    if len(geometry) != EXPECTED_GEOMETRIES:
        raise ValueError(
            "Quantidade inesperada de feições na malha. "
            f"Esperado: {EXPECTED_GEOMETRIES:,}; "
            f"obtido: {len(geometry):,}."
        )

    required_columns = {
        GEOMETRY_CODE_COLUMN,
        "NM_MUN",
        "CD_UF",
        "NM_UF",
        "geometry",
    }

    missing = required_columns - set(geometry.columns)

    if missing:
        raise ValueError("Colunas geográficas ausentes: " + ", ".join(sorted(missing)))

    if geometry.crs is None:
        raise ValueError("A malha não possui CRS.")

    if geometry.crs.to_epsg() != GEOGRAPHIC_CRS:
        raise ValueError(
            "CRS inesperado na malha. "
            f"Esperado: EPSG:{GEOGRAPHIC_CRS}; "
            f"obtido: {geometry.crs}."
        )

    geometry[GEOMETRY_CODE_COLUMN] = geometry[GEOMETRY_CODE_COLUMN].astype("string")

    if geometry[GEOMETRY_CODE_COLUMN].duplicated().any():
        raise ValueError("Existem códigos duplicados na malha.")

    if geometry.geometry.is_empty.any():
        raise ValueError("Existem geometrias vazias.")

    invalid = ~geometry.geometry.is_valid

    invalid_count = int(invalid.sum())

    if invalid_count:
        geometry.loc[
            invalid,
            "geometry",
        ] = geometry.loc[invalid].geometry.make_valid()

    if (~geometry.geometry.is_valid).any():
        raise ValueError("Persistem geometrias inválidas após make_valid().")

    return (
        geometry,
        invalid_count,
    )


def reconcile_geometry(
    geometry: gpd.GeoDataFrame,
    dataframe: pd.DataFrame,
) -> gpd.GeoDataFrame:
    """Concilia exatamente as chaves da malha com os dados."""
    geometry_codes = set(geometry[GEOMETRY_CODE_COLUMN].astype(str))

    data_codes = set(dataframe[DATA_CODE_COLUMN].astype(str))

    extra_geometry = geometry_codes - data_codes

    missing_geometry = data_codes - geometry_codes

    if extra_geometry != EXPECTED_EXTRA_GEOMETRIES:
        raise ValueError(
            "Conjunto inesperado de geometrias extras. "
            f"Obtido: {sorted(extra_geometry)}."
        )

    if missing_geometry:
        raise ValueError(
            "Existem unidades epidemiológicas sem geometria: "
            + ", ".join(sorted(missing_geometry))
        )

    geometry = geometry.loc[
        geometry[GEOMETRY_CODE_COLUMN].astype(str).isin(data_codes)
    ].copy()

    if len(geometry) != EXPECTED_DATA_TERRITORIES:
        raise ValueError("Quantidade inesperada de geometrias após conciliação.")

    output = geometry.merge(
        dataframe,
        left_on=GEOMETRY_CODE_COLUMN,
        right_on=DATA_CODE_COLUMN,
        how="left",
        validate="one_to_one",
    )

    if output[INCIDENCE_COLUMN].isna().any():
        raise ValueError("Existem geometrias sem indicador epidemiológico.")

    if len(output) != EXPECTED_DATA_TERRITORIES:
        raise ValueError("O merge espacial alterou a quantidade de unidades.")

    return output


def build_classes(
    dataframe: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, dict[str, float]]:
    """Classifica incidência com limites definidos por quantis."""
    output = dataframe.copy()

    incidence = output[INCIDENCE_COLUMN]

    quantiles = {f"p{int(q * 100)}": float(incidence.quantile(q)) for q in QUANTILES}

    p25 = quantiles["p25"]

    p50 = quantiles["p50"]

    p75 = quantiles["p75"]

    p90 = quantiles["p90"]

    p95 = quantiles["p95"]

    p99 = quantiles["p99"]

    bins = [
        -np.inf,
        p25,
        p50,
        p75,
        p90,
        p95,
        p99,
        np.inf,
    ]

    labels = [
        f"≤ {format_decimal_br(p25)}",
        (f"{format_decimal_br(p25)} – {format_decimal_br(p50)}"),
        (f"{format_decimal_br(p50)} – {format_decimal_br(p75)}"),
        (f"{format_decimal_br(p75)} – {format_decimal_br(p90)}"),
        (f"{format_decimal_br(p90)} – {format_decimal_br(p95)}"),
        (f"{format_decimal_br(p95)} – {format_decimal_br(p99)}"),
        f"> {format_decimal_br(p99)}",
    ]

    output["classe_incidencia"] = pd.cut(
        incidence,
        bins=bins,
        labels=labels,
        include_lowest=True,
        ordered=True,
    )

    if output["classe_incidencia"].isna().any():
        raise ValueError("Existem unidades sem classe de incidência.")

    return (
        output,
        quantiles,
    )


def generate_figure(
    dataframe: gpd.GeoDataFrame,
) -> None:
    """Gera o mapa coroplético municipal."""
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    map_data = dataframe.to_crs(epsg=PLOT_CRS)

    states = map_data.dissolve(by="codigo_uf_ibge")

    fig, ax = plt.subplots(
        figsize=(
            12,
            10,
        )
    )

    map_data.plot(
        ax=ax,
        column="classe_incidencia",
        categorical=True,
        cmap="viridis",
        legend=True,
        linewidth=0,
        legend_kwds={
            "title": ("Incidência mediana anual\npor 100 mil habitantes"),
            "loc": "center left",
            "bbox_to_anchor": (
                0.91,
                0.5,
            ),
            "frameon": False,
            "fontsize": 9.5,
            "title_fontsize": 10,
        },
    )

    states.boundary.plot(
        ax=ax,
        linewidth=0.45,
    )

    ax.set_title(
        ("Intensidade histórica da dengue nos municípios brasileiros — 2016–2025"),
        fontsize=18,
        fontweight="bold",
        pad=26,
    )

    ax.text(
        0,
        1.01,
        (
            "Incidência mediana anual por 100 mil habitantes; "
            "classes definidas a partir da distribuição municipal"
        ),
        transform=ax.transAxes,
        fontsize=10.5,
        va="bottom",
    )

    ax.set_axis_off()

    fig.text(
        0.01,
        0.01,
        (
            "Fonte: elaboração própria a partir de "
            "SINAN/OpenDataSUS, IBGE e malha municipal IBGE 2024."
        ),
        fontsize=9,
        ha="left",
    )

    fig.text(
        0.01,
        0.035,
        (
            "Nota: limites das classes baseados em P25, P50, "
            "P75, P90, P95 e P99 da incidência mediana municipal."
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
    dataframe: gpd.GeoDataFrame,
    quantiles: dict[str, float],
    invalid_count: int,
) -> None:
    """Exibe auditoria resumida da Figura 03."""
    print("=" * 104)

    print("FIGURA 03 — MAPA DA INCIDÊNCIA MEDIANA MUNICIPAL")

    print("=" * 104)

    print()

    print(f"Feições originais da malha        : {EXPECTED_GEOMETRIES:,}")

    print(f"Áreas operacionais removidas      : {len(EXPECTED_EXTRA_GEOMETRIES):,}")

    print(f"Geometrias reparadas              : {invalid_count:,}")

    print(f"Unidades representadas            : {len(dataframe):,}")

    print(f"CRS original                      : EPSG:{GEOGRAPHIC_CRS}")

    print(f"CRS de visualização               : EPSG:{PLOT_CRS}")

    print()

    print("QUANTIS DA INCIDÊNCIA MEDIANA ANUAL")

    for key in (
        "p25",
        "p50",
        "p75",
        "p90",
        "p95",
        "p99",
    ):
        print(f"  {key.upper():<4} : {quantiles[key]:,.2f}")

    print()

    class_counts = dataframe["classe_incidencia"].value_counts(sort=False)

    print("UNIDADES POR CLASSE")

    for label, count in class_counts.items():
        print(f"  {label!s:<24} : {int(count):,}")

    print()

    print(f"Arquivo gerado                    : {OUTPUT_FILE}")

    print()

    print("STATUS: FIGURA GERADA")


def main() -> None:
    """Executa a geração da Figura 03."""
    dataframe = load_data()

    geometry, invalid_count = load_geometry()

    spatial = reconcile_geometry(
        geometry,
        dataframe,
    )

    classified, quantiles = build_classes(spatial)

    generate_figure(classified)

    print_summary(
        classified,
        quantiles,
        invalid_count,
    )


if __name__ == "__main__":
    main()
