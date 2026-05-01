---
feature_id: assured-id-system
module: P1.SP1.M2
granularity: design
---

# Design Specification: Assured-id-system

**Feature-id:** assured-id-system
**Module:** P1.SP1.M2
**Granularity:** design
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

Two design units implement the ID system: a parser/formatter/predicate trio handling namespace form discrimination, and a registry trio handling idempotent construction, markdown rendering, and path remapping.

---

## Design

### DES-assured-id-system-001

`parse_id(text: str) -> ParsedId` applies two compiled regular expressions in priority order: `_FLAT_RE` (`^(?P<kind>REQ|DES|TEST|CODE)-(?P<feature>[a-z0-9][a-z0-9-]*)-(?P<num>\d+)$`) first, then `_POSITIONAL_RE` (`^(?P<prog>P\d+)\.(?P<sub>SP\d+)\.(?P<mod>M\d+)\.(?P<kind>REQ|DES|TEST|CODE)-(?P<num>\d+)$`). On a flat match it returns a `ParsedId` with `program=None`, `sub_program=None`, `module=None`, and the `feature` and `number` fields populated. On a positional match it returns a `ParsedId` with `program`, `sub_program`, and `module` populated and `feature=None`. If neither regex matches, it raises `IdParseError`.

`format_id(parsed: ParsedId) -> str` delegates to `is_positional` to select the output template: positional IDs render as `{program}.{sub_program}.{module}.{kind}-{number:03d}`; flat IDs render as `{kind}-{feature}-{number:03d}`.

`is_positional(parsed: ParsedId) -> bool` returns `True` when `parsed.program is not None`, exploiting the invariant that flat IDs always have `program=None`.

**satisfies:** REQ-assured-id-system-001

### DES-assured-id-system-002

`build_id_registry(project_root: Path) -> List[IdRecord]` walks `docs/specs/**/*.md` in sorted order so that output ordering is deterministic across runs. For each file it applies a line-by-line state machine: a `_HEADING_RE` match opens a new current-ID slot (flushing the previous record if any); a `_SATISFIES_RE` match within an open slot extracts forward-link refs via `_REF_ID_RE`. Code blocks (delimited by ` ``` `) are skipped. The final pending record is flushed after the last line. Because file enumeration is sorted and all state is rebuilt from file contents, two calls on the same project root produce identical `List[IdRecord]` output (idempotent).

`render_id_registry(records: List[IdRecord]) -> str` formats the list as a markdown table with a generation comment header. It is a pure function of its input — the same `records` list always yields the same string.

`remap_ids(records: List[IdRecord], path_remapping: dict[str, str]) -> List[IdRecord]` iterates each record and tests its `source` field against each key in `path_remapping`; the first matching prefix is replaced by the corresponding new prefix. The `id`, `kind`, and `satisfies` fields of every record are copied without modification, preserving ID immutability across module-path changes.

**satisfies:** REQ-assured-id-system-002

---

## Out of scope

- Incremental or watched registry updates — the registry is rebuilt in full on each invocation; caching is the caller's responsibility.
- ID uniqueness enforcement — `build_id_registry` collects all IDs including duplicates; deduplication and uniqueness errors are raised by the traceability validators layer.
- Line-number tracking within source files — the registry records file-level source attribution only.
