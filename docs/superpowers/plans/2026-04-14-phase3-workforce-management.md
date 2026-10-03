# Phase 3: Workforce Management — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver coaching, visibility, dynamic composition, and play-calling for containerised delegation teams — the management layer on top of Phase 2's infrastructure.

**Architecture:** Four new Python scripts provide the data layer (inventory, status, coaching signals, override logging). Two new skills (`manage-teams`, `teams-status`) expose this to users via guided Q&A. Dynamic composition extends the existing workflow schema with `team_extend`. Play-calling adds a `--plan-task` mode to `manage-teams` that recommends workflow + team formations. All scripts follow the Phase 2 pattern: pure functions with CLI wrappers, tested via pytest, imported through the `plugins_sdlc_workflows_scripts.py` shim.

**Tech Stack:** Python 3.14, PyYAML, pytest, Docker CLI (subprocess), existing Phase 2 scripts (`resolve_plugin_paths.py`, `validate_team_manifest.py`, `generate_team_claude_md.py`, `generate_team_dockerfile.py`)

**Branch:** `feature/96-sdlc-workflows` (worktree at `.worktrees/feature-96-sdlc-workflows`)

**Spec:** `docs/superpowers/specs/2026-04-13-phase2-team-composition-and-delegation-design.md` (Sections 5, 10-12)

**Review feedback incorporated:**
- Simplified lifecycle: `active` / deleted (manifest removed). Validator still accepts all 4 statuses for backward compat, but coaching UI only surfaces active + delete. (Agile coach W8, R9)
- Right-sizing guards in `--create`: check team count vs workflow count before suggesting granularity. (Agile coach Section 1)
- Level 1 adoption path: when no teams exist, offer a single general-purpose team. (Agile coach W7, R10, O3)
- Tiered coaching signals: critical / advisory / informational. (Agile coach Section 4)
- `team_extend` injection is prompt-context-only — honest about the trade-off vs filesystem enforcement. (SWOT W4, R12)
- Play-calling scoped as workflow-template selection + team adjustment, NOT a per-task ceremony. (Agile coach Section 3)
- `deploy-team` stays independent (already shipped in Phase 2) but `manage-teams` auto-invokes it after create/update. (Agile coach Section 5)

---

## File Structure

### New files

| File | Responsibility |
|------|---------------|
| `plugins/sdlc-workflows/scripts/team_inventory.py` | Discover available agents + skills from installed plugins. Walks plugin directories, returns structured inventory. |
| `plugins/sdlc-workflows/scripts/teams_status_report.py` | Generate fleet status data: manifests, staleness, Docker image presence, workflow usage mapping. |
| `plugins/sdlc-workflows/scripts/coaching_signals.py` | Analyse team fleet for tiered coaching signals (critical/advisory/informational). |
| `plugins/sdlc-workflows/scripts/override_logger.py` | Append-only JSONL logger for `team_extend` overrides. Read + aggregate for coaching. |
| `plugins/sdlc-workflows/skills/manage-teams/SKILL.md` | Coaching skill: `--create`, `--update`, `--delete`, `--review`, `--plan-task`. |
| `plugins/sdlc-workflows/skills/teams-status/SKILL.md` | Fleet visibility skill: fleet view, single-team detail, coaching signals. |
| `tests/test_team_inventory.py` | Tests for plugin inventory discovery. |
| `tests/test_teams_status_report.py` | Tests for fleet status reporting. |
| `tests/test_coaching_signals.py` | Tests for coaching signal analysis. |
| `tests/test_override_logger.py` | Tests for override logging + aggregation. |
| `tests/test_team_extend_validation.py` | Tests for `team_extend` reference validation. |

### Modified files

| File | Change |
|------|--------|
| `plugins_sdlc_workflows_scripts.py` | Add new script modules to import shim. |
| `tools/validation/check_workflow_teams.py` | Add `team_extend` reference validation. |
| `CLAUDE.md` | Add Phase 3 skills to Available Skills table. |

---

## Task 1: Plugin Inventory Discovery (`team_inventory.py`)

The foundation script. Discovers all available agents and skills across installed plugins so that `manage-teams --create` can show what's available and `teams-status` can report "available but not included."

**Files:**
- Create: `plugins/sdlc-workflows/scripts/team_inventory.py`
- Create: `tests/test_team_inventory.py`
- Modify: `plugins_sdlc_workflows_scripts.py`

- [ ] **Step 1: Write failing tests for `discover_plugin_agents`**

```python
#!/usr/bin/env python3
"""Tests for team_inventory — plugin agent and skill discovery."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plugins_sdlc_workflows_scripts as scripts  # noqa: E402

team_inventory = scripts.team_inventory


class TestDiscoverPluginAgents:
    def test_finds_agents_in_plugin(self, tmp_path: Path) -> None:
        """Agents are discovered from a plugin's agents/ directory."""
        plugin_dir = tmp_path / "cache" / "mkt" / "my-plugin" / "1.0.0"
        agents_dir = plugin_dir / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "security-architect.md").write_text(
            "---\nname: security-architect\n"
            "description: OWASP and threat modelling\n---\n"
        )
        (agents_dir / "compliance-auditor.md").write_text(
            "---\nname: compliance-auditor\n"
            "description: Regulatory compliance checks\n---\n"
        )

        result = team_inventory.discover_plugin_agents(plugin_dir)
        assert len(result) == 2
        names = {a["name"] for a in result}
        assert names == {"security-architect", "compliance-auditor"}

    def test_extracts_description_from_frontmatter(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "plugin"
        agents_dir = plugin_dir / "agents"
        agents_dir.mkdir(parents=True)
        (agents_dir / "architect.md").write_text(
            "---\nname: architect\n"
            "description: System architecture design\n---\n\nBody text."
        )

        result = team_inventory.discover_plugin_agents(plugin_dir)
        assert result[0]["description"] == "System architecture design"

    def test_empty_agents_dir(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "plugin"
        (plugin_dir / "agents").mkdir(parents=True)
        result = team_inventory.discover_plugin_agents(plugin_dir)
        assert result == []

    def test_no_agents_dir(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "plugin"
        plugin_dir.mkdir(parents=True)
        result = team_inventory.discover_plugin_agents(plugin_dir)
        assert result == []


class TestDiscoverPluginSkills:
    def test_finds_skills_in_plugin(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "plugin"
        skill_dir = plugin_dir / "skills" / "validate"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: validate\n"
            "description: Run validation pipeline\n---\n"
        )

        result = team_inventory.discover_plugin_skills(plugin_dir)
        assert len(result) == 1
        assert result[0]["name"] == "validate"
        assert result[0]["description"] == "Run validation pipeline"

    def test_skips_dirs_without_skill_md(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "plugin"
        (plugin_dir / "skills" / "broken").mkdir(parents=True)
        result = team_inventory.discover_plugin_skills(plugin_dir)
        assert result == []


class TestDiscoverAll:
    def test_full_inventory(self, tmp_path: Path) -> None:
        """discover_all builds a complete inventory from installed_plugins.json."""
        # Set up plugin directories
        plugin_a = tmp_path / "cache" / "mkt" / "plugin-a" / "1.0.0"
        (plugin_a / "agents").mkdir(parents=True)
        (plugin_a / "agents" / "agent-x.md").write_text(
            "---\nname: agent-x\ndescription: Agent X\n---\n"
        )
        (plugin_a / "skills" / "skill-y").mkdir(parents=True)
        (plugin_a / "skills" / "skill-y" / "SKILL.md").write_text(
            "---\nname: skill-y\ndescription: Skill Y\n---\n"
        )
        (plugin_a / ".claude-plugin").mkdir(parents=True)
        (plugin_a / ".claude-plugin" / "plugin.json").write_text("{}")

        plugin_b = tmp_path / "cache" / "mkt" / "plugin-b" / "2.0.0"
        (plugin_b / "agents").mkdir(parents=True)
        (plugin_b / "agents" / "agent-z.md").write_text(
            "---\nname: agent-z\ndescription: Agent Z\n---\n"
        )
        (plugin_b / ".claude-plugin").mkdir(parents=True)
        (plugin_b / ".claude-plugin" / "plugin.json").write_text("{}")

        # Create installed_plugins.json
        installed = {
            "plugin-a@mkt": {"name": "plugin-a", "installPath": str(plugin_a)},
            "plugin-b@mkt": {"name": "plugin-b", "installPath": str(plugin_b)},
        }
        installed_json = tmp_path / "installed_plugins.json"
        installed_json.write_text(json.dumps(installed))

        result = team_inventory.discover_all(installed_json)
        assert "plugin-a" in result
        assert "plugin-b" in result
        assert len(result["plugin-a"]["agents"]) == 1
        assert len(result["plugin-a"]["skills"]) == 1
        assert len(result["plugin-b"]["agents"]) == 1
        assert len(result["plugin-b"]["skills"]) == 0

    def test_missing_plugin_path_skipped(self, tmp_path: Path) -> None:
        """Plugins whose installPath doesn't exist are skipped."""
        installed = {
            "ghost@mkt": {"name": "ghost", "installPath": "/nonexistent/path"},
        }
        installed_json = tmp_path / "installed_plugins.json"
        installed_json.write_text(json.dumps(installed))

        result = team_inventory.discover_all(installed_json)
        assert result == {}


class TestInventoryForTeam:
    def test_available_but_not_included(self, tmp_path: Path) -> None:
        """Reports agents available in a plugin but not in the team manifest."""
        plugin_dir = tmp_path / "cache" / "mkt" / "sec-plugin" / "1.0.0"
        (plugin_dir / "agents").mkdir(parents=True)
        (plugin_dir / "agents" / "architect.md").write_text(
            "---\nname: architect\ndescription: Arch\n---\n"
        )
        (plugin_dir / "agents" / "auditor.md").write_text(
            "---\nname: auditor\ndescription: Audit\n---\n"
        )
        (plugin_dir / "agents" / "privacy.md").write_text(
            "---\nname: privacy\ndescription: Privacy\n---\n"
        )
        (plugin_dir / ".claude-plugin").mkdir(parents=True)
        (plugin_dir / ".claude-plugin" / "plugin.json").write_text("{}")

        installed = {
            "sec-plugin@mkt": {
                "name": "sec-plugin",
                "installPath": str(plugin_dir),
            },
        }
        installed_json = tmp_path / "installed_plugins.json"
        installed_json.write_text(json.dumps(installed))

        team_agents = ["sec-plugin:architect"]

        available = team_inventory.available_but_not_included(
            installed_json=installed_json,
            team_plugins=["sec-plugin"],
            team_agents=team_agents,
        )
        names = {a["qualified"] for a in available["agents"]}
        assert "sec-plugin:auditor" in names
        assert "sec-plugin:privacy" in names
        assert "sec-plugin:architect" not in names
```

