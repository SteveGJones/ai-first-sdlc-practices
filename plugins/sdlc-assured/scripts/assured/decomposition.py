"""Decomposition declaration: programs.yaml parser + validators."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


class DecompositionParseError(ValueError):
    """Raised when programs.yaml cannot be parsed."""


@dataclass(frozen=True)
class Module:
    id: str
    name: str
    paths: List[str]
    granularity: str
    structure: str
    owner: Optional[str] = None


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
                modules.append(
                    Module(
                        id=m["id"],
                        name=m["name"],
                        paths=list(m.get("paths", [])),
                        granularity=m.get("granularity", "requirement"),
                        structure=m.get("structure", "flat"),
                        owner=m.get("owner"),
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
