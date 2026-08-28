"""Instala e valida localmente um archive do serving runtime compacto."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from package_serving_runtime import (
    DEFAULT_MANIFEST_PATH,
    DEFAULT_OUTPUT_ROOT,
    RUNTIME_VERSION,
    RuntimePackagingError,
    deterministic_json_bytes,
    hash_file_stable,
    manifest_file_map,
    validate_runtime_tree,
    verify_runtime_archive,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DISTRIBUTION_PATH = (
    PROJECT_ROOT / "artifacts" / "serving" / "serving-runtime-v1.0.0-distribution.json"
)
SOURCE_SNAPSHOT_VERSION = "serving-v1.0.0"
RELEASE_BASE_URL = (
    f"https://github.com/lgustavoab/dengue-alert/releases/download/{RUNTIME_VERSION}"
)
DOWNLOAD_CHUNK_SIZE = 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 300
SYNC_SCRIPTS = (
    "sync_web_serving.py",
    "sync_web_geography.py",
)


class RuntimeBootstrapError(RuntimePackagingError):
    """Indica falha segura na instalação local do runtime."""


@dataclass(frozen=True)
class RuntimeBootstrapResult:
    """Resume uma instalação ou validação local."""

    status: str
    destination: Path
    archive_sha256: str | None
    archive_size_bytes: int | None
    source: str
    synced_web: bool


def load_expected_manifest(path: Path) -> dict[str, Any]:
    """Carrega o manifest técnico versionado."""
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeBootstrapError(f"Manifest runtime inválido: {path}") from error

    if not isinstance(manifest, dict):
        raise RuntimeBootstrapError("Manifest runtime não é objeto JSON")

    if manifest.get("runtime_version") != RUNTIME_VERSION:
        raise RuntimeBootstrapError("Versão do manifest runtime é incompatível")

    manifest_file_map(manifest)

    if deterministic_json_bytes(manifest) != path.read_bytes():
        raise RuntimeBootstrapError("Manifest versionado não é determinístico")

    return manifest


def validate_archive_sidecar(archive_path: Path) -> tuple[str, int]:
    """Valida o SHA-256 externo criado junto do archive local."""
    sidecar = archive_path.with_suffix(archive_path.suffix + ".sha256")

    try:
        line = sidecar.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, UnicodeDecodeError) as error:
        raise RuntimeBootstrapError(f"Checksum externo ausente: {sidecar}") from error

    parts = line.split("  ")

    if len(parts) != 2 or parts[1] != archive_path.name:
        raise RuntimeBootstrapError("Checksum externo possui formato inválido")

    expected_digest = parts[0]

    if len(expected_digest) != 64 or any(
        character not in "0123456789abcdef" for character in expected_digest
    ):
        raise RuntimeBootstrapError("SHA-256 externo inválido")

    digest, size = hash_file_stable(archive_path)

    if digest != expected_digest:
        raise RuntimeBootstrapError("SHA-256 externo diverge do archive runtime")

    return digest, size


def load_distribution_descriptor(path: Path) -> dict[str, Any]:
    """Carrega e valida o descriptor imutável da Release runtime."""
    try:
        descriptor = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeBootstrapError(
            f"Descriptor de distribuição inválido: {path}"
        ) from error

    expected_values = {
        "schema_version": "1.0",
        "runtime_version": RUNTIME_VERSION,
        "source_snapshot_version": SOURCE_SNAPSHOT_VERSION,
        "asset_name": f"{RUNTIME_VERSION}.zip",
        "checksum_asset_name": f"{RUNTIME_VERSION}.zip.sha256",
    }

    if not isinstance(descriptor, dict):
        raise RuntimeBootstrapError("Descriptor de distribuição não é objeto JSON")

    for field, expected in expected_values.items():
        if descriptor.get(field) != expected:
            raise RuntimeBootstrapError(
                f"Descriptor de distribuição incompatível: {field}"
            )

    for field in (
        "archive_size_bytes",
        "checksum_size_bytes",
        "file_count",
        "uncompressed_size_bytes",
    ):
        value = descriptor.get(field)

        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise RuntimeBootstrapError(
                f"Descriptor possui valor numérico inválido: {field}"
            )

    for field in ("archive_sha256", "checksum_sha256"):
        value = descriptor.get(field)

        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise RuntimeBootstrapError(f"Descriptor possui SHA-256 inválido: {field}")

    expected_urls = {
        "download_url": f"{RELEASE_BASE_URL}/{descriptor['asset_name']}",
        "checksum_url": f"{RELEASE_BASE_URL}/{descriptor['checksum_asset_name']}",
    }

    for field, expected in expected_urls.items():
        value = descriptor.get(field)

        if value != expected or urllib.parse.urlparse(value).scheme != "https":
            raise RuntimeBootstrapError(f"Descriptor possui URL inválida: {field}")

    return descriptor


def download_verified_file(
    url: str,
    destination: Path,
    expected_size: int,
    expected_sha256: str,
) -> None:
    """Baixa um asset HTTPS com limite exato e validação SHA-256."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Dengue-Alert-Runtime-Bootstrap/1.0"},
    )
    digest = hashlib.sha256()
    size = 0

    try:
        with (
            urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as source,
            destination.open("xb") as target,
        ):
            content_length = source.headers.get("Content-Length")

            if content_length is not None and int(content_length) != expected_size:
                raise RuntimeBootstrapError(
                    f"Tamanho HTTP divergente para {destination.name}"
                )

            while chunk := source.read(DOWNLOAD_CHUNK_SIZE):
                size += len(chunk)

                if size > expected_size:
                    raise RuntimeBootstrapError(
                        f"Download excedeu o tamanho esperado: {destination.name}"
                    )

                digest.update(chunk)
                target.write(chunk)
    except RuntimeBootstrapError:
        destination.unlink(missing_ok=True)
        raise
    except (OSError, urllib.error.URLError, ValueError) as error:
        destination.unlink(missing_ok=True)
        raise RuntimeBootstrapError(
            f"Falha ao baixar runtime: {destination.name}"
        ) from error

    if size != expected_size or digest.hexdigest() != expected_sha256:
        destination.unlink(missing_ok=True)
        raise RuntimeBootstrapError(
            f"Tamanho ou SHA-256 remoto divergente: {destination.name}"
        )


