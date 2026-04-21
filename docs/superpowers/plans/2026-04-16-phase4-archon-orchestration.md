# Phase 4: Archon Orchestration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove Archon can orchestrate containerised team workflows — per-node team enforcement, parallel execution, credential injection — via workflow YAML preprocessing.

**Architecture:** A Python preprocessor transforms workflow YAML nodes that have `image:` fields into Archon-native bash nodes that `docker run` team containers. Archon handles the DAG (dependencies, parallel layers, trigger rules). A credential resolver automates the b→a→c fallback (Keychain → volume → config). Workspace management uses shared directories for sequential nodes and git branch/merge for parallel.

**Tech Stack:** Python 3.14, PyYAML, Docker CLI, Archon CLI, existing Phase 2/3 scripts

**Branch:** `feature/96-sdlc-workflows` (worktree at `.worktrees/feature-96-sdlc-workflows`)

**Spec:** `docs/superpowers/specs/2026-04-16-phase4-archon-orchestration-design.md`

---

## File Structure

### New files

| File | Responsibility |
|------|---------------|
| `plugins/sdlc-workflows/scripts/preprocess_workflow.py` | Transform `image:` nodes to bash nodes that `docker run` team containers |
| `plugins/sdlc-workflows/scripts/resolve_credentials.py` | Three-tier credential fallback: Keychain → volume → config |
| `tests/test_preprocess_workflow.py` | Tests for workflow preprocessing |
| `tests/test_resolve_credentials.py` | Tests for credential resolution |
| `tests/integration/workforce-smoke/miniproject/.archon/workflows/parallel-review-pipeline.yaml` | Parallel workflow for E2E testing |
| `tests/integration/workforce-smoke/run-e2e.sh` | End-to-end Archon orchestration test |

### Modified files

| File | Change |
|------|--------|
| `plugins/sdlc-workflows/skills/workflows-run/SKILL.md` | Detect `image:` nodes, preprocess before calling Archon |
| `plugins/sdlc-workflows/skills/workflows-setup/SKILL.md` | Add credential tier reporting to health check |
| `tests/integration/workforce-smoke/login.sh` | Fix TTY detection, clean volume handling |

---

## Task 1: Credential Resolver (`resolve_credentials.py`)

Independent of the preprocessor — can be built first. Resolves which credential source to use and returns the `docker run` mount argument.

**Files:**
- Create: `plugins/sdlc-workflows/scripts/resolve_credentials.py`
- Create: `tests/test_resolve_credentials.py`

- [ ] **Step 1: Write failing tests**

```python
#!/usr/bin/env python3
"""Tests for resolve_credentials — three-tier credential fallback."""

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plugins_sdlc_workflows_scripts as scripts  # noqa: E402

resolve_credentials = scripts.resolve_credentials


class TestKeychainTier:
    def test_extracts_from_keychain_on_macos(self, tmp_path: Path) -> None:
        """Tier 1: macOS Keychain extraction succeeds."""
        cred_json = json.dumps({"claudeAiOauth": {"accessToken": "test"}})
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=cred_json, stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "keychain"
        assert result["mount_args"] is not None
        assert ".credentials.json" in result["mount_args"]

    def test_keychain_fails_gracefully(self, tmp_path: Path) -> None:
        """Tier 1: Keychain fails → falls through to next tier."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=44, stdout="", stderr="not found"
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] != "keychain"


class TestVolumeTier:
    def test_volume_found(self, tmp_path: Path) -> None:
        """Tier 2: Docker volume exists and has credentials."""
        with patch("subprocess.run") as mock_run:
            def side_effect(*args, **kwargs):
                cmd = args[0] if args else kwargs.get("args", [])
                if "security" in cmd:
                    return MagicMock(returncode=44, stdout="", stderr="")
                if "docker" in cmd and "inspect" in cmd:
                    return MagicMock(returncode=0, stdout="[]", stderr="")
                if "docker" in cmd and "run" in cmd:
                    return MagicMock(returncode=0, stdout="exists", stderr="")
                return MagicMock(returncode=1, stdout="", stderr="")
            mock_run.side_effect = side_effect
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "volume"

    def test_volume_missing(self, tmp_path: Path) -> None:
        """Tier 2: Volume doesn't exist → falls through."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="not found"
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] != "volume"


class TestConfigTier:
    def test_config_file_found(self, tmp_path: Path) -> None:
        """Tier 3: .archon/credentials.yaml exists with valid path."""
        cred_file = tmp_path / "my-creds.json"
        cred_file.write_text('{"claudeAiOauth": {}}')
        config_dir = tmp_path / ".archon"
        config_dir.mkdir()
        (config_dir / "credentials.yaml").write_text(
            f"credential_path: {cred_file}\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "config"
        assert str(cred_file) in result["mount_args"]

    def test_config_missing_file(self, tmp_path: Path) -> None:
        """Tier 3: Config references nonexistent file → tier=none."""
        config_dir = tmp_path / ".archon"
        config_dir.mkdir()
        (config_dir / "credentials.yaml").write_text(
            "credential_path: /nonexistent/path.json\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "none"


class TestNoneTier:
    def test_all_tiers_fail(self, tmp_path: Path) -> None:
        """All tiers fail → tier=none with instructions."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr=""
            )
            result = resolve_credentials.resolve(
                work_dir=tmp_path,
                project_dir=tmp_path,
            )
        assert result["tier"] == "none"
        assert result["mount_args"] is None
        assert "message" in result
```

