---
feature_id: assured-substrate
module: P1.SP1.M2
granularity: test
---

# Test Specification: Assured-substrate

**Feature-id:** assured-substrate
**Module:** P1.SP1.M2
**Granularity:** test
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

One test per DES item. Tests are unit-level, exercising the public API in isolation using temporary directories and in-memory fixture data.

---

## Tests

### TEST-assured-substrate-001

**Title:** `commission_assured_scaffold` happy-path and re-commission guard

**Description:** Given a temporary empty directory `project_root`, call `commission_assured_scaffold(project_root)` and assert: (1) `programs.yaml` exists and contains the placeholder text `# TODO: fill in`; (2) `library/` exists as a directory; (3) `docs/specs/` exists as a directory; (4) `docs/change-impacts/` exists as a directory; (5) the returned list contains exactly the paths that were written. Separately, write a non-empty `programs.yaml` into `project_root` and assert that a second call to `commission_assured_scaffold(project_root)` raises `CommissionError` whose message contains `"already exists with content"`. Assert that calling again on a project where only the directories already exist (but `programs.yaml` is absent) does NOT raise an error (idempotent directory creation).

**satisfies:** REQ-assured-substrate-001 via DES-assured-substrate-001

---

### TEST-assured-substrate-002

**Title:** Constitution Articles 15-17 overlay verification

**Description:** Read `plugins/sdlc-assured/CONSTITUTION.md` and assert: (1) the text contains `## Article 15` with a phrase referencing identifiers or traceability; (2) the text contains `## Article 16` with a phrase referencing decomposition; (3) the text contains `## Article 17` with a phrase referencing annotations or KB-for-code. Additionally assert that the document contains a preamble phrase indicating it extends articles 1-14 (e.g., `extends` or `apply unchanged`). This test verifies the overlay contract at the structural level — it does not re-validate governance prose quality, which is the domain of phase-review.

**satisfies:** REQ-assured-substrate-002 via DES-assured-substrate-002

---

### TEST-assured-substrate-003

**Title:** `load_change_impact_gate_config` and `run_change_impact_gate` behaviour

**Description:** (a) Given a temporary `team-config.json` with `{"assured": {"change_impact_gate": "disabled"}}`, assert `load_change_impact_gate_config` returns a `ChangeImpactGateConfig` with `enabled == False`. (b) Given `{"assured": {"change_impact_gate": "enabled"}}`, assert `enabled == True`. (c) Given a `team-config.json` with no `assured` key, assert the loader returns `enabled == False` (default). (d) Given a missing `team-config.json` path, assert `load_change_impact_gate_config` raises `ConfigError` whose message contains `"not found"`. (e) Given a malformed JSON file, assert `ConfigError` is raised with `"not valid JSON"` in the message. (f) Given `{"assured": {"change_impact_gate": "strict"}}`, assert `ConfigError` is raised with `"must be 'enabled' or 'disabled'"` in the message. (g) Assert that `run_change_impact_gate(ChangeImpactGateConfig(enabled=False), diff=["any line"])` returns a `GateResult` with `skipped == True` without raising. (h) Assert that `run_change_impact_gate(ChangeImpactGateConfig(enabled=True), diff=[])` returns a `GateResult` with an empty `violations` list.

**satisfies:** REQ-assured-substrate-003 via DES-assured-substrate-003
