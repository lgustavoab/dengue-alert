"""Testes do bootstrap local do serving runtime compacto."""

import hashlib
import importlib.util
import json
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
    assert destination.stat().st_mtime_ns == marker


def test_missing_runtime_requires_explicit_local_archive(tmp_path: Path) -> None:
    """Ausência de Release não pode ser mascarada por URL fictícia."""
    bundle = create_bundle(tmp_path)

    with pytest.raises(bootstrap.RuntimeBootstrapError, match="--archive local"):
        bootstrap.bootstrap_runtime(
            archive_path=None,
            manifest_path=bundle["manifest"],
            destination=tmp_path / "missing" / runtime.RUNTIME_VERSION,
            project_root=tmp_path,
        )


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
