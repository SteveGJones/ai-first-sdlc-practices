#!/usr/bin/env python3
"""Sync agents/ source tree to .claude/agents/ flat directory.

Copies agent markdown files from the categorized agents/ directory
to .claude/agents/ (flat structure) for Claude Code to discover.
"""

import argparse
import shutil
import sys
from pathlib import Path


def find_agent_sources(agents_dir: Path):
    """Find all agent source files, excluding READMEs and templates."""
    return sorted(
        f
        for f in agents_dir.rglob("*.md")
        if "README" not in f.name
        and "template" not in f.stem.lower()
        and "templates" not in f.parts
    )


def sync_agents(dry_run: bool = False):
    """Sync agents/ tree to .claude/agents/ flat directory."""
    agents_dir = Path("agents")
    target_dir = Path(".claude/agents")

    if not agents_dir.exists():
        print("Error: agents/ directory not found. Run from project root.")
        return 1

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    source_files = find_agent_sources(agents_dir)
    added, updated, unchanged = 0, 0, 0

    for src in source_files:
        dest = target_dir / src.name
        if not dest.exists():
            if not dry_run:
                shutil.copy2(src, dest)
            print(f"  ADD: {src} -> {dest}")
            added += 1
        elif src.read_text(encoding="utf-8") != dest.read_text(encoding="utf-8"):
            if not dry_run:
                shutil.copy2(src, dest)
            print(f"  UPDATE: {src} -> {dest}")
            updated += 1
        else:
            unchanged += 1

    prefix = "[DRY RUN] " if dry_run else ""
    print(f"\n{prefix}Sync complete: {added} added, {updated} updated, {unchanged} unchanged")
    print(f"Total agents in source: {len(source_files)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Sync agents/ to .claude/agents/")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would change without modifying files"
    )
    args = parser.parse_args()
    sys.exit(sync_agents(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
