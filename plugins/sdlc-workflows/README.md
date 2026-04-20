# sdlc-workflows

Containerised delegated execution for the AI-First SDLC. Archon orchestrates
DAG workflows where each node runs in an isolated `sdlc-worker:*-team` Docker
container with a manifest-scoped subset of plugins, agents, and skills.

## What this plugin ships

- **Three-tier Docker image model** — `sdlc-worker:base` (toolchain) →
  `sdlc-worker:full` (base + all installed plugins) →
  `sdlc-worker:<team>-team` (base + manifest-selected subset). Team images are
  the only ones intended to run workloads.
- **Team manifests** (`*.archon/teams/*.yaml`) — declare which plugins,
  agents, skills, and context files each team carries. Schema v1.0 —
  see CLAUDE-CONTEXT-workflows.md for the authoritative reference.
- **Workflow preprocessor** — translates `image:` nodes into bash nodes Archon
  can execute, injects credential mounts, per-node timeouts, and safety flags.
- **Credential resolver** — three-tier fallback
  (Keychain → `sdlc-claude-credentials` volume → `.archon/credentials.yaml`).
- **No Archon schema patches** — the preprocessor rewrites `image:` nodes
  into native `bash: docker run` nodes before Archon sees the workflow,
  so we stay decoupled from upstream Archon schema changes. (An earlier
  sed-based ContainerProvider patch was removed; it was both wrong and
  unnecessary once the preprocessor was in place.)
- **Seven user-invocable skills** (see below).

## Skills

| Skill | Purpose |
|-------|---------|
| `/sdlc-workflows:workflows-setup` | First-time setup: installs host Archon, builds base + full images, scaffolds `.archon/` dirs |
| `/sdlc-workflows:workflows-run <name>` | Execute a workflow by name |
| `/sdlc-workflows:workflows-status` | Show running / recent workflow runs |
| `/sdlc-workflows:author-workflow` | Recommend an existing workflow + team formation for a task (`--for-task "<desc>"`) or author a new one (`--new`) |
| `/sdlc-workflows:deploy-team <name>` | Build a team image from a manifest |
| `/sdlc-workflows:manage-teams` | Team lifecycle coaching (create / update / delete / review) |
| `/sdlc-workflows:teams-status` | Fleet report — team roster, staleness, coaching signals |

## Prerequisites

- Claude Code CLI, authenticated
- Docker (daemon must be running)
- Archon CLI — installed by `/sdlc-workflows:workflows-setup` or manually per
  <https://archon.diy>

## Quickstart

```bash
# Install the plugin
/plugin install sdlc-workflows@ai-first-sdlc

# First-time setup — installs host Archon, builds base + full images
/sdlc-workflows:workflows-setup

# Deploy a team (reads .archon/teams/<name>.yaml)
/sdlc-workflows:deploy-team dev-team

# Run a workflow
/sdlc-workflows:workflows-run sdlc-parallel-review
```

See `docs/quickstart.md` for the full first-run walkthrough with expected
output at each step.

## Troubleshooting

Symptom → cause → fix table in `docs/troubleshooting.md`. Covers
authentication errors, container hangs, healthcheck transitions, permission
denied on agents/skills/plugins, `workflow not found`, stale credentials, and
credential-path edge cases.

## Design references

- `CLAUDE-CONTEXT-workflows.md` (repo root) — the canonical schema reference.
  Loaded by Claude Code when working with workflows, teams, or containers.
- `docs/superpowers/specs/2026-04-17-phase5-production-hardening-design.md` —
  security hardening, signal handling, healthcheck, the `--read-only` deviation.
- `docs/superpowers/specs/2026-04-16-phase4-archon-orchestration-design.md` —
  bash-node preprocessing and the three-tier credential resolver.

## Docker on Apple Silicon (ARM64)

The Docker image includes a conditional patch for Archon's Claude client that
forces the Claude Agent SDK subprocess to run on Node.js instead of Bun. This
is needed because Bun's `child_process` stdin pipe handling hangs on ARM64
Linux when the SDK spawns `cli.js` in stream-json mode.

**The patch is conditional**: it checks whether Archon already sets
`executable:` in its SDK options. If Archon has merged the upstream fix, the
patch is skipped automatically. No action is needed from you — `docker build`
handles it.

**Upstream issue**: See `docs/issues/archon-arm64-sdk-executable.md`.

**Affected platforms**: Only ARM64 Linux containers (Docker Desktop on Apple
Silicon Macs). x86_64 Linux (CI runners, cloud VMs) is not affected.

**What it does**: Archon itself runs on Bun (for `bun:sqlite` and `.md`
import support). The Claude Agent SDK subprocess — which calls the Claude
API — runs on Node.js. Both runtimes are present in the image. The patch adds
one line: `executable: "node"` to Archon's SDK options.
