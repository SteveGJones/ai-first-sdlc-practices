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

The Assured bundle MUST be able to extract every `# implements:` annotation from a supplied list of source files, capturing for each the relative file path, the line number, and the cited IDs in both flat (`KIND-feature-NNN`) and positional (`P1.SP1.M1.KIND-NNN`) forms — so that callers can build a complete code-index without implementing annotation parsing themselves. Non-existent files in the list MUST be silently skipped rather than raising an error.

**Module:** P1.SP1.M2
**Evidence-Status:** LINKED
**Justification:** `parse_code_annotations` in `plugins/sdlc-assured/scripts/assured/code_index.py:47-50` carries `# implements: DES-assured-code-index-001`. Annotation added in Task 36A; Phase G acceptance measurement confirms DES-mediated coverage.

### REQ-assured-code-index-002

The Assured bundle MUST produce code-index and spec-findings documents in the shelf-index Markdown format (standard four-field header comment block followed by numbered `## N. <title>` sections with `**Terms:**`, `**Facts:**`, and `**Links:**` fields) so that the `research-librarian` agent can query them without any modification to the agent or the librarian dispatch layer.

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
