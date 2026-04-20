# Containerised Workers — Troubleshooting

Symptom-based troubleshooting guide. When a containerised workflow fails, match the error to find the fix.

## Authentication Errors

### `authentication_error` / HTTP 401

**Cause:** Credentials expired or not available to the container.

**Diagnosis:**
```bash
python3 plugins/sdlc-workflows/scripts/resolve_credentials.py
```

**Fixes:**
- **Tier shows "none"**: Claude Code is not authenticated on this machine. Run `claude auth login` in a terminal, then retry.
- **Tier shows "keychain" but container fails**: The Keychain credential may have expired. Re-authenticate Claude Code (`claude auth login`), then retry.
- **Tier shows "volume"**: The Docker volume credential may be stale. Re-run `plugins/sdlc-workflows/scripts/login.sh`.
- **Tier shows "config"**: Check that the file at the `credential_path` in `.archon/credentials.yaml` exists and contains valid JSON with a `claudeAiOauth` key.

### `not logged in` / `please run /login`

**Cause:** The entrypoint's auth check (`claude -p "say ok"`) failed. Same fixes as above.

## Container Execution Errors

### Container hangs — no output for >5 minutes

**Cause:** Claude may be in a prompt loop, or there's a network issue.

**Diagnosis:**
```bash
docker ps  # Check health status
docker logs <container-id>  # Check output
```

**Fixes:**
- `docker stop <container-id>` — triggers graceful cleanup via SIGTERM trap.
- If CLAUDE_TIMEOUT is set (default 300s), the container auto-exits after that duration.
- To increase timeout for long-running tasks, set `timeout: 600` on the workflow node.

### `Permission denied` writing agents, skills, or plugins

**Cause:** The image locks `/home/sdlc/.claude/agents/`, `/home/sdlc/.claude/skills/`, and `/home/sdlc/.claude/plugins/` to read-only via `chmod -R a-w` at build time (S-I-2). A runtime prompt or tool cannot drop new agent/skill/plugin definitions.

**This is intentional.** It removes the primary runtime agent-injection surface. Combined with `--cap-drop ALL` and `--security-opt no-new-privileges` on `docker run`, the container has no legitimate reason to write user-level agent definitions.

**Note:** `--read-only` is **not** applied to the root filesystem. Claude Code needs writable paths under `~/.claude/` for plugin runtime state, so the root filesystem is left writable and the specific attack surfaces are chmod'd instead.

**If you need to extend the team:**
- Add the agent/skill to the team manifest (`.archon/teams/<team>.yaml`) and rebuild the team image.
- Place local agents/skills under the project tree and reference them with `local:<path>` in the manifest.
- **Do not** attempt to work around the chmod lock at runtime — that is the control point this feature exists to enforce.

**If you see permission errors from Claude Code itself** (e.g. unable to write cache files):
- Report these — the baseline permissions are expected to leave Claude Code's runtime-state paths writable. A regression in the Dockerfile generator may have over-locked.

### Exit code 124 (timeout)

**Cause:** CLAUDE_TIMEOUT expired before Claude finished.

**Fixes:**
- Increase timeout: add `timeout: 600` (or higher) to the workflow node.
- Simplify the command prompt — break complex work into multiple nodes.
- Check if the prompt is causing Claude to loop (open-ended instructions without clear completion criteria).

### `OCI runtime create failed` / `permission denied`

**Cause:** Capability or filesystem restriction blocking an operation.

**Fixes:**
- Containers run with `--cap-drop ALL`. If a tool truly needs a capability (unlikely for Claude Code), check if the tool can be run differently.
- Check file permissions on the workspace mount — the sdlc user (UID 1001) must be able to read/write.

## Workflow Errors

### `archon: command not found` / `archon not on PATH`

**Cause:** The `archon` CLI is not on PATH.

**Diagnosis:**
```bash
which archon                    # empty → not installed or not on PATH
ls ~/.archon/archon.db          # present → Archon was installed here before
```

**Fixes:**
- **Not installed:** `/sdlc-workflows:workflows-setup` installs it, or run the
  upstream installer directly:
  ```bash
  curl -fsSL https://archon.diy/install | bash
  ```
