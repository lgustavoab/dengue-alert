"""Cria o perfil epidemiológico histórico municipal para análise pós-teste."""

import json

import numpy as np
import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.modeling.splits import MUNICIPALITY_COLUMN, YEAR_COLUMN

INPUT_DATASET = MASTER_PANEL.parent / "dataset_modelagem_2018_2024.parquet"

OUTPUT_PARQUET = (
    MASTER_PANEL.parent / "perfil_epidemiologico_municipios_2018_2024.parquet"
)

AUDIT_OUTPUT = REPORTS_DIR / "audits" / "auditoria_perfil_epidemiologico_2018_2024.json"

EXPECTED_ROWS = 2_032_685
EXPECTED_MUNICIPALITIES = 5_569
EXPECTED_YEARS = tuple(
    range(
        2018,
        2025,
    )
)
EXPECTED_WEEKS_PER_MUNICIPALITY = 365

INCIDENCE_COLUMN = "incidencia_100mil"
PROFILE_COLUMN = "incidencia_media_semanal_2018_2024"
QUARTILE_COLUMN = "quartil_epidemiologico"

QUARTILE_LABELS = (
    "Q1",
    "Q2",
    "Q3",
    "Q4",
)


def required_columns() -> list[str]:
    """Retorna somente as colunas necessárias para criar o perfil."""
    return [
        MUNICIPALITY_COLUMN,
        "nome_municipio_ibge",
        "nome_uf_ibge",
        YEAR_COLUMN,
        "semana_epidemiologica",
        INCIDENCE_COLUMN,
    ]


def validate_input(
    dataframe: pd.DataFrame,
) -> None:
    """Valida a base histórica antes da agregação municipal."""
    if len(dataframe) != EXPECTED_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas históricas. "
            f"Esperado: {EXPECTED_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    municipalities = int(dataframe[MUNICIPALITY_COLUMN].nunique())

    if municipalities != EXPECTED_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de municípios históricos. "
            f"Esperado: {EXPECTED_MUNICIPALITIES:,}; "
            f"obtido: {municipalities:,}."
        )

    years = tuple(sorted(int(value) for value in dataframe[YEAR_COLUMN].unique()))

    if years != EXPECTED_YEARS:
        raise ValueError(
            "Período histórico inesperado. "
            f"Esperado: {EXPECTED_YEARS}; "
            f"obtido: {years}."
        )

    if dataframe[MUNICIPALITY_COLUMN].isna().any():
        raise ValueError("Existem códigos municipais ausentes.")

    if dataframe[INCIDENCE_COLUMN].isna().any():
        missing = int(dataframe[INCIDENCE_COLUMN].isna().sum())

        raise ValueError(f"Existem {missing:,} incidências históricas ausentes.")

    if not np.isfinite(
        dataframe[INCIDENCE_COLUMN].to_numpy(
            dtype=np.float64,
            copy=False,
        )
    ).all():
        raise ValueError("Existem valores de incidência não finitos.")

    if (dataframe[INCIDENCE_COLUMN] < 0).any():
        raise ValueError("Existem valores negativos de incidência.")


