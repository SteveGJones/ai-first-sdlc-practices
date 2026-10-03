"""Tests for sdlc_knowledge_base_scripts.library_files (issue #241)."""
import os
import unicodedata
from pathlib import Path

import pytest

from sdlc_knowledge_base_scripts.library_files import (
    BUILTIN_EXCLUDED_DIRS,
    discover_library_files,
    existing_excluded_dirs,
    is_library_file,
    load_exclusions,
    top_level_bucket,
)


def _write(path: Path, text: str = "# x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _rels(library: Path, files: list[Path]) -> list[str]:
    return [str(f.relative_to(library)) for f in files]


def test_builtin_excludes_raw_and_special_names(tmp_path: Path) -> None:
    _write(tmp_path / "a.md")
    _write(tmp_path / "raw" / "r.md")
    _write(tmp_path / "log.md")
    _write(tmp_path / "_index.md")
    _write(tmp_path / "_shelf-index.md")
    _write(tmp_path / "sub" / "b.md")
    assert BUILTIN_EXCLUDED_DIRS == frozenset({"raw"})
    assert _rels(tmp_path, discover_library_files(tmp_path)) == ["a.md", "sub/b.md"]


def test_raw_is_top_level_only(tmp_path: Path) -> None:
    _write(tmp_path / "sub" / "raw" / "kept.md")
    assert _rels(tmp_path, discover_library_files(tmp_path)) == ["sub/raw/kept.md"]


def test_ignore_file_excludes_top_level_and_nested(tmp_path: Path) -> None:
    _write(tmp_path / "keep.md")
    _write(tmp_path / "iso20022" / "a" / "x.md")
    _write(tmp_path / "vendor" / "exports" / "y.md")
    _write(tmp_path / "vendor" / "own.md")
    (tmp_path / ".kb-index-ignore").write_text(
        "# vendored dumps\n\niso20022/\nvendor/exports\n", encoding="utf-8"
    )
    assert _rels(tmp_path, discover_library_files(tmp_path)) == [
        "keep.md",
        "vendor/own.md",
    ]


def test_ignore_match_is_case_sensitive_and_warns(tmp_path: Path) -> None:
    _write(tmp_path / "Vendor" / "x.md")
    (tmp_path / ".kb-index-ignore").write_text("vendor\n", encoding="utf-8")
    warnings: list[str] = []
    excluded = load_exclusions(tmp_path, warnings)
    assert any("'vendor'" in w and "'Vendor'" in w and "case" in w for w in warnings)
    assert "vendor" not in excluded
    assert _rels(tmp_path, discover_library_files(tmp_path, excluded)) == [
        "Vendor/x.md"
    ]


def test_nested_wrong_case_entry_suggests_real_path(tmp_path: Path) -> None:
    _write(tmp_path / "Vendor" / "Exports" / "x.md")
    (tmp_path / ".kb-index-ignore").write_text("Vendor/exports\n", encoding="utf-8")
    warnings: list[str] = []
    load_exclusions(tmp_path, warnings)
    assert any("'Vendor/Exports'" in w and "case" in w for w in warnings)


def test_wrong_case_entry_not_in_exclusion_set_or_excluded_listing(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "Vendor" / "x.md")
    (tmp_path / ".kb-index-ignore").write_text("vendor\n", encoding="utf-8")
    excluded = load_exclusions(tmp_path, [])
    assert excluded == BUILTIN_EXCLUDED_DIRS
    assert existing_excluded_dirs(tmp_path, frozenset({"raw", "vendor"})) == []


def test_symlink_entry_gets_distinct_warning_and_is_not_excluded(
    tmp_path: Path,
) -> None:
    target = tmp_path / "real"
    _write(target / "x.md")
    (tmp_path / "link").symlink_to(target, target_is_directory=True)
    (tmp_path / ".kb-index-ignore").write_text("link\n", encoding="utf-8")
    warnings: list[str] = []
    excluded = load_exclusions(tmp_path, warnings)
    assert "link" not in excluded
    assert any(
        "'link'" in w and "symlink" in w and "unnecessary" in w for w in warnings
    )
    assert not any("matches no directory" in w for w in warnings)


def test_unreadable_directory_gets_distinct_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path / "locked" / "x.md")
    (tmp_path / ".kb-index-ignore").write_text("locked\n", encoding="utf-8")
    real_scandir = os.scandir

    def fake_scandir(path: "str | os.PathLike[str]") -> object:
        if Path(path) == tmp_path:
            raise PermissionError(13, "Permission denied")
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", fake_scandir)
    warnings: list[str] = []
    excluded = load_exclusions(tmp_path, warnings)
    assert "locked" not in excluded
    assert any("could not read" in w and "Permission denied" in w for w in warnings)
    assert not any("matches no directory" in w for w in warnings)


