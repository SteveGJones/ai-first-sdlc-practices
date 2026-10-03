---
feature_id: assured-traceability-validators
module: P1.SP1.M2
granularity: design
---

# Design Specification: Assured-traceability-validators

**Feature-id:** assured-traceability-validators
**Module:** P1.SP1.M2
**Granularity:** design
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

Five design units map to the five requirements. DES-001 covers the two blocking reference-integrity validators (`id_uniqueness`, `cited_ids_resolve`). DES-002 covers the two directional-coverage validators (`forward_link_integrity`, `backward_coverage`). DES-003 covers the idempotency check (`index_regenerability`). DES-004 covers the annotation scanner (`annotation_format_integrity`). DES-005 covers the non-blocking orphan detector (`orphan_ids`). The `change_impact_gate` function is annotated to DES-assured-substrate-003 (cross-feature reference).

All validators accept `List[IdRecord]` or a similar typed input and return `ValidatorResult(passed: bool, errors: List[str], warnings: List[str])`. None perform I/O beyond what is explicitly passed through their arguments.

---

## Design

### DES-assured-traceability-validators-001

The two blocking reference-integrity validators operate as follows:

`id_uniqueness(records: List[IdRecord]) -> ValidatorResult` builds a frequency counter over all `r.id` values. Any ID with count > 1 is a duplicate. For each duplicate, it constructs an error string listing all source paths where it appears. Returns `passed=False` with a non-empty errors list when duplicates exist; `passed=True` otherwise.

`cited_ids_resolve(records: List[IdRecord]) -> ValidatorResult` builds the declared set `{r.id for r in records}`. For each record `r` and each item `cited` in `r.satisfies`, if `cited` is not in the declared set it appends an error. Returns `passed=False` when any errors were collected; `passed=True` otherwise.

**satisfies:** REQ-assured-traceability-validators-001

### DES-assured-traceability-validators-002

The two directional-coverage validators operate as follows:

`forward_link_integrity(records: List[IdRecord]) -> ValidatorResult` checks forward direction: every DES must cite at least one REQ (non-empty `satisfies`), every TEST must cite at least one DES (non-empty `satisfies`). Additionally, all cited IDs in `satisfies` must exist in the declared set. Any missing link or unresolved citation is a blocking error.

`backward_coverage(records: List[IdRecord]) -> ValidatorResult` inverts the graph to build a `cited_by` map: `{r.id: [list of IDs whose satisfies contains r.id]}`. For every REQ record it checks that at least one entry in `cited_by[r.id]` is a DES-prefixed ID. For every DES record it checks that at least one entry in `cited_by[r.id]` is a TEST-prefixed ID. Missing coverage is a blocking error.

**satisfies:** REQ-assured-traceability-validators-002

### DES-assured-traceability-validators-003

`index_regenerability(index_path: Path, regenerate: Callable[[], str]) -> ValidatorResult` performs the following steps:

1. If `index_path` does not name an existing file, return `passed=False` with error `"index file does not exist: <path>"`.
2. Read the file content as UTF-8 text.
3. Call `regenerate()` to obtain the freshly produced content.
4. If the two strings are equal, return `passed=True`.
5. Otherwise return `passed=False` with error `"index <path> is not idempotent — committed content differs from regenerated output. Run kb-rebuild-indexes and commit."`.

The `regenerate` callable is provided by the caller (typically a thin wrapper around `render_id_registry`) so that `index_regenerability` has no coupling to the ID registry implementation.

**satisfies:** REQ-assured-traceability-validators-003

### DES-assured-traceability-validators-004

`annotation_format_integrity(code_files: List[Path], declared_ids: set[str]) -> ValidatorResult` scans each file that exists on disk for lines matching `_IMPLEMENTS_RE = re.compile(r"^\s*#\s*implements:\s*(?P<ids>.+)$", re.MULTILINE)`. For each matched line it extracts the token list from the `ids` capture group using `_ID_TOKEN_RE`. For each token:

- Call `parse_id(tok)`. If `IdParseError` is raised, append an error of the form `"<file>:<line>: malformed annotation token '<tok>'"` and continue to the next token (do not perform the declared-ID check for a malformed token).
- If the token parses cleanly but is not in `declared_ids`, append an error of the form `"<file>:<line>: annotation cites '<tok>' which is not declared"`.

Returns `passed=False` with a non-empty errors list if any errors were collected; `passed=True` otherwise. Files that do not exist on disk are skipped without error.

**satisfies:** REQ-assured-traceability-validators-004

### DES-assured-traceability-validators-005

`orphan_ids(records: List[IdRecord]) -> ValidatorResult` builds the cited set from all `r.satisfies` across all records. For each record `r`, if `r.id` is not in the cited set, it appends a warning (covers REQ, DES, TEST, and CODE kinds). Always returns `passed=True` regardless of warnings — orphan detection is advisory, not a blocker.

**satisfies:** REQ-assured-traceability-validators-005

---

## Out of scope

- Aggregation or de-duplication of validator results across multiple calls — the caller is responsible for combining `ValidatorResult` objects.
- HTML-comment form `<!-- implements: ... -->` annotation detection — this is a known gap documented as F-001 in `research/phase-f-dogfood-findings.md`; the scanner is Python-comment-only in this version.
- Configurable severity overrides — the block/warn distinction is fixed per validator; no configuration knob is provided in this design.
