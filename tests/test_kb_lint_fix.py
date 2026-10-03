"""Tests for sdlc_knowledge_base_scripts.kb_lint_fix."""

from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.kb_lint_fix import fix_missing_fields


def _write_complete(path: Path) -> None:
    path.write_text(
        "---\ntitle: Test\ndomain: testing\nlayer: methodology\nconfidence: high\n"
        "status: active\ncross_references: []\n---\n## Key Question\nWhat?\n",
        encoding="utf-8",
    )


def _write_partial(path: Path, missing: list[str]) -> None:
    fm: dict[str, str] = {
        "title": "Test",
        "domain": "testing",
        "layer": "methodology",
        "confidence": "high",
        "status": "active",
        "cross_references": "[]",
    }
    for key in missing:
        fm.pop(key, None)
    fm_str = "\n".join(f"{k}: {v}" for k, v in fm.items())
    path.write_text(f"---\n{fm_str}\n---\n## Key Question\nWhat?\n", encoding="utf-8")


def _write_no_frontmatter(
    path: Path, body: str = "# Some content\n\nNo YAML here.\n"
) -> None:
    path.write_text(body, encoding="utf-8")


def _make_lib(tmp_path: Path) -> Path:
    lib = tmp_path / "library"
    lib.mkdir()
    return lib


def test_fix_adds_missing_layer(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_partial(lib / "a.md", missing=["layer"])
    fix_missing_fields(lib)
    assert "layer: uncategorized" in (lib / "a.md").read_text()


def test_fix_adds_missing_confidence(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_partial(lib / "a.md", missing=["confidence"])
    fix_missing_fields(lib)
    assert "confidence: medium" in (lib / "a.md").read_text()


def test_fix_adds_missing_cross_references(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_partial(lib / "a.md", missing=["cross_references"])
    fix_missing_fields(lib)
    assert "cross_references: []" in (lib / "a.md").read_text()


def test_fix_adds_all_three_when_all_missing(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_partial(lib / "a.md", missing=["layer", "confidence", "cross_references"])
    result = fix_missing_fields(lib)
    assert result.files_fixed == 1
    assert result.fields_added == 3
    content = (lib / "a.md").read_text()
    assert "layer: uncategorized" in content
    assert "confidence: medium" in content
    assert "cross_references: []" in content


def test_fix_preserves_existing_fields(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_partial(lib / "a.md", missing=["cross_references"])
    fix_missing_fields(lib)
    content = (lib / "a.md").read_text()
    assert "title: Test" in content
    assert "domain: testing" in content
    assert "layer: methodology" in content
    assert "confidence: high" in content
    assert "status: active" in content


def test_fix_preserves_body_content(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_partial(lib / "a.md", missing=["cross_references"])
    fix_missing_fields(lib)
    content = (lib / "a.md").read_text()
    assert "## Key Question" in content
    assert "What?" in content


def test_fix_skips_complete_files(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_complete(lib / "a.md")
    result = fix_missing_fields(lib)
    assert result.files_fixed == 0
    assert result.files_skipped == 1


def test_fix_dry_run_reports_without_writing(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_partial(lib / "a.md", missing=["layer"])
    original = (lib / "a.md").read_text()
    result = fix_missing_fields(lib, dry_run=True)
    assert result.files_fixed == 1
    assert (lib / "a.md").read_text() == original


def test_fix_atomic_no_tmp_file_on_success(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_partial(lib / "a.md", missing=["layer"])
    fix_missing_fields(lib)
    assert not (lib / "a.md.tmp").exists()


def test_fix_creates_stub_for_file_without_frontmatter(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_no_frontmatter(lib / "my-topic.md")
    result = fix_missing_fields(lib)
    assert result.files_fixed == 1
    content = (lib / "my-topic.md").read_text()
    assert "---" in content
    assert "title:" in content


def test_stub_has_confidence_low(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_no_frontmatter(lib / "orphan.md")
    fix_missing_fields(lib)
    assert "confidence: low" in (lib / "orphan.md").read_text()


def test_stub_has_status_draft(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_no_frontmatter(lib / "orphan.md")
    fix_missing_fields(lib)
    assert "status: draft" in (lib / "orphan.md").read_text()


def test_stub_derives_title_from_filename(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    _write_no_frontmatter(lib / "my-research-topic.md")
    fix_missing_fields(lib)
    assert "title: My Research Topic" in (lib / "my-research-topic.md").read_text()


def test_fix_skips_excluded_files(tmp_path: Path) -> None:
    lib = _make_lib(tmp_path)
    (lib / "_shelf-index.md").write_text("# Index\n", encoding="utf-8")
    (lib / "log.md").write_text("# Log\n", encoding="utf-8")
    (lib / "_index.md").write_text("# Index2\n", encoding="utf-8")
    raw = lib / "raw"
    raw.mkdir()
    _write_no_frontmatter(raw / "source.md")
    result = fix_missing_fields(lib)
    assert result.files_fixed == 0
