# Phase E — Assured Bundle (Method 2 Substrate) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `sdlc-assured` plugin v0.1.0 — Method 2 substrate for regulated-industry SDLC: positional namespace IDs, ID registry with bidirectional traceability, DDD-decomposition with visibility-rule discipline, KB extension to code, module-scoped render, and standard-specific traceability exports (DO-178C, IEC 62304, ISO 26262, FDA DHF). Layers cleanly on the Phase D Programme bundle without retrofit.

**Architecture:** A new plugin at `plugins/sdlc-assured/` mirroring the `sdlc-programme` shape. Six new Python modules under `scripts/assured/` with single responsibilities: `ids.py` (positional ID parser + registry build + remap), `traceability_validators.py` (4 mandatory + 1 optional), `decomposition.py` (programs.yaml schema + 5 module-bound validators), `code_index.py` (annotation parser + shelf-index emitter), `render.py` (module-scoped render + Q1 module-dependency-graph as markdown edge-list), `export.py` (4 standard-specific formats + reuses Programme's csv/markdown). Eight new skills (commission-assured, req-add, req-link, code-annotate, module-bound-check, kb-codeindex, change-impact-annotate, traceability-render). Integration with the existing `synthesis-librarian` agent via a new `SYNTHESISE-ACROSS-SPEC-TYPES` mode.

**Tech Stack:** Python 3.10+ (line-wise markdown parsing, regex, hashlib, pathlib, yaml); pytest for tests; conftest.py-based scripts package registration (avoids PEP 668 with Homebrew Python); existing `sdlc-knowledge-base` shelf-index entry shape; existing `sdlc-programme` templates and `spec_parser` (extended to recognise positional IDs).

**Branch:** `feature/sdlc-programme-assured-bundles` (already on it). EPIC #178 / sub-issue #104. No PR until Phase G (closure).

---

## File structure

### New files in this phase

| File | Responsibility |
|------|----------------|
| `plugins/sdlc-assured/manifest.yaml` | Bundle manifest — depends on sdlc-core, sdlc-programme, sdlc-team-common, sdlc-team-fullstack, sdlc-knowledge-base |
| `plugins/sdlc-assured/.claude-plugin/plugin.json` | Claude Code plugin descriptor |
| `plugins/sdlc-assured/CONSTITUTION.md` | Articles 15-17 overlay (Method 2 traceability, decomposition, KB-for-code) |
| `plugins/sdlc-assured/README.md` | Bundle overview |
| `plugins/sdlc-assured/pyproject.toml` | Package metadata for scripts/ |
| `plugins/sdlc-assured/templates/programs.yaml` | Decomposition declaration template |
| `plugins/sdlc-assured/templates/visibility-rules.md` | Context-map template |
| `plugins/sdlc-assured/templates/change-impact.md` | Change-impact annotation template |
| `plugins/sdlc-assured/templates/requirements-spec-assured.md` | Assured requirements-spec (extends Programme: positional ID, module assignment, granularity) |
| `plugins/sdlc-assured/templates/design-spec-assured.md` | Assured design-spec |
| `plugins/sdlc-assured/templates/test-spec-assured.md` | Assured test-spec |
| `plugins/sdlc-assured/scripts/assured/__init__.py` | Package marker |
| `plugins/sdlc-assured/scripts/assured/ids.py` | Positional ID parsing, registry build (`library/_ids.md`), remap |
| `plugins/sdlc-assured/scripts/assured/traceability_validators.py` | Forward link, backward coverage, idempotency, annotation format, change-impact-gate |
| `plugins/sdlc-assured/scripts/assured/decomposition.py` | programs.yaml parser + 5 module-bound validators |
| `plugins/sdlc-assured/scripts/assured/code_index.py` | Annotation parser → `library/_code-index.md` |
| `plugins/sdlc-assured/scripts/assured/render.py` | Module-scoped render + module-dependency-graph (markdown edge-list) |
| `plugins/sdlc-assured/scripts/assured/export.py` | DO-178C RTM, IEC 62304 matrix, ISO 26262 ASIL matrix, FDA DHF + csv/markdown |
| `plugins/sdlc-assured/skills/commission-assured/SKILL.md` | Bundle commissioning — programs block prompt, granularity, change-impact gating |
| `plugins/sdlc-assured/skills/req-add/SKILL.md` | Mint a new REQ ID with module assignment |
| `plugins/sdlc-assured/skills/req-link/SKILL.md` | Add satisfies link between artefacts |
| `plugins/sdlc-assured/skills/code-annotate/SKILL.md` | Auto-generate `# implements:` boilerplate |
| `plugins/sdlc-assured/skills/module-bound-check/SKILL.md` | Run all 5 decomposition validators |
| `plugins/sdlc-assured/skills/kb-codeindex/SKILL.md` | Parse annotations → `_code-index.md` |
| `plugins/sdlc-assured/skills/change-impact-annotate/SKILL.md` | Guide change-impact declaration |
| `plugins/sdlc-assured/skills/traceability-render/SKILL.md` | Module-scoped human doc |
| `skills/commission-assured/SKILL.md` | Root mirror |
| `skills/req-add/SKILL.md` | Root mirror |
| `skills/req-link/SKILL.md` | Root mirror |
| `skills/code-annotate/SKILL.md` | Root mirror |
| `skills/module-bound-check/SKILL.md` | Root mirror |
| `skills/kb-codeindex/SKILL.md` | Root mirror |
| `skills/change-impact-annotate/SKILL.md` | Root mirror |
| `skills/traceability-render/SKILL.md` | Root mirror |
| `tests/test_assured_ids.py` | ID parsing, registry build, remap tests |
| `tests/test_assured_traceability_validators.py` | 5 traceability validator tests |
| `tests/test_assured_decomposition.py` | programs.yaml parse + 5 validator tests |
| `tests/test_assured_code_index.py` | Annotation parser + emitter tests |
| `tests/test_assured_render.py` | Render + dependency-graph tests |
| `tests/test_assured_export.py` | 6 export format tests |
| `tests/test_assured_skill_integration.py` | End-to-end skill flow tests |
| `tests/fixtures/assured/feature-sample/` | Multi-module sample with programs.yaml, code annotations |
| `retrospectives/104-phase-e-assured-bundle-substrate.md` | Phase E retrospective scaffold |

### Files modified in this phase

| File | Change |
|------|--------|
| `tests/conftest.py` | Add `_register_scripts_package("sdlc-assured", "sdlc_assured_scripts")` |
| `plugins/sdlc-knowledge-base/agents/synthesis-librarian.md` | Add `SYNTHESISE-ACROSS-SPEC-TYPES` mode + spec-type pseudo-handles |
| `release-mapping.yaml` | Add `sdlc-assured:` top-level key |
| `.claude-plugin/marketplace.json` | Add sdlc-assured plugin entry |
| `.gitignore` | Add `!tests/fixtures/assured/**` if needed |

### Resolved open question (Q1)

**Q1: Module-dependency-graph visualisation format.** Resolved: **markdown edge-list** in v0.1.0. Each declared visibility relationship becomes a row `| From | → | To | Allowed? |` sorted by from-module. ASCII DAG and HTML SVG remain explicit stretch goals (out of v0.1.0 scope per design spec §9). Worked example in Task 26.

---

## Task 1: Plugin scaffold

**Files:**
- Create: `plugins/sdlc-assured/manifest.yaml`
- Create: `plugins/sdlc-assured/.claude-plugin/plugin.json`
- Create: `plugins/sdlc-assured/README.md`
- Create: `plugins/sdlc-assured/pyproject.toml`
- Create: `plugins/sdlc-assured/scripts/assured/__init__.py`
- Modify: `tests/conftest.py`

- [ ] **Step 1: Create the plugin manifest**

Write `plugins/sdlc-assured/manifest.yaml`:

```yaml
schema_version: 1
name: assured
version: 0.1.0
supported_levels: [enterprise]
description: Regulated-industry SDLC with positional namespace IDs, bidirectional traceability, DDD decomposition, and standard-specific exports (DO-178C, IEC 62304, ISO 26262, FDA DHF)
constitution: CONSTITUTION.md
depends_on: [sdlc-core, sdlc-programme, sdlc-team-common, sdlc-team-fullstack, sdlc-knowledge-base]
agents: []
skills:
  - commission-assured
  - req-add
  - req-link
  - code-annotate
  - module-bound-check
  - kb-codeindex
  - change-impact-annotate
  - traceability-render
templates:
  - programs.yaml
  - visibility-rules.md
  - change-impact.md
  - requirements-spec-assured.md
  - design-spec-assured.md
  - test-spec-assured.md
validators:
  syntax: [python_ast]
  quick: [check_technical_debt, check_logging_compliance]
  pre_push:
    - python_ast
    - check_technical_debt
    - check_logging_compliance
    - run_tests
    - id_uniqueness_validator
    - cited_ids_resolve_validator
    - orphan_ids_validator
    - forward_link_integrity_validator
    - backward_coverage_validator
    - index_regenerability_validator
    - annotation_format_integrity_validator
    - req_module_assignment_validator
    - code_module_mapping_validator
    - visibility_rule_validator
    - anaemic_context_validator
    - granularity_match_validator
```

- [ ] **Step 2: Create the plugin descriptor**

Write `plugins/sdlc-assured/.claude-plugin/plugin.json`:

```json
{
  "name": "sdlc-assured",
  "version": "0.1.0",
  "description": "Assured (Method 2) regulated-industry SDLC bundle"
}
```

- [ ] **Step 3: Create the package marker**

Write `plugins/sdlc-assured/scripts/assured/__init__.py`:

```python
"""sdlc-assured runtime helpers — ID registry, validators, exporters."""
```

- [ ] **Step 4: Create pyproject.toml**

Write `plugins/sdlc-assured/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "sdlc-assured-scripts"
version = "0.1.0"
description = "Assured bundle runtime helpers"
requires-python = ">=3.10"

[tool.setuptools.packages.find]
where = ["scripts"]
```

- [ ] **Step 5: Register the package in conftest.py**

Read `tests/conftest.py` first to find the existing `_register_scripts_package` calls.

Add this line after the existing `_register_scripts_package("sdlc-programme", "sdlc_programme_scripts")` line:

```python
_register_scripts_package("sdlc-assured", "sdlc_assured_scripts")
```

- [ ] **Step 6: Create the README**

Write `plugins/sdlc-assured/README.md`:

```markdown
# sdlc-assured

Regulated-industry SDLC bundle (Method 2) for projects targeting DO-178C, IEC 62304, ISO 26262, IEC 61508, or FDA 21 CFR Part 820. Layers on top of `sdlc-programme` (Phase D) with positional namespace IDs, bidirectional traceability, DDD-style decomposition with visibility rules, KB extension to code, and standard-specific traceability exports.

## What this bundle adds over Programme

- **Identifier system**: positional namespace IDs (`P1.SP2.M3.REQ-007`) for decomposed projects; flat IDs preserved for non-decomposed projects.
- **ID registry**: `library/_ids.md` auto-generated, tracking every ID, source, and links. Validators enforce uniqueness and reference resolution.
- **Bidirectional traceability**: 4 mandatory validators (forward link integrity, backward coverage, index regenerability, annotation format) + 1 optional (change-impact-gate).
- **Decomposition**: declarative `programs.yaml` with DDD bounded contexts, visibility rules, hexagonal-architecture opt-in.
- **KB extension to code**: inline `# implements: <ID>` annotations parsed into `library/_code-index.md` (shelf-index-shaped).
- **Render and export**: module-scoped traceability render, module-dependency-graph (markdown edge-list), 4 standard-specific export formats.

## Constitution

Articles 15-17 overlay the universal articles 1-11 and Programme articles 12-14:

- Article 15: Identifier and traceability integrity
- Article 16: Decomposition discipline
- Article 17: KB-for-code annotation completeness

See `CONSTITUTION.md`.

## Skills

| Skill | Purpose |
|-------|---------|
| `commission-assured` | Install Assured bundle into a project; prompt for programs block, granularity, regulatory context |
| `req-add` | Mint a new REQ ID with module assignment |
| `req-link` | Add a satisfies link between artefacts |
| `code-annotate` | Auto-generate `# implements:` boilerplate for a function |
| `module-bound-check` | Run all 5 decomposition validators |
| `kb-codeindex` | Parse annotations into `library/_code-index.md` |
| `change-impact-annotate` | Guide change-impact declaration for IEC 62304 / FDA / ISO 26262 |
| `traceability-render` | Module-scoped human-readable doc with anchor links |

## Out of scope (v0.1.0)

- AST-level code intelligence
- IDE integration
- ALM database
- Industry certification itself (this is substrate, not certification)
- Bidirectional ReqIF sync
- Decomposition suggestion (we declare; we don't suggest)
- Distributed multi-team ID coordination
```

- [ ] **Step 7: Verify plugin is discoverable**

Run:
```bash
python3 -c "import yaml; m=yaml.safe_load(open('plugins/sdlc-assured/manifest.yaml')); print(m['name'], m['version'])"
```

Expected: `assured 0.1.0`

- [ ] **Step 8: Commit**

```bash
git add plugins/sdlc-assured/manifest.yaml \
        plugins/sdlc-assured/.claude-plugin/ \
        plugins/sdlc-assured/README.md \
        plugins/sdlc-assured/pyproject.toml \
        plugins/sdlc-assured/scripts/ \
        tests/conftest.py
git commit -m "feat(assured): plugin scaffold (Phase E task 1)"
```

---

## Task 2: Assured constitution (Articles 15-17)

**Files:**
- Create: `plugins/sdlc-assured/CONSTITUTION.md`

- [ ] **Step 1: Write the constitution**

Write `plugins/sdlc-assured/CONSTITUTION.md`:

```markdown
# Assured Constitution (sdlc-assured bundle v0.1.0)

This constitution applies to projects commissioned to the **Assured** SDLC option. It extends the universal AI-First SDLC Constitution (`CONSTITUTION.md` at the framework root, articles 1-11) and the Programme Constitution (`plugins/sdlc-programme/CONSTITUTION.md`, articles 12-14) with three Assured-specific articles enforcing Method 2 (agent-first specs with traceability + decomposition + KB-for-code).

The universal articles (1-11) and Programme articles (12-14) apply unchanged. Assured adds articles 15-17.

---

## Article 15 — Identifier and traceability integrity (Assured)

**Every artefact MUST declare stable IDs in the project's identifier namespace.**

- For non-decomposed projects: `REQ-<feature>-NNN`, `DES-<feature>-NNN`, `TEST-<feature>-NNN`, `CODE-<feature>-NNN`. The default namespace `P1.SP1.M1.*` is implicit.
- For decomposed projects: `<program>.<sub-program>.<module>.<type>-NNN` (e.g., `P1.SP2.M3.REQ-007`).

**The ID registry (`library/_ids.md`) is the single source of truth.** Generated by `kb-rebuild-indexes`. Auditors verify by re-running and comparing byte-for-byte (idempotency).

**Validators enforce at pre-push:**

- ID uniqueness: no duplicate IDs in the registry
- Cited IDs resolve: every `satisfies:`, `derived-from:`, `# implements:` reference targets an ID in the registry
- No orphan IDs: every declared ID is cited at least once (warn, not block — orphans are a smell, not always a defect)
- Forward link integrity: REQ → DES → TEST → CODE chain has no broken edges
- Backward coverage: every REQ has at least one DES; every DES has at least one TEST; every TEST has at least one CODE annotation
- Index regenerability: `kb-rebuild-indexes` produces byte-identical output on repeat runs (idempotency)
- Annotation format integrity: `# implements: <ID>` annotations parse cleanly; broken annotations block

**ID stability is non-negotiable.** Once an ID is committed, it does not change. Renames happen via decomposition refactoring (`kb-rebuild-indexes` remaps old paths to new paths while preserving the ID), never by editing the ID itself.

## Article 16 — Decomposition discipline (Assured)

**Decomposition is declared, not inferred.** The project's `programs.yaml` (or default `P1.SP1.M1.*`) is the authoritative decomposition. Code, REQs, DESs, TESTs assert their position by ID prefix and module assignment.

**Validators enforce at pre-push:**

- Every REQ has a module assignment (either explicit YAML frontmatter `module: P1.SP1.M1` or implicit via positional ID prefix)
- Every CODE annotation maps to a declared module path (the file's directory must be reachable from the declared module's `paths`)
- Visibility rules are respected: cross-module imports follow the declared visibility (in advisory mode, violations warn; in strict mode, violations block)
- No anaemic contexts: code implementing REQ/DES is co-located in the declared module's directory tree (not scattered across modules)
- Granularity matches declared mode: `requirement` granularity declared → at least one annotation per REQ; `function` granularity → annotation per function; `module` granularity → annotation per module entry-point

**Default decomposition is `P1.SP1.M1.*`.** Greenfield projects ship with this default. Refactoring to multi-module decomposition is intentional and requires a `programs.yaml` commit.

**Visibility rules are advisory by default; strict in regulated contexts.** Commissioning sets the mode based on declared regulatory context.

## Article 17 — KB-for-code annotation completeness (Assured)

**Code is text-with-annotations.** Each non-trivial function or module-level entry point that implements a REQ/DES MUST carry an inline annotation:

```python
def authenticate(token: str) -> AuthResult:
    # implements: DES-auth-005, REQ-auth-003
    ...
```

**`kb-codeindex` parses these annotations** into `library/_code-index.md`, structurally a KB shelf-index entry per code location. The librarian queries this like the regular shelf-index.

**Annotations MUST resolve.** Broken `# implements:` annotations are defects, not style issues — they block at pre-push.

**The framework does NOT do AST analysis.** It parses comments, not code semantics. Auditors validate annotation completeness; the framework validates annotation syntax and reference resolution.

**`change-impact-gate` is optional but recommended for IEC 62304 / FDA 21 CFR Part 820 / ISO 26262 ASIL C/D.** When enabled at commissioning, every code change MUST carry a change-impact annotation declaring which downstream artefacts (DES, TEST, REQ, modules) the change affects.

---

## What this bundle does NOT enforce

- Industry certification itself — the bundle produces substrate, not certificate. Certification requires an accredited authority.
- AST-level code intelligence (call graphs, semantic search, automatic change-impact detection)
- IDE integration
- Full ALM database (Jama, Polarion, Codebeamer integration is out of scope; plugin-shaped if needed)
- Bidirectional ReqIF sync (one-way export only via `traceability-export`)
- Migration of pre-Assured projects' un-annotated code (greenfield-friendly only)
- Decomposition suggestion (we validate declarations; we don't propose them)
- Distributed multi-team ID coordination

The Assured constitution is the floor for regulated-industry work — universal articles plus Programme phase gates plus Method 2 traceability. Teams may layer additional process on top via their own retrospective decisions.
```

- [ ] **Step 2: Verify the constitution renders cleanly**

Run:
```bash
wc -l plugins/sdlc-assured/CONSTITUTION.md
```

Expected: 60-90 lines.

- [ ] **Step 3: Commit**

```bash
git add plugins/sdlc-assured/CONSTITUTION.md
git commit -m "feat(assured): constitution articles 15-17 (Phase E task 2)"
```

---

## Task 3: Phase E artefact templates

**Files:**
- Create: `plugins/sdlc-assured/templates/programs.yaml`
- Create: `plugins/sdlc-assured/templates/visibility-rules.md`
- Create: `plugins/sdlc-assured/templates/change-impact.md`
- Create: `plugins/sdlc-assured/templates/requirements-spec-assured.md`
- Create: `plugins/sdlc-assured/templates/design-spec-assured.md`
- Create: `plugins/sdlc-assured/templates/test-spec-assured.md`

- [ ] **Step 1: Write the programs.yaml template**

Write `plugins/sdlc-assured/templates/programs.yaml`:

```yaml
# Decomposition declaration for an Assured-bundle project.
#
# This file declares the project's programs / sub-programs / modules,
# their directory paths, granularity, and (optional) visibility rules.
# Replace placeholders before committing.

schema_version: 1

programs:
  - id: P1
    name: <Program 1 Name>
    description: <One-line description>
    sub_programs:
      - id: SP1
        name: <Sub-program 1 Name>
        modules:
          - id: M1
            name: <Module 1 Name>
            paths: [src/<module-1-dir>/]
            granularity: requirement   # one of: requirement | function | module
            structure: flat            # one of: flat | hexagonal
            owner: <team-or-person>    # optional
          - id: M2
            name: <Module 2 Name>
            paths: [src/<module-2-dir>/]
            granularity: requirement
            structure: flat

# Visibility rules declare which modules may depend on which.
# Rules omitted = no cross-module dependencies allowed.
# See visibility-rules.md for the context-map document.
visibility:
  - from: P1.SP1.M1
    to: [P1.SP1.M2]
  - from: P1.SP1.M2
    to: []
```

- [ ] **Step 2: Write the visibility-rules template**

Write `plugins/sdlc-assured/templates/visibility-rules.md`:

```markdown
# Context Map: Module Visibility Rules

This document explains the visibility rules declared in `programs.yaml`. It is the team's shared understanding of which modules depend on which, why, and what the rules guard against. Required for ISO 26262, IEC 62304, and DO-178C contexts; recommended for all Assured projects.

---

## Programs and modules

<!-- Briefly summarise what each program / sub-program / module is responsible for. -->

| Module | Responsibility | Owner |
|--------|----------------|-------|
| P1.SP1.M1 | <Responsibility> | <Owner> |
| P1.SP1.M2 | <Responsibility> | <Owner> |

## Allowed dependencies

<!-- For each declared visibility rule, explain WHY the dependency is allowed. -->

- **P1.SP1.M1 → P1.SP1.M2**: <reason>

## Disallowed dependencies (explicit)

<!-- Note dependencies that were considered and rejected. This is auditor-grade evidence that the team thought about it. -->

- **P1.SP1.M2 → P1.SP1.M1**: <reason for rejection — typically "this would create a cycle" or "this violates the bounded context">

## Anaemic-context checks

<!-- Note any code paths that are at risk of becoming anaemic (logic scattered across modules) and how the team mitigates. -->

- <Risk>: <mitigation>
```

- [ ] **Step 3: Write the change-impact template**

Write `plugins/sdlc-assured/templates/change-impact.md`:

```markdown
# Change Impact Annotation

**Change ID:** <CHG-NNN — assigned by team>
**Author:** <name>
**Date:** <YYYY-MM-DD>
**Affected commit:** <git SHA — populated after commit>

---

## Change summary

<!-- One paragraph: what changed, in plain English. -->

## Impacted artefacts

### REQs touched

<!-- Each REQ-ID that this change directly modifies or invalidates. -->

- REQ-<feature>-NNN: <how impacted — modifies/invalidates/extends>

### DESs touched

- DES-<feature>-NNN: <how impacted>

### TESTs touched

- TEST-<feature>-NNN: <how impacted — needs re-run / needs new test / replaced>

### CODE locations touched

- <file>:<function>: <what changed>

### Modules touched

- P1.SP1.M1: <how impacted>

## Downstream effects

<!-- What happens elsewhere in the system because of this change. Be specific. -->

## Verification approach

<!-- How will the team verify this change is safe? Reference test runs, peer review, formal verification, etc. -->

## Approver

**Approved by:** <name>
**Approval date:** <YYYY-MM-DD>
```

- [ ] **Step 4: Write the assured requirements-spec template**

Write `plugins/sdlc-assured/templates/requirements-spec-assured.md`:

```markdown
---
feature_id: <feature-id>
module: P1.SP1.M1
granularity: requirement
---

# Requirements Specification: <Feature Title> (Assured)

**Feature-id:** <feature-id>
**Module:** P1.SP1.M1
**Granularity:** requirement
**Status:** Draft
**Author:** <Your name>
**Created:** <YYYY-MM-DD>

---

## Motivation

<!-- WHY this feature exists. Regulatory citations go here when relevant (e.g., "IEC 62304 §5.2.2"). -->

## Requirements

<!-- Each requirement is a single declarative sentence with a stable ID. For non-decomposed projects use `REQ-<feature-id>-NNN`. For decomposed projects use the positional form `P1.SP2.M3.REQ-NNN`. IDs are immutable once committed. -->

### REQ-<feature-id>-001

<Single declarative sentence describing one requirement.>

**Module:** P1.SP1.M1

### REQ-<feature-id>-002

<Single declarative sentence describing the next requirement.>

**Module:** P1.SP1.M1

## Out of scope

<!-- What this feature explicitly does NOT do. -->

## Success criteria

<!-- How we know this feature is done — verifiable, observable. -->
```

- [ ] **Step 5: Write the assured design-spec template**

Write `plugins/sdlc-assured/templates/design-spec-assured.md`:

```markdown
---
feature_id: <feature-id>
module: P1.SP1.M1
---

# Design Specification: <Feature Title> (Assured)

**Feature-id:** <feature-id>
**Module:** P1.SP1.M1
**Author:** <Your name>
**Created:** <YYYY-MM-DD>

---

## Architecture

<!-- High-level approach — components, data flow, error handling. -->

## Design elements

### DES-<feature-id>-001

<Single declarative design statement.>

**satisfies:** REQ-<feature-id>-001
**Module:** P1.SP1.M1

### DES-<feature-id>-002

<Single declarative design statement.>

**satisfies:** REQ-<feature-id>-002
**Module:** P1.SP1.M1

## Visibility rules used

<!-- Which other modules does this design depend on? Each entry must be in the project's programs.yaml visibility block. -->

- P1.SP1.M1 → P1.SP1.M2: <reason>

## Out of scope

<!-- What this design explicitly does NOT cover. -->
```

- [ ] **Step 6: Write the assured test-spec template**

Write `plugins/sdlc-assured/templates/test-spec-assured.md`:

```markdown
---
feature_id: <feature-id>
module: P1.SP1.M1
---

# Test Specification: <Feature Title> (Assured)

**Feature-id:** <feature-id>
**Module:** P1.SP1.M1
**Author:** <Your name>
**Created:** <YYYY-MM-DD>

---

## Test strategy

<!-- Testing approach: unit, integration, property-based, mutation, etc. -->

## Test cases

### TEST-<feature-id>-001

<Test case description.>

**satisfies:** REQ-<feature-id>-001 via DES-<feature-id>-001
**Module:** P1.SP1.M1

### TEST-<feature-id>-002

<Test case description.>

**satisfies:** REQ-<feature-id>-002 via DES-<feature-id>-002
**Module:** P1.SP1.M1

## Coverage gaps (acknowledged)

<!-- Any REQ or DES not covered by a test in this spec, with rationale. Helps reviewers and auditors. -->
```

- [ ] **Step 7: Verify all six templates parse**

Run:
```bash
ls plugins/sdlc-assured/templates/ && python3 -c "import yaml; print(yaml.safe_load(open('plugins/sdlc-assured/templates/programs.yaml'))['schema_version'])"
```

Expected: 6 templates listed; `1` printed.

- [ ] **Step 8: Commit**

```bash
git add plugins/sdlc-assured/templates/
git commit -m "feat(assured): phase E artefact templates (Phase E task 3)"
```

---

## Task 4: Positional ID parser

**Files:**
- Create: `plugins/sdlc-assured/scripts/assured/ids.py`
- Create: `tests/test_assured_ids.py`

- [ ] **Step 1: Write the failing tests**

Write `tests/test_assured_ids.py`:

```python
"""Tests for assured.ids — positional namespace ID parsing."""

import pytest

from sdlc_assured_scripts.assured.ids import (
    IdParseError,
    ParsedId,
    parse_id,
    format_id,
    is_positional,
)


def test_parse_flat_id():
    parsed = parse_id("REQ-auth-001")
    assert parsed == ParsedId(
        program=None, sub_program=None, module=None,
        kind="REQ", feature="auth", number=1,
    )
    assert is_positional(parsed) is False


def test_parse_positional_id():
    parsed = parse_id("P1.SP2.M3.REQ-007")
    assert parsed == ParsedId(
        program="P1", sub_program="SP2", module="M3",
        kind="REQ", feature=None, number=7,
    )
    assert is_positional(parsed) is True


def test_parse_positional_id_kinds():
    for kind in ("REQ", "DES", "TEST", "CODE"):
        parsed = parse_id(f"P1.SP1.M1.{kind}-001")
        assert parsed.kind == kind


def test_parse_invalid_id_raises():
    with pytest.raises(IdParseError):
        parse_id("not-an-id")
    with pytest.raises(IdParseError):
        parse_id("REQ-AUTH-001")  # uppercase feature
    with pytest.raises(IdParseError):
        parse_id("P1.SP2.REQ-007")  # missing module


def test_format_id_flat_round_trip():
    parsed = parse_id("REQ-auth-001")
    assert format_id(parsed) == "REQ-auth-001"


def test_format_id_positional_round_trip():
    parsed = parse_id("P1.SP2.M3.REQ-007")
    assert format_id(parsed) == "P1.SP2.M3.REQ-007"


def test_default_namespace_is_implicit():
    """A flat ID is treated as living in P1.SP1.M1 by default."""
    parsed = parse_id("REQ-auth-001")
    assert parsed.program is None  # explicitly not stored
    # The validators apply P1.SP1.M1 as default when checking module assignment.
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
```bash
python3 -m pytest tests/test_assured_ids.py -v 2>&1 | tail -10
```

Expected: ImportError on `sdlc_assured_scripts.assured.ids`.

- [ ] **Step 3: Implement the parser**

Write `plugins/sdlc-assured/scripts/assured/ids.py`:

```python
"""Positional namespace ID parsing for the Assured bundle."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


class IdParseError(ValueError):
    """Raised when a string cannot be parsed as an Assured ID."""


@dataclass(frozen=True)
class ParsedId:
    """Decomposed view of an Assured ID."""

    program: Optional[str]
    sub_program: Optional[str]
    module: Optional[str]
    kind: str
    feature: Optional[str]
    number: int


_FLAT_RE = re.compile(
    r"^(?P<kind>REQ|DES|TEST|CODE)-(?P<feature>[a-z0-9][a-z0-9-]*)-(?P<num>\d+)$"
)
_POSITIONAL_RE = re.compile(
    r"^(?P<prog>P\d+)\.(?P<sub>SP\d+)\.(?P<mod>M\d+)\."
    r"(?P<kind>REQ|DES|TEST|CODE)-(?P<num>\d+)$"
)


def parse_id(text: str) -> ParsedId:
    flat = _FLAT_RE.match(text)
    if flat:
        return ParsedId(
            program=None,
            sub_program=None,
            module=None,
            kind=flat["kind"],
            feature=flat["feature"],
            number=int(flat["num"]),
        )
    positional = _POSITIONAL_RE.match(text)
    if positional:
        return ParsedId(
            program=positional["prog"],
            sub_program=positional["sub"],
            module=positional["mod"],
            kind=positional["kind"],
            feature=None,
            number=int(positional["num"]),
        )
    raise IdParseError(f"not a valid Assured ID: {text!r}")


def format_id(parsed: ParsedId) -> str:
    if is_positional(parsed):
        return f"{parsed.program}.{parsed.sub_program}.{parsed.module}.{parsed.kind}-{parsed.number:03d}"
    return f"{parsed.kind}-{parsed.feature}-{parsed.number:03d}"


def is_positional(parsed: ParsedId) -> bool:
    return parsed.program is not None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_ids.py -v 2>&1 | tail -10
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/ids.py tests/test_assured_ids.py
git commit -m "feat(assured): positional ID parser (Phase E task 4)"
```

---

## Task 5: ID registry builder

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/ids.py`
- Modify: `tests/test_assured_ids.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_assured_ids.py`:

```python
from pathlib import Path

from sdlc_assured_scripts.assured.ids import (
    IdRecord,
    build_id_registry,
    render_id_registry,
)


def test_build_id_registry_walks_specs(tmp_path: Path):
    feature_dir = tmp_path / "docs" / "specs" / "auth"
    feature_dir.mkdir(parents=True)
    (feature_dir / "requirements-spec.md").write_text(
        "### REQ-auth-001\nLogin must support OAuth.\n"
        "### REQ-auth-002\nSessions expire after 24h.\n"
    )
    (feature_dir / "design-spec.md").write_text(
        "### DES-auth-001\n**satisfies:** REQ-auth-001\nUse PKCE.\n"
    )
    (feature_dir / "test-spec.md").write_text(
        "### TEST-auth-001\n**satisfies:** REQ-auth-001 via DES-auth-001\nVerify PKCE flow.\n"
    )
    records = build_id_registry(tmp_path)
    by_id = {r.id: r for r in records}
    assert "REQ-auth-001" in by_id
    assert by_id["REQ-auth-001"].kind == "REQ"
    assert by_id["REQ-auth-001"].source.endswith("requirements-spec.md")
    assert by_id["DES-auth-001"].satisfies == ["REQ-auth-001"]
    assert by_id["TEST-auth-001"].satisfies == ["REQ-auth-001", "DES-auth-001"]


def test_render_id_registry_produces_markdown_table(tmp_path: Path):
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="docs/specs/auth/requirements-spec.md", satisfies=[]),
        IdRecord(id="DES-auth-001", kind="DES", source="docs/specs/auth/design-spec.md", satisfies=["REQ-auth-001"]),
    ]
    output = render_id_registry(records)
    assert "| ID | Kind | Source | Satisfies |" in output
    assert "| REQ-auth-001 | REQ | docs/specs/auth/requirements-spec.md |  |" in output
    assert "| DES-auth-001 | DES | docs/specs/auth/design-spec.md | REQ-auth-001 |" in output
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
```bash
python3 -m pytest tests/test_assured_ids.py::test_build_id_registry_walks_specs -v
```

Expected: ImportError on `IdRecord`, `build_id_registry`, `render_id_registry`.

- [ ] **Step 3: Implement the registry builder**

Append to `plugins/sdlc-assured/scripts/assured/ids.py`:

```python
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class IdRecord:
    """A single ID with its source artefact and forward links."""

    id: str
    kind: str
    source: str
    satisfies: List[str]


_HEADING_RE = re.compile(
    r"^###\s+(?P<id>(?:P\d+\.SP\d+\.M\d+\.)?(?:REQ|DES|TEST|CODE)-(?:[a-z0-9][a-z0-9-]*-)?\d+)\b"
)
_SATISFIES_RE = re.compile(r"^\*\*satisfies:\*\*\s+(?P<refs>.+)$", re.MULTILINE)
_REF_ID_RE = re.compile(
    r"\b((?:P\d+\.SP\d+\.M\d+\.)?(?:REQ|DES|TEST|CODE)-(?:[a-z0-9][a-z0-9-]*-)?\d+)\b"
)


def build_id_registry(project_root: Path) -> List[IdRecord]:
    """Walk docs/specs/ and collect every declared ID with its forward links."""
    specs_dir = project_root / "docs" / "specs"
    records: List[IdRecord] = []
    if not specs_dir.is_dir():
        return records
    for spec_file in sorted(specs_dir.glob("**/*.md")):
        text = spec_file.read_text(encoding="utf-8")
        rel_source = str(spec_file.relative_to(project_root))
        in_code_block = False
        current_id: Optional[str] = None
        current_satisfies: List[str] = []

        def _flush() -> None:
            nonlocal current_id, current_satisfies
            if current_id is not None:
                records.append(IdRecord(
                    id=current_id,
                    kind=parse_id(current_id).kind,
                    source=rel_source,
                    satisfies=current_satisfies,
                ))
            current_id = None
            current_satisfies = []

        for line in text.splitlines():
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            heading = _HEADING_RE.match(line)
            if heading:
                _flush()
                current_id = heading["id"]
                continue
            satisfies = _SATISFIES_RE.match(line)
            if satisfies and current_id is not None:
                current_satisfies = _REF_ID_RE.findall(satisfies["refs"])
        _flush()
    return records


def render_id_registry(records: List[IdRecord]) -> str:
    """Render the registry as a markdown table."""
    lines = [
        "<!-- Generated by kb-rebuild-indexes; do not edit by hand. -->",
        "# ID Registry",
        "",
        "| ID | Kind | Source | Satisfies |",
        "|----|------|--------|-----------|",
    ]
    for r in records:
        sat = ", ".join(r.satisfies)
        lines.append(f"| {r.id} | {r.kind} | {r.source} | {sat} |")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_ids.py -v 2>&1 | tail -10
```

Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/ids.py tests/test_assured_ids.py
git commit -m "feat(assured): ID registry builder + markdown render (Phase E task 5)"
```

---

## Task 6: ID uniqueness validator

**Files:**
- Create: `plugins/sdlc-assured/scripts/assured/traceability_validators.py`
- Create: `tests/test_assured_traceability_validators.py`

- [ ] **Step 1: Write the failing test**

Write `tests/test_assured_traceability_validators.py`:

```python
"""Tests for assured.traceability_validators."""

from pathlib import Path

import pytest

from sdlc_assured_scripts.assured.ids import IdRecord
from sdlc_assured_scripts.assured.traceability_validators import (
    ValidatorResult,
    id_uniqueness,
)


def test_id_uniqueness_passes_when_all_ids_unique():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="REQ-auth-002", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]),
    ]
    result = id_uniqueness(records)
    assert result.passed is True
    assert result.errors == []


