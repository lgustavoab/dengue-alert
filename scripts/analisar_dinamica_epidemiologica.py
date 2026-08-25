"""Analisa duração, persistência e recorrência do risco epidemiológico."""

import json

import numpy as np
import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR

DEVELOPMENT_TARGETS = MASTER_PANEL.parent / "alvos_modelagem_2018_2024.parquet"

FINAL_TARGETS = MASTER_PANEL.parent / "alvos_teste_final_2025.parquet"

EPISODES_OUTPUT = REPORTS_DIR / "audits" / "episodios_risco_elevado_2018_2025.csv"

MUNICIPAL_OUTPUT = REPORTS_DIR / "audits" / "dinamica_risco_municipio_2018_2025.csv"

WEEKLY_OUTPUT = (
    REPORTS_DIR / "audits" / "serie_risco_semanal_nacional_regional_2018_2025.csv"
)

YEAR_REGION_OUTPUT = REPORTS_DIR / "audits" / "dinamica_risco_ano_regiao_2018_2025.csv"

AUDIT_OUTPUT = REPORTS_DIR / "audits" / "dinamica_epidemiologica_2018_2025.json"


EXPECTED_DEVELOPMENT_ROWS = 2_032_685
EXPECTED_FINAL_ROWS = 295_210
EXPECTED_TOTAL_ROWS = 2_327_895
EXPECTED_DEFINED_ROWS = 2_327_842
EXPECTED_MISSING_RISK = 53
EXPECTED_POSITIVE_ROWS = 414_678
EXPECTED_ELIGIBLE_MUNICIPALITIES = 5_569
EXPECTED_TOTAL_MUNICIPALITIES = 5_570
EXPECTED_WEEKS = 418
EXPECTED_OBSERVATIONS_PER_ELIGIBLE_MUNICIPALITY = 418

INELIGIBLE_2025_CODE = "5101837"

YEAR_COLUMN = "ano_epidemiologico"
WEEK_COLUMN = "semana_epidemiologica"
DATE_COLUMN = "data_inicio_semana"
TERRITORY_COLUMN = "codigo_ibge_7"

CASES_4W_COLUMN = "casos_4s"
INCIDENCE_4W_COLUMN = "incidencia_4s_100mil"
THRESHOLD_COLUMN = "limiar_sazonal_p90"
RISK_COLUMN = "risco_elevado"
MARGIN_COLUMN = "margem_limiar_p90"

TARGET_COLUMNS = [
    TERRITORY_COLUMN,
    YEAR_COLUMN,
    WEEK_COLUMN,
    DATE_COLUMN,
    CASES_4W_COLUMN,
    INCIDENCE_4W_COLUMN,
    THRESHOLD_COLUMN,
    RISK_COLUMN,
]

REGISTRY_COLUMNS = [
    TERRITORY_COLUMN,
    "nome_municipio_ibge",
    "codigo_uf_ibge",
    "nome_uf_ibge",
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

REGION_ORDER = (
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul",
)

EXPECTED_YEARS = tuple(
    range(
        2018,
        2026,
    )
)


def load_targets() -> pd.DataFrame:
    """Carrega e concatena os targets sem recalculá-los."""
    development = pd.read_parquet(
        DEVELOPMENT_TARGETS,
        columns=TARGET_COLUMNS,
    )

    final = pd.read_parquet(
        FINAL_TARGETS,
        columns=TARGET_COLUMNS,
    )

    if len(development) != EXPECTED_DEVELOPMENT_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas no desenvolvimento. "
            f"Esperado: {EXPECTED_DEVELOPMENT_ROWS:,}; "
            f"obtido: {len(development):,}."
        )

    if len(final) != EXPECTED_FINAL_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas no teste final. "
            f"Esperado: {EXPECTED_FINAL_ROWS:,}; "
            f"obtido: {len(final):,}."
        )

    dataframe = pd.concat(
        [
            development,
            final,
        ],
        ignore_index=True,
    )

    return dataframe


