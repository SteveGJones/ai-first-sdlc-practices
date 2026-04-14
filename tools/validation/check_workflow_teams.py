#!/usr/bin/env python3
"""
Validate workflow YAML image references against team manifests.

Checks:
1. Every image: reference must have a corresponding team manifest
2. Referenced teams must be active or ephemeral status
3. Nodes without image: are allowed (default worktree isolation)
4. sdlc-worker:base is always valid (no manifest needed)

Usage:
    python tools/validation/check_workflow_teams.py
    python tools/validation/check_workflow_teams.py --workflows-dir <path> --teams-dir <path>

Exit codes:
    0 -- all references valid
    1 -- validation errors found
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    # Fallback: use a minimal YAML parser for simple cases
    yaml = None  # type: ignore[assignment]

# The base image tag requires no team manifest
BASE_IMAGE_TAG = "base"

# Statuses that are acceptable for referenced teams
VALID_STATUSES = {"active", "ephemeral"}


def _parse_yaml(path: Path) -> dict:
    """Parse a YAML file and return its contents as a dict."""
    text = path.read_text()
    if yaml is not None:
        result = yaml.safe_load(text)
        if result is None:
            return {}
        if not isinstance(result, dict):
            return {}
        return result
    # Minimal fallback parser for CI environments without PyYAML
    # Handles the simple flat/list structures in workflow and team YAMLs
    return _minimal_yaml_parse(text)


def _minimal_yaml_parse(text: str) -> dict:
    """Very basic YAML parser for workflow/team files.

    Handles top-level keys, string values, and list-of-dict nodes.
    """
    result: dict = {}
    current_key: str | None = None
    current_list: list | None = None
    current_item: dict | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # Top-level key
        if indent == 0 and ":" in stripped:
            # Save pending item
            if current_item is not None and current_list is not None:
                current_list.append(current_item)
                current_item = None
            key, _, val = stripped.partition(":")
            val = val.strip()
            if val == "" or val == "|":
                current_key = key
                if current_key not in result:
                    result[current_key] = None
                current_list = None
            else:
                result[key] = val.strip("'\"")
                current_key = key
                current_list = None
            continue

        # List item at indent 2 (under a top-level key)
        if indent == 2 and stripped.startswith("- "):
            if current_item is not None and current_list is not None:
                current_list.append(current_item)
                current_item = None

            item_content = stripped[2:]
            if ":" in item_content:
                # Dict item in list: "- id: foo"
                if current_list is None:
                    current_list = []
                    if current_key is not None:
                        result[current_key] = current_list
                current_item = {}
                k, _, v = item_content.partition(":")
                current_item[k.strip()] = v.strip().strip("'\"")
            else:
                # Scalar list item: "- value"
                if current_list is None:
                    current_list = []
                    if current_key is not None:
                        result[current_key] = current_list
                current_list.append(item_content.strip().strip("'\""))
            continue

        # Nested key under a list item (indent 4)
        if indent == 4 and ":" in stripped and current_item is not None:
            k, _, v = stripped.partition(":")
            current_item[k.strip()] = v.strip().strip("'\"")
            continue

    # Flush last pending item
    if current_item is not None and current_list is not None:
        current_list.append(current_item)

    return result


def load_team_manifests(teams_dir: Path) -> dict[str, dict]:
    """Load all .yaml files from teams_dir, return name -> manifest dict."""
    manifests: dict[str, dict] = {}
    if not teams_dir.is_dir():
        return manifests
    for yaml_file in sorted(teams_dir.glob("*.yaml")):
        data = _parse_yaml(yaml_file)
        name = data.get("name", yaml_file.stem)
        manifests[name] = data
    return manifests


def extract_image_refs(workflow_path: Path) -> list[tuple[str, str, str]]:
    """Extract (node_id, image_value, team_name) from workflow nodes.

    Returns a list of tuples for each node that has an image: field.
    The team_name is extracted from 'sdlc-worker:<team-name>'.
    """
    refs: list[tuple[str, str, str]] = []
    data = _parse_yaml(workflow_path)
    nodes = data.get("nodes", [])
    if not isinstance(nodes, list):
        return refs
    for node in nodes:
        if not isinstance(node, dict):
            continue
        image = node.get("image")
        if not image:
            continue
        node_id = node.get("id", "<unknown>")
        # Parse sdlc-worker:<team-name>
        if ":" in str(image):
            _, _, team_name = str(image).partition(":")
            refs.append((str(node_id), str(image), team_name))
    return refs


def validate(
    workflows_dir: Path,
    teams_dir: Path,
) -> list[str]:
    """Validate all workflow image references against team manifests.

    Returns a list of error strings. Empty list means all valid.
    """
    errors: list[str] = []

    # Load team manifests
    teams = load_team_manifests(teams_dir)

    # Find all workflow YAML files
    if not workflows_dir.is_dir():
        return errors

    for wf_path in sorted(workflows_dir.glob("*.yaml")):
        refs = extract_image_refs(wf_path)
        for node_id, image_value, team_name in refs:
            # sdlc-worker:base is always valid
            if team_name == BASE_IMAGE_TAG:
                continue

            # Check team manifest exists
            if team_name not in teams:
                errors.append(
                    f"{wf_path.name}: node '{node_id}' references image "
                    f"'{image_value}' but no team manifest found for "
                    f"'{team_name}'"
                )
                continue

            # Check team status
            manifest = teams[team_name]
            status = manifest.get("status", "unknown")
            if status not in VALID_STATUSES:
                errors.append(
                    f"{wf_path.name}: node '{node_id}' references team "
                    f"'{team_name}' which has status '{status}' "
                    f"(inactive/decommissioned teams should not be "
                    f"referenced in workflows)"
                )

    return errors


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate workflow image references against team manifests"
    )
    parser.add_argument(
        "--workflows-dir",
        type=Path,
        default=Path(".archon/workflows"),
        help="Directory containing workflow YAML files (default: .archon/workflows)",
    )
    parser.add_argument(
        "--teams-dir",
        type=Path,
        default=Path(".archon/teams"),
        help="Directory containing team manifest YAML files (default: .archon/teams)",
    )
    args = parser.parse_args()

    errors = validate(
        workflows_dir=args.workflows_dir,
        teams_dir=args.teams_dir,
    )

    if errors:
        print(f"Workflow-team validation FAILED ({len(errors)} error(s)):")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("Workflow-team validation passed: all image references valid.")
        sys.exit(0)


if __name__ == "__main__":
    main()
