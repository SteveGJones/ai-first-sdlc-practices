---
name: integration-test
description: Run the SDLC plugin integration test suite — fast smoke mode (~5 min, Docker) or full mode (~45-60 min, Ralph loop builds a complete app). Use to verify plugin install and setup-team flows still work end-to-end after framework changes.
disable-model-invocation: true
argument-hint: "[--smoke | --full] [--fixture <name>]"
---

# SDLC Integration Test

Run the SDLC plugin integration test suite. Two modes:

- **`--smoke`** (default) — Docker-based smoke test, ~5 minutes. Verifies plugin install, setup-team, tech detection, 1st-party discovery, and tool installation against a realistic fixture.
- **`--full`** — Legacy Ralph-driven end-to-end test, ~45-60 minutes. Builds a complete Python web app from scratch using the framework, with a full build journal.

## Arguments

- `--smoke` — Fast Docker smoke test (default). Best for routine "did I break something?" checks after framework changes.
- `--full` — Full end-to-end build. Use before major releases or when validating large framework changes.
- `--fixture <name>` — Selects which fixture to test against. Currently only `eventflow` is implemented; the argument is structured for future fixture expansion.

If no arguments are given, run `--smoke` against the `eventflow` fixture.

## --smoke (default mode)

### Preflight

Before running, verify:

1. **Docker is running.** Check with `docker info`. If it returns an error, tell the user to start Docker Desktop and retry.
2. **Auth volume exists.** Run `docker volume ls --filter name=sdlc-smoke-claude-creds --format '{{.Name}}'`. If empty, tell the user:
   ```
   Auth volume not found. Run the one-time login first:
     cd tests/integration/setup-smoke && ./login.sh
   ```
3. **Fixture exists.** Verify `tests/integration/setup-smoke/fixtures/<fixture>/README.md` exists. Default fixture is `eventflow`. If the requested fixture is missing, list the available fixtures and stop.
4. **Base image exists.** Run `docker image inspect sdlc-smoke-base:latest > /dev/null 2>&1`. If exit code is non-zero, tell the user:
   ```
   Base image not built. Build it first:
     cd tests/integration/setup-smoke && ./build.sh
   ```

If all preflight checks pass, proceed.

### Run

```bash
cd tests/integration/setup-smoke
./run.sh
```

The script:
- Mounts the credential volume at `/home/sdlc/.claude` inside a fresh container
- Mounts `PROMPT.md`, `ralph.yml`, and `fixtures/<fixture>/README.md` read-only
- Runs Ralph with the smoke test prompt
- Reports the result on stdout

### Report

After the run finishes, parse the output and produce a clean summary:

```
=== SDLC Smoke Test Result ===

Mode: --smoke
Fixture: eventflow
Runtime: <seconds>
Ralph iterations: <N>
Output checks: <passed>/<total>
Plugins discovered: <count>
Plugins installed: <count>

Status: [✅ PASS | ❌ FAIL]
```

If FAIL, point at the diagnostic logs:
```
Diagnostic logs: tests/integration/setup-smoke/.ralph/diagnostics/logs/
Most recent run: <symlink to latest>
```

### Exit Code

- 0 if all output checks passed and Ralph reported `LOOP_COMPLETE`
- 1 otherwise

## --full (legacy end-to-end mode)

### Preflight

The full mode is **not yet wrapped by this skill**. It runs the legacy `tests/integration/PROMPT.md` harness, which requires:

1. A blank GitHub repository (the test populates it from scratch)
2. Ralph CLI installed locally (`npm install -g @ralph-orchestrator/ralph-cli`)
3. Claude Code Max OAuth on the host (not a mounted volume)
4. ~45-60 minutes of wall time

Tell the user:

```
The --full mode requires manual setup outside this skill:

  1. Create a blank GitHub repo (private is fine)
  2. Clone it locally
  3. Copy tests/integration/PROMPT.md and tests/integration/ralph.yml into the clone
  4. cd into the clone and run: ralph run
  5. Watch the build journal at docs/build-journal.md as the test runs

Full mode automation via this skill is tracked as future work.
For routine "did I break something?" checks, use --smoke instead.
```

Stop after printing this message. Do not attempt to invoke the legacy harness automatically.

## Output Format

Produce one of these final lines so callers can grep for status:

- `RESULT: PASS` on success
- `RESULT: FAIL` on failure
- `RESULT: SKIPPED` when the user requested `--full` (since this skill doesn't auto-run it)

## Common Failures

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Cannot connect to Docker daemon` | Docker not running | Start Docker Desktop |
| `auth volume not found` | First-time setup not done | Run `./login.sh` in `tests/integration/setup-smoke/` |
| `base image not found` | Build step skipped | Run `./build.sh` in `tests/integration/setup-smoke/` |
| Ralph terminates in <5s with `Too many consecutive failures` | Stale image without non-root user | Rebuild base image: `cd tests/integration/setup-smoke && ./build.sh` |
| Auth session expired | Credentials volume stale | Delete and recreate: `docker volume rm sdlc-smoke-claude-creds && ./login.sh` |

For more troubleshooting, see `tests/integration/setup-smoke/README.md`.

## Why This Skill Exists

Before this skill, running the integration test required remembering Docker commands, ralph.yml paths, fixture locations, and credential volume mechanics. This skill is the canonical entry point: one slash command, one set of arguments, one report format. Use it before merging any change that touches `release-mapping.yaml`, the validate skill, the setup-team skill, or any agent that ships in the plugin family.