def test_id_uniqueness_fails_on_duplicate():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="REQ-auth-001", kind="REQ", source="b.md", satisfies=[]),
    ]
    result = id_uniqueness(records)
    assert result.passed is False
    assert any("duplicate" in e.lower() for e in result.errors)
    assert any("REQ-auth-001" in e for e in result.errors)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py::test_id_uniqueness_passes_when_all_ids_unique -v
```

Expected: ImportError on `traceability_validators`.

- [ ] **Step 3: Implement the validator**

Write `plugins/sdlc-assured/scripts/assured/traceability_validators.py`:

```python
"""Mandatory + optional traceability validators for the Assured bundle."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import List

from .ids import IdRecord


@dataclass
class ValidatorResult:
    """Outcome of a single validator run."""

    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def id_uniqueness(records: List[IdRecord]) -> ValidatorResult:
    counts = Counter(r.id for r in records)
    duplicates = [id_ for id_, n in counts.items() if n > 1]
    if not duplicates:
        return ValidatorResult(passed=True)
    errors = [
        f"duplicate ID {id_!r} declared in: "
        + ", ".join(r.source for r in records if r.id == id_)
        for id_ in sorted(duplicates)
    ]
    return ValidatorResult(passed=False, errors=errors)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/traceability_validators.py tests/test_assured_traceability_validators.py
git commit -m "feat(assured): id_uniqueness validator (Phase E task 6)"
```

---

## Task 7: Cited-IDs-resolve validator

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/traceability_validators.py`
- Modify: `tests/test_assured_traceability_validators.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_traceability_validators.py`:

```python
from sdlc_assured_scripts.assured.traceability_validators import cited_ids_resolve


def test_cited_ids_resolve_passes_when_all_targets_exist():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]),
    ]
    result = cited_ids_resolve(records)
    assert result.passed is True


def test_cited_ids_resolve_fails_on_missing_target():
    records = [
        IdRecord(id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-999"]),
    ]
    result = cited_ids_resolve(records)
    assert result.passed is False
    assert any("REQ-auth-999" in e for e in result.errors)
    assert any("DES-auth-001" in e for e in result.errors)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py::test_cited_ids_resolve_passes_when_all_targets_exist -v
```

Expected: ImportError on `cited_ids_resolve`.

- [ ] **Step 3: Implement the validator**

Append to `plugins/sdlc-assured/scripts/assured/traceability_validators.py`:

```python
def cited_ids_resolve(records: List[IdRecord]) -> ValidatorResult:
    declared = {r.id for r in records}
    errors: List[str] = []
    for r in records:
        for cited in r.satisfies:
            if cited not in declared:
                errors.append(
                    f"{r.id} (in {r.source}) cites {cited!r} which is not declared anywhere"
                )
    return ValidatorResult(passed=not errors, errors=errors)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/traceability_validators.py tests/test_assured_traceability_validators.py
git commit -m "feat(assured): cited_ids_resolve validator (Phase E task 7)"
```

---

## Task 8: Orphan-IDs validator

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/traceability_validators.py`
- Modify: `tests/test_assured_traceability_validators.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_traceability_validators.py`:

```python
from sdlc_assured_scripts.assured.traceability_validators import orphan_ids


def test_orphan_ids_warns_when_req_never_cited():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="REQ-auth-002", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]),
    ]
    result = orphan_ids(records)
    assert result.passed is True
    assert any("REQ-auth-002" in w for w in result.warnings)


def test_orphan_ids_does_not_warn_for_test_or_code():
    """TEST and CODE are leaves — they cite, but nothing cites them."""
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]),
        IdRecord(id="TEST-auth-001", kind="TEST", source="c.md", satisfies=["REQ-auth-001", "DES-auth-001"]),
    ]
    result = orphan_ids(records)
    assert result.passed is True
    assert result.warnings == []
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py::test_orphan_ids_warns_when_req_never_cited -v
```

Expected: ImportError on `orphan_ids`.

- [ ] **Step 3: Implement the validator**

Append to `plugins/sdlc-assured/scripts/assured/traceability_validators.py`:

```python
def orphan_ids(records: List[IdRecord]) -> ValidatorResult:
    """Warn when an ID that should be cited (REQ, DES) is never cited.

    TEST and CODE are leaves; missing back-references for them are
    surfaced by backward_coverage instead.
    """
    cited: set[str] = set()
    for r in records:
        cited.update(r.satisfies)
    warnings: List[str] = []
    for r in records:
        if r.kind in {"REQ", "DES"} and r.id not in cited:
            warnings.append(f"orphan {r.kind} {r.id!r} (declared in {r.source}) is never cited")
    return ValidatorResult(passed=True, warnings=warnings)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/traceability_validators.py tests/test_assured_traceability_validators.py
git commit -m "feat(assured): orphan_ids validator (warn-not-block) (Phase E task 8)"
```

---

## Task 9: Decomposition refactoring / ID remapping

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/ids.py`
- Modify: `tests/test_assured_ids.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_ids.py`:

```python
from sdlc_assured_scripts.assured.ids import remap_ids


def test_remap_ids_preserves_id_when_module_moves():
    """When a module's path changes, the ID stays the same; only the source path updates."""
    records = [
        IdRecord(id="P1.SP1.M1.REQ-001", kind="REQ", source="docs/specs/legacy/requirements-spec.md", satisfies=[]),
    ]
    remapping = {"docs/specs/legacy/": "docs/specs/auth/"}
    remapped = remap_ids(records, remapping)
    assert remapped[0].id == "P1.SP1.M1.REQ-001"
    assert remapped[0].source == "docs/specs/auth/requirements-spec.md"


