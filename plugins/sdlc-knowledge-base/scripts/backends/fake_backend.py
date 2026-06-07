"""Deterministic backend for tests — no model calls. (#211, M0)"""
from __future__ import annotations


class FakeBackend:
    def __init__(self, responses: dict[str, str] | None = None):
        self.responses = responses or {}
        self.calls: list[dict] = []

    def generate(self, prompt: str, *, schema: dict | None = None) -> str:
        self.calls.append({"prompt": prompt, "schema": schema})
        if prompt not in self.responses:
            raise KeyError(f"FakeBackend has no scripted response for prompt: {prompt!r}")
        return self.responses[prompt]

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for t in texts:
            base = float(len(t))
            out.append([base + i + float(sum(ord(c) for c in t) % 7) for i in range(8)])
        return out
