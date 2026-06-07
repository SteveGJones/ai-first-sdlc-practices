"""Tests for sdlc_knowledge_base_scripts.mutation."""

from __future__ import annotations

from pathlib import Path

import pytest

from sdlc_knowledge_base_scripts.contracts import MutationAction, MutationProposal
from sdlc_knowledge_base_scripts.mutation import (
    CommitConflict,
    FenceError,
    commit_mutation,
    validate_proposal,
)
from sdlc_knowledge_base_scripts.resume import LibraryLock


def _proposal(**kw):
    base = dict(
        target_file="topic.md",
        action=MutationAction.create,
        frontmatter={"layer": "domain", "confidence": "medium"},
        body="# Topic\n",
        citations=["DORA 2024"],
        cross_refs=[],
    )
    base.update(kw)
    return MutationProposal(**base)


def test_valid_create_passes(tmp_path: Path):
    assert (
        validate_proposal(
            _proposal(),
            library_path=tmp_path,
            allowed_layers=["domain"],
            known_citations={"DORA 2024"},
        )
        == []
    )


def test_path_escape_rejected(tmp_path: Path):
    errs = validate_proposal(
        _proposal(target_file="../evil.md"),
        library_path=tmp_path,
        allowed_layers=["domain"],
        known_citations={"DORA 2024"},
    )
    assert any("path" in e.lower() for e in errs)


def test_missing_frontmatter_rejected(tmp_path: Path):
    errs = validate_proposal(
        _proposal(frontmatter={"layer": "domain"}),
        library_path=tmp_path,
        allowed_layers=["domain"],
        known_citations={"DORA 2024"},
    )
    assert any("confidence" in e.lower() for e in errs)


def test_invalid_layer_rejected(tmp_path: Path):
    errs = validate_proposal(
        _proposal(frontmatter={"layer": "bogus", "confidence": "medium"}),
        library_path=tmp_path,
        allowed_layers=["domain"],
        known_citations={"DORA 2024"},
    )
    assert any("layer" in e.lower() for e in errs)


def test_dangling_citation_rejected(tmp_path: Path):
    errs = validate_proposal(
        _proposal(citations=["Ghost 2099"]),
        library_path=tmp_path,
        allowed_layers=["domain"],
        known_citations={"DORA 2024"},
    )
    assert any("citation" in e.lower() for e in errs)


def test_create_with_expected_hash_rejected(tmp_path: Path):
    errs = validate_proposal(
        _proposal(expected_hash="deadbeef"),
        library_path=tmp_path,
        allowed_layers=["domain"],
        known_citations={"DORA 2024"},
    )
    assert any("expected_hash" in e.lower() for e in errs)


def test_extend_without_expected_hash_rejected(tmp_path: Path):
    errs = validate_proposal(
        _proposal(action=MutationAction.extend),
        library_path=tmp_path,
        allowed_layers=["domain"],
        known_citations={"DORA 2024"},
    )
    assert any("expected_hash" in e.lower() for e in errs)


def _seed_library(tmp_path: Path) -> Path:
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "_shelf-index.md").write_text("<!-- format_version: 1 -->\n# Shelf\n")
    return lib


def test_commit_create_writes_page_and_journals(tmp_path: Path):
    lib = _seed_library(tmp_path)
    lock = LibraryLock(lib)
    token = lock.acquire()
    p = MutationProposal(
        target_file="topic.md",
        action=MutationAction.create,
        frontmatter={"layer": "domain", "confidence": "medium"},
        body="# Topic\n",
    )
    commit_mutation(p, library_path=lib, fencing_token=token, lock=lock)
    assert (lib / "topic.md").exists()
    journal = list((lib / ".kb-offline" / "journal").glob("*.json"))
    assert journal, "a journal record must be written"
    lock.release()


def test_create_no_replace_conflict(tmp_path: Path):
    lib = _seed_library(tmp_path)
    (lib / "topic.md").write_text("existing")
    lock = LibraryLock(lib)
    token = lock.acquire()
    p = MutationProposal(
        target_file="topic.md",
        action=MutationAction.create,
        frontmatter={"layer": "domain", "confidence": "medium"},
        body="# new\n",
    )
    try:
        with pytest.raises(CommitConflict):
            commit_mutation(p, library_path=lib, fencing_token=token, lock=lock)
    finally:
        lock.release()


def test_extend_hash_mismatch_conflict(tmp_path: Path):
    lib = _seed_library(tmp_path)
    (lib / "topic.md").write_text("v1")
    lock = LibraryLock(lib)
    token = lock.acquire()
    p = MutationProposal(
        target_file="topic.md",
        action=MutationAction.extend,
        frontmatter={"layer": "domain", "confidence": "medium"},
        body="v1\nmore\n",
        expected_hash="not-the-real-hash",
    )
    try:
        with pytest.raises(CommitConflict):
            commit_mutation(p, library_path=lib, fencing_token=token, lock=lock)
    finally:
        lock.release()


def test_stale_fencing_token_fenced_out(tmp_path: Path):
    lib = _seed_library(tmp_path)
    lock = LibraryLock(lib)
    old_token = lock.acquire()
    lock.release()
    lock2 = LibraryLock(lib)
    lock2.acquire()
    p = MutationProposal(
        target_file="topic.md",
        action=MutationAction.create,
        frontmatter={"layer": "domain", "confidence": "medium"},
        body="# t\n",
    )
    try:
        with pytest.raises(FenceError):
            commit_mutation(p, library_path=lib, fencing_token=old_token, lock=lock2)
    finally:
        lock2.release()
