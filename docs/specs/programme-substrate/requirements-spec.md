---
feature_id: programme-substrate
module: P1.SP1.M1
granularity: requirement
---

# Requirements Specification: Programme-substrate (Assured)

**Feature-id:** programme-substrate
**Module:** P1.SP1.M1
**Granularity:** requirement
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Motivation

The Programme SDLC option enforces a formal waterfall phase-gate sequence. Three substrate components underpin this enforcement: a spec-file parser that deserialises phase artefacts, a traceability-matrix builder and exporter that makes the REQ→DES→TEST→CODE chain auditable, and the Constitution articles (12-14) that establish the governance rules the tooling enforces. Without these three components a Programme-commissioned project cannot demonstrate cross-phase coverage to an auditor.

## Requirements

### REQ-programme-substrate-001

The spec parser SHALL deserialise a phase spec file into a structured `ParsedSpec` object, raise a typed `SpecParseError` on any malformed input, and preserve the original file path for error reporting.

**Module:** P1.SP1.M1

### REQ-programme-substrate-002

The traceability matrix builder SHALL produce one row per REQ-ID covering its satisfaction chain through DES, TEST, and CODE artefacts, and the export functions SHALL emit the matrix in RFC-4180 CSV and CommonMark Markdown without data loss.

**Module:** P1.SP1.M1

### REQ-programme-substrate-003

The Constitution SHALL define Articles 12-14 prescribing the mandatory four-phase gate sequence, the spec-file naming convention, and the review-record format required by the Programme bundle.

**Module:** P1.SP1.M1

## Out of scope

- Format-specific export variants for regulated-industry standards (DO-178C RTM, IEC 62304 matrix, ISO 26262 ASIL matrix, FDA DHF) — deferred to the Assured bundle Phase E.
- CODE-level annotation scanning — handled by the code-gate validator, not the spec parser.
- Remote artefact storage or retrieval — all phase artefacts are local filesystem files.

## Success criteria

- A well-formed requirements-spec.md parses to a `ParsedSpec` with a non-empty `declared_ids` set and no raised exceptions.
- A malformed file (missing `**Feature-id:**` line) raises `SpecParseError` whose string representation includes the file path.
- `build_matrix` on a complete three-artefact feature directory returns rows whose REQ-IDs match the declared IDs in requirements-spec.md.
- `export_csv` produces a string with a `REQ,DES,TEST` header line followed by data rows; `export_markdown` produces a string with a markdown table header `| REQ | DES | TEST |`.
- CONSTITUTION.md contains H2 headings `## Article 12`, `## Article 13`, and `## Article 14` with the correct prescriptions for phase gates, naming, and review records.
