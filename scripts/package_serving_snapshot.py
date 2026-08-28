"""Gera e valida o snapshot científico imutável de ``data/serving``."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import tempfile
import time
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "data" / "serving"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "artifacts" / "serving" / "serving-v1.0.0.json"
DEFAULT_ARCHIVE_PATH = PROJECT_ROOT / "dist" / "serving-v1.0.0.zip"

SCHEMA_VERSION = "1.0"
SNAPSHOT_VERSION = "serving-v1.0.0"
SCIENTIFIC_PERIOD = "2016-2025"
PREDICTION_EVALUATION_PERIOD = "2025"
SOURCE_ROOT_LABEL = "data/serving"
ARCHIVE_SERVING_ROOT = PurePosixPath(SOURCE_ROOT_LABEL)
MANIFEST_NAME = "manifest.json"
CHECKSUMS_NAME = "SHA256SUMS"

ALLOWED_SUFFIXES = frozenset({".json", ".topojson"})
FORBIDDEN_COMPONENTS = frozenset(
    {
        ".git",
        ".next",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
    }
)
FORBIDDEN_NAMES = frozenset({".DS_Store", "Desktop.ini", "Thumbs.db"})
TEMPORARY_SUFFIXES = (".bak", ".swp", ".temp", ".tmp", "~")

ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ZIP_MODE = stat.S_IFREG | 0o644
CHUNK_SIZE = 1024 * 1024
MAX_CONTROL_FILE_SIZE = 16 * 1024 * 1024


class SnapshotError(RuntimeError):
    """Indica que o serving não pode ser empacotado com segurança."""


@dataclass(frozen=True)
class FileRecord:
    """Representa um arquivo canônico e sua identidade de conteúdo."""

    source_path: Path
    archive_path: str
    size_bytes: int
    sha256: str

    def manifest_entry(self) -> dict[str, str | int]:
        """Converte o registro para a representação pública do manifest."""
        return {
            "path": self.archive_path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class SnapshotResult:
    """Resume o snapshot validado produzido pelo empacotador."""

    archive_path: Path
    manifest_path: Path
    checksum_path: Path
    file_count: int
    total_size_bytes: int
    archive_size_bytes: int
    archive_sha256: str
    elapsed_seconds: float


def _stat_signature(path: Path) -> tuple[int, int, int, int, int]:
    """Obtém atributos capazes de revelar mudança durante uma leitura."""
    metadata = path.stat()
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _hash_stream(stream: BinaryIO) -> tuple[str, int]:
    """Calcula SHA-256 e tamanho de um stream binário."""
    digest = hashlib.sha256()
    size = 0

    for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
        digest.update(chunk)
        size += len(chunk)

    return digest.hexdigest(), size


def hash_file_stable(path: Path) -> tuple[str, int]:
    """Calcula hash e falha se o arquivo mudar durante a leitura."""
    before = _stat_signature(path)

    with path.open("rb") as source:
        digest, size = _hash_stream(source)

    after = _stat_signature(path)

    if before != after or size != before[2]:
        raise SnapshotError(f"Arquivo mudou durante a leitura: {path}")

    return digest, size


def validate_archive_path(path: str) -> PurePosixPath:
    """Valida um caminho interno relativo ao serving do snapshot."""
    if not path or "\\" in path or any(ord(character) < 32 for character in path):
        raise SnapshotError(f"Caminho interno inválido: {path!r}")

    candidate = PurePosixPath(path)

    if candidate.is_absolute() or ".." in candidate.parts or "." in candidate.parts:
        raise SnapshotError(f"Caminho interno inseguro: {path}")

    if candidate.parts and candidate.parts[0].endswith(":"):
        raise SnapshotError(f"Caminho interno absoluto não permitido: {path}")

    if candidate.parts[:2] != ARCHIVE_SERVING_ROOT.parts or len(candidate.parts) < 3:
        raise SnapshotError(f"Arquivo fora de {SOURCE_ROOT_LABEL}: {path}")

    return candidate


def archive_path_for_file(source_root: Path, path: Path) -> str:
    """Converte um arquivo canônico em caminho POSIX seguro do snapshot."""
    resolved_root = source_root.resolve(strict=True)
    resolved_path = path.resolve(strict=True)

    try:
        relative_path = resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise SnapshotError(f"Arquivo fora da raiz de serving: {path}") from error

    archive_path = (ARCHIVE_SERVING_ROOT / relative_path.as_posix()).as_posix()
    validate_archive_path(archive_path)
    return archive_path


def _validate_source_entry(source_root: Path, path: Path) -> None:
    """Rejeita links, caches, temporários e formatos inesperados."""
    if path.is_symlink():
        raise SnapshotError(f"Link simbólico não permitido: {path}")

    archive_path = archive_path_for_file(source_root, path)
    relative_parts = validate_archive_path(archive_path).parts[2:]

    if any(part in FORBIDDEN_COMPONENTS for part in relative_parts):
        raise SnapshotError(f"Diretório inesperado no serving: {archive_path}")

    if any(part.startswith(".") for part in relative_parts):
        raise SnapshotError(f"Caminho oculto não permitido: {archive_path}")

    if path.name in FORBIDDEN_NAMES or path.name.endswith(TEMPORARY_SUFFIXES):
        raise SnapshotError(f"Arquivo temporário não permitido: {archive_path}")

    if path.is_file() and path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise SnapshotError(f"Formato inesperado no serving: {archive_path}")


def inventory_serving(source_root: Path) -> list[FileRecord]:
    """Inventaria o serving em ordem determinística e calcula seus hashes."""
    if not source_root.exists():
        raise FileNotFoundError(f"Diretório de serving ausente: {source_root}")

    if not source_root.is_dir():
        raise SnapshotError(f"Raiz de serving não é diretório: {source_root}")

    entries = list(source_root.rglob("*"))

    for entry in entries:
        _validate_source_entry(source_root, entry)

        if not entry.is_file() and not entry.is_dir():
            raise SnapshotError(f"Entrada de tipo inesperado: {entry}")

    file_paths = [entry for entry in entries if entry.is_file()]

    if not file_paths:
        raise SnapshotError(f"Diretório de serving vazio: {source_root}")

    ordered_paths = sorted(
        file_paths,
        key=lambda path: archive_path_for_file(source_root, path),
    )

    records: list[FileRecord] = []

    for path in ordered_paths:
        digest, size = hash_file_stable(path)
        records.append(
            FileRecord(
                source_path=path,
                archive_path=archive_path_for_file(source_root, path),
                size_bytes=size,
                sha256=digest,
            )
        )

    return records


def build_manifest(
    records: Iterable[FileRecord],
    snapshot_version: str = SNAPSHOT_VERSION,
) -> dict[str, Any]:
    """Cria o manifest completo e determinístico do snapshot."""
    ordered_records = sorted(records, key=lambda record: record.archive_path)
    paths = [record.archive_path for record in ordered_records]

    if len(paths) != len(set(paths)):
        raise SnapshotError("O inventário contém caminhos duplicados")

    for path in paths:
        validate_archive_path(path)

    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot_version": snapshot_version,
        "period": SCIENTIFIC_PERIOD,
        "prediction_evaluation_period": PREDICTION_EVALUATION_PERIOD,
        "source_root": SOURCE_ROOT_LABEL,
        "methodology": {
            "prediction_horizons": ["H1", "H2", "H3", "H4"],
            "thresholds_contract": ("data/serving/prediction/metadata/model.json"),
        },
        "file_count": len(ordered_records),
        "total_size_bytes": sum(record.size_bytes for record in ordered_records),
        "files": [record.manifest_entry() for record in ordered_records],
    }


def manifest_bytes(manifest: dict[str, Any]) -> bytes:
    """Serializa o manifest sem valores ou metadata voláteis."""
    return (
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def checksums_bytes(manifest: dict[str, Any]) -> bytes:
    """Deriva SHA256SUMS das entradas do manifest, na mesma ordem."""
    lines = [f"{entry['sha256']}  {entry['path']}" for entry in manifest["files"]]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _zip_info(path: str) -> zipfile.ZipInfo:
    """Cria metadata ZIP normalizada para reprodução binária."""
    info = zipfile.ZipInfo(filename=path, date_time=ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = ZIP_MODE << 16
    return info


def _write_record(
    archive: zipfile.ZipFile,
    record: FileRecord,
) -> None:
    """Copia bytes originais para o ZIP e reconfirma sua identidade."""
    before = _stat_signature(record.source_path)
    digest = hashlib.sha256()
    size = 0

    with (
        record.source_path.open("rb") as source,
        archive.open(_zip_info(record.archive_path), "w") as destination,
    ):
        for chunk in iter(lambda: source.read(CHUNK_SIZE), b""):
            destination.write(chunk)
            digest.update(chunk)
            size += len(chunk)

    after = _stat_signature(record.source_path)

    if before != after:
        raise SnapshotError(
            f"Arquivo mudou durante o empacotamento: {record.source_path}"
        )

    if size != record.size_bytes or digest.hexdigest() != record.sha256:
        raise SnapshotError(f"Conteúdo divergiu do manifest: {record.archive_path}")


def create_snapshot_archive(
    archive_path: Path,
    records: list[FileRecord],
    manifest: dict[str, Any],
) -> None:
    """Cria ZIP determinístico sem sobrescrever snapshot existente."""
    if archive_path.exists():
        raise FileExistsError(f"Snapshot já existe e é imutável: {archive_path}")

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    payload = manifest_bytes(manifest)
    checksums = checksums_bytes(manifest)

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{archive_path.name}.",
        suffix=".tmp",
        dir=archive_path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)

    try:
        with zipfile.ZipFile(
            temporary_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            archive.writestr(
                _zip_info(MANIFEST_NAME),
                payload,
                compresslevel=9,
            )
            archive.writestr(
                _zip_info(CHECKSUMS_NAME),
                checksums,
                compresslevel=9,
            )

            for record in records:
                _write_record(archive, record)

        verify_snapshot_archive(temporary_path, manifest)
        temporary_path.replace(archive_path)
    finally:
        temporary_path.unlink(missing_ok=True)


def manifest_file_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Valida e indexa as entradas de arquivo do manifest."""
    files = manifest.get("files")

    if not isinstance(files, list):
        raise SnapshotError("Manifest sem lista de arquivos")

    paths = [entry.get("path") for entry in files if isinstance(entry, dict)]

    if len(paths) != len(files) or paths != sorted(paths):
        raise SnapshotError("Arquivos do manifest não estão em ordem lexicográfica")

    if len(paths) != len(set(paths)):
        raise SnapshotError("Manifest contém caminhos duplicados")

    indexed: dict[str, dict[str, Any]] = {}

    for entry in files:
        path = entry.get("path")

        if not isinstance(path, str):
            raise SnapshotError("Manifest contém caminho inválido")

        validate_archive_path(path)
        indexed[path] = entry

    expected_count = manifest.get("file_count")
    expected_size = manifest.get("total_size_bytes")
    calculated_size = sum(int(entry["size_bytes"]) for entry in files)

    if expected_count != len(files) or expected_size != calculated_size:
        raise SnapshotError("Totais do manifest são inconsistentes")

    return indexed


