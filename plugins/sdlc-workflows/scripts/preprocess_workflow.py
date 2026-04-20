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
import re
import secrets
import shlex
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_PRESERVED_FIELDS = {
    "id", "depends_on", "trigger_rule", "when", "timeout", "retry", "budget",
}

# Patterns that indicate a command brief writes to the shared workspace
# git index from a parallel branch — the single-writer hazard surfaced
# during Phase A bring-up (archon fork-a + fork-b racing on
# /workspace/.git/index.lock).  Parallel branches MUST write to
# per-node subdirectories and let a downstream fan-in node produce the
# single commit.  See CLAUDE-CONTEXT-workflows.md -> Parallel Execution
# Semantics -> Per-node subdirectory pattern.
_GIT_WRITE_PATTERNS = (
    re.compile(r"\bgit\s+commit\b"),
    re.compile(r"\bgit\s+add\b"),
    re.compile(r"\bgit\s+push\b"),
)

# Image-tag allowlist (U-1).  Only images matching this prefix may be
# used in workflow nodes.  A malicious YAML with ``image: evil.com/x``
# would otherwise become ``docker run evil.com/x`` with credentials
# mounted and the user's source tree at /workspace.
_ALLOWED_IMAGE_PREFIX = "sdlc-worker:"


class UnsafeImageError(ValueError):
    """Raised when a workflow node references an image outside the allowlist."""

    def __init__(self, image: str, node_id: str | None = None) -> None:
        self.image = image
        self.node_id = node_id
        loc = f" (node {node_id!r})" if node_id else ""
        super().__init__(
            f"Image {image!r}{loc} is not in the allowlist. "
            f"Only images matching the prefix '{_ALLOWED_IMAGE_PREFIX}' "
            f"are permitted (e.g. sdlc-worker:base, sdlc-worker:dev-team). "
            f"Build a team image with /sdlc-workflows:deploy-team."
        )


def _validate_image_tag(image: str, node_id: str | None = None) -> None:
    """Raise :class:`UnsafeImageError` if *image* is not in the allowlist."""
    if not image.startswith(_ALLOWED_IMAGE_PREFIX):
        raise UnsafeImageError(image, node_id)

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


def _collect_parallel_branch_ids(workflow: dict) -> set[str]:
    """Return the set of node ids that run as parallel branches.

    A node is a parallel branch if it shares a fan-out parent with at
    least one sibling.  These nodes all run concurrently against the
    same mounted /workspace, so writes to the shared git index race.
    """
    fan_outs = _detect_fan_outs(workflow)
    parallel: set[str] = set()
    for children in fan_outs.values():
        parallel.update(children)
    return parallel


def _brief_text_for_node(
    node: dict,
    commands_dir: str,
    commands_root: Path | None,
) -> str | None:
    """Return the prompt text a node will execute, or None if unknown.

    Inline ``prompt:`` and ``loop.prompt`` values are returned directly.
    For ``command:`` nodes, the matching file under *commands_root* is
    read.  If the file cannot be located we return None so the guardrail
    can surface a soft warning instead of crashing preprocessing —
    workflows are authored outside our tree and the file may live at a
    runtime-only path.
    """
    if "prompt" in node:
        return str(node["prompt"])
    if "loop" in node and isinstance(node["loop"], dict):
        loop_prompt = node["loop"].get("prompt")
        if loop_prompt:
            return str(loop_prompt)
        # Multi-stage loop: concatenate every stage's inline prompt and
        # every locatable stage command brief.  The G4 check then sees
        # git-write verbs from ANY stage, which is what we want —
        # stages run sequentially inside the loop node, but the loop
        # node itself may be a parallel branch at the DAG level, and a
        # git-write in any of its stages is still a race.
        stages = node["loop"].get("stages")
        if isinstance(stages, list):
            parts: list[str] = []
            for stage in stages:
                if not isinstance(stage, dict):
                    continue
                if "prompt" in stage:
                    parts.append(str(stage["prompt"]))
                elif "command" in stage and commands_root is not None:
                    cand = commands_root / f"{stage['command']}.md"
                    if cand.is_file():
                        try:
                            parts.append(cand.read_text(encoding="utf-8"))
                        except OSError:
                            continue
            if parts:
                return "\n".join(parts)
    if "command" in node and commands_root is not None:
        candidate = commands_root / f"{node['command']}.md"
        if candidate.is_file():
            try:
                return candidate.read_text(encoding="utf-8")
            except OSError:
                return None
    return None


