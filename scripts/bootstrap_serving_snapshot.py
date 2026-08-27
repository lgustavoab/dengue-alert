"""Verifica e instala com segurança um snapshot científico de serving."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from package_serving_snapshot import (
    CHUNK_SIZE,
    SCHEMA_VERSION,
    SnapshotError,
    build_manifest,
    hash_file_stable,
    inventory_serving,
    manifest_bytes,
    manifest_file_map,
    restore_snapshot,
    verify_snapshot_archive,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DESCRIPTOR_PATH = (
    PROJECT_ROOT / "artifacts" / "serving" / "serving-v1.0.0-distribution.json"
)
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "artifacts" / "serving" / "serving-v1.0.0.json"
DEFAULT_DESTINATION = PROJECT_ROOT / "data" / "serving"

HTTP_TIMEOUT_SECONDS = 30
USER_AGENT = "DengueAlert-Snapshot-Bootstrap/1.0"
SYNC_SCRIPTS = (
    "sync_web_serving.py",
    "sync_web_geography.py",
)


class BootstrapError(SnapshotError):
    """Indica falha segura antes ou durante a instalação do snapshot."""


@dataclass(frozen=True)
class DistributionDescriptor:
    """Identidade externa confiável do asset a ser instalado."""

    schema_version: str
    snapshot_version: str
    asset_name: str
    archive_sha256: str
    archive_size_bytes: int
    scientific_file_count: int
    uncompressed_size_bytes: int


@dataclass(frozen=True)
class BootstrapResult:
    """Resumo verificável de uma execução do bootstrap."""

    status: str
    snapshot_version: str
    archive_sha256: str
    archive_size_bytes: int
    scientific_file_count: int
    uncompressed_size_bytes: int
    destination: Path
    synced_web: bool


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    """Carrega JSON UTF-8 e exige um objeto na raiz."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BootstrapError(f"{label} inválido: {path}") from error

    if not isinstance(payload, dict):
        raise BootstrapError(f"{label} não é objeto JSON: {path}")

    return payload


def load_distribution_descriptor(path: Path) -> DistributionDescriptor:
    """Carrega e valida tipos básicos do descriptor externo."""
    payload = _load_json_object(path, "Descriptor")
    required_fields = {
        "schema_version",
        "snapshot_version",
        "asset_name",
        "archive_sha256",
        "archive_size_bytes",
        "scientific_file_count",
        "uncompressed_size_bytes",
    }

    if set(payload) != required_fields:
        raise BootstrapError("Campos do descriptor estão ausentes ou inesperados")

    string_fields = (
        "schema_version",
        "snapshot_version",
        "asset_name",
        "archive_sha256",
    )

    if any(not isinstance(payload[field], str) for field in string_fields):
        raise BootstrapError("Descriptor contém campo textual inválido")

    integer_fields = (
        "archive_size_bytes",
        "scientific_file_count",
        "uncompressed_size_bytes",
    )

    if any(
        not isinstance(payload[field], int)
        or isinstance(payload[field], bool)
        or payload[field] <= 0
        for field in integer_fields
    ):
        raise BootstrapError("Descriptor contém tamanho ou contagem inválida")

    asset_name = payload["asset_name"]

    if (
        not asset_name
        or asset_name in {".", ".."}
        or "/" in asset_name
        or "\\" in asset_name
    ):
        raise BootstrapError("Nome de asset inválido no descriptor")

    archive_sha256 = payload["archive_sha256"]

    if re.fullmatch(r"[0-9a-f]{64}", archive_sha256) is None:
        raise BootstrapError("SHA-256 externo inválido no descriptor")

    return DistributionDescriptor(
        schema_version=payload["schema_version"],
        snapshot_version=payload["snapshot_version"],
        asset_name=asset_name,
        archive_sha256=archive_sha256,
        archive_size_bytes=payload["archive_size_bytes"],
        scientific_file_count=payload["scientific_file_count"],
        uncompressed_size_bytes=payload["uncompressed_size_bytes"],
    )


def load_bootstrap_metadata(
    descriptor_path: Path,
    manifest_path: Path,
) -> tuple[DistributionDescriptor, dict[str, Any]]:
    """Cruza descriptor externo e manifest completo versionado."""
    descriptor = load_distribution_descriptor(descriptor_path)
    manifest = _load_json_object(manifest_path, "Manifest versionado")
    manifest_file_map(manifest)

    if descriptor.schema_version != SCHEMA_VERSION:
        raise BootstrapError("Schema do descriptor não suportado")

    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise BootstrapError("Schema do manifest versionado não suportado")

    comparisons = {
        "snapshot_version": manifest.get("snapshot_version"),
        "scientific_file_count": manifest.get("file_count"),
        "uncompressed_size_bytes": manifest.get("total_size_bytes"),
    }

    for field, manifest_value in comparisons.items():
        if getattr(descriptor, field) != manifest_value:
            raise BootstrapError(f"Descriptor diverge do manifest em {field}")

    return descriptor, manifest


