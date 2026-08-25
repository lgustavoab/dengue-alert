"""Auditoria independente das features reais de modelagem do Dengue Alert."""

import json
from time import perf_counter

import numpy as np
import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.features.engineering import (
    CLIMATE_FEATURES,
    EPIDEMIOLOGICAL_CLIMATE_SPATIAL_FEATURES,
    EPIDEMIOLOGICAL_FEATURES,
)

DEVELOPMENT_DATASET = MASTER_PANEL.parent / "dataset_modelagem_2018_2024.parquet"

FINAL_TEST_DATASET = MASTER_PANEL.parent / "dataset_teste_final_2025.parquet"

AUDIT_OUTPUT = REPORTS_DIR / "audits" / "auditoria_independente_features_modelagem.json"

EXPECTED_DEVELOPMENT_ROWS = 2_032_685
EXPECTED_DEVELOPMENT_MUNICIPALITIES = 5_569

EXPECTED_TEST_ROWS = 295_210
EXPECTED_TEST_MUNICIPALITIES = 5_570
EXPECTED_TEST_ELIGIBLE_ROWS = 295_157

NEW_MUNICIPALITY_CODE = "5101837"

FEATURE_COLUMNS = tuple(EPIDEMIOLOGICAL_CLIMATE_SPATIAL_FEATURES)

NUMERIC_FEATURE_COLUMNS = tuple(
    column for column in FEATURE_COLUMNS if column != "risco_elevado"
)


def validate_dataset_structure(
    dataframe: pd.DataFrame,
    *,
    expected_rows: int,
    expected_municipalities: int,
    name: str,
) -> None:
    """Valida estrutura básica do dataset."""
    if len(dataframe) != expected_rows:
        raise ValueError(
            f"{name}: quantidade inesperada de linhas. "
            f"Esperado: {expected_rows:,}; "
            f"obtido: {len(dataframe):,}."
        )

    municipalities = int(dataframe["codigo_ibge_7"].nunique())

    if municipalities != expected_municipalities:
        raise ValueError(
            f"{name}: quantidade inesperada de municípios. "
            f"Esperado: {expected_municipalities:,}; "
            f"obtido: {municipalities:,}."
        )

    duplicated = int(
        dataframe.duplicated(
            [
                "codigo_ibge_7",
                "ano_epidemiologico",
                "semana_epidemiologica",
            ]
        ).sum()
    )

    if duplicated:
        raise ValueError(f"{name}: {duplicated:,} chaves duplicadas.")


def validate_numeric_features(
    dataframe: pd.DataFrame,
    *,
    mask: pd.Series,
    name: str,
) -> None:
    """Valida nulos e infinitos das features numéricas."""
    for column in NUMERIC_FEATURE_COLUMNS:
        values = dataframe.loc[
            mask,
            column,
        ]

        missing = int(values.isna().sum())

        if missing:
            raise ValueError(f"{name}: {column!r} possui {missing:,} valores ausentes.")

        array = values.to_numpy(
            dtype="float64",
            copy=False,
        )

        invalid = int((~np.isfinite(array)).sum())

        if invalid:
            raise ValueError(
                f"{name}: {column!r} possui {invalid:,} valores não finitos."
            )


def validate_development_ranges(
    dataframe: pd.DataFrame,
) -> dict:
    """Audita faixas físicas e matemáticas básicas no desenvolvimento."""
    validations = {}

    checks = {
        "incidencia_nao_negativa": (dataframe["incidencia_100mil"] >= 0),
        "incidencia_4s_nao_negativa": (dataframe["incidencia_4s_100mil"] >= 0),
        "temperatura_fisicamente_plausivel": (
            dataframe["temperatura_media_c_lag_0"].between(-20, 50)
        ),
        "umidade_entre_0_e_100": (
            dataframe["umidade_relativa_media_pct_lag_0"].between(0, 100)
        ),
        "precipitacao_nao_negativa": (dataframe["precipitacao_total_mm_lag_0"] >= 0),
        "precipitacao_2s_nao_negativa": (dataframe["precipitacao_acumulada_2s"] >= 0),
        "precipitacao_4s_nao_negativa": (dataframe["precipitacao_acumulada_4s"] >= 0),
        "precipitacao_8s_nao_negativa": (dataframe["precipitacao_acumulada_8s"] >= 0),
        "semana_sin_valida": (dataframe["semana_sin"].between(-1, 1)),
        "semana_cos_valida": (dataframe["semana_cos"].between(-1, 1)),
        "log_populacao_positivo": (dataframe["log_populacao"] > 0),
    }

    for name, mask in checks.items():
        invalid = int((~mask).sum())

        validations[name] = {
            "violacoes": invalid,
        }

        if invalid:
            raise ValueError(f"Validação {name!r}: {invalid:,} violações.")

    return validations


