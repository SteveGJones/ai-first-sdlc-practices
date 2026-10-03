#!/usr/bin/env python3
"""Compute a deterministic sha256 hash of an assessment stack item directory.

The hash covers every file under the item directory (item.json, prompt.md,
inputs/*, expected/*), in sorted relative-path order. For each file the
POSIX-style relative path and the raw file bytes are folded into the digest,
so the hash changes if any file's content OR its path/name changes, but is
stable across machines/OSes (no mtimes, no absolute paths).

Usage (importable module + CLI):
    python3 stack_hash.py <item-dir>   # prints the hex digest and exits 0

Stdlib only.
"""

import hashlib
import os
import sys


def _iter_relative_files(item_dir):
    """Yield POSIX-style relative file paths under `item_dir`, sorted."""
    base = os.path.abspath(item_dir)
    rels = []
    for root, dirs, filenames in os.walk(base):
        dirs.sort()
        for fn in filenames:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, base)
            rels.append(rel.replace(os.sep, "/"))
    return sorted(rels)


def compute_hash(item_dir):
    """Return the hex sha256 digest for the contents of `item_dir`.

    Raises FileNotFoundError if `item_dir` does not exist or is empty.
    """
    base = os.path.abspath(item_dir)
    if not os.path.isdir(base):
        raise FileNotFoundError(f"not a directory: {item_dir}")
    rel_paths = _iter_relative_files(base)
    if not rel_paths:
        raise FileNotFoundError(f"no files found under: {item_dir}")

    digest = hashlib.sha256()
    for rel in rel_paths:
        full = os.path.join(base, rel.replace("/", os.sep))
        with open(full, "rb") as f:
            content = f.read()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(content)
        digest.update(b"\x00")
    return digest.hexdigest()


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: stack_hash.py <item-dir>\n")
        return 2
    try:
        print(compute_hash(argv[1]))
    except FileNotFoundError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
