"""Direct Anthropic API backend (model calls only). The `anthropic` SDK import is
deferred to construction so importing this module never requires the dependency. (#211)"""
from __future__ import annotations


class AnthropicBackend:
    def __init__(self, model: str = "claude-sonnet-4-6", *, client=None, max_tokens: int = 4096):
        self.model = model
        self.max_tokens = max_tokens
        if client is not None:
            self._client = client
        else:
            import anthropic

            self._client = anthropic.Anthropic()

    def generate(self, prompt: str, *, schema: dict | None = None) -> str:
        system = ""
        if schema is not None:
            system = (
                "Respond with a single JSON object that conforms exactly to this "
                f"JSON Schema. Output JSON only, no prose:\n{schema}"
            )
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system or None,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(getattr(b, "text", "") for b in msg.content)

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Anthropic backend does not provide embeddings; use Ollama (M3).")
