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

**Important — Archon UI clickthrough is degraded for CLI-launched runs.**
`archon serve` only renders the rich UI (DAG graph, conversation thread,
live events) for workflows *launched through the server*. Workflows
started by `/sdlc-workflows:workflows-run` use the CLI path — they write
to the same SQLite DB and show up in `archon workflow status` and in
this skill, but the web UI's per-run detail pages will render empty for
them. This is how Archon 1.x scopes the server — not a bug on our side.
For CLI-launched runs use this skill (REST or SQLite), the CLI's own
stderr stream, or `docker logs -f`.

**Prefix matching on `--run-id`:** the `--recent` table only prints
the first 8 characters of each id. The helper accepts any unique
prefix — no need to look up the full 32-char UUID. If two runs share
a prefix you will get an "ambiguous" error; paste more characters.

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
  `archon serve` in another terminal gives live event data **and
  opens the Archon web UI at http://localhost:3090**, which
  visualises every run, every node, every event.
- The table as-is, or summarise the top 5 with bullet points if the
  user asked for a narrative.
- For `--run-id`, the detail block shows per-node `node_started` /
  `node_completed` / `node_failed` events in order — highlight any
  failures.
- If any listed run is `failed`, remind the user that
  `archon workflow run <name> --resume` picks up the most recent
  failed run from where it stopped.

### 3. Companion skills

- `/sdlc-workflows:workflows-run <name>` — launch a new workflow.
- Live per-node output during a run: the CLI streams every node's stderr to your terminal as `[node-name] <line>`. No extra helper needed.
- `docker ps --filter name=sdlc-worker` and `docker logs -f <container>` — the currently-running node containers behind any preprocessed workflow.
