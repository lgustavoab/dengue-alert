"""Testes dos contratos de serving de metadata e qualidade."""

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SERVING_SCRIPT = PROJECT_ROOT / "scripts" / "gerar_serving_quality_metadata.py"

SPEC = importlib.util.spec_from_file_location(
    "gerar_serving_quality_metadata",
    SERVING_SCRIPT,
)

if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Não foi possível carregar o script: {SERVING_SCRIPT}")

serving = importlib.util.module_from_spec(SPEC)

SPEC.loader.exec_module(serving)


def test_write_json_preserves_utf8_and_rejects_nan(
    tmp_path,
) -> None:
    """JSON deve ser UTF-8, válido e não permitir NaN."""
    output = tmp_path / "contract.json"

    payload = {
        "schema_version": "1.0",
        "data": {
            "texto": "Dados climáticos",
            "valor": 10,
        },
    }

    serving.write_json(
        output,
        payload,
    )

    text = output.read_text(encoding="utf-8")

    assert "Dados climáticos" in text

    loaded = json.loads(text)

    assert loaded == payload

    with pytest.raises(ValueError):
        serving.write_json(
            tmp_path / "invalid.json",
            {"data": {"valor": float("nan")}},
        )


def test_build_temporal_coverage() -> None:
    """Cobertura temporal deve preservar os anos auditados."""
    funnel_audit = {
        "grade_epidemiologica": {
            "anos_com_53_semanas": [
                2020,
                2025,
            ],
            "regra_semana": (
                "domingo a sabado; semana epidemiologica 1 "
                "definida de forma a conter o dia 4 de janeiro"
            ),
        }
    }

    panorama_audit = {
        "painel_mestre": {
            "anos": list(
                range(
                    2016,
                    2026,
                )
            ),
            "semanas_nacionais": 522,
        }
    }

    contract = serving.build_temporal_coverage(
        funnel_audit,
        panorama_audit,
    )

    data = contract["data"]

    assert contract["schema_version"] == "1.0"

    assert data["periodo_historico"] == "2016-2025"

    assert data["anos"] == list(
        range(
            2016,
            2026,
        )
    )

    assert data["semanas_nacionais"] == 522

    assert data["anos_com_53_semanas"] == [
        2020,
        2025,
    ]


def test_build_quality_overview_preserves_audited_totals() -> None:
    """Overview deve reproduzir os totais científicos auditados."""
    funnel_audit = {
        "entrada_sinan": {
            "registros_brutos": 19_336_281,
        },
        "processamento_v2": {
            "registros_mantidos_apos_filtros": 16_294_945,
        },
        "grade_epidemiologica": {
            "linhas_preenchidas_com_zero": 2_186_284,
        },
    }

    master_audit = {
        "painel": {
            "casos_provaveis": 16_294_913,
            "municipios": 5_571,
            "linhas": 2_907_593,
        },
        "clima": {
            "linhas_com_clima": 2_907_071,
            "linhas_sem_clima": 522,
        },
    }

    keys_audit = {
        "mapeamento_climatico": {
            "unidades": 5_570,
        }
    }

    contract = serving.build_quality_overview(
        funnel_audit,
        master_audit,
        keys_audit,
    )

    data = contract["data"]

    assert data == {
        "registros_sinan_brutos": 19_336_281,
        "registros_sinan_mantidos_apos_filtros": 16_294_945,
        "casos_finais_preservados": 16_294_913,
        "unidades_territoriais": 5_571,
        "municipio_semanas": 2_907_593,
        "linhas_zero_fill": 2_186_284,
        "unidades_com_cobertura_climatica": 5_570,
        "municipio_semanas_com_clima": 2_907_071,
        "municipio_semanas_sem_clima": 522,
    }

    assert contract["source"] == [
        "reports/audits/auditoria_funil_sinan_2016_2025.json",
        "reports/audits/auditoria_painel_mestre.json",
        "reports/audits/auditoria_chaves_painel_mestre.json",
    ]


