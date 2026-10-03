"""Tests for the local-model agentic loop.

The loop is what makes a one-shot text adapter comparable to the agentic
Sonnet/Haiku runs: write -> verify -> feed failures back -> retry. Both the
model call and the verifier are injected, so the whole loop is testable
without a live mlx_lm.server or Docker.

Fairness note driving several assertions below: the iteration count is the
headline caveat when comparing a local run against the existing baselines,
so it must be recorded exactly, never silently.
"""

from __future__ import annotations

import json

from harness.local_agent import DEFAULT_MAX_ITERATIONS, run_loop

BRIEF = "Build a poker server."
PASS = {"passed": True, "scenarios": []}


def _fail(detail: str = "AssertionError: pot was 30, expected 20") -> dict:
    return {"passed": False, "scenarios": [{"name": "side_pot", "error": detail}]}


def test_passes_on_first_attempt_runs_exactly_one_iteration() -> None:
    calls = []

    def model(messages) -> str:
        calls.append(messages)
        return "```file:server.py\nOK\n```"

    result = run_loop(BRIEF, impl_dir=None, model_fn=model, verify_fn=lambda d: PASS)

    assert result.passed is True
    assert result.iteration_count == 1
    assert result.stop_reason == "passed"
    assert len(calls) == 1


def test_retries_with_feedback_and_can_pass_on_second_attempt() -> None:
    reports = [_fail(), PASS]

    def verify(_) -> dict:
        return reports.pop(0)

    result = run_loop(
        BRIEF,
        impl_dir=None,
        model_fn=lambda m: "```file:server.py\nX\n```",
        verify_fn=verify,
    )

    assert result.passed is True
    assert result.iteration_count == 2
    assert result.stop_reason == "passed"


def test_stops_at_max_iterations_when_never_passing() -> None:
    result = run_loop(
        BRIEF,
        impl_dir=None,
        model_fn=lambda m: "```file:server.py\nX\n```",
        verify_fn=lambda d: _fail(),
        max_iterations=3,
    )

    assert result.passed is False
    assert result.iteration_count == 3
    assert result.stop_reason == "max_iterations"


def test_model_sees_growing_conversation_with_its_own_prior_answer() -> None:
    """A retry is only meaningfully agentic if the model can see what it
    previously wrote and what broke — otherwise it is just N one-shots."""
    seen = []

    def model(messages) -> str:
        seen.append(list(messages))
        return "```file:server.py\nattempt\n```"

    run_loop(
        BRIEF,
        impl_dir=None,
        model_fn=model,
        verify_fn=lambda d: _fail(),
        max_iterations=2,
    )

    first, second = seen
    assert [m["role"] for m in first] == ["user"]
    assert [m["role"] for m in second] == ["user", "assistant", "user"]
    assert second[1]["content"] == "```file:server.py\nattempt\n```"


def test_feedback_includes_the_actual_failure_detail() -> None:
    seen = []

    def model(messages) -> str:
        seen.append(list(messages))
        return "```file:server.py\nX\n```"

    run_loop(
        BRIEF,
        impl_dir=None,
        model_fn=model,
        verify_fn=lambda d: _fail("AssertionError: pot was 30, expected 20"),
        max_iterations=2,
    )

    feedback = seen[1][-1]["content"]
    assert "pot was 30, expected 20" in feedback


def test_harness_error_is_fed_back_too() -> None:
    """A build failure is the most common real outcome and is reported as
    harness_error, not as a scenario failure — it must still reach the model."""
    seen = []

    def model(messages) -> str:
        seen.append(list(messages))
        return "```file:server.py\nX\n```"

    run_loop(
        BRIEF,
        impl_dir=None,
        model_fn=model,
        verify_fn=lambda d: {
            "passed": False,
            "harness_error": "docker compose build failed: no module named flask",
        },
        max_iterations=2,
    )

    assert "no module named flask" in seen[1][-1]["content"]


def test_response_with_no_file_blocks_is_nudged_about_the_format() -> None:
    """Qwen3-Coder-30B-A3B was previously contract-failed for using a plain
    ```python fence. A nudge costs one iteration and is fairer than scoring
    a formatting slip as a capability failure."""
    seen = []
    responses = ["```python\nx = 1\n```", "```file:server.py\nX\n```"]

    def model(messages) -> str:
        seen.append(list(messages))
        return responses.pop(0)

    result = run_loop(
        BRIEF,
        impl_dir=None,
        model_fn=model,
        verify_fn=lambda d: PASS,
        max_iterations=3,
    )

    assert result.passed is True
    assert result.iteration_count == 2
    nudge = seen[1][-1]["content"]
    assert "file:" in nudge
    assert result.iterations[0].files_written == []


def test_verifier_not_called_when_no_files_were_produced() -> None:
    """Running Docker against an unchanged tree would score the PREVIOUS
    iteration's code again and could report a false pass."""
    verify_calls = []

    def verify(d) -> dict:
        verify_calls.append(d)
        return PASS

    run_loop(
        BRIEF,
        impl_dir=None,
        model_fn=lambda m: "no code here",
        verify_fn=verify,
        max_iterations=1,
    )

    assert verify_calls == []


def test_default_iteration_cap_is_explicit_and_small() -> None:
    assert DEFAULT_MAX_ITERATIONS == 5


def test_files_are_written_to_impl_dir_between_iterations(tmp_path) -> None:
    run_loop(
        BRIEF,
        impl_dir=tmp_path,
        model_fn=lambda m: "```file:server.py\nreal content\n```",
        verify_fn=lambda d: PASS,
    )
    assert (tmp_path / "server.py").read_text() == "real content\n"


def test_transcript_records_every_iteration_for_audit(tmp_path) -> None:
    impl = tmp_path / "impl"
    transcript = tmp_path / "t"
    reports = [_fail(), PASS]

    run_loop(
        BRIEF,
        impl_dir=impl,
        model_fn=lambda m: "```file:server.py\nX\n```",
        verify_fn=lambda d: reports.pop(0),
        transcript_dir=transcript,
    )

    record = json.loads((transcript / "loop.json").read_text())
    assert record["iteration_count"] == 2
    assert record["passed"] is True
    assert len(record["iterations"]) == 2
    assert (transcript / "iteration-001.response.txt").exists()
    assert (transcript / "iteration-002.response.txt").exists()


def test_unsafe_path_ends_the_run_without_writing(tmp_path) -> None:
    result = run_loop(
        BRIEF,
        impl_dir=tmp_path,
        model_fn=lambda m: "```file:../escape.py\npwned\n```",
        verify_fn=lambda d: PASS,
    )

    assert result.passed is False
    assert result.stop_reason == "unsafe_path"
    assert not (tmp_path.parent / "escape.py").exists()
