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

### 1. Verify Archon is installed and on PATH

The upstream installer places archon at `~/.bun/bin/archon`, which is
not on the default macOS PATH. Distinguish between truly missing and
"installed but not discoverable":

```bash
if command -v archon >/dev/null 2>&1; then
    :  # on PATH — proceed
elif [ -x "$HOME/.bun/bin/archon" ]; then
    echo "Archon is installed at ~/.bun/bin/archon but that directory"
    echo "is not on your PATH. For this session, run:"
    echo ""
    echo "    export PATH=\"\$HOME/.bun/bin:\$PATH\""
    echo ""
    echo "For a permanent fix (recommended):"
    echo "    echo 'export PATH=\"\$HOME/.bun/bin:\$PATH\"' >> ~/.zshrc"
    echo "    # then open a new terminal"
    echo ""
    echo "Or re-run /sdlc-workflows:workflows-setup --health-check to"
    echo "diagnose."
    exit 1
else
    echo "Archon is not installed. Run /sdlc-workflows:workflows-setup first."
    exit 1
fi
```

Do NOT silently fall back to `$HOME/.bun/bin/archon` — that hides the
real problem (PATH misconfiguration) and the user will hit it again
the next time they open a shell. Fix the environment, not the
symptom.

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

5. Report artefacts — BEFORE cleanup:

The containers commit to the temp workspace's git. If we cleaned
up silently the user would see "Completed" and have nothing to
look at. Show what was produced first:

```bash
echo ""
echo "=== Workflow artefacts ==="
echo "Workspace: $WORKSPACE"
echo ""
echo "--- New commits in workspace (vs your checkout) ---"
(cd "$WORKSPACE" && git log --oneline "$(git -C . rev-parse HEAD)..HEAD" 2>/dev/null) \
    || echo "(no commits beyond your current HEAD)"
echo ""
echo "--- New or modified files ---"
(cd "$WORKSPACE" && git diff --name-status "$(git -C . rev-parse HEAD)" HEAD 2>/dev/null) \
    || echo "(no diff available)"
echo ""
```

6. Offer the user three choices — NEVER silently discard work:

```
Workflow complete. What would you like to do with the results?

  1. Cherry-pick commits onto your current branch (default)
  2. Keep the workspace so you can inspect it: <path>
  3. Discard everything (rm -rf the workspace)

Reply with 1, 2, or 3.
```

Default when the user is absent or replies unclearly: **1**
(cherry-pick, the least surprising and the least destructive).

**If option 1 — cherry-pick onto current branch:**

We cannot use `git cherry-pick <sha>` or `git commit -C <sha>` because
those require the main repo to have the commit *object* — and the
containers committed into a *separate* git dir (the temp workspace's
`.git/`). Instead, replay each commit's diff and author metadata
explicitly:

```bash
COMMITS=$(cd "$WORKSPACE" && git log --reverse --format=%H \
    "$(git -C . rev-parse HEAD)..HEAD" 2>/dev/null)
for sha in $COMMITS; do
    # Apply the commit's diff to our index + working tree.
    if ! (cd "$WORKSPACE" && git format-patch -1 --stdout "$sha") \
            | git apply --index; then
        echo "Cherry-pick of $sha failed — workspace preserved at $WORKSPACE for manual recovery."
        SKIP_CLEANUP=1
        break
    fi
    # Pull the original commit's author + message out of the workspace
    # repo (where the object exists) and use them here.
    AUTHOR_NAME=$(cd "$WORKSPACE" && git log -1 --format=%an "$sha")
    AUTHOR_EMAIL=$(cd "$WORKSPACE" && git log -1 --format=%ae "$sha")
    AUTHOR_DATE=$(cd "$WORKSPACE" && git log -1 --format=%aI "$sha")
    MSG=$(cd "$WORKSPACE" && git log -1 --format=%B "$sha")
    if ! GIT_AUTHOR_NAME="$AUTHOR_NAME" \
         GIT_AUTHOR_EMAIL="$AUTHOR_EMAIL" \
         GIT_AUTHOR_DATE="$AUTHOR_DATE" \
         git commit -m "$MSG" >/dev/null; then
        echo "Commit of $sha failed — workspace preserved at $WORKSPACE for manual recovery."
        SKIP_CLEANUP=1
        break
    fi
done
[ -n "${SKIP_CLEANUP:-}" ] || rm -rf "$WORKSPACE"
```

**If option 2 — keep:** print the path, skip the `rm -rf`.

**If option 3 — discard:** `rm -rf "$WORKSPACE"`.

In all three cases:
```bash
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

## Long-running or multi-cycle workflows

If the workflow has nodes that take more than a few minutes, or the
user is running iterative designer→dev→review cycles:

- **Per-node timeout**: each long node must set `timeout: <seconds>` in its YAML. The default 300 s (5 min) is almost always wrong for real work.
- **Live progress during a long node**: this skill redirects Archon's stdout to a log so preprocessing errors aren't lost. For real-time feedback, tell the user to run `docker logs -f <node-container>` in a second terminal, or `tail -f` the archon log path printed by the skill.
- **Cycles (designer → dev → review → designer …)**: Archon is a DAG executor and cannot cycle within a single workflow. See *Long-Running Workflows, Cycles, and Monitoring* in `CLAUDE-CONTEXT-workflows.md` — pick per-node `loop:`, unrolled iterations, or an outer-loop wrapper depending on the shape of the problem.
- **Monitoring during a long run**: `archon workflow status` (what's live), `archon isolation list` (per-run worktrees), `docker events --since <epoch>` (node lifecycle), `docker stats` (resource use). An in-depth Prometheus/Grafana exporter is a planned follow-up PR.
- **Cost**: there is no cost meter in v1 — a multi-hour cyclical run on Opus will burn meaningful tokens. Flag this to the user before launching.
