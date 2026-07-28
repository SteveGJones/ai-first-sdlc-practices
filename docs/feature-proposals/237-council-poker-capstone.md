# Feature Proposal: Multi-stage agentic coding capstone — client/server poker (research)

**Proposal Number:** 237
**Status:** Draft
**Author:** Claude (Sonnet 5) + Steve Jones
**Created:** 2026-07-28
**Target Branch:** `feature/council-poker-capstone`
**Location:** `research/poker-capstone/` — **this is a research project, not a
shipped plugin capability.** `release-mapping.yaml` has no
`sdlc-model-council` entry, confirming `plugins/` is reserved for shippable
content; everything here lives under this repo's existing `research/`
convention instead. It reuses the council's adapter/`extdel.sh` machinery as
a dependency for the CLI-reachable models, but is not itself part of the
`sdlc-model-council` plugin.

---

## Problem Statement

Every existing `sdlc-model-council` assessment (v1's four static dims, #235's
`command-exec`/`monitoring`) is deterministic, single-turn, no-live-shell
propose-and-score: give a model a prompt, get an answer, score it against a
golden reference — nothing ever runs. That design is deliberate (safety,
reproducibility, uniform elicitation) but it cannot measure what most real
software delivery actually requires: can a model **architect** a system,
**design** its components in enough detail that someone else could build them,
**implement** that design across multiple cooperating processes, and produce
something that **actually runs correctly end-to-end**? None of the existing
scorers, item schema, or `assess.sh` orchestration answer that question, and
none should be stretched to — live execution of model-generated, network-facing
code is a fundamentally different risk and scoring problem from parsing a text
answer.

[NEEDS CLARIFICATION]: The scoring approach for the two open-ended design
stages (architecture, detailed design) is the least precedented part of this
proposal — see "Open Questions".

## User Stories

- As the council operator, I want to know whether a model can carry a
  non-trivial application from architecture through a working, tested
  implementation, not just answer isolated single-turn prompts.
- As the council operator, I want to separate "can this model design well"
  from "can this model implement a good design well", so a weak result on
  one doesn't hide a strong result on the other.
- As the council operator, I want the hardest, most safety-relevant part of
  this (executing model-generated server code) handled by a mechanism that
  also tests a real capability (correct Docker packaging), not bolted on as
  pure harness plumbing.

## Proposed Solution

### High-Level Approach

