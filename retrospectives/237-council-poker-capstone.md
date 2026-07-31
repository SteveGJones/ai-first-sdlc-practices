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

## P1 built and run (2026-07-29): document the exemplar

Built `docs/P1-GROUND-TRUTH-FACTS.md` (15 specific, checkable claims
about the exemplar's actual behavior, extracted by re-reading the
current source — not copied from the design docs, which could
themselves have drifted) and `harness/doc_fidelity.py` (a deterministic
topic-coverage checklist, same style as `checklist.py`, plus a judge-
prompt builder for fact-accuracy grading).

**Ran it**: a Sonnet subagent given *only* the exemplar's four server
source files (no existing docs, explicitly instructed not to look for
any) wrote `runs/sonnet-p1-2026-07-29/exemplar-documentation.md`.
Checklist score: **1.0 (10/10 topics)**. A judge subagent then verified
it against the 15 ground-truth facts.

**Raw judge verdict: 13 correct, 1 incorrect, 1 omitted.** The
"incorrect" one (F1, turn-check ordering) turned out to be **a bug in
the ground-truth fact, not the documentation** — F1 claimed the turn
check happens before any other validation; the actual code checks
`hand_in_progress` first, then the turn. The candidate's documentation
correctly reported the real order and was penalized for it. Verified
against source, fact corrected in place (dated, cross-referenced), full
correction recorded in `runs/sonnet-p1-2026-07-29/judge_verdict_CORRECTED.md`
rather than silently edited. **Corrected tally: 14 correct, 0 incorrect,
1 omitted** — the one real gap (F6, the short-all-in-raise rule) is a
partial-credit omission (correctly stated one of three required parts),
not a wrong claim.

**Same pattern as every other grading mechanism built this session**:
the REST harness, the client contract, and now the doc-fidelity judge
each had a real bug in the *grading infrastructure itself*, found only
by running it against real output, not by careful writing. Worth stating
plainly: a ground-truth fact list isn't self-evidently correct just
because its author also wrote the code under test.

**What this tells us that P9 didn't**: Sonnet's comprehension/
documentation capability (P1) came back strong — 14/15 facts accurately
and specifically documented, including catching the genuinely subtle
short-all-in-raise nuance unprompted and correctly flagging a real,
previously-unnoted issue (`viewer_seat`/`seat` has no authentication —
any caller can view another seat's hole cards by declaring that seat
number). P9 (full-stack full-autonomy build) failed on a real
implementation bug. That's exactly the differentiated signal the
capability ladder was built to produce: this is not one number, and a
model's ceiling on one phase doesn't predict its result on another.

## P2 built and run (2026-07-29): QA the exemplar (blind mode)

Built `harness/qa_fidelity.py`: unlike P1's judge, this is fully
deterministic — run a model-authored pytest suite (unmodified) against
two real codebases and check it discriminates. Blind mode: the model is
never told a bug exists anywhere, just asked to write a thorough suite
"as if it were going into a regression suite" for code it's shown.

**Ran it**: Sonnet, given only the exemplar's three game-logic source
files, wrote 72 tests. Independently re-verified (not just trusting the
subagent's self-report) via `qa_fidelity.evaluate()`: **72/72 pass
against the real exemplar; 3 fail against `broken-variants/wrong-pot-
split`** — and all three are exactly the payout-focused tests
(`test_three_way_all_in_with_side_pots_pays_correct_winners`,
`test_split_pot_with_odd_chip_...`, `test_deeper_stack_reclaims_...`).
Three independently-constructed payout scenarios all correctly caught
the same min()-instead-of-max() bug — not one lucky assertion. Full
writeup: `runs/sonnet-p2-2026-07-29/RESULTS.md`.

**Sonnet caught two bugs in its own first draft** (a mislabeled
assertion, two deck-exhaustion crashes) by actually running the suite
against the real source rather than trusting hand-worked arithmetic —
the "run it, don't just trust it" pattern this project keeps
rediscovering, this time demonstrated unprompted by the model under
test itself, not just by us building the harness.

**A genuine bonus finding, unrelated to the planted bug**: Sonnet's
suite pins that `Table.non_folded_seats()` (`models.py`) counts
`SITTING_OUT` players as not-folded, which feeds
`_maybe_end_hand_early`'s remaining-player count. Traced and confirmed:
at a 3+-seat table with a busted (`SITTING_OUT`) seat present, a
2-player pot where one side folds would not correctly trigger
early-hand-end detection — the sitting-out ghost inflates the count
from 1 to 2. Not chased down or fixed here (scope discipline — this is
about proving P2 works, not fixing every bug it finds), recorded as a
follow-up action item.

**The `qa_fidelity` harness had a real bug too**, same pattern as
everything else: `_parse_summary`'s regex had every group optional and
unanchored, so `re.search` always matched an empty string at position 0
before ever reaching pytest's actual "N passed" numbers later in the
line — found by the harness's own sanity-check suite (a synthetic
scripted-hand test) before it was ever pointed at Sonnet's real output,
fixed, re-verified.

