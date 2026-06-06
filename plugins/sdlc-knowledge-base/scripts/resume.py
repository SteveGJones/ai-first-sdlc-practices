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
