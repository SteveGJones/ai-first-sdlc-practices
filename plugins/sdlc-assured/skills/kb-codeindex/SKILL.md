---
name: kb-codeindex
description: Parse all `# implements:` annotations in source code and emit `library/_code-index.md` as a shelf-index. Also extracts cross-module import edges and writes `library/_dependency-edges.md`. Idempotent — re-running produces byte-identical output if no annotations or imports changed.
---

<!-- implements: DES-assured-skills-005 -->

# Skill: kb-codeindex

**Use this skill** to build or refresh the project's code index. The output is structurally a KB shelf-index, queryable by the `research-librarian` agent like the regular library files. Run after adding/changing `# implements:` annotations or modifying import structure.

## Inputs

- (no arguments — operates on the whole project)

## Steps

1. **Load the project root.** Detect from `.git/`.

2. **Walk source files.** Glob `**/*.{py,js,ts,go,rs,java}` excluding standard ignored paths (`.venv/`, `node_modules/`, `.git/`, etc.).

3. **Parse annotations.** Use `parse_code_annotations` to extract every `# implements:` line.

4. **Verify cited IDs.** For each citation, look it up in `library/_ids.md`. Report unresolved citations as warnings (not errors — `annotation_format_integrity` blocks at pre-push).

5. **Render the index.** Use `render_code_index` to produce shelf-index-shaped markdown.

6. **Write to `library/_code-index.md`.** If the file already exists, compare byte-for-byte; only write if different.

7. **Extract dependency edges.** For each language detected in the project paths, invoke the registered `DependencyExtractor` adapter:
   - Python paths → `PythonAstExtractor` (uses `ast.parse` for precise cross-module import resolution)
   - All other paths → `GenericRegexExtractor` (regex-based; configured per language via `make_swift_extractor()` or equivalent)

   Accumulate all returned `ImportEdge` objects across languages. Resolve each edge against the `Decomposition` module paths so edges carry qualified module IDs (e.g. `P1.SP1.M1 → P1.SP1.M2`). Edges that cannot be resolved to a known module are silently dropped (same policy as unresolved annotation citations).

8. **Write to `library/_dependency-edges.md`.** Use `render_dependency_edges(edges, library_handle=<library-handle>)` to produce the artefact. If the file already exists, compare byte-for-byte; only write if different. The file is consumed by `visibility_rule_enforcement` during decomposition validation.

9. **Report.** Print: number of annotations processed, number of unresolved citations, number of import edges extracted, whether either index file changed.

## Done criteria

- `library/_code-index.md` is up to date.
- `library/_dependency-edges.md` is up to date.
- Idempotent (re-running with no changes produces no diff on either file).
- Unresolved citations and unresolvable edges reported but not failed.
