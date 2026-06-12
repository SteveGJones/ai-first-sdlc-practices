"""The backend seam: model calls ONLY. No validation, no retries, no file I/O —
those belong to the pipeline. (#211, M0)"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Backend(Protocol):
    def generate(self, prompt: str, *, schema: dict | None = None) -> str:
        """Return model text. If schema is given, the backend constrains output to it."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
        ...
    # Embedding-capable backends ALSO expose:
    #   def embedding_model_id(self) -> str
    # which returns the identifier of the embedding model in use.
    # Backends whose embed() is unsupported (e.g. AnthropicBackend) OMIT this
    # method entirely — absence is the capability signal checked by the index gate.
