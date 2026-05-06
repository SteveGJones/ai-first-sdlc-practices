"""Tests for sdlc_knowledge_base_scripts.confidence."""

from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.confidence import (
    COMBINATION_TABLE,
    combine_confidence,
    check_confidence_compliance,
    parse_finding_confidence,
)


def _write_lib_file(path: Path, confidence: str | None = "high") -> None:
    conf_line = f"confidence: {confidence}\n" if confidence is not None else ""
    path.write_text(
        f"---\ntitle: Test\ndomain: testing\nlayer: methodology\n{conf_line}status: active\n---\n## Key Question\nWhat?\n",
        encoding="utf-8",
    )


def test_combine_all_table_entries() -> None:
    expected = {
        ("high", "direct"): "high",
        ("high", "supporting"): "medium",
        ("high", "tangential"): "medium",
        ("medium", "direct"): "medium",
        ("medium", "supporting"): "medium",
        ("medium", "tangential"): "low",
        ("low", "direct"): "low",
        ("low", "supporting"): "low",
        ("low", "tangential"): "low",
        ("unknown", "direct"): "medium",
        ("unknown", "supporting"): "low",
        ("unknown", "tangential"): "low",
    }
    for (source, rel), combined in expected.items():
        assert combine_confidence(source, rel) == combined, f"({source}, {rel})"


def test_combine_safe_fallback_for_unknown_input() -> None:
    assert combine_confidence("garbage", "garbage") == "low"
    assert combine_confidence("", "") == "low"


def test_combine_case_insensitive() -> None:
    assert combine_confidence("HIGH", "DIRECT") == "high"
    assert combine_confidence("Medium", "Supporting") == "medium"


def test_combination_table_has_twelve_entries() -> None:
    assert len(COMBINATION_TABLE) == 12


def test_parse_finding_all_tags_present() -> None:
    text = (
        "**Source library:** local\n"
        "**Source confidence:** high\n"
        "**Query relevance:** direct\n"
        "**Confidence:** high\n"
        "**File:** library/test.md\n"
    )
    sc, qr, comb = parse_finding_confidence(text)
    assert sc == "high"
    assert qr == "direct"
    assert comb == "high"


def test_parse_finding_missing_tags_returns_unknowns() -> None:
    assert parse_finding_confidence("**Finding:** Something.\n") == (
        "unknown",
        "unknown",
        "unknown",
    )


def test_parse_finding_partial_tags_returns_unknowns() -> None:
    text = "**Source confidence:** high\n**File:** test.md\n"
    assert parse_finding_confidence(text) == ("unknown", "unknown", "unknown")


def test_parse_finding_case_normalised() -> None:
    text = (
        "**Source confidence:** HIGH\n"
        "**Query relevance:** Direct\n"
        "**Confidence:** High\n"
    )
    sc, qr, comb = parse_finding_confidence(text)
    assert sc == "high"
    assert qr == "direct"
    assert comb == "high"


def test_check_compliance_passes_all_valid(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    _write_lib_file(lib / "a.md", "high")
    _write_lib_file(lib / "b.md", "medium")
    assert check_confidence_compliance(lib) == []


def test_check_compliance_flags_missing(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    _write_lib_file(lib / "no-conf.md", confidence=None)
    violations = check_confidence_compliance(lib)
    assert len(violations) == 1
    path, msg = violations[0]
    assert "no-conf.md" in path
    assert "missing" in msg.lower()


def test_check_compliance_flags_invalid_value(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    _write_lib_file(lib / "bad.md", "excellent")
    violations = check_confidence_compliance(lib)
    assert len(violations) == 1
    _, msg = violations[0]
    assert "excellent" in msg


def test_check_compliance_skips_excluded_files(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("# Index\n", encoding="utf-8")
    (lib / "log.md").write_text("# Log\n", encoding="utf-8")
    raw = lib / "raw"
    raw.mkdir()
    _write_lib_file(raw / "source.md", confidence=None)
    assert check_confidence_compliance(lib) == []