def summarize_development_features(
    dataframe: pd.DataFrame,
) -> dict:
    """Resume faixas das features sem utilizar o teste final."""
    summary = {}

    for column in NUMERIC_FEATURE_COLUMNS:
        values = dataframe[column]

        summary[column] = {
            "min": float(values.min()),
            "p01": float(values.quantile(0.01)),
            "mediana": float(values.median()),
            "p99": float(values.quantile(0.99)),
            "max": float(values.max()),
        }

    return summary


def validate_boundary_lag(
    *,
    master: pd.DataFrame,
    modeled: pd.DataFrame,
    previous_year: int,
    modeled_year: int,
    name: str,
) -> dict:
    """Confirma que lag 1 atravessa corretamente a fronteira anual."""
    previous = (
        master.loc[
            master["ano_epidemiologico"] == previous_year,
            [
                "codigo_ibge_7",
                "data_inicio_semana",
                "incidencia_100mil",
                "temperatura_media_c",
                "umidade_relativa_media_pct",
                "precipitacao_total_mm",
            ],
        ]
        .sort_values(
            [
                "codigo_ibge_7",
                "data_inicio_semana",
            ]
        )
        .groupby(
            "codigo_ibge_7",
            observed=True,
            as_index=False,
        )
        .tail(1)
        .rename(
            columns={
                "data_inicio_semana": "data_inicio_semana_anterior",
                "incidencia_100mil": "incidencia_100mil_anterior",
                "temperatura_media_c": "temperatura_media_c_anterior",
                "umidade_relativa_media_pct": ("umidade_relativa_media_pct_anterior"),
                "precipitacao_total_mm": "precipitacao_total_mm_anterior",
            }
        )
    )

    current = (
        modeled.loc[modeled["ano_epidemiologico"] == modeled_year]
        .sort_values(
            [
                "codigo_ibge_7",
                "data_inicio_semana",
            ]
        )
        .groupby(
            "codigo_ibge_7",
            observed=True,
            as_index=False,
        )
        .head(1)
    )

    comparison = current.merge(
        previous,
        on="codigo_ibge_7",
        how="inner",
        validate="one_to_one",
    )

    comparisons = {
        "incidencia_100mil_lag_1": "incidencia_100mil_anterior",
        "temperatura_media_c_lag_1": "temperatura_media_c_anterior",
        "umidade_relativa_media_pct_lag_1": "umidade_relativa_media_pct_anterior",
        "precipitacao_total_mm_lag_1": "precipitacao_total_mm_anterior",
    }

    result = {
        "municipios_comparados": len(comparison),
        "variaveis": {},
    }

    for feature, expected in comparisons.items():
        actual_values = comparison[feature].to_numpy(
            dtype="float64",
        )

        expected_values = comparison[expected].to_numpy(
            dtype="float64",
        )

        equal = np.isclose(
            actual_values,
            expected_values,
            rtol=1e-12,
            atol=1e-12,
            equal_nan=False,
        )

        mismatches = int((~equal).sum())

        result["variaveis"][feature] = {
            "divergencias": mismatches,
        }

        if mismatches:
            raise ValueError(
                f"{name}: {feature!r} possui "
                f"{mismatches:,} divergências "
                "na fronteira temporal."
            )

    return result


