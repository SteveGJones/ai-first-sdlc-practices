"""Tests for sdlc_knowledge_base_scripts.mutation."""
from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.contracts import MutationAction, MutationProposal
from sdlc_knowledge_base_scripts.mutation import validate_proposal


def _proposal(**kw):
    base = dict(target_file="topic.md", action=MutationAction.create,
                frontmatter={"layer": "domain", "confidence": "medium"},
                body="# Topic\n", citations=["DORA 2024"], cross_refs=[])
    base.update(kw)
    return MutationProposal(**base)


def test_valid_create_passes(tmp_path: Path):
    assert validate_proposal(_proposal(), library_path=tmp_path,
                             allowed_layers=["domain"], known_citations={"DORA 2024"}) == []


def test_path_escape_rejected(tmp_path: Path):
    errs = validate_proposal(_proposal(target_file="../evil.md"), library_path=tmp_path,
                             allowed_layers=["domain"], known_citations={"DORA 2024"})
    assert any("path" in e.lower() for e in errs)


def test_missing_frontmatter_rejected(tmp_path: Path):
    errs = validate_proposal(_proposal(frontmatter={"layer": "domain"}),
                             library_path=tmp_path, allowed_layers=["domain"],
                             known_citations={"DORA 2024"})
    assert any("confidence" in e.lower() for e in errs)


def test_invalid_layer_rejected(tmp_path: Path):
    errs = validate_proposal(_proposal(frontmatter={"layer": "bogus", "confidence": "medium"}),
                             library_path=tmp_path, allowed_layers=["domain"],
                             known_citations={"DORA 2024"})
    assert any("layer" in e.lower() for e in errs)


def test_dangling_citation_rejected(tmp_path: Path):
    errs = validate_proposal(_proposal(citations=["Ghost 2099"]), library_path=tmp_path,
                             allowed_layers=["domain"], known_citations={"DORA 2024"})
    assert any("citation" in e.lower() for e in errs)


def test_create_with_expected_hash_rejected(tmp_path: Path):
    errs = validate_proposal(_proposal(expected_hash="deadbeef"), library_path=tmp_path,
                             allowed_layers=["domain"], known_citations={"DORA 2024"})
    assert any("expected_hash" in e.lower() for e in errs)