Build a **new, separate assessment harness** (not an extension of
`assess.sh`'s propose-and-score contract) around a single capstone
application: a client/server poker game. Server = dealer/judge (hand
evaluation, pot/side-pot math, turn enforcement). Client = web app where
players view state and act. Four stages, each independently gradable:

1. **Architecture** — system design document.
2. **Detailed design** — server design (turn state machine, betting rounds,
   pot/side-pot logic, hand-ranking algorithm) + client design (UI flow, API
   contract).
3. **Implementation** — server + client code, **including Docker
   packaging** (Dockerfile(s)/compose) written by the model itself.
4. **Run + end-to-end test** — a fixed harness, built once and never
   per-model, builds and runs the model's own Docker artifacts, then scripts
   a multi-hand game via the server's API and asserts correct outcomes.

Claude builds a full **exemplar** (all four stages) that serves two purposes:
a grading anchor for the two open-ended design stages, and a second test
mode — hand a model only the exemplar's stage-2 design and have it implement
against spec, run through the identical stage-4 harness. That isolates
design skill from implementation skill as two separate, comparable numbers.

**This is the point of the whole project**: the exemplar plus the stage-4
harness together are a **reusable scoring process**, not a one-off build. The
deliverable is something we re-run against new models as they show up — a
research instrument, not a shipped plugin feature.

**Model roster and how each is reached** (two genuinely different elicitation
mechanisms, both scored the same way):

- **External CLIs — Gemini (via the `agy` adapter), Codex, OpenCode** —
  reached the way the council already reaches them: `extdel.sh` spawning the
  real CLI, same adapter infrastructure as `assess.sh`.
- **Claude family — Fable, Opus, Sonnet, Haiku** — reached via **Claude
  Code's own Agent tool**, using a `model` override per stage, *not* through
  an external CLI adapter. This is an in-session subagent invocation, a
  fundamentally different path from spawning an external process.

**Fairness caveat, recorded now rather than discovered later** (same
discipline as the #234 Path A/B lesson): a Claude Code subagent invocation
carries its own harness/system-prompt overhead that a bare external-CLI
prompt doesn't. Elicitation prompts will be kept as close to identical as
possible across both paths, but the asymmetry can't be fully eliminated —
document it plainly in results, the way Haiku's subagent-path numbers were
caveated in #235, rather than presenting cross-path scores as directly
apples-to-apples.

### Technical Approach

- **Execution/isolation**: the stage-4 harness never runs generated code
  directly on the host. It only ever `docker build`s and `docker run`s (or
  `docker compose up`s) whatever Dockerfile(s)/compose the model itself
  produced in stage 3. This makes "can the model correctly containerize its
  own solution" a scored capability *and* the isolation boundary, rather
  than the harness silently wrapping the model's code in a container the
  model never had to reason about. Verified this session: no container
  runtime existed on this machine; OrbStack installed via `brew install
  --cask orbstack`, daemon confirmed live (`docker run hello-world`
  succeeded).
- **Stage-4 test surface**: primarily the server's API, scripted directly
  (HTTP/WebSocket calls simulating client actions) — deterministic, fast,
  no browser needed, and matches where the hard logic (turn enforcement,
  pot, hand judging) actually lives per the problem statement. Browser
  automation (Playwright) against the client's UI is an explicit stretch
  goal, not required for a first pass, since arbitrary model-generated DOM
  is much harder to assert against reliably than a JSON API.
- **Scoring**:
  - Stage 1/2 (design): a deterministic checklist (required elements
    present — e.g. turn-timeout/enforcement mechanism named explicitly,
    side-pot handling addressed, hand-ranking approach specified) plus an
    LLM-judge comparison against the exemplar for nuance. This is a new
    scorer category for the council — the first to use a judge rather than
    a golden-answer diff.
  - Stage 3 (implementation): does it build; static checks.
  - Stage 4 (run): fully deterministic pass/fail per scripted scenario
    (correct pot math, correct hand ranking/winner, illegal-turn-order
    actions rejected, betting round sequencing correct).
- **Reuses** from the existing council: adapters and `extdel.sh` for
  reaching models uniformly; **does not reuse** `assess.sh`'s scorer ABI or
  item schema, which are intentionally shaped around single-turn
  golden-answer comparison.

### Alternatives Considered

1. **Extend `assess.sh`/the existing scorer ABI to support multi-turn +
   live execution.** Rejected: would compromise the safety/reproducibility
   properties that make the existing propose-and-score stack trustworthy
   for routine, low-friction runs. Keeping this as a separate, clearly
   heavier-weight harness keeps that contract intact.
2. **Sandbox via the `sdlc-workflows` Archon/Docker orchestration plugin.**
   Rejected for this pass (operator decision): that plugin is built for
   DAG-orchestrated multi-agent delegation, heavier machinery than needed
   here. Plain `docker build`/`docker run` driven by our own harness script
   is enough, and doubles as the capability-under-test.
3. **Test the client via full browser automation from the start.** Deferred
   to a stretch goal: the server API is where the graded logic lives, and
   scripting the API directly is far more deterministic across arbitrary
   model-generated implementations than driving arbitrary generated HTML/JS.

---

## Implementation Plan

### Phase 1: Exemplar
- [ ] [P] Architecture design doc (Claude)
- [ ] [P] Detailed design docs — server (turn state machine, pot/side-pot
      math, hand ranking) + client (UI flow, API contract)
- [ ] Server implementation + Dockerfile
- [ ] Client implementation + Dockerfile/compose wiring
- [ ] Exemplar runs end-to-end manually (sanity check before the harness
      exists to check it automatically)

### Phase 2: Stage-4 harness
- [ ] Harness: `docker build`/`run` the exemplar's own containers
- [ ] Scripted multi-hand scenarios against the server API (pot math, hand
      ranking, turn-order enforcement, illegal-action rejection)
- [ ] Prove the harness against the exemplar (must pass cleanly) and against
      at least one deliberately-broken variant (must fail correctly) —
      the harness needs its own negative-case proof, same discipline as the
      existing council scorers

### Phase 3: Model-facing test modes
- [ ] Full-autonomy mode: model does all 4 stages, each stage scored
- [ ] Spec-fidelity mode: model receives the exemplar's stage-2 design only,
      implements + runs through the identical stage-4 harness
- [ ] Checklist + judge scoring for stages 1/2
- [ ] Wire results into a comparable output (not necessarily the existing
      roster/priors machinery — TBD per the open questions below)

**Dependencies:** OrbStack (installed, verified). Model access via two paths:
`extdel.sh`/council adapters (agy→Gemini, codex, opencode) for external CLIs
— likely a longer-running delegated session per model per stage, not the
single-turn `extdel.sh start` used today; and Claude Code's Agent tool with
per-stage `model` overrides (Fable, Opus, Sonnet, Haiku) for the Claude
family — no adapter involved, a genuinely different mechanism (see "Model
roster" above).

---

## Acceptance Criteria

```
Given the exemplar's Dockerfile(s) and stage-3 implementation
When the stage-4 harness builds and runs them
Then the harness completes a full scripted multi-hand game with all
     assertions (pot math, hand ranking, turn enforcement) passing
```

```
Given a deliberately broken variant of the exemplar (e.g. pot math wrong)
When the stage-4 harness runs the same scripted scenarios
Then the harness fails on the specific assertion the break violates,
     not silently or on an unrelated one
```

```
Given a model in spec-fidelity mode, handed only the exemplar's stage-2
design docs
When it implements and the harness runs its containers
Then the harness produces the same pass/fail signal it would for any
     other implementation of that design
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Model-generated server/client code has bugs that hang, spin, or exhaust resources | Medium | Medium | Containerized; harness applies its own timeouts/resource limits around `docker run` |
| Design-stage scoring (checklist + judge) is subjective/noisy compared to existing deterministic scorers | High | Medium | Treat stage 1/2 scores as directional, not roster-grade-equivalent; keep stage 4 as the hard signal |
| Per-model cost/time is far higher than existing items (full app generation + multi-stage) | High | Medium | Phase 3 explicitly deferred until phases 1/2 are proven; budget-gate stage 3+ for paid models |
| Docker packaging quality becomes a confound (good design, bad Dockerfile fails stage 4) | Medium | Low | Acceptable and intentional — containerization correctness is an explicitly tested capability, not incidental |

## Open Questions

- [ ] Exact judge mechanism for stages 1/2 — which model judges, single vs.
      multi-judge, how its cost is budgeted.
- [ ] Whether/how results from this harness fold into the existing
      `roster.py`/priors machinery, or stay a standalone report.
- [ ] Turn-enforcement test depth — how many adversarial scenarios (acting
      out of turn, betting below minimum, disconnecting mid-hand) stage 4
      needs to be a meaningful signal vs. a token check.
- [ ] Whether Playwright-based client UI testing gets added in a later
      phase, and if so, what "correct" means for arbitrary generated DOM.

## Security & Privacy

Model-generated code is executed, which is new for this council (existing
dims never execute anything). Mitigated by containerization: the harness
never runs generated code on the host, only inside the container the model
itself built, with the harness controlling what ports/resources it exposes.
No real user data involved (synthetic poker game state only). No secrets
required by the application under test.

---

**Retrospective**: `retrospectives/237-council-poker-capstone.md`
