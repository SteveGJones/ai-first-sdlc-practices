---
feature_id: assured-code-index
module: P1.SP1.M2
granularity: requirement
---

# Requirements Specification: Assured-code-index

**Feature-id:** assured-code-index
**Module:** P1.SP1.M2
**Granularity:** requirement
**Status:** Draft
**Author:** Phase F dogfood
**Created:** 2026-04-28

---

## Motivation

The Assured SDLC option requires that every non-trivial function implementing a REQ or DES carries an inline `# implements:` annotation (Article 17). Without a tool to extract and surface these annotations the KB-for-code completeness rule cannot be verified automatically and the knowledge base cannot be queried for traceability evidence. `code_index.py` provides the two-direction bridge: parsing annotations from source files and rendering both the code index and the spec findings as shelf-index-shaped Markdown documents that the existing `research-librarian` agent can query without modification.

## Requirements

### REQ-assured-code-index-001

`parse_code_annotations` SHALL extract every `# implements:` annotation from the supplied list of source files, returning each as a `CodeIndexEntry` with the relative file path, the line number, and the list of cited IDs parsed from the annotation; files that do not exist SHALL be silently skipped; ID tokens SHALL conform to the pattern recognised by `_ID_TOKEN_RE` (flat `KIND-feature-NNN` or positional `P1.SP1.M1.KIND-NNN`).

**Module:** P1.SP1.M2

### REQ-assured-code-index-002

`render_code_index` and `render_spec_findings` SHALL each emit a shelf-index-shaped Markdown document — beginning with the standard four-field header comment block (`format_version`, optional `last_rebuilt`, `library_handle`, `library_description`) followed by numbered `## N. <title>` sections with `**Terms:**`, `**Facts:**`, and `**Links:**` fields — such that the document is directly queryable by the existing `research-librarian` agent without modification to the agent or the librarian dispatch layer.

**Module:** P1.SP1.M2

## Out of scope

- Automatic discovery of source files to annotate — callers supply the file list; directory traversal is the responsibility of the invoking skill or CLI.
- Writing the emitted Markdown to disk — rendering functions return strings; file I/O is the caller's responsibility.
- Validation that every function has an annotation — completeness checking is the domain of `assured-traceability-validators`, not this module.

## Success criteria

- `parse_code_annotations` called on a Python file containing two `# implements:` lines returns exactly two `CodeIndexEntry` objects with correct file path, line numbers, and cited IDs.
- `parse_code_annotations` called with a path to a non-existent file returns an empty list without raising.
- `render_code_index` output starts with `<!-- format_version: 1 -->` and contains a `## 1.` section for each entry with `**Links:**` populated from `cited_ids`.
- `render_spec_findings` output starts with `<!-- format_version: 1 -->` and contains a `## 1.` section for each `IdRecord` with `**Terms:**` populated from `kind` and feature segment.
- Both render functions produce byte-identical output on repeated calls with the same inputs when `timestamp=None`.
