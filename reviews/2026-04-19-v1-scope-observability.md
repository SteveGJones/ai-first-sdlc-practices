# sdlc-workflows v1 Scope — Observability Review

**Date:** 2026-04-19
**Reviewer:** observability-specialist
**Branch:** `feature/96-plugin-scope-review`
**Question asked:** Is any of the monitoring surface genuinely ours to build, or are we duplicating Archon?

**Bottom line:** Most of it should stay, but for different reasons than Phase F
claimed. The critical finding (serve-catalog asymmetry → UI widgets spin for
CLI-launched runs — the primary run pattern we ship) flips the calculus.
Archon's native observability is **materially broken for our integration shape**.
That justifies `workflows-status` + `workflows_status_query.py` as a user-facing
dashboard substitute. It does **not** justify `sse_stream_follow.py`, which
targets an SSE stream that by design never carries our events.

Net cut: ~158 LOC (sse_stream_follow.py + its doc paragraphs). Net rework:
Phase F coupling-risk table and CLAUDE-CONTEXT-workflows.md monitoring framing.

---

## 1. The user journey — what does an SDLC practitioner actually want?

Ranked by frequency of the question an engineer will ask after running
`/sdlc-workflows:workflows-run`:

| # | Question | When they ask it |
|---|---|---|
| Q1 | "Did my workflow finish, and was it OK?" | Every run, within ~5 min of launch |
| Q2 | "Which step is it on right now?" | During a long run, every few minutes |
| Q3 | "It failed — which node, and what was the error?" | Every red run |
| Q4 | "Show me the last N runs — what's been happening on this repo?" | Starts of sessions; post-weekend catchup |
| Q5 | "What's running in the container *right now*?" (logs tail) | Suspected hang; node taking longer than feels right |
| Q6 | "How long did node X take? Is it getting slower?" | Performance regression suspicion; rare |
| Q7 | "Dashboard / single pane of glass across all my runs" | Nice-to-have; rare at v1 scale |
| Q8 | "Prometheus metrics / SLOs / alert on run failure" | Zero day-1 users ask this |

Q1-Q4 cover >95% of day-1 usage. Q5 is Docker-native (`docker logs -f`), not
ours to build. Q7-Q8 are v2/v3.

---

## 2. Archon's native observability — honest coverage map

Evidence from `reviews/2026-04-19-v1-scope-archon-inventory.md` (§1.6–1.7, §3.2–3.3)
and live probe in `tests/integration/workforce-smoke/run-e2e.sh:604-675` (the
non-LIVE block proves CLI snapshot works; LIVE block proves serve REST + UI
static assets are served).

| Q | Archon surface that answers it | Works for CLI-launched runs? | Evidence |
|---|---|---|---|
| Q1 "did it finish OK?" | `archon workflow run` final stderr line + exit code; `archon workflow status` | Yes — CLI writes to SQLite; `archon workflow status` reads same DB | inventory §1.6 |
| Q2 "which step now?" | `archon workflow run` streams `[node] Started/Completed` to stderr | Yes, but only if user kept the launching terminal attached | Phase F pivot #4 in `.pr-body-phase-f.md:22` |
| Q3 "which node failed, why?" | `archon workflow status` shows status; REST `/api/workflows/runs/{id}` has events; web UI has DAG + events panel | **Partial.** SQLite has `remote_agent_workflow_events`; REST reads DB. **UI DAG/SSE views are broken for CLI runs** (inventory §3.3 + brief "confirmed gaps"). Stderr of the launch terminal is the only reliable source. | inventory §3.3; brief `2026-04-19-v1-scope-review-brief.md:77-87` |
| Q4 "last N runs" | `GET /api/workflows/runs` (REST, needs `archon serve`); no CLI equivalent | **No.** `archon workflow status` shows active only, not history. CLI has no `archon workflow list-runs`. | inventory §1.6, row "Active runs" vs "Workflow run list" |
| Q5 "logs tail" | `docker logs -f` on the preprocessed node container | Yes | CLAUDE-CONTEXT-workflows.md:487 |
| Q6 "per-node duration" | REST run detail has event timestamps; UI renders them | **Partial for CLI runs** (UI views spin — see Q3) | same as Q3 |
| Q7 "dashboard" | `archon serve` web UI at localhost:3090 | **Broken for CLI runs** — DAG graph, conversation thread, SSE all spin forever | brief lines 77-87 |
| Q8 "Prometheus" | none | n/a | CLAUDE-CONTEXT-workflows.md:494-504 (acknowledged gap) |

