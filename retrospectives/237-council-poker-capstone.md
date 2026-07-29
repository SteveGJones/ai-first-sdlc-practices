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
tests green.

**Phase 2 (stage-4 harness) complete, 2026-07-29.** Builds/runs a
submitted implementation's own Docker artifacts (a new "packaging
contract" appended to `design-server.md`: a service named `server` on
container port 8000), drives 3 REST-only scenarios, and — since the
harness cannot force particular cards — cross-validates every payout
against an independent oracle (`harness/oracle.py`, zero dependency on
the exemplar's own code) rather than asserting one scripted outcome.
Proven in both directions per the acceptance criteria in the feature
proposal: 4 consecutive clean passes against the exemplar, and a
deliberately-broken variant (`broken-variants/wrong-pot-split`, one
injected bug: pot winner picked via `min()` instead of `max()`) correctly
fails only the two payout-related scenarios while `turn_enforcement`
(untouched by that bug) still passes.

Phase 3 (model-facing test modes) in progress — see "Decisions &
rationale" below for the agreed Sonnet-only first-verification plan.

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
- **First verification: Sonnet-only, subagent-orchestrated, full-autonomy
  mode — agreed 2026-07-29.** Before touching the harder cross-path
  fairness question (external CLIs vs. Claude-family subagents) or
  spec-fidelity mode, prove the whole 4-stage pipeline once, single model,
  against the just-proven harness. Design (operator-confirmed):
  - I (the orchestrating session) act as conductor across 4 sequential
    `Agent` tool calls (`model: "claude-sonnet-5"`, general-purpose type,
    task-only prompt — no persona, same fairness discipline as Path A/B),
    each stage writing its own output directly to files under a run
    directory rather than relaying large output through my own context.
  - Stage 1 (architecture) and Stage 2 (detailed design): same brief that
    seeded the exemplar, the subagent never shown the exemplar itself.
  - Stage 3 (implementation): **two parallel subagents** (server, client)
    from the same locked Stage 1+2 output — operator-chosen over one
    subagent doing both, to test whether the Stage 2 design doc is
    detailed enough for independently-implemented halves to integrate,
    closer to the real client/server integration risk.
  - Stage 4: not a subagent — the Phase 2 harness, unchanged, run against
    whatever the Stage 3 subagents produced.
  - **Backfill, explicit and logged, stages 1-2 only.** After each of
    stages 1-2, a deterministic checklist (the required-elements list
    already in `design-server.md`/`design-client.md`) checks whether the
    model's own output is sufficient to usefully drive the next stage. If
    not, the corresponding exemplar section is spliced in — but the
    model's own output is still kept and scored as produced, and every
    backfill event is logged (stage, what was missing, what was
    substituted) so the final report can separate "reached stage 4 on its
    own merits" from "reached stage 4 because the pipeline carried it."
  - **No backfill for stage 3 (implementation) — operator-confirmed hard
    rule.** If the Stage 3 output fails to build/run in Docker, that's a
    hard stage-4 failure, full stop. Backfilling code (not just design)
    would make the stage-4 result meaningless — implementation
    correctness is exactly what stage 4 measures.

## First verification run (Sonnet-only) — 2026-07-29

Ran the design agreed above end-to-end: `runs/sonnet-only-2026-07-29/`.

- **Stage 1 (architecture):** checklist score 1.0 (5/5), no backfill.
  Sonnet chose Node.js/TypeScript server + React client, WebSocket-primary
  live channel — a different, equally valid stack from the exemplar's
  Python/FastAPI/vanilla-JS. Independence from the exemplar preserved
  throughout (the subagent was told never to look for or read anything
  under a directory named "exemplar").
- **Stage 2 (detailed design):** server 0.857 (6/7), client 0.8 (4/5),
  both above the 0.6 sufficiency threshold — no backfill. Both misses were
  `*_contract_specified` items whose keyword patterns assume a REST/HTTP
  vocabulary ("API", "endpoint", "POST /"); Sonnet's genuinely
  well-specified WebSocket-message contract just doesn't use those words.
  Noted as a checklist-calibration gap worth revisiting, not a real design
  gap — the actual design quality (worked side-pot example, precise
  7-step turn-validation pipeline, explicit short-all-in-raise handling)
  was, if anything, more rigorous than the exemplar's own prose.
- **Stage 3 (implementation) — real infrastructure friction, not content
  problems.** Both parallel subagents (server, client) hit **transient API
  connection drops mid-task**, twice each, unrelated to task content —
  resumed each via `SendMessage` (one accidental duplicate-agent-instead-
  of-resume mistake corrected; no functional harm since the original had
  already terminated). Both eventually completed with substantial,
  verified work: the server subagent wrote its own throwaway WebSocket
  smoke test and confirmed a full heads-up hand end-to-end (correct
  payout, button rotation) before reporting done; the client ran its own
  build (`tsc -b && vite build`, 0 errors) before reporting done.
- **Stage 4 (harness) — two real, harness-side bugs found, both fixed:**
  1. **Build timeout too short for a legitimate heavier stack.** The
     300s default (calibrated implicitly against the exemplar's own fast
     Python build) timed out on TypeScript/React's `npm install`. Not a
     submission problem — a harness limitation. Fixed: default raised to
     900s, and `--build-timeout-s`/`--health-timeout-s` added as CLI
     overrides (`harness/__main__.py`, `harness/runner.py`).
  2. **The wire API was never actually protocol-agnostic.**
     `harness/scenarios.py` hardcodes the exemplar's own REST endpoint
     shapes. Sonnet's Stage 2 chose a WebSocket-message protocol instead
     — a legitimate design choice the brief never ruled out — and stage 4
     had no way to drive it (`POST /tables` → 404). **Root cause:** the
     "packaging contract" fixed *deployment* (service name, port) but not
     *the API surface the harness actually calls*, and that gap was
     invisible until an independently-designed (not exemplar-authored)
     implementation hit it. **Fix, operator-confirmed:** the wire API is
     now a fixed constraint everywhere, same status as the packaging
     contract — extracted into a new canonical
     `docs/HARNESS-CONTRACT.md` (endpoints + exact response JSON shape,
     since the oracle cross-validation reads specific fields like
     `total_committed`/`last_showdown`), referenced from both
     `exemplar/docs/design-server.md` (no more duplicated copy to drift)
     and a new `docs/BRIEF-TEMPLATE.md` for future full-autonomy runs.
     This run's own `brief.md` predates the fix and was annotated, not
     rewritten, to keep the historical record accurate. Sonnet's server
     subagent was asked to add a thin REST facade over its existing,
     already-verified engine to satisfy the now-fixed contract — noted
     explicitly as a retrofit this run's Stage 2 wasn't designed against
     from the start, not a clean measurement of "did the design
     anticipate this."
- **Third harness gap, smaller: `HARNESS-CONTRACT.md`'s own response
  shape was incomplete.** After the REST facade retrofit, the harness
  crashed with `KeyError: 'current_bet'` — the contract doc I wrote
  omitted a field `scenarios.py` actually reads (per-player `current_bet`,
  distinct from `total_committed`). Audited every field the harness
  reads against both the doc and the exemplar's own response shape to
  confirm this was the only omission; fixed the doc, Sonnet's server
  agent added the one missing field (already tracked internally, just not
  exposed) and re-verified directly.
- **Stage 4 final result: FAIL — a genuine implementation bug, not
  another harness gap.** With the harness itself now correctly wired,
  `turn_enforcement` passed but `basic_multihand` hung. Manually stepped
  through the REST calls by hand to diagnose (`GET`/`POST` against a live
  container, not guessing from the error message alone) and found: the
  server correctly deals, enforces turns, and evaluates the showdown
  (`last_showdown` populated with correct hand categories — seat 0's
  pocket-derived straight beats seat 1's two pair beats seat 2's one
  pair) — but never *completes* the hand. `hand_in_progress` stays `true`,
  the pot's chips are never paid into any stack (294 across seats + 6
  stranded in `pots` = 300, correct total but wrong distribution), and
  the engine loops back into accepting further betting actions instead
  of starting the next hand. Very likely a REST-facade integration
  regression, not a defect in the original WS-verified game logic (the
  server agent's own pre-retrofit WS smoke test completed a full hand to
  `HAND_COMPLETE` with correct payout) — but per the operator-confirmed
  rule, **no backfill for stage 3/4**: this is the honest, recorded
  result, not something to keep patching on the model's behalf. See
  `runs/sonnet-only-2026-07-29/` for the full artifact trail.