def download_runtime_release(
    descriptor: dict[str, Any],
    destination: Path,
) -> Path:
    """Baixa ZIP e sidecar públicos para uma staging efêmera."""
    archive_path = destination / descriptor["asset_name"]
    sidecar_path = destination / descriptor["checksum_asset_name"]
    download_verified_file(
        descriptor["download_url"],
        archive_path,
        descriptor["archive_size_bytes"],
        descriptor["archive_sha256"],
    )
    download_verified_file(
        descriptor["checksum_url"],
        sidecar_path,
        descriptor["checksum_size_bytes"],
        descriptor["checksum_sha256"],
    )
    digest, size = validate_archive_sidecar(archive_path)

    if (
        digest != descriptor["archive_sha256"]
        or size != descriptor["archive_size_bytes"]
    ):
        raise RuntimeBootstrapError("Sidecar remoto diverge do descriptor")

    return archive_path


def validate_distribution_inventory(
    runtime_root: Path,
    descriptor: dict[str, Any],
) -> None:
    """Confirma o inventário extraído declarado pela distribuição."""
    files = [path for path in runtime_root.rglob("*") if path.is_file()]
    total_size = sum(path.stat().st_size for path in files)

    if len(files) != descriptor["file_count"]:
        raise RuntimeBootstrapError(
            "Quantidade extraída diverge do descriptor de distribuição"
        )

    if total_size != descriptor["uncompressed_size_bytes"]:
        raise RuntimeBootstrapError(
            "Tamanho extraído diverge do descriptor de distribuição"
        )


def _safe_extract_destination(root: Path, archive_name: str) -> Path:
    """Resolve uma entrada ZIP sem permitir escape da staging."""
    if "\\" in archive_name:
        raise RuntimeBootstrapError(f"Caminho ZIP inválido: {archive_name}")

    relative = PurePosixPath(archive_name)

    if (
        relative.is_absolute()
        or "." in relative.parts
        or ".." in relative.parts
        or not relative.parts
        or relative.parts[0] != RUNTIME_VERSION
    ):
        raise RuntimeBootstrapError(f"Caminho ZIP inseguro: {archive_name}")

    destination = root.joinpath(*relative.parts)
    resolved_root = root.resolve()
    resolved_destination = destination.resolve()

    try:
        resolved_destination.relative_to(resolved_root)
    except ValueError as error:
        raise RuntimeBootstrapError(
            f"Entrada ZIP escaparia da staging: {archive_name}"
        ) from error

    return destination