Save to: `tests/test_team_inventory.py`

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_team_inventory.py -v 2>&1 | head -20`
Expected: FAIL — `team_inventory` module not found

- [ ] **Step 3: Implement `team_inventory.py`**

```python
#!/usr/bin/env python3
"""Discover available agents and skills from installed plugins.

Walks each plugin's ``agents/`` and ``skills/`` directories to build
a structured inventory.  Used by ``manage-teams`` (to show what's
available during team creation) and ``teams-status`` (to report
"available but not included").

Public API
----------
discover_plugin_agents(plugin_path) -> list[dict]
discover_plugin_skills(plugin_path) -> list[dict]
discover_all(installed_json) -> dict[str, dict]
available_but_not_included(installed_json, team_plugins, team_agents) -> dict
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Allow sibling import when run as a script.
_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import resolve_plugin_paths  # noqa: E402

# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract key: value pairs from YAML frontmatter."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip().strip("'\"")
    return result


# ---------------------------------------------------------------------------
# Plugin discovery
# ---------------------------------------------------------------------------


def discover_plugin_agents(plugin_path: Path) -> list[dict[str, str]]:
    """Discover agents in a plugin's ``agents/`` directory.

    Returns a list of dicts with ``name`` and ``description`` keys.
    """
    agents_dir = plugin_path / "agents"
    if not agents_dir.is_dir():
        return []

    agents: list[dict[str, str]] = []
    for md_file in sorted(agents_dir.glob("*.md")):
        text = md_file.read_text()
        fm = _parse_frontmatter(text)
        name = fm.get("name", md_file.stem)
        description = fm.get("description", "")
        agents.append({"name": name, "description": description})
    return agents


def discover_plugin_skills(plugin_path: Path) -> list[dict[str, str]]:
    """Discover skills in a plugin's ``skills/`` directory.

    A valid skill is a subdirectory containing ``SKILL.md``.
    Returns a list of dicts with ``name`` and ``description`` keys.
    """
    skills_dir = plugin_path / "skills"
    if not skills_dir.is_dir():
        return []

    skills: list[dict[str, str]] = []
    for child in sorted(skills_dir.iterdir()):
        skill_md = child / "SKILL.md"
        if child.is_dir() and skill_md.exists():
            text = skill_md.read_text()
            fm = _parse_frontmatter(text)
            name = fm.get("name", child.name)
            description = fm.get("description", "")
            skills.append({"name": name, "description": description})
    return skills


def discover_all(
    installed_json: Path,
) -> dict[str, dict[str, list[dict[str, str]]]]:
    """Build a complete inventory of agents and skills from all installed plugins.

    Parameters
    ----------
    installed_json:
        Path to ``installed_plugins.json``.

    Returns
    -------
    dict
        ``{plugin_name: {"agents": [...], "skills": [...]}}``
        Plugins whose install path doesn't exist are silently skipped.
    """
    with installed_json.open() as fh:
        raw = json.load(fh)

    # Normalise to flat dict of key -> entry
    entries: dict[str, dict[str, str]] = {}
    if isinstance(raw, dict) and "version" in raw and "plugins" in raw:
        for key, val_list in raw["plugins"].items():
            if isinstance(val_list, list) and val_list:
                entries[key] = val_list[0]
            elif isinstance(val_list, dict):
                entries[key] = val_list
    else:
        for key, val in raw.items():
            if isinstance(val, dict):
                entries[key] = val
            elif isinstance(val, list) and val:
                entries[key] = val[0]

    inventory: dict[str, dict[str, list[dict[str, str]]]] = {}
    for key, entry in entries.items():
        install_path = entry.get("installPath")
        if not install_path:
            continue
        plugin_path = Path(install_path)
        if not plugin_path.is_dir():
            continue

        bare_name = key.split("@")[0] if "@" in key else key
        inventory[bare_name] = {
            "agents": discover_plugin_agents(plugin_path),
            "skills": discover_plugin_skills(plugin_path),
        }

    return inventory


def available_but_not_included(
    installed_json: Path,
    team_plugins: list[str],
    team_agents: list[str],
) -> dict[str, list[dict[str, str]]]:
    """Find agents and skills available in team plugins but not on the team.

    Parameters
    ----------
    installed_json:
        Path to ``installed_plugins.json``.
    team_plugins:
        Plugin names listed in the team manifest.
    team_agents:
        Qualified agent references (``plugin:agent``) in the team manifest.

    Returns
    -------
    dict
        ``{"agents": [{"qualified": "plugin:agent", "description": "..."}]}``
    """
    inventory = discover_all(installed_json)

    # Build set of already-included agent names
    included_agents: set[str] = set()
    for ref in team_agents:
        if ":" in ref and not ref.startswith("local:"):
            included_agents.add(ref)

    available_agents: list[dict[str, str]] = []
    for plugin_name in team_plugins:
        bare = plugin_name.split("@")[0] if "@" in plugin_name else plugin_name
        if bare not in inventory:
            continue
        for agent in inventory[bare]["agents"]:
            qualified = f"{bare}:{agent['name']}"
            if qualified not in included_agents:
                available_agents.append({
                    "qualified": qualified,
                    "description": agent.get("description", ""),
                })

    return {"agents": available_agents}
```

Save to: `plugins/sdlc-workflows/scripts/team_inventory.py`

- [ ] **Step 4: Update import shim**

In `plugins_sdlc_workflows_scripts.py` — this file dynamically imports all `.py` files from `plugins/sdlc-workflows/scripts/`, so no change is needed. Verify it picks up the new module:

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -c "import plugins_sdlc_workflows_scripts as s; print(hasattr(s, 'team_inventory'))"`
Expected: `True`

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_team_inventory.py -v`
Expected: All 8 tests PASS

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-workflows/scripts/team_inventory.py tests/test_team_inventory.py
git commit -m "feat(inventory): add plugin agent and skill discovery for workforce management"
```

---

## Task 2: Fleet Status Reporting (`teams_status_report.py`)

Reads all team manifests, checks Docker image presence and staleness, maps workflow references. Pure data — no formatting.

**Files:**
- Create: `plugins/sdlc-workflows/scripts/teams_status_report.py`
- Create: `tests/test_teams_status_report.py`

- [ ] **Step 1: Write failing tests**

```python
#!/usr/bin/env python3
"""Tests for teams_status_report — fleet status data generation."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plugins_sdlc_workflows_scripts as scripts  # noqa: E402

