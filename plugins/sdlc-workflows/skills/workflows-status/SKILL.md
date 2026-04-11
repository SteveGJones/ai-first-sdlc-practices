---
name: workflows-status
description: Check the status of running or recent SDLC delegated workflows.
disable-model-invocation: false
argument-hint: "[--running | --recent | <run-id>]"
---

# SDLC Workflow Status

Check the status of Archon workflow runs.

## Arguments

- `--running` — show currently running workflows
- `--recent` (default) — show recent workflow runs
- `<run-id>` — show details for a specific run

## Steps

### 1. Verify Archon is installed

Run `archon --version 2>/dev/null`. If not found:
```
Archon is not installed. Run /sdlc-workflows:workflows-setup first.
```

### 2. Query workflow status

For `--running`:
```bash
archon workflow list --running 2>/dev/null
```

For `--recent`:
```bash
archon workflow list --recent 2>/dev/null
```

For a specific run:
```bash
archon workflow status {run-id} 2>/dev/null
```

### 3. Present results

Format the output showing:
- Run ID, workflow name, start time, duration
- Node status: completed / running / pending / failed / skipped
- For failed nodes: error summary
- For completed runs: final output summary
