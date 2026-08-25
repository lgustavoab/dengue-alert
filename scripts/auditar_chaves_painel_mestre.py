"""Audita as chaves necessárias para a construção do painel mestre."""

import json

import pandas as pd

from dengue_alert.config.paths import (
    CLIMATE_COMBINATIONS,
    CLIMATE_EXCLUSIONS,
    DENGUE_WEEKLY_POPULATION,
    ERA5_WEEKLY_COMBINATIONS,
    MUNICIPALITY_CLIMATE_COMBINATION_MAP,
    REPORTS_DIR,
)


def normalizar_codigo_ibge(serie: pd.Series) -> pd.Series:
    """Normaliza código IBGE municipal como texto de 7 dígitos."""
    return serie.astype("string").str.strip().str.zfill(7)


def main() -> None:
    print("=" * 88)
    print("AUDITORIA DAS CHAVES — PAINEL MESTRE")
    print("=" * 88)

    epidemiologia = pd.read_parquet(
        DENGUE_WEEKLY_POPULATION,
        columns=[
            "codigo_ibge_7",
            "ano_epidemiologico",
            "semana_epidemiologica",
            "data_inicio_semana",
            "data_fim_semana",
        ],
    )

    mapeamento = pd.read_csv(
        MUNICIPALITY_CLIMATE_COMBINATION_MAP,
        dtype={"codigo_ibge_7": "string"},
        usecols=["codigo_ibge_7", "combo_id"],
    )

    clima = pd.read_parquet(
        ERA5_WEEKLY_COMBINATIONS,
        columns=[
            "combo_id",
            "ano_epidemiologico",
            "semana_epidemiologica",
            "data_inicio_semana",
            "data_fim_semana",
        ],
    )

    combinacoes = pd.read_csv(
        CLIMATE_COMBINATIONS,
        usecols=["combo_id"],
    )

    exclusoes = pd.read_csv(
        CLIMATE_EXCLUSIONS,
        dtype={"codigo_ibge_7": "string"},
        usecols=["codigo_ibge_7", "nome_unidade"],
    )

    epidemiologia["codigo_ibge_7"] = normalizar_codigo_ibge(
        epidemiologia["codigo_ibge_7"]
    )
    mapeamento["codigo_ibge_7"] = normalizar_codigo_ibge(mapeamento["codigo_ibge_7"])
    exclusoes["codigo_ibge_7"] = normalizar_codigo_ibge(exclusoes["codigo_ibge_7"])

    chave_epidemiologica = [
        "codigo_ibge_7",
        "ano_epidemiologico",
        "semana_epidemiologica",
    ]

    chave_climatica = [
        "combo_id",
        "ano_epidemiologico",
        "semana_epidemiologica",
    ]

    duplicadas_epidemiologia = int(epidemiologia.duplicated(chave_epidemiologica).sum())

    duplicados_mapeamento = int(mapeamento.duplicated(["codigo_ibge_7"]).sum())

    duplicadas_clima = int(clima.duplicated(chave_climatica).sum())

    codigos_epi = set(epidemiologia["codigo_ibge_7"].dropna())
    codigos_mapeados = set(mapeamento["codigo_ibge_7"].dropna())
    codigos_excluidos = set(exclusoes["codigo_ibge_7"].dropna())

    codigos_epi_sem_mapeamento = sorted(codigos_epi - codigos_mapeados)

    codigos_mapeamento_sem_epi = sorted(codigos_mapeados - codigos_epi)

    combos_mapeamento = set(mapeamento["combo_id"])
    combos_definidos = set(combinacoes["combo_id"])
    combos_clima = set(clima["combo_id"])

    combos_sem_definicao = sorted(combos_mapeamento - combos_definidos)

    combos_sem_serie_climatica = sorted(combos_mapeamento - combos_clima)

    contagem_por_municipio = (
        epidemiologia.groupby("codigo_ibge_7", observed=True).size().sort_values()
    )

    municipios_sem_522_semanas = {
        codigo: int(qtd) for codigo, qtd in contagem_por_municipio.items() if qtd != 522
    }

    painel = epidemiologia.merge(
        mapeamento,
        on="codigo_ibge_7",
        how="left",
        validate="many_to_one",
    )

    linhas_sem_combo = int(painel["combo_id"].isna().sum())

    codigos_sem_combo = sorted(
        painel.loc[
            painel["combo_id"].isna(),
            "codigo_ibge_7",
        ].unique()
    )

    clima_validacao = clima.copy()
    clima_validacao["clima_presente"] = True

    painel = painel.merge(
        clima_validacao,
        on=[
            "combo_id",
            "ano_epidemiologico",
            "semana_epidemiologica",
        ],
        how="left",
        validate="many_to_one",
        suffixes=("_epi", "_era5"),
    )

    linhas_sem_clima = int(painel["clima_presente"].isna().sum())

    linhas_com_clima = int(painel["clima_presente"].notna().sum())

    com_clima = painel["clima_presente"].notna()

    divergencias_inicio = int(
        (
            painel.loc[com_clima, "data_inicio_semana_epi"]
            != painel.loc[com_clima, "data_inicio_semana_era5"]
        ).sum()
    )

    divergencias_fim = int(
        (
            painel.loc[com_clima, "data_fim_semana_epi"]
            != painel.loc[com_clima, "data_fim_semana_era5"]
        ).sum()
    )

    criterios = {
        "sem_duplicidade_epidemiologica": duplicadas_epidemiologia == 0,
        "sem_duplicidade_mapeamento": duplicados_mapeamento == 0,
        "sem_duplicidade_climatica": duplicadas_clima == 0,
        "codigos_nao_mapeados_sao_exclusoes": set(codigos_epi_sem_mapeamento)
        == codigos_excluidos,
        "nenhum_codigo_mapeado_ausente_epidemiologia": len(codigos_mapeamento_sem_epi)
        == 0,
        "todos_combos_definidos": len(combos_sem_definicao) == 0,
        "todos_combos_possuem_clima": len(combos_sem_serie_climatica) == 0,
        "sem_divergencia_data_inicio": divergencias_inicio == 0,
        "sem_divergencia_data_fim": divergencias_fim == 0,
    }

    status = "APROVADO" if all(criterios.values()) else "REPROVADO"

    resumo = {
        "status": status,
        "epidemiologia": {
            "linhas": len(epidemiologia),
            "municipios": int(epidemiologia["codigo_ibge_7"].nunique()),
            "chaves_duplicadas": duplicadas_epidemiologia,
        },
        "mapeamento_climatico": {
            "unidades": len(mapeamento),
            "chaves_duplicadas": duplicados_mapeamento,
        },
        "clima": {
            "linhas": len(clima),
            "combos": int(clima["combo_id"].nunique()),
            "chaves_duplicadas": duplicadas_clima,
        },
        "cobertura": {
            "linhas_com_clima": linhas_com_clima,
            "linhas_sem_clima": linhas_sem_clima,
            "linhas_sem_combo": linhas_sem_combo,
            "codigos_sem_combo": codigos_sem_combo,
            "codigos_excluidos": sorted(codigos_excluidos),
        },
        "temporalidade": {
            "municipios_sem_522_semanas": municipios_sem_522_semanas,
            "divergencias_data_inicio": divergencias_inicio,
            "divergencias_data_fim": divergencias_fim,
        },
        "integridade_combos": {
            "combos_sem_definicao": combos_sem_definicao,
            "combos_sem_serie_climatica": combos_sem_serie_climatica,
        },
        "criterios": criterios,
    }

    destino = REPORTS_DIR / "audits" / "auditoria_chaves_painel_mestre.json"
    destino.parent.mkdir(parents=True, exist_ok=True)

    with destino.open("w", encoding="utf-8") as arquivo:
        json.dump(
            resumo,
            arquivo,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(f"Status                         : {status}")
    print(f"Linhas epidemiológicas        : {len(epidemiologia):,}")
    print(
        f"Municípios epidemiológicos    : {epidemiologia['codigo_ibge_7'].nunique():,}"
    )
    print(f"Duplicidades epidemiológicas  : {duplicadas_epidemiologia:,}")
    print(f"Unidades mapeadas para clima  : {len(mapeamento):,}")
    print(f"Combinações climáticas        : {clima['combo_id'].nunique():,}")
    print(f"Duplicidades climáticas       : {duplicadas_clima:,}")
    print(f"Linhas com clima              : {linhas_com_clima:,}")
    print(f"Linhas sem clima              : {linhas_sem_clima:,}")
    print(f"Códigos sem combo             : {codigos_sem_combo}")
    print(f"Exclusões climáticas          : {sorted(codigos_excluidos)}")
    print(f"Municípios != 522 semanas     : {municipios_sem_522_semanas}")
    print(f"Divergências início semana    : {divergencias_inicio:,}")
    print(f"Divergências fim semana       : {divergencias_fim:,}")
    print()
    print(f"Relatório: {destino}")


if __name__ == "__main__":
    main()