- **Harness improvement made in the process of diagnosing this:** the
  original timeout error (`"hand did not complete within 500 actions"`)
  carried zero diagnostic detail — finding the actual bug required
  manually replaying the REST calls by hand. Fixed: `_drive_hand` now (a)
  detects the specific "showdown evaluated but hand never completed"
  pattern immediately rather than spinning through the remaining
  iterations, and (b) includes the full final state in both error
  messages. A future run hitting the same class of bug won't need manual
  reproduction to find it.
- **Quality sweep on the exemplar/broken-variant found a real
  vulnerability in our own code — not the model's.**
  `check-technical-debt.py` had never been run against `research/` before
  (only `--syntax` had). It found: a genuine stored-XSS in the exemplar's
  client (`app.js` interpolated a player-supplied seat name, e.g.
  `POST /tables/{id}/players {"name": ...}`, directly into `innerHTML` —
  a malicious name would execute in every other player's browser; fixed
  with safe DOM construction via `textContent`), two `.innerHTML = ""`
  clears flagged as the same category (false positives, but trivially
  replaced with `.replaceChildren()` to remove the ambiguity), and a
  `# type: ignore[attr-defined]` in `main.py` from stashing a seat number
  as a dynamic attribute on a `WebSocket` object (refactored to a
  `dict[WebSocket, seat]` keyed by the socket itself, removing the need
  for the suppression entirely rather than just silencing the checker).
  One flagged "commented code" hit was a genuine false positive (an
  explanatory prose comment, not commented-out code) and left as-is.
  Sonnet's own Stage 3 output has three narrow, idiomatic
  `eslint-disable-next-line` comments (`no-console` on a startup log,
  `react-hooks/exhaustive-deps` on two deliberately-scoped effects) —
  **not fixed**, on the same no-backfill-on-implementation principle as
  the showdown bug: that's the model's own work being measured, not ours
  to polish. All fixes re-verified: exemplar 25/25 tests + harness
  clean pass, broken-variant still fails on exactly the same two
  scenarios as before.