def test_remap_ids_no_op_when_no_paths_match():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="docs/specs/auth/requirements-spec.md", satisfies=[]),
    ]
    remapping = {"docs/specs/legacy/": "docs/specs/old/"}
    remapped = remap_ids(records, remapping)
    assert remapped == records
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
```bash
python3 -m pytest tests/test_assured_ids.py::test_remap_ids_preserves_id_when_module_moves -v
```

Expected: ImportError on `remap_ids`.

- [ ] **Step 3: Implement the remapper**

Append to `plugins/sdlc-assured/scripts/assured/ids.py`:

```python
def remap_ids(records: List[IdRecord], path_remapping: dict[str, str]) -> List[IdRecord]:
    """Remap source paths using the given prefix remapping. IDs themselves are immutable."""
    out: List[IdRecord] = []
    for r in records:
        new_source = r.source
        for old_prefix, new_prefix in path_remapping.items():
            if r.source.startswith(old_prefix):
                new_source = new_prefix + r.source[len(old_prefix):]
                break
        out.append(IdRecord(
            id=r.id,
            kind=r.kind,
            source=new_source,
            satisfies=list(r.satisfies),
        ))
    return out
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_ids.py -v
```

Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/ids.py tests/test_assured_ids.py
git commit -m "feat(assured): id remapping for decomposition refactoring (Phase E task 9)"
```

---

## Task 10: programs.yaml parser

**Files:**
- Create: `plugins/sdlc-assured/scripts/assured/decomposition.py`
- Create: `tests/test_assured_decomposition.py`

- [ ] **Step 1: Write the failing test**

Write `tests/test_assured_decomposition.py`:

```python
"""Tests for assured.decomposition — programs.yaml schema + validators."""

from pathlib import Path

import pytest

from sdlc_assured_scripts.assured.decomposition import (
    DecompositionParseError,
    Module,
    Program,
    SubProgram,
    parse_programs_yaml,
    default_decomposition,
)


def test_parse_programs_yaml_extracts_modules(tmp_path: Path):
    pyaml = tmp_path / "programs.yaml"
    pyaml.write_text(
        """schema_version: 1
programs:
  - id: P1
    name: Auth platform
    sub_programs:
      - id: SP1
        name: Identity
        modules:
          - id: M1
            name: OAuth
            paths: [src/auth/oauth/]
            granularity: requirement
            structure: flat
visibility:
  - from: P1.SP1.M1
    to: []
"""
    )
    parsed = parse_programs_yaml(pyaml)
    assert parsed.programs[0].id == "P1"
    assert parsed.programs[0].sub_programs[0].id == "SP1"
    assert parsed.programs[0].sub_programs[0].modules[0].id == "M1"
    assert parsed.programs[0].sub_programs[0].modules[0].paths == ["src/auth/oauth/"]
    assert parsed.programs[0].sub_programs[0].modules[0].granularity == "requirement"


def test_parse_programs_yaml_raises_on_missing_schema_version(tmp_path: Path):
    pyaml = tmp_path / "programs.yaml"
    pyaml.write_text("programs: []\n")
    with pytest.raises(DecompositionParseError):
        parse_programs_yaml(pyaml)


def test_default_decomposition_is_p1_sp1_m1():
    parsed = default_decomposition(project_root_paths=["."])
    assert parsed.programs[0].id == "P1"
    assert parsed.programs[0].sub_programs[0].id == "SP1"
    assert parsed.programs[0].sub_programs[0].modules[0].id == "M1"
    assert parsed.programs[0].sub_programs[0].modules[0].paths == ["."]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
```bash
python3 -m pytest tests/test_assured_decomposition.py -v 2>&1 | tail -10
```

Expected: ImportError on `decomposition`.

- [ ] **Step 3: Implement the parser**

Write `plugins/sdlc-assured/scripts/assured/decomposition.py`:

```python
"""Decomposition declaration: programs.yaml parser + validators."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml


class DecompositionParseError(ValueError):
    """Raised when programs.yaml cannot be parsed."""


@dataclass(frozen=True)
class Module:
    id: str
    name: str
    paths: List[str]
    granularity: str
    structure: str
    owner: Optional[str] = None


@dataclass(frozen=True)
class SubProgram:
    id: str
    name: str
    modules: List[Module]


@dataclass(frozen=True)
class Program:
    id: str
    name: str
    description: Optional[str]
    sub_programs: List[SubProgram]


@dataclass(frozen=True)
class VisibilityRule:
    from_module: str
    to_modules: List[str]


@dataclass(frozen=True)
class Decomposition:
    programs: List[Program]
    visibility: List[VisibilityRule] = field(default_factory=list)


def parse_programs_yaml(path: Path) -> Decomposition:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DecompositionParseError(f"{path}: top-level must be a mapping")
    if raw.get("schema_version") != 1:
        raise DecompositionParseError(f"{path}: missing or unsupported schema_version (expected 1)")
    programs_raw = raw.get("programs", [])
    if not isinstance(programs_raw, list):
        raise DecompositionParseError(f"{path}: programs must be a list")
    programs: List[Program] = []
    for p in programs_raw:
        sub_programs: List[SubProgram] = []
        for sp in p.get("sub_programs", []):
            modules: List[Module] = []
            for m in sp.get("modules", []):
                modules.append(Module(
                    id=m["id"],
                    name=m["name"],
                    paths=list(m.get("paths", [])),
                    granularity=m.get("granularity", "requirement"),
                    structure=m.get("structure", "flat"),
                    owner=m.get("owner"),
                ))
            sub_programs.append(SubProgram(id=sp["id"], name=sp["name"], modules=modules))
        programs.append(Program(
            id=p["id"], name=p["name"],
            description=p.get("description"),
            sub_programs=sub_programs,
        ))
    visibility: List[VisibilityRule] = []
    for v in raw.get("visibility", []) or []:
        visibility.append(VisibilityRule(
            from_module=v["from"],
            to_modules=list(v.get("to", [])),
        ))
    return Decomposition(programs=programs, visibility=visibility)


def default_decomposition(project_root_paths: Optional[List[str]] = None) -> Decomposition:
    paths = project_root_paths or ["."]
    module = Module(
        id="M1", name="Default module",
        paths=paths,
        granularity="requirement",
        structure="flat",
    )
    sub_program = SubProgram(id="SP1", name="Default sub-program", modules=[module])
    program = Program(id="P1", name="Default program", description=None, sub_programs=[sub_program])
    return Decomposition(programs=[program], visibility=[])
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_decomposition.py -v 2>&1 | tail -10
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/decomposition.py tests/test_assured_decomposition.py
git commit -m "feat(assured): programs.yaml parser + default decomposition (Phase E task 10)"
```

---

## Task 11: REQ-has-module-assignment validator

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/decomposition.py`
- Modify: `tests/test_assured_decomposition.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_decomposition.py`:

```python
from sdlc_assured_scripts.assured.decomposition import (
    SpecArtefact,
    req_has_module_assignment,
)


def test_req_has_module_assignment_passes_when_frontmatter_declared():
    spec = SpecArtefact(
        path="docs/specs/auth/requirements-spec.md",
        feature_id="auth",
        module="P1.SP1.M1",
        ids=["REQ-auth-001"],
    )
    decomp = default_decomposition()
    result = req_has_module_assignment([spec], decomp)
    assert result.passed is True


def test_req_has_module_assignment_passes_when_positional_id_used():
    spec = SpecArtefact(
        path="docs/specs/auth/requirements-spec.md",
        feature_id=None,
        module=None,
        ids=["P1.SP1.M1.REQ-001"],
    )
    decomp = default_decomposition()
    result = req_has_module_assignment([spec], decomp)
    assert result.passed is True


def test_req_has_module_assignment_fails_when_module_undeclared():
    spec = SpecArtefact(
        path="docs/specs/auth/requirements-spec.md",
        feature_id="auth",
        module="P9.SP9.M9",  # not in decomposition
        ids=["REQ-auth-001"],
    )
    decomp = default_decomposition()
    result = req_has_module_assignment([spec], decomp)
    assert result.passed is False
    assert any("P9.SP9.M9" in e for e in result.errors)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
```bash
python3 -m pytest tests/test_assured_decomposition.py::test_req_has_module_assignment_passes_when_frontmatter_declared -v
```

Expected: ImportError on `SpecArtefact`, `req_has_module_assignment`.

- [ ] **Step 3: Implement the validator**

Append to `plugins/sdlc-assured/scripts/assured/decomposition.py`:

```python
@dataclass(frozen=True)
class SpecArtefact:
    """A parsed spec artefact for module-assignment validation."""

    path: str
    feature_id: Optional[str]
    module: Optional[str]
    ids: List[str]


@dataclass
class DecompositionValidatorResult:
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _all_module_ids(decomp: Decomposition) -> set[str]:
    out: set[str] = set()
    for p in decomp.programs:
        for sp in p.sub_programs:
            for m in sp.modules:
                out.add(f"{p.id}.{sp.id}.{m.id}")
    return out


def _module_from_positional_id(id_: str) -> Optional[str]:
    if "." not in id_:
        return None
    parts = id_.split(".")
    if len(parts) >= 4:
        return ".".join(parts[:3])
    return None


def req_has_module_assignment(
    specs: List[SpecArtefact], decomp: Decomposition
) -> DecompositionValidatorResult:
    declared = _all_module_ids(decomp)
    errors: List[str] = []
    for spec in specs:
        for id_ in spec.ids:
            if not id_.startswith("REQ"):
                # Only REQ artefacts need explicit module assignment per Article 16.
                if "." in id_ and id_.startswith("P"):
                    pass
                else:
                    continue
            module = _module_from_positional_id(id_) or spec.module
            if module is None:
                errors.append(
                    f"{id_} (in {spec.path}) has no module assignment"
                )
                continue
            if module not in declared:
                errors.append(
                    f"{id_} (in {spec.path}) is assigned to module {module!r} "
                    "which is not declared in programs.yaml"
                )
    return DecompositionValidatorResult(passed=not errors, errors=errors)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_decomposition.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/decomposition.py tests/test_assured_decomposition.py
git commit -m "feat(assured): req_has_module_assignment validator (Phase E task 11)"
```

---

## Task 12: CODE-annotation-maps-to-module validator

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/decomposition.py`
- Modify: `tests/test_assured_decomposition.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_decomposition.py`:

```python
from sdlc_assured_scripts.assured.decomposition import (
    CodeAnnotation,
    code_annotation_maps_to_module,
)


def test_code_annotation_maps_to_module_passes_when_path_under_module():
    annotation = CodeAnnotation(
        file_path="src/auth/oauth/login.py",
        line=42,
        cited_ids=["REQ-auth-001"],
    )
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: Auth
    sub_programs:
      - id: SP1
        name: Identity
        modules:
          - id: M1
            name: OAuth
            paths: [src/auth/oauth/]
            granularity: requirement
            structure: flat
"""
    )
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1"}
    result = code_annotation_maps_to_module([annotation], decomp, spec_lookup)
    assert result.passed is True


def test_code_annotation_maps_to_module_fails_when_path_outside_module():
    annotation = CodeAnnotation(
        file_path="src/payments/charge.py",
        line=10,
        cited_ids=["REQ-auth-001"],
    )
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: Auth
    sub_programs:
      - id: SP1
        name: Identity
        modules:
          - id: M1
            name: OAuth
            paths: [src/auth/oauth/]
            granularity: requirement
            structure: flat
"""
    )
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1"}
    result = code_annotation_maps_to_module([annotation], decomp, spec_lookup)
    assert result.passed is False
    assert any("src/payments/charge.py" in e for e in result.errors)
```

Add this helper near the top of `tests/test_assured_decomposition.py`:

```python
def parse_programs_yaml_inline(content: str) -> "Decomposition":
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(content)
        return parse_programs_yaml(Path(f.name))
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_decomposition.py::test_code_annotation_maps_to_module_passes_when_path_under_module -v
```

Expected: ImportError on `CodeAnnotation`, `code_annotation_maps_to_module`.

- [ ] **Step 3: Implement the validator**

Append to `plugins/sdlc-assured/scripts/assured/decomposition.py`:

```python
@dataclass(frozen=True)
class CodeAnnotation:
    """A parsed `# implements:` annotation."""

    file_path: str
    line: int
    cited_ids: List[str]


def _module_paths(decomp: Decomposition) -> dict[str, List[str]]:
    out: dict[str, List[str]] = {}
    for p in decomp.programs:
        for sp in p.sub_programs:
            for m in sp.modules:
                out[f"{p.id}.{sp.id}.{m.id}"] = list(m.paths)
    return out


def _file_under_paths(file_path: str, paths: List[str]) -> bool:
    return any(file_path.startswith(p) for p in paths)


def code_annotation_maps_to_module(
    annotations: List[CodeAnnotation],
    decomp: Decomposition,
    spec_module_lookup: dict[str, str],
) -> DecompositionValidatorResult:
    """Each annotation's file path must lie under its cited spec's module path.

    spec_module_lookup maps REQ/DES/TEST IDs to their declared module.
    """
    paths_by_module = _module_paths(decomp)
    errors: List[str] = []
    for ann in annotations:
        for cited in ann.cited_ids:
            module = spec_module_lookup.get(cited)
            if module is None:
                # Caught by cited_ids_resolve; skip here.
                continue
            allowed_paths = paths_by_module.get(module, [])
            if not _file_under_paths(ann.file_path, allowed_paths):
                errors.append(
                    f"{ann.file_path}:{ann.line} cites {cited} (module {module}) "
                    f"but file is not under any declared path: {allowed_paths}"
                )
    return DecompositionValidatorResult(passed=not errors, errors=errors)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_decomposition.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/decomposition.py tests/test_assured_decomposition.py
git commit -m "feat(assured): code_annotation_maps_to_module validator (Phase E task 12)"
```

---

## Task 13: Visibility-rule-enforcement validator

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/decomposition.py`
- Modify: `tests/test_assured_decomposition.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_decomposition.py`:

```python
from sdlc_assured_scripts.assured.decomposition import (
    ImportEdge,
    visibility_rule_enforcement,
)


def test_visibility_rule_enforcement_passes_when_edge_declared():
    edges = [ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2")]
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: M1, paths: [src/a/], granularity: requirement, structure: flat}
          - {id: M2, name: M2, paths: [src/b/], granularity: requirement, structure: flat}
visibility:
  - from: P1.SP1.M1
    to: [P1.SP1.M2]
"""
    )
    result = visibility_rule_enforcement(edges, decomp, mode="strict")
    assert result.passed is True


def test_visibility_rule_enforcement_fails_when_edge_undeclared_in_strict_mode():
    edges = [ImportEdge(from_module="P1.SP1.M2", to_module="P1.SP1.M1")]
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: M1, paths: [src/a/], granularity: requirement, structure: flat}
          - {id: M2, name: M2, paths: [src/b/], granularity: requirement, structure: flat}
visibility:
  - from: P1.SP1.M1
    to: [P1.SP1.M2]
"""
    )
    result = visibility_rule_enforcement(edges, decomp, mode="strict")
    assert result.passed is False
    assert any("P1.SP1.M2" in e and "P1.SP1.M1" in e for e in result.errors)


def test_visibility_rule_enforcement_warns_in_advisory_mode():
    edges = [ImportEdge(from_module="P1.SP1.M2", to_module="P1.SP1.M1")]
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: M1, paths: [src/a/], granularity: requirement, structure: flat}
          - {id: M2, name: M2, paths: [src/b/], granularity: requirement, structure: flat}
visibility:
  - from: P1.SP1.M1
    to: [P1.SP1.M2]
"""
    )
    result = visibility_rule_enforcement(edges, decomp, mode="advisory")
    assert result.passed is True
    assert any("P1.SP1.M2" in w and "P1.SP1.M1" in w for w in result.warnings)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_decomposition.py::test_visibility_rule_enforcement_passes_when_edge_declared -v
```

Expected: ImportError on `ImportEdge`, `visibility_rule_enforcement`.

- [ ] **Step 3: Implement the validator**

Append to `plugins/sdlc-assured/scripts/assured/decomposition.py`:

