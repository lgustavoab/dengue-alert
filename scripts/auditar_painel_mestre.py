"""Audita o painel municipal semanal integrado após sua geração."""

import json

import pandas as pd

from dengue_alert.config.paths import MASTER_PANEL, REPORTS_DIR

EXPECTED_ROWS = 2_907_593
EXPECTED_MUNICIPALITIES = 5_571
EXPECTED_CASES = 16_294_913
EXPECTED_ROWS_WITH_CLIMATE = 2_907_071
EXPECTED_ROWS_WITHOUT_CLIMATE = 522

FERNANDO_DE_NORONHA = "2605459"
BOA_ESPERANCA_DO_NORTE = "5101837"


def normalize_ibge_code(series: pd.Series) -> pd.Series:
    """Normaliza código IBGE como texto de sete dígitos."""
    return series.astype("string").str.strip().str.zfill(7)


def main() -> None:
    """Executa as verificações de aceite do painel mestre."""
    print("=" * 88)
    print("AUDITORIA DO PAINEL MESTRE — DENGUE ALERT")
    print("=" * 88)

    columns = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "semana_epidemiologica",
        "casos_provaveis",
        "populacao",
        "incidencia_100mil",
        "combo_id",
        "modelavel_era5_land",
        "clima_disponivel",
        "horas_esperadas",
        "temperatura_media_c",
        "temperatura_min_c",
        "temperatura_max_c",
        "umidade_relativa_media_pct",
        "precipitacao_total_mm",
    ]

    panel = pd.read_parquet(
        MASTER_PANEL,
        columns=columns,
    )

    panel["codigo_ibge_7"] = normalize_ibge_code(panel["codigo_ibge_7"])

    key = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "semana_epidemiologica",
    ]

    total_rows = len(panel)
    municipalities = panel["codigo_ibge_7"].nunique()
    duplicate_keys = int(panel.duplicated(key).sum())
    total_cases = int(panel["casos_provaveis"].sum())

    missing_population = int(panel["populacao"].isna().sum())
    invalid_population = int((panel["populacao"] <= 0).sum())

    missing_modelable_flag = int(panel["modelavel_era5_land"].isna().sum())
    missing_climate_flag = int(panel["clima_disponivel"].isna().sum())

    rows_with_climate = int(panel["clima_disponivel"].sum())
    rows_without_climate = int((~panel["clima_disponivel"]).sum())

    codes_without_climate = sorted(
        panel.loc[
            ~panel["clima_disponivel"],
            "codigo_ibge_7",
        ].unique()
    )

    modelable_without_climate = int(
        (panel["modelavel_era5_land"] & ~panel["clima_disponivel"]).sum()
    )

    non_modelable_with_climate = int(
        (~panel["modelavel_era5_land"] & panel["clima_disponivel"]).sum()
    )

    combo_missing_modelable = int(
        (panel["modelavel_era5_land"] & panel["combo_id"].isna()).sum()
    )

    climate_mask = panel["clima_disponivel"]

    invalid_rh = int(
        (
            climate_mask
            & ~panel["umidade_relativa_media_pct"].between(
                0,
                100,
                inclusive="both",
            )
        ).sum()
    )

    negative_precipitation = int(
        (climate_mask & (panel["precipitacao_total_mm"] < 0)).sum()
    )

    min_above_mean = int(
        (
            climate_mask & (panel["temperatura_min_c"] > panel["temperatura_media_c"])
        ).sum()
    )

    mean_above_max = int(
        (
            climate_mask & (panel["temperatura_media_c"] > panel["temperatura_max_c"])
        ).sum()
    )

    invalid_expected_hours = int(
        (climate_mask & ~panel["horas_esperadas"].isin([167, 168, 169])).sum()
    )

    climate_variables = [
        "horas_esperadas",
        "temperatura_media_c",
        "temperatura_min_c",
        "temperatura_max_c",
        "umidade_relativa_media_pct",
        "precipitacao_total_mm",
    ]

    missing_climate_values = int(
        panel.loc[
            climate_mask,
            climate_variables,
        ]
        .isna()
        .any(axis=1)
        .sum()
    )

    noronha = panel.loc[panel["codigo_ibge_7"] == FERNANDO_DE_NORONHA]

    boa_esperanca = panel.loc[panel["codigo_ibge_7"] == BOA_ESPERANCA_DO_NORTE]

    noronha_rows = len(noronha)
    noronha_rows_without_climate = int((~noronha["clima_disponivel"]).sum())

    boa_esperanca_rows = len(boa_esperanca)
    boa_esperanca_years = sorted(
        int(year) for year in boa_esperanca["ano_epidemiologico"].unique()
    )

    criteria = {
        "quantidade_linhas": total_rows == EXPECTED_ROWS,
        "quantidade_municipios": municipalities == EXPECTED_MUNICIPALITIES,
        "sem_chaves_duplicadas": duplicate_keys == 0,
        "casos_preservados": total_cases == EXPECTED_CASES,
        "sem_populacao_ausente": missing_population == 0,
        "populacao_positiva": invalid_population == 0,
        "sem_flag_modelavel_ausente": missing_modelable_flag == 0,
        "sem_flag_clima_ausente": missing_climate_flag == 0,
        "quantidade_com_clima": rows_with_climate == EXPECTED_ROWS_WITH_CLIMATE,
        "quantidade_sem_clima": rows_without_climate == EXPECTED_ROWS_WITHOUT_CLIMATE,
        "somente_noronha_sem_clima": codes_without_climate == [FERNANDO_DE_NORONHA],
        "nenhum_modelavel_sem_clima": modelable_without_climate == 0,
        "nenhum_nao_modelavel_com_clima": non_modelable_with_climate == 0,
        "nenhum_modelavel_sem_combo": combo_missing_modelable == 0,
        "sem_umidade_invalida": invalid_rh == 0,
        "sem_precipitacao_negativa": negative_precipitation == 0,
        "temperatura_minima_consistente": min_above_mean == 0,
        "temperatura_maxima_consistente": mean_above_max == 0,
        "horas_semanais_validas": invalid_expected_hours == 0,
        "clima_sem_valores_ausentes": missing_climate_values == 0,
        "noronha_tem_522_semanas": noronha_rows == 522,
        "noronha_totalmente_sem_clima": noronha_rows_without_climate == 522,
        "boa_esperanca_tem_53_semanas": boa_esperanca_rows == 53,
        "boa_esperanca_somente_2025": boa_esperanca_years == [2025],
    }

    status = "APROVADO" if all(criteria.values()) else "REPROVADO"

    report = {
        "status": status,
        "painel": {
            "linhas": total_rows,
            "municipios": int(municipalities),
            "casos_provaveis": total_cases,
            "chaves_duplicadas": duplicate_keys,
        },
        "populacao": {
            "ausentes": missing_population,
            "nao_positivas": invalid_population,
        },
        "clima": {
            "linhas_com_clima": rows_with_climate,
            "linhas_sem_clima": rows_without_climate,
            "codigos_sem_clima": codes_without_climate,
            "modelaveis_sem_clima": modelable_without_climate,
            "nao_modelaveis_com_clima": non_modelable_with_climate,
            "modelaveis_sem_combo": combo_missing_modelable,
            "umidade_invalida": invalid_rh,
            "precipitacao_negativa": negative_precipitation,
            "temperatura_minima_acima_media": min_above_mean,
            "temperatura_media_acima_maxima": mean_above_max,
            "horas_semanais_invalidas": invalid_expected_hours,
            "linhas_climaticas_com_nulos": missing_climate_values,
        },
        "territorio": {
            "fernando_de_noronha": {
                "codigo_ibge_7": FERNANDO_DE_NORONHA,
                "linhas": noronha_rows,
                "linhas_sem_clima": noronha_rows_without_climate,
            },
            "boa_esperanca_do_norte": {
                "codigo_ibge_7": BOA_ESPERANCA_DO_NORTE,
                "linhas": boa_esperanca_rows,
                "anos": boa_esperanca_years,
            },
        },
        "criterios": criteria,
    }

    destination = REPORTS_DIR / "audits" / "auditoria_painel_mestre.json"

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
    print(f"Status                         : {status}")
    print(f"Linhas                         : {total_rows:,}")
    print(f"Municípios                     : {municipalities:,}")
    print(f"Chaves duplicadas              : {duplicate_keys:,}")
    print(f"Casos prováveis                : {total_cases:,}")
    print(f"População ausente              : {missing_population:,}")
    print(f"Linhas com clima               : {rows_with_climate:,}")
    print(f"Linhas sem clima               : {rows_without_climate:,}")
    print(f"Códigos sem clima              : {codes_without_climate}")
    print(f"Modeláveis sem clima           : {modelable_without_climate:,}")
    print(f"RH inválida                    : {invalid_rh:,}")
    print(f"Precipitação negativa          : {negative_precipitation:,}")
    print(f"Temperatura mín > média        : {min_above_mean:,}")
    print(f"Temperatura média > máx        : {mean_above_max:,}")
    print(f"Horas semanais inválidas       : {invalid_expected_hours:,}")

    print()
    print(
        "Fernando de Noronha           : "
        f"{noronha_rows:,} linhas / "
        f"{noronha_rows_without_climate:,} sem clima"
    )
    print(
        "Boa Esperança do Norte        : "
        f"{boa_esperanca_rows:,} linhas / anos {boa_esperanca_years}"
    )

    print()
    print(f"Relatório: {destination}")

    if status != "APROVADO":
        failed = [name for name, approved in criteria.items() if not approved]

        print()
        print("Critérios reprovados:")

        for criterion in failed:
            print(f"- {criterion}")

        raise SystemExit(1)


if __name__ == "__main__":
    main()
