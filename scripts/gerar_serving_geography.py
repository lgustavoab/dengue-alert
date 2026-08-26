"""Gera a malha municipal otimizada para serving web."""

from __future__ import annotations

import gzip
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "geography"
    / "ibge_municipios_2024"
    / "BR_Municipios_2024.shp"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "serving" / "geography"

STAGING_DIR = OUTPUT_DIR.parent / "geography.__staging__"

BACKUP_DIR = OUTPUT_DIR.parent / "geography.__backup__"

AUDIT_FILE = PROJECT_ROOT / "reports" / "audits" / "serving_geography.json"

TOPOJSON_NAME = "municipalities.topojson"

METADATA_NAME = "metadata.json"

SCHEMA_VERSION = "1.0"

SOURCE_CRS = "EPSG:4674"
AUDIT_CRS = "EPSG:5880"

MAPSHAPER_VERSION = "0.7.55"
SIMPLIFICATION_METHOD = "Ramer-Douglas-Peucker"
SIMPLIFICATION_INTERVAL_M = 100

EXPECTED_SOURCE_FEATURES = 5_573
EXPECTED_TERRITORIES = 5_571

EXPECTED_INVALID_SOURCE_CODES = {
    "5007802",
}

EXPECTED_REMOVED_CODES = {
    "4300001",
    "4300002",
}

EXPECTED_GEOMETRY_TYPES = {
    "Polygon",
    "MultiPolygon",
}


def sha256_file(
    path: Path,
) -> str:
    """Calcula SHA-256 de um arquivo."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def gzip_size(
    data: bytes,
) -> int:
    """Calcula tamanho gzip determinístico."""
    return len(
        gzip.compress(
            data,
            compresslevel=9,
            mtime=0,
        )
    )


def load_source() -> gpd.GeoDataFrame:
    """Carrega a malha municipal original do IBGE."""
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Malha IBGE não encontrada: {SOURCE_FILE}")

    dataframe = gpd.read_file(
        SOURCE_FILE,
        columns=[
            "CD_MUN",
        ],
    )

    if len(dataframe) != EXPECTED_SOURCE_FEATURES:
        raise ValueError(
            "Quantidade inesperada de feições na malha original. "
            f"Esperado: {EXPECTED_SOURCE_FEATURES:,}; "
            f"obtido: {len(dataframe):,}."
        )

    if dataframe.crs is None or dataframe.crs.to_string() != SOURCE_CRS:
        raise ValueError(
            "CRS inesperado na malha original. "
            f"Esperado: {SOURCE_CRS}; "
            f"obtido: {dataframe.crs}."
        )

    dataframe["CD_MUN"] = dataframe["CD_MUN"].astype("string").str.strip()

    invalid_codes = set(
        dataframe.loc[
            ~dataframe.geometry.is_valid,
            "CD_MUN",
        ]
        .astype(str)
        .tolist()
    )

    if invalid_codes != EXPECTED_INVALID_SOURCE_CODES:
        raise ValueError(
            "Conjunto inesperado de geometrias inválidas "
            "na malha original. "
            f"Esperado: {sorted(EXPECTED_INVALID_SOURCE_CODES)}; "
            f"obtido: {sorted(invalid_codes)}."
        )

    if dataframe.geometry.is_empty.any():
        raise ValueError("A malha original possui geometrias vazias.")

    return dataframe


def prepare_source(
    dataframe: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Repara a geometria conhecida e remove feições extraterritoriais."""
    prepared = dataframe.copy()

    invalid_mask = ~prepared.geometry.is_valid

    prepared.loc[
        invalid_mask,
        "geometry",
    ] = prepared.loc[
        invalid_mask,
        "geometry",
    ].make_valid(
        method="structure",
        keep_collapsed=False,
    )

    if (~prepared.geometry.is_valid).any():
        raise ValueError("Persistiram geometrias inválidas após make_valid.")

    prepared = (
        prepared[~prepared["CD_MUN"].isin(EXPECTED_REMOVED_CODES)]
        .copy()
        .reset_index(drop=True)
    )

    if len(prepared) != EXPECTED_TERRITORIES:
        raise ValueError(
            "Quantidade territorial inesperada após preparação. "
            f"Esperado: {EXPECTED_TERRITORIES:,}; "
            f"obtido: {len(prepared):,}."
        )

    if prepared["CD_MUN"].nunique() != EXPECTED_TERRITORIES:
        raise ValueError("Códigos IBGE duplicados após preparação.")

    if set(prepared["CD_MUN"]) & EXPECTED_REMOVED_CODES:
        raise ValueError("Feições extraterritoriais não foram removidas.")

    geometry_types = set(prepared.geometry.geom_type.unique().tolist())

    if not geometry_types.issubset(EXPECTED_GEOMETRY_TYPES):
        raise ValueError(
            f"Foram produzidos tipos geométricos inesperados: {sorted(geometry_types)}."
        )

    if prepared.geometry.is_empty.any():
        raise ValueError("Foram produzidas geometrias vazias.")

    return prepared


