"""Decomposition declaration: programs.yaml parser + validators."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


class DecompositionParseError(ValueError):
    """Raised when programs.yaml cannot be parsed."""


@dataclass(frozen=True)
class PathSection:
    """A named-anchor scope within a file.

    Restricts a module path entry to the section of a file delimited by
    the heading text *anchor* (e.g. ``### MODE: SYNTHESISE-ACROSS-SPEC-TYPES``).
    Both fields are required; anchor must be the exact markdown heading text.
    """

    file: str
    anchor: str


@dataclass(frozen=True)
class Module:
    id: str
    name: str
    paths: List[str]
    granularity: str
    structure: str
    owner: Optional[str] = None
    paths_sections: List[PathSection] = field(default_factory=list)


@dataclass(frozen=True)
class SubProgram:
    id: str
    name: str
    modules: List[Module]


@dataclass(frozen=True)
class Program:
    id: str
    name: str
    description: Optional[str]
    sub_programs: List[SubProgram]


@dataclass(frozen=True)
class VisibilityRule:
    from_module: str
    to_modules: List[str]


@dataclass(frozen=True)
class Decomposition:
    programs: List[Program]
    visibility: List[VisibilityRule] = field(default_factory=list)


def parse_programs_yaml(path: Path) -> Decomposition:
    """Parse a programs.yaml file into a Decomposition.

    Raises DecompositionParseError if the file is missing schema_version: 1
    or is otherwise malformed.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DecompositionParseError(f"{path}: top-level must be a mapping")
    if raw.get("schema_version") != 1:
        raise DecompositionParseError(
            f"{path}: missing or unsupported schema_version (expected 1)"
        )
    programs_raw = raw.get("programs", [])
    if not isinstance(programs_raw, list):
        raise DecompositionParseError(f"{path}: programs must be a list")
    programs: List[Program] = []
    for p in programs_raw:
        sub_programs: List[SubProgram] = []
        for sp in p.get("sub_programs", []):
            modules: List[Module] = []
            for m in sp.get("modules", []):
                raw_sections = m.get("paths_sections", []) or []
                paths_sections: List[PathSection] = [
                    PathSection(file=ps["file"], anchor=ps["anchor"])
                    for ps in raw_sections
                ]
                modules.append(
                    Module(
                        id=m["id"],
                        name=m["name"],
                        paths=list(m.get("paths", [])),
                        granularity=m.get("granularity", "requirement"),
                        structure=m.get("structure", "flat"),
                        owner=m.get("owner"),
                        paths_sections=paths_sections,
                    )
                )
            sub_programs.append(
                SubProgram(id=sp["id"], name=sp["name"], modules=modules)
            )
        programs.append(
            Program(
                id=p["id"],
                name=p["name"],
                description=p.get("description"),
                sub_programs=sub_programs,
            )
        )
    visibility: List[VisibilityRule] = []
    for v in raw.get("visibility", []) or []:
        visibility.append(
            VisibilityRule(
                from_module=v["from"],
                to_modules=list(v.get("to", [])),
            )
        )
    return Decomposition(programs=programs, visibility=visibility)


def default_decomposition(
    project_root_paths: Optional[List[str]] = None,
) -> Decomposition:
    """Return a minimal single-module P1.SP1.M1 decomposition.

    Used when no programs.yaml is present in the project root.
    """
    paths = project_root_paths or ["."]
    module = Module(
        id="M1",
        name="Default module",
        paths=paths,
        granularity="requirement",
        structure="flat",
    )
    sub_program = SubProgram(id="SP1", name="Default sub-program", modules=[module])
    program = Program(
        id="P1", name="Default program", description=None, sub_programs=[sub_program]
    )
    return Decomposition(programs=[program], visibility=[])


@dataclass(frozen=True)
class SpecArtefact:
    """A parsed spec artefact for module-assignment validation."""

    path: str
    feature_id: Optional[str]
    module: Optional[str]
    ids: List[str]


@dataclass
class DecompositionValidatorResult:
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _all_module_ids(decomp: Decomposition) -> set:
    out: set = set()
    for p in decomp.programs:
        for sp in p.sub_programs:
            for m in sp.modules:
                out.add(f"{p.id}.{sp.id}.{m.id}")
    return out


def _module_from_positional_id(id_: str) -> Optional[str]:
    if "." not in id_:
        return None
    parts = id_.split(".")
    if len(parts) >= 4:
        return ".".join(parts[:3])
    return None


def req_has_module_assignment(
    specs: List[SpecArtefact], decomp: Decomposition
) -> DecompositionValidatorResult:
    # implements: DES-assured-decomposition-validators-001
    """Validate that every REQ ID has a module assignment within the decomposition.

    A REQ ID gets its module either from a positional prefix (e.g. P1.SP1.M1.REQ-001)
    or from the spec's explicit module field.  Missing or undeclared modules are errors.
    """
    declared = _all_module_ids(decomp)
    errors: List[str] = []
    for spec in specs:
        for id_ in spec.ids:
            if not id_.startswith("REQ"):
                # Only REQ artefacts need explicit module assignment per Article 16.
                if "." in id_ and id_.startswith("P"):
                    pass
                else:
                    continue
            module = _module_from_positional_id(id_) or spec.module
            if module is None:
                errors.append(f"{id_} (in {spec.path}) has no module assignment")
                continue
            if module not in declared:
                errors.append(
                    f"{id_} (in {spec.path}) is assigned to module {module!r} "
                    "which is not declared in programs.yaml"
                )
    return DecompositionValidatorResult(passed=not errors, errors=errors)


@dataclass(frozen=True)
class CodeAnnotation:
    """A parsed `# implements:` annotation."""

    file_path: str
    line: int
    cited_ids: List[str]


def _module_paths(decomp: Decomposition) -> dict:
    out: dict = {}
    for p in decomp.programs:
        for sp in p.sub_programs:
            for m in sp.modules:
                out[f"{p.id}.{sp.id}.{m.id}"] = list(m.paths)
    return out


def _file_under_paths(file_path: str, paths: List[str]) -> bool:
    return any(file_path.startswith(p) for p in paths)


def code_annotation_maps_to_module(
    annotations: List[CodeAnnotation],
    decomp: Decomposition,
    spec_module_lookup: dict,
) -> DecompositionValidatorResult:
    # implements: DES-assured-decomposition-validators-002
    """Each annotation's file path must lie under its cited spec's module path.

    spec_module_lookup maps REQ/DES/TEST IDs to their declared module.
    """
    paths_by_module = _module_paths(decomp)
    errors: List[str] = []
    for ann in annotations:
        for cited in ann.cited_ids:
            module = spec_module_lookup.get(cited)
            if module is None:
                # Caught by cited_ids_resolve; skip here.
                continue
            allowed_paths = paths_by_module.get(module, [])
            if not _file_under_paths(ann.file_path, allowed_paths):
                errors.append(
                    f"{ann.file_path}:{ann.line} cites {cited} (module {module}) "
                    f"but file is not under any declared path: {allowed_paths}"
                )
    return DecompositionValidatorResult(passed=not errors, errors=errors)


@dataclass(frozen=True)
class ImportEdge:
    """A directed dependency edge between modules, derived from imports."""

    from_module: str
    to_module: str


def visibility_rule_enforcement(
    edges: List[ImportEdge], decomp: Decomposition, mode: str = "advisory"
) -> DecompositionValidatorResult:
    # implements: DES-assured-decomposition-validators-003
    """Verify each cross-module edge is declared in the visibility block.

    mode = 'strict' -> undeclared edges block (errors).
    mode = 'advisory' -> undeclared edges warn.
    """
    declared: dict = {}
    for v in decomp.visibility:
        declared[v.from_module] = set(v.to_modules)
    issues: List[str] = []
    for edge in edges:
        if edge.from_module == edge.to_module:
            continue
        allowed = declared.get(edge.from_module, set())
        if edge.to_module not in allowed:
            issues.append(
                f"undeclared visibility: {edge.from_module} → {edge.to_module}"
            )
    if mode == "strict":
        return DecompositionValidatorResult(passed=not issues, errors=issues)
    return DecompositionValidatorResult(passed=True, warnings=issues)


def anaemic_context_detection(
    annotations: List[CodeAnnotation],
    decomp: Decomposition,
    spec_module_lookup: dict,
    scatter_threshold: float = 0.20,
) -> DecompositionValidatorResult:
    # implements: DES-assured-decomposition-validators-004
    """Flag systemic anaemia: a module whose implementations are significantly scattered.

    This validator detects DDD bounded-context erosion at the module level.
    It differs from :func:`code_annotation_maps_to_module`, which blocks on
    *every* individual out-of-module annotation.  Anaemic-context detection
    only flags when the *proportion* of a module's annotations that live
    outside its declared paths exceeds *scatter_threshold* (default 20%).
    A single stray annotation is an outlier; 25% scatter is a smell.

    Parameters
    ----------
    annotations:
        All ``# implements:`` annotations for the project.
    decomp:
        Parsed decomposition declaration.
    spec_module_lookup:
        Mapping from spec ID to its declared module (e.g. ``"REQ-auth-001"``
        → ``"P1.SP1.M1"``).
    scatter_threshold:
        Fraction of a module's annotations that must be outside the module's
        declared paths before the validator fires (0.0–1.0, default 0.20).

    Returns
    -------
    DecompositionValidatorResult
        Errors for every module whose scatter ratio exceeds the threshold,
        listing the out-of-module annotations as evidence.
    """
    paths_by_module = _module_paths(decomp)

    # Collect per-module annotation counts: inside vs outside declared paths.
    inside: dict = {}  # module → count of in-module annotations
    outside: dict = {}  # module → list of (file_path, line, cited_id) triples

    for ann in annotations:
        for cited in ann.cited_ids:
            module = spec_module_lookup.get(cited)
            if module is None:
                continue
            allowed_paths = paths_by_module.get(module, [])
            if _file_under_paths(ann.file_path, allowed_paths):
                inside[module] = inside.get(module, 0) + 1
            else:
                outside.setdefault(module, []).append((ann.file_path, ann.line, cited))

    errors: List[str] = []
    for module, stray_annotations in outside.items():
        stray_count = len(stray_annotations)
        total = inside.get(module, 0) + stray_count
        ratio = stray_count / total if total > 0 else 1.0
        if ratio > scatter_threshold:
            pct = int(ratio * 100)
            errors.append(
                f"anaemic context: module {module} has {pct}% of its annotations "
                f"({stray_count}/{total}) outside its declared paths — "
                f"evidence: "
                + "; ".join(
                    f"{fp}:{ln} implements {cid}" for fp, ln, cid in stray_annotations
                )
            )
    return DecompositionValidatorResult(passed=not errors, errors=errors)


def granularity_match(
    declared_reqs: List[str],
    annotations: List[CodeAnnotation],
    decomp: Decomposition,
    spec_module_lookup: dict[str, str],
    satisfies_graph: Optional[dict[str, list[str]]] = None,
) -> DecompositionValidatorResult:
    # implements: DES-assured-decomposition-validators-005
    """For modules with granularity=requirement, every REQ must have at least one
    annotation — directly OR via a satisfies-linked DES (F-008 indirect coverage).

    satisfies_graph maps DES-id → list of REQ-ids it satisfies. If None, falls back to
    direct-only coverage (v0.1.0 behaviour, deprecated).
    """
    annotated_ids: set[str] = set()
    for ann in annotations:
        annotated_ids.update(ann.cited_ids)

    granularity_by_module: dict[str, str] = {}
    for p in decomp.programs:
        for sp in p.sub_programs:
            for m in sp.modules:
                granularity_by_module[f"{p.id}.{sp.id}.{m.id}"] = m.granularity

    # Build the inverse: REQ-id → list of DES-ids that satisfy it
    inverse_satisfies: dict[str, list[str]] = {}
    if satisfies_graph:
        for des_id, req_ids in satisfies_graph.items():
            for req_id in req_ids:
                inverse_satisfies.setdefault(req_id, []).append(des_id)

    warnings: List[str] = []
    for req in declared_reqs:
        module = spec_module_lookup.get(req)
        if module is None or granularity_by_module.get(module) != "requirement":
            continue
        # Direct coverage check
        if req in annotated_ids:
            continue
        # Indirect coverage: any satisfies-linked DES annotated?
        satisfying_dess = inverse_satisfies.get(req, [])
        if any(des_id in annotated_ids for des_id in satisfying_dess):
            continue
        warnings.append(
            f"under-specified: {req} (module {module}) has no `# implements:` "
            "annotation directly OR via a satisfies-linked DES"
        )
    return DecompositionValidatorResult(passed=True, warnings=warnings)


def _is_single_line_getter_setter(node: ast.FunctionDef) -> bool:
    """Return True if the function body is a single return-self-attr or assign-self-attr."""
    if len(node.body) != 1:
        return False
    stmt = node.body[0]
    # Single return self.<x>
    if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Attribute):
        if isinstance(stmt.value.value, ast.Name) and stmt.value.value.id == "self":
            return True
    # Single self.<x> = <y>  (plain Assign, not AnnAssign)
    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
        target = stmt.targets[0]
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            if target.value.id == "self":
                return True
    return False


