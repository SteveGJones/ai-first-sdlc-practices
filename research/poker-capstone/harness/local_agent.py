"""The write -> verify -> feed-back -> retry loop for a text-only model.

Why this exists: the `mlx:` adapter (Path B) is one-shot and has no
filesystem or Docker access, but the Sonnet and Haiku P11 runs were
agentic — they wrote code, ran it, saw failures and fixed them. Scoring a
single one-shot answer against those baselines would not be measuring the
same activity. This loop supplies the missing feedback cycle so a local
model's build-phase result is comparable.

`model_fn` and `verify_fn` are injected so the loop is testable without a
live mlx_lm.server or Docker, and so the same loop can drive any backend.

**Fairness caveat, deliberately surfaced rather than hidden:** the
iteration count is recorded on every result and written to the transcript.
A local run that needed five attempts is not the same result as a Sonnet
run that needed one, and any write-up must say so.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .file_blocks import UnsafePathError, parse_file_blocks, write_file_blocks

DEFAULT_MAX_ITERATIONS = 5

#: Appended to the brief so the model knows the only output shape we can apply.
FORMAT_INSTRUCTIONS = """
## Required answer format

Reply with the COMPLETE contents of every file you want written, each in
its own fenced block labelled with its path relative to the project root:

```file:docker-compose.yml
services:
  server:
    ...
```

```file:src/server.py
...
```

Rules:
- Give the WHOLE file every time, never a diff, patch or excerpt.
- Re-send any file you change on a later attempt, complete, in the same form.
- Do not put commentary inside a file block.
- If a file must itself contain a ``` fence, open its block with four
  backticks (````file:README.md) so the inner fence does not close it.
"""

_NUDGE = (
    "Your reply contained no ```file:PATH blocks, so nothing could be written "
    "to disk. Reply again with the complete contents of each file in the "
    "required format:\n\n```file:path/to/file.py\n<entire file>\n```"
)

_MAX_FEEDBACK_CHARS = 6000


@dataclass
class Iteration:
    index: int
    response: str
    files_written: list[str] = field(default_factory=list)
    report: dict | None = None
    passed: bool = False


@dataclass
class LoopResult:
    passed: bool
    stop_reason: str
    iterations: list[Iteration]
    impl_dir: str | None = None

    @property
    def iteration_count(self) -> int:
        return len(self.iterations)


def build_feedback(report: dict) -> str:
    """Turn a verification report into the next user message.

    A build failure arrives as ``harness_error`` and a logic failure as
    per-scenario entries; both have to reach the model or the retry is
    blind.
    """
    parts = ["Your implementation was built and tested. It did not pass."]

    harness_error = report.get("harness_error")
    if harness_error:
        parts.append(
            f"It failed before the tests could run — fix this first:\n\n{harness_error}"
        )

    failures = [
        s
        for s in report.get("scenarios", []) or []
        if isinstance(s, dict) and (s.get("error") or s.get("passed") is False)
    ]
    if failures:
        lines = ["These checks failed:"]
        for scenario in failures:
            name = scenario.get("name", "<unnamed>")
            detail = scenario.get("error") or scenario.get("detail") or "failed"
            lines.append(f"- {name}: {detail}")
        parts.append("\n".join(lines))

    if not harness_error and not failures:
        parts.append(f"Full report:\n{json.dumps(report, indent=2, default=str)}")

    parts.append(
        "Send the complete corrected contents of every file you need to "
        "change, each in its own ```file:PATH block."
    )

    feedback = "\n\n".join(parts)
    if len(feedback) > _MAX_FEEDBACK_CHARS:
        keep = _MAX_FEEDBACK_CHARS // 2
        feedback = (
            feedback[:keep] + "\n\n[...feedback truncated...]\n\n" + feedback[-keep:]
        )
    return feedback


def _write_transcript(transcript_dir: Path, result: LoopResult) -> None:
    transcript_dir.mkdir(parents=True, exist_ok=True)
    for iteration in result.iterations:
        (transcript_dir / f"iteration-{iteration.index:03d}.response.txt").write_text(
            iteration.response, encoding="utf-8"
        )
    payload = {
        "passed": result.passed,
        "stop_reason": result.stop_reason,
        "iteration_count": result.iteration_count,
        "impl_dir": result.impl_dir,
        "iterations": [asdict(i) for i in result.iterations],
    }
    (transcript_dir / "loop.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )


def run_loop(
    brief: str,
    impl_dir: Path | None,
    model_fn: Callable[[list[dict]], str],
    verify_fn: Callable[[Path | None], dict],
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    transcript_dir: Path | None = None,
) -> LoopResult:
    """Drive ``model_fn`` until ``verify_fn`` passes or attempts run out."""
    messages: list[dict] = [{"role": "user", "content": brief + FORMAT_INSTRUCTIONS}]
    iterations: list[Iteration] = []
    stop_reason = "max_iterations"
    passed = False

    for index in range(1, max_iterations + 1):
        response = model_fn(messages)
        iteration = Iteration(index=index, response=response)
        iterations.append(iteration)

        blocks = parse_file_blocks(response)

        if not blocks:
            # A formatting slip is not a capability failure — nudge once and
            # let the iteration cap bound the cost. The verifier is NOT run:
            # the tree is unchanged, so it would re-score the previous
            # attempt and could report a false pass.
            messages = messages + [
                {"role": "assistant", "content": response},
                {"role": "user", "content": _NUDGE},
            ]
            continue

        try:
            written = write_file_blocks(impl_dir, blocks) if impl_dir else []
        except UnsafePathError as exc:
            iteration.report = {"passed": False, "unsafe_path": str(exc)}
            stop_reason = "unsafe_path"
            break

        iteration.files_written = (
            [str(p) for p in written] if impl_dir else sorted(blocks)
        )

        report = verify_fn(impl_dir)
        iteration.report = report
        iteration.passed = bool(report.get("passed"))

        if iteration.passed:
            passed = True
            stop_reason = "passed"
            break

        messages = messages + [
            {"role": "assistant", "content": response},
            {"role": "user", "content": build_feedback(report)},
        ]

    result = LoopResult(
        passed=passed,
        stop_reason=stop_reason,
        iterations=iterations,
        impl_dir=str(impl_dir) if impl_dir else None,
    )

    if transcript_dir:
        _write_transcript(Path(transcript_dir), result)

    return result