def find_corepack() -> str:
    """Localiza o executável do Corepack."""
    executable = shutil.which("corepack")

    if executable is None:
        raise FileNotFoundError("Corepack não encontrado no PATH.")

    return executable


def run_command(
    command: list[str],
) -> None:
    """Executa comando externo e falha em caso de erro."""
    subprocess.run(
        command,
        check=True,
    )


def get_mapshaper_version(
    corepack: str,
) -> str:
    """Obtém e valida a versão efetiva do Mapshaper."""
    result = subprocess.run(
        [
            corepack,
            "pnpm",
            "dlx",
            f"mapshaper@{MAPSHAPER_VERSION}",
            "-v",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    version = result.stdout.strip() or result.stderr.strip()

    if MAPSHAPER_VERSION not in version:
        raise ValueError(
            "Versão inesperada do Mapshaper. "
            f"Esperado: {MAPSHAPER_VERSION}; "
            f"obtido: {version}."
        )

    return version


def generate_candidate(
    prepared: gpd.GeoDataFrame,
    temp_dir: Path,
    output_topojson: Path,
) -> Path:
    """Gera TopoJSON simplificado e GeoJSON temporário para auditoria."""
    prepared_shapefile = temp_dir / "prepared" / "BR_Municipios_2024_prepared.shp"

    prepared_shapefile.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    prepared[
        [
            "CD_MUN",
            "geometry",
        ]
    ].to_file(
        prepared_shapefile,
        driver="ESRI Shapefile",
        encoding="UTF-8",
        index=False,
    )

    corepack = find_corepack()

    version = get_mapshaper_version(corepack)

    print(f"Mapshaper  : {version}")

    run_command(
        [
            corepack,
            "pnpm",
            "dlx",
            f"mapshaper@{MAPSHAPER_VERSION}",
            str(prepared_shapefile),
            "-filter-fields",
            "CD_MUN",
            "-simplify",
            "dp",
            f"interval={SIMPLIFICATION_INTERVAL_M}m",
            "keep-shapes",
            "stats",
            "-o",
            str(output_topojson),
            "format=topojson",
            "id-field=CD_MUN",
            "no-quantization",
        ]
    )

    audit_geojson = temp_dir / "municipalities.audit.geojson"

    run_command(
        [
            corepack,
            "pnpm",
            "dlx",
            f"mapshaper@{MAPSHAPER_VERSION}",
            str(output_topojson),
            "-o",
            str(audit_geojson),
            "format=geojson",
        ]
    )

    return audit_geojson


def audit_candidate(
    audit_geojson: Path,
    expected_codes: set[str],
) -> dict[str, Any]:
    """Audita integridade geométrica e topológica do candidato."""
    candidate = gpd.read_file(audit_geojson)

    candidate = candidate.set_crs(
        SOURCE_CRS,
        allow_override=True,
    )

    candidate["CD_MUN"] = candidate["CD_MUN"].astype("string").str.strip()

    features = len(candidate)

    unique_codes = int(candidate["CD_MUN"].nunique())

    candidate_codes = set(candidate["CD_MUN"].astype(str).tolist())

    missing_codes = sorted(expected_codes - candidate_codes)

    unexpected_codes = sorted(candidate_codes - expected_codes)

    invalid_source_crs = int((~candidate.geometry.is_valid).sum())

    empty_geometries = int(candidate.geometry.is_empty.sum())

    geometry_types = sorted(candidate.geometry.geom_type.unique().tolist())

    projected = candidate.to_crs(AUDIT_CRS)

    invalid_audit_crs = int((~projected.geometry.is_valid).sum())

    valid_coverage = bool(projected.geometry.is_valid_coverage())

    invalid_edges = projected.geometry.invalid_coverage_edges()

    problematic_edges = int((~invalid_edges.is_empty).sum())

    if features != EXPECTED_TERRITORIES:
        raise ValueError("Quantidade divergente no candidato TopoJSON.")

    if unique_codes != EXPECTED_TERRITORIES:
        raise ValueError("Quantidade divergente de códigos únicos no candidato.")

    if missing_codes:
        raise ValueError(f"Códigos ausentes no candidato: {missing_codes}")

    if unexpected_codes:
        raise ValueError(f"Códigos inesperados no candidato: {unexpected_codes}")

    if invalid_source_crs:
        raise ValueError("O candidato possui geometrias inválidas em EPSG:4674.")

    if invalid_audit_crs:
        raise ValueError("O candidato possui geometrias inválidas em EPSG:5880.")

    if empty_geometries:
        raise ValueError("O candidato possui geometrias vazias.")

    if not set(geometry_types).issubset(EXPECTED_GEOMETRY_TYPES):
        raise ValueError("O candidato possui tipos geométricos inesperados.")

    if not valid_coverage:
        raise ValueError("O candidato não forma cobertura topológica válida.")

    if problematic_edges:
        raise ValueError(
            "O candidato possui arestas problemáticas "
            f"de cobertura: {problematic_edges}."
        )

    return {
        "features": features,
        "unique_codes": unique_codes,
        "invalid_epsg_4674": (invalid_source_crs),
        "invalid_epsg_5880": (invalid_audit_crs),
        "empty_geometries": (empty_geometries),
        "geometry_types": (geometry_types),
        "valid_coverage": (valid_coverage),
        "problematic_coverage_edges": (problematic_edges),
    }


def build_metadata(
    topology_path: Path,
    audit: dict[str, Any],
) -> dict[str, Any]:
    """Cria metadados do asset geográfico."""
    raw_bytes = topology_path.read_bytes()

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "APROVADO",
        "source": {
            "institution": "IBGE",
            "dataset": "Malha Municipal 2024",
            "file": (SOURCE_FILE.relative_to(PROJECT_ROOT).as_posix()),
            "crs": SOURCE_CRS,
            "source_features": (EXPECTED_SOURCE_FEATURES),
        },
        "preparation": {
            "invalid_source_codes": sorted(EXPECTED_INVALID_SOURCE_CODES),
            "make_valid": {
                "method": "structure",
                "keep_collapsed": False,
            },
            "removed_codes": sorted(EXPECTED_REMOVED_CODES),
            "territories": (EXPECTED_TERRITORIES),
        },
        "web_geometry": {
            "format": "TopoJSON",
            "file": TOPOJSON_NAME,
            "id_field": "CD_MUN",
            "mapshaper_version": (MAPSHAPER_VERSION),
            "simplification_method": (SIMPLIFICATION_METHOD),
            "simplification_interval_m": (SIMPLIFICATION_INTERVAL_M),
            "keep_shapes": True,
            "quantization": False,
            "size_bytes": len(raw_bytes),
            "gzip_size_bytes": gzip_size(raw_bytes),
            "sha256": sha256_file(topology_path),
        },
        "audit": audit,
    }


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    """Grava JSON de forma determinística."""
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def prepare_staging() -> None:
    """Prepara diretório temporário de serving."""
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)

    STAGING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def promote_staging() -> None:
    """Promove staging preservando versão anterior."""
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)

    had_previous = OUTPUT_DIR.exists()

    if had_previous:
        OUTPUT_DIR.replace(BACKUP_DIR)

    try:
        STAGING_DIR.replace(OUTPUT_DIR)
    except Exception:
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)

        if had_previous and BACKUP_DIR.exists():
            BACKUP_DIR.replace(OUTPUT_DIR)

        raise

    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)


