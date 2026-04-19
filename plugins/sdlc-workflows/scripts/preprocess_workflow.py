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
import logging
import secrets
import shlex
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_PRESERVED_FIELDS = {
    "id", "depends_on", "trigger_rule", "when", "timeout", "retry",
}

# Resource defaults baked into every generated `docker run` command.
# Override knob lives in the team manifest (future) — v1 is fixed.
_DEFAULT_MEMORY = "4g"
_DEFAULT_CPUS = "2"


def _fresh_heredoc_sentinel() -> str:
    """Return a per-invocation heredoc sentinel.

    Using a random suffix eliminates the ``SDLC_PROMPT_EOF`` collision
    risk in prompt bodies (CR-I-2 / S-M-9).  16 hex chars = 64 bits of
    entropy; collision probability is negligible.
    """
    return f"SDLC_PROMPT_EOF_{secrets.token_hex(8)}"


def _detect_fan_outs(workflow: dict) -> dict[str, list[str]]:
    """Detect fan-out points in the workflow DAG.

    A *fan-out* is any node referenced by two or more other nodes
    via ``depends_on``.  The returned mapping is
    ``{parent_id: [child_id, ...]}`` for each such parent.

    Used by :func:`transform_workflow` to surface a structured warning
    about the shared-workspace contract (see
    ``CLAUDE-CONTEXT-workflows.md -> Parallel Execution Semantics``).
    """
    children: dict[str, list[str]] = {}
    for node in workflow.get("nodes", []):
        node_id = node.get("id")
        for dep in node.get("depends_on", []) or []:
            children.setdefault(dep, []).append(str(node_id))
    return {parent: kids for parent, kids in children.items() if len(kids) >= 2}


def has_image_nodes(workflow: dict) -> bool:
    """Return True if any node in the workflow has an ``image:`` field."""
    node_count = len(workflow.get("nodes", []))
    logger.debug("Checking workflow for image nodes", extra={"node_count": node_count})
    for node in workflow.get("nodes", []):
        if "image" in node:
            return True
    return False


def _build_docker_run(
    image: str,
    workspace: str,
    cred_mount: str,
    prompt_source: str,
    timeout: int | None = None,
    model: str | None = None,
) -> str:
    """Build a ``docker run`` command string.

    *prompt_source* is a shell expression that produces the prompt text.
    For command nodes: ``cat /workspace/.archon/commands/X.md``
    For inline prompts: a heredoc or echo statement.

    If *model* is provided, ``CLAUDE_MODEL`` is passed to the container
    so the entrypoint can invoke Claude with ``--model <model>``.
    """
    # Use the container entrypoint which handles:
    #   - credential setup (from .claude-auth or .claude-creds mount)
    #   - git init
    #   - loop workaround
    #   - CLAUDE_PROMPT execution
    # We write the prompt to a file and set CLAUDE_PROMPT via env var.
    # Every shell-interpolated value is shlex.quote'd so that workspace
    # paths, cred-mount strings, command-file names, image tags, and
    # timeout/model values can contain spaces, quotes, or other shell
    # metacharacters without breaking the generated bash (S-I-6 / CR-I-2
    # / SA-I-1).  shlex.quote leaves simple paths unwrapped and
    # single-quotes anything with metacharacters.
    timeout_env = (
        f" -e {shlex.quote(f'CLAUDE_TIMEOUT={timeout}')}"
        if timeout is not None
        else ""
    )
    model_env = (
        f" -e {shlex.quote(f'CLAUDE_MODEL={model}')}" if model else ""
    )
    workspace_mount = shlex.quote(f"{workspace}:/workspace")
    cred_mount_q = shlex.quote(cred_mount)
    image_q = shlex.quote(image)
    lines = [
        "PROMPT=$(" + prompt_source + ")",
        (
            "docker run --rm"
            " --cap-drop ALL"
            " --security-opt no-new-privileges"
            f" --memory={_DEFAULT_MEMORY} --cpus={_DEFAULT_CPUS}"
            f" -v {workspace_mount}"
            f" -v {cred_mount_q}"
            ' -e "CLAUDE_PROMPT=$PROMPT"'
            f"{timeout_env}"
            f"{model_env}"
            f" {image_q}"
        ),
    ]
    return "\n".join(lines)


def _resolve_prompt_source(node: dict, commands_dir: str) -> str:
    """Return a shell expression that produces the prompt text.

    For command nodes, ``cat`` the command file from the workspace.
    For inline prompts, ``echo`` the text (writing to a heredoc).
    """
    if "command" in node:
        command_name = node["command"]
        # The command file is inside the HOST workspace (mounted later),
        # so we cat from the host path.  shlex.quote protects against
        # spaces/metacharacters in either the commands_dir or the
        # command name.
        path = shlex.quote(f"{commands_dir}/{command_name}.md")
        return f"cat {path}"
    if "prompt" in node:
        # Use a heredoc to avoid quoting issues.  The sentinel is a
        # per-invocation nonce so a prompt body that happens to contain
        # the literal ``SDLC_PROMPT_EOF`` token cannot break generation.
        prompt_text = node["prompt"]
        sentinel = _fresh_heredoc_sentinel()
        return f"cat <<'{sentinel}'\n{prompt_text}\n{sentinel}"
    return "echo 'No prompt specified.'"


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
    logger.info(
        "Transforming image node to bash docker-run",
        extra={"node_id": node.get("id"), "image": image},
    )
    result: dict = {}

    for field in _PRESERVED_FIELDS:
        if field in node:
            result[field] = node[field]

    if "loop" in node:
        loop_config = node["loop"]
        prompt = loop_config.get("prompt", "Continue working.")
        until_signal = loop_config.get("until", "DONE")
        max_iter = loop_config.get("max_iterations", 5)

        sentinel = _fresh_heredoc_sentinel()
        prompt_source = f"cat <<'{sentinel}'\n{prompt}\n{sentinel}"
        docker_cmd = _build_docker_run(
            image=image,
            workspace=workspace,
            cred_mount=cred_mount,
            prompt_source=prompt_source,
            timeout=node.get("timeout"),
            model=node.get("model"),
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

    prompt_source = _resolve_prompt_source(node, commands_dir)
    docker_cmd = _build_docker_run(
        image=image,
        workspace=workspace,
        cred_mount=cred_mount,
        prompt_source=prompt_source,
        timeout=node.get("timeout"),
        model=node.get("model"),
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
    node_count = len(workflow.get("nodes", []))
    logger.info(
        "Transforming workflow",
        extra={"node_count": node_count, "workspace": workspace},
    )
    fan_outs = _detect_fan_outs(workflow)
    if fan_outs:
        logger.warning(
            "Workflow contains parallel fan-out points — "
            "branches share the mounted workspace (last writer wins). "
            "See CLAUDE-CONTEXT-workflows.md -> Parallel Execution Semantics.",
            extra={"fan_out_points": fan_outs},
        )
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
    logger.info(
        "Preprocessing workflow",
        extra={"input": str(input_path), "output": str(output_path)},
    )
    with input_path.open() as fh:
        workflow = yaml.safe_load(fh)

    transformed = transform_workflow(workflow, workspace, cred_mount, commands_dir)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as fh:
        yaml.dump(transformed, fh, default_flow_style=False, sort_keys=False)

    logger.info("Preprocess complete", extra={"output": str(output_path)})
    return output_path


def main() -> None:
    """CLI entry point — preprocess a workflow YAML."""
    import argparse

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    logger.info("preprocess_workflow CLI start")

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
