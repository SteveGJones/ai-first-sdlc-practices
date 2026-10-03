"""Multi-turn OpenAI-compatible client for a local ``mlx_lm.server``.

The council's existing ``mlx-chat`` is a one-shot CLI that rebuilds history
from the engine's per-turn files. The agentic loop holds its conversation in
memory instead, so it needs an importable client rather than a subprocess.

Two mlx_lm.server behaviours are carried over from that adapter because they
are still real:

- **Always send ``stop``.** mlx_lm.server >= 0.31.3 can leak the chat stop
  token (Qwen's ``<|im_end|>``) into message content
  (ml-explore/mlx-lm #973/#875); passing ``stop`` makes the server trim it.
- **Bound the prompt cache when launching the server.** Unbounded, it
  accumulates a KV sequence per session and OOMs the GPU — this crashed a
  run on 2026-07-30. See ``--prompt-cache-size`` in the module docstring of
  the CLI.

``max_tokens`` defaults far above the adapter's 2048: a build phase emits
several complete files in one answer, and truncation mid-file is discarded
by the parser, wasting the whole iteration.
"""

from __future__ import annotations

import json
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

DEFAULT_BASE_URL = "http://127.0.0.1:8081/v1"
DEFAULT_STOP = ["<|im_end|>"]
DEFAULT_MAX_TOKENS = 8192


class MlxError(Exception):
    """The local server could not be reached or returned an unusable reply."""


class MlxClient:
    """Callable that maps a message list to the assistant's reply text.

    Shaped to drop straight into ``local_agent.run_loop`` as ``model_fn``.
    """

    def __init__(
        self,
        model: str,
        base_url: str = DEFAULT_BASE_URL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = 0.0,
        stop: list[str] | None = None,
        timeout_s: int = 1800,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.stop = list(stop) if stop else list(DEFAULT_STOP)
        self.timeout_s = timeout_s
        self.usage: list[dict] = []

    def build_payload(self, messages: list[dict]) -> dict:
        return {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stop": self.stop,
        }

    @staticmethod
    def extract_content(data: dict) -> str:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return ""
        return content or ""

    def __call__(self, messages: list[dict]) -> str:
        body = json.dumps(self.build_payload(messages)).encode("utf-8")
        req = urlrequest.Request(
            self.base_url + "/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=self.timeout_s) as resp:
                data = json.loads(resp.read())
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:500]
            raise MlxError(
                f"server HTTP {exc.code} at {self.base_url}: {detail}"
            ) from exc
        except URLError as exc:
            raise MlxError(
                f"cannot reach mlx_lm.server at {self.base_url} ({exc}). Start it with "
                "a bounded prompt cache: mlx_lm.server --model <hf-id> --port 8081 "
                "--prompt-cache-size 2"
            ) from exc
        except (ValueError, OSError) as exc:
            raise MlxError(f"bad response from {self.base_url}: {exc}") from exc

        if isinstance(data, dict) and data.get("usage"):
            self.usage.append(data["usage"])
        return self.extract_content(data)


def probe(base_url: str = DEFAULT_BASE_URL) -> bool:
    try:
        with urlrequest.urlopen(base_url.rstrip("/") + "/models", timeout=5) as resp:
            return resp.status == 200
    except (HTTPError, URLError, OSError):
        return False
