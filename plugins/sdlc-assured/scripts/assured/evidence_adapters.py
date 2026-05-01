"""File-type adapters for the v0.2.0 EvidenceIndexEntry registry."""

from __future__ import annotations

import re
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
