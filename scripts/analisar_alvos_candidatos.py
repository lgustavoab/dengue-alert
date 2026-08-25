"""Analisa definições candidatas para o alvo epidemiológico do projeto."""

import json

import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR

DEVELOPMENT_END_YEAR = 2024
ROLLING_CASE_WEEKS = 4
HISTORICAL_WINDOW_WEEKS = 104
MINIMUM_HISTORY_WEEKS = 52

CANDIDATE_QUANTILES = {
    "p75": 0.75,
    "p80": 0.80,
    "p90": 0.90,
}


def normalize_ibge_code(series: pd.Series) -> pd.Series:
    """Normaliza códigos IBGE como texto de sete dígitos."""
    return series.astype("string").str.strip().str.zfill(7)


def calculate_four_week_incidence(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula casos e incidência acumulados em janela móvel de quatro semanas."""
    dataframe = dataframe.copy()

    dataframe["casos_4s"] = dataframe.groupby(
        "codigo_ibge_7",
        observed=True,
    )["casos_provaveis"].transform(
        lambda series: series.rolling(
            window=ROLLING_CASE_WEEKS,
            min_periods=ROLLING_CASE_WEEKS,
        ).sum()
    )

    dataframe["incidencia_4s_100mil"] = (
        dataframe["casos_4s"] / dataframe["populacao"] * 100_000
    )

    return dataframe


def calculate_historical_threshold(
    series: pd.Series,
    quantile: float,
) -> pd.Series:
    """Calcula limiar usando somente semanas anteriores do mesmo município."""
    return (
        series.shift(1)
        .rolling(
            window=HISTORICAL_WINDOW_WEEKS,
            min_periods=MINIMUM_HISTORY_WEEKS,
        )
        .quantile(quantile)
    )


def summarize_candidate(
    dataframe: pd.DataFrame,
    candidate: str,
    threshold_column: str,
    target_column: str,
) -> dict:
    """Resume prevalência e cobertura de uma definição candidata."""
    eligible = dataframe.loc[
        dataframe[threshold_column].notna() & dataframe["incidencia_4s_100mil"].notna()
    ].copy()

    positives = int(eligible[target_column].sum())
    total = len(eligible)

    prevalence = float(eligible[target_column].mean()) if total else None

    by_year = {}

    for year, group in eligible.groupby(
        "ano_epidemiologico",
        observed=True,
    ):
        by_year[str(int(year))] = {
            "linhas": len(group),
            "positivos": int(group[target_column].sum()),
            "prevalencia": float(group[target_column].mean()),
        }

    by_population_group = {}

    for population_group, group in eligible.groupby(
        "faixa_populacional",
        observed=True,
    ):
        by_population_group[str(population_group)] = {
            "linhas": len(group),
            "positivos": int(group[target_column].sum()),
            "prevalencia": float(group[target_column].mean()),
            "municipios": int(group["codigo_ibge_7"].nunique()),
        }

    by_municipality = eligible.groupby(
        "codigo_ibge_7",
        observed=True,
    )[target_column].agg(
        semanas="size",
        positivos="sum",
        prevalencia="mean",
    )

    municipalities_without_positive = int((by_municipality["positivos"] == 0).sum())

    municipalities_with_positive = int((by_municipality["positivos"] > 0).sum())

    return {
        "candidato": candidate,
        "linhas_elegiveis": total,
        "positivos": positives,
        "prevalencia": prevalence,
        "municipios_com_evento": municipalities_with_positive,
        "municipios_sem_evento": municipalities_without_positive,
        "prevalencia_mediana_municipal": (
            float(by_municipality["prevalencia"].median())
            if not by_municipality.empty
            else None
        ),
        "por_ano": by_year,
        "por_faixa_populacional": by_population_group,
    }


def main() -> None:
    """Executa a análise dos candidatos a alvo epidemiológico."""
    print("=" * 88)
    print("ANÁLISE DE ALVOS CANDIDATOS — DENGUE ALERT")
    print("=" * 88)

    columns = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "semana_epidemiologica",
        "casos_provaveis",
        "populacao",
        "modelavel_era5_land",
    ]

    dataframe = pd.read_parquet(
        MASTER_PANEL,
        columns=columns,
        filters=[
            (
                "ano_epidemiologico",
                "<=",
                DEVELOPMENT_END_YEAR,
            )
        ],
    )

    dataframe["codigo_ibge_7"] = normalize_ibge_code(dataframe["codigo_ibge_7"])

    if dataframe["ano_epidemiologico"].max() > DEVELOPMENT_END_YEAR:
        raise ValueError(
            "Dados posteriores a 2024 foram carregados na análise de desenvolvimento."
        )

    dataframe = dataframe.loc[dataframe["modelavel_era5_land"]].copy()

    dataframe = dataframe.sort_values(
        [
            "codigo_ibge_7",
            "ano_epidemiologico",
            "semana_epidemiologica",
        ]
    ).reset_index(drop=True)

    duplicate_keys = int(
        dataframe.duplicated(
            [
                "codigo_ibge_7",
                "ano_epidemiologico",
                "semana_epidemiologica",
            ]
        ).sum()
    )

    if duplicate_keys:
        raise ValueError(
            f"A base de desenvolvimento contém {duplicate_keys:,} chaves duplicadas."
        )

    dataframe = calculate_four_week_incidence(dataframe)

    dataframe["faixa_populacional"] = pd.cut(
        dataframe["populacao"],
        bins=[
            0,
            20_000,
            100_000,
            500_000,
            float("inf"),
        ],
        labels=[
            "ate_20_mil",
            "20_a_100_mil",
            "100_a_500_mil",
            "mais_de_500_mil",
        ],
        right=False,
    )

    summaries = {}

    for candidate, quantile in CANDIDATE_QUANTILES.items():
        threshold_column = f"limiar_{candidate}"
        target_column = f"alvo_{candidate}"

        dataframe[threshold_column] = dataframe.groupby(
            "codigo_ibge_7",
            observed=True,
        )["incidencia_4s_100mil"].transform(
            lambda series, q=quantile: calculate_historical_threshold(
                series,
                q,
            )
        )

        eligible = dataframe[threshold_column].notna()

        dataframe[target_column] = False

        dataframe.loc[
            eligible,
            target_column,
        ] = (
            dataframe.loc[
                eligible,
                "incidencia_4s_100mil",
            ]
            > dataframe.loc[
                eligible,
                threshold_column,
            ]
        )

        summaries[candidate] = summarize_candidate(
            dataframe=dataframe,
            candidate=candidate,
            threshold_column=threshold_column,
            target_column=target_column,
        )

    report = {
        "status": "CONCLUIDO",
        "escopo": {
            "periodo": "2016-2024",
            "ano_teste_final_excluido": 2025,
            "somente_unidades_modelaveis_era5": True,
            "municipios": int(dataframe["codigo_ibge_7"].nunique()),
            "linhas": len(dataframe),
        },
        "definicao_experimental": {
            "janela_incidencia_semanas": ROLLING_CASE_WEEKS,
            "janela_historica_semanas": HISTORICAL_WINDOW_WEEKS,
            "historico_minimo_semanas": MINIMUM_HISTORY_WEEKS,
            "usa_apenas_passado": True,
            "quantis_candidatos": CANDIDATE_QUANTILES,
        },
        "candidatos": summaries,
        "observacao": (
            "Esta análise compara definições candidatas. "
            "Nenhum percentil foi selecionado como alvo "
            "definitivo nesta etapa."
        ),
    }

    destination = REPORTS_DIR / "audits" / "analise_alvos_candidatos.json"

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with destination.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("Período analisado               : 2016–2024")
    print(f"Linhas de desenvolvimento       : {len(dataframe):,}")
    print(f"Municípios                      : {dataframe['codigo_ibge_7'].nunique():,}")
    print(f"Janela da incidência            : {ROLLING_CASE_WEEKS} semanas")
    print(f"Histórico do limiar             : {HISTORICAL_WINDOW_WEEKS} semanas")
    print(f"Histórico mínimo                : {MINIMUM_HISTORY_WEEKS} semanas")

    for candidate in CANDIDATE_QUANTILES:
        summary = summaries[candidate]

        print()
        print(f"{candidate.upper()}")
        print(f"  Linhas elegíveis              : {summary['linhas_elegiveis']:,}")
        print(f"  Eventos positivos             : {summary['positivos']:,}")
        print(f"  Prevalência                   : {summary['prevalencia']:.2%}")
        print(f"  Municípios com evento         : {summary['municipios_com_evento']:,}")
        print(f"  Municípios sem evento         : {summary['municipios_sem_evento']:,}")
        print(
            "  Prevalência mediana municipal : "
            f"{summary['prevalencia_mediana_municipal']:.2%}"
        )

    print()
    print(f"Relatório: {destination}")


if __name__ == "__main__":
    main()
