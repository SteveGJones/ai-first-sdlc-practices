"""Tests for the kb-offline backend seam."""
from __future__ import annotations

from sdlc_knowledge_base_scripts.backends.base import Backend
from sdlc_knowledge_base_scripts.backends.fake_backend import FakeBackend


def test_fake_backend_is_a_backend():
    fb = FakeBackend(responses={"hello": "world"})
    assert isinstance(fb, Backend)


def test_fake_generate_returns_scripted_response():
    fb = FakeBackend(responses={"q1": '{"ok": true}'})
    assert fb.generate("q1") == '{"ok": true}'


def test_fake_generate_records_calls():
    fb = FakeBackend(responses={"q1": "a"})
    fb.generate("q1", schema={"type": "object"})
    assert fb.calls[0]["prompt"] == "q1"
    assert fb.calls[0]["schema"] == {"type": "object"}


def test_fake_embed_returns_fixed_dim_vectors():
    fb = FakeBackend()
    vecs = fb.embed(["a", "b"])
    assert len(vecs) == 2 and all(len(v) == 8 for v in vecs)