**The critical finding changes the answer for Q3, Q4, Q6, Q7.**

Before today we assumed: "Archon web UI is the rich observability surface;
our CLI skill is a thin wrapper." Today's finding is: **for the CLI-launched
runs we ship by default, the UI's DAG graph, conversation thread, and SSE
stream views do not work.** They display spinners indefinitely because the
`archon serve` in-memory catalog never sees CLI-launched workflow definitions
(inventory §3.2). The UI *header lists* CLI runs (because `/api/workflows/runs`
reads SQLite) but *clicking into one* doesn't render.

This means the "rich UI" answer collapses back to: the web UI, for our users,
covers Q1 (status) but fails Q3/Q6 (per-node detail) and Q7 (dashboard feel).
**There is a legitimate gap for us to fill** — not because we want to be
redundant with Archon, but because Archon's own UI is materially degraded for
our integration shape.

This is the missing row in the Phase F "Coupling risk" table. See §4.

---

## 3. Our observability surface — per-component verdict

### 3.1 `workflows-status` skill + `workflows_status_query.py` (REST+SQLite): **KEEP**

**(a) Real question:** Q1, Q3, Q4 — did it finish, which node failed, last N runs.

**(b) Archon coverage today:** `archon workflow status` answers Q1 for active
runs only. No CLI answer to Q4 (history). REST `/api/workflows/runs` answers
Q4 but requires `archon serve` running. UI answers Q3/Q4 but detail views spin
for CLI runs.

**(c) If cut, user loses:** the single answer to Q4 on a fresh machine with no
`archon serve`. That is the overwhelmingly common first-time state. `archon
workflow status` doesn't fill the gap (active-only). The user would have to
learn `sqlite3 ~/.archon/archon.db 'SELECT …'` or start a serve process and
hope the UI renders the view they need — which it won't for CLI runs.

**(d) Simplest shape:** already close. Keep the dual-source (REST→SQLite
fallback); it is the only way the skill works on a fresh machine and also
works when `archon serve` is up. The `Source: rest|sqlite` banner (line 347)
is essential for trust; keep it. Consider noting in the table footer that
`archon workflow status` is the upstream equivalent for the active-runs slice.

**LOC budget:** 353 (script) + 95 (skill) + 276 (integration tests). The
integration tests earn their keep: they lock in the SQLite schema assumption
which is the #1 coupling risk and the test failure is the only way we find
out Archon changed the schema.

### 3.2 `sse_stream_follow.py`: **CUT**

**(a) Real question:** Q2 (live step progress) for programmatic/piped
consumption, per the docstring at `sse_stream_follow.py:14-16`.

