# GitHub Issue Draft: coleam00/Archon

## Title

CLI-launched workflow runs have empty detail pages in web UI

## Description

Runs launched via `archon workflow run <name>` (CLI) appear in the web
UI run listing but their detail pages (DAG graph, conversation thread,
live events) render empty / show spinners. Only runs launched through
`archon serve` (HTTP API) render fully.

## Steps to reproduce

1. `archon serve` (start the web UI)
2. In another terminal: `archon workflow run sdlc-parallel-review --no-worktree`
3. Open http://localhost:3090
4. The run appears in the run list with status and timing
5. Click into the run -- DAG graph is empty, conversation thread is blank

## Expected behaviour

CLI-launched runs should render the same detail pages as server-launched
runs. Both paths write to the same SQLite database, so the data exists.

## Impact

For CLI-first integrations (which is how most workflow automation tools
invoke Archon), the web UI is view-only on the listing page. Users must
fall back to `archon workflow status`, SQLite queries, or `docker logs`
for per-node detail.

## Root cause (suspected)

`archon serve` maintains an in-memory workflow catalog. CLI-launched runs
reference workflow definitions that serve never loaded (the CLI resolved
them from `.archon/workflows/` at launch time). When the UI tries to
render the detail page, it looks up the workflow definition in the serve
catalog, finds nothing, and renders empty.

## Suggested fix

When serving a run detail page for a workflow not in the serve catalog,
load the workflow definition from the SQLite record (which captures the
workflow name and node structure) or from the `.archon/workflows/`
directory on disk. This would decouple graph rendering from the serve
launch path.

## Versions

- Archon v0.3.6 (Homebrew compiled binary)
- macOS, Docker Desktop
