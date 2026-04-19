---
name: workflows-status
description: Check the status of running or recent SDLC delegated workflows.
disable-model-invocation: false
argument-hint: "[--running | --recent N | <run-id>]"
---

# SDLC Workflow Status

Query Archon workflow runs — live + historical — without depending on
`archon` being on PATH.

## Arguments

- `--running` — show currently running workflows only
- `--recent N` — show the latest N runs (default 20)
- `<run-id>` — show full detail for a specific run, including every node
  event in order

## Steps

### 1. Query the Archon state

The `archon` CLI only exposes `archon workflow status` (active runs, no
run-id filter) and `archon workflow list` (available workflows, not runs).
Neither covers the ask. Use the query helper instead — it prefers the
REST API on `archon serve` (if running) and falls back to reading the
SQLite state DB at `~/.archon/archon.db`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/workflows_status_query.py \
    [--running | --recent <N> | --run-id <id>]
```

Additional flags:
- `--url <base>` — override the REST URL (default `http://localhost:3090`)
- `--no-rest` — skip the REST probe entirely, go straight to SQLite
- `--json` — machine-readable output (one JSON object per response)
- `--timeout <sec>` — REST probe timeout before falling back (default 1.0)

Behaviour matrix:

| `archon serve` running? | Output source |
|-------------------------|---------------|
| Yes | REST API — live + historical, richest |
| No  | SQLite read — historical + most-recent, read-only |

If neither is available (fresh machine, no Archon state yet), the script
returns `(no workflow runs found)` cleanly — this is not an error.

### 2. Present results

Default output is a table:

```
Source: rest  (archon serve)
RUN ID     WORKFLOW                       STATUS       STARTED              STEP
---------------------------------------------------------------------------------
bbdfce69   feature-pipeline               completed    2026-04-19 20:26:10
a1b2c3d4   parallel-review-pipeline       running      2026-04-19 20:30:02  2
```

Report to the user:
- The source row (REST vs SQLite) — if SQLite, hint that starting
  `archon serve` in another terminal would give live event data.
- The table as-is, or summarise the top 5 with bullet points if the
  user asked for a narrative.
- For `--run-id`, the detail block shows per-node `node_started` /
  `node_completed` / `node_failed` events in order — highlight any
  failures.

### 3. Companion skills

- `/sdlc-workflows:workflows-run <name>` — launch a new workflow.
- Live event following during a run: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sse_stream_follow.py` (requires `archon serve`).
- `docker ps --filter name=sdlc-worker` — the currently-running node containers behind any preprocessed workflow.
