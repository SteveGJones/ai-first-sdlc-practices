---
feature_id: assured-traceability-validators
module: P1.SP1.M2
granularity: requirement
---

# Requirements Specification: Assured-traceability-validators

**Feature-id:** assured-traceability-validators
**Module:** P1.SP1.M2
**Granularity:** requirement
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Motivation

The Assured SDLC option requires a suite of validators that can detect structural integrity violations in the ID graph before they reach the phase-gate: duplicate declarations, broken citations, missing directional links, index drift, and malformed inline annotations. Eight public functions in `traceability_validators.py` collectively provide this coverage. Without them, an auditor cannot mechanically confirm that the artefact graph is consistent — the assurance case depends on tooling enforcing what the Constitution requires.

## Requirements

### REQ-assured-traceability-validators-001

The reference-integrity validators (`id_uniqueness`, `cited_ids_resolve`, `orphan_ids`) SHALL collectively detect: duplicate IDs across all records and report each duplicate as a blocking error; citations in any record's `satisfies` list that do not resolve to a declared ID and report each as a blocking error; and REQ or DES IDs that are declared but never cited by any other record and report each as a non-blocking warning (orphan detection SHALL NOT prevent a passing result).

**Module:** P1.SP1.M2

### REQ-assured-traceability-validators-002

The directional-coverage validators (`forward_link_integrity`, `backward_coverage`) SHALL collectively enforce that every DES record cites at least one REQ, every TEST record cites at least one DES, every REQ record is covered by at least one DES, and every DES record is covered by at least one TEST; all violations SHALL be reported as blocking errors.

**Module:** P1.SP1.M2

### REQ-assured-traceability-validators-003

`index_regenerability` SHALL report a blocking error when a committed ID-registry file on disk differs byte-for-byte from the output produced by the caller-supplied regeneration function; when the file is absent it SHALL report a blocking error; when the content matches it SHALL pass with no errors or warnings (idempotency check).

**Module:** P1.SP1.M2

### REQ-assured-traceability-validators-004

`annotation_format_integrity` SHALL scan source files for `# implements:` annotation lines and report a blocking error for each token that fails the ID format parse AND a separate blocking error for each well-formed token that cites an ID not present in the caller-supplied declared set.

**Module:** P1.SP1.M2

## Out of scope

- Persistence of validator results to disk — callers are responsible for writing reports; the validators return `ValidatorResult` objects only.
- Ordering or priority among validator errors — the caller chooses which validators to run and in what sequence; this module makes no scheduling decisions.
- Cross-repository or remote ID resolution — `cited_ids_resolve` and `annotation_format_integrity` operate only on the records and declared-ID set supplied by the caller.
- `change_impact_gate` — this function is part of this module but its requirement is covered by REQ-assured-substrate-003 (opt-in/disabled-by-default gate configuration).

## Success criteria

- `id_uniqueness` given two records with the same `id` returns `ValidatorResult(passed=False)` with an error mentioning both source paths.
- `cited_ids_resolve` given a record whose `satisfies` list contains an undeclared ID returns `passed=False` with a descriptive error; given a record whose `satisfies` list is empty or fully declared returns `passed=True`.
- `orphan_ids` given a REQ that is never cited returns `passed=True` with a non-empty `warnings` list containing the orphan ID.
- `forward_link_integrity` given a DES with an empty `satisfies` list returns `passed=False`; given a fully-linked graph returns `passed=True`.
- `backward_coverage` given a REQ with no DES citing it returns `passed=False`; given a fully-covered graph returns `passed=True`.
- `index_regenerability` given matching on-disk and regenerated content returns `passed=True`; given differing content returns `passed=False`.
- `annotation_format_integrity` given a file with a well-formed annotation token that is not in `declared_ids` returns `passed=False`; given a file with a malformed token returns `passed=False`; given a clean file returns `passed=True`.
