"""Tests for OllamaBackend (no live daemon — injected client)."""
from __future__ import annotations

import pytest

from sdlc_knowledge_base_scripts.backends.ollama_backend import OllamaBackend


class _FakeClient:
    def __init__(self):
        self.calls = []
        self.last = None

    def chat(self, **kwargs):
        self.last = kwargs
        self.calls.append({"model": kwargs.get("model"), "messages": kwargs.get("messages"), "format": kwargs.get("format")})
        return {"message": {"content": '{"ok": true}'}}

    def embed(self, *, model, input):
        return {"embeddings": [[0.0] * 4 for _ in input]}


def test_generate_passes_schema_as_format_and_returns_text():
    c = _FakeClient()
    be = OllamaBackend(model="gpt-oss:20b", client=c)
    out = be.generate("q", schema={"type": "object"})
    assert out == '{"ok": true}'
    assert c.calls[0]["format"] == {"type": "object"}
    assert c.calls[0]["model"] == "gpt-oss:20b"


def test_embed_returns_vectors():
    c = _FakeClient()
    be = OllamaBackend(model="gpt-oss:20b", client=c, embed_model="nomic-embed-text")
    vecs = be.embed(["a", "b"])
    assert len(vecs) == 2 and len(vecs[0]) == 4


def test_strict_offline_rejects_remote_host():
    with pytest.raises(ValueError):
        OllamaBackend(model="m", host="http://remote.example.com:11434")


def test_remote_host_allowed_when_opted_in():
    be = OllamaBackend(model="m", host="http://remote.example.com:11434", allow_remote=True, client=_FakeClient())
    assert be.model == "m"


def test_localhost_variants_accepted():
    for h in ("http://localhost:11434", "http://127.0.0.1:11434", "http://[::1]:11434"):
        OllamaBackend(model="m", host=h, client=_FakeClient())


# --- pinning tests (M1c-2 Task 6) ---

def test_generate_forwards_pinned_options():
    fc = _FakeClient()
    be = OllamaBackend(model="gpt-oss:20b", client=fc,
                       options={"temperature": 0, "seed": 7, "top_p": 1})
    be.generate("hi", schema={"type": "object"})
    assert fc.last["options"] == {"temperature": 0, "seed": 7, "top_p": 1}
    assert fc.last["model"] == "gpt-oss:20b"
    assert fc.last["format"] == {"type": "object"}


def test_generate_without_options_omits_or_empties_them():
    fc = _FakeClient()
    be = OllamaBackend(model="m", client=fc)
    be.generate("hi")
    assert fc.last.get("options") in (None, {})
