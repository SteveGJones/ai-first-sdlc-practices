"""Tests for assured.decomposition — programs.yaml schema + validators."""

from pathlib import Path

import pytest

from sdlc_assured_scripts.assured.decomposition import (
    DecompositionParseError,
    parse_programs_yaml,
    default_decomposition,
)


def test_parse_programs_yaml_extracts_modules(tmp_path: Path):
    pyaml = tmp_path / "programs.yaml"
    pyaml.write_text(
        """schema_version: 1
programs:
  - id: P1
    name: Auth platform
    sub_programs:
      - id: SP1
        name: Identity
        modules:
          - id: M1
            name: OAuth
            paths: [src/auth/oauth/]
            granularity: requirement
            structure: flat
visibility:
  - from: P1.SP1.M1
    to: []
"""
    )
    parsed = parse_programs_yaml(pyaml)
    assert parsed.programs[0].id == "P1"
    assert parsed.programs[0].sub_programs[0].id == "SP1"
    assert parsed.programs[0].sub_programs[0].modules[0].id == "M1"
    assert parsed.programs[0].sub_programs[0].modules[0].paths == ["src/auth/oauth/"]
    assert parsed.programs[0].sub_programs[0].modules[0].granularity == "requirement"


def test_parse_programs_yaml_raises_on_missing_schema_version(tmp_path: Path):
    pyaml = tmp_path / "programs.yaml"
    pyaml.write_text("programs: []\n")
    with pytest.raises(DecompositionParseError):
        parse_programs_yaml(pyaml)


def test_default_decomposition_is_p1_sp1_m1():
    parsed = default_decomposition(project_root_paths=["."])
    assert parsed.programs[0].id == "P1"
    assert parsed.programs[0].sub_programs[0].id == "SP1"
    assert parsed.programs[0].sub_programs[0].modules[0].id == "M1"
    assert parsed.programs[0].sub_programs[0].modules[0].paths == ["."]