def generate() -> dict[str, Any]:
    """Executa a geração completa da malha para serving."""
    source = load_source()

    print(f"Feições IBGE : {len(source):,}")

    prepared = prepare_source(source)

    print(f"Municípios   : {len(prepared):,}")

    expected_codes = set(prepared["CD_MUN"].astype(str).tolist())

    prepare_staging()

    topology_path = STAGING_DIR / TOPOJSON_NAME

    try:
        with tempfile.TemporaryDirectory(
            prefix="dengue-serving-geography-"
        ) as temporary:
            temp_dir = Path(temporary)

            audit_geojson = generate_candidate(
                prepared,
                temp_dir,
                topology_path,
            )

            print()
            print("Auditando TopoJSON final...")

            audit = audit_candidate(
                audit_geojson,
                expected_codes,
            )

        metadata = build_metadata(
            topology_path,
            audit,
        )

        write_json(
            STAGING_DIR / METADATA_NAME,
            metadata,
        )

        persisted_metadata = json.loads(
            (STAGING_DIR / METADATA_NAME).read_text(encoding="utf-8")
        )

        if persisted_metadata != metadata:
            raise ValueError("Metadata persistida diverge da versão em memória.")

        if sha256_file(topology_path) != metadata["web_geometry"]["sha256"]:
            raise ValueError("SHA-256 do TopoJSON diverge da metadata.")

        AUDIT_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        write_json(
            AUDIT_FILE,
            metadata,
        )

        promote_staging()

    except Exception:
        if STAGING_DIR.exists():
            shutil.rmtree(STAGING_DIR)

        raise

    return metadata


