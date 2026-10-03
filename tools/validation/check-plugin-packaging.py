#!/usr/bin/env python3
"""
Plugin packaging validator.

Ensures every source file listed in release-mapping.yaml has been packaged into
the corresponding plugin directory. This catches the failure mode where source
files are added to release-mapping.yaml but release-plugin is never run, leaving
the plugin directory empty or out-of-sync with source.

This would have caught issue #137 (sdlc-knowledge-base plugin shipped empty in
EPIC #105) at PR time.

Usage:
    python tools/validation/check-plugin-packaging.py
    python tools/validation/check-plugin-packaging.py --verbose

Exit codes:
    0 — all source files are packaged
    1 — at least one source file is missing from its plugin directory
    2 — configuration error (release-mapping.yaml missing or malformed)
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MAPPING_FILE = REPO_ROOT / "release-mapping.yaml"


def source_to_plugin_dest(source: str, dest_override: str | None, plugin: str) -> Path:
    """
    Compute the expected destination path in the plugin directory for a source
    file, following the same rules release-plugin uses.

    Rules:
    - agents/<category>/<file>.md → plugins/<plugin>/agents/<file>.md
      (category flattened to just the filename)
    - skills/<skill-name>/<rest> → plugins/<plugin>/skills/<skill-name>/<rest>
      (structure preserved under skills/)
    - CONSTITUTION.md or other single-file sources with explicit dest → plugins/<plugin>/<dest>
    - plugins/<plugin>/... → same path (already in plugin; verify presence only)
    - tools/validation/<file> → plugins/<plugin>/scripts/<file>
      (single-file tool scripts go to plugins/<plugin>/scripts/ per the release-plugin skill)
    """
    if dest_override:
        return REPO_ROOT / "plugins" / plugin / dest_override

    src_path = Path(source)
    parts = src_path.parts

    # Already-in-plugin case: hooks and pre-existing plugin scripts
    if parts[0] == "plugins":
        return REPO_ROOT / src_path

    # agents/<category>/<file>.md — flatten category
    if parts[0] == "agents" and len(parts) >= 3:
        return REPO_ROOT / "plugins" / plugin / "agents" / parts[-1]

    # skills/<skill-name>/<rest> — preserve structure under skills/
    if parts[0] == "skills" and len(parts) >= 2:
        return REPO_ROOT / "plugins" / plugin / Path(*parts)

    # tools/validation/<file> — becomes plugins/<plugin>/scripts/<file>
    if parts[0] == "tools" and len(parts) >= 2:
        return REPO_ROOT / "plugins" / plugin / "scripts" / parts[-1]

    # data/<path> — preserve structure under data/
    if parts[0] == "data" and len(parts) >= 2:
        return REPO_ROOT / "plugins" / plugin / Path(*parts)

    # Fallback: unknown shape, return source mapped under plugin root
    # (will likely fail the existence check and surface the unknown case)
    return REPO_ROOT / "plugins" / plugin / src_path


def check_plugin(plugin_name: str, plugin_config: dict, verbose: bool) -> list[str]:
    """
    Check one plugin's packaging. Returns a list of error messages (empty if OK).
    """
    errors = []
    component_types = ("skills", "agents", "scripts", "hooks", "data")

    for component_type in component_types:
        entries = plugin_config.get(component_type) or []
        for entry in entries:
            source = entry.get("source")
            dest_override = entry.get("dest")
            if not source:
                errors.append(
                    f"[{plugin_name}] {component_type} entry missing 'source' field: {entry}"
                )
                continue

            src_abs = REPO_ROOT / source
            if not src_abs.exists():
                errors.append(
                    f"[{plugin_name}] source file missing: {source}"
                )
                continue

            expected_dest = source_to_plugin_dest(source, dest_override, plugin_name)
            if not expected_dest.exists():
                rel = expected_dest.relative_to(REPO_ROOT)
                errors.append(
                    f"[{plugin_name}] source file {source} is not packaged — "
                    f"expected at {rel} but file missing. "
                    f"Run /sdlc-core:release-plugin to sync."
                )
                continue

            # Content check: the packaged file should match the source byte-for-byte
            # (or the override destination should exist with expected content)
            try:
                src_bytes = src_abs.read_bytes()
                dst_bytes = expected_dest.read_bytes()
            except OSError as exc:
                errors.append(
                    f"[{plugin_name}] could not read {source} or its destination: {exc}"
                )
                continue

            if src_bytes != dst_bytes:
                rel = expected_dest.relative_to(REPO_ROOT)
                errors.append(
                    f"[{plugin_name}] source file {source} differs from packaged copy at "
                    f"{rel}. Run /sdlc-core:release-plugin to resync."
                )
                continue

            if verbose:
                print(f"  OK {source} → {expected_dest.relative_to(REPO_ROOT)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify plugin packaging matches release-mapping.yaml"
    )
    parser.add_argument("--verbose", action="store_true", help="Show every OK file")
    args = parser.parse_args()

    if not MAPPING_FILE.exists():
        print(f"ERROR: {MAPPING_FILE} not found", file=sys.stderr)
        return 2

    try:
        with MAPPING_FILE.open() as handle:
            mapping = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        print(f"ERROR: {MAPPING_FILE} is not valid YAML: {exc}", file=sys.stderr)
        return 2

    if not isinstance(mapping, dict):
        print(f"ERROR: {MAPPING_FILE} must be a YAML mapping", file=sys.stderr)
        return 2

    all_errors = []
    plugin_count = 0
    for plugin_name, plugin_config in mapping.items():
        if not isinstance(plugin_config, dict):
            continue
        plugin_count += 1
        if args.verbose:
            print(f"Checking {plugin_name}...")
        errors = check_plugin(plugin_name, plugin_config, args.verbose)
        all_errors.extend(errors)

    if all_errors:
        print()
        print(f"Plugin packaging check FAILED — {len(all_errors)} error(s) across "
              f"{plugin_count} plugin(s):")
        print()
        for error in all_errors:
            print(f"  - {error}")
        print()
        print("To fix: run /sdlc-core:release-plugin to sync source files into "
              "their plugin directories, then re-run this check.")
        return 1

    print(f"Plugin packaging check PASSED — {plugin_count} plugin(s) verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
