---
name: workflows-run
description: Run an SDLC delegated workflow via Archon. Wraps the archon CLI with project-aware defaults.
disable-model-invocation: false
argument-hint: "<workflow-name> [arguments]"
---

# Run SDLC Workflow

Execute a named SDLC workflow via the Archon CLI.

## Arguments

- First argument: workflow name (e.g., `sdlc-parallel-review`)
- Remaining arguments: passed through to Archon as workflow arguments

## Steps

### 1. Verify Archon is installed

Run `archon --version 2>/dev/null`. If not found:
```
Archon is not installed. Run /sdlc-workflows:workflows-setup first.
```

### 2. Verify workflow exists

Run `archon workflow list 2>/dev/null` and check if the requested workflow name appears.

If not found:
```
Workflow '{name}' not found. Available workflows:
{list from archon workflow list}

To install SDLC workflows, run /sdlc-workflows:workflows-setup
```

### 3. Run the workflow

Execute:
```bash
archon run {workflow-name} {remaining-arguments}
```

Stream the output to the user. Report completion status when done.

### 4. Report results

After workflow completes, report:
- Workflow name and duration
- Node completion status (which nodes passed/failed/skipped)
- Final output (from the terminal node)
- Any errors or warnings
