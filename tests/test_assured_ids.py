"""Tests for assured.ids — positional namespace ID parsing."""

from pathlib import Path

import pytest

from sdlc_assured_scripts.assured.ids import (
    IdParseError,
    IdRecord,
    ParsedId,
    RemapResult,
    build_id_registry,
    format_id,
    is_positional,
    parse_id,
    remap_ids,
    render_id_registry,
)


def test_parse_flat_id() -> None:
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


def test_parse_positional_id() -> None:
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


def test_parse_positional_id_kinds() -> None:
    for kind in ("REQ", "DES", "TEST", "CODE"):
        parsed = parse_id(f"P1.SP1.M1.{kind}-001")
        assert parsed.kind == kind


def test_parse_invalid_id_raises() -> None:
    with pytest.raises(IdParseError):
        parse_id("not-an-id")
    with pytest.raises(IdParseError):
        parse_id("REQ-AUTH-001")  # uppercase feature
    with pytest.raises(IdParseError):
        parse_id("P1.SP2.REQ-007")  # missing module


def test_format_id_flat_round_trip() -> None:
    parsed = parse_id("REQ-auth-001")
    assert format_id(parsed) == "REQ-auth-001"


def test_format_id_positional_round_trip() -> None:
    parsed = parse_id("P1.SP2.M3.REQ-007")
    assert format_id(parsed) == "P1.SP2.M3.REQ-007"


def test_default_namespace_is_implicit() -> None:
    """A flat ID is treated as living in P1.SP1.M1 by default."""
    parsed = parse_id("REQ-auth-001")
    assert parsed.program is None  # explicitly not stored
    # The validators apply P1.SP1.M1 as default when checking module assignment.


def test_build_id_registry_walks_specs(tmp_path: Path) -> None:
    feature_dir = tmp_path / "docs" / "specs" / "auth"
    feature_dir.mkdir(parents=True)
    (feature_dir / "requirements-spec.md").write_text(
        "### REQ-auth-001\nLogin must support OAuth.\n"
        "### REQ-auth-002\nSessions expire after 24h.\n"
    )
    (feature_dir / "design-spec.md").write_text(
        "### DES-auth-001\n**satisfies:** REQ-auth-001\nUse PKCE.\n"
    )
    (feature_dir / "test-spec.md").write_text(
        "### TEST-auth-001\n**satisfies:** REQ-auth-001 via DES-auth-001\nVerify PKCE flow.\n"
    )
    records = build_id_registry(tmp_path)
    by_id = {r.id: r for r in records}
    assert "REQ-auth-001" in by_id
    assert by_id["REQ-auth-001"].kind == "REQ"
    assert by_id["REQ-auth-001"].source.endswith("requirements-spec.md")
    assert by_id["DES-auth-001"].satisfies == ["REQ-auth-001"]
    assert by_id["TEST-auth-001"].satisfies == ["REQ-auth-001", "DES-auth-001"]


def test_render_id_registry_produces_markdown_table(tmp_path: Path) -> None:
    records = [
        IdRecord(
            id="REQ-auth-001",
            kind="REQ",
            source="docs/specs/auth/requirements-spec.md",
            satisfies=[],
        ),
        IdRecord(
            id="DES-auth-001",
            kind="DES",
            source="docs/specs/auth/design-spec.md",
            satisfies=["REQ-auth-001"],
        ),
    ]
    output = render_id_registry(records)
    assert "| ID | Kind | Source | Satisfies |" in output
    assert "| REQ-auth-001 | REQ | docs/specs/auth/requirements-spec.md |  |" in output
    assert (
        "| DES-auth-001 | DES | docs/specs/auth/design-spec.md | REQ-auth-001 |"
        in output
    )


def test_remap_ids_preserves_id_when_module_moves() -> None:
    """When a module's path changes, the ID stays the same; only the source path updates."""
    records = [
        IdRecord(
            id="P1.SP1.M1.REQ-001",
            kind="REQ",
            source="docs/specs/legacy/requirements-spec.md",
            satisfies=[],
        ),
    ]
    remapping = {"docs/specs/legacy/": "docs/specs/auth/"}
    result = remap_ids(records, remapping)
    assert result.records[0].id == "P1.SP1.M1.REQ-001"
    assert result.records[0].source == "docs/specs/auth/requirements-spec.md"


def test_remap_ids_no_op_when_no_paths_match() -> None:
    records = [
        IdRecord(
            id="REQ-auth-001",
            kind="REQ",
            source="docs/specs/auth/requirements-spec.md",
            satisfies=[],
        ),
    ]
    remapping = {"docs/specs/legacy/": "docs/specs/old/"}
    result = remap_ids(records, remapping)
    assert result.records == records
    assert result.warnings == []


def test_remap_ids_warns_on_multiple_prefix_match() -> None:
    records = [
        IdRecord(id="REQ-x-001", kind="REQ", source="docs/specs/foo/bar/spec.md", satisfies=[]),
    ]
    remapping = {
        "docs/specs/foo/": "renamed/foo/",
        "docs/specs/foo/bar/": "renamed/foobar/",
    }
    result = remap_ids(records, remapping, on_overlap="warn")
    assert result.records[0].source == "renamed/foobar/spec.md"
    assert any("multiple prefix match" in w.lower() for w in result.warnings)


def test_remap_ids_error_mode_raises_on_overlap() -> None:
    records = [IdRecord(id="REQ-x-001", kind="REQ", source="docs/specs/foo/bar/spec.md", satisfies=[])]
    remapping = {"docs/specs/foo/": "a/", "docs/specs/foo/bar/": "b/"}
    with pytest.raises(ValueError, match="multiple prefix match"):
        remap_ids(records, remapping, on_overlap="error")


def test_remap_ids_single_match_no_warning() -> None:
    records = [IdRecord(id="REQ-x-001", kind="REQ", source="docs/specs/foo/spec.md", satisfies=[])]
    remapping = {"docs/specs/foo/": "renamed/foo/"}
    result = remap_ids(records, remapping)
    assert result.records[0].source == "renamed/foo/spec.md"
    assert result.warnings == []


def test_remap_ids_invalid_on_overlap_value_raises() -> None:
    with pytest.raises(ValueError, match="on_overlap"):
        remap_ids([], {}, on_overlap="bogus")