teams_status_report = scripts.teams_status_report


def write_manifest(teams_dir: Path, name: str, **overrides: str) -> Path:
    """Write a minimal team manifest YAML."""
    fields = {
        "schema_version": '"1.0"',
        "name": name,
        "status": "active",
        "plugins": "[sdlc-core]",
        "agents": "[]",
        "skills": "[]",
        **overrides,
    }
    content = "\n".join(f"{k}: {v}" for k, v in fields.items())
    path = teams_dir / f"{name}.yaml"
    path.write_text(content)
    return path


class TestLoadManifests:
    def test_loads_all_yaml_files(self, tmp_path: Path) -> None:
        teams_dir = tmp_path / "teams"
        teams_dir.mkdir()
        write_manifest(teams_dir, "alpha")
        write_manifest(teams_dir, "beta")

        result = teams_status_report.load_manifests(teams_dir)
        assert len(result) == 2
        names = {m["name"] for m in result}
        assert names == {"alpha", "beta"}

    def test_skips_generated_subdir(self, tmp_path: Path) -> None:
        teams_dir = tmp_path / "teams"
        teams_dir.mkdir()
        write_manifest(teams_dir, "alpha")
        gen_dir = teams_dir / ".generated"
        gen_dir.mkdir()
        (gen_dir / "should-skip.yaml").write_text("name: skip")

        result = teams_status_report.load_manifests(teams_dir)
        assert len(result) == 1

    def test_empty_dir(self, tmp_path: Path) -> None:
        teams_dir = tmp_path / "teams"
        teams_dir.mkdir()
        result = teams_status_report.load_manifests(teams_dir)
        assert result == []


class TestStalenessCheck:
    def test_current_when_image_newer(self) -> None:
        manifest = {
            "name": "team-a",
            "updated": "2026-04-10T12:00:00",
            "image_built": "2026-04-12T12:00:00",
        }
        assert teams_status_report.staleness(manifest) == "current"

    def test_stale_when_manifest_newer(self) -> None:
        manifest = {
            "name": "team-a",
            "updated": "2026-04-12T12:00:00",
            "image_built": "2026-04-10T12:00:00",
        }
        assert teams_status_report.staleness(manifest) == "stale"

    def test_not_built_when_no_image_timestamp(self) -> None:
        manifest = {"name": "team-a", "updated": "2026-04-12T12:00:00"}
        assert teams_status_report.staleness(manifest) == "not_built"

    def test_current_when_equal(self) -> None:
        manifest = {
            "name": "team-a",
            "updated": "2026-04-12T12:00:00",
            "image_built": "2026-04-12T12:00:00",
        }
        assert teams_status_report.staleness(manifest) == "current"


