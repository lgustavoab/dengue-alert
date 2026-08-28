"""Gera o serving compacto e determinístico derivado de ``data/serving``."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from package_serving_snapshot import (
    CHUNK_SIZE,
    ZIP_MODE,
    ZIP_TIMESTAMP,
    hash_file_stable,
)
from sync_web_serving import CONTRACT_PATHS as PUBLIC_CONTRACT_PATHS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_VERSION = "serving-runtime-v1.0.0"
SCHEMA_VERSION = "1.0"
PACK_FORMAT = "ndjson-offset-v1"
DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "data" / "serving"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "dist" / RUNTIME_VERSION
DEFAULT_ARCHIVE_PATH = PROJECT_ROOT / "dist" / f"{RUNTIME_VERSION}.zip"
DEFAULT_MANIFEST_PATH = (
    PROJECT_ROOT / "artifacts" / "serving" / f"{RUNTIME_VERSION}.json"
)
MANIFEST_NAME = "manifest.json"
CHECKSUMS_NAME = "SHA256SUMS"
HISTORICAL_COUNT = 5_571
PREDICTION_COUNT = 5_569
MAP_SLICE_COUNT = 202
CODE_PATTERN = re.compile(r"^[0-9]{7}\.json$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

COLLECTIONS = {
    "historical": HISTORICAL_COUNT,
    "prediction": PREDICTION_COUNT,
}
GEOGRAPHY_PATHS = (
    "geography/metadata.json",
    "geography/municipalities.topojson",
)


class RuntimePackagingError(RuntimeError):
    """Indica que o runtime derivado não pode ser gerado com segurança."""


@dataclass(frozen=True)
class RuntimeFile:
    """Identidade de um arquivo pertencente ao runtime."""

    path: str
    size_bytes: int
    sha256: str
    role: str

    def manifest_entry(self) -> dict[str, str | int]:
        """Converte o arquivo para a entrada determinística do manifest."""
        return {
            "path": self.path,
            "role": self.role,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class RuntimeResult:
    """Resume uma geração completa e validada."""

    output_root: Path
    archive_path: Path
    manifest_path: Path
    checksum_path: Path
    runtime_file_count: int
    payload_file_count: int
    total_size_bytes: int
    archive_size_bytes: int
    archive_sha256: str
    elapsed_seconds: float


def _stat_signature(path: Path) -> tuple[int, int, int, int, int]:
    """Obtém atributos capazes de revelar alteração durante a leitura."""
    metadata = path.stat()
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def sha256_bytes(payload: bytes) -> str:
    """Calcula SHA-256 de bytes já carregados."""
    return hashlib.sha256(payload).hexdigest()


def read_stable_bytes(path: Path) -> bytes:
    """Lê bytes e falha se o arquivo mudar durante a operação."""
    before = _stat_signature(path)
    payload = path.read_bytes()
    after = _stat_signature(path)

    if before != after or len(payload) != before[2]:
        raise RuntimePackagingError(f"Arquivo mudou durante a leitura: {path}")

    return payload


def deterministic_json_bytes(payload: dict[str, Any]) -> bytes:
    """Serializa JSON técnico sem metadata volátil."""
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _safe_relative_path(value: str) -> PurePosixPath:
    """Valida um caminho relativo usado pelo runtime e pelo ZIP."""
    if not value or "\\" in value or any(ord(char) < 32 for char in value):
        raise RuntimePackagingError(f"Caminho de runtime inválido: {value!r}")

    path = PurePosixPath(value)

    if path.is_absolute() or "." in path.parts or ".." in path.parts:
        raise RuntimePackagingError(f"Caminho de runtime inseguro: {value}")

    if path.parts and path.parts[0].endswith(":"):
        raise RuntimePackagingError(f"Caminho absoluto não permitido: {value}")

    return path


def _safe_destination(root: Path, relative_path: str) -> Path:
    """Resolve um destino e garante confinamento na raiz informada."""
    safe_path = _safe_relative_path(relative_path)
    destination = root.joinpath(*safe_path.parts)
    resolved_root = root.resolve()
    resolved_destination = destination.resolve()

    try:
        resolved_destination.relative_to(resolved_root)
    except ValueError as error:
        raise RuntimePackagingError(
            f"Destino escaparia da raiz de runtime: {relative_path}"
        ) from error

    return destination


def discover_series_files(source_directory: Path) -> list[Path]:
    """Lista somente séries municipais esperadas, em ordem por código."""
    if not source_directory.is_dir():
        raise FileNotFoundError(f"Diretório municipal ausente: {source_directory}")

    entries = list(source_directory.iterdir())
    unexpected = [
        entry.name
        for entry in entries
        if not entry.is_file() or CODE_PATTERN.fullmatch(entry.name) is None
    ]

    if unexpected:
        raise RuntimePackagingError(
            "Arquivos municipais inesperados: " + ", ".join(sorted(unexpected))
        )

    files = sorted(entries, key=lambda path: path.stem)
    codes = [path.stem for path in files]

    if len(codes) != len(set(codes)):
        raise RuntimePackagingError("Código municipal duplicado")

    return files


def validate_source_payload(path: Path, payload: bytes) -> None:
    """Valida identidade mínima sem reserializar o payload científico."""
    if not payload:
        raise RuntimePackagingError(f"Payload municipal vazio: {path}")

    try:
        decoded = payload.decode("utf-8")
        contract = json.loads(decoded)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimePackagingError(f"Payload municipal inválido: {path}") from error

    if not isinstance(contract, dict):
        raise RuntimePackagingError(f"Payload municipal não é objeto: {path}")

    if contract.get("schema_version") != SCHEMA_VERSION:
        raise RuntimePackagingError(f"schema_version divergente: {path}")

    if contract.get("codigo_ibge_7") != path.stem:
        raise RuntimePackagingError(f"Código interno divergente: {path}")


def create_pack(
    source_files: list[Path],
    pack_path: Path,
    index_path: Path,
    collection: str,
    expected_count: int,
) -> tuple[RuntimeFile, RuntimeFile]:
    """Copia payloads originais para um pack e cria seu índice técnico."""
    source_files = sorted(source_files, key=lambda path: path.stem)
    source_codes = [path.stem for path in source_files]

    if len(source_codes) != len(set(source_codes)):
        raise RuntimePackagingError("Código municipal duplicado")

    if len(source_files) != expected_count:
        raise RuntimePackagingError(
            f"Quantidade divergente em {collection}: "
            f"esperado {expected_count}, obtido {len(source_files)}"
        )

    pack_path.parent.mkdir(parents=True, exist_ok=True)
    entries: dict[str, dict[str, str | int]] = {}
    offset = 0

    with pack_path.open("xb") as pack:
        for source in source_files:
            code = source.stem
            payload = read_stable_bytes(source)
            validate_source_payload(source, payload)
            length = len(payload)
            entries[code] = {
                "length": length,
                "offset": offset,
                "sha256": sha256_bytes(payload),
            }
            pack.write(payload)
            pack.write(b"\n")
            offset += length + 1

    pack_sha256, pack_size = hash_file_stable(pack_path)
    index = {
        "collection": collection,
        "encoding": "utf-8",
        "entries": entries,
        "format": PACK_FORMAT,
        "pack_file": pack_path.name,
        "pack_sha256": pack_sha256,
        "pack_size_bytes": pack_size,
        "record_count": len(entries),
        "runtime_version": RUNTIME_VERSION,
        "schema_version": SCHEMA_VERSION,
    }
    index_path.write_bytes(deterministic_json_bytes(index))
    validate_pack(source_files, pack_path, index_path, expected_count)
    index_sha256, index_size = hash_file_stable(index_path)

    return (
        RuntimeFile(
            path=pack_path.relative_to(pack_path.parents[1]).as_posix(),
            size_bytes=pack_size,
            sha256=pack_sha256,
            role=f"{collection}-municipality-pack",
        ),
        RuntimeFile(
            path=index_path.relative_to(index_path.parents[1]).as_posix(),
            size_bytes=index_size,
            sha256=index_sha256,
            role=f"{collection}-municipality-index",
        ),
    )


def load_runtime_index(index_path: Path) -> dict[str, Any]:
    """Carrega e valida a forma geral de um índice técnico."""
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimePackagingError(f"Índice inválido: {index_path}") from error

    if not isinstance(index, dict) or index.get("schema_version") != SCHEMA_VERSION:
        raise RuntimePackagingError(f"Índice incompatível: {index_path}")

    if index.get("format") != PACK_FORMAT or index.get("encoding") != "utf-8":
        raise RuntimePackagingError(f"Formato de índice incompatível: {index_path}")

    if not isinstance(index.get("entries"), dict):
        raise RuntimePackagingError(f"Índice sem entradas: {index_path}")

    return index


def validate_pack(
    source_files: list[Path],
    pack_path: Path,
    index_path: Path,
    expected_count: int,
) -> None:
    """Prova offsets, hashes, limites e equivalência byte a byte integral."""
    index = load_runtime_index(index_path)
    entries = index["entries"]
    source_by_code = {path.stem: path for path in source_files}

    if len(source_by_code) != len(source_files):
        raise RuntimePackagingError("Código duplicado na fonte municipal")

    if set(entries) != set(source_by_code) or len(entries) != expected_count:
        raise RuntimePackagingError("Entradas do índice divergem da fonte")

    pack_size = pack_path.stat().st_size
    pack_sha256, _ = hash_file_stable(pack_path)

    if index.get("pack_size_bytes") != pack_size:
        raise RuntimePackagingError("Tamanho do pack diverge do índice")

    if index.get("pack_sha256") != pack_sha256:
        raise RuntimePackagingError("SHA-256 do pack diverge do índice")

    if index.get("record_count") != expected_count:
        raise RuntimePackagingError("record_count diverge do índice")

    expected_offset = 0

    with pack_path.open("rb") as pack:
        for code in sorted(entries):
            entry = entries[code]

            if not isinstance(entry, dict):
                raise RuntimePackagingError(f"Entrada inválida no índice: {code}")

            offset = entry.get("offset")
            length = entry.get("length")
            digest = entry.get("sha256")

            if (
                not isinstance(offset, int)
                or isinstance(offset, bool)
                or offset != expected_offset
            ):
                raise RuntimePackagingError(f"Offset inválido ou overlap: {code}")

            if not isinstance(length, int) or isinstance(length, bool) or length <= 0:
                raise RuntimePackagingError(f"Length inválido: {code}")

            if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
                raise RuntimePackagingError(f"SHA-256 inválido no índice: {code}")

            if offset + length >= pack_size:
                raise RuntimePackagingError(f"Intervalo fora do pack: {code}")

            pack.seek(offset)
            payload = pack.read(length)
            separator = pack.read(1)
            canonical = read_stable_bytes(source_by_code[code])

            if payload != canonical:
                raise RuntimePackagingError(f"Payload diverge do canônico: {code}")

            if sha256_bytes(payload) != digest:
                raise RuntimePackagingError(f"SHA-256 do payload diverge: {code}")

            if separator != b"\n":
                raise RuntimePackagingError(f"Separador ausente após payload: {code}")

            expected_offset = offset + length + 1

    if expected_offset != pack_size:
        raise RuntimePackagingError("Pack contém bytes não indexados")


def expected_map_paths(source_root: Path) -> list[str]:
    """Define e valida exatamente o índice e os 202 slices do mapa."""
    relative_paths = ["prediction/map/index.json"]

    for horizon, weeks in ((1, 52), (2, 51), (3, 50), (4, 49)):
        relative_paths.extend(
            f"prediction/map/h{horizon}/se{week:02d}.json"
            for week in range(1, weeks + 1)
        )

    if len(relative_paths) != MAP_SLICE_COUNT + 1:
        raise RuntimePackagingError("Definição interna do mapa está divergente")

    map_root = source_root / "prediction" / "map"
    actual = {
        path.relative_to(source_root).as_posix()
        for path in map_root.rglob("*")
        if path.is_file()
    }
    expected = set(relative_paths)

    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise RuntimePackagingError(
            f"Mapa divergente. Ausentes: {missing}; inesperados: {unexpected}"
        )

    return relative_paths


def remaining_runtime_paths(source_root: Path) -> list[tuple[str, str]]:
    """Lista explicitamente contratos públicos/geográficos e mapa necessários."""
    paths = [(path, "public-contract") for path in PUBLIC_CONTRACT_PATHS]
    paths.extend((path, "public-geography") for path in GEOGRAPHY_PATHS)
    paths.extend((path, "prediction-map") for path in expected_map_paths(source_root))

    names = [path for path, _ in paths]

    if len(names) != len(set(names)):
        raise RuntimePackagingError("Lista de contratos restantes contém duplicatas")

    return sorted(paths)


def copy_remaining_files(
    source_root: Path,
    runtime_root: Path,
) -> list[RuntimeFile]:
    """Copia somente a allowlist necessária, sempre byte a byte."""
    records: list[RuntimeFile] = []

    for relative_path, role in remaining_runtime_paths(source_root):
        source = source_root.joinpath(*PurePosixPath(relative_path).parts)

        if not source.is_file():
            raise FileNotFoundError(f"Contrato de runtime ausente: {source}")

        payload = read_stable_bytes(source)
        destination = _safe_destination(runtime_root, relative_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)

        if destination.read_bytes() != payload:
            raise RuntimePackagingError(f"Cópia divergiu da fonte: {relative_path}")

        records.append(
            RuntimeFile(
                path=relative_path,
                size_bytes=len(payload),
                sha256=sha256_bytes(payload),
                role=role,
            )
        )

    return records


def canonical_fingerprint(source_root: Path) -> dict[str, str | int]:
    """Calcula uma impressão SHA-256 determinística de toda a fonte canônica."""
    files = sorted(
        (path for path in source_root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(source_root).as_posix(),
    )
    digest = hashlib.sha256()
    total_size = 0

    for path in files:
        relative = path.relative_to(source_root).as_posix()
        file_sha256, size = hash_file_stable(path)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha256.encode("ascii"))
        digest.update(b"\n")
        total_size += size

    return {
        "digest_algorithm": "sha256-path-content-manifest-v1",
        "digest": digest.hexdigest(),
        "file_count": len(files),
        "total_size_bytes": total_size,
    }


def build_manifest(
    files: list[RuntimeFile],
    source_fingerprint: dict[str, str | int],
) -> dict[str, Any]:
    """Cria o manifest completo do runtime derivado."""
    ordered = sorted(files, key=lambda record: record.path)
    paths = [record.path for record in ordered]

    if len(paths) != len(set(paths)):
        raise RuntimePackagingError("Manifest contém caminhos duplicados")

    return {
        "canonical_source": "data/serving",
        "derivation": {
            "municipality_format": PACK_FORMAT,
            "municipality_payloads": "byte-preserved UTF-8 JSON",
            "prediction_map": "byte-preserved individual slices",
            "public_contracts": "explicit allowlist",
        },
        "file_count": len(ordered),
        "files": [record.manifest_entry() for record in ordered],
        "runtime_version": RUNTIME_VERSION,
        "schema_version": SCHEMA_VERSION,
        "source_fingerprint": source_fingerprint,
        "total_size_bytes": sum(record.size_bytes for record in ordered),
    }


def manifest_file_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Valida e indexa as entradas do manifest do runtime."""
    files = manifest.get("files")

    if not isinstance(files, list):
        raise RuntimePackagingError("Manifest sem lista de arquivos")

    paths = [entry.get("path") for entry in files if isinstance(entry, dict)]

    if len(paths) != len(files) or paths != sorted(paths):
        raise RuntimePackagingError("Manifest não está ordenado")

    if len(paths) != len(set(paths)):
        raise RuntimePackagingError("Manifest contém caminhos duplicados")

    indexed: dict[str, dict[str, Any]] = {}

    for entry in files:
        path_value = entry.get("path")
        size = entry.get("size_bytes")
        digest = entry.get("sha256")

        if not isinstance(path_value, str):
            raise RuntimePackagingError("Manifest contém caminho inválido")

        _safe_relative_path(path_value)

        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            raise RuntimePackagingError(f"Tamanho inválido no manifest: {path_value}")

        if not isinstance(digest, str) or SHA256_PATTERN.fullmatch(digest) is None:
            raise RuntimePackagingError(f"SHA-256 inválido no manifest: {path_value}")

        indexed[path_value] = entry

    if manifest.get("file_count") != len(indexed):
        raise RuntimePackagingError("file_count divergente no manifest")

    if manifest.get("total_size_bytes") != sum(
        int(entry["size_bytes"]) for entry in files
    ):
        raise RuntimePackagingError("total_size_bytes divergente no manifest")

    return indexed


