---
name: release-plugin
description: Package source files into plugin directories using release-mapping.yaml. Use when preparing a plugin release.
disable-model-invocation: false
argument-hint: "[patch | minor | major]"
---

# Release Plugin

Package source files into plugin directories based on `release-mapping.yaml`.

## Arguments

- `patch` — Bump patch version (0.1.0 → 0.1.1). Default if no argument.
- `minor` — Bump minor version (0.1.0 → 0.2.0).
- `major` — Bump major version (0.1.0 → 1.0.0).

## Steps

1. **Read `release-mapping.yaml`** from the repository root. This file defines which source files map to which plugin directories.

2. **For each plugin in the mapping**, process each component type:

   **Skills** — for each skill entry:
   - Read the source file (e.g., `skills/validate/SKILL.md`)
   - Determine the destination path in the plugin: `plugins/<plugin>/skills/<skill-name>/SKILL.md`
   - The skill directory name comes from the source path (e.g., `skills/validate/SKILL.md` → `skills/validate/SKILL.md`)
   - Copy the file, preserving directory structure
   - For skills with supporting files (templates, references), copy the entire skill directory

   **Agents** — for each agent entry:
   - Read the source file (e.g., `agents/core/sdlc-enforcer.md`)
   - Copy to `plugins/<plugin>/agents/<filename>`

   **Scripts** — for each script entry:
   - Read the source file (e.g., `plugins/sdlc-core/scripts/session-banner.sh`)
   - Copy to `plugins/<plugin>/scripts/<filename>`
   - The validation pipeline itself runs through the `validate` skill, not via wrapper scripts. Only hook-invoked scripts (e.g., `session-banner.sh`, `check-tmp-usage.py`) belong here.

   **Hooks** — hooks are plugin-native, no copy needed (they reference `${CLAUDE_PLUGIN_ROOT}`)

3. **Bump version** in each non-stub plugin's `plugin.json`:
   - Read the current version from `.claude-plugin/plugin.json`
   - Apply the version bump (patch/minor/major)
   - Write the updated version back
   - Also update the version in `.claude-plugin/marketplace.json` (at the repo root) for this plugin

4. **Validate the result:**
   - Verify every source file in the mapping exists
   - Verify every destination file was written
   - Check that `plugin.json` is valid JSON for each plugin
   - Report any missing source files as errors

5. **Report** what was packaged:
   ```
   Release packaged:
     sdlc-core v0.1.1:
       Skills: 7 (validate, new-feature, commit, pr, rules, setup-team, release-plugin)
       Agents: 3 (sdlc-enforcer, critical-goal-reviewer, code-review-specialist)
       Scripts: 6
       Hooks: 1

     Stub plugins unchanged:
       sdlc-team-ai (0.1.0-stub)
       sdlc-team-fullstack (0.1.0-stub)
       ...

   Next steps:
     1. Review changes: git diff plugins/
     2. Commit: git add plugins/ && git commit -m "release: sdlc-core v0.1.1"
     3. Tag for stable: git tag v0.1.1
   ```