def test_build_sinan_pipeline_keeps_duplicate_check_without_fake_count() -> None:
    """NDUPLIC_N deve aparecer como verificação, sem exclusão inventada."""
    funnel_audit = {
        "processamento_v2": {
            "duplicidade_logica": {
                "campo": "NDUPLIC_N",
                "observacao": "Contagem separada de exclusões não documentada.",
            },
            "filtros_documentados": {
                "classi_fin_5": {
                    "registros_removidos": 3_002_212,
                },
                "municipio_invalido": {
                    "registros_removidos": 1_149,
                },
                "sem_pri_invalida": {
                    "registros_removidos": 79,
                },
                "fora_periodo_2016_2025": {
                    "registros_removidos": 37_896,
                },
            },
            "registros_mantidos_apos_filtros": 16_294_945,
            "grupos_municipio_ano_semana_antes_normalizacao_territorial": 723_860,
            "codigos_sinan_6_digitos": 5_621,
        },
        "entrada_sinan": {
            "registros_brutos": 19_336_281,
        },
        "resultado_apos_normalizacao_territorial": {
            "casos_preservados": 16_294_913,
        },
        "grade_epidemiologica": {
            "linhas_observadas_antes_zero_fill": 721_309,
            "linhas_apos_zero_fill": 2_907_593,
            "linhas_preenchidas_com_zero": 2_186_284,
            "casos_antes_zero_fill": 16_294_913,
            "casos_depois_zero_fill": 16_294_913,
        },
    }

    contract = serving.build_sinan_pipeline(funnel_audit)

    data = contract["data"]

    duplicate_step = data["etapas"][0]

    assert duplicate_step["field"] == "NDUPLIC_N"

    assert duplicate_step["operation"] == "validation"

    assert duplicate_step["records_removed"] is None

    assert data["total_remocoes_documentadas"] == 3_041_336

    assert (
        data["registros_brutos"] - data["total_remocoes_documentadas"]
        == data["registros_mantidos_apos_filtros"]
    )

    assert data["casos_finais"] == 16_294_913


def test_build_territories_creates_stable_identifiers(
    tmp_path,
    monkeypatch,
) -> None:
    """Territórios devem usar códigos como strings normalizadas."""
    input_file = tmp_path / "territories.csv"

    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": [
                "123456",
                "7654321",
            ],
            "nome_municipio_ibge": [
                "Município A",
                "Município B",
            ],
            "codigo_uf_ibge": [
                "1",
                "35",
            ],
            "nome_uf_ibge": [
                "Estado A",
                "São Paulo",
            ],
            "regiao": [
                "Norte",
                "Sudeste",
            ],
            "anos_disponiveis": [
                10,
                10,
            ],
        }
    )

    dataframe.to_csv(
        input_file,
        index=False,
    )

    monkeypatch.setattr(
        serving,
        "SPATIAL_MUNICIPAL_FILE",
        input_file,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_TERRITORIES",
        2,
    )

    monkeypatch.setattr(
        serving,
        "source_path",
        lambda _: "tests/fixtures/territories.csv",
    )

    contract = serving.build_territories()

    assert contract["count"] == 2

    assert contract["data"][0]["codigo_ibge_7"] == "0123456"

    assert contract["data"][0]["codigo_uf_ibge"] == "01"

    assert contract["data"][1]["codigo_ibge_7"] == "7654321"


def test_build_population_coverage_validates_2023_reference(
    monkeypatch,
) -> None:
    """2023 deve permanecer explicitamente associado ao Censo 2022."""
    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": [
                "1111111",
                "2222222",
                "1111111",
                "2222222",
            ],
            "ano_epidemiologico": [
                2022,
                2022,
                2023,
                2023,
            ],
            "populacao": [
                10_000,
                20_000,
                10_500,
                20_500,
            ],
            "tipo_populacao": [
                "censo",
                "censo",
                "censo_reutilizado",
                "censo_reutilizado",
            ],
            "ano_referencia_populacao": [
                2022,
                2022,
                2022,
                2022,
            ],
        }
    )

    monkeypatch.setattr(
        serving,
        "load_population_panel",
        lambda: dataframe,
    )

    master_audit = {
        "populacao": {
            "ausentes": 0,
            "nao_positivas": 0,
        }
    }

    contract = serving.build_population_coverage(master_audit)

    reference = contract["data"]["referencia_2023"]

    assert reference == {
        "ano_epidemiologico": 2023,
        "ano_referencia_populacao": 2022,
        "usa_referencia_censo_2022": True,
    }


