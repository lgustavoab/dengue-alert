"""Sincroniza o asset geográfico canônico para o frontend."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_DIR = PROJECT_ROOT / "data" / "serving" / "geography"

PUBLIC_SERVING_DIR = PROJECT_ROOT / "web" / "public" / "data" / "serving"

OUTPUT_DIR = PUBLIC_SERVING_DIR / "geography"

STAGING_DIR = PUBLIC_SERVING_DIR / "geography.__staging__"

BACKUP_DIR = PUBLIC_SERVING_DIR / "geography.__backup__"

TOPOJSON_NAME = "municipalities.topojson"
METADATA_NAME = "metadata.json"

SOURCE_TOPOJSON = SOURCE_DIR / TOPOJSON_NAME

SOURCE_METADATA = SOURCE_DIR / METADATA_NAME

EXPECTED_SCHEMA_VERSION = "1.0"
EXPECTED_STATUS = "APROVADO"
EXPECTED_TERRITORIES = 5_571

EXPECTED_MAPSHAPER_VERSION = "0.7.55"
EXPECTED_SIMPLIFICATION_INTERVAL_M = 100
EXPECTED_FORMAT = "TopoJSON"
EXPECTED_ID_FIELD = "CD_MUN"


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


def reject_nonfinite_constant(
    value: str,
) -> None:
    """Rejeita NaN e Infinity durante leitura de JSON."""
    raise ValueError(f"Constante JSON não permitida: {value}")


def load_json_strict(
    path: Path,
) -> dict[str, Any]:
    """Carrega um JSON com validação estrita."""
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_nonfinite_constant,
        )
    except (
        json.JSONDecodeError,
        ValueError,
    ) as error:
        raise ValueError(f"JSON inválido: {path}") from error

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError(f"JSON não possui objeto na raiz: {path}")

    return payload


def validate_source_files() -> None:
    """Confirma a existência dos artefatos canônicos."""
    for path in [
        SOURCE_TOPOJSON,
        SOURCE_METADATA,
    ]:
        if not path.exists():
            raise FileNotFoundError(f"Asset geográfico ausente: {path}")

        if not path.is_file():
            raise ValueError(f"Caminho geográfico não é arquivo: {path}")


def validate_metadata(
    metadata: dict[str, Any],
) -> None:
    """Valida os metadados congelados da malha web."""
    if metadata.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        raise ValueError("schema_version divergente na metadata geográfica.")

    if metadata.get("status") != EXPECTED_STATUS:
        raise ValueError("Status divergente na metadata geográfica.")

    preparation = metadata.get("preparation")

    if not isinstance(
        preparation,
        dict,
    ):
        raise TypeError("Bloco preparation ausente ou inválido.")

    if preparation.get("territories") != EXPECTED_TERRITORIES:
        raise ValueError("Quantidade territorial divergente na metadata.")

    geometry = metadata.get("web_geometry")

    if not isinstance(
        geometry,
        dict,
    ):
        raise TypeError("Bloco web_geometry ausente ou inválido.")

    if geometry.get("format") != EXPECTED_FORMAT:
        raise ValueError("Formato geográfico divergente.")

    if geometry.get("file") != TOPOJSON_NAME:
        raise ValueError("Nome do TopoJSON divergente.")

    if geometry.get("id_field") != EXPECTED_ID_FIELD:
        raise ValueError("Campo identificador divergente.")

    if geometry.get("mapshaper_version") != EXPECTED_MAPSHAPER_VERSION:
        raise ValueError("Versão do Mapshaper divergente.")

    if geometry.get("simplification_interval_m") != EXPECTED_SIMPLIFICATION_INTERVAL_M:
        raise ValueError("Intervalo de simplificação divergente.")

    if geometry.get("quantization") is not False:
        raise ValueError("A metadata indica quantização inesperada.")

    expected_size = geometry.get("size_bytes")

    if (
        not isinstance(
            expected_size,
            int,
        )
        or expected_size <= 0
    ):
        raise TypeError("size_bytes inválido na metadata.")

    actual_size = SOURCE_TOPOJSON.stat().st_size

    if actual_size != expected_size:
        raise ValueError(
            "Tamanho do TopoJSON diverge da metadata. "
            f"Esperado: {expected_size:,}; "
            f"obtido: {actual_size:,}."
        )

    expected_sha256 = geometry.get("sha256")

    if (
        not isinstance(
            expected_sha256,
            str,
        )
        or len(expected_sha256) != 64
    ):
        raise TypeError("SHA-256 inválido na metadata.")

    actual_sha256 = sha256_file(SOURCE_TOPOJSON)

    if actual_sha256 != expected_sha256:
        raise ValueError("SHA-256 do TopoJSON diverge da metadata.")


def collect_geometry_ids(
    geometry: Any,
) -> list[str]:
    """Extrai IDs municipais dos objetos TopoJSON."""
    if not isinstance(
        geometry,
        dict,
    ):
        raise TypeError("Geometria TopoJSON inválida.")

    geometry_type = geometry.get("type")

    if geometry_type == "GeometryCollection":
        geometries = geometry.get("geometries")

        if not isinstance(
            geometries,
            list,
        ):
            raise TypeError("GeometryCollection sem lista de geometrias.")

        ids: list[str] = []

        for item in geometries:
            ids.extend(collect_geometry_ids(item))

        return ids

    if geometry_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        raise ValueError(f"Tipo geométrico inesperado no TopoJSON: {geometry_type}")

    identifier = geometry.get("id")

    if not isinstance(
        identifier,
        str,
    ):
        if isinstance(
            identifier,
            int,
        ):
            identifier = str(identifier)
        else:
            raise TypeError("Geometria municipal sem ID válido.")

    identifier = identifier.strip().zfill(7)

    if len(identifier) != 7 or not identifier.isdigit():
        raise ValueError(f"ID municipal inválido no TopoJSON: {identifier}")

    return [
        identifier,
    ]


def validate_topology(
    topology: dict[str, Any],
) -> None:
    """Valida a estrutura mínima e IDs do TopoJSON."""
    if topology.get("type") != "Topology":
        raise ValueError("Asset geográfico não possui type=Topology.")

    if "transform" in topology:
        raise ValueError("TopoJSON contém transform; quantização não era esperada.")

    arcs = topology.get("arcs")

    if (
        not isinstance(
            arcs,
            list,
        )
        or not arcs
    ):
        raise TypeError("TopoJSON não possui arcos válidos.")

    objects = topology.get("objects")

    if (
        not isinstance(
            objects,
            dict,
        )
        or not objects
    ):
        raise TypeError("TopoJSON não possui objetos geográficos válidos.")

    municipality_ids: list[str] = []

    for geometry in objects.values():
        municipality_ids.extend(collect_geometry_ids(geometry))

    if len(municipality_ids) != EXPECTED_TERRITORIES:
        raise ValueError(
            "Quantidade de geometrias municipais divergente. "
            f"Esperado: {EXPECTED_TERRITORIES:,}; "
            f"obtido: {len(municipality_ids):,}."
        )

    unique_ids = set(municipality_ids)

    if len(unique_ids) != EXPECTED_TERRITORIES:
        raise ValueError("TopoJSON possui IDs municipais duplicados.")


def prepare_staging() -> None:
    """Prepara staging vazio."""
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)

    STAGING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def copy_asset(
    source: Path,
) -> Path:
    """Copia um asset e valida a integridade da cópia."""
    destination = STAGING_DIR / source.name

    shutil.copy2(
        source,
        destination,
    )

    source_hash = sha256_file(source)

    destination_hash = sha256_file(destination)

    if source_hash != destination_hash:
        raise ValueError(f"SHA-256 divergente após cópia: {source.name}")

    return destination


def validate_staging(
    source_metadata: dict[str, Any],
) -> None:
    """Relê e valida os assets copiados."""
    expected_files = {
        TOPOJSON_NAME,
        METADATA_NAME,
    }

    actual_files = {path.name for path in STAGING_DIR.iterdir() if path.is_file()}

    if actual_files != expected_files:
        raise ValueError(
            "Conjunto de arquivos geográficos do staging divergente. "
            f"Esperado: {sorted(expected_files)}; "
            f"obtido: {sorted(actual_files)}."
        )

    metadata = load_json_strict(STAGING_DIR / METADATA_NAME)

    if metadata != source_metadata:
        raise ValueError("Metadata copiada diverge da fonte canônica.")

    topology = load_json_strict(STAGING_DIR / TOPOJSON_NAME)

    validate_topology(topology)

    expected_sha256 = metadata["web_geometry"]["sha256"]

    actual_sha256 = sha256_file(STAGING_DIR / TOPOJSON_NAME)

    if actual_sha256 != expected_sha256:
        raise ValueError("SHA-256 do TopoJSON no staging diverge da metadata.")


def promote_staging() -> None:
    """Promove staging preservando a versão anterior."""
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)

    had_previous_output = OUTPUT_DIR.exists()

    if had_previous_output:
        OUTPUT_DIR.replace(BACKUP_DIR)

    try:
        STAGING_DIR.replace(OUTPUT_DIR)
    except Exception:
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)

        if had_previous_output and BACKUP_DIR.exists():
            BACKUP_DIR.replace(OUTPUT_DIR)

        raise

    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)


def synchronize() -> dict[str, Any]:
    """Executa a sincronização completa."""
    validate_source_files()

    metadata = load_json_strict(SOURCE_METADATA)

    validate_metadata(metadata)

    topology = load_json_strict(SOURCE_TOPOJSON)

    validate_topology(topology)

    prepare_staging()

    try:
        copy_asset(SOURCE_TOPOJSON)

        copy_asset(SOURCE_METADATA)

        validate_staging(metadata)

        promote_staging()

    except Exception:
        if STAGING_DIR.exists():
            shutil.rmtree(STAGING_DIR)

        raise

    return metadata


def format_mib(
    value: int,
) -> str:
    """Formata bytes em MiB."""
    return f"{value / 1024**2:.2f} MiB"


def print_summary(
    metadata: dict[str, Any],
) -> None:
    """Exibe resumo da sincronização."""
    geometry = metadata["web_geometry"]

    print("=" * 108)

    print("SERVING GEOGRÁFICO → FRONTEND")

    print("=" * 108)

    print()

    print(f"Municípios       : {EXPECTED_TERRITORIES:,}")

    print(f"TopoJSON bruto   : {format_mib(geometry['size_bytes'])}")

    print(f"TopoJSON gzip    : {format_mib(geometry['gzip_size_bytes'])}")

    print(f"SHA-256          : {geometry['sha256']}")

    print()

    print("Fonte:")

    print(f"  {SOURCE_DIR.relative_to(PROJECT_ROOT).as_posix()}")

    print()

    print("Destino:")

    print(f"  {OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}")

    print()

    print("URL pública planejada:")

    print("  /data/serving/geography/municipalities.topojson")

    print()

    print("STATUS: GEOMETRIA WEB SINCRONIZADA E VALIDADA")


def main() -> None:
    """Executa o sincronizador geográfico."""
    metadata = synchronize()

    print_summary(metadata)


if __name__ == "__main__":
    main()
