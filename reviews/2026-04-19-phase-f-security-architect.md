# Phase F Security Architect Review — EPIC #96

**Date**: 2026-04-19
**Reviewer**: security-architect
**Scope**: Containerised Claude Code workers — credential handling, workspace seed, container hardening, network boundary, YAML trust boundary.
**Verdict**: **No blockers for workstation-scoped MVP.** Ship with the H-1 rsync exclude-list widening applied, and file M-1/M-2 as follow-up issues.

---

## CRITICAL

None.

## HIGH

### H-1 — Workspace seed may leak developer secrets into worker containers
**Evidence**: `plugins/sdlc-workflows/skills/workflows-run/SKILL.md:121-127` — `rsync -a --exclude='.git/' --exclude='.worktrees/' --exclude='node_modules/' --exclude='.venv/' --exclude='__pycache__/' ./ "$WORKSPACE/"`.
**Finding**: The exclude list blocks `.git/` and heavy dirs but **not** common developer-secret files that sit at a project root: `.env`, `.env.*`, `.npmrc`, `.netrc`, `.pypirc`, `.aws/`, `.azure/`, `.gcloud/`, `.kube/`, `.ssh/`, `.docker/config.json`, `.terraformrc`, `.pgpass`. Any of these get copied into `$WORKSPACE`, mounted read-write at `/workspace`, and are readable by the Claude Code process inside the container. A prompt-injection in any command brief can then read them and exfiltrate them via a commit or tool output.
**Remediation**: Extend the rsync exclude list to cover well-known secret paths. Add `--exclude='.env'`, `--exclude='.env.*'`, `--exclude='.npmrc'`, `--exclude='.netrc'`, `--exclude='.pypirc'`, `--exclude='.aws/'`, `--exclude='.azure/'`, `--exclude='.gcloud/'`, `--exclude='.kube/'`, `--exclude='.ssh/'`, `--exclude='.docker/'`, `--exclude='.terraformrc'`, `--exclude='.pgpass'`, plus an `--exclude='*.pem'` / `--exclude='*.key'` belt-and-braces pass. Document the exclude contract in `CLAUDE-CONTEXT-workflows.md` so additions are deliberate. Log which entries were excluded at `$WORKSPACE` seed time for auditability.

## MEDIUM

### M-1 — Credentials briefly land inside a writable, container-accessible path
**Evidence**: `plugins/sdlc-workflows/docker/entrypoint.sh:26-30` copies the read-only mount to `/home/sdlc/.claude/.credentials.json` (writable). `docker/Dockerfile.base` deliberately leaves `/home/sdlc/.claude/` writable (per the dropped `--read-only` decision).
**Finding**: Claude Code itself reads this file, which is required. However, any post-exploitation code running as `sdlc` can read the full OAuth token (`claudeAiOauth.accessToken`, `refreshToken`) from the file, or from Claude's own in-memory handle, and exfiltrate it to the workspace git or stdout. Containment relies entirely on Claude Code not being coerced into `cat`-ing it. The cleanup trap removes it on exit, but the token is already valid off-host if leaked.
**Remediation (defence-in-depth, not blocker)**: (a) Tighten entrypoint to `chmod 400` (not 600) and `chown sdlc:sdlc` explicitly; (b) add a post-run host-side check that the credential file was removed (exit-code audit); (c) consider a short-lived token proxy in a future EPIC so containers never see the long-lived OAuth refresh token. File as follow-up issue.

### M-2 — Network boundary is implicit, not enforced
**Evidence**: `plugins/sdlc-workflows/scripts/preprocess_workflow.py:266-279` — `docker run` flags do **not** include `--network` restriction. Containers inherit the default bridge network, which can reach anything the host can: Anthropic API (required), plugin marketplace (required), arbitrary internet (not required).
**Finding**: A prompt-injected worker can POST the OAuth token or workspace contents to any URL. No egress allow-listing exists. For a workstation MVP this is consistent with the developer threat model (the host already has full network), but it should be explicit, not accidental.
**Remediation**: Document the accepted risk in `CLAUDE-CONTEXT-workflows.md` "Security model". For a hardened mode, add an optional `--network sdlc-egress` where `sdlc-egress` is a user-created Docker network with iptables rules allowlisting `api.anthropic.com` and the plugin marketplace. Treat as post-MVP.