**(b) Archon coverage today:** For CLI-launched runs — **none via SSE, by
design** (inventory §3.3; gate in Archon's `executor.ts:615-623`). CLI runs
emit into a separate in-process `WorkflowEventEmitter` that is never bridged
to the serve process's emitter. The script connects to
`/api/stream/__dashboard__`, which for a CLI run will **only ever deliver
heartbeats**. For server-initiated runs it would work, but we do not ship a
`workflows-run --server` path in v1 (deferred per `.pr-body-phase-f.md:48`).

**(c) If cut, user loses:** Nothing, today. There is no user-visible path
where `sse_stream_follow.py` produces events. The parallel-reviewer inventory
says so in §4.2: *"The script has no effect in our current integration
shape. This is a candidate for removal."* The CLAUDE-CONTEXT-workflows.md
footnote already admits it is only useful for server-launched runs.

**(d) Simplest shape if kept:** none — it is blind for the default run path.
Keeping it is disclosure debt (we have to explain why it's here and when it
does nothing) for no v1 user gain.

**Deferral option considered and rejected:** "keep for when v2 ships
`--server` mode." Rejected because (1) that mode isn't designed yet; (2) when
it ships it will re-invoke or re-write this helper anyway; (3) the helper is
155 LOC of dead code in the meantime, plus ~12 lines of explanatory prose in
three docs, plus a link from `workflows-status/SKILL.md:93` that leads to a
helper that won't fire for the user's run.

**Cut target:** delete `plugins/sdlc-workflows/scripts/sse_stream_follow.py`,
its reference in `workflows-status/SKILL.md:93`, and the paragraph in
`CLAUDE-CONTEXT-workflows.md:499` that explains when it does and doesn't
fire. Re-add when `workflows-run --server` lands.

### 3.3 `teams-status` skill: **KEEP** (but not an observability concern)

**(a) Real question:** "What delegation teams do I have configured, is the
team image stale relative to the manifest, and which workflows reference the
team?" This is team lifecycle / fleet health, not workflow observability.

**(b) Archon coverage:** None. Archon has no team concept.

**(c) If cut:** the user has to read each `.archon/teams/*.yaml` manifest by
hand and cross-reference against `docker images`. Painful.

**(d) Shape:** already minimal.

**Observability note:** the `Plugin environment changes` section (SKILL.md §4)
and `coaching signals` (§3) are health-check-style observability, but they
address a surface Archon doesn't cover at all. Not a re-implementation.

This component should be reviewed by the solution-architect reviewer, not me
— it is out of my scope. Listing it here because the brief asks for a
verdict, and the verdict is KEEP.

### 3.4 B1/B2 disclosure pattern: **KEEP B1, REWORK B2**

B1 — run-id prefix resolution (`resolve_run_id_prefix`, script lines 141-171).
**KEEP.** The skill prints 8-char IDs but the detail lookup needed 32 chars;
that mismatch was the #1 predicted user-frustration bug in my earlier review
(`reviews/2026-04-19-phase-f-observability-specialist.md:9-16`). Fix is in,
9 integration tests in `test_workflows_status_query_sqlite_integration.py`
exercise the resolver. Keep it.

B2 — SSE-blindness disclosure in `workflows-status/SKILL.md:52-57` and
`CLAUDE-CONTEXT-workflows.md:448-456`. **REWORK.** Today's disclosure tells
the user "SSE only sees server-launched runs." What it omits is the more
important half of today's finding: **the whole `archon serve` web UI is
degraded for CLI-launched runs, not just the SSE stream view.** DAG graph and
conversation thread views also fail. Users who read the current disclosure
will still click into the UI expecting the DAG view to work and hit a
spinner. Rewrite B2 to say: *"For CLI-launched runs (the default), the
Archon web UI lists the run but its DAG graph, conversation thread, and SSE
stream views show spinners — not a bug on our side, an Archon serve-catalog
asymmetry. Use `workflows-status` for per-node events; use `docker logs -f`
for live output."*

### 3.5 `--live-monitoring` block in e2e (`run-e2e.sh:620-678`): **KEEP**

**(a) Real question:** does the serve REST + bundled UI *actually* work
against our generated runs?

**(b) Archon coverage:** n/a — this is our assertion that Archon's own
surfaces work end-to-end for users we send at them.

**(c) If cut:** we lose the regression guard on "does `archon serve` still
respond, does the UI bundle still serve HTML, does the REST payload contain
our run id." Those are exactly the surfaces Phase F's PR body claims work.
Without the test, those claims are session-memory.

**(d) Shape:** already minimal (3 checks, 60-90s, opt-in). Critical catch:
**add a 4th LIVE assertion for the critical finding** — fetch
`/api/workflows/runs/{id}` and assert the payload actually contains the
events array for a CLI-launched run. If that returns `{}` or spins, the
disclosure in §3.4 is vindicated and the PR body's UI-works claim needs
another qualifier. This is a 5-line curl+jq check.

The current LIVE block does **not** test the one thing we just discovered is
broken. That's a gap.

### 3.6 CLAUDE-CONTEXT-workflows.md monitoring section: **REWORK**

Lines 446-534. The surface-mapping table (462-475) is useful — keep. The
"Monitoring gaps (v1)" list (494-504) is useful — keep. The "Recommended
follow-up issue" block (508-533) is 25 lines of Prometheus-exporter
speculation that reads as roadmap, not v1 user doc. **Move it to an issue
body in the tracker, replace with a one-line pointer.** v1 users don't need
25 lines of unshipped-code speculation in the reference doc; a v2 design
document belongs in `docs/superpowers/specs/`.

Second rework: the section header "Monitoring — what Archon provides"
implicitly over-claims that everything in the table works. After today's
finding, the table needs an asterisk on the SSE rows and the Web UI row,
pointing to a new "Known gap: serve-catalog asymmetry" note immediately
after. This is the biggest single disclosure improvement in the doc.

---

## 4. Disclosure honesty audit — `.pr-body-phase-f.md`

### 4.1 Redrafted "Coupling risk — Archon" table

Current table at `.pr-body-phase-f.md:28-32` has 3 rows. Today's finding is
row 4. Here's the honest version:

| Surface | What we read/rely on | Failure mode | User-visible symptom |
|---|---|---|---|
| SQLite schema | `remote_agent_workflow_runs`, `remote_agent_workflow_events` column names | Archon migration → our status skill breaks silently | `workflows-status` returns `(no workflow runs found)` or raises; 9 integration tests catch schema drift in CI but only if we run them |
| Node primitive | `bash:` node type in workflow YAML | Archon drops/renames bash node → preprocessor output rejected | `archon workflow run` fails at YAML validation, no run recorded |
| REST shape | `/api/workflows/runs` and `/api/workflows/runs/<id>` wrapper | Shape change → blank detail rows | Detail view misses events; hit during dogfood and fixed |
| **serve catalog asymmetry** | `archon serve`'s in-memory workflow catalog | Serve only registers workflows it loaded at startup from a registered codebase. **CLI-launched runs reference workflow definitions serve has never heard of.** Not a "migration" failure mode — it is the *current* behaviour. | Web UI lists the run in the header but DAG graph, conversation thread, and SSE stream views show spinners forever. Our `workflows-status` skill + `docker logs -f` are the working alternatives. |

### 4.2 Specific monitoring claims to audit

**Claim at line 14:** *"Each surface is asserted end-to-end"* followed by a
list of surfaces. The LIVE block asserts `archon serve` accepts connections,
the REST runs list contains the id, and the UI returns HTML. It does **not**
assert the UI's detail views render for a CLI-launched run. Given today's
finding, "the web UI is actually served" is true but "the web UI is actually
*useful* for the runs we ship" is unproven. Rewrite:
> *"archon serve and the REST/runs-list endpoints work against our runs;
> the web UI serves static HTML. The UI's DAG graph and SSE views are not
> asserted — they are known degraded for CLI-launched runs and bypassed by
> workflows-status."*

**Claim at line 7 (summary):** *"monitor them from the same terminal."* True
for the stderr stream while the launching shell stays attached; misleading
for "checking on a run that started earlier" (for that, `workflows-status`
is what works, not same-terminal). Tighten to: *"…monitor them via
workflows-status and the launching terminal's stderr."*

**Claim at line 13 (Summary → Archon-native monitoring):** *"the **Archon web
UI at `archon serve` / http://localhost:3090** (bundled, downloads on first
run)"* — listed as a monitoring surface without caveat. After today's
finding, this line is the one most likely to make a first-time user think
the UI is the answer and then conclude the plugin is broken when the DAG
view spins. Add: *"(lists CLI-launched runs in the header only; clickthrough
views are degraded for CLI-launched runs — see disclosure)."*

