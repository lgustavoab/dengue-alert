"""Testes pequenos do empacotamento do serving runtime compacto."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "package_serving_runtime.py"
SNAPSHOT_SCRIPT = PROJECT_ROOT / "scripts" / "package_serving_snapshot.py"
SYNC_SCRIPT = PROJECT_ROOT / "scripts" / "sync_web_serving.py"


def load_dependency(name: str, path: Path) -> None:
    """Registra dependência local importada pelo script de runtime."""
    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Não foi possível carregar o script: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)


load_dependency("package_serving_snapshot", SNAPSHOT_SCRIPT)
load_dependency("sync_web_serving", SYNC_SCRIPT)

SPEC = importlib.util.spec_from_file_location("package_serving_runtime", SCRIPT)

if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Não foi possível carregar o script: {SCRIPT}")

runtime = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runtime
SPEC.loader.exec_module(runtime)


def write_series(directory: Path, code: str, marker: int = 1) -> Path:
    """Cria uma série municipal sintética compacta."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{code}.json"
    path.write_bytes(
        json.dumps(
            {
                "schema_version": "1.0",
                "codigo_ibge_7": code,
                "count": 1,
                "data": {"marker": [marker]},
            },
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return path


def build_small_pack(tmp_path: Path) -> tuple[list[Path], Path, Path]:
    """Cria pack de duas séries em ordem física inversa."""
    source = tmp_path / "source"
    second = write_series(source, "2222222", marker=2)
    first = write_series(source, "1111111", marker=1)
    pack = tmp_path / "runtime" / "historical" / "municipalities.ndjson"
    index = pack.with_name("municipalities.index.json")
    files = [second, first]
    runtime.create_pack(files, pack, index, "historical", 2)
    return files, pack, index


def test_pack_preserves_bytes_offsets_lengths_and_hashes(tmp_path: Path) -> None:
    """Cada range deve corresponder exatamente ao arquivo canônico."""
    files, pack, index_path = build_small_pack(tmp_path)
    index = runtime.load_runtime_index(index_path)
    pack_bytes = pack.read_bytes()

    for source in sorted(files, key=lambda path: path.stem):
        entry = index["entries"][source.stem]
        payload = pack_bytes[entry["offset"] : entry["offset"] + entry["length"]]
        assert payload == source.read_bytes()
        assert entry["sha256"] == hashlib.sha256(payload).hexdigest()
        assert pack_bytes[entry["offset"] + entry["length"]] == 10


def test_pack_and_index_are_deterministic(tmp_path: Path) -> None:
    """Mesmas entradas devem produzir bytes idênticos."""
    source = tmp_path / "source"
    files = [
        write_series(source, "2222222", marker=2),
        write_series(source, "1111111", marker=1),
    ]
    outputs: list[tuple[bytes, bytes]] = []

    for name in ("first", "second"):
        pack = tmp_path / name / "historical" / "municipalities.ndjson"
        index = pack.with_name("municipalities.index.json")
        runtime.create_pack(files, pack, index, "historical", 2)
        outputs.append((pack.read_bytes(), index.read_bytes()))

    assert outputs[0] == outputs[1]


def test_duplicate_code_is_rejected(tmp_path: Path) -> None:
    """Duas fontes com o mesmo stem não podem entrar no índice."""
    first = write_series(tmp_path / "one", "1111111")
    second = write_series(tmp_path / "two", "1111111")
    pack = tmp_path / "runtime" / "historical" / "municipalities.ndjson"

    with pytest.raises(runtime.RuntimePackagingError, match="duplicado"):
        runtime.create_pack(
            [first, second],
            pack,
            pack.with_name("municipalities.index.json"),
            "historical",
            2,
        )


def test_empty_payload_is_rejected(tmp_path: Path) -> None:
    """Arquivo municipal vazio deve interromper a geração."""
    source = tmp_path / "1111111.json"
    source.write_bytes(b"")
    pack = tmp_path / "runtime" / "historical" / "municipalities.ndjson"

    with pytest.raises(runtime.RuntimePackagingError, match="vazio"):
        runtime.create_pack(
            [source],
            pack,
            pack.with_name("municipalities.index.json"),
            "historical",
            1,
        )


def test_source_change_during_read_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Assinatura alterada durante a leitura deve falhar."""
    source = write_series(tmp_path, "1111111")
    signatures = iter(
        (
            (1, 1, source.stat().st_size, 1, 1),
            (1, 1, source.stat().st_size, 2, 2),
        )
    )
    monkeypatch.setattr(runtime, "_stat_signature", lambda _: next(signatures))

    with pytest.raises(runtime.RuntimePackagingError, match="mudou"):
        runtime.read_stable_bytes(source)


def test_unexpected_series_file_is_rejected(tmp_path: Path) -> None:
    """Extras e nomes fora do padrão não podem entrar por glob amplo."""
    source = tmp_path / "series"
    write_series(source, "1111111")
    (source / "notes.txt").write_text("extra", encoding="utf-8")

    with pytest.raises(runtime.RuntimePackagingError, match="inesperados"):
        runtime.discover_series_files(source)


def test_invalid_offset_is_rejected(tmp_path: Path) -> None:
    """Offset fora da sequência deve ser detectado na validação."""
    files, pack, index_path = build_small_pack(tmp_path)
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["entries"]["1111111"]["offset"] = 1
    index_path.write_bytes(runtime.deterministic_json_bytes(index))

    with pytest.raises(runtime.RuntimePackagingError, match="Offset"):
        runtime.validate_pack(files, pack, index_path, 2)


def test_manifest_records_roles_hashes_and_totals(tmp_path: Path) -> None:
    """Manifest técnico deve ser pequeno, ordenado e completo."""
    payload = b"payload\n"
    record = runtime.RuntimeFile(
        path="historical/municipalities.ndjson",
        size_bytes=len(payload),
        sha256=hashlib.sha256(payload).hexdigest(),
        role="historical-municipality-pack",
    )
    fingerprint = {
        "digest_algorithm": "sha256-path-content-manifest-v1",
        "digest": "a" * 64,
        "file_count": 1,
        "total_size_bytes": len(payload),
    }
    manifest = runtime.build_manifest([record], fingerprint)

    assert manifest["runtime_version"] == runtime.RUNTIME_VERSION
    assert manifest["file_count"] == 1
    assert manifest["total_size_bytes"] == len(payload)
    assert manifest["files"][0]["role"] == "historical-municipality-pack"


def test_runtime_tree_rejects_individual_series(tmp_path: Path) -> None:
    """O formato final não pode reintroduzir séries municipais individuais."""
    runtime_root = tmp_path / runtime.RUNTIME_VERSION
    forbidden = runtime_root / "historical" / "municipality" / "series" / "1111111.json"
    forbidden.parent.mkdir(parents=True)
    forbidden.write_text("{}", encoding="utf-8")
    digest = hashlib.sha256(forbidden.read_bytes()).hexdigest()
    manifest = runtime.build_manifest(
        [
            runtime.RuntimeFile(
                path=forbidden.relative_to(runtime_root).as_posix(),
                size_bytes=forbidden.stat().st_size,
                sha256=digest,
                role="forbidden",
            )
        ],
        {
            "digest_algorithm": "test",
            "digest": "a" * 64,
            "file_count": 1,
            "total_size_bytes": 2,
        },
    )
    (runtime_root / runtime.MANIFEST_NAME).write_bytes(
        runtime.deterministic_json_bytes(manifest)
    )
    (runtime_root / runtime.CHECKSUMS_NAME).write_bytes(
        runtime.checksums_bytes(manifest)
    )

    with pytest.raises(runtime.RuntimePackagingError, match="séries individuais"):
        runtime.validate_runtime_tree(runtime_root, manifest)


def test_map_allowlist_has_index_and_202_slices(tmp_path: Path) -> None:
    """A allowlist do mapa deve aceitar exatamente a cobertura congelada."""
    source = tmp_path / "source"
    paths = ["prediction/map/index.json"]

    for horizon, weeks in ((1, 52), (2, 51), (3, 50), (4, 49)):
        paths.extend(
            f"prediction/map/h{horizon}/se{week:02d}.json"
            for week in range(1, weeks + 1)
        )

    for relative_path in paths:
        path = source / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")

    assert runtime.expected_map_paths(source) == paths
    assert len(paths) == 203
