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

0. Pre-flight image check. Extract every distinct `image:` value from
   the workflow and verify each exists locally via `docker image
   inspect`. Fail fast with a build hint before we do the expensive
   rsync + seed-commit setup — otherwise the user waits, then sees a
   mid-run docker error from a single node.

```bash
MISSING_IMAGES=$(python3 -c "
import yaml
from pathlib import Path
wf = yaml.safe_load(Path('.archon/workflows/<workflow-name>.yaml').read_text())
images = sorted({n['image'] for n in wf.get('nodes', []) if 'image' in n})
for img in images:
    print(img)
" | while read -r img; do
    [ -z "$img" ] && continue
    if ! docker image inspect "$img" >/dev/null 2>&1; then
        echo "$img"
    fi
done)

if [ -n "$MISSING_IMAGES" ]; then
    echo "Workflow references team images that are not built:"
    echo "$MISSING_IMAGES" | sed 's/^/  - /'
    echo ""
    echo "Build the missing images before running:"
    echo "  • For a team image (sdlc-worker:<team-name>):"
    echo "        /sdlc-workflows:deploy-team <team-name>"
    echo "  • For sdlc-worker:base or sdlc-worker:full:"
    echo "        /sdlc-workflows:workflows-setup --with-docker"
    exit 1
fi
```

This check is deliberate: we do NOT silently auto-build the missing
image. Building a team image requires a manifest the user authored.
Building `base`/`full` is the setup skill's job. Either way, the user
makes the call, not us.

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

2. Create workspace directory with its own git root:
```bash
WORKSPACE=$(mktemp -d "${TMPDIR:-/tmp}/sdlc-run-XXXXXX")

# Extend the credential trap to also remove $WORKSPACE if we bail out
# before the user chooses what to do with it (step 6). Guarded by
# SKIP_CLEANUP so explicit "keep workspace" still wins.
cleanup_workspace_and_credentials() {
    if [ -z "${SKIP_CLEANUP:-}" ] && [ -n "${WORKSPACE:-}" ] && [ -d "$WORKSPACE" ]; then
        rm -rf "$WORKSPACE"
    fi
    cleanup_credentials
}
trap cleanup_workspace_and_credentials EXIT INT TERM

# Copy the project into the workspace, but EXCLUDE:
#   - parent .git/ (we re-init below, and would otherwise inherit
#     core.hooksPath, refs, and any committed secrets)
#   - other git worktrees
#   - heavy artefacts (node_modules, venvs, __pycache__)
#   - developer secrets that live alongside a project but are NOT
#     part of what the container should see: SSH keys, AWS creds,
#     npm/pip tokens, Docker config, shell login files, etc.
# Prompt-injection inside the container could otherwise read any of
# these and exfiltrate via tool calls. Keep this list STRICT.
rsync -a \
    --exclude='.git' \
    --exclude='.worktrees/' \
    --exclude='node_modules/' \
    --exclude='.venv/' \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='.env' \
    --exclude='.env.*' \
    --exclude='.envrc' \
    --exclude='.ssh/' \
    --exclude='.aws/' \
    --exclude='.gcp/' \
    --exclude='.azure/' \
    --exclude='.kube/' \
    --exclude='.docker/' \
    --exclude='.npmrc' \
    --exclude='.netrc' \
    --exclude='.pypirc' \
    --exclude='.gnupg/' \
    --exclude='.keychain/' \
    --exclude='.*_history' \
    --exclude='secrets/' \
    --exclude='credentials/' \
    ./ "$WORKSPACE/"

# Archon resolves cwd to the enclosing git root before discovering
# .archon/workflows/. Without a fresh git root in the workspace it
# walks up to the parent repo and fails to find the workflow. Seed
# a minimal repo so discovery stops inside $WORKSPACE. Disable hooks
# so a parent repo's pre-commit (e.g. lint gates) cannot block the
# seed commit.
(cd "$WORKSPACE" \
    && git -c core.hooksPath=/dev/null init -q \
    && git -c core.hooksPath=/dev/null add -A \
    && git -c core.hooksPath=/dev/null \
           -c user.email=sdlc-workflows@local \
           -c user.name=sdlc-workflows \
           commit -q -m "workflow-seed" >/dev/null)

# Capture the seed SHA as our "before" reference. Step 5's diff and
# step 6's cherry-pick compare against this — NOT against any
# `git -C .` lookup, which inside a `cd "$WORKSPACE"` subshell would
# collapse to the workspace HEAD itself and report zero commits.
SEED_SHA=$(cd "$WORKSPACE" && git rev-parse HEAD)
```

3. Preprocess the workflow INTO the workspace:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/preprocess_workflow.py \
    "$WORKSPACE/.archon/workflows/<workflow-name>.yaml" \
    --output "$WORKSPACE/.archon/workflows/.generated/<workflow-name>.yaml" \
    --workspace "$WORKSPACE" \
    --cred-mount "$CRED_MOUNT" \
    --commands-dir "$WORKSPACE/.archon/commands"

# Archon's workflow discovery recurses into `.archon/workflows/`, which
# means both the original (with `image:` nodes Archon cannot execute)
# and the preprocessed (with `bash:` nodes) are loaded keyed by the same
# filename — readdir order decides which wins. Overwrite the original
# in the workspace with the preprocessed version to make this
# deterministic.
rm -f "$WORKSPACE/.archon/workflows/<workflow-name>.yaml"
cp "$WORKSPACE/.archon/workflows/.generated/<workflow-name>.yaml" \
    "$WORKSPACE/.archon/workflows/<workflow-name>.yaml"