**Claim at line 53 (B2 SSE-blindness disclosure):** the bullet says B2 is
fixed by documenting SSE-only-for-server-launched. Given §3.4 above, B2 as
shipped is insufficient — it covers SSE but not the broader UI catalog
asymmetry. Either re-scope B2 in the bullet, or file a B3 in the same list
for the UI detail views.

**Claim at line 499 (CLAUDE-CONTEXT-workflows.md item 2):** *"`workflows-run`
does not auto-subscribe to the SSE stream"* — accurate, but the explanation
pivots to "the exporter follow-up will choose when to auto-launch archon
serve." That sentence should come out now. It implies future auto-launch is
on the roadmap; post-finding, auto-launching serve doesn't fix the UI
catalog problem, so it is not the path v2 should commit to.

**Claim at line 3 (TL;DR):** *"monitor them from the same terminal."* Same
issue as line 7 — tighten.

### 4.3 Items the PR body should add, not currently present

- One-line disclosure in the **Summary** section that the Archon UI's
  clickthrough views are degraded for CLI-launched runs. Not buried in a
  coupling-risk table deep in the body.
- Explicit statement that `sse_stream_follow.py` is removed (if we accept
  the cut) OR dormant-until-server-mode (if we keep it).
- A "what works where" matrix for day-1 users, similar to §2 above but
  compressed: `workflows-status` for run history/detail; launching stderr
  for live step progress; `docker logs -f` for inside-the-container view;
  `archon serve` UI for run header only, clickthrough degraded.