class TestWorkflowUsage:
    def test_counts_team_references(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        (wf_dir / "review.yaml").write_text(
            "name: review\nnodes:\n"
            "  - id: sec\n    command: review\n    image: sdlc-worker:sec-team\n"
            "  - id: arch\n    command: review\n    image: sdlc-worker:sec-team\n"
        )
        (wf_dir / "dev.yaml").write_text(
            "name: dev\nnodes:\n"
            "  - id: impl\n    command: impl\n    image: sdlc-worker:dev-team\n"
        )

        usage = teams_status_report.workflow_usage(wf_dir)
        assert usage["sec-team"] == [
            {"workflow": "review", "node": "sec"},
            {"workflow": "review", "node": "arch"},
        ]
        assert usage["dev-team"] == [
            {"workflow": "dev", "node": "impl"},
        ]

    def test_empty_workflows_dir(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        assert teams_status_report.workflow_usage(wf_dir) == {}


class TestFleetReport:
    def test_assembles_complete_report(self, tmp_path: Path) -> None:
        teams_dir = tmp_path / "teams"
        teams_dir.mkdir()
        write_manifest(
            teams_dir,
            "sec-team",
            status="active",
            agents="[sdlc-core:architect]",
            skills="[sdlc-core:validate]",
            updated="2026-04-10T12:00:00",
            image_built="2026-04-12T12:00:00",
        )

        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        (wf_dir / "review.yaml").write_text(
            "name: review\nnodes:\n"
            "  - id: sec\n    command: review\n    image: sdlc-worker:sec-team\n"
        )

        report = teams_status_report.fleet_report(
            teams_dir=teams_dir,
            workflows_dir=wf_dir,
        )
        assert report["team_count"] == 1
        assert report["teams"][0]["name"] == "sec-team"
        assert report["teams"][0]["staleness"] == "current"
        assert report["teams"][0]["workflow_count"] == 1
```

Save to: `tests/test_teams_status_report.py`

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_teams_status_report.py -v 2>&1 | head -20`
Expected: FAIL — `teams_status_report` module not found

- [ ] **Step 3: Implement `teams_status_report.py`**

```python
#!/usr/bin/env python3
"""Generate fleet status data for delegation teams.

Reads team manifests from ``.archon/teams/``, checks staleness via
timestamp comparison, maps workflow references, and assembles a
structured report.

Public API
----------
load_manifests(teams_dir) -> list[dict]
staleness(manifest) -> str
workflow_usage(workflows_dir) -> dict[str, list[dict]]
fleet_report(teams_dir, workflows_dir) -> dict
"""

from __future__ import annotations

from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Manifest loading
# ---------------------------------------------------------------------------


def load_manifests(teams_dir: Path) -> list[dict]:
    """Load all team manifest YAML files from *teams_dir*.

    Skips subdirectories (e.g. ``.generated/``).
    """
    if not teams_dir.is_dir():
        return []
    manifests: list[dict] = []
    for yaml_file in sorted(teams_dir.glob("*.yaml")):
        with yaml_file.open() as fh:
            data = yaml.safe_load(fh)
        if isinstance(data, dict):
            manifests.append(data)
    return manifests


# ---------------------------------------------------------------------------
# Staleness
# ---------------------------------------------------------------------------


def staleness(manifest: dict) -> str:
    """Determine staleness of a team image.

    Returns ``"current"``, ``"stale"``, or ``"not_built"``.
    """
    updated = manifest.get("updated")
    image_built = manifest.get("image_built")

    if not image_built:
        return "not_built"

    # Compare as strings — ISO-8601 sorts lexicographically
    if str(updated) > str(image_built):
        return "stale"
    return "current"


# ---------------------------------------------------------------------------
# Workflow usage
# ---------------------------------------------------------------------------


def workflow_usage(
    workflows_dir: Path,
) -> dict[str, list[dict[str, str]]]:
    """Map team names to their workflow node references.

    Returns ``{team_name: [{"workflow": name, "node": node_id}]}``.
    """
    if not workflows_dir.is_dir():
        return {}

    usage: dict[str, list[dict[str, str]]] = {}

    for wf_path in sorted(workflows_dir.glob("*.yaml")):
        with wf_path.open() as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            continue

        wf_name = data.get("name", wf_path.stem)
        nodes = data.get("nodes", [])
        if not isinstance(nodes, list):
            continue

        for node in nodes:
            if not isinstance(node, dict):
                continue
            image = node.get("image")
            if not image or ":" not in str(image):
                continue
            _, _, team_name = str(image).partition(":")
            if team_name == "base":
                continue
            usage.setdefault(team_name, []).append({
                "workflow": str(wf_name),
                "node": str(node.get("id", "<unknown>")),
            })

    return usage


# ---------------------------------------------------------------------------
# Fleet report
# ---------------------------------------------------------------------------


def _count_list(manifest: dict, key: str) -> int:
    """Count items in a manifest list field, handling None/missing."""
    val = manifest.get(key)
    if isinstance(val, list):
        return len(val)
    return 0


def fleet_report(
    teams_dir: Path,
    workflows_dir: Path,
) -> dict:
    """Assemble a complete fleet status report.

    Returns a dict with ``team_count``, ``workflow_count``, and
    ``teams`` (list of per-team status dicts).
    """
    manifests = load_manifests(teams_dir)
    usage = workflow_usage(workflows_dir)

    teams: list[dict] = []
    for manifest in manifests:
        name = str(manifest.get("name", "unknown"))
        refs = usage.get(name, [])
        teams.append({
            "name": name,
            "status": str(manifest.get("status", "unknown")),
            "agent_count": _count_list(manifest, "agents"),
            "skill_count": _count_list(manifest, "skills"),
            "staleness": staleness(manifest),
            "workflow_count": len(refs),
            "workflow_refs": refs,
            "updated": manifest.get("updated"),
            "image_built": manifest.get("image_built"),
        })

    return {
        "team_count": len(teams),
        "workflow_count": len(set(
            ref["workflow"]
            for t in teams
            for ref in t["workflow_refs"]
        )),
        "teams": teams,
    }
```

Save to: `plugins/sdlc-workflows/scripts/teams_status_report.py`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_teams_status_report.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-workflows/scripts/teams_status_report.py tests/test_teams_status_report.py
git commit -m "feat(status): add fleet status reporting for delegation teams"
```

---

## Task 3: Coaching Signals (`coaching_signals.py`)

Analyzes the team fleet for actionable coaching recommendations, tiered by severity.

**Files:**
- Create: `plugins/sdlc-workflows/scripts/coaching_signals.py`
- Create: `tests/test_coaching_signals.py`

- [ ] **Step 1: Write failing tests**

```python
#!/usr/bin/env python3
"""Tests for coaching_signals — tiered coaching signal analysis."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plugins_sdlc_workflows_scripts as scripts  # noqa: E402

coaching_signals = scripts.coaching_signals


class TestSignalTiers:
    def test_stale_image_is_advisory(self) -> None:
        team = {
            "name": "dev-team",
            "status": "active",
            "staleness": "stale",
            "updated": "2026-04-12",
            "image_built": "2026-04-10",
            "workflow_count": 1,
        }
        signals = coaching_signals.analyse_team(team)
        stale = [s for s in signals if s["type"] == "stale_image"]
        assert len(stale) == 1
        assert stale[0]["tier"] == "advisory"

    def test_not_built_is_critical(self) -> None:
        team = {
            "name": "new-team",
            "status": "active",
            "staleness": "not_built",
            "workflow_count": 1,
        }
        signals = coaching_signals.analyse_team(team)
        not_built = [s for s in signals if s["type"] == "not_built"]
        assert len(not_built) == 1
        assert not_built[0]["tier"] == "critical"

    def test_unused_team_is_advisory(self) -> None:
        team = {
            "name": "orphan",
            "status": "active",
            "staleness": "current",
            "workflow_count": 0,
        }
        signals = coaching_signals.analyse_team(team)
        unused = [s for s in signals if s["type"] == "unused_team"]
        assert len(unused) == 1
        assert unused[0]["tier"] == "advisory"

    def test_healthy_team_has_no_signals(self) -> None:
        team = {
            "name": "healthy",
            "status": "active",
            "staleness": "current",
            "workflow_count": 2,
        }
        signals = coaching_signals.analyse_team(team)
        assert signals == []


class TestFleetSignals:
    def test_aggregates_across_teams(self) -> None:
        teams = [
            {
                "name": "stale-team",
                "status": "active",
                "staleness": "stale",
                "updated": "2026-04-12",
                "image_built": "2026-04-10",
                "workflow_count": 1,
            },
            {
                "name": "healthy",
                "status": "active",
                "staleness": "current",
                "workflow_count": 1,
            },
        ]
        result = coaching_signals.analyse_fleet(teams)
        assert result["critical"] == []
        assert len(result["advisory"]) == 1
        assert result["advisory"][0]["team"] == "stale-team"

    def test_empty_fleet(self) -> None:
        result = coaching_signals.analyse_fleet([])
        assert result == {"critical": [], "advisory": [], "informational": []}


class TestOverrideSignals:
    def test_frequent_override_detected(self, tmp_path: Path) -> None:
        """An agent extended 3+ times triggers a promotion signal."""
        log_path = tmp_path / "overrides.jsonl"
        lines = [
            '{"team": "dev", "agent": "sec:architect", "workflow": "feat"}',
            '{"team": "dev", "agent": "sec:architect", "workflow": "feat"}',
            '{"team": "dev", "agent": "sec:architect", "workflow": "fix"}',
        ]
        log_path.write_text("\n".join(lines) + "\n")

        signals = coaching_signals.analyse_overrides(log_path, threshold=3)
        assert len(signals) == 1
        assert signals[0]["type"] == "frequent_override"
        assert signals[0]["agent"] == "sec:architect"
        assert signals[0]["tier"] == "informational"

    def test_below_threshold_no_signal(self, tmp_path: Path) -> None:
        log_path = tmp_path / "overrides.jsonl"
        log_path.write_text('{"team": "dev", "agent": "sec:architect"}\n')
        signals = coaching_signals.analyse_overrides(log_path, threshold=3)
        assert signals == []

    def test_missing_log_file(self, tmp_path: Path) -> None:
        signals = coaching_signals.analyse_overrides(
            tmp_path / "nonexistent.jsonl"
        )
        assert signals == []
```

Save to: `tests/test_coaching_signals.py`

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_coaching_signals.py -v 2>&1 | head -20`
Expected: FAIL — `coaching_signals` module not found

- [ ] **Step 3: Implement `coaching_signals.py`**

```python
#!/usr/bin/env python3
"""Analyse delegation teams for tiered coaching signals.

Signal tiers:
- **critical** — action required (e.g. referenced team not built)
- **advisory** — worth reviewing (e.g. stale image, unused team)
- **informational** — patterns to be aware of (e.g. frequent overrides)

Public API
----------
analyse_team(team_data) -> list[dict]
analyse_fleet(teams) -> dict[str, list[dict]]
analyse_overrides(log_path, threshold=3) -> list[dict]
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


# ---------------------------------------------------------------------------
# Per-team analysis
# ---------------------------------------------------------------------------


def analyse_team(team: dict) -> list[dict]:
    """Produce coaching signals for a single team status dict.

    Parameters
    ----------
    team:
        A dict from ``teams_status_report.fleet_report()["teams"]``.

    Returns
    -------
    list[dict]
        Each signal has ``type``, ``tier``, ``team``, ``message`` keys.
    """
    signals: list[dict] = []
    name = team.get("name", "unknown")
    stale = team.get("staleness", "current")
    wf_count = team.get("workflow_count", 0)

    if stale == "not_built" and wf_count > 0:
        signals.append({
            "type": "not_built",
            "tier": "critical",
            "team": name,
            "message": (
                f"{name} is referenced by {wf_count} workflow(s) "
                "but has no image built"
            ),
        })
    elif stale == "not_built":
        signals.append({
            "type": "not_built",
            "tier": "critical",
            "team": name,
            "message": f"{name} has no image built",
        })

    if stale == "stale":
        signals.append({
            "type": "stale_image",
            "tier": "advisory",
            "team": name,
            "message": (
                f"{name} image is stale (manifest updated "
                f"{team.get('updated', '?')}, image built "
                f"{team.get('image_built', '?')})"
            ),
        })

    if wf_count == 0 and stale != "not_built":
        signals.append({
            "type": "unused_team",
            "tier": "advisory",
            "team": name,
            "message": (
                f"{name} is not referenced by any workflow — "
                "consider deleting or assigning to a workflow"
            ),
        })

    return signals


# ---------------------------------------------------------------------------
# Fleet analysis
# ---------------------------------------------------------------------------


def analyse_fleet(
    teams: list[dict],
) -> dict[str, list[dict]]:
    """Aggregate coaching signals across all teams.

    Returns ``{"critical": [...], "advisory": [...], "informational": [...]}``.
    """
    result: dict[str, list[dict]] = {
        "critical": [],
        "advisory": [],
        "informational": [],
    }

    for team in teams:
        for signal in analyse_team(team):
            tier = signal.get("tier", "informational")
            result.setdefault(tier, []).append(signal)

    return result


# ---------------------------------------------------------------------------
# Override analysis
# ---------------------------------------------------------------------------


def analyse_overrides(
    log_path: Path,
    threshold: int = 3,
) -> list[dict]:
    """Detect frequently overridden agents from the override log.

    Parameters
    ----------
    log_path:
        Path to ``overrides.jsonl`` (append-only JSONL file).
    threshold:
        Minimum number of overrides to trigger a signal.

    Returns
    -------
    list[dict]
        Coaching signals for frequently overridden agents.
    """
    if not log_path.exists():
        return []

    counter: Counter[str] = Counter()
    teams_for_agent: dict[str, set[str]] = {}

    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        agent = entry.get("agent", "")
        team = entry.get("team", "")
        if agent:
            counter[agent] += 1
            teams_for_agent.setdefault(agent, set()).add(team)

    signals: list[dict] = []
    for agent, count in counter.items():
        if count >= threshold:
            team_names = ", ".join(sorted(teams_for_agent.get(agent, set())))
            signals.append({
                "type": "frequent_override",
                "tier": "informational",
                "agent": agent,
                "count": count,
                "teams": team_names,
                "message": (
                    f"{agent} has been added via team_extend {count} times "
                    f"(on teams: {team_names}) — consider promoting to "
                    "a standing team member"
                ),
            })

    return signals
```

Save to: `plugins/sdlc-workflows/scripts/coaching_signals.py`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_coaching_signals.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-workflows/scripts/coaching_signals.py tests/test_coaching_signals.py
git commit -m "feat(coaching): add tiered coaching signal analysis for delegation teams"
```

---

## Task 4: Override Logger (`override_logger.py`)

Append-only JSONL logger for `team_extend` overrides. Coaching signals read this to detect frequent overrides.

**Files:**
- Create: `plugins/sdlc-workflows/scripts/override_logger.py`
- Create: `tests/test_override_logger.py`

- [ ] **Step 1: Write failing tests**

```python
#!/usr/bin/env python3
"""Tests for override_logger — team_extend override logging."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plugins_sdlc_workflows_scripts as scripts  # noqa: E402

override_logger = scripts.override_logger


class TestLogOverride:
    def test_appends_entry(self, tmp_path: Path) -> None:
        log_path = tmp_path / "overrides.jsonl"
        override_logger.log_override(
            log_path=log_path,
            team="dev-team",
            agent="sec:architect",
            workflow="feature-dev",
            node="implement",
        )
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["team"] == "dev-team"
        assert entry["agent"] == "sec:architect"
        assert entry["workflow"] == "feature-dev"
        assert entry["node"] == "implement"
        assert "timestamp" in entry

    def test_appends_multiple(self, tmp_path: Path) -> None:
        log_path = tmp_path / "overrides.jsonl"
        override_logger.log_override(log_path, "t1", "a1", "w1", "n1")
        override_logger.log_override(log_path, "t2", "a2", "w2", "n2")
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        log_path = tmp_path / "logs" / "deep" / "overrides.jsonl"
        override_logger.log_override(log_path, "t", "a", "w", "n")
        assert log_path.exists()


class TestReadOverrides:
    def test_reads_all_entries(self, tmp_path: Path) -> None:
        log_path = tmp_path / "overrides.jsonl"
        override_logger.log_override(log_path, "t1", "a1", "w1", "n1")
        override_logger.log_override(log_path, "t2", "a2", "w2", "n2")
        entries = override_logger.read_overrides(log_path)
        assert len(entries) == 2

    def test_empty_file(self, tmp_path: Path) -> None:
        log_path = tmp_path / "overrides.jsonl"
        log_path.write_text("")
        entries = override_logger.read_overrides(log_path)
        assert entries == []

    def test_missing_file(self, tmp_path: Path) -> None:
        entries = override_logger.read_overrides(tmp_path / "nope.jsonl")
        assert entries == []
```

Save to: `tests/test_override_logger.py`

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_override_logger.py -v 2>&1 | head -10`
Expected: FAIL — `override_logger` module not found

- [ ] **Step 3: Implement `override_logger.py`**

```python
#!/usr/bin/env python3
"""Append-only JSONL logger for team_extend overrides.

Each workflow run that uses ``team_extend`` logs one entry per extended
agent.  The coaching signals module reads this log to detect frequently
overridden agents that should be promoted to standing team members.

Public API
----------
log_override(log_path, team, agent, workflow, node) -> None
read_overrides(log_path) -> list[dict]
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def log_override(
    log_path: Path,
    team: str,
    agent: str,
    workflow: str,
    node: str,
) -> None:
    """Append a single override entry to the JSONL log.

    Creates parent directories and the file if they don't exist.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "team": team,
        "agent": agent,
        "workflow": workflow,
        "node": node,
    }

    with log_path.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_overrides(log_path: Path) -> list[dict]:
    """Read all override entries from the JSONL log.

    Returns an empty list if the file doesn't exist or is empty.
    """
    if not log_path.exists():
        return []

    entries: list[dict] = []
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries
```

Save to: `plugins/sdlc-workflows/scripts/override_logger.py`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_override_logger.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-workflows/scripts/override_logger.py tests/test_override_logger.py
git commit -m "feat(logging): add team_extend override logger for coaching signal detection"
```

---

## Task 5: `team_extend` Validation

Extend the existing `check_workflow_teams.py` to validate `team_extend` agent and skill references against the plugin inventory.

**Files:**
- Modify: `tools/validation/check_workflow_teams.py`
- Create: `tests/test_team_extend_validation.py`

- [ ] **Step 1: Write failing tests**

```python
#!/usr/bin/env python3
"""Tests for team_extend validation in workflow-team checker."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "validation"))
import check_workflow_teams  # noqa: E402


def write_yaml(parent: Path, name: str, content: str) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    path = parent / name
    path.write_text(content)
    return path


class TestTeamExtendValidation:
    def test_valid_extend_passes(self, tmp_path: Path) -> None:
        """team_extend with agents from an installed plugin passes."""
        write_yaml(
            tmp_path / "workflows",
            "dev.yaml",
            "name: dev\nnodes:\n"
            "  - id: impl\n    command: impl\n"
            "    image: sdlc-worker:dev-team\n"
            "    team_extend:\n"
            "      agents:\n"
            "        - sec-plugin:security-architect\n",
        )
        write_yaml(
            tmp_path / "teams",
            "dev-team.yaml",
            "schema_version: '1.0'\nname: dev-team\n"
            "status: active\nplugins: [sdlc-core]\n",
        )

        # Create a mock installed_plugins.json with the sec-plugin
        plugin_dir = tmp_path / "plugins" / "cache" / "mkt" / "sec-plugin" / "1.0"
        (plugin_dir / "agents").mkdir(parents=True)
        (plugin_dir / "agents" / "security-architect.md").write_text(
            "---\nname: security-architect\n---\n"
        )
        (plugin_dir / ".claude-plugin").mkdir(parents=True)
        (plugin_dir / ".claude-plugin" / "plugin.json").write_text("{}")

        installed_json = tmp_path / "installed_plugins.json"
        installed_json.write_text(json.dumps({
            "sec-plugin@mkt": {
                "name": "sec-plugin",
                "installPath": str(plugin_dir),
            },
        }))

        errors = check_workflow_teams.validate(
            workflows_dir=tmp_path / "workflows",
            teams_dir=tmp_path / "teams",
            installed_json=installed_json,
        )
        assert errors == []

    def test_extend_with_nonexistent_agent_fails(self, tmp_path: Path) -> None:
        """team_extend referencing an agent not in any plugin fails."""
        write_yaml(
            tmp_path / "workflows",
            "dev.yaml",
            "name: dev\nnodes:\n"
            "  - id: impl\n    command: impl\n"
            "    image: sdlc-worker:dev-team\n"
            "    team_extend:\n"
            "      agents:\n"
            "        - ghost-plugin:phantom-agent\n",
        )
        write_yaml(
            tmp_path / "teams",
            "dev-team.yaml",
            "schema_version: '1.0'\nname: dev-team\n"
            "status: active\nplugins: [sdlc-core]\n",
        )

        installed_json = tmp_path / "installed_plugins.json"
        installed_json.write_text(json.dumps({}))

        errors = check_workflow_teams.validate(
            workflows_dir=tmp_path / "workflows",
            teams_dir=tmp_path / "teams",
            installed_json=installed_json,
        )
        assert len(errors) == 1
        assert "ghost-plugin:phantom-agent" in errors[0]

    def test_no_team_extend_no_extra_validation(self, tmp_path: Path) -> None:
        """Nodes without team_extend are not affected by this check."""
        write_yaml(
            tmp_path / "workflows",
            "review.yaml",
            "name: review\nnodes:\n"
            "  - id: sec\n    command: review\n"
            "    image: sdlc-worker:sec-team\n",
        )
        write_yaml(
            tmp_path / "teams",
            "sec-team.yaml",
            "schema_version: '1.0'\nname: sec-team\n"
            "status: active\nplugins: [sdlc-core]\n",
        )

        errors = check_workflow_teams.validate(
            workflows_dir=tmp_path / "workflows",
            teams_dir=tmp_path / "teams",
        )
        assert errors == []
```

Save to: `tests/test_team_extend_validation.py`

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_team_extend_validation.py -v 2>&1 | head -20`
Expected: FAIL — `validate()` doesn't accept `installed_json` parameter yet

- [ ] **Step 3: Add `team_extend` validation to `check_workflow_teams.py`**

Add the `installed_json` parameter to `validate()` and extend the validation logic:

At the top of the file, after the existing imports, add:

```python
import sys

_scripts_dir = Path(__file__).resolve().parent.parent.parent / "plugins" / "sdlc-workflows" / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))
```

Modify the `extract_image_refs` function to also return `team_extend` data:

```python
def extract_image_refs(workflow_path: Path) -> list[tuple[str, str, str, dict]]:
    """Extract (node_id, image_value, team_name, team_extend) from workflow nodes."""
    refs: list[tuple[str, str, str, dict]] = []
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
        if ":" in str(image):
            _, _, team_name = str(image).partition(":")
            team_extend = node.get("team_extend", {})
            if not isinstance(team_extend, dict):
                team_extend = {}
            refs.append((str(node_id), str(image), team_name, team_extend))
    return refs
