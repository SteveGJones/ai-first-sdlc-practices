---
feature_id: assured-id-system
module: P1.SP1.M2
granularity: requirement
---

# Requirements Specification: Assured-id-system

**Feature-id:** assured-id-system
**Module:** P1.SP1.M2
**Granularity:** requirement
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Motivation

The Assured SDLC option uses IDs in two distinct namespace forms: a flat form (`REQ-feature-NNN`) used in single-module contexts and a positional form (`P1.SP2.M3.REQ-007`) used when artefacts are decomposed across a programme hierarchy. Both forms must be round-trippable through a parse/format cycle, and the registry built from them must be regenerable byte-identically from project artefacts so that tooling can detect drift without storing intermediate state.

## Requirements

### REQ-assured-id-system-001

The ID parser SHALL parse both flat (`REQ-feature-NNN`) and positional (`P1.SP2.M3.REQ-007`) namespace forms from a single string, distinguishing them via an `is_positional` predicate, and SHALL raise a typed `IdParseError` for any string that matches neither form.

**Module:** P1.SP1.M2
**Evidence-Status:** LINKED
**Justification:** `parse_id`, `format_id`, and `is_positional` in `plugins/sdlc-assured/scripts/assured/ids.py` (lines 36, 61, 67) all carry `# implements: DES-assured-id-system-001`. Phase G acceptance measurement (`research/v020-acceptance-metrics.md`) confirms DES-mediated coverage post-Task-36A path-resolution fix.

### REQ-assured-id-system-002

The ID registry SHALL be regenerable byte-identically from project artefacts (idempotent): given the same set of spec files on disk, `build_id_registry` SHALL return the same ordered list of `IdRecord` values on every invocation. The registry SHALL also be remappable across module-path changes — `remap_ids` SHALL update source-file paths in existing records without altering the ID strings themselves.

**Module:** P1.SP1.M2
**Evidence-Status:** LINKED
**Justification:** `build_id_registry`, `render_id_registry`, and `remap_ids` in `plugins/sdlc-assured/scripts/assured/ids.py` (lines 90, 136, 159) all carry `# implements: DES-assured-id-system-002`. Phase G acceptance measurement confirms DES-mediated coverage post-Task-36A path-resolution fix.

## Out of scope

- Validation that IDs are globally unique across a project — that is the responsibility of `traceability_validators`, not the parser or registry.
- Persistence of the registry to disk — `render_id_registry` produces a markdown representation but file I/O is handled by the caller (e.g. `kb-rebuild-indexes`).
- Namespace collision detection between flat and positional IDs sharing a numbering sequence — out of scope for this module.

## Success criteria

- `parse_id("REQ-my-feature-001")` returns a `ParsedId` with `kind="REQ"`, `feature="my-feature"`, `number=1`, `program=None`, and `is_positional` returns `False`.
- `parse_id("P1.SP1.M2.REQ-007")` returns a `ParsedId` with `kind="REQ"`, `program="P1"`, `sub_program="SP1"`, `module="M2"`, `number=7`, and `is_positional` returns `True`.
- `parse_id("INVALID")` raises `IdParseError`.
- Calling `build_id_registry` twice on the same project root returns lists that compare equal element-by-element.
- `remap_ids(records, {"docs/specs/old/": "docs/specs/new/"})` returns new records where source paths are updated and `id` fields are unchanged.
