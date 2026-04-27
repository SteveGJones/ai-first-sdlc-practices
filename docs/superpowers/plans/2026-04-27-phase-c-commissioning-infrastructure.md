# Phase C — Commissioning Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the bundle contract, commission skill, `.sdlc/team-config.json` schema extension, and sdlc-enforcer awareness so Programme (Phase D) and Assured (Phase E) bundles can be installed by `/sdlc-core:commission`.

**Architecture:** Mirror EPIC #164's pattern — Python helpers under `plugins/sdlc-core/scripts/commission/` (manifest, installer, recorder); skill `SKILL.md` orchestrates via bash snippets that invoke the helpers; mock bundle fixture validates the installer end-to-end before any real bundle exists. Schema fields reserved for Phase E (source/derived paths, known-violations, anaemic-context-detection, ID format) baked into the contract documentation but not validated this phase.

**Tech Stack:** Python 3.10+, pytest, JSON Schema (informally — `.sdlc/team-config.json` validated by hand-written checker, not a JSON Schema runtime), markdown-driven skills, sdlc-workflows containerised review (Phase B precedent).

**Spec:** `docs/feature-proposals/98-sdlc-commissioning-infrastructure.md`
**EPIC:** #178 (Joint Programme + Assured bundle delivery; this is Phase C)
**Branch:** `feature/sdlc-programme-assured-bundles` (continuing from Phase B)

---

## Critical lessons from prior EPICs (apply to every task)

1. **Plugin-dir vs root-source split** — when editing files mirrored into plugins, edit root source first, then `cp` to plugin-dir, then `python3 tools/validation/check-plugin-packaging.py` to verify before commit. See `memory/feedback_phase_a_plugin_dir_regression.md`.
2. **Test commits proof of completion** — every task ships a test that proves the work landed correctly. No "DONE" reports without evidence. See `memory/feedback_test_proves_completion.md`.
3. **Containerised review for design artefacts** — load-bearing design reviews (e.g. the bundle contract spec in Task 1) go through the `sdlc-workflows` containerised mechanism, not in-session Agent dispatch. See `memory/feedback_containerised_review_for_design_artefacts.md`.

---

## File structure

**New files:**

| File | Responsibility |
|---|---|
| `docs/architecture/option-bundle-contract.md` | Authoritative spec of what a bundle contains, file layout, manifest schema, plugin packaging shape, versioning, and reserved Phase E fields |
| `plugins/sdlc-core/scripts/commission/__init__.py` | Module marker |
| `plugins/sdlc-core/scripts/commission/manifest.py` | `BundleManifest` dataclass + parser + validator |
| `plugins/sdlc-core/scripts/commission/recorder.py` | `CommissioningRecord` dataclass + read/write `.sdlc/team-config.json` |
| `plugins/sdlc-core/scripts/commission/installer.py` | Install bundle contents (constitution, agents, skills, templates, validators) into project |
| `skills/commission/SKILL.md` | Commission skill — context detect, ask questions, recommend, install (root source) |
| `skills/commission/templates/sample-bundle/manifest.yaml` | Mock bundle manifest for testing |
| `skills/commission/templates/sample-bundle/CONSTITUTION.md` | Mock bundle constitution |
| `skills/commission/templates/sample-bundle/agents/sample-agent.md` | Mock agent in bundle |
| `skills/commission/templates/sample-bundle/skills/sample-skill/SKILL.md` | Mock skill in bundle |
| `tests/test_commission_manifest.py` | Manifest parsing + validation tests |
| `tests/test_commission_recorder.py` | Read/write `.sdlc/team-config.json` tests |
| `tests/test_commission_installer.py` | Bundle installation tests against mock fixture |
| `tests/test_commission_skill_integration.py` | End-to-end skill flow tests |
| `tests/fixtures/commissioning/empty-project/` | Project with no `.sdlc/team-config.json` |
| `tests/fixtures/commissioning/existing-project/.sdlc/team-config.json` | Project pre-dating commissioning (no `sdlc_option`) |

**Modified files:**

| File | Change |
|---|---|
| `release-mapping.yaml` | Add `commission` skill + `commission` scripts to `sdlc-core` |
| `CLAUDE-CORE.md` | Document commissioning concept + `.sdlc/team-config.json` schema |
| `agents/core/sdlc-enforcer.md` + plugin mirror | Read commissioning record, default to `single-team` if unset, log `sdlc_option` in compliance reports |

---

## Task 1: Bundle contract specification

**Files:**
- Create: `docs/architecture/option-bundle-contract.md`

**Why first**: every other task references the contract. Documenting the contract before implementing it forces the schema decisions to be explicit.

- [ ] **Step 1: Create the contract document**

Create `docs/architecture/option-bundle-contract.md`:

```markdown
# Option Bundle Contract

**Version:** 1
**Status:** Draft (Phase C of EPIC #178)
**Authoritative for:** Programme bundle (#103), Assured bundle (#104), and future bundles (Solo #100, Single-team #99)

---

## What a bundle is

An option bundle is a standalone Claude Code plugin that, when commissioned into a project, installs:

- A constitution (`CONSTITUTION.md`)
- Option-specific agents (markdown files with frontmatter)
- Option-specific skills (markdown files with frontmatter)
- Templates for required artefacts (feature proposal, retrospective, architecture documents, etc.)
- Validator configuration (which checks run at `--syntax`, `--quick`, `--pre-push`)

A bundle ships as a plugin alongside `sdlc-team-*` and `sdlc-lang-*` plugins in the marketplace. Plugin name convention: `sdlc-<option>` (e.g. `sdlc-programme`, `sdlc-assured`).

## File layout

A bundle plugin directory MUST contain:

\`\`\`
plugins/sdlc-<option>/
├── .claude-plugin/
│   └── plugin.json              # standard plugin metadata + bundle: true marker
├── manifest.yaml                # bundle manifest (this contract's primary artefact)
├── CONSTITUTION.md              # option-specific constitution
├── agents/                      # option-specific agents
├── skills/                      # option-specific skills
├── templates/                   # artefact templates
└── validators/                  # validator config (paths to run, thresholds)
\`\`\`

## Manifest schema (`manifest.yaml`)

Every bundle has a manifest at the bundle root with these fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | int | yes | Bundle contract schema version (currently `1`) |
| `name` | string | yes | Bundle name (`solo` / `single-team` / `programme` / `assured`) |
| `version` | semver string | yes | Bundle version (e.g. `0.1.0`) |
| `supported_levels` | list[string] | yes | One or more of `prototype` / `production` / `enterprise` |
| `description` | string | yes | One-line description |
| `depends_on` | list[string] | no | Other plugins this bundle depends on (default: `[sdlc-core]`) |
| `agents` | list[string] | no | Agent file basenames provided (e.g. `["sdlc-enforcer.md"]`) |
| `skills` | list[string] | no | Skill directory names provided (e.g. `["validate", "phase-review"]`) |
| `templates` | list[string] | no | Template file paths within `templates/` |
| `validators` | object | no | Validator configuration (see below) |

### Reserved Phase E fields

These fields are reserved in the schema; bundles MAY include them. Phase C does not validate their semantics; Phase E (Assured bundle) implements full validator support.

| Field | Type | Description |
|---|---|---|
| `decomposition_support` | bool | Whether the bundle supports declarative decomposition (Method 2 / Assured) |
| `id_format` | enum | `positional` (`P1.SP2.M3.REQ-007`) or `named` (`aisp.kb.kbsk.REQ-NNN`); applies when `decomposition_support: true` |
| `paths_split_supported` | bool | Whether the bundle's modules use the `source-paths` / `derived-paths` distinction |
| `known_violations_field` | bool | Whether the bundle's commissioning record carries a `known_violations` array |
| `anaemic_context_opt_out` | bool | Whether modules in this bundle may declare `anaemic-context-detection: suppressed` |

### Versioning rules

- **Bundle version** (`version` in manifest): semver. Patch = bug fix; minor = added validator; major = breaking schema or rule change.
- **Project record** (`option_bundle_version` in `.sdlc/team-config.json`): records exact bundle version installed.
- **Migration**: when a bundle's major version changes, the migration skill (#101, future sub-feature) handles upgrade. Phase C does not implement migration; bundles ship at major version 0 until migration lands.

## Reserved schema for `.sdlc/team-config.json`

Bundles populate the project's `.sdlc/team-config.json` with commissioning record fields:

| Field | Required | Populated by |
|---|---|---|
| `sdlc_option` | yes | Phase C — Solo / Single-team / Programme / Assured |
| `sdlc_level` | yes | Phase C — prototype / production / enterprise |
| `commissioned_at` | yes | Phase C — ISO 8601 timestamp |
| `commissioned_by` | yes | Phase C — username or "claude-agent" |
| `option_bundle_version` | yes | Phase C — bundle's manifest version |
| `commissioning_history` | yes | Phase C — array of past commissioning entries |
| `decomposition` | reserved | Phase E — pointer to `library/_decomposition.md` |
| `commissioning_options` | reserved | Phase E — per-bundle config (e.g. `regulatory_context`, `change_impact_gate_enabled`, `id_format`) |

Reserved fields appear in the schema but are NOT populated by Phase C bundles. Phase E bundles populate them when commissioning to Assured.

## Validator configuration

Bundles declare which validators run at each pipeline phase:

\`\`\`yaml
validators:
  syntax:
    - python_ast
  quick:
    - check_technical_debt
    - check_logging_compliance
  pre_push:
    - python_ast
    - check_technical_debt
    - check_logging_compliance
    - validate_architecture
    - run_tests
\`\`\`

Bundle commissioning writes this configuration to the project's pre-push hook configuration. Phase C uses a stub configuration; Phase D and E refine.

## Backward compatibility

Existing projects without `sdlc_option` in `.sdlc/team-config.json` continue to work unchanged. The sdlc-enforcer (modified in Phase C Task 12) silently defaults to `single-team` for any project where `sdlc_option` is unset.

## What Phase C does NOT cover

- Programme bundle implementation (Phase D, #103)
- Assured bundle implementation (Phase E, #104)
- Single-team and Solo bundle implementation (#99 / #100, separate sub-features)
- Migration between options (#101)
- The Method 2 schema fields' validator semantics (Phase E)

Phase C ships the contract + the commission skill + the recorder + the installer + sdlc-enforcer adaptation. Bundles get built on top.
```

