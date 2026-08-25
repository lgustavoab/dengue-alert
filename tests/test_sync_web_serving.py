"""Testes da sincronização do serving para o frontend."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SYNC_SCRIPT = PROJECT_ROOT / "scripts" / "sync_web_serving.py"

SPEC = importlib.util.spec_from_file_location(
    "sync_web_serving",
    SYNC_SCRIPT,
)

if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Não foi possível carregar o script: {SYNC_SCRIPT}")

sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


TEST_CONTRACTS = (
    "metadata/territories.json",
    "quality/overview.json",
)


def write_json(
    path: Path,
    payload: dict,
) -> None:
    """Grava JSON auxiliar para os testes."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def patch_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, Path, Path, Path]:
    """Redireciona origem e destinos para diretórios temporários."""
    source_root = tmp_path / "source"

    output_dir = tmp_path / "public" / "data" / "serving"

    staging_dir = tmp_path / "public" / "data" / "serving.__staging__"

    backup_dir = tmp_path / "public" / "data" / "serving.__backup__"

    monkeypatch.setattr(
        sync,
        "SOURCE_ROOT",
        source_root,
    )

    monkeypatch.setattr(
        sync,
        "OUTPUT_DIR",
        output_dir,
    )

    monkeypatch.setattr(
        sync,
        "STAGING_DIR",
        staging_dir,
    )

    monkeypatch.setattr(
        sync,
        "BACKUP_DIR",
        backup_dir,
    )

    monkeypatch.setattr(
        sync,
        "CONTRACT_PATHS",
        TEST_CONTRACTS,
    )

    return (
        source_root,
        output_dir,
        staging_dir,
        backup_dir,
    )


def create_source_contracts(
    source_root: Path,
) -> None:
    """Cria os contratos sintéticos utilizados pelos testes."""
    write_json(
        source_root / "metadata" / "territories.json",
        {
            "schema_version": "1.0",
            "count": 2,
            "data": [
                {
                    "codigo_ibge_7": "1111111",
                },
                {
                    "codigo_ibge_7": "2222222",
                },
            ],
        },
    )

    write_json(
        source_root / "quality" / "overview.json",
        {
            "schema_version": "1.0",
            "period": "2016-2025",
            "data": {
                "status": "ok",
            },
        },
    )


def test_load_json_strict_accepts_valid_object(
    tmp_path: Path,
) -> None:
    """Objeto JSON válido e finito deve ser aceito."""
    path = tmp_path / "valid.json"

    write_json(
        path,
        {
            "schema_version": "1.0",
            "value": 10,
        },
    )

    payload = sync.load_json_strict(path)

    assert payload["schema_version"] == "1.0"

    assert payload["value"] == 10


def test_load_json_strict_rejects_nan(
    tmp_path: Path,
) -> None:
    """NaN não pode entrar nos contratos web."""
    path = tmp_path / "invalid.json"

    path.write_text(
        '{"schema_version":"1.0","value":NaN}\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="JSON inválido",
    ):
        sync.load_json_strict(path)


def test_load_json_strict_rejects_non_object(
    tmp_path: Path,
) -> None:
    """A raiz do contrato deve ser um objeto JSON."""
    path = tmp_path / "array.json"

    path.write_text(
        "[1,2,3]\n",
        encoding="utf-8",
    )

    with pytest.raises(
        TypeError,
        match="não é objeto",
    ):
        sync.load_json_strict(path)


def test_validate_source_contract_accepts_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contrato existente com schema correto deve ser aceito."""
    source_root = tmp_path / "source"

    monkeypatch.setattr(
        sync,
        "SOURCE_ROOT",
        source_root,
    )

    relative_path = "metadata/territories.json"

    path = source_root / relative_path

    write_json(
        path,
        {
            "schema_version": "1.0",
        },
    )

    result = sync.validate_source_contract(relative_path)

    assert result == path


def test_validate_source_contract_rejects_missing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contrato obrigatório ausente deve interromper a sincronização."""
    monkeypatch.setattr(
        sync,
        "SOURCE_ROOT",
        tmp_path,
    )

    with pytest.raises(
        FileNotFoundError,
        match="Contrato de serving ausente",
    ):
        sync.validate_source_contract("metadata/missing.json")


def test_validate_source_contract_rejects_wrong_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """schema_version divergente deve ser rejeitado."""
    source_root = tmp_path / "source"

    monkeypatch.setattr(
        sync,
        "SOURCE_ROOT",
        source_root,
    )

    relative_path = "metadata/territories.json"

    write_json(
        source_root / relative_path,
        {
            "schema_version": "2.0",
        },
    )

    with pytest.raises(
        ValueError,
        match="schema_version",
    ):
        sync.validate_source_contract(relative_path)


def test_sha256_file_matches_hashlib(
    tmp_path: Path,
) -> None:
    """Hash calculado deve corresponder ao SHA-256 real."""
    path = tmp_path / "sample.txt"

    content = b"dengue-alert\n"

    path.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()

    assert sync.sha256_file(path) == expected


