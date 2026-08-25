"""Testes da construção do painel municipal semanal."""

import pandas as pd
import pytest

from dengue_alert.dataset.master import build_master_panel


def make_epidemiology() -> pd.DataFrame:
    """Cria uma base epidemiológica mínima para os testes."""
    return pd.DataFrame(
        {
            "codigo_ibge_7": ["1000001", "2605459"],
            "ano_epidemiologico": [2025, 2025],
            "semana_epidemiologica": [1, 1],
            "casos_provaveis": [10, 2],
            "populacao": [100_000, 3_000],
        }
    )


def make_spatial_mapping() -> pd.DataFrame:
    """Cria mapeamento espacial com uma unidade modelável e uma excluída."""
    return pd.DataFrame(
        {
            "codigo_ibge_7": ["1000001", "2605459"],
            "timezone_iana": [
                "America/Sao_Paulo",
                "America/Noronha",
            ],
            "latitude_sede": [-20.0, -3.85],
            "longitude_sede": [-50.0, -32.42],
            "latitude_grid_era5_final": [-20.0, pd.NA],
            "longitude_grid_era5_final": [-50.0, pd.NA],
            "distancia_sede_grid_final_km": [1.0, pd.NA],
            "metodo_selecao_grid": [
                "nearest_valid",
                "excluded",
            ],
            "modelavel_era5_land": [True, False],
            "motivo_exclusao": [
                pd.NA,
                "Sem célula ERA5-Land válida dentro do critério adotado.",
            ],
        }
    )


def make_combination_mapping() -> pd.DataFrame:
    """Cria associação da unidade modelável ao combo climático."""
    return pd.DataFrame(
        {
            "codigo_ibge_7": ["1000001"],
            "combo_id": [1],
        }
    )


def make_climate() -> pd.DataFrame:
    """Cria uma observação climática semanal válida."""
    return pd.DataFrame(
        {
            "combo_id": [1],
            "ano_epidemiologico": [2025],
            "semana_epidemiologica": [1],
            "horas_esperadas": [168],
            "temperatura_media_c": [25.0],
            "temperatura_min_c": [20.0],
            "temperatura_max_c": [30.0],
            "ponto_orvalho_medio_c": [18.0],
            "umidade_relativa_media_pct": [70.0],
            "precipitacao_total_mm": [40.0],
        }
    )


def test_preserva_unidade_sem_clima() -> None:
    """Unidade não modelável deve permanecer no painel sem receber clima."""
    panel = build_master_panel(
        epidemiology=make_epidemiology(),
        spatial_mapping=make_spatial_mapping(),
        combination_mapping=make_combination_mapping(),
        climate=make_climate(),
    )

    modelable = panel.loc[panel["codigo_ibge_7"] == "1000001"].iloc[0]

    excluded = panel.loc[panel["codigo_ibge_7"] == "2605459"].iloc[0]

    assert modelable["modelavel_era5_land"]
    assert modelable["clima_disponivel"]
    assert modelable["temperatura_media_c"] == 25.0

    assert not excluded["modelavel_era5_land"]
    assert not excluded["clima_disponivel"]
    assert pd.isna(excluded["temperatura_media_c"])


def test_preserva_quantidade_de_linhas_epidemiologicas() -> None:
    """Os joins não podem criar nem eliminar linhas epidemiológicas."""
    epidemiology = make_epidemiology()

    panel = build_master_panel(
        epidemiology=epidemiology,
        spatial_mapping=make_spatial_mapping(),
        combination_mapping=make_combination_mapping(),
        climate=make_climate(),
    )

    assert len(panel) == len(epidemiology)


def test_rejeita_unidade_modelavel_sem_combo() -> None:
    """Uma unidade modelável sem combo climático deve interromper a integração."""
    combination_mapping = pd.DataFrame(
        {
            "codigo_ibge_7": pd.Series(dtype="string"),
            "combo_id": pd.Series(dtype="Int64"),
        }
    )

    with pytest.raises(
        ValueError,
        match="Unidades modeláveis sem combo climático",
    ):
        build_master_panel(
            epidemiology=make_epidemiology(),
            spatial_mapping=make_spatial_mapping(),
            combination_mapping=combination_mapping,
            climate=make_climate(),
        )


def test_rejeita_chave_climatica_duplicada() -> None:
    """O mesmo combo e semana não podem aparecer duas vezes no clima."""
    climate = pd.concat(
        [
            make_climate(),
            make_climate(),
        ],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="Base climática contém",
    ):
        build_master_panel(
            epidemiology=make_epidemiology(),
            spatial_mapping=make_spatial_mapping(),
            combination_mapping=make_combination_mapping(),
            climate=climate,
        )


def test_rejeita_unidade_modelavel_sem_clima_semanal() -> None:
    """Combo existente sem observação da semana deve causar erro."""
    climate = make_climate()
    climate["semana_epidemiologica"] = 2

    with pytest.raises(
        ValueError,
        match="Existem unidades modeláveis sem dados climáticos",
    ):
        build_master_panel(
            epidemiology=make_epidemiology(),
            spatial_mapping=make_spatial_mapping(),
            combination_mapping=make_combination_mapping(),
            climate=climate,
        )


def test_rejeita_chave_epidemiologica_duplicada() -> None:
    """Município, ano e semana devem formar uma chave epidemiológica única."""
    epidemiology = pd.concat(
        [
            make_epidemiology(),
            make_epidemiology().iloc[[0]],
        ],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="Base epidemiológica contém",
    ):
        build_master_panel(
            epidemiology=epidemiology,
            spatial_mapping=make_spatial_mapping(),
            combination_mapping=make_combination_mapping(),
            climate=make_climate(),
        )
