# Retrospective: Council multi-stage agentic coding capstone — client/server poker

**Branch:** `feature/council-poker-capstone`
**Date:** 2026-07-28 (started)
**Duration:** In progress

---

## Summary

In progress. Scope, design, and phasing agreed 2026-07-28 — see
`docs/feature-proposals/237-council-poker-capstone.md`. This entry will be
filled in as each phase lands.

## Decisions & rationale (recorded as made, not deferred to the end)

- **New, separate harness, not an extension of `assess.sh`.** The existing
  propose-and-score contract is deliberately safe/deterministic/no-live-shell;
  this capstone is the opposite (multi-stage, stateful, live execution) and
  stretching the existing contract to cover both would compromise what makes
  the existing one trustworthy.
- **Docker packaging is both a tested capability and the isolation
  mechanism.** Model-generated server code binds a port and accepts network
  input from the test harness — rather than the harness silently wrapping
  generated code in a container the model never reasoned about, the model's
  own Dockerfile/compose is what gets built and run. Tests containerization
  skill and provides isolation in one mechanism.
- **No container runtime existed on this machine** (checked Docker, Colima,
  Podman, OrbStack, Lima — none present) — a hard blocker discovered before
  any design work could proceed. **OrbStack** installed via
  `brew install --cask orbstack` and verified (`docker run hello-world`
  succeeded, daemon confirmed live via `docker ps`).
- **Stage-4 test surface is primarily the server API**, scripted directly
  (no browser needed) — matches where the graded logic (turn enforcement,
  pot math, hand judging) actually lives. Browser automation against the
  client UI is an explicit stretch goal, deferred.
- **Phased build, agreed with operator**: exemplar first (Phase 1), then the
  stage-4 harness proven against the exemplar including a deliberately-broken
  negative case (Phase 2), then the two model-facing test modes — full
  autonomy and spec-fidelity — last (Phase 3).
- **New branch/issue** (#237), separate from #235 — #235's four deliverables
  were already complete and its branch ready for a PR; this is a materially
  new, multi-day epic that shouldn't block or entangle with it. (#235's PR
  #236 has since merged, including an in-flight CodeQL fix for a
  partial-SSRF finding in `mlx-stop-proxy.py`.)
- **Research project, not a plugin — operator correction 2026-07-28.** The
  deliverable is the exemplar + stage-4 harness *as a reusable scoring
  process*, re-run against new models as they appear, not a shipped
  `sdlc-model-council` capability. Lives at `research/poker-capstone/`
  (`release-mapping.yaml` has no `sdlc-model-council` entry, confirming
  `plugins/` is reserved for shippable content) — reuses the council's
  adapter/`extdel.sh` machinery as a dependency, but isn't part of the
  plugin itself.
- **Two elicitation mechanisms for one model roster.** External CLIs
  (Gemini via `agy`, Codex, OpenCode) go through `extdel.sh`, same as the
  council today. The Claude family (Fable, Opus, Sonnet, Haiku) go through
  Claude Code's own **Agent tool** with per-stage `model` overrides — an
  in-session subagent invocation, not a spawned external process. Recorded
  as a fairness caveat up front (same discipline as #234's Path A/B
  lesson): a subagent invocation carries harness/system-prompt overhead a
  bare CLI prompt doesn't, so cross-path scores need the same caveat
  treatment Haiku's subagent numbers got in #235, not presentation as
  directly apples-to-apples.

## What Went Well

*(fill in as phases land)*

## What Could Improve

*(fill in as phases land)*

## Lessons Learned

*(fill in as phases land)*

## Changes Made

### Files Created
- `docs/feature-proposals/237-council-poker-capstone.md` — scope, design,
  phasing
- `retrospectives/237-council-poker-capstone.md` — this file

## Action Items

- [ ] Phase 1: exemplar (architecture + detailed design + server + client +
      Docker packaging)
- [ ] Phase 2: stage-4 harness, proven against exemplar + a broken variant
- [ ] Phase 3: full-autonomy and spec-fidelity model-facing test modes
