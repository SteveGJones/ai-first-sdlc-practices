#!/usr/bin/env python3
"""Unit coverage for the §7.4 full-formation super-smoke.

Runs the preprocessor over the real miniproject
``full-formation-pipeline.yaml`` and asserts every structural property
the bash super-smoke checks.  Keeps the multi-team guarantees in CI
even when docker/archon aren't available on the host.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from sdlc_workflows_scripts import preprocess_workflow


REPO_ROOT = Path(__file__).resolve().parent.parent
MINI = REPO_ROOT / "tests" / "integration" / "workforce-smoke" / "miniproject"
WORKFLOW = MINI / ".archon" / "workflows" / "full-formation-pipeline.yaml"
COMMANDS = MINI / ".archon" / "commands"


def _preprocessed() -> dict:
    """Return the preprocessed workflow as a dict."""
    src = yaml.safe_load(WORKFLOW.read_text())
    return preprocess_workflow.transform_workflow(
        src,
        workspace="/tmp/ws",
        cred_mount="/dev/null:/tmp/dummy:ro",
        commands_dir=str(COMMANDS),
    )


def test_source_workflow_exists() -> None:
    assert WORKFLOW.is_file(), f"missing source workflow: {WORKFLOW}"


def test_all_four_team_images_referenced() -> None:
    wf = _preprocessed()
    blob = yaml.dump(wf)
    for team in ("planner-team", "dev-team", "qa-team", "synth-team"):
        assert f"sdlc-worker:{team}" in blob, f"missing image: {team}"


def test_timeout_override_propagates_to_implement() -> None:
    wf = _preprocessed()
    implement = next(n for n in wf["nodes"] if n["id"] == "implement")
    assert "CLAUDE_TIMEOUT=600" in implement["bash"]


def test_model_override_propagates_to_every_image_node() -> None:
    wf = _preprocessed()
    for node in wf["nodes"]:
        if "bash" not in node:
            continue
        assert "CLAUDE_MODEL=claude-sonnet-4-6" in node["bash"], (
            f"node {node['id']} missing CLAUDE_MODEL"
        )


def test_dag_preserved() -> None:
    wf = _preprocessed()
    nm = {n["id"]: n for n in wf["nodes"]}
    assert nm["qa-security"]["depends_on"] == ["implement"]
    assert nm["qa-architecture"]["depends_on"] == ["implement"]
    assert set(nm["synthesise"]["depends_on"]) == {"qa-security", "qa-architecture"}
    assert nm["synthesise"]["trigger_rule"] == "all_success"


def test_security_flags_on_every_image_node() -> None:
    wf = _preprocessed()
    flags = [
        "--cap-drop ALL",
        "--security-opt no-new-privileges",
        "--memory=4g",
        "--cpus=2",
    ]
    for node in wf["nodes"]:
        if "bash" not in node:
            continue
        for flag in flags:
            assert flag in node["bash"], (
                f"node {node['id']} missing flag {flag!r}"
            )


def test_finalise_node_preserved_untransformed() -> None:
    wf = _preprocessed()
    finalise = next(n for n in wf["nodes"] if n["id"] == "finalise")
    assert "bash" not in finalise
    assert "prompt" in finalise