```

Modify `validate()` to accept `installed_json` and validate `team_extend` references:

```python
def validate(
    workflows_dir: Path,
    teams_dir: Path,
    installed_json: Path | None = None,
) -> list[str]:
    """Validate all workflow image references against team manifests."""
    errors: list[str] = []
    teams = load_team_manifests(teams_dir)

    if not workflows_dir.is_dir():
        return errors

    # Build plugin inventory for team_extend validation
    inventory: dict | None = None
    if installed_json is not None and installed_json.exists():
        try:
            import team_inventory
            inventory = team_inventory.discover_all(installed_json)
        except ImportError:
            pass

    for wf_path in sorted(workflows_dir.glob("*.yaml")):
        refs = extract_image_refs(wf_path)
        for node_id, image_value, team_name, team_extend in refs:
            if team_name == BASE_IMAGE_TAG:
                continue

            if team_name not in teams:
                errors.append(
                    f"{wf_path.name}: node '{node_id}' references image "
                    f"'{image_value}' but no team manifest found for "
                    f"'{team_name}'"
                )
                continue

            manifest = teams[team_name]
            status = manifest.get("status", "unknown")
            if status not in VALID_STATUSES:
                errors.append(
                    f"{wf_path.name}: node '{node_id}' references team "
                    f"'{team_name}' which has status '{status}' "
                    f"(inactive/decommissioned teams should not be "
                    f"referenced in workflows)"
                )

            # Validate team_extend references
            if team_extend and inventory is not None:
                extend_agents = team_extend.get("agents", [])
                if isinstance(extend_agents, list):
                    for agent_ref in extend_agents:
                        agent_str = str(agent_ref)
                        if ":" not in agent_str:
                            continue
                        plugin_key, _, agent_name = agent_str.partition(":")
                        bare_key = plugin_key.split("@")[0]
                        if bare_key not in inventory:
                            errors.append(
                                f"{wf_path.name}: node '{node_id}' "
                                f"team_extend references '{agent_str}' "
                                f"but plugin '{bare_key}' is not installed"
                            )

    return errors
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_team_extend_validation.py tests/test_workflow_team_validation.py -v`
Expected: All tests PASS (both new and existing)

- [ ] **Step 5: Commit**

```bash
git add tools/validation/check_workflow_teams.py tests/test_team_extend_validation.py
git commit -m "feat(validation): add team_extend reference validation to workflow checker"
```

---

## Task 6: `teams-status` Skill

The fleet visibility skill. Uses `teams_status_report.py` and `coaching_signals.py` to display team fleet status.

**Files:**
- Create: `plugins/sdlc-workflows/skills/teams-status/SKILL.md`

- [ ] **Step 1: Write the skill**

```markdown
---
name: teams-status
description: Fleet-level visibility for delegation teams. Shows roster, staleness, workflow usage, and coaching signals.
disable-model-invocation: false
argument-hint: "[--team <name>]"
---

