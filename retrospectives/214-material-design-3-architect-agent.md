# Retrospective: material-design-3-architect Agent

**Branch:** `feature/material-design-3-agent`
**Date:** 2026-07-22
**Duration:** ~1 session (research fan-out + authoring + wiring)

---

## Summary

Added a Material Design 3-grounded UX specialist agent (`material-design-3-architect`) to
`sdlc-team-fullstack`, filling the gap where the deliberately design-system-agnostic
`ux-ui-architect` carried no M3-specific knowledge (M3 appeared once, in a build-vs-buy table).
The agent is grounded in a four-part, officially-sourced research reference persisted under
`research/material-design-3/`, and the setup flow was made M3-aware via a technology-registry entry.
Delivered successfully with all format validators and touched test suites passing.

## What Went Well

- **Scoped from a verified gap, not a guess**: confirmed by inspection that `ux-ui-architect`
  mentioned Material Design exactly once before proposing the new specialist.
- **Parallel deep research**: four agents fanned out across M3's knowledge domains concurrently
  (foundations/tokens, components/layout, motion/a11y/content, implementation/tooling), each
  grounded in official Google sources with a retained Sources list. ~4 minutes wall-clock instead
  of serial.
- **Research persisted, not discarded**: the four references were saved to `research/material-design-3/`
  with an index README, so every agent claim is traceable and the material can later feed a KB ingest.
- **New specialist, not a bloated generalist**: kept `ux-ui-architect` design-system-neutral and
  added bidirectional cross-references, preserving a clean scope split (strategy vs M3 fidelity).
- **Setup awareness done at the right layer**: the technology-registry entry (not the setup skill
  itself) is what makes setup surface the agent on detecting `@material/web` / color-utils usage.

## What Could Improve

- **Colour frontmatter value rejected on first pass**:
  - What happened: chose `color: teal`; `validate-agent-format.py` rejects anything outside
    {blue, green, purple, red, cyan, yellow, orange}.
  - Root cause: the allowed colour set is not documented in the agent file contract I mirrored from.
  - Improvement: check `validate-agent-format.py`'s allowed enums before authoring frontmatter.

- **Stale published-agent count in AGENT-INDEX header**:
  - What happened: the pre-existing manual header claimed "56 published"; the real count was 58
    before this change (59 after). Regenerating the catalog dropped the manual SDLC-bundle note.
  - Root cause: AGENT-INDEX.md mixes an auto-generated body with manually-maintained header notes;
    the two drift.
  - Improvement: verified the true count by counting files rather than trusting the prior number;
    re-added the manual note. Longer term, the count/notes should be generated, not hand-maintained.

- **No project `.venv` existed**:
  - What happened: validators failed with `ModuleNotFoundError: yaml` under system Python.
  - Root cause: fresh checkout, no venv; global-install is (correctly) blocked by policy.
  - Improvement: created `.venv` via `uv venv --seed` + `uv pip install -r requirements.txt`.

## Lessons Learned

1. **Persist research as a first-class artifact.** Saving the four M3 references under `research/`
   (with sources) turns a throwaway fan-out into a durable, auditable knowledge base the agent cites.
2. **Make tooling aware at the data layer, not the prose layer.** The setup skill recommends *plugins*;
   the technology-registry is the extension point that surfaces a specific *agent* on tech detection.
3. **Verify counts, don't propagate them.** The "56 published" figure was already stale; trusting it
   would have compounded the error.

## Changes Made

### Files Created
- `docs/feature-proposals/214-material-design-3-architect-agent.md` — feature proposal
- `retrospectives/214-material-design-3-architect-agent.md` — this retrospective
- `research/material-design-3/{README,01-foundations-tokens,02-components-layout,03-motion-accessibility-content,04-implementation-tooling-migration}.md` — cited M3 reference
- `agents/core/material-design-3-architect.md` — the new specialist agent (source)
- `plugins/sdlc-team-fullstack/agents/material-design-3-architect.md` — released copy
- `data/technology-registry/material-design-3.yaml` + `plugins/sdlc-core/data/technology-registry/material-design-3.yaml` — setup awareness

### Files Modified
- `agents/core/ux-ui-architect.md` (+ plugin copy) — cross-reference the M3 specialist
- `release-mapping.yaml` — register the new agent + registry entry
- `data/technology-registry/_index.yaml` (+ plugin copy) — M3 detection patterns + aliases
- `plugins/sdlc-team-fullstack/.claude-plugin/plugin.json` — version 1.0.0 → 1.1.0
- `AGENT-INDEX.md` + `AGENT-CATALOG.json` — regenerated (fullstack 10 → 11 agents)
- `CLAUDE.md`, `README.md`, `plugins/sdlc-team-fullstack/README.md` — agent-count / description updates

### Validation
- `validate-agent-format.py` — PASS; `validate-agent-official.py` — PASS (with the same
  `first_party_alternatives` info-warning `ux-ui-architect` carries)
- `check-technical-debt.py --threshold 0` — COMPLIANT
- `check-broken-references.py` — no broken refs in any new/modified M3 file
- `pytest` registry + `test_setup_smart_e2e.py` — 35 + 15 passed

## Action Items

- [ ] (Optional follow-up) Ingest `research/material-design-3/` into a project KB via `/sdlc-knowledge-base:kb-ingest` so any agent can query M3 (deferred per proposal Open Questions).
- [ ] (Housekeeping) Consider generating AGENT-INDEX header counts/notes instead of hand-maintaining them — Owner: framework author.