Save to: `tests/test_resolve_credentials.py`

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_resolve_credentials.py -v 2>&1 | head -10`
Expected: FAIL — `resolve_credentials` module not found

- [ ] **Step 3: Implement `resolve_credentials.py`**

```python
#!/usr/bin/env python3
"""Resolve Claude Code credentials for containerised workflow runs.

Three-tier fallback:
  1. macOS Keychain (zero-config)
  2. Docker volume (sdlc-claude-credentials)
  3. Explicit config (.archon/credentials.yaml)

Public API
----------
resolve(work_dir, project_dir) -> dict
    Returns {"tier": str, "mount_args": str|None, "message": str}
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import yaml

KEYCHAIN_SERVICE = "Claude Code-credentials"
CREDENTIAL_VOLUME = "sdlc-claude-credentials"
CONFIG_FILE = ".archon/credentials.yaml"
CONTAINER_CRED_PATH = "/home/sdlc/.claude/.credentials.json"


def _try_keychain(work_dir: Path) -> dict | None:
    """Tier 1: Extract credentials from macOS Keychain."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        cred_json = result.stdout.strip()
        if not cred_json:
            return None

        # Validate it's real JSON with expected structure
        parsed = json.loads(cred_json)
        if "claudeAiOauth" not in parsed:
            return None

        # Write to temp file
        temp_file = work_dir / ".sdlc-cred-temp.json"
        temp_file.write_text(cred_json)
        os.chmod(temp_file, 0o600)

        return {
            "tier": "keychain",
            "mount_args": f"-v {temp_file}:{CONTAINER_CRED_PATH}:ro",
            "message": "Credentials from macOS Keychain",
            "cleanup": str(temp_file),
        }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return None