```python
@dataclass(frozen=True)
class ImportEdge:
    """A directed dependency edge between modules, derived from imports."""

    from_module: str
    to_module: str


def visibility_rule_enforcement(
    edges: List[ImportEdge], decomp: Decomposition, mode: str = "advisory"
) -> DecompositionValidatorResult:
    """Verify each cross-module edge is declared in the visibility block.

    mode = 'strict' → undeclared edges block (errors).
    mode = 'advisory' → undeclared edges warn.
    """
    declared: dict[str, set[str]] = {}
    for v in decomp.visibility:
        declared[v.from_module] = set(v.to_modules)
    issues: List[str] = []
    for edge in edges:
        if edge.from_module == edge.to_module:
            continue
        allowed = declared.get(edge.from_module, set())
        if edge.to_module not in allowed:
            issues.append(
                f"undeclared visibility: {edge.from_module} → {edge.to_module}"
            )
    if mode == "strict":
        return DecompositionValidatorResult(passed=not issues, errors=issues)
    return DecompositionValidatorResult(passed=True, warnings=issues)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_decomposition.py -v
```

Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/decomposition.py tests/test_assured_decomposition.py
git commit -m "feat(assured): visibility_rule_enforcement (advisory + strict) (Phase E task 13)"
```

---

## Task 14: Anaemic-context-detection validator

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/decomposition.py`
- Modify: `tests/test_assured_decomposition.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_decomposition.py`:

```python
from sdlc_assured_scripts.assured.decomposition import anaemic_context_detection


def test_anaemic_context_passes_when_code_co_located():
    annotations = [
        CodeAnnotation(file_path="src/auth/oauth/login.py", line=10, cited_ids=["REQ-auth-001"]),
        CodeAnnotation(file_path="src/auth/oauth/refresh.py", line=20, cited_ids=["REQ-auth-002"]),
    ]
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1", "REQ-auth-002": "P1.SP1.M1"}
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: OAuth, paths: [src/auth/oauth/], granularity: requirement, structure: flat}
"""
    )
    result = anaemic_context_detection(annotations, decomp, spec_lookup)
    assert result.passed is True


def test_anaemic_context_fails_when_code_scattered():
    """Two REQs from the same module, but their code lives under different module paths."""
    annotations = [
        CodeAnnotation(file_path="src/auth/oauth/login.py", line=10, cited_ids=["REQ-auth-001"]),
        CodeAnnotation(file_path="src/payments/charge.py", line=20, cited_ids=["REQ-auth-002"]),
    ]
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1", "REQ-auth-002": "P1.SP1.M1"}
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: OAuth, paths: [src/auth/oauth/], granularity: requirement, structure: flat}
"""
    )
    result = anaemic_context_detection(annotations, decomp, spec_lookup)
    assert result.passed is False
    assert any("anaemic" in e.lower() for e in result.errors)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_decomposition.py::test_anaemic_context_passes_when_code_co_located -v
```

Expected: ImportError on `anaemic_context_detection`.

- [ ] **Step 3: Implement the validator**

Append to `plugins/sdlc-assured/scripts/assured/decomposition.py`:

```python
def anaemic_context_detection(
    annotations: List[CodeAnnotation],
    decomp: Decomposition,
    spec_module_lookup: dict[str, str],
) -> DecompositionValidatorResult:
    """Flag when code implementing a module's REQs/DESs lives outside the module's paths."""
    paths_by_module = _module_paths(decomp)
    errors: List[str] = []
    for ann in annotations:
        for cited in ann.cited_ids:
            module = spec_module_lookup.get(cited)
            if module is None:
                continue
            allowed_paths = paths_by_module.get(module, [])
            if not _file_under_paths(ann.file_path, allowed_paths):
                errors.append(
                    f"anaemic context: {ann.file_path}:{ann.line} implements {cited} "
                    f"(module {module}) but file is outside the module's paths {allowed_paths}"
                )
    return DecompositionValidatorResult(passed=not errors, errors=errors)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_decomposition.py -v
```

Expected: 13 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/decomposition.py tests/test_assured_decomposition.py
git commit -m "feat(assured): anaemic_context_detection validator (Phase E task 14)"
```

---

## Task 15: Granularity-match validator

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/decomposition.py`
- Modify: `tests/test_assured_decomposition.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_decomposition.py`:

```python
from sdlc_assured_scripts.assured.decomposition import granularity_match


def test_granularity_match_passes_when_each_req_has_annotation():
    declared_reqs = ["REQ-auth-001", "REQ-auth-002"]
    annotations = [
        CodeAnnotation(file_path="src/auth/oauth/login.py", line=10, cited_ids=["REQ-auth-001"]),
        CodeAnnotation(file_path="src/auth/oauth/refresh.py", line=20, cited_ids=["REQ-auth-002"]),
    ]
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1", "REQ-auth-002": "P1.SP1.M1"}
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: OAuth, paths: [src/auth/oauth/], granularity: requirement, structure: flat}
"""
    )
    result = granularity_match(declared_reqs, annotations, decomp, spec_lookup)
    assert result.passed is True


def test_granularity_match_warns_when_req_under_specified():
    declared_reqs = ["REQ-auth-001", "REQ-auth-002"]
    annotations = [
        CodeAnnotation(file_path="src/auth/oauth/login.py", line=10, cited_ids=["REQ-auth-001"]),
    ]
    spec_lookup = {"REQ-auth-001": "P1.SP1.M1", "REQ-auth-002": "P1.SP1.M1"}
    decomp = parse_programs_yaml_inline(
        """schema_version: 1
programs:
  - id: P1
    name: P1
    sub_programs:
      - id: SP1
        name: SP1
        modules:
          - {id: M1, name: OAuth, paths: [src/auth/oauth/], granularity: requirement, structure: flat}
"""
    )
    result = granularity_match(declared_reqs, annotations, decomp, spec_lookup)
    assert result.passed is True
    assert any("REQ-auth-002" in w for w in result.warnings)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_decomposition.py::test_granularity_match_passes_when_each_req_has_annotation -v
```

Expected: ImportError on `granularity_match`.

- [ ] **Step 3: Implement the validator**

Append to `plugins/sdlc-assured/scripts/assured/decomposition.py`:

```python
def granularity_match(
    declared_reqs: List[str],
    annotations: List[CodeAnnotation],
    decomp: Decomposition,
    spec_module_lookup: dict[str, str],
) -> DecompositionValidatorResult:
    """For modules with granularity=requirement, every REQ must have at least one annotation."""
    cited: set[str] = set()
    for ann in annotations:
        cited.update(ann.cited_ids)
    granularity_by_module: dict[str, str] = {}
    for p in decomp.programs:
        for sp in p.sub_programs:
            for m in sp.modules:
                granularity_by_module[f"{p.id}.{sp.id}.{m.id}"] = m.granularity
    warnings: List[str] = []
    for req in declared_reqs:
        module = spec_module_lookup.get(req)
        if module is None:
            continue
        if granularity_by_module.get(module) != "requirement":
            continue
        if req not in cited:
            warnings.append(f"under-specified: {req} (module {module}) has no `# implements:` annotation")
    return DecompositionValidatorResult(passed=True, warnings=warnings)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_decomposition.py -v
```

Expected: 15 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/decomposition.py tests/test_assured_decomposition.py
git commit -m "feat(assured): granularity_match validator (Phase E task 15)"
```

---

## Task 16: Forward link integrity validator

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/traceability_validators.py`
- Modify: `tests/test_assured_traceability_validators.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_traceability_validators.py`:

```python
from sdlc_assured_scripts.assured.traceability_validators import forward_link_integrity


def test_forward_link_integrity_passes_when_chain_intact():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]),
        IdRecord(id="TEST-auth-001", kind="TEST", source="c.md", satisfies=["REQ-auth-001", "DES-auth-001"]),
    ]
    result = forward_link_integrity(records)
    assert result.passed is True


def test_forward_link_integrity_fails_when_des_targets_missing_req():
    records = [
        IdRecord(id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-999"]),
    ]
    result = forward_link_integrity(records)
    assert result.passed is False
    assert any("REQ-auth-999" in e for e in result.errors)


def test_forward_link_integrity_requires_des_to_cite_a_req():
    """A DES with no satisfies links is a defect under Article 15."""
    records = [
        IdRecord(id="DES-auth-001", kind="DES", source="b.md", satisfies=[]),
    ]
    result = forward_link_integrity(records)
    assert result.passed is False
    assert any("DES-auth-001" in e and "no satisfies" in e.lower() for e in result.errors)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py::test_forward_link_integrity_passes_when_chain_intact -v
```

Expected: ImportError on `forward_link_integrity`.

- [ ] **Step 3: Implement the validator**

Append to `plugins/sdlc-assured/scripts/assured/traceability_validators.py`:

```python
def forward_link_integrity(records: List[IdRecord]) -> ValidatorResult:
    """Verify every DES cites at least one REQ; every TEST cites at least one DES; targets resolve."""
    declared = {r.id: r for r in records}
    errors: List[str] = []
    for r in records:
        if r.kind == "DES" and not r.satisfies:
            errors.append(f"{r.id} (in {r.source}) has no satisfies links — DES must cite at least one REQ")
        if r.kind == "TEST" and not r.satisfies:
            errors.append(f"{r.id} (in {r.source}) has no satisfies links — TEST must cite at least one DES")
        for cited in r.satisfies:
            if cited not in declared:
                errors.append(f"{r.id} (in {r.source}) cites missing target {cited!r}")
    return ValidatorResult(passed=not errors, errors=errors)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py -v
```

Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/traceability_validators.py tests/test_assured_traceability_validators.py
git commit -m "feat(assured): forward_link_integrity validator (Phase E task 16)"
```

---

## Task 17: Backward coverage validator

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/traceability_validators.py`
- Modify: `tests/test_assured_traceability_validators.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_traceability_validators.py`:

```python
from sdlc_assured_scripts.assured.traceability_validators import backward_coverage


def test_backward_coverage_passes_when_every_req_has_des_test():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]),
        IdRecord(id="TEST-auth-001", kind="TEST", source="c.md", satisfies=["REQ-auth-001", "DES-auth-001"]),
    ]
    result = backward_coverage(records)
    assert result.passed is True


def test_backward_coverage_fails_when_req_has_no_des():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
    ]
    result = backward_coverage(records)
    assert result.passed is False
    assert any("REQ-auth-001" in e and "no DES" in e for e in result.errors)


def test_backward_coverage_fails_when_des_has_no_test():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="a.md", satisfies=[]),
        IdRecord(id="DES-auth-001", kind="DES", source="b.md", satisfies=["REQ-auth-001"]),
    ]
    result = backward_coverage(records)
    assert result.passed is False
    assert any("DES-auth-001" in e and "no TEST" in e for e in result.errors)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py::test_backward_coverage_passes_when_every_req_has_des_test -v
```

Expected: ImportError on `backward_coverage`.

- [ ] **Step 3: Implement the validator**

Append to `plugins/sdlc-assured/scripts/assured/traceability_validators.py`:

```python
def backward_coverage(records: List[IdRecord]) -> ValidatorResult:
    cited_by: dict[str, list[str]] = {r.id: [] for r in records}
    for r in records:
        for target in r.satisfies:
            if target in cited_by:
                cited_by[target].append(r.id)
    errors: List[str] = []
    for r in records:
        if r.kind == "REQ":
            des_children = [c for c in cited_by[r.id] if c.startswith("DES") or "DES-" in c.split(".")[-1]]
            if not des_children:
                errors.append(f"{r.id} (in {r.source}) has no DES covering it")
        if r.kind == "DES":
            test_children = [c for c in cited_by[r.id] if c.startswith("TEST") or "TEST-" in c.split(".")[-1]]
            if not test_children:
                errors.append(f"{r.id} (in {r.source}) has no TEST covering it")
    return ValidatorResult(passed=not errors, errors=errors)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py -v
```

Expected: 12 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/traceability_validators.py tests/test_assured_traceability_validators.py
git commit -m "feat(assured): backward_coverage validator (Phase E task 17)"
```

---

## Task 18: Index regenerability validator (idempotency)

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/traceability_validators.py`
- Modify: `tests/test_assured_traceability_validators.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_traceability_validators.py`:

```python
from pathlib import Path

from sdlc_assured_scripts.assured.traceability_validators import index_regenerability


def test_index_regenerability_passes_when_byte_identical(tmp_path: Path):
    index_path = tmp_path / "_ids.md"
    index_path.write_text("# ID Registry\n| ID | Kind | Source | Satisfies |\n")
    def regenerate() -> str:
        return "# ID Registry\n| ID | Kind | Source | Satisfies |\n"
    result = index_regenerability(index_path, regenerate)
    assert result.passed is True


def test_index_regenerability_fails_when_drift(tmp_path: Path):
    index_path = tmp_path / "_ids.md"
    index_path.write_text("# ID Registry\nOLD\n")
    def regenerate() -> str:
        return "# ID Registry\nNEW\n"
    result = index_regenerability(index_path, regenerate)
    assert result.passed is False
    assert any("not idempotent" in e.lower() for e in result.errors)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py::test_index_regenerability_passes_when_byte_identical -v
```

Expected: ImportError on `index_regenerability`.

- [ ] **Step 3: Implement the validator**

Append to `plugins/sdlc-assured/scripts/assured/traceability_validators.py`:

```python
from pathlib import Path
from typing import Callable


def index_regenerability(
    index_path: Path, regenerate: Callable[[], str]
) -> ValidatorResult:
    """Idempotency check: re-running the generator must produce byte-identical output."""
    if not index_path.is_file():
        return ValidatorResult(
            passed=False,
            errors=[f"index file does not exist: {index_path}"],
        )
    on_disk = index_path.read_text(encoding="utf-8")
    fresh = regenerate()
    if on_disk == fresh:
        return ValidatorResult(passed=True)
    return ValidatorResult(
        passed=False,
        errors=[
            f"index {index_path} is not idempotent — committed content differs from regenerated output. "
            "Run kb-rebuild-indexes and commit."
        ],
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py -v
```

Expected: 14 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/traceability_validators.py tests/test_assured_traceability_validators.py
git commit -m "feat(assured): index_regenerability validator (Phase E task 18)"
```

---

## Task 19: Annotation format integrity validator

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/traceability_validators.py`
- Modify: `tests/test_assured_traceability_validators.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_traceability_validators.py`:

```python
from sdlc_assured_scripts.assured.traceability_validators import annotation_format_integrity


def test_annotation_format_integrity_passes_on_valid_annotations(tmp_path: Path):
    f = tmp_path / "login.py"
    f.write_text(
        "def login():\n"
        "    # implements: REQ-auth-001\n"
        "    pass\n"
    )
    result = annotation_format_integrity([f], declared_ids={"REQ-auth-001"})
    assert result.passed is True


def test_annotation_format_integrity_fails_on_unknown_id(tmp_path: Path):
    f = tmp_path / "login.py"
    f.write_text(
        "def login():\n"
        "    # implements: REQ-auth-999\n"
        "    pass\n"
    )
    result = annotation_format_integrity([f], declared_ids={"REQ-auth-001"})
    assert result.passed is False
    assert any("REQ-auth-999" in e for e in result.errors)


def test_annotation_format_integrity_fails_on_malformed_annotation(tmp_path: Path):
    f = tmp_path / "login.py"
    f.write_text(
        "def login():\n"
        "    # implements: not_an_id\n"
        "    pass\n"
    )
    result = annotation_format_integrity([f], declared_ids={"REQ-auth-001"})
    assert result.passed is False
    assert any("malformed" in e.lower() or "not_an_id" in e for e in result.errors)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py::test_annotation_format_integrity_passes_on_valid_annotations -v
```

Expected: ImportError on `annotation_format_integrity`.

- [ ] **Step 3: Implement the validator**

Append to `plugins/sdlc-assured/scripts/assured/traceability_validators.py`:

```python
import re

from .ids import IdParseError, parse_id

_IMPLEMENTS_RE = re.compile(r"^\s*#\s*implements:\s*(?P<ids>.+)$", re.MULTILINE)
_ID_TOKEN_RE = re.compile(r"[A-Za-z0-9.\-]+")


def annotation_format_integrity(
    code_files: List[Path], declared_ids: set[str]
) -> ValidatorResult:
    errors: List[str] = []
    for f in code_files:
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            m = _IMPLEMENTS_RE.match(line)
            if not m:
                continue
            ids_part = m["ids"]
            tokens = [t.strip(",") for t in _ID_TOKEN_RE.findall(ids_part)]
            for tok in tokens:
                try:
                    parse_id(tok)
                except IdParseError:
                    errors.append(f"{f}:{line_no}: malformed annotation token {tok!r}")
                    continue
                if tok not in declared_ids:
                    errors.append(f"{f}:{line_no}: annotation cites {tok!r} which is not declared")
    return ValidatorResult(passed=not errors, errors=errors)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py -v
```

Expected: 17 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/traceability_validators.py tests/test_assured_traceability_validators.py
git commit -m "feat(assured): annotation_format_integrity validator (Phase E task 19)"
```

---

## Task 20: Optional change-impact-gate validator

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/traceability_validators.py`
- Modify: `tests/test_assured_traceability_validators.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_traceability_validators.py`:

```python
from sdlc_assured_scripts.assured.traceability_validators import change_impact_gate


def test_change_impact_gate_passes_when_disabled():
    """The gate is opt-in; when disabled, it always passes."""
    result = change_impact_gate(
        changed_code_files=[Path("src/auth/login.py")],
        change_impact_records_dir=Path("docs/change-impacts"),
        enabled=False,
    )
    assert result.passed is True


def test_change_impact_gate_fails_when_enabled_and_no_record(tmp_path: Path):
    code_file = tmp_path / "src" / "auth" / "login.py"
    code_file.parent.mkdir(parents=True)
    code_file.write_text("def login(): pass\n")
    impacts_dir = tmp_path / "docs" / "change-impacts"
    impacts_dir.mkdir(parents=True)  # empty
    result = change_impact_gate(
        changed_code_files=[code_file],
        change_impact_records_dir=impacts_dir,
        enabled=True,
    )
    assert result.passed is False
    assert any("change-impact" in e.lower() for e in result.errors)


def test_change_impact_gate_passes_when_record_exists(tmp_path: Path):
    code_file = tmp_path / "src" / "auth" / "login.py"
    code_file.parent.mkdir(parents=True)
    code_file.write_text("def login(): pass\n")
    impacts_dir = tmp_path / "docs" / "change-impacts"
    impacts_dir.mkdir(parents=True)
    (impacts_dir / "CHG-001.md").write_text(
        "# Change CHG-001\n## CODE locations touched\n- src/auth/login.py: rewrite\n"
    )
    result = change_impact_gate(
        changed_code_files=[code_file],
        change_impact_records_dir=impacts_dir,
        enabled=True,
    )
    assert result.passed is True
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py::test_change_impact_gate_passes_when_disabled -v
```

Expected: ImportError on `change_impact_gate`.

- [ ] **Step 3: Implement the validator**

Append to `plugins/sdlc-assured/scripts/assured/traceability_validators.py`:

```python
def change_impact_gate(
    changed_code_files: List[Path],
    change_impact_records_dir: Path,
    enabled: bool,
) -> ValidatorResult:
    """When enabled, every changed code file must be cited in at least one change-impact record."""
    if not enabled:
        return ValidatorResult(passed=True)
    if not change_impact_records_dir.is_dir():
        return ValidatorResult(
            passed=False,
            errors=[f"change-impact directory {change_impact_records_dir} does not exist"],
        )
    cited_paths: set[str] = set()
    for record in change_impact_records_dir.glob("*.md"):
        cited_paths |= {
            line.split(":")[0].strip().lstrip("- ")
            for line in record.read_text(encoding="utf-8").splitlines()
            if "src/" in line and ":" in line
        }
    errors: List[str] = []
    for f in changed_code_files:
        rel = str(f).replace(str(f.anchor), "")
        if not any(rel.endswith(c) or c in str(f) for c in cited_paths):
            errors.append(f"{f}: no change-impact record cites this file")
    return ValidatorResult(passed=not errors, errors=errors)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_traceability_validators.py -v
```

Expected: 20 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/traceability_validators.py tests/test_assured_traceability_validators.py
git commit -m "feat(assured): change_impact_gate (optional) validator (Phase E task 20)"
```

---

## Task 21: KB code index parser

**Files:**
- Create: `plugins/sdlc-assured/scripts/assured/code_index.py`
- Create: `tests/test_assured_code_index.py`

- [ ] **Step 1: Write the failing test**

Write `tests/test_assured_code_index.py`:

```python
"""Tests for assured.code_index — annotation parsing + shelf-index emission."""

from pathlib import Path

from sdlc_assured_scripts.assured.code_index import (
    CodeIndexEntry,
    parse_code_annotations,
    render_code_index,
)


def test_parse_code_annotations_extracts_implements_lines(tmp_path: Path):
    f = tmp_path / "login.py"
    f.write_text(
        "def login(token):\n"
        "    # implements: DES-auth-005, REQ-auth-003\n"
        "    return token\n"
        "\n"
        "def logout():\n"
        "    # implements: REQ-auth-007\n"
        "    pass\n"
    )
    entries = parse_code_annotations([f], project_root=tmp_path)
    assert len(entries) == 2
    assert entries[0].file_path == "login.py"
    assert entries[0].line == 2
    assert entries[0].cited_ids == ["DES-auth-005", "REQ-auth-003"]
    assert entries[1].cited_ids == ["REQ-auth-007"]


def test_render_code_index_produces_shelf_shape(tmp_path: Path):
    entries = [
        CodeIndexEntry(
            file_path="src/auth/login.py", line=10,
            cited_ids=["REQ-auth-001"],
            terms=["login", "auth", "session"],
            facts=["Issues a session cookie on success"],
        ),
    ]
    output = render_code_index(entries, library_handle="local-project")
    assert "<!-- format_version: 1 -->" in output
    assert "<!-- library_handle: local-project -->" in output
    assert "## 1. src/auth/login.py:10" in output
    assert "**Terms:** login, auth, session" in output
    assert "**Facts:**" in output
    assert "**Links:** REQ-auth-001" in output
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_code_index.py -v 2>&1 | tail -10
```

Expected: ImportError on `code_index`.

- [ ] **Step 3: Implement the parser + emitter**

Write `plugins/sdlc-assured/scripts/assured/code_index.py`:

```python
"""Code annotation parsing and `_code-index.md` emission for the Assured bundle."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List


_IMPLEMENTS_RE = re.compile(r"^\s*#\s*implements:\s*(?P<ids>.+)$")
_ID_TOKEN_RE = re.compile(
    r"\b((?:P\d+\.SP\d+\.M\d+\.)?(?:REQ|DES|TEST|CODE)-(?:[a-z0-9][a-z0-9-]*-)?\d+)\b"
)


@dataclass(frozen=True)
class CodeIndexEntry:
    file_path: str
    line: int
    cited_ids: List[str]
    terms: List[str] = field(default_factory=list)
    facts: List[str] = field(default_factory=list)


def parse_code_annotations(
    files: List[Path], project_root: Path
) -> List[CodeIndexEntry]:
    entries: List[CodeIndexEntry] = []
    for f in files:
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        rel_path = str(f.relative_to(project_root)) if project_root in f.parents or f.parent == project_root else str(f.name)
        for line_no, line in enumerate(text.splitlines(), start=1):
            m = _IMPLEMENTS_RE.match(line)
            if not m:
                continue
            cited = _ID_TOKEN_RE.findall(m["ids"])
            entries.append(CodeIndexEntry(
                file_path=rel_path,
                line=line_no,
                cited_ids=cited,
            ))
    return entries


def render_code_index(entries: List[CodeIndexEntry], library_handle: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "<!-- format_version: 1 -->",
        f"<!-- last_rebuilt: {timestamp} -->",
        f"<!-- library_handle: {library_handle} -->",
        "<!-- library_description: Code index — annotation-derived shelf-index for source code -->",
        "# Code Index",
        "",
        "Generated by `kb-codeindex`. Each entry corresponds to one `# implements:` annotation in source code.",
        "",
        "---",
        "",
    ]
    for n, e in enumerate(entries, start=1):
        terms = ", ".join(e.terms) if e.terms else ""
        lines.append(f"## {n}. {e.file_path}:{e.line}")
        lines.append("")
        lines.append(f"**Terms:** {terms}")
        if e.facts:
            lines.append("**Facts:**")
            for fact in e.facts:
                lines.append(f"- {fact}")
        else:
            lines.append("**Facts:**")
        lines.append(f"**Links:** {', '.join(e.cited_ids)}")
        lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_code_index.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/code_index.py tests/test_assured_code_index.py