- [ ] **Step 2: Run pre-push validation on the new doc**

```bash
python3 tools/validation/local-validation.py --quick
```

Expected: PASS, 0 errors.

- [ ] **Step 3: Commit**

```bash
git add docs/architecture/option-bundle-contract.md
git commit -m "$(cat <<'EOF'
docs(commissioning): bundle contract specification (Phase C task 1)

Authoritative spec for what an option bundle contains, file layout,
manifest schema, plugin packaging shape, versioning, reserved Phase E
fields, validator configuration, and backward compatibility behaviour.

Reserved schema fields for Phase E (Assured bundle) baked into the
contract documentation but not validated this phase: decomposition_support,
id_format, paths_split_supported, known_violations_field,
anaemic_context_opt_out (manifest), and decomposition,
commissioning_options (.sdlc/team-config.json).

Phase C task 1 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: BundleManifest module — dataclass and parser

**Files:**
- Create: `plugins/sdlc-core/scripts/commission/__init__.py`
- Create: `plugins/sdlc-core/scripts/commission/manifest.py`
- Create: `tests/test_commission_manifest.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_commission_manifest.py`:

```python
"""Tests for plugins.sdlc-core.scripts.commission.manifest."""
import json
from pathlib import Path

import pytest

from sdlc_core_scripts.commission.manifest import (
    BundleManifest,
    ManifestValidationError,
    parse_manifest,
)


def test_parse_manifest_minimal_valid(tmp_path: Path) -> None:
    """A manifest with only required fields parses successfully."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "schema_version: 1\n"
        "name: single-team\n"
        "version: 0.1.0\n"
        "supported_levels: [prototype, production]\n"
        "description: Standard team SDLC\n"
    )

    manifest = parse_manifest(manifest_path)

    assert isinstance(manifest, BundleManifest)
    assert manifest.name == "single-team"
    assert manifest.version == "0.1.0"
    assert manifest.supported_levels == ["prototype", "production"]
    assert manifest.depends_on == ["sdlc-core"]  # default
    assert manifest.agents == []
    assert manifest.skills == []


def test_parse_manifest_missing_required_field(tmp_path: Path) -> None:
    """Missing a required field raises ManifestValidationError."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "schema_version: 1\n"
        "name: single-team\n"
        "supported_levels: [prototype]\n"
        "description: missing version field\n"
    )

    with pytest.raises(ManifestValidationError, match="version"):
        parse_manifest(manifest_path)


def test_parse_manifest_unknown_option_name(tmp_path: Path) -> None:
    """An unknown option name raises ManifestValidationError."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "schema_version: 1\n"
        "name: not-a-real-option\n"
        "version: 0.1.0\n"
        "supported_levels: [production]\n"
        "description: Bogus\n"
    )

    with pytest.raises(ManifestValidationError, match="not-a-real-option"):
        parse_manifest(manifest_path)


def test_parse_manifest_unsupported_level(tmp_path: Path) -> None:
    """An unsupported level raises ManifestValidationError."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "schema_version: 1\n"
        "name: single-team\n"
        "version: 0.1.0\n"
        "supported_levels: [unrealistic-tier]\n"
        "description: Bogus\n"
    )

    with pytest.raises(ManifestValidationError, match="unrealistic-tier"):
        parse_manifest(manifest_path)


def test_parse_manifest_with_phase_e_reserved_fields(tmp_path: Path) -> None:
    """Reserved Phase E fields parse without validation but are preserved on the dataclass."""
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "schema_version: 1\n"
        "name: assured\n"
        "version: 0.1.0\n"
        "supported_levels: [enterprise]\n"
        "description: Assured bundle\n"
        "decomposition_support: true\n"
        "id_format: positional\n"
        "paths_split_supported: true\n"
        "known_violations_field: true\n"
        "anaemic_context_opt_out: true\n"
    )

    manifest = parse_manifest(manifest_path)

    assert manifest.decomposition_support is True
    assert manifest.id_format == "positional"
    assert manifest.paths_split_supported is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m pytest tests/test_commission_manifest.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'sdlc_core_scripts'" or similar import error.

- [ ] **Step 3: Create the module**

Create `plugins/sdlc-core/scripts/commission/__init__.py` (empty file).

Create `plugins/sdlc-core/scripts/commission/manifest.py`:

```python
"""Bundle manifest parsing and validation for the option bundle contract.

Reads `manifest.yaml` from a bundle directory and returns a validated
`BundleManifest`. Rejects manifests with missing required fields, unknown
option names, or unsupported levels.

Reserved Phase E fields (decomposition_support, id_format,
paths_split_supported, known_violations_field, anaemic_context_opt_out)
are preserved on the dataclass but not semantically validated; that's
Phase E's job.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


VALID_OPTIONS = {"solo", "single-team", "programme", "assured"}
VALID_LEVELS = {"prototype", "production", "enterprise"}
VALID_ID_FORMATS = {"positional", "named"}


class ManifestValidationError(Exception):
    """Raised when a bundle manifest fails validation."""


@dataclass
class BundleManifest:
    """Parsed and validated bundle manifest."""

    schema_version: int
    name: str
    version: str
    supported_levels: list[str]
    description: str
    depends_on: list[str] = field(default_factory=lambda: ["sdlc-core"])
    agents: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    templates: list[str] = field(default_factory=list)
    validators: dict = field(default_factory=dict)

    # Reserved Phase E fields
    decomposition_support: bool = False
    id_format: Optional[str] = None
    paths_split_supported: bool = False
    known_violations_field: bool = False
    anaemic_context_opt_out: bool = False


def parse_manifest(path: Path) -> BundleManifest:
    """Parse and validate a bundle manifest at the given path."""
    if not path.exists():
        raise ManifestValidationError(f"Manifest file not found: {path}")

    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ManifestValidationError(
            f"Manifest must be a YAML mapping at top level: {path}"
        )

    # Required fields
    for required in ("schema_version", "name", "version", "supported_levels", "description"):
        if required not in raw:
            raise ManifestValidationError(
                f"Manifest missing required field '{required}': {path}"
            )

    # Validate name
    if raw["name"] not in VALID_OPTIONS:
        raise ManifestValidationError(
            f"Manifest 'name' must be one of {sorted(VALID_OPTIONS)}, "
            f"got: {raw['name']}"
        )

    # Validate levels
    levels = raw["supported_levels"]
    if not isinstance(levels, list) or not levels:
        raise ManifestValidationError(
            f"Manifest 'supported_levels' must be a non-empty list: {path}"
        )
    for level in levels:
        if level not in VALID_LEVELS:
            raise ManifestValidationError(
                f"Manifest level '{level}' not in {sorted(VALID_LEVELS)}: {path}"
            )

    # Validate id_format if present
    if "id_format" in raw and raw["id_format"] not in VALID_ID_FORMATS:
        raise ManifestValidationError(
            f"Manifest 'id_format' must be one of {sorted(VALID_ID_FORMATS)}, "
            f"got: {raw['id_format']}"
        )

    return BundleManifest(
        schema_version=raw["schema_version"],
        name=raw["name"],
        version=raw["version"],
        supported_levels=raw["supported_levels"],
        description=raw["description"],
        depends_on=raw.get("depends_on", ["sdlc-core"]),
        agents=raw.get("agents", []),
        skills=raw.get("skills", []),
        templates=raw.get("templates", []),
        validators=raw.get("validators", {}),
        decomposition_support=raw.get("decomposition_support", False),
        id_format=raw.get("id_format"),
        paths_split_supported=raw.get("paths_split_supported", False),
        known_violations_field=raw.get("known_violations_field", False),
        anaemic_context_opt_out=raw.get("anaemic_context_opt_out", False),
    )
```

