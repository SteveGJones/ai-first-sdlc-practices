---
name: req-add
description: Mint a new REQ ID in the Assured project's namespace, with module assignment, and append it to the requirements-spec.
---

# Skill: req-add

**Use this skill** when adding a new requirement to an existing requirements-spec under the Assured bundle. Computes the next sequential ID for the feature and module, prompts for the requirement text, and appends a properly-formatted `### REQ-...` section.

## Inputs

- `<feature-id>` (or `<module-id>` for positional projects): which spec to append to
- The requirement text (single declarative sentence)

## Steps

1. **Locate the requirements-spec.** Read `docs/specs/<feature-id>/requirements-spec.md`. If the project uses positional decomposition, read the spec for the matching module.

2. **Compute the next REQ number.** Scan existing `### REQ-...` headings. New ID is the max + 1, zero-padded to 3 digits.

3. **Prompt for the requirement text.** Ask: "Single declarative sentence describing the new requirement?"

4. **Append the section.**
    ```markdown
    ### REQ-<feature-id>-<NNN>

    <text>

    **Module:** <module-id>
    ```

5. **Confirm.** Show the diff to the user before saving.

6. **Save.** Write the file.

7. **Remind.** "Next steps: add a corresponding DES in design-spec.md (use `req-link`), then a TEST in test-spec.md."

## Done criteria

- New REQ section appended with correct ID, no renumbering of existing IDs.
- Module assignment present.
- File saved; no other changes.
