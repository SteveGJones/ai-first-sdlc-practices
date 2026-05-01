"""CommissioningRecord — read/write the `.sdlc/team-config.json` schema extension.

The recorder is filesystem-only; no database. Existing `.sdlc/team-config.json`
files (e.g. team_name, project metadata) are preserved on write. The
commissioning_history array accumulates each commissioning event; the
top-level fields reflect the latest commissioning.

Backward compatibility: projects without sdlc_option in their team-config.json
are NOT commissioned (per is_commissioned). Callers should use
default_option_for_uncommissioned() to get the safe default ("single-team").
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class CommissioningRecord:
    """One commissioning event."""

    sdlc_option: str
    sdlc_level: str
    commissioned_at: str  # ISO 8601 UTC
    commissioned_by: str
    option_bundle_version: str
    commissioning_history: list[dict[str, Any]] = field(default_factory=list)

    # Reserved Phase E fields (populated by Assured bundle commissioning)
    decomposition: Optional[Any] = None
    commissioning_options: dict[str, Any] = field(default_factory=dict)


def _to_history_entry(record: CommissioningRecord) -> dict[str, Any]:
    """Convert a record to a history-array entry (the per-event snapshot)."""
    return {
        "sdlc_option": record.sdlc_option,
        "sdlc_level": record.sdlc_level,
        "commissioned_at": record.commissioned_at,
        "commissioned_by": record.commissioned_by,
        "option_bundle_version": record.option_bundle_version,
    }


def read_record(path: Path) -> CommissioningRecord:
    """Read a CommissioningRecord from a `.sdlc/team-config.json` file.

    Raises FileNotFoundError if the file is absent. May raise KeyError if the
    file exists but lacks required commissioning fields (sdlc_option,
    sdlc_level, commissioned_at, commissioned_by, option_bundle_version) —
    callers wanting a soft check should use is_commissioned() first.
    """
    if not path.exists():
        raise FileNotFoundError(f"team-config.json not found at {path}")

    raw = json.loads(path.read_text())
    return CommissioningRecord(
        sdlc_option=raw["sdlc_option"],
        sdlc_level=raw["sdlc_level"],
        commissioned_at=raw["commissioned_at"],
        commissioned_by=raw["commissioned_by"],
        option_bundle_version=raw["option_bundle_version"],
        commissioning_history=raw.get("commissioning_history", []),
        decomposition=raw.get("decomposition"),
        commissioning_options=raw.get("commissioning_options", {}),
    )


def write_record(path: Path, record: CommissioningRecord) -> None:
    """Write a CommissioningRecord to `.sdlc/team-config.json`.

    Preserves any existing keys unrelated to commissioning. Appends to
    commissioning_history if the file already had a record; otherwise starts
    a one-entry history.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        existing = json.loads(path.read_text())
    else:
        existing = {}

    history = existing.get("commissioning_history", [])
    history.append(_to_history_entry(record))

    merged = dict(existing)
    merged.update(
        {
            "sdlc_option": record.sdlc_option,
            "sdlc_level": record.sdlc_level,
            "commissioned_at": record.commissioned_at,
            "commissioned_by": record.commissioned_by,
            "option_bundle_version": record.option_bundle_version,
            "commissioning_history": history,
        }
    )
    if record.decomposition is not None:
        merged["decomposition"] = record.decomposition
    if record.commissioning_options:
        merged["commissioning_options"] = record.commissioning_options

    path.write_text(json.dumps(merged, indent=2) + "\n")


def is_commissioned(path: Path) -> bool:
    """Return True if the team-config.json at `path` contains a sdlc_option."""
    if not path.exists():
        return False
    try:
        raw = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    return "sdlc_option" in raw


def default_option_for_uncommissioned() -> str:
    """Backward-compat default for projects that haven't been commissioned."""
    return "single-team"
