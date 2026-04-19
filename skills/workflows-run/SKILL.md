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

### 2b. Preprocess for containerised execution (if workflow has team images)

Check if any node in the workflow has an `image:` field:

```bash
python3 -c "
import yaml
from pathlib import Path
wf = yaml.safe_load(Path('.archon/workflows/<workflow-name>.yaml').read_text())
has_images = any('image' in n for n in wf.get('nodes', []))
print('NEEDS_PREPROCESSING' if has_images else 'NATIVE')
"
```

**If NEEDS_PREPROCESSING:**

1. Resolve credentials:
```bash
CRED_INFO=$(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/resolve_credentials.py --project-dir . --json)
CRED_TIER=$(echo "$CRED_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['tier'])")
CRED_MOUNT=$(echo "$CRED_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('mount_args',''))")
CRED_CLEANUP=$(echo "$CRED_INFO" | python3 -c "import sys,json; p=json.load(sys.stdin).get('cleanup') or ''; print(p)")

# Install cleanup trap *immediately* so the temp credential file is
# removed even if preprocessing or the archon run fails/is interrupted.
# The Keychain tier creates a temp file; volume and config tiers return
# an empty CRED_CLEANUP (no-op) so the trap is safe in all tiers.
cleanup_credentials() {
    if [ -n "$CRED_CLEANUP" ] && [ -f "$CRED_CLEANUP" ]; then
        rm -f "$CRED_CLEANUP"
    fi
}
trap cleanup_credentials EXIT INT TERM
```

If CRED_TIER is "none", report the error message from the resolver and stop.

2. Create workspace directory:
```bash
WORKSPACE=$(mktemp -d "${TMPDIR:-/tmp}/sdlc-run-XXXXXX")
cp -R . "$WORKSPACE/"
```

3. Preprocess the workflow:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/preprocess_workflow.py \
    .archon/workflows/<workflow-name>.yaml \
    --output .archon/workflows/.generated/<workflow-name>.yaml \
    --workspace "$WORKSPACE" \
    --cred-mount "$CRED_MOUNT" \
    --commands-dir .archon/commands
```

4. Run the preprocessed workflow through Archon:
```bash
archon workflow run <workflow-name> --no-worktree
```

Note: `--no-worktree` is used because workspace isolation is managed by the containers, not by Archon's worktree provider. The preprocessed YAML is placed in `.archon/workflows/.generated/` and Archon discovers it automatically.

5. Clean up:
```bash
rm -rf "$WORKSPACE"
rm -f .archon/workflows/.generated/<workflow-name>.yaml
# CRED_CLEANUP is removed automatically by the trap installed in step 1,
# so no explicit rm is needed here — but it is harmless to re-run:
cleanup_credentials
```

**If NATIVE (no image: nodes):**

Proceed with the existing `archon workflow run` invocation — no preprocessing needed.

### 3. Run the workflow

Execute:
```bash
archon workflow run {workflow-name} {remaining-arguments}
```

Stream the output to the user. Report completion status when done.

### 4. Report results

After workflow completes, report:
- Workflow name and duration
- Node completion status (which nodes passed/failed/skipped)
- Final output (from the terminal node)
- Any errors or warnings