def test_correct_case_entry_has_no_warning(tmp_path: Path) -> None:
    _write(tmp_path / "Vendor" / "x.md")
    (tmp_path / ".kb-index-ignore").write_text("Vendor\n", encoding="utf-8")
    warnings: list[str] = []
    load_exclusions(tmp_path, warnings)
    assert warnings == []


def test_backslash_entry_tells_user_to_use_forward_slashes(tmp_path: Path) -> None:
    (tmp_path / ".kb-index-ignore").write_text("vendor\\exports\n", encoding="utf-8")
    warnings: list[str] = []
    load_exclusions(tmp_path, warnings)
    assert any("forward slashes" in w for w in warnings)


def test_ignore_file_with_utf8_bom_is_honoured(tmp_path: Path) -> None:
    _write(tmp_path / "iso20022" / "x.md")
    _write(tmp_path / "keep.md")
    (tmp_path / ".kb-index-ignore").write_bytes(b"\xef\xbb\xbfiso20022\n")
    warnings: list[str] = []
    excluded = load_exclusions(tmp_path, warnings)
    assert "iso20022" in excluded
    assert warnings == []
    assert _rels(tmp_path, discover_library_files(tmp_path, excluded)) == ["keep.md"]


def test_existing_excluded_dirs_lists_only_real_dirs(tmp_path: Path) -> None:
    _write(tmp_path / "raw" / "r.md")
    _write(tmp_path / "vendor" / "exports" / "y.md")
    excluded = frozenset({"raw", "vendor/exports", "ghost"})
    assert existing_excluded_dirs(tmp_path, excluded) == ["raw", "vendor/exports"]


def test_raw_cannot_be_negated(tmp_path: Path) -> None:
    _write(tmp_path / "raw" / "r.md")
    (tmp_path / ".kb-index-ignore").write_text("!raw\n", encoding="utf-8")
    assert "raw" in load_exclusions(tmp_path)
    assert discover_library_files(tmp_path) == []


def test_unsafe_entries_rejected_with_warning(tmp_path: Path) -> None:
    _write(tmp_path / "a" / "x.md")
    (tmp_path / ".kb-index-ignore").write_text("../a\n/etc\na/../a\n", encoding="utf-8")
    warnings: list[str] = []
    excluded = load_exclusions(tmp_path, warnings)
    assert excluded == BUILTIN_EXCLUDED_DIRS
    assert len([w for w in warnings if "rejected" in w]) == 3
    assert _rels(tmp_path, discover_library_files(tmp_path, excluded)) == ["a/x.md"]


def test_unmatched_entry_warns(tmp_path: Path) -> None:
    (tmp_path / ".kb-index-ignore").write_text("nonexistent\n", encoding="utf-8")
    warnings: list[str] = []
    excluded = load_exclusions(tmp_path, warnings)
    assert "nonexistent" not in excluded
    assert any("nonexistent" in w and "matches no" in w for w in warnings)