git commit -m "feat(assured): kb-codeindex parser + emitter (Phase E task 21)"
```

---

## Task 22: Spec-as-finding emitter

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/code_index.py`
- Modify: `tests/test_assured_code_index.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_code_index.py`:

```python
from sdlc_assured_scripts.assured.ids import IdRecord
from sdlc_assured_scripts.assured.code_index import render_spec_findings


def test_render_spec_findings_emits_one_entry_per_id():
    records = [
        IdRecord(
            id="REQ-auth-001", kind="REQ",
            source="docs/specs/auth/requirements-spec.md",
            satisfies=[],
        ),
        IdRecord(
            id="DES-auth-001", kind="DES",
            source="docs/specs/auth/design-spec.md",
            satisfies=["REQ-auth-001"],
        ),
    ]
    output = render_spec_findings(records, library_handle="local-project")
    assert "<!-- format_version: 1 -->" in output
    assert "## 1. REQ-auth-001" in output
    assert "**Terms:** REQ, auth" in output
    assert "**Links:**" in output
    assert "## 2. DES-auth-001" in output
    assert "REQ-auth-001" in output
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_code_index.py::test_render_spec_findings_emits_one_entry_per_id -v
```

Expected: ImportError on `render_spec_findings`.

- [ ] **Step 3: Implement the emitter**

Append to `plugins/sdlc-assured/scripts/assured/code_index.py`:

```python
from .ids import IdRecord


def render_spec_findings(records: List[IdRecord], library_handle: str) -> str:
    """Render REQ/DES/TEST records as shelf-index entries (spec-as-KB-finding)."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "<!-- format_version: 1 -->",
        f"<!-- last_rebuilt: {timestamp} -->",
        f"<!-- library_handle: {library_handle} -->",
        "<!-- library_description: Spec findings — REQ/DES/TEST records as shelf-index entries -->",
        "# Spec Findings",
        "",
    ]
    for n, r in enumerate(records, start=1):
        feature = _feature_from_id(r.id)
        terms = ", ".join([r.kind] + ([feature] if feature else []))
        links = ", ".join(r.satisfies) if r.satisfies else r.source
        lines.append(f"## {n}. {r.id}")
        lines.append("")
        lines.append(f"**Terms:** {terms}")
        lines.append("**Facts:**")
        lines.append(f"- Declared in {r.source}")
        lines.append(f"**Links:** {links}")
        lines.append("")
    return "\n".join(lines)


def _feature_from_id(id_: str) -> str | None:
    if id_.startswith("P") and "." in id_:
        return None
    parts = id_.split("-")
    if len(parts) >= 3:
        return parts[1]
    return None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_code_index.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/code_index.py tests/test_assured_code_index.py
git commit -m "feat(assured): spec-as-KB-finding emitter (Phase E task 22)"
```

---

## Task 23: Synthesis-librarian SYNTHESISE-ACROSS-SPEC-TYPES extension

**Files:**
- Modify: `plugins/sdlc-knowledge-base/agents/synthesis-librarian.md`
- Modify: `skills/synthesis-librarian.md` (if it exists as a root mirror — verify first; otherwise skip)

- [ ] **Step 1: Read the existing synthesis-librarian to understand the mode-switch pattern**

Run:
```bash
grep -n "MODE:" plugins/sdlc-knowledge-base/agents/synthesis-librarian.md
```

Note the existing modes (e.g., `SYNTHESISE-ACROSS-SOURCES`).

- [ ] **Step 2: Add the SYNTHESISE-ACROSS-SPEC-TYPES mode**

Read `plugins/sdlc-knowledge-base/agents/synthesis-librarian.md`. Find the section that documents the `SYNTHESISE-ACROSS-SOURCES` mode. After that section, add:

```markdown
### MODE: SYNTHESISE-ACROSS-SPEC-TYPES

**Activated when** the dispatch prompt declares `mode: synthesise-across-spec-types` and provides spec-type pseudo-handles (`req`, `des`, `test`, `code`).

**Behaviour:** treat each spec-type pseudo-handle as a sub-library. The shelf-index entries are spec records emitted by `kb-codeindex` and the spec-as-finding emitter. Compose an answer that connects findings across REQ → DES → TEST → CODE, attributing each fact to its source ID. Always cite by ID, not by file path.

**Output format:**

```
## Synthesis

<connected argument across spec types>

## Attribution

- REQ-auth-001 (source: docs/specs/auth/requirements-spec.md)
- DES-auth-001 (source: docs/specs/auth/design-spec.md)
- TEST-auth-001 (source: docs/specs/auth/test-spec.md)
- CODE: src/auth/login.py:42
```

**valid_handles extension:** when this mode is active, accept `req`, `des`, `test`, `code` as pseudo-handles in addition to the project's library handles.
```

- [ ] **Step 3: Verify the file is well-formed**

Run:
```bash
grep -c "^## " plugins/sdlc-knowledge-base/agents/synthesis-librarian.md
```

Expected: count of top-level headings increased by 0 (the mode is a `###` subheading).

- [ ] **Step 4: Commit**

```bash
git add plugins/sdlc-knowledge-base/agents/synthesis-librarian.md
git commit -m "feat(kb): synthesis-librarian SYNTHESISE-ACROSS-SPEC-TYPES mode (Phase E task 23)"
```

---

## Task 24: Module-scoped render

**Files:**
- Create: `plugins/sdlc-assured/scripts/assured/render.py`
- Create: `tests/test_assured_render.py`

- [ ] **Step 1: Write the failing test**

Write `tests/test_assured_render.py`:

```python
"""Tests for assured.render — module-scoped traceability render."""

from sdlc_assured_scripts.assured.ids import IdRecord
from sdlc_assured_scripts.assured.code_index import CodeIndexEntry
from sdlc_assured_scripts.assured.render import render_module_scope


def test_render_module_scope_includes_reqs_des_tests_code():
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="docs/specs/auth/requirements-spec.md", satisfies=[]),
        IdRecord(id="DES-auth-001", kind="DES", source="docs/specs/auth/design-spec.md", satisfies=["REQ-auth-001"]),
        IdRecord(id="TEST-auth-001", kind="TEST", source="docs/specs/auth/test-spec.md", satisfies=["REQ-auth-001", "DES-auth-001"]),
    ]
    code_entries = [
        CodeIndexEntry(file_path="src/auth/login.py", line=10, cited_ids=["REQ-auth-001"]),
    ]
    spec_module_lookup = {"REQ-auth-001": "P1.SP1.M1", "DES-auth-001": "P1.SP1.M1", "TEST-auth-001": "P1.SP1.M1"}
    output = render_module_scope(
        module_id="P1.SP1.M1",
        records=records,
        code_entries=code_entries,
        spec_module_lookup=spec_module_lookup,
    )
    assert "# Module: P1.SP1.M1" in output
    assert "## Requirements" in output
    assert "REQ-auth-001" in output
    assert "## Designs" in output
    assert "DES-auth-001" in output
    assert "## Tests" in output
    assert "TEST-auth-001" in output
    assert "## Code" in output
    assert "src/auth/login.py:10" in output


def test_render_module_scope_flags_orphan_code():
    records = []
    code_entries = [
        CodeIndexEntry(file_path="src/auth/orphan.py", line=5, cited_ids=["REQ-auth-999"]),
    ]
    spec_module_lookup = {}
    output = render_module_scope(
        module_id="P1.SP1.M1",
        records=records,
        code_entries=code_entries,
        spec_module_lookup=spec_module_lookup,
    )
    assert "## Orphan code" in output
    assert "src/auth/orphan.py:5" in output
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_render.py -v 2>&1 | tail -10
```

Expected: ImportError on `render`.

- [ ] **Step 3: Implement the render**

Write `plugins/sdlc-assured/scripts/assured/render.py`:

```python
"""Module-scoped traceability render and module-dependency-graph for the Assured bundle."""

from __future__ import annotations

from typing import List

from .code_index import CodeIndexEntry
from .ids import IdRecord


def render_module_scope(
    module_id: str,
    records: List[IdRecord],
    code_entries: List[CodeIndexEntry],
    spec_module_lookup: dict[str, str],
) -> str:
    """Render the REQ → DES → TEST → CODE chain for a single module."""
    in_module = [r for r in records if spec_module_lookup.get(r.id) == module_id]
    reqs = [r for r in in_module if r.kind == "REQ"]
    deses = [r for r in in_module if r.kind == "DES"]
    tests = [r for r in in_module if r.kind == "TEST"]
    in_module_code = [
        c for c in code_entries
        if any(spec_module_lookup.get(cid) == module_id for cid in c.cited_ids)
    ]
    orphan_code = [
        c for c in code_entries
        if c not in in_module_code
        and not any(cid in spec_module_lookup for cid in c.cited_ids)
    ]
    lines = [
        f"# Module: {module_id}",
        "",
        "## Requirements",
        "",
    ]
    for r in reqs:
        lines.append(f"- **{r.id}** — [{r.source}](../../{r.source})")
    if not reqs:
        lines.append("_(no requirements)_")
    lines.extend(["", "## Designs", ""])
    for d in deses:
        sat = ", ".join(d.satisfies) if d.satisfies else "(no satisfies)"
        lines.append(f"- **{d.id}** satisfies {sat} — [{d.source}](../../{d.source})")
    if not deses:
        lines.append("_(no designs)_")
    lines.extend(["", "## Tests", ""])
    for t in tests:
        sat = ", ".join(t.satisfies) if t.satisfies else "(no satisfies)"
        lines.append(f"- **{t.id}** satisfies {sat} — [{t.source}](../../{t.source})")
    if not tests:
        lines.append("_(no tests)_")
    lines.extend(["", "## Code", ""])
    for c in in_module_code:
        cited = ", ".join(c.cited_ids)
        lines.append(f"- `{c.file_path}:{c.line}` implements {cited}")
    if not in_module_code:
        lines.append("_(no code annotations)_")
    if orphan_code:
        lines.extend(["", "## Orphan code", "", "Code citing IDs that do not exist in the registry:"])
        for c in orphan_code:
            cited = ", ".join(c.cited_ids)
            lines.append(f"- `{c.file_path}:{c.line}` cites missing {cited}")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_render.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/render.py tests/test_assured_render.py
git commit -m "feat(assured): module-scoped traceability render (Phase E task 24)"
```

---

## Task 25: Module-dependency-graph (Q1: markdown edge-list)

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/render.py`
- Modify: `tests/test_assured_render.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_render.py`:

```python
from sdlc_assured_scripts.assured.decomposition import (
    Decomposition, ImportEdge, Module, Program, SubProgram, VisibilityRule,
)
from sdlc_assured_scripts.assured.render import render_module_dependency_graph


def _two_module_decomp() -> Decomposition:
    m1 = Module(id="M1", name="M1", paths=["src/a/"], granularity="requirement", structure="flat")
    m2 = Module(id="M2", name="M2", paths=["src/b/"], granularity="requirement", structure="flat")
    sp = SubProgram(id="SP1", name="SP1", modules=[m1, m2])
    p = Program(id="P1", name="P1", description=None, sub_programs=[sp])
    visibility = [VisibilityRule(from_module="P1.SP1.M1", to_modules=["P1.SP1.M2"])]
    return Decomposition(programs=[p], visibility=visibility)


def test_render_module_dependency_graph_lists_each_actual_edge():
    decomp = _two_module_decomp()
    actual_edges = [
        ImportEdge(from_module="P1.SP1.M1", to_module="P1.SP1.M2"),
        ImportEdge(from_module="P1.SP1.M2", to_module="P1.SP1.M1"),  # disallowed
    ]
    output = render_module_dependency_graph(decomp, actual_edges)
    assert "| From | → | To | Allowed? |" in output
    assert "| P1.SP1.M1 | → | P1.SP1.M2 | yes |" in output
    assert "| P1.SP1.M2 | → | P1.SP1.M1 | NO |" in output


def test_render_module_dependency_graph_handles_zero_edges():
    decomp = _two_module_decomp()
    output = render_module_dependency_graph(decomp, [])
    assert "_(no module-to-module dependencies detected)_" in output
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_render.py::test_render_module_dependency_graph_lists_each_actual_edge -v
```

Expected: ImportError on `render_module_dependency_graph`.

- [ ] **Step 3: Implement the render**

Append to `plugins/sdlc-assured/scripts/assured/render.py`:

```python
from .decomposition import Decomposition, ImportEdge


def render_module_dependency_graph(
    decomp: Decomposition, actual_edges: List[ImportEdge]
) -> str:
    """Render the module-dependency graph as a markdown edge-list (Q1 v0.1.0 format)."""
    declared: dict[str, set[str]] = {}
    for v in decomp.visibility:
        declared[v.from_module] = set(v.to_modules)
    lines = [
        "# Module Dependency Graph",
        "",
        "Each row represents one observed cross-module edge. \"Allowed?\" reflects the project's `programs.yaml` visibility block.",
        "",
    ]
    if not actual_edges:
        lines.append("_(no module-to-module dependencies detected)_")
        return "\n".join(lines) + "\n"
    lines.extend([
        "| From | → | To | Allowed? |",
        "|------|---|----|----------|",
    ])
    sorted_edges = sorted({(e.from_module, e.to_module) for e in actual_edges})
    for from_, to_ in sorted_edges:
        allowed = "yes" if to_ in declared.get(from_, set()) else "NO"
        lines.append(f"| {from_} | → | {to_} | {allowed} |")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_render.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/render.py tests/test_assured_render.py
git commit -m "feat(assured): module-dependency-graph as markdown edge-list (Q1 v0.1.0) (Phase E task 25)"
```

---

## Task 26: Traceability-export — DO-178C RTM format

**Files:**
- Create: `plugins/sdlc-assured/scripts/assured/export.py`
- Create: `tests/test_assured_export.py`

- [ ] **Step 1: Write the failing test**

Write `tests/test_assured_export.py`:

```python
"""Tests for assured.export — standard-specific traceability formats."""

from sdlc_assured_scripts.assured.ids import IdRecord
from sdlc_assured_scripts.assured.code_index import CodeIndexEntry
from sdlc_assured_scripts.assured.export import export_do178c_rtm


def _three_id_chain() -> tuple[list[IdRecord], list[CodeIndexEntry]]:
    records = [
        IdRecord(id="REQ-auth-001", kind="REQ", source="docs/specs/auth/requirements-spec.md", satisfies=[]),
        IdRecord(id="DES-auth-001", kind="DES", source="docs/specs/auth/design-spec.md", satisfies=["REQ-auth-001"]),
        IdRecord(id="TEST-auth-001", kind="TEST", source="docs/specs/auth/test-spec.md", satisfies=["REQ-auth-001", "DES-auth-001"]),
    ]
    code = [CodeIndexEntry(file_path="src/auth/login.py", line=10, cited_ids=["REQ-auth-001"])]
    return records, code


