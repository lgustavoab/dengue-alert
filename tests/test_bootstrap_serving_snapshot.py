"""Testes do bootstrap seguro do snapshot científico de serving."""

import importlib.util
import io
import json
import stat
import sys
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Any, Self

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = PROJECT_ROOT / "scripts" / "package_serving_snapshot.py"
BOOTSTRAP_SCRIPT = PROJECT_ROOT / "scripts" / "bootstrap_serving_snapshot.py"


def load_script(name: str, path: Path) -> ModuleType:
    """Carrega script como módulo registrado para suportar dataclasses."""
    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Não foi possível carregar o script: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


snapshot = load_script("package_serving_snapshot", PACKAGE_SCRIPT)
bootstrap = load_script("bootstrap_serving_snapshot", BOOTSTRAP_SCRIPT)


def create_source(root: Path) -> Path:
    """Cria serving sintético suficiente para os testes do bootstrap."""
    source = root / "source" / "data" / "serving"
    files = {
        "quality/overview.json": b'{"schema_version":"1.0","ok":true}\n',
        "geography/municipalities.topojson": b'{"type":"Topology"}\n',
        "metadata/territories.json": b'{"schema_version":"1.0","count":2}\n',
    }

    for relative_path, content in files.items():
        path = source / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    return source


def write_descriptor(path: Path, payload: dict[str, Any]) -> None:
    """Grava descriptor determinístico usado pelas fixtures."""
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def create_bundle(tmp_path: Path) -> dict[str, Any]:
    """Gera snapshot, manifest e descriptor pequenos e íntegros."""
    source = create_source(tmp_path)
    manifest_path = tmp_path / "snapshot.json"
    archive_path = tmp_path / "snapshot.zip"
    result = snapshot.package_snapshot(source, manifest_path, archive_path)
    descriptor_path = tmp_path / "distribution.json"
    descriptor = {
        "schema_version": snapshot.SCHEMA_VERSION,
        "snapshot_version": snapshot.SNAPSHOT_VERSION,
        "asset_name": archive_path.name,
        "archive_sha256": result.archive_sha256,
        "archive_size_bytes": result.archive_size_bytes,
        "scientific_file_count": result.file_count,
        "uncompressed_size_bytes": result.total_size_bytes,
    }
    write_descriptor(descriptor_path, descriptor)
    return {
        "source": source,
        "manifest": manifest_path,
        "archive": archive_path,
        "descriptor": descriptor_path,
        "descriptor_payload": descriptor,
    }


def refresh_descriptor(bundle: dict[str, Any], **overrides: Any) -> None:
    """Atualiza identidade externa após mutação intencional de fixture."""
    digest, size = snapshot.hash_file_stable(bundle["archive"])
    payload = {
        **bundle["descriptor_payload"],
        "archive_sha256": digest,
        "archive_size_bytes": size,
        **overrides,
    }
    bundle["descriptor_payload"] = payload
    write_descriptor(bundle["descriptor"], payload)


def rewrite_entry(
    archive_path: Path,
    entry_name: str,
    transform: Any,
) -> None:
    """Recria ZIP substituindo deterministicamente uma entrada."""
    temporary = archive_path.with_suffix(".rewritten.zip")

    with zipfile.ZipFile(archive_path, mode="r") as source:
        entries = [(info, source.read(info.filename)) for info in source.infolist()]

    with zipfile.ZipFile(temporary, mode="w") as target:
        for info, content in entries:
            if info.filename == entry_name:
                content = transform(content)
            target.writestr(info, content)

    temporary.replace(archive_path)


def run_bootstrap(
    bundle: dict[str, Any],
    destination: Path,
    **options: Any,
) -> Any:
    """Executa bootstrap local com metadata da fixture."""
    return bootstrap.bootstrap_snapshot(
        descriptor_path=bundle["descriptor"],
        manifest_path=bundle["manifest"],
        destination=destination,
        project_root=destination.parents[1],
        local_archive=bundle["archive"],
        **options,
    )


def test_valid_local_bootstrap_installs_missing_destination(tmp_path: Path) -> None:
    """Destino ausente deve ser restaurado integralmente."""
    bundle = create_bundle(tmp_path)
    destination = tmp_path / "workspace" / "data" / "serving"

    result = run_bootstrap(bundle, destination)

    assert result.status == "installed"
    assert (
        bootstrap.installed_serving_status(
            destination,
            json.loads(bundle["manifest"].read_text(encoding="utf-8")),
        )
        == "valid"
    )


