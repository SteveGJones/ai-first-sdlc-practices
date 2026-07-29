"""CLI entry point for the (optional) client verification pass — kept
separate from `python -m harness` (the required, server-only stage-4
result) since HARNESS-CONTRACT.md is explicit that a client is not
required and its absence never fails the core result.

Usage: python -m harness.client_verify --impl-dir <path> [--project-name NAME]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import browser_scenarios, runner


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl-dir", required=True)
    ap.add_argument("--project-name", default="poker-client-harness")
    ap.add_argument("--build-timeout-s", type=int, default=900)
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

    if not stack.client_url:
        report = {
            "passed": None,
            "skipped": True,
            "reason": "no client service discovered (client is optional per HARNESS-CONTRACT.md)",
        }
        runner.tear_down(impl_dir, args.project_name)
        print(json.dumps(report, indent=2))
        return 0

    try:
        report = browser_scenarios.run_all(stack.base_url, stack.client_url)
    except browser_scenarios.BrowserScenarioError as exc:
        report = {"passed": False, "harness_error": str(exc)}
    finally:
        runner.tear_down(impl_dir, args.project_name)

    print(json.dumps(report, indent=2, default=str))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    sys.exit(main())
