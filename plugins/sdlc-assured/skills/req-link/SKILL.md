---
name: req-link
description: Add a satisfies link from a DES → REQ, TEST → REQ/DES, or CODE annotation → ID, validating that the target exists in the registry.
---

# Skill: req-link

**Use this skill** when adding a `satisfies:` link between artefacts, OR when adding an inline `# implements:` annotation in source code. This skill validates that the target ID exists before writing the link.

## Inputs

- `<source-id>` — the artefact gaining the link (e.g., `DES-auth-001`)
- `<target-ids>` — the ID(s) being satisfied (e.g., `REQ-auth-001`)

## Steps

1. **Read the registry.** Load `library/_ids.md`. Confirm every `<target-id>` exists.

2. **Locate the source artefact.** Find the file declaring `<source-id>`.

3. **Insert the link.**
    - For spec artefacts: insert `**satisfies:** <target-ids>` immediately after the `### <source-id>` heading.
    - For code annotations: prompt for the function name; insert `# implements: <target-ids>` as the first line of the function body.

4. **Re-validate.** Run `id_uniqueness`, `cited_ids_resolve`, `forward_link_integrity`. Report results.

5. **Commit the link** (separate commit so it can be reverted independently).

## Done criteria

- Link inserted; target IDs verified to exist in the registry.
- Validators pass after the link is added.
- One commit, scope-limited to the link.
