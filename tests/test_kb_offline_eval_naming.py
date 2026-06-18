"""safe_model_name filename sanitizer (#211, eval traces)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.eval.report import safe_model_name


def test_safe_model_name_replaces_colon():
    assert safe_model_name("gemma4:12b") == "gemma4_12b"


def test_safe_model_name_replaces_slash_and_whitespace():
    assert safe_model_name("ns/custom:tag") == "ns_custom_tag"
    assert safe_model_name("a b") == "a_b"


def test_safe_model_name_idempotent_on_clean_name():
    assert safe_model_name("claude-sonnet-4-6") == "claude-sonnet-4-6"
