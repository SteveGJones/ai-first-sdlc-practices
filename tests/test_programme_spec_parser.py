"""Tests for plugins.sdlc-programme.scripts.programme.spec_parser."""
from pathlib import Path

import pytest

from sdlc_programme_scripts.programme.spec_parser import (
    ParsedSpec,
    SpecParseError,
    parse_spec,
)


def test_parse_requirements_spec_extracts_feature_id_and_req_ids(
    tmp_path: Path,
) -> None:
    """A valid requirements-spec yields the feature-id and all REQ-NNN headings."""
    spec_path = tmp_path / "requirements-spec.md"
    spec_path.write_text(
        "# Requirements Specification: Test Feature\n\n"
        "**Feature-id:** my-feature\n\n"
        "## Motivation\n\nWhy.\n\n"
        "## Requirements\n\n"
        "### REQ-my-feature-001\nFirst requirement.\n\n"
        "### REQ-my-feature-002\nSecond requirement.\n\n"
        "## Success criteria\n- [ ] one\n"
    )

    parsed = parse_spec(spec_path, phase="requirements")

    assert isinstance(parsed, ParsedSpec)
    assert parsed.feature_id == "my-feature"
    assert parsed.declared_ids == {"REQ-my-feature-001", "REQ-my-feature-002"}
    assert parsed.references == set()  # requirements-spec has no cross-phase refs


def test_parse_design_spec_extracts_des_ids_and_satisfies_references(
    tmp_path: Path,
) -> None:
    """A valid design-spec yields DES-IDs declared and REQ-IDs referenced via satisfies."""
    spec_path = tmp_path / "design-spec.md"
    spec_path.write_text(
        "# Design Specification: Test Feature\n\n"
        "**Feature-id:** my-feature\n\n"
        "## Approach\n\nHow.\n\n"
        "## Design elements\n\n"
        "### DES-my-feature-001 — first\n"
        "**satisfies:** REQ-my-feature-001\n\nDescription.\n\n"
        "### DES-my-feature-002 — second\n"
        "**satisfies:** REQ-my-feature-002, REQ-my-feature-003\n\nDescription.\n\n"
    )

    parsed = parse_spec(spec_path, phase="design")

    assert parsed.feature_id == "my-feature"
    assert parsed.declared_ids == {"DES-my-feature-001", "DES-my-feature-002"}
    assert parsed.references == {
        "REQ-my-feature-001",
        "REQ-my-feature-002",
        "REQ-my-feature-003",
    }


def test_parse_test_spec_extracts_test_ids_and_both_prior_phase_references(
    tmp_path: Path,
) -> None:
    """A valid test-spec yields TEST-IDs declared and both REQ + DES IDs referenced."""
    spec_path = tmp_path / "test-spec.md"
    spec_path.write_text(
        "# Test Specification: Test Feature\n\n"
        "**Feature-id:** my-feature\n\n"
        "## Test cases\n\n"
        "### TEST-my-feature-001 — first\n"
        "**satisfies:** REQ-my-feature-001 via DES-my-feature-001\n\nSetup.\n\n"
        "### TEST-my-feature-002 — second\n"
        "**satisfies:** REQ-my-feature-002, REQ-my-feature-003 via DES-my-feature-002\n\nSetup.\n\n"
    )

    parsed = parse_spec(spec_path, phase="test")

    assert parsed.feature_id == "my-feature"
    assert parsed.declared_ids == {"TEST-my-feature-001", "TEST-my-feature-002"}
    assert parsed.references == {
        "REQ-my-feature-001",
        "REQ-my-feature-002",
        "REQ-my-feature-003",
        "DES-my-feature-001",
        "DES-my-feature-002",
    }


def test_parse_spec_missing_feature_id_raises(tmp_path: Path) -> None:
    """A spec without a feature-id line raises SpecParseError."""
    spec_path = tmp_path / "requirements-spec.md"
    spec_path.write_text("# Requirements Specification\n\n## Motivation\n\nWhy.\n")

    with pytest.raises(SpecParseError, match="feature-id"):
        parse_spec(spec_path, phase="requirements")