def test_export_do178c_rtm_columns():
    records, code = _three_id_chain()
    output = export_do178c_rtm(records, code)
    # DO-178C Requirements Traceability Matrix expects: HLR → LLR → Source code → Test cases.
    assert "Requirements Traceability Matrix (DO-178C)" in output
    assert "| HLR | LLR | Source code | Test case |" in output
    assert "| REQ-auth-001 | DES-auth-001 | src/auth/login.py:10 | TEST-auth-001 |" in output
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_export.py -v 2>&1 | tail -10
```

Expected: ImportError on `export`.

- [ ] **Step 3: Implement the export**

Write `plugins/sdlc-assured/scripts/assured/export.py`:

```python
"""Standard-specific traceability exports."""

from __future__ import annotations

from collections import defaultdict
from typing import List

from .code_index import CodeIndexEntry
from .ids import IdRecord


def _index_by_satisfies(records: List[IdRecord]) -> dict[str, list[IdRecord]]:
    """Records keyed by what they satisfy: target_id → [records that cite target_id]."""
    out: dict[str, list[IdRecord]] = defaultdict(list)
    for r in records:
        for target in r.satisfies:
            out[target].append(r)
    return out


def _code_by_cited(code: List[CodeIndexEntry]) -> dict[str, list[CodeIndexEntry]]:
    out: dict[str, list[CodeIndexEntry]] = defaultdict(list)
    for c in code:
        for cited in c.cited_ids:
            out[cited].append(c)
    return out


def export_do178c_rtm(records: List[IdRecord], code: List[CodeIndexEntry]) -> str:
    """DO-178C Requirements Traceability Matrix.

    Columns: HLR (high-level requirement) | LLR (low-level requirement / design) |
    Source code | Test case.
    """
    cited_by = _index_by_satisfies(records)
    code_by_cited = _code_by_cited(code)
    lines = [
        "# Requirements Traceability Matrix (DO-178C)",
        "",
        "Generated by `traceability-export do-178c-rtm`. Each row links a high-level requirement to its low-level requirements (designs), implementing source code, and verifying test cases.",
        "",
        "| HLR | LLR | Source code | Test case |",
        "|-----|-----|-------------|-----------|",
    ]
    reqs = [r for r in records if r.kind == "REQ"]
    for req in reqs:
        deses = [d for d in cited_by.get(req.id, []) if d.kind == "DES"]
        for des in deses:
            tests = [t for t in cited_by.get(des.id, []) if t.kind == "TEST"]
            code_locs = code_by_cited.get(req.id, []) + code_by_cited.get(des.id, [])
            code_str = ", ".join(f"{c.file_path}:{c.line}" for c in code_locs) or "—"
            test_str = ", ".join(t.id for t in tests) or "—"
            lines.append(f"| {req.id} | {des.id} | {code_str} | {test_str} |")
        if not deses:
            lines.append(f"| {req.id} | — | — | — |")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_export.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/export.py tests/test_assured_export.py
git commit -m "feat(assured): export do-178c-rtm format (Phase E task 26)"
```

---

## Task 27: Traceability-export — IEC 62304 matrix format

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/export.py`
- Modify: `tests/test_assured_export.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_export.py`:

```python
from sdlc_assured_scripts.assured.export import export_iec_62304_matrix


def test_export_iec_62304_matrix_columns():
    records, code = _three_id_chain()
    output = export_iec_62304_matrix(records, code, software_safety_class="B")
    # IEC 62304 expects: Software requirement → Software unit → Verification activity.
    assert "IEC 62304 Software Traceability Matrix" in output
    assert "Software safety class: B" in output
    assert "| Software requirement | Software unit | Verification activity |" in output
    assert "REQ-auth-001" in output
    assert "src/auth/login.py" in output
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_export.py::test_export_iec_62304_matrix_columns -v
```

Expected: ImportError on `export_iec_62304_matrix`.

- [ ] **Step 3: Implement the export**

Append to `plugins/sdlc-assured/scripts/assured/export.py`:

```python
def export_iec_62304_matrix(
    records: List[IdRecord], code: List[CodeIndexEntry], software_safety_class: str = "A"
) -> str:
    """IEC 62304 Software Traceability Matrix.

    Columns: Software requirement | Software unit (code) | Verification activity (test).
    Software safety class is declared in the heading (A, B, or C).
    """
    cited_by = _index_by_satisfies(records)
    code_by_cited = _code_by_cited(code)
    lines = [
        "# IEC 62304 Software Traceability Matrix",
        "",
        f"Software safety class: {software_safety_class}",
        "",
        "| Software requirement | Software unit | Verification activity |",
        "|----------------------|---------------|------------------------|",
    ]
    reqs = [r for r in records if r.kind == "REQ"]
    for req in reqs:
        units = code_by_cited.get(req.id, [])
        deses = [d for d in cited_by.get(req.id, []) if d.kind == "DES"]
        tests: List[IdRecord] = []
        for des in deses:
            units.extend(code_by_cited.get(des.id, []))
            tests.extend([t for t in cited_by.get(des.id, []) if t.kind == "TEST"])
        unit_str = ", ".join(f"{c.file_path}:{c.line}" for c in units) or "—"
        test_str = ", ".join(t.id for t in tests) or "—"
        lines.append(f"| {req.id} | {unit_str} | {test_str} |")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_export.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/export.py tests/test_assured_export.py
git commit -m "feat(assured): export iec-62304-matrix format (Phase E task 27)"
```

---

## Task 28: Traceability-export — ISO 26262 ASIL matrix format

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/export.py`
- Modify: `tests/test_assured_export.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_export.py`:

```python
from sdlc_assured_scripts.assured.export import export_iso_26262_asil_matrix


def test_export_iso_26262_asil_matrix_columns():
    records, code = _three_id_chain()
    output = export_iso_26262_asil_matrix(records, code, asil_level="C")
    assert "ISO 26262 ASIL Traceability Matrix" in output
    assert "ASIL: C" in output
    assert "| Safety requirement | Architectural element | Implementation | Verification |" in output
    assert "REQ-auth-001" in output
    assert "DES-auth-001" in output
    assert "src/auth/login.py" in output
    assert "TEST-auth-001" in output
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_export.py::test_export_iso_26262_asil_matrix_columns -v
```

Expected: ImportError on `export_iso_26262_asil_matrix`.

- [ ] **Step 3: Implement the export**

Append to `plugins/sdlc-assured/scripts/assured/export.py`:

```python
def export_iso_26262_asil_matrix(
    records: List[IdRecord], code: List[CodeIndexEntry], asil_level: str = "B"
) -> str:
    """ISO 26262 ASIL Traceability Matrix.

    Columns: Safety requirement | Architectural element (design) |
    Implementation (code) | Verification (test).
    """
    cited_by = _index_by_satisfies(records)
    code_by_cited = _code_by_cited(code)
    lines = [
        "# ISO 26262 ASIL Traceability Matrix",
        "",
        f"ASIL: {asil_level}",
        "",
        "| Safety requirement | Architectural element | Implementation | Verification |",
        "|---------------------|----------------------|----------------|---------------|",
    ]
    reqs = [r for r in records if r.kind == "REQ"]
    for req in reqs:
        deses = [d for d in cited_by.get(req.id, []) if d.kind == "DES"]
        for des in deses:
            tests = [t for t in cited_by.get(des.id, []) if t.kind == "TEST"]
            code_locs = code_by_cited.get(req.id, []) + code_by_cited.get(des.id, [])
            code_str = ", ".join(f"{c.file_path}:{c.line}" for c in code_locs) or "—"
            test_str = ", ".join(t.id for t in tests) or "—"
            lines.append(f"| {req.id} | {des.id} | {code_str} | {test_str} |")
        if not deses:
            lines.append(f"| {req.id} | — | — | — |")
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_export.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/export.py tests/test_assured_export.py
git commit -m "feat(assured): export iso-26262-asil-matrix format (Phase E task 28)"
```

---

## Task 29: Traceability-export — FDA DHF structure format

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/export.py`
- Modify: `tests/test_assured_export.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_export.py`:

```python
from sdlc_assured_scripts.assured.export import export_fda_dhf_structure


def test_export_fda_dhf_structure_sections():
    records, code = _three_id_chain()
    output = export_fda_dhf_structure(records, code)
    # FDA 21 CFR §820.30 Design History File expects sections per design control element.
    assert "FDA Design History File (21 CFR §820.30)" in output
    assert "## Design inputs" in output
    assert "REQ-auth-001" in output
    assert "## Design outputs" in output
    assert "DES-auth-001" in output
    assert "## Design verification" in output
    assert "TEST-auth-001" in output
    assert "## Design validation" in output  # placeholder section per regulation
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_export.py::test_export_fda_dhf_structure_sections -v
```

Expected: ImportError on `export_fda_dhf_structure`.

- [ ] **Step 3: Implement the export**

Append to `plugins/sdlc-assured/scripts/assured/export.py`:

```python
def export_fda_dhf_structure(records: List[IdRecord], code: List[CodeIndexEntry]) -> str:
    """FDA Design History File structure (21 CFR §820.30).

    Sections: Design inputs (REQs) | Design outputs (DESs + code) |
    Design verification (TESTs) | Design validation (placeholder for human attestation).
    """
    reqs = [r for r in records if r.kind == "REQ"]
    deses = [r for r in records if r.kind == "DES"]
    tests = [r for r in records if r.kind == "TEST"]
    lines = [
        "# FDA Design History File (21 CFR §820.30)",
        "",
        "Generated by `traceability-export fda-dhf-structure`. This document organises traceability artefacts under the design control sections of 21 CFR §820.30.",
        "",
        "## Design inputs",
        "",
        "(Per §820.30(c) — Design inputs)",
        "",
    ]
    for r in reqs:
        lines.append(f"- **{r.id}**: see {r.source}")
    if not reqs:
        lines.append("_(no requirements declared)_")
    lines.extend(["", "## Design outputs", "", "(Per §820.30(d) — Design outputs)", ""])
    for d in deses:
        lines.append(f"- **{d.id}** satisfies {', '.join(d.satisfies)}: see {d.source}")
    lines.append("")
    for c in code:
        lines.append(f"- Source code: `{c.file_path}:{c.line}` implements {', '.join(c.cited_ids)}")
    if not deses and not code:
        lines.append("_(no design outputs declared)_")
    lines.extend(["", "## Design verification", "", "(Per §820.30(f) — Design verification)", ""])
    for t in tests:
        lines.append(f"- **{t.id}** verifies {', '.join(t.satisfies)}: see {t.source}")
    if not tests:
        lines.append("_(no verification tests declared)_")
    lines.extend([
        "",
        "## Design validation",
        "",
        "(Per §820.30(g) — Design validation)",
        "",
        "_Design validation is performed under defined operating conditions on initial production units, units that simulate them, or their equivalents._ This section is a placeholder for human-attested validation evidence; the framework does not auto-populate it.",
        "",
    ])
    return "\n".join(lines)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_export.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/export.py tests/test_assured_export.py
git commit -m "feat(assured): export fda-dhf-structure format (Phase E task 29)"
```

---

## Task 30: Traceability-export — csv + markdown re-exports

**Files:**
- Modify: `plugins/sdlc-assured/scripts/assured/export.py`
- Modify: `tests/test_assured_export.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_assured_export.py`:

```python
from sdlc_assured_scripts.assured.export import export_csv, export_markdown


def test_export_csv_emits_header_and_rows():
    records, code = _three_id_chain()
    output = export_csv(records, code)
    assert output.startswith("REQ,DES,TEST,CODE")
    assert "REQ-auth-001" in output
    assert "src/auth/login.py:10" in output


def test_export_markdown_emits_table():
    records, code = _three_id_chain()
    output = export_markdown(records, code)
    assert "| REQ | DES | TEST | CODE |" in output
    assert "| REQ-auth-001 | DES-auth-001 | TEST-auth-001 |" in output
```

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/test_assured_export.py::test_export_csv_emits_header_and_rows -v
```

Expected: ImportError on `export_csv`, `export_markdown`.

- [ ] **Step 3: Implement the exports**

Append to `plugins/sdlc-assured/scripts/assured/export.py`:

```python
def _build_rows(records: List[IdRecord], code: List[CodeIndexEntry]) -> list[tuple[str, str, str, str]]:
    cited_by = _index_by_satisfies(records)
    code_by_cited = _code_by_cited(code)
    rows: list[tuple[str, str, str, str]] = []
    for req in [r for r in records if r.kind == "REQ"]:
        deses = [d for d in cited_by.get(req.id, []) if d.kind == "DES"]
        if not deses:
            rows.append((req.id, "", "", ""))
            continue
        for des in deses:
            tests = [t for t in cited_by.get(des.id, []) if t.kind == "TEST"]
            code_locs = code_by_cited.get(req.id, []) + code_by_cited.get(des.id, [])
            code_str = "; ".join(f"{c.file_path}:{c.line}" for c in code_locs)
            test_str = "; ".join(t.id for t in tests)
            rows.append((req.id, des.id, test_str, code_str))
    return rows


def export_csv(records: List[IdRecord], code: List[CodeIndexEntry]) -> str:
    rows = _build_rows(records, code)
    out = ["REQ,DES,TEST,CODE"]
    for r in rows:
        out.append(",".join(c.replace(",", ";") for c in r))
    return "\n".join(out) + "\n"


def export_markdown(records: List[IdRecord], code: List[CodeIndexEntry]) -> str:
    rows = _build_rows(records, code)
    out = [
        "# Traceability Matrix",
        "",
        "| REQ | DES | TEST | CODE |",
        "|-----|-----|------|------|",
    ]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out) + "\n"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/test_assured_export.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add plugins/sdlc-assured/scripts/assured/export.py tests/test_assured_export.py
git commit -m "feat(assured): export csv + markdown formats (Phase E task 30)"
```

---

## Task 31: Skill — commission-assured

**Files:**
- Create: `skills/commission-assured/SKILL.md`
- Create: `plugins/sdlc-assured/skills/commission-assured/SKILL.md` (mirror)

- [ ] **Step 1: Write the SKILL.md**

Write `skills/commission-assured/SKILL.md`:

```markdown
---
name: commission-assured
description: Commission a project to the Assured (Method 2) SDLC bundle — install plugin, scaffold programs.yaml, set granularity and regulatory context, configure change-impact-gate.
disable-model-invocation: true
---

# Skill: commission-assured

**Use this skill** when the user wants to commission a project to the Assured (Method 2) SDLC option. This is a one-time installation that scaffolds the decomposition declaration, sets regulatory context, and configures optional validators.

This skill assumes:
- The project already has the `sdlc-programme` plugin installed (Assured layers on Programme).
- The user has authority to commission (this is an irrevocable decision per Article 16).

## Steps

1. **Verify prerequisites.** Confirm `sdlc-programme` is installed; confirm `sdlc-knowledge-base` is initialised (run `kb-init` if not).

2. **Prompt for regulatory context.**
    - Which regulatory standards apply? (DO-178C / IEC 62304 / ISO 26262 / IEC 61508 / FDA 21 CFR §820 / none / multiple)
    - For IEC 62304: software safety class (A / B / C)
    - For ISO 26262: ASIL level (A / B / C / D)
    - For DO-178C: DAL (A / B / C / D / E)

3. **Prompt for decomposition.**
    - Does the project have one logical area or multiple? (single → use default `P1.SP1.M1`; multiple → scaffold a `programs.yaml` with placeholders to fill in)
    - If multiple: how many programs? Sub-programs per program? Modules per sub-program?

4. **Scaffold the artefacts.**
    - Copy `programs.yaml` template to `programs.yaml` (project root) with placeholders substituted.
    - Copy `visibility-rules.md` template to `docs/architecture/visibility-rules.md`.
    - For regulated contexts (IEC 62304 ≥ B, FDA, ISO 26262 ASIL ≥ C): copy `change-impact.md` template to `docs/change-impacts/CHG-template.md`.
    - Add `library/_ids.md` and `library/_code-index.md` placeholders (will be populated by `kb-codeindex` and `kb-rebuild-indexes`).

5. **Configure validators.**
    - Set commissioning flags in `.sdlc/team-config.json`:
      - `assured.visibility_mode: strict` for regulated contexts; `advisory` otherwise
      - `assured.change_impact_gate: enabled` for IEC 62304 ≥ B, FDA, ISO 26262 ASIL ≥ C; `disabled` otherwise

6. **Run initial validation.**
    - `python3 -m sdlc_assured_scripts.assured.ids` to build initial `library/_ids.md`
    - `kb-codeindex` to build initial `library/_code-index.md` (will be empty until annotations exist)
    - Confirm validators run cleanly on the empty/scaffolded project.

7. **Commit the commissioning.**
    - One commit per scaffolded artefact group (programs.yaml + visibility-rules.md as one; change-impact template as another).

## Done criteria

- `programs.yaml` committed with no placeholder text remaining.
- `library/_ids.md` and `library/_code-index.md` exist (may be empty).
- `.sdlc/team-config.json` has `assured.*` flags set.
- Validators run without errors on the freshly-commissioned project.
```

- [ ] **Step 2: Mirror to the plugin directory**

```bash
mkdir -p plugins/sdlc-assured/skills/commission-assured/
cp skills/commission-assured/SKILL.md plugins/sdlc-assured/skills/commission-assured/SKILL.md
```

- [ ] **Step 3: Verify byte-identical mirror**

Run:
```bash
diff skills/commission-assured/SKILL.md plugins/sdlc-assured/skills/commission-assured/SKILL.md
```

Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add skills/commission-assured/ plugins/sdlc-assured/skills/commission-assured/
git commit -m "feat(assured): commission-assured skill (Phase E task 31)"
```

---

## Task 32: Skill — req-add

**Files:**
- Create: `skills/req-add/SKILL.md`
- Create: `plugins/sdlc-assured/skills/req-add/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

Write `skills/req-add/SKILL.md`:

```markdown
---
name: req-add
description: Mint a new REQ ID in the Assured project's namespace, with module assignment, and append it to the requirements-spec.
---

# Skill: req-add

**Use this skill** when adding a new requirement to an existing requirements-spec under the Assured bundle. Computes the next sequential ID for the feature and module, prompts for the requirement text, and appends a properly-formatted `### REQ-...` section.

## Inputs

- `<feature-id>` (or `<module-id>` for positional projects): which spec to append to
- The requirement text (single declarative sentence)

## Steps

1. **Locate the requirements-spec.** Read `docs/specs/<feature-id>/requirements-spec.md`. If the project uses positional decomposition, read the spec for the matching module.

2. **Compute the next REQ number.** Scan existing `### REQ-...` headings. New ID is the max + 1, zero-padded to 3 digits.

3. **Prompt for the requirement text.** Ask: "Single declarative sentence describing the new requirement?"

4. **Append the section.**
    ```markdown
    ### REQ-<feature-id>-<NNN>

    <text>

    **Module:** <module-id>
    ```

5. **Confirm.** Show the diff to the user before saving.

6. **Save.** Write the file.

7. **Remind.** "Next steps: add a corresponding DES in design-spec.md (use `req-link`), then a TEST in test-spec.md."

## Done criteria

- New REQ section appended with correct ID, no renumbering of existing IDs.
- Module assignment present.
- File saved; no other changes.
```

- [ ] **Step 2: Mirror**

```bash
mkdir -p plugins/sdlc-assured/skills/req-add/
cp skills/req-add/SKILL.md plugins/sdlc-assured/skills/req-add/SKILL.md
```

- [ ] **Step 3: Commit**

```bash
git add skills/req-add/ plugins/sdlc-assured/skills/req-add/
git commit -m "feat(assured): req-add skill (Phase E task 32)"
```

---

## Task 33: Skill — req-link

**Files:**
- Create: `skills/req-link/SKILL.md`
- Create: `plugins/sdlc-assured/skills/req-link/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

Write `skills/req-link/SKILL.md`:

```markdown
---
name: req-link
description: Add a satisfies link from a DES → REQ, TEST → REQ/DES, or CODE annotation → ID, validating that the target exists in the registry.
---

# Skill: req-link

**Use this skill** when adding a `satisfies:` link between artefacts, OR when adding an inline `# implements:` annotation in source code. This skill validates that the target ID exists before writing the link.

