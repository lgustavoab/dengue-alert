"""Testes da auditoria integrada da camada de serving."""

import importlib.util
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

AUDIT_SCRIPT = PROJECT_ROOT / "scripts" / "auditar_serving_integrado.py"

SPEC = importlib.util.spec_from_file_location(
    "auditar_serving_integrado",
    AUDIT_SCRIPT,
)

if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Não foi possível carregar o script: {AUDIT_SCRIPT}")

audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def write_json(
    path: Path,
    payload: dict,
) -> None:
    """Escreve JSON auxiliar para os testes."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def test_load_json_strict_accepts_object(
    tmp_path: Path,
) -> None:
    """JSON finito e em formato de objeto deve ser aceito."""
    path = tmp_path / "valid.json"

    write_json(
        path,
        {
            "schema_version": "1.0",
            "value": 10,
        },
    )

    payload = audit.load_json_strict(path)

    assert payload["schema_version"] == "1.0"

    assert payload["value"] == 10


def test_load_json_strict_rejects_nan(
    tmp_path: Path,
) -> None:
    """NaN não deve ser aceito nos contratos de serving."""
    path = tmp_path / "invalid.json"

    path.write_text(
        '{"schema_version":"1.0","value":NaN}\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="JSON inválido",
    ):
        audit.load_json_strict(path)


def test_load_json_strict_rejects_non_object(
    tmp_path: Path,
) -> None:
    """Contrato raiz deve ser um objeto JSON."""
    path = tmp_path / "array.json"

    path.write_text(
        "[1,2,3]\n",
        encoding="utf-8",
    )

    with pytest.raises(
        TypeError,
        match="não é objeto",
    ):
        audit.load_json_strict(path)


def test_extract_index_codes_supports_historical_data_schema(
    tmp_path: Path,
) -> None:
    """Índice histórico deve aceitar a coleção data."""
    path = tmp_path / "historical-index.json"

    payload = {
        "schema_version": "1.0",
        "period": "2016-2025",
        "data": [
            {
                "codigo_ibge_7": "1111111",
            },
            {
                "codigo_ibge_7": "2222222",
            },
        ],
    }

    write_json(
        path,
        payload,
    )

    loaded, codes, count = audit.extract_index_codes(path)

    assert loaded["period"] == "2016-2025"

    assert codes == {
        "1111111",
        "2222222",
    }

    assert count == 2


def test_extract_index_codes_supports_prediction_items_schema(
    tmp_path: Path,
) -> None:
    """Índice preditivo deve aceitar items e validar count."""
    path = tmp_path / "prediction-index.json"

    payload = {
        "schema_version": "1.0",
        "count": 2,
        "items": [
            {
                "codigo_ibge_7": "1111111",
            },
            {
                "codigo_ibge_7": "2222222",
            },
        ],
    }

    write_json(
        path,
        payload,
    )

    _, codes, count = audit.extract_index_codes(path)

    assert codes == {
        "1111111",
        "2222222",
    }

    assert count == 2


def test_extract_index_codes_rejects_declared_count_divergence(
    tmp_path: Path,
) -> None:
    """Count declarado deve coincidir com códigos únicos."""
    path = tmp_path / "prediction-index.json"

    write_json(
        path,
        {
            "schema_version": "1.0",
            "count": 3,
            "items": [
                {
                    "codigo_ibge_7": "1111111",
                },
                {
                    "codigo_ibge_7": "2222222",
                },
            ],
        },
    )

    with pytest.raises(
        ValueError,
        match="Count divergente",
    ):
        audit.extract_index_codes(path)


def test_extract_index_codes_rejects_duplicate_code(
    tmp_path: Path,
) -> None:
    """Um índice não pode repetir o mesmo código IBGE."""
    path = tmp_path / "index.json"

    write_json(
        path,
        {
            "schema_version": "1.0",
            "data": [
                {
                    "codigo_ibge_7": "1111111",
                },
                {
                    "codigo_ibge_7": "1111111",
                },
            ],
        },
    )

    with pytest.raises(
        ValueError,
        match="Código duplicado",
    ):
        audit.extract_index_codes(path)


def test_validate_required_files_rejects_missing_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Contrato obrigatório ausente deve interromper a auditoria."""
    existing = tmp_path / "existing.json"

    missing = tmp_path / "missing.json"

    write_json(
        existing,
        {
            "schema_version": "1.0",
        },
    )

    monkeypatch.setattr(
        audit,
        "REQUIRED_FILES",
        [
            existing,
            missing,
        ],
    )

    monkeypatch.setattr(
        audit,
        "PROJECT_ROOT",
        tmp_path,
    )

    with pytest.raises(
        FileNotFoundError,
        match="Contratos obrigatórios ausentes",
    ):
        audit.validate_required_files()


def test_validate_territorial_relationship_accepts_expected_difference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Predição deve ser subconjunto do universo histórico."""
    historical = {
        "1111111",
        "2222222",
        "3333333",
        "4444444",
    }

    prediction = {
        "1111111",
        "2222222",
    }

    monkeypatch.setattr(
        audit,
        "EXPECTED_NON_PREDICTIVE_CODES",
        {
            "3333333",
            "4444444",
        },
    )

    result = audit.validate_territorial_relationship(
        historical,
        prediction,
    )

    assert result["historical"] == 4

    assert result["prediction"] == 2

    assert result["historical_only"] == [
        "3333333",
        "4444444",
    ]


def test_validate_territorial_relationship_rejects_prediction_outside_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Não pode existir município preditivo ausente do histórico."""
    monkeypatch.setattr(
        audit,
        "EXPECTED_NON_PREDICTIVE_CODES",
        set(),
    )

    with pytest.raises(
        ValueError,
        match="preditivos ausentes do histórico",
    ):
        audit.validate_territorial_relationship(
            {
                "1111111",
            },
            {
                "1111111",
                "2222222",
            },
        )


def test_validate_territorial_relationship_rejects_unexpected_gap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A diferença histórico × predição deve ser a documentada."""
    monkeypatch.setattr(
        audit,
        "EXPECTED_NON_PREDICTIVE_CODES",
        {
            "3333333",
        },
    )

    with pytest.raises(
        ValueError,
        match="Diferença territorial",
    ):
        audit.validate_territorial_relationship(
            {
                "1111111",
                "2222222",
            },
            {
                "1111111",
            },
        )


def test_write_audit_creates_strict_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auditoria estruturada deve ser gravada em JSON válido."""
    output = tmp_path / "auditoria.json"

    monkeypatch.setattr(
        audit,
        "AUDIT_FILE",
        output,
    )

    audit.write_audit(
        {
            "schema_version": "1.0",
            "status": "APROVADO",
            "checks": {
                "strict_json": True,
            },
        }
    )

    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["status"] == "APROVADO"

    assert payload["checks"]["strict_json"] is True


def test_write_audit_rejects_nan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auditoria persistida também não pode conter NaN."""
    output = tmp_path / "auditoria.json"

    monkeypatch.setattr(
        audit,
        "AUDIT_FILE",
        output,
    )

    with pytest.raises(
        ValueError,
    ):
        audit.write_audit(
            {
                "schema_version": "1.0",
                "value": float("nan"),
            }
        )
