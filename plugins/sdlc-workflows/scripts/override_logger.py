#!/usr/bin/env python3
"""Append-only JSONL logger for team_extend overrides.

Each workflow run that uses ``team_extend`` logs one entry per extended
agent.  The coaching signals module reads this log to detect frequently
overridden agents that should be promoted to standing team members.

Public API
----------
log_override(log_path, team, agent, workflow, node) -> None
read_overrides(log_path) -> list[dict]
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def log_override(
    log_path: Path,
    team: str,
    agent: str,
    workflow: str,
    node: str,
) -> None:
    """Append a single override entry to the JSONL log.

    Creates parent directories and the file if they don't exist.
    """
    logger.info(
        "Recording team_extend override",
        extra={
            "team": team,
            "agent": agent,
            "workflow": workflow,
            "node": node,
            "log_path": str(log_path),
        },
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "team": team,
        "agent": agent,
        "workflow": workflow,
        "node": node,
    }

    with log_path.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_overrides(log_path: Path) -> list[dict]:
    """Read all override entries from the JSONL log.

    Returns an empty list if the file doesn't exist or is empty.
    """
    logger.debug("Reading override log", extra={"log_path": str(log_path)})
    if not log_path.exists():
        return []

    entries: list[dict] = []
    malformed = 0
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            logger.warning(
                "Skipping malformed override log entry",
                extra={"log_path": str(log_path)},
            )
            malformed += 1
            continue
    logger.info(
        "Override log read complete",
        extra={"log_path": str(log_path), "entries": len(entries), "malformed": malformed},
    )
    return entries
