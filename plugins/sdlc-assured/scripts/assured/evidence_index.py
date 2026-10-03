"""EvidenceIndexEntry abstraction — v0.2.0 file-type registry foundation.

Replaces the v0.1.0 monolithic parse_code_annotations approach.
See docs/superpowers/specs/2026-05-01-v020-assured-improvements-design.md §3 Phase A decisions 2 + 6.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional, Protocol


class EvidenceKind(Enum):
    """Kind of evidence carried by an EvidenceIndexEntry."""

    PYTHON_COMMENT = "python_comment"
    MARKDOWN_HTML_COMMENT = "markdown_html_comment"
    YAML_FRONTMATTER = "yaml_frontmatter"
    SATISFIES_BY_EXISTENCE = "satisfies_by_existence"


@dataclass(frozen=True)
class EvidenceIndexEntry:
    """One unit of implementation evidence pointing at one or more spec IDs."""

    kind: EvidenceKind
    source: str
    line: Optional[int]
    cited_ids: List[str]
    terms: List[str] = field(default_factory=list)
    facts: List[str] = field(default_factory=list)


class EvidenceAdapter(Protocol):
    """Protocol for file-type-specific evidence adapters."""

    file_extensions: tuple[str, ...]

    def extract(
        self, files: list[Path], project_root: Path
    ) -> Iterable[EvidenceIndexEntry]:
        ...


class EvidenceIndexRegistry:
    """Dispatches files to file-type-specific evidence adapters."""

    def __init__(self, adapters: list[EvidenceAdapter]) -> None:
        self._adapters = list(adapters)

    @classmethod
    def with_default_adapters(cls) -> "EvidenceIndexRegistry":
        from .evidence_adapters import (
            MarkdownHtmlCommentAdapter,
            PythonCommentAdapter,
            SatisfiesByExistenceAdapter,
            YamlFrontmatterAdapter,
        )

        return cls(
            [
                PythonCommentAdapter(),
                MarkdownHtmlCommentAdapter(),
                YamlFrontmatterAdapter(),
                SatisfiesByExistenceAdapter(),
            ]
        )

    def scan(
        self, files: list[Path], project_root: Path
    ) -> Iterable[EvidenceIndexEntry]:
        for adapter in self._adapters:
            yield from adapter.extract(files, project_root)