def _scan_parallel_git_writes(
    workflow: dict,
    commands_dir: str,
    commands_root: Path | None,
) -> list[tuple[str, str]]:
    """Return [(node_id, matched_pattern), ...] for parallel git writers.

    Only nodes that (a) run as a parallel branch AND (b) have a brief
    whose text contains a git-write verb are reported.  Fan-in nodes
    (``trigger_rule: one_success`` or similar with multiple
    ``depends_on`` but no siblings) are not parallel branches and may
    commit freely — that is the documented pattern.
    """
    parallel_ids = _collect_parallel_branch_ids(workflow)
    if not parallel_ids:
        return []

    offenders: list[tuple[str, str]] = []
    for node in workflow.get("nodes", []):
        node_id = str(node.get("id", ""))
        if node_id not in parallel_ids:
            continue
        text = _brief_text_for_node(node, commands_dir, commands_root)
        if text is None:
            continue
        for pattern in _GIT_WRITE_PATTERNS:
            match = pattern.search(text)
            if match:
                offenders.append((node_id, match.group(0)))
                break
    return offenders


class ParallelGitWriteError(ValueError):
    """Raised when a parallel branch attempts a git-index write.

    Carries the offending (node_id, matched_token) pairs so callers
    (CI, tests) can surface structured diagnostics rather than parsing
    the message string.
    """

    def __init__(self, offenders: list[tuple[str, str]]) -> None:
        self.offenders = offenders
        details = "\n".join(
            f"  - node '{nid}' contains '{tok}'" for nid, tok in offenders
        )
        super().__init__(
            "Parallel branches must not write to /workspace/.git — "
            "concurrent commits race on .git/index.lock and silently "
            "drop work.  Offending nodes:\n"
            f"{details}\n"
            "Fix: have each parallel branch write its output to a "
            "per-node subdirectory (e.g. /workspace/reports/<node-id>/) "
            "without committing, then let the downstream fan-in node "
            "produce the single commit.  See CLAUDE-CONTEXT-workflows.md "
            "-> Parallel Execution Semantics."
        )


def has_image_nodes(workflow: dict) -> bool:
    """Return True if any node in the workflow needs preprocessing.

    A node needs preprocessing if it has a top-level ``image:`` field
    (single-image node, with or without single-image ``loop:``) **or** if
    it has ``loop.stages:`` (multi-stage loop — images live on each
    stage, not on the node itself).
    """
    node_count = len(workflow.get("nodes", []))
    logger.debug("Checking workflow for image nodes", extra={"node_count": node_count})
    for node in workflow.get("nodes", []):
        if "image" in node:
            return True
        loop_cfg = node.get("loop")
        if isinstance(loop_cfg, dict) and "stages" in loop_cfg:
            return True
    return False


