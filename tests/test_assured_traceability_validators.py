"""Tests for assured.traceability_validators."""

from sdlc_assured_scripts.assured.ids import IdRecord
from sdlc_assured_scripts.assured.traceability_validators import (
    ValidatorResult,
    cited_ids_resolve,
    id_uniqueness,
    orphan_ids,
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


def test_cited_ids_resolve_passes_when_all_targets_exist():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]
        ),
    ]
    result = cited_ids_resolve(records)
    assert result.passed is True


def test_cited_ids_resolve_fails_on_missing_target():
    records = [
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-999"]
        ),
    ]
    result = cited_ids_resolve(records)
    assert result.passed is False
    assert any("REQ-auth-999" in e for e in result.errors)
    assert any("DES-auth-001" in e for e in result.errors)


def test_orphan_ids_warns_when_req_never_cited():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="REQ-auth-002", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]
        ),
    ]
    result = orphan_ids(records)
    assert result.passed is True
    assert any("REQ-auth-002" in w for w in result.warnings)


def test_orphan_ids_does_not_warn_for_test_or_code():
    """TEST and CODE are leaves — they cite, but nothing cites them."""
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(
            id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]
        ),
        IdRecord(
            id="TEST-auth-001",
            kind="TEST",
            source="c.md",
            satisfies=["REQ-auth-001", "DES-auth-001"],
        ),
    ]
    result = orphan_ids(records)
    assert result.passed is True
    assert result.warnings == []
