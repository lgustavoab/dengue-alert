"""Sincroniza contratos selecionados do serving para o frontend."""

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_ROOT = PROJECT_ROOT / "data" / "serving"

PUBLIC_DATA_ROOT = PROJECT_ROOT / "web" / "public" / "data"

OUTPUT_DIR = PUBLIC_DATA_ROOT / "serving"

STAGING_DIR = PUBLIC_DATA_ROOT / "serving.__staging__"

BACKUP_DIR = PUBLIC_DATA_ROOT / "serving.__backup__"

MANIFEST_FILE = "manifest.json"

SCHEMA_VERSION = "1.0"

CONTRACT_PATHS = (
    "historical/climate/national_lags.json",
    "historical/climate/regional_lags.json",
    "historical/municipality/index.json",
    "historical/panorama/annual.json",
    "historical/panorama/weekly.json",
    "historical/risk_dynamics/episode_duration.json",
    "historical/risk_dynamics/municipalities.json",
    "historical/risk_dynamics/weekly.json",
    "historical/seasonality/national.json",
    "historical/seasonality/regional.json",
    "historical/spatial/municipalities.json",
    "historical/spatial/regions.json",
    "historical/spatial/states.json",
    "metadata/temporal_coverage.json",
    "metadata/territories.json",
    "prediction/evaluation/by_horizon.json",
    "prediction/evaluation/overview.json",
    "prediction/metadata/model.json",
    "prediction/municipality/index.json",
    "quality/climate_coverage.json",
    "quality/overview.json",
    "quality/population_coverage.json",
    "quality/sinan_pipeline.json",
    "quality/territorial_coverage.json",
)

EXCLUDED_PATTERNS = (
    "historical/municipality/series/*.json",
    "prediction/municipality/series/*.json",
)


def reject_nonfinite_constant(
    value: str,
) -> None:
    """Rejeita NaN e Infinity durante leitura dos contratos."""
    raise ValueError(f"Constante JSON não permitida: {value}")


def load_json_strict(
    path: Path,
) -> dict[str, Any]:
    """Carrega contrato JSON com validação estrita."""
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_nonfinite_constant,
        )
    except (
        json.JSONDecodeError,
        ValueError,
    ) as error:
        raise ValueError(f"JSON inválido: {path}") from error

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError(f"Contrato JSON não é objeto: {path}")

    return payload


def validate_source_contract(
    relative_path: str,
) -> Path:
    """Valida um contrato antes da sincronização."""
    path = SOURCE_ROOT / relative_path

    if not path.exists():
        raise FileNotFoundError(f"Contrato de serving ausente: {path}")

    if not path.is_file():
        raise ValueError(f"Caminho de serving não é arquivo: {path}")

    payload = load_json_strict(path)

    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version ausente ou divergente em {relative_path}")

    return path


def sha256_file(
    path: Path,
) -> str:
    """Calcula SHA-256 de um arquivo."""
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def prepare_staging_directory() -> None:
    """Prepara staging vazio."""
    if STAGING_DIR.exists():
        shutil.rmtree(STAGING_DIR)

    STAGING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def copy_contract(
    relative_path: str,
) -> dict[str, Any]:
    """Valida e copia um contrato para o staging."""
    source = validate_source_contract(relative_path)

    destination = STAGING_DIR / relative_path

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        source,
        destination,
    )

    source_hash = sha256_file(source)

    destination_hash = sha256_file(destination)

    if source_hash != destination_hash:
        raise ValueError(f"SHA-256 divergente após cópia: {relative_path}")

    return {
        "path": relative_path,
        "size_bytes": source.stat().st_size,
        "sha256": source_hash,
    }


def build_manifest(
    files: list[dict[str, Any]],
) -> dict[str, Any]:
    """Cria manifesto determinístico da sincronização."""
    total_size = sum(int(item["size_bytes"]) for item in files)

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "APROVADO",
        "source": "data/serving",
        "destination": "web/public/data/serving",
        "contract_count": len(files),
        "total_size_bytes": total_size,
        "excluded": list(EXCLUDED_PATTERNS),
        "files": files,
    }


