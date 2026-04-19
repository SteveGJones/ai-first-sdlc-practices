#!/usr/bin/env python3
"""Tests for preprocess_workflow — image node to bash node transformation."""

import logging

from sdlc_workflows_scripts import preprocess_workflow


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

    def test_docker_run_has_no_new_privileges(self) -> None:
        """--security-opt no-new-privileges is always present (S-M-1)."""
        result = self._transform()
        assert "--security-opt no-new-privileges" in result["bash"]

    def test_docker_run_has_memory_and_cpu_limits(self) -> None:
        """Resource limits capped by default (D-M-7)."""
        result = self._transform()
        assert "--memory=4g" in result["bash"]
        assert "--cpus=2" in result["bash"]


class TestShellEscapeHygiene:
    """Adversarial cases covering shlex.quote hygiene (S-I-6 / CR-I-2 / SA-I-1).

    Every shell-interpolated value in the generated ``docker run`` must
    survive metacharacters.  These tests exercise the preprocessor's
    quoting — never the code-review claim that "it looks safe".
    """

    _CRED_MOUNT = "/tmp/c.json:/home/sdlc/.claude-creds/.credentials.json:ro"

    def _transform(self, node: dict, **overrides) -> dict:
        kwargs = {
            "workspace": "/workspace",
            "cred_mount": self._CRED_MOUNT,
            "commands_dir": ".archon/commands",
        }
        kwargs.update(overrides)
        return preprocess_workflow.transform_node(node, **kwargs)

    def test_workspace_with_spaces_is_quoted(self) -> None:
        """Workspace with spaces produces a valid docker run (SA-I-1)."""
        node = {
            "id": "n",
            "image": "sdlc-worker:dev",
            "command": "cmd",
        }
        result = self._transform(node, workspace="/path with spaces/ws")
        # shlex.quote wraps in single quotes because of the space
        assert "'/path with spaces/ws:/workspace'" in result["bash"]
        # Bare, unquoted path MUST NOT appear in the command
        assert "-v /path with spaces/ws" not in result["bash"]

    def test_prompt_containing_sentinel_literal_survives(self) -> None:
        """Prompt body with literal 'SDLC_PROMPT_EOF' does not break
        generation (CR-M-5).  The heredoc sentinel is a per-invocation
        nonce, so the literal token inside the body is just text."""
        node = {
            "id": "n",
            "image": "sdlc-worker:dev",
            "prompt": (
                "Please handle the SDLC_PROMPT_EOF token carefully.\n"
                "SDLC_PROMPT_EOF should not end the heredoc."
            ),
        }
        result = self._transform(node)
        bash = result["bash"]
        # A per-invocation sentinel has a hex suffix — the bare literal
        # alone is not used as a heredoc terminator.
        import re
        sentinels = re.findall(r"SDLC_PROMPT_EOF_[0-9a-f]{16}", bash)
        assert len(sentinels) == 2, (
            "Heredoc must open and close with a nonce sentinel"
        )
        assert sentinels[0] == sentinels[1]

    def test_heredoc_sentinels_differ_across_invocations(self) -> None:
        """Per-invocation nonces are actually different each call."""
        node = {
            "id": "n",
            "image": "sdlc-worker:dev",
            "prompt": "hello",
        }
        a = self._transform(node)["bash"]
        b = self._transform(node)["bash"]
        import re
        sa = re.findall(r"SDLC_PROMPT_EOF_[0-9a-f]{16}", a)[0]
        sb = re.findall(r"SDLC_PROMPT_EOF_[0-9a-f]{16}", b)[0]
        assert sa != sb

    def test_image_with_metacharacters_is_quoted(self) -> None:
        """A maliciously crafted image tag can't break out of docker run."""
        node = {
            "id": "n",
            "image": "sdlc-worker:dev; rm -rf /",
            "command": "cmd",
        }
        result = self._transform(node)
        # shlex.quote renders the whole tag as a single quoted token
        assert "'sdlc-worker:dev; rm -rf /'" in result["bash"]
        # Bare, unquoted metacharacter sequence MUST NOT appear
        assert "sdlc-worker:dev; rm -rf /" not in result["bash"].replace(
            "'sdlc-worker:dev; rm -rf /'", ""
        )

    def test_command_name_with_spaces_is_quoted(self) -> None:
        """A command name with a space (yes, odd, but possible) stays
        a single shell token."""
        node = {
            "id": "n",
            "image": "sdlc-worker:dev",
            "command": "weird command",
        }
        result = self._transform(node)
        assert "'.archon/commands/weird command.md'" in result["bash"]


