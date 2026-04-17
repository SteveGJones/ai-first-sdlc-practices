#!/usr/bin/env python3
"""Tests for preprocess_workflow — image node to bash node transformation."""

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plugins_sdlc_workflows_scripts as scripts  # noqa: E402

preprocess_workflow = scripts.preprocess_workflow


CRED_MOUNT = "-v /tmp/creds.json:/home/sdlc/.claude-creds/.credentials.json:ro"


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


class TestSecurityFlags:
    """Security flags are present in generated docker run commands."""

    _NODE = {
        "id": "implement",
        "image": "sdlc-worker:dev-team",
        "command": "sdlc-implement",
    }
    _CRED_MOUNT = "/tmp/c.json:/home/sdlc/.claude-creds/.credentials.json:ro"
    _COMMANDS_DIR = ".archon/commands"

    def _transform(self, node: dict | None = None) -> dict:
        return preprocess_workflow.transform_node(
            node or dict(self._NODE),
            workspace="/workspace",
            cred_mount=self._CRED_MOUNT,
            commands_dir=self._COMMANDS_DIR,
        )

    def test_docker_run_has_cap_drop(self) -> None:
        result = self._transform()
        assert "--cap-drop ALL" in result["bash"]

    def test_docker_run_no_read_only(self) -> None:
        """--read-only is NOT used (conflicts with Claude Code plugin paths)."""
        result = self._transform()
        assert "--read-only" not in result["bash"]

    def test_timeout_env_passed(self) -> None:
        node = dict(self._NODE)
        node["timeout"] = 600
        result = self._transform(node)
        assert "CLAUDE_TIMEOUT=600" in result["bash"]
