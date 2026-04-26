"""Unit tests for sdlc_knowledge_base_scripts.shelf_index_header."""
from pathlib import Path
from sdlc_knowledge_base_scripts.shelf_index_header import (
    parse_shelf_index_header,
    ShelfIndexHeader,
    CURRENT_FORMAT_VERSION,
)


def test_parse_full_header(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text(
        "<!-- format_version: 1 -->\n"
        "<!-- last_rebuilt: 2026-04-26T15:30:00Z -->\n"
        "<!-- library_handle: corp-semi -->\n"
        "<!-- library_description: Corporate semiconductor findings 2024-2026 -->\n"
        "# Knowledge Base Shelf-Index\n"
    )
    header = parse_shelf_index_header(shelf)
    assert header.format_version == 1
    assert header.last_rebuilt == "2026-04-26T15:30:00Z"
    assert header.library_handle == "corp-semi"
    assert header.library_description == "Corporate semiconductor findings 2024-2026"


def test_parse_only_format_version_legacy(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("<!-- format_version: 1 -->\n# Shelf\n")
    header = parse_shelf_index_header(shelf)
    assert header.format_version == 1
    assert header.last_rebuilt is None
    assert header.library_handle is None
    assert header.library_description is None


def test_parse_no_header_legacy(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text("# Shelf\n## Entry\n")
    header = parse_shelf_index_header(shelf)
    assert header.format_version == CURRENT_FORMAT_VERSION
    assert header.last_rebuilt is None
    assert header.library_handle is None


def test_parse_unknown_future_version(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text(
        "<!-- format_version: 99 -->\n"
        "<!-- last_rebuilt: 2027-01-01T00:00:00Z -->\n"
        "# Shelf\n"
    )
    header = parse_shelf_index_header(shelf)
    assert header.format_version == 99
    assert header.last_rebuilt == "2027-01-01T00:00:00Z"


def test_parse_malformed_date_field(tmp_path: Path) -> None:
    shelf = tmp_path / "_shelf-index.md"
    shelf.write_text(
        "<!-- format_version: 1 -->\n"
        "<!-- last_rebuilt: not-a-date -->\n"
        "# Shelf\n"
    )
    header = parse_shelf_index_header(shelf)
    # Malformed date is parsed as the literal string; downstream consumers handle
    assert header.last_rebuilt == "not-a-date"


def test_parse_missing_file(tmp_path: Path) -> None:
    header = parse_shelf_index_header(tmp_path / "missing.md")
    assert header.format_version == CURRENT_FORMAT_VERSION
    assert header.last_rebuilt is None
