"""Durable atomic file write (issue #211, M0).

write temp -> fsync file -> atomic replace -> fsync directory. Used by the mutation
committer, the journal, and the upgraded #208 helpers so a crash cannot leave a
half-written or non-durable file.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path


def atomic_write_text(path, text: str, encoding: str = "utf-8") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Unique temp name per write: a fixed ".tmp" suffix collides when two workers
    # write the same target concurrently (M1b parallel heartbeats), where one
    # worker's os.replace consumes the shared temp before the other's runs.
    tmp = path.with_suffix(f"{path.suffix}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    with open(tmp, "w", encoding=encoding) as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    dir_fd = os.open(str(path.parent), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
    return path
