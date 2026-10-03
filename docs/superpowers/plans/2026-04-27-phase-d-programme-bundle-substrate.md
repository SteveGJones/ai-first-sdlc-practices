# Phase D — Programme Bundle (Method 1 Substrate) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `sdlc-programme` plugin v0.1.0 — Method 1 phase-gate substrate (4 gates + 5 skills + Programme constitution + 3 phase artefact templates) per METHODS.md §3.

**Architecture:** Mirror Phase C's pattern. Python helpers under `plugins/sdlc-programme/scripts/programme/` (spec_parser, gates, traceability). Skill SKILL.md files orchestrate via bash snippets that invoke the helpers. Each phase gate is a focused function that uses the shared spec_parser. Plugin packaged as new top-level entry in release-mapping.yaml + marketplace.json.

**Tech Stack:** Python 3.10+, pytest, markdown-driven skills, sdlc-workflows containerised review (Phase B/C precedent).

**Spec:** `docs/feature-proposals/186-phase-d-programme-bundle-substrate.md`
**EPIC:** #178 (Joint Programme + Assured bundle delivery)
**Branch:** `feature/sdlc-programme-assured-bundles` (continuing from Phase C)

---

## Critical lessons from Phase C (apply preventively)

1. **Plugin-dir vs root-source split** — when editing files mirrored into plugins, edit root source first, then `cp` to plugin-dir, then `python3 tools/validation/check-plugin-packaging.py`. The 5 SKILL.md files in this phase ship at root + plugin-mirror.
2. **Black before commit** — run `python3 -m black --check <files>` BEFORE committing. Black auto-splits multi-line tuples and long lines.
3. **No unused imports** — flake8 F401. Don't `import pytest` unless using `pytest.raises`.
4. **Wrap exceptions at boundaries** — like `parse_manifest` wraps `yaml.YAMLError` → `ManifestValidationError`, `spec_parser` wraps any parse error in a single `SpecParseError`.
5. **Containerised review for design artefacts** — Task 14 dispatches the architect via `sdlc-workflows` for the Programme bundle design before close.

---

## ID format conventions

Phase artefact IDs use the format `<TYPE>-<feature-id>-<num>`:

- `REQ-cross-library-001` — requirement
- `DES-cross-library-001` — design element
- `TEST-cross-library-001` — test

The spec_parser recognises these patterns. Phase E (Assured bundle) will add namespaced format (`P1.SP2.M3.REQ-007`) per the Phase B spike's open ID-format question; Phase D ships only the simpler feature-prefixed format.

---

## File structure

**New files:**

| File | Responsibility |
|---|---|
| `plugins/sdlc-programme/.claude-plugin/plugin.json` | Plugin metadata |
| `plugins/sdlc-programme/manifest.yaml` | Bundle manifest (name=programme, v0.1.0) |
| `plugins/sdlc-programme/CONSTITUTION.md` | Programme constitution overlay |
| `plugins/sdlc-programme/README.md` | Bundle overview |
| `plugins/sdlc-programme/pyproject.toml` | Python package config |
| `plugins/sdlc-programme/templates/requirements-spec.md` | Req-spec template |
| `plugins/sdlc-programme/templates/design-spec.md` | Design-spec template |
| `plugins/sdlc-programme/templates/test-spec.md` | Test-spec template |
| `plugins/sdlc-programme/scripts/__init__.py` | Package marker |
| `plugins/sdlc-programme/scripts/programme/__init__.py` | Module marker |
| `plugins/sdlc-programme/scripts/programme/spec_parser.py` | Parse IDs and refs from phase markdown |
| `plugins/sdlc-programme/scripts/programme/gates.py` | 4 gate validators |
| `plugins/sdlc-programme/scripts/programme/traceability.py` | Export to csv/markdown |
| `plugins/sdlc-programme/skills/commission-programme/SKILL.md` | Programme-specific commission |
| `plugins/sdlc-programme/skills/phase-init/SKILL.md` | Instantiate phase artefact |
| `plugins/sdlc-programme/skills/phase-gate/SKILL.md` | Run gate validator |
| `plugins/sdlc-programme/skills/phase-review/SKILL.md` | Mandatory cross-phase review |
| `plugins/sdlc-programme/skills/traceability-export/SKILL.md` | Export traceability matrix |
| `skills/commission-programme/SKILL.md` | Root source for commission-programme |
| `skills/phase-init/SKILL.md` | Root source for phase-init |
| `skills/phase-gate/SKILL.md` | Root source for phase-gate |
| `skills/phase-review/SKILL.md` | Root source for phase-review |
| `skills/traceability-export/SKILL.md` | Root source for traceability-export |
| `tests/test_programme_spec_parser.py` | spec_parser unit tests |
| `tests/test_programme_gates.py` | gate validator tests |
| `tests/test_programme_traceability.py` | traceability-export tests |
| `tests/test_programme_skill_integration.py` | end-to-end skill flow tests |
| `tests/fixtures/programme/feature-sample/requirements-spec.md` | Minimal valid req-spec |
| `tests/fixtures/programme/feature-sample/design-spec.md` | Minimal valid design-spec |
| `tests/fixtures/programme/feature-sample/test-spec.md` | Minimal valid test-spec |

**Modified files:**

| File | Change |
|---|---|
| `release-mapping.yaml` | New `sdlc-programme:` top-level key |
| `.claude-plugin/marketplace.json` | New `sdlc-programme` v0.1.0 entry |
| `tests/conftest.py` | Register `sdlc_programme_scripts` package |

---

## Task 1: Plugin scaffold (manifest, plugin.json, README, pyproject.toml)

**Files:**
- Create: `plugins/sdlc-programme/.claude-plugin/plugin.json`
- Create: `plugins/sdlc-programme/manifest.yaml`
- Create: `plugins/sdlc-programme/README.md`
- Create: `plugins/sdlc-programme/pyproject.toml`
- Create: `plugins/sdlc-programme/scripts/__init__.py` (empty)
- Create: `plugins/sdlc-programme/scripts/programme/__init__.py` (empty)

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p plugins/sdlc-programme/.claude-plugin \
         plugins/sdlc-programme/scripts/programme \
         plugins/sdlc-programme/templates \
         plugins/sdlc-programme/skills
touch plugins/sdlc-programme/scripts/__init__.py
touch plugins/sdlc-programme/scripts/programme/__init__.py
```

- [ ] **Step 2: Create plugin.json**

Create `plugins/sdlc-programme/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-programme",
  "version": "0.1.0",
  "description": "Programme SDLC bundle — formal waterfall phase gates with mandatory cross-phase review",
  "author": { "name": "SteveGJones" },
  "repository": "https://github.com/SteveGJones/ai-first-sdlc-practices",
  "license": "MIT",
  "keywords": ["sdlc", "programme", "phase-gates", "method-1", "bundle"]
}
```

- [ ] **Step 3: Create manifest.yaml**

Create `plugins/sdlc-programme/manifest.yaml`:

```yaml
schema_version: 1
name: programme
version: 0.1.0
supported_levels: [production, enterprise]
description: Multi-team programme SDLC with formal waterfall phase gates and mandatory cross-phase review
constitution: CONSTITUTION.md
depends_on: [sdlc-core]
agents: []
skills:
  - commission-programme
  - phase-init
  - phase-gate
  - phase-review
  - traceability-export
templates:
  - requirements-spec.md
  - design-spec.md
  - test-spec.md
validators:
  syntax: [python_ast]
  quick: [check_technical_debt, check_logging_compliance]
  pre_push: [python_ast, check_technical_debt, check_logging_compliance, run_tests, requirements_gate, design_gate, test_gate, code_gate]
```

- [ ] **Step 4: Create README.md**

Create `plugins/sdlc-programme/README.md`:

```markdown
# sdlc-programme — Programme SDLC bundle (v0.1.0)

Method 1 phase-gate substrate for programme-of-work delivery. Ship a project to **Programme** when:

- Team size 11-50 people across 2-5 teams
- Specification maturity is formal or contract-first
- Blast radius is moderate-to-high
- Audit-friendly traceability matters but full regulated-industry traceability does not

For regulated-industry projects (DO-178C, IEC 62304, ISO 26262, IEC 61508, FDA), use the **Assured** bundle instead (Phase E).
For 1-2 person projects, use **Solo**. For 3-10 person product teams, **Single-team** (the framework default).

## What this bundle ships

- **4 phase gates** — `requirements-gate`, `design-gate`, `test-gate`, `code-gate` enforced at pre-push and CI. Block on missing artefact or broken cross-phase reference; warn on weak references.
- **3 phase artefact templates** — `requirements-spec.md`, `design-spec.md`, `test-spec.md` copied into a project on commission. Each phase artefact has stable IDs that subsequent phases reference.
- **5 skills** — `commission-programme`, `phase-init <phase>`, `phase-gate <phase>`, `phase-review <phase>` (mandatory for design-spec and test-spec), `traceability-export <format>` (csv, markdown).
- **Programme constitution** — overlays Single-team's foundations with 3 Programme-specific articles enforcing phase-gate compliance, cross-phase reference integrity, and mandatory `phase-review`.

## What this bundle does NOT ship (yet)

- Multi-team SAFe-Lite features (contract registry, dependency tracking, programme-wide audit consolidation, multi-team agents). See issue #103 — those land in v1.0 when a real multi-team collaborator is available.
- Method 2 features (traceability registry, decomposition, KB-for-code). See the Assured bundle (Phase E).

## How to commission

\`\`\`
/sdlc-core:commission --option programme --level production
\`\`\`

After commission, every feature follows: `phase-init requirements <feature-id>` → fill in template → `phase-gate requirements <feature-id>` → `phase-init design <feature-id>` → fill in → `phase-review design <feature-id>` (mandatory) → `phase-gate design <feature-id>` → repeat for test → write code under TDD against the test-spec → push.

## See also

- Bundle contract: `docs/architecture/option-bundle-contract.md`
- Phase D substrate spec: `docs/feature-proposals/186-phase-d-programme-bundle-substrate.md`
- Method 1 design: `research/sdlc-bundles/METHODS.md` §3
- Future v1.0 scope: #103
```

- [ ] **Step 5: Create pyproject.toml**

Create `plugins/sdlc-programme/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "sdlc-programme-scripts"
version = "0.1.0"
description = "Python helpers shipped with sdlc-programme plugin"
requires-python = ">=3.10"

[tool.setuptools.packages.find]
where = ["scripts"]
include = ["*"]

[tool.setuptools.package-dir]
"" = "scripts"
```

- [ ] **Step 6: Verify manifest parses cleanly via Phase C's manifest parser**

```bash
python3 -c "
from pathlib import Path
from sdlc_core_scripts.commission.manifest import parse_manifest
m = parse_manifest(Path('plugins/sdlc-programme/manifest.yaml'))
print(f'name={m.name} version={m.version} levels={m.supported_levels}')
print(f'skills={m.skills}')
print(f'templates={m.templates}')
print(f'depends_on={m.depends_on}')
"
```

Expected output:
```
name=programme version=0.1.0 levels=['production', 'enterprise']
skills=['commission-programme', 'phase-init', 'phase-gate', 'phase-review', 'traceability-export']
templates=['requirements-spec.md', 'design-spec.md', 'test-spec.md']
depends_on=['sdlc-core']
```

If parse fails, fix the manifest — it must be valid per the Phase C bundle contract.

- [ ] **Step 7: Run validation**

```bash
python3 tools/validation/local-validation.py --quick
```

Expected: PASSED.

- [ ] **Step 8: Commit**

```bash
git add plugins/sdlc-programme/.claude-plugin/ plugins/sdlc-programme/manifest.yaml plugins/sdlc-programme/README.md plugins/sdlc-programme/pyproject.toml plugins/sdlc-programme/scripts/__init__.py plugins/sdlc-programme/scripts/programme/__init__.py
git commit -m "$(cat <<'EOF'
feat(programme): plugin scaffold — manifest, plugin.json, README, pyproject (Phase D task 1)

Creates plugins/sdlc-programme/ with:
- .claude-plugin/plugin.json — standard plugin metadata
- manifest.yaml — bundle manifest (v0.1.0, supported_levels: production+enterprise,
  5 skills, 3 templates, validators per pipeline phase)
- README.md — bundle overview, audience, level guidance
- pyproject.toml — Python package shape mirroring sdlc-core/sdlc-knowledge-base
- scripts/__init__.py + scripts/programme/__init__.py — package markers

Manifest parses cleanly through sdlc_core_scripts.commission.manifest.parse_manifest.

Phase D task 1 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Programme constitution

**Files:**
- Create: `plugins/sdlc-programme/CONSTITUTION.md`

Programme constitution overlays Single-team's foundations (universal articles 1-11 from `CONSTITUTION.md` at repo root) with 3 Programme-specific articles. The bundle's CONSTITUTION.md REPLACES the project's existing CONSTITUTION.md on commission, but its content extends rather than discards the universal rules.

- [ ] **Step 1: Read the universal Constitution to understand articles 1-11**

```bash
grep -E "^## Article" CONSTITUTION.md
```

Note the existing article structure so the Programme constitution doesn't duplicate or contradict.

- [ ] **Step 2: Create the Programme constitution**

Create `plugins/sdlc-programme/CONSTITUTION.md`:

```markdown
# Programme Constitution (sdlc-programme bundle v0.1.0)

