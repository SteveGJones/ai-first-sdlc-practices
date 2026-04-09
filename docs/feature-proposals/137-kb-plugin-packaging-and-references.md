# Feature Proposal: Fix Empty sdlc-knowledge-base Plugin + Wrong Slash Command References + Structural Prevention

**Proposal Number:** 137
**Status:** In Progress
**Author:** Claude (AI Agent) and Steve Jones
**Created:** 2026-04-08
**Target Branch:** `fix/kb-plugin-packaging-and-references`
**Issue:** #137
**Type:** Critical bug fix + preventive infrastructure

---

## Executive Summary

Three related defects in one PR:

1. **`sdlc-knowledge-base` plugin directory is empty** (except for manifest and README). EPIC #105 shipped source files for 2 agents and 15 skills/templates but never ran `release-plugin` to populate `plugins/sdlc-knowledge-base/`. Users installing the plugin get a non-functional shell. Reported as #137 from a fresh machine.
2. **Wrong slash command references** throughout the knowledge base skills and documentation. I wrote `/sdlc-core:kb-*` everywhere when it should be `/sdlc-knowledge-base:kb-*` because the plugin is `sdlc-knowledge-base`, not `sdlc-core`. This affects user-facing files including the `[Knowledge Base]` CLAUDE.md template that gets installed into consumer projects.
3. **No structural check for plugin packaging drift.** Running the new validator against main revealed nine additional pre-existing drifts across `sdlc-core`, `sdlc-team-common`, `sdlc-team-ai`, `sdlc-team-fullstack`, and `sdlc-team-security` — source and plugin copies silently out of sync from earlier work. The fourth discovery-style fix pattern: the bug exists because nothing was checking.

This PR fixes all three: populates the plugin directory from source, corrects the slash command references, adds a validator script + CI workflow that prevents future recurrence, and resyncs the nine pre-existing drifts so CI goes green.

---

## Motivation

### Problem 1: sdlc-knowledge-base plugin shipped empty

EPIC #105 shipped 12 sub-features across ~12 commits. Each commit added source files (agents, skills, templates) to `release-mapping.yaml` under the `sdlc-knowledge-base:` block. But the workflow of adding to release-mapping does not automatically sync the files — `release-plugin` is a separate skill that reads the mapping and copies files into the plugin directories. That skill was never run during the EPIC.

Result: on `main`, `plugins/sdlc-knowledge-base/` contains only:
- `.claude-plugin/plugin.json` (from sub-feature 2 scaffolding)
- `README.md` (from sub-feature 2)

And that's it. No agents, no skills, no templates. `/plugin install sdlc-knowledge-base@ai-first-sdlc` produces a non-functional plugin. Steve's team discovered this on a fresh machine and raised #137.

### Problem 2: wrong slash command references

During EPIC #105 I wrote the knowledge base skill invocations as `/sdlc-core:kb-init`, `/sdlc-core:kb-query`, etc. throughout:

- The skill bodies themselves (in cross-references and "next steps" output)
- The `[Knowledge Base]` CLAUDE.md section template that gets installed into user projects
- The starter pack files (shelf-index, log.md)
- The plugin README
- CLAUDE.md's skills table

This is wrong. The `kb-*` skills live in `sdlc-knowledge-base`, not `sdlc-core`. The correct invocation is `/sdlc-knowledge-base:kb-init`. Users following the documentation would hit "skill not found" errors.

### Problem 3: no structural check for plugin packaging drift

The broader pattern: after #120, #122, #124, #129, and now #137, every discovery-related bug shared a shape — source file was correct, plugin copy was wrong or missing. Running a hand-rolled validator against main for the first time surfaced nine additional drifts across five other plugins that had been in the repo silently:

