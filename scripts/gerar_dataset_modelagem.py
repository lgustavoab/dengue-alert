"""Gera e audita os datasets definitivos de modelagem do Dengue Alert."""

import json
from time import perf_counter

import numpy as np
import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.features.engineering import (
    CLIMATE_FEATURES,
    EPIDEMIOLOGICAL_CLIMATE_FEATURES,
    EPIDEMIOLOGICAL_CLIMATE_SPATIAL_FEATURES,
    EPIDEMIOLOGICAL_FEATURES,
    SPATIAL_FEATURES,
    build_model_features,
)
from dengue_alert.features.targets import (
    DEFAULT_HORIZONS,
    TARGET_COLUMN,
    build_epidemiological_target,
    build_horizon_targets,
)

DEVELOPMENT_START_YEAR = 2018
DEVELOPMENT_END_YEAR = 2024
FINAL_TEST_YEAR = 2025

MAXIMUM_FEATURE_LAG_WEEKS = 8

EXPECTED_MASTER_ROWS = 2_907_593
EXPECTED_MODELABLE_ROWS = 2_907_071

EXPECTED_DEVELOPMENT_ROWS = 2_032_685
EXPECTED_DEVELOPMENT_MUNICIPALITIES = 5_569
EXPECTED_DEVELOPMENT_POSITIVES = 377_275

EXPECTED_TEST_ROWS = 295_210
EXPECTED_TEST_MUNICIPALITIES = 5_570
EXPECTED_TEST_ELIGIBLE_ROWS = 295_157
EXPECTED_TEST_INELIGIBLE_ROWS = 53

NEW_MUNICIPALITY_CODE = "5101837"

DEVELOPMENT_OUTPUT = MASTER_PANEL.parent / "dataset_modelagem_2018_2024.parquet"

FINAL_TEST_OUTPUT = MASTER_PANEL.parent / "dataset_teste_final_2025.parquet"

AUDIT_OUTPUT = REPORTS_DIR / "audits" / "auditoria_features_modelagem.json"


IDENTIFICATION_COLUMNS = (
    "codigo_ibge_7",
    "nome_municipio_ibge",
    "nome_uf_ibge",
    "ano_epidemiologico",
    "semana_epidemiologica",
    "data_inicio_semana",
    "populacao",
)

HORIZON_COLUMNS = tuple(f"target_h{horizon}" for horizon in DEFAULT_HORIZONS)

OFFICIAL_FEATURE_COLUMNS = tuple(EPIDEMIOLOGICAL_CLIMATE_SPATIAL_FEATURES)


def validate_unique_keys(
    dataframe: pd.DataFrame,
    name: str,
) -> None:
    """Valida unicidade das chaves município-semana."""
    key = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "semana_epidemiologica",
    ]

    duplicates = int(dataframe.duplicated(key).sum())

    if duplicates:
        raise ValueError(f"{name}: encontradas {duplicates:,} chaves duplicadas.")


