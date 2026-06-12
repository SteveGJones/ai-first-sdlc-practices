"""Embedding index + store tests. kb-offline M3a (#211)."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend


def test_fake_backend_advertises_embedding_model_id():
    assert FakeBackend().embedding_model_id() == "fake-embed"


def test_anthropic_backend_is_not_embedding_capable():
    from sdlc_knowledge_base_scripts.backends.anthropic_backend import AnthropicBackend
    assert not hasattr(AnthropicBackend, "embedding_model_id")