class TestModelPassthrough:
    """Nodes declaring ``model:`` propagate it to CLAUDE_MODEL env var.

    Covers SA-C-1 from the seven-dimension review: a workflow author
    who sets ``model: claude-opus-4-6[1m]`` on a node expects the
    container to run Claude with that model selected — currently the
    field is silently dropped.
    """

    _CRED_MOUNT = "/tmp/c.json:/home/sdlc/.claude-creds/.credentials.json:ro"
    _COMMANDS_DIR = ".archon/commands"

    def _transform(self, node: dict) -> dict:
        return preprocess_workflow.transform_node(
            node,
            workspace="/workspace",
            cred_mount=self._CRED_MOUNT,
            commands_dir=self._COMMANDS_DIR,
        )

    def test_model_field_preserved_in_command_node(self) -> None:
        node = {
            "id": "reason",
            "image": "sdlc-worker:dev-team",
            "command": "sdlc-implement",
            "model": "claude-opus-4-6[1m]",
        }
        result = self._transform(node)
        assert 'CLAUDE_MODEL=claude-opus-4-6[1m]' in result["bash"]

    def test_model_field_preserved_in_prompt_node(self) -> None:
        node = {
            "id": "synth",
            "image": "sdlc-worker:dev-team",
            "prompt": "Summarise the reviews.",
            "model": "claude-sonnet-4-6",
        }
        result = self._transform(node)
        assert "CLAUDE_MODEL=claude-sonnet-4-6" in result["bash"]

    def test_model_field_preserved_in_loop_node(self) -> None:
        node = {
            "id": "implement",
            "image": "sdlc-worker:dev-team",
            "model": "claude-opus-4-6",
            "loop": {
                "prompt": "Fix the code until tests pass.",
                "until": "DONE",
                "max_iterations": 3,
            },
        }
        result = self._transform(node)
        assert "CLAUDE_MODEL=claude-opus-4-6" in result["bash"]

    def test_model_absent_means_no_env_var(self) -> None:
        node = {
            "id": "implement",
            "image": "sdlc-worker:dev-team",
            "command": "sdlc-implement",
        }
        result = self._transform(node)
        assert "CLAUDE_MODEL" not in result["bash"]


