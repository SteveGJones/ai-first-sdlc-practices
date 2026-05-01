---
name: code-annotate
description: Generate boilerplate `# implements:` annotation for a function based on the artefact ID, inserting it as the first line of the function body.
---

<!-- implements: DES-assured-skills-003 -->

# Skill: code-annotate

**Use this skill** when adding implementation code that satisfies a REQ or DES. Generates the correct `# implements:` annotation, validates that the cited IDs exist in the registry, and inserts the annotation in a syntactically-correct place.

## Inputs

- `<artefact-id>` — the REQ or DES being implemented (e.g., `REQ-auth-001`, `DES-auth-001`, or `P1.SP2.M3.REQ-007`)
- File path and function name (from active editing context)

## Steps

1. **Verify the artefact exists.** Read `library/_ids.md`; confirm `<artefact-id>` is declared.

2. **Detect the language.** Python (`#`), JavaScript/TypeScript (`//`), Go (`//`), Rust (`//`). Default `#` if unknown.

3. **Determine the comment line.** Choose the comment syntax matching the file extension.

4. **Insert the annotation.** Place `<comment-prefix> implements: <artefact-id>` as the first line of the function body, immediately after the opening brace / `:` / `func ... {`.

5. **Confirm.** Show the diff to the user.

6. **Run annotation_format_integrity** on the file to verify the annotation parses correctly.

## Annotation placement rules

`<!-- implements: <DES-ID> -->` and `# implements: <DES-ID>` annotations ALWAYS go on the implementing artefact:

- A Python function body — first line of the body, comment form
- A SKILL.md file — immediately after frontmatter close `---`, HTML-comment form
- A governance document — YAML frontmatter `satisfies_by_existence: [...]` or `implements: [...]`

NEVER place annotations:

- Inside a design-spec.md DES element (the DES is what is satisfied, not what implements)
- Inside a requirements-spec.md REQ element
- Inside a test-spec.md TEST element

The spec layer expresses obligation; the implementing artefact carries evidence. Crossing the layers blurs the audit trail.

## Done criteria

- Annotation inserted in syntactically-correct location.
- annotation_format_integrity passes.
- One commit with the annotation; the implementing code is the user's responsibility.
