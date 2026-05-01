"""Dependency extractor interface — F-007."""

from __future__ import annotations

import ast
import logging
import re as _re
from pathlib import Path
from typing import Dict, List, Optional, Protocol, runtime_checkable

from .decomposition import Decomposition, ImportEdge

__all__ = [
    "ImportEdge",
    "DependencyExtractor",
    "PythonAstExtractor",
    "GenericRegexExtractor",
    "make_swift_extractor",
]

logger = logging.getLogger(__name__)


@runtime_checkable
class DependencyExtractor(Protocol):
    """Language-specific extractor of cross-module dependency edges."""

    language: str  # e.g. "python", "swift"

    def extract(
        self, source_paths: List[Path], programs: Decomposition
    ) -> List[ImportEdge]:
        ...


class PythonAstExtractor:
    """Python implementation of DependencyExtractor using ``ast.parse``.

    Walks each source file, resolves its owning module from the programs
    decomposition, then maps every ``import`` / ``from … import`` statement to
    its target module.  Only cross-module edges (from_module != to_module) are
    emitted, and duplicate edges are collapsed.
    """

    language = "python"

    # ------------------------------------------------------------------
    # Public API (satisfies DependencyExtractor protocol)
    # ------------------------------------------------------------------

    def extract(
        self, source_paths: List[Path], programs: Decomposition
    ) -> List[ImportEdge]:
        """Return ImportEdges for all cross-module imports found in *source_paths*."""
        path_index = self._build_path_index(source_paths, programs)
        seen: set = set()
        edges: List[ImportEdge] = []

        for src_path in source_paths:
            from_module = self._resolve_module(src_path, programs)
            if from_module is None:
                logger.debug(
                    "dependency_extractor: %s does not map to any module — skipping",
                    src_path,
                )
                continue

            try:
                tree = ast.parse(
                    src_path.read_text(encoding="utf-8"), filename=str(src_path)
                )
            except SyntaxError:
                logger.warning(
                    "dependency_extractor: syntax error in %s — skipping", src_path
                )
                continue
            except OSError:
                logger.warning(
                    "dependency_extractor: cannot read %s — skipping", src_path
                )
                continue

            for node in ast.walk(tree):
                to_module = self._import_target_module(node, path_index)
                if to_module is None or to_module == from_module:
                    continue
                edge = ImportEdge(from_module=from_module, to_module=to_module)
                if edge not in seen:
                    seen.add(edge)
                    edges.append(edge)

        return edges

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_path_index(
        self, source_paths: List[Path], programs: Decomposition
    ) -> Dict[Path, str]:
        """Build a mapping from each *source_path* to its module_id string."""
        index: Dict[Path, str] = {}
        for path in source_paths:
            module_id = self._resolve_module(path, programs)
            if module_id is not None:
                index[path] = module_id
        return index

    def _resolve_module(
        self, file_path: Path, programs: Decomposition
    ) -> Optional[str]:
        """Return the fully-qualified module_id (e.g. 'P1.SP1.M1') for *file_path*.

        Matches the file against each module's declared ``paths`` list.  The
        first prefix match wins.  Returns ``None`` if the file falls outside
        every declared path.
        """
        file_str = str(file_path)
        for p in programs.programs:
            for sp in p.sub_programs:
                for m in sp.modules:
                    for declared_path in m.paths:
                        if file_str.startswith(declared_path):
                            return f"{p.id}.{sp.id}.{m.id}"
        return None

    def _import_target_module(
        self, node: ast.AST, path_index: Dict[Path, str]
    ) -> Optional[str]:
        """Resolve an AST import node to a module_id using *path_index*.

        Handles both ``ast.Import`` (e.g. ``import b.module_b``) and
        ``ast.ImportFrom`` (e.g. ``from b.module_b import foo``).

        The dotted name is matched against every known source path by converting
        each path to a dotted suffix and checking whether the import name starts
        with that suffix (or vice versa).  Returns the module_id of the first
        match, or ``None`` if no known source file corresponds to the import.
        """
        if isinstance(node, ast.ImportFrom):
            names_to_check = [node.module] if node.module else []
        elif isinstance(node, ast.Import):
            names_to_check = [alias.name for alias in node.names]
        else:
            return None

        for imported_name in names_to_check:
            if imported_name is None:
                continue
            match = self._match_import_to_path_index(imported_name, path_index)
            if match is not None:
                return match
        return None

    @staticmethod
    def _match_import_to_path_index(
        imported_name: str, path_index: Dict[Path, str]
    ) -> Optional[str]:
        """Return the module_id for *imported_name* by comparing against path stems.

        Converts each known source file to a dotted module path (relative to
        every candidate root) and checks whether *imported_name* is a prefix
        match or exact match.
        """
        import_parts = imported_name.split(".")

        for src_path, module_id in path_index.items():
            # Build candidate dotted paths from all possible root depths.
            # E.g. "/tmp/src/b/module_b.py" → tries "module_b", "b.module_b",
            # "src.b.module_b", etc.
            parts = list(src_path.with_suffix("").parts)
            for start in range(len(parts)):
                candidate_parts = parts[start:]
                if not candidate_parts:
                    continue
                # Exact match or the import is a prefix (package import)
                if (
                    candidate_parts[: len(import_parts)] == import_parts
                    or import_parts[: len(candidate_parts)] == candidate_parts
                ):
                    return module_id
        return None


class GenericRegexExtractor:
    """Generic regex-based extractor parameterised by language + import pattern.

    Demonstrates the DependencyExtractor interface is not Python-shaped.
    Phase C task 15 uses this with a Swift-import pattern to validate
    cross-platform genericity.
    """

    def __init__(
        self,
        language: str,
        file_extensions: tuple,
        import_pattern: "_re.Pattern[str]",
    ) -> None:
        self.language = language
        self._file_extensions = file_extensions
        self._import_pattern = import_pattern

    def extract(
        self, source_paths: List[Path], programs: Decomposition
    ) -> List[ImportEdge]:
        """Return ImportEdges by matching *import_pattern* against file text.

        Reuses PythonAstExtractor path-resolution helpers so module assignment
        is identical regardless of language — only the import-detection step
        differs (regex text scan vs AST walk).
        """
        py = PythonAstExtractor()
        path_to_module: Dict[Path, str] = py._build_path_index(source_paths, programs)
        seen: set = set()
        edges: List[ImportEdge] = []

        for src_path in source_paths:
            if src_path.suffix not in self._file_extensions:
                continue
            if not src_path.is_file():
                continue
            from_module = py._resolve_module(src_path, programs)
            if from_module is None:
                continue
            try:
                text = src_path.read_text(encoding="utf-8")
            except OSError:
                logger.warning(
                    "dependency_extractor: cannot read %s — skipping", src_path
                )
                continue
            for match in self._import_pattern.finditer(text):
                target_name = match.group(1)
                for known_path, module_id in path_to_module.items():
                    stem = known_path.stem.lower()
                    parent = known_path.parent.name.lower()
                    if target_name.lower() in (stem, parent):
                        if module_id != from_module:
                            edge = ImportEdge(
                                from_module=from_module, to_module=module_id
                            )
                            if edge not in seen:
                                seen.add(edge)
                                edges.append(edge)
                        break

        return edges


def make_swift_extractor() -> GenericRegexExtractor:
    """Return a toy Swift import extractor for v0.2.0 interface validation."""
    return GenericRegexExtractor(
        language="swift",
        file_extensions=(".swift",),
        import_pattern=_re.compile(r"^\s*import\s+(\w+)\s*$", _re.MULTILINE),
    )