def test_build_population_coverage_rejects_wrong_2023_reference(
    monkeypatch,
) -> None:
    """Uma referência populacional incorreta para 2023 deve falhar."""
    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": [
                "1111111",
            ],
            "ano_epidemiologico": [
                2023,
            ],
            "populacao": [
                10_000,
            ],
            "tipo_populacao": [
                "estimativa",
            ],
            "ano_referencia_populacao": [
                2023,
            ],
        }
    )

    monkeypatch.setattr(
        serving,
        "load_population_panel",
        lambda: dataframe,
    )

    master_audit = {
        "populacao": {
            "ausentes": 0,
            "nao_positivas": 0,
        }
    }

    with pytest.raises(
        ValueError,
        match="referência populacional de 2023",
    ):
        serving.build_population_coverage(master_audit)


def test_build_climate_coverage_preserves_mapping_counts(
    monkeypatch,
) -> None:
    """Cobertura climática deve respeitar território, grade e combos."""
    dataframe = pd.DataFrame(
        {
            "codigo_ibge_7": [
                "1111111",
                "2222222",
                "3333333",
                "2605459",
            ],
            "modelavel_era5_land": [
                True,
                True,
                True,
                False,
            ],
            "metodo_selecao_grid": [
                "grid_mais_proximo_valido",
                "grid_mais_proximo_valido",
                "fallback_valido_intersecta_municipio",
                None,
            ],
            "latitude_grid_era5_final": [
                -10.0,
                -10.0,
                -11.0,
                None,
            ],
            "longitude_grid_era5_final": [
                -50.0,
                -50.0,
                -51.0,
                None,
            ],
            "combo_id": [
                "combo_1",
                "combo_2",
                "combo_3",
                None,
            ],
            "timezone_iana": [
                "America/Sao_Paulo",
                "America/Manaus",
                "America/Sao_Paulo",
                "America/Noronha",
            ],
            "clima_disponivel": [
                True,
                True,
                True,
                False,
            ],
        }
    )

    monkeypatch.setattr(
        serving,
        "load_climate_panel",
        lambda: dataframe,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CLIMATE_TERRITORIES",
        3,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CLIMATE_GRID_POINTS",
        2,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CLIMATE_COMBOS",
        3,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CLIMATE_ROWS_AVAILABLE",
        3,
    )

    monkeypatch.setattr(
        serving,
        "EXPECTED_CLIMATE_ROWS_UNAVAILABLE",
        1,
    )

    master_audit = {
        "clima": {
            "linhas_com_clima": 3,
            "linhas_sem_clima": 1,
        }
    }

    keys_audit = {
        "clima": {
            "linhas": 100,
            "combos": 3,
        },
        "cobertura": {
            "codigos_excluidos": ["2605459"],
        },
    }

    contract = serving.build_climate_coverage(
        master_audit,
        keys_audit,
    )

    data = contract["data"]

    assert data["unidades_com_mapeamento_climatico"] == 3

    assert data["pontos_grade_distintos"] == 2

    assert data["combinacoes_grade_timezone"] == 3

    assert data["municipio_semanas_com_clima"] == 3

    assert data["municipio_semanas_sem_clima"] == 1

    assert data["codigos_excluidos"] == ["2605459"]

    assert data["metodos_selecao_grid"] == {
        "fallback_valido_intersecta_municipio": 1,
        "grid_mais_proximo_valido": 2,
    }

    assert sum(data["metodos_selecao_grid"].values()) == 3
