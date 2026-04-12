# GitHub Issue Draft: coleam00/Archon

**Title**: Loop node reports `max_iterations_reached` despite completion signal being present in output

**Labels**: bug, workflows

---

### Environment

- Archon v0.3.5 running from source
- Docker on Apple Silicon (ARM64 Linux containers)
- Workflow with `loop:` node using `until: ALL_CLEAN` and `max_iterations: 3`

### Problem

A loop node with `until: ALL_CLEAN` and `max_iterations: 3` runs all 3 iterations successfully. The Claude agent outputs `<COMPLETE>ALL_CLEAN</COMPLETE>` (matching the `until` signal) in iteration output. Despite the signal being present, Archon reports `max_iterations_reached` and exits the loop with code 1.

This causes dependent nodes (e.g., a `final-report` node with `depends_on: [fix-and-review]`) to be skipped, because the loop node is treated as failed.

### Expected Behaviour

When the completion signal (`ALL_CLEAN`) is present in the loop iteration output, the loop should terminate with success (exit 0) regardless of which iteration number it was found in. Reaching `max_iterations` should only be a failure when the signal was NOT found.

### Workflow Definition

```yaml
nodes:
  - id: fix-and-review
    model: claude-sonnet-4-6
    context: fresh
    loop:
      prompt: |
        # Fix-Review Iteration
        ...
        If BOTH reviews pass with zero issues found, output:
        <COMPLETE>ALL_CLEAN</COMPLETE>
      until: ALL_CLEAN
      max_iterations: 3
      fresh_context: true

  - id: final-report
    depends_on: [fix-and-review]
    prompt: |
      Generate a final report...
```

### Observed Behaviour

- Iteration 1: Agent fixes code, finds remaining issues, outputs summary (no signal)
- Iteration 2: Agent reviews fixes, finds more issues, fixes them (no signal)
- Iteration 3: Agent reviews again, all clean, outputs `ALL_CLEAN` signal
- Archon: reports `max_iterations_reached`, exits loop with code 1
- `final-report` node: skipped (dependency failed)

### Possible Causes

1. Signal detection may run before the full iteration output is captured
2. The signal may need to be outside the `<COMPLETE>` tags (just the bare string)
3. Max iterations check may take precedence over signal detection on the final iteration
4. The signal may be present in stdout but not in the captured `node_output` field

### Workaround

None currently. The underlying work completes correctly — all code fixes are applied and committed. Only the loop termination status and dependent node execution are affected.