def test_parse_spec_unknown_phase_raises(tmp_path: Path) -> None:
    """An unknown phase name raises SpecParseError."""
    spec_path = tmp_path / "spec.md"
    spec_path.write_text("**Feature-id:** test\n")

    with pytest.raises(SpecParseError, match="phase"):
        parse_spec(spec_path, phase="bogus")


def test_parse_spec_missing_file_raises(tmp_path: Path) -> None:
    """A non-existent file raises SpecParseError."""
    spec_path = tmp_path / "missing.md"

    with pytest.raises(SpecParseError, match="not found"):
        parse_spec(spec_path, phase="requirements")


def test_parse_spec_ignores_ids_in_code_blocks(tmp_path: Path) -> None:
    """IDs inside fenced code blocks are NOT counted as declared or referenced."""
    spec_path = tmp_path / "design-spec.md"
    spec_path.write_text(
        "**Feature-id:** my-feature\n\n"
        "### DES-my-feature-001 — real\n"
        "**satisfies:** REQ-my-feature-001\n\n"
        "Real description.\n\n"
        "```\n"
        "### DES-my-feature-999 — fake (in code block)\n"
        "**satisfies:** REQ-my-feature-999\n"
        "```\n"
    )

    parsed = parse_spec(spec_path, phase="design")

    assert parsed.declared_ids == {"DES-my-feature-001"}  # not -999
    assert parsed.references == {"REQ-my-feature-001"}  # not -999


def test_parse_spec_ignores_ids_in_blockquotes(tmp_path: Path) -> None:
    """IDs inside blockquote lines (> ...) are NOT counted as declared or referenced."""
    spec_path = tmp_path / "design-spec.md"
    spec_path.write_text(
        "**Feature-id:** my-feature\n\n"
        "### DES-my-feature-001 — real\n"
        "**satisfies:** REQ-my-feature-001\n\n"
        "> ### DES-my-feature-999 — fake (blockquote)\n"
        "> **satisfies:** REQ-my-feature-999\n"
    )

    parsed = parse_spec(spec_path, phase="design")

    assert parsed.declared_ids == {"DES-my-feature-001"}  # not -999
    assert parsed.references == {"REQ-my-feature-001"}  # not -999


def test_parse_spec_ignores_ids_in_inline_code(tmp_path: Path) -> None:
    """IDs inside inline code spans on a satisfies line are NOT extracted as references."""
    spec_path = tmp_path / "design-spec.md"
    spec_path.write_text(
        "**Feature-id:** my-feature\n\n"
        "### DES-my-feature-001 — real\n"
        "**satisfies:** REQ-my-feature-001\n\n"
        "### DES-my-feature-002 — inline-code satisfies\n"
        "**satisfies:** `REQ-my-feature-999`\n"
    )

    parsed = parse_spec(spec_path, phase="design")

    assert parsed.declared_ids == {"DES-my-feature-001", "DES-my-feature-002"}
    # REQ-my-feature-999 is inside backtick span — must NOT be extracted
    assert parsed.references == {"REQ-my-feature-001"}  # not -999


def test_parse_spec_ignores_ids_in_html_comments(tmp_path: Path) -> None:
    """IDs inside HTML comments (<!-- ... -->) are NOT counted as declared or referenced."""
    spec_path = tmp_path / "design-spec.md"
    spec_path.write_text(
        "**Feature-id:** my-feature\n\n"
        "### DES-my-feature-001 — real\n"
        "**satisfies:** REQ-my-feature-001\n\n"
        "<!-- ### DES-my-feature-999 — fake (html comment) -->\n"
        "<!-- **satisfies:** REQ-my-feature-999 -->\n"
    )

    parsed = parse_spec(spec_path, phase="design")

    assert parsed.declared_ids == {"DES-my-feature-001"}  # not -999
    assert parsed.references == {"REQ-my-feature-001"}  # not -999
