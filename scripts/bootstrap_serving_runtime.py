"""Instala e valida localmente um archive do serving runtime compacto."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
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
            synced_web=sync_web,
        )

    if archive_path is None:
        raise RuntimeBootstrapError(
            "Runtime ausente; informe --archive local. A fonte remota será ativada "
            "somente após a publicação autorizada do runtime."
        )

    archive_path = archive_path.resolve(strict=True)
    archive_sha256, archive_size = validate_archive_sidecar(archive_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

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
        restored_root.replace(destination)

    validate_runtime_tree(destination, manifest)

    if sync_web:
        run_web_sync(project_root, destination)

    return RuntimeBootstrapResult(
        status="installed",
        destination=destination,
        archive_sha256=archive_sha256,
        archive_size_bytes=archive_size,
        synced_web=sync_web,
    )


def parse_args() -> argparse.Namespace:
    """Lê archive local e destinos explícitos."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--destination", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--sync-web", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Executa bootstrap local sem qualquer acesso remoto."""
    args = parse_args()
    result = bootstrap_runtime(
        archive_path=args.archive,
        manifest_path=args.manifest,
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
