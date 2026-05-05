"""Stage source files into library/raw/ with optional format conversion.

Supports copy/move mode and converts non-markdown formats via markitdown
(PDF/DOCX/PPTX/XLSX/HTML/CSV) or pandoc (TeX/EPUB/RST/ORG).  Adds YAML
provenance frontmatter to every staged file.

CLI usage::

    python3 -m sdlc_knowledge_base_scripts.kb_prepare_batch \\
        --target-dir library/raw/ \\
        --copy \\
        file1.pdf file2.md

Or via --from manifest (one path per line)::

    python3 -m sdlc_knowledge_base_scripts.kb_prepare_batch \\
        --from batch.txt --target-dir library/raw/ --move
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MARKITDOWN_EXTS = frozenset({".pdf", ".docx", ".pptx", ".xlsx", ".html", ".csv"})
_PANDOC_EXTS = frozenset({".tex", ".epub", ".rst", ".org"})


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class BatchResult:
    """Aggregate result of a prepare_batch run."""

    staged: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class ConversionError(Exception):
    """Raised when markitdown or pandoc exits non-zero."""


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def detect_converter(path: Path) -> str | None:
    """Return the converter name for *path*, or None if unsupported."""
    suffix = path.suffix.lower()
    if suffix == ".md":
        return "passthrough"
    if suffix in _MARKITDOWN_EXTS:
        return "markitdown"
    if suffix in _PANDOC_EXTS:
        return "pandoc"
    return None


def write_provenance_frontmatter(source: str, converter: str, body: str) -> str:
    """Prepend YAML frontmatter with provenance metadata to *body*."""
    converted_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    frontmatter = (
        "---\n"
        f"source: {source}\n"
        f"converted_by: {converter}\n"
        f"converted_at: {converted_at}\n"
        "status: raw\n"
        "---\n"
    )
    return frontmatter + body


# ---------------------------------------------------------------------------
# Internal conversion runners
# ---------------------------------------------------------------------------


def _run_markitdown(source: Path) -> str:
    """Run markitdown and return markdown text, or raise ConversionError."""
    proc = subprocess.run(
        ["markitdown", str(source)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise ConversionError(
            f"markitdown failed ({proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.stdout


def _run_pandoc(source: Path) -> str:
    """Run pandoc and return markdown text, or raise ConversionError."""
    proc = subprocess.run(
        ["pandoc", str(source), "-t", "markdown"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise ConversionError(
            f"pandoc failed ({proc.returncode}): {proc.stderr.strip()}"
        )
    return proc.stdout


# ---------------------------------------------------------------------------
# Core batch function
# ---------------------------------------------------------------------------


def prepare_batch(
    sources: list[Path],
    target_dir: Path,
    mode: str = "copy",
    converter_override: str | None = None,
    overwrite: bool = False,
) -> BatchResult:
    """Stage *sources* into *target_dir*, converting as needed.

    Args:
        sources: File paths to stage.
        target_dir: Destination directory (must exist).
        mode: ``"copy"`` leaves originals in place; ``"move"`` removes them.
        converter_override: Force ``"markitdown"`` or ``"pandoc"`` for all files.
        overwrite: When False (default) skip files already present in target_dir.

    Returns:
        :class:`BatchResult` with staged/skipped/failed counts.
    """
    result = BatchResult()

    for source in sources:
        try:
            converter = converter_override or detect_converter(source)
            if converter is None:
                raise ConversionError(f"unsupported extension '{source.suffix}'")

            dest_name = source.stem + ".md"
            dest = target_dir / dest_name

            if dest.exists() and not overwrite:
                result.skipped += 1
                continue

            if converter == "passthrough":
                body = source.read_text(encoding="utf-8")
            elif converter == "markitdown":
                body = _run_markitdown(source)
            else:
                body = _run_pandoc(source)

            final_content = write_provenance_frontmatter(str(source), converter, body)
            dest.write_text(final_content, encoding="utf-8")

            if mode == "move":
                source.unlink()

            result.staged += 1

        except Exception as exc:  # noqa: BLE001
            result.failed += 1
            result.errors.append(f"{source.name}: {exc}")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(args: list[str] | None = None) -> int:
    """Entry point for kb_prepare_batch CLI."""
    parser = argparse.ArgumentParser(
        description="Stage source files into library/raw/ with optional conversion."
    )
    parser.add_argument("sources", nargs="*", type=Path, help="Source file paths")
    parser.add_argument(
        "--from", dest="manifest", type=Path, help="File with one path per line"
    )
    parser.add_argument(
        "--target-dir", required=True, type=Path, help="Destination raw/ directory"
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--copy", dest="mode", action="store_const", const="copy", default="copy"
    )
    mode_group.add_argument("--move", dest="mode", action="store_const", const="move")

    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing files"
    )

    conv_group = parser.add_mutually_exclusive_group()
    conv_group.add_argument(
        "--force-markitdown",
        dest="converter_override",
        action="store_const",
        const="markitdown",
    )
    conv_group.add_argument(
        "--force-pandoc",
        dest="converter_override",
        action="store_const",
        const="pandoc",
    )

    ns = parser.parse_args(args)

    source_paths: list[Path] = list(ns.sources)
    if ns.manifest:
        lines = ns.manifest.read_text(encoding="utf-8").splitlines()
        source_paths.extend(Path(line.strip()) for line in lines if line.strip())

    if not source_paths:
        print("No source files specified.", file=sys.stderr)
        return 1

    result = prepare_batch(
        source_paths,
        ns.target_dir,
        mode=ns.mode,
        converter_override=ns.converter_override,
        overwrite=ns.overwrite,
    )

    print("Batch preparation complete:")
    print(f"  Staged:  {result.staged}")
    print(f"  Skipped: {result.skipped}")
    print(f"  Failed:  {result.failed}")

    if result.errors:
        print("\nIssues:")
        for err in result.errors:
            print(f"  - {err}")

    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