## Inputs

- `<source-id>` — the artefact gaining the link (e.g., `DES-auth-001`)
- `<target-ids>` — the ID(s) being satisfied (e.g., `REQ-auth-001`)

## Steps

1. **Read the registry.** Load `library/_ids.md`. Confirm every `<target-id>` exists.

2. **Locate the source artefact.** Find the file declaring `<source-id>`.

3. **Insert the link.**
    - For spec artefacts: insert `**satisfies:** <target-ids>` immediately after the `### <source-id>` heading.
    - For code annotations: prompt for the function name; insert `# implements: <target-ids>` as the first line of the function body.

4. **Re-validate.** Run `id_uniqueness`, `cited_ids_resolve`, `forward_link_integrity`. Report results.

5. **Commit the link** (separate commit so it can be reverted independently).

## Done criteria

- Link inserted; target IDs verified to exist in the registry.
- Validators pass after the link is added.
- One commit, scope-limited to the link.
```

- [ ] **Step 2: Mirror**

```bash
mkdir -p plugins/sdlc-assured/skills/req-link/
cp skills/req-link/SKILL.md plugins/sdlc-assured/skills/req-link/SKILL.md
```

- [ ] **Step 3: Commit**

```bash
git add skills/req-link/ plugins/sdlc-assured/skills/req-link/
git commit -m "feat(assured): req-link skill (Phase E task 33)"
```

---

## Task 34: Skill — code-annotate

**Files:**
- Create: `skills/code-annotate/SKILL.md`
- Create: `plugins/sdlc-assured/skills/code-annotate/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

Write `skills/code-annotate/SKILL.md`:

```markdown
---
name: code-annotate
description: Generate boilerplate `# implements:` annotation for a function based on the artefact ID, inserting it as the first line of the function body.
---

# Skill: code-annotate

**Use this skill** when adding implementation code that satisfies a REQ or DES. Generates the correct `# implements:` annotation, validates that the cited IDs exist in the registry, and inserts the annotation in a syntactically-correct place.

## Inputs

- `<artefact-id>` — the REQ or DES being implemented (e.g., `REQ-auth-001`, `DES-auth-001`, or `P1.SP2.M3.REQ-007`)
- File path and function name (from active editing context)

## Steps

1. **Verify the artefact exists.** Read `library/_ids.md`; confirm `<artefact-id>` is declared.

2. **Detect the language.** Python (`#`), JavaScript/TypeScript (`//`), Go (`//`), Rust (`//`). Default `#` if unknown.

3. **Determine the comment line.** Choose the comment syntax matching the file extension.

4. **Insert the annotation.** Place `<comment-prefix> implements: <artefact-id>` as the first line of the function body, immediately after the opening brace / `:` / `func ... {`.

5. **Confirm.** Show the diff to the user.

6. **Run annotation_format_integrity** on the file to verify the annotation parses correctly.

## Done criteria

- Annotation inserted in syntactically-correct location.
- annotation_format_integrity passes.
- One commit with the annotation; the implementing code is the user's responsibility.
```

- [ ] **Step 2: Mirror + commit**

```bash
mkdir -p plugins/sdlc-assured/skills/code-annotate/
cp skills/code-annotate/SKILL.md plugins/sdlc-assured/skills/code-annotate/SKILL.md
git add skills/code-annotate/ plugins/sdlc-assured/skills/code-annotate/
git commit -m "feat(assured): code-annotate skill (Phase E task 34)"
```

---

## Task 35: Skill — module-bound-check

**Files:**
- Create: `skills/module-bound-check/SKILL.md`
- Create: `plugins/sdlc-assured/skills/module-bound-check/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

Write `skills/module-bound-check/SKILL.md`:

```markdown
---
name: module-bound-check
description: Run all 5 decomposition validators (req-has-module, code-annotation-maps-to-module, visibility-rule-enforcement, anaemic-context-detection, granularity-match) on the project, reporting violations.
---

# Skill: module-bound-check

**Use this skill** to verify the project's decomposition is sound. Aggregates results from all 5 module-bound validators and reports a single pass/fail with per-validator detail. Run this before pushing a substantial change to a regulated-context project.

## Steps

1. **Load the decomposition.** Read `programs.yaml` (or use `default_decomposition` if absent).

2. **Build the spec_module_lookup.** Walk all `docs/specs/**/*.md` artefacts; map each declared ID → module (from frontmatter or positional ID prefix).

3. **Build the import-edge graph.** Walk source files; for each import, determine the from-module and to-module by mapping the file path to declared module paths.

4. **Run each validator.**
    - `req_has_module_assignment`
    - `code_annotation_maps_to_module`
    - `visibility_rule_enforcement` (mode from team-config: strict for regulated, advisory otherwise)
    - `anaemic_context_detection`
    - `granularity_match`

5. **Aggregate results.** Print a table:
    ```
    Validator                          Status   Errors  Warnings
    req_has_module_assignment          PASS     0       0
    code_annotation_maps_to_module     FAIL     2       0
    visibility_rule_enforcement        PASS     0       1
    anaemic_context_detection          PASS     0       0
    granularity_match                  PASS     0       3
    ```

6. **Report each error and warning** with file path and line number.

## Done criteria

- All 5 validators ran.
- Result table printed.
- Exit code: 0 if all pass; 1 if any error; 0 if only warnings (warnings don't block).
```

- [ ] **Step 2: Mirror + commit**

```bash
mkdir -p plugins/sdlc-assured/skills/module-bound-check/
cp skills/module-bound-check/SKILL.md plugins/sdlc-assured/skills/module-bound-check/SKILL.md
git add skills/module-bound-check/ plugins/sdlc-assured/skills/module-bound-check/
git commit -m "feat(assured): module-bound-check skill (Phase E task 35)"
```

---

## Task 36: Skill — kb-codeindex

**Files:**
- Create: `skills/kb-codeindex/SKILL.md`
- Create: `plugins/sdlc-assured/skills/kb-codeindex/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

Write `skills/kb-codeindex/SKILL.md`:

```markdown
---
name: kb-codeindex
description: Parse all `# implements:` annotations in source code and emit `library/_code-index.md` as a shelf-index. Idempotent — re-running produces byte-identical output if no annotations changed.
---

# Skill: kb-codeindex

**Use this skill** to build or refresh the project's code index. The output is structurally a KB shelf-index, queryable by the `research-librarian` agent like the regular library files. Run after adding/changing `# implements:` annotations.

## Inputs

- (no arguments — operates on the whole project)

## Steps

1. **Load the project root.** Detect from `.git/`.

2. **Walk source files.** Glob `**/*.{py,js,ts,go,rs,java}` excluding standard ignored paths (`.venv/`, `node_modules/`, `.git/`, etc.).

3. **Parse annotations.** Use `parse_code_annotations` to extract every `# implements:` line.

4. **Verify cited IDs.** For each citation, look it up in `library/_ids.md`. Report unresolved citations as warnings (not errors — `annotation_format_integrity` blocks at pre-push).

5. **Render the index.** Use `render_code_index` to produce shelf-index-shaped markdown.

6. **Write to `library/_code-index.md`.** If the file already exists, compare byte-for-byte; only write if different.

7. **Report.** Print: number of annotations processed, number of unresolved citations, whether the index file changed.

## Done criteria

- `library/_code-index.md` is up to date.
- Idempotent (re-running with no changes produces no diff).
- Unresolved citations reported but not failed.
```

- [ ] **Step 2: Mirror + commit**

```bash
mkdir -p plugins/sdlc-assured/skills/kb-codeindex/
cp skills/kb-codeindex/SKILL.md plugins/sdlc-assured/skills/kb-codeindex/SKILL.md
git add skills/kb-codeindex/ plugins/sdlc-assured/skills/kb-codeindex/
git commit -m "feat(assured): kb-codeindex skill (Phase E task 36)"
```

---

## Task 37: Skill — change-impact-annotate

**Files:**
- Create: `skills/change-impact-annotate/SKILL.md`
- Create: `plugins/sdlc-assured/skills/change-impact-annotate/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

Write `skills/change-impact-annotate/SKILL.md`:

```markdown
---
name: change-impact-annotate
description: Guide the team through writing a change-impact record for IEC 62304 / FDA / ISO 26262 ASIL C+ projects. Surfaces the affected REQ/DES/TEST/CODE artefacts and captures human-attested verification approach.
---

# Skill: change-impact-annotate

**Use this skill** before pushing a code change that touches a regulated-context project where `change_impact_gate` is enabled. Produces a `docs/change-impacts/CHG-NNN.md` record that satisfies the gate.

## Inputs

- The unstaged or just-staged code changes (read from `git diff`)

## Steps

1. **Inspect the diff.** Identify the touched files and (best-effort) the touched functions.

2. **Map files to module IDs** using `programs.yaml`.

3. **Map touched functions to cited artefact IDs** by parsing existing `# implements:` annotations.

4. **Compute the next CHG number.** Scan `docs/change-impacts/CHG-*.md`; new ID = max + 1.

5. **Generate a draft.** Use the `change-impact.md` template, pre-filled with:
    - Discovered REQs, DESs, TESTs, code locations, modules
    - Empty fields for: change summary, downstream effects, verification approach, approver