- [ ] **Step 4: Wire up the import path**

The kb tests use `sdlc_knowledge_base_scripts` as the module name. We need an equivalent for sdlc-core. Check the existing pattern:

```bash
ls plugins/sdlc-core/scripts/ 2>&1 || echo "no scripts dir yet"
ls plugins/sdlc-core/pyproject.toml 2>&1 || echo "no pyproject"
```

If `plugins/sdlc-core/pyproject.toml` does not exist, create one mirroring `plugins/sdlc-knowledge-base/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "sdlc-core-scripts"
version = "0.1.0"
description = "Python helpers shipped with sdlc-core plugin"
requires-python = ">=3.10"

[tool.setuptools.packages.find]
where = ["scripts"]
include = ["*"]

[tool.setuptools.package-dir]
"" = "scripts"
```

Then install editable:

```bash
pip install -e plugins/sdlc-core/
```

Verify the import works:

```bash
python3 -c "from sdlc_core_scripts.commission.manifest import BundleManifest; print(BundleManifest)"
```

Expected: `<class 'sdlc_core_scripts.commission.manifest.BundleManifest'>`

- [ ] **Step 5: Run test to verify it passes**

```bash
python3 -m pytest tests/test_commission_manifest.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-core/scripts/commission/ plugins/sdlc-core/pyproject.toml tests/test_commission_manifest.py
git commit -m "$(cat <<'EOF'
feat(commissioning): bundle manifest parser and validator (Phase C task 2)

Adds BundleManifest dataclass + parse_manifest function that reads a
YAML manifest from a bundle directory and validates required fields,
known option names, supported levels, and id_format choice.

Reserved Phase E fields (decomposition_support, id_format,
paths_split_supported, known_violations_field, anaemic_context_opt_out)
parse but are not semantically validated; that's Phase E's job.

5 unit tests covering minimal-valid, missing-required-field,
unknown-option-name, unsupported-level, and Phase E reserved fields.

New plugins/sdlc-core/pyproject.toml mirrors sdlc-knowledge-base's
package layout for editable install.

Phase C task 2 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: CommissioningRecord module — read/write `.sdlc/team-config.json`

**Files:**
- Create: `plugins/sdlc-core/scripts/commission/recorder.py`
- Create: `tests/test_commission_recorder.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_commission_recorder.py`:

```python
"""Tests for plugins.sdlc-core.scripts.commission.recorder."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from sdlc_core_scripts.commission.recorder import (
    CommissioningRecord,
    read_record,
    write_record,
    is_commissioned,
    default_option_for_uncommissioned,
)


def test_write_and_read_round_trip(tmp_path: Path) -> None:
    """Writing a record and reading it back returns equivalent data."""
    config_path = tmp_path / ".sdlc" / "team-config.json"
    record = CommissioningRecord(
        sdlc_option="single-team",
        sdlc_level="production",
        commissioned_at="2026-04-27T10:00:00Z",
        commissioned_by="claude-agent",
        option_bundle_version="0.1.0",
    )

    write_record(config_path, record)

    loaded = read_record(config_path)
    assert loaded.sdlc_option == "single-team"
    assert loaded.sdlc_level == "production"
    assert loaded.option_bundle_version == "0.1.0"
    assert len(loaded.commissioning_history) == 1


def test_write_preserves_existing_team_config_keys(tmp_path: Path) -> None:
    """Writing a record into an existing team-config.json keeps unrelated keys."""
    config_path = tmp_path / ".sdlc" / "team-config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(json.dumps({"existing_key": "existing_value", "team_name": "alpha"}))

    record = CommissioningRecord(
        sdlc_option="solo",
        sdlc_level="prototype",
        commissioned_at="2026-04-27T10:00:00Z",
        commissioned_by="alice",
        option_bundle_version="0.1.0",
    )
    write_record(config_path, record)

    loaded_raw = json.loads(config_path.read_text())
    assert loaded_raw["existing_key"] == "existing_value"
    assert loaded_raw["team_name"] == "alpha"
    assert loaded_raw["sdlc_option"] == "solo"


def test_write_appends_to_commissioning_history(tmp_path: Path) -> None:
    """Re-commissioning appends to history rather than replacing it."""
    config_path = tmp_path / ".sdlc" / "team-config.json"

    first = CommissioningRecord(
        sdlc_option="solo",
        sdlc_level="prototype",
        commissioned_at="2026-04-27T10:00:00Z",
        commissioned_by="alice",
        option_bundle_version="0.1.0",
    )
    write_record(config_path, first)

    second = CommissioningRecord(
        sdlc_option="single-team",
        sdlc_level="production",
        commissioned_at="2026-04-28T10:00:00Z",
        commissioned_by="alice",
        option_bundle_version="0.2.0",
    )
    write_record(config_path, second)

    loaded = read_record(config_path)
    assert loaded.sdlc_option == "single-team"  # latest wins
    assert len(loaded.commissioning_history) == 2
    assert loaded.commissioning_history[0]["sdlc_option"] == "solo"
    assert loaded.commissioning_history[1]["sdlc_option"] == "single-team"


def test_is_commissioned_true_when_record_exists(tmp_path: Path) -> None:
    """is_commissioned returns True when a record exists in the file."""
    config_path = tmp_path / ".sdlc" / "team-config.json"
    write_record(
        config_path,
        CommissioningRecord(
            sdlc_option="single-team",
            sdlc_level="production",
            commissioned_at="2026-04-27T10:00:00Z",
            commissioned_by="claude-agent",
            option_bundle_version="0.1.0",
        ),
    )

    assert is_commissioned(config_path) is True


def test_is_commissioned_false_when_file_absent(tmp_path: Path) -> None:
    """is_commissioned returns False when team-config.json does not exist."""
    config_path = tmp_path / ".sdlc" / "team-config.json"
    assert is_commissioned(config_path) is False


def test_is_commissioned_false_when_file_lacks_sdlc_option(tmp_path: Path) -> None:
    """is_commissioned returns False when team-config.json has no sdlc_option key."""
    config_path = tmp_path / ".sdlc" / "team-config.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(json.dumps({"team_name": "alpha"}))

    assert is_commissioned(config_path) is False


def test_default_option_for_uncommissioned_returns_single_team() -> None:
    """Backward compatibility: uncommissioned projects default to single-team."""
    assert default_option_for_uncommissioned() == "single-team"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m pytest tests/test_commission_recorder.py -v
```

Expected: FAIL with import error.

- [ ] **Step 3: Implement the recorder**

Create `plugins/sdlc-core/scripts/commission/recorder.py`:

```python
"""CommissioningRecord — read/write the `.sdlc/team-config.json` schema extension.

The recorder is filesystem-only; no database. Existing `.sdlc/team-config.json`
files (e.g. team_name, project metadata) are preserved on write. The
commissioning_history array accumulates each commissioning event; the
top-level fields reflect the latest commissioning.

Backward compatibility: projects without sdlc_option in their team-config.json
are NOT commissioned (per is_commissioned). Callers should use
default_option_for_uncommissioned() to get the safe default ("single-team").
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class CommissioningRecord:
    """One commissioning event."""

    sdlc_option: str
    sdlc_level: str
    commissioned_at: str  # ISO 8601 UTC
    commissioned_by: str
    option_bundle_version: str
    commissioning_history: list[dict[str, Any]] = field(default_factory=list)

    # Reserved Phase E fields (populated by Assured bundle commissioning)
    decomposition: Optional[Any] = None
    commissioning_options: dict[str, Any] = field(default_factory=dict)


def _to_history_entry(record: CommissioningRecord) -> dict[str, Any]:
    """Convert a record to a history-array entry (the per-event snapshot)."""
    return {
        "sdlc_option": record.sdlc_option,
        "sdlc_level": record.sdlc_level,
        "commissioned_at": record.commissioned_at,
        "commissioned_by": record.commissioned_by,
        "option_bundle_version": record.option_bundle_version,
    }


