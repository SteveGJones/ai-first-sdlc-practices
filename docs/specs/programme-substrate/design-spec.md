---
feature_id: programme-substrate
module: P1.SP1.M1
granularity: design
---

# Design Specification: Programme-substrate (Assured)

**Feature-id:** programme-substrate
**Module:** P1.SP1.M1
**Granularity:** design
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

Three design units constitute the programme-substrate: a line-wise spec-file parser, a matrix builder with two export renderers, and the Constitution document containing Articles 12-14.

---

## Design

### DES-programme-substrate-001

`parse_spec(path: Path, phase: str) -> ParsedSpec` implements a single-pass, line-wise parser over the raw text of a phase artefact. It extracts the `**Feature-id:**` field via a compiled regex, then iterates lines tracking fenced-code-block depth to avoid false-positive ID matches inside code samples. H3 headings matching the pattern `### TYPE-<feature-id>-NNN` are collected into `declared_ids`; `**satisfies:**` lines are scanned for cross-phase references collected into `references`. Any missing `**Feature-id:**` line, non-existent file path, or unrecognised phase name raises `SpecParseError(message)` where `message` includes the file path.

**satisfies:** REQ-programme-substrate-001

### DES-programme-substrate-002

`build_matrix(feature_dir, feature_id)` loads all three phase artefacts via `parse_spec`, then constructs a reverse-index from REQ-IDs to satisfying DES-IDs and TEST-IDs (including transitive TEST→DES→REQ paths). It returns a list of `TraceabilityRow` objects sorted by REQ-ID. `export_csv` and `export_markdown` call `build_matrix` and render the result: CSV uses a `REQ,DES,TEST` header with Cartesian-product row expansion (empty DES or TEST renders as empty string); markdown renders a `| REQ | DES | TEST |` table with the same expansion. Both renderers produce a trailing newline.

**satisfies:** REQ-programme-substrate-002

### DES-programme-substrate-003

Articles 12-14 are authored as H2 sections in `plugins/sdlc-programme/CONSTITUTION.md`, extending the universal constitution (Articles 1-11). Article 12 mandates the three-artefact phase-gate sequence and names the required files. Article 13 prescribes cross-phase reference integrity rules enforced by the gate validators. Article 14 prescribes mandatory phase-review records committed alongside design-spec and test-spec artefacts.

**satisfies:** REQ-programme-substrate-003

---

## Out of scope

- Caching or incremental re-parse — the parser re-reads files on every invocation; build tooling is responsible for call frequency.
- Parallel export formats — the Assured Phase E extension point is noted in the module docstring only.
