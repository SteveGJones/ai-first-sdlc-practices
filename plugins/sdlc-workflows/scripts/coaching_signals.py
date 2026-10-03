#!/usr/bin/env python3
"""Analyse delegation teams for tiered coaching signals.

Signal tiers:
- **critical** — action required (e.g. referenced team not built)
- **advisory** — worth reviewing (e.g. stale image, unused team)
- **informational** — patterns to be aware of (e.g. frequent overrides)

Public API
----------
analyse_team(team_data) -> list[dict]
analyse_fleet(teams) -> dict[str, list[dict]]
analyse_overrides(log_path, threshold=3) -> list[dict]
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

logger = logging.getLogger(__name__)


def analyse_team(team: dict) -> list[dict]:
    """Produce coaching signals for a single team status dict.

    Parameters
    ----------
    team:
        A dict from ``teams_status_report.fleet_report()["teams"]``.

    Returns
    -------
    list[dict]
        Each signal has ``type``, ``tier``, ``team``, ``message`` keys.
    """
    signals: list[dict] = []
    name = team.get("name", "unknown")
    stale = team.get("staleness", "current")
    wf_count = team.get("workflow_count", 0)
    logger.debug(
        "Analysing team for coaching signals",
        extra={"team": name, "staleness": stale, "workflow_count": wf_count},
    )

    if stale == "not_built" and wf_count > 0:
        signals.append({
            "type": "not_built",
            "tier": "critical",
            "team": name,
            "message": (
                f"{name} is referenced by {wf_count} workflow(s) "
                "but has no image built"
            ),
        })
    elif stale == "not_built":
        signals.append({
            "type": "not_built",
            "tier": "critical",
            "team": name,
            "message": f"{name} has no image built",
        })

    if stale == "stale":
        signals.append({
            "type": "stale_image",
            "tier": "advisory",
            "team": name,
            "message": (
                f"{name} image is stale (manifest updated "
                f"{team.get('updated', '?')}, image built "
                f"{team.get('image_built', '?')})"
            ),
        })

    if wf_count == 0 and stale != "not_built":
        signals.append({
            "type": "unused_team",
            "tier": "advisory",
            "team": name,
            "message": (
                f"{name} is not referenced by any workflow — "
                "consider deleting or assigning to a workflow"
            ),
        })

    return signals


def analyse_fleet(
    teams: list[dict],
) -> dict[str, list[dict]]:
    """Aggregate coaching signals across all teams.

    Returns ``{"critical": [...], "advisory": [...], "informational": [...]}``.
    """
    logger.info("Analysing fleet coaching signals", extra={"team_count": len(teams)})
    result: dict[str, list[dict]] = {
        "critical": [],
        "advisory": [],
        "informational": [],
    }

    for team in teams:
        for signal in analyse_team(team):
            tier = signal.get("tier", "informational")
            result.setdefault(tier, []).append(signal)

    return result


def analyse_overrides(
    log_path: Path,
    threshold: int = 3,
) -> list[dict]:
    """Detect frequently overridden agents from the override log.

    Parameters
    ----------
    log_path:
        Path to ``overrides.jsonl`` (append-only JSONL file).
    threshold:
        Minimum number of overrides to trigger a signal.

    Returns
    -------
    list[dict]
        Coaching signals for frequently overridden agents.
    """
    logger.info(
        "Analysing override log",
        extra={"log_path": str(log_path), "threshold": threshold},
    )
    if not log_path.exists():
        return []

    counter: Counter[str] = Counter()
    teams_for_agent: dict[str, set[str]] = {}
    malformed = 0

    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            logger.warning(
                "Skipping malformed override log line",
                extra={"log_path": str(log_path)},
            )
            malformed += 1
            continue
        agent = entry.get("agent", "")
        team = entry.get("team", "")
        if agent:
            counter[agent] += 1
            teams_for_agent.setdefault(agent, set()).add(team)

    signals: list[dict] = []
    for agent, count in counter.items():
        if count >= threshold:
            logger.info(
                "Override threshold crossed",
                extra={"agent": agent, "count": count, "threshold": threshold},
            )
            team_names = ", ".join(sorted(teams_for_agent.get(agent, set())))
            signals.append({
                "type": "frequent_override",
                "tier": "informational",
                "agent": agent,
                "count": count,
                "teams": team_names,
                "message": (
                    f"{agent} has been added via team_extend {count} times "
                    f"(on teams: {team_names}) — consider promoting to "
                    "a standing team member"
                ),
            })

    return signals


def main() -> None:
    """CLI entry point — run fleet + override analysis and print results."""
    import argparse
    import sys as _sys

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    logger.info("coaching_signals CLI start")

    _scripts_dir = Path(__file__).resolve().parent
    if str(_scripts_dir) not in _sys.path:
        _sys.path.insert(0, str(_scripts_dir))
    import teams_status_report

    parser = argparse.ArgumentParser(description="Coaching signal analysis")
    parser.add_argument(
        "--teams-dir", type=Path, default=Path(".archon/teams"),
    )
    parser.add_argument(
        "--workflows-dir", type=Path, default=Path(".archon/workflows"),
    )
    parser.add_argument(
        "--overrides", type=Path, default=Path(".archon/logs/overrides.jsonl"),
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    report = teams_status_report.fleet_report(args.teams_dir, args.workflows_dir)
    fleet_result = analyse_fleet(report["teams"])
    override_result = analyse_overrides(args.overrides)

    combined = {
        "critical": fleet_result["critical"],
        "advisory": fleet_result["advisory"],
        "informational": fleet_result["informational"] + override_result,
    }

    import json as json_mod

    if args.json:
        print(json_mod.dumps(combined, indent=2))
    else:
        for tier in ("critical", "advisory", "informational"):
            if combined[tier]:
                print(f"\n{tier.upper()}:")
                for signal in combined[tier]:
                    print(f"  - {signal['message']}")
        if not any(combined.values()):
            print("No coaching signals — fleet is healthy.")


if __name__ == "__main__":
    main()