- **Installed but not on PATH:** check the installer's target directory and
  add it to your shell rc (`~/.zshrc`, `~/.bashrc`). `workflows-setup`
  distinguishes "installed-not-on-PATH" from "not-installed-at-all" in its
  diagnostic output.
- **Local iteration without Archon:** `/sdlc-workflows:workflows-run` and the
  integration smoke suites default to strict-Archon mode, but the smoke
  suites accept `--direct-only` to skip the orchestrator and drive the
  workflow preprocessor + credential resolver + containers directly:
  ```bash
  bash tests/integration/workforce-smoke/run-e2e.sh --direct-only
  bash tests/integration/workforce-smoke/run-e2e.sh --parallel --direct-only
  ```
  This exercises everything this plugin owns end-to-end; only the Archon
  scheduling step is bypassed. Use `--allow-fallback` to try Archon first
  and only drop to direct mode if Archon is missing. Note that
  `/sdlc-workflows:workflows-status` still works — its REST + SQLite
  fallback needs neither `archon serve` nor the CLI.

### `workflow not found`

**Cause:** Archon can't find the workflow by name.

**Diagnosis:**
```bash
archon workflow list  # Shows available workflows
```

**Fixes:**
- Check the `name:` field inside the YAML matches what you're requesting (Archon resolves by name, not filename).
- Verify the workflow file is in `.archon/workflows/`.
- Check for YAML syntax errors: `python3 -c "import yaml; yaml.safe_load(open('.archon/workflows/<file>.yaml'))"`.

### `no commits produced` after workflow run

**Cause:** The container ran but Claude didn't follow the commit instruction.

**Fixes:**
- Check the command prompt — does it end with an explicit `git add -A && git commit -m "..."` instruction?
- Check the workspace had a git repo (the entrypoint creates one if missing).
- Run the workflow again — LLM output is non-deterministic and may follow instructions more closely on retry.

### Review files missing after parallel workflow

**Cause:** Parallel containers writing to the same workspace may have git lock contention, or Claude didn't follow the file output instruction.

**Fixes:**
- Check git log — if commits exist but files are missing, the commit may have been made before the file was written.
- Check the command prompt — be explicit about the output file path (e.g., `/workspace/security-review.md`, not just "write a review").
- If git lock contention: the containers write different files, so minor timing differences usually resolve this naturally.

### Stale team image — container runs outdated plugins/agents

**Cause:** The team manifest was updated (new plugins, agents, skills, or a
bumped plugin version) but the team image was not rebuilt. Containers launch
with whatever was baked in last time the image was built.

**Diagnosis:**
```bash
# When was the team image last built?
docker image inspect sdlc-worker:<team>-team --format '{{.Created}}'

# When was the manifest last modified?
yq '.updated' .archon/teams/<team>.yaml
ls -l .archon/teams/<team>.yaml
```

If the manifest is newer than the image, the image is stale.

**Fixes:**
- Rebuild: `bash plugins/sdlc-workflows/docker/build-team.sh <team>` (or
  `/sdlc-workflows:deploy-team <team>`).
- Check `/sdlc-workflows:teams-status` — it flags stale images by comparing
  `image_built` in the manifest against the image creation timestamp.
- After a `build-full.sh` run (e.g. after upgrading a plugin on the host),
  rebuild every team image that depends on that plugin.

### `unhealthy` container (Phase 5 healthcheck)

**Cause:** Docker's HEALTHCHECK runs `claude -p 'say ok'` every 30s. If three
consecutive probes fail (≈90s), the container is marked `unhealthy`. Common
triggers: credential staging failed, network unreachable, Claude CLI missing
from PATH, or CLAUDE_TIMEOUT killed Claude mid-request.

**Diagnosis:**
```bash
docker inspect --format '{{json .State.Health}}' <container-id> | jq
docker logs <container-id> 2>&1 | tail -50
```

The `Health` block shows each probe's exit code and stderr — look at the most
recent `FailingStreak` entries.

**Fixes:**
- Credential issue (`authentication_error` in probe stderr): see the
  Authentication Errors section above.