6. **Prompt the user** to fill in the empty fields. Surface verification approach as the highest-stakes field (this is the regulator's primary check).

7. **Save.** Write to `docs/change-impacts/CHG-<NNN>.md`.

8. **Re-run change_impact_gate** to verify the record covers all touched code files.

9. **Remind.** "Approval signature is required before merge — the framework records it; the human authorises it."

## Done criteria

- `CHG-<NNN>.md` written.
- All touched code files cited in the record.
- `change_impact_gate` passes.
```

- [ ] **Step 2: Mirror + commit**

```bash
mkdir -p plugins/sdlc-assured/skills/change-impact-annotate/
cp skills/change-impact-annotate/SKILL.md plugins/sdlc-assured/skills/change-impact-annotate/SKILL.md
git add skills/change-impact-annotate/ plugins/sdlc-assured/skills/change-impact-annotate/
git commit -m "feat(assured): change-impact-annotate skill (Phase E task 37)"
```

---

## Task 38: Skill — traceability-render

**Files:**
- Create: `skills/traceability-render/SKILL.md`
- Create: `plugins/sdlc-assured/skills/traceability-render/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

Write `skills/traceability-render/SKILL.md`:

```markdown
---
name: traceability-render
description: Render module-scoped human-readable traceability for a single module — REQs, DESs, TESTs, code locations with anchor links, plus the module-dependency graph as a markdown edge-list.
---

# Skill: traceability-render

**Use this skill** when a reviewer or auditor needs a human-readable view of one module's traceability. Produces a markdown document with anchors that resolve in any markdown renderer, no Sphinx required.

## Inputs

- `<module-id>` — e.g., `P1.SP1.M1`. If the project uses default decomposition, just `M1` is accepted.

## Steps

1. **Validate the module exists.** Read `programs.yaml`; confirm the module is declared.

2. **Load the registry.** Read `library/_ids.md` and `library/_code-index.md`.

3. **Filter to the module.** Keep only IDs whose module assignment matches.

4. **Render the module scope.** Use `render_module_scope`.

5. **Render the dependency graph.** Walk source-file imports to derive the `actual_edges`. Use `render_module_dependency_graph`.

6. **Concatenate** scope + dependency graph into one document.

7. **Write to `docs/traceability/<module-id>.md`.** Idempotent.

8. **Print** the path of the rendered document.

## Done criteria

- Document written.
- Contains REQs, DESs, TESTs, code, orphan code, dependency graph.
- Idempotent.
```

- [ ] **Step 2: Mirror + commit**

```bash
mkdir -p plugins/sdlc-assured/skills/traceability-render/
cp skills/traceability-render/SKILL.md plugins/sdlc-assured/skills/traceability-render/SKILL.md
git add skills/traceability-render/ plugins/sdlc-assured/skills/traceability-render/
git commit -m "feat(assured): traceability-render skill (Phase E task 38)"
```

---

## Task 39: End-to-end integration tests + Assured fixture

**Files:**
- Create: `tests/fixtures/assured/feature-sample/programs.yaml`
- Create: `tests/fixtures/assured/feature-sample/docs/specs/auth/requirements-spec.md`
- Create: `tests/fixtures/assured/feature-sample/docs/specs/auth/design-spec.md`
- Create: `tests/fixtures/assured/feature-sample/docs/specs/auth/test-spec.md`
- Create: `tests/fixtures/assured/feature-sample/src/auth/oauth/login.py`
- Create: `tests/test_assured_skill_integration.py`

- [ ] **Step 1: Build the fixture programs.yaml**

Write `tests/fixtures/assured/feature-sample/programs.yaml`:

```yaml
schema_version: 1
programs:
  - id: P1
    name: Auth Platform
    sub_programs:
      - id: SP1
        name: Identity
        modules:
          - id: M1
            name: OAuth
            paths: [src/auth/oauth/]
            granularity: requirement
            structure: flat
visibility:
  - from: P1.SP1.M1
    to: []
```

- [ ] **Step 2: Build the fixture spec artefacts**

Write `tests/fixtures/assured/feature-sample/docs/specs/auth/requirements-spec.md`:

```markdown
---
feature_id: auth
module: P1.SP1.M1
granularity: requirement
---

# Requirements Specification: Authentication

**Feature-id:** auth
**Module:** P1.SP1.M1

## Requirements

### REQ-auth-001
The system must authenticate users via OAuth 2.0.

**Module:** P1.SP1.M1

### REQ-auth-002
Sessions must expire after 24 hours of inactivity.

**Module:** P1.SP1.M1
```

Write `tests/fixtures/assured/feature-sample/docs/specs/auth/design-spec.md`:

```markdown
---
feature_id: auth
module: P1.SP1.M1
---

# Design Specification: Authentication

## Design elements

### DES-auth-001
Use PKCE (RFC 7636) for OAuth authorisation code flow.

**satisfies:** REQ-auth-001
**Module:** P1.SP1.M1

### DES-auth-002
Store session expiry as absolute UTC timestamp; check on every request.

**satisfies:** REQ-auth-002
**Module:** P1.SP1.M1
```

Write `tests/fixtures/assured/feature-sample/docs/specs/auth/test-spec.md`:

```markdown
---
feature_id: auth
module: P1.SP1.M1
---

# Test Specification: Authentication

## Test cases

### TEST-auth-001
Verify PKCE challenge/verifier round-trip.

**satisfies:** REQ-auth-001 via DES-auth-001
**Module:** P1.SP1.M1

### TEST-auth-002
Verify session expires exactly 24h after last activity.

**satisfies:** REQ-auth-002 via DES-auth-002
**Module:** P1.SP1.M1
```

- [ ] **Step 3: Build the fixture source code**

Write `tests/fixtures/assured/feature-sample/src/auth/oauth/login.py`:

```python
"""Sample OAuth login implementation for the assured fixture."""


def login_with_pkce(code: str, verifier: str) -> str:
    # implements: REQ-auth-001, DES-auth-001
    return f"session-for-{code}"


def is_session_active(last_activity_seconds_ago: int) -> bool:
    # implements: REQ-auth-002, DES-auth-002
    return last_activity_seconds_ago < 24 * 60 * 60
```

- [ ] **Step 4: Write the integration tests**

Write `tests/test_assured_skill_integration.py`:

```python
"""End-to-end integration tests over the Assured fixture.

These tests traverse the full pipeline: parse programs.yaml, build the ID
registry, parse code annotations, run all validators, render module scope.
The fixture is the smallest plausible Assured-bundle project.
"""

from pathlib import Path

import pytest

from sdlc_assured_scripts.assured.code_index import (
    parse_code_annotations,
    render_code_index,
    render_spec_findings,
)
from sdlc_assured_scripts.assured.decomposition import (
    CodeAnnotation,
    Decomposition,
    Module,
    Program,
    SubProgram,
    VisibilityRule,
    code_annotation_maps_to_module,
    parse_programs_yaml,
    req_has_module_assignment,
    SpecArtefact,
)
from sdlc_assured_scripts.assured.ids import build_id_registry, render_id_registry
from sdlc_assured_scripts.assured.render import render_module_scope
from sdlc_assured_scripts.assured.traceability_validators import (
    backward_coverage,
    cited_ids_resolve,
    forward_link_integrity,
    id_uniqueness,
)


FIXTURE = Path(__file__).parent / "fixtures" / "assured" / "feature-sample"


def test_fixture_programs_yaml_parses():
    decomp = parse_programs_yaml(FIXTURE / "programs.yaml")
    assert decomp.programs[0].id == "P1"
    assert decomp.programs[0].sub_programs[0].modules[0].id == "M1"


def test_fixture_id_registry_has_six_ids():
    records = build_id_registry(FIXTURE)
    ids = {r.id for r in records}
    assert ids == {
        "REQ-auth-001", "REQ-auth-002",
        "DES-auth-001", "DES-auth-002",
        "TEST-auth-001", "TEST-auth-002",
    }


def test_fixture_validators_all_pass():
    records = build_id_registry(FIXTURE)
    assert id_uniqueness(records).passed
    assert cited_ids_resolve(records).passed
    assert forward_link_integrity(records).passed
    assert backward_coverage(records).passed


def test_fixture_code_annotations_parse():
    code_files = list((FIXTURE / "src").rglob("*.py"))
    entries = parse_code_annotations(code_files, project_root=FIXTURE)
    cited = sorted({cid for e in entries for cid in e.cited_ids})
    assert cited == ["DES-auth-001", "DES-auth-002", "REQ-auth-001", "REQ-auth-002"]


def test_fixture_render_module_scope_produces_full_doc():
    records = build_id_registry(FIXTURE)
    code_files = list((FIXTURE / "src").rglob("*.py"))
    entries = parse_code_annotations(code_files, project_root=FIXTURE)
    spec_module_lookup = {r.id: "P1.SP1.M1" for r in records}
    output = render_module_scope("P1.SP1.M1", records, entries, spec_module_lookup)
    for required in ("REQ-auth-001", "DES-auth-001", "TEST-auth-001", "src/auth/oauth/login.py"):
        assert required in output


def test_fixture_code_annotations_in_module():
    decomp = parse_programs_yaml(FIXTURE / "programs.yaml")
    code_files = list((FIXTURE / "src").rglob("*.py"))
    entries = parse_code_annotations(code_files, project_root=FIXTURE)
    annotations = [
        CodeAnnotation(file_path=e.file_path, line=e.line, cited_ids=e.cited_ids)
        for e in entries
    ]
    spec_module_lookup = {
        "REQ-auth-001": "P1.SP1.M1", "REQ-auth-002": "P1.SP1.M1",
        "DES-auth-001": "P1.SP1.M1", "DES-auth-002": "P1.SP1.M1",
    }
    result = code_annotation_maps_to_module(annotations, decomp, spec_module_lookup)
    assert result.passed is True
```

- [ ] **Step 5: Run all assured tests**

Run:
```bash
python3 -m pytest tests/test_assured_*.py -v 2>&1 | tail -10
```

Expected: ~36-40 tests pass (6 ids + 8 validators + 13 decomposition + 3 code_index + 4 render + 6 export + 6 integration ≈ 46; adjust if subtests counted differently).

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/assured/ tests/test_assured_skill_integration.py
git commit -m "test(assured): end-to-end integration tests + fixture (Phase E task 39)"
```

---

## Task 40: Plugin packaging

**Files:**
- Modify: `release-mapping.yaml`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Add the assured entry to release-mapping**

Read `release-mapping.yaml`. Find the `sdlc-programme:` block. Below it, add:

```yaml
sdlc-assured:
  skills:
    - commission-assured
    - req-add
    - req-link
    - code-annotate
    - module-bound-check
    - kb-codeindex
    - change-impact-annotate
    - traceability-render
  scripts:
    - source: plugins/sdlc-assured/scripts/assured/__init__.py
      destination: plugins/sdlc-assured/scripts/assured/__init__.py
    - source: plugins/sdlc-assured/scripts/assured/ids.py
      destination: plugins/sdlc-assured/scripts/assured/ids.py
    - source: plugins/sdlc-assured/scripts/assured/traceability_validators.py
      destination: plugins/sdlc-assured/scripts/assured/traceability_validators.py
    - source: plugins/sdlc-assured/scripts/assured/decomposition.py
      destination: plugins/sdlc-assured/scripts/assured/decomposition.py
    - source: plugins/sdlc-assured/scripts/assured/code_index.py
      destination: plugins/sdlc-assured/scripts/assured/code_index.py
    - source: plugins/sdlc-assured/scripts/assured/render.py
      destination: plugins/sdlc-assured/scripts/assured/render.py
    - source: plugins/sdlc-assured/scripts/assured/export.py
      destination: plugins/sdlc-assured/scripts/assured/export.py
  files:
    bundle:
      - source: plugins/sdlc-assured/manifest.yaml
        destination: plugins/sdlc-assured/manifest.yaml
      - source: plugins/sdlc-assured/CONSTITUTION.md
        destination: plugins/sdlc-assured/CONSTITUTION.md
      - source: plugins/sdlc-assured/README.md
        destination: plugins/sdlc-assured/README.md
      - source: plugins/sdlc-assured/pyproject.toml
        destination: plugins/sdlc-assured/pyproject.toml
      - source: plugins/sdlc-assured/.claude-plugin/plugin.json
        destination: plugins/sdlc-assured/.claude-plugin/plugin.json
    templates:
      - source: plugins/sdlc-assured/templates/programs.yaml
        destination: plugins/sdlc-assured/templates/programs.yaml
      - source: plugins/sdlc-assured/templates/visibility-rules.md
        destination: plugins/sdlc-assured/templates/visibility-rules.md
      - source: plugins/sdlc-assured/templates/change-impact.md
        destination: plugins/sdlc-assured/templates/change-impact.md
      - source: plugins/sdlc-assured/templates/requirements-spec-assured.md
        destination: plugins/sdlc-assured/templates/requirements-spec-assured.md
      - source: plugins/sdlc-assured/templates/design-spec-assured.md
        destination: plugins/sdlc-assured/templates/design-spec-assured.md
      - source: plugins/sdlc-assured/templates/test-spec-assured.md
        destination: plugins/sdlc-assured/templates/test-spec-assured.md
```

- [ ] **Step 2: Add to marketplace.json**

Read `.claude-plugin/marketplace.json`. Find the `sdlc-programme` entry. Add after it:

```json
{
  "name": "sdlc-assured",
  "source": "./plugins/sdlc-assured",
  "description": "Regulated-industry SDLC bundle (Method 2): positional namespace IDs, bidirectional traceability, DDD decomposition, KB extension to code, standard-specific exports (DO-178C, IEC 62304, ISO 26262, FDA DHF)",
  "version": "0.1.0",
  "category": "sdlc-bundle"
}
```

- [ ] **Step 3: Run the packaging validator**

Run:
```bash
python3 tools/validation/check-plugin-packaging.py 2>&1 | tail -5
```

Expected: 14/14 plugins verified (was 13/13 before adding sdlc-assured).

- [ ] **Step 4: Run release-plugin to populate plugin dir**

Run:
```bash
python3 tools/release-plugin.py 2>&1 | tail -3
```

Expected: success message; no diff in `plugins/sdlc-assured/` (we authored everything in-place already).

- [ ] **Step 5: Commit**

```bash
git add release-mapping.yaml .claude-plugin/marketplace.json
git commit -m "chore(assured): plugin packaging — release-mapping + marketplace (Phase E task 40)"
```

---

## Task 41: Containerised architect review of Assured bundle

**Files:**
- Create: `research/sdlc-bundles/dogfood-workflows/assured-bundle-review.md`
- Create: `research/sdlc-bundles/dogfood-workflows/assured-bundle-review.yaml`
- Create: `research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md` (written by the review agent)

- [ ] **Step 1: Write the review command brief**

Write `research/sdlc-bundles/dogfood-workflows/assured-bundle-review.md`:

````markdown
# Assured Bundle Review

## Your Role

You are a senior solution architect reviewing the Assured bundle (`plugins/sdlc-assured/`) — the Method 2 regulated-industry substrate from EPIC #178 Phase E. This bundle layers on the Phase D Programme substrate. Phase F (real dogfood) layers on this; getting Assured right matters.

You operate in a fresh container with SDLC plugins installed. Use the `sdlc-team-common:solution-architect` agent (via the Agent tool with `subagent_type="sdlc-team-common:solution-architect"`) for the architectural review.

## What you're reviewing

Primary input: `plugins/sdlc-assured/` (the entire bundle).

Walk these files specifically:

- `plugins/sdlc-assured/manifest.yaml`
- `plugins/sdlc-assured/CONSTITUTION.md` — Articles 15-17
- `plugins/sdlc-assured/templates/{programs.yaml, visibility-rules.md, change-impact.md, requirements-spec-assured.md, design-spec-assured.md, test-spec-assured.md}`
- `plugins/sdlc-assured/scripts/assured/{ids.py, traceability_validators.py, decomposition.py, code_index.py, render.py, export.py}`
- `plugins/sdlc-assured/skills/*/SKILL.md` — 8 skills
- `plugins/sdlc-assured/README.md`

## Required context

- `docs/architecture/option-bundle-contract.md` — bundle contract (Phase C)
- `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` §4 — Method 2 design
- `research/sdlc-bundles/METHODS.md` §4 — Method 2 summary
- `tests/fixtures/assured/feature-sample/` — minimal feature fixture
- `tests/test_assured_*.py` — unit and integration tests
- The Phase D containerised review at `research/sdlc-bundles/dogfood-workflows/programme-bundle-review-output.md` for review-style precedent

## What to do

Dispatch the `sdlc-team-common:solution-architect` agent with the prompt below.

### Prompt to dispatch

```
You are conducting an INDEPENDENT critical review of the Assured bundle
at plugins/sdlc-assured/ — Phase E deliverable of EPIC #178.

Phase F (real dogfood on EPIC #142) layers on this substrate; getting
Assured right matters.

Required reading first:
- docs/architecture/option-bundle-contract.md (Phase C contract)
- docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md §4 (Method 2 design)
- research/sdlc-bundles/METHODS.md §4
- plugins/sdlc-assured/ (the bundle itself)
- tests/test_assured_*.py

You may walk plugins/sdlc-programme/, plugins/sdlc-knowledge-base/,
plugins/sdlc-core/ to compare conventions.

Answer these 6 questions, in order, each with a verdict (AGREE /
AGREE-WITH-CONCERNS / DISAGREE / NEEDS-REWORK):

1. **Constitution overlay soundness (Articles 15-17)**: do the new
   articles extend articles 1-14 cleanly? Are there gaps between what
   the constitution promises and what the validators actually
   enforce?

2. **ID system fitness**: does the positional namespace ID format
   (`P1.SP2.M3.REQ-007`) coexist cleanly with the flat form
   (`REQ-feature-NNN`)? Does `remap_ids` actually preserve traceability
   under decomposition refactoring? What edge cases worry you?

3. **Traceability validator coverage**: do the 4 mandatory + 1 optional
   validators catch the broken-reference cases regulated-industry
   teams care about? Specifically: forward link integrity (DES with
   no satisfies, TEST with no satisfies), backward coverage (REQ
   with no DES, DES with no TEST), idempotency, annotation format.

4. **Decomposition validator coverage**: do the 5 module-bound
   validators correctly model DDD bounded contexts + Bazel
   visibility-rule discipline? Specifically: anaemic-context
   detection (does the implementation actually catch scattered
   logic?), granularity match (warns vs blocks correctly?),
   visibility rule advisory vs strict.

5. **KB integration realism**: does the `SYNTHESISE-ACROSS-SPEC-TYPES`
   mode actually compose with the existing `synthesis-librarian`
   without breaking the existing modes? Does the `_code-index.md`
   shelf-shape match what the `research-librarian` queries?

6. **Bundle layout vs Phase C contract**: does the actual Assured
   bundle layout match what docs/architecture/option-bundle-contract.md
   specifies? Are reserved Phase E fields (decomposition_support,
   id_format, paths_split_supported, known_violations_field,
   anaemic_context_opt_out) used correctly?

Then provide a SUMMARY paragraph stating whether the Assured bundle is
good enough to ship as v0.1.0 AND whether Phase F (real dogfood) can
proceed without retrofit, or whether Phase E needs revision before
either.

End your review by writing the verbatim review (6 verdicts + summary) to:
research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md

Do NOT propose alternative bundles. Do NOT modify the bundle. Do NOT
dispatch other agents. Read-only review; output is a markdown file.
```

## Done criteria

- The agent has been dispatched
- The agent's verbatim response is written to `research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md`
- The agent returned 6 verdict labels (one per question) plus a summary paragraph
- The agent stated explicit go/no-go on whether the bundle ships as v0.1.0 AND whether Phase F can proceed
````

- [ ] **Step 2: Write the workflow YAML**

Write `research/sdlc-bundles/dogfood-workflows/assured-bundle-review.yaml`:

```yaml
name: assured-bundle-review
description: |
  Independent containerised architect review of the Assured bundle (Phase E
  deliverable). Phase F (real dogfood) layers on top of Method 2's
  traceability + decomposition substrate, so getting Assured right matters.

  Reuses the sdlc-worker:decomposition-review team image used in Phase B
  and Phase D.

provider: claude

nodes:
  - id: assured-review
    command: assured-bundle-review
    context: fresh
    effort: high
    image: sdlc-worker:decomposition-review
    timeout: 600000
```

- [ ] **Step 3: Run the workflow**

Run:
```bash
/sdlc-workflows:workflows-run assured-bundle-review
```

Expected: workflow completes; agent's review output written to `research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md`.

- [ ] **Step 4: Read the review output**

Read `research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md`. Note any AGREE-WITH-CONCERNS or DISAGREE / NEEDS-REWORK verdicts.

- [ ] **Step 5: Triage the findings**

Apply the same discipline as Phase D:
- **Constitutional contract violations** → fix inline before close (do not defer to v0.2.0)
- **Validator gaps that affect regulated-industry credibility** → fix inline
- **Stylistic / minor concerns** → document in the retrospective for v0.2.0
- **Architecture-level disagreements** → escalate to user; do not silently close

- [ ] **Step 6: Commit the review artefacts**

```bash
git add research/sdlc-bundles/dogfood-workflows/assured-bundle-review.md \
        research/sdlc-bundles/dogfood-workflows/assured-bundle-review.yaml \
        research/sdlc-bundles/dogfood-workflows/assured-bundle-review-output.md
git commit -m "review(assured): containerised architect review (Phase E task 41)"
```

If inline fixes were applied, follow-up commits land before Task 42.

---

## Task 42: Phase E closure — validation, retrospective, issue close

**Files:**
- Create: `retrospectives/104-phase-e-assured-bundle-substrate.md`

- [ ] **Step 1: Run full Phase E validation**

```bash
python3 -m pytest tests/test_assured_*.py -v 2>&1 | tail -5
python3 tools/validation/check-plugin-packaging.py 2>&1 | tail -3
python3 tools/validation/local-validation.py --quick 2>&1 | tail -5
```

Expected: assured tests pass; 14/14 plugins verified; quick validation PASSED.

- [ ] **Step 2: Run pre-push validation**

```bash
python3 tools/validation/local-validation.py --pre-push 2>&1 | tail -10
```

Expected: PASSED, or 9/10 with the documented pre-commit-binary env limitation.

- [ ] **Step 3: Write the Phase E retrospective**

Write `retrospectives/104-phase-e-assured-bundle-substrate.md`:

```markdown
# Retrospective: Phase E — Assured Bundle (Method 2 Substrate)

**Branch:** `feature/sdlc-programme-assured-bundles`
**Issue:** #104 (Phase E of EPIC #178)
**Status:** COMPLETE

---

## What we set out to do

Build the Assured bundle Method 2 substrate — `sdlc-assured` plugin v0.1.0 implementing positional namespace IDs, bidirectional traceability with 4 mandatory + 1 optional validators, DDD decomposition with 5 module-bound validators, KB extension to code via annotations, and standard-specific traceability exports (DO-178C, IEC 62304, ISO 26262, FDA DHF).

## What was built

(Filled in at phase end based on actual deliverables.)

- Plugin scaffold (manifest, plugin.json, README, CONSTITUTION.md articles 15-17)
- 6 templates (programs.yaml, visibility-rules.md, change-impact.md, 3 spec templates)
- 6 Python modules (ids, traceability_validators, decomposition, code_index, render, export)
- 8 skills (commission-assured, req-add, req-link, code-annotate, module-bound-check, kb-codeindex, change-impact-annotate, traceability-render)
- Synthesis librarian extension (SYNTHESISE-ACROSS-SPEC-TYPES mode)
- End-to-end fixture (programs.yaml + 3 spec artefacts + sample source code)
- ~30+ tests covering all validators and integration flows
- Containerised architect review

## Q1 resolved

Module-dependency-graph visualisation format: **markdown edge-list** in v0.1.0. ASCII DAG and HTML SVG remain explicit stretch goals.

## What worked well

(Filled in at phase end.)

## What was harder than expected

(Filled in at phase end.)

## Lessons learned

(Filled in at phase end — particularly around: positional ID coexistence with flat IDs; anaemic-context detection trade-offs; decomposition refactoring with ID preservation.)

## Containerised review verdict

(Filled in at phase end — what the architect said, which findings were fixed inline vs documented for v0.2.0.)

## Validation

(Filled in at phase end — pre-push status, plugin packaging count (14/14?), test totals.)

## References

- Parent EPIC: #178
- Issue: #104
- Phase D closure: `retrospectives/186-phase-d-programme-bundle-substrate.md`
- Method 2 design: `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` §4
- Bundle contract: `docs/architecture/option-bundle-contract.md`
- Implementation plan: `docs/superpowers/plans/2026-04-29-phase-e-assured-bundle-substrate.md`
```

Replace each `(Filled in at phase end)` placeholder with concrete content based on what was actually built.

- [ ] **Step 4: Commit retrospective + close issue**

```bash
git add retrospectives/104-phase-e-assured-bundle-substrate.md
git commit -m "$(cat <<'EOF'
docs: Phase E retrospective complete; Assured bundle substrate ready (Phase E task 42)

Closes #104 (Phase E of EPIC #178). Full Method 2 substrate shipped:
plugin scaffold, Assured constitution (Articles 15-17), 6 templates,
6 Python modules (ids, traceability_validators, decomposition,
code_index, render, export), 8 skills, KB integration via
SYNTHESISE-ACROSS-SPEC-TYPES, end-to-end fixture, plugin packaging
(14/14). Q1 resolved: module-dependency-graph as markdown edge-list.

Phase F (real dogfood on EPIC #142) can now build on this substrate.

Closes #104.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: Push branch**

```bash
git push 2>&1 | tail -3
```

Verify push succeeded. Branch now has Phases A + B + C + D + E. Phase F (dogfood) is next.

---

## Self-review

**Spec coverage check** — every section of `docs/superpowers/specs/2026-04-26-programme-assured-bundles-design.md` §4 mapped to a task:

| Spec section | Task |
|---|---|
| Identifier system (positional + flat) | Task 4 |
| ID registry (`library/_ids.md`) | Task 5 |
| ID uniqueness, cited IDs resolve, no orphans | Tasks 6-8 |
| Decomposition refactoring with ID remap | Task 9 |
| Spec-as-KB-finding | Task 22 |
| Forward link integrity | Task 16 |
| Backward coverage | Task 17 |
| Index regenerability (idempotency) | Task 18 |
| Annotation format integrity | Task 19 |
| Optional change-impact-gate | Task 20 |
| Decomposition declaration (programs.yaml) | Tasks 3, 10 |
| REQ has module assignment | Task 11 |
| CODE annotation maps to module | Task 12 |
| Visibility rule enforcement | Task 13 |
| Anaemic context detection | Task 14 |
| Granularity match | Task 15 |
| Organisational metadata (optional) | Task 3 (frontmatter slots) |
| KB extension to code (annotations + index) | Tasks 21, 22, 36 |
| Synthesis librarian extension | Task 23 |
| Render pipeline (module-scoped) | Task 24 |
| Module-dependency-graph (Q1) | Task 25 |
| traceability-export DO-178C RTM | Task 26 |
| traceability-export IEC 62304 matrix | Task 27 |
| traceability-export ISO 26262 ASIL matrix | Task 28 |
| traceability-export FDA DHF structure | Task 29 |
| traceability-export csv + markdown | Task 30 |
| Skills shipped (8 new) | Tasks 31-38 |
| Commissioning guidance | Task 31 |
| Plugin packaging | Task 40 |
| Containerised architect review | Task 41 |
| Phase E retrospective | Task 42 |
| Issue #104 closed | Task 42 |

All §4 sections covered.

**Placeholder scan**: no "TBD", "TODO", "implement later", "fill in details" in any task body. Every code block contains real content. Test functions have real bodies. The retrospective scaffold has explicit `(Filled in at phase end)` markers — these are placeholders BY DESIGN and are filled in during Task 42 Step 3. Commit messages use heredoc form.

**Type consistency check**:

- `ParsedId`, `IdRecord`, `ValidatorResult`, `DecompositionValidatorResult`, `Module`, `SubProgram`, `Program`, `Decomposition`, `VisibilityRule`, `ImportEdge`, `SpecArtefact`, `CodeAnnotation`, `CodeIndexEntry` — all defined once and referenced consistently across tasks.
- `IdParseError`, `DecompositionParseError` — exception types, defined in their respective modules.
- Function names: `parse_id`, `format_id`, `is_positional`, `build_id_registry`, `render_id_registry`, `remap_ids`, `parse_programs_yaml`, `default_decomposition`, `req_has_module_assignment`, `code_annotation_maps_to_module`, `visibility_rule_enforcement`, `anaemic_context_detection`, `granularity_match`, `id_uniqueness`, `cited_ids_resolve`, `orphan_ids`, `forward_link_integrity`, `backward_coverage`, `index_regenerability`, `annotation_format_integrity`, `change_impact_gate`, `parse_code_annotations`, `render_code_index`, `render_spec_findings`, `render_module_scope`, `render_module_dependency_graph`, `export_do178c_rtm`, `export_iec_62304_matrix`, `export_iso_26262_asil_matrix`, `export_fda_dhf_structure`, `export_csv`, `export_markdown` — each defined in exactly one task and consumed in subsequent tasks with the same signature.

**Open question resolution**: Q1 resolved as markdown edge-list in v0.1.0 (Task 25). Q2-Q6 either out-of-scope for v0.1.0 (per design spec §9) or absorbed by commissioning configuration (Task 31).

**Validator wiring**: manifest.yaml `pre_push` validator list (Task 1) names 13 validators — these correspond to the validators implemented in Tasks 6-20. The wiring is symbolic at this stage; runtime invocation is the responsibility of the existing pre-push validation pipeline (which discovers validators by manifest declaration).

---

## Execution

Use `superpowers:subagent-driven-development` to execute this plan task-by-task. Fresh subagent per task; spec-compliance review then code-quality review between tasks. Use a standard model for the mostly-mechanical TDD tasks (Tasks 4-30); use a more capable model for the skill SKILL.md drafting (Tasks 31-38) and the retrospective (Task 42 Step 3).
