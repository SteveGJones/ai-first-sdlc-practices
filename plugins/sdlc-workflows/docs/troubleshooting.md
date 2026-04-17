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

### `read-only file system` error

**Cause:** Container attempting to write outside allowed paths.

**Allowed writable paths:**
- `/workspace` (volume mount — project files)
- `/tmp` (tmpfs — temporary files)
- `/home/sdlc/.claude` (tmpfs — Claude runtime state)

**Fixes:**
- Ensure your command prompt writes to `/workspace/`, not elsewhere.
- If a tool needs to write to a custom path, it must be under `/workspace` or `/tmp`.
- Check the entrypoint — `npm install -g` and similar commands will fail on read-only filesystem (they should be done at image build time, not runtime).

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