def _build_docker_run(
    image: str,
    workspace: str,
    cred_mount: str,
    prompt_source: str,
    timeout: int | None = None,
    model: str | None = None,
    budget: float | int | None = None,
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
    # Tiered termination: CLAUDE_TIMEOUT (inner, seconds) must be LOWER
    # than Archon's bash node timeout (outer, milliseconds) to create a
    # "save window".  Claude gets SIGTERM from the inner timeout and has
    # ~60s to write partial output before Archon kills the container.
    # Floor: never below 60s (always give Claude time to write something).
    _SAVE_WINDOW_SECONDS = 60
    _FLOOR_SECONDS = 60
    if timeout is not None:
        inner_seconds = max(_FLOOR_SECONDS, int(timeout / 1000) - _SAVE_WINDOW_SECONDS)
        timeout_env = f" -e {shlex.quote(f'CLAUDE_TIMEOUT={inner_seconds}')}"
    else:
        timeout_env = ""
    model_env = (
        f" -e {shlex.quote(f'CLAUDE_MODEL={model}')}" if model else ""
    )
    # Tier 1 spiral detection: cost-based cap.  If the model loops and
    # burns tokens without progress, the budget kills it before the time
    # cap fires.  Passed as env var; entrypoint forwards to --max-budget-usd.
    budget_env = (
        f" -e {shlex.quote(f'CLAUDE_MAX_BUDGET={budget}')}"
        if budget is not None
        else ""
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
            f"{budget_env}"
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


def _transform_multistage_loop(
    node: dict,
    workspace: str,
    cred_mount: str,
    commands_dir: str,
) -> dict:
    """Transform a node whose ``loop:`` carries a ``stages:`` list.

    Each stage has its own ``image:`` and ``command:`` / ``prompt:``.
    Stages run sequentially inside one iteration; if any stage's
    output contains the ``until:`` signal, the entire loop terminates
    early.  This is the natural shape for multi-team cycles like
    ``designer → developer → reviewer → designer …`` — Archon still
    sees one DAG node, state flows through the shared workspace,
    and signal detection is our own ``grep`` (same pattern as the
    single-image loop, which already sidesteps upstream Archon
    loop-completion bugs).
    """
    loop_config = node["loop"]
    stages = loop_config.get("stages")
    if not isinstance(stages, list) or not stages:
        raise ValueError(
            f"loop.stages must be a non-empty list (node {node.get('id')!r})"
        )

    until_signal = str(loop_config.get("until", "DONE"))
    try:
        max_iter = int(loop_config.get("max_iterations", 5))
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"loop.max_iterations must be an integer (node {node.get('id')!r})"
        ) from exc
    if max_iter < 1:
        raise ValueError(
            f"loop.max_iterations must be >= 1 (node {node.get('id')!r})"
        )

    result: dict = {}
    for field in _PRESERVED_FIELDS:
        if field in node:
            result[field] = node[field]

    logger.info(
        "Transforming multi-stage loop node",
        extra={
            "node_id": node.get("id"),
            "stage_count": len(stages),
            "max_iterations": max_iter,
        },
    )

    signal_q = shlex.quote(until_signal)
    bash_lines: list[str] = [f"for i in $(seq 1 {max_iter}); do"]
    bash_lines.append(f'  echo "=== Iteration $i/{max_iter} ==="')

    for idx, stage in enumerate(stages):
        if not isinstance(stage, dict):
            raise ValueError(
                f"loop.stages[{idx}] in node {node.get('id')!r} must be a mapping"
            )
        if "image" not in stage:
            raise ValueError(
                f"loop.stages[{idx}] in node {node.get('id')!r} "
                "missing required field: image"
            )
        stage_id = str(stage.get("id", f"s{idx + 1}"))
        stage_image = stage["image"]
        _validate_image_tag(stage_image, f"{node.get('id')}.stages[{idx}]")
        stage_prompt_source = _resolve_prompt_source(stage, commands_dir)
        docker_cmd = _build_docker_run(
            image=stage_image,
            workspace=workspace,
            cred_mount=cred_mount,
            prompt_source=stage_prompt_source,
            timeout=stage.get("timeout") or node.get("timeout"),
            model=stage.get("model") or node.get("model"),
            budget=stage.get("budget") or node.get("budget"),
        )
        var_name = f"STAGE_{idx + 1}_OUT"
        stage_label = shlex.quote(f"--- stage {stage_id} ({stage_image}) ---")
        bash_lines.append(f"  echo {stage_label}")
        # Capture each stage's stdout so we can scan for the until: signal.
        # The PROMPT=... assignment in docker_cmd stays local to the $()
        # subshell by virtue of running inside it.
        bash_lines.append(f"  {var_name}=$(")
        for sub in docker_cmd.split("\n"):
            bash_lines.append(f"    {sub}")
        bash_lines.append("  )")
        bash_lines.append(f'  echo "${var_name}"')
        bash_lines.append(f'  if echo "${var_name}" | grep -q {signal_q}; then')
        bash_lines.append(
            f'    echo "LOOP_COMPLETE: signal detected in stage '
            f'{stage_id} of iteration $i"'
        )
        bash_lines.append("    break")
        bash_lines.append("  fi")

    bash_lines.append("done")
    result["bash"] = "\n".join(bash_lines)
    return result


def transform_node(
    node: dict,
    workspace: str,
    cred_mount: str,
    commands_dir: str,
) -> dict:
    """Transform a single workflow node.

    Dispatches to a multi-stage loop transformer when the node carries
    ``loop.stages:``; otherwise transforms single-image nodes (with or
    without single-image ``loop:``) into a bash ``docker run``.  Nodes
    with neither ``image:`` nor ``loop.stages:`` pass through unchanged.
    """
    loop_cfg = node.get("loop")
    if isinstance(loop_cfg, dict) and "stages" in loop_cfg:
        return _transform_multistage_loop(
            node, workspace, cred_mount, commands_dir
        )

    if "image" not in node:
        return node

    image = node["image"]
    _validate_image_tag(image, node.get("id"))
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
            budget=node.get("budget"),
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
        budget=node.get("budget"),
    )
    result["bash"] = docker_cmd
    return result


