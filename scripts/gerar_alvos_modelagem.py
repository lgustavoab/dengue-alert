"""Gera e audita os alvos definitivos para modelagem e teste final."""

import json
from time import perf_counter

import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR
from dengue_alert.features.targets import (
    HISTORICAL_COUNT_COLUMN,
    TARGET_COLUMN,
    THRESHOLD_COLUMN,
    build_epidemiological_target,
    build_horizon_targets,
)

DEVELOPMENT_START_YEAR = 2018
DEVELOPMENT_END_YEAR = 2024
FINAL_TEST_YEAR = 2025

HORIZONS = (1, 2, 3, 4)

EXPECTED_DEVELOPMENT_ROWS = 2_032_685
EXPECTED_DEVELOPMENT_MUNICIPALITIES = 5_569
EXPECTED_DEVELOPMENT_POSITIVES = 377_275

EXPECTED_TEST_ROWS = 295_210
EXPECTED_TEST_ELIGIBLE_ROWS = 295_157
EXPECTED_TEST_INELIGIBLE_ROWS = 53

NEW_MUNICIPALITY_CODE = "5101837"

DEVELOPMENT_OUTPUT = MASTER_PANEL.parent / "alvos_modelagem_2018_2024.parquet"

FINAL_TEST_OUTPUT = MASTER_PANEL.parent / "alvos_teste_final_2025.parquet"


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


def summarize_horizons(
    dataframe: pd.DataFrame,
    *,
    include_positives: bool,
) -> dict:
    """Resume disponibilidade dos horizontes preditivos."""
    summary = {}

    for horizon in HORIZONS:
        column = f"target_h{horizon}"

        valid = dataframe[column].notna()

        horizon_summary = {
            "linhas_com_target": int(valid.sum()),
            "linhas_sem_target": int((~valid).sum()),
        }

        if include_positives:
            positives = int(
                dataframe.loc[
                    valid,
                    column,
                ].sum()
            )

            horizon_summary["positivos"] = positives
            horizon_summary["prevalencia"] = float(
                dataframe.loc[
                    valid,
                    column,
                ].mean()
            )

        summary[f"h{horizon}"] = horizon_summary

    return summary


def validate_development(
    dataframe: pd.DataFrame,
) -> None:
    """Valida estruturalmente a partição de desenvolvimento."""
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
        missing = int(dataframe[TARGET_COLUMN].isna().sum())

        raise ValueError(
            f"O desenvolvimento possui {missing:,} alvos contemporâneos ausentes."
        )

    positives = int(dataframe[TARGET_COLUMN].sum())

    if positives != EXPECTED_DEVELOPMENT_POSITIVES:
        raise ValueError(
            "A implementação definitiva não reproduziu "
            "o P90 sazonal previamente congelado. "
            f"Esperado: "
            f"{EXPECTED_DEVELOPMENT_POSITIVES:,}; "
            f"obtido: {positives:,}."
        )

    total_weeks = len(dataframe) // EXPECTED_DEVELOPMENT_MUNICIPALITIES

    for horizon in HORIZONS:
        column = f"target_h{horizon}"

        expected_valid = EXPECTED_DEVELOPMENT_MUNICIPALITIES * (total_weeks - horizon)

        actual_valid = int(dataframe[column].notna().sum())

        if actual_valid != expected_valid:
            raise ValueError(
                f"{column}: quantidade inesperada "
                "de rótulos disponíveis. "
                f"Esperado: {expected_valid:,}; "
                f"obtido: {actual_valid:,}."
            )


def validate_final_test(
    dataframe: pd.DataFrame,
) -> None:
    """Valida a estrutura do teste final sem inspecionar seus positivos."""
    if len(dataframe) != EXPECTED_TEST_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas em 2025. "
            f"Esperado: {EXPECTED_TEST_ROWS:,}; "
            f"obtido: {len(dataframe):,}."
        )

    eligible = dataframe[TARGET_COLUMN].notna()

    eligible_rows = int(eligible.sum())
    ineligible_rows = int((~eligible).sum())

    if eligible_rows != EXPECTED_TEST_ELIGIBLE_ROWS:
        raise ValueError(
            "Quantidade inesperada de alvos elegíveis "
            "no teste final. "
            f"Esperado: {EXPECTED_TEST_ELIGIBLE_ROWS:,}; "
            f"obtido: {eligible_rows:,}."
        )

    if ineligible_rows != EXPECTED_TEST_INELIGIBLE_ROWS:
        raise ValueError(
            "Quantidade inesperada de linhas "
            "inelegíveis no teste final. "
            f"Esperado: {EXPECTED_TEST_INELIGIBLE_ROWS:,}; "
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
            "As linhas sem alvo em 2025 não pertencem "
            "exclusivamente a Boa Esperança do Norte. "
            f"Códigos encontrados: {ineligible_codes}."
        )

    weeks_in_test = int(dataframe["semana_epidemiologica"].nunique())

    eligible_municipalities = int(
        dataframe.loc[
            eligible,
            "codigo_ibge_7",
        ].nunique()
    )

    for horizon in HORIZONS:
        column = f"target_h{horizon}"

        expected_valid = eligible_municipalities * (weeks_in_test - horizon)

        actual_valid = int(dataframe[column].notna().sum())

        if actual_valid != expected_valid:
            raise ValueError(
                f"{column}: quantidade inesperada "
                "de rótulos disponíveis em 2025. "
                f"Esperado: {expected_valid:,}; "
                f"obtido: {actual_valid:,}."
            )


