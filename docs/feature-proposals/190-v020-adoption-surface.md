# Feature Proposal #190 — v0.2.0 Adoption Surface

**Issue:** [#190](https://github.com/SteveGJones/ai-first-sdlc-practices/issues/190)
**Branch:** `feature/190-v020-adoption-surface`
**Target Branch:** `feature/190-v020-adoption-surface`
**Author:** Steve Jones (with Claude Opus 4.7)
**Date opened:** 2026-05-02
**Type:** Documentation + onboarding (no production code change)
**Depends on:** EPIC #178 (merged), EPIC #188 (merged)
**Carried-forward from:** Fresh-user audit conducted 2026-05-02 in-session (post-#188 merge)

---

## Motivation

See **Section 1: Problem statement** below — the motivation for this proposal is the gap between EPIC #188 having shipped audit-readiness in `main` and a fresh user being unable to discover, pick, or even reach v0.2.0 of `sdlc-assured` through the natural reading paths.

## Proposed Solution

See **Section 4: Scope (what this PR will change)** below — the proposed solution is a 6-tier file-by-file punch list of documentation, onboarding-skill, and version-metadata edits, totalling ~159 minutes of doc-only work with no production code change.

## Success Criteria

See **Section 6: Acceptance criteria** below — 13 explicit acceptance criteria covering version metadata, fresh-user discoverability, setup-team gating, audit-readiness narrative, and CI passes.

---

## 1. Problem statement

EPIC #178 (PR #187, 2026-05-01) shipped `sdlc-programme` v0.1.0 and `sdlc-assured` v0.1.0. EPIC #188 (PR #189, 2026-05-02) shipped `sdlc-assured` v0.2.0 audit-readiness. The capability is in `main` and the underlying commission infrastructure (`/sdlc-core:commission`) already supports four SDLC options (solo / single-team / programme / assured).

**However, the adoption surface — the docs and skills a fresh user actually lands on — still reflects the pre-#178 world.** A fresh-user audit on 2026-05-02 found three classes of failure:

1. **Discovery failure.** A user reading the natural discovery paths (`README.md` → `docs/HOWTO.md` → `docs/QUICK-REFERENCE.md` → `docs/PLUGIN-CONSUMER-GUIDE.md`) sees no mention of `sdlc-programme` or `sdlc-assured` and no SDLC-method-selection guidance. The plugin table at `README.md:73-87` lists 12 plugins; the two new bundles are absent.
2. **Onboarding failure.** `/sdlc-core:setup-team` (the recommended onboarding entry point) recommends team plugins but never asks the SDLC-method-selection questions that would route a user to `sdlc-programme` or `sdlc-assured`. A regulated-industry user installs `sdlc-team-security` and never discovers `sdlc-assured` exists.
3. **Version metadata failure.** `.claude-plugin/marketplace.json:21` and `plugins/sdlc-assured/.claude-plugin/plugin.json:3` both still declare `"0.1.0"` for `sdlc-assured`. A user running `/plugin install sdlc-assured@ai-first-sdlc` today gets v0.1.0 — the v0.2.0 audit-readiness features are not actually installed despite being in `main`.

This proposal closes that adoption surface gap. **No production code is touched.** This is purely the consumer-facing layer.

## 2. Why this matters now

- EPIC #188 was merged with the claim "`sdlc-assured` is now audit-ready at the tooling layer." That claim is currently unverifiable for any user installing through the marketplace — they get v0.1.0.
- The framework already had a four-option commission taxonomy (`/sdlc-core:commission` supports `solo / single-team / programme / assured`). Two of those four (`programme`, `assured`) are not surfaced anywhere a fresh user reads — so the framework's own commission infrastructure is unreachable.
- Two recently-shipped EPICs are silently invisible. If we don't close this surface, the next set of users we onboard will have the same "I didn't know that existed" reaction we got from the Amkor engagement (memory: `project_amkor_feedback_issues.md`).

## 3. Verification of capability (this is a docs/onboarding issue, not a build issue)

To rule out scope creep, I verified the underlying capability is complete:

- `plugins/sdlc-core/skills/commission/SKILL.md` — exists, walks the user through all four options (solo / single-team / programme / assured), records decision in `.sdlc/team-config.json`, supports `--option`, `--level`, `--bundle-dir` arguments.
- `plugins/sdlc-programme/skills/commission-programme/SKILL.md` — exists, delegates to `/sdlc-core:commission --option programme`.
- `plugins/sdlc-assured/skills/commission-assured/SKILL.md` — exists, delegates to `/sdlc-core:commission --option assured`.
- `plugins/sdlc-programme/skills/` lists 5 skills: `commission-programme`, `phase-init`, `phase-gate`, `phase-review`, `traceability-export`.
- `plugins/sdlc-assured/skills/` lists 8 skills: `commission-assured`, `req-add`, `req-link`, `code-annotate`, `module-bound-check`, `kb-codeindex`, `change-impact-annotate`, `traceability-render`.
- `release-mapping.yaml` covers all source files in both bundles (verified by `check-plugin-packaging.py` in CI).

**Conclusion: capability is shipped, only the adoption surface is missing.**

## 4. Scope (what this PR will change)

A categorised, file-by-file punch list. Effort estimates assume a single implementation session (~2 hours for tiers 1–3, +~1 hour 15 min for tiers 4–5).

### Tier 1 — Version metadata (CRITICAL — unblocks everything else)

| File | Change | Effort |
|------|--------|--------|
| `.claude-plugin/marketplace.json` (line 21) | `"version": "0.1.0"` → `"version": "0.2.0"` for `sdlc-assured`; expand description to mention v0.2.0 audit-ready highlights (typed evidence statuses, multi-format evidence model, platform-neutral dependency extractor, indirect DES-mediated coverage). | 2 min |
| `plugins/sdlc-assured/.claude-plugin/plugin.json` (line 3) | `"version": "0.1.0"` → `"version": "0.2.0"` | 1 min |
| `CHANGELOG.md` | Add `## [0.2.0] - 2026-05-02` section under the existing `## [Unreleased]` block, summarising EPIC #188 deliverables (typed evidence statuses, multi-format evidence model, platform-neutral dependency extractor, indirect DES-mediated coverage, REQ-quality linter candidate, 4 v0.3.0 carry-forward items). | 10 min |

**Tier 1 total: ~13 min.**

### Tier 2 — Fresh-user discovery (CRITICAL)

| File | Change | Effort |
|------|--------|--------|
| `README.md` | (a) Insert new "SDLC Method Selection" subsection above the "Available Plugins" table (line 73 area), with a four-row decision table (`solo` / `single-team` / `programme` / `assured`) and a one-paragraph framing of `/sdlc-core:commission`. (b) Add `sdlc-programme` and `sdlc-assured` rows to the plugin table at lines 76-87. (c) Add `docs/METHODS-GUIDE.md` to the Documentation index near line 212. | 12 min |
| `docs/HOWTO.md` | Add two new "Common Scenarios" subsections at the end: "Setting up Programme-of-Work (multi-team with phase gates)" and "Setting up Regulated-Industry Traceability (DO-178C / IEC 62304 / ISO 26262 / FDA)". Each shows the commission command and a short workflow snippet. | 12 min |
| `docs/QUICK-REFERENCE.md` | Add two new sections after the existing `sdlc-workflows` section: tables of skills for `sdlc-programme` (5 skills) and `sdlc-assured` (8 skills). | 5 min |
| `docs/PLUGIN-CONSUMER-GUIDE.md` | Insert "SDLC Method Selection (Optional)" subsection in the "Which plugins to install" area, with the four-option decision criteria and links to bundle READMEs and `METHODS-GUIDE.md`. | 10 min |
| `CLAUDE.md` | (No change required — already mentions both bundles at lines 125–126 with current v0.2.0 framing. Verify only.) | 0 min |

**Tier 2 total: ~39 min.**

### Tier 3 — Onboarding skill (CRITICAL)

| File | Change | Effort |
|------|--------|--------|
| `plugins/sdlc-core/skills/setup-team/SKILL.md` | Insert a new "SDLC method selection" step between the existing project-type detection step and the team-plugin recommendation step. Step asks the user a single 4-way choice (solo / single-team / programme / assured), records `sdlc_method` in `.sdlc/team-config.json`, and adds the appropriate bundle to the install recommendations (no install for solo or single-team since those are sdlc-core defaults). Renumber subsequent steps. | 20 min |
| `plugins/sdlc-core/skills/setup-team/SKILL.md` (post-check section) | Update the verification step to confirm the chosen bundle plugin (if programme or assured) is installed; if not, surface the install command in "Still pending". | 5 min |

**Tier 3 total: ~25 min.**

### Tier 4 — Bundle self-documentation (IMPORTANT)

| File | Change | Effort |
|------|--------|--------|
| `plugins/sdlc-programme/README.md` | Insert a "Getting Started" section after the existing "Constitution" section. Show install → commission → per-feature workflow (`phase-init` → fill spec → `phase-gate` → `phase-review` → next phase) → `traceability-export`. Cross-link to `docs/HOWTO.md`. | 8 min |
| `plugins/sdlc-assured/README.md` | (a) Insert a "Getting Started" section showing install → commission → declare modules in `programmes.yaml` → `req-add` → `req-link` → `code-annotate` → `kb-codeindex` → `module-bound-check` → `traceability-render`. (b) Insert a new "Audit-Ready at the Tooling Layer (v0.2.0)" section explaining (i) what's automated, (ii) what requires manual evidence, (iii) what an auditor can regenerate, (iv) what's deferred to v0.3.0 (corpus-policy formalisation, REQ-quality linter CI integration, GenericRegexExtractor refactor, 6 deferred F-010 drifters). Include a metrics table from EPIC #188 Phase G (594/594 tests pass; granularity-match noise 0%; RTM gap 4.55%; FAC FPR 0%). | 25 min |

**Tier 4 total: ~33 min.**

### Tier 5 — Decision doc + secondary surfaces (IMPORTANT)

| File | Change | Effort |
|------|--------|--------|
| `docs/METHODS-GUIDE.md` | **Create new file.** Comprehensive decision guide: overview of the four options (solo / single-team / programme / assured), decision tree, per-option detail (when to use, what you get, example workflow), comparison table, trade-offs, migration notes (single-team → programme, single-team → assured, programme → assured), further reading links. Target ~600-800 lines. | 45 min |
| `AGENT-INDEX.md` (line 96) | Reframe the "0 agents in v0.1.0" note to: "`sdlc-programme` v0.1.0 + `sdlc-assured` v0.2.0 are skill+validator bundles, not agent plugins — they provide structured SDLC delivery methodology rather than new specialist roles." Avoids the "not built yet" misread. | 2 min |
| `CLAUDE.md` (Context Loading section) | Add `docs/METHODS-GUIDE.md` to the context-loading hints list. | 2 min |

**Tier 5 total: ~49 min.**

### Tier 6 — Verification (no edit; CI confirms)

| Check | Expected outcome |
|-------|-----------------|
| `python tools/validation/check-plugin-packaging.py` | PASS — `release-mapping.yaml` already maps both bundles correctly (verified out-of-band 2026-05-02). |
| `python tools/validation/check-broken-references.py` | PASS — all new cross-links are within-repo and target files we author in this PR. |
| Manual: `/plugin install sdlc-assured@ai-first-sdlc` after PR merge | Resolves to v0.2.0 (post Tier 1.1 + 1.2 fix). |
| Manual: fresh user reads `README.md` and can answer "do I need a bundle?" | Yes (post Tier 2 + 5). |
| Manual: `/sdlc-core:setup-team` asks the four-option question | Yes (post Tier 3). |

**Tier 6 total: 0 min new edits.**

### Total effort

**~159 min (~2 h 40 min) of implementation, all docs and skill-prose edits.** No production code change. No test additions required (existing 594/594 pass; this PR adds zero code paths).

## 5. Out of scope

Explicitly **not** in this PR (keep scope tight):

1. **Any change to `tools/sdlc_assured/` or `plugins/sdlc-assured/scripts/`.** Pure consumer surface only.
2. **Any change to `sdlc-programme` semantics or skill behaviour.** It stays v0.1.0 functionally; only its discoverability changes.
3. **v0.3.0 carry-forward items** from EPIC #188 — formalising MANUAL_EVIDENCE_REQUIRED policy, wiring `check-req-quality.py --strict` into CI, refactoring GenericRegexExtractor/PythonAstExtractor coupling, addressing the 6 deferred F-010 drifters. These remain v0.3.0 work in a separate EPIC.
4. **Re-architecting the four-option taxonomy.** We document what already exists in `/sdlc-core:commission`. If the taxonomy itself needs revision, that's a separate proposal.
5. **Migrating existing single-team default behaviour.** We add programme/assured as discoverable options; we don't change what happens when a user does nothing.
6. **Adding a `/sdlc-core:methods-help` skill or new commands.** Documentation reach is sufficient; no new surface area to maintain.
7. **Renaming or deprecating any plugin.**

## 6. Acceptance criteria

The PR is ready to merge when **all** of the following are true:

1. **Marketplace ships v0.2.0**: `.claude-plugin/marketplace.json` and `plugins/sdlc-assured/.claude-plugin/plugin.json` both declare `"0.2.0"` for `sdlc-assured`.
2. **CHANGELOG documents v0.2.0**: A `[0.2.0] - 2026-05-02` section exists summarising EPIC #188 deliverables and v0.3.0 carry-forward.
3. **README has method selection**: A fresh user reading `README.md` only can identify which of the four options (solo / single-team / programme / assured) applies to their project.
4. **Plugin table is complete**: The `Available Plugins` table in `README.md` includes rows for `sdlc-programme` and `sdlc-assured`.
5. **setup-team gates on method**: `plugins/sdlc-core/skills/setup-team/SKILL.md` includes a step asking the four-option SDLC method question and recommends installing the appropriate bundle.
6. **METHODS-GUIDE exists and is linked**: `docs/METHODS-GUIDE.md` exists, contains the decision tree + four-option detail + comparison table + trade-offs, and is referenced from `README.md`, `docs/PLUGIN-CONSUMER-GUIDE.md`, and `CLAUDE.md`.
7. **Audit-readiness explained**: `plugins/sdlc-assured/README.md` includes an "Audit-Ready at the Tooling Layer (v0.2.0)" section covering automated / manual / regenerable / deferred-to-v0.3.0.
8. **Both bundle READMEs have Getting Started**: `plugins/sdlc-programme/README.md` and `plugins/sdlc-assured/README.md` both include a step-by-step "Getting Started" section showing the commission command and a per-feature workflow.
9. **HOWTO and QUICK-REFERENCE updated**: New common-scenario subsections in `docs/HOWTO.md`; new skill tables in `docs/QUICK-REFERENCE.md`.
10. **PLUGIN-CONSUMER-GUIDE updated**: New "SDLC Method Selection (Optional)" subsection.
11. **AGENT-INDEX reframed**: The "0 agents" note is reframed to "skill+validator bundles by design".
12. **CI passes**: `check-plugin-packaging.py`, `check-broken-references.py`, and the local pre-push pipeline (10 checks) all pass.
13. **Retrospective complete**: `retrospectives/190-v020-adoption-surface.md` is filled in (not just a skeleton) before opening the PR.

## 7. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Adding a new step to `setup-team` SKILL.md breaks the existing skill flow for users who install only team plugins. | Low | Medium | The new step adds an A/B/C/D question with a default that maps to current behaviour (`single-team` = no bundle install). All other steps proceed unchanged. We test by re-running the skill in this repo (dogfood) with each of the four answers. |
| The version bump in `marketplace.json` is read as a release event before the docs are merged. | Low | Low | Land all changes in a single PR; the bump is in the same commit as the docs. |
| `METHODS-GUIDE.md` overlaps with `CONSTITUTION.md` and confuses readers about which is canonical. | Medium | Low | `METHODS-GUIDE.md` is *user-facing* (when to pick which option); `CONSTITUTION.md` is *rule-defining* (what each option enforces). Cross-link both to make the relationship explicit; add a one-line note in the guide stating "for rules, see CONSTITUTION.md". |
| Audit-readiness section over-promises on what v0.2.0 actually delivers. | Medium | High | Section explicitly lists "what requires manual evidence" and "what's deferred to v0.3.0" with concrete examples (corpus-policy formalisation, REQ-quality linter CI integration). The four v0.3.0 carry-forward items from EPIC #188 architect review are listed verbatim. |
| Scope creep — readers ask "while you're touching this, also fix X". | High | Medium | Section 5 (Out of scope) explicitly enumerates what is not in this PR. Any "while you're at it" requests get filed as separate issues. |

## 8. Implementation plan

Single feature branch (`feature/190-v020-adoption-surface`), single PR, single retrospective. Suggested commit ordering:

1. **Commit 1 — Tier 1 (version metadata + CHANGELOG).** Smallest possible commit; unblocks the rest.
2. **Commit 2 — Tier 3 (setup-team SKILL.md).** Onboarding skill update; biggest single-file change in the SDLC core plugin.
3. **Commit 3 — Tier 2 (README + HOWTO + QUICK-REFERENCE + PLUGIN-CONSUMER-GUIDE).** All discovery-surface docs.
4. **Commit 4 — Tier 4 (bundle READMEs).** Self-documentation for each bundle.
5. **Commit 5 — Tier 5 (METHODS-GUIDE + AGENT-INDEX + CLAUDE.md context-loading hint).** Decision guide + secondary references.
6. **Commit 6 — Retrospective.** Filled-in `retrospectives/190-v020-adoption-surface.md` (skeleton was committed at branch creation).
7. **Commit 7 (only if needed) — fixes from `superpowers:code-reviewer` and `sdlc-team-docs:technical-writer` review.**

After commit 5, run dogfood pass:
- `/sdlc-core:setup-team` end-to-end with each of the four method answers
- Re-read `README.md` → `METHODS-GUIDE.md` → bundle READMEs cold and check coherence
- Run `python tools/validation/local-validation.py --pre-push`

Open PR after commit 6.

## 9. Review plan

Per [`feedback_external_review_before_merge.md`](../../memory/feedback_external_review_before_merge.md), this is a documentation-only PR so the bar for external review is lower than for audit-readiness PRs:

- **In-session review**: `superpowers:code-reviewer` on the doc diff (catch internal-link breakage, factual drift from skill behaviour).
- **In-session review**: `sdlc-team-docs:technical-writer` on the new `METHODS-GUIDE.md` and the audit-readiness section in `sdlc-assured/README.md` (the two newly-authored prose blocks).
- **No containerised architect review required** — no production code changes; no design decisions; no new contracts.
- **No Codex pre-merge review required** — no behaviour change; no risk of stale spec drift.

## 10. References

- Issue: [#190](https://github.com/SteveGJones/ai-first-sdlc-practices/issues/190)
- Audit conducted in-session 2026-05-02 (post-EPIC #188 merge); findings carried forward into Section 4 above.
- EPIC #188: [`retrospectives/188-v020-assured-improvements.md`](../../retrospectives/188-v020-assured-improvements.md)
- EPIC #178: [`retrospectives/178-programme-assured-bundles-epic.md`](../../retrospectives/178-programme-assured-bundles-epic.md)
- Commission infrastructure: `plugins/sdlc-core/skills/commission/SKILL.md` (already supports four options)
- Existing bundle entry points: `plugins/sdlc-programme/skills/commission-programme/SKILL.md`, `plugins/sdlc-assured/skills/commission-assured/SKILL.md`
- Memory: [`feedback_use_shipped_skills_and_agents.md`](../../memory/feedback_use_shipped_skills_and_agents.md) (this proposal dogfoods our own skills)
- Memory: [`project_amkor_feedback_issues.md`](../../memory/project_amkor_feedback_issues.md) (precedent for "users couldn't find what already shipped")

---

**Status: ready to implement.**
