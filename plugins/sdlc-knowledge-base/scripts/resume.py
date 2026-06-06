"""Run identity, hashing, locking (with fencing), and lifecycle for kb-offline (#211, M0).

The manifest is the operator-visible source of run truth; the LangGraph checkpointer
(M1+) is only an internal retry convenience.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
from pathlib import Path


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def config_hash(config: dict) -> str:
    return content_hash(json.dumps(config, sort_keys=True, separators=(",", ":")))