def restore_runtime_archive(
    archive_path: Path,
    staging_parent: Path,
    manifest: dict[str, Any],
) -> Path:
    """Extrai manualmente um archive já validado para staging vazia."""
    verify_runtime_archive(archive_path, manifest)

    if staging_parent.exists() and any(staging_parent.iterdir()):
        raise RuntimeBootstrapError(f"Staging não está vazia: {staging_parent}")

    staging_parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path, mode="r") as archive:
        for info in archive.infolist():
            destination = _safe_extract_destination(staging_parent, info.filename)
            destination.parent.mkdir(parents=True, exist_ok=True)

            if destination.exists():
                raise RuntimeBootstrapError(
                    f"Extração sobrescreveria arquivo: {destination}"
                )

            with (
                archive.open(info, mode="r") as source,
                destination.open("xb") as target,
            ):
                shutil.copyfileobj(source, target)

    runtime_root = staging_parent / RUNTIME_VERSION
    validate_runtime_tree(runtime_root, manifest)
    return runtime_root


def run_web_sync(project_root: Path, runtime_root: Path) -> None:
    """Reconstrói os 27 assets públicos a partir da allowlist do runtime."""
    scripts_root = project_root / "scripts"
    environment = {
        **os.environ,
        "DENGUE_SERVING_SOURCE_ROOT": str(runtime_root),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }

    for script_name in SYNC_SCRIPTS:
        subprocess.run(
            [sys.executable, str(scripts_root / script_name)],
            cwd=project_root,
            env=environment,
            check=True,
        )


def bootstrap_runtime(
    archive_path: Path | None,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    distribution_path: Path = DEFAULT_DISTRIBUTION_PATH,
    destination: Path = DEFAULT_OUTPUT_ROOT,
    project_root: Path = PROJECT_ROOT,
    sync_web: bool = False,
) -> RuntimeBootstrapResult:
    """Valida runtime existente ou instala um archive local imutável."""
    manifest = load_expected_manifest(manifest_path)

    if destination.exists():
        validate_runtime_tree(destination, manifest)

        if sync_web:
            run_web_sync(project_root, destination)

        return RuntimeBootstrapResult(
            status="already-valid",
            destination=destination,
            archive_sha256=None,
            archive_size_bytes=None,
            source="existing",
            synced_web=sync_web,
        )

    destination.parent.mkdir(parents=True, exist_ok=True)

    if archive_path is None:
        descriptor = load_distribution_descriptor(distribution_path)

        with tempfile.TemporaryDirectory(
            prefix=f".{RUNTIME_VERSION}-download.",
            dir=destination.parent,
        ) as temporary:
            archive_path = download_runtime_release(
                descriptor,
                Path(temporary),
            )
            return install_runtime_archive(
                archive_path,
                manifest,
                destination,
                project_root,
                sync_web,
                source="remote",
                distribution_descriptor=descriptor,
            )

    return install_runtime_archive(
        archive_path.resolve(strict=True),
        manifest,
        destination,
        project_root,
        sync_web,
        source="local",
        distribution_descriptor=None,
    )


def install_runtime_archive(
    archive_path: Path,
    manifest: dict[str, Any],
    destination: Path,
    project_root: Path,
    sync_web: bool,
    source: str,
    distribution_descriptor: dict[str, Any] | None,
) -> RuntimeBootstrapResult:
    """Valida e instala um archive local ou baixado em staging."""
    archive_sha256, archive_size = validate_archive_sidecar(archive_path)

    with tempfile.TemporaryDirectory(
        prefix=f".{RUNTIME_VERSION}-restore.",
        dir=destination.parent,
    ) as temporary:
        staging_parent = Path(temporary)
        restored_root = restore_runtime_archive(
            archive_path,
            staging_parent,
            manifest,
        )

        if distribution_descriptor is not None:
            validate_distribution_inventory(
                restored_root,
                distribution_descriptor,
            )

        restored_root.replace(destination)

    validate_runtime_tree(destination, manifest)

    if sync_web:
        run_web_sync(project_root, destination)

    return RuntimeBootstrapResult(
        status="installed",
        destination=destination,
        archive_sha256=archive_sha256,
        archive_size_bytes=archive_size,
        source=source,
        synced_web=sync_web,
    )


def parse_args() -> argparse.Namespace:
    """Lê archive local e destinos explícitos."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument(
        "--distribution",
        type=Path,
        default=DEFAULT_DISTRIBUTION_PATH,
    )
    parser.add_argument("--destination", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--sync-web", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Executa bootstrap local sem qualquer acesso remoto."""
    args = parse_args()
    result = bootstrap_runtime(
        archive_path=args.archive,
        manifest_path=args.manifest,
        distribution_path=args.distribution,
        destination=args.destination,
        project_root=PROJECT_ROOT,
        sync_web=args.sync_web,
    )
    print(
        json.dumps(
            {
                "archive_sha256": result.archive_sha256,
                "archive_size_bytes": result.archive_size_bytes,
                "destination": str(result.destination),
                "runtime_version": RUNTIME_VERSION,
                "source": result.source,
                "status": result.status,
                "synced_web": result.synced_web,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