def validate_targets(
    dataframe: pd.DataFrame,
) -> None:
    """Valida targets e elegibilidade antes da análise dinâmica."""
    if len(dataframe) != EXPECTED_TOTAL_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas concatenadas. "
            f"Esperado: {EXPECTED_TOTAL_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    if dataframe.duplicated(
        subset=[
            TERRITORY_COLUMN,
            DATE_COLUMN,
        ]
    ).any():
        raise ValueError("Existem município-semana duplicados.")

    years = tuple(sorted(int(value) for value in dataframe[YEAR_COLUMN].unique()))

    if years != EXPECTED_YEARS:
        raise ValueError(
            "Anos epidemiológicos inesperados. "
            f"Esperado: {EXPECTED_YEARS}; "
            f"obtido: {years}."
        )

    municipalities = int(dataframe[TERRITORY_COLUMN].nunique())

    if municipalities != EXPECTED_TOTAL_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de municípios nos targets. "
            f"Esperado: {EXPECTED_TOTAL_MUNICIPALITIES:,}; "
            f"obtido: {municipalities:,}."
        )

    missing_risk = dataframe[RISK_COLUMN].isna()

    if int(missing_risk.sum()) != EXPECTED_MISSING_RISK:
        raise ValueError(
            "Quantidade inesperada de riscos ausentes. "
            f"Esperado: {EXPECTED_MISSING_RISK}; "
            f"obtido: {int(missing_risk.sum())}."
        )

    missing_codes = set(
        dataframe.loc[
            missing_risk,
            TERRITORY_COLUMN,
        ].unique()
    )

    if missing_codes != {INELIGIBLE_2025_CODE}:
        raise ValueError(
            "Os targets ausentes não pertencem exclusivamente "
            f"ao código esperado {INELIGIBLE_2025_CODE}. "
            f"Obtido: {sorted(missing_codes)}."
        )

    defined = dataframe.loc[~missing_risk]

    if len(defined) != EXPECTED_DEFINED_ROWS:
        raise ValueError(
            "Quantidade inesperada de riscos definidos. "
            f"Esperado: {EXPECTED_DEFINED_ROWS:,}; "
            f"obtido: {len(defined):,}."
        )

    positives = int(defined[RISK_COLUMN].eq(True).sum())

    if positives != EXPECTED_POSITIVE_ROWS:
        raise ValueError(
            "Quantidade inesperada de semanas em risco. "
            f"Esperado: {EXPECTED_POSITIVE_ROWS:,}; "
            f"obtido: {positives:,}."
        )

    eligible_municipalities = int(defined[TERRITORY_COLUMN].nunique())

    if eligible_municipalities != EXPECTED_ELIGIBLE_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de municípios elegíveis. "
            f"Esperado: {EXPECTED_ELIGIBLE_MUNICIPALITIES:,}; "
            f"obtido: {eligible_municipalities:,}."
        )

    counts = defined.groupby(
        TERRITORY_COLUMN,
        observed=True,
    ).size()

    if not counts.eq(EXPECTED_OBSERVATIONS_PER_ELIGIBLE_MUNICIPALITY).all():
        invalid = int(~counts.eq(EXPECTED_OBSERVATIONS_PER_ELIGIBLE_MUNICIPALITY)).sum()

        raise ValueError(
            f"Foram encontrados {invalid:,} municípios elegíveis sem 418 observações."
        )

    required_defined_columns = [
        CASES_4W_COLUMN,
        INCIDENCE_4W_COLUMN,
        THRESHOLD_COLUMN,
    ]

    if defined[required_defined_columns].isna().any().any():
        raise ValueError(
            "Existem valores epidemiológicos ausentes em linhas com risco definido."
        )

    for column in required_defined_columns:
        values = defined[column].to_numpy(
            dtype=np.float64,
            copy=False,
        )

        if not np.isfinite(values).all():
            raise ValueError(f"Existem valores não finitos em {column}.")

    margin = defined[INCIDENCE_4W_COLUMN] - defined[THRESHOLD_COLUMN]

    risk = defined[RISK_COLUMN].astype(bool)

    if not margin.loc[risk].gt(0).all():
        raise ValueError(
            "Existem semanas classificadas em risco sem incidência acima do limiar."
        )

    if not margin.loc[~risk].le(0).all():
        raise ValueError(
            "Existem semanas fora de risco com incidência acima do limiar."
        )