def read_record(path: Path) -> CommissioningRecord:
    """Read a CommissioningRecord from a `.sdlc/team-config.json` file."""
    if not path.exists():
        raise FileNotFoundError(f"team-config.json not found at {path}")

    raw = json.loads(path.read_text())
    return CommissioningRecord(
        sdlc_option=raw["sdlc_option"],
        sdlc_level=raw["sdlc_level"],
        commissioned_at=raw["commissioned_at"],
        commissioned_by=raw["commissioned_by"],
        option_bundle_version=raw["option_bundle_version"],
        commissioning_history=raw.get("commissioning_history", []),
        decomposition=raw.get("decomposition"),
        commissioning_options=raw.get("commissioning_options", {}),
    )


def write_record(path: Path, record: CommissioningRecord) -> None:
    """Write a CommissioningRecord to `.sdlc/team-config.json`.

    Preserves any existing keys unrelated to commissioning. Appends to
    commissioning_history if the file already had a record; otherwise starts
    a one-entry history.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        existing = json.loads(path.read_text())
    else:
        existing = {}

    history = existing.get("commissioning_history", [])
    history.append(_to_history_entry(record))

    merged = dict(existing)
    merged.update({
        "sdlc_option": record.sdlc_option,
        "sdlc_level": record.sdlc_level,
        "commissioned_at": record.commissioned_at,
        "commissioned_by": record.commissioned_by,
        "option_bundle_version": record.option_bundle_version,
        "commissioning_history": history,
    })
    if record.decomposition is not None:
        merged["decomposition"] = record.decomposition
    if record.commissioning_options:
        merged["commissioning_options"] = record.commissioning_options

    path.write_text(json.dumps(merged, indent=2) + "\n")


def is_commissioned(path: Path) -> bool:
    """Return True if the team-config.json at `path` contains a sdlc_option."""
    if not path.exists():
        return False
    try:
        raw = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    return "sdlc_option" in raw


def default_option_for_uncommissioned() -> str:
    """Backward-compat default for projects that haven't been commissioned."""
    return "single-team"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m pytest tests/test_commission_recorder.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-core/scripts/commission/recorder.py tests/test_commission_recorder.py
git commit -m "$(cat <<'EOF'
feat(commissioning): commissioning record reader/writer (Phase C task 3)

CommissioningRecord dataclass + read/write/is_commissioned/
default_option_for_uncommissioned helpers for the .sdlc/team-config.json
schema extension. Preserves existing team-config.json keys on write;
appends to commissioning_history on re-commissioning; defaults to
single-team for backward-compat with existing un-commissioned projects.

Reserved Phase E fields (decomposition, commissioning_options) supported
in the schema but populated only by Assured bundle commissioning.

7 unit tests covering write/read round-trip, key preservation, history
append, is_commissioned variants, and default backward-compat option.

Phase C task 3 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Mock bundle fixture for installer testing

**Files:**
- Create: `skills/commission/templates/sample-bundle/manifest.yaml`
- Create: `skills/commission/templates/sample-bundle/CONSTITUTION.md`
- Create: `skills/commission/templates/sample-bundle/agents/sample-agent.md`
- Create: `skills/commission/templates/sample-bundle/skills/sample-skill/SKILL.md`
- Create: `skills/commission/templates/sample-bundle/templates/feature-proposal.md`

**Why now**: The installer (Task 5) needs something to install. Building the mock bundle first gives Task 5 a real fixture rather than a stub.

- [ ] **Step 1: Create the sample bundle directory structure**

```bash
mkdir -p skills/commission/templates/sample-bundle/agents \
         skills/commission/templates/sample-bundle/skills/sample-skill \
         skills/commission/templates/sample-bundle/templates
```

- [ ] **Step 2: Create the manifest**

Create `skills/commission/templates/sample-bundle/manifest.yaml`:

```yaml
schema_version: 1
name: single-team
version: 0.0.1-mock
supported_levels: [prototype, production]
description: Mock bundle for Phase C installer testing
depends_on: [sdlc-core]
agents:
  - sample-agent.md
skills:
  - sample-skill
templates:
  - feature-proposal.md
validators:
  syntax: [python_ast]
  quick: [check_technical_debt]
  pre_push: [python_ast, check_technical_debt, run_tests]
```

- [ ] **Step 3: Create the bundle's constitution**

Create `skills/commission/templates/sample-bundle/CONSTITUTION.md`:

```markdown
# Sample Bundle Constitution (mock)

This is a mock constitution used by Phase C tests of the commissioning
installer. It is NOT a real SDLC option's constitution.

## Article 1 — Sample rule

This bundle requires nothing in particular. It exists to validate that
the installer copies a CONSTITUTION.md into the project.
```

- [ ] **Step 4: Create the sample agent**

Create `skills/commission/templates/sample-bundle/agents/sample-agent.md`:

```markdown
---
name: sample-agent
description: Mock agent shipped by the sample bundle for installer testing
model: sonnet
tools: Read, Glob, Grep
color: blue
examples:
  - '<example>This is a mock example for installer testing.</example>'
---

# Sample Agent

This is a mock agent. The installer copies it into the project's plugin
structure during commissioning.
```

- [ ] **Step 5: Create the sample skill**

Create `skills/commission/templates/sample-bundle/skills/sample-skill/SKILL.md`:

```markdown
---
name: sample-skill
description: Mock skill shipped by the sample bundle for installer testing
disable-model-invocation: false
---

# Sample Skill

This is a mock skill. The installer copies it into the project's plugin
structure during commissioning.

## Steps

1. This skill does nothing — it exists to validate the installer.
```

- [ ] **Step 6: Create the sample template**

Create `skills/commission/templates/sample-bundle/templates/feature-proposal.md`:

```markdown
# Feature Proposal: <Feature Name>

**Proposal Number:** <NNN>
**Status:** Draft
**Author:** <Your name>

---

## Summary

<One-paragraph summary>

## Motivation

<Why this feature exists>

## Proposed Solution

<How it will be built>

## Success Criteria

- [ ] <Criterion 1>
```

- [ ] **Step 7: Verify structure**

```bash
find skills/commission/templates/sample-bundle -type f | sort
```

Expected output:
```
skills/commission/templates/sample-bundle/CONSTITUTION.md
skills/commission/templates/sample-bundle/agents/sample-agent.md
skills/commission/templates/sample-bundle/manifest.yaml
skills/commission/templates/sample-bundle/skills/sample-skill/SKILL.md
skills/commission/templates/sample-bundle/templates/feature-proposal.md
```

- [ ] **Step 8: Commit**

```bash
git add skills/commission/templates/sample-bundle/
git commit -m "$(cat <<'EOF'
feat(commissioning): sample mock bundle fixture for installer tests (Phase C task 4)

Mock bundle at skills/commission/templates/sample-bundle/ with manifest,
constitution, one agent, one skill, one template. Used by Phase C task 5
(installer) and task 8 (skill integration tests) to validate the
installation flow without depending on a real bundle existing.

Phase C task 4 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Bundle installer module

**Files:**
- Create: `plugins/sdlc-core/scripts/commission/installer.py`
- Create: `tests/test_commission_installer.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_commission_installer.py`:

```python
"""Tests for plugins.sdlc-core.scripts.commission.installer."""
from pathlib import Path

import pytest

from sdlc_core_scripts.commission.installer import (
    BundleInstallationError,
    install_bundle,
    InstallationResult,
)
from sdlc_core_scripts.commission.manifest import parse_manifest


REPO_ROOT = Path(__file__).parent.parent
SAMPLE_BUNDLE = REPO_ROOT / "skills/commission/templates/sample-bundle"


def test_install_bundle_into_empty_project_creates_expected_files(tmp_path: Path) -> None:
    """Installing the sample bundle into an empty project creates the expected files."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")
    result = install_bundle(SAMPLE_BUNDLE, project_dir, manifest)

    assert isinstance(result, InstallationResult)
    assert (project_dir / "CONSTITUTION.md").exists()
    assert (project_dir / ".claude" / "agents" / "sample-agent.md").exists()
    assert (project_dir / ".claude" / "skills" / "sample-skill" / "SKILL.md").exists()
    assert (project_dir / ".sdlc" / "templates" / "feature-proposal.md").exists()


def test_install_bundle_returns_list_of_installed_paths(tmp_path: Path) -> None:
    """The installer returns a list of paths it created so the caller can audit."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")

    result = install_bundle(SAMPLE_BUNDLE, project_dir, manifest)

    assert len(result.installed_paths) >= 4  # constitution + agent + skill + template
    assert any(p.name == "CONSTITUTION.md" for p in result.installed_paths)
    assert any(p.name == "sample-agent.md" for p in result.installed_paths)