---

## 5. Recommendations — ranked by user-impact-per-LOC

### CUT (do now, in this PR)

**C1. `sse_stream_follow.py` — ~155 LOC + ~15 LOC doc prose.**
Zero user-visible loss. The stream it targets never carries our events.
The parallel-reviewer inventory agrees (§4.2). Remove the file, the link
from `workflows-status/SKILL.md:93`, the bullet in
`CLAUDE-CONTEXT-workflows.md:499`, and the two references in the
monitoring follow-up issue block (sse_stream_follow.py mentions at
CLAUDE-CONTEXT-workflows.md:527). Ship note in PR body: *"Removed the SSE
dashboard follower helper; it targets a stream that does not carry
CLI-launched runs. Will re-add when workflows-run --server ships."*
**Priority: highest — deletes something that can't work.**

**C2. Prometheus exporter follow-up spec block (~25 LOC of prose).**
Move from `CLAUDE-CONTEXT-workflows.md:508-533` into a proper
`docs/superpowers/specs/` design doc or an issue body. User-facing
reference doc shouldn't carry v2 roadmap speculation.
**Priority: medium — pure doc hygiene.**

### REWORK (do now, in this PR)

**R1. Coupling-risk table — add row 4 (serve catalog asymmetry).**
This is the single most important disclosure improvement. Without it, the
PR misleads by omission about the most common user-frustration path we
discovered today.
**Priority: highest rework.**

**R2. B2 disclosure — widen from "SSE blind" to "UI clickthrough
degraded."** The narrower claim gives false comfort that the rest of the
UI works. Fix `workflows-status/SKILL.md:52-57` and
`CLAUDE-CONTEXT-workflows.md:448-456` to name the broader asymmetry.
**Priority: highest rework (ties with R1).**

**R3. PR body Summary — tighten "monitor from the same terminal"
phrasing; add "UI clickthrough degraded for CLI runs" one-liner.**
~4 lines of edits.
**Priority: high.**

