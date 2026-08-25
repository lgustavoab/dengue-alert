"""Analisa associações defasadas entre clima e incidência de dengue."""

import json

import numpy as np
import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR

MUNICIPAL_OUTPUT = (
    REPORTS_DIR / "audits" / "associacao_clima_dengue_municipios_2016_2025.csv"
)

NATIONAL_OUTPUT = (
    REPORTS_DIR / "audits" / "associacao_clima_dengue_nacional_2016_2025.csv"
)

REGIONAL_OUTPUT = (
    REPORTS_DIR / "audits" / "associacao_clima_dengue_regional_2016_2025.csv"
)

AUDIT_OUTPUT = REPORTS_DIR / "audits" / "associacao_clima_dengue_2016_2025.json"


EXPECTED_ROWS = 2_907_593
EXPECTED_CLIMATE_ROWS = 2_907_071
EXPECTED_NO_CLIMATE_ROWS = 522
EXPECTED_CLIMATE_TERRITORIES = 5_570

YEAR_COLUMN = "ano_epidemiologico"
WEEK_COLUMN = "semana_epidemiologica"
DATE_COLUMN = "data_inicio_semana"
TERRITORY_COLUMN = "codigo_ibge_7"
INCIDENCE_COLUMN = "incidencia_100mil"
CLIMATE_AVAILABLE_COLUMN = "clima_disponivel"

CLIMATE_VARIABLES = [
    "temperatura_media_c",
    "umidade_relativa_media_pct",
    "precipitacao_total_mm",
]

LAGS = [
    0,
    1,
    2,
    3,
    4,
    6,
    8,
]

REQUIRED_COLUMNS = [
    TERRITORY_COLUMN,
    "nome_municipio_ibge",
    "codigo_uf_ibge",
    "nome_uf_ibge",
    YEAR_COLUMN,
    WEEK_COLUMN,
    DATE_COLUMN,
    INCIDENCE_COLUMN,
    CLIMATE_AVAILABLE_COLUMN,
    *CLIMATE_VARIABLES,
]

REGION_BY_UF_CODE = {
    "11": "Norte",
    "12": "Norte",
    "13": "Norte",
    "14": "Norte",
    "15": "Norte",
    "16": "Norte",
    "17": "Norte",
    "21": "Nordeste",
    "22": "Nordeste",
    "23": "Nordeste",
    "24": "Nordeste",
    "25": "Nordeste",
    "26": "Nordeste",
    "27": "Nordeste",
    "28": "Nordeste",
    "29": "Nordeste",
    "31": "Sudeste",
    "32": "Sudeste",
    "33": "Sudeste",
    "35": "Sudeste",
    "41": "Sul",
    "42": "Sul",
    "43": "Sul",
    "50": "Centro-Oeste",
    "51": "Centro-Oeste",
    "52": "Centro-Oeste",
    "53": "Centro-Oeste",
}

REGION_ORDER = [
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul",
]


def load_data() -> pd.DataFrame:
    """Carrega somente as colunas necessárias do painel mestre."""
    dataframe = pd.read_parquet(
        MASTER_PANEL,
        columns=REQUIRED_COLUMNS,
    )

    dataframe[DATE_COLUMN] = pd.to_datetime(
        dataframe[DATE_COLUMN],
        errors="raise",
    )

    return dataframe