def validate_external_archive(
    archive_path: Path,
    descriptor: DistributionDescriptor,
) -> None:
    """Valida tamanho e SHA-256 externos antes de abrir o ZIP."""
    if not archive_path.is_file():
        raise FileNotFoundError(f"Snapshot local ausente: {archive_path}")

    digest, size = hash_file_stable(archive_path)

    if size != descriptor.archive_size_bytes:
        raise BootstrapError(
            "Tamanho externo divergente: "
            f"esperado {descriptor.archive_size_bytes}, obtido {size}"
        )

    if digest != descriptor.archive_sha256:
        raise BootstrapError(
            "SHA-256 externo divergente: "
            f"esperado {descriptor.archive_sha256}, obtido {digest}"
        )


def _validate_https_url(url: str) -> None:
    """Aceita somente URL HTTPS absoluta com host explícito."""
    parsed = urlparse(url)

    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise BootstrapError("A fonte remota deve usar uma URL HTTPS absoluta")


def _response_status(response: BinaryIO) -> int:
    """Obtém status HTTP de respostas reais ou simuladas."""
    status = getattr(response, "status", None)

    if not isinstance(status, int):
        raise BootstrapError("Resposta remota sem status HTTP válido")

    return status


def download_https_snapshot(
    url: str,
    destination: Path,
    descriptor: DistributionDescriptor,
    opener: Callable[..., BinaryIO] = urlopen,
) -> None:
    """Baixa o asset por streaming e remove parciais em qualquer falha."""
    _validate_https_url(url)

    if destination.exists():
        raise FileExistsError(f"Destino temporário já existe: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(
        url,
        headers={
            "Accept": "application/zip",
            "User-Agent": USER_AGENT,
        },
    )
    digest = hashlib.sha256()
    size = 0

    try:
        with opener(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            status = _response_status(response)

            if status < 200 or status >= 300:
                raise BootstrapError(f"Download falhou com HTTP {status}")

            final_url = response.geturl()
            _validate_https_url(final_url)

            content_length = response.headers.get("Content-Length")

            if content_length is not None:
                try:
                    declared_length = int(content_length)
                except ValueError as error:
                    raise BootstrapError("Content-Length remoto inválido") from error

                if declared_length != descriptor.archive_size_bytes:
                    raise BootstrapError("Content-Length remoto diverge do descriptor")

            with destination.open("xb") as output:
                for chunk in iter(lambda: response.read(CHUNK_SIZE), b""):
                    size += len(chunk)

                    if size > descriptor.archive_size_bytes:
                        raise BootstrapError("Download excede o tamanho esperado")

                    digest.update(chunk)
                    output.write(chunk)

        if size != descriptor.archive_size_bytes:
            raise BootstrapError("Download terminou com tamanho divergente")

        if digest.hexdigest() != descriptor.archive_sha256:
            raise BootstrapError("Download terminou com SHA-256 divergente")
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def installed_serving_status(
    destination: Path,
    expected_manifest: dict[str, Any],
) -> str:
    """Classifica o destino como ausente, íntegro ou divergente."""
    if not destination.exists():
        return "missing"

    if destination.is_symlink() or not destination.is_dir():
        return "different"

    try:
        current_manifest = build_manifest(
            inventory_serving(destination),
            snapshot_version=str(expected_manifest["snapshot_version"]),
        )
    except (OSError, SnapshotError):
        return "different"

    if manifest_bytes(current_manifest) == manifest_bytes(expected_manifest):
        return "valid"

    return "different"


def promote_restored_serving(
    restored_root: Path,
    destination: Path,
    replace: bool,
) -> str:
    """Promove diretório validado com swap recuperável no Windows."""
    restored_serving = restored_root / "data" / "serving"

    if not restored_serving.is_dir():
        raise BootstrapError("Restauração validada não contém data/serving")

    destination.parent.mkdir(parents=True, exist_ok=True)

    if not destination.exists():
        restored_serving.replace(destination)
        return "installed"

    if not replace:
        raise BootstrapError("Destino existente exige --replace")

    backup_path = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.backup-",
            dir=destination.parent,
        )
    )
    backup_path.rmdir()
    destination.replace(backup_path)

    try:
        restored_serving.replace(destination)
    except Exception:
        if destination.exists():
            shutil.rmtree(destination)
        backup_path.replace(destination)
        raise

    shutil.rmtree(backup_path)
    return "replaced"


