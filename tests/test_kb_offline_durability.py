"""Tests for sdlc_knowledge_base_scripts.durability."""
from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.durability import atomic_write_text


def test_atomic_write_creates_file(tmp_path: Path):
    p = tmp_path / "sub" / "f.txt"
    atomic_write_text(p, "hello")
    assert p.read_text() == "hello"


def test_atomic_write_overwrites_and_leaves_no_tmp(tmp_path: Path):
    p = tmp_path / "f.txt"
    atomic_write_text(p, "one")
    atomic_write_text(p, "two")
    assert p.read_text() == "two"
    assert list(tmp_path.glob("*.tmp")) == []
