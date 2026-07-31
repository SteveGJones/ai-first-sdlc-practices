"""Tests for the multi-turn mlx_lm.server client.

Only the pure parts are exercised here (payload shape, reply extraction) —
the HTTP call itself is covered by the live smoke check in the CLI.
"""

from __future__ import annotations

from harness.mlx_client import DEFAULT_MAX_TOKENS, MlxClient


def _client(**kw):
    return MlxClient(model="mlx-community/Qwen2.5-Coder-14B-Instruct-4bit", **kw)


def test_payload_carries_the_full_conversation():
    messages = [
        {"role": "user", "content": "build it"},
        {"role": "assistant", "content": "here"},
        {"role": "user", "content": "it failed"},
    ]
    assert _client().build_payload(messages)["messages"] == messages


def test_stop_token_is_always_sent():
    """mlx_lm.server >=0.31.3 leaks <|im_end|> into content without it."""
    assert "<|im_end|>" in _client().build_payload([])["stop"]


def test_max_tokens_defaults_high_enough_for_multi_file_answers():
    """The one-shot adapter's 2048 truncates a build answer mid-file, and a
    truncated block is discarded — the whole iteration would be wasted."""
    assert DEFAULT_MAX_TOKENS >= 8192
    assert _client().build_payload([])["max_tokens"] == DEFAULT_MAX_TOKENS


def test_temperature_defaults_to_zero_for_reproducibility():
    assert _client().build_payload([])["temperature"] == 0.0


def test_extract_content_reads_the_reply():
    data = {"choices": [{"message": {"content": "```file:a.py\nX\n```"}}]}
    assert MlxClient.extract_content(data) == "```file:a.py\nX\n```"


def test_extract_content_tolerates_a_malformed_reply():
    """An empty answer must come back as empty text so the loop can nudge,
    rather than raising and killing the run."""
    assert MlxClient.extract_content({}) == ""
    assert MlxClient.extract_content({"choices": []}) == ""
    assert (
        MlxClient.extract_content({"choices": [{"message": {"content": None}}]}) == ""
    )
