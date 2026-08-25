"""Diagnostica o alvo epidemiológico definitivo do projeto Dengue Alert."""

import json
from time import perf_counter

import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR

DEVELOPMENT_END_YEAR = 2024

ROLLING_CASE_WEEKS = 4
SEASONAL_RADIUS_WEEKS = 4
MINIMUM_PRIOR_YEARS = 2
MINIMUM_HISTORICAL_OBSERVATIONS = 12
TARGET_QUANTILE = 0.90

EXPECTED_ELIGIBLE_ROWS = 2_032_685
EXPECTED_MUNICIPALITIES = 5_569
EXPECTED_POSITIVES = 377_275


def normalize_ibge_code(series: pd.Series) -> pd.Series:
    """Normaliza códigos IBGE como texto de sete dígitos."""
    return series.astype("string").str.strip().str.zfill(7)


def calculate_four_week_incidence(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula casos e incidência acumulados nas últimas quatro semanas."""
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
) -> list[int]:
    """Retorna semanas sazonais vizinhas respeitando anos de 52 ou 53 semanas."""
    center_week = min(
        target_week,
        weeks_in_source_year,
    )

    return sorted(
        {
            ((center_week - 1 + offset) % weeks_in_source_year) + 1
            for offset in range(
                -SEASONAL_RADIUS_WEEKS,
                SEASONAL_RADIUS_WEEKS + 1,
            )
        }
    )


def calculate_seasonal_p90_threshold(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula P90 sazonal utilizando exclusivamente anos anteriores."""
    dataframe = dataframe.copy()

    dataframe["limiar_sazonal_p90"] = float("nan")
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

    for (year, week), group in dataframe.groupby(
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

        print(f"Calculando P90 de {target_year}: {len(prior_years)} anos anteriores...")

        for target_week in target_weeks:
            historical_parts = []

            for source_year in prior_years:
                source_weeks = seasonal_week_window(
                    target_week=target_week,
                    weeks_in_source_year=(weeks_per_year[source_year]),
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

            threshold = grouped.quantile(TARGET_QUANTILE)

            valid_codes = counts.loc[counts >= MINIMUM_HISTORICAL_OBSERVATIONS].index

            threshold = threshold.loc[threshold.index.intersection(valid_codes)]

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
                "limiar_sazonal_p90",
            ] = target_codes.map(threshold)

            dataframe.loc[
                target_mask,
                "observacoes_historicas_sazonais",
            ] = target_codes.map(counts)

    return dataframe


def build_definitive_target(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Seleciona semanas elegíveis e cria o indicador de risco elevado."""
    dataframe = dataframe.copy()

    eligible = dataframe.loc[
        dataframe["limiar_sazonal_p90"].notna()
        & dataframe["incidencia_4s_100mil"].notna()
    ].copy()

    eligible["risco_elevado"] = (
        eligible["incidencia_4s_100mil"] > eligible["limiar_sazonal_p90"]
    )

    eligible = eligible.sort_values(
        [
            "codigo_ibge_7",
            "data_inicio_semana",
        ]
    ).reset_index(drop=True)

    return eligible


def diagnose_episodes(
    dataframe: pd.DataFrame,
) -> dict:
    """Caracteriza episódios consecutivos de risco epidemiológico elevado."""
    dataframe = dataframe.copy()

    grouped = dataframe.groupby(
        "codigo_ibge_7",
        observed=True,
        sort=False,
    )

    previous_target = grouped["risco_elevado"].shift(1)

    previous_date = grouped["data_inicio_semana"].shift(1)

    gap_days = (dataframe["data_inicio_semana"] - previous_date).dt.days

    non_weekly_gaps = int((previous_date.notna() & gap_days.ne(7)).sum())

    dataframe["inicio_episodio"] = dataframe["risco_elevado"] & (
        previous_target.ne(True) | gap_days.ne(7)
    )

    dataframe["episodio_id"] = dataframe.groupby(
        "codigo_ibge_7",
        observed=True,
        sort=False,
    )["inicio_episodio"].cumsum()

    episodes = (
        dataframe.loc[dataframe["risco_elevado"]]
        .groupby(
            [
                "codigo_ibge_7",
                "episodio_id",
            ],
            observed=True,
        )
        .agg(
            inicio=(
                "data_inicio_semana",
                "min",
            ),
            fim=(
                "data_inicio_semana",
                "max",
            ),
            duracao_semanas=(
                "risco_elevado",
                "size",
            ),
        )
        .reset_index()
    )

    longest_episodes = (
        episodes.sort_values(
            "duracao_semanas",
            ascending=False,
        )
        .head(20)
        .copy()
    )

    municipality_info = dataframe[
        [
            "codigo_ibge_7",
            "nome_municipio_ibge",
            "nome_uf_ibge",
        ]
    ].drop_duplicates(subset=["codigo_ibge_7"])

    longest_episodes = longest_episodes.merge(
        municipality_info,
        on="codigo_ibge_7",
        how="left",
        validate="many_to_one",
    )

    duration = episodes["duracao_semanas"]

    duration_distribution = {
        "1_semana": int((duration == 1).sum()),
        "2_semanas": int((duration == 2).sum()),
        "3_semanas": int((duration == 3).sum()),
        "4_semanas": int((duration == 4).sum()),
        "5_a_7_semanas": int(
            duration.between(
                5,
                7,
                inclusive="both",
            ).sum()
        ),
        "8_ou_mais_semanas": int((duration >= 8).sum()),
    }

    return {
        "quantidade_episodios": len(episodes),
        "municipios_com_episodio": int(episodes["codigo_ibge_7"].nunique()),
        "duracao_semanas": {
            "media": float(duration.mean()),
            "mediana": float(duration.median()),
            "p75": float(duration.quantile(0.75)),
            "p90": float(duration.quantile(0.90)),
            "maximo": int(duration.max()),
        },
        "distribuicao_duracao": duration_distribution,
        "episodios_mais_longos": [
            {
                "codigo_ibge_7": row.codigo_ibge_7,
                "municipio": row.nome_municipio_ibge,
                "uf": row.nome_uf_ibge,
                "inicio": row.inicio.strftime("%Y-%m-%d"),
                "fim": row.fim.strftime("%Y-%m-%d"),
                "duracao_semanas": int(row.duracao_semanas),
            }
            for row in longest_episodes.itertuples(index=False)
        ],
        "lacunas_temporais_na_serie": non_weekly_gaps,
    }


def diagnose_persistence(
    dataframe: pd.DataFrame,
) -> dict:
    """Mede a persistência do estado de risco nos horizontes de 1 a 4 semanas."""
    persistence = {}

    grouped = dataframe.groupby(
        "codigo_ibge_7",
        observed=True,
        sort=False,
    )

    for horizon in range(1, 5):
        future_target = grouped["risco_elevado"].shift(-horizon)

        valid = future_target.notna()

        current = dataframe.loc[
            valid,
            "risco_elevado",
        ]

        future = future_target.loc[valid].astype(bool)

        current_positive = current

        current_negative = ~current

        agreement = float((current.to_numpy() == future.to_numpy()).mean())

        future_positive_given_positive = float(future.loc[current_positive].mean())

        future_positive_given_negative = float(future.loc[current_negative].mean())

        persistence[f"h{horizon}"] = {
            "linhas_com_futuro_disponivel": int(valid.sum()),
            "acordo_estado_atual_futuro": agreement,
            "probabilidade_futuro_positivo_dado_atual_positivo": future_positive_given_positive,
            "probabilidade_futuro_positivo_dado_atual_negativo": future_positive_given_negative,
        }

    return persistence


def main() -> None:
    """Executa o diagnóstico do alvo definitivo."""
    print("=" * 88)
    print("DIAGNÓSTICO DO ALVO DEFINITIVO — DENGUE ALERT")
    print("=" * 88)

    start = perf_counter()

    columns = [
        "codigo_ibge_7",
        "nome_municipio_ibge",
        "nome_uf_ibge",
        "ano_epidemiologico",
        "semana_epidemiologica",
        "data_inicio_semana",
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

    dataframe["data_inicio_semana"] = pd.to_datetime(dataframe["data_inicio_semana"])

    dataframe = dataframe.loc[dataframe["modelavel_era5_land"]].copy()

    dataframe = dataframe.sort_values(
        [
            "codigo_ibge_7",
            "ano_epidemiologico",
            "semana_epidemiologica",
        ]
    ).reset_index(drop=True)

    dataframe = calculate_four_week_incidence(dataframe)

    dataframe = calculate_seasonal_p90_threshold(dataframe)

    target = build_definitive_target(dataframe)

    eligible_rows = len(target)
    municipalities = int(target["codigo_ibge_7"].nunique())
    positives = int(target["risco_elevado"].sum())
    prevalence = float(target["risco_elevado"].mean())

    years = sorted(int(year) for year in target["ano_epidemiologico"].unique())

    if eligible_rows != EXPECTED_ELIGIBLE_ROWS:
        raise ValueError(
            f"Quantidade inesperada de linhas elegíveis: {eligible_rows:,}."
        )

    if municipalities != EXPECTED_MUNICIPALITIES:
        raise ValueError(f"Quantidade inesperada de municípios: {municipalities:,}.")

    if positives != EXPECTED_POSITIVES:
        raise ValueError(
            "O alvo P90 sazonal não reproduziu "
            "a análise anterior. "
            f"Esperado: {EXPECTED_POSITIVES:,}; "
            f"obtido: {positives:,}."
        )

    if years != list(range(2018, 2025)):
        raise ValueError(f"Período elegível inesperado: {years}.")

    episodes = diagnose_episodes(target)

    persistence = diagnose_persistence(target)

    by_year = {}

    for year, group in target.groupby(
        "ano_epidemiologico",
        observed=True,
    ):
        by_year[str(int(year))] = {
            "linhas": len(group),
            "positivos": int(group["risco_elevado"].sum()),
            "prevalencia": float(group["risco_elevado"].mean()),
        }

    duration = perf_counter() - start

    report = {
        "status": "APROVADO",
        "definicao_alvo": {
            "nome": ("risco_epidemiologico_elevado"),
            "janela_incidencia_semanas": ROLLING_CASE_WEEKS,
            "percentil_historico": TARGET_QUANTILE,
            "raio_sazonal_semanas": SEASONAL_RADIUS_WEEKS,
            "somente_anos_anteriores": True,
            "anos_anteriores_minimos": MINIMUM_PRIOR_YEARS,
            "observacoes_historicas_minimas": MINIMUM_HISTORICAL_OBSERVATIONS,
            "regra": ("incidencia_4s_100mil > limiar_sazonal_p90"),
        },
        "escopo": {
            "periodo_elegivel": "2018-2024",
            "ano_teste_final_excluido": 2025,
            "linhas_elegiveis": eligible_rows,
            "municipios": municipalities,
            "positivos": positives,
            "prevalencia": prevalence,
        },
        "por_ano": by_year,
        "episodios": episodes,
        "persistencia": persistence,
        "tempo_execucao_segundos": duration,
    }

    destination = REPORTS_DIR / "audits" / "diagnostico_alvo_definitivo.json"

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
    print("Período elegível                 : 2018–2024")
    print(f"Linhas elegíveis                 : {eligible_rows:,}")
    print(f"Municípios                       : {municipalities:,}")
    print(f"Semanas de risco elevado         : {positives:,}")
    print(f"Prevalência                      : {prevalence:.2%}")

    print()
    print("EPISÓDIOS")
    print(f"  Quantidade                     : {episodes['quantidade_episodios']:,}")
    print(f"  Municípios com episódio        : {episodes['municipios_com_episodio']:,}")
    print(
        f"  Duração média                  : {episodes['duracao_semanas']['media']:.2f}"
    )
    print(
        "  Duração mediana                : "
        f"{episodes['duracao_semanas']['mediana']:.1f}"
    )
    print(
        f"  Duração P75                    : {episodes['duracao_semanas']['p75']:.1f}"
    )
    print(
        f"  Duração P90                    : {episodes['duracao_semanas']['p90']:.1f}"
    )
    print(f"  Duração máxima                 : {episodes['duracao_semanas']['maximo']}")

    print()
    print("EPISÓDIOS MAIS LONGOS")

    for episode in episodes["episodios_mais_longos"]:
        print(
            f"  {episode['municipio']} - {episode['uf']} | "
            f"{episode['inicio']} a {episode['fim']} | "
            f"{episode['duracao_semanas']} semanas"
        )

    print()
    print("PERSISTÊNCIA")

    for horizon, values in persistence.items():
        print(
            f"  {horizon.upper()} | "
            "P(futuro alto | atual alto): "
            f"{values['probabilidade_futuro_positivo_dado_atual_positivo']:.2%}"
        )
        print(
            "       P(futuro alto | atual normal): "
            f"{values['probabilidade_futuro_positivo_dado_atual_negativo']:.2%}"
        )
        print(f"       Acordo atual/futuro: {values['acordo_estado_atual_futuro']:.2%}")

    print()
    print(
        f"Lacunas temporais                : {episodes['lacunas_temporais_na_serie']:,}"
    )
    print(f"Tempo de execução                : {duration:.2f} s")
    print()
    print(f"Relatório: {destination}")


if __name__ == "__main__":
    main()
