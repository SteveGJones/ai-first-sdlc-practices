---
feature_id: assured-substrate
module: P1.SP1.M2
granularity: design
---

# Design Specification: Assured-substrate

**Feature-id:** assured-substrate
**Module:** P1.SP1.M2
**Granularity:** design
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

Three design units constitute the assured-substrate: the `commission-assured` skill scaffolding behaviour, the Assured Constitution document containing Articles 15-17, and the `change_impact_gate` configuration reader and gate guard function.

---

## Design

### DES-assured-substrate-001

`commission_assured_scaffold(project_root: Path) -> list[Path]` is called by the `commission-assured` skill at step 4 (Scaffold the artefacts). It creates the following four targets under `project_root` if they do not exist:

- `programs.yaml` — written from the stub template embedded in the skill; contains placeholder module entries `P1.SP1.M1` through `P1.SP1.M3` with `# TODO: fill in` comments.
- `library/` — created as an empty directory with a `.gitkeep` sentinel.
- `docs/specs/` — created as an empty directory with a `.gitkeep` sentinel.
- `docs/change-impacts/` — created as an empty directory with a `.gitkeep` sentinel (also writes `CHG-template.md` for regulated contexts per step 4 of the skill).

Before writing any file, the function checks whether the target already exists. If `programs.yaml` exists and has non-zero size, it raises `CommissionError("programs.yaml already exists with content — re-commissioning not supported")`. If any directory exists, the function proceeds without error (idempotent directory creation). The function returns the list of `Path` objects actually written.

**satisfies:** REQ-assured-substrate-001

### DES-assured-substrate-002

Articles 15-17 are authored as H2 sections in `plugins/sdlc-assured/CONSTITUTION.md`. The document opens with a preamble stating that it extends the universal constitution (Articles 1-11) and the Programme constitution (Articles 12-14), and that those articles apply unchanged. Each of Articles 15-17 introduces new obligations that operate on top of the article set beneath them:

- Article 15 (identifier and traceability integrity) extends the general ID discipline of articles 1-11 with Assured-specific ID format rules, registry source-of-truth requirements, and validator obligations. It does not restate universal rules.
- Article 16 (decomposition discipline) extends Article 15 by adding module-assignment and visibility-rule obligations specific to multi-module decompositions. It does not re-specify ID uniqueness (Article 15) or phase-gate sequence (Articles 12-14).
- Article 17 (KB-for-code annotation completeness) extends Article 16 by requiring inline code annotations for every non-trivial function implementing a REQ/DES. It does not re-specify what a valid ID looks like (Article 15) or how modules are declared (Article 16).

No article in 15-17 negates a rule in 1-14. Assured strengthens enforcement; it does not relax any universal or Programme obligation.

**satisfies:** REQ-assured-substrate-002

### DES-assured-substrate-003

`load_change_impact_gate_config(config_path: Path) -> ChangeImpactGateConfig` reads `.sdlc/team-config.json` and returns a typed `ChangeImpactGateConfig` dataclass with field `enabled: bool` (default `False`). The loader:

1. If `config_path` does not exist, raises `ConfigError("team-config.json not found at <path>")`.
2. If the JSON is malformed, raises `ConfigError("team-config.json is not valid JSON: <detail>")`.
3. Reads `config["assured"]["change_impact_gate"]`; if the key path is absent, defaults to `"disabled"`.
4. Maps `"enabled"` → `True`, `"disabled"` → `False`; any other value raises `ConfigError("change_impact_gate must be 'enabled' or 'disabled', got '<value>'")`.

`run_change_impact_gate(config: ChangeImpactGateConfig, diff: list[str]) -> GateResult` is the gate guard. If `config.enabled` is `False`, it returns `GateResult(skipped=True)` immediately without inspecting `diff`. If enabled, it checks each modified spec line for the presence of a `change-impact-annotate` annotation block; lines without one are collected into `GateResult(violations=[...])`. A non-empty `violations` list causes the pre-push hook to exit non-zero.

**satisfies:** REQ-assured-substrate-003

---

## Out of scope

- The `change-impact-annotate` skill itself (which produces the annotation blocks consumed by the gate) — covered in `assured-skills`.
- Bypass-approval workflow for the gate — flagged as a future extension point in the `ChangeImpactGateConfig` dataclass but not implemented in this design unit.
- Parallel or incremental scaffold operations — the scaffold runs once per project and is not performance-sensitive.
