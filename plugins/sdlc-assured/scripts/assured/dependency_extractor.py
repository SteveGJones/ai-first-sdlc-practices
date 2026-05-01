"""Dependency extractor interface — F-007."""

from __future__ import annotations

from pathlib import Path
from typing import List, Protocol, runtime_checkable

from .decomposition import Decomposition, ImportEdge

__all__ = ["ImportEdge", "DependencyExtractor"]


@runtime_checkable
class DependencyExtractor(Protocol):
    """Language-specific extractor of cross-module dependency edges."""

    language: str  # e.g. "python", "swift"

    def extract(
        self, source_paths: List[Path], programs: Decomposition
    ) -> List[ImportEdge]:
        ...
