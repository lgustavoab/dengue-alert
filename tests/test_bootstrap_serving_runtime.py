"""Testes do bootstrap local do serving runtime compacto."""

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = PROJECT_ROOT / "scripts" / "package_serving_runtime.py"
BOOTSTRAP_SCRIPT = PROJECT_ROOT / "scripts" / "bootstrap_serving_runtime.py"
SNAPSHOT_SCRIPT = PROJECT_ROOT / "scripts" / "package_serving_snapshot.py"
SYNC_SCRIPT = PROJECT_ROOT / "scripts" / "sync_web_serving.py"


def load_script(name: str, path: Path) -> ModuleType:
    """Carrega script como módulo registrado para suportar dataclasses."""
    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Não foi possível carregar o script: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


load_script("package_serving_snapshot", SNAPSHOT_SCRIPT)
load_script("sync_web_serving", SYNC_SCRIPT)
runtime = load_script("package_serving_runtime", PACKAGE_SCRIPT)
bootstrap = load_script("bootstrap_serving_runtime", BOOTSTRAP_SCRIPT)


def create_bundle(tmp_path: Path) -> dict[str, Path]:
    """Cria archive runtime mínimo, íntegro e determinístico."""
    runtime_root = tmp_path / "source" / runtime.RUNTIME_VERSION
    payload_path = runtime_root / "historical" / "municipalities.ndjson"
    payload_path.parent.mkdir(parents=True)
    payload_path.write_bytes(b'{"codigo_ibge_7":"1111111"}\n')
    payload = payload_path.read_bytes()
    record = runtime.RuntimeFile(
        path=payload_path.relative_to(runtime_root).as_posix(),
        size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        role="historical-municipality-pack",
    )
    manifest = runtime.build_manifest(
        [record],
        {
            "digest_algorithm": "test",
            "digest": "a" * 64,
            "file_count": 1,
            "total_size_bytes": len(payload),
        },
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_payload = runtime.deterministic_json_bytes(manifest)
    manifest_path.write_bytes(manifest_payload)
    (runtime_root / runtime.MANIFEST_NAME).write_bytes(manifest_payload)
    (runtime_root / runtime.CHECKSUMS_NAME).write_bytes(
        runtime.checksums_bytes(manifest)
    )
    archive_path = tmp_path / f"{runtime.RUNTIME_VERSION}.zip"
    runtime.create_runtime_archive(runtime_root, archive_path, manifest)
    digest, _ = runtime.hash_file_stable(archive_path)
    archive_path.with_suffix(".zip.sha256").write_text(
        f"{digest}  {archive_path.name}\n",
        encoding="utf-8",
    )
    return {
        "archive": archive_path,
        "manifest": manifest_path,
        "runtime_root": runtime_root,
    }


def create_distribution_descriptor(
    tmp_path: Path,
    bundle: dict[str, Path],
) -> Path:
    """Cria descriptor mínimo coerente com o bundle sintético."""
    archive = bundle["archive"]
    sidecar = archive.with_suffix(".zip.sha256")
    archive_sha256, archive_size = runtime.hash_file_stable(archive)
    checksum_sha256, checksum_size = runtime.hash_file_stable(sidecar)
    descriptor = {
        "archive_sha256": archive_sha256,
        "archive_size_bytes": archive_size,
        "asset_name": f"{runtime.RUNTIME_VERSION}.zip",
        "checksum_asset_name": f"{runtime.RUNTIME_VERSION}.zip.sha256",
        "checksum_sha256": checksum_sha256,
        "checksum_size_bytes": checksum_size,
        "checksum_url": (
            f"{bootstrap.RELEASE_BASE_URL}/{runtime.RUNTIME_VERSION}.zip.sha256"
        ),
        "download_url": (f"{bootstrap.RELEASE_BASE_URL}/{runtime.RUNTIME_VERSION}.zip"),
        "file_count": 3,
        "runtime_version": runtime.RUNTIME_VERSION,
        "schema_version": "1.0",
        "source_snapshot_version": bootstrap.SOURCE_SNAPSHOT_VERSION,
        "uncompressed_size_bytes": sum(
            path.stat().st_size
            for path in bundle["runtime_root"].rglob("*")
            if path.is_file()
        ),
    }
    descriptor_path = tmp_path / "distribution.json"
    descriptor_path.write_text(
        json.dumps(descriptor, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return descriptor_path


def test_local_archive_is_installed_and_validated(tmp_path: Path) -> None:
    """Bootstrap deve instalar somente a árvore interna validada."""
    bundle = create_bundle(tmp_path)
    destination = tmp_path / "workspace" / "dist" / runtime.RUNTIME_VERSION
    result = bootstrap.bootstrap_runtime(
        archive_path=bundle["archive"],
        manifest_path=bundle["manifest"],
        destination=destination,
        project_root=tmp_path / "workspace",
    )

    assert result.status == "installed"
    assert result.source == "local"
    assert destination.is_dir()
    runtime.validate_runtime_tree(
        destination,
        json.loads(bundle["manifest"].read_text(encoding="utf-8")),
    )


def test_valid_existing_runtime_is_not_replaced(tmp_path: Path) -> None:
    """Runtime íntegro deve ser reconhecido sem nova extração."""
    bundle = create_bundle(tmp_path)
    destination = bundle["runtime_root"]
    marker = destination.stat().st_mtime_ns
    result = bootstrap.bootstrap_runtime(
        archive_path=None,
        manifest_path=bundle["manifest"],
        destination=destination,
        project_root=tmp_path,
    )

    assert result.status == "already-valid"
    assert result.source == "existing"
    assert destination.stat().st_mtime_ns == marker


def test_missing_runtime_requires_valid_distribution_descriptor(tmp_path: Path) -> None:
    """Bootstrap remoto falha fechado quando o descriptor está ausente."""
    bundle = create_bundle(tmp_path)

    with pytest.raises(bootstrap.RuntimeBootstrapError, match="Descriptor"):
        bootstrap.bootstrap_runtime(
            archive_path=None,
            manifest_path=bundle["manifest"],
            distribution_path=tmp_path / "missing-distribution.json",
            destination=tmp_path / "missing" / runtime.RUNTIME_VERSION,
            project_root=tmp_path,
        )


def test_remote_release_is_used_when_archive_is_not_explicit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ausência de --archive deve usar somente os assets descritos na Release."""
    bundle = create_bundle(tmp_path)
    descriptor_path = create_distribution_descriptor(tmp_path, bundle)
    destination = tmp_path / "workspace" / "dist" / runtime.RUNTIME_VERSION

    def fake_download(
        descriptor: dict[str, object],
        download_root: Path,
    ) -> Path:
        archive = download_root / str(descriptor["asset_name"])
        sidecar = download_root / str(descriptor["checksum_asset_name"])
        shutil.copy2(bundle["archive"], archive)
        shutil.copy2(bundle["archive"].with_suffix(".zip.sha256"), sidecar)
        return archive

    monkeypatch.setattr(
        bootstrap,
        "download_runtime_release",
        fake_download,
    )
    result = bootstrap.bootstrap_runtime(
        archive_path=None,
        manifest_path=bundle["manifest"],
        distribution_path=descriptor_path,
        destination=destination,
        project_root=tmp_path / "workspace",
    )

    assert result.status == "installed"
    assert result.source == "remote"
    runtime.validate_runtime_tree(
        destination,
        json.loads(bundle["manifest"].read_text(encoding="utf-8")),
    )


def test_remote_inventory_must_match_distribution_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inventário extraído divergente deve falhar antes da instalação."""
    bundle = create_bundle(tmp_path)
    descriptor_path = create_distribution_descriptor(tmp_path, bundle)
    descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
    descriptor["file_count"] += 1
    descriptor_path.write_text(
        json.dumps(descriptor, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    destination = tmp_path / "workspace" / "dist" / runtime.RUNTIME_VERSION

    def fake_download(
        distribution: dict[str, object],
        download_root: Path,
    ) -> Path:
        archive = download_root / str(distribution["asset_name"])
        sidecar = download_root / str(distribution["checksum_asset_name"])
        shutil.copy2(bundle["archive"], archive)
        shutil.copy2(bundle["archive"].with_suffix(".zip.sha256"), sidecar)
        return archive

    monkeypatch.setattr(
        bootstrap,
        "download_runtime_release",
        fake_download,
    )

    with pytest.raises(bootstrap.RuntimeBootstrapError, match="Quantidade"):
        bootstrap.bootstrap_runtime(
            archive_path=None,
            manifest_path=bundle["manifest"],
            distribution_path=descriptor_path,
            destination=destination,
            project_root=tmp_path / "workspace",
        )

    assert not destination.exists()


def test_wrong_external_checksum_is_rejected(tmp_path: Path) -> None:
    """SHA-256 externo divergente deve falhar antes da extração."""
    bundle = create_bundle(tmp_path)
    bundle["archive"].with_suffix(".zip.sha256").write_text(
        f"{'0' * 64}  {bundle['archive'].name}\n",
        encoding="utf-8",
    )
    destination = tmp_path / "workspace" / "dist" / runtime.RUNTIME_VERSION

    with pytest.raises(bootstrap.RuntimeBootstrapError, match="diverge"):
        bootstrap.bootstrap_runtime(
            archive_path=bundle["archive"],
            manifest_path=bundle["manifest"],
            destination=destination,
            project_root=tmp_path / "workspace",
        )

    assert not destination.exists()


def test_versioned_distribution_descriptor_is_pinned_to_public_release() -> None:
    """Descriptor real deve fixar somente os dois assets autorizados."""
    descriptor = bootstrap.load_distribution_descriptor(
        bootstrap.DEFAULT_DISTRIBUTION_PATH
    )

    assert descriptor == {
        "archive_sha256": (
            "9cfe0c61bf406f10b66e4519a996ca0cad93e01402b262117bd74f276bec11bb"
        ),
        "archive_size_bytes": 38_553_264,
        "asset_name": "serving-runtime-v1.0.0.zip",
        "checksum_asset_name": "serving-runtime-v1.0.0.zip.sha256",
        "checksum_sha256": (
            "b62659974316e55e8b4e99d5b9fe80ace7bb81ca3aa7420271f4ba5002a49e9a"
        ),
        "checksum_size_bytes": 93,
        "checksum_url": (
            "https://github.com/lgustavoab/dengue-alert/releases/download/"
            "serving-runtime-v1.0.0/serving-runtime-v1.0.0.zip.sha256"
        ),
        "download_url": (
            "https://github.com/lgustavoab/dengue-alert/releases/download/"
            "serving-runtime-v1.0.0/serving-runtime-v1.0.0.zip"
        ),
        "file_count": 235,
        "runtime_version": "serving-runtime-v1.0.0",
        "schema_version": "1.0",
        "source_snapshot_version": "serving-v1.0.0",
        "uncompressed_size_bytes": 281_337_226,
    }
