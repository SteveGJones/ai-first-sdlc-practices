# Observability Review — EPIC #96 Phase F (pre-PR)

**Scope:** Observability surface of `feature/96-sdlc-workflows` as of 2026-04-19.
**Verdict:** Ship. The dual-surface (REST + SQLite) design is sound for v1; the
SSE split is a real cliff but an honest one — fix the docs, not the code.

## v1-blocker (must fix before PR merges)

**B1. Rename the `--recent` RUN ID column to match `--run-id`.**
The skill truncates to 8 chars in the table but requires 32 chars on lookup.
This is the single most likely way a user concludes "your tool is broken."
Mitigation: print the full id when `--json`, and in the table show
`<8-char>…` with a footer line `use --run-id <full-id>  (archon workflow status <run-id> also accepts full)`.
No code change required if you add the footer in the skill wrapper; 10-min doc
fix. Classified blocker because it directly undermines the trust the dogfood
was meant to build.

**B2. Promote the SSE-blindness disclosure out of workflows-run/SKILL.md and
into workflows-status and CLAUDE-CONTEXT-workflows.md.**
Users who read only workflows-status will hit the cliff. One sentence in each
skill header: *"SSE dashboard only sees runs launched through `archon serve`
HTTP API; `archon workflow run` (CLI) writes to SQLite only. `workflows-status`
reads both."* Keep the existing follow-up note in workflows-run.

## v1-ship-with-caveat (document, track as follow-ups)

**C1. Dual-surface REST+SQLite is coherent IF the `Source: rest|sqlite` banner
stays visible.** The script prints it; good. The risk is users not noticing
when they fall back (e.g. REST timed out mid-list so they see a stale SQLite
view). Mitigation: when REST returns but times out on a specific run detail,
surface `Source: sqlite (REST timed out)` rather than silent fallback. Current
code silently returns None on URLError — acceptable for v1, log it in v2.

**C2. Event schema is missing four fields you will regret not emitting.**
Looking at `format_event()` in `sse_stream_follow.py`, events carry
`type/runId/status/name/duration/error/timestamp`. Missing:
- **`exit_code`** (container/process) — distinguishes "node ran, returned
  non-zero" from "container crashed" from "signal killed."
- **`attempt` / `retry_of`** — for loop.stages cycles, there is no way today
  to know if event N is a retry of event M. A correlation id (`cycle_id` +
  `iteration`) would make Prometheus counters honest.
- **`workflow_run_id` on every child event** — `runId` is the conversation
  id; Phase F dogfood showed confusion between conversation and run.
- **`reason`** (free-text) on status transitions — "cancelled by user,"
  "approval rejected," "worker timeout." Without it, alerts can only say
  "this failed."

None block v1 (the table view is usable without them), but adding them before
the Prometheus exporter is cheaper than migrating dashboards later.

**C3. No cost/token meter.** Already documented as a known gap. Note it in
the PR body as the single biggest unmitigated risk for multi-hour Opus cycles
and file a follow-up issue with a concrete data source (Claude Code usage
log, if available, else usage-reporting API).

## v2 (follow-up PR, no action now)

**V1. Prometheus exporter design.** To cover **both** server-launched and
CLI-launched runs, the exporter must read from SQLite (the one universal
surface) as the primary source, and enrich with live SSE deltas when
`archon serve` is up. Architecture:

```
exporter ──▶ SQLite poller (5s)  ──▶ gauges/counters (always present)
         └──▶ SSE subscriber      ──▶ histograms (low-latency, serve-only)
         └──▶ docker events       ──▶ container lifecycle
```

Metrics (OTel semconv-aligned where possible): `sdlc_workflow_runs_total
{workflow,status}`, `sdlc_workflow_run_duration_seconds` (native histogram),
`sdlc_workflow_node_duration_seconds{workflow,node,status}`,
`sdlc_workflow_cycle_iterations{workflow,cycle}`,
`sdlc_team_container_starts_total{team}`. SLI candidates: node success rate,
p95 node duration, cycle-convergence rate.

**V2. Structured JSON log emission from `archon workflow run` stderr.** The
current `[name] Started` / `Completed (duration)` is human-readable but not
machine-parseable. A `--log-format=json` flag on the CLI would let Fluent Bit
ship CLI-run events to Loki without the SSE detour.

**V3. Soak test (≥20min nodes, ≥3 cycles).** Without this, credential expiry
and workspace-corruption bugs stay hypothetical.

---
**Bottom line:** ship with B1+B2 fixed. Phase F surfaces are better than most
observability stacks ship at v1. Don't let perfect block the PR.