**Why this counts as the first verification succeeding, not failing** —
the entire point of a first verification run is to pressure-test the
harness against a real, independently-produced implementation before
trusting it on anything else, and to prove the whole pipeline start to
finish. It found and fixed **three genuine harness bugs** an exemplar-only
test could never have surfaced (the exemplar can't reveal "the harness
assumes REST" when the exemplar IS the REST implementation), then — with
the harness now trustworthy — correctly identified a **real
implementation defect** and, per the project's own design principle,
reported it honestly rather than papering over it. That is exactly what
this system exists to do.

## Testing matrix — where we are, and the client-testing problem

Operator asked (2026-07-29) for a full capability matrix — what we
*should* aim to test vs. what the Sonnet run actually covered — and to
organize it into difficulty-ordered phases (P1..P11) so a model's run can
stop at its first failure instead of always paying for the full pipeline.
Key finding from that exercise: the Sonnet run jumped straight to the
hardest phase (P9, full-stack full-autonomy) — we don't actually know
whether it would have cleared the simpler phases first. P3/P4 (judged
design quality) turned out to need no new infrastructure at all — a
"judge" inside Claude Code is just another `Agent` call with a comparison
prompt, the same pattern `council-judge` already uses elsewhere in this
repo.

**P6/P8 (client verification) needed real design work first.** The
REST harness generalizes to any server because `HARNESS-CONTRACT.md`
fixes the wire shape. The client has no equivalent — arbitrary DOM,
arbitrary framework, arbitrary labels — so a fixed Playwright script
can't drive arbitrary markup the way `scenarios.py` drives arbitrary
REST implementations. Two options considered: (a) generate a bespoke
Playwright suite per submitted app, or (b) fix a `data-testid`/`data-*`
attribute contract, same principle as the wire API, leaving framework/
styling/layout free. Chose **(b)**, for the same reason the wire API got
fixed: a bespoke-per-app suite would make test-generation quality a
hidden confound inside every client-verification result, and wouldn't be
reusable or comparable across models. Bespoke test-authoring against an
unfamiliar app is still a genuinely interesting capability — noted as a
**separate future phase**, not the core client-verification mechanism.

**Built and proven, 2026-07-29:**
- `docs/CLIENT-TEST-CONTRACT.md` — a data-attribute state mirror (same
  shape as the REST JSON, via `data-*` attributes) plus a URL deep-link
  contract (`?table={id}&seat={n}`) so the driver never has to touch a
  submission's own lobby UI. Playwright reads attributes only, never
  rendered text or CSS selectors — the reason the contract can stay fixed
  while every submission's actual UI looks completely different.
- Exemplar client (`app.js`, `index.html`) retrofitted to the contract —
  same "fix the reference implementation first" discipline as
  `HARNESS-CONTRACT.md`.
- `harness/browser_scenarios.py` + `harness/client_verify.py` — a fixed
  Playwright driver, kept as a separate opt-in entry point from
  `python -m harness` since a client is optional and its absence must
  never fail the required (server-only) stage-4 result. Three scenarios:
  hole-card privacy (own cards visible, every other seat's hidden),
  turn-gated action controls (enabled only for the current actor, every
  other seat's page disabled), and **live cross-browser sync** (an
  action taken in one browser context must update every seat's mirror,
  not just the actor's own — the one check that exercises real-time
  propagation, not just correct initial render).
- Proven both directions, same discipline as the REST harness: two clean
  passes against the retrofitted exemplar (2 browser contexts, a real
  heads-up hand driven end-to-end through actual rendered pages), then a
  new fixture `broken-variants/leaky-hole-cards` (one injected client-side
  bug: `data-hidden` hardcoded to `"false"`) correctly fails only
  `hole_card_privacy` with exact per-seat/slot mismatch details, while
  `turn_gated_controls` and `action_propagates` — untouched by that bug —
  still pass.
- `runner.py` extended to discover the client's host-mapped port
  (`docker compose port client 80`), best-effort and non-fatal — absence
  is `None`, not a `HarnessError`, matching the client's optional status.
- Found one real gap while building this: the harness had never had its
  own `requirements.txt` — dependencies (`pytest`, `httpx`, now
  `playwright`) had only ever been installed ad hoc into the venv, never
  recorded. Fixed.

P6/P8 are now unblocked — a spec-fidelity or full-autonomy client build
can be verified the same way the server already is.

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
- **Two more real bugs, this time in the harness itself, both caught by
  actually running it against the (already-correct) exemplar rather than
  trusting the code by inspection:**
  1. `pre_hand_stacks` was captured from the `/start` response, which
     already reflects blinds posted — but `total_committed` (used in the
     same formula) also counts blinds, so every payout comparison
     double-counted them, producing small but consistent false-fail
     mismatches (off by exactly the blind amount) even against a fully
     correct server. Fixed by capturing pre-hand stacks via a `GET` made
     *before* calling `/start`, not derived from `/start`'s own response.
  2. The first `short_all_in_side_pot` scenario design didn't actually
     force a side pot: after the short stack's all-in, the other two
     players only ever called to match it, then checked every remaining
     street — so every seat's total contribution ended up equal and no
     side-pot layer ever formed. Fixed by having whichever of the two
     remaining players acts first each street make an additional forced
     bet, guaranteeing contributions diverge from the short stack's
     regardless of the random cards.
  Neither bug was in the thing being tested — both were in the test
  itself producing a false negative against known-good code. Same lesson
  as Phase 1's bugs, one level up: a harness needs the same "run it,
  don't just read it" discipline as the thing it's judging.

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
- `research/poker-capstone/harness/oracle.py` — independent hand-eval +
  pot-reconstruction oracle, zero dependency on the exemplar's code
- `research/poker-capstone/harness/runner.py` — docker-compose lifecycle
  (build/up/health-poll/teardown), discovers the host port dynamically via
  `docker compose port server 8000`
- `research/poker-capstone/harness/scenarios.py` — turn enforcement,
  5-hand chip-conservation run, forced short-all-in side pot; every
  payout cross-validated against the oracle
- `research/poker-capstone/harness/__main__.py` — CLI entry point
  (`python -m harness --impl-dir <path>`)
- `research/poker-capstone/harness/tests/test_oracle.py` — 10 golden
  cases for the oracle
- `research/poker-capstone/broken-variants/wrong-pot-split/` — deliberately-
  broken exemplar copy (one injected bug) proving the harness fails
  correctly, not just passes

### Files Modified
- `research/poker-capstone/exemplar/docs/design-server.md` — added the
  "Packaging contract" section (service named `server`, container port
  8000) and rewrote "What the stage-4 harness will check" to describe the
  oracle cross-validation approach, once that became the actual design

## Action Items

- [x] Phase 1: exemplar (architecture + detailed design + server + client +
      Docker packaging) — complete 2026-07-28
- [x] Phase 2: stage-4 harness, proven against exemplar + a broken variant
      — complete 2026-07-29
- [x] Phase 3, first verification (Sonnet-only, full-autonomy): run
      complete 2026-07-29 — result FAIL (genuine implementation bug: hand
      never completes past showdown), three harness bugs found and fixed
      along the way. See "First verification run" above.
- [x] P6/P8 prerequisite: client-testing mechanism designed
      (`docs/CLIENT-TEST-CONTRACT.md`, data-attribute mirror + URL
      deep-link) and built (`harness/browser_scenarios.py` +
      `client_verify.py`), proven both directions — complete 2026-07-29
- [ ] Full capability ladder (P1-P11, see "Testing matrix" above) not yet
      run for any model — only P9 (full-stack full-autonomy) has been
      exercised, and only with Sonnet
- [ ] P3/P4 judge step (an `Agent` call, no new infra needed) not yet
      wired into the pipeline
- [ ] P1/P2 (document/QA the exemplar) and P10 (post-hoc documentation
      drift check) not yet built
- [ ] Spec-fidelity mode (P5/P6/P7/P8) not yet run against the
      now-corrected harness — including whether a second full-autonomy
      run (Sonnet or another model) passes Stage 4 cleanly when nothing
      needs retrofitting after the fact
- [ ] Cross-model roster (P11) — folding results into a comparable
      report format across external CLIs + Claude family