def validate_input(
    dataframe: pd.DataFrame,
) -> None:
    """Valida o painel antes do cálculo das associações."""
    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas. "
            f"Esperado: {EXPECTED_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    if dataframe.duplicated(
        subset=[
            TERRITORY_COLUMN,
            DATE_COLUMN,
        ]
    ).any():
        raise ValueError("Existem combinações território-semana duplicadas.")

    years = tuple(sorted(int(value) for value in dataframe[YEAR_COLUMN].unique()))

    if years != tuple(
        range(
            2016,
            2026,
        )
    ):
        raise ValueError(f"Período epidemiológico inesperado: {years}.")

    climate_available = dataframe[CLIMATE_AVAILABLE_COLUMN].astype(bool)

    available_rows = int(climate_available.sum())

    unavailable_rows = int((~climate_available).sum())

    if available_rows != EXPECTED_CLIMATE_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas com clima. "
            f"Esperado: {EXPECTED_CLIMATE_ROWS:,}; "
            f"obtido: {available_rows:,}."
        )

    if unavailable_rows != EXPECTED_NO_CLIMATE_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas sem clima. "
            f"Esperado: {EXPECTED_NO_CLIMATE_ROWS:,}; "
            f"obtido: {unavailable_rows:,}."
        )

    climate_data = dataframe.loc[climate_available]

    if climate_data[CLIMATE_VARIABLES].isna().any().any():
        raise ValueError(
            "Existem variáveis meteorológicas ausentes "
            "em linhas marcadas como clima disponível."
        )

    climate_values = climate_data[CLIMATE_VARIABLES].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    if not np.isfinite(climate_values).all():
        raise ValueError("Existem valores meteorológicos não finitos.")

    incidence = climate_data[INCIDENCE_COLUMN].to_numpy(
        dtype=np.float64,
        copy=False,
    )

    if not np.isfinite(incidence).all():
        raise ValueError("Existem incidências não finitas.")

    if (incidence < 0).any():
        raise ValueError("Existem incidências negativas.")

    climate_territories = int(climate_data[TERRITORY_COLUMN].nunique())

    if climate_territories != EXPECTED_CLIMATE_TERRITORIES:
        raise ValueError(
            "Quantidade inesperada de unidades territoriais "
            "com cobertura climática. "
            f"Esperado: {EXPECTED_CLIMATE_TERRITORIES:,}; "
            f"obtido: {climate_territories:,}."
        )

    mapping = dataframe.groupby(
        TERRITORY_COLUMN,
        observed=True,
    ).agg(
        nomes=(
            "nome_municipio_ibge",
            "nunique",
        ),
        codigos_uf=(
            "codigo_uf_ibge",
            "nunique",
        ),
        nomes_uf=(
            "nome_uf_ibge",
            "nunique",
        ),
    )

    inconsistent = mapping.loc[
        (mapping["nomes"] != 1)
        | (mapping["codigos_uf"] != 1)
        | (mapping["nomes_uf"] != 1)
    ]

    if not inconsistent.empty:
        raise ValueError(
            "Existem códigos territoriais associados a mais de um município ou UF."
        )