- `sdlc-core`: setup-team drift (my own wording fix from earlier today missed the plugin copy), critical-goal-reviewer (source had examples, plugin copy didn't)
- `sdlc-team-common`: solution-architect, deep-research-agent, repo-knowledge-distiller
- `sdlc-team-ai`: ai-team-transformer
- `sdlc-team-fullstack`: backend-architect
- `sdlc-team-security`: compliance-report-generator, enforcement-strategy-advisor

All invisible. No check, no diff, no warning. The constitution-sync check (#93) handles `CONSTITUTION.md` ↔ plugin copy drift; there is no equivalent for any other source file, despite release-mapping.yaml listing dozens.

---

## Proposed Solution

Four changes in one PR.

### Change 1: Populate `plugins/sdlc-knowledge-base/`

Copy every source file listed in `release-mapping.yaml`'s `sdlc-knowledge-base:` block into its expected plugin destination, following the rules from the `release-plugin` skill:

- `agents/knowledge-base/<file>.md` → `plugins/sdlc-knowledge-base/agents/<file>.md` (category flattened)
- `skills/kb-*/<rest>` → `plugins/sdlc-knowledge-base/skills/kb-*/<rest>` (structure preserved)

Total: 2 agents + 15 skill/template files copied.

### Change 2: Fix `/sdlc-core:kb-*` → `/sdlc-knowledge-base:kb-*` references

Batch replace across all active source files and their plugin copies:

- `agents/knowledge-base/agent-knowledge-updater.md`
- `skills/kb-*/` (all source skills)
- `plugins/sdlc-knowledge-base/**` (all plugin copies after Change 1)
- `CLAUDE.md`

Historical files (retrospectives, feature proposals, EPIC issue comments) are intentionally NOT rewritten. They captured the reference as believed at the time; rewriting would erase the history. The fix goes in the files consumers actually read, not in the institutional memory of the project.

### Change 3: Add `check-plugin-packaging.py` validator + CI workflow

New file: `tools/validation/check-plugin-packaging.py`

- Reads `release-mapping.yaml`
- For each plugin block, computes the expected plugin destination for each source file using the release-plugin mapping rules
- Verifies the source file exists
- Verifies the destination file exists and matches source byte-for-byte
- Reports every mismatch with a specific file path and remediation message
- Exit 0 on pass, exit 1 on any mismatch

New file: `.github/workflows/plugin-packaging-sync.yml`

- Runs on PR and push to `main`, `develop`, `feature/**`, `fix/**`, `docs/**`
- Triggers only when `release-mapping.yaml`, `agents/`, `skills/`, `plugins/`, the validator, or the workflow itself changes
- Calls the validator; fails the PR on any mismatch with the remediation message

Same pattern as `constitution-sync.yml` (#93) but generalised to all source-to-plugin sync, not just `CONSTITUTION.md`.

### Change 4: Resync the nine pre-existing drifts

Running the validator against main (before any of my changes) revealed drift in:

- `plugins/sdlc-core/skills/setup-team/SKILL.md` (my earlier wording fix, missed the plugin copy)
- `plugins/sdlc-core/agents/critical-goal-reviewer.md` (source has examples block, plugin copy doesn't)
- `plugins/sdlc-team-common/agents/solution-architect.md`
- `plugins/sdlc-team-common/agents/deep-research-agent.md`
- `plugins/sdlc-team-common/agents/repo-knowledge-distiller.md`
- `plugins/sdlc-team-ai/agents/ai-team-transformer.md`
- `plugins/sdlc-team-fullstack/agents/backend-architect.md`
- `plugins/sdlc-team-security/agents/compliance-report-generator.md`
- `plugins/sdlc-team-security/agents/enforcement-strategy-advisor.md`

Each is resynced by copying the source file over the plugin copy. These are all pre-existing drifts from earlier work in the repo, invisible because nothing was checking. Without these fixes, the new validator would fail on main and the CI workflow would be useless.

### Change 5: Update CONTRIBUTING.md and add memory file

`CONTRIBUTING.md` gains a new subsection under "Development Workflow" documenting the plugin packaging sync check, referencing #137, and listing the two options for keeping plugin copies in sync (run `release-plugin` or manually copy, then run the validator locally).

Memory file `feedback_release_plugin_sync.md` captures the lesson for future sessions: whenever `release-mapping.yaml` or a source file with a plugin copy changes, sync the plugin copy in the same commit. Referenced from `MEMORY.md`.

---

## Success Criteria

- [ ] `plugins/sdlc-knowledge-base/` contains all 2 agents + 15 skill/template files per release-mapping.yaml
- [ ] No active source file (non-historical) contains `/sdlc-core:kb-*` references
- [ ] The `[Knowledge Base]` template, starter pack files, and kb-init skill output all use `/sdlc-knowledge-base:kb-*`
- [ ] `tools/validation/check-plugin-packaging.py` exists, runs, and exits 0 against the updated tree
- [ ] `.github/workflows/plugin-packaging-sync.yml` exists and wires the validator into CI
- [ ] Nine pre-existing drifts resynced so the validator passes on the full repo
- [ ] `CONTRIBUTING.md` documents the check and its failure mode
- [ ] Memory file `feedback_release_plugin_sync.md` exists and is referenced from `MEMORY.md`
- [ ] CI passes on the PR including the new workflow
- [ ] Feature proposal + retrospective written

---

## User-path verification (per the #128 rule, pre-Article 12)

- **Surface touched**: `plugins/sdlc-knowledge-base/` (user-installable plugin contents), user-facing slash command references in multiple files, CI workflow that runs automatically
- **Fresh client used**: N/A with limitation — the empty-plugin bug requires `/plugin marketplace update ai-first-sdlc` + `/plugin install sdlc-knowledge-base@ai-first-sdlc` on a fresh client to verify the fix end-to-end, and I can't run that from inside this session
- **Commands run**:
  - `python3 tools/validation/check-plugin-packaging.py` — 11/11 plugins pass after the fixes
  - `find plugins/sdlc-knowledge-base -type f | sort` — 19 files present (was 2 before fix)
  - `grep -rln "sdlc-core:kb-" agents/ skills/ plugins/sdlc-knowledge-base/ CLAUDE.md` excluding historical files — zero matches after fix
  - `diff` on each resynced file to confirm source matches plugin copy
- **Output observed**: plugin directory populated with all expected files; slash command references corrected everywhere they matter for consumers; validator passes on the whole repo
- **Result**: pass with post-merge verification recommendation — Steve should run `/plugin marketplace update ai-first-sdlc` + `/plugin install sdlc-knowledge-base@ai-first-sdlc` on a fresh machine and confirm the plugin is actually functional (agents discoverable, skills invocable)

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Some of the nine resync'd files have drift that was intentional (not a bug) | Legitimate content gets overwritten by "wrong" version | Each drift was examined: the source file is always the authoritative version because that's where edits go first. Plugin copies are generated from source via release-plugin. The drift means source was updated but sync was skipped, never the other way round. Risk is minimal but non-zero. |
| The validator's mapping rules don't match release-plugin's actual behaviour for edge cases | False negatives or positives | Rules implemented by reading the release-plugin skill and verifying against the current passing state of all 11 plugins. Running the validator against main *before* the fixes surfaced exactly the files we expected plus the nine drifts — matching behaviour. |
| CI workflow fires on every PR including ones that don't touch plugin files | Noise | The `paths:` filter in the workflow limits firing to PRs that touch `release-mapping.yaml`, `agents/`, `skills/`, `plugins/`, the validator script, or the workflow itself. Zero impact on PRs that don't touch those paths. |
| The fix itself could introduce new drift if I copy the wrong version of a file | Bug in the fix | The validator is run after every copy step and at the end; any drift in my own fix would fail the validator and I'd have to resolve it before committing. |

---

## Out of scope

- Extending `local-validation.py --pre-push` to include the plugin packaging check. The CI workflow is sufficient for now; adding it to pre-push is a separate decision about contributor experience.
- A `release-plugin --verify` mode that runs the check without writing. The standalone validator already does this job.
- Rewriting historical references in retrospectives, feature proposals, and EPIC issue comments. They're captured-in-time records; rewriting them would erase how the bug was introduced and found.
- Fixing the underlying issue that `release-plugin` isn't run automatically when `release-mapping.yaml` changes. That's a separate design question (auto-sync vs. manual-sync-with-check). For now, manual with a structural check is the lowest-risk fix.

---

## Changes Made

| Action | File | Purpose |
|---|---|---|
| Create | 17 files under `plugins/sdlc-knowledge-base/` (2 agents + 15 skill/template files) | Populate the empty plugin directory from source per release-mapping |
| Modify | Multiple source + plugin files (see Change 2 above) | Replace `/sdlc-core:kb-*` with `/sdlc-knowledge-base:kb-*` |
| Create | `tools/validation/check-plugin-packaging.py` | Structural validator for source→plugin sync |
| Create | `.github/workflows/plugin-packaging-sync.yml` | CI enforcement of the validator |
| Modify | 9 files under `plugins/` (resync of pre-existing drifts) | Make the validator pass on main |
| Modify | `CONTRIBUTING.md` | Document the new check and failure mode |
| Create | Memory file `feedback_release_plugin_sync.md` (outside git) | Institutional memory of the lesson |
| Modify | `MEMORY.md` (outside git) | Reference the new memory file |
| Create | `docs/feature-proposals/137-kb-plugin-packaging-and-references.md` (this file) | Feature proposal |
| Create | `retrospectives/137-kb-plugin-packaging-and-references.md` | Retrospective |

---

## References

- Issue: #137
- Related: #128 review — the user-facing path verification rule this PR exercises again
- Related: #93 / constitution-sync.yml — the pattern this PR generalises
- Related: #120, #122, #124, #129 — the cumulative pattern of source/plugin drift that this validator now catches structurally
- Related: #132 (Constitution Article 12), #133 (test harness convention), #134 (path-glob CI check) — follow-ons from #128 that this PR complements
