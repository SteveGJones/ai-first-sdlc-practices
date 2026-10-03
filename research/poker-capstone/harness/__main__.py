"""CLI entry point: build+run a submitted implementation, drive the
stage-4 scenarios against it, tear down, report.

Usage: python -m harness --impl-dir <path> [--project-name NAME]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import runner, scenarios


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--impl-dir", required=True, help="directory containing docker-compose.yml"
    )
    ap.add_argument("--project-name", default="poker-harness")
    ap.add_argument(
        "--build-timeout-s",
        type=int,
        default=900,
        help="submitted stacks vary a lot in build weight (a lightweight Python "
        "server vs. a TypeScript/React client with npm install) — tune per run "
        "if a legitimate heavier stack needs more than the default",
    )
    ap.add_argument("--health-timeout-s", type=int, default=60)
    args = ap.parse_args()

    impl_dir = Path(args.impl_dir).resolve()
    try:
        stack = runner.bring_up(
            impl_dir,
            args.project_name,
            build_timeout_s=args.build_timeout_s,
            health_timeout_s=args.health_timeout_s,
        )
    except runner.HarnessError as exc:
        print(json.dumps({"passed": False, "harness_error": str(exc)}, indent=2))
        return 1

    try:
        report = scenarios.run_all(stack.base_url)
    except scenarios.ScenarioError as exc:
        report = {"passed": False, "harness_error": str(exc)}
    finally:
        runner.tear_down(impl_dir, args.project_name)

    print(json.dumps(report, indent=2, default=str))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    sys.exit(main())