def test_install_bundle_does_not_overwrite_existing_constitution_without_flag(tmp_path: Path) -> None:
    """If CONSTITUTION.md already exists, installer refuses without overwrite=True."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "CONSTITUTION.md").write_text("# Existing constitution\n")

    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")

    with pytest.raises(BundleInstallationError, match="CONSTITUTION.md"):
        install_bundle(SAMPLE_BUNDLE, project_dir, manifest, overwrite=False)


def test_install_bundle_overwrite_true_replaces_existing_constitution(tmp_path: Path) -> None:
    """If overwrite=True, existing CONSTITUTION.md is replaced."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "CONSTITUTION.md").write_text("# Existing constitution\n")

    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")
    result = install_bundle(SAMPLE_BUNDLE, project_dir, manifest, overwrite=True)

    new_text = (project_dir / "CONSTITUTION.md").read_text()
    assert "Sample Bundle Constitution" in new_text


def test_install_bundle_missing_bundle_raises(tmp_path: Path) -> None:
    """Installing a bundle whose source dir does not exist raises."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    bogus_bundle = tmp_path / "no-such-bundle"

    with pytest.raises(BundleInstallationError, match="bundle directory not found"):
        install_bundle(
            bogus_bundle,
            project_dir,
            parse_manifest(SAMPLE_BUNDLE / "manifest.yaml"),
        )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m pytest tests/test_commission_installer.py -v
```

Expected: FAIL with import error.

- [ ] **Step 3: Implement the installer**

Create `plugins/sdlc-core/scripts/commission/installer.py`:

```python
"""Bundle installer — copies a bundle's contents into a project directory.

The installer copies:
- CONSTITUTION.md from bundle root → project root
- agents/<name>.md from bundle → project/.claude/agents/<name>.md
- skills/<name>/SKILL.md from bundle → project/.claude/skills/<name>/SKILL.md
- templates/<name>.md from bundle → project/.sdlc/templates/<name>.md

By default, refuses to overwrite an existing CONSTITUTION.md (the most
likely existing artefact). Other files are overwritten if present.
Pass overwrite=True to replace an existing constitution.

The installer does NOT modify .sdlc/team-config.json — that's the
recorder's job (called separately by the skill).
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .manifest import BundleManifest


class BundleInstallationError(Exception):
    """Raised when bundle installation cannot proceed."""


@dataclass
class InstallationResult:
    """Audit log of what install_bundle did."""

    bundle_name: str
    installed_paths: list[Path] = field(default_factory=list)
    skipped_paths: list[Path] = field(default_factory=list)


def install_bundle(
    bundle_dir: Path,
    project_dir: Path,
    manifest: BundleManifest,
    overwrite: bool = False,
) -> InstallationResult:
    """Install bundle contents into project_dir.

    Returns an InstallationResult listing every path created/overwritten.
    """
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        raise BundleInstallationError(f"bundle directory not found: {bundle_dir}")

    result = InstallationResult(bundle_name=manifest.name)

    # 1. Constitution
    src_constitution = bundle_dir / "CONSTITUTION.md"
    dst_constitution = project_dir / "CONSTITUTION.md"
    if src_constitution.exists():
        if dst_constitution.exists() and not overwrite:
            raise BundleInstallationError(
                f"CONSTITUTION.md already exists at {dst_constitution}; "
                "pass overwrite=True to replace"
            )
        shutil.copy2(src_constitution, dst_constitution)
        result.installed_paths.append(dst_constitution)

    # 2. Agents
    agents_src = bundle_dir / "agents"
    agents_dst = project_dir / ".claude" / "agents"
    for agent_name in manifest.agents:
        src = agents_src / agent_name
        dst = agents_dst / agent_name
        if not src.exists():
            raise BundleInstallationError(
                f"Manifest declares agent {agent_name} but file not found at {src}"
            )
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        result.installed_paths.append(dst)

    # 3. Skills
    skills_src = bundle_dir / "skills"
    skills_dst = project_dir / ".claude" / "skills"
    for skill_name in manifest.skills:
        src_dir = skills_src / skill_name
        dst_dir = skills_dst / skill_name
        if not src_dir.exists() or not src_dir.is_dir():
            raise BundleInstallationError(
                f"Manifest declares skill {skill_name} but directory not found at {src_dir}"
            )
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)
        # Track every file we created
        for installed in dst_dir.rglob("*"):
            if installed.is_file():
                result.installed_paths.append(installed)

    # 4. Templates
    templates_src = bundle_dir / "templates"
    templates_dst = project_dir / ".sdlc" / "templates"
    for template_name in manifest.templates:
        src = templates_src / template_name
        dst = templates_dst / template_name
        if not src.exists():
            raise BundleInstallationError(
                f"Manifest declares template {template_name} but file not found at {src}"
            )
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        result.installed_paths.append(dst)

    return result
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m pytest tests/test_commission_installer.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-core/scripts/commission/installer.py tests/test_commission_installer.py
git commit -m "$(cat <<'EOF'
feat(commissioning): bundle installer module (Phase C task 5)

install_bundle copies a bundle's CONSTITUTION.md, agents/<name>.md,
skills/<name>/SKILL.md, and templates/<name>.md into project root /
.claude/agents / .claude/skills / .sdlc/templates respectively. Refuses
to overwrite existing CONSTITUTION.md without overwrite=True flag;
other files are replaced if present. Returns InstallationResult listing
every path created/overwritten for audit.

5 unit tests covering happy-path install, audit-result correctness,
overwrite refusal, overwrite-true replacement, and missing-bundle error.
Tests run against the sample-bundle fixture from task 4.

Phase C task 5 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Commission skill — SKILL.md

**Files:**
- Create: `skills/commission/SKILL.md`

**Why this is a single-task chunk**: SKILL.md is a markdown procedure; it doesn't have unit tests in the same shape as Python modules. The integration test in Task 8 exercises the bash flow end-to-end.

- [ ] **Step 1: Create the skill**

Create `skills/commission/SKILL.md`:

```markdown
---
name: commission
description: Commission a project to an SDLC option bundle (solo / single-team / programme / assured). Asks structured questions, recommends an option × level, installs the bundle, and records the decision in .sdlc/team-config.json.
disable-model-invocation: true
argument-hint: "[--option <name>] [--level <level>] [--bundle-dir <path>]"
---

# Commission an SDLC Option Bundle

Walk a project through commissioning to one of four SDLC options:
**solo** (1-2 people, fast iteration), **single-team** (3-10, current
default), **programme** (11-50, formal phase gates), **assured**
(regulated industries with traceability).

## Pre-flight

```bash
PROJECT_DIR=$(pwd)
TEAM_CONFIG="$PROJECT_DIR/.sdlc/team-config.json"

# Check if already commissioned
python3 -c "
from pathlib import Path
from sdlc_core_scripts.commission.recorder import is_commissioned
print('COMMISSIONED' if is_commissioned(Path('$TEAM_CONFIG')) else 'FRESH')
"
```

If `COMMISSIONED`, ask the user to confirm re-commissioning before
proceeding. Show the existing record:

```bash
python3 -c "
from pathlib import Path
from sdlc_core_scripts.commission.recorder import read_record
r = read_record(Path('$TEAM_CONFIG'))
print(f'  Current option: {r.sdlc_option}')
print(f'  Current level: {r.sdlc_level}')
print(f'  Bundle version: {r.option_bundle_version}')
print(f'  Commissioned: {r.commissioned_at} by {r.commissioned_by}')
"
```

## Questions (ask one at a time, brief)

Skip any question whose answer is in arguments (`--option`, `--level`).

1. **Team size** — 1-2 / 3-10 / 11-50 / 50+
2. **Blast radius** of a defect — low / moderate / high / severe
3. **Regulatory burden** — none / low / moderate / high
4. **Specification maturity** — emergent / mixed / contract-first / formal
5. **Time-to-market pressure** — very high / high / moderate / low

If user has set arguments overriding all of these, skip directly to recommendation.

## Recommendation logic

```
team-size 1-2 + low blast radius          → solo / prototype
team-size 3-10 + moderate blast radius    → single-team / production
team-size 11-50 + formal spec             → programme / production
any size + high regulatory burden         → assured / enterprise
```

If two recommendations tie, prefer the simpler one (solo > single-team > programme > assured).

Show the recommendation with rationale (which questions drove it).

## Override

User may override the recommendation. If the override is unusual
(e.g. solo + enterprise, programme + prototype), warn but never block:

```
WARNING: solo + enterprise is unusual. Solo bundles are designed for
1-2 person projects with fast iteration; enterprise level mandates
formal architecture documents. Are you sure?  (y/N)
```

The user knows things the framework doesn't.

## Install

```bash
BUNDLE_DIR="${ARG_BUNDLE_DIR:-skills/commission/templates/sample-bundle}"