```

4. Run the preprocessed workflow from inside the workspace:
```bash
# Archon 1.x emits a spurious "nested Claude Code detected" warning
# when CLAUDECODE=1 is in the env, and that warning path can suppress
# workflow discovery. Unset the CC handshake vars before the call.
(cd "$WORKSPACE" \
    && env -u CLAUDECODE -u CLAUDE_CODE_SSE_PORT -u CLAUDE_CODE_IPC_FD \
           archon workflow run <workflow-name> --no-worktree)
```

Notes:
- `--no-worktree` — workspace isolation is managed by the containers,
  not by Archon's worktree provider.
- The `cd "$WORKSPACE"` is load-bearing: Archon resolves cwd to the
  enclosing git root before looking for `.archon/workflows/`. The fresh
  git in step 2 is what stops that walk.
- The SSE dashboard stream on `archon serve` only observes runs
  launched through the server; CLI-launched runs write to SQLite but
  do not appear in the SSE stream. Use `workflows-status` (REST or
  SQLite) for CLI runs.

**While it runs — tell the user where to watch:**

Archon ships the monitoring surfaces; our job is to name them.
Emit this block to the user as soon as `archon workflow run` is
launched so they know how to observe without asking:

```
Workflow launched. Monitoring surfaces (Archon-native):

  • Live per-node lines in this terminal
        "[node] Started" / "[node] Completed (duration)" on stderr.

  • Archon web UI
        archon serve          # in another terminal
        open http://localhost:3090
      Full dashboard with every run, every node, every event.
      (First run downloads the UI; subsequent runs start instantly.)

  • CLI snapshot (no server needed)
        archon workflow status            # what's live right now
        archon isolation list             # per-run worktrees
        /sdlc-workflows:workflows-status  # REST + SQLite, works either way

  • Container-level detail
        docker ps --filter name=sdlc-worker
        docker logs -f <container-id>
```

If the run fails part-way, Archon supports resumption:
`archon workflow run <name> --resume` picks up the most recent
failed run from where it stopped.

5. Report artefacts — BEFORE cleanup:

The containers commit to the temp workspace's git. If we cleaned
up silently the user would see "Completed" and have nothing to
look at. Show what was produced first:

```bash
echo ""
echo "=== Workflow artefacts ==="
echo "Workspace: $WORKSPACE"
echo ""
echo "--- New commits in workspace (vs seed) ---"
(cd "$WORKSPACE" && git log --oneline "$SEED_SHA..HEAD") \
    || echo "(no commits beyond the seed)"
echo ""
echo "--- New or modified files ---"
(cd "$WORKSPACE" && git diff --stat "$SEED_SHA" HEAD) \
    || echo "(no diff available)"
echo ""

# U-5: Fan-in overlap warning.  When two or more commits in the
# workspace touched the same file, the last writer's version won
# silently.  Show a warning so the user knows what was overridden
# before they cherry-pick.  This is a soft warning, not a hard fail.
OVERLAP=$(cd "$WORKSPACE" && \
    git log --name-only --format="" "$SEED_SHA..HEAD" 2>/dev/null \
    | sort | uniq -d)
if [ -n "$OVERLAP" ]; then
    echo "⚠  Fan-in overlap: the following files were modified by"
    echo "   multiple workflow nodes. The last writer's version won."
    echo "   Review the diff before cherry-picking."
    echo "$OVERLAP" | sed 's/^/     /'
    echo ""
fi
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
    "$SEED_SHA..HEAD" 2>/dev/null)
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

**If option 2 — keep:** print the path and set `SKIP_CLEANUP=1`
so the exit trap does not destroy the workspace.

**If option 3 — discard:** `rm -rf "$WORKSPACE"`.

In all three cases:
```bash
# Credential file + any workspace we chose to discard are removed by
# the trap installed in step 2. Re-running is harmless:
cleanup_workspace_and_credentials
```
Note: the preprocessed YAML lives inside $WORKSPACE, so it goes
away with the workspace (option 3 or a failed run). Options 1 and 2
preserve the workspace intentionally.

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
- **Live progress during a long node**: `archon workflow run` emits per-node `[name] Started` / `[name] Completed (duration)` lines to stderr as they happen — no redirect needed to see them. For tool-level detail inside a node, add `--verbose` and pass it through to archon. For the container's own output (whatever the AI is printing), open a second terminal and run `docker logs -f $(docker ps -q --filter name=sdlc-worker --latest)`.
- **Cycles (designer → dev → review → designer …)**: use `loop.stages:` — see *Long-Running Workflows, Cycles, and Monitoring* in `CLAUDE-CONTEXT-workflows.md` for the primary pattern, with unrolled iterations as a fallback for fixed small counts.
- **Monitoring surfaces** (any combination): the CLI's own stderr stream (shown automatically), `/sdlc-workflows:workflows-status` for historical + REST-backed detail, `archon workflow status` (what's live), `archon isolation list` (per-run worktrees), `docker logs -f <container>` (per-node output), `docker events --since <epoch>` (node lifecycle), `docker stats` (resource use). The Archon web UI (`archon serve` on http://localhost:3090) renders the rich per-run graph only for runs launched through the server — CLI-launched runs show up in listing but the detail pages render empty. Use `workflows-status` and `docker logs` for CLI runs.
- **Cost**: there is no cost meter in v1 — a multi-hour cyclical run on Opus will burn meaningful tokens. Flag this to the user before launching.