**R4. `--live-monitoring` block — add a 4th assertion that
`/api/workflows/runs/{id}` returns events for a CLI-launched run.**
If that assertion fails (it should, per today's finding), it proves
the disclosure is accurate and the non-LIVE path is the correct v1
recommendation. ~10 lines of bash.
**Priority: medium — test-vs-claim alignment.**

**R5. Monitoring section header in `CLAUDE-CONTEXT-workflows.md` — add
asterisks on SSE and web-UI rows of the surface table (lines 470-472),
with a "Known asymmetry" callout below the table.** ~8 lines of prose.
**Priority: medium.**

### KEEP (as-is)

- `workflows-status` skill (§3.1)
- `workflows_status_query.py` (§3.1) — the SQLite fallback is the only
  day-1 answer to Q4 (history) on a fresh machine
- `resolve_run_id_prefix` / B1 fix (§3.4)
- `test_workflows_status_query_sqlite_integration.py` — lock on the
  SQLite schema coupling risk
- `--live-monitoring` block minus R4 extension
- `teams-status` skill (§3.3; not my primary area)

### DEFER (v2 — do not block v1)

- Prometheus exporter (CLAUDE-CONTEXT-workflows.md:498 item 1)
- `workflows-run --server` mode (which would legitimise re-adding
  `sse_stream_follow.py`)
- Cost/token meter
- Long-run soak test with deliberate slow nodes
- OTel semconv alignment for event schema — the four missing fields
  flagged in my Phase F review (`exit_code`, `attempt/retry_of`,
  `workflow_run_id` on every child event, `reason`). Not v1 blockers
  individually, but cheaper to add before a Prometheus exporter exists.

Deferral justification: each of these is a positive addition, not a gap
that makes v1 actively harmful. Day-1 users answering Q1-Q5 don't need
them.

---

## Summary of cuts/reworks

| Action | Target | LOC delta | User impact |
|---|---|---|---|
| CUT | `sse_stream_follow.py` + 3 references | −170 | None (dead code) |
| CUT | CLAUDE-CONTEXT-workflows.md:508-533 follow-up block | −25 (move to issue) | None |
| REWORK | Coupling-risk table row 4 | +4 lines | +honest disclosure |
| REWORK | B2 breadth (UI clickthrough, not just SSE) | ~6 lines edited | +honest disclosure |
| REWORK | PR body Summary (2 sentences tightened) | ~4 lines edited | +honest disclosure |
| REWORK | `--live-monitoring` LIVE 4th assertion | +10 lines | +regression guard |
| REWORK | Monitoring section asterisks + callout | +8 lines | +honest disclosure |
| KEEP | Everything else in the observability surface | 0 | n/a |

**Net:** −~180 LOC, +~30 lines of honest disclosure, 0 net user-facing
capability loss. The plugin ships with a smaller, less-ambiguously-working
observability surface.

---

## Meta: what today's finding changes about the observability story

Before today, the Phase F narrative was: "Archon has a rich UI; we ship
the CLI fallback." Today's finding flips it: **the UI is degraded for our
default run shape, and our CLI fallback is actually the primary
observability surface for users, not the fallback.** The honest v1
framing is:

- **Primary:** `workflows-status` (ours) + `archon workflow status`
  (theirs, for active slice) + launching-terminal stderr (theirs).
- **Secondary:** `docker logs -f` per container.
- **Degraded (avoid / know the limits):** `archon serve` web UI for
  CLI-launched runs — lists in header only, clickthrough views spin.

That framing belongs at the top of both `workflows-status/SKILL.md` and
the `CLAUDE-CONTEXT-workflows.md` monitoring section. If we ship v1
without it, first-time users will hit the spinners, assume our plugin is
the broken piece, and the observability story we spent Phase F building
will be remembered as "that plugin where the dashboard never loaded."