def run_web_sync(project_root: Path, destination: Path) -> None:
    """Executa os dois syncs existentes sem replicar sua lógica."""
    expected_destination = (project_root / "data" / "serving").resolve()

    if destination.resolve() != expected_destination:
        raise BootstrapError(
            "--sync-web exige destino igual a <project-root>/data/serving"
        )

    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["PYTHONUTF8"] = "1"

    for script_name in SYNC_SCRIPTS:
        script_path = project_root / "scripts" / script_name

        if not script_path.is_file():
            raise FileNotFoundError(f"Script de sync ausente: {script_path}")

        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=project_root,
            env=environment,
            check=True,
        )


def _obtain_archive(
    stack: ExitStack,
    local_archive: Path | None,
    url: str | None,
    descriptor: DistributionDescriptor,
) -> Path:
    """Seleciona arquivo local ou baixa cópia temporária HTTPS."""
    if (local_archive is None) == (url is None):
        raise BootstrapError("Informe exatamente uma fonte: --archive ou --url")

    if local_archive is not None:
        validate_external_archive(local_archive, descriptor)
        return local_archive

    temporary = Path(
        stack.enter_context(
            tempfile.TemporaryDirectory(prefix="dengue-serving-download-")
        )
    )
    downloaded = temporary / descriptor.asset_name
    download_https_snapshot(str(url), downloaded, descriptor)
    return downloaded


def bootstrap_snapshot(
    *,
    descriptor_path: Path,
    manifest_path: Path,
    destination: Path,
    project_root: Path,
    local_archive: Path | None = None,
    url: str | None = None,
    replace: bool = False,
    verify_only: bool = False,
    sync_web: bool = False,
) -> BootstrapResult:
    """Verifica, instala e opcionalmente sincroniza um snapshot."""
    if verify_only and replace:
        raise BootstrapError("--verify não pode ser combinado com --replace")

    if verify_only and sync_web:
        raise BootstrapError("--verify não pode ser combinado com --sync-web")

    descriptor, manifest = load_bootstrap_metadata(descriptor_path, manifest_path)

    with ExitStack() as stack:
        archive_path = _obtain_archive(
            stack,
            local_archive,
            url,
            descriptor,
        )
        verify_snapshot_archive(archive_path, manifest)
        destination_status = installed_serving_status(destination, manifest)

        if verify_only:
            if destination_status == "different":
                raise BootstrapError("Serving instalado diverge do snapshot esperado")

            status = (
                "verified-installed"
                if destination_status == "valid"
                else "verified-archive"
            )
        elif destination_status == "valid":
            status = "already-valid"
        else:
            if destination_status == "different" and not replace:
                raise BootstrapError(
                    "Serving existente diverge; use --replace para substituí-lo"
                )

            destination.parent.mkdir(parents=True, exist_ok=True)
            staging_root = Path(
                stack.enter_context(
                    tempfile.TemporaryDirectory(
                        prefix=f".{destination.name}.staging-",
                        dir=destination.parent,
                    )
                )
            )
            restore_snapshot(archive_path, staging_root, manifest)
            status = promote_restored_serving(
                staging_root,
                destination,
                replace=replace,
            )

        synced_web = False

        if sync_web:
            run_web_sync(project_root, destination)
            synced_web = True

    return BootstrapResult(
        status=status,
        snapshot_version=descriptor.snapshot_version,
        archive_sha256=descriptor.archive_sha256,
        archive_size_bytes=descriptor.archive_size_bytes,
        scientific_file_count=descriptor.scientific_file_count,
        uncompressed_size_bytes=descriptor.uncompressed_size_bytes,
        destination=destination,
        synced_web=synced_web,
    )


def parse_args() -> argparse.Namespace:
    """Define a interface local/remota, verify, replace e sync."""
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--archive", type=Path)
    source.add_argument("--url")
    parser.add_argument("--descriptor", type=Path, default=DEFAULT_DESCRIPTOR_PATH)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--sync-web", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Executa o bootstrap e imprime resultado JSON estável."""
    args = parse_args()
    destination = args.destination or args.project_root / "data" / "serving"
    result = bootstrap_snapshot(
        descriptor_path=args.descriptor,
        manifest_path=args.manifest,
        destination=destination,
        project_root=args.project_root,
        local_archive=args.archive,
        url=args.url,
        replace=args.replace,
        verify_only=args.verify,
        sync_web=args.sync_web,
    )
    print(
        json.dumps(
            {
                "archive_sha256": result.archive_sha256,
                "archive_size_bytes": result.archive_size_bytes,
                "destination": str(result.destination),
                "scientific_file_count": result.scientific_file_count,
                "snapshot_version": result.snapshot_version,
                "status": result.status,
                "synced_web": result.synced_web,
                "uncompressed_size_bytes": result.uncompressed_size_bytes,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