def main() -> None:
    """Executa a auditoria independente."""
    print("=" * 88)
    print("AUDITORIA INDEPENDENTE DAS FEATURES — DENGUE ALERT")
    print("=" * 88)

    start = perf_counter()

    print()
    print("Carregando datasets de modelagem...")

    development = pd.read_parquet(DEVELOPMENT_DATASET)

    final_test = pd.read_parquet(FINAL_TEST_DATASET)

    print(f"Desenvolvimento                  : {len(development):,} linhas")

    print(f"Teste final                      : {len(final_test):,} linhas")

    validate_dataset_structure(
        development,
        expected_rows=(EXPECTED_DEVELOPMENT_ROWS),
        expected_municipalities=(EXPECTED_DEVELOPMENT_MUNICIPALITIES),
        name="Desenvolvimento",
    )

    validate_dataset_structure(
        final_test,
        expected_rows=(EXPECTED_TEST_ROWS),
        expected_municipalities=(EXPECTED_TEST_MUNICIPALITIES),
        name="Teste final",
    )

    print()
    print("Validando completude das features...")

    development_mask = pd.Series(
        True,
        index=development.index,
    )

    validate_numeric_features(
        development,
        mask=development_mask,
        name="Desenvolvimento",
    )

    final_eligible = final_test["risco_elevado"].notna()

    if int(final_eligible.sum()) != EXPECTED_TEST_ELIGIBLE_ROWS:
        raise ValueError("Quantidade inesperada de linhas elegíveis no teste final.")

    validate_numeric_features(
        final_test,
        mask=final_eligible,
        name="Teste final elegível",
    )

    ineligible_codes = set(
        final_test.loc[
            ~final_eligible,
            "codigo_ibge_7",
        ].unique()
    )

    if ineligible_codes != {NEW_MUNICIPALITY_CODE}:
        raise ValueError(
            "As linhas inelegíveis de 2025 "
            "não pertencem exclusivamente "
            "a Boa Esperança do Norte."
        )

    print("Auditando faixas no desenvolvimento...")

    range_validations = validate_development_ranges(development)

    feature_summary = summarize_development_features(development)

    print()
    print("Carregando painel mestre para auditoria das fronteiras...")

    master_columns = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "data_inicio_semana",
        "incidencia_100mil",
        "temperatura_media_c",
        "umidade_relativa_media_pct",
        "precipitacao_total_mm",
        "modelavel_era5_land",
    ]

    master = pd.read_parquet(
        MASTER_PANEL,
        columns=master_columns,
    )

    master["data_inicio_semana"] = pd.to_datetime(master["data_inicio_semana"])

    master = master.loc[master["modelavel_era5_land"]].copy()

    print("Validando fronteira 2017 → 2018...")

    boundary_2018 = validate_boundary_lag(
        master=master,
        modeled=development,
        previous_year=2017,
        modeled_year=2018,
        name="Fronteira 2017→2018",
    )

    print("Validando fronteira 2024 → 2025...")

    boundary_2025 = validate_boundary_lag(
        master=master,
        modeled=final_test.loc[final_test["codigo_ibge_7"] != NEW_MUNICIPALITY_CODE],
        previous_year=2024,
        modeled_year=2025,
        name="Fronteira 2024→2025",
    )

    duration = perf_counter() - start

    report = {
        "status": "APROVADO",
        "desenvolvimento": {
            "linhas": len(development),
            "municipios": int(development["codigo_ibge_7"].nunique()),
            "features_epidemiologicas": len(EPIDEMIOLOGICAL_FEATURES),
            "features_climaticas": len(CLIMATE_FEATURES),
            "features_totais": len(FEATURE_COLUMNS),
            "faixas": range_validations,
            "resumo_features": feature_summary,
        },
        "teste_final": {
            "linhas": len(final_test),
            "municipios": int(final_test["codigo_ibge_7"].nunique()),
            "linhas_elegiveis": int(final_eligible.sum()),
            "prevalencia_inspecionada": False,
            "codigo_inelegivel": NEW_MUNICIPALITY_CODE,
        },
        "fronteiras": {
            "2017_2018": boundary_2018,
            "2024_2025": boundary_2025,
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
    print("RESULTADO")
    print("=" * 88)

    print("Desenvolvimento sem nulos/inf    : OK")

    print("Teste elegível sem nulos/inf     : OK")

    print("Faixas físicas/matemáticas       : OK")

    print(
        "Fronteira 2017 → 2018            : "
        f"{boundary_2018['municipios_comparados']:,} "
        "municípios — OK"
    )

    print(
        "Fronteira 2024 → 2025            : "
        f"{boundary_2025['municipios_comparados']:,} "
        "municípios — OK"
    )

    print("Prevalência de 2025              : NÃO INSPECIONADA")

    print(f"Relatório                        : {AUDIT_OUTPUT}")

    print(f"Tempo de execução                : {duration:.2f} s")

    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