This constitution applies to projects commissioned to the **Programme** SDLC option. It extends the universal AI-First SDLC Constitution (`CONSTITUTION.md` at the framework root) with three Programme-specific articles enforcing formal waterfall phase gates and mandatory cross-phase review.

The universal articles (1-11) apply unchanged. Programme adds articles 12-14.

---

## Article 12 — Phase-gate compliance (Programme)

**Every feature MUST have all three phase artefacts in `docs/specs/<feature-id>/` before code commits proceed:**

1. `requirements-spec.md` — what the feature must do
2. `design-spec.md` — how it will be built, citing the requirements-spec by feature-id
3. `test-spec.md` — what tests verify, citing both requirements-spec and design-spec

Code may not be committed for a feature whose phase artefacts are incomplete. The `code-gate` validator enforces this at pre-push.

**Each phase artefact has mandatory sections** declared by its template (see `plugins/sdlc-programme/templates/`). Missing mandatory sections block the corresponding phase-gate validator.

**Each artefact has a stable feature-id** assigned at the requirements-spec phase and inherited by design-spec and test-spec. The feature-id format is `<short-slug>` (e.g., `cross-library-query`, `oauth-flow`).

## Article 13 — Cross-phase reference integrity (Programme)

**Citations between phase artefacts MUST resolve to existing IDs.**

- `design-spec.md` references requirements-spec via `satisfies: REQ-<feature-id>-NNN` lines. Each cited REQ-ID MUST exist in the requirements-spec.
- `test-spec.md` references both requirements-spec via `satisfies: REQ-<feature-id>-NNN` and design-spec via `satisfies: DES-<feature-id>-NNN`. Each cited ID MUST exist in the corresponding artefact.
- Code MUST cite a test-spec section via `# implements: TEST-<feature-id>-NNN` annotation. The cited TEST-ID MUST exist in the test-spec.

The `design-gate`, `test-gate`, and `code-gate` validators enforce this at pre-push. Broken references are defects, not style issues — they block.

Weak references (vague but non-broken; e.g., a citation that refers to a real REQ-ID but where the design-spec content doesn't actually address that requirement) are caught by `phase-review` (Article 14), not by the gates. Gates check structure; reviews check meaning.

## Article 14 — Mandatory phase-review (Programme)

**Cross-phase review via `phase-review <phase> <feature-id>` is mandatory for:**

- `design-spec.md` — review against the cited requirements-spec
- `test-spec.md` — review against both cited requirements-spec and design-spec

**Recommended (not mandatory) for:**

- `requirements-spec.md` — self-review or peer-review of completeness

The review record MUST be committed alongside the artefact under review. Review records live at `docs/specs/<feature-id>/reviews/<phase>-review-<reviewer>.md`. The review records are checked into git as the auditable evidence that human-in-the-loop review occurred.

`phase-gate` validators check that a review record exists before they pass for design-spec and test-spec phases. Missing review records block the gate.

---

## What this bundle does NOT enforce

- Decomposition / programs / sub-programs / modules — that's the **Assured** bundle (Method 2)
- Bidirectional traceability beyond REQ → DES → TEST → CODE — that's Assured
- Industry certification compliance (DO-178C, IEC 62304, etc.) — Programme is not a certification path; it is an audit-friendly substrate. Use Assured for regulated industries.
- Multi-team SAFe-Lite features — see #103 future v1.0 scope

The Programme constitution is the floor — universal articles plus phase gates. Teams may layer additional process on top via their own retrospective decisions.
```

- [ ] **Step 3: Run validation**

```bash
python3 tools/validation/local-validation.py --quick
```

Expected: PASSED.

- [ ] **Step 4: Commit**

```bash
git add plugins/sdlc-programme/CONSTITUTION.md
git commit -m "$(cat <<'EOF'
feat(programme): Programme constitution with 3 Programme-specific articles (Phase D task 2)

Programme constitution overlays Single-team's foundations (universal
articles 1-11 from CONSTITUTION.md at repo root) with 3 Programme-specific
articles:

- Article 12: Phase-gate compliance — every feature has req-spec, design-spec,
  test-spec in docs/specs/<feature-id>/ before code commits
- Article 13: Cross-phase reference integrity — citations between phase
  artefacts MUST resolve to existing IDs; gates block on broken refs
- Article 14: Mandatory phase-review for design-spec and test-spec; review
  records committed alongside the reviewed artefact

Phase D task 2 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Phase artefact templates

**Files:**
- Create: `plugins/sdlc-programme/templates/requirements-spec.md`
- Create: `plugins/sdlc-programme/templates/design-spec.md`
- Create: `plugins/sdlc-programme/templates/test-spec.md`

Templates are the artefacts the installer copies into `<project>/.sdlc/templates/` on commission. Each template has mandatory sections (validator-checked) and inline guidance prompts (commented-out paragraphs explaining what each section should contain).

- [ ] **Step 1: Create requirements-spec template**

Create `plugins/sdlc-programme/templates/requirements-spec.md`:

```markdown
# Requirements Specification: <Feature Title>

**Feature-id:** <feature-id>
**Status:** Draft
**Author:** <Your name>
**Created:** <YYYY-MM-DD>

---

## Motivation

<!-- WHY this feature exists. What user need / business motivation / regulatory constraint drives it? Keep this short — one or two paragraphs. The motivation drives traceability: every REQ below should be a concrete instantiation of this motivation. -->

## Requirements

<!-- WHAT the feature must do. Each requirement is a single declarative sentence with a stable ID. Numbering: REQ-<feature-id>-NNN starting at 001. IDs are immutable once committed; do not renumber. -->

### REQ-<feature-id>-001
<Single declarative sentence describing one requirement.>

### REQ-<feature-id>-002
<Single declarative sentence describing the next requirement.>

<!-- Add more requirements as needed, each with its own REQ-NNN heading. -->

## Out of scope

<!-- What this feature explicitly does NOT do. Listing out-of-scope items here keeps subsequent phases honest. -->

## Success criteria

<!-- The conditions under which this feature is considered complete. These should map to test cases in the test-spec. -->

- [ ] <Criterion 1>
- [ ] <Criterion 2>
```

- [ ] **Step 2: Create design-spec template**

Create `plugins/sdlc-programme/templates/design-spec.md`:

```markdown
# Design Specification: <Feature Title>

**Feature-id:** <feature-id>
**Status:** Draft
**Author:** <Your name>
**Created:** <YYYY-MM-DD>
**Requirements-spec:** [requirements-spec.md](requirements-spec.md)

---

## Approach

<!-- HOW the feature will be built. 2-3 paragraphs describing the architectural approach. Cite the relevant REQs by ID. -->

## Design elements

<!-- Each design element is a discrete decision with a stable ID. Numbering: DES-<feature-id>-NNN starting at 001. The "satisfies" line is mandatory and references one or more REQ-IDs from requirements-spec.md. -->

### DES-<feature-id>-001 — <short title>
**satisfies:** REQ-<feature-id>-001

<Description of this design element. What component is created, modified, or removed? What interface does it expose?>

### DES-<feature-id>-002 — <short title>
**satisfies:** REQ-<feature-id>-002, REQ-<feature-id>-003

<Description.>

<!-- Add more design elements as needed. Each must satisfy at least one REQ. -->

## Out of scope (this design)

<!-- Aspects of the requirements deliberately not addressed in this design — typically deferred to a follow-up feature or another component. -->

## Risks

<!-- What could go wrong with this design. Each risk has an impact + mitigation. -->

| Risk | Impact | Mitigation |
|---|---|---|
| <risk> | <impact> | <mitigation> |
```

- [ ] **Step 3: Create test-spec template**

Create `plugins/sdlc-programme/templates/test-spec.md`:

```markdown
# Test Specification: <Feature Title>

**Feature-id:** <feature-id>
**Status:** Draft
**Author:** <Your name>
**Created:** <YYYY-MM-DD>
**Requirements-spec:** [requirements-spec.md](requirements-spec.md)
**Design-spec:** [design-spec.md](design-spec.md)

---

## Testing approach

<!-- HOW the feature will be verified. Describe the test pyramid balance: unit tests, integration tests, end-to-end. Cite the relevant DESs by ID. -->

## Test cases

<!-- Each test case is a discrete verifiable statement with a stable ID. Numbering: TEST-<feature-id>-NNN starting at 001. The "satisfies" line is mandatory and references one or more REQ-IDs and DES-IDs. -->

### TEST-<feature-id>-001 — <short title>
**satisfies:** REQ-<feature-id>-001 via DES-<feature-id>-001

**Setup:** <prerequisite state>

**Action:** <what the test does>

**Expected result:** <what passes>

### TEST-<feature-id>-002 — <short title>
**satisfies:** REQ-<feature-id>-002 via DES-<feature-id>-002

**Setup:** <prerequisite state>

**Action:** <what the test does>

**Expected result:** <what passes>

<!-- Add more test cases. Each must satisfy at least one REQ + DES. Code annotations will reference these TEST-IDs via "# implements: TEST-..." -->

## Test data and fixtures

<!-- Any fixtures, mocks, or test data required. -->

## Out of scope (this test plan)

<!-- Verification deliberately not part of this test plan — e.g., manual QA passes that the team performs separately. -->
```

- [ ] **Step 4: Run validation**

```bash
python3 tools/validation/local-validation.py --quick
```

Expected: PASSED.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-programme/templates/
git commit -m "$(cat <<'EOF'
feat(programme): phase artefact templates — req-spec, design-spec, test-spec (Phase D task 3)

Templates copied into <project>/.sdlc/templates/ on commission. Each
template has:
- Mandatory sections (validator-checked by phase gates)
- Stable IDs (REQ-NNN, DES-NNN, TEST-NNN per feature-id)
- Inline guidance prompts (HTML comments explaining what each section
  should contain)
- Required cross-phase reference markers (design-spec → requirements-spec;
  test-spec → both prior phases)

Templates are the contract that phase-gate validators (task 5) enforce.

Phase D task 3 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: spec_parser module — extract IDs and references from phase markdown

**Files:**
- Create: `plugins/sdlc-programme/scripts/programme/spec_parser.py`
- Create: `tests/test_programme_spec_parser.py`
- Modify: `tests/conftest.py` (register `sdlc_programme_scripts`)

The spec_parser is the foundation for all 4 gate validators. Every gate parses the relevant phase artefact and extracts (a) the IDs declared in that artefact and (b) the cross-phase references it makes. A single shared parser keeps the regex discipline consistent.

- [ ] **Step 1: Write the failing test**

Create `tests/test_programme_spec_parser.py`:

```python
"""Tests for plugins.sdlc-programme.scripts.programme.spec_parser."""
from pathlib import Path

import pytest

from sdlc_programme_scripts.programme.spec_parser import (
    ParsedSpec,
    SpecParseError,
    parse_spec,
)


def test_parse_requirements_spec_extracts_feature_id_and_req_ids(tmp_path: Path) -> None:
    """A valid requirements-spec yields the feature-id and all REQ-NNN headings."""
    spec_path = tmp_path / "requirements-spec.md"
    spec_path.write_text(
        "# Requirements Specification: Test Feature\n\n"
        "**Feature-id:** my-feature\n\n"
        "## Motivation\n\nWhy.\n\n"
        "## Requirements\n\n"
        "### REQ-my-feature-001\nFirst requirement.\n\n"
        "### REQ-my-feature-002\nSecond requirement.\n\n"
        "## Success criteria\n- [ ] one\n"
    )

    parsed = parse_spec(spec_path, phase="requirements")

    assert isinstance(parsed, ParsedSpec)
    assert parsed.feature_id == "my-feature"
    assert parsed.declared_ids == {"REQ-my-feature-001", "REQ-my-feature-002"}
    assert parsed.references == set()  # requirements-spec has no cross-phase refs


def test_parse_design_spec_extracts_des_ids_and_satisfies_references(tmp_path: Path) -> None:
    """A valid design-spec yields DES-IDs declared and REQ-IDs referenced via satisfies."""
    spec_path = tmp_path / "design-spec.md"
    spec_path.write_text(
        "# Design Specification: Test Feature\n\n"
        "**Feature-id:** my-feature\n\n"
        "## Approach\n\nHow.\n\n"
        "## Design elements\n\n"
        "### DES-my-feature-001 — first\n"
        "**satisfies:** REQ-my-feature-001\n\nDescription.\n\n"
        "### DES-my-feature-002 — second\n"
        "**satisfies:** REQ-my-feature-002, REQ-my-feature-003\n\nDescription.\n\n"
    )

    parsed = parse_spec(spec_path, phase="design")

    assert parsed.feature_id == "my-feature"
    assert parsed.declared_ids == {"DES-my-feature-001", "DES-my-feature-002"}
    assert parsed.references == {
        "REQ-my-feature-001",
        "REQ-my-feature-002",
        "REQ-my-feature-003",
    }


def test_parse_test_spec_extracts_test_ids_and_both_prior_phase_references(tmp_path: Path) -> None:
    """A valid test-spec yields TEST-IDs declared and both REQ + DES IDs referenced."""
    spec_path = tmp_path / "test-spec.md"
    spec_path.write_text(
        "# Test Specification: Test Feature\n\n"
        "**Feature-id:** my-feature\n\n"
        "## Test cases\n\n"
        "### TEST-my-feature-001 — first\n"
        "**satisfies:** REQ-my-feature-001 via DES-my-feature-001\n\nSetup.\n\n"
        "### TEST-my-feature-002 — second\n"
        "**satisfies:** REQ-my-feature-002, REQ-my-feature-003 via DES-my-feature-002\n\nSetup.\n\n"
    )

    parsed = parse_spec(spec_path, phase="test")

    assert parsed.feature_id == "my-feature"
    assert parsed.declared_ids == {"TEST-my-feature-001", "TEST-my-feature-002"}
    assert parsed.references == {
        "REQ-my-feature-001",
        "REQ-my-feature-002",
        "REQ-my-feature-003",
        "DES-my-feature-001",
        "DES-my-feature-002",
    }


def test_parse_spec_missing_feature_id_raises(tmp_path: Path) -> None:
    """A spec without a feature-id line raises SpecParseError."""
    spec_path = tmp_path / "requirements-spec.md"
    spec_path.write_text(
        "# Requirements Specification\n\n## Motivation\n\nWhy.\n"
    )

    with pytest.raises(SpecParseError, match="feature-id"):
        parse_spec(spec_path, phase="requirements")


def test_parse_spec_unknown_phase_raises(tmp_path: Path) -> None:
    """An unknown phase name raises SpecParseError."""
    spec_path = tmp_path / "spec.md"
    spec_path.write_text("**Feature-id:** test\n")

    with pytest.raises(SpecParseError, match="phase"):
        parse_spec(spec_path, phase="bogus")


def test_parse_spec_missing_file_raises(tmp_path: Path) -> None:
    """A non-existent file raises SpecParseError."""
    spec_path = tmp_path / "missing.md"

    with pytest.raises(SpecParseError, match="not found"):
        parse_spec(spec_path, phase="requirements")


def test_parse_spec_ignores_ids_in_code_blocks(tmp_path: Path) -> None:
    """IDs inside fenced code blocks are NOT counted as declared or referenced."""
    spec_path = tmp_path / "design-spec.md"
    spec_path.write_text(
        "**Feature-id:** my-feature\n\n"
        "### DES-my-feature-001 — real\n"
        "**satisfies:** REQ-my-feature-001\n\n"
        "Real description.\n\n"
        "```\n"
        "### DES-my-feature-999 — fake (in code block)\n"
        "**satisfies:** REQ-my-feature-999\n"
        "```\n"
    )

    parsed = parse_spec(spec_path, phase="design")

    assert parsed.declared_ids == {"DES-my-feature-001"}  # not -999
    assert parsed.references == {"REQ-my-feature-001"}  # not -999
