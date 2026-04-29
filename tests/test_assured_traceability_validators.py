"""Tests for assured.traceability_validators."""

from sdlc_assured_scripts.assured.ids import IdRecord
from sdlc_assured_scripts.assured.traceability_validators import (
    ValidatorResult,
    id_uniqueness,
)


def test_id_uniqueness_passes_when_all_ids_unique():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="REQ-auth-002", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]
        ),
    ]
    result = id_uniqueness(records)
    assert isinstance(result, ValidatorResult)
    assert result.passed is True
    assert result.errors == []


def test_id_uniqueness_fails_on_duplicate():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="REQ-auth-001", kind="REQ", source="b.md", satisfies=[]),
    ]
    result = id_uniqueness(records)
    assert result.passed is False
    assert any("duplicate" in e.lower() for e in result.errors)
    assert any("REQ-auth-001" in e for e in result.errors)
