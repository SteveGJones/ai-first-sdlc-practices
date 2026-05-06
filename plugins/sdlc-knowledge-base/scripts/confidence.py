"""Confidence metadata helpers for sdlc-knowledge-base."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

VALID_CONFIDENCE_VALUES: frozenset[str] = frozenset({"high", "medium", "low"})
VALID_RELEVANCE_VALUES: frozenset[str] = frozenset(
    {"direct", "supporting", "tangential"}
)

COMBINATION_TABLE: dict[tuple[str, str], str] = {
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

_EXCLUDED_NAMES = frozenset({"_shelf-index.md", "_index.md", "log.md"})
_EXCLUDED_DIRS = frozenset({"raw"})
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_SOURCE_CONF_RE = re.compile(r"^\*\*Source confidence:\*\*\s+(\S+)", re.MULTILINE)
_QUERY_REL_RE = re.compile(r"^\*\*Query relevance:\*\*\s+(\S+)", re.MULTILINE)
_COMBINED_RE = re.compile(r"^\*\*Confidence:\*\*\s+(\S+)", re.MULTILINE)


def combine_confidence(source: str, relevance: str) -> str:
    """Look up combined confidence. Returns 'low' for unrecognised inputs."""
    key = (source.strip().lower(), relevance.strip().lower())
    return COMBINATION_TABLE.get(key, "low")


def parse_finding_confidence(text: str) -> tuple[str, str, str]:
    """Extract (source_confidence, query_relevance, combined) from a finding block.

    Returns ('unknown', 'unknown', 'unknown') if any tag is absent.
    """
    sc = _SOURCE_CONF_RE.search(text)
    qr = _QUERY_REL_RE.search(text)
    comb = _COMBINED_RE.search(text)
    if not (sc and qr and comb):
        return ("unknown", "unknown", "unknown")
    return (
        sc.group(1).strip().lower(),
        qr.group(1).strip().lower(),
        comb.group(1).strip().lower(),
    )


def _parse_frontmatter(text: str) -> dict[str, object]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    try:
        result = yaml.safe_load(m.group(1))
        return result if isinstance(result, dict) else {}
    except yaml.YAMLError:
        return {}


def _is_library_file(path: Path, library_path: Path) -> bool:
    if path.name in _EXCLUDED_NAMES:
        return False
    try:
        rel = path.relative_to(library_path)
    except ValueError:
        return False
    if rel.parts[0] in _EXCLUDED_DIRS:
        return False
    return path.suffix == ".md"


def check_confidence_compliance(library_path: Path) -> list[tuple[str, str]]:
    """Return (rel_path, error_msg) for files missing a valid confidence: field."""
    violations: list[tuple[str, str]] = []
    for md_file in sorted(library_path.rglob("*.md")):
        if not _is_library_file(md_file, library_path):
            continue
        rel = str(md_file.relative_to(library_path))
        text = md_file.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)
        val = fm.get("confidence", "")
        if not val:
            violations.append((rel, "missing `confidence:` field"))
        elif str(val).strip().lower() not in VALID_CONFIDENCE_VALUES:
            violations.append(
                (rel, f"invalid confidence '{val}' — must be high, medium, or low")
            )
    return violations


def main(args: list[str] | None = None) -> int:
    """CLI: check confidence compliance for a library directory."""
    import argparse

    parser = argparse.ArgumentParser(description="Check KB confidence compliance.")
    parser.add_argument("library_path", help="Path to the library directory")
    parsed = parser.parse_args(args)
    library_path = Path(parsed.library_path)
    if not library_path.is_dir():
        print(f"Error: '{library_path}' does not exist.", file=sys.stderr)
        return 1
    violations = check_confidence_compliance(library_path)
    if not violations:
        print("Confidence compliance: OK")
        return 0
    print(f"Confidence compliance: {len(violations)} violation(s)")
    for path, msg in violations:
        print(f"  {path}: {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