## P3-P10 built and run (2026-07-29): the full Sonnet baseline

Operator asked to complete the entire remaining capability ladder for
Sonnet specifically, to establish it as the "medium" reference point on
the rubric before testing other models (Opus expected to score higher,
others lower). P3/P4 needed no new infrastructure beyond a prompt
template (`harness/design_judge.py`) — same `Agent`-dispatch judge
pattern as P1/P2's judge steps, reusing Sonnet's existing P9 artifacts
(`stage1/architecture.md`, `stage2/design-server.md`,
`stage2/design-client.md`) as the candidate rather than generating new
material, since those documents already exist and re-scoring them at a
different capability tier is exactly what the ladder is for.

**P3 (architecture.md vs. exemplar's reference architecture)**: 2/2/1/2
(completeness/turn-enforcement/edge-case/consistency). Candidate
*exceeded* the reference on message-envelope precision (concrete JSON
shapes with idempotency tokens and sequence numbers), connection-identity
binding (closes a spoofing vector the reference doesn't address), and
turn-timeout/reconnection handling (both entirely absent from the
reference, which explicitly scopes them out). Lost points only on
edge-case awareness: no mention of short-all-in/side-pot mechanics or
heads-up-vs-multi-way turn differences, and silently expanded scope
(auth, persistence, reconnection) opposite the reference's explicit
test-harness-tractability tradeoff, without engaging that tradeoff.
Full verdict: `runs/p3-p4-judging/p3_architecture_verdict.json`.

**P4 (design-server.md / design-client.md vs. reference)**: server 2/2/2/2
(gap: no packaging/deployment section — no docker-compose/service-name/
port/healthz specified). Client: completeness 1/2, others 2/2 (gap:
omits the Lobby view entirely, no concrete tech stack committed;
superior: an actionSeq/handSeq gap-detection-and-resync protocol the
reference doesn't have). Full verdicts:
`runs/p3-p4-judging/p4_{server,client}_verdict.json`.

**P5 (spec-fidelity server build, own tech stack, no exemplar access)**:
built a Python/FastAPI server from `design-server.md` + `HARNESS-
CONTRACT.md` alone. Independently re-verified — not just the build
subagent's self-report — by running the same REST harness already
proven against the exemplar and both broken-variants
(`python -m harness --impl-dir runs/sonnet-p5-2026-07-29/impl`):
**all 3 scenarios pass** (`turn_enforcement`, `basic_multihand`,
`short_all_in_side_pot`). Result: `runs/sonnet-p5-2026-07-29/HARNESS-VERIFICATION.json`.

**P6 (spec-fidelity client build, own framework, no exemplar access)**:
built a vanilla-JS/nginx client from `design-client.md` +
`HARNESS-CONTRACT.md` + `CLIENT-TEST-CONTRACT.md` alone. Paired (by us,
not the build agent — P6 was deliberately not asked to write its own
docker-compose.yml) with the exemplar's own known-good server and run
through `harness/client_verify.py`: **all 3 browser scenarios pass**
(`hole_card_privacy`, `turn_gated_controls`, `action_propagates`).
Result: `runs/sonnet-p6-2026-07-29/HARNESS-VERIFICATION.json`.

**Two more real harness bugs found and fixed by P5/P6, same pattern as
every prior phase** (never fix a model's own output, only our own
infrastructure):
- `harness/scenarios.py` called `GET /tables/{id}/state` without a
  `seat` query param in four scenarios, relying on the exemplar's own
  undocumented choice to treat a missing `seat` as a fully-redacted
  spectator view. P5's server made `seat` required and correctly
  rejected the un-parameterized call with `422` — a reasonable reading
  the contract didn't rule out. Fixed by always passing `seat`
  explicitly (never by changing P5's server) and documenting the
  requirement in `HARNESS-CONTRACT.md`'s "Rollout note".
- `harness/browser_scenarios.py`'s `wait_for_selector` used Playwright's
  default `state="visible"`, but `CLIENT-TEST-CONTRACT.md` explicitly
  says "the visible page can look like anything" — nothing requires the
  state-mirror element to be CSS-visible, only DOM-present with correct
  attributes. P6's client made the mirror element genuinely invisible
  (`width:0; height:0; overflow:hidden`), a legitimate reading the
  exemplar's own implementation happened not to exercise. Fixed by
  waiting for `state="attached"` instead, documented in
  `CLIENT-TEST-CONTRACT.md`'s "Rollout note". Both fixes re-verified
  clean against the exemplar (regression) and the `leaky-hole-cards`
  negative control (still correctly fails `hole_card_privacy` only)
  before trusting them on P5/P6's real output.

**P7/P8, first attempt (cross-pairing P9's server/client with the
exemplar's opposite half)**: both failed, but **not informatively about
P9's design quality** — P9 was built before `HARNESS-CONTRACT.md`'s
`hole_cards`/`table_id`/etc. fields and before `CLIENT-TEST-CONTRACT.md`
existed at all, so P7 (P9 server + exemplar client) failed on a missing
`hole_cards` field and P8 (exemplar server + P9 client) timed out
immediately — P9's client carried no `data-testid` attributes
whatsoever. Recorded as a finding about the scoring process itself
(contract versioning matters for a benchmark meant to be re-run over
time) rather than about P9. Full writeup: `runs/p7-p8-crosspair/README.md`.

**P7-v2/P8-v2 — redone clean.** Operator asked to redo this properly
rather than leave it inconclusive. Rather than re-running the whole
ladder, only Stage 3 (implementation) was rebuilt from scratch — a fresh
server and fresh client, each a blind Agent dispatch from Sonnet's
*existing*, already-judged `stage1/architecture.md` +
`stage2/design-{server,client}.md`, built against the current, complete
contracts (`runs/sonnet-p9v2-2026-07-29/`). `docs/BRIEF-TEMPLATE.md` was
also updated to point future full-autonomy briefs at
`CLIENT-TEST-CONTRACT.md`, closing that gap for the next model run.

Independently verifying P9-v2's own server+client paired together
(before even reaching the cross-pairs) surfaced **a third real contract
gap**: every browser fetch was blocked by CORS. `HARNESS-CONTRACT.md`
never documented that the server must send CORS headers — the exemplar
has always silently depended on `CORSMiddleware(allow_origins=["*"])`
without it ever being written down. Fixed by adding a "Cross-origin
access (CORS)" section to the contract, then asking the same
server-build agent to add the now-documented requirement — same
precedent as the original P9 run's `current_bet` field: a contract-
clarity fix the model completes once told, not a backfill of its own
logic. Re-verified clean afterward (`curl -H "Origin: ..." ...` showing
the header present).

**All three passes then came back clean**: P9-v2 self-paired — REST
harness 3/3 scenarios (unlike the original P9, `basic_multihand` now
passes too — a different implementation of the same design didn't
reproduce the original's hand-completion bug) and browser harness 3/3;
**P7-v2** (P9-v2 server + exemplar client) 3/3 browser scenarios; **P8-v2**
(exemplar server + P9-v2 client) 3/3 browser scenarios. P9-v2's server
and client both correctly interoperate with an independently-built
reference in either direction — the actual signal P7/P8 was designed to
produce. Full writeup: `runs/p7-p8-crosspair-v2/README.md`.

**P10 (post-hoc documentation drift, newly designed this session — no
prior mechanism existed)**: a realistic "keep docs in sync after a code
change" task. Gave Sonnet one row of its own P1 documentation plus a
genuine unified diff changing a validation rule (`buy_in<=0` →
`buy_in < 20 * big_blind`), asked it to produce only the updated row.
**5/5 on a deterministic checklist**: removed the now-stale claim, stated
the new rule correctly, invented nothing beyond what the diff showed,
left untouched details untouched. Note: the diff is synthetic, applied
only for this test, not to the real exemplar (which still validates
`buy_in<=0`) — this would disturb every other phase that depends on the
exemplar's actual behavior. Full writeup: `runs/p10-doc-drift/RESULTS.md`.

**Sonnet baseline summary (P1-P10; P9 already recorded above; P11
cross-model roster deliberately deferred as the next phase)**:

| Phase | What | Result |
|---|---|---|
| P1 | Document the exemplar | 14/15 facts correct (1 corrected — our ground-truth error, not the model's) |
| P2 | QA/test-authoring (blind) | 72/72 pass vs. exemplar, 3/3 correctly catch the planted bug |
| P3 | Judged architecture quality | 2/2/1/2 — exceeds reference on protocol precision, loses on edge-case awareness |
| P4 | Judged detailed-design quality | server 2/2/2/2; client 1/2/2/2 |
| P5 | Spec-fidelity server build | 3/3 harness scenarios pass |
| P6 | Spec-fidelity client build | 3/3 browser scenarios pass |
| P7/P8 | Cross-pair with exemplar | clean pass (v2 redo: fresh Stage 3 build, all 3 pairings 3/3) |
| P9 | Full-autonomy full-stack build | FAIL — real hand-completion/payout bug, reproduced again this session |
| P10 | Post-hoc documentation drift | 5/5 — correctly updated only the invalidated claim |

## Haiku P5/P6, 2026-07-29 — the first genuine FAILs

Continued the fail-fast Haiku run into P5 (spec-fidelity server, built
solely from `exemplar/docs/design-server.md` + `HARNESS-CONTRACT.md`,
blind to the exemplar's code) and P6 (spec-fidelity client, same
principle). Both **FAIL**, independently verified — the build agents'
own self-reports both claimed success (P5's own report even contained a
visible self-correction mid-summary, "wait, let me recheck... actually
300, not 301," which should itself have been a signal), underscoring why
this project never trusts a self-report without running the harness.

**P5 (server) root cause, confirmed by manually stepping through REST
calls**: two related defects in exactly the highest-risk area (all-in
handling). (1) A player's `status` never transitions to `all_in` when
their stack reaches zero — stays `"active"`. (2) Turn-advancement
incorrectly selects an ALL_IN seat as `current_actor` instead of
skipping it, and then treats that seat's resulting no-op "call" as a
real action requiring another betting lap — so the betting round never
closes and `current_bet` is never reset for the next street. A normal
player computing `to_call = current_bet - my_current_bet` off the
server's own (stale) state then reasonably opens a fresh bet, which the
server rejects because its internal round state never actually advanced.
Full writeup: `runs/haiku-p5-2026-07-29/RESULTS.md`.

**P6 (client) root cause, confirmed by inspecting the live DOM**: a
self-inflicted regression, not a game-logic bug. `index.html`'s static
markup correctly includes every `data-testid="seat-N-hole-card-I"`
element the contract requires. `app.js` has two blocks touching the same
`.hole-cards` container on every render — the first correctly sets
`data-hidden`/`data-rank`/`data-suit` on the existing contract elements,
the second (titled "Render hole cards visually," running immediately
after) does `cardsContainer.innerHTML = ''` on the *same* container and
rebuilds it from scratch with plain, non-compliant `<div class="card">`
elements. The second block silently destroys the first's correct work on
every single render. The build agent's own compliance self-review had
explicitly checked off hole-card compliance as satisfied — it found the
correct code (block 1) without noticing block 2 immediately undoes it.
Every other contract element (table/seat mirrors, community cards, pots,
action controls) was genuinely correct. Full writeup:
`runs/haiku-p6-2026-07-29/RESULTS.md`.

**Reading**: both failures land in exactly the areas P2 and P4 already
flagged as Haiku's weak spots — all-in/round-completion mechanics (P5,
echoing P4 server's arithmetic error in the same area) and a
self-consistency slip between two pieces of code meant to do the same
job (P6, echoing P4 server's leftover "let me rethink" draft fragment).
Haiku's ladder profile is now reasonably clear: strong on high-level
comprehension and architecture (P1, P3 both clean), but progressively
less reliable the deeper into mechanical/detailed correctness the task
goes (P2's blind spot, P4's real defects, now P5/P6's real defects) —
exactly the kind of differentiated, per-phase signal this ladder was
built to produce instead of one aggregate pass/fail number.

## P11 begins: Haiku run (P1-P4), 2026-07-29

Operator asked to start the cross-model roster with Haiku (Claude Haiku
4.5), the "weaker" reference point the ladder was built to also measure,
not just assume. Ran fail-fast: P1, then P2 (both cheap, reusing all
existing grading infrastructure unmodified), checked in, then continued
into P3/P4 on request — which for Haiku required first generating its
own Stage 1/2 (architecture + design docs) from scratch, since unlike
Sonnet there was no pre-existing P9 run to reuse.

**P1**: 15/15 facts correct after grading (checklist coverage 1.0 too).
**P2**: 42 tests, all pass against the exemplar, but **0 catch the
planted bug** — every payout-adjacent test asserts only chip
conservation, never which seat wins or by how much, so the suite is
structurally blind to a "wrong winner" bug regardless of how many such
tests it has. A real, narrow capability gap versus Sonnet's suite (which
had specific winner-correctness assertions). Full writeup:
`runs/haiku-p2-2026-07-29/RESULTS.md`.

**P3** (architecture.md vs. exemplar reference), corrected: **2/2/2/2**.
**P4** (design docs vs. exemplar reference), corrected: server **2/2/2/1**,
client **2/2/1/1**. Real, verified defects in Haiku's server design: a
leftover "Hmm, this logic is confusing. Let me rethink." draft fragment
left inside a safety-critical function, and a worked side-pot example
whose own arithmetic is wrong ((200-100)*2 written as 100, not 200),
self-contradicting the document's own stated chip-conservation
invariant. Real gaps in the client design: no client-side max-bet-vs-
stack ceiling, no explicit big_blind-when-current_bet-zero floor, no
dealer-button visual convention, under-treated side-pot eligible_seats
and reconnect-resync semantics.

**Three real errors found in this project's own reference materials by
grading Haiku's output, none by re-reading our own material harder:**

1. `docs/P1-GROUND-TRUTH-FACTS.md` F15 was wrong (claimed the showdown
   hole-card reveal excludes folded seats; the real code — `Table.to_dict()`
   line 170 — has no folded-status check at all, and folding never
   clears `hole_cards`). Haiku's P1 documentation stated the broader,
   correct claim and was marked INCORRECT against the flawed fact.
   Corrected, and retroactively corrects Sonnet's own P1 tally down to
   13/15 (Sonnet's documentation made the same, also-wrong, "non-folded
   only" claim and was originally marked correct only because it matched
   the flawed fact). See `docs/P1-GROUND-TRUTH-FACTS.md` F15 and
   `runs/sonnet-p1-2026-07-29/judge_verdict_SECOND_CORRECTION.md`.
2. The raw P3 judge verdict claimed an internal contradiction in Haiku's
   architecture doc (unauthenticated hole-card privacy vs. its own
   "server is authoritative" principle) — false: Haiku's document
   explicitly scopes authentication out in its own "Out of Scope"
   section, identically to how the reference does. Judge simply missed
   it. Corrected `internal_consistency` back from 1 to 2.
3. `exemplar/docs/design-server.md`'s "Turn state machine" section
   claimed the actor check is "checked before any other validation" —
   stale; the real code checks `hand_in_progress` first (already
   established via P1-GROUND-TRUTH-FACTS.md F1's correction earlier this
   session, but never propagated back to this design doc). The P4 judge
   penalized Haiku's candidate for getting this "wrong" when it was
   actually right — its order matches real system behavior, the
   reference document didn't. Corrected in place, raised
   `turn_enforcement_soundness` from 1 to 2.

Worth stating plainly as a general lesson for the rest of P11: **a
disagreement between a model's output and one of this project's own
"ground truth" fact lists or reference documents is exactly as likely to
be our bug as the model's.** Running the same fixed grading apparatus
against a second, independently-produced model's output is itself a
second independent check on whether the apparatus is correct — not just
a second data point on the model. Every model run from here should keep
re-verifying surprising "incorrect" judge findings against real source
before accepting them, the same discipline already applied throughout
this project to harness/contract bugs.

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

## Local-model agentic wrapper, 2026-07-31 — and the end of the OpenCode question

Two threads closed this session, one infrastructural and one methodological.

**1. The `mlx_lm.server` OOM is fixed, and OpenCode (Path A) is now
definitively rejected.** The 2026-07-30 crash was diagnosed as an unbounded
prompt cache accumulating a KV sequence per session ("9 sequences, 9.72 GB")
until the GPU ran out. Rather than re-run all 18 audition pairs, only the one
item that had hung was re-run against a bounded server: it completed in **71s,
rc=0**, cache steady at "1 sequences, 0.10 GB". Two corrections to the notes
written before the reboot: `--prompt-cache-size` is the lever that actually
matters (sequence count was the direct cause, not total bytes), and
**`--max-concurrent` does not exist in mlx-lm 0.31.3** — the flags are
`--decode-concurrency` / `--prompt-concurrency`, and passing the wrong one
makes the server exit immediately.

With the OOM gone the run completed — and its output was corrupted by the
quote-escaping bug previously seen only on a 7B, now **reproduced on 14B**.
The emitted Python contains literal `\"\"\"` instead of `"""` and does not
compile. Critically this is an **encoding fault, not a capability one**:
repairing only the escaping, the same answer passes 9/9 correctness cases.
The planned 18-pair re-run was abandoned as uninterpretable (it would measure
corruption, not quality), and OpenCode is ruled out as the agentic runner for
the file-writing phases. The cheap single-item probe replaced a multi-hour run
that could not have answered the question either way.

**Scope of that rejection, stated precisely — an initial write-up of this
section over-claimed it as "definitively rejected" and that was too strong.**
Checking the three code-review items that had completed cleanly on 14B before
the crash found **zero corruption** in all three. They emit JSON findings
rather than reproduced source. So the fault is **task-shaped, not uniform**:
it appears when the model reproduces source code in a fenced block, which is
consistent with the original 2026-07-26 mechanism ("escape quotes in
reproduced code") but means the 14B evidence is **1 corrupted item alongside 3
clean ones**. The honest claim: corruption is confirmed on 14B for
code-reproduction answers, consistent with the prior 7B finding; it does NOT
support a blanket "OpenCode is broken for local models". It is still enough to
disqualify OpenCode as a build-phase runner, because P2/P5/P6/P9 are precisely
the code-reproduction case — but the ranking cross-check it was originally
meant to provide remains genuinely **unrun**, not answered.

**Also worth stating because it is easy to misread the above as broader than
it is: 0 of the 11 poker-capstone phases have ever been run through OpenCode.**
Every item in every OpenCode run to date is from the council v1 assessment
stack (code-review / bug-fix / long-context / instruction-format). Running
totals through OpenCode: the timeout-bounded run produced 0 usable outputs (all
timeouts, now suspected OOM-contaminated), the unbounded run produced 3 (all
clean code-review), and the smoke test produced 1 (corrupted bug-fix).

**2. A wrapper now makes build phases runnable by a text-only local model.**
The `mlx:` adapter is one-shot with no filesystem or Docker access, so it
could only attempt P1/P3/P4/P10. That is precisely the wrong subset: Haiku
passed P1 and P3 cleanly and its two genuine FAILs were P5 and P6, so a
text-only local run would have exercised only the non-discriminating phases.
Three new modules close the gap:

- `harness/file_blocks.py` — parses ```file:PATH fences and writes them under
  the impl dir. Follows CommonMark's variable-length fence rule so a
  submitted file containing its own ``` fence survives; discards unclosed
  (truncated) blocks rather than writing half a source file; rejects path
  traversal, absolute/home paths and symlink escapes, validating every path
  before writing any so one bad name cannot leave a half-applied tree.
- `harness/mlx_client.py` — importable multi-turn client (the existing
  `mlx-chat` is a one-shot CLI). Keeps the `stop`-token workaround for
  mlx-lm #973/#875 and raises `max_tokens` to 8192, since 2048 truncates a
  multi-file build answer mid-file and the parser then discards it.
- `harness/local_agent.py` + `harness/run_local.py` — the write → verify →
  feed-back → retry loop, with `model_fn` and `verify_fn` injected so it is
  testable without a live server or Docker.

Design decisions worth recording. A response with no file blocks gets a
**format nudge instead of a score of zero** — Qwen3-Coder-30B-A3B was
previously contract-failed for using a plain ```python fence when its actual
fix was correct, and that is a formatting slip, not a capability gap. The
verifier is **not** run when no files were produced, because building an
unchanged tree re-scores the previous iteration and can report a false pass.
And `iteration_count` is recorded on every result and written to the
transcript: a pass on attempt 5 is not a pass on attempt 1, and comparisons
against the Sonnet/Haiku baselines must say which it was.

**Verification, live rather than assumed.** 36 new unit tests (60 total in
the harness suite, no regressions), then three live checks against the real
14B. A one-shot task produced clean, compiling, correct code on disk — the
direct Path A/Path B contrast on identical input, since OpenCode corrupted
that exact task. Conversation growth was confirmed server-side
(`prompt_tokens` 184 → 311 on the retry), proving the model really receives
its prior answer plus the feedback rather than the loop silently dropping it.
And on a deliberately under-specified brief the model's failures went
**1 → 6 → 1** across three iterations: it added the missing function from
the feedback alone, broke two things doing so, then fixed them. That
convergence is the agentic behaviour the one-shot adapter could not supply.

One honest caveat: an earlier probe using angle brackets produced no
revision across three iterations, but that probe was badly designed (`<>`
returning True is consistent with simply ignoring angle brackets, so only a
lone `<` distinguished the cases — a single confusing data point). It is not
evidence about the model, and was replaced with the unambiguous test above.

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
- [x] P1 (document the exemplar) built and run with Sonnet — complete
      2026-07-29. Checklist 1.0, judge-verified 14/15 facts correct (1
      omission, 0 wrong) after correcting a bug found in the ground-truth
      facts themselves. See "P1 built and run" above.
- [x] P2 (QA the exemplar, blind mode) built and run with Sonnet —
      complete 2026-07-29. 72/72 tests pass on the exemplar, 3/3 planted-
      bug-catching tests correctly fail on the broken variant, all
      independently re-verified. See "P2 built and run" above.
- [ ] **Follow-up bug found via P2, not yet fixed**: `Table.non_folded_seats()`
      (`exemplar/server/app/models.py`) counts `SITTING_OUT` players as
      not-folded, which feeds `_maybe_end_hand_early`'s remaining-player
      count — at a 3+-seat table with a busted/sitting-out seat present,
      a 2-player pot where one side folds may not correctly trigger
      early-hand-end detection. Traced and confirmed, not fixed (scope
      discipline this session).
- [x] Full capability ladder (P1-P10) run end-to-end for Sonnet as the
      "medium" baseline — complete 2026-07-29. See "P3-P10 built and run"
      above for the full per-phase results table.
- [x] P3/P4 judge step (`harness/design_judge.py`, an `Agent` call, no new
      infra needed) built and wired — complete 2026-07-29
- [x] P10 (post-hoc documentation drift check) designed and built from
      scratch this session (no prior mechanism existed) and run — 5/5.
      See "P3-P10 built and run" above.
- [x] Spec-fidelity mode (P5/P6) run against the now-corrected harness —
      both pass cleanly (3/3 REST scenarios, 3/3 browser scenarios). Two
      more real harness bugs found and fixed along the way (`seat` query
      param, Playwright visibility assumption) — see "P3-P10 built and
      run" above.
- [x] P7/P8, first attempt — inconclusive by design (P9 predates several
      contract fields), recorded as a finding about contract versioning
      rather than about P9. See `runs/p7-p8-crosspair/README.md`.
- [x] P7-v2/P8-v2 — redone clean, 2026-07-29. Rebuilt only Stage 3
      (server + client) fresh from Sonnet's existing, already-judged
      stage1/stage2 docs against the current complete contracts
      (`runs/sonnet-p9v2-2026-07-29/`). Found and fixed a third real
      contract gap (undocumented CORS requirement) along the way. All
      three pairings (self-paired, P7-v2, P8-v2) pass 3/3. Updated
      `docs/BRIEF-TEMPLATE.md` to reference `CLIENT-TEST-CONTRACT.md` for
      future runs. See `runs/p7-p8-crosspair-v2/README.md`.
- [x] Cross-model roster (P11) started — Haiku, P1-P4 run 2026-07-29.
      P1 15/15, P2 42/42 vs. exemplar but 0/42 catch the planted bug
      (chip-conservation-only assertions, structurally blind to a wrong-
      winner bug), P3 2/2/2/2, P4 server 2/2/2/1 / client 2/2/1/1. Found
      and fixed three more real errors in this project's own reference
      materials along the way (P1-GROUND-TRUTH-FACTS.md F15, a raw P3
      judge miss, `exemplar/docs/design-server.md` doc-drift from its own
      code) — see "P11 begins: Haiku run" above. P5-P10 for Haiku not yet
      run; not yet folded into the `sdlc-model-council` roster format
      (`plugins/sdlc-model-council/scripts/council/roster.py`).
- [x] Haiku P5/P6 — run and independently verified 2026-07-29, both
      **FAIL** (first genuine FAILs in Haiku's ladder). P5: real all-in
      handling bug (status never transitions to `all_in`; turn-
      advancement doesn't skip all-in seats, corrupting round closure).
      P6: real self-inflicted regression (a second render block wipes
      out the first's correct hole-card data-attribute contract on every
      render). See "Haiku P5/P6, 2026-07-29" above.
- [x] **Haiku's ladder run stops at P6 — operator decision, 2026-07-30.**
      Per the fail-fast design intent stated when the ladder was first
      designed ("organize it into difficulty-ordered phases so a model's
      run can stop at its first failure instead of always paying for the
      full pipeline"), P7-P10 deliberately NOT run: P5/P6 already
      produced two independently-verified genuine FAILs, consistent with
      the weakening trend visible since P2 (see "Haiku P5/P6" above for
      the full profile). Haiku's final P11 record: **P1 clean, P2 blind
      spot, P3 clean, P4 real defects, P5 FAIL, P6 FAIL, P7-P10 not run
      (stopped)**.
- [x] **`mlx_lm.server` OOM fixed and OpenCode (Path A) definitively
      rejected, 2026-07-31.** Bounded prompt cache (`--prompt-cache-size 2`)
      turns the 2h48m hang into a 71s clean run; the completed output is
      then corrupted by the quote-escaping bug, now reproduced on 14B and
      not just 7B. The 18-pair re-run was abandoned as uninterpretable. See
      "Local-model agentic wrapper" above.
- [x] **Agentic wrapper for text-only local models built and verified,
      2026-07-31** — `harness/file_blocks.py`, `harness/mlx_client.py`,
      `harness/local_agent.py`, `harness/run_local.py`; 36 new unit tests
      plus three live checks against the real 14B (clean one-shot output,
      server-side confirmation the conversation reaches the model, and
      1 → 6 → 1 failure convergence across three feedback iterations).
- [ ] **Run Qwen2.5-Coder-14B through the ladder starting at P1, in order**,
      using the new wrapper, fail-fast as with the Sonnet and Haiku runs.
      (Terminology: P1-P10 are the phases; **P11 is the cross-model roster
      exercise, not a phase** — "running P11" for a model means running it
      from P1 upwards, as Haiku's P11 run meant P1-P6.) Do not skip ahead to
      the build phases just because the wrapper newly reaches them. Record
      `iteration_count` per phase, since a pass on attempt 5 is not
      comparable to a baseline pass on attempt 1.
- [ ] Opus and external-CLI (codex/agy/opencode) roster runs — not started.
- [ ] Fold poker-capstone phase results into the existing
      `sdlc-model-council` roster card format so they sit alongside the
      council's other assessed capability dimensions in one comparable
      report, not a separate document.
