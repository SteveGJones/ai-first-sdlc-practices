"""Unit tests for sdlc_knowledge_base_scripts.format_version."""
from pathlib import Path
from sdlc_knowledge_base_scripts.format_version import (
    parse_format_version,
    CURRENT_FORMAT_VERSION,
)


def test_format_version_header_v1(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("<!-- format_version: 1 -->\n# Shelf Index\n\nContent.\n")
    assert parse_format_version(shelf) == 1


def test_format_version_header_missing_treated_as_v1(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("# Shelf Index\n\nContent.\n")
    assert parse_format_version(shelf) == CURRENT_FORMAT_VERSION


def test_format_version_unknown_future_version(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("<!-- format_version: 99 -->\n# Shelf Index\n")
    assert parse_format_version(shelf) == 99


def test_format_version_header_must_be_first_line(tmp_path: Path) -> None:
    # Header on line 5 should NOT be picked up; treated as v1 legacy
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("# Shelf Index\n\n\n\n<!-- format_version: 99 -->\nContent.\n")
    assert parse_format_version(shelf) == CURRENT_FORMAT_VERSION


def test_format_version_malformed_header(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("<!-- format_version: not-a-number -->\n# Shelf Index\n")
    assert parse_format_version(shelf) == CURRENT_FORMAT_VERSION  # fall back
