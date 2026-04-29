---
name: change-impact-annotate
description: Guide the team through writing a change-impact record for IEC 62304 / FDA / ISO 26262 ASIL C+ projects. Surfaces the affected REQ/DES/TEST/CODE artefacts and captures human-attested verification approach.
---

# Skill: change-impact-annotate

**Use this skill** before pushing a code change that touches a regulated-context project where `change_impact_gate` is enabled. Produces a `docs/change-impacts/CHG-NNN.md` record that satisfies the gate.

## Inputs

- The unstaged or just-staged code changes (read from `git diff`)

## Steps

1. **Inspect the diff.** Identify the touched files and (best-effort) the touched functions.

2. **Map files to module IDs** using `programs.yaml`.

3. **Map touched functions to cited artefact IDs** by parsing existing `# implements:` annotations.

4. **Compute the next CHG number.** Scan `docs/change-impacts/CHG-*.md`; new ID = max + 1.

5. **Generate a draft.** Use the `change-impact.md` template, pre-filled with:
    - Discovered REQs, DESs, TESTs, code locations, modules
    - Empty fields for: change summary, downstream effects, verification approach, approver

6. **Prompt the user** to fill in the empty fields. Surface verification approach as the highest-stakes field (this is the regulator's primary check).

7. **Save.** Write to `docs/change-impacts/CHG-<NNN>.md`.

8. **Re-run change_impact_gate** to verify the record covers all touched code files.

9. **Remind.** "Approval signature is required before merge — the framework records it; the human authorises it."

## Done criteria

- `CHG-<NNN>.md` written.
- All touched code files cited in the record.
- `change_impact_gate` passes.
