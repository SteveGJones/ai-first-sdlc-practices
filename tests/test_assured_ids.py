"""Tests for assured.ids — positional namespace ID parsing."""

import pytest

from sdlc_assured_scripts.assured.ids import (
    IdParseError,
    ParsedId,
    parse_id,
    format_id,
    is_positional,
)


def test_parse_flat_id():
    parsed = parse_id("REQ-auth-001")
    assert parsed == ParsedId(
        program=None,
        sub_program=None,
        module=None,
        kind="REQ",
        feature="auth",
        number=1,
    )
    assert is_positional(parsed) is False


def test_parse_positional_id():
    parsed = parse_id("P1.SP2.M3.REQ-007")
    assert parsed == ParsedId(
        program="P1",
        sub_program="SP2",
        module="M3",
        kind="REQ",
        feature=None,
        number=7,
    )
    assert is_positional(parsed) is True


def test_parse_positional_id_kinds():
    for kind in ("REQ", "DES", "TEST", "CODE"):
        parsed = parse_id(f"P1.SP1.M1.{kind}-001")
        assert parsed.kind == kind


def test_parse_invalid_id_raises():
    with pytest.raises(IdParseError):
        parse_id("not-an-id")
    with pytest.raises(IdParseError):
        parse_id("REQ-AUTH-001")  # uppercase feature
    with pytest.raises(IdParseError):
        parse_id("P1.SP2.REQ-007")  # missing module


def test_format_id_flat_round_trip():
    parsed = parse_id("REQ-auth-001")
    assert format_id(parsed) == "REQ-auth-001"


def test_format_id_positional_round_trip():
    parsed = parse_id("P1.SP2.M3.REQ-007")
    assert format_id(parsed) == "P1.SP2.M3.REQ-007"


def test_default_namespace_is_implicit():
    """A flat ID is treated as living in P1.SP1.M1 by default."""
    parsed = parse_id("REQ-auth-001")
    assert parsed.program is None  # explicitly not stored
    # The validators apply P1.SP1.M1 as default when checking module assignment.
