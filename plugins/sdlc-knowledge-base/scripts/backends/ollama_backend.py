"""Local Ollama backend — model calls only (#211, M1a). Uses the raw `ollama` client
with `format=<JSON schema>` for grammar-constrained output; the pipeline owns parsing.
Strict-offline by default: a non-loopback host is rejected unless allow_remote=True."""
from __future__ import annotations

from urllib.parse import urlparse

_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _is_loopback(host: str) -> bool:
    netloc = urlparse(host).hostname or host
    return netloc in _LOOPBACK_HOSTS


class OllamaBackend:
    def __init__(
        self,
        model: str = "gpt-oss:20b",
        *,
        host: str = "http://localhost:11434",
        embed_model: str = "nomic-embed-text",
        allow_remote: bool = False,
        client=None,
    ):
        if not allow_remote and not _is_loopback(host):
            raise ValueError(
                f"strict-offline: refusing non-loopback Ollama host {host!r}; "
                "pass allow_remote=True (--allow-remote-ollama) to override"
            )
        self.model = model
        self.embed_model = embed_model
        self.host = host
        if client is not None:
            self._client = client
        else:
            import ollama

            self._client = ollama.Client(host=host)

    def generate(self, prompt: str, *, schema: dict | None = None) -> str:
        resp = self._client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format=schema,
            stream=False,
        )
        return resp["message"]["content"]

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embed(model=self.embed_model, input=texts)
        return resp["embeddings"]
