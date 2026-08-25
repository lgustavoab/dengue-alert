"""Executa a construção do painel municipal semanal integrado."""

from time import perf_counter

from dengue_alert.config.paths import MASTER_PANEL
from dengue_alert.dataset.master import generate_master_panel


def main() -> None:
    """Constrói e grava o painel mestre."""
    print("=" * 88)
    print("CONSTRUÇÃO DO PAINEL MESTRE — DENGUE ALERT")
    print("=" * 88)

    inicio = perf_counter()

    panel = generate_master_panel()

    duracao = perf_counter() - inicio

    print()
    print(f"Linhas geradas       : {len(panel):,}")
    print(f"Municípios           : {panel['codigo_ibge_7'].nunique():,}")
    print(f"Linhas com clima     : {panel['clima_disponivel'].sum():,}")
    print(f"Linhas sem clima     : {(~panel['clima_disponivel']).sum():,}")
    print(f"Casos preservados    : {panel['casos_provaveis'].sum():,}")
    print(f"Tempo total          : {duracao:.2f} s")
    print()
    print(f"Arquivo: {MASTER_PANEL}")


if __name__ == "__main__":
    main()
