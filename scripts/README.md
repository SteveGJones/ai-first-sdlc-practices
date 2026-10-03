# Development Scripts

## setup-dev-environment.sh

Symlinks the skills and agents that we **ship** (per `release-mapping.yaml`) into `.claude/skills/` and `.claude/agents/` so the local Claude Code session uses the source code we are actively editing — not a stale published version.

### Why this exists

When developing the SDLC plugin family, we need to test our changes to skills and agents locally. But Claude Code installs plugins from a published marketplace (GitHub), which means:

- Editing `skills/validate/SKILL.md` in the source has no effect on the local session — it's still using the published version
- Adding a new agent at `agents/core/foo.md` requires publishing before we can use it
- Bug fixes can't be verified until they're merged

This script creates symlinks so local edits take effect immediately. When you change a shipped skill or agent, the local Claude Code session sees the change after a restart.

### Scope

The script only links files **we ship** (anything listed in `release-mapping.yaml`). It does NOT touch:

- Skills/agents from other plugins (`superpowers`, `claude-code-guide`, `code-review`, etc.) — these stay globally installed and unaffected
- Per-developer Claude state (sessions, history, settings)
- Anything outside `.claude/skills/` and `.claude/agents/`

### Usage

```bash
# First time after cloning the repo:
./scripts/setup-dev-environment.sh

# Re-run after release-mapping.yaml changes (new skills/agents added):
./scripts/setup-dev-environment.sh

# Replace pre-existing real files (e.g., from a previous developer setup):
./scripts/setup-dev-environment.sh --force
```

After running, restart Claude Code for the symlinks to take effect.

### How it works

The script reads `release-mapping.yaml` to find every skill and agent we ship. For each one:

- **Skills**: Links `.claude/skills/<name>` → `skills/<name>/` (a directory symlink covering SKILL.md, templates, references, etc.)
- **Agents**: Links `.claude/agents/<name>.md` → `agents/<category>/<name>.md` (a file symlink)

The script is idempotent — re-running it removes existing symlinks and creates fresh ones based on the current `release-mapping.yaml`. It never touches non-symlink files unless `--force` is used.

### Safety

- **Symlinks only** — the script never copies, moves, or deletes real files (without `--force`)
- **`.claude/` is gitignored** — symlinks are per-developer state, not committed
- **Source files are the only truth** — editing `skills/validate/SKILL.md` updates the symlinked target; editing the symlink updates the source (they're the same file)
- **`--force` deletes pre-existing real files** — only use if you're sure the existing files are stale and should be replaced with symlinks to the source

### Rule for developers

> **Only use shipped skills and agents during development.** Don't create project-specific skills in `.claude/skills/` or download agents to `.claude/agents/`. Anything you'd want to use should either be:
>
> 1. **Shipped in the SDLC plugin** (then edit it in `skills/` or `agents/` and re-run `setup-dev-environment.sh`)
> 2. **Installed from another plugin** (then it lives in the global plugin cache, not in this repo)
>
> This prevents accidentally testing against stale state and keeps the dev environment consistent across the team.

### Troubleshooting

**"Symlink already exists, not a symlink"** — A previous developer setup left real files in `.claude/agents/` or `.claude/skills/`. Use `./scripts/setup-dev-environment.sh --force` to replace them.

**Symlinks point to nonexistent files** — `release-mapping.yaml` references a file that doesn't exist. Check the mapping or restore the missing source file.

**Local Claude Code still uses old version** — Restart Claude Code. Symlinks are detected at session start.
