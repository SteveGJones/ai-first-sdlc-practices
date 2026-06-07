"""Run identity, hashing, locking (with fencing), and lifecycle for kb-offline (#211, M0).

The manifest is the operator-visible source of run truth; the LangGraph checkpointer
(M1+) is only an internal retry convenience.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import time
from pathlib import Path


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def config_hash(config: dict) -> str:
    return content_hash(json.dumps(config, sort_keys=True, separators=(",", ":")))


_LOCK_NAME = ".kb-offline/lock.json"
_FENCE_NAME = ".kb-offline/fence.txt"


def _kb_dir(library_path: Path) -> Path:
    d = Path(library_path) / ".kb-offline"
    d.mkdir(parents=True, exist_ok=True)
    return d


class LibraryLock:
    """Per-library advisory lock with PID + heartbeat staleness and a monotonic
    fencing token. The token, checked before every commit, makes stale-lock reclaim
    *safe*: a paused process that lost its lease is fenced out at commit time."""

    def __init__(self, library_path, ttl_seconds: float = 120.0):
        self.library_path = Path(library_path)
        self.ttl = ttl_seconds
        self._token: int | None = None

    def _lockfile(self) -> Path:
        return self.library_path / _LOCK_NAME

    def _fencefile(self) -> Path:
        return self.library_path / _FENCE_NAME

    def _next_token(self) -> int:
        from .durability import atomic_write_text
        _kb_dir(self.library_path)
        f = self._fencefile()
        current = int(f.read_text()) if f.exists() else 0
        nxt = current + 1
        atomic_write_text(f, str(nxt))
        return nxt

    def current_token(self) -> int:
        f = self._fencefile()
        return int(f.read_text()) if f.exists() else 0

    def _read_lock(self) -> dict | None:
        lf = self._lockfile()
        if not lf.exists():
            return None
        try:
            return json.loads(lf.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def _is_stale(self, lock: dict, now: float) -> bool:
        if (now - float(lock.get("heartbeat", 0))) > self.ttl:
            return True
        pid = int(lock.get("pid", -1))
        if lock.get("host") == socket.gethostname():
            try:
                os.kill(pid, 0)
            except (OSError, ProcessLookupError):
                return True
        return False

    def try_acquire(self) -> int | None:
        from .durability import atomic_write_text
        now = time.time()
        existing = self._read_lock()
        if existing is not None and not self._is_stale(existing, now):
            return None
        token = self._next_token()
        atomic_write_text(self._lockfile(), json.dumps({
            "pid": os.getpid(), "host": socket.gethostname(),
            "heartbeat": now, "token": token,
        }))
        self._token = token
        return token

    def acquire(self) -> int:
        token = self.try_acquire()
        if token is None:
            raise RuntimeError(f"library is locked by a live run: {self.library_path}")
        return token

    def heartbeat(self) -> None:
        from .durability import atomic_write_text
        lock = self._read_lock() or {}
        lock["heartbeat"] = time.time()
        atomic_write_text(self._lockfile(), json.dumps(lock))

    def release(self) -> None:
        lf = self._lockfile()
        if lf.exists():
            lf.unlink()
        self._token = None


_RUNS_NAME = ".kb-offline/runs.json"

RESUMABLE_STATES = {"running", "failed"}


class RunRegistry:
    """Manifest-backed registry of runs and their lifecycle states. Run IDs are
    derived deterministically from a caller-supplied timestamp + fingerprint (no
    Date.now/random at import or in pure logic — the caller passes the timestamp)."""

    def __init__(self, library_path):
        self.library_path = Path(library_path)

    def _path(self) -> Path:
        _kb_dir(self.library_path)
        return self.library_path / _RUNS_NAME

    def _load(self) -> dict:
        p = self._path()
        if not p.exists():
            return {"runs": {}}
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            return {"runs": {}}

    def _save(self, data: dict) -> None:
        from .durability import atomic_write_text
        atomic_write_text(self._path(), json.dumps(data, indent=2))

    def start_run(self, timestamp: str, fingerprint: dict) -> str:
        data = self._load()
        run_id = content_hash(timestamp + json.dumps(fingerprint, sort_keys=True))[:16]
        data["runs"][run_id] = {
            "run_id": run_id, "started_at": timestamp, "state": "running",
            "fingerprint": fingerprint, "seq": len(data["runs"]),
        }
        self._save(data)
        return run_id

    def exists(self, run_id: str) -> bool:
        return run_id in self._load().get("runs", {})

    def set_state(self, run_id: str, state: str) -> None:
        data = self._load()
        data["runs"][run_id]["state"] = state
        self._save(data)

    def select_resumable(self, fingerprint: dict) -> str | None:
        data = self._load()
        candidates = [
            r for r in data["runs"].values()
            if r["state"] in RESUMABLE_STATES and r["fingerprint"] == fingerprint
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda r: r["seq"])["run_id"]


def step_id(run_id: str, stage: str, item: str) -> str:
    """Canonical journal/graph step identifier: f"{run_id}:{stage}:{item}".

    Single scheme across the CLI, ingest_graph, and commit_mutation so a replayed
    node passes the identical journal step ID (idempotent replay). stage e.g.
    'extract'/'reduce'; item is the source slug or target filename."""
    return f"{run_id}:{stage}:{item}"
