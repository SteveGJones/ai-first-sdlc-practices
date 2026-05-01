---
feature_id: assured-code-index
module: P1.SP1.M2
granularity: design
---

# Design Specification: Assured-code-index

**Feature-id:** assured-code-index
**Module:** P1.SP1.M2
**Granularity:** design
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Overview

Two design units implement the assured-code-index requirements: the annotation extractor (`parse_code_annotations`) that produces `CodeIndexEntry` records from source files, and the pair of shelf-index renderers (`render_code_index` and `render_spec_findings`) that serialise those records — and raw `IdRecord` objects — into Markdown documents shaped for the `research-librarian` agent.

---

## Design

### DES-assured-code-index-001

<!-- implements: DES-assured-code-index-001 -->

`parse_code_annotations(files: List[Path], project_root: Path) -> List[CodeIndexEntry]` iterates over the supplied `files` list in order. For each path it:

1. Skips the file silently if `f.is_file()` returns `False` (handles missing paths without raising).
2. Reads the file content as UTF-8 text.
3. Relativises the path against `project_root` when the file is under the root; falls back to `f.name` when it is not.
4. Iterates over lines (1-indexed) and applies `_IMPLEMENTS_RE` to each line.
5. For every matching line, calls `_ID_TOKEN_RE.findall` on the captured `ids` group to extract all conforming ID tokens.
6. Appends a `CodeIndexEntry(file_path=rel_path, line=line_no, cited_ids=cited)` to the result list.

The function returns the accumulated entries in file-then-line order. `_IMPLEMENTS_RE` matches lines of the form `# implements: <ids>` with optional leading whitespace. `_ID_TOKEN_RE` matches tokens of the form `KIND-feature-NNN` (flat) or `P1.SP1.M1.KIND-NNN` (positional), where `KIND` is one of `REQ`, `DES`, `TEST`, or `CODE`.

**satisfies:** REQ-assured-code-index-001

### DES-assured-code-index-002

<!-- implements: DES-assured-code-index-002 -->

Both `render_code_index` and `render_spec_findings` produce shelf-index-shaped Markdown using the same four-field header pattern:

```
<!-- format_version: 1 -->
<!-- last_rebuilt: <timestamp> -->   # omitted when timestamp is None
<!-- library_handle: <handle> -->
<!-- library_description: <description> -->
```

**`render_code_index(entries, library_handle, timestamp=None) -> str`** emits one `## N. <file_path>:<line>` section per `CodeIndexEntry`. Each section contains:
- `**Terms:**` — comma-joined `entry.terms` (empty string when no terms are set).
- `**Facts:**` — bullet list from `entry.facts`, or bare `**Facts:**` when empty.
- `**Links:**` — comma-joined `entry.cited_ids`.

**`render_spec_findings(records, library_handle, timestamp=None) -> str`** emits one `## N. <record.id>` section per `IdRecord`. Each section contains:
- `**Terms:**` — `record.kind` plus the feature segment extracted by `_feature_from_id` (if present), joined by `, `.
- `**Facts:**` — single bullet `Declared in <record.source>`.
- `**Links:**` — comma-joined `record.satisfies` when present, otherwise `record.source`.

When `timestamp` is `None`, the `last_rebuilt` header line is omitted, ensuring repeated calls on identical inputs produce byte-identical output. Both functions join the assembled lines with `"\n"` and return the complete document as a single string.

**satisfies:** REQ-assured-code-index-002

---

## Out of scope

- Incremental or cached rendering — both functions rebuild the full document on every call; caching is the caller's responsibility.
- Writing output to the filesystem — callers (skills or the `kb-codeindex` command) handle file I/O.
- Validation of ID token conformance beyond regex matching — deep semantic validation is performed by the traceability validators, not by the renderers.