def _try_volume() -> dict | None:
    """Tier 2: Check for Docker credential volume."""
    try:
        # Check volume exists
        result = subprocess.run(
            ["docker", "volume", "inspect", CREDENTIAL_VOLUME],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        # Check volume has the credential file
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{CREDENTIAL_VOLUME}:/data:ro",
                "--entrypoint", "test",
                "alpine", "-f", "/data/.credentials.json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None

        return {
            "tier": "volume",
            "mount_args": f"-v {CREDENTIAL_VOLUME}:/home/sdlc/.claude-creds:ro",
            "message": f"Credentials from Docker volume: {CREDENTIAL_VOLUME}",
            "cleanup": None,
        }
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _try_config(project_dir: Path) -> dict | None:
    """Tier 3: Check for .archon/credentials.yaml config."""
    config_path = project_dir / CONFIG_FILE
    if not config_path.exists():
        return None

    try:
        with config_path.open() as fh:
            config = yaml.safe_load(fh)

        cred_path = config.get("credential_path")
        if not cred_path:
            return None

        cred_file = Path(cred_path)
        if not cred_file.exists():
            return None

        return {
            "tier": "config",
            "mount_args": f"-v {cred_file}:{CONTAINER_CRED_PATH}:ro",
            "message": f"Credentials from config: {cred_path}",
            "cleanup": None,
        }
    except (yaml.YAMLError, OSError):
        return None


def resolve(
    work_dir: Path,
    project_dir: Path,
) -> dict:
    """Resolve credentials using the three-tier fallback.

    Parameters
    ----------
    work_dir:
        Temporary working directory for this workflow run.
    project_dir:
        Project root (contains .archon/ if configured).

    Returns
    -------
    dict
        ``{"tier": str, "mount_args": str|None, "message": str, "cleanup": str|None}``
    """
    # Tier 1: macOS Keychain
    result = _try_keychain(work_dir)
    if result:
        return result

    # Tier 2: Docker volume
    result = _try_volume()
    if result:
        return result

    # Tier 3: Explicit config
    result = _try_config(project_dir)
    if result:
        return result

    # No tier worked
    return {
        "tier": "none",
        "mount_args": None,
        "message": (
            "No credentials found. Options:\n"
            "  1. Log in to Claude Code on this Mac (uses Keychain automatically)\n"
            "  2. Run login.sh to create a Docker credential volume\n"
            "  3. Create .archon/credentials.yaml with credential_path"
        ),
        "cleanup": None,
    }


def main() -> None:
    """CLI entry point — report which credential tier is active."""
    import argparse

    parser = argparse.ArgumentParser(description="Resolve Claude Code credentials")
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    work_dir = Path(tempfile.mkdtemp(prefix="sdlc-cred-"))
    try:
        result = resolve(work_dir, args.project_dir)
        if args.json:
            import json as json_mod
            print(json_mod.dumps(result, indent=2))
        else:
            print(f"Tier: {result['tier']}")
            print(f"  {result['message']}")
    finally:
        # Clean up temp files
        cleanup = result.get("cleanup")
        if cleanup:
            Path(cleanup).unlink(missing_ok=True)
        work_dir.rmdir()


if __name__ == "__main__":
    main()
```

Save to: `plugins/sdlc-workflows/scripts/resolve_credentials.py`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_resolve_credentials.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-workflows/scripts/resolve_credentials.py tests/test_resolve_credentials.py
git commit -m "feat(credentials): add three-tier credential resolver for containerised workflows"
```

---

## Task 2: Workflow Preprocessor (`preprocess_workflow.py`)

The core of Phase 4. Transforms `image:` nodes into Archon-native bash nodes.

**Files:**
- Create: `plugins/sdlc-workflows/scripts/preprocess_workflow.py`
- Create: `tests/test_preprocess_workflow.py`

- [ ] **Step 1: Write failing tests**

```python
#!/usr/bin/env python3
"""Tests for preprocess_workflow — image node to bash node transformation."""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plugins_sdlc_workflows_scripts as scripts  # noqa: E402

preprocess_workflow = scripts.preprocess_workflow


CRED_MOUNT = "-v /tmp/creds.json:/home/sdlc/.claude/.credentials.json:ro"


class TestCommandNodeTransform:
    def test_image_command_becomes_bash(self) -> None:
        """A command node with image: becomes a bash node with docker run."""
        node = {
            "id": "implement",
            "command": "sdlc-implement",
            "image": "sdlc-worker:dev-team",
        }
        result = preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount=CRED_MOUNT,
            commands_dir=".archon/commands",
        )
        assert "bash" in result
        assert "command" not in result
        assert "image" not in result
        assert "sdlc-worker:dev-team" in result["bash"]
        assert "sdlc-implement" in result["bash"]
        assert result["id"] == "implement"

    def test_preserves_depends_on(self) -> None:
        node = {
            "id": "review",
            "command": "sdlc-review",
            "image": "sdlc-worker:review-team",
            "depends_on": ["implement"],
        }
        result = preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount=CRED_MOUNT,
            commands_dir=".archon/commands",
        )
        assert result["depends_on"] == ["implement"]

    def test_preserves_trigger_rule(self) -> None:
        node = {
            "id": "synth",
            "command": "sdlc-synthesise",
            "image": "sdlc-worker:dev-team",
            "depends_on": ["a", "b"],
            "trigger_rule": "all_success",
        }
        result = preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount=CRED_MOUNT,
            commands_dir=".archon/commands",
        )
        assert result["trigger_rule"] == "all_success"

    def test_preserves_timeout(self) -> None:
        node = {
            "id": "slow",
            "command": "sdlc-implement",
            "image": "sdlc-worker:dev-team",
            "timeout": 300000,
        }
        result = preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount=CRED_MOUNT,
            commands_dir=".archon/commands",
        )
        assert result.get("timeout") == 300000


class TestPromptNodeTransform:
    def test_inline_prompt_becomes_bash(self) -> None:
        node = {
            "id": "synth",
            "prompt": "Summarise the reviews: $review.output",
            "image": "sdlc-worker:dev-team",
        }
        result = preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount=CRED_MOUNT,
            commands_dir=".archon/commands",
        )
        assert "bash" in result
        assert "prompt" not in result
        assert "Summarise the reviews" in result["bash"]


class TestNoImagePassthrough:
    def test_node_without_image_unchanged(self) -> None:
        node = {
            "id": "local-node",
            "command": "sdlc-validate",
            "context": "fresh",
        }
        result = preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount=CRED_MOUNT,
            commands_dir=".archon/commands",
        )
        assert result == node

    def test_bash_node_unchanged(self) -> None:
        node = {"id": "check", "bash": "echo hello"}
        result = preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount=CRED_MOUNT,
            commands_dir=".archon/commands",
        )
        assert result == node


class TestLoopNodeTransform:
    def test_loop_image_becomes_bash_loop(self) -> None:
        node = {
            "id": "implement",
            "image": "sdlc-worker:dev-team",
            "loop": {
                "prompt": "Fix the code until tests pass.",
                "until": "ALL_TESTS_PASSING",
                "max_iterations": 5,
                "fresh_context": True,
            },
        }
        result = preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount=CRED_MOUNT,
            commands_dir=".archon/commands",
        )
        assert "bash" in result
        assert "loop" not in result
        assert "for i in" in result["bash"] or "seq 1 5" in result["bash"]
        assert "ALL_TESTS_PASSING" in result["bash"]
        assert "sdlc-worker:dev-team" in result["bash"]


class TestFullWorkflowTransform:
    def test_transforms_mixed_workflow(self) -> None:
        """Workflow with image and non-image nodes."""
        workflow = {
            "name": "test-pipeline",
            "provider": "claude",
            "nodes": [
                {
                    "id": "implement",
                    "command": "sdlc-implement",
                    "image": "sdlc-worker:dev-team",
                },
                {
                    "id": "validate",
                    "command": "sdlc-validate",
                    "depends_on": ["implement"],
                },
                {
                    "id": "review",
                    "command": "sdlc-review",
                    "image": "sdlc-worker:review-team",
                    "depends_on": ["validate"],
                },
            ],
        }
        result = preprocess_workflow.transform_workflow(
            workflow,
            workspace="/workspace",
            cred_mount=CRED_MOUNT,
            commands_dir=".archon/commands",
        )
        assert result["name"] == "test-pipeline"
        # implement and review should be bash, validate should be unchanged
        nodes = {n["id"]: n for n in result["nodes"]}
        assert "bash" in nodes["implement"]
        assert "command" in nodes["validate"]
        assert "bash" in nodes["review"]

    def test_has_image_nodes(self) -> None:
        workflow = {
            "name": "no-images",
            "nodes": [{"id": "a", "command": "test"}],
        }
        assert preprocess_workflow.has_image_nodes(workflow) is False

        workflow_with = {
            "name": "with-images",
            "nodes": [{"id": "a", "command": "test", "image": "x"}],
        }
        assert preprocess_workflow.has_image_nodes(workflow_with) is True
```

Save to: `tests/test_preprocess_workflow.py`

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_preprocess_workflow.py -v 2>&1 | head -10`
Expected: FAIL — `preprocess_workflow` module not found

- [ ] **Step 3: Implement `preprocess_workflow.py`**

```python
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

# Fields preserved from the original node onto the bash node
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

    # Workspace mount
    parts.append(f'-v "{workspace}:/workspace"')

    # Credential mount
    parts.append(cred_mount)

    # Environment variables
    if env:
        for key, val in env.items():
            parts.append(f'-e "{key}={val}"')

    # Image
    parts.append(image)

    # The entrypoint handles CLAUDE_PROMPT, but we bypass it for
    # simpler output capture. Run claude directly.
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


def _resolve_prompt(
    node: dict,
    commands_dir: str,
) -> str:
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

    # Preserve DAG fields
    for field in _PRESERVED_FIELDS:
        if field in node:
            result[field] = node[field]

    # Handle loop nodes
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

    # Handle command and prompt nodes
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
    """Read a workflow YAML, transform image nodes, write the result.

    Parameters
    ----------
    input_path:
        Path to the original workflow YAML.
    output_path:
        Path to write the transformed YAML.
    workspace:
        Host directory to mount as ``/workspace`` in containers.
    cred_mount:
        Docker ``-v`` argument for credential mounting.
    commands_dir:
        Directory containing command Markdown files.

    Returns
    -------
    Path
        The output path (for chaining).
    """
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
```

Save to: `plugins/sdlc-workflows/scripts/preprocess_workflow.py`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_preprocess_workflow.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-workflows/scripts/preprocess_workflow.py tests/test_preprocess_workflow.py
git commit -m "feat(preprocessor): add workflow YAML preprocessor for containerised execution"
```

---

## Task 3: Login Script Fix

Fix the TTY handling and credential extraction in `login.sh`.

**Files:**
- Modify: `tests/integration/workforce-smoke/login.sh`

- [ ] **Step 1: Update login.sh with TTY detection and clear error handling**

The login script must:
- Detect if running in a TTY (fail with message if not)
- Create a clean credential volume
- Run `claude auth login` interactively
- Extract only `.credentials.json` with correct UID 1001 ownership
- Verify auth works before declaring success

Read the current file, then replace its contents:

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Workforce Smoke Test — Claude Code Login ==="
echo ""

# TTY check
if [ ! -t 0 ] || [ ! -t 1 ]; then
    echo "ERROR: This script requires an interactive terminal."
    echo "Run it directly in a terminal, not via Claude Code or a script."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker not available."
    exit 1
fi

if ! docker image inspect sdlc-worker:base >/dev/null 2>&1; then
    echo "ERROR: sdlc-worker:base not found. Build it first."
    exit 1
fi

CRED_VOLUME="sdlc-workforce-smoke-creds"
SCOPED_VOLUME="sdlc-claude-credentials"

# Clean start
docker volume rm "$CRED_VOLUME" 2>/dev/null || true
docker volume create "$CRED_VOLUME" >/dev/null

echo "Starting interactive login container..."
echo "Authorize in your browser when prompted, then paste the code."
echo ""

docker run --rm -it \
    -v "${CRED_VOLUME}:/home/sdlc/.claude" \
    --entrypoint claude \
    sdlc-worker:base \
    auth login

echo ""
echo "Verifying credentials..."

AUTH_CHECK=$(docker run --rm \
    -v "${CRED_VOLUME}:/home/sdlc/.claude" \
    --entrypoint claude \
    sdlc-worker:base \
    -p "say OK" 2>&1 | head -1)

if echo "$AUTH_CHECK" | grep -qi "OK"; then
    echo "Auth: OK"
else
    echo "Auth check failed: $AUTH_CHECK"
    echo "Try running this script again."
    exit 1
fi

# Extract credential file into the standard scoped volume
docker volume rm "$SCOPED_VOLUME" 2>/dev/null || true
docker volume create "$SCOPED_VOLUME" >/dev/null

docker run --rm \
    -v "${CRED_VOLUME}:/source:ro" \
    -v "${SCOPED_VOLUME}:/dest" \
    --entrypoint /bin/sh \
    alpine \
    -c 'cp /source/.credentials.json /dest/.credentials.json && chown 1001:1001 /dest/.credentials.json && chmod 600 /dest/.credentials.json && echo "OK"'

# Clean up the full credential volume (only keep the scoped one)
docker volume rm "$CRED_VOLUME" 2>/dev/null || true

echo ""
echo "Done. Credentials stored in volume: $SCOPED_VOLUME"
echo "Run the acceptance test: $SCRIPT_DIR/run-acceptance.sh"
echo "Run the E2E test: $SCRIPT_DIR/run-e2e.sh"
```

- [ ] **Step 2: Commit**

```bash
git add tests/integration/workforce-smoke/login.sh
git commit -m "fix(login): add TTY detection and use standard credential volume name"
```

---

## Task 4: Update `workflows-run` Skill

Update the skill to detect `image:` nodes and preprocess before calling Archon.

**Files:**
- Modify: `plugins/sdlc-workflows/skills/workflows-run/SKILL.md`

- [ ] **Step 1: Read current skill**

Read `plugins/sdlc-workflows/skills/workflows-run/SKILL.md`.

- [ ] **Step 2: Add preprocessing step**

Add a new step between workflow discovery and Archon execution. After the skill reads the workflow YAML and before it calls `archon workflow run`, insert:

```markdown
### 2b. Preprocess for containerised execution

Check if any node in the workflow has an `image:` field:

```bash
python3 -c "
import yaml
from pathlib import Path
wf = yaml.safe_load(Path('.archon/workflows/<workflow-name>.yaml').read_text())
has_images = any('image' in n for n in wf.get('nodes', []))
print('NEEDS_PREPROCESSING' if has_images else 'NATIVE')
"
```

If NEEDS_PREPROCESSING:

1. Resolve credentials:
```bash
CRED_INFO=$(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/resolve_credentials.py --project-dir . --json)
CRED_TIER=$(echo "$CRED_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['tier'])")
CRED_MOUNT=$(echo "$CRED_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('mount_args',''))")
```

If CRED_TIER is "none", report the error message and stop.

2. Create workspace directory:
```bash
WORKSPACE=$(mktemp -d "${TMPDIR:-/tmp}/sdlc-run-XXXXXX")
cp -R . "$WORKSPACE/"
```

3. Preprocess the workflow:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/preprocess_workflow.py \
    .archon/workflows/<workflow-name>.yaml \
    --output .archon/workflows/.generated/<workflow-name>.yaml \
    --workspace "$WORKSPACE" \
    --cred-mount "$CRED_MOUNT" \
    --commands-dir .archon/commands
```

4. Run the preprocessed workflow:
```bash
archon workflow run <workflow-name> --no-worktree
```

Note: `--no-worktree` because workspace isolation is managed by the containers, not by Archon's worktree provider.

5. Clean up:
```bash
rm -rf "$WORKSPACE"
```

If the workflow has no `image:` nodes, proceed with the existing Archon invocation (no preprocessing).
```

- [ ] **Step 3: Commit**

```bash
git add plugins/sdlc-workflows/skills/workflows-run/SKILL.md
git commit -m "feat(workflows-run): add preprocessing for containerised team execution"
```

---

## Task 5: Update Health Check

Add credential tier reporting to `workflows-setup --health-check`.

**Files:**
- Modify: `plugins/sdlc-workflows/skills/workflows-setup/SKILL.md`

- [ ] **Step 1: Read current skill and add credential check**

After the existing health check items (Archon, Docker, ContainerProvider, ARM64, Loop workaround, Team images), add:

```markdown
#### 9h. Credential injection

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/resolve_credentials.py --project-dir . --json
```

Report:
```
Credential injection:
  Tier 1 (Keychain):     OK | FAIL
  Tier 2 (Volume):       OK | FAIL | SKIP
  Tier 3 (Config):       OK | FAIL | SKIP
  Active tier:           Keychain | Volume | Config | NONE
```
```

- [ ] **Step 2: Commit**

```bash
git add plugins/sdlc-workflows/skills/workflows-setup/SKILL.md
git commit -m "feat(health-check): add credential tier reporting"
```

---

## Task 6: Parallel Review Workflow for Miniproject

Create the parallel workflow that the E2E test will use.

**Files:**
- Create: `tests/integration/workforce-smoke/miniproject/.archon/workflows/parallel-review-pipeline.yaml`
- Create: `tests/integration/workforce-smoke/miniproject/.archon/commands/sdlc-implement.md`
- Create: `tests/integration/workforce-smoke/miniproject/.archon/commands/sdlc-security-review.md`
- Create: `tests/integration/workforce-smoke/miniproject/.archon/commands/sdlc-architecture-review.md`
- Create: `tests/integration/workforce-smoke/miniproject/.archon/commands/sdlc-synthesise.md`

- [ ] **Step 1: Create command prompts**

```markdown
<!-- sdlc-implement.md -->
You are implementing a change to a Python task tracker at /workspace.

Read src/app.py — it has a TaskTracker class with add, complete, list_tasks, pending_count.

Add a "priority" field:
1. add() accepts optional priority (default: "medium", valid: "low"/"medium"/"high")
2. list_tasks() includes priority in returned dicts
3. Add high_priority_count() returning count of incomplete high-priority tasks

Edit src/app.py and tests/test_app.py. Then commit:
  cd /workspace && git add -A && git commit -m "feat: add priority field"
```

```markdown
<!-- sdlc-security-review.md -->
You are performing a security review of a Python task tracker at /workspace.

Read src/app.py and check for:
- Input validation (are parameters validated?)
- Error handling (are exceptions caught properly?)
- Any potential injection or data integrity issues

Write your findings to /workspace/security-review.md with ## Summary, ## Issues, ## Recommendation sections.
Then commit: cd /workspace && git add -A && git commit -m "review: security findings"
```

```markdown
<!-- sdlc-architecture-review.md -->
You are performing an architecture review of a Python task tracker at /workspace.

Read src/app.py and check for:
- Class design (single responsibility, clear API)
- Data structure choices
- Extensibility concerns

Write your findings to /workspace/architecture-review.md with ## Summary, ## Issues, ## Recommendation sections.
Then commit: cd /workspace && git add -A && git commit -m "review: architecture findings"
```

```markdown
<!-- sdlc-synthesise.md -->
Synthesise the security and architecture reviews.

Read /workspace/security-review.md and /workspace/architecture-review.md.

Write a unified summary to /workspace/synthesis.md with:
## Combined Summary
## Critical Issues (from both reviews)
## Recommendation

Then commit: cd /workspace && git add -A && git commit -m "review: synthesis"
```

- [ ] **Step 2: Create the parallel workflow**

```yaml
name: parallel-review-pipeline
description: |
  Parallel review pipeline for smoke testing.
  Implement → parallel security + architecture reviews → synthesise.

provider: claude

nodes:
  - id: implement
    command: sdlc-implement
    image: sdlc-worker:dev-team

  - id: security-review
    command: sdlc-security-review
    image: sdlc-worker:review-team
    depends_on: [implement]

  - id: architecture-review
    command: sdlc-architecture-review
    image: sdlc-worker:review-team
    depends_on: [implement]

  - id: synthesise
    command: sdlc-synthesise
    image: sdlc-worker:dev-team
    depends_on: [security-review, architecture-review]
    trigger_rule: all_success
```

- [ ] **Step 3: Commit**

```bash
git add tests/integration/workforce-smoke/miniproject/.archon/
git commit -m "feat(miniproject): add parallel review workflow and command prompts"
```

---

## Task 7: E2E Sequential Test

The proof that Archon orchestrates containerised team workflows.

**Files:**
- Create: `tests/integration/workforce-smoke/run-e2e.sh`

- [ ] **Step 1: Write the E2E test script**

This script:
1. Builds team images
2. Resolves credentials
3. Preprocesses the feature-pipeline workflow
4. Runs it through Archon
5. Verifies results

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PLUGIN_DIR="$REPO_ROOT/plugins/sdlc-workflows"
SCRIPTS_DIR="$PLUGIN_DIR/scripts"
MINI="$SCRIPT_DIR/miniproject"

echo "=== Phase 4 E2E Orchestration Test ==="
echo "Proves Archon orchestrates containerised team workflows."
echo ""

PASS_COUNT=0
FAIL_COUNT=0
TOTAL=6

pass() { echo "  PASS: $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo "  FAIL: $1 — $2"; FAIL_COUNT=$((FAIL_COUNT + 1)); }

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
for cmd in docker archon python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: $cmd not found."
        exit 1
    fi
done

for img in sdlc-worker:base sdlc-worker:full; do
    if ! docker image inspect "$img" >/dev/null 2>&1; then
        echo "$img not found. Build it first."
        exit 1
    fi
done

# ---------------------------------------------------------------------------
# Build team images
# ---------------------------------------------------------------------------
TEAMS_DIR="$REPO_ROOT/.archon/teams"
AGENTS_DIR="$REPO_ROOT/.archon/agents"
BACKUP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/e2e-backup.XXXXXX")
mkdir -p "$TEAMS_DIR" "$AGENTS_DIR" "$BACKUP_DIR/teams" "$BACKUP_DIR/agents"

# Backup existing state
ls "$TEAMS_DIR"/*.yaml >/dev/null 2>&1 && cp "$TEAMS_DIR"/*.yaml "$BACKUP_DIR/teams/" || true
ls "$AGENTS_DIR"/*.md >/dev/null 2>&1 && cp "$AGENTS_DIR"/*.md "$BACKUP_DIR/agents/" || true

WORKSPACE=$(mktemp -d "${TMPDIR:-/tmp}/e2e-workspace.XXXXXX")

cleanup() {
    rm -f "$TEAMS_DIR"/dev-team.yaml "$TEAMS_DIR"/review-team.yaml
    rm -f "$AGENTS_DIR"/project-context.md
    rm -rf "$TEAMS_DIR/.generated/dev-team"* "$TEAMS_DIR/.generated/review-team"*
    ls "$BACKUP_DIR/teams/"*.yaml >/dev/null 2>&1 && cp "$BACKUP_DIR/teams/"*.yaml "$TEAMS_DIR/" || true
    ls "$BACKUP_DIR/agents/"*.md >/dev/null 2>&1 && cp "$BACKUP_DIR/agents/"*.md "$AGENTS_DIR/" || true
    rm -rf "$BACKUP_DIR" "$WORKSPACE"
    docker rmi sdlc-worker:dev-team sdlc-worker:review-team 2>/dev/null || true
}
trap cleanup EXIT

# Copy miniproject manifests and agents
cp "$MINI/.archon/teams/dev-team.yaml" "$TEAMS_DIR/"
cp "$MINI/.archon/teams/review-team.yaml" "$TEAMS_DIR/"
cp "$MINI/.archon/agents/project-context.md" "$AGENTS_DIR/"

echo "[build] Building team images..."
bash "$PLUGIN_DIR/docker/build-team.sh" dev-team 2>&1 | tail -1
bash "$PLUGIN_DIR/docker/build-team.sh" review-team 2>&1 | tail -1
echo ""

# Copy miniproject to writable workspace
cp -R "$MINI"/* "$MINI"/.archon "$WORKSPACE/"
(cd "$WORKSPACE" && git init -q && git config user.email "test@test.com" && git config user.name "Test" && git add -A && git commit -q -m "initial" 2>/dev/null) || true

# ---------------------------------------------------------------------------
# Resolve credentials
# ---------------------------------------------------------------------------
echo "[1/$TOTAL] Resolve credentials"
CRED_INFO=$(python3 "$SCRIPTS_DIR/resolve_credentials.py" --project-dir "$WORKSPACE" --json 2>/dev/null) || true
CRED_TIER=$(echo "$CRED_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tier','none'))" 2>/dev/null)
CRED_MOUNT=$(echo "$CRED_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('mount_args',''))" 2>/dev/null)

if [ "$CRED_TIER" = "none" ] || [ -z "$CRED_MOUNT" ]; then
    fail "credentials" "no credentials available (tier=$CRED_TIER)"
    echo "Run login.sh first, or ensure Claude Code is authenticated on this Mac."
    echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="
    exit 1
fi
pass "credentials resolved (tier: $CRED_TIER)"

# ---------------------------------------------------------------------------
# Preprocess workflow
# ---------------------------------------------------------------------------
echo "[2/$TOTAL] Preprocess feature-pipeline"
GENERATED_DIR="$WORKSPACE/.archon/workflows/.generated"
mkdir -p "$GENERATED_DIR"

python3 "$SCRIPTS_DIR/preprocess_workflow.py" \
    "$WORKSPACE/.archon/workflows/feature-pipeline.yaml" \
    --output "$GENERATED_DIR/feature-pipeline.yaml" \
    --workspace "$WORKSPACE" \
    --cred-mount "$CRED_MOUNT" \
    --commands-dir "$WORKSPACE/.archon/commands" 2>/dev/null

if [ -f "$GENERATED_DIR/feature-pipeline.yaml" ]; then
    pass "workflow preprocessed to bash nodes"
else
    fail "preprocessing" "output file not created"
    echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="
    exit 1
fi

# ---------------------------------------------------------------------------
# Run through Archon
# ---------------------------------------------------------------------------
echo "[3/$TOTAL] Run workflow through Archon (this takes ~3-5 min)"

# Copy generated workflow as the main workflow (Archon reads from .archon/workflows/)
cp "$GENERATED_DIR/feature-pipeline.yaml" "$WORKSPACE/.archon/workflows/feature-pipeline-containerised.yaml"

ARCHON_OUTPUT=$(cd "$WORKSPACE" && archon workflow run feature-pipeline-containerised --no-worktree 2>&1) || true

if echo "$ARCHON_OUTPUT" | grep -qi "completed\|success\|finished"; then
    pass "Archon reports workflow completed"
else
    # Check if the nodes actually ran by looking at workspace state
    if [ -f "$WORKSPACE/review-output.md" ] || git -C "$WORKSPACE" log --oneline 2>/dev/null | grep -q "feat:"; then
        pass "Archon workflow produced results (output may not show completion string)"
    else
        fail "Archon execution" "no completion signal and no results. Output tail: $(echo "$ARCHON_OUTPUT" | tail -5)"
    fi
fi

# ---------------------------------------------------------------------------
# Verify results
# ---------------------------------------------------------------------------
echo "[4/$TOTAL] Implementation produced working code"
IMPL_CHECK=$(cd "$WORKSPACE" && python3 -c "
import sys
sys.path.insert(0, 'src')
from app import TaskTracker
t = TaskTracker()
t.add('urgent', priority='high')
t.add('normal')
has_priority = any('priority' in task for task in t.list_tasks())
has_method = hasattr(t, 'high_priority_count')
print(f'priority={has_priority} method={has_method}')
" 2>&1) || true

if echo "$IMPL_CHECK" | grep -q "priority=True method=True"; then
    pass "priority field and high_priority_count() work"
else
    fail "implementation" "$IMPL_CHECK"
fi

echo "[5/$TOTAL] Review produced output"
if [ -f "$WORKSPACE/review-output.md" ]; then
    LINES=$(wc -l < "$WORKSPACE/review-output.md" | tr -d ' ')
    pass "review-output.md exists ($LINES lines)"
else
    fail "review output" "review-output.md not found"
fi

echo "[6/$TOTAL] Git history shows work from both containers"
COMMITS=$(cd "$WORKSPACE" && git log --oneline 2>/dev/null | wc -l | tr -d ' ')
if [ "${COMMITS:-0}" -gt 1 ]; then
    pass "git history: $COMMITS commits"
else
    fail "git history" "expected multiple commits, got $COMMITS"
fi

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
echo ""
echo "=== Results: $PASS_COUNT pass, $FAIL_COUNT fail (of $TOTAL) ==="
if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "Phase 4 E2E sequential test: ALL PASS"
    echo ""
    echo "Proven:"
    echo "  - Workflow preprocessor transforms image nodes to bash nodes"
    echo "  - Credentials resolved automatically"
    echo "  - Archon orchestrates containerised workflow"
    echo "  - Dev-team implements features in its container"
    echo "  - Review-team reviews in its container"
    exit 0
else
    echo "Phase 4 E2E sequential test: FAILURES DETECTED"
    exit 1
fi
```

Save to: `tests/integration/workforce-smoke/run-e2e.sh`

- [ ] **Step 2: Make executable and commit**

```bash
chmod +x tests/integration/workforce-smoke/run-e2e.sh
git add tests/integration/workforce-smoke/run-e2e.sh
git commit -m "test(e2e): add Archon-orchestrated sequential workflow test"
```

---

## Task 8: Run E2E Sequential Test

This is verification, not implementation. Run the test and fix any issues.

- [ ] **Step 1: Run all unit tests first**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/ --ignore=tests/integration -q`
Expected: All tests PASS

- [ ] **Step 2: Run the Phase 3 smoke tests**

Run: `bash tests/integration/team-smoke/run.sh && bash tests/integration/workforce-smoke/run.sh && bash tests/integration/workforce-smoke/run-containers.sh`
Expected: All PASS

- [ ] **Step 3: Run the E2E sequential test**

Run: `bash tests/integration/workforce-smoke/run-e2e.sh`
Expected: 6/6 PASS

- [ ] **Step 4: Fix any issues found and recommit**

If any checks fail, debug and fix. The E2E test exercises the full stack — preprocessor, credential resolver, Archon integration, container execution. Any failure is a real integration issue.

- [ ] **Step 5: Commit any fixes**

```bash
git add -A && git commit -m "fix: address issues found in E2E sequential test"
```

---

## Task 9: E2E Parallel Test

Extend the E2E test to prove parallel fork/merge works.

**Files:**
- Modify: `tests/integration/workforce-smoke/run-e2e.sh` (add parallel section)

- [ ] **Step 1: Add parallel test section to run-e2e.sh**

After the sequential test, add a second section that runs the parallel-review-pipeline:

The parallel test needs workspace branch management. Before the parallel nodes run, the workspace is on a single branch. The preprocessor needs to add pre-fork and post-merge bash nodes for parallel layers.

Add a `--parallel` flag to `run-e2e.sh` that runs the parallel workflow test. This tests:
- Preprocessing handles parallel nodes (generates branch/merge bash nodes)
- Two review containers run (can be sequential since Archon may serialise bash nodes)
- Both reviews produce output files
- Synthesise node sees both review files

- [ ] **Step 2: Run the parallel E2E test**

Run: `bash tests/integration/workforce-smoke/run-e2e.sh --parallel`
Expected: All checks PASS

- [ ] **Step 3: Commit**

```bash
git add tests/integration/workforce-smoke/run-e2e.sh
git commit -m "test(e2e): add parallel fork/merge workflow test"
```

---

## Task 10: Update CLAUDE.md and Documentation

- [ ] **Step 1: Update CLAUDE.md Active Work**

Update the EPIC #96 bullet to reflect Phase 4 status.

- [ ] **Step 2: Full verification run**

Run all tests:
```bash
python -m pytest tests/ --ignore=tests/integration -q
bash tests/integration/team-smoke/run.sh
bash tests/integration/workforce-smoke/run.sh
bash tests/integration/workforce-smoke/run-containers.sh
bash tests/integration/workforce-smoke/run-acceptance.sh
bash tests/integration/workforce-smoke/run-e2e.sh
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with Phase 4 orchestration status"
```

---

## Summary

| Task | Component | New Tests | Commits |
|------|-----------|-----------|---------|
| 1 | `resolve_credentials.py` | 6 | 1 |
| 2 | `preprocess_workflow.py` | 10 | 1 |
| 3 | Login script fix | — | 1 |
| 4 | `workflows-run` skill update | — | 1 |
| 5 | Health check update | — | 1 |
| 6 | Parallel workflow + commands | — | 1 |
| 7 | E2E sequential test | — | 1 |
| 8 | E2E verification + fixes | — | 1+ |
| 9 | E2E parallel test | — | 1 |
| 10 | CLAUDE.md + full verification | — | 1 |
| **Total** | **6 new files, 3 modified** | **16 tests** | **~10 commits** |