python3 << 'EOF'
import json
from datetime import datetime, timezone
from pathlib import Path
from sdlc_core_scripts.commission.manifest import parse_manifest
from sdlc_core_scripts.commission.installer import install_bundle
from sdlc_core_scripts.commission.recorder import CommissioningRecord, write_record, is_commissioned

bundle_dir = Path("$BUNDLE_DIR")
project_dir = Path("$PROJECT_DIR")
team_config = Path("$TEAM_CONFIG")

manifest = parse_manifest(bundle_dir / "manifest.yaml")

# Ask user before overwrite if constitution exists and project is uncommissioned
constitution = project_dir / "CONSTITUTION.md"
overwrite = is_commissioned(team_config)  # re-commissioning ⇒ overwrite OK
if constitution.exists() and not overwrite:
    print(f"WARNING: {constitution} exists and project is uncommissioned.")
    print("  Continuing will replace the existing constitution.")
    response = input("  Proceed? [y/N] ")
    if response.lower() != "y":
        print("Aborted.")
        raise SystemExit(1)
    overwrite = True

result = install_bundle(bundle_dir, project_dir, manifest, overwrite=overwrite)
print(f"Installed {len(result.installed_paths)} files:")
for p in result.installed_paths:
    print(f"  {p.relative_to(project_dir)}")

record = CommissioningRecord(
    sdlc_option="<USER_CHOSEN_OPTION>",
    sdlc_level="<USER_CHOSEN_LEVEL>",
    commissioned_at=datetime.now(timezone.utc).isoformat(),
    commissioned_by="claude-agent",
    option_bundle_version=manifest.version,
)
write_record(team_config, record)
print(f"Commissioned: {record.sdlc_option} / {record.sdlc_level} / {record.option_bundle_version}")
EOF
```

Substitute `<USER_CHOSEN_OPTION>` and `<USER_CHOSEN_LEVEL>` based on
the recommendation + user override outcome.

## Done

Report:

- Bundle installed: `<option> v<version>`
- Files written: count + list
- Commissioning record at: `.sdlc/team-config.json`
- Next step: run `/sdlc-core:validate --quick` to confirm the bundle's
  validators run cleanly against the project.

## Model selection

This skill is mostly mechanical (file copies, JSON writes). A smaller
or faster model is sufficient. The recommendation logic is a
deterministic table lookup, not deep reasoning.
```

- [ ] **Step 2: Mirror to plugin-dir + verify packaging**

```bash
mkdir -p plugins/sdlc-core/skills/commission
cp skills/commission/SKILL.md plugins/sdlc-core/skills/commission/SKILL.md
mkdir -p plugins/sdlc-core/skills/commission/templates
cp -r skills/commission/templates/sample-bundle plugins/sdlc-core/skills/commission/templates/
```

Update `release-mapping.yaml` to include the commission skill. Find the `sdlc-core.skills` section and add:

```yaml
    - source: skills/commission/SKILL.md
    - source: skills/commission/templates/sample-bundle/manifest.yaml
    - source: skills/commission/templates/sample-bundle/CONSTITUTION.md
    - source: skills/commission/templates/sample-bundle/agents/sample-agent.md
    - source: skills/commission/templates/sample-bundle/skills/sample-skill/SKILL.md
    - source: skills/commission/templates/sample-bundle/templates/feature-proposal.md
```

Also add the scripts:

```yaml
  scripts:
    - source: plugins/sdlc-core/scripts/commission/__init__.py
    - source: plugins/sdlc-core/scripts/commission/manifest.py
    - source: plugins/sdlc-core/scripts/commission/installer.py
    - source: plugins/sdlc-core/scripts/commission/recorder.py
```

