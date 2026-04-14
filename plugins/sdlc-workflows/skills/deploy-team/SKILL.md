---
name: deploy-team
description: Build a team Docker image from a manifest in .archon/teams/. Resolves plugin paths, generates Dockerfile with additive copy-only, makes plugins read-only, bakes team CLAUDE.md.
disable-model-invocation: false
argument-hint: "--name <team-name> [--image <registry/path>]"
---

# Deploy Team Image

Build a team-specific Docker image from a team manifest.

## Arguments

- `--name <team-name>` (required) — team manifest in `.archon/teams/<team-name>.yaml`
- `--image <tag>` (optional) — custom image tag (default: `sdlc-worker:<team-name>`)

## Steps

### 1. Read and validate the manifest

Read `.archon/teams/<team-name>.yaml`. Validate:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_team_manifest.py \
    .archon/teams/<team-name>.yaml \
    --installed-plugins ~/.claude/plugins/installed_plugins.json \
    --project-root .
```
If validation fails, report errors and stop.
Check status field — refuse to build inactive or decommissioned teams.

### 2. Verify base and full images exist

```bash
docker image inspect sdlc-worker:base >/dev/null 2>&1
docker image inspect sdlc-worker:full >/dev/null 2>&1
```
If missing, inform user and offer to build them:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/docker/build-base.sh
bash ${CLAUDE_PLUGIN_ROOT}/docker/build-full.sh
```

### 3. Generate team CLAUDE.md

Use the generate_team_claude_md.py script to create the team's CLAUDE.md from the manifest:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate_team_claude_md.py \
    .archon/teams/<team-name>.yaml \
    --installed-plugins ~/.claude/plugins/installed_plugins.json \
    --output .archon/teams/.generated/<team-name>-CLAUDE.md
```
If the project has a CLAUDE.md, concatenate it (project first, team second).

### 4. Build the team image

```bash
bash ${CLAUDE_PLUGIN_ROOT}/docker/build-team.sh <team-name> [--image <tag>]
```

This generates a Dockerfile with additive copy-only (no prune) and builds the image.
The generated Dockerfile and CLAUDE.md go to `.archon/teams/.generated/`.

### 5. Update manifest timestamp

After successful build, update `image_built` in the manifest YAML to current ISO-8601 datetime.

### 6. Report

Report the following:
- Image name and tag
- Image size (from `docker image inspect`)
- Agent count and skill count (from manifest)
- Generated file locations (Dockerfile and CLAUDE.md)
