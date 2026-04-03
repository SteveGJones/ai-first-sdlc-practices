#!/usr/bin/env python3
"""Check for /tmp/ usage in agent and template files.

Framework agents and templates must use ./tmp/ (project-local) instead of /tmp/
(system temp directory) to avoid Claude Code permission issues and cross-session
file collisions.
"""

import re
import sys
from pathlib import Path

# Directories to scan
SCAN_DIRS = ["agents", "templates"]

# Directories to exclude (use /tmp/ legitimately)
EXCLUDE_DIRS = {
    "examples/ci-cd",
    "templates/gitignore",
    "docs/feature-proposals",
}

# Pattern: matches /tmp/ but NOT ./tmp/ (negative lookbehind)
TMP_PATTERN = re.compile(r"(?<!\.)\/tmp\/")


def should_exclude(filepath: Path) -> bool:
    """Check if a file path falls under an excluded directory."""
    path_str = str(filepath)
    return any(excluded in path_str for excluded in EXCLUDE_DIRS)


def check_file(filepath: Path) -> list:
    """Scan a single file for /tmp/ usage. Returns list of (line_num, line) tuples."""
    violations = []
    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return violations

    for line_num, line in enumerate(content.splitlines(), start=1):
        if TMP_PATTERN.search(line):
            violations.append((line_num, line.strip()))
    return violations


def main():
    root = Path(__file__).resolve().parent.parent.parent
    all_violations = {}

    for scan_dir in SCAN_DIRS:
        dir_path = root / scan_dir
        if not dir_path.exists():
            continue
        for md_file in dir_path.rglob("*.md"):
            if should_exclude(md_file.relative_to(root)):
                continue
            violations = check_file(md_file)
            if violations:
                rel_path = md_file.relative_to(root)
                all_violations[str(rel_path)] = violations

    if all_violations:
        print("ERROR: Found /tmp/ usage (use ./tmp/ instead):\n")
        total = 0
        for filepath, violations in sorted(all_violations.items()):
            for line_num, line in violations:
                print(f"  {filepath}:{line_num}: {line}")
                total += 1
        print(f"\n{total} violation(s) found in {len(all_violations)} file(s).")
        print("Replace /tmp/ with ./tmp/ and add 'mkdir -p ./tmp' before first use.")
        sys.exit(1)
    else:
        print("OK: No /tmp/ usage found in agent/template files.")
        sys.exit(0)


if __name__ == "__main__":
    main()
