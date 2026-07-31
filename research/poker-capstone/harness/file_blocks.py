"""Parse and safely write ```file:NAME fenced blocks from a model answer.

This is the transport between a text-only local model and a real
implementation directory. Two things matter more than they might look:

1. **Variable-length fences.** A submission can legitimately contain a
   file that itself has a ``` fence (a README, a docs snippet). We follow
   CommonMark's rule — an opening fence of N backticks is closed only by a
   line of N or more — so those survive intact.
2. **A truncated block is discarded, not half-written.** Running out of
   max_tokens mid-file is a transport failure; writing the partial file
   would surface later as a syntax error and be scored as a model defect.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

_OPEN_FENCE = re.compile(r"^(`{3,})file:(.+?)\s*$")


class UnsafePathError(Exception):
    """A block named a path that would land outside the implementation
    directory. Treated as fatal for the run rather than skipped, because a
    model emitting one means the answer is not something we should be
    applying to disk at all."""


def _consume_block(
    lines: list[str], start: int, fence_len: int
) -> tuple[list[str], int, bool]:
    """Read a block body from ``start`` until a fence of >= ``fence_len``.

    Returns (body, index_after_block, closed). ``closed`` is False when the
    answer ran out first, which means the response was truncated.
    """
    close = re.compile(rf"^`{{{fence_len},}}\s*$")
    body: list[str] = []
    index = start
    while index < len(lines):
        if close.match(lines[index]):
            return body, index + 1, True
        body.append(lines[index])
        index += 1
    return body, index, False


def parse_file_blocks(text: str) -> dict[str, str]:
    """Return {path: content} for every complete ```file:PATH block.

    Later blocks win on duplicate paths — a model correcting itself later
    in the same answer means the last version is the intended one.
    """
    blocks: dict[str, str] = {}
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    index = 0
    while index < len(lines):
        match = _OPEN_FENCE.match(lines[index])
        if not match:
            index += 1
            continue

        fence, path = match.group(1), match.group(2).strip()
        body, index, closed = _consume_block(lines, index + 1, len(fence))

        # An unclosed fence means the answer was cut off mid-file. Drop it.
        if closed and path:
            blocks[path] = "".join(line + "\n" for line in body)

    return blocks


def _safe_destination(root: Path, name: str) -> Path:
    if not name or name.startswith(("/", "~")) or os.path.isabs(name):
        raise UnsafePathError(f"absolute or home-relative path not allowed: {name!r}")
    if ".." in Path(name).parts:
        raise UnsafePathError(f"parent-directory traversal not allowed: {name!r}")

    dest = root / name
    # realpath resolves symlinks, so a link planted inside impl_dir cannot
    # be used to write outside it.
    resolved_root = Path(os.path.realpath(root))
    resolved_dest = Path(os.path.realpath(dest))
    if resolved_root not in resolved_dest.parents:
        raise UnsafePathError(f"path escapes the implementation directory: {name!r}")
    return dest


def write_file_blocks(root: Path, blocks: dict[str, str]) -> list[Path]:
    """Write every block under ``root``, creating parent directories.

    All paths are validated before anything is written, so one bad path
    cannot leave a half-applied tree for the next iteration to build on.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)

    destinations = {name: _safe_destination(root, name) for name in blocks}

    written: list[Path] = []
    for name, dest in destinations.items():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(blocks[name], encoding="utf-8")
        written.append(dest)
    return written