# Delegation Teams Status

Show the status of all delegation teams or a single team in detail.

## Arguments

- (no arguments) — fleet view of all teams
- `--team <name>` — detailed view of a single team

## Steps

### 1. Load team data

Read all manifests from `.archon/teams/`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teams_status_report.py --teams-dir .archon/teams --workflows-dir .archon/workflows
```

If no manifests exist:
```
No delegation teams configured.
Create a team: /sdlc-workflows:manage-teams --create
```

### 2. Fleet view (no arguments)

Display a summary table of all teams:

```
Delegation workforce: N teams, M workflows

  Team                        Status   Agents  Skills  Image     Workflows
  ─────────────────────────── ──────── ─────── ─────── ───────── ─────────
  security-review-team        active   3       2       current   2
  dev-team-python             active   4       6       stale     3
  test-team                   active   1       2       not built 0
```

### 3. Coaching signals

After the table, display tiered coaching signals:

**Critical** (action required):
```
  ✗ test-team has no image built
```

**Advisory** (worth reviewing):
```
  ! dev-team-python image is stale (manifest updated 2026-04-12, image built 2026-04-10)
  ! test-team is not referenced by any workflow
```

**Informational** (patterns):
```
  ℹ sec:security-architect has been added via team_extend 5 times — consider promoting
```

Read override signals from `.archon/logs/overrides.jsonl` if it exists.

### 4. Plugin environment changes

Check if any installed plugins have been updated since the last full image build by comparing plugin directory modification times against the full image build timestamp.

```
  Plugin environment changes:
    + mongodb-plugin updated since last full image build
```

### 5. Single team detail (`--team <name>`)

Read `.archon/teams/<name>.yaml` and display:

```
Team: security-review-team
  Status:      active
  Updated:     2026-04-12
  Image built: 2026-04-12 (current)

  Plugins (3):
    sdlc-core, sdlc-team-security, sdlc-team-common

  Agents (3):
    sdlc-team-security:security-architect
    sdlc-team-security:compliance-auditor
    sdlc-team-common:solution-architect

  Skills (2):
    sdlc-core:validate
    sdlc-core:rules

  Context:
    CONSTITUTION.md, CLAUDE-CONTEXT-security.md

  Used by workflows:
    sdlc-parallel-review.yaml → node: security-review
    sdlc-commissioned-pipeline.yaml → node: security-gate

  Available but not included (from installed plugins):
    sdlc-team-security:data-privacy-officer
    sdlc-team-security:enforcement-strategy-advisor
```

Use `team_inventory.py` to compute the "available but not included" section:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/team_inventory.py --installed-json ~/.claude/plugins/installed_plugins.json --team-manifest .archon/teams/<name>.yaml
```

### 6. Footer