def build_partition_features(
    target_panel: pd.DataFrame,
    *,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Constrói features preservando o histórico necessário aos lags."""
    partition_start = target_panel.loc[
        target_panel["ano_epidemiologico"] == start_year,
        "data_inicio_semana",
    ].min()

    if pd.isna(partition_start):
        raise ValueError(f"Não foi encontrada data inicial para {start_year}.")

    history_start = partition_start - pd.Timedelta(weeks=MAXIMUM_FEATURE_LAG_WEEKS)

    source = target_panel.loc[
        (target_panel["data_inicio_semana"] >= history_start)
        & (target_panel["ano_epidemiologico"] <= end_year)
    ].copy()

    features = build_model_features(source)

    partition = build_horizon_targets(
        features,
        start_year=start_year,
        end_year=end_year,
        horizons=DEFAULT_HORIZONS,
    )

    return partition


def validate_feature_columns(
    dataframe: pd.DataFrame,
) -> None:
    """Garante que todas as features oficiais foram criadas."""
    missing = sorted(set(OFFICIAL_FEATURE_COLUMNS) - set(dataframe.columns))

    if missing:
        raise ValueError("Features oficiais ausentes: " + ", ".join(missing))


def validate_complete_features(
    dataframe: pd.DataFrame,
    *,
    mask: pd.Series,
    name: str,
) -> None:
    """Valida ausência de nulos e infinitos nas linhas elegíveis."""
    eligible_rows = int(mask.sum())

    if eligible_rows == 0:
        raise ValueError(f"{name}: nenhuma linha elegível.")

    for column in OFFICIAL_FEATURE_COLUMNS:
        missing = int(
            dataframe.loc[
                mask,
                column,
            ]
            .isna()
            .sum()
        )

        if missing:
            raise ValueError(
                f"{name}: feature {column!r} possui "
                f"{missing:,} valores ausentes "
                "em linhas elegíveis."
            )

    numeric_columns = [
        column for column in OFFICIAL_FEATURE_COLUMNS if column != TARGET_COLUMN
    ]

    for column in numeric_columns:
        values = dataframe.loc[
            mask,
            column,
        ].to_numpy(
            dtype="float64",
            copy=False,
        )

        invalid = int((~np.isfinite(values)).sum())

        if invalid:
            raise ValueError(
                f"{name}: feature {column!r} possui {invalid:,} valores não finitos."
            )


def count_rows_with_incomplete_features(
    dataframe: pd.DataFrame,
) -> int:
    """Conta linhas com pelo menos uma feature oficial ausente."""
    incomplete = pd.Series(
        False,
        index=dataframe.index,
    )

    for column in OFFICIAL_FEATURE_COLUMNS:
        incomplete |= dataframe[column].isna()

    return int(incomplete.sum())


def validate_development(
    dataframe: pd.DataFrame,
) -> None:
    """Valida o dataset completo de desenvolvimento."""
    if len(dataframe) != EXPECTED_DEVELOPMENT_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas "
            "no desenvolvimento. "
            f"Esperado: {EXPECTED_DEVELOPMENT_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    municipalities = int(dataframe["codigo_ibge_7"].nunique())

    if municipalities != EXPECTED_DEVELOPMENT_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de municípios "
            "no desenvolvimento. "
            f"Esperado: "
            f"{EXPECTED_DEVELOPMENT_MUNICIPALITIES:,}; "
            f"obtido: {municipalities:,}."
        )

    if dataframe[TARGET_COLUMN].isna().any():
        raise ValueError("O desenvolvimento possui risco atual sem rótulo.")

    positives = int(dataframe[TARGET_COLUMN].sum())

    if positives != EXPECTED_DEVELOPMENT_POSITIVES:
        raise ValueError(
            "Quantidade inesperada de semanas "
            "de risco elevado no desenvolvimento. "
            f"Esperado: "
            f"{EXPECTED_DEVELOPMENT_POSITIVES:,}; "
            f"obtido: {positives:,}."
        )

    validate_complete_features(
        dataframe,
        mask=pd.Series(
            True,
            index=dataframe.index,
        ),
        name="Desenvolvimento",
    )


def validate_final_test(
    dataframe: pd.DataFrame,
) -> None:
    """Valida 2025 sem inspecionar prevalências do teste final."""
    if len(dataframe) != EXPECTED_TEST_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas em 2025. "
            f"Esperado: {EXPECTED_TEST_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    municipalities = int(dataframe["codigo_ibge_7"].nunique())

    if municipalities != EXPECTED_TEST_MUNICIPALITIES:
        raise ValueError(
            "Quantidade inesperada de municípios "
            "no teste final. "
            f"Esperado: "
            f"{EXPECTED_TEST_MUNICIPALITIES:,}; "
            f"obtido: {municipalities:,}."
        )

    eligible = dataframe[TARGET_COLUMN].notna()

    eligible_rows = int(eligible.sum())

    ineligible_rows = int((~eligible).sum())

    if eligible_rows != EXPECTED_TEST_ELIGIBLE_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas "
            "elegíveis em 2025. "
            f"Esperado: "
            f"{EXPECTED_TEST_ELIGIBLE_ROWS:,}; "
            f"obtido: {eligible_rows:,}."
        )

    if ineligible_rows != EXPECTED_TEST_INELIGIBLE_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas "
            "inelegíveis em 2025. "
            f"Esperado: "
            f"{EXPECTED_TEST_INELIGIBLE_ROWS:,}; "
            f"obtido: {ineligible_rows:,}."
        )

    ineligible_codes = set(
        dataframe.loc[
            ~eligible,
            "codigo_ibge_7",
        ].unique()
    )

    if ineligible_codes != {NEW_MUNICIPALITY_CODE}:
        raise ValueError(
            "As linhas inelegíveis de 2025 "
            "não pertencem exclusivamente a "
            "Boa Esperança do Norte. "
            f"Códigos: {ineligible_codes}."
        )

    validate_complete_features(
        dataframe,
        mask=eligible,
        name="Teste final elegível",
    )


def validate_horizon_structure(
    dataframe: pd.DataFrame,
    *,
    expected_municipalities: int,
    name: str,
) -> dict:
    """Valida disponibilidade estrutural dos horizontes."""
    eligible = dataframe[TARGET_COLUMN].notna()

    eligible_data = dataframe.loc[eligible]

    actual_municipalities = int(eligible_data["codigo_ibge_7"].nunique())

    if actual_municipalities != expected_municipalities:
        raise ValueError(
            f"{name}: quantidade inesperada "
            "de municípios elegíveis. "
            f"Esperado: {expected_municipalities:,}; "
            f"obtido: {actual_municipalities:,}."
        )

    rows_per_municipality = eligible_data.groupby(
        "codigo_ibge_7",
        observed=True,
    ).size()

    summary = {}

    for horizon in DEFAULT_HORIZONS:
        column = f"target_h{horizon}"

        expected_valid = int((rows_per_municipality - horizon).clip(lower=0).sum())

        actual_valid = int(dataframe[column].notna().sum())

        if actual_valid != expected_valid:
            raise ValueError(
                f"{name} {column}: quantidade "
                "inesperada de rótulos disponíveis. "
                f"Esperado: {expected_valid:,}; "
                f"obtido: {actual_valid:,}."
            )

        summary[f"h{horizon}"] = {
            "linhas_com_target": actual_valid,
            "linhas_sem_target": int(len(dataframe) - actual_valid),
        }

    return summary


def select_output_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Seleciona identificação, features oficiais e targets futuros."""
    columns = [
        *IDENTIFICATION_COLUMNS,
        *OFFICIAL_FEATURE_COLUMNS,
        *HORIZON_COLUMNS,
    ]

    unique_columns = list(dict.fromkeys(columns))

    return dataframe[unique_columns].copy()


def main() -> None:
    """Gera os datasets finais de desenvolvimento e teste."""
    print("=" * 88)
    print("GERAÇÃO DO DATASET DE MODELAGEM — DENGUE ALERT")
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
        "incidencia_100mil",
        "modelavel_era5_land",
        "temperatura_media_c",
        "umidade_relativa_media_pct",
        "precipitacao_total_mm",
        "latitude_sede",
        "longitude_sede",
    ]

    print()
    print("Carregando painel mestre...")

    dataframe = pd.read_parquet(
        MASTER_PANEL,
        columns=columns,
    )

    if len(dataframe) != EXPECTED_MASTER_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas "
            "no painel mestre. "
            f"Esperado: {EXPECTED_MASTER_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    print(f"Linhas do painel mestre          : {len(dataframe):,}")

    print()
    print("Reconstruindo o alvo epidemiológico congelado...")

    target_panel = build_epidemiological_target(
        dataframe,
        modelable_only=True,
    )

    if len(target_panel) != EXPECTED_MODELABLE_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas "
            "modeláveis. "
            f"Esperado: {EXPECTED_MODELABLE_ROWS:,}; "
            f"obtido: {len(target_panel):,}."
        )

    print(f"Linhas modeláveis                : {len(target_panel):,}")

    print()
    print("Construindo features de desenvolvimento...")

    development = build_partition_features(
        target_panel,
        start_year=DEVELOPMENT_START_YEAR,
        end_year=DEVELOPMENT_END_YEAR,
    )

    print("Construindo features de teste final...")

    final_test = build_partition_features(
        target_panel,
        start_year=FINAL_TEST_YEAR,
        end_year=FINAL_TEST_YEAR,
    )

    validate_unique_keys(
        development,
        "Desenvolvimento",
    )

    validate_unique_keys(
        final_test,
        "Teste final",
    )

    validate_feature_columns(development)

    validate_feature_columns(final_test)

    print()
    print("Auditando features de desenvolvimento...")

    validate_development(development)

    print("Auditando estrutura de 2025 sem inspecionar prevalências...")

    validate_final_test(final_test)

    development_horizons = validate_horizon_structure(
        development,
        expected_municipalities=(EXPECTED_DEVELOPMENT_MUNICIPALITIES),
        name="Desenvolvimento",
    )

    final_test_horizons = validate_horizon_structure(
        final_test,
        expected_municipalities=(EXPECTED_TEST_ELIGIBLE_ROWS // 53),
        name="Teste final",
    )

    development = select_output_columns(development)

    final_test = select_output_columns(final_test)

    DEVELOPMENT_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    development.to_parquet(
        DEVELOPMENT_OUTPUT,
        index=False,
    )

    final_test.to_parquet(
        FINAL_TEST_OUTPUT,
        index=False,
    )

    incomplete_test_rows = count_rows_with_incomplete_features(final_test)

    if incomplete_test_rows != EXPECTED_TEST_INELIGIBLE_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas "
            "com features incompletas em 2025. "
            f"Esperado: "
            f"{EXPECTED_TEST_INELIGIBLE_ROWS:,}; "
            f"obtido: {incomplete_test_rows:,}."
        )

    duration = perf_counter() - start

    report = {
        "status": "APROVADO",
        "escopo": {
            "desenvolvimento": "2018-2024",
            "teste_final": "2025",
            "teste_final_prevalencia_inspecionada": False,
            "lag_maximo_semanas": MAXIMUM_FEATURE_LAG_WEEKS,
        },
        "conjuntos_features": {
            "epidemiologico": {
                "quantidade": len(EPIDEMIOLOGICAL_FEATURES),
                "colunas": list(EPIDEMIOLOGICAL_FEATURES),
            },
            "clima": {
                "quantidade": len(CLIMATE_FEATURES),
                "colunas": list(CLIMATE_FEATURES),
            },
            "epidemiologico_mais_clima": {
                "quantidade": len(EPIDEMIOLOGICAL_CLIMATE_FEATURES),
            },
            "espacial": {
                "quantidade": len(SPATIAL_FEATURES),
                "colunas": list(SPATIAL_FEATURES),
            },
            "total_com_espaco": {
                "quantidade": len(OFFICIAL_FEATURE_COLUMNS),
            },
        },
        "desenvolvimento": {
            "linhas": len(development),
            "municipios": int(development["codigo_ibge_7"].nunique()),
            "features_completas": True,
            "risco_atual_positivos": int(development[TARGET_COLUMN].sum()),
            "horizontes": development_horizons,
        },
        "teste_final": {
            "linhas": len(final_test),
            "municipios": int(final_test["codigo_ibge_7"].nunique()),
            "linhas_elegiveis": int(final_test[TARGET_COLUMN].notna().sum()),
            "linhas_inelegiveis": int(final_test[TARGET_COLUMN].isna().sum()),
            "linhas_features_incompletas": incomplete_test_rows,
            "codigo_inelegivel": NEW_MUNICIPALITY_CODE,
            "prevalencia_ocultada": True,
            "horizontes": final_test_horizons,
        },
        "arquivos": {
            "desenvolvimento": str(DEVELOPMENT_OUTPUT),
            "teste_final": str(FINAL_TEST_OUTPUT),
        },
        "tempo_execucao_segundos": duration,
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
    print("=" * 88)
    print("DESENVOLVIMENTO")
    print("=" * 88)
    print(f"Linhas                           : {len(development):,}")
    print(
        f"Municípios                       : {development['codigo_ibge_7'].nunique():,}"
    )
    print(f"Features epidemiológicas         : {len(EPIDEMIOLOGICAL_FEATURES)}")
    print(f"Features climáticas              : {len(CLIMATE_FEATURES)}")
    print(f"Features epi + clima             : {len(EPIDEMIOLOGICAL_CLIMATE_FEATURES)}")
    print(f"Features espaciais opcionais     : {len(SPATIAL_FEATURES)}")
    print(f"Features totais com espaço       : {len(OFFICIAL_FEATURE_COLUMNS)}")
    print("Features ausentes                : 0")
    print(
        f"Risco atual positivo             : {int(development[TARGET_COLUMN].sum()):,}"
    )

    print()
    print("=" * 88)
    print("TESTE FINAL")
    print("=" * 88)
    print(f"Linhas                           : {len(final_test):,}")
    print(
        f"Municípios                       : {final_test['codigo_ibge_7'].nunique():,}"
    )
    print(
        "Linhas elegíveis                 : "
        f"{final_test[TARGET_COLUMN].notna().sum():,}"
    )
    print(
        f"Linhas inelegíveis               : {final_test[TARGET_COLUMN].isna().sum():,}"
    )
    print(f"Linhas com features incompletas  : {incomplete_test_rows:,}")
    print("Prevalência de 2025              : NÃO INSPECIONADA")

    print()
    print(f"Dataset desenvolvimento          : {DEVELOPMENT_OUTPUT}")
    print(f"Dataset teste final              : {FINAL_TEST_OUTPUT}")
    print(f"Relatório                        : {AUDIT_OUTPUT}")
    print(f"Tempo de execução                : {duration:.2f} s")
    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