def write_manifest(
    manifest: dict[str, Any],
) -> None:
    """Grava manifesto da sincronização no staging."""
    path = STAGING_DIR / MANIFEST_FILE

    path.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def validate_staging_directory(
    manifest: dict[str, Any],
) -> None:
    """Relê e valida o staging antes da promoção."""
    expected_paths = set(CONTRACT_PATHS)

    generated_contracts = {
        path.relative_to(STAGING_DIR).as_posix()
        for path in STAGING_DIR.rglob("*.json")
        if path.name != MANIFEST_FILE
    }

    if generated_contracts != expected_paths:
        missing = sorted(expected_paths - generated_contracts)

        unexpected = sorted(generated_contracts - expected_paths)

        raise ValueError(
            "Conjunto de contratos do staging divergente. "
            f"Ausentes: {missing}; "
            f"inesperados: {unexpected}."
        )

    if manifest.get("contract_count") != len(CONTRACT_PATHS):
        raise ValueError("Quantidade divergente no manifesto.")

    manifest_files = manifest.get("files")

    if not isinstance(
        manifest_files,
        list,
    ):
        raise TypeError("Manifesto sem lista de arquivos.")

    if len(manifest_files) != len(CONTRACT_PATHS):
        raise ValueError("Quantidade de arquivos do manifesto divergente.")

    manifest_paths = {item["path"] for item in manifest_files}

    if manifest_paths != expected_paths:
        raise ValueError("Caminhos do manifesto divergem dos contratos esperados.")

    for item in manifest_files:
        relative_path = str(item["path"])

        path = STAGING_DIR / relative_path

        payload = load_json_strict(path)

        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"schema_version divergente no staging: {relative_path}")

        expected_hash = str(item["sha256"])

        actual_hash = sha256_file(path)

        if actual_hash != expected_hash:
            raise ValueError(f"SHA-256 divergente no staging: {relative_path}")

    manifest_path = STAGING_DIR / MANIFEST_FILE

    persisted_manifest = load_json_strict(manifest_path)

    if persisted_manifest != manifest:
        raise ValueError("Manifesto persistido diverge do manifesto em memória.")


def promote_staging_directory() -> None:
    """Promove staging preservando versão anterior durante a troca."""
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)

    had_previous_output = OUTPUT_DIR.exists()

    if had_previous_output:
        OUTPUT_DIR.replace(BACKUP_DIR)

    try:
        STAGING_DIR.replace(OUTPUT_DIR)
    except Exception:
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)

        if had_previous_output and BACKUP_DIR.exists():
            BACKUP_DIR.replace(OUTPUT_DIR)

        raise

    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)


def synchronize() -> dict[str, Any]:
    """Executa sincronização completa."""
    if not SOURCE_ROOT.exists():
        raise FileNotFoundError(f"Serving não encontrado: {SOURCE_ROOT}")

    prepare_staging_directory()

    try:
        files = [copy_contract(relative_path) for relative_path in CONTRACT_PATHS]

        manifest = build_manifest(files)

        write_manifest(manifest)

        validate_staging_directory(manifest)

        promote_staging_directory()

    except Exception:
        if STAGING_DIR.exists():
            shutil.rmtree(STAGING_DIR)

        raise

    return manifest


def format_bytes(
    value: float,
) -> str:
    """Formata bytes para apresentação."""
    size = float(value)

    if size < 1024:
        return f"{size:.0f} B"

    size /= 1024

    if size < 1024:
        return f"{size:.2f} KB"

    size /= 1024

    return f"{size:.2f} MB"


def print_summary(
    manifest: dict[str, Any],
) -> None:
    """Exibe resumo da sincronização."""
    print("=" * 108)

    print("SERVING → FRONTEND — SINCRONIZAÇÃO DE CONTRATOS")

    print("=" * 108)

    print()

    print(f"Contratos sincronizados : {manifest['contract_count']}")

    print(f"Tamanho sincronizado    : {format_bytes(manifest['total_size_bytes'])}")

    print()

    print("Excluídos deliberadamente:")

    for pattern in manifest["excluded"]:
        print(f"  {pattern}")

    print()

    print("Destino:")

    print("  " + OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix())

    print()

    print("STATUS: CONTRATOS WEB SINCRONIZADOS E VALIDADOS")


def main() -> None:
    """Executa o sincronizador."""
    manifest = synchronize()

    print_summary(manifest)


if __name__ == "__main__":
    main()