def test_wrong_external_hash_stops_before_destination(tmp_path: Path) -> None:
    """SHA externo divergente deve impedir qualquer extração."""
    bundle = create_bundle(tmp_path)
    destination = tmp_path / "workspace" / "data" / "serving"
    refresh_descriptor(bundle, archive_sha256="0" * 64)

    with pytest.raises(bootstrap.BootstrapError, match="SHA-256 externo"):
        run_bootstrap(bundle, destination)

    assert not destination.exists()


def test_truncated_archive_is_rejected(tmp_path: Path) -> None:
    """Arquivo parcial deve falhar na integridade externa."""
    bundle = create_bundle(tmp_path)
    destination = tmp_path / "workspace" / "data" / "serving"
    content = bundle["archive"].read_bytes()
    bundle["archive"].write_bytes(content[: len(content) // 2])

    with pytest.raises(bootstrap.BootstrapError, match="Tamanho externo"):
        run_bootstrap(bundle, destination)

    assert not destination.exists()


def test_path_traversal_zip_is_rejected(tmp_path: Path) -> None:
    """Entrada com traversal deve falhar antes da restauração."""
    bundle = create_bundle(tmp_path)

    with zipfile.ZipFile(bundle["archive"], mode="a") as archive:
        archive.writestr("../evil.json", b"{}")

    refresh_descriptor(bundle)
    destination = tmp_path / "workspace" / "data" / "serving"

    with pytest.raises(snapshot.SnapshotError, match="inseguro|fora"):
        run_bootstrap(bundle, destination)

    assert not (tmp_path / "evil.json").exists()


def test_duplicate_zip_entry_is_rejected(tmp_path: Path) -> None:
    """Nomes duplicados não podem ser aceitos pelo bootstrap."""
    bundle = create_bundle(tmp_path)

    with (
        pytest.warns(UserWarning, match="Duplicate name"),
        zipfile.ZipFile(bundle["archive"], mode="a") as archive,
    ):
        archive.writestr(snapshot.MANIFEST_NAME, b"{}")

    refresh_descriptor(bundle)

    with pytest.raises(snapshot.SnapshotError, match="duplicadas"):
        run_bootstrap(
            bundle,
            tmp_path / "workspace" / "data" / "serving",
        )


def test_symlink_zip_entry_is_rejected(tmp_path: Path) -> None:
    """Metadata Unix de symlink deve ser rejeitada antes da escrita."""
    bundle = create_bundle(tmp_path)
    link = zipfile.ZipInfo("data/serving/link.json")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16

    with zipfile.ZipFile(bundle["archive"], mode="a") as archive:
        archive.writestr(link, b"quality/overview.json")

    refresh_descriptor(bundle)

    with pytest.raises(snapshot.SnapshotError, match="Symlink"):
        run_bootstrap(
            bundle,
            tmp_path / "workspace" / "data" / "serving",
        )


def test_internal_manifest_divergence_is_rejected(tmp_path: Path) -> None:
    """Manifest interno deve ser idêntico ao versionado."""
    bundle = create_bundle(tmp_path)
    rewrite_entry(
        bundle["archive"],
        snapshot.MANIFEST_NAME,
        lambda content: content.replace(b"serving-v1.0.0", b"serving-v9.0.0"),
    )
    refresh_descriptor(bundle)

    with pytest.raises(
        snapshot.SnapshotError, match="manifest interno|Manifest interno"
    ):
        run_bootstrap(
            bundle,
            tmp_path / "workspace" / "data" / "serving",
        )


def test_sha256sums_divergence_is_rejected(tmp_path: Path) -> None:
    """SHA256SUMS interno não pode divergir do manifest."""
    bundle = create_bundle(tmp_path)
    rewrite_entry(
        bundle["archive"],
        snapshot.CHECKSUMS_NAME,
        lambda content: b"f" + content[1:],
    )
    refresh_descriptor(bundle)

    with pytest.raises(snapshot.SnapshotError, match="SHA256SUMS"):
        run_bootstrap(
            bundle,
            tmp_path / "workspace" / "data" / "serving",
        )


def test_modified_scientific_file_is_rejected(tmp_path: Path) -> None:
    """Conteúdo científico alterado deve falhar no hash interno."""
    bundle = create_bundle(tmp_path)
    manifest = json.loads(bundle["manifest"].read_text(encoding="utf-8"))
    scientific_path = manifest["files"][0]["path"]
    rewrite_entry(
        bundle["archive"],
        scientific_path,
        lambda content: bytes([content[0] ^ 1]) + content[1:],
    )
    refresh_descriptor(bundle)

    with pytest.raises(snapshot.SnapshotError, match="Hash ou tamanho"):
        run_bootstrap(
            bundle,
            tmp_path / "workspace" / "data" / "serving",
        )


@pytest.mark.parametrize(
    ("field", "delta"),
    (
        ("scientific_file_count", 1),
        ("uncompressed_size_bytes", 1),
    ),
)
def test_descriptor_count_and_size_must_match_manifest(
    tmp_path: Path,
    field: str,
    delta: int,
) -> None:
    """Limites externos devem coincidir com o manifest versionado."""
    bundle = create_bundle(tmp_path)
    refresh_descriptor(
        bundle,
        **{field: bundle["descriptor_payload"][field] + delta},
    )

    with pytest.raises(bootstrap.BootstrapError, match="diverge do manifest"):
        run_bootstrap(
            bundle,
            tmp_path / "workspace" / "data" / "serving",
        )


def test_valid_installed_destination_avoids_replacement(tmp_path: Path) -> None:
    """Serving íntegro deve ser reconhecido sem reinstalação."""
    bundle = create_bundle(tmp_path)
    destination = tmp_path / "workspace" / "data" / "serving"
    first = run_bootstrap(bundle, destination)
    marker = destination.stat().st_mtime_ns
    second = run_bootstrap(bundle, destination)

    assert first.status == "installed"
    assert second.status == "already-valid"
    assert destination.stat().st_mtime_ns == marker


def test_different_destination_requires_replace(tmp_path: Path) -> None:
    """Destino divergente deve permanecer intacto sem autorização explícita."""
    bundle = create_bundle(tmp_path)
    destination = tmp_path / "workspace" / "data" / "serving"
    old_file = destination / "quality" / "old.json"
    old_file.parent.mkdir(parents=True)
    old_file.write_text("{}\n", encoding="utf-8")

    with pytest.raises(bootstrap.BootstrapError, match="--replace"):
        run_bootstrap(bundle, destination)

    assert old_file.read_text(encoding="utf-8") == "{}\n"


def test_explicit_replace_installs_snapshot(tmp_path: Path) -> None:
    """Substituição autorizada deve promover somente o serving validado."""
    bundle = create_bundle(tmp_path)
    destination = tmp_path / "workspace" / "data" / "serving"
    old_file = destination / "quality" / "old.json"
    old_file.parent.mkdir(parents=True)
    old_file.write_text("{}\n", encoding="utf-8")

    result = run_bootstrap(bundle, destination, replace=True)

    assert result.status == "replaced"
    assert not old_file.exists()
    assert len([path for path in destination.rglob("*") if path.is_file()]) == 3


def test_failure_before_promotion_preserves_existing_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Falha na restauração não pode tocar no serving anterior."""
    bundle = create_bundle(tmp_path)
    destination = tmp_path / "workspace" / "data" / "serving"
    old_file = destination / "old.json"
    destination.mkdir(parents=True)
    old_file.write_text("previous\n", encoding="utf-8")

    def fail_restore(*_: Any, **__: Any) -> None:
        raise snapshot.SnapshotError("falha simulada")

    monkeypatch.setattr(bootstrap, "restore_snapshot", fail_restore)

    with pytest.raises(snapshot.SnapshotError, match="falha simulada"):
        run_bootstrap(bundle, destination, replace=True)

    assert old_file.read_text(encoding="utf-8") == "previous\n"


def test_sync_is_not_run_without_explicit_flag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Instalação padrão não deve produzir o subconjunto web."""
    bundle = create_bundle(tmp_path)
    called = False

    def record_sync(*_: Any) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(bootstrap, "run_web_sync", record_sync)
    run_bootstrap(
        bundle,
        tmp_path / "workspace" / "data" / "serving",
    )

    assert called is False


def test_sync_runs_when_explicitly_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Flag explícita deve delegar aos scripts de sync existentes."""
    bundle = create_bundle(tmp_path)
    destination = tmp_path / "workspace" / "data" / "serving"
    calls: list[tuple[Path, Path]] = []
    monkeypatch.setattr(
        bootstrap,
        "run_web_sync",
        lambda project_root, target: calls.append((project_root, target)),
    )

    result = run_bootstrap(bundle, destination, sync_web=True)

    assert result.synced_web is True
    assert calls == [(destination.parents[1], destination)]


def test_sync_subprocesses_force_utf8_console(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Scripts existentes devem imprimir Unicode de forma estável no Windows."""
    project_root = tmp_path / "workspace"
    destination = project_root / "data" / "serving"
    scripts_root = project_root / "scripts"
    destination.mkdir(parents=True)
    scripts_root.mkdir(parents=True)

    for script_name in bootstrap.SYNC_SCRIPTS:
        (scripts_root / script_name).write_text("pass\n", encoding="utf-8")

    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        bootstrap.subprocess,
        "run",
        lambda *args, **kwargs: calls.append({"args": args, "kwargs": kwargs}),
    )

    bootstrap.run_web_sync(project_root, destination)

    assert len(calls) == 2
    assert all(call["kwargs"]["env"]["PYTHONIOENCODING"] == "utf-8" for call in calls)
    assert all(call["kwargs"]["env"]["PYTHONUTF8"] == "1" for call in calls)


def test_verify_mode_does_not_modify_filesystem(tmp_path: Path) -> None:
    """Verify deve validar o arquivo sem criar o destino ausente."""
    bundle = create_bundle(tmp_path)
    destination = tmp_path / "untouched" / "data" / "serving"

    result = run_bootstrap(bundle, destination, verify_only=True)

    assert result.status == "verified-archive"
    assert not destination.parent.exists()


class FakeResponse(io.BytesIO):
    """Resposta HTTPS em memória para testar streaming sem Internet."""

    def __init__(
        self,
        content: bytes,
        *,
        status: int = 200,
        final_url: str = "https://example.test/snapshot.zip",
        content_length: int | None = None,
    ) -> None:
        super().__init__(content)
        self.status = status
        self.final_url = final_url
        self.headers = {
            "Content-Length": str(
                len(content) if content_length is None else content_length
            )
        }

    def geturl(self) -> str:
        """Retorna URL final após redirecionamentos simulados."""
        return self.final_url

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def test_https_download_streams_and_validates(tmp_path: Path) -> None:
    """Download HTTPS mockado deve produzir arquivo idêntico."""
    bundle = create_bundle(tmp_path)
    descriptor = bootstrap.load_distribution_descriptor(bundle["descriptor"])
    content = bundle["archive"].read_bytes()
    destination = tmp_path / "downloaded.zip"

    bootstrap.download_https_snapshot(
        "https://example.test/snapshot.zip",
        destination,
        descriptor,
        opener=lambda *_args, **_kwargs: FakeResponse(content),
    )

    assert destination.read_bytes() == content


def test_https_download_removes_partial_on_truncation(tmp_path: Path) -> None:
    """Download incompleto não pode deixar arquivo parcial utilizável."""
    bundle = create_bundle(tmp_path)
    descriptor = bootstrap.load_distribution_descriptor(bundle["descriptor"])
    content = bundle["archive"].read_bytes()[:-10]
    destination = tmp_path / "partial.zip"

    with pytest.raises(bootstrap.BootstrapError, match="tamanho divergente"):
        bootstrap.download_https_snapshot(
            "https://example.test/snapshot.zip",
            destination,
            descriptor,
            opener=lambda *_args, **_kwargs: FakeResponse(
                content,
                content_length=descriptor.archive_size_bytes,
            ),
        )

    assert not destination.exists()


def test_https_download_rejects_non_success_status(tmp_path: Path) -> None:
    """Resposta HTTP fora de 2xx deve falhar sem deixar arquivo."""
    bundle = create_bundle(tmp_path)
    descriptor = bootstrap.load_distribution_descriptor(bundle["descriptor"])
    content = bundle["archive"].read_bytes()
    destination = tmp_path / "failed.zip"

    with pytest.raises(bootstrap.BootstrapError, match="HTTP 503"):
        bootstrap.download_https_snapshot(
            "https://example.test/snapshot.zip",
            destination,
            descriptor,
            opener=lambda *_args, **_kwargs: FakeResponse(content, status=503),
        )

    assert not destination.exists()


@pytest.mark.parametrize(
    ("url", "final_url"),
    (
        ("http://example.test/snapshot.zip", "http://example.test/snapshot.zip"),
        ("https://example.test/snapshot.zip", "http://example.test/redirected.zip"),
    ),
)
def test_http_and_insecure_redirect_are_rejected(
    tmp_path: Path,
    url: str,
    final_url: str,
) -> None:
    """Fonte inicial ou redirecionamento final não podem abandonar HTTPS."""
    bundle = create_bundle(tmp_path)
    descriptor = bootstrap.load_distribution_descriptor(bundle["descriptor"])
    content = bundle["archive"].read_bytes()
    destination = tmp_path / "unsafe.zip"

    with pytest.raises(bootstrap.BootstrapError, match="HTTPS"):
        bootstrap.download_https_snapshot(
            url,
            destination,
            descriptor,
            opener=lambda *_args, **_kwargs: FakeResponse(
                content,
                final_url=final_url,
            ),
        )

    assert not destination.exists()