def test_symlinked_dir_outside_library_not_followed(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    _write(outside / "secret.md")
    library = tmp_path / "library"
    _write(library / "a.md")
    os.symlink(outside, library / "link", target_is_directory=True)
    assert _rels(library, discover_library_files(library)) == ["a.md"]


def test_is_library_file(tmp_path: Path) -> None:
    excluded = frozenset({"raw", "iso20022"})
    assert is_library_file(tmp_path / "a.md", tmp_path, excluded)
    assert not is_library_file(tmp_path / "log.md", tmp_path, excluded)
    assert not is_library_file(tmp_path / "a.txt", tmp_path, excluded)
    assert not is_library_file(tmp_path / "raw" / "a.md", tmp_path, excluded)
    assert not is_library_file(tmp_path / "iso20022" / "s" / "a.md", tmp_path, excluded)
    assert not is_library_file(tmp_path.parent / "a.md", tmp_path, excluded)
    assert is_library_file(tmp_path / "isoX" / "a.md", tmp_path, excluded)


def test_top_level_bucket() -> None:
    assert top_level_bucket("a.md") == "."
    assert top_level_bucket("iso20022/s/a.md") == "iso20022"


def _vendored_library(tmp_path: Path) -> Path:
    """Library with one real file lacking metadata and a vendored dump dir."""
    _write(
        tmp_path / "ok.md",
        "---\ntitle: T\nlayer: domain\nconfidence: high\n---\nbody\n",
    )
    _write(tmp_path / "iso20022" / "sub" / "dump.md", "no frontmatter\n")
    (tmp_path / ".kb-index-ignore").write_text("iso20022\n", encoding="utf-8")
    return tmp_path


def test_confidence_honours_ignore_file(tmp_path: Path) -> None:
    from sdlc_knowledge_base_scripts.confidence import check_confidence_compliance

    assert check_confidence_compliance(_vendored_library(tmp_path)) == []


def test_kb_config_honours_ignore_file(tmp_path: Path) -> None:
    from sdlc_knowledge_base_scripts.kb_config import check_layer_compliance

    assert check_layer_compliance(_vendored_library(tmp_path), ["domain"]) == []


def test_kb_lint_fix_honours_ignore_file(tmp_path: Path) -> None:
    from sdlc_knowledge_base_scripts.kb_lint_fix import fix_missing_fields

    library = _vendored_library(tmp_path)
    dump = library / "iso20022" / "sub" / "dump.md"
    before = dump.read_bytes()
    fix_missing_fields(library)
    assert dump.read_bytes() == before


def _nfd_dir(library: Path, nfc_name: str) -> str:
    """Create a directory named in NFD; return the name as listed on disk."""
    nfd = unicodedata.normalize("NFD", nfc_name)
    (library / nfd).mkdir()
    listed = [p.name for p in library.iterdir() if p.name != ".kb-index-ignore"]
    return listed[0]


def test_nfc_entry_matches_nfd_on_disk_name_and_prunes(tmp_path: Path) -> None:
    on_disk = _nfd_dir(tmp_path, "café")
    if on_disk != unicodedata.normalize("NFD", "café"):
        pytest.skip("filesystem normalises names; NFC/NFD mismatch cannot occur")
    _write(tmp_path / on_disk / "x.md")
    _write(tmp_path / "keep.md")
    nfc_entry = unicodedata.normalize("NFC", "café")
    assert nfc_entry != on_disk
    (tmp_path / ".kb-index-ignore").write_text(nfc_entry + "\n", encoding="utf-8")
    warnings: list[str] = []
    excluded = load_exclusions(tmp_path, warnings)
    assert warnings == []
    assert on_disk in excluded
    assert _rels(tmp_path, discover_library_files(tmp_path, excluded)) == ["keep.md"]
    assert on_disk in existing_excluded_dirs(tmp_path, excluded)


def test_nfc_comparison_keeps_exact_case_semantics(tmp_path: Path) -> None:
    on_disk = _nfd_dir(tmp_path, "Café")
    if on_disk != unicodedata.normalize("NFD", "Café"):
        pytest.skip("filesystem normalises names; NFC/NFD mismatch cannot occur")
    (tmp_path / ".kb-index-ignore").write_text("café\n", encoding="utf-8")
    warnings: list[str] = []
    excluded = load_exclusions(tmp_path, warnings)
    assert on_disk not in excluded
    assert any("case" in w and "matches no directory" not in w for w in warnings)


def test_symlink_warning_names_the_symlinked_component(tmp_path: Path) -> None:
    target = tmp_path / "real"
    _write(target / "sub" / "x.md")
    (tmp_path / "link").symlink_to(target, target_is_directory=True)
    (tmp_path / ".kb-index-ignore").write_text("link/sub\n", encoding="utf-8")
    warnings: list[str] = []
    excluded = load_exclusions(tmp_path, warnings)
    assert "link/sub" not in excluded
    assert any(
        "symlink 'link'" in w and "'link/sub' is a symlink" not in w for w in warnings
    )
    assert not any("matches no directory" in w for w in warnings)


def test_wrong_case_symlink_component_reports_case_difference(tmp_path: Path) -> None:
    target = tmp_path / "real"
    _write(target / "x.md")
    (tmp_path / "link").symlink_to(target, target_is_directory=True)
    (tmp_path / ".kb-index-ignore").write_text("LINK\n", encoding="utf-8")
    warnings: list[str] = []
    excluded = load_exclusions(tmp_path, warnings)
    assert "LINK" not in excluded
    assert any("'LINK'" in w and "'link'" in w and "case" in w for w in warnings)
    assert not any("matches no directory" in w for w in warnings)