- Network unreachable: verify the host has outbound HTTPS to
  `api.anthropic.com`; containers inherit the host network stack.
- CLAUDE_TIMEOUT too aggressive: probes share the workload's `claude` calls —
  if the workload hogs CPU, probes may time out. Increase `timeout:` on the
  node or split the command into smaller nodes.
- The probe itself failing but Claude is otherwise fine: `docker exec` in and
  run `claude -p 'say ok'` manually to see the real error.

### Credential staging failure — `tmpfs shadow` symptom

**Cause:** The entrypoint copies the mounted credential file from
`/home/sdlc/.claude-creds/` into `/home/sdlc/.claude/.credentials.json`
before launching Claude. This two-step indirection exists because a bind
mount onto `.credentials.json` gets shadowed by Claude Code's own tmpfs
mount of `~/.claude/` — the credentials would exist on the host bind but be
invisible to Claude inside the container.

**Symptoms:** `authentication_error` even though `resolve_credentials.py`
reports a valid tier, and the host file at `mount_args` source path is
readable and valid.

**Diagnosis:**
```bash
docker exec <container-id> ls -l /home/sdlc/.claude-creds/
docker exec <container-id> ls -l /home/sdlc/.claude/.credentials.json
docker exec <container-id> cat /home/sdlc/.claude/.credentials.json | jq .claudeAiOauth.expiresAt
```

**Fixes:**
- Verify the mount source: `docker inspect <container-id> | jq '.[].Mounts'`
  — the staging bind must land under `/home/sdlc/.claude-creds/`, not directly
  at `/home/sdlc/.claude/.credentials.json`.
- Check ownership: `/home/sdlc/.claude/` must be writable by UID 1001 so the
  entrypoint copy succeeds. A stricter UID or `--read-only` on the root FS
  will break this (intentionally not used — see design spec).
- If `expiresAt` is in the past: re-run `login.sh` (for the volume tier) or
  re-authenticate Claude Code (for the Keychain tier).

## Image Build Errors

### `sdlc-worker:full is a source image`

**Cause:** Attempting to run the full image directly. It's a source layer, not a runnable container.

**Fix:** Build a team image: `bash plugins/sdlc-workflows/docker/build-team.sh <team-name>`

### `manifest not found` during build

**Cause:** The team manifest YAML doesn't exist in `.archon/teams/`.

**Fix:** Create the manifest. Use `/sdlc-workflows:manage-teams --create` or see the quickstart guide.

### `plugin not found in installed_plugins.json`

**Cause:** The team manifest references a plugin that isn't installed on the host.

**Fix:** Install the plugin first, then rebuild the full image (`build-full.sh`), then rebuild the team image.

## Credential Volume Errors

### `volume not found` when running login.sh

**Cause:** Docker volume doesn't exist yet.

**Fix:** `login.sh` creates the volume automatically. Just run it: `bash plugins/sdlc-workflows/scripts/login.sh`

### Stale credentials in volume

**Cause:** OAuth token in the Docker volume has expired.

**Fix:** Re-run `plugins/sdlc-workflows/scripts/login.sh` to refresh credentials.

### `mount_args` has spaces or special characters

**Cause:** The credential file path contains spaces.

**Fix:** Check `resolve_credentials.py --json` output. Move credential files to a path without spaces.

---

## See Also

- **`CLAUDE-CONTEXT-workflows.md`** (repo root) — canonical schema reference
  for workflow YAML, team manifests, command prompts, security model, and
  credential model. Load this first when authoring or debugging workflows.
- **`plugins/sdlc-workflows/docs/quickstart.md`** — first-run walkthrough with
  expected output at each step. If a step here fails, the quickstart shows
  what success looks like for comparison.
- **`docs/superpowers/specs/2026-04-17-phase5-production-hardening-design.md`**
  — the authoritative design document for security, healthcheck, signal
  handling, and the `--read-only` deviation.
- **`docs/superpowers/specs/2026-04-16-phase4-archon-orchestration-design.md`**
  — bash-node preprocessing and credential resolver internals.
