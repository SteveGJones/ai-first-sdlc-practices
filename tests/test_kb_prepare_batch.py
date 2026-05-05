"""Integration tests for sdlc_knowledge_base_scripts.kb_prepare_batch."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from sdlc_knowledge_base_scripts.kb_prepare_batch import (
    detect_converter,
    prepare_batch,
    write_provenance_frontmatter,
)


def _write_md(path: Path, content: str = "# Content\n\nSome text.\n") -> None:
    path.write_text(content, encoding="utf-8")


def test_detect_converter_md_passthrough() -> None:
    assert detect_converter(Path("file.md")) == "passthrough"


def test_detect_converter_pdf_returns_markitdown() -> None:
    assert detect_converter(Path("file.pdf")) == "markitdown"


def test_detect_converter_docx_returns_markitdown() -> None:
    assert detect_converter(Path("file.docx")) == "markitdown"


def test_detect_converter_tex_returns_pandoc() -> None:
    assert detect_converter(Path("file.tex")) == "pandoc"


def test_detect_converter_epub_returns_pandoc() -> None:
    assert detect_converter(Path("file.epub")) == "pandoc"


def test_detect_converter_unknown_returns_none() -> None:
    assert detect_converter(Path("file.xyz")) is None


def test_write_provenance_frontmatter_adds_metadata() -> None:
    content = write_provenance_frontmatter("~/Downloads/test.pdf", "markitdown", "Body content.\n")
    assert "source: ~/Downloads/test.pdf" in content
    assert "converted_by: markitdown" in content
    assert "converted_at:" in content
    assert "status: raw" in content
    assert "Body content." in content


def test_write_provenance_frontmatter_passthrough_has_status_raw() -> None:
    content = write_provenance_frontmatter("~/docs/notes.md", "passthrough", "# Notes\n")
    assert "status: raw" in content
    assert "converted_by: passthrough" in content


def test_prepare_batch_copies_md_files(tmp_path: Path) -> None:
    src = tmp_path / "docs"
    src.mkdir()
    raw = tmp_path / "library" / "raw"
    raw.mkdir(parents=True)
    _write_md(src / "a.md")
    _write_md(src / "b.md")

    result = prepare_batch([src / "a.md", src / "b.md"], raw, mode="copy")
    assert result.staged == 2
    assert result.failed == 0
    assert (raw / "a.md").exists()
    assert (raw / "b.md").exists()
    assert (src / "a.md").exists()  # originals intact on copy


def test_prepare_batch_moves_md_files(tmp_path: Path) -> None:
    src = tmp_path / "docs"
    src.mkdir()
    raw = tmp_path / "library" / "raw"
    raw.mkdir(parents=True)
    _write_md(src / "note.md")

    result = prepare_batch([src / "note.md"], raw, mode="move")
    assert result.staged == 1
    assert (raw / "note.md").exists()
    assert not (src / "note.md").exists()  # moved away


def test_prepare_batch_refuses_overwrite_by_default(tmp_path: Path) -> None:
    src = tmp_path / "docs"
    src.mkdir()
    raw = tmp_path / "library" / "raw"
    raw.mkdir(parents=True)
    _write_md(src / "a.md")
    (raw / "a.md").write_text("existing", encoding="utf-8")

    result = prepare_batch([src / "a.md"], raw, mode="copy")
    assert result.skipped == 1
    assert (raw / "a.md").read_text() == "existing"


def test_prepare_batch_overwrites_when_flag_set(tmp_path: Path) -> None:
    src = tmp_path / "docs"
    src.mkdir()
    raw = tmp_path / "library" / "raw"
    raw.mkdir(parents=True)
    _write_md(src / "a.md", "# New content")
    (raw / "a.md").write_text("old content", encoding="utf-8")

    result = prepare_batch([src / "a.md"], raw, mode="copy", overwrite=True)
    assert result.staged == 1
    assert "New content" in (raw / "a.md").read_text()


def test_prepare_batch_converts_pdf_via_markitdown(tmp_path: Path) -> None:
    src = tmp_path / "docs"
    src.mkdir()
    raw = tmp_path / "library" / "raw"
    raw.mkdir(parents=True)
    pdf = src / "report.pdf"
    pdf.write_bytes(b"%PDF fake content")

    with patch("sdlc_knowledge_base_scripts.kb_prepare_batch.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="# Converted content\n", stderr="")
        result = prepare_batch([pdf], raw, mode="copy")

    assert result.staged == 1
    assert (raw / "report.md").exists()
    out_content = (raw / "report.md").read_text()
    assert "converted_by: markitdown" in out_content
    assert "status: raw" in out_content


def test_prepare_batch_converts_tex_via_pandoc(tmp_path: Path) -> None:
    src = tmp_path / "docs"
    src.mkdir()
    raw = tmp_path / "library" / "raw"
    raw.mkdir(parents=True)
    tex = src / "paper.tex"
    tex.write_text("\\documentclass{article}\\begin{document}Hello\\end{document}", encoding="utf-8")

    with patch("sdlc_knowledge_base_scripts.kb_prepare_batch.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="# Paper\n\nHello\n", stderr="")
        result = prepare_batch([tex], raw, mode="copy")

    assert result.staged == 1
    out_content = (raw / "paper.md").read_text()
    assert "converted_by: pandoc" in out_content


def test_prepare_batch_fails_unknown_extension(tmp_path: Path) -> None:
    src = tmp_path / "docs"
    src.mkdir()
    raw = tmp_path / "library" / "raw"
    raw.mkdir(parents=True)
    f = src / "file.xyz"
    f.write_bytes(b"binary data")

    result = prepare_batch([f], raw, mode="copy")
    assert result.failed == 1
    assert not (raw / "file.md").exists()


def test_prepare_batch_continues_after_individual_failure(tmp_path: Path) -> None:
    src = tmp_path / "docs"
    src.mkdir()
    raw = tmp_path / "library" / "raw"
    raw.mkdir(parents=True)
    _write_md(src / "good.md")
    bad = src / "bad.xyz"
    bad.write_bytes(b"binary")

    result = prepare_batch([src / "good.md", bad], raw, mode="copy")
    assert result.staged == 1
    assert result.failed == 1