def checksums_bytes(manifest: dict[str, Any]) -> bytes:
    """Deriva SHA256SUMS dos arquivos de payload do runtime."""
    indexed = manifest_file_map(manifest)
    lines = [f"{entry['sha256']}  {path}" for path, entry in indexed.items()]
    return ("\n".join(lines) + "\n").encode("utf-8")


def validate_runtime_tree(
    runtime_root: Path,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Valida allowlist, controles, hashes e ausência das séries individuais."""
    manifest_path = runtime_root / MANIFEST_NAME
    checksums_path = runtime_root / CHECKSUMS_NAME

    try:
        persisted = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimePackagingError(
            "Manifest do runtime ausente ou inválido"
        ) from error

    if manifest is not None and persisted != manifest:
        raise RuntimePackagingError("Manifest persistido diverge do esperado")

    indexed = manifest_file_map(persisted)
    expected_paths = {MANIFEST_NAME, CHECKSUMS_NAME, *indexed}
    actual_paths = {
        path.relative_to(runtime_root).as_posix()
        for path in runtime_root.rglob("*")
        if path.is_file()
    }

    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        unexpected = sorted(actual_paths - expected_paths)
        raise RuntimePackagingError(
            f"Árvore runtime divergente. Ausentes: {missing}; extras: {unexpected}"
        )

    forbidden = [path for path in actual_paths if "/municipality/series/" in f"/{path}"]

    if forbidden:
        raise RuntimePackagingError("Runtime contém séries individuais")

    if manifest_path.read_bytes() != deterministic_json_bytes(persisted):
        raise RuntimePackagingError("Serialização do manifest não é determinística")

    if checksums_path.read_bytes() != checksums_bytes(persisted):
        raise RuntimePackagingError("SHA256SUMS diverge do manifest")

    for relative_path, entry in indexed.items():
        path = _safe_destination(runtime_root, relative_path)
        digest, size = hash_file_stable(path)

        if digest != entry["sha256"] or size != entry["size_bytes"]:
            raise RuntimePackagingError(
                f"Hash ou tamanho divergente no runtime: {relative_path}"
            )

    return persisted


def _zip_info(name: str) -> zipfile.ZipInfo:
    """Cria metadata ZIP normalizada."""
    info = zipfile.ZipInfo(name, date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = ZIP_MODE << 16
    return info


def create_runtime_archive(
    runtime_root: Path,
    archive_path: Path,
    manifest: dict[str, Any],
) -> None:
    """Cria ZIP determinístico em diretório ignorado."""
    if archive_path.exists():
        raise FileExistsError(f"Archive runtime já existe: {archive_path}")

    validate_runtime_tree(runtime_root, manifest)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{archive_path.name}.",
        suffix=".tmp",
        dir=archive_path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    ordered_paths = [MANIFEST_NAME, CHECKSUMS_NAME, *manifest_file_map(manifest)]

    try:
        with zipfile.ZipFile(
            temporary_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for relative_path in ordered_paths:
                source = _safe_destination(runtime_root, relative_path)
                archive_name = f"{RUNTIME_VERSION}/{relative_path}"

                with (
                    source.open("rb") as input_file,
                    archive.open(_zip_info(archive_name), "w") as output_file,
                ):
                    shutil.copyfileobj(input_file, output_file, CHUNK_SIZE)

        verify_runtime_archive(temporary_path, manifest)
        temporary_path.replace(archive_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def verify_runtime_archive(
    archive_path: Path,
    expected_manifest: dict[str, Any],
) -> None:
    """Valida caminhos, ordem, controles e hashes internos do ZIP."""
    indexed = manifest_file_map(expected_manifest)
    relative_paths = [MANIFEST_NAME, CHECKSUMS_NAME, *indexed]
    expected_names = [f"{RUNTIME_VERSION}/{path}" for path in relative_paths]

    with zipfile.ZipFile(archive_path, mode="r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]

        if names != expected_names or len(names) != len(set(names)):
            raise RuntimePackagingError("ZIP não contém exatamente a ordem esperada")

        for info in infos:
            if info.flag_bits & 0x1 or info.is_dir():
                raise RuntimePackagingError(f"Entrada ZIP inválida: {info.filename}")

            file_type = (info.external_attr >> 16) & 0o170000

            if file_type == stat.S_IFLNK:
                raise RuntimePackagingError(f"Symlink não permitido: {info.filename}")

            relative = PurePosixPath(info.filename)

            if relative.parts[0] != RUNTIME_VERSION or len(relative.parts) < 2:
                raise RuntimePackagingError(f"Raiz ZIP inválida: {info.filename}")

            _safe_relative_path(PurePosixPath(*relative.parts[1:]).as_posix())

        manifest_name = f"{RUNTIME_VERSION}/{MANIFEST_NAME}"
        checksums_name = f"{RUNTIME_VERSION}/{CHECKSUMS_NAME}"

        if archive.read(manifest_name) != deterministic_json_bytes(expected_manifest):
            raise RuntimePackagingError("Manifest interno do ZIP diverge")

        if archive.read(checksums_name) != checksums_bytes(expected_manifest):
            raise RuntimePackagingError("SHA256SUMS interno do ZIP diverge")

        for relative_path, entry in indexed.items():
            payload = archive.read(f"{RUNTIME_VERSION}/{relative_path}")

            if len(payload) != entry["size_bytes"]:
                raise RuntimePackagingError(
                    f"Tamanho divergente no ZIP: {relative_path}"
                )

            if sha256_bytes(payload) != entry["sha256"]:
                raise RuntimePackagingError(
                    f"SHA-256 divergente no ZIP: {relative_path}"
                )


def _write_or_validate_manifest(path: Path, payload: bytes) -> None:
    """Grava o manifest inicial ou exige equivalência com o já versionado."""
    if path.exists():
        if path.read_bytes() != payload:
            raise RuntimePackagingError(f"Manifest versionado diverge: {path}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def package_runtime(
    source_root: Path = DEFAULT_SOURCE_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    archive_path: Path = DEFAULT_ARCHIVE_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> RuntimeResult:
    """Gera árvore, manifest, ZIP e valida integralmente a derivação."""
    started = time.monotonic()
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")

    for destination in (output_root, archive_path, checksum_path):
        if destination.exists():
            raise FileExistsError(f"Destino de runtime já existe: {destination}")

    source_root = source_root.resolve(strict=True)
    source_fingerprint = canonical_fingerprint(source_root)
    output_root.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=f".{RUNTIME_VERSION}.",
        dir=output_root.parent,
    ) as temporary:
        staging_root = Path(temporary) / RUNTIME_VERSION
        staging_root.mkdir()
        runtime_files: list[RuntimeFile] = []

        for collection, expected_count in COLLECTIONS.items():
            source_directory = source_root / collection / "municipality" / "series"
            source_files = discover_series_files(source_directory)
            collection_root = staging_root / collection
            pack_path = collection_root / "municipalities.ndjson"
            index_path = collection_root / "municipalities.index.json"
            runtime_files.extend(
                create_pack(
                    source_files,
                    pack_path,
                    index_path,
                    collection,
                    expected_count,
                )
            )

        runtime_files.extend(copy_remaining_files(source_root, staging_root))
        manifest = build_manifest(runtime_files, source_fingerprint)
        manifest_payload = deterministic_json_bytes(manifest)
        (staging_root / MANIFEST_NAME).write_bytes(manifest_payload)
        (staging_root / CHECKSUMS_NAME).write_bytes(checksums_bytes(manifest))
        validate_runtime_tree(staging_root, manifest)
        _write_or_validate_manifest(manifest_path, manifest_payload)
        staging_root.replace(output_root)

    create_runtime_archive(output_root, archive_path, manifest)
    archive_sha256, archive_size = hash_file_stable(archive_path)
    checksum_path.write_text(
        f"{archive_sha256}  {archive_path.name}\n",
        encoding="utf-8",
        newline="\n",
    )
    final_fingerprint = canonical_fingerprint(source_root)

    if final_fingerprint != source_fingerprint:
        raise RuntimePackagingError("Fonte canônica mudou durante a geração")

    runtime_paths = [path for path in output_root.rglob("*") if path.is_file()]

    return RuntimeResult(
        output_root=output_root,
        archive_path=archive_path,
        manifest_path=manifest_path,
        checksum_path=checksum_path,
        runtime_file_count=len(runtime_paths),
        payload_file_count=int(manifest["file_count"]),
        total_size_bytes=sum(path.stat().st_size for path in runtime_paths),
        archive_size_bytes=archive_size,
        archive_sha256=archive_sha256,
        elapsed_seconds=time.monotonic() - started,
    )


def parse_args() -> argparse.Namespace:
    """Lê caminhos explícitos para a geração local."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE_PATH)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    return parser.parse_args()


def main() -> None:
    """Gera o runtime completo e imprime um resumo legível por máquina."""
    args = parse_args()
    result = package_runtime(
        source_root=args.source,
        output_root=args.output_root,
        archive_path=args.archive,
        manifest_path=args.manifest,
    )
    print(
        json.dumps(
            {
                "archive": str(result.archive_path),
                "archive_sha256": result.archive_sha256,
                "archive_size_bytes": result.archive_size_bytes,
                "checksum": str(result.checksum_path),
                "elapsed_seconds": round(result.elapsed_seconds, 3),
                "manifest": str(result.manifest_path),
                "output_root": str(result.output_root),
                "payload_file_count": result.payload_file_count,
                "runtime_file_count": result.runtime_file_count,
                "runtime_version": RUNTIME_VERSION,
                "total_size_bytes": result.total_size_bytes,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