def load_registry() -> pd.DataFrame:
    """Carrega o cadastro territorial já validado no painel mestre."""
    registry = pd.read_parquet(
        MASTER_PANEL,
        columns=REGISTRY_COLUMNS,
    )

    consistency = registry.groupby(
        TERRITORY_COLUMN,
        observed=True,
    ).agg(
        nomes_municipio=(
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

    invalid = consistency.loc[
        (consistency["nomes_municipio"] != 1)
        | (consistency["codigos_uf"] != 1)
        | (consistency["nomes_uf"] != 1)
    ]

    if not invalid.empty:
        raise ValueError(
            "Existem códigos territoriais associados a mais de um nome ou UF."
        )

    registry = registry.drop_duplicates(subset=[TERRITORY_COLUMN]).reset_index(
        drop=True
    )

    uf_code = registry["codigo_uf_ibge"].astype(str).str.zfill(2)

    registry["regiao"] = uf_code.map(REGION_BY_UF_CODE)

    if registry["regiao"].isna().any():
        raise ValueError("Existem unidades territoriais sem macrorregião.")

    return registry


def enrich_targets(
    dataframe: pd.DataFrame,
    registry: pd.DataFrame,
) -> pd.DataFrame:
    """Adiciona município, UF e região sem alterar os targets."""
    output = dataframe.merge(
        registry,
        on=TERRITORY_COLUMN,
        how="left",
        validate="many_to_one",
    )

    if output["nome_municipio_ibge"].isna().any():
        raise ValueError("Existem targets sem cadastro territorial.")

    output[MARGIN_COLUMN] = output[INCIDENCE_4W_COLUMN] - output[THRESHOLD_COLUMN]

    return output


def build_episodes(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Identifica sequências máximas consecutivas de risco elevado."""
    eligible = (
        dataframe.loc[dataframe[RISK_COLUMN].notna()]
        .copy()
        .sort_values(
            [
                TERRITORY_COLUMN,
                DATE_COLUMN,
            ]
        )
        .reset_index(drop=True)
    )

    eligible[RISK_COLUMN] = eligible[RISK_COLUMN].astype(bool)

    municipality_group = eligible.groupby(
        TERRITORY_COLUMN,
        observed=True,
        sort=False,
    )

    previous_date = municipality_group[DATE_COLUMN].shift()

    previous_risk = municipality_group[RISK_COLUMN].shift().fillna(False).astype(bool)

    gap_days = (eligible[DATE_COLUMN] - previous_date).dt.days

    episode_start = eligible[RISK_COLUMN] & ((~previous_risk) | gap_days.ne(7))

    eligible["numero_episodio"] = (
        episode_start.groupby(
            eligible[TERRITORY_COLUMN],
            sort=False,
        )
        .cumsum()
        .astype("int64")
    )

    risk_rows = eligible.loc[eligible[RISK_COLUMN]].copy()

    metadata_columns = [
        TERRITORY_COLUMN,
        "nome_municipio_ibge",
        "codigo_uf_ibge",
        "nome_uf_ibge",
        "regiao",
        "numero_episodio",
    ]

    episodes = risk_rows.groupby(
        metadata_columns,
        as_index=False,
        observed=True,
    ).agg(
        data_inicio=(
            DATE_COLUMN,
            "first",
        ),
        data_fim=(
            DATE_COLUMN,
            "last",
        ),
        ano_epidemiologico_inicio=(
            YEAR_COLUMN,
            "first",
        ),
        semana_epidemiologica_inicio=(
            WEEK_COLUMN,
            "first",
        ),
        ano_epidemiologico_fim=(
            YEAR_COLUMN,
            "last",
        ),
        semana_epidemiologica_fim=(
            WEEK_COLUMN,
            "last",
        ),
        duracao_semanas=(
            RISK_COLUMN,
            "size",
        ),
        casos_4s_maximos=(
            CASES_4W_COLUMN,
            "max",
        ),
        incidencia_4s_maxima_100mil=(
            INCIDENCE_4W_COLUMN,
            "max",
        ),
        incidencia_4s_media_100mil=(
            INCIDENCE_4W_COLUMN,
            "mean",
        ),
        margem_maxima_limiar_100mil=(
            MARGIN_COLUMN,
            "max",
        ),
    )

    episodes["atravessa_ano_epidemiologico"] = (
        episodes["ano_epidemiologico_inicio"] != episodes["ano_epidemiologico_fim"]
    )

    expected_duration = (
        episodes["data_fim"] - episodes["data_inicio"]
    ).dt.days // 7 + 1

    if not expected_duration.eq(episodes["duracao_semanas"]).all():
        raise ValueError("Existem episódios com semanas não consecutivas.")

    if int(episodes["duracao_semanas"].sum()) != EXPECTED_POSITIVE_ROWS:
        raise ValueError(
            "A duração acumulada dos episódios não preservou as semanas em risco."
        )

    return episodes.sort_values(
        [
            TERRITORY_COLUMN,
            "data_inicio",
        ]
    ).reset_index(drop=True)


def build_municipal_summary(
    dataframe: pd.DataFrame,
    episodes: pd.DataFrame,
) -> pd.DataFrame:
    """Resume persistência e recorrência por município."""
    eligible = dataframe.loc[dataframe[RISK_COLUMN].notna()].copy()

    eligible[RISK_COLUMN] = eligible[RISK_COLUMN].astype(bool)

    metadata = [
        TERRITORY_COLUMN,
        "nome_municipio_ibge",
        "codigo_uf_ibge",
        "nome_uf_ibge",
        "regiao",
    ]

    summary = eligible.groupby(
        metadata,
        as_index=False,
        observed=True,
    ).agg(
        observacoes_elegiveis=(
            RISK_COLUMN,
            "size",
        ),
        anos_elegiveis=(
            YEAR_COLUMN,
            "nunique",
        ),
        semanas_risco=(
            RISK_COLUMN,
            "sum",
        ),
    )

    summary["proporcao_semanas_risco"] = (
        summary["semanas_risco"] / summary["observacoes_elegiveis"]
    )

    risk_years = (
        eligible.loc[eligible[RISK_COLUMN]]
        .groupby(
            TERRITORY_COLUMN,
            as_index=False,
            observed=True,
        )
        .agg(
            anos_com_risco=(
                YEAR_COLUMN,
                "nunique",
            ),
            primeira_semana_risco=(
                DATE_COLUMN,
                "min",
            ),
            ultima_semana_risco=(
                DATE_COLUMN,
                "max",
            ),
        )
    )

    episode_summary = episodes.groupby(
        TERRITORY_COLUMN,
        as_index=False,
        observed=True,
    ).agg(
        episodios=(
            "numero_episodio",
            "size",
        ),
        duracao_media_episodio=(
            "duracao_semanas",
            "mean",
        ),
        duracao_mediana_episodio=(
            "duracao_semanas",
            "median",
        ),
        duracao_maxima_episodio=(
            "duracao_semanas",
            "max",
        ),
        episodios_multianuais=(
            "atravessa_ano_epidemiologico",
            "sum",
        ),
    )

    summary = summary.merge(
        risk_years,
        on=TERRITORY_COLUMN,
        how="left",
        validate="one_to_one",
    )

    summary = summary.merge(
        episode_summary,
        on=TERRITORY_COLUMN,
        how="left",
        validate="one_to_one",
    )

    summary["anos_com_risco"] = summary["anos_com_risco"].fillna(0).astype("int64")

    summary["episodios"] = summary["episodios"].fillna(0).astype("int64")

    summary["episodios_multianuais"] = (
        summary["episodios_multianuais"].fillna(0).astype("int64")
    )

    summary["recorrencia_multianual"] = summary["anos_com_risco"].ge(2)

    if len(summary) != EXPECTED_ELIGIBLE_MUNICIPALITIES:
        raise ValueError("Quantidade inesperada de municípios no resumo dinâmico.")

    if (
        not summary["observacoes_elegiveis"]
        .eq(EXPECTED_OBSERVATIONS_PER_ELIGIBLE_MUNICIPALITY)
        .all()
    ):
        raise ValueError(
            "Nem todos os municípios do resumo possuem 418 semanas elegíveis."
        )

    if int(summary["semanas_risco"].sum()) != EXPECTED_POSITIVE_ROWS:
        raise ValueError(
            "O resumo municipal não preservou o total de semanas em risco."
        )

    return summary.sort_values(TERRITORY_COLUMN).reset_index(drop=True)


def aggregate_weekly(
    dataframe: pd.DataFrame,
    *,
    group_columns: list[str],
    scale: str,
) -> pd.DataFrame:
    """Agrega simultaneidade de risco por semana."""
    result = dataframe.groupby(
        group_columns,
        as_index=False,
        observed=True,
    ).agg(
        unidades_elegiveis=(
            TERRITORY_COLUMN,
            "nunique",
        ),
        unidades_em_risco=(
            RISK_COLUMN,
            "sum",
        ),
        incidencia_4s_media_100mil=(
            INCIDENCE_4W_COLUMN,
            "mean",
        ),
        incidencia_4s_mediana_100mil=(
            INCIDENCE_4W_COLUMN,
            "median",
        ),
        limiar_p90_mediano_100mil=(
            THRESHOLD_COLUMN,
            "median",
        ),
    )

    result["proporcao_unidades_em_risco"] = (
        result["unidades_em_risco"] / result["unidades_elegiveis"]
    )

    result["escala"] = scale

    return result


def build_weekly_series(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Constrói séries nacional e regionais de municípios em risco."""
    eligible = dataframe.loc[dataframe[RISK_COLUMN].notna()].copy()

    eligible[RISK_COLUMN] = eligible[RISK_COLUMN].astype(bool)

    national = aggregate_weekly(
        eligible,
        group_columns=[
            YEAR_COLUMN,
            WEEK_COLUMN,
            DATE_COLUMN,
        ],
        scale="nacional",
    )

    national["grupo"] = "Brasil"

    regional = aggregate_weekly(
        eligible,
        group_columns=[
            "regiao",
            YEAR_COLUMN,
            WEEK_COLUMN,
            DATE_COLUMN,
        ],
        scale="regional",
    )

    regional = regional.rename(
        columns={
            "regiao": "grupo",
        }
    )

    columns = [
        "escala",
        "grupo",
        YEAR_COLUMN,
        WEEK_COLUMN,
        DATE_COLUMN,
        "unidades_elegiveis",
        "unidades_em_risco",
        "proporcao_unidades_em_risco",
        "incidencia_4s_media_100mil",
        "incidencia_4s_mediana_100mil",
        "limiar_p90_mediano_100mil",
    ]

    output = pd.concat(
        [
            national[columns],
            regional[columns],
        ],
        ignore_index=True,
    )

    national_rows = output.loc[output["escala"].eq("nacional")]

    regional_rows = output.loc[output["escala"].eq("regional")]

    if len(national_rows) != EXPECTED_WEEKS:
        raise ValueError("Quantidade inesperada de semanas nacionais.")

    if len(regional_rows) != (EXPECTED_WEEKS * len(REGION_ORDER)):
        raise ValueError("Quantidade inesperada de semanas regionais.")

    if (
        not national_rows["unidades_elegiveis"]
        .eq(EXPECTED_ELIGIBLE_MUNICIPALITIES)
        .all()
    ):
        raise ValueError(
            "A série nacional não preservou os 5.569 municípios elegíveis."
        )

    return output.sort_values(
        [
            DATE_COLUMN,
            "escala",
            "grupo",
        ]
    ).reset_index(drop=True)


def build_year_region_summary(
    dataframe: pd.DataFrame,
    episodes: pd.DataFrame,
) -> pd.DataFrame:
    """Resume risco por ano epidemiológico e macrorregião."""
    eligible = dataframe.loc[dataframe[RISK_COLUMN].notna()].copy()

    eligible[RISK_COLUMN] = eligible[RISK_COLUMN].astype(bool)

    municipality_year = eligible.groupby(
        [
            YEAR_COLUMN,
            "regiao",
            TERRITORY_COLUMN,
        ],
        as_index=False,
        observed=True,
    ).agg(
        semanas_elegiveis=(
            RISK_COLUMN,
            "size",
        ),
        semanas_risco=(
            RISK_COLUMN,
            "sum",
        ),
    )

    municipality_year["teve_risco"] = municipality_year["semanas_risco"].gt(0)

    summary = municipality_year.groupby(
        [
            YEAR_COLUMN,
            "regiao",
        ],
        as_index=False,
        observed=True,
    ).agg(
        municipios_elegiveis=(
            TERRITORY_COLUMN,
            "nunique",
        ),
        municipios_com_risco=(
            "teve_risco",
            "sum",
        ),
        semanas_municipais_elegiveis=(
            "semanas_elegiveis",
            "sum",
        ),
        semanas_municipais_em_risco=(
            "semanas_risco",
            "sum",
        ),
    )

    summary["proporcao_municipios_com_risco"] = (
        summary["municipios_com_risco"] / summary["municipios_elegiveis"]
    )

    summary["proporcao_semanas_municipais_em_risco"] = (
        summary["semanas_municipais_em_risco"] / summary["semanas_municipais_elegiveis"]
    )

    episode_year_region = (
        episodes.groupby(
            [
                "ano_epidemiologico_inicio",
                "regiao",
            ],
            as_index=False,
            observed=True,
        )
        .agg(
            episodios_iniciados=(
                "numero_episodio",
                "size",
            ),
            duracao_mediana_episodios_iniciados=(
                "duracao_semanas",
                "median",
            ),
            duracao_media_episodios_iniciados=(
                "duracao_semanas",
                "mean",
            ),
            duracao_maxima_episodios_iniciados=(
                "duracao_semanas",
                "max",
            ),
        )
        .rename(
            columns={
                "ano_epidemiologico_inicio": YEAR_COLUMN,
            }
        )
    )

    summary = summary.merge(
        episode_year_region,
        on=[
            YEAR_COLUMN,
            "regiao",
        ],
        how="left",
        validate="one_to_one",
    )

    summary["episodios_iniciados"] = (
        summary["episodios_iniciados"].fillna(0).astype("int64")
    )

    summary["regiao"] = pd.Categorical(
        summary["regiao"],
        categories=REGION_ORDER,
        ordered=True,
    )

    return summary.sort_values(
        [
            YEAR_COLUMN,
            "regiao",
        ]
    ).reset_index(drop=True)


def build_audit(
    dataframe: pd.DataFrame,
    episodes: pd.DataFrame,
    municipal: pd.DataFrame,
    weekly: pd.DataFrame,
    year_region: pd.DataFrame,
) -> dict:
    """Monta a auditoria consolidada da dinâmica epidemiológica."""
    national = weekly.loc[weekly["escala"].eq("nacional")]

    peak_index = national["unidades_em_risco"].idxmax()

    peak = national.loc[peak_index]

    return {
        "status": "APROVADO",
        "analise": "dinâmica epidemiológica do risco elevado",
        "periodo_epidemiologico": "2018-2025",
        "definicao_episodio": (
            "Sequência máxima de semanas consecutivas, "
            "separadas por exatamente sete dias, "
            "com risco_elevado=True para o mesmo município."
        ),
        "targets": {
            "linhas_totais": len(dataframe),
            "linhas_risco_definido": int(dataframe[RISK_COLUMN].notna().sum()),
            "linhas_risco_ausente": int(dataframe[RISK_COLUMN].isna().sum()),
            "codigo_sem_target_elegivel": INELIGIBLE_2025_CODE,
            "municipios_elegiveis": len(municipal),
            "semanas_em_risco": int(municipal["semanas_risco"].sum()),
        },
        "episodios": {
            "quantidade": len(episodes),
            "duracao_media_semanas": float(episodes["duracao_semanas"].mean()),
            "duracao_mediana_semanas": float(episodes["duracao_semanas"].median()),
            "duracao_maxima_semanas": int(episodes["duracao_semanas"].max()),
            "episodios_multianuais": int(
                episodes["atravessa_ano_epidemiologico"].sum()
            ),
        },
        "municipios": {
            "com_algum_risco": int(municipal["semanas_risco"].gt(0).sum()),
            "com_recorrencia_multianual": int(
                municipal["recorrencia_multianual"].sum()
            ),
        },
        "pico_simultaneo_nacional": {
            "data_inicio_semana": str(peak[DATE_COLUMN].date()),
            "ano_epidemiologico": int(peak[YEAR_COLUMN]),
            "semana_epidemiologica": int(peak[WEEK_COLUMN]),
            "municipios_em_risco": int(peak["unidades_em_risco"]),
            "proporcao": float(peak["proporcao_unidades_em_risco"]),
        },
        "validacoes": {
            "targets_recalculados": False,
            "ausencias_convertidas_em_false": False,
            "semanas_risco_preservadas": True,
            "episodios_consecutivos": True,
            "virada_ano_pode_manter_episodio": True,
        },
        "linhas_artefatos": {
            "episodios": len(episodes),
            "municipios": len(municipal),
            "serie_semanal": len(weekly),
            "ano_regiao": len(year_region),
        },
        "artefatos": {
            "episodios": str(EPISODES_OUTPUT),
            "municipios": str(MUNICIPAL_OUTPUT),
            "serie_semanal": str(WEEKLY_OUTPUT),
            "ano_regiao": str(YEAR_REGION_OUTPUT),
            "auditoria": str(AUDIT_OUTPUT),
        },
    }


def main() -> None:
    """Executa a análise de dinâmica epidemiológica."""
    print("=" * 108)
    print("DINÂMICA EPIDEMIOLÓGICA DO RISCO ELEVADO — 2018–2025")
    print("=" * 108)

    print()
    print("Carregando targets oficiais...")

    dataframe = load_targets()

    validate_targets(dataframe)

    registry = load_registry()

    dataframe = enrich_targets(
        dataframe,
        registry,
    )

    episodes = build_episodes(dataframe)

    municipal = build_municipal_summary(
        dataframe,
        episodes,
    )

    weekly = build_weekly_series(dataframe)

    year_region = build_year_region_summary(
        dataframe,
        episodes,
    )

    EPISODES_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    episodes.to_csv(
        EPISODES_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    municipal.to_csv(
        MUNICIPAL_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    weekly.to_csv(
        WEEKLY_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    year_region.to_csv(
        YEAR_REGION_OUTPUT,
        index=False,
        encoding="utf-8",
    )

    audit = build_audit(
        dataframe,
        episodes,
        municipal,
        weekly,
        year_region,
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

    print(f"Linhas totais                     : {len(dataframe):,}")

    print(
        f"Risco definido                    : {dataframe[RISK_COLUMN].notna().sum():,}"
    )

    print(
        f"Risco ausente                     : {dataframe[RISK_COLUMN].isna().sum():,}"
    )

    print(f"Municípios elegíveis              : {len(municipal):,}")

    print(
        f"Semanas em risco                  : {int(municipal['semanas_risco'].sum()):,}"
    )

    print()
    print("=" * 108)
    print("EPISÓDIOS")
    print("=" * 108)

    print(f"Quantidade de episódios           : {len(episodes):,}")

    print(
        "Duração média                     : "
        f"{episodes['duracao_semanas'].mean():.2f} semanas"
    )

    print(
        "Duração mediana                   : "
        f"{episodes['duracao_semanas'].median():.2f} semanas"
    )

    print(
        "Duração máxima                    : "
        f"{int(episodes['duracao_semanas'].max())} semanas"
    )

    print(
        "Episódios atravessando ano        : "
        f"{int(episodes['atravessa_ano_epidemiologico'].sum()):,}"
    )

    print()
    print("=" * 108)
    print("RECORRÊNCIA MUNICIPAL")
    print("=" * 108)

    print(
        "Municípios com algum risco        : "
        f"{int(municipal['semanas_risco'].gt(0).sum()):,}"
    )

    print(
        "Recorrência em >= 2 anos           : "
        f"{int(municipal['recorrencia_multianual'].sum()):,}"
    )

    national = weekly.loc[weekly["escala"].eq("nacional")]

    peak = national.loc[national["unidades_em_risco"].idxmax()]

    print()
    print("=" * 108)
    print("PICO DE MUNICÍPIOS SIMULTANEAMENTE EM RISCO")
    print("=" * 108)

    print(f"Ano epidemiológico                : {int(peak[YEAR_COLUMN])}")

    print(f"Semana epidemiológica             : {int(peak[WEEK_COLUMN])}")

    print(f"Data inicial                      : {peak[DATE_COLUMN].date()}")

    print(f"Municípios em risco               : {int(peak['unidades_em_risco']):,}")

    print(
        f"Proporção                         : {peak['proporcao_unidades_em_risco']:.2%}"
    )

    print()
    print("Arquivos gerados:")

    print(f"  Episódios                        : {EPISODES_OUTPUT}")

    print(f"  Resumo municipal                 : {MUNICIPAL_OUTPUT}")

    print(f"  Série semanal                    : {WEEKLY_OUTPUT}")

    print(f"  Ano × região                     : {YEAR_REGION_OUTPUT}")

    print(f"  Auditoria                        : {AUDIT_OUTPUT}")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
