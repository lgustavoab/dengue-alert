"""Analisa definições sazonais candidatas para o alvo epidemiológico."""

import json
from time import perf_counter

import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR

DEVELOPMENT_END_YEAR = 2024

ROLLING_CASE_WEEKS = 4

SEASONAL_RADIUS_WEEKS = 4
MINIMUM_PRIOR_YEARS = 2
MINIMUM_HISTORICAL_OBSERVATIONS = 12

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
    """Calcula casos e incidência acumulados em quatro semanas."""
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


def seasonal_week_window(
    target_week: int,
    weeks_in_source_year: int,
    radius: int = SEASONAL_RADIUS_WEEKS,
) -> list[int]:
    """Retorna semanas vizinhas respeitando anos de 52 ou 53 semanas."""
    center_week = min(
        target_week,
        weeks_in_source_year,
    )

    return sorted(
        {
            ((center_week - 1 + offset) % weeks_in_source_year) + 1
            for offset in range(-radius, radius + 1)
        }
    )


def calculate_seasonal_thresholds(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula limiares sazonais usando somente anos anteriores."""
    dataframe = dataframe.copy()

    threshold_columns = {
        candidate: f"limiar_sazonal_{candidate}" for candidate in CANDIDATE_QUANTILES
    }

    for column in threshold_columns.values():
        dataframe[column] = float("nan")

    dataframe["observacoes_historicas_sazonais"] = float("nan")

    weeks_per_year = (
        dataframe.groupby(
            "ano_epidemiologico",
            observed=True,
        )["semana_epidemiologica"]
        .max()
        .astype(int)
        .to_dict()
    )

    lookup = {}

    for (
        year,
        week,
    ), group in dataframe.groupby(
        [
            "ano_epidemiologico",
            "semana_epidemiologica",
        ],
        observed=True,
    ):
        lookup[(int(year), int(week))] = (
            group[
                [
                    "codigo_ibge_7",
                    "incidencia_4s_100mil",
                ]
            ]
            .dropna(subset=["incidencia_4s_100mil"])
            .copy()
        )

    years = sorted(int(year) for year in dataframe["ano_epidemiologico"].unique())

    for target_year in years:
        prior_years = [year for year in years if year < target_year]

        if len(prior_years) < MINIMUM_PRIOR_YEARS:
            continue

        target_weeks = sorted(
            int(week)
            for week in dataframe.loc[
                dataframe["ano_epidemiologico"] == target_year,
                "semana_epidemiologica",
            ].unique()
        )

        print(f"Calculando {target_year}: {len(prior_years)} anos anteriores...")

        for target_week in target_weeks:
            historical_parts = []

            for source_year in prior_years:
                weeks_in_source_year = weeks_per_year[source_year]

                source_weeks = seasonal_week_window(
                    target_week=target_week,
                    weeks_in_source_year=(weeks_in_source_year),
                )

                for source_week in source_weeks:
                    part = lookup.get(
                        (
                            source_year,
                            source_week,
                        )
                    )

                    if part is not None and not part.empty:
                        historical_parts.append(part)

            if not historical_parts:
                continue

            historical = pd.concat(
                historical_parts,
                ignore_index=True,
            )

            grouped = historical.groupby(
                "codigo_ibge_7",
                observed=True,
            )["incidencia_4s_100mil"]

            counts = grouped.count()

            quantiles = grouped.quantile(list(CANDIDATE_QUANTILES.values())).unstack()

            valid_codes = counts.loc[counts >= MINIMUM_HISTORICAL_OBSERVATIONS].index

            quantiles = quantiles.loc[quantiles.index.intersection(valid_codes)]

            counts = counts.loc[counts.index.intersection(valid_codes)]

            target_mask = (dataframe["ano_epidemiologico"] == target_year) & (
                dataframe["semana_epidemiologica"] == target_week
            )

            target_codes = dataframe.loc[
                target_mask,
                "codigo_ibge_7",
            ]

            dataframe.loc[
                target_mask,
                "observacoes_historicas_sazonais",
            ] = target_codes.map(counts)

            for candidate, quantile in CANDIDATE_QUANTILES.items():
                dataframe.loc[
                    target_mask,
                    threshold_columns[candidate],
                ] = target_codes.map(quantiles[quantile])

    return dataframe


def add_population_group(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Adiciona faixas populacionais para diagnóstico."""
    dataframe = dataframe.copy()

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

    return dataframe


def summarize_candidate(
    dataframe: pd.DataFrame,
    candidate: str,
) -> dict:
    """Resume prevalência e distribuição do candidato sazonal."""
    threshold_column = f"limiar_sazonal_{candidate}"
    target_column = f"alvo_sazonal_{candidate}"

    eligible = dataframe.loc[
        dataframe[threshold_column].notna() & dataframe["incidencia_4s_100mil"].notna()
    ].copy()

    eligible[target_column] = (
        eligible["incidencia_4s_100mil"] > eligible[threshold_column]
    )

    total = len(eligible)
    positives = int(eligible[target_column].sum())

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

    municipalities_with_positive = int((by_municipality["positivos"] > 0).sum())

    municipalities_without_positive = int((by_municipality["positivos"] == 0).sum())

    observations = eligible["observacoes_historicas_sazonais"]

    return {
        "candidato": candidate,
        "linhas_elegiveis": total,
        "positivos": positives,
        "prevalencia": (float(eligible[target_column].mean()) if total else None),
        "municipios_com_evento": municipalities_with_positive,
        "municipios_sem_evento": municipalities_without_positive,
        "prevalencia_mediana_municipal": (
            float(by_municipality["prevalencia"].median())
            if not by_municipality.empty
            else None
        ),
        "observacoes_historicas": {
            "minimo": (int(observations.min()) if not observations.empty else None),
            "mediana": (
                float(observations.median()) if not observations.empty else None
            ),
            "maximo": (int(observations.max()) if not observations.empty else None),
        },
        "por_ano": by_year,
        "por_faixa_populacional": by_population_group,
    }


def main() -> None:
    """Executa a análise dos alvos sazonais candidatos."""
    print("=" * 88)
    print("ANÁLISE DE ALVOS SAZONAIS CANDIDATOS — DENGUE ALERT")
    print("=" * 88)

    start = perf_counter()

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

    key = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "semana_epidemiologica",
    ]

    duplicate_keys = int(dataframe.duplicated(key).sum())

    if duplicate_keys:
        raise ValueError(
            f"A base de desenvolvimento contém {duplicate_keys:,} chaves duplicadas."
        )

    dataframe = calculate_four_week_incidence(dataframe)

    dataframe = add_population_group(dataframe)

    dataframe = calculate_seasonal_thresholds(dataframe)

    summaries = {
        candidate: summarize_candidate(
            dataframe,
            candidate,
        )
        for candidate in CANDIDATE_QUANTILES
    }

    duration = perf_counter() - start

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
            "raio_sazonal_semanas": SEASONAL_RADIUS_WEEKS,
            "largura_nominal_janela_sazonal": (SEASONAL_RADIUS_WEEKS * 2 + 1),
            "somente_anos_anteriores": True,
            "anos_anteriores_minimos": MINIMUM_PRIOR_YEARS,
            "observacoes_historicas_minimas": MINIMUM_HISTORICAL_OBSERVATIONS,
            "quantis_candidatos": CANDIDATE_QUANTILES,
        },
        "candidatos": summaries,
        "tempo_execucao_segundos": duration,
        "observacao": (
            "Esta análise compara definições "
            "sazonais candidatas. Nenhum percentil "
            "foi selecionado como alvo definitivo."
        ),
    }

    destination = REPORTS_DIR / "audits" / "analise_alvos_sazonais_candidatos.json"

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
    print("Período carregado                : 2016–2024")
    print(f"Linhas                           : {len(dataframe):,}")
    print(
        f"Municípios                       : {dataframe['codigo_ibge_7'].nunique():,}"
    )
    print(f"Janela da incidência             : {ROLLING_CASE_WEEKS} semanas")
    print(f"Janela sazonal                   : ±{SEASONAL_RADIUS_WEEKS} semanas")
    print(f"Anos anteriores mínimos          : {MINIMUM_PRIOR_YEARS}")
    print(f"Observações históricas mínimas   : {MINIMUM_HISTORICAL_OBSERVATIONS}")

    for candidate in CANDIDATE_QUANTILES:
        summary = summaries[candidate]

        print()
        print(candidate.upper())
        print(f"  Linhas elegíveis               : {summary['linhas_elegiveis']:,}")
        print(f"  Eventos positivos              : {summary['positivos']:,}")
        print(f"  Prevalência                    : {summary['prevalencia']:.2%}")
        print(
            f"  Municípios com evento          : {summary['municipios_com_evento']:,}"
        )
        print(
            f"  Municípios sem evento          : {summary['municipios_sem_evento']:,}"
        )
        print(
            "  Prevalência mediana municipal  : "
            f"{summary['prevalencia_mediana_municipal']:.2%}"
        )
        print(
            "  Histórico sazonal (min/med/max): "
            f"{summary['observacoes_historicas']['minimo']} / "
            f"{summary['observacoes_historicas']['mediana']:.0f} / "
            f"{summary['observacoes_historicas']['maximo']}"
        )

    print()
    print(f"Tempo de execução                : {duration:.2f} s")
    print(f"Relatório: {destination}")


if __name__ == "__main__":
    main()
