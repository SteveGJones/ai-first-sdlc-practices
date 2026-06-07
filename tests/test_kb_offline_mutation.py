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
from sdlc_knowledge_base_scripts.resume import LibraryLock, content_hash


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
    commit_mutation(p, library_path=lib, fencing_token=token, lock=lock, run_step="s1")
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
            commit_mutation(
                p, library_path=lib, fencing_token=token, lock=lock, run_step="s1"
            )
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
            commit_mutation(
                p, library_path=lib, fencing_token=token, lock=lock, run_step="s1"
            )
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
            commit_mutation(
                p,
                library_path=lib,
                fencing_token=old_token,
                lock=lock2,
                run_step="s1",
            )
    finally:
        lock2.release()


def test_extend_success_overwrites_and_commits(tmp_path: Path):
    lib = _seed_library(tmp_path)
    (lib / "topic.md").write_text("v1 content")
    lock = LibraryLock(lib)
    token = lock.acquire()
    p = MutationProposal(
        target_file="topic.md",
        action=MutationAction.extend,
        frontmatter={"layer": "domain", "confidence": "medium"},
        body="v1 content\nplus more\n",
        expected_hash=content_hash("v1 content"),
    )
    try:
        commit_mutation(
            p, library_path=lib, fencing_token=token, lock=lock, run_step="s1"
        )
        text = (lib / "topic.md").read_text()
        assert "plus more" in text and text.startswith("---")
        import json as _j

        rec = _j.loads((lib / ".kb-offline" / "journal" / "s1.json").read_text())
        assert rec["stage"] == "committed"
    finally:
        lock.release()


def test_render_page_escapes_colon_in_frontmatter(tmp_path: Path):
    import yaml

    lib = _seed_library(tmp_path)
    lock = LibraryLock(lib)
    token = lock.acquire()
    p = MutationProposal(
        target_file="t.md",
        action=MutationAction.create,
        frontmatter={
            "layer": "domain",
            "confidence": "medium",
            "title": "Cost: a study",
        },
        body="# body\n",
    )
    try:
        commit_mutation(
            p, library_path=lib, fencing_token=token, lock=lock, run_step="s1"
        )
        raw = (lib / "t.md").read_text()
        fm = yaml.safe_load(raw.split("---")[1])  # must parse without error
        assert fm["title"] == "Cost: a study"
    finally:
        lock.release()