def validate_zip_entry(info: zipfile.ZipInfo) -> None:
    """Rejeita entradas ZIP capazes de escapar ou representar links."""
    if info.flag_bits & 0x1:
        raise SnapshotError(f"Entrada ZIP criptografada não permitida: {info.filename}")

    if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
        raise SnapshotError(f"Compressão ZIP não permitida: {info.filename}")

    if info.filename in {MANIFEST_NAME, CHECKSUMS_NAME}:
        if info.file_size > MAX_CONTROL_FILE_SIZE:
            raise SnapshotError(f"Arquivo de controle excede o limite: {info.filename}")
        return

    validate_archive_path(info.filename)

    file_type = (info.external_attr >> 16) & 0o170000

    if file_type == stat.S_IFLNK:
        raise SnapshotError(f"Symlink não permitido no ZIP: {info.filename}")

    if info.is_dir():
        raise SnapshotError(f"Diretório explícito inesperado no ZIP: {info.filename}")


def verify_snapshot_archive(
    archive_path: Path,
    expected_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Valida estrutura, manifest, SHA256SUMS e bytes do ZIP."""
    with zipfile.ZipFile(archive_path, mode="r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]

        if len(names) != len(set(names)):
            raise SnapshotError("Snapshot contém entradas duplicadas")

        for info in infos:
            validate_zip_entry(info)

        if MANIFEST_NAME not in names or CHECKSUMS_NAME not in names:
            raise SnapshotError("Snapshot não contém manifest e SHA256SUMS")

        if expected_manifest is not None:
            expected_indexed = manifest_file_map(expected_manifest)
            expected_names = [MANIFEST_NAME, CHECKSUMS_NAME, *expected_indexed]

            if names != expected_names:
                raise SnapshotError(
                    "Snapshot não contém exatamente os caminhos esperados"
                )

            infos_by_name = {info.filename: info for info in infos}

            if infos_by_name[MANIFEST_NAME].file_size != len(
                manifest_bytes(expected_manifest)
            ):
                raise SnapshotError("Tamanho declarado do manifest interno diverge")

            if infos_by_name[CHECKSUMS_NAME].file_size != len(
                checksums_bytes(expected_manifest)
            ):
                raise SnapshotError("Tamanho declarado de SHA256SUMS diverge")

            for path, entry in expected_indexed.items():
                if infos_by_name[path].file_size != entry["size_bytes"]:
                    raise SnapshotError(f"Tamanho declarado diverge no ZIP: {path}")

            declared_size = sum(
                infos_by_name[path].file_size for path in expected_indexed
            )

            if declared_size != expected_manifest["total_size_bytes"]:
                raise SnapshotError("Tamanho descompactado declarado diverge")

        try:
            manifest = json.loads(archive.read(MANIFEST_NAME).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SnapshotError("Manifest interno inválido") from error

        indexed = manifest_file_map(manifest)
        internal_names = [MANIFEST_NAME, CHECKSUMS_NAME, *indexed]

        if names != internal_names:
            raise SnapshotError("Snapshot não contém exatamente os caminhos esperados")

        if archive.read(MANIFEST_NAME) != manifest_bytes(manifest):
            raise SnapshotError("Serialização do manifest interno não é canônica")

        if archive.read(CHECKSUMS_NAME) != checksums_bytes(manifest):
            raise SnapshotError("SHA256SUMS diverge do manifest")

        if expected_manifest is not None and manifest != expected_manifest:
            raise SnapshotError("Manifest interno diverge do manifest esperado")

        for path, entry in indexed.items():
            with archive.open(path, mode="r") as source:
                digest, size = _hash_stream(source)

            if digest != entry["sha256"] or size != entry["size_bytes"]:
                raise SnapshotError(f"Hash ou tamanho divergente no ZIP: {path}")

    return manifest


def _safe_destination(root: Path, archive_path: str) -> Path:
    """Resolve destino de extração e garante confinamento na raiz."""
    if archive_path not in {MANIFEST_NAME, CHECKSUMS_NAME}:
        validate_archive_path(archive_path)

    destination = root.joinpath(*PurePosixPath(archive_path).parts)
    resolved_root = root.resolve()
    resolved_destination = destination.resolve()

    try:
        resolved_destination.relative_to(resolved_root)
    except ValueError as error:
        raise SnapshotError(
            f"Entrada escaparia da restauração: {archive_path}"
        ) from error

    return destination


def restore_snapshot(
    archive_path: Path,
    destination_root: Path,
    expected_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extrai o snapshot em diretório vazio com validação de caminhos."""
    if destination_root.exists() and any(destination_root.iterdir()):
        raise SnapshotError(
            f"Diretório de restauração não está vazio: {destination_root}"
        )

    destination_root.mkdir(parents=True, exist_ok=True)
    manifest = verify_snapshot_archive(archive_path, expected_manifest)

    with zipfile.ZipFile(archive_path, mode="r") as archive:
        for info in archive.infolist():
            validate_zip_entry(info)
            destination = _safe_destination(destination_root, info.filename)

            if destination.exists():
                raise SnapshotError(f"Restauração sobrescreveria: {destination}")

            destination.parent.mkdir(parents=True, exist_ok=True)

            with (
                archive.open(info, mode="r") as source,
                destination.open("xb") as target,
            ):
                shutil.copyfileobj(source, target, length=CHUNK_SIZE)

    validate_restored_snapshot(destination_root, manifest)
    return manifest


def validate_restored_snapshot(
    restored_root: Path,
    manifest: dict[str, Any],
) -> None:
    """Compara uma restauração com todos os hashes do manifest."""
    manifest_path = restored_root / MANIFEST_NAME
    checksums_path = restored_root / CHECKSUMS_NAME

    if manifest_path.read_bytes() != manifest_bytes(manifest):
        raise SnapshotError("Manifest restaurado diverge do snapshot")

    if checksums_path.read_bytes() != checksums_bytes(manifest):
        raise SnapshotError("SHA256SUMS restaurado diverge do snapshot")

    serving_root = restored_root / SOURCE_ROOT_LABEL
    restored_records = inventory_serving(serving_root)
    restored_manifest = build_manifest(
        restored_records,
        snapshot_version=str(manifest["snapshot_version"]),
    )

    if restored_manifest != manifest:
        raise SnapshotError("Serving restaurado diverge do manifest")


def _write_or_validate_manifest(path: Path, payload: bytes) -> None:
    """Grava o manifest inicial ou valida a versão já congelada."""
    if path.exists():
        if path.read_bytes() != payload:
            raise SnapshotError(f"Manifest versionado diverge do serving: {path}")
        return

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("xb") as output:
        output.write(payload)


def _write_checksum_sidecar(path: Path, digest: str, archive_name: str) -> None:
    """Registra o hash externo ao lado do artefato ignorado."""
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(f"{digest}  {archive_name}\n")


def package_snapshot(
    source_root: Path,
    manifest_path: Path,
    archive_path: Path,
    snapshot_version: str = SNAPSHOT_VERSION,
    validate_restore: bool = True,
) -> SnapshotResult:
    """Executa inventário, empacotamento e restauração temporária."""
    started = time.monotonic()
    checksum_path = archive_path.with_suffix(archive_path.suffix + ".sha256")

    if checksum_path.exists():
        raise FileExistsError(f"Checksum externo já existe: {checksum_path}")

    records = inventory_serving(source_root)
    manifest = build_manifest(records, snapshot_version=snapshot_version)
    payload = manifest_bytes(manifest)

    _write_or_validate_manifest(manifest_path, payload)
    create_snapshot_archive(archive_path, records, manifest)

    archive_digest, archive_size = hash_file_stable(archive_path)
    _write_checksum_sidecar(checksum_path, archive_digest, archive_path.name)

    current_manifest = build_manifest(
        inventory_serving(source_root),
        snapshot_version=snapshot_version,
    )

    if current_manifest != manifest:
        raise SnapshotError("Serving mudou durante o empacotamento")

    if validate_restore:
        with tempfile.TemporaryDirectory(prefix="dengue-serving-restore-") as temporary:
            restore_snapshot(archive_path, Path(temporary), manifest)

    return SnapshotResult(
        archive_path=archive_path,
        manifest_path=manifest_path,
        checksum_path=checksum_path,
        file_count=int(manifest["file_count"]),
        total_size_bytes=int(manifest["total_size_bytes"]),
        archive_size_bytes=archive_size,
        archive_sha256=archive_digest,
        elapsed_seconds=time.monotonic() - started,
    )


def parse_args() -> argparse.Namespace:
    """Lê os caminhos explícitos do empacotamento local."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_ARCHIVE_PATH)
    parser.add_argument("--snapshot-version", default=SNAPSHOT_VERSION)
    return parser.parse_args()


def main() -> None:
    """Gera o snapshot real e imprime um resumo legível por máquina."""
    args = parse_args()
    result = package_snapshot(
        source_root=args.source,
        manifest_path=args.manifest,
        archive_path=args.output,
        snapshot_version=args.snapshot_version,
    )
    print(
        json.dumps(
            {
                "snapshot_version": args.snapshot_version,
                "archive": str(result.archive_path),
                "manifest": str(result.manifest_path),
                "checksum": str(result.checksum_path),
                "file_count": result.file_count,
                "total_size_bytes": result.total_size_bytes,
                "archive_size_bytes": result.archive_size_bytes,
                "archive_sha256": result.archive_sha256,
                "elapsed_seconds": round(result.elapsed_seconds, 3),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
