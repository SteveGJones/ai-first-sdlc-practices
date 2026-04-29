---
name: kb-codeindex
description: Parse all `# implements:` annotations in source code and emit `library/_code-index.md` as a shelf-index. Idempotent — re-running produces byte-identical output if no annotations changed.
---

# Skill: kb-codeindex

**Use this skill** to build or refresh the project's code index. The output is structurally a KB shelf-index, queryable by the `research-librarian` agent like the regular library files. Run after adding/changing `# implements:` annotations.

## Inputs

- (no arguments — operates on the whole project)

## Steps

1. **Load the project root.** Detect from `.git/`.

2. **Walk source files.** Glob `**/*.{py,js,ts,go,rs,java}` excluding standard ignored paths (`.venv/`, `node_modules/`, `.git/`, etc.).

3. **Parse annotations.** Use `parse_code_annotations` to extract every `# implements:` line.

4. **Verify cited IDs.** For each citation, look it up in `library/_ids.md`. Report unresolved citations as warnings (not errors — `annotation_format_integrity` blocks at pre-push).

5. **Render the index.** Use `render_code_index` to produce shelf-index-shaped markdown.

6. **Write to `library/_code-index.md`.** If the file already exists, compare byte-for-byte; only write if different.

7. **Report.** Print: number of annotations processed, number of unresolved citations, whether the index file changed.

## Done criteria

- `library/_code-index.md` is up to date.
- Idempotent (re-running with no changes produces no diff).
- Unresolved citations reported but not failed.