def select_output_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Seleciona somente colunas necessárias à tabela oficial de alvos."""
    columns = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "semana_epidemiologica",
        "data_inicio_semana",
        "casos_4s",
        "incidencia_4s_100mil",
        THRESHOLD_COLUMN,
        HISTORICAL_COUNT_COLUMN,
        TARGET_COLUMN,
        "target_h1",
        "target_h2",
        "target_h3",
        "target_h4",
    ]

    return dataframe[columns].copy()


def main() -> None:
    """Gera as tabelas oficiais de alvos."""
    print("=" * 88)
    print("GERAÇÃO DOS ALVOS DE MODELAGEM — DENGUE ALERT")
    print("=" * 88)

    start = perf_counter()

    columns = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "semana_epidemiologica",
        "data_inicio_semana",
        "casos_provaveis",
        "populacao",
        "modelavel_era5_land",
    ]

    print()
    print("Carregando painel mestre...")

    dataframe = pd.read_parquet(
        MASTER_PANEL,
        columns=columns,
    )

    print(f"Linhas carregadas                : {len(dataframe):,}")

    print()
    print("Construindo risco epidemiológico P90 sazonal...")

    target_panel = build_epidemiological_target(
        dataframe,
        modelable_only=True,
    )

    print()
    print("Construindo horizontes de desenvolvimento...")

    development = build_horizon_targets(
        target_panel,
        start_year=DEVELOPMENT_START_YEAR,
        end_year=DEVELOPMENT_END_YEAR,
        horizons=HORIZONS,
    )

    print("Construindo horizontes do teste final...")

    final_test = build_horizon_targets(
        target_panel,
        start_year=FINAL_TEST_YEAR,
        end_year=FINAL_TEST_YEAR,
        horizons=HORIZONS,
    )

    validate_unique_keys(
        development,
        "Desenvolvimento",
    )

    validate_unique_keys(
        final_test,
        "Teste final",
    )

    print()
    print("Validando desenvolvimento...")

    validate_development(development)

    print("Validando estrutura do teste final sem inspecionar prevalência...")

    validate_final_test(final_test)

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

    development_horizons = summarize_horizons(
        development,
        include_positives=True,
    )

    final_test_horizons = summarize_horizons(
        final_test,
        include_positives=False,
    )

    duration = perf_counter() - start

    report = {
        "status": "APROVADO",
        "definicao": {
            "alvo_contemporaneo": TARGET_COLUMN,
            "horizontes": list(HORIZONS),
            "desenvolvimento": "2018-2024",
            "teste_final": "2025",
            "teste_final_prevalencia_inspecionada": False,
        },
        "desenvolvimento": {
            "linhas": len(development),
            "municipios": int(development["codigo_ibge_7"].nunique()),
            "positivos_risco_atual": int(development[TARGET_COLUMN].sum()),
            "prevalencia_risco_atual": float(development[TARGET_COLUMN].mean()),
            "horizontes": development_horizons,
        },
        "teste_final": {
            "linhas": len(final_test),
            "municipios_totais": int(final_test["codigo_ibge_7"].nunique()),
            "linhas_elegiveis": int(final_test[TARGET_COLUMN].notna().sum()),
            "linhas_inelegiveis": int(final_test[TARGET_COLUMN].isna().sum()),
            "codigo_inelegivel": (NEW_MUNICIPALITY_CODE),
            "prevalencia_ocultada": True,
            "horizontes": final_test_horizons,
        },
        "arquivos": {
            "desenvolvimento": str(DEVELOPMENT_OUTPUT),
            "teste_final": str(FINAL_TEST_OUTPUT),
        },
        "tempo_execucao_segundos": duration,
    }

    report_path = REPORTS_DIR / "audits" / "auditoria_alvos_modelagem.json"

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with report_path.open(
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
    print("Período                          : 2018–2024")
    print(f"Linhas                           : {len(development):,}")
    print(
        f"Municípios                       : {development['codigo_ibge_7'].nunique():,}"
    )
    print(
        f"Risco atual positivo             : {int(development[TARGET_COLUMN].sum()):,}"
    )
    print(f"Prevalência                      : {development[TARGET_COLUMN].mean():.2%}")

    for horizon in HORIZONS:
        summary = development_horizons[f"h{horizon}"]

        print(
            f"H{horizon} disponível                   : "
            f"{summary['linhas_com_target']:,}"
        )
        print(f"H{horizon} positivos                    : {summary['positivos']:,}")
        print(f"H{horizon} prevalência                  : {summary['prevalencia']:.2%}")

    print()
    print("=" * 88)
    print("TESTE FINAL")
    print("=" * 88)
    print("Período                          : 2025")
    print(f"Linhas                           : {len(final_test):,}")
    print(
        f"Municípios totais                : {final_test['codigo_ibge_7'].nunique():,}"
    )
    print(
        "Linhas com alvo atual disponível : "
        f"{final_test[TARGET_COLUMN].notna().sum():,}"
    )
    print(
        f"Linhas sem alvo atual            : {final_test[TARGET_COLUMN].isna().sum():,}"
    )
    print("Prevalência de 2025              : NÃO INSPECIONADA")

    for horizon in HORIZONS:
        summary = final_test_horizons[f"h{horizon}"]

        print(
            f"H{horizon} disponível                   : "
            f"{summary['linhas_com_target']:,}"
        )

    print()
    print(f"Arquivo desenvolvimento          : {DEVELOPMENT_OUTPUT}")
    print(f"Arquivo teste final              : {FINAL_TEST_OUTPUT}")
    print(f"Relatório                        : {report_path}")
    print(f"Tempo de execução                : {duration:.2f} s")
    print()
    print("STATUS: APROVADO")


if __name__ == "__main__":
    main()
