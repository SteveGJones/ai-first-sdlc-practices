"""CLI: run a build phase against a local MLX model, agentically.

This is the entry point that makes P5/P6-style build phases runnable by a
text-only local model. It wires the real Docker verifier into
``local_agent.run_loop``.

Usage:

    # Start the server FIRST, with a bounded prompt cache. Unbounded, it
    # accumulates a KV sequence per session and OOMs the GPU (crashed a run
    # on 2026-07-30). Note --max-concurrent does NOT exist in mlx-lm 0.31.3.
    uv run --with mlx-lm mlx_lm.server \\
      --model mlx-community/Qwen2.5-Coder-14B-Instruct-4bit --port 8081 \\
      --decode-concurrency 1 --prompt-concurrency 1 \\
      --prompt-cache-size 2 --prompt-cache-bytes 4294967296

    python -m harness.run_local \\
      --brief runs/local-p5/brief.md \\
      --impl-dir runs/local-p5/impl \\
      --transcript-dir runs/local-p5/transcript \\
      --model mlx-community/Qwen2.5-Coder-14B-Instruct-4bit

Reported ``iteration_count`` is the headline fairness caveat when comparing
against the Sonnet/Haiku baselines — a pass on attempt 5 is not a pass on
attempt 1, and the write-up must say which it was.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import runner, scenarios
from .local_agent import DEFAULT_MAX_ITERATIONS, run_loop
from .mlx_client import DEFAULT_BASE_URL, MlxClient, probe


def verify_server(
    impl_dir: Path,
    project_name: str = "poker-local",
    build_timeout_s: int = 900,
    health_timeout_s: int = 60,
) -> dict:
    """Bring the submitted stack up, drive the stage-4 scenarios, tear down.

    Mirrors ``harness.__main__`` but returns the report instead of printing
    it, and never raises — the loop needs every failure as feedback, not as
    an exception.
    """
    try:
        stack = runner.bring_up(
            impl_dir,
            project_name,
            build_timeout_s=build_timeout_s,
            health_timeout_s=health_timeout_s,
        )
    except runner.HarnessError as exc:
        return {"passed": False, "harness_error": str(exc)}

    try:
        return scenarios.run_all(stack.base_url)
    except scenarios.ScenarioError as exc:
        return {"passed": False, "harness_error": str(exc)}
    finally:
        runner.tear_down(impl_dir, project_name)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--brief", required=True, help="path to the phase brief")
    ap.add_argument("--impl-dir", required=True, help="where the model's files land")
    ap.add_argument("--transcript-dir", default="", help="per-iteration audit trail")
    ap.add_argument(
        "--model", required=True, help="hf model id served by mlx_lm.server"
    )
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--max-iterations", type=int, default=DEFAULT_MAX_ITERATIONS)
    ap.add_argument("--project-name", default="poker-local")
    ap.add_argument("--build-timeout-s", type=int, default=900)
    ap.add_argument(
        "--context",
        action="append",
        default=[],
        help="extra file to append to the brief (e.g. docs/HARNESS-CONTRACT.md); "
        "repeatable",
    )
    args = ap.parse_args(argv)

    if not probe(args.base_url):
        print(
            f"mlx_lm.server not reachable at {args.base_url}. Start it with a "
            "bounded prompt cache (see this module's docstring).",
            file=sys.stderr,
        )
        return 2

    brief = Path(args.brief).read_text(encoding="utf-8")
    for extra in args.context:
        path = Path(extra)
        brief += f"\n\n---\n\n# {path.name}\n\n{path.read_text(encoding='utf-8')}"

    impl_dir = Path(args.impl_dir).resolve()
    client = MlxClient(model=args.model, base_url=args.base_url)

    result = run_loop(
        brief,
        impl_dir=impl_dir,
        model_fn=client,
        verify_fn=lambda d: verify_server(
            d,
            project_name=args.project_name,
            build_timeout_s=args.build_timeout_s,
        ),
        max_iterations=args.max_iterations,
        transcript_dir=Path(args.transcript_dir) if args.transcript_dir else None,
    )

    print(
        json.dumps(
            {
                "passed": result.passed,
                "stop_reason": result.stop_reason,
                "iteration_count": result.iteration_count,
                "model": args.model,
                "impl_dir": str(impl_dir),
                "per_iteration_passed": [i.passed for i in result.iterations],
            },
            indent=2,
        )
    )
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