def build_profile(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Agrega a incidência semanal e cria quartis epidemiológicos."""
    profile = (
        dataframe.groupby(
            [
                MUNICIPALITY_COLUMN,
                "nome_municipio_ibge",
                "nome_uf_ibge",
            ],
            as_index=False,
            observed=True,
        )
        .agg(
            **{
                PROFILE_COLUMN: (
                    INCIDENCE_COLUMN,
                    "mean",
                ),
                "semanas_historicas": (
                    INCIDENCE_COLUMN,
                    "size",
                ),
            }
        )
        .sort_values(MUNICIPALITY_COLUMN)
        .reset_index(drop=True)
    )

    quantiles = profile[PROFILE_COLUMN].quantile(
        [
            0.25,
            0.50,
            0.75,
        ]
    )

    q25 = float(quantiles.loc[0.25])

    q50 = float(quantiles.loc[0.50])

    q75 = float(quantiles.loc[0.75])

    if not (q25 <= q50 <= q75):
        raise ValueError("Os pontos de corte dos quartis são inconsistentes.")

    profile[QUARTILE_COLUMN] = np.select(
        [
            profile[PROFILE_COLUMN] <= q25,
            profile[PROFILE_COLUMN] <= q50,
            profile[PROFILE_COLUMN] <= q75,
        ],
        [
            "Q1",
            "Q2",
            "Q3",
        ],
        default="Q4",
    )

    cutpoints = {
        "q25": q25,
        "q50": q50,
        "q75": q75,
    }

    return (
        profile,
        cutpoints,
    )


def validate_profile(
    profile: pd.DataFrame,
) -> dict:
    """Audita a caracterização histórica municipal."""
    if len(profile) != EXPECTED_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de perfis municipais. "
            f"Esperado: {EXPECTED_MUNICIPALITIES:,}; "
            f"obtido: {len(profile):,}."
        )

    if profile[MUNICIPALITY_COLUMN].duplicated().any():
        duplicates = int(profile[MUNICIPALITY_COLUMN].duplicated().sum())

        raise ValueError(
            f"Foram encontrados {duplicates:,} códigos municipais duplicados."
        )

    weeks = {int(value) for value in profile["semanas_historicas"].unique()}

    if weeks != {EXPECTED_WEEKS_PER_MUNICIPALITY}:
        raise ValueError(
            "Quantidade inesperada de semanas por município. "
            f"Esperado: {EXPECTED_WEEKS_PER_MUNICIPALITY}; "
            f"obtido: {sorted(weeks)}."
        )

    if profile[PROFILE_COLUMN].isna().any():
        raise ValueError("Existem perfis epidemiológicos sem incidência média.")

    labels = set(profile[QUARTILE_COLUMN].unique())

    if labels != set(QUARTILE_LABELS):
        raise ValueError(
            "Quartis epidemiológicos inesperados. "
            f"Esperado: {QUARTILE_LABELS}; "
            f"obtido: {sorted(labels)}."
        )

    distribution = (
        profile[QUARTILE_COLUMN]
        .value_counts()
        .reindex(
            QUARTILE_LABELS,
            fill_value=0,
        )
    )

    if int(distribution.sum()) != EXPECTED_MUNICIPALITIES:
        raise ValueError(
            "A distribuição dos quartis não preservou todos os municípios."
        )

    return {
        "municipios": len(profile),
        "semanas_por_municipio": EXPECTED_WEEKS_PER_MUNICIPALITY,
        "incidencia_media_minima": float(profile[PROFILE_COLUMN].min()),
        "incidencia_media_maxima": float(profile[PROFILE_COLUMN].max()),
        "distribuicao_quartis": {
            label: int(distribution.loc[label]) for label in QUARTILE_LABELS
        },
    }


def main() -> None:
    """Gera e audita o perfil epidemiológico histórico."""
    print("=" * 96)
    print("PERFIL EPIDEMIOLÓGICO HISTÓRICO — 2018–2024")
    print("=" * 96)

    print()
    print("Carregando dataset histórico...")

    dataframe = pd.read_parquet(
        INPUT_DATASET,
        columns=required_columns(),
    )

    validate_input(dataframe)

    print(f"Linhas históricas                : {len(dataframe):,}")

    print(
        "Municípios históricos            : "
        f"{dataframe[MUNICIPALITY_COLUMN].nunique():,}"
    )

    print("Período                          : 2018–2024")

    print(f"Semanas por município            : {EXPECTED_WEEKS_PER_MUNICIPALITY}")

    profile, cutpoints = build_profile(dataframe)

    audit = validate_profile(profile)

    OUTPUT_PARQUET.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    profile.to_parquet(
        OUTPUT_PARQUET,
        index=False,
    )

    report = {
        "status": "APROVADO",
        "analise": "perfil epidemiológico histórico municipal",
        "periodo": "2018-2024",
        "metrica": {
            "nome": PROFILE_COLUMN,
            "definicao": (
                "Média da incidência semanal por 100 mil habitantes entre 2018 e 2024."
            ),
        },
        "quartis": {
            "metodo": (
                "Pontos de corte nacionais nos percentis "
                "25, 50 e 75 da incidência média municipal."
            ),
            "pontos_de_corte": cutpoints,
            "labels": list(QUARTILE_LABELS),
        },
        "auditoria": audit,
        "observacao": (
            "O perfil usa somente 2018-2024. "
            "Municípios sem existência histórica nesse período "
            "não recebem perfil por imputação."
        ),
        "arquivo": str(OUTPUT_PARQUET),
    }

    AUDIT_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with AUDIT_OUTPUT.open(
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
    print("=" * 96)
    print("RESULTADO")
    print("=" * 96)

    print(f"Perfis municipais                : {audit['municipios']:,}")

    print()
    print("Pontos de corte:")

    print(f"  Q25                             : {cutpoints['q25']:.6f}")

    print(f"  Q50                             : {cutpoints['q50']:.6f}")

    print(f"  Q75                             : {cutpoints['q75']:.6f}")

    print()
    print("Distribuição:")

    for label in QUARTILE_LABELS:
        print(
            f"  {label:<3}                             : "
            f"{audit['distribuicao_quartis'][label]:,}"
        )

    print()
    print(f"Arquivo Parquet                  : {OUTPUT_PARQUET}")

    print(f"Auditoria JSON                   : {AUDIT_OUTPUT}")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
