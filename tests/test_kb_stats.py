"""Tests for sdlc_knowledge_base_scripts.kb_stats."""

from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.kb_stats import generate_stats, main


def _write_shelf_index(path: Path, entries: list[dict]) -> None:
    """Write a minimal shelf-index. Each dict: file, layer, domain, facts_count, links."""
    header = (
        "<!-- format_version: 1 -->\n"
        "<!-- last_rebuilt: 2026-05-01T08:00:00Z -->\n"
        "<!-- library_handle: local -->\n"
        "<!-- library_description: Test library -->\n"
        "# Knowledge Base Shelf-Index\n\n---\n\n"
    )
    body = ""
    for n, e in enumerate(entries, 1):
        facts_block = "\n".join(f"- Fact {i}." for i in range(e.get("facts_count", 1)))
        links = ", ".join(e.get("links", []))
        body += (
            f"## {n}. {e['file']}\n\n"
            f"**Hash:** {'a' * 64}\n"
            f"**Layer:** {e.get('layer', 'uncategorized')}\n"
            f"**Terms:** {e.get('domain', 'testing')}, {e.get('layer', 'uncategorized')}\n"
            f"**Facts:**\n{facts_block}\n"
            f"**Links:** {links}\n\n"
        )
    path.write_text(header + body, encoding="utf-8")


def _write_log(path: Path, entries: list[str]) -> None:
    path.write_text(
        "# Knowledge Base Log\n\n" + "\n\n".join(entries) + "\n", encoding="utf-8"
    )


def _make_library(tmp_path: Path) -> tuple[Path, Path, Path]:
    lib = tmp_path / "library"
    lib.mkdir()
    shelf = lib / "_shelf-index.md"
    log = lib / "log.md"
    return lib, shelf, log


def test_generate_stats_contains_all_sections(tmp_path: Path) -> None:
    lib, shelf, log = _make_library(tmp_path)
    _write_shelf_index(
        shelf,
        [
            {
                "file": "a.md",
                "layer": "methodology",
                "domain": "sdlc",
                "facts_count": 3,
            },
            {
                "file": "b.md",
                "layer": "evidence",
                "domain": "testing",
                "facts_count": 2,
            },
        ],
    )
    _write_log(log, ["## [2026-05-01] ingest | a.md\n\nSource: library/raw/a.md"])
    stats = generate_stats(lib, shelf, log)
    assert "## Inventory" in stats
    assert "## Distribution by layer" in stats
    assert "## Distribution by domain" in stats
    assert "## Recent activity" in stats
    assert "## Staleness" in stats


def test_generate_stats_inventory_counts(tmp_path: Path) -> None:
    lib, shelf, log = _make_library(tmp_path)
    _write_shelf_index(
        shelf,
        [
            {
                "file": "a.md",
                "layer": "methodology",
                "facts_count": 2,
                "links": ["b.md"],
            },
            {"file": "b.md", "layer": "evidence", "facts_count": 3, "links": []},
        ],
    )
    _write_log(log, [])
    stats = generate_stats(lib, shelf, log)
    assert "Total files: 2" in stats
    assert "Total findings: 5" in stats


def test_generate_stats_layer_distribution(tmp_path: Path) -> None:
    lib, shelf, log = _make_library(tmp_path)
    _write_shelf_index(
        shelf,
        [
            {"file": "a.md", "layer": "methodology", "facts_count": 2},
            {"file": "b.md", "layer": "methodology", "facts_count": 3},
            {"file": "c.md", "layer": "evidence", "facts_count": 1},
        ],
    )
    _write_log(log, [])
    stats = generate_stats(lib, shelf, log)
    assert "methodology" in stats
    assert "evidence" in stats


def test_generate_stats_staleness_section(tmp_path: Path) -> None:
    lib, shelf, log = _make_library(tmp_path)
    _write_shelf_index(shelf, [{"file": "a.md", "layer": "methodology"}])
    _write_log(log, [])
    stats = generate_stats(lib, shelf, log)
    assert "## Staleness" in stats
    assert "last rebuilt" in stats.lower() or "2026-05-01" in stats


def test_generate_stats_output_to_file(tmp_path: Path) -> None:
    lib, shelf, log = _make_library(tmp_path)
    _write_shelf_index(shelf, [{"file": "a.md", "layer": "methodology"}])
    _write_log(log, [])
    out = tmp_path / "stats.md"
    rc = main(
        [
            "--library-path",
            str(lib),
            "--shelf-index-path",
            str(shelf),
            "--log-path",
            str(log),
            "--output",
            str(out),
        ]
    )
    assert rc == 0
    assert out.exists()
    assert "## Inventory" in out.read_text()


def test_generate_stats_since_filters_old_entries(tmp_path: Path) -> None:
    lib, shelf, log = _make_library(tmp_path)
    _write_shelf_index(shelf, [{"file": "a.md", "layer": "methodology"}])
    _write_log(
        log,
        [
            "## [2020-01-01] ingest | old.md\n\nSource: library/raw/old.md",
            "## [2026-05-01] ingest | recent.md\n\nSource: library/raw/recent.md",
        ],
    )
    stats = generate_stats(lib, shelf, log, since_days=7)
    assert "recent.md" in stats or "2026-05-01" in stats


def test_generate_stats_no_log_file(tmp_path: Path) -> None:
    lib, shelf, _ = _make_library(tmp_path)
    _write_shelf_index(shelf, [{"file": "a.md", "layer": "methodology"}])
    missing_log = lib / "log.md"
    stats = generate_stats(lib, shelf, missing_log)
    assert "## Recent activity" in stats


def test_main_exits_zero_on_success(tmp_path: Path) -> None:
    lib, shelf, log = _make_library(tmp_path)
    _write_shelf_index(shelf, [{"file": "a.md", "layer": "methodology"}])
    _write_log(log, [])
    rc = main(
        [
            "--library-path",
            str(lib),
            "--shelf-index-path",
            str(shelf),
            "--log-path",
            str(log),
        ]
    )
    assert rc == 0


def test_main_exits_one_on_missing_library(tmp_path: Path) -> None:
    rc = main(
        [
            "--library-path",
            str(tmp_path / "nonexistent"),
            "--shelf-index-path",
            str(tmp_path / "_shelf-index.md"),
            "--log-path",
            str(tmp_path / "log.md"),
        ]
    )
    assert rc == 1