def transform_workflow(
    workflow: dict,
    workspace: str,
    cred_mount: str,
    commands_dir: str,
    commands_root: Path | None = None,
) -> dict:
    """Transform an entire workflow, converting image nodes to bash nodes.

    If *commands_root* is provided, parallel-branch command briefs are
    scanned for git-index writes (``git commit``/``git add``/
    ``git push``).  Any hits raise :class:`ParallelGitWriteError`
    before any docker-run bash is emitted — the author must switch the
    branch to the per-node-subdirectory pattern.  Without
    *commands_root* the scan still runs over inline ``prompt:`` and
    ``loop.prompt`` text, but command-file nodes are skipped silently
    because the files are not reachable from preprocessing context.
    """
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
    offenders = _scan_parallel_git_writes(workflow, commands_dir, commands_root)
    if offenders:
        logger.error(
            "Refusing to preprocess workflow with parallel git-index writers",
            extra={"offenders": offenders},
        )
        raise ParallelGitWriteError(offenders)
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
    """Read a workflow YAML, transform image nodes, write the result.

    The guardrail resolves command briefs from
    ``<workspace>/<commands_dir>`` so parallel branches whose briefs
    contain ``git commit``/``git add``/``git push`` are rejected with
    a structured :class:`ParallelGitWriteError` before any bash is
    generated.
    """
    logger.info(
        "Preprocessing workflow",
        extra={"input": str(input_path), "output": str(output_path)},
    )
    with input_path.open() as fh:
        workflow = yaml.safe_load(fh)

    commands_root = Path(workspace) / commands_dir
    transformed = transform_workflow(
        workflow,
        workspace,
        cred_mount,
        commands_dir,
        commands_root=commands_root,
    )

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

    try:
        result = preprocess(
            args.input, args.output, args.workspace, args.cred_mount, args.commands_dir,
        )
    except ParallelGitWriteError as exc:
        # Exit code 3 distinguishes guardrail rejection from generic
        # argparse (2) or OS (1) errors so CI can gate on it.
        print(f"preprocess_workflow: {exc}", file=__import__("sys").stderr)
        raise SystemExit(3) from exc
    print(f"Preprocessed: {result}")


if __name__ == "__main__":
    main()
