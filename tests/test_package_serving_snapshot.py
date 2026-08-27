"""Testes do empacotamento determinístico do snapshot de serving."""

import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SCRIPT = PROJECT_ROOT / "scripts" / "package_serving_snapshot.py"

SPEC = importlib.util.spec_from_file_location(
    "package_serving_snapshot",
    PACKAGE_SCRIPT,
)

if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Não foi possível carregar o script: {PACKAGE_SCRIPT}")

snapshot = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = snapshot
SPEC.loader.exec_module(snapshot)


def create_source(root: Path) -> Path:
    """Cria um serving sintético pequeno, com ordem física não canônica."""
    source = root / "data" / "serving"
    files = {
        "quality/overview.json": b'{"schema_version":"1.0","ok":true}\n',
        "geography/municipalities.topojson": b'{"type":"Topology"}\n',
        "metadata/territories.json": b'{"schema_version":"1.0","count":2}\n',
    }

    for relative_path in reversed(tuple(files)):
        path = source / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(files[relative_path])

    return source


def package_fixture(
    tmp_path: Path,
    name: str,
) -> tuple[Path, Path, snapshot.SnapshotResult]:
    """Empacota a fixture em destinos independentes."""
    source = create_source(tmp_path)
    manifest = tmp_path / f"{name}.json"
    archive = tmp_path / f"{name}.zip"
    result = snapshot.package_snapshot(source, manifest, archive)
    return manifest, archive, result


def test_hashing_is_deterministic(tmp_path: Path) -> None:
    """O mesmo arquivo deve produzir sempre o mesmo SHA-256."""
    path = tmp_path / "contract.json"
    content = b'{"schema_version":"1.0"}\n'
    path.write_bytes(content)

    first = snapshot.hash_file_stable(path)
    second = snapshot.hash_file_stable(path)

    assert first == second
    assert first == (hashlib.sha256(content).hexdigest(), len(content))


def test_inventory_and_manifest_are_sorted_and_deterministic(tmp_path: Path) -> None:
    """Ordem física não pode afetar inventário nem serialização."""
    source = create_source(tmp_path)
    first_records = snapshot.inventory_serving(source)
    second_records = snapshot.inventory_serving(source)
    first_manifest = snapshot.build_manifest(first_records)
    second_manifest = snapshot.build_manifest(second_records)

    paths = [entry["path"] for entry in first_manifest["files"]]

    assert paths == sorted(paths)
    assert snapshot.manifest_bytes(first_manifest) == snapshot.manifest_bytes(
        second_manifest
    )


def test_manifest_count_and_size_match_source(tmp_path: Path) -> None:
    """Contagem e tamanho devem representar somente os contratos."""
    source = create_source(tmp_path)
    manifest = snapshot.build_manifest(snapshot.inventory_serving(source))
    expected_size = sum(
        path.stat().st_size for path in source.rglob("*") if path.is_file()
    )

    assert manifest["file_count"] == 3
    assert manifest["total_size_bytes"] == expected_size
    assert len(manifest["files"]) == 3


@pytest.mark.parametrize(
    "unsafe_path",
    (
        "../evil.json",
        "/absolute.json",
        "C:/absolute.json",
        "data/serving/../evil.json",
        "data\\serving\\evil.json",
    ),
)
def test_path_traversal_is_rejected(unsafe_path: str) -> None:
    """Caminhos absolutos, ambíguos ou com traversal devem falhar."""
    with pytest.raises(snapshot.SnapshotError):
        snapshot.validate_archive_path(unsafe_path)


def test_file_outside_source_root_is_rejected(tmp_path: Path) -> None:
    """Um arquivo externo não pode receber caminho interno no snapshot."""
    source = create_source(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")

    with pytest.raises(snapshot.SnapshotError, match="fora da raiz"):
        snapshot.archive_path_for_file(source, outside)


def test_file_change_during_hashing_is_detected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assinaturas diferentes antes/depois devem interromper o hash."""
    path = tmp_path / "contract.json"
    path.write_text("{}\n", encoding="utf-8")
    signatures = iter(
        (
            (1, 1, 3, 1, 1),
            (1, 1, 4, 2, 2),
        )
    )
    monkeypatch.setattr(snapshot, "_stat_signature", lambda _: next(signatures))

    with pytest.raises(snapshot.SnapshotError, match="mudou durante a leitura"):
        snapshot.hash_file_stable(path)


def test_snapshot_contains_all_and_only_expected_files(tmp_path: Path) -> None:
    """ZIP deve conter controles e exatamente os contratos do manifest."""
    manifest_path, archive_path, _ = package_fixture(tmp_path, "snapshot")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    with zipfile.ZipFile(archive_path) as archive:
        assert archive.namelist() == [
            snapshot.MANIFEST_NAME,
            snapshot.CHECKSUMS_NAME,
            *(entry["path"] for entry in manifest["files"]),
        ]

    assert snapshot.verify_snapshot_archive(archive_path) == manifest


def test_restore_produces_identical_hashes(tmp_path: Path) -> None:
    """Restauração temporária deve preservar todos os bytes."""
    manifest_path, archive_path, _ = package_fixture(tmp_path, "snapshot")
    restored = tmp_path / "restored"
    manifest = snapshot.restore_snapshot(archive_path, restored)

    assert manifest == json.loads(manifest_path.read_text(encoding="utf-8"))
    snapshot.validate_restored_snapshot(restored, manifest)


def test_same_input_produces_same_zip_sha256(tmp_path: Path) -> None:
    """Metadata ZIP normalizada deve tornar o arquivo binário reproduzível."""
    source = create_source(tmp_path)
    first_archive = tmp_path / "first.zip"
    second_archive = tmp_path / "second.zip"

    snapshot.package_snapshot(
        source,
        tmp_path / "first.json",
        first_archive,
    )
    snapshot.package_snapshot(
        source,
        tmp_path / "second.json",
        second_archive,
    )

    first_hash, _ = snapshot.hash_file_stable(first_archive)
    second_hash, _ = snapshot.hash_file_stable(second_archive)

    assert first_hash == second_hash
    assert first_archive.read_bytes() == second_archive.read_bytes()


def test_malicious_zip_is_rejected_before_extraction(tmp_path: Path) -> None:
    """Validação deve rejeitar traversal antes de gravar qualquer arquivo."""
    archive_path = tmp_path / "malicious.zip"
    destination = tmp_path / "restore"

    with zipfile.ZipFile(archive_path, mode="w") as archive:
        archive.writestr("../evil.json", "{}")

    with pytest.raises(snapshot.SnapshotError):
        snapshot.restore_snapshot(archive_path, destination)

    assert not (tmp_path / "evil.json").exists()


def test_unexpected_and_temporary_files_are_rejected(tmp_path: Path) -> None:
    """Serving não pode incorporar caches ou arquivos temporários."""
    source = create_source(tmp_path)
    temporary = source / "quality" / "overview.json.tmp"
    temporary.write_text("temporary", encoding="utf-8")

    with pytest.raises(snapshot.SnapshotError, match="temporário"):
        snapshot.inventory_serving(source)