def test_prepare_staging_directory_removes_stale_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Staging anterior deve ser limpo antes da sincronização."""
    (
        _,
        _,
        staging_dir,
        _,
    ) = patch_paths(
        tmp_path,
        monkeypatch,
    )

    staging_dir.mkdir(
        parents=True,
    )

    (staging_dir / "stale.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    sync.prepare_staging_directory()

    assert staging_dir.exists()

    assert list(staging_dir.iterdir()) == []


def test_copy_contract_preserves_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contrato copiado deve preservar bytes e SHA-256."""
    (
        source_root,
        _,
        staging_dir,
        _,
    ) = patch_paths(
        tmp_path,
        monkeypatch,
    )

    create_source_contracts(source_root)

    sync.prepare_staging_directory()

    result = sync.copy_contract("metadata/territories.json")

    destination = staging_dir / "metadata" / "territories.json"

    assert destination.exists()

    assert result["path"] == "metadata/territories.json"

    assert result["size_bytes"] == destination.stat().st_size

    assert result["sha256"] == sync.sha256_file(destination)


def test_build_manifest_preserves_totals() -> None:
    """Manifesto deve registrar quantidade e tamanho total."""
    files = [
        {
            "path": "a.json",
            "size_bytes": 100,
            "sha256": "a",
        },
        {
            "path": "b.json",
            "size_bytes": 250,
            "sha256": "b",
        },
    ]

    manifest = sync.build_manifest(files)

    assert manifest["schema_version"] == "1.0"

    assert manifest["status"] == "APROVADO"

    assert manifest["contract_count"] == 2

    assert manifest["total_size_bytes"] == 350

    assert manifest["files"] == files


def test_validate_staging_directory_accepts_complete_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Staging completo com hashes válidos deve ser aceito."""
    (
        source_root,
        _,
        _,
        _,
    ) = patch_paths(
        tmp_path,
        monkeypatch,
    )

    create_source_contracts(source_root)

    sync.prepare_staging_directory()

    files = [sync.copy_contract(relative_path) for relative_path in TEST_CONTRACTS]

    manifest = sync.build_manifest(files)

    sync.write_manifest(manifest)

    sync.validate_staging_directory(manifest)


def test_validate_staging_directory_rejects_missing_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Staging incompleto deve ser rejeitado."""
    (
        source_root,
        _,
        _,
        _,
    ) = patch_paths(
        tmp_path,
        monkeypatch,
    )

    create_source_contracts(source_root)

    sync.prepare_staging_directory()

    files = [sync.copy_contract("metadata/territories.json")]

    manifest = sync.build_manifest(files)

    sync.write_manifest(manifest)

    with pytest.raises(
        ValueError,
        match="Conjunto de contratos do staging divergente",
    ):
        sync.validate_staging_directory(manifest)


def test_promote_staging_directory_replaces_previous_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Promoção bem-sucedida deve substituir a versão anterior."""
    (
        _,
        output_dir,
        staging_dir,
        backup_dir,
    ) = patch_paths(
        tmp_path,
        monkeypatch,
    )

    output_dir.mkdir(
        parents=True,
    )

    (output_dir / "old.json").write_text(
        '{"version":"old"}\n',
        encoding="utf-8",
    )

    staging_dir.mkdir(
        parents=True,
    )

    (staging_dir / "new.json").write_text(
        '{"version":"new"}\n',
        encoding="utf-8",
    )

    sync.promote_staging_directory()

    assert output_dir.exists()

    assert (output_dir / "new.json").exists()

    assert not (output_dir / "old.json").exists()

    assert not staging_dir.exists()

    assert not backup_dir.exists()


def test_promote_staging_directory_restores_previous_output_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Falha na promoção deve restaurar a versão anterior."""
    (
        _,
        output_dir,
        staging_dir,
        backup_dir,
    ) = patch_paths(
        tmp_path,
        monkeypatch,
    )

    output_dir.mkdir(
        parents=True,
    )

    old_file = output_dir / "old.json"

    old_file.write_text(
        '{"version":"old"}\n',
        encoding="utf-8",
    )

    staging_dir.mkdir(
        parents=True,
    )

    (staging_dir / "new.json").write_text(
        '{"version":"new"}\n',
        encoding="utf-8",
    )

    original_replace = Path.replace

    def fail_when_promoting(
        self: Path,
        target: Path,
    ) -> Path:
        if self == staging_dir and Path(target) == output_dir:
            raise OSError("falha sintética na promoção")

        return original_replace(
            self,
            target,
        )

    monkeypatch.setattr(
        Path,
        "replace",
        fail_when_promoting,
    )

    with pytest.raises(
        OSError,
        match="falha sintética na promoção",
    ):
        sync.promote_staging_directory()

    assert output_dir.exists()

    assert old_file.exists()

    assert old_file.read_text(encoding="utf-8") == '{"version":"old"}\n'

    assert staging_dir.exists()

    assert (staging_dir / "new.json").exists()

    assert not backup_dir.exists()


def test_synchronize_generates_manifest_and_promotes_contracts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sincronização completa deve gerar cópia validada e manifesto."""
    (
        source_root,
        output_dir,
        staging_dir,
        backup_dir,
    ) = patch_paths(
        tmp_path,
        monkeypatch,
    )

    create_source_contracts(source_root)

    manifest = sync.synchronize()

    assert manifest["contract_count"] == 2

    assert output_dir.exists()

    assert not staging_dir.exists()

    assert not backup_dir.exists()

    assert (output_dir / "manifest.json").exists()

    for relative_path in TEST_CONTRACTS:
        source = source_root / relative_path

        destination = output_dir / relative_path

        assert destination.exists()

        assert sync.sha256_file(source) == sync.sha256_file(destination)