class TestParallelWorkspaceContract:
    """Locks in the documented parallel-fan-out workspace contract.

    Covers SA-C-2.  Full branch-merge workspace isolation is out of
    scope for v1 (see CLAUDE-CONTEXT-workflows.md -> Parallel Execution
    Semantics).  In v1, parallel nodes share the mounted workspace; the
    preprocessor emits a structured warning at fan-out points so the
    contract is surfaced at preprocess time, not discovered at runtime.
    """

    def test_detects_simple_fan_out(self) -> None:
        workflow = {
            "nodes": [
                {"id": "plan", "image": "sdlc-worker:dev", "command": "plan"},
                {
                    "id": "review-a",
                    "image": "sdlc-worker:dev",
                    "command": "review",
                    "depends_on": ["plan"],
                },
                {
                    "id": "review-b",
                    "image": "sdlc-worker:dev",
                    "command": "review",
                    "depends_on": ["plan"],
                },
            ],
        }
        fan_outs = preprocess_workflow._detect_fan_outs(workflow)
        assert fan_outs == {"plan": ["review-a", "review-b"]}

    def test_no_fan_out_in_sequential(self) -> None:
        workflow = {
            "nodes": [
                {"id": "a", "image": "sdlc-worker:dev", "command": "a"},
                {
                    "id": "b",
                    "image": "sdlc-worker:dev",
                    "command": "b",
                    "depends_on": ["a"],
                },
                {
                    "id": "c",
                    "image": "sdlc-worker:dev",
                    "command": "c",
                    "depends_on": ["b"],
                },
            ],
        }
        assert preprocess_workflow._detect_fan_outs(workflow) == {}

    def test_parallel_nodes_share_workspace_mount(self) -> None:
        """Regression: parallel siblings get the same -v <workspace>:/workspace.

        Locks in the current v1 contract: workspace is shared; outputs
        with the same filename will clobber.  This test fails the day
        we introduce branch-scoped workspace isolation — intentionally.
        """
        workflow = {
            "nodes": [
                {"id": "plan", "image": "sdlc-worker:dev", "command": "plan"},
                {
                    "id": "review-a",
                    "image": "sdlc-worker:dev",
                    "command": "review",
                    "depends_on": ["plan"],
                },
                {
                    "id": "review-b",
                    "image": "sdlc-worker:dev",
                    "command": "review",
                    "depends_on": ["plan"],
                },
            ],
        }
        transformed = preprocess_workflow.transform_workflow(
            workflow,
            workspace="/host/ws",
            cred_mount="/tmp/c.json:/home/sdlc/.claude-creds/.credentials.json:ro",
            commands_dir=".archon/commands",
        )
        branch_nodes = [n for n in transformed["nodes"] if n["id"].startswith("review-")]
        assert len(branch_nodes) == 2
        for n in branch_nodes:
            # shlex.quote leaves the safe ':' path unwrapped, so the
            # generated mount looks like: -v /host/ws:/workspace
            assert "-v /host/ws:/workspace" in n["bash"]

    def test_fan_out_emits_warning(self, caplog: "logging.LogRecord") -> None:
        workflow = {
            "nodes": [
                {"id": "plan", "image": "sdlc-worker:dev", "command": "plan"},
                {
                    "id": "review-a",
                    "image": "sdlc-worker:dev",
                    "command": "review",
                    "depends_on": ["plan"],
                },
                {
                    "id": "review-b",
                    "image": "sdlc-worker:dev",
                    "command": "review",
                    "depends_on": ["plan"],
                },
            ],
        }
        with caplog.at_level(
            logging.WARNING, logger="sdlc_workflows_scripts.preprocess_workflow"
        ):
            preprocess_workflow.transform_workflow(
                workflow,
                workspace="/host/ws",
                cred_mount="/tmp/c.json:/home/sdlc/.claude-creds/.credentials.json:ro",
                commands_dir=".archon/commands",
            )
        assert any(
            "share the mounted workspace" in rec.message for rec in caplog.records
        )

    def test_sequential_workflow_no_warning(self, caplog: "logging.LogRecord") -> None:
        workflow = {
            "nodes": [
                {"id": "a", "image": "sdlc-worker:dev", "command": "a"},
                {
                    "id": "b",
                    "image": "sdlc-worker:dev",
                    "command": "b",
                    "depends_on": ["a"],
                },
            ],
        }
        with caplog.at_level(
            logging.WARNING, logger="sdlc_workflows_scripts.preprocess_workflow"
        ):
            preprocess_workflow.transform_workflow(
                workflow,
                workspace="/host/ws",
                cred_mount="/tmp/c.json:/home/sdlc/.claude-creds/.credentials.json:ro",
                commands_dir=".archon/commands",
            )
        assert not any(
            "share the mounted workspace" in rec.message for rec in caplog.records
        )
