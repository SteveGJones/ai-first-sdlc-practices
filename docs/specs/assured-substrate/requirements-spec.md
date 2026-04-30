---
feature_id: assured-substrate
module: P1.SP1.M2
granularity: requirement
---

# Requirements Specification: Assured-substrate

**Feature-id:** assured-substrate
**Module:** P1.SP1.M2
**Granularity:** requirement
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Motivation

The Assured SDLC option (Method 2) adds three substrate components on top of the Programme bundle: a commissioning skill that erects the artefact scaffold, the Constitution articles (15-17) that define identifier integrity, decomposition discipline, and KB-for-code completeness, and a configurable change-impact gate that guards spec mutations in regulated contexts. Without these three components a project commissioned to the Assured option cannot demonstrate traceability integrity or change-impact governance to an auditor.

## Requirements

### REQ-assured-substrate-001

The `commission-assured` skill SHALL scaffold `programs.yaml`, `library/`, `docs/specs/`, and `docs/change-impacts/` directories on first run, creating stub files where needed, and SHALL exit with a structured error if any target path already exists with conflicting content.

**Module:** P1.SP1.M2

### REQ-assured-substrate-002

The Assured Constitution articles 15-17 SHALL overlay articles 1-14 cleanly with no contradictions: article 15 (identifier and traceability integrity), article 16 (decomposition discipline), and article 17 (KB-for-code annotation completeness) SHALL each extend, not duplicate, the rules established by articles 1-14, and no rule in articles 15-17 SHALL directly contradict any rule in articles 1-14.

**Module:** P1.SP1.M2

### REQ-assured-substrate-003

The `change_impact_gate` validator SHALL be opt-in (default disabled) and SHALL be configurable via `.sdlc/team-config.json` using the key `assured.change_impact_gate` with permitted values `enabled` and `disabled`; the validator SHALL read the configuration on every invocation and apply the gate only when the value is `enabled`.

**Module:** P1.SP1.M2

## Out of scope

- The detailed per-article prose of Articles 15-17 — governance content is the domain of the Constitution document itself; this spec covers only the overlay/non-contradiction contract.
- The implementation of `change-impact-annotate` skill or downstream audit queries — covered by `assured-skills` and `assured-traceability-validators` feature directories.
- CI pipeline wiring for the change-impact gate — deferred to the CI/CD automation issue.

## Success criteria

- Running `commission-assured` on a clean project produces all four scaffold targets (`programs.yaml`, `library/`, `docs/specs/`, `docs/change-impacts/`) and commits them without error.
- Running `commission-assured` on a project where `programs.yaml` already exists with content raises a structured error rather than overwriting.
- `plugins/sdlc-assured/CONSTITUTION.md` contains `## Article 15`, `## Article 16`, and `## Article 17` headings, and no rule text in those articles directly negates a rule stated in articles 1-14.
- Loading `.sdlc/team-config.json` with `assured.change_impact_gate: disabled` causes the gate validator to skip execution; setting it to `enabled` causes the gate to run.
- The gate validator raises a typed `ConfigError` if `team-config.json` is absent or malformed rather than silently defaulting to enabled.
