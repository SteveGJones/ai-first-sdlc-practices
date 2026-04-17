#!/usr/bin/env python3
"""Preprocess workflow YAML for containerised team execution.

Transforms nodes with ``image:`` fields into Archon-native bash nodes
that ``docker run`` team containers.  Nodes without ``image:`` pass
through unchanged.  Archon handles the DAG natively.

Public API
----------
has_image_nodes(workflow) -> bool
transform_node(node, workspace, cred_mount, commands_dir) -> dict
transform_workflow(workflow, workspace, cred_mount, commands_dir) -> dict
preprocess(input_path, output_path, workspace, cred_mount, commands_dir) -> Path
"""

from __future__ import annotations

import copy
import shlex
from pathlib import Path

import yaml

_PRESERVED_FIELDS = {
    "id", "depends_on", "trigger_rule", "when", "timeout", "retry",
}


def has_image_nodes(workflow: dict) -> bool:
    """Return True if any node in the workflow has an ``image:`` field."""
    for node in workflow.get("nodes", []):
        if "image" in node:
            return True
    return False


def _build_docker_run(
    image: str,
    workspace: str,
    cred_mount: str,
    prompt: str,
    env: dict[str, str] | None = None,
) -> str:
    """Build a ``docker run`` command string."""
    parts = ["docker run --rm"]
    parts.append(f'-v "{workspace}:/workspace"')
    parts.append(cred_mount)
    if env:
        for key, val in env.items():
            parts.append(f'-e "{key}={val}"')
    parts.append(image)

    escaped_prompt = prompt.replace("'", "'\\''")
    parts.append("/bin/bash -c '")
    parts.append(
        "cp /home/sdlc/.claude-creds/.credentials.json "
        "/home/sdlc/.claude/.credentials.json 2>/dev/null; "
        "chmod 600 /home/sdlc/.claude/.credentials.json 2>/dev/null; "
        "unset ANTHROPIC_API_KEY; "
        "cd /workspace; "
        "if [ ! -d .git ]; then "
        'git init -q && git config user.email "sdlc@worker" && '
        'git config user.name "SDLC Worker" && '
        "git add -A && git commit -q -m initial 2>/dev/null; "
        "fi; "
    )
    parts.append(
        f"claude --dangerously-skip-permissions -p {shlex.quote(escaped_prompt)}"
    )
    parts.append("'")
    return " ".join(parts)


def _resolve_prompt(node: dict, commands_dir: str) -> str:
    """Resolve the prompt for a node from command file or inline prompt."""
    if "command" in node:
        command_name = node["command"]
        return f"$(cat {commands_dir}/{command_name}.md 2>/dev/null || echo 'Execute: {command_name}')"
    if "prompt" in node:
        return node["prompt"]
    return "No prompt specified."


def transform_node(
    node: dict,
    workspace: str,
    cred_mount: str,
    commands_dir: str,
) -> dict:
    """Transform a single workflow node.

    If the node has ``image:``, returns a bash node with ``docker run``.
    Otherwise returns the node unchanged.
    """
    if "image" not in node:
        return node

    image = node["image"]
    result: dict = {}

    for field in _PRESERVED_FIELDS:
        if field in node:
            result[field] = node[field]

    if "loop" in node:
        loop_config = node["loop"]
        prompt = loop_config.get("prompt", "Continue working.")
        until_signal = loop_config.get("until", "DONE")
        max_iter = loop_config.get("max_iterations", 5)

        docker_cmd = _build_docker_run(
            image=image,
            workspace=workspace,
            cred_mount=cred_mount,
            prompt=prompt,
        )

        result["bash"] = (
            f"for i in $(seq 1 {max_iter}); do\n"
            f"  echo \"Iteration $i/{max_iter}\"\n"
            f"  OUTPUT=$({docker_cmd})\n"
            f"  echo \"$OUTPUT\"\n"
            f"  if echo \"$OUTPUT\" | grep -q \"{until_signal}\"; then\n"
            f"    echo \"LOOP_COMPLETE: signal detected at iteration $i\"\n"
            f"    break\n"
            f"  fi\n"
            f"done"
        )
        return result

    prompt = _resolve_prompt(node, commands_dir)
    docker_cmd = _build_docker_run(
        image=image,
        workspace=workspace,
        cred_mount=cred_mount,
        prompt=prompt,
    )
    result["bash"] = docker_cmd
    return result


def transform_workflow(
    workflow: dict,
    workspace: str,
    cred_mount: str,
    commands_dir: str,
) -> dict:
    """Transform an entire workflow, converting image nodes to bash nodes."""
    result = copy.deepcopy(workflow)
    result["nodes"] = [
        transform_node(node, workspace, cred_mount, commands_dir)
        for node in workflow.get("nodes", [])
    ]
    return result


def preprocess(
    input_path: Path,
    output_path: Path,
    workspace: str,
    cred_mount: str,
    commands_dir: str = ".archon/commands",
) -> Path:
    """Read a workflow YAML, transform image nodes, write the result."""
    with input_path.open() as fh:
        workflow = yaml.safe_load(fh)

    transformed = transform_workflow(workflow, workspace, cred_mount, commands_dir)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as fh:
        yaml.dump(transformed, fh, default_flow_style=False, sort_keys=False)

    return output_path


def main() -> None:
    """CLI entry point — preprocess a workflow YAML."""
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess workflow for containerised execution")
    parser.add_argument("input", type=Path, help="Input workflow YAML")
    parser.add_argument("--output", type=Path, required=True, help="Output path")
    parser.add_argument("--workspace", required=True, help="Host workspace directory")
    parser.add_argument("--cred-mount", required=True, help="Docker -v argument for credentials")
    parser.add_argument("--commands-dir", default=".archon/commands")
    args = parser.parse_args()

    result = preprocess(
        args.input, args.output, args.workspace, args.cred_mount, args.commands_dir,
    )
    print(f"Preprocessed: {result}")


if __name__ == "__main__":
    main()