### M-3 — `archon workflow` and command briefs are trusted strings
**Evidence**: `preprocess_workflow.py:284-305` uses `shlex.quote` on paths but `node["prompt"]` text is injected via heredoc sentinel (`_fresh_heredoc_sentinel`, good) while `node["command"]` names are `shlex.quote`'d (also good). However, workflow YAML and team manifests are arbitrary user input; a malicious manifest could set an image tag that pulls a rogue registry (`image: evil.example.com/worker:tag`) and the preprocessor will `docker run` it with the credential mount.
**Finding**: There is no image-tag allowlist or signature verification. A tampered `.archon/workflows/*.yaml` in a dependency's example directory, or a `git apply` from a hostile PR, can redirect credential mounts to any image.
**Remediation**: (a) Validate image names against an allowlist prefix (`sdlc-worker:` or `sdlc-team-*:`) in `transform_node`; (b) for v2, require cosign signature verification via sigstore policy controller or a shell wrapper before `docker run`.

## LOW

### L-1 — `ARCHON_ARGS` unquoted word-splitting (acknowledged in code)
**Evidence**: `entrypoint.sh:146` — `timeout "$TIMEOUT" archon run "$ARCHON_WORKFLOW" ${ARCHON_ARGS}`. The comment explicitly accepts this as contract.
**Finding**: The author has chosen word-splitting as a feature. Acceptable given the constrained caller, but any code path that ever lets a workflow author supply `ARCHON_ARGS` from an untrusted manifest field becomes shell-injection. Tag the risk.
**Remediation**: Add a unit test that asserts `ARCHON_ARGS` is never populated from YAML fields; only from the workflows-run skill's own argv. Already conformant; lock it in.

### L-2 — `detect-loop-bug.sh` and `loop-workaround.sh` are `source`'d from a world-readable path
**Evidence**: `entrypoint.sh:108-115`. Files live at `/opt/sdlc-scripts/` (root-owned from Dockerfile copy). Inside the container this is fine, but if a future image build step ever copies these from a writable bind mount (e.g. during dev), tampering becomes trivial.
**Remediation**: Add a Dockerfile assertion that `/opt/sdlc-scripts/` is root-owned and mode `0755`, and that files are `0555`.

### L-3 — Credential freshness check uses Python heredoc without `set -e` coverage
**Evidence**: `entrypoint.sh:49-75`. The heredoc Python block swallows JSON errors with `sys.exit(0)`, which silently continues even on credential-file tampering. Prefer surfacing the parse error so a corrupted credential file is visible rather than treated as absent.
**Remediation**: Change bare `except Exception: sys.exit(0)` to log a structured warning to stderr before exiting 0.

### L-4 — No SBOM or image signing
**Evidence**: Phase 5 spec "Out of scope" — CI/CD automation, image registry, scanning, SBOM, cosign signing all deferred.
**Finding**: Acceptable for workstation MVP (users build locally), but must be addressed before any shared registry or fleet deployment. The supply-chain pins (`ARCHON_SHA`, `BUN_IMAGE_TAG`, Claude CLI version) are good; digest pins (`@sha256:...`) would be better, as acknowledged in the Dockerfile comment.

## Accepted Risks (not findings, called out for transparency)

- **`--read-only` dropped** — Documented rationale (Claude Code requires writable `~/.claude/`) is sound. `chmod -R a-w` on `plugins/`, `agents/`, `skills/` is a reasonable compensating control.
- **`--cap-drop ALL` + `--no-new-privileges` + UID 1001** — Correct baseline for workstation threat model.
- **Memory/CPU caps (`--memory=4g --cpus=2`)** — Prevent host starvation under parallel fork/merge. Sufficient.
- **Signal handling via `trap cleanup SIGTERM SIGINT EXIT`** — Kills the process group; correctly scoped.
- **Shell-escape hygiene in `_build_docker_run`** — `shlex.quote` on every interpolated path/image/timeout/model; heredoc sentinels use 64-bit nonces. Good.
- **Parallel git-write guardrail (`ParallelGitWriteError`)** — Prevents a correctness bug that would also have security implications (interleaved commits containing another branch's unreviewed changes).

## Shipping Decision

Ship Phase F with **H-1 remediated in this branch** (exclude list widening is a one-line change). File M-1, M-2, M-3, L-3, L-4 as follow-up issues before any non-workstation (CI, fleet, multi-tenant) deployment. L-1, L-2 are documentation-level tightening.

---

**Files referenced (absolute paths)**:
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/plugins/sdlc-workflows/skills/workflows-run/SKILL.md`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/plugins/sdlc-workflows/docker/entrypoint.sh`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/plugins/sdlc-workflows/docker/Dockerfile.base`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/plugins/sdlc-workflows/scripts/preprocess_workflow.py`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/plugins/sdlc-workflows/scripts/resolve_credentials.py`
