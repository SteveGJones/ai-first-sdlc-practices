"""File-type adapters for the v0.2.0 EvidenceIndexEntry registry."""

from __future__ import annotations

import re
import yaml as _yaml
from pathlib import Path
from typing import Iterable

from .evidence_index import EvidenceIndexEntry, EvidenceKind


_IMPLEMENTS_RE = re.compile(r"^\s*#\s*implements:\s*(?P<ids>.+)$")
_ID_TOKEN_RE = re.compile(
    r"\b((?:P\d+\.SP\d+\.M\d+\.)?(?:REQ|DES|TEST|CODE)-(?:[a-z0-9][a-z0-9-]*-)?\d+)\b"
)


class PythonCommentAdapter:
    """Adapter for Python `# implements: <ID>` annotations."""

    file_extensions = (".py",)

    def extract(
        self, files: list[Path], project_root: Path
    ) -> Iterable[EvidenceIndexEntry]:
        for f in files:
            if f.suffix not in self.file_extensions:
                continue
            if not f.is_file():
                continue
            text = f.read_text(encoding="utf-8")
            try:
                rel_path = str(f.relative_to(project_root))
            except ValueError:
                rel_path = str(f.name)
            for line_no, line in enumerate(text.splitlines(), start=1):
                m = _IMPLEMENTS_RE.match(line)
                if not m:
                    continue
                cited = _ID_TOKEN_RE.findall(m["ids"])
                yield EvidenceIndexEntry(
                    kind=EvidenceKind.PYTHON_COMMENT,
                    source=rel_path,
                    line=line_no,
                    cited_ids=cited,
                )


def _parse_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter from a markdown document. Returns None if no frontmatter."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return _yaml.safe_load(parts[1]) or {}
    except _yaml.YAMLError:
        return None


_HTML_IMPLEMENTS_RE = re.compile(r"<!--\s*implements:\s*(?P<ids>.+?)\s*-->")


class MarkdownHtmlCommentAdapter:
    """Adapter for markdown `<!-- implements: <ID> -->` HTML-comment annotations."""

    file_extensions = (".md",)

    def extract(
        self, files: list[Path], project_root: Path
    ) -> Iterable[EvidenceIndexEntry]:
        for f in files:
            if f.suffix not in self.file_extensions:
                continue
            if not f.is_file():
                continue
            text = f.read_text(encoding="utf-8")
            try:
                rel_path = str(f.relative_to(project_root))
            except ValueError:
                rel_path = str(f.name)
            for line_no, line in enumerate(text.splitlines(), start=1):
                m = _HTML_IMPLEMENTS_RE.search(line)
                if not m:
                    continue
                cited = _ID_TOKEN_RE.findall(m["ids"])
                yield EvidenceIndexEntry(
                    kind=EvidenceKind.MARKDOWN_HTML_COMMENT,
                    source=rel_path,
                    line=line_no,
                    cited_ids=cited,
                )


class YamlFrontmatterAdapter:
    """Adapter for `implements: [...]` in YAML frontmatter."""

    file_extensions = (".md",)

    def extract(
        self, files: list[Path], project_root: Path
    ) -> Iterable[EvidenceIndexEntry]:
        for f in files:
            if f.suffix not in self.file_extensions or not f.is_file():
                continue
            text = f.read_text(encoding="utf-8")
            fm = _parse_frontmatter(text)
            if not fm or "implements" not in fm:
                continue
            ids = fm["implements"]
            if not isinstance(ids, list):
                continue
            try:
                rel_path = str(f.relative_to(project_root))
            except ValueError:
                rel_path = str(f.name)
            yield EvidenceIndexEntry(
                kind=EvidenceKind.YAML_FRONTMATTER,
                source=rel_path,
                line=None,
                cited_ids=[str(x) for x in ids],
            )


class SatisfiesByExistenceAdapter:
    """Adapter for governance documents declaring `satisfies_by_existence: [...]` (F-003)."""

    file_extensions = (".md",)

    def extract(
        self, files: list[Path], project_root: Path
    ) -> Iterable[EvidenceIndexEntry]:
        for f in files:
            if f.suffix not in self.file_extensions or not f.is_file():
                continue
            text = f.read_text(encoding="utf-8")
            fm = _parse_frontmatter(text)
            if not fm or "satisfies_by_existence" not in fm:
                continue
            ids = fm["satisfies_by_existence"]
            if not isinstance(ids, list):
                continue
            try:
                rel_path = str(f.relative_to(project_root))
            except ValueError:
                rel_path = str(f.name)
            yield EvidenceIndexEntry(
                kind=EvidenceKind.SATISFIES_BY_EXISTENCE,
                source=rel_path,
                line=None,
                cited_ids=[str(x) for x in ids],
            )