```
Run /sdlc-workflows:manage-teams --review for guided resolution.
```
```

Save to: `plugins/sdlc-workflows/skills/teams-status/SKILL.md`

- [ ] **Step 2: Add CLI to `teams_status_report.py`**

Append a `main()` function to `teams_status_report.py` for CLI use:

```python
def main() -> None:
    """CLI entry point for teams_status_report."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate fleet status report")
    parser.add_argument(
        "--teams-dir", type=Path, default=Path(".archon/teams"),
    )
    parser.add_argument(
        "--workflows-dir", type=Path, default=Path(".archon/workflows"),
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    import json as json_mod
    report = fleet_report(args.teams_dir, args.workflows_dir)
    if args.json:
        print(json_mod.dumps(report, indent=2, default=str))
    else:
        print(f"Teams: {report['team_count']}, Workflows: {report['workflow_count']}")
        for team in report["teams"]:
            print(
                f"  {team['name']:30s} {team['status']:10s} "
                f"{team['agent_count']} agents  {team['skill_count']} skills  "
                f"{team['staleness']:10s} {team['workflow_count']} wf"
            )


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Add CLI to `team_inventory.py`**

Append a `main()` function to `team_inventory.py` for CLI use:

```python
def main() -> None:
    """CLI entry point — print plugin inventory or available-but-not-included."""
    import argparse

    import yaml as yaml_mod

    parser = argparse.ArgumentParser(description="Plugin inventory discovery")
    parser.add_argument(
        "--installed-json",
        type=Path,
        default=Path.home() / ".claude" / "plugins" / "installed_plugins.json",
    )
    parser.add_argument(
        "--team-manifest",
        type=Path,
        default=None,
        help="Show available-but-not-included for a specific team manifest.",
    )
    args = parser.parse_args()

    import json as json_mod

    if args.team_manifest:
        with args.team_manifest.open() as fh:
            manifest = yaml_mod.safe_load(fh)
        plugins = [str(p) for p in manifest.get("plugins", [])]
        agents = [str(a) for a in manifest.get("agents", [])]
        result = available_but_not_included(args.installed_json, plugins, agents)
        print(json_mod.dumps(result, indent=2))
    else:
        inv = discover_all(args.installed_json)
        print(json_mod.dumps(inv, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Commit**

```bash
git add plugins/sdlc-workflows/skills/teams-status/SKILL.md \
    plugins/sdlc-workflows/scripts/teams_status_report.py \
    plugins/sdlc-workflows/scripts/team_inventory.py
git commit -m "feat(visibility): add teams-status skill for fleet visibility"
```

---

## Task 7: `manage-teams` Skill

The coaching skill. Guided Q&A for team lifecycle, with right-sizing guards and Level 1 adoption path.

**Files:**
- Create: `plugins/sdlc-workflows/skills/manage-teams/SKILL.md`

- [ ] **Step 1: Write the skill**

```markdown
---
name: manage-teams
description: Guided coaching for delegation team lifecycle — create, update, delete, review, and plan task formations. The primary interface for team management.
disable-model-invocation: false
argument-hint: "--create | --update <team> | --delete <team> | --review | --plan-task <description>"
---

# Manage Delegation Teams

Guided Q&A coaching for team lifecycle management. Follows the same
interactive pattern as `/sdlc-core:setup-team`.

## Arguments

- `--create` — create a new team with guided coaching
- `--update <team>` — update an existing team
- `--delete <team>` — delete a team (removes manifest + image)
- `--review` — review the entire delegation workforce with coaching signals
- `--plan-task "<description>"` — recommend a workflow + team formation for a task

## Lifecycle Model

Teams have a simple lifecycle:
- **Create** → manifest written to `.archon/teams/<name>.yaml` with `status: active`
- **Update** → manifest modified, `updated` timestamp set, image marked stale
- **Delete** → manifest file removed, Docker image removed, git history provides audit trail

There are no intermediate states. A manifest exists and is active, or it has been deleted. Git history provides the full audit trail for compliance.

## Mode: `--create`

### Step 1: Right-sizing check

Before creating a team, assess the project's delegation maturity:

```bash
# Count existing teams and workflows
ls .archon/teams/*.yaml 2>/dev/null | wc -l
ls .archon/workflows/*.yaml 2>/dev/null | wc -l
```

**If no teams exist (Level 1 adoption):**

```
You don't have any delegation teams yet.

For your first team, I recommend a general-purpose team that mirrors
your current Claude Code environment — all your installed plugins,
agents, and skills.

This gets you to your first delegated workflow run with one command.
You can specialise into multiple teams later as your needs become
clearer.

  (a) Create a general-purpose team (recommended for first-time setup)
  (b) Create a specialist team (I know what I want)
```

If (a): generate a manifest that includes ALL installed plugins, agents, and skills. Name it `general-purpose`. Skip the Q&A flow — go straight to manifest generation and offer to build the image.

**If teams exist but fewer teams than workflows:**

```
You have N team(s) and M workflow(s). Creating another team gives
you more granular control over which agents each workflow node uses.
```

Proceed to step 2.

**If teams >= 2× workflows:**

```
You have N team(s) but only M workflow(s). Consider whether you need
another team — more teams means more images to build and maintain.

  (a) Create the team anyway
  (b) Show me my current teams first (/sdlc-workflows:teams-status)
```

### Step 2: Team purpose

```
What is this team's purpose?
  (a) Code review (security, architecture, quality)
  (b) Implementation (feature development, bug fixes)
  (c) Testing (test coverage, integration testing)
  (d) Validation (linting, compliance, CI checks)
  (e) Something else — describe it
```

### Step 3: Agent selection

Based on the purpose, show available agents from installed plugins. Use `team_inventory.py` to discover what's installed:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/team_inventory.py \
    --installed-json ~/.claude/plugins/installed_plugins.json
```

Present agents relevant to the chosen purpose:

```
For a security review team, here are the available agents:

  From sdlc-team-security:
    security-architect     — OWASP, threat modelling
    compliance-auditor     — regulatory compliance
    data-privacy-officer   — PII/GDPR analysis

  From sdlc-team-common:
    solution-architect     — architectural context

  Which agents should be on this team?
    (a) All recommended (4 agents)
    (b) Let me pick individually
    (c) Start minimal — I'll add more later
```

Frame as "commonly paired with" rather than "everything available" — curated recommendations, not a full inventory.

### Step 4: Skill selection

Same pattern as agents. Show skills relevant to the team's purpose:

```
  Which skills should this team have?
    (a) Standard set: validate, rules (recommended)
    (b) Let me pick individually
    (c) Start minimal
```

### Step 5: Context files

```
  Which context files should this team load?
    (a) Standard: CONSTITUTION.md (recommended for all teams)
    (b) Add domain-specific context (show available CLAUDE-CONTEXT-*.md files)
    (c) None
```

### Step 6: Name the team

```
  Team name (lowercase, hyphens ok): security-review-team
```

Validate: must match `^[a-z0-9]+(?:[._-][a-z0-9]+)*$` (Docker tag component).

### Step 7: Write manifest and offer to build

Write the manifest to `.archon/teams/<name>.yaml`:

```yaml
schema_version: "1.0"
name: <name>
description: >
  <generated from purpose + selected agents>
status: active
created: <ISO-8601 now>
updated: <ISO-8601 now>

plugins:
  - <inferred from selected agents and skills>

agents:
  - <selected agents>

skills:
  - <selected skills>

context:
  - <selected context files>
```

Validate the manifest:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_team_manifest.py \
    .archon/teams/<name>.yaml \
    --installed-plugins ~/.claude/plugins/installed_plugins.json \
    --project-root .
```

Then offer to build:

```
Manifest written: .archon/teams/<name>.yaml

Build the team image now?
  (a) Yes — run /sdlc-workflows:deploy-team --name <name>
  (b) Later — I'll build when I'm ready
```

## Mode: `--update <team>`

### Step 1: Load current state

Read `.archon/teams/<team>.yaml`. Display current composition:

```
Updating team: security-review-team
  Current: 3 agents, 2 skills (image built 2026-04-10)

  What would you like to change?
    (a) Add agents or skills
    (b) Remove agents or skills
    (c) Change context files
    (d) Show commonly paired agents not on this team
    (e) Review the full manifest
```

### Step 2: Apply changes

For option (d), use `team_inventory.py` to find available agents in the team's plugins that aren't currently on the team.

After changes, update the manifest's `updated` timestamp and warn about staleness:

```
Manifest updated. The team image was built on 2026-04-10 but
the manifest has changed. Rebuild now?
  (a) Yes — run /sdlc-workflows:deploy-team --name <team>
  (b) Later
```

## Mode: `--delete <team>`

### Step 1: Check workflow references

```bash
python3 -c "
import sys; sys.path.insert(0, 'tools/validation')
import check_workflow_teams
refs = check_workflow_teams.extract_image_refs_for_team('.archon/workflows', '<team>')
print(refs)
"
```

### Step 2: Confirm and delete

```
Deleting team: legacy-review-team

  This team is referenced by 1 workflow:
    sdlc-parallel-review.yaml → node: legacy-check

  Deleting will:
    - Remove the manifest file (.archon/teams/legacy-review-team.yaml)
    - Remove the Docker image (sdlc-worker:legacy-review-team)
    - Git history retains the full audit trail

  You will need to update the workflow to remove or replace the reference.

  Proceed?
    (a) Yes — delete and show workflow references to fix
    (b) No — keep the team
```

If confirmed:
```bash
rm .archon/teams/<team>.yaml
rm -rf .archon/teams/.generated/<team>*
docker rmi sdlc-worker:<team> 2>/dev/null || true
```

## Mode: `--review`

### Step 1: Run fleet analysis

Internally invoke the same data as `/sdlc-workflows:teams-status` plus coaching signals:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/teams_status_report.py \
    --teams-dir .archon/teams --workflows-dir .archon/workflows --json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/coaching_signals.py \
    --teams-dir .archon/teams --workflows-dir .archon/workflows \
    --overrides .archon/logs/overrides.jsonl --json
```

### Step 2: Present coaching observations

```
Delegation workforce review:

  Your project has 4 active teams and 3 workflows.

  Observations:
    1. dev-team-python — image is stale (manifest updated 3 days
       after last build)
    2. test-team — not referenced by any workflow. Delete or assign?
    3. sec:security-architect was extended via team_extend 5 times
       on dev-team — consider adding to the standing team.

  Would you like to address any of these?
    (a) Rebuild stale images
    (b) Delete unused test-team
    (c) Add security-architect to dev-team-python
    (d) Skip for now
```

## Mode: `--plan-task "<description>"`

### Step 1: Analyse the task

Read the task description and the current roster (all manifests in `.archon/teams/`).

### Step 2: Recommend a formation

Recommend a workflow template + which teams map to which nodes:

```
Task: "Add OAuth2 authentication to the API"

Recommended formation:

  Workflow: sdlc-feature-development

  Node          Team                     Notes
  ──────────── ──────────────────────── ────────────────────
  plan          general-purpose          architecture + planning
  implement     dev-team-python          primary dev team
  validate      dev-team-python          validation pipeline
  security      security-review-team     auth = security-sensitive
  architecture  general-purpose          architecture review
  quality       general-purpose          code quality review
  synthesise    general-purpose          unified summary

  This task involves authentication, so I've included the
  security-review-team for the security review node.

  (a) Accept this formation
  (b) Modify — change team assignments
  (c) Show alternative workflow templates
  (d) Skip — I'll assign teams myself
```

### Step 3: Record the task plan

If accepted, write to `.archon/tasks/<slug>.yaml`:

```yaml
task: add-oauth2-authentication
created: 2026-04-14T10:00:00Z
workflow: sdlc-feature-development
formation:
  - node: plan
    team: general-purpose
  - node: implement
    team: dev-team-python
  - node: validate
    team: dev-team-python
  - node: security-review
    team: security-review-team
  - node: architecture-review
    team: general-purpose
  - node: code-quality-review
    team: general-purpose
  - node: synthesise
    team: general-purpose
```

```bash
mkdir -p .archon/tasks
```

### Step 4: Offer to run

```
Task plan saved: .archon/tasks/add-oauth2-authentication.yaml

Run this workflow now?
  (a) Yes — /sdlc-workflows:workflows-run sdlc-feature-development
  (b) Not yet
```
```

Save to: `plugins/sdlc-workflows/skills/manage-teams/SKILL.md`

- [ ] **Step 2: Commit**

```bash
git add plugins/sdlc-workflows/skills/manage-teams/SKILL.md
git commit -m "feat(coaching): add manage-teams skill with guided Q&A and play-calling"
```

---

## Task 8: Add CLI to `coaching_signals.py`

Add CLI entry point so the skill can invoke it directly.

**Files:**
- Modify: `plugins/sdlc-workflows/scripts/coaching_signals.py`

- [ ] **Step 1: Append CLI to `coaching_signals.py`**

```python
def main() -> None:
    """CLI entry point — run fleet + override analysis and print results."""
    import argparse

    import yaml as yaml_mod

    parser = argparse.ArgumentParser(description="Coaching signal analysis")
    parser.add_argument(
        "--teams-dir", type=Path, default=Path(".archon/teams"),
    )
    parser.add_argument(
        "--workflows-dir", type=Path, default=Path(".archon/workflows"),
    )
    parser.add_argument(
        "--overrides", type=Path, default=Path(".archon/logs/overrides.jsonl"),
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Build fleet data
    import sys as _sys

    _scripts_dir = Path(__file__).resolve().parent
    if str(_scripts_dir) not in _sys.path:
        _sys.path.insert(0, str(_scripts_dir))
    import teams_status_report

    report = teams_status_report.fleet_report(args.teams_dir, args.workflows_dir)
    fleet_result = analyse_fleet(report["teams"])
    override_result = analyse_overrides(args.overrides)

    combined = {
        "critical": fleet_result["critical"],
        "advisory": fleet_result["advisory"],
        "informational": fleet_result["informational"] + override_result,
    }

    import json as json_mod

    if args.json:
        print(json_mod.dumps(combined, indent=2))
    else:
        for tier in ("critical", "advisory", "informational"):
            if combined[tier]:
                print(f"\n{tier.upper()}:")
                for signal in combined[tier]:
                    print(f"  - {signal['message']}")
        if not any(combined.values()):
            print("No coaching signals — fleet is healthy.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run all tests to verify nothing is broken**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/test_coaching_signals.py tests/test_teams_status_report.py tests/test_team_inventory.py tests/test_override_logger.py -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add plugins/sdlc-workflows/scripts/coaching_signals.py
git commit -m "feat(coaching): add CLI entry point for coaching signal analysis"
```

---

## Task 9: Update CLAUDE.md and Documentation

Update the branch CLAUDE.md with Phase 3 skills.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add Phase 3 skills to Available Skills table**

Add these rows to the Available Skills table in CLAUDE.md:

```markdown
| `/sdlc-workflows:manage-teams` | Guided coaching for team lifecycle (create, update, delete, review, plan-task) |
| `/sdlc-workflows:teams-status` | Fleet visibility — team roster, staleness, workflow usage, coaching signals |
```

- [ ] **Step 2: Update Active Work section**

Update the EPIC #96 entry to reflect Phase 3 status:

```markdown
- **EPIC #96** — Containerised Claude Code workers. Phases 1-2 complete. Phase 3 (workforce management) in progress — manage-teams coaching, teams-status visibility, dynamic composition, play-calling. Branch `feature/96-sdlc-workflows`.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with Phase 3 workforce management skills"
```

---

## Task 10: Full Test Suite Run

Verify all tests pass — both new Phase 3 tests and existing Phase 2 tests.

**Files:** None (verification only)

- [ ] **Step 1: Run all tests**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS (existing Phase 2 tests + new Phase 3 tests)

- [ ] **Step 2: Run syntax validation**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python tools/validation/local-validation.py --syntax`
Expected: PASS

- [ ] **Step 3: Run technical debt check**

Run: `cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows && python tools/validation/check-technical-debt.py --threshold 0`
Expected: 0 issues

- [ ] **Step 4: Verify new scripts have no import issues**

Run:
```bash
cd /Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows
python -c "import plugins_sdlc_workflows_scripts as s; print('team_inventory:', hasattr(s, 'team_inventory')); print('teams_status_report:', hasattr(s, 'teams_status_report')); print('coaching_signals:', hasattr(s, 'coaching_signals')); print('override_logger:', hasattr(s, 'override_logger'))"
```
Expected: All `True`

---

## Summary

| Task | Component | New Tests | Commits |
|------|-----------|-----------|---------|
| 1 | `team_inventory.py` | 8 | 1 |
| 2 | `teams_status_report.py` | 9 | 1 |
| 3 | `coaching_signals.py` | 8 | 1 |
| 4 | `override_logger.py` | 6 | 1 |
| 5 | `team_extend` validation | 3 | 1 |
| 6 | `teams-status` SKILL.md | — | 1 |
| 7 | `manage-teams` SKILL.md | — | 1 |
| 8 | CLI entry points | — | 1 |
| 9 | CLAUDE.md updates | — | 1 |
| 10 | Full test suite verification | — | — |
| **Total** | **11 files created, 3 modified** | **34 tests** | **9 commits** |

### Review feedback disposition

| Finding | Disposition | Task |
|---------|------------|------|
| W7 Level 1 adoption path | `--create` offers general-purpose team when no teams exist | 7 |
| W8 Overcomplicated lifecycle | Simplified to active/deleted. Git = audit trail. | 7 |
| W4 team_extend unspecified | Prompt-context injection, validated pre-flight, override logged | 5, 7 |
| R9 Simplify lifecycle states | manage-teams only creates `active`, deletes by removing manifest | 7 |
| R10 Design Level 1 path | Single command → general-purpose team → first delegated run | 7 |
| R12 Specify team_extend mechanism | Concrete: agents added to node command prompt context | 5, 7 |
| Agile coach: tier coaching signals | critical / advisory / informational | 3, 6 |
| Agile coach: right-sizing guards | Team count vs workflow count check before create | 7 |
| Agile coach: pair play-calling with workflow selection | `--plan-task` recommends workflow template + team mapping | 7 |
| Agile coach: consolidate entry points | manage-teams auto-invokes deploy-team; stays separate for power users | 7 |