def prepare_climate_data(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Mantém somente observações com cobertura climática válida."""
    output = (
        dataframe.loc[dataframe[CLIMATE_AVAILABLE_COLUMN].astype(bool)]
        .copy()
        .sort_values(
            [
                TERRITORY_COLUMN,
                DATE_COLUMN,
            ]
        )
        .reset_index(drop=True)
    )

    uf_code = output["codigo_uf_ibge"].astype(str).str.zfill(2)

    output["regiao"] = uf_code.map(REGION_BY_UF_CODE)

    if output["regiao"].isna().any():
        raise ValueError("Existem unidades sem macrorregião.")

    return output


def build_registry(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Constrói cadastro das unidades com cobertura climática."""
    registry = (
        dataframe[
            [
                TERRITORY_COLUMN,
                "nome_municipio_ibge",
                "codigo_uf_ibge",
                "nome_uf_ibge",
                "regiao",
            ]
        ]
        .drop_duplicates(subset=[TERRITORY_COLUMN])
        .sort_values(TERRITORY_COLUMN)
        .reset_index(drop=True)
    )

    if len(registry) != EXPECTED_CLIMATE_TERRITORIES:
        raise ValueError("Cadastro climático territorial inesperado.")

    return registry


def calculate_rank_correlation(
    base: pd.DataFrame,
    x_values: pd.Series,
) -> pd.DataFrame:
    """Calcula Spearman por município via correlação dos ranks."""
    temporary = base[
        [
            TERRITORY_COLUMN,
            "rank_y",
        ]
    ].copy()

    temporary["x"] = x_values.to_numpy()

    temporary["rank_x"] = temporary.groupby(
        TERRITORY_COLUMN,
        observed=True,
        sort=False,
    )["x"].rank(method="average")

    temporary["rank_x2"] = temporary["rank_x"] * temporary["rank_x"]

    temporary["rank_y2"] = temporary["rank_y"] * temporary["rank_y"]

    temporary["rank_xy"] = temporary["rank_x"] * temporary["rank_y"]

    grouped = temporary.groupby(
        TERRITORY_COLUMN,
        as_index=False,
        observed=True,
        sort=False,
    ).agg(
        observacoes_validas=(
            "x",
            "size",
        ),
        soma_x=(
            "rank_x",
            "sum",
        ),
        soma_y=(
            "rank_y",
            "sum",
        ),
        soma_x2=(
            "rank_x2",
            "sum",
        ),
        soma_y2=(
            "rank_y2",
            "sum",
        ),
        soma_xy=(
            "rank_xy",
            "sum",
        ),
    )

    n = grouped["observacoes_validas"].astype(np.float64)

    numerator = grouped["soma_xy"] - (grouped["soma_x"] * grouped["soma_y"] / n)

    variance_x = grouped["soma_x2"] - (grouped["soma_x"] ** 2 / n)

    variance_y = grouped["soma_y2"] - (grouped["soma_y"] ** 2 / n)

    denominator = np.sqrt(variance_x * variance_y)

    valid = n.ge(2) & variance_x.gt(0) & variance_y.gt(0)

    grouped["correlacao_spearman"] = np.where(
        valid,
        numerator / denominator,
        np.nan,
    )

    grouped["correlacao_valida"] = valid

    return grouped[
        [
            TERRITORY_COLUMN,
            "observacoes_validas",
            "correlacao_spearman",
            "correlacao_valida",
        ]
    ]


def calculate_municipal_associations(
    dataframe: pd.DataFrame,
    registry: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula correlações municipais para todas as variáveis e lags."""
    results = []

    grouped = dataframe.groupby(
        TERRITORY_COLUMN,
        observed=True,
        sort=False,
    )

    for lag in LAGS:
        print(f"Calculando lag {lag}...")

        if lag == 0:
            lagged_climate = dataframe[CLIMATE_VARIABLES]

            valid_time = pd.Series(
                True,
                index=dataframe.index,
            )

        else:
            lagged_climate = grouped[CLIMATE_VARIABLES].shift(lag)

            lagged_date = grouped[DATE_COLUMN].shift(lag)

            difference_days = (dataframe[DATE_COLUMN] - lagged_date).dt.days

            valid_time = difference_days.eq(lag * 7)

        valid_index = dataframe.index[valid_time]

        base = dataframe.loc[
            valid_index,
            [
                TERRITORY_COLUMN,
                INCIDENCE_COLUMN,
            ],
        ].copy()

        base["rank_y"] = base.groupby(
            TERRITORY_COLUMN,
            observed=True,
            sort=False,
        )[INCIDENCE_COLUMN].rank(method="average")

        for variable in CLIMATE_VARIABLES:
            correlations = calculate_rank_correlation(
                base,
                lagged_climate.loc[
                    valid_index,
                    variable,
                ],
            )

            correlations["variavel_climatica"] = variable

            correlations["lag_semanas"] = lag

            correlations = registry.merge(
                correlations,
                on=TERRITORY_COLUMN,
                how="left",
                validate="one_to_one",
            )

            correlations["correlacao_valida"] = correlations[
                "correlacao_valida"
            ].fillna(False)

            results.append(correlations)

    output = pd.concat(
        results,
        ignore_index=True,
    )

    expected_rows = EXPECTED_CLIMATE_TERRITORIES * len(CLIMATE_VARIABLES) * len(LAGS)

    if len(output) != expected_rows:
        raise ValueError(
            "Quantidade inesperada de resultados municipais. "
            f"Esperado: {expected_rows:,}; "
            f"obtido: {len(output):,}."
        )

    return output


def summarize_group(
    dataframe: pd.DataFrame,
) -> pd.Series:
    """Resume uma distribuição de correlações municipais."""
    valid = dataframe.loc[
        dataframe["correlacao_valida"].astype(bool)
        & dataframe["correlacao_spearman"].notna(),
        "correlacao_spearman",
    ]

    observations = dataframe.loc[
        dataframe["correlacao_valida"].astype(bool),
        "observacoes_validas",
    ]

    if valid.empty:
        return pd.Series(
            {
                "municipios_total": len(dataframe),
                "municipios_correlacao_valida": 0,
                "observacoes_validas_mediana": np.nan,
                "correlacao_media": np.nan,
                "correlacao_mediana": np.nan,
                "correlacao_p10": np.nan,
                "correlacao_p25": np.nan,
                "correlacao_p75": np.nan,
                "correlacao_p90": np.nan,
                "proporcao_correlacao_positiva": np.nan,
                "proporcao_correlacao_negativa": np.nan,
            }
        )

    return pd.Series(
        {
            "municipios_total": len(dataframe),
            "municipios_correlacao_valida": len(valid),
            "observacoes_validas_mediana": float(observations.median()),
            "correlacao_media": float(valid.mean()),
            "correlacao_mediana": float(valid.median()),
            "correlacao_p10": float(valid.quantile(0.10)),
            "correlacao_p25": float(valid.quantile(0.25)),
            "correlacao_p75": float(valid.quantile(0.75)),
            "correlacao_p90": float(valid.quantile(0.90)),
            "proporcao_correlacao_positiva": float(valid.gt(0).mean()),
            "proporcao_correlacao_negativa": float(valid.lt(0).mean()),
        }
    )


def build_national_summary(
    municipal: pd.DataFrame,
) -> pd.DataFrame:
    """Resume as correlações municipais em escala nacional."""
    summary = (
        municipal.groupby(
            [
                "variavel_climatica",
                "lag_semanas",
            ],
            observed=True,
            sort=False,
        )
        .apply(
            summarize_group,
            include_groups=False,
        )
        .reset_index()
    )

    expected_rows = len(CLIMATE_VARIABLES) * len(LAGS)

    if len(summary) != expected_rows:
        raise ValueError("Quantidade inesperada de resultados nacionais.")

    return summary


def build_regional_summary(
    municipal: pd.DataFrame,
) -> pd.DataFrame:
    """Resume as correlações municipais por macrorregião."""
    summary = (
        municipal.groupby(
            [
                "regiao",
                "variavel_climatica",
                "lag_semanas",
            ],
            observed=True,
            sort=False,
        )
        .apply(
            summarize_group,
            include_groups=False,
        )
        .reset_index()
    )

    expected_rows = len(REGION_ORDER) * len(CLIMATE_VARIABLES) * len(LAGS)

    if len(summary) != expected_rows:
        raise ValueError("Quantidade inesperada de resultados regionais.")

    return summary


def identify_peak_lags(
    national: pd.DataFrame,
) -> pd.DataFrame:
    """Identifica a maior associação mediana em magnitude por variável."""
    candidates = national.copy()

    candidates["magnitude_correlacao_mediana"] = candidates["correlacao_mediana"].abs()

    peaks = (
        candidates.sort_values(
            [
                "variavel_climatica",
                "magnitude_correlacao_mediana",
                "lag_semanas",
            ],
            ascending=[
                True,
                False,
                True,
            ],
        )
        .drop_duplicates(
            subset=["variavel_climatica"],
            keep="first",
        )
        .reset_index(drop=True)
    )

    return peaks


def build_audit(
    dataframe: pd.DataFrame,
    municipal: pd.DataFrame,
    national: pd.DataFrame,
    regional: pd.DataFrame,
    peaks: pd.DataFrame,
) -> dict:
    """Monta a auditoria consolidada."""
    peak_records = []

    for row in peaks.itertuples(index=False):
        peak_records.append(
            {
                "variavel_climatica": row.variavel_climatica,
                "lag_semanas": int(row.lag_semanas),
                "correlacao_mediana": float(row.correlacao_mediana),
                "magnitude_correlacao_mediana": float(row.magnitude_correlacao_mediana),
                "municipios_correlacao_valida": int(row.municipios_correlacao_valida),
            }
        )

    invalid_correlations = int((~municipal["correlacao_valida"].astype(bool)).sum())

    return {
        "status": "APROVADO",
        "analise": "associação descritiva defasada entre clima e dengue",
        "periodo": "2016-2025",
        "metodo": {
            "correlacao": "Spearman por unidade territorial",
            "desfecho": INCIDENCE_COLUMN,
            "variaveis_climaticas": CLIMATE_VARIABLES,
            "lags_semanas": LAGS,
            "interpretacao_lag": (
                "clima observado em t-k comparado com incidência observada em t"
            ),
        },
        "painel": {
            "linhas_totais": len(dataframe),
            "linhas_com_clima": int(
                dataframe[CLIMATE_AVAILABLE_COLUMN].astype(bool).sum()
            ),
            "linhas_sem_clima": int(
                (~dataframe[CLIMATE_AVAILABLE_COLUMN].astype(bool)).sum()
            ),
            "unidades_com_clima": EXPECTED_CLIMATE_TERRITORIES,
        },
        "resultados": {
            "linhas_municipais": len(municipal),
            "linhas_nacionais": len(national),
            "linhas_regionais": len(regional),
            "correlacoes_municipais_invalidas": invalid_correlations,
            "defasagens_maior_associacao_mediana": peak_records,
        },
        "validacoes": {
            "variaveis_congeladas_antes_execucao": True,
            "lags_congelados_antes_execucao": True,
            "metrica_congelada_antes_execucao": True,
            "defasagem_exige_continuidade_semanal": True,
            "correlacoes_calculadas_separadamente_por_municipio": True,
            "correlacao_interpretada_como_causalidade": False,
            "modelo_final_modificado": False,
        },
        "artefatos": {
            "municipios": str(MUNICIPAL_OUTPUT),
            "nacional": str(NATIONAL_OUTPUT),
            "regional": str(REGIONAL_OUTPUT),
            "auditoria": str(AUDIT_OUTPUT),
        },
    }


def main() -> None:
    """Executa a análise clima × dengue."""
    print("=" * 112)
    print("ASSOCIAÇÃO CLIMA × DENGUE — 2016–2025")
    print("=" * 112)

    print()
    print("Carregando painel mestre...")

    dataframe = load_data()

    validate_input(dataframe)

    climate_data = prepare_climate_data(dataframe)

    registry = build_registry(climate_data)

    print(f"Linhas totais                     : {len(dataframe):,}")

    print(f"Linhas com clima                  : {len(climate_data):,}")

    print(f"Linhas sem clima                  : {len(dataframe) - len(climate_data):,}")

    print(f"Unidades com cobertura climática  : {len(registry):,}")

    print()
    print("Calculando correlações municipais...")

    municipal = calculate_municipal_associations(
        climate_data,
        registry,
    )

    print()
    print("Consolidando resultados nacionais...")

    national = build_national_summary(municipal)

    regional = build_regional_summary(municipal)

    peaks = identify_peak_lags(national)

    MUNICIPAL_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    municipal.to_csv(
        MUNICIPAL_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    national.to_csv(
        NATIONAL_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    regional.to_csv(
        REGIONAL_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    audit = build_audit(
        dataframe,
        municipal,
        national,
        regional,
        peaks,
    )

    with AUDIT_OUTPUT.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            audit,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 112)
    print("RESUMO NACIONAL — CORRELAÇÃO MEDIANA MUNICIPAL")
    print("=" * 112)

    display = national[
        [
            "variavel_climatica",
            "lag_semanas",
            "municipios_correlacao_valida",
            "observacoes_validas_mediana",
            "correlacao_mediana",
            "correlacao_p25",
            "correlacao_p75",
            "proporcao_correlacao_positiva",
        ]
    ].copy()

    display["correlacao_mediana"] = display["correlacao_mediana"].map(
        lambda value: f"{value:.4f}"
    )

    display["correlacao_p25"] = display["correlacao_p25"].map(
        lambda value: f"{value:.4f}"
    )

    display["correlacao_p75"] = display["correlacao_p75"].map(
        lambda value: f"{value:.4f}"
    )

    display["proporcao_correlacao_positiva"] = display[
        "proporcao_correlacao_positiva"
    ].map(lambda value: f"{value:.2%}")

    print(display.to_string(index=False))

    print()
    print("=" * 112)
    print("DEFASAGEM DE MAIOR ASSOCIAÇÃO MEDIANA EM MAGNITUDE")
    print("=" * 112)

    peak_display = peaks[
        [
            "variavel_climatica",
            "lag_semanas",
            "correlacao_mediana",
            "magnitude_correlacao_mediana",
            "municipios_correlacao_valida",
        ]
    ].copy()

    print(peak_display.to_string(index=False))

    print()
    print("Arquivos gerados:")

    print(f"  Município × variável × lag       : {MUNICIPAL_OUTPUT}")

    print(f"  Resumo nacional                  : {NATIONAL_OUTPUT}")

    print(f"  Resumo regional                  : {REGIONAL_OUTPUT}")

    print(f"  Auditoria                        : {AUDIT_OUTPUT}")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