def _is_property_single_line(node: ast.FunctionDef) -> bool:
    """Return True if the function has a @property decorator and a single-statement body."""
    has_property = any(
        isinstance(d, ast.Name) and d.id == "property"
        for d in node.decorator_list
    )
    if not has_property:
        return False
    return len(node.body) == 1


def _is_stub_body(node: ast.FunctionDef) -> bool:
    """Return True if the function body is exactly one `...` (Ellipsis) or `pass` statement.

    Both are non-substantive: they carry no semantics and are the conventional
    body form for Protocol method stubs and empty placeholder implementations.
    """
    if len(node.body) != 1:
        return False
    stmt = node.body[0]
    # `pass` statement
    if isinstance(stmt, ast.Pass):
        return True
    # `...` expressed as a bare expression statement
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
        return stmt.value.value is ...
    return False


def _is_trivial(node: ast.FunctionDef) -> bool:
    """Return True if the function should be excluded from annotation checks."""
    name = node.name
    # Dunder methods
    if name.startswith("__") and name.endswith("__"):
        return True
    # Private functions
    if name.startswith("_"):
        return True
    # Single-line getter/setter
    if _is_single_line_getter_setter(node):
        return True
    # @property with single-line body
    if _is_property_single_line(node):
        return True
    # Protocol stub or pass-only body (no runtime semantics)
    if _is_stub_body(node):
        return True
    return False