(If `sdlc-core.scripts` doesn't exist as a key, add it. Mirror the `sdlc-knowledge-base.scripts` shape.)

Verify packaging:

```bash
python3 tools/validation/check-plugin-packaging.py
```

Expected: PASSED, 12 plugins verified.

- [ ] **Step 3: Commit**

```bash
git add skills/commission/SKILL.md plugins/sdlc-core/skills/commission/ release-mapping.yaml
git commit -m "$(cat <<'EOF'
feat(commissioning): commission skill — SKILL.md + plugin mirror (Phase C task 6)

Adds /sdlc-core:commission skill that:
- Detects whether the project is already commissioned
- Asks structured questions (5 max) covering team-size, blast-radius,
  regulatory-burden, spec-maturity, time-to-market
- Recommends an option × level using a deterministic table lookup
- Lets the user override with warning (never blocks)
- Installs the chosen bundle via install_bundle helper
- Writes the commissioning record via write_record helper

Bundle source defaults to the sample-bundle fixture from task 4 so the
skill is testable end-to-end before any real bundle exists. The
release-mapping.yaml now includes the commission skill, sample-bundle
templates, and the scripts/commission/* helpers under sdlc-core.

Phase C task 6 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Update CLAUDE-CORE.md with commissioning concept and schema

**Files:**
- Modify: `CLAUDE-CORE.md`

- [ ] **Step 1: Read current CLAUDE-CORE.md**

```bash
grep -n "team-config" CLAUDE-CORE.md || echo "no existing reference"
wc -l CLAUDE-CORE.md
```

- [ ] **Step 2: Add the commissioning section**

Find a sensible insertion point (after the Constitution section or near other top-level concept sections). Insert:

```markdown
## Commissioning

Projects commission to one SDLC **option** at the start of work. Options express different *shapes* of SDLC, not different stringency levels:

- **solo** — 1-2 person projects, fast iteration, minimal ceremony
- **single-team** — 3-10 person product teams, the framework's default
- **programme** — 11-50 person multi-team programmes with formal phase gates
- **assured** — regulated-industry work with bidirectional traceability

Each option ships as a **bundle** (a Claude Code plugin) installed by `/sdlc-core:commission`. The commissioning decision is recorded in `.sdlc/team-config.json` and read on every sdlc-enforcer invocation.

### `.sdlc/team-config.json` commissioning fields

| Field | Required | Description |
|---|---|---|
| `sdlc_option` | yes | One of `solo` / `single-team` / `programme` / `assured` |
| `sdlc_level` | yes | One of `prototype` / `production` / `enterprise` |
| `commissioned_at` | yes | ISO 8601 UTC timestamp |
| `commissioned_by` | yes | Username or "claude-agent" |
| `option_bundle_version` | yes | Bundle's manifest version (semver) |
| `commissioning_history` | yes | Array of past commissioning entries |
| `decomposition` | reserved | Phase E (Assured only) — pointer to `library/_decomposition.md` |
| `commissioning_options` | reserved | Phase E (Assured only) — per-bundle config knobs |

### Backward compatibility

Projects without `sdlc_option` in `.sdlc/team-config.json` continue to work unchanged. The sdlc-enforcer silently defaults to `single-team` when `sdlc_option` is unset. No project must do anything to keep working when commissioning ships.

### See also

- Bundle contract: `docs/architecture/option-bundle-contract.md`
- Commission skill: `/sdlc-core:commission`
- EPIC #178 — joint Programme + Assured delivery
```

- [ ] **Step 3: Verify reference to bundle contract is correct**

```bash
ls docs/architecture/option-bundle-contract.md && echo "OK"
```

Expected: `OK` (created in Task 1).

- [ ] **Step 4: Run validation**

```bash
python3 tools/validation/local-validation.py --quick
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE-CORE.md
git commit -m "$(cat <<'EOF'
docs(commissioning): document commissioning concept and team-config.json schema (Phase C task 7)

Adds a Commissioning section to CLAUDE-CORE.md describing the four
options (solo / single-team / programme / assured), the commissioning
fields in .sdlc/team-config.json, and the backward-compat default
(single-team for uncommissioned projects).

Phase C task 7 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: End-to-end skill integration test

**Files:**
- Create: `tests/test_commission_skill_integration.py`
- Create: `tests/fixtures/commissioning/empty-project/.gitkeep`
- Create: `tests/fixtures/commissioning/existing-project/.sdlc/team-config.json`

- [ ] **Step 1: Set up fixtures**

```bash
mkdir -p tests/fixtures/commissioning/empty-project
touch tests/fixtures/commissioning/empty-project/.gitkeep

mkdir -p tests/fixtures/commissioning/existing-project/.sdlc
cat > tests/fixtures/commissioning/existing-project/.sdlc/team-config.json << 'EOF'
{
  "team_name": "alpha",
  "created": "2025-12-01T00:00:00Z"
}
EOF
```

- [ ] **Step 2: Write the integration tests**

Create `tests/test_commission_skill_integration.py`:

```python
"""End-to-end tests of the commission flow against the sample bundle.

Each test simulates the bash flow inside skills/commission/SKILL.md
by invoking the same Python helpers (parse_manifest → install_bundle →
write_record) that the skill's bash snippets call. This catches gaps
between the helpers and the skill flow.
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from sdlc_core_scripts.commission.installer import install_bundle
from sdlc_core_scripts.commission.manifest import parse_manifest
from sdlc_core_scripts.commission.recorder import (
    CommissioningRecord,
    is_commissioned,
    read_record,
    write_record,
)


REPO_ROOT = Path(__file__).parent.parent
SAMPLE_BUNDLE = REPO_ROOT / "skills/commission/templates/sample-bundle"
EMPTY_FIXTURE = REPO_ROOT / "tests/fixtures/commissioning/empty-project"
EXISTING_FIXTURE = REPO_ROOT / "tests/fixtures/commissioning/existing-project"


def test_fresh_project_full_commission_flow(tmp_path: Path) -> None:
    """A fresh project commissions cleanly: install bundle + write record."""
    project = tmp_path / "fresh"
    shutil.copytree(EMPTY_FIXTURE, project)

    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")

    assert is_commissioned(project / ".sdlc" / "team-config.json") is False

    result = install_bundle(SAMPLE_BUNDLE, project, manifest)
    record = CommissioningRecord(
        sdlc_option="single-team",
        sdlc_level="production",
        commissioned_at=datetime.now(timezone.utc).isoformat(),
        commissioned_by="claude-agent",
        option_bundle_version=manifest.version,
    )
    write_record(project / ".sdlc" / "team-config.json", record)

    # Verify final state
    assert (project / "CONSTITUTION.md").exists()
    assert (project / ".claude" / "agents" / "sample-agent.md").exists()
    assert is_commissioned(project / ".sdlc" / "team-config.json") is True

    loaded = read_record(project / ".sdlc" / "team-config.json")
    assert loaded.sdlc_option == "single-team"
    assert loaded.option_bundle_version == "0.0.1-mock"


def test_existing_project_keeps_unrelated_team_config_keys(tmp_path: Path) -> None:
    """A project with an existing team-config.json keeps its non-commissioning keys."""
    project = tmp_path / "existing"
    shutil.copytree(EXISTING_FIXTURE, project)

    # Pre-existing keys
    pre_config = json.loads((project / ".sdlc" / "team-config.json").read_text())
    assert pre_config["team_name"] == "alpha"

    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")
    install_bundle(SAMPLE_BUNDLE, project, manifest, overwrite=True)
    write_record(
        project / ".sdlc" / "team-config.json",
        CommissioningRecord(
            sdlc_option="single-team",
            sdlc_level="production",
            commissioned_at="2026-04-27T12:00:00Z",
            commissioned_by="claude-agent",
            option_bundle_version=manifest.version,
        ),
    )

    post_config = json.loads((project / ".sdlc" / "team-config.json").read_text())
    assert post_config["team_name"] == "alpha"  # unrelated key preserved
    assert post_config["sdlc_option"] == "single-team"
    assert post_config["created"] == "2025-12-01T00:00:00Z"


def test_re_commissioning_appends_to_history(tmp_path: Path) -> None:
    """Re-commissioning to a different option appends to commissioning_history."""
    project = tmp_path / "rec"
    shutil.copytree(EMPTY_FIXTURE, project)
    manifest = parse_manifest(SAMPLE_BUNDLE / "manifest.yaml")

    # First commission
    install_bundle(SAMPLE_BUNDLE, project, manifest)
    write_record(
        project / ".sdlc" / "team-config.json",
        CommissioningRecord(
            sdlc_option="solo",
            sdlc_level="prototype",
            commissioned_at="2026-04-27T10:00:00Z",
            commissioned_by="alice",
            option_bundle_version=manifest.version,
        ),
    )

    # Re-commission
    write_record(
        project / ".sdlc" / "team-config.json",
        CommissioningRecord(
            sdlc_option="single-team",
            sdlc_level="production",
            commissioned_at="2026-04-28T10:00:00Z",
            commissioned_by="alice",
            option_bundle_version=manifest.version,
        ),
    )

    record = read_record(project / ".sdlc" / "team-config.json")
    assert record.sdlc_option == "single-team"  # latest wins
    assert len(record.commissioning_history) == 2
    assert record.commissioning_history[0]["sdlc_option"] == "solo"
    assert record.commissioning_history[1]["sdlc_option"] == "single-team"
```

- [ ] **Step 3: Run integration tests**

```bash
python3 -m pytest tests/test_commission_skill_integration.py -v
```

Expected: 3 passed.

- [ ] **Step 4: Run all commission tests**

```bash
python3 -m pytest tests/test_commission_*.py -v
```

Expected: 20 passed (5 manifest + 7 recorder + 5 installer + 3 integration).

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/commissioning/ tests/test_commission_skill_integration.py
git commit -m "$(cat <<'EOF'
test(commissioning): end-to-end skill integration tests (Phase C task 8)

Three integration tests against tests/fixtures/commissioning/ that
exercise the full skill flow (parse_manifest → install_bundle →
write_record):

- test_fresh_project_full_commission_flow: empty project commissions cleanly
- test_existing_project_keeps_unrelated_team_config_keys: pre-existing
  team-config.json keys (team_name, created) are preserved on commission
- test_re_commissioning_appends_to_history: re-commissioning to a
  different option keeps both entries in commissioning_history

Phase C total commission test count: 20 (5 manifest + 7 recorder +
5 installer + 3 integration). All passing.

Phase C task 8 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: sdlc-enforcer reads commissioning record

**Files:**
- Modify: `agents/core/sdlc-enforcer.md` + plugin mirror

- [ ] **Step 1: Read the current sdlc-enforcer**

```bash
head -30 agents/core/sdlc-enforcer.md
```

- [ ] **Step 2: Add the commissioning-aware section**

Find a section near the top describing what the enforcer reads. Add:

```markdown
## Read commissioning record on every invocation

Before applying rules, read the project's commissioning record:

\`\`\`bash
python3 -c "
from pathlib import Path
from sdlc_core_scripts.commission.recorder import (
    is_commissioned,
    read_record,
    default_option_for_uncommissioned,
)

team_config = Path('.sdlc/team-config.json')
if is_commissioned(team_config):
    record = read_record(team_config)
    print(f'sdlc_option={record.sdlc_option}')
    print(f'sdlc_level={record.sdlc_level}')
    print(f'option_bundle_version={record.option_bundle_version}')
else:
    print(f'sdlc_option={default_option_for_uncommissioned()}')
    print('sdlc_level=production')
    print('option_bundle_version=unset')
"
\`\`\`

The commissioning record drives:
- Which constitution applies (the project's `CONSTITUTION.md`, populated by the bundle)
- Which validators run at each pipeline stage (per the bundle's `validators` config)
- Which option-specific rules to enforce (per the bundle's agents and skills)

**Backward compatibility**: projects without `sdlc_option` continue to work as before, defaulting to `single-team` behaviour. No project must take action to keep working when commissioning ships.

## Log commissioning state in compliance reports

When the enforcer produces a compliance report (e.g. for a feature branch review), include the project's `sdlc_option` and `option_bundle_version` in the report header. This makes it visible at a glance which SDLC shape the project is being held to.
```

- [ ] **Step 3: Mirror to plugin-dir + verify packaging**

```bash
cp agents/core/sdlc-enforcer.md plugins/sdlc-core/agents/sdlc-enforcer.md
python3 tools/validation/check-plugin-packaging.py
```

Expected: PASSED, 12 plugins verified.

- [ ] **Step 4: Verify the agent format check still passes**

```bash
python3 tools/validation/validate-agent-official.py agents/ --audit --mode project 2>&1 | grep -E "Failing|sdlc-enforcer"
```

Expected: `Failing: 0`.

- [ ] **Step 5: Commit**

```bash
git add agents/core/sdlc-enforcer.md plugins/sdlc-core/agents/sdlc-enforcer.md
git commit -m "$(cat <<'EOF'
feat(commissioning): sdlc-enforcer reads commissioning record (Phase C task 9)

Adds a "Read commissioning record on every invocation" section to the
sdlc-enforcer agent prompt. The enforcer now:

- Reads .sdlc/team-config.json via sdlc_core_scripts.commission.recorder
- Defaults to single-team for projects without sdlc_option (backward compat)
- Includes sdlc_option and option_bundle_version in compliance report headers

Mirrors to plugins/sdlc-core/agents/sdlc-enforcer.md per the
plugin-packaging contract (verified by check-plugin-packaging.py).

Phase C task 9 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: Containerised review of the bundle contract spec

**Files:**
- Create: `research/sdlc-bundles/dogfood-workflows/bundle-contract-review.md` (workflow command)
- Create: `research/sdlc-bundles/dogfood-workflows/bundle-contract-review.yaml` (workflow YAML)
- Capture: `research/sdlc-bundles/dogfood-workflows/bundle-contract-review-output.md` (review output)

**Why before Task 11**: the bundle contract is load-bearing for Phase D and Phase E. Per `memory/feedback_containerised_review_for_design_artefacts.md`, load-bearing design artefacts go through containerised review by default.

- [ ] **Step 1: Author the workflow command**

Create `research/sdlc-bundles/dogfood-workflows/bundle-contract-review.md` modeled on `architect-review-spike.md` from Phase B (~150 lines). The agent under dispatch is `sdlc-team-common:solution-architect`. Reviewing target: `docs/architecture/option-bundle-contract.md`.

Brief the agent to answer:

1. Is the manifest schema permissive enough for Programme + Assured + future Solo / Single-team without retrofit?
2. Are the reserved Phase E fields adequate, or are gaps visible already?
3. Does the file layout match the existing 12-plugin family pattern, or does it diverge in surprising ways?
4. Is the backward-compatibility story tight (uncommissioned projects default cleanly)?
5. What would a regulated-industry engagement adopting Assured find missing in this contract?

- [ ] **Step 2: Author the workflow YAML**

Create `research/sdlc-bundles/dogfood-workflows/bundle-contract-review.yaml`:

```yaml
name: bundle-contract-review
description: |
  Independent containerised architect review of the option bundle contract
  (Phase C task 1 deliverable). Load-bearing artefact: Phase D and Phase E
  both build bundles against this contract; getting it wrong is expensive.
provider: claude
nodes:
  - id: contract-review
    command: bundle-contract-review
    context: fresh
    effort: high
    image: sdlc-worker:decomposition-review  # reuse the team built in Phase B
    timeout: 600000
```

- [ ] **Step 3: Install workflow + command into .archon and run**

```bash
cp research/sdlc-bundles/dogfood-workflows/bundle-contract-review.md .archon/commands/
cp research/sdlc-bundles/dogfood-workflows/bundle-contract-review.yaml .archon/workflows/

# Run via /sdlc-workflows:workflows-run
# (See plugins/sdlc-workflows/skills/workflows-run/SKILL.md for the procedure;
# the Phase B precedent in commit dbf4128 has the working invocation.)
```

Capture the review output to `research/sdlc-bundles/dogfood-workflows/bundle-contract-review-output.md`.

- [ ] **Step 4: Integrate review findings**

If the review surfaces real issues:

- Fix the contract inline; re-run validation
- Note any deferred Phase D / Phase E concerns in the bundle contract document's "Future enhancements" section
- Update Phase C retrospective with finding-by-finding response

If the review surfaces nothing actionable:

- Note in retrospective that the contract held up under independent review

- [ ] **Step 5: Commit**

```bash
git add research/sdlc-bundles/dogfood-workflows/bundle-contract-review.* \
        .archon/commands/bundle-contract-review.md \
        .archon/workflows/bundle-contract-review.yaml \
        docs/architecture/option-bundle-contract.md  # only if revised
git commit -m "$(cat <<'EOF'
review(commissioning): containerised architect review of bundle contract (Phase C task 10)

Re-ran the bundle contract spec through the containerised architect review
mechanism (sdlc-workflows + sdlc-worker:decomposition-review team image).
Per memory/feedback_containerised_review_for_design_artefacts.md, load-
bearing design artefacts go through containerised review by default.

Workflow + command artefacts reusable for future contract reviews.
Review output captured for audit. [Findings integrated inline / no actionable
findings] — see Phase C retrospective for finding-by-finding response.

Phase C task 10 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: Phase C closure — validation, retrospective, issue close

**Files:**
- Modify: `retrospectives/98-phase-c-commissioning-infrastructure.md`

- [ ] **Step 1: Run full validation**

```bash
python3 -m pytest tests/test_commission_*.py -v 2>&1 | tail -5
python3 tools/validation/check-plugin-packaging.py 2>&1 | tail -3
python3 tools/validation/local-validation.py --quick 2>&1 | tail -5
```

Expected: 20 commission tests pass; 12 plugins verified; quick validation PASSED.

- [ ] **Step 2: Run pre-push validation**

```bash
python3 tools/validation/local-validation.py --pre-push 2>&1 | tail -10
```

Expected: PASSED, or 9/10 with the documented pre-commit-binary env limitation.

- [ ] **Step 3: Complete the Phase C retrospective**

Edit `retrospectives/98-phase-c-commissioning-infrastructure.md`. Replace the "(Filled in at phase end)" placeholders with actual findings:

- **What was built**: 4 deliverables matching the spec (bundle contract, manifest module, recorder, installer + skill). 20 unit/integration tests. Mock bundle fixture. CLAUDE-CORE.md updated. sdlc-enforcer commissioning-aware. Containerised contract review captured.
- **What worked well**: TDD discipline held throughout. Phase E reserved fields baked into the contract early (no retrofit needed when Phase E lands). The mock-bundle fixture pattern (sample-bundle for installer testing) made the installer testable before any real bundle existed.
- **What was harder than expected**: [fill from actual experience]
- **Lessons learned**: [fill from actual experience]

Set status to **COMPLETE**.

- [ ] **Step 4: Commit retrospective**

```bash
git add retrospectives/98-phase-c-commissioning-infrastructure.md
git commit -m "$(cat <<'EOF'
docs: Phase C retrospective complete; commissioning infrastructure ready (Phase C task 11)

Closes #98 (absorbed as Phase C of EPIC #178). All four deliverables
shipped: bundle contract specification, BundleManifest module,
CommissioningRecord module, bundle installer module, commission skill,
sdlc-enforcer commissioning awareness. Mock bundle fixture validates
the installer end-to-end. Containerised architect review of the bundle
contract captured for audit.

20 commission tests (5 manifest + 7 recorder + 5 installer + 3 integration)
all passing. Plugin packaging 12/12 verified. Pre-push 9/10 (pre-commit
binary env limitation; pre-existing).

Phase D (Programme bundle) and Phase E (Assured bundle) can now build
on top of this commissioning infrastructure.

Closes #98.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: Push branch**

```bash
git push 2>&1 | tail -3
```

Verify push succeeded. The branch now has Phase A + Phase B + Phase C work. Phase D (Programme bundle) is next.

---

## Self-review

**Spec coverage check** — every section of `docs/feature-proposals/98-sdlc-commissioning-infrastructure.md` Success Criteria mapped to a task:

| Spec criterion | Task |
|---|---|
| Bundle contract documented with manifest schema, file layout, reserved Phase E fields | Task 1 |
| Plugin packaging shape decided and documented | Task 1 |
| `commission` skill exists at `skills/commission/SKILL.md`, wired into `release-mapping.yaml` | Task 6 |
| `commission` skill asks structured questions and derives recommendation | Task 6 (skill content) |
| `commission` skill respects user override with warning | Task 6 (skill content) |
| `commission` skill installs a bundle (via mock) | Task 6 + Task 8 |
| `.sdlc/team-config.json` schema includes 5 required + history + reserved Phase E fields | Task 3 + Task 7 |
| CLAUDE-CORE.md documents schema and commissioning concept | Task 7 |
| `sdlc-enforcer` reads commissioning record and adapts | Task 9 |
| Existing projects continue to work unchanged (default to single-team) | Task 3 + Task 9 (backward-compat tests + enforcer default) |
| Unit tests for the commissioning skill against a mock bundle | Tasks 2, 3, 5, 8 (20 tests total) |
| Containerised review of bundle contract | Task 10 |
| Pre-push validation passes | Task 11 |
| Phase C retrospective committed | Task 11 |

All criteria covered.

**Placeholder scan**: no "TBD", "TODO", "implement later". Every code block contains real content. Test functions have real bodies. Commit messages use heredoc form per the repo convention.

**Type consistency**: `BundleManifest`, `CommissioningRecord`, `InstallationResult` defined once and referenced consistently. `parse_manifest`, `install_bundle`, `read_record`, `write_record`, `is_commissioned`, `default_option_for_uncommissioned` all defined and consumed by the right test names.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-27-phase-c-commissioning-infrastructure.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, two-stage review per task (spec compliance + code quality), fast iteration. Each task ships its commit before moving on; Phase C retrospective consolidates at the end.

**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints. Heavier on context budget; faster wall-clock.

**Recommended: subagent-driven** — Phase C is 11 tasks of independent file-by-file work, ideal for the subagent pattern. The Phase B containerised-review pattern can be reused for Task 10 (already provisioned).

Which approach?
