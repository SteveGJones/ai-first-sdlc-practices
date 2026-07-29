# Retrospective: Council multi-stage agentic coding capstone — client/server poker

**Branch:** `feature/council-poker-capstone`
**Date:** 2026-07-28 (started)
**Duration:** In progress

---

## Summary

**Phase 1 (exemplar) complete, 2026-07-28.** Full Texas Hold'em client/
server built at `research/poker-capstone/exemplar/`: architecture + two
detailed design docs (server, client), a FastAPI+WebSocket server (hand
evaluation, turn state machine, side pots, showdown), a static HTML/JS
client, both containerized, and a live end-to-end run through the actual
`docker compose` stack (3 players, 3 hands, chip conservation held every
time, turn enforcement rejected an out-of-turn action live). 25/25 pytest
tests green. Phases 2 (stage-4 harness) and 3 (model-facing test modes)
not yet started — see `docs/feature-proposals/237-council-poker-capstone.md`
for the full design and phasing.

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

- **Writing the detailed design doc before the code caught the hard rules
  design decisions up front.** The short-all-in-raise rule (a short all-in
  raise doesn't reopen full action for players who already matched the
  previous bet, and doesn't raise `min_raise`) and the side-pot layering
  algorithm were both fully specified in `design-server.md` before any
  code existed, so implementation was a direct translation rather than
  discovering the rules mid-build.
- **TDD on hand evaluation in isolation paid off immediately.** All 9
  hand categories plus the wheel-straight (A-2-3-4-5) edge case were
  verified correct via golden-case unit tests before the game engine was
  built on top of it — any bug there would have silently corrupted every
  downstream showdown result.
- **A deterministic `FixedDeck` test double** made the game-engine tests
  (turn enforcement, betting rules, fold-out, side pots) fully scripted
  and reproducible, rather than relying on statistical confidence over
  many random hands.
- **The live Docker end-to-end run caught nothing new** — by the time
  `docker compose up` ran a real 3-hand game, the 25 pytest tests had
  already exercised the same code paths. That's the intended outcome (the
  test suite should be the thing that catches bugs, not manual E2E
  poking), and it's worth recording as a positive result, not just an
  absence of findings.

## What Could Improve

- **Three real bugs shipped in the first draft, all caught by tests
  before commit, not by careful reading:**
  1. `Player`'s default `status` was `SITTING_OUT`, so freshly-seated
     players in tests (and in the real API flow — `seat_player` also
     relies on this default) were silently excluded from every hand until
     the default was fixed to `ACTIVE`.
  2. A leftover reference to a renamed function (`_resolve_showdown`
     instead of `_finish_hand`) — a `NameError` at the exact moment a
     hand reached showdown, i.e. the one path every complete game must
     take.
  3. Draft-stage test code (`if False else`, a silly self-referential
     assert) that ran clean but tested nothing, caught only by rereading
     before running, not by the test framework itself.
  Root cause for all three: writing a large module in one pass rather
  than testing incrementally as each piece landed. Improvement: for the
  next phase (the stage-4 harness), test each function as it's written,
  not after the whole file is done.
- **Lint/format was run scoped this time** (only the new files), a
  direct application of the lesson from earlier this session (an
  unscoped `pre-commit run --all-files` had reformatted ~107 unrelated
  files). Worth calling out as the improvement actually landing, not just
  the mistake it fixed.

## Lessons Learned

1. **A detailed design doc is worth writing even when you're also the
   implementer** — the discipline of stating the short-all-in-raise rule
   and the side-pot algorithm in prose, precisely enough for someone else
   to implement identically, forced decisions that would otherwise have
   been made ad hoc mid-code and might have differed subtly from what a
   model implementing the same spec would (in)validly assume.
2. **Default values on shared dataclasses are load-bearing** — the
   `SITTING_OUT` default bug would have silently broken the real API too
   (`seat_player` creates a `Player()` with no explicit `status`), not
   just the tests. A default that's wrong for the common case is a bug
   that tests catch by accident, not by design; worth an explicit test
   for "does a freshly seated player get included in the next hand" as a
   named case, not just incidentally covered by every other test.
3. **`FixedDeck`-style deterministic test doubles are the right pattern
   for anything with real randomness in its critical path** — reused for
   both the heads-up and 3-handed side-pot scenarios, and will likely be
   reused again by the stage-4 harness's scripted scenarios.

## Changes Made

### Files Created
- `docs/feature-proposals/237-council-poker-capstone.md` — scope, design,
  phasing
- `retrospectives/237-council-poker-capstone.md` — this file
- `research/poker-capstone/README.md` — project overview, layout, status
- `research/poker-capstone/exemplar/docs/architecture.md` — Stage 1
- `research/poker-capstone/exemplar/docs/design-server.md` — Stage 2
  (server): data model, turn state machine, short-all-in-raise rule,
  side-pot algorithm, hand evaluation spec, API contract
- `research/poker-capstone/exemplar/docs/design-client.md` — Stage 2
  (client): views, state sync, action submission
- `research/poker-capstone/exemplar/server/app/models.py` — Card, Deck,
  Player, Pot, Table
- `research/poker-capstone/exemplar/server/app/hand_eval.py` — best-5-of-7
  hand evaluation, all 9 categories
- `research/poker-capstone/exemplar/server/app/game_engine.py` — turn
  state machine, betting rounds, side pots, showdown
- `research/poker-capstone/exemplar/server/app/main.py` — FastAPI REST +
  WebSocket API
- `research/poker-capstone/exemplar/server/tests/` — 25 pytest tests
  (`test_hand_eval.py`, `test_game_engine.py`, `test_api.py`)
- `research/poker-capstone/exemplar/server/{Dockerfile,requirements*.txt,
  .dockerignore}`
- `research/poker-capstone/exemplar/client/{index.html,style.css,app.js,
  Dockerfile}` — static, no-build-step web client
- `research/poker-capstone/exemplar/docker-compose.yml`

## Action Items

- [x] Phase 1: exemplar (architecture + detailed design + server + client +
      Docker packaging) — complete 2026-07-28
- [ ] Phase 2: stage-4 harness, proven against exemplar + a broken variant
- [ ] Phase 3: full-autonomy and spec-fidelity model-facing test modes