```

- [ ] **Step 2: Run test, verify it fails**

```bash
python3 -m pytest tests/test_programme_spec_parser.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'sdlc_programme_scripts'`.

- [ ] **Step 3: Register sdlc_programme_scripts in conftest**

Edit `tests/conftest.py`. Find the bottom where existing registrations are:

```python
_register_scripts_package("sdlc-workflows", "sdlc_workflows_scripts")
_register_scripts_package("sdlc-knowledge-base", "sdlc_knowledge_base_scripts")
_register_scripts_package("sdlc-core", "sdlc_core_scripts")
```

Append one line:

```python
_register_scripts_package("sdlc-programme", "sdlc_programme_scripts")
```

Also update the docstring at the top of conftest.py to mention sdlc-programme:

Find the line:
```
Also registers ``sdlc_knowledge_base_scripts`` from
``plugins/sdlc-knowledge-base/scripts/`` and ``sdlc_core_scripts`` from
``plugins/sdlc-core/scripts/`` using the same pattern.
```

Replace with:
```
Also registers ``sdlc_knowledge_base_scripts``, ``sdlc_core_scripts``, and
``sdlc_programme_scripts`` from their respective ``plugins/<name>/scripts/``
trees using the same pattern.
```

- [ ] **Step 4: Implement spec_parser.py**

Create `plugins/sdlc-programme/scripts/programme/spec_parser.py`:

```python
"""Parse phase artefact markdown to extract declared IDs and cross-phase references.

Each phase artefact (requirements-spec, design-spec, test-spec) declares IDs via
H3 headings of the form ``### TYPE-<feature-id>-NNN`` and (for design-spec and
test-spec) references prior-phase IDs via ``**satisfies:**`` lines.

The parser is line-wise and skips fenced code blocks so that IDs in code
samples don't pollute the parse.

Used by the four phase-gate validators in ``gates.py``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

VALID_PHASES = {"requirements", "design", "test"}

# Phase → ID type prefix
_PHASE_TO_PREFIX = {
    "requirements": "REQ",
    "design": "DES",
    "test": "TEST",
}

_FEATURE_ID_RE = re.compile(r"^\*\*Feature-id:\*\*\s+([a-z0-9][a-z0-9-]*)\s*$", re.MULTILINE)
_HEADING_ID_RE = re.compile(
    r"^###\s+(?P<id>(?:REQ|DES|TEST)-[a-z0-9][a-z0-9-]*-\d+)\b"
)
_SATISFIES_RE = re.compile(
    r"^\*\*satisfies:\*\*\s+(?P<refs>.+)$"
)
_REF_ID_RE = re.compile(r"\b((?:REQ|DES)-[a-z0-9][a-z0-9-]*-\d+)\b")


class SpecParseError(Exception):
    """Raised when a phase artefact cannot be parsed."""


@dataclass
class ParsedSpec:
    """Parsed phase artefact."""

    feature_id: str
    phase: str
    declared_ids: set[str] = field(default_factory=set)
    references: set[str] = field(default_factory=set)


def parse_spec(path: Path, phase: str) -> ParsedSpec:
    """Parse a phase artefact and extract declared IDs + cross-phase references.

    Skips IDs inside fenced code blocks (``` blocks).
    """
    if phase not in VALID_PHASES:
        raise SpecParseError(
            f"Unknown phase '{phase}'; must be one of {sorted(VALID_PHASES)}"
        )

    if not path.exists():
        raise SpecParseError(f"Phase artefact not found: {path}")

    text = path.read_text()

    # Extract feature-id (first occurrence wins; required)
    match = _FEATURE_ID_RE.search(text)
    if match is None:
        raise SpecParseError(
            f"Phase artefact missing **Feature-id:** line: {path}"
        )
    feature_id = match.group(1)

    declared_ids: set[str] = set()
    references: set[str] = set()
    expected_prefix = _PHASE_TO_PREFIX[phase]

    in_code_block = False
    for line in text.splitlines():
        stripped = line.strip()

        # Track fenced code blocks
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # H3 headings — declared IDs (only those matching this phase's prefix)
        heading_match = _HEADING_ID_RE.match(line)
        if heading_match:
            heading_id = heading_match.group("id")
            if heading_id.startswith(expected_prefix + "-"):
                declared_ids.add(heading_id)
            continue

        # **satisfies:** lines — cross-phase references
        satisfies_match = _SATISFIES_RE.match(line)
        if satisfies_match:
            refs_text = satisfies_match.group("refs")
            for ref in _REF_ID_RE.findall(refs_text):
                references.add(ref)

    return ParsedSpec(
        feature_id=feature_id,
        phase=phase,
        declared_ids=declared_ids,
        references=references,
    )
```

- [ ] **Step 5: Run tests, verify they pass**

```bash
python3 -m pytest tests/test_programme_spec_parser.py -v
```

Expected: 7 passed.

- [ ] **Step 6: Lint check**

```bash
python3 -m black --check plugins/sdlc-programme/scripts/programme/spec_parser.py tests/test_programme_spec_parser.py
python3 -m flake8 plugins/sdlc-programme/scripts/programme/spec_parser.py tests/test_programme_spec_parser.py
```

If black wants reformatting, apply with `python3 -m black <files>`.

- [ ] **Step 7: Commit**

```bash
git add plugins/sdlc-programme/scripts/programme/spec_parser.py tests/test_programme_spec_parser.py tests/conftest.py
git commit -m "$(cat <<'EOF'
feat(programme): spec_parser module — extract IDs and references from phase markdown (Phase D task 4)

Line-wise parser that extracts:
- feature-id from **Feature-id:** line
- declared IDs from H3 headings matching phase prefix (REQ for requirements,
  DES for design, TEST for test)
- cross-phase references from **satisfies:** lines (REQ-IDs and DES-IDs)

Skips fenced code blocks so example IDs in documentation don't pollute
the parse.

Foundation for the 4 phase-gate validators (task 5). Each gate uses
parse_spec() to load a phase artefact and check structure + reference
integrity.

7 unit tests covering: requirements parse, design parse with satisfies,
test parse with both prior phases, missing feature-id, unknown phase,
missing file, code-block ignore.

conftest.py extended with sdlc_programme_scripts package registration
mirroring the sdlc_core_scripts pattern.

Phase D task 4 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: gates module — 4 phase-gate validators

**Files:**
- Create: `plugins/sdlc-programme/scripts/programme/gates.py`
- Create: `tests/test_programme_gates.py`
- Create: `tests/fixtures/programme/feature-sample/requirements-spec.md`
- Create: `tests/fixtures/programme/feature-sample/design-spec.md`
- Create: `tests/fixtures/programme/feature-sample/test-spec.md`

The 4 gates each check structure of one phase artefact + (for design / test / code) reference integrity against prior phases.

- [ ] **Step 1: Create the test fixture**

Create `tests/fixtures/programme/feature-sample/requirements-spec.md`:

```markdown
# Requirements Specification: Sample Feature

**Feature-id:** sample
**Status:** Draft
**Author:** Test
**Created:** 2026-04-27

---

## Motivation

Test fixture for Programme bundle gate validators.

## Requirements

### REQ-sample-001
The system MUST do thing one.

### REQ-sample-002
The system MUST do thing two.

## Out of scope

Things this fixture does not cover.

## Success criteria

- [ ] Thing one works
- [ ] Thing two works
```

Create `tests/fixtures/programme/feature-sample/design-spec.md`:

```markdown
# Design Specification: Sample Feature

**Feature-id:** sample
**Status:** Draft
**Author:** Test
**Created:** 2026-04-27
**Requirements-spec:** [requirements-spec.md](requirements-spec.md)

---

## Approach

Test fixture for the design-gate.

## Design elements

### DES-sample-001 — thing one design
**satisfies:** REQ-sample-001

Description.

### DES-sample-002 — thing two design
**satisfies:** REQ-sample-002

Description.

## Out of scope (this design)

None.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Test fixture is too minimal | Tests don't catch edge cases | Add more cases as gates evolve |
```

Create `tests/fixtures/programme/feature-sample/test-spec.md`:

```markdown
# Test Specification: Sample Feature

**Feature-id:** sample
**Status:** Draft
**Author:** Test
**Created:** 2026-04-27
**Requirements-spec:** [requirements-spec.md](requirements-spec.md)
**Design-spec:** [design-spec.md](design-spec.md)

---

## Testing approach

Test fixture for the test-gate.

## Test cases

### TEST-sample-001 — thing one test
**satisfies:** REQ-sample-001 via DES-sample-001

**Setup:** none

**Action:** call thing one

**Expected result:** thing one returns expected value

### TEST-sample-002 — thing two test
**satisfies:** REQ-sample-002 via DES-sample-002

**Setup:** none

**Action:** call thing two

**Expected result:** thing two returns expected value

## Test data and fixtures

None.

## Out of scope (this test plan)

Manual QA passes.
```

- [ ] **Step 2: Write the failing tests**

Create `tests/test_programme_gates.py`:

```python
"""Tests for plugins.sdlc-programme.scripts.programme.gates."""
import shutil
from pathlib import Path

import pytest

from sdlc_programme_scripts.programme.gates import (
    GateError,
    GateResult,
    code_gate,
    design_gate,
    requirements_gate,
    test_gate,
)


REPO_ROOT = Path(__file__).parent.parent
SAMPLE_FEATURE = REPO_ROOT / "tests/fixtures/programme/feature-sample"


def _copy_feature(tmp_path: Path) -> Path:
    """Copy the sample feature fixture to tmp_path/specs/sample/ and return that dir."""
    dst = tmp_path / "specs" / "sample"
    shutil.copytree(SAMPLE_FEATURE, dst)
    return dst


def test_requirements_gate_passes_for_valid_spec(tmp_path: Path) -> None:
    """Valid requirements-spec passes the gate."""
    feature_dir = _copy_feature(tmp_path)

    result = requirements_gate(feature_dir, "sample")

    assert isinstance(result, GateResult)
    assert result.passed is True
    assert result.errors == []


def test_requirements_gate_fails_when_spec_missing(tmp_path: Path) -> None:
    """Missing requirements-spec.md fails the gate."""
    feature_dir = tmp_path / "specs" / "sample"
    feature_dir.mkdir(parents=True)

    result = requirements_gate(feature_dir, "sample")

    assert result.passed is False
    assert any("requirements-spec.md" in e for e in result.errors)


def test_design_gate_passes_when_all_satisfies_resolve(tmp_path: Path) -> None:
    """Design-spec whose every satisfies reference exists in requirements-spec passes."""
    feature_dir = _copy_feature(tmp_path)

    result = design_gate(feature_dir, "sample")

    assert result.passed is True


def test_design_gate_fails_on_broken_satisfies_reference(tmp_path: Path) -> None:
    """Design-spec satisfying a non-existent REQ-ID fails the gate."""
    feature_dir = _copy_feature(tmp_path)

    # Inject a broken reference
    design_spec = feature_dir / "design-spec.md"
    text = design_spec.read_text()
    text = text.replace(
        "**satisfies:** REQ-sample-001",
        "**satisfies:** REQ-sample-999",
    )
    design_spec.write_text(text)

    result = design_gate(feature_dir, "sample")

    assert result.passed is False
    assert any("REQ-sample-999" in e for e in result.errors)


def test_design_gate_fails_when_design_spec_missing(tmp_path: Path) -> None:
    """Missing design-spec.md fails the gate."""
    feature_dir = _copy_feature(tmp_path)
    (feature_dir / "design-spec.md").unlink()

    result = design_gate(feature_dir, "sample")

    assert result.passed is False
    assert any("design-spec.md" in e for e in result.errors)


def test_test_gate_passes_when_all_references_resolve(tmp_path: Path) -> None:
    """Test-spec whose every satisfies reference exists in prior phases passes."""
    feature_dir = _copy_feature(tmp_path)

    result = test_gate(feature_dir, "sample")

    assert result.passed is True


def test_test_gate_fails_on_broken_des_reference(tmp_path: Path) -> None:
    """Test-spec referencing a non-existent DES-ID fails the gate."""
    feature_dir = _copy_feature(tmp_path)

    test_spec = feature_dir / "test-spec.md"
    text = test_spec.read_text()
    text = text.replace(
        "via DES-sample-001",
        "via DES-sample-999",
    )
    test_spec.write_text(text)

    result = test_gate(feature_dir, "sample")

    assert result.passed is False
    assert any("DES-sample-999" in e for e in result.errors)


def test_test_gate_fails_on_broken_req_reference(tmp_path: Path) -> None:
    """Test-spec referencing a non-existent REQ-ID fails the gate."""
    feature_dir = _copy_feature(tmp_path)

    test_spec = feature_dir / "test-spec.md"
    text = test_spec.read_text()
    text = text.replace(
        "**satisfies:** REQ-sample-001",
        "**satisfies:** REQ-sample-999",
    )
    test_spec.write_text(text)

    result = test_gate(feature_dir, "sample")

    assert result.passed is False
    assert any("REQ-sample-999" in e for e in result.errors)


def test_code_gate_passes_when_test_id_in_test_spec(tmp_path: Path) -> None:
    """Code citing a TEST-ID that exists in test-spec passes the gate."""
    feature_dir = _copy_feature(tmp_path)
    code_text = "def do_thing():\n    # implements: TEST-sample-001\n    return 1\n"

    result = code_gate(feature_dir, "sample", code_text=code_text)

    assert result.passed is True


def test_code_gate_fails_when_test_id_not_in_test_spec(tmp_path: Path) -> None:
    """Code citing a non-existent TEST-ID fails the gate."""
    feature_dir = _copy_feature(tmp_path)
    code_text = "def do_thing():\n    # implements: TEST-sample-999\n    return 1\n"

    result = code_gate(feature_dir, "sample", code_text=code_text)

    assert result.passed is False
    assert any("TEST-sample-999" in e for e in result.errors)


def test_code_gate_fails_when_code_has_no_implements_annotation(tmp_path: Path) -> None:
    """Code without any # implements: annotation fails the gate."""
    feature_dir = _copy_feature(tmp_path)
    code_text = "def do_thing():\n    return 1\n"

    result = code_gate(feature_dir, "sample", code_text=code_text)

    assert result.passed is False
    assert any("annotation" in e.lower() for e in result.errors)
```

- [ ] **Step 3: Run tests, verify they fail**

```bash
python3 -m pytest tests/test_programme_gates.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 4: Implement gates.py**

Create `plugins/sdlc-programme/scripts/programme/gates.py`:

```python
"""Phase-gate validators for the Programme bundle (Method 1).

Four gates correspond to the four phases:
- requirements_gate — checks requirements-spec.md exists with feature-id and at least one REQ
- design_gate — checks design-spec.md exists with feature-id, references requirements-spec,
  and all satisfies references resolve to declared REQ-IDs
- test_gate — checks test-spec.md exists, references both prior phases, and all
  references resolve to declared REQ + DES IDs
- code_gate — checks code text has at least one # implements: TEST-<feature>-NNN
  annotation and the cited TEST-ID exists in test-spec.md

Each gate returns a GateResult with passed: bool and errors: list[str]. Block on
errors at pre-push validation; warn on weak (vague but non-broken) references is
out of scope here — phase-review (skill) catches those.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .spec_parser import ParsedSpec, SpecParseError, parse_spec


_TEST_ID_REF_RE = re.compile(r"#\s*implements:\s*([^\n]+)")
_TEST_ID_RE = re.compile(r"\b(TEST-[a-z0-9][a-z0-9-]*-\d+)\b")


class GateError(Exception):
    """Raised when a gate cannot be executed (not the same as the gate failing)."""


@dataclass
class GateResult:
    """Outcome of running a phase gate."""

    gate_name: str
    feature_id: str
    passed: bool = True
    errors: list[str] = field(default_factory=list)


def _try_parse(path: Path, phase: str) -> tuple[ParsedSpec | None, str | None]:
    """Parse a spec; return (parsed, None) on success or (None, error_message) on failure."""
    try:
        return parse_spec(path, phase=phase), None
    except SpecParseError as e:
        return None, str(e)


def requirements_gate(feature_dir: Path, feature_id: str) -> GateResult:
    """Check requirements-spec.md exists, has feature-id, and declares at least one REQ-ID."""
    result = GateResult(gate_name="requirements", feature_id=feature_id)
    spec = feature_dir / "requirements-spec.md"

    parsed, err = _try_parse(spec, "requirements")
    if parsed is None:
        result.passed = False
        result.errors.append(f"requirements-spec.md: {err}")
        return result

    if parsed.feature_id != feature_id:
        result.passed = False
        result.errors.append(
            f"requirements-spec.md feature-id mismatch: expected {feature_id}, got {parsed.feature_id}"
        )
    if not parsed.declared_ids:
        result.passed = False
        result.errors.append(
            "requirements-spec.md declares no REQ-IDs (need at least one ### REQ-<feature>-NNN heading)"
        )

    return result


def design_gate(feature_dir: Path, feature_id: str) -> GateResult:
    """Check design-spec.md exists with valid satisfies references to requirements-spec."""
    result = GateResult(gate_name="design", feature_id=feature_id)

    req_spec = feature_dir / "requirements-spec.md"
    des_spec = feature_dir / "design-spec.md"

    req_parsed, req_err = _try_parse(req_spec, "requirements")
    if req_parsed is None:
        result.passed = False
        result.errors.append(f"requirements-spec.md (prerequisite): {req_err}")
        return result

    des_parsed, des_err = _try_parse(des_spec, "design")
    if des_parsed is None:
        result.passed = False
        result.errors.append(f"design-spec.md: {des_err}")
        return result

    if des_parsed.feature_id != feature_id:
        result.passed = False
        result.errors.append(
            f"design-spec.md feature-id mismatch: expected {feature_id}, got {des_parsed.feature_id}"
        )

    if not des_parsed.declared_ids:
        result.passed = False
        result.errors.append(
            "design-spec.md declares no DES-IDs (need at least one ### DES-<feature>-NNN heading)"
        )

    # Every satisfies reference must resolve to a declared REQ-ID
    for ref in sorted(des_parsed.references):
        if ref.startswith("REQ-") and ref not in req_parsed.declared_ids:
            result.passed = False
            result.errors.append(
                f"design-spec.md references {ref} which is not declared in requirements-spec.md"
            )

    return result


def test_gate(feature_dir: Path, feature_id: str) -> GateResult:
    """Check test-spec.md exists with valid satisfies references to both prior phases."""
    result = GateResult(gate_name="test", feature_id=feature_id)

    req_spec = feature_dir / "requirements-spec.md"
    des_spec = feature_dir / "design-spec.md"
    test_spec = feature_dir / "test-spec.md"

    req_parsed, req_err = _try_parse(req_spec, "requirements")
    if req_parsed is None:
        result.passed = False
        result.errors.append(f"requirements-spec.md (prerequisite): {req_err}")
        return result

    des_parsed, des_err = _try_parse(des_spec, "design")
    if des_parsed is None:
        result.passed = False
        result.errors.append(f"design-spec.md (prerequisite): {des_err}")
        return result

    test_parsed, test_err = _try_parse(test_spec, "test")
    if test_parsed is None:
        result.passed = False
        result.errors.append(f"test-spec.md: {test_err}")
        return result

    if test_parsed.feature_id != feature_id:
        result.passed = False
        result.errors.append(
            f"test-spec.md feature-id mismatch: expected {feature_id}, got {test_parsed.feature_id}"
        )

    if not test_parsed.declared_ids:
        result.passed = False
        result.errors.append(
            "test-spec.md declares no TEST-IDs (need at least one ### TEST-<feature>-NNN heading)"
        )

    for ref in sorted(test_parsed.references):
        if ref.startswith("REQ-") and ref not in req_parsed.declared_ids:
            result.passed = False
            result.errors.append(
                f"test-spec.md references {ref} which is not declared in requirements-spec.md"
            )
        elif ref.startswith("DES-") and ref not in des_parsed.declared_ids:
            result.passed = False
            result.errors.append(
                f"test-spec.md references {ref} which is not declared in design-spec.md"
            )

    return result


def code_gate(feature_dir: Path, feature_id: str, code_text: str) -> GateResult:
    """Check code_text has a TEST-ID annotation that resolves to test-spec.md."""
    result = GateResult(gate_name="code", feature_id=feature_id)

    test_spec = feature_dir / "test-spec.md"
    test_parsed, test_err = _try_parse(test_spec, "test")
    if test_parsed is None:
        result.passed = False
        result.errors.append(f"test-spec.md (prerequisite): {test_err}")
        return result

    # Find # implements: lines and the TEST-IDs in them
    cited_test_ids: set[str] = set()
    for match in _TEST_ID_REF_RE.finditer(code_text):
        for tid in _TEST_ID_RE.findall(match.group(1)):
            cited_test_ids.add(tid)

    if not cited_test_ids:
        result.passed = False
        result.errors.append(
            "code has no # implements: TEST-<feature>-NNN annotation"
        )
        return result

    for tid in sorted(cited_test_ids):
        if tid not in test_parsed.declared_ids:
            result.passed = False
            result.errors.append(
                f"code references {tid} which is not declared in test-spec.md"
            )

    return result
```

- [ ] **Step 5: Run tests, verify they pass**

```bash
python3 -m pytest tests/test_programme_gates.py -v
```

Expected: 11 passed.

- [ ] **Step 6: Lint**

```bash
python3 -m black --check plugins/sdlc-programme/scripts/programme/gates.py tests/test_programme_gates.py
python3 -m flake8 plugins/sdlc-programme/scripts/programme/gates.py tests/test_programme_gates.py
```

Apply black if needed.

- [ ] **Step 7: Commit**

```bash
git add plugins/sdlc-programme/scripts/programme/gates.py tests/test_programme_gates.py tests/fixtures/programme/
git commit -m "$(cat <<'EOF'
feat(programme): 4 phase-gate validators (Phase D task 5)

Four gate validators built on top of spec_parser:
- requirements_gate: checks requirements-spec exists, has feature-id, declares ≥1 REQ
- design_gate: checks design-spec exists; every satisfies-REQ reference resolves
  to a REQ declared in requirements-spec
- test_gate: checks test-spec exists; every satisfies-REQ + satisfies-DES
  reference resolves to a declared ID in the corresponding prior phase
- code_gate: checks code text has # implements: TEST-<feature>-NNN annotation
  that resolves to a TEST-ID declared in test-spec

Each gate returns a GateResult with passed: bool + errors: list[str].
Errors block at pre-push validation. Phase-review (Article 14) catches
weak (vague but non-broken) references — out of scope here.

11 unit tests covering: req-gate happy path, missing spec, design-gate
happy path, broken REQ ref, missing design-spec, test-gate happy path,
broken REQ ref, broken DES ref, code-gate happy path, broken TEST ref,
no annotation.

Test fixture at tests/fixtures/programme/feature-sample/ provides minimal
valid req-spec, design-spec, test-spec for the gate tests.

Phase D task 5 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: traceability module — export REQ↔DES↔TEST matrix

**Files:**
- Create: `plugins/sdlc-programme/scripts/programme/traceability.py`
- Create: `tests/test_programme_traceability.py`

The traceability module produces an audit-friendly matrix from a feature's three phase artefacts. Two formats: csv (one row per REQ, columns DES + TEST) and markdown (a rendered table). Phase E adds standard-specific formats; Phase D ships csv + markdown only.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_programme_traceability.py`:

```python
"""Tests for plugins.sdlc-programme.scripts.programme.traceability."""
import shutil
from pathlib import Path

import pytest

from sdlc_programme_scripts.programme.traceability import (
    TraceabilityError,
    build_matrix,
    export_csv,
    export_markdown,
)


REPO_ROOT = Path(__file__).parent.parent
SAMPLE_FEATURE = REPO_ROOT / "tests/fixtures/programme/feature-sample"


def _copy_feature(tmp_path: Path) -> Path:
    dst = tmp_path / "specs" / "sample"
    shutil.copytree(SAMPLE_FEATURE, dst)
    return dst


def test_build_matrix_returns_one_row_per_req(tmp_path: Path) -> None:
    """The matrix has one row per REQ with the DES and TEST IDs that satisfy it."""
    feature_dir = _copy_feature(tmp_path)

    matrix = build_matrix(feature_dir, "sample")

    assert len(matrix) == 2
    req_001 = next(row for row in matrix if row.req_id == "REQ-sample-001")
    assert req_001.des_ids == {"DES-sample-001"}
    assert req_001.test_ids == {"TEST-sample-001"}

    req_002 = next(row for row in matrix if row.req_id == "REQ-sample-002")
    assert req_002.des_ids == {"DES-sample-002"}
    assert req_002.test_ids == {"TEST-sample-002"}


def test_export_csv_produces_header_and_rows(tmp_path: Path) -> None:
    """export_csv produces a CSV string with header + one row per REQ."""
    feature_dir = _copy_feature(tmp_path)

    csv_text = export_csv(feature_dir, "sample")

    lines = csv_text.strip().split("\n")
    assert lines[0] == "REQ,DES,TEST"
    assert any("REQ-sample-001,DES-sample-001,TEST-sample-001" in line for line in lines[1:])
    assert any("REQ-sample-002,DES-sample-002,TEST-sample-002" in line for line in lines[1:])


def test_export_markdown_produces_table(tmp_path: Path) -> None:
    """export_markdown produces a markdown table with REQ + DES + TEST columns."""
    feature_dir = _copy_feature(tmp_path)

    md = export_markdown(feature_dir, "sample")

    assert "| REQ | DES | TEST |" in md
    assert "| --- | --- | --- |" in md
    assert "| REQ-sample-001 | DES-sample-001 | TEST-sample-001 |" in md
    assert "| REQ-sample-002 | DES-sample-002 | TEST-sample-002 |" in md


def test_build_matrix_orphan_req_appears_with_empty_des_test(tmp_path: Path) -> None:
    """A REQ with no DES/TEST satisfying it appears in the matrix with empty sets."""
    feature_dir = _copy_feature(tmp_path)
    # Add REQ-sample-003 that nothing satisfies
    req_spec = feature_dir / "requirements-spec.md"
    text = req_spec.read_text()
    text += "\n### REQ-sample-003\nUnsatisfied requirement.\n"
    req_spec.write_text(text)

    matrix = build_matrix(feature_dir, "sample")
    orphan = next(row for row in matrix if row.req_id == "REQ-sample-003")
    assert orphan.des_ids == set()
    assert orphan.test_ids == set()


def test_build_matrix_missing_artefact_raises(tmp_path: Path) -> None:
    """If a phase artefact is missing, traceability cannot be built."""
    feature_dir = _copy_feature(tmp_path)
    (feature_dir / "test-spec.md").unlink()

    with pytest.raises(TraceabilityError, match="test-spec.md"):
        build_matrix(feature_dir, "sample")
```

- [ ] **Step 2: Run tests, verify they fail**

```bash
python3 -m pytest tests/test_programme_traceability.py -v
```

Expected: FAIL with ModuleNotFoundError.

- [ ] **Step 3: Implement traceability.py**

Create `plugins/sdlc-programme/scripts/programme/traceability.py`:

```python
"""Build and export traceability matrix from a feature's phase artefacts.

The matrix is one row per REQ-ID, with the DES-IDs that satisfy it and the
TEST-IDs that satisfy it (transitively through the design-spec). Two export
formats: CSV (audit tooling) and markdown (review tooling).

Phase E (Assured bundle) extends with standard-specific formats (DO-178C RTM,
IEC 62304 matrix, ISO 26262 ASIL matrix, FDA DHF). Phase D ships csv + markdown.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .spec_parser import ParsedSpec, SpecParseError, parse_spec


class TraceabilityError(Exception):
    """Raised when a traceability matrix cannot be built."""


@dataclass
class TraceabilityRow:
    """One row of the traceability matrix — a REQ and what satisfies it."""

    req_id: str
    des_ids: set[str] = field(default_factory=set)
    test_ids: set[str] = field(default_factory=set)


def _load_phase(feature_dir: Path, phase: str, filename: str) -> ParsedSpec:
    path = feature_dir / filename
    try:
        return parse_spec(path, phase=phase)
    except SpecParseError as e:
        raise TraceabilityError(f"{filename}: {e}") from e


def _satisfies_for_des(des_spec_text: str) -> dict[str, set[str]]:
    """Map each DES-ID heading to the set of REQ-IDs in its **satisfies:** line.

    Walks the design-spec line-wise: when an ``### DES-...`` heading is found,
    the next ``**satisfies:**`` line within the section is parsed for REQ-IDs.
    """
    result: dict[str, set[str]] = {}
    current_des: str | None = None
    in_code_block = False

    heading_re = re.compile(r"^###\s+(DES-[a-z0-9][a-z0-9-]*-\d+)\b")
    satisfies_re = re.compile(r"^\*\*satisfies:\*\*\s+(.+)$")
    ref_re = re.compile(r"\b(REQ-[a-z0-9][a-z0-9-]*-\d+)\b")

    for line in des_spec_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        m = heading_re.match(line)
        if m:
            current_des = m.group(1)
            result.setdefault(current_des, set())
            continue

        s = satisfies_re.match(line)
        if s and current_des is not None:
            for req in ref_re.findall(s.group(1)):
                result[current_des].add(req)

    return result


def _satisfies_for_test(test_spec_text: str) -> dict[str, tuple[set[str], set[str]]]:
    """Map each TEST-ID to (REQ-IDs, DES-IDs) it satisfies.

    Walks line-wise like ``_satisfies_for_des`` but extracts both REQ and DES
    references from the ``**satisfies:**`` line of each TEST section.
    """
    result: dict[str, tuple[set[str], set[str]]] = {}
    current_test: str | None = None
    in_code_block = False

    heading_re = re.compile(r"^###\s+(TEST-[a-z0-9][a-z0-9-]*-\d+)\b")
    satisfies_re = re.compile(r"^\*\*satisfies:\*\*\s+(.+)$")
    req_re = re.compile(r"\b(REQ-[a-z0-9][a-z0-9-]*-\d+)\b")
    des_re = re.compile(r"\b(DES-[a-z0-9][a-z0-9-]*-\d+)\b")

    for line in test_spec_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        m = heading_re.match(line)
        if m:
            current_test = m.group(1)
            result.setdefault(current_test, (set(), set()))
            continue

        s = satisfies_re.match(line)
        if s and current_test is not None:
            reqs, dess = result[current_test]
            for req in req_re.findall(s.group(1)):
                reqs.add(req)
            for des in des_re.findall(s.group(1)):
                dess.add(des)

    return result


def build_matrix(feature_dir: Path, feature_id: str) -> list[TraceabilityRow]:
    """Build the traceability matrix as a list of rows ordered by REQ-ID."""
    req = _load_phase(feature_dir, "requirements", "requirements-spec.md")
    des = _load_phase(feature_dir, "design", "design-spec.md")
    test = _load_phase(feature_dir, "test", "test-spec.md")

    des_text = (feature_dir / "design-spec.md").read_text()
    test_text = (feature_dir / "test-spec.md").read_text()

    des_satisfies = _satisfies_for_des(des_text)
    test_satisfies = _satisfies_for_test(test_text)

    # Reverse-index: for each REQ, which DES-IDs satisfy it?
    req_to_des: dict[str, set[str]] = {r: set() for r in req.declared_ids}
    for des_id, reqs in des_satisfies.items():
        for r in reqs:
            req_to_des.setdefault(r, set()).add(des_id)

    # For each REQ, which TEST-IDs satisfy it directly OR via a satisfying DES?
    req_to_test: dict[str, set[str]] = {r: set() for r in req.declared_ids}
    for test_id, (reqs, dess) in test_satisfies.items():
        for r in reqs:
            req_to_test.setdefault(r, set()).add(test_id)
        # Transitive: if test satisfies DES, and DES satisfies REQ, then test → REQ
        for d in dess:
            for r, satisfying_des in req_to_des.items():
                if d in satisfying_des:
                    req_to_test.setdefault(r, set()).add(test_id)

    rows: list[TraceabilityRow] = []
    for r in sorted(req.declared_ids):
        rows.append(
            TraceabilityRow(
                req_id=r,
                des_ids=req_to_des.get(r, set()),
                test_ids=req_to_test.get(r, set()),
            )
        )
    return rows


def export_csv(feature_dir: Path, feature_id: str) -> str:
    """Export the matrix as CSV: one row per (REQ, DES, TEST) triple.

    Cartesian-product expansion: a REQ with 2 DES and 3 TEST yields up to 6 rows.
    Empty DES or TEST cells render as empty strings.
    """
    rows = build_matrix(feature_dir, feature_id)
    out_lines = ["REQ,DES,TEST"]
    for row in rows:
        des_list = sorted(row.des_ids) or [""]
        test_list = sorted(row.test_ids) or [""]
        for d in des_list:
            for t in test_list:
                out_lines.append(f"{row.req_id},{d},{t}")
    return "\n".join(out_lines) + "\n"


def export_markdown(feature_dir: Path, feature_id: str) -> str:
    """Export the matrix as a markdown table."""
    rows = build_matrix(feature_dir, feature_id)
    lines = ["| REQ | DES | TEST |", "| --- | --- | --- |"]
    for row in rows:
        des_list = sorted(row.des_ids) or [""]
        test_list = sorted(row.test_ids) or [""]
        for d in des_list:
            for t in test_list:
                lines.append(f"| {row.req_id} | {d} | {t} |")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run tests, verify they pass**

```bash
python3 -m pytest tests/test_programme_traceability.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Lint**

```bash
python3 -m black --check plugins/sdlc-programme/scripts/programme/traceability.py tests/test_programme_traceability.py
python3 -m flake8 plugins/sdlc-programme/scripts/programme/traceability.py tests/test_programme_traceability.py
```

- [ ] **Step 6: Commit**

```bash
git add plugins/sdlc-programme/scripts/programme/traceability.py tests/test_programme_traceability.py
git commit -m "$(cat <<'EOF'
feat(programme): traceability matrix builder + csv/markdown exporters (Phase D task 6)

build_matrix produces a list of TraceabilityRow (one per REQ-ID, with
the DES-IDs and TEST-IDs that satisfy it). The transitive resolution
walks through DES → REQ to compute REQ → TEST coverage even when a
test references the design-element rather than the requirement directly.

Two export formats:
- export_csv: cartesian-product expansion (REQ with 2 DES and 3 TEST
  yields up to 6 rows). Audit tooling ingests this.
- export_markdown: rendered table for review tooling.

Phase E (Assured bundle) adds standard-specific formats (DO-178C RTM,
IEC 62304, ISO 26262 ASIL matrix, FDA DHF). Phase D ships csv + markdown.

5 unit tests covering: matrix has row-per-REQ, csv format, markdown
format, orphan-REQ (no satisfying DES/TEST), missing artefact raises.

Phase D task 6 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: phase-init skill

**Files:**
- Create: `skills/phase-init/SKILL.md` (root source)
- Create: `plugins/sdlc-programme/skills/phase-init/SKILL.md` (plugin mirror)

`phase-init <phase> <feature-id>` instantiates a phase artefact from the bundle's template into `docs/specs/<feature-id>/<phase>-spec.md`. Refuses to overwrite an existing artefact.

- [ ] **Step 1: Create the skill**

Create `skills/phase-init/SKILL.md`:

```markdown
---
name: phase-init
description: Instantiate a phase artefact (requirements-spec / design-spec / test-spec) from the Programme bundle's template into docs/specs/<feature-id>/. Refuses to overwrite existing artefacts.
disable-model-invocation: false
argument-hint: "<phase> <feature-id>"
---

# Initialise a Phase Artefact

Instantiate a phase artefact from the Programme bundle's template.

## Arguments

- `<phase>` — one of `requirements`, `design`, `test`
- `<feature-id>` — short slug for the feature (e.g., `oauth-flow`, `cross-library-query`)

## Steps

\`\`\`bash
PHASE="$1"
FEATURE_ID="$2"

if [ -z "$PHASE" ] || [ -z "$FEATURE_ID" ]; then
    echo "Usage: phase-init <phase> <feature-id>" >&2
    exit 1
fi

case "$PHASE" in
    requirements|design|test) ;;
    *)
        echo "phase must be one of: requirements, design, test" >&2
        exit 1
        ;;
esac

# Validate feature-id format (lowercase alphanumeric + hyphens, starting with alpha-numeric)
if ! echo "$FEATURE_ID" | grep -qE '^[a-z0-9][a-z0-9-]*$'; then
    echo "feature-id must match /^[a-z0-9][a-z0-9-]*$/" >&2
    exit 1
fi

FEATURE_DIR="docs/specs/$FEATURE_ID"
SPEC_PATH="$FEATURE_DIR/$PHASE-spec.md"

if [ -f "$SPEC_PATH" ]; then
    echo "$SPEC_PATH already exists; refusing to overwrite" >&2
    exit 1
fi

mkdir -p "$FEATURE_DIR"

# Locate the template — try project-installed first (./.sdlc/templates/), then fallback to plugin
if [ -f ".sdlc/templates/$PHASE-spec.md" ]; then
    TEMPLATE=".sdlc/templates/$PHASE-spec.md"
elif [ -f "$CLAUDE_PLUGIN_ROOT/templates/$PHASE-spec.md" ]; then
    TEMPLATE="$CLAUDE_PLUGIN_ROOT/templates/$PHASE-spec.md"
else
    echo "template for phase '$PHASE' not found (looked in .sdlc/templates/ and \$CLAUDE_PLUGIN_ROOT/templates/)" >&2
    exit 1
fi

# Copy template; substitute the feature-id placeholder
sed "s/<feature-id>/$FEATURE_ID/g" "$TEMPLATE" > "$SPEC_PATH"

echo "Created $SPEC_PATH from $TEMPLATE"
echo "Edit the file, then run: phase-gate $PHASE $FEATURE_ID"
\`\`\`

## Done

Report:

- File created: `docs/specs/<feature-id>/<phase>-spec.md`
- Source template: shown in output
- Next step: edit the file, then `phase-gate <phase> <feature-id>`

## Model selection

This skill is mechanical (file copy + sed substitution). Smaller models are sufficient.
```

- [ ] **Step 2: Mirror to plugin**

```bash
mkdir -p plugins/sdlc-programme/skills/phase-init
cp skills/phase-init/SKILL.md plugins/sdlc-programme/skills/phase-init/SKILL.md
diff skills/phase-init/SKILL.md plugins/sdlc-programme/skills/phase-init/SKILL.md
```

Diff should be empty.

- [ ] **Step 3: Commit**

```bash
git add skills/phase-init/SKILL.md plugins/sdlc-programme/skills/phase-init/SKILL.md
git commit -m "$(cat <<'EOF'
feat(programme): phase-init skill — instantiate phase artefact from template (Phase D task 7)

phase-init <phase> <feature-id>:
- Validates phase ∈ {requirements, design, test}
- Validates feature-id format (/^[a-z0-9][a-z0-9-]*$/)
- Refuses to overwrite an existing artefact at docs/specs/<feature-id>/<phase>-spec.md
- Locates template at .sdlc/templates/<phase>-spec.md (project) or
  $CLAUDE_PLUGIN_ROOT/templates/<phase>-spec.md (plugin fallback)
- sed-substitutes <feature-id> placeholder in the template
- Reports the next step (phase-gate <phase> <feature-id>)

Skills root + plugin mirror byte-identical.

Phase D task 7 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: phase-gate skill

**Files:**
- Create: `skills/phase-gate/SKILL.md` (root source)
- Create: `plugins/sdlc-programme/skills/phase-gate/SKILL.md` (plugin mirror)

`phase-gate <phase> <feature-id>` runs the corresponding gate validator and reports pass/fail with broken-reference details.

- [ ] **Step 1: Create the skill**

Create `skills/phase-gate/SKILL.md`:

```markdown
---
name: phase-gate
description: Run a Programme phase gate validator (requirements / design / test / code) against docs/specs/<feature-id>/. Block on missing artefact or broken cross-phase reference.
disable-model-invocation: false
argument-hint: "<phase> <feature-id> [code-file-glob-for-code-gate]"
---

# Run a Phase Gate

Run the named gate validator against a feature's phase artefacts.

## Arguments

- `<phase>` — one of `requirements`, `design`, `test`, `code`
- `<feature-id>` — short slug for the feature
- `[code-file-glob]` — only required when `<phase>` is `code`; e.g., `src/**/*.py`

## Steps

\`\`\`bash
PHASE="$1"
FEATURE_ID="$2"
CODE_GLOB="${3:-}"

if [ -z "$PHASE" ] || [ -z "$FEATURE_ID" ]; then
    echo "Usage: phase-gate <phase> <feature-id> [code-file-glob]" >&2
    exit 1
fi

case "$PHASE" in
    requirements|design|test|code) ;;
    *)
        echo "phase must be one of: requirements, design, test, code" >&2
        exit 1
        ;;
esac

FEATURE_DIR="docs/specs/$FEATURE_ID"

if [ "$PHASE" = "code" ] && [ -z "$CODE_GLOB" ]; then
    echo "code phase requires a code-file-glob (e.g., 'src/**/*.py')" >&2
    exit 1
fi

python3 << PYEOF
from pathlib import Path
from sdlc_programme_scripts.programme.gates import (
    code_gate, design_gate, requirements_gate, test_gate,
)

phase = "$PHASE"
feature_id = "$FEATURE_ID"
feature_dir = Path("$FEATURE_DIR")

if phase == "requirements":
    result = requirements_gate(feature_dir, feature_id)
elif phase == "design":
    result = design_gate(feature_dir, feature_id)
elif phase == "test":
    result = test_gate(feature_dir, feature_id)
elif phase == "code":
    code_glob = "$CODE_GLOB"
    code_text = ""
    for path in Path().glob(code_glob):
        if path.is_file():
            code_text += path.read_text() + "\n"
    result = code_gate(feature_dir, feature_id, code_text=code_text)

if result.passed:
    print(f"PASS: {result.gate_name}-gate for feature {result.feature_id}")
    raise SystemExit(0)
else:
    print(f"FAIL: {result.gate_name}-gate for feature {result.feature_id}")
    for err in result.errors:
        print(f"  - {err}")
    raise SystemExit(1)
PYEOF
\`\`\`

## Done

Report:

- Gate name and feature-id
- PASS or FAIL
- For FAIL: each broken reference / missing artefact

If FAIL, the user must fix the cited issues before commit/push. The same gates run at pre-push validation.

## Model selection

This skill runs deterministic Python validators. Smaller models are sufficient.
```

- [ ] **Step 2: Mirror to plugin**

```bash
mkdir -p plugins/sdlc-programme/skills/phase-gate
cp skills/phase-gate/SKILL.md plugins/sdlc-programme/skills/phase-gate/SKILL.md
```

- [ ] **Step 3: Commit**

```bash
git add skills/phase-gate/SKILL.md plugins/sdlc-programme/skills/phase-gate/SKILL.md
git commit -m "$(cat <<'EOF'
feat(programme): phase-gate skill — run gate validator and report (Phase D task 8)

phase-gate <phase> <feature-id> [code-glob] runs the named gate validator
from sdlc_programme_scripts.programme.gates against docs/specs/<feature-id>/
and reports PASS or FAIL with broken-reference details.

For phase=code, a code-file-glob argument is required; the skill reads
all files matching the glob and feeds their content to code_gate.

Skills root + plugin mirror byte-identical.

Phase D task 8 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: phase-review skill (mandatory for design-spec and test-spec)

**Files:**
- Create: `skills/phase-review/SKILL.md` (root source)
- Create: `plugins/sdlc-programme/skills/phase-review/SKILL.md` (plugin mirror)

`phase-review <phase> <feature-id>` dispatches a structured review of the artefact against its cited prior artefacts. Programme constitution Article 14 makes this MANDATORY for design-spec and test-spec phases.

- [ ] **Step 1: Create the skill**

Create `skills/phase-review/SKILL.md`:

```markdown
---
name: phase-review
description: Dispatch a structured cross-phase review of a phase artefact. MANDATORY for design-spec and test-spec; the gate validator checks for the resulting review record before passing. Recommended for requirements-spec.
disable-model-invocation: false
argument-hint: "<phase> <feature-id>"
---

# Cross-Phase Review

Dispatch a structured review of a phase artefact against its cited prior artefacts.

## Arguments

- `<phase>` — one of `requirements`, `design`, `test`
- `<feature-id>` — short slug for the feature

## Why this is mandatory for design and test

`phase-gate` checks structure: do citations resolve to declared IDs? `phase-review` checks meaning: do the citations actually capture the requirement / design intent? Programme Article 14 requires the review record for design-spec and test-spec — the gate validator looks for `docs/specs/<feature-id>/reviews/<phase>-review-*.md` before passing.

## Steps

\`\`\`bash
PHASE="$1"
FEATURE_ID="$2"

if [ -z "$PHASE" ] || [ -z "$FEATURE_ID" ]; then
    echo "Usage: phase-review <phase> <feature-id>" >&2
    exit 1
fi

case "$PHASE" in
    requirements|design|test) ;;
    *)
        echo "phase must be one of: requirements, design, test" >&2
        exit 1
        ;;
esac

FEATURE_DIR="docs/specs/$FEATURE_ID"
SPEC_PATH="$FEATURE_DIR/$PHASE-spec.md"

if [ ! -f "$SPEC_PATH" ]; then
    echo "$SPEC_PATH does not exist; run phase-init $PHASE $FEATURE_ID first" >&2
    exit 1
fi

REVIEWS_DIR="$FEATURE_DIR/reviews"
mkdir -p "$REVIEWS_DIR"

# Determine reviewer agent based on phase
case "$PHASE" in
    requirements)
        REVIEWER_AGENT="sdlc-team-common:solution-architect"
        REVIEWER_LABEL="solution-architect"
        ;;
    design)
        REVIEWER_AGENT="sdlc-team-common:solution-architect"
        REVIEWER_LABEL="solution-architect"
        ;;
    test)
        REVIEWER_AGENT="sdlc-team-fullstack:backend-architect"
        REVIEWER_LABEL="backend-architect"
        ;;
esac

REVIEW_PATH="$REVIEWS_DIR/$PHASE-review-$REVIEWER_LABEL.md"
\`\`\`

Now use the `Agent` tool to dispatch `$REVIEWER_AGENT` (substituting the value from the bash variable) with this prompt:

\`\`\`
You are reviewing a $PHASE-spec for feature $FEATURE_ID.

Read the artefact at: $SPEC_PATH

Required prior artefacts to read:
- For design phase: docs/specs/$FEATURE_ID/requirements-spec.md (the requirements being satisfied)
- For test phase: both docs/specs/$FEATURE_ID/requirements-spec.md AND docs/specs/$FEATURE_ID/design-spec.md

Your review must answer:

1. **Coverage**: are all REQ-IDs from the prior phase(s) addressed by this artefact's elements?
2. **Soundness**: do the satisfies references make semantic sense — does each cited DES/TEST actually address what the cited REQ/DES says?
3. **Completeness**: are there obvious requirements / design elements missing that should have been declared?
4. **Out-of-scope cleanliness**: does the artefact stay within scope, or does it sneak in elements that don't trace back?

Return your review as a markdown file with these sections:
- ## Reviewer
- ## Coverage assessment
- ## Soundness assessment
- ## Completeness assessment
- ## Out-of-scope concerns
- ## Verdict: APPROVE / NEEDS-REWORK / NOT-APPROVED

Save the review to: $REVIEW_PATH (use the Write tool)
\`\`\`

After the agent dispatch completes, verify the review file was created:

\`\`\`bash
if [ -f "$REVIEW_PATH" ]; then
    echo "Review record created at $REVIEW_PATH"
    git add "$REVIEW_PATH"
    echo "Stage the review record with the next commit."
else
    echo "ERROR: $REVIEW_PATH was not created" >&2
    exit 1
fi
\`\`\`

## Done

Report:

- Phase artefact reviewed
- Reviewer agent used (`solution-architect` for design; `backend-architect` for test)
- Review record path
- Verdict from the review (APPROVE / NEEDS-REWORK / NOT-APPROVED)

If verdict is NEEDS-REWORK or NOT-APPROVED, the user must address the review's findings before commit/push.

## Model selection

This skill is **structured comparison and reasoning** — comparing artefacts against prior phases, surfacing semantic gaps. Prefer a model with strong reasoning over one optimised for throughput. Reviewer agents (`solution-architect`, `backend-architect`) are dispatched via the Agent tool; they should run on a high-quality model.
```

- [ ] **Step 2: Mirror to plugin**

```bash
mkdir -p plugins/sdlc-programme/skills/phase-review
cp skills/phase-review/SKILL.md plugins/sdlc-programme/skills/phase-review/SKILL.md
```

- [ ] **Step 3: Commit**

```bash
git add skills/phase-review/SKILL.md plugins/sdlc-programme/skills/phase-review/SKILL.md
git commit -m "$(cat <<'EOF'
feat(programme): phase-review skill — mandatory cross-phase review for design and test (Phase D task 9)

phase-review <phase> <feature-id> dispatches a structured review of the
phase artefact against its cited prior artefacts. Programme Article 14
makes this MANDATORY for design-spec and test-spec; the gate validator
looks for docs/specs/<feature-id>/reviews/<phase>-review-*.md before
passing.

Reviewer agent dispatch:
- design phase → sdlc-team-common:solution-architect
- test phase → sdlc-team-fullstack:backend-architect
- requirements phase (recommended, not mandatory) → solution-architect

Reviewer answers 4 questions: Coverage, Soundness, Completeness,
Out-of-scope. Verdict labels: APPROVE / NEEDS-REWORK / NOT-APPROVED.

Skills root + plugin mirror byte-identical.

Phase D task 9 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 10: traceability-export skill

**Files:**
- Create: `skills/traceability-export/SKILL.md` (root source)
- Create: `plugins/sdlc-programme/skills/traceability-export/SKILL.md` (plugin mirror)

`traceability-export <format> <feature-id>` produces an audit-friendly traceability matrix. Phase D ships csv + markdown formats.

- [ ] **Step 1: Create the skill**

Create `skills/traceability-export/SKILL.md`:

```markdown
---
name: traceability-export
description: Export the REQ↔DES↔TEST traceability matrix for a feature in csv or markdown format. Phase D ships csv + markdown; Phase E (Assured) extends with standard-specific formats.
disable-model-invocation: false
argument-hint: "<format> <feature-id> [output-path]"
---

# Export Traceability Matrix

Produce an audit-friendly REQ↔DES↔TEST traceability matrix.

## Arguments

- `<format>` — `csv` or `markdown`
- `<feature-id>` — short slug for the feature
- `[output-path]` — optional. Defaults to `docs/specs/<feature-id>/traceability.<ext>` where `.ext` is `.csv` or `.md`.

## Steps

\`\`\`bash
FORMAT="$1"
FEATURE_ID="$2"
OUTPUT_PATH="${3:-}"

if [ -z "$FORMAT" ] || [ -z "$FEATURE_ID" ]; then
    echo "Usage: traceability-export <format> <feature-id> [output-path]" >&2
    exit 1
fi

case "$FORMAT" in
    csv|markdown) ;;
    *)
        echo "format must be one of: csv, markdown" >&2
        exit 1
        ;;
esac

FEATURE_DIR="docs/specs/$FEATURE_ID"

if [ -z "$OUTPUT_PATH" ]; then
    case "$FORMAT" in
        csv) OUTPUT_PATH="$FEATURE_DIR/traceability.csv" ;;
        markdown) OUTPUT_PATH="$FEATURE_DIR/traceability.md" ;;
    esac
fi

python3 << PYEOF
from pathlib import Path
from sdlc_programme_scripts.programme.traceability import (
    TraceabilityError, export_csv, export_markdown,
)

format = "$FORMAT"
feature_id = "$FEATURE_ID"
feature_dir = Path("$FEATURE_DIR")
output_path = Path("$OUTPUT_PATH")

try:
    if format == "csv":
        text = export_csv(feature_dir, feature_id)
    elif format == "markdown":
        text = export_markdown(feature_dir, feature_id)
except TraceabilityError as e:
    print(f"ERROR: {e}", flush=True)
    raise SystemExit(1)

output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(text)
print(f"Wrote {format} traceability matrix to {output_path}")
PYEOF
\`\`\`

## Done

Report:

- Format used (csv or markdown)
- Output path
- Number of REQ rows in the matrix
- Any orphan REQs (declared but no DES/TEST satisfying them) — these are coverage gaps the team should resolve

## Model selection

This skill runs deterministic Python helpers. Smaller models are sufficient.
```

- [ ] **Step 2: Mirror to plugin**

```bash
mkdir -p plugins/sdlc-programme/skills/traceability-export
cp skills/traceability-export/SKILL.md plugins/sdlc-programme/skills/traceability-export/SKILL.md
```

- [ ] **Step 3: Commit**

```bash
git add skills/traceability-export/SKILL.md plugins/sdlc-programme/skills/traceability-export/SKILL.md
git commit -m "$(cat <<'EOF'
feat(programme): traceability-export skill — csv + markdown matrix (Phase D task 10)

traceability-export <format> <feature-id> [output-path] writes the
REQ↔DES↔TEST traceability matrix for a feature.

Formats supported in Phase D: csv (audit tooling), markdown (review
tooling). Phase E (Assured bundle) adds standard-specific formats
(DO-178C RTM, IEC 62304 matrix, ISO 26262 ASIL matrix, FDA DHF).

Default output path is docs/specs/<feature-id>/traceability.<ext>.

Skills root + plugin mirror byte-identical.

Phase D task 10 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 11: commission-programme skill

**Files:**
- Create: `skills/commission-programme/SKILL.md` (root source)
- Create: `plugins/sdlc-programme/skills/commission-programme/SKILL.md` (plugin mirror)

`commission-programme` is the bundle-specific commissioning entry point: alternative to `/sdlc-core:commission --option programme`. Tailored audience-specific guidance.

- [ ] **Step 1: Create the skill**

Create `skills/commission-programme/SKILL.md`:

```markdown
---
name: commission-programme
description: Commission a project to the Programme SDLC bundle. Tailored entry point with Programme-specific audience guidance; equivalent to /sdlc-core:commission --option programme.
disable-model-invocation: true
argument-hint: "[--level production|enterprise]"
---

# Commission to Programme

Install the `sdlc-programme` bundle into a project. Use this when:

- Team size 11-50 across 2-5 teams
- Specification maturity is formal or contract-first
- Blast radius is moderate-to-high
- Audit-friendly traceability matters but full regulated-industry traceability does not

For other team shapes:

- 1-2 person projects → use `commission-solo` (or `/sdlc-core:commission --option solo`)
- 3-10 person product teams → use the framework default (no commissioning needed)
- Regulated industries → use `commission-assured` (Phase E, future)

## Steps

\`\`\`bash
LEVEL="${1:-production}"  # default production for Programme

if [ -n "$1" ] && [ "$1" != "--level" ]; then
    echo "Usage: commission-programme [--level production|enterprise]" >&2
    exit 1
fi
LEVEL="${2:-production}"

case "$LEVEL" in
    production|enterprise) ;;
    *)
        echo "Programme supports levels: production, enterprise" >&2
        exit 1
        ;;
esac

# Delegate to sdlc-core:commission with --option programme --level <LEVEL> --bundle-dir <Programme bundle path>
PROJECT_DIR=$(pwd)
BUNDLE_DIR="$CLAUDE_PLUGIN_ROOT"  # the sdlc-programme plugin's own root inside the container/install

# Sanity check the bundle dir
if [ ! -f "$BUNDLE_DIR/manifest.yaml" ]; then
    echo "Programme bundle manifest not found at $BUNDLE_DIR/manifest.yaml" >&2
    exit 1
fi

python3 << PYEOF
from datetime import datetime, timezone
from pathlib import Path

from sdlc_core_scripts.commission.installer import install_bundle
from sdlc_core_scripts.commission.manifest import parse_manifest
from sdlc_core_scripts.commission.recorder import (
    CommissioningRecord, is_commissioned, write_record,
)

bundle_dir = Path("$BUNDLE_DIR")
project_dir = Path("$PROJECT_DIR")
team_config = project_dir / ".sdlc" / "team-config.json"

manifest = parse_manifest(bundle_dir / "manifest.yaml")

constitution = project_dir / "CONSTITUTION.md"
overwrite = is_commissioned(team_config)
if constitution.exists() and not overwrite:
    print(f"WARNING: {constitution} exists and project is uncommissioned.")
    response = input("Replace existing constitution and commission to Programme? [y/N] ")
    if response.lower() != "y":
        print("Aborted.")
        raise SystemExit(1)
    overwrite = True

result = install_bundle(bundle_dir, project_dir, manifest, overwrite=overwrite)
print(f"Installed {len(result.installed_paths)} files")

record = CommissioningRecord(
    sdlc_option="programme",
    sdlc_level="$LEVEL",
    commissioned_at=datetime.now(timezone.utc).isoformat(),
    commissioned_by="claude-agent",
    option_bundle_version=manifest.version,
)
write_record(team_config, record)
print(f"Commissioned: programme / $LEVEL / {manifest.version}")
PYEOF
\`\`\`

## Done

Report:

- Bundle installed: `programme v0.1.0`
- Files written: count + key paths (CONSTITUTION.md, .claude/skills/, .sdlc/templates/)
- Commissioning record at: `.sdlc/team-config.json`
- Next steps:
  1. Read the new `CONSTITUTION.md` — it adds Programme-specific articles 12-14
  2. For your first feature, run: `phase-init requirements <feature-id>`
  3. Edit the requirements-spec, then `phase-gate requirements <feature-id>`
  4. Continue through design, test, and code phases

## Model selection

This skill is mostly mechanical (file copies, JSON writes). A smaller model is sufficient.
```

- [ ] **Step 2: Mirror to plugin**

```bash
mkdir -p plugins/sdlc-programme/skills/commission-programme
cp skills/commission-programme/SKILL.md plugins/sdlc-programme/skills/commission-programme/SKILL.md
```

- [ ] **Step 3: Commit**

```bash
git add skills/commission-programme/SKILL.md plugins/sdlc-programme/skills/commission-programme/SKILL.md
git commit -m "$(cat <<'EOF'
feat(programme): commission-programme skill — tailored bundle commissioning (Phase D task 11)

commission-programme [--level production|enterprise] is the bundle-specific
commissioning entry point. Equivalent to /sdlc-core:commission --option programme
but with Programme-specific audience guidance (when to use / when not to use).

Default level is production (Programme is overkill for prototype).

Reuses sdlc_core_scripts.commission.{installer,recorder} from Phase C —
no new commissioning logic; just bundle-tailored UX.

disable-model-invocation: true (high-stakes operation; explicit invocation only).

Skills root + plugin mirror byte-identical.

Phase D task 11 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: Plugin packaging — release-mapping.yaml + marketplace.json

**Files:**
- Modify: `release-mapping.yaml`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Add sdlc-programme to release-mapping.yaml**

Find the bottom of `release-mapping.yaml`. Add a new top-level key:

```yaml

sdlc-programme:
  skills:
    - source: skills/commission-programme/SKILL.md
    - source: skills/phase-init/SKILL.md
    - source: skills/phase-gate/SKILL.md
    - source: skills/phase-review/SKILL.md
    - source: skills/traceability-export/SKILL.md
  templates:
    - source: plugins/sdlc-programme/templates/requirements-spec.md
    - source: plugins/sdlc-programme/templates/design-spec.md
    - source: plugins/sdlc-programme/templates/test-spec.md
  scripts:
    - source: plugins/sdlc-programme/scripts/__init__.py
    - source: plugins/sdlc-programme/scripts/programme/__init__.py
    - source: plugins/sdlc-programme/scripts/programme/spec_parser.py
    - source: plugins/sdlc-programme/scripts/programme/gates.py
    - source: plugins/sdlc-programme/scripts/programme/traceability.py
  bundle:
    - source: plugins/sdlc-programme/manifest.yaml
    - source: plugins/sdlc-programme/CONSTITUTION.md
    - source: plugins/sdlc-programme/README.md
    - source: plugins/sdlc-programme/pyproject.toml
```

(If the existing release-mapping doesn't have a `bundle:` sub-key for top-level bundle artefacts, look at how `sdlc-knowledge-base` packages its top-level `README.md` and `pyproject.toml` and follow that pattern.)

- [ ] **Step 2: Add sdlc-programme to marketplace.json**

Edit `.claude-plugin/marketplace.json`. Add a new entry to the `plugins` array:

```json
{ "name": "sdlc-programme", "source": "./plugins/sdlc-programme", "description": "Programme SDLC bundle — formal waterfall phase gates with mandatory cross-phase review (Method 1 substrate)", "version": "0.1.0" }
```

Insert this after the existing `sdlc-knowledge-base` entry (alphabetical-ish ordering).

- [ ] **Step 3: Verify packaging**

```bash
python3 tools/validation/check-plugin-packaging.py
```

Expected: `Plugin packaging check PASSED — 13 plugin(s) verified.` (was 12; added sdlc-programme).

If it fails, the most likely issue is that some source file in `release-mapping.yaml` doesn't exist OR a plugin-dir copy is missing. Diagnose and fix — this validator is exact about the source-to-plugin mapping.

- [ ] **Step 4: Validation**

```bash
python3 tools/validation/local-validation.py --quick
```

Expected: PASSED.

- [ ] **Step 5: Commit**

```bash
git add release-mapping.yaml .claude-plugin/marketplace.json
git commit -m "$(cat <<'EOF'
chore(programme): plugin packaging — release-mapping + marketplace (Phase D task 12)

Adds sdlc-programme to release-mapping.yaml (skills, templates, scripts,
bundle artefacts) and to .claude-plugin/marketplace.json (v0.1.0 entry).

check-plugin-packaging.py now passes 13/13 (was 12; sdlc-programme added).

Phase D task 12 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 13: End-to-end skill integration test

**Files:**
- Create: `tests/test_programme_skill_integration.py`

The integration test exercises the full bash flow inside the Programme skills, mirroring the Phase C task 8 pattern but for Programme.

- [ ] **Step 1: Write the test**

Create `tests/test_programme_skill_integration.py`:

```python
"""End-to-end tests of the Programme bundle skill flows.

Each test simulates the bash flow inside a Programme skill by invoking
the same Python helpers that the skill's bash snippets call. This catches
gaps between the helpers and the skill flow.
"""
import shutil
from pathlib import Path

import pytest

from sdlc_programme_scripts.programme.gates import (
    code_gate, design_gate, requirements_gate, test_gate,
)
from sdlc_programme_scripts.programme.traceability import (
    build_matrix, export_csv, export_markdown,
)


REPO_ROOT = Path(__file__).parent.parent
SAMPLE_FEATURE = REPO_ROOT / "tests/fixtures/programme/feature-sample"
PROGRAMME_TEMPLATES = REPO_ROOT / "plugins/sdlc-programme/templates"


def _new_project(tmp_path: Path) -> Path:
    """Create a project dir with .sdlc/templates/ populated from the Programme bundle."""
    project = tmp_path / "project"
    project.mkdir()
    (project / ".sdlc" / "templates").mkdir(parents=True)
    for tpl in PROGRAMME_TEMPLATES.iterdir():
        shutil.copy2(tpl, project / ".sdlc" / "templates" / tpl.name)
    return project


def test_phase_init_creates_artefact_from_template(tmp_path: Path) -> None:
    """phase-init copies the template into docs/specs/<feature-id>/<phase>-spec.md
    with the feature-id substituted."""
    project = _new_project(tmp_path)
    feature_id = "test-feature"

    # Simulate phase-init bash
    feature_dir = project / "docs" / "specs" / feature_id
    feature_dir.mkdir(parents=True)
    template = project / ".sdlc" / "templates" / "requirements-spec.md"
    spec_path = feature_dir / "requirements-spec.md"
    spec_path.write_text(template.read_text().replace("<feature-id>", feature_id))

    assert spec_path.exists()
    text = spec_path.read_text()
    assert "<feature-id>" not in text
    # The template's example REQ heading uses <feature-id>, so it should now read REQ-test-feature-001
    assert "REQ-test-feature-001" in text


def test_phase_gate_requirements_passes_on_filled_template(tmp_path: Path) -> None:
    """A requirements-spec with a filled feature-id and at least one REQ heading passes."""
    project = _new_project(tmp_path)
    feature_id = "good-feature"

    feature_dir = project / "docs" / "specs" / feature_id
    feature_dir.mkdir(parents=True)
    feature_dir.joinpath("requirements-spec.md").write_text(
        "**Feature-id:** good-feature\n\n"
        "## Motivation\nWhy.\n\n"
        "## Requirements\n\n"
        "### REQ-good-feature-001\nThe thing.\n"
    )

    result = requirements_gate(feature_dir, feature_id)
    assert result.passed is True


def test_full_phase_chain_against_sample_feature(tmp_path: Path) -> None:
    """The sample feature fixture passes all four gates including code-gate
    when given valid code text."""
    feature_dir = tmp_path / "specs" / "sample"
    shutil.copytree(SAMPLE_FEATURE, feature_dir)

    assert requirements_gate(feature_dir, "sample").passed is True
    assert design_gate(feature_dir, "sample").passed is True
    assert test_gate(feature_dir, "sample").passed is True

    code_text = "def thing_one():\n    # implements: TEST-sample-001\n    return 1\n"
    assert code_gate(feature_dir, "sample", code_text=code_text).passed is True


def test_traceability_export_against_sample_feature(tmp_path: Path) -> None:
    """The sample feature fixture exports a non-empty traceability matrix in both formats."""
    feature_dir = tmp_path / "specs" / "sample"
    shutil.copytree(SAMPLE_FEATURE, feature_dir)

    matrix = build_matrix(feature_dir, "sample")
    assert len(matrix) >= 2

    csv_text = export_csv(feature_dir, "sample")
    assert "REQ-sample-001" in csv_text
    assert "DES-sample-001" in csv_text
    assert "TEST-sample-001" in csv_text

    md_text = export_markdown(feature_dir, "sample")
    assert "| REQ | DES | TEST |" in md_text
    assert "| REQ-sample-001 |" in md_text
```

- [ ] **Step 2: Run the test**

```bash
python3 -m pytest tests/test_programme_skill_integration.py -v
```

Expected: 4 passed.

- [ ] **Step 3: Run all programme tests together**

```bash
python3 -m pytest tests/test_programme_*.py -v
```

Expected: 27 passed (7 spec_parser + 11 gates + 5 traceability + 4 integration).

- [ ] **Step 4: Commit**

```bash
git add tests/test_programme_skill_integration.py
git commit -m "$(cat <<'EOF'
test(programme): end-to-end skill integration tests (Phase D task 13)

Four integration tests exercising the Programme skill flows:
- phase-init: template copy + feature-id substitution
- phase-gate requirements: passes on a filled-template artefact
- full phase chain: sample fixture passes all four gates including code-gate
- traceability-export: csv + markdown produced from sample fixture

Phase D test count: 27 (7 spec_parser + 11 gates + 5 traceability + 4 integration).

Phase D task 13 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Containerised architect review of the Programme bundle design

**Files:**
- Create: `research/sdlc-bundles/dogfood-workflows/programme-bundle-review.md`
- Create: `research/sdlc-bundles/dogfood-workflows/programme-bundle-review.yaml`
- Capture: `research/sdlc-bundles/dogfood-workflows/programme-bundle-review-output.md`

Per `feedback_containerised_review_for_design_artefacts.md`, load-bearing design artefacts go through containerised review by default. The Programme bundle is load-bearing — Phase E (Assured) layers on top of it.

- [ ] **Step 1: Author the workflow command**

Create `research/sdlc-bundles/dogfood-workflows/programme-bundle-review.md` modeled on the bundle-contract-review pattern from Phase C task 10.

The agent under dispatch is `sdlc-team-common:solution-architect`. Reviewing target: the Programme bundle (manifest, constitution, templates, gates, skills) committed in Phase D tasks 1-13.

Brief the agent to answer:

1. **Constitution overlay soundness**: Articles 12-14 extend the universal constitution. Are the new articles well-bounded, internally consistent with articles 1-11, and free of obvious gaps?
2. **Phase artefact templates fitness**: do the three templates produce artefacts that the gates can actually validate? Any template structures that gates would need to special-case?
3. **Gate validator robustness**: do the gates catch the kinds of broken-reference issue regulated-industry teams would care about? Where might they false-positive or false-negative?
4. **Phase-review skill realism**: is dispatching `solution-architect` (design phase) and `backend-architect` (test phase) the right architectural choice? What's missing if the project doesn't have those agents installed?
5. **Bundle layout vs Phase C contract**: does the actual Programme bundle layout match what the bundle contract specifies (`docs/architecture/option-bundle-contract.md`)? Any divergences?

- [ ] **Step 2: Author the workflow YAML**

Create `research/sdlc-bundles/dogfood-workflows/programme-bundle-review.yaml`:

```yaml
name: programme-bundle-review
description: |
  Independent containerised architect review of the Programme bundle (Phase D
  deliverable). Load-bearing artefact: Phase E (Assured bundle) layers on top
  of Method 1's phase-gate substrate, so getting Programme right matters.

  Reuses the sdlc-worker:decomposition-review team image built in Phase B
  and reused in Phase C task 10.

provider: claude

nodes:
  - id: programme-review
    command: programme-bundle-review
    context: fresh
    effort: high
    image: sdlc-worker:decomposition-review
    timeout: 600000
```

- [ ] **Step 3: Install + run via the sdlc-workflows skill**

```bash
cp research/sdlc-bundles/dogfood-workflows/programme-bundle-review.md .archon/commands/
cp research/sdlc-bundles/dogfood-workflows/programme-bundle-review.yaml .archon/workflows/
```

Run via the workflows-run skill — see `plugins/sdlc-workflows/skills/workflows-run/SKILL.md` for the procedure. The Phase B and Phase C task 10 commits demonstrate the working invocation pattern.

Capture the review output to `research/sdlc-bundles/dogfood-workflows/programme-bundle-review-output.md`.

- [ ] **Step 4: Integrate findings**

If the review surfaces real issues (DISAGREE or NEEDS-REWORK on any question), fix them inline:
- Constitution issues → edit `plugins/sdlc-programme/CONSTITUTION.md`
- Template issues → edit `plugins/sdlc-programme/templates/`
- Gate issues → edit `plugins/sdlc-programme/scripts/programme/gates.py` and update tests
- Skill issues → edit the relevant SKILL.md (root + plugin mirror)
- Layout vs contract divergence → either fix the bundle layout or update the contract (the contract is authoritative — fix the bundle)

If only AGREE-WITH-CONCERNS findings, note them in the Phase D retrospective rather than fixing inline (concerns are deferrable).

- [ ] **Step 5: Commit**

```bash
git add research/sdlc-bundles/dogfood-workflows/programme-bundle-review.* \
        .archon/commands/programme-bundle-review.md \
        .archon/workflows/programme-bundle-review.yaml \
        plugins/sdlc-programme/  # include any inline fixes
git commit -m "$(cat <<'EOF'
review(programme): containerised architect review of Programme bundle (Phase D task 14)

Re-ran the Programme bundle through the containerised architect review
mechanism (sdlc-workflows + sdlc-worker:decomposition-review team image,
reusing the Phase B + C task 10 pattern). Per memory/feedback_containerised
_review_for_design_artefacts.md, load-bearing design artefacts go through
containerised review by default.

Workflow + command artefacts reusable for future Programme reviews.
Review output captured for audit. [Findings integrated inline / no actionable
findings] — see Phase D retrospective for finding-by-finding response.

Phase D task 14 of EPIC #178.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 15: Phase D closure — validation, retrospective, issue close

**Files:**
- Modify: `retrospectives/186-phase-d-programme-bundle-substrate.md`

- [ ] **Step 1: Run full Phase D validation**

```bash
python3 -m pytest tests/test_programme_*.py -v 2>&1 | tail -5
python3 tools/validation/check-plugin-packaging.py 2>&1 | tail -3
python3 tools/validation/local-validation.py --quick 2>&1 | tail -5
```

Expected: 27 programme tests pass; 13 plugins verified; quick validation PASSED.

- [ ] **Step 2: Run pre-push validation**

```bash
python3 tools/validation/local-validation.py --pre-push 2>&1 | tail -10
```

Expected: PASSED, or 9/10 with the documented pre-commit-binary env limitation (carried from earlier phases).

- [ ] **Step 3: Complete the Phase D retrospective**

Edit `retrospectives/186-phase-d-programme-bundle-substrate.md`. Replace each "(Filled in at phase end)" section with concrete content based on what was actually built. Include:

- **What was built**: 6 categories (plugin scaffold, constitution, templates, validators, skills, packaging) + 27 tests + containerised review
- **What worked well**: lessons-learned-applied across tasks; spec_parser as shared foundation; mock-fixture pattern from Phase C reused
- **What was harder than expected**: phase-review reviewer-agent dispatch (no test-architect agent in the family — used backend-architect as proxy); bundle layout convergence with the Phase C contract
- **Lessons learned**: spec_parser pattern (shared regex foundation for multiple validators) — durable feedback memory if applicable
- **Programme bundle assessment**: does the substrate genuinely serve a programme audience? Layout matches the bundle contract from Phase C?
- **Phase gate assessment**: do the gates catch real broken refs? False positive rate?
- **phase-review skill assessment**: is the design-spec→solution-architect dispatch producing useful reviews? Test-spec via backend-architect — adequate?
- **Containerised review verdict**: what the architect said; integration approach (inline fix or deferred-to-retrospective)
- **Validation**: pre-push status, plugin packaging count (13/13), test totals (27/27)

Mark status COMPLETE.

- [ ] **Step 4: Commit retrospective + close issue**

```bash
git add retrospectives/186-phase-d-programme-bundle-substrate.md
git commit -m "$(cat <<'EOF'
docs: Phase D retrospective complete; Programme bundle substrate ready (Phase D task 15)

Closes #186 (Phase D of EPIC #178). All 7 deliverable categories shipped:
plugin scaffold, Programme constitution, 3 phase artefact templates,
4 gate validators (built on shared spec_parser), 5 skills (commission-
programme, phase-init, phase-gate, phase-review-mandatory, traceability-
export), plugin packaging (13/13). Mock feature fixture validates the
gates end-to-end. Containerised architect review captured for audit.

27 programme tests (7 spec_parser + 11 gates + 5 traceability + 4
integration) all passing. Plugin packaging 13/13 verified. Pre-push
PASSED (or 9/10 with pre-commit env limitation; pre-existing).

Phase E (Assured bundle) can now build on top of this Method 1
substrate, layering Method 2 traceability + decomposition + KB-for-code.

Closes #186.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: Push branch**

```bash
git push 2>&1 | tail -3
```

Verify push succeeded. The branch now has Phases A + B + C + D work. Phase E (Assured bundle, Method 2) is next.

---

## Self-review

**Spec coverage check** — every section of `docs/feature-proposals/186-phase-d-programme-bundle-substrate.md` "Success Criteria" mapped to a task:

| Spec criterion | Task |
|---|---|
| `sdlc-programme` plugin v0.1.0 packaged and installable | Tasks 1, 12 |
| All 4 phase gate validators implemented and unit-tested | Task 5 |
| All 5 skills shipped at root + plugin mirror | Tasks 7-11 |
| Phase artefact templates copied into a project on commission | Tasks 3, 13 |
| `phase-review` mandatory for design-spec and test-spec | Task 9 (skill behaviour) + Task 2 (constitution Article 14) |
| `traceability-export csv` and `markdown` formats supported | Tasks 6, 10 |
| Plugin packaging passes 13/13 | Task 12 |
| Pre-push validation passes | Task 15 |
| Containerised architect review of Programme bundle | Task 14 |
| Phase D retrospective committed | Task 15 |
| Issue #186 closed | Task 15 |

All criteria covered.

**Placeholder scan**: no "TBD", "TODO", "implement later". Every code block contains real content. Test functions have real bodies. Commit messages use heredoc form per repo convention.

**Type consistency**: `ParsedSpec`, `GateResult`, `TraceabilityRow`, `SpecParseError`, `GateError`, `TraceabilityError` all defined once and referenced consistently. `parse_spec`, `requirements_gate`, `design_gate`, `test_gate`, `code_gate`, `build_matrix`, `export_csv`, `export_markdown` all defined and consumed by the right tests/skills.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-27-phase-d-programme-bundle-substrate.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, two-stage review per task (spec compliance + code quality), fast iteration. Each task ships its commit before moving on; Phase D retrospective consolidates at the end. Mirrors the Phase C execution model.

**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints. Heavier on context budget; faster wall-clock.

**Recommended: subagent-driven** — Phase D is 15 tasks of largely independent file-by-file work, ideal for the subagent pattern. Phase B and C task 10 patterns for containerised review are reused at Task 14.

Which approach?