def _collect_functions(tree: ast.Module) -> List[ast.FunctionDef]:
    """Recursively collect all FunctionDef and AsyncFunctionDef nodes in the AST."""
    funcs: List[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append(node)  # type: ignore[arg-type]
    return funcs


def forward_annotation_completeness(
    source_paths: List[Path],
    decomp: Decomposition,
) -> DecompositionValidatorResult:
    # implements: DES-assured-decomposition-validators-006
    """E2: every non-trivial public function in declared paths has a `# implements:` annotation.

    Returns errors (not warnings) for functions missing annotations.
    Files outside declared module paths are silently skipped.
    Test files (test_*.py, conftest.py) are silently skipped.
    """
    declared_paths: List[str] = []
    for p in decomp.programs:
        for sp in p.sub_programs:
            for m in sp.modules:
                declared_paths.extend(m.paths)

    errors: List[str] = []
    for src in source_paths:
        # Skip files outside declared module paths
        if not _file_under_paths(str(src), declared_paths):
            continue
        # Skip test files and conftest — check filename only (not directory components)
        if src.name.startswith("test_") or src.name == "conftest.py":
            continue

        try:
            source_text = src.read_text(encoding="utf-8")
            tree = ast.parse(source_text, filename=str(src))
        except (SyntaxError, OSError):
            continue

        source_lines = source_text.splitlines()

        for node in _collect_functions(tree):
            if _is_trivial(node):
                continue

            # Check for `# implements:` anywhere in the function's line range
            start_line = node.lineno - 1  # 0-indexed
            end_line = node.end_lineno  # exclusive upper bound (0-indexed)
            func_source_lines = source_lines[start_line:end_line]
            has_annotation = any(
                "# implements:" in line for line in func_source_lines
            )
            if not has_annotation:
                errors.append(f"{src}:{node.lineno} {node.name}")

    return DecompositionValidatorResult(passed=not errors, errors=errors)