def format_mib(
    value: int,
) -> str:
    """Formata bytes como MiB."""
    return f"{value / 1024**2:.2f} MiB"


def print_summary(
    metadata: dict[str, Any],
) -> None:
    """Exibe resumo final."""
    geometry = metadata["web_geometry"]

    audit = metadata["audit"]

    print()
    print("=" * 108)
    print("SERVING GEOGRÁFICO MUNICIPAL")
    print("=" * 108)

    print(f"Municípios                 : {audit['features']:,}")

    print(f"Códigos únicos             : {audit['unique_codes']:,}")

    print(f"Inválidas EPSG:4674        : {audit['invalid_epsg_4674']}")

    print(f"Inválidas EPSG:5880        : {audit['invalid_epsg_5880']}")

    print(f"Geometrias vazias          : {audit['empty_geometries']}")

    print(f"Cobertura válida           : {audit['valid_coverage']}")

    print(f"Arestas problemáticas      : {audit['problematic_coverage_edges']}")

    print()
    print(f"TopoJSON bruto             : {format_mib(geometry['size_bytes'])}")

    print(f"TopoJSON gzip              : {format_mib(geometry['gzip_size_bytes'])}")

    print(f"Mapshaper                  : {geometry['mapshaper_version']}")

    print(f"Simplificação              : {geometry['simplification_interval_m']} m")

    print(f"Quantização                : {geometry['quantization']}")

    print()
    print(f"Destino                    : {OUTPUT_DIR}")

    print(f"Auditoria                  : {AUDIT_FILE}")

    print()
    print("STATUS: SERVING GEOGRÁFICO GERADO E VALIDADO")


def main() -> None:
    """Executa o gerador geográfico."""
    print("=" * 108)
    print("GERAÇÃO DO SERVING GEOGRÁFICO MUNICIPAL")
    print("=" * 108)

    print()
    print(f"Fonte       : {SOURCE_FILE}")

    print(f"Destino     : {OUTPUT_DIR}")

    print()

    metadata = generate()

    print_summary(metadata)


if __name__ == "__main__":
    main()
