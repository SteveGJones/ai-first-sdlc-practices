"""Tests for sdlc_knowledge_base_scripts.resume."""
from __future__ import annotations

from pathlib import Path

from sdlc_knowledge_base_scripts.resume import config_hash, content_hash


def test_content_hash_stable_and_sensitive():
    assert content_hash("abc") == content_hash("abc")
    assert content_hash("abc") != content_hash("abd")


def test_config_hash_order_independent():
    assert config_hash({"a": 1, "b": 2}) == config_hash({"b": 2, "a": 1})
    assert config_hash({"a": 1}) != config_hash({"a": 2})
