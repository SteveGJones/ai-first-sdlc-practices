"""Shared library-file discovery for sdlc-knowledge-base (issue #241).

One definition of "which .md files belong to the library", used by the
shelf-index builder, confidence check, layer check and lint auto-fix so they
cannot drift apart.

Exclusions are directory paths relative to the library root. `raw/` is always
excluded (top level only). Further directories are listed one per line in
`<library>/.kb-index-ignore`; `#` comments and blank lines are ignored, there
are no globs, and an entry excludes that directory and everything under it.
"""
from __future__ import annotations

import os
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Optional

BUILTIN_EXCLUDED_DIRS: frozenset[str] = frozenset({"raw"})
EXCLUDED_NAMES: frozenset[str] = frozenset({"_shelf-index.md", "_index.md", "log.md"})
IGNORE_FILE_NAME = ".kb-index-ignore"


def _normalise_entry(line: str) -> Optional[str]:
    """Return a safe library-relative dir path for one ignore line, or None."""
    entry = line.strip().rstrip("/")
    if not entry or entry.startswith("/") or "\\" in entry:
        return None
    parts = PurePosixPath(entry).parts
    if not parts or ".." in parts or "." in parts:
        return None
    return "/".join(parts)


def _nfc(name: str) -> str:
    """Unicode NFC form, so macOS-NFD on-disk names match NFC-typed entries."""
    return unicodedata.normalize("NFC", name)


def _check_entry_case(library_path: Path, entry: str) -> tuple[str, str]:
    """Classify entry against the real directory names on disk.

    Returns (status, detail). status is one of:
      "exact"      every component matches a real directory name exactly (up to
                   Unicode normalisation); detail is the ON-DISK path, which
                   is what pruning compares against
      "case"       differs only by case; detail is the real-cased path
      "symlink"    a component is a symlink (the scan never follows it);
                   detail is the symlinked path component
      "unreadable" a directory could not be listed; detail is the reason
      "missing"    no directory matches
    Real names are listed rather than probed with is_dir(), because
    case-insensitive filesystems answer is_dir() for wrong-case names while
    pruning stays case-sensitive. Components are compared in NFC on both
    sides because macOS stores names as NFD while editors type NFC.
    """
    current = library_path
    real_parts: list[str] = []
    differs = False
    parts = PurePosixPath(entry).parts
    for index, part in enumerate(parts):
        try:
            with os.scandir(current) as it:
                children = list(it)
        except OSError as exc:
            reason = exc.strerror or exc.__class__.__name__
            return "unreadable", f"{current}: {reason}"
        wanted = _nfc(part)
        names = [c.name for c in children if c.is_dir(follow_symlinks=False)]
        links = [c.name for c in children if c.is_symlink() and c.is_dir()]
        exact = sorted(n for n in names if _nfc(n) == wanted)
        if exact:
            real = exact[0]
        elif any(_nfc(n) == wanted for n in links):
            return "symlink", "/".join([*real_parts, part])
        else:
            folded = sorted(
                n for n in names + links if _nfc(n).casefold() == wanted.casefold()
            )
            if not folded:
                return "missing", ""
            real = folded[0]
            differs = True
            if real in links:
                rest = list(parts[index + 1 :])
                return "case", "/".join([*real_parts, real, *rest])
        real_parts.append(real)
        current = current / real
    return ("case" if differs else "exact", "/".join(real_parts))


def load_exclusions(
    library_path: Path, warnings: Optional[list[str]] = None
) -> frozenset[str]:
    """Return built-in exclusions plus valid entries from `.kb-index-ignore`.

    Only entries naming a real directory with exact casing are honoured.
    Unsafe, wrong-case, unmatched, file and symlink entries are warned about
    (appended to `warnings` when supplied) and dropped.
    """
    sink: list[str] = warnings if warnings is not None else []
    excluded = set(BUILTIN_EXCLUDED_DIRS)
    ignore_file = library_path / IGNORE_FILE_NAME
    if not ignore_file.is_file():
        return frozenset(excluded)
    for raw_line in ignore_file.read_text(encoding="utf-8-sig").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entry = _normalise_entry(stripped)
        if entry is None:
            if "\\" in stripped:
                sink.append(
                    f"{IGNORE_FILE_NAME}: entry '{stripped}' rejected "
                    "(use forward slashes, not backslashes)"
                )
            else:
                sink.append(
                    f"{IGNORE_FILE_NAME}: entry '{stripped}' rejected (unsafe path)"
                )
            continue
        status, detail = _check_entry_case(library_path, entry)
        if status == "exact":
            excluded.add(detail)
        elif status == "case":
            sink.append(
                f"{IGNORE_FILE_NAME}: entry '{entry}' differs only in case from the "
                f"real directory '{detail}'; entries are case-sensitive, so use "
                f"'{detail}' (entry not applied)"
            )
        elif status == "symlink":
            sink.append(
                f"{IGNORE_FILE_NAME}: entry '{entry}' passes through the symlink "
                f"'{detail}', which the scan does not follow, so the entry is "
                "unnecessary (entry not applied)"
            )
        elif status == "unreadable":
            sink.append(
                f"{IGNORE_FILE_NAME}: could not read {detail} while checking entry "
                f"'{entry}' (entry not applied)"
            )
        else:
            sink.append(
                f"{IGNORE_FILE_NAME}: entry '{entry}' matches no directory "
                "(entry not applied)"
            )
    return frozenset(excluded)


def _rel_is_excluded(rel_dir: PurePosixPath, excluded: frozenset[str]) -> bool:
    """True when rel_dir or any ancestor is in excluded."""
    parts = rel_dir.parts
    return any("/".join(parts[:i]) in excluded for i in range(1, len(parts) + 1))


def is_library_file(path: Path, library_path: Path, excluded: frozenset[str]) -> bool:
    """True when path is an indexable .md file inside library_path."""
    if path.suffix != ".md" or path.name in EXCLUDED_NAMES:
        return False
    try:
        rel = path.relative_to(library_path)
    except ValueError:
        return False
    return not _rel_is_excluded(PurePosixPath(*rel.parts[:-1]), excluded)


def discover_library_files(
    library_path: Path, excluded: Optional[frozenset[str]] = None
) -> list[Path]:
    """Return sorted library .md files, pruning excluded trees without walking them."""
    active = excluded if excluded is not None else load_exclusions(library_path)
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(library_path, followlinks=False):
        rel_dir = Path(dirpath).relative_to(library_path)
        rel_posix = PurePosixPath(*rel_dir.parts)
        dirnames[:] = [d for d in dirnames if str(rel_posix / d) not in active]
        for name in filenames:
            if name.endswith(".md") and name not in EXCLUDED_NAMES:
                files.append(Path(dirpath) / name)
    return sorted(files)


def top_level_bucket(rel: str) -> str:
    """Return '.' for files at the library root, else the first path component."""
    parts = PurePosixPath(rel).parts
    return parts[0] if len(parts) > 1 else "."


def existing_excluded_dirs(library_path: Path, excluded: frozenset[str]) -> list[str]:
    """Return sorted excluded entries that exist as real directories, exact case.

    Lists only the ancestors of each entry instead of walking the excluded
    trees, so cost is independent of how large the excluded content is. No
    case-insensitive is_dir() probe is used.
    """
    found: set[str] = set()
    for entry in excluded:
        status, detail = _check_entry_case(library_path, entry)
        if status == "exact":
            found.add(detail)
    return sorted(found)
