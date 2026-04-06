# Plugin Library — Part 3 of #83

**Date**: 2026-04-05
**Status**: Approved
**Issue**: #83 (Part 3 of 3)
**Branch**: `feature/extend-discovery-setup-audit`

## Problem

Projects that use the SDLC framework accumulate tool recommendations from multiple sources: setup-team discovers tools at project init, pipeline-orchestrator discovers tools when building agents, users find tools manually. There's no single place that records "what tools has this project evaluated and chosen to use."

## Solution

A `.sdlc/recommended-plugins.json` file per project that accumulates tool recommendations over the project's lifetime. Written to by setup-team and pipeline-orchestrator on their respective events. No dedicated skill — just JSON writes.

## File Format

`.sdlc/recommended-plugins.json`:

```json
{
  "version": "1.0",
  "last_updated": "<YYYY-MM-DD>",
  "plugins": [
    {
      "name": "sdlc-core",
      "source": "ai-first-sdlc",
      "type": "sdlc-framework",
      "installed": true,
      "added_by": "setup-team",
      "added_at": "2026-04-05"
    },
    {
      "name": "@postgresql/mcp-server",
      "source": "npmjs.com",
      "type": "mcp-server",
      "installed": true,
      "added_by": "setup-team",
      "added_at": "2026-04-05"
    },
    {
      "name": "mongodb/agent-skills",
      "source": "github.com/mongodb/agent-skills",
      "type": "agent-skills",
      "installed": false,
      "added_by": "pipeline-orchestrator",
      "added_at": "2026-04-06",
      "note": "Discovered during MongoDB agent creation. Not installed — user chose custom build."
    }
  ]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Tool/plugin name |
| `source` | string | Where it comes from (marketplace name, npm, GitHub URL) |
| `type` | string | One of: `sdlc-framework`, `mcp-server`, `agent-skills`, `plugin`, `action` |
| `installed` | boolean | Whether the user chose to install this tool |
| `added_by` | string | What added this entry: `setup-team`, `pipeline-orchestrator`, `manual` |
| `added_at` | string | Date added (YYYY-MM-DD) |
| `note` | string (optional) | Context — why it was added, why not installed, etc. |

## Write Points

Three sources write to this file. No dedicated skill — each source appends to the `plugins` array directly.

### 1. Setup-team (Part 1 of #83)

**When:** After the user confirms the recommendation (step 8, install plugins).

**What it writes:**
- All SDLC framework plugins the user chose to install (`type: sdlc-framework`)
- All discovered technology-specific tools (`type: mcp-server`, `agent-skills`, etc.) with `installed: true/false` based on user's choice
- `added_by: "setup-team"`

### 2. Pipeline-orchestrator (#82)

**When:** After Phase 0 discovery finds tools and the user makes a decision.

**What it writes:**
- All tools found during discovery, with `installed: true` if user chose "use as-is" or "hybrid", `installed: false` if user chose "build custom"
- `added_by: "pipeline-orchestrator"`
- `note` explaining the user's decision

### 3. Manual

Users can edit the file directly to add tools they've found independently. Use `added_by: "manual"`.

## Write Logic

When writing to the file:

1. If `.sdlc/recommended-plugins.json` doesn't exist, create it with `version: "1.0"` and an empty `plugins` array
2. Read the existing file
3. For each new tool to add, check if it already exists (match on `name`)
   - If exists: update `installed` status if changed, don't duplicate
   - If not exists: append to the `plugins` array
4. Update `last_updated` to today's date
5. Write the file back

This is idempotent — running setup-team twice doesn't create duplicate entries.

## Files Changed

| File | Change |
|------|--------|
| `plugins/sdlc-core/skills/setup-team/SKILL.md` | Add step to write `.sdlc/recommended-plugins.json` after install confirmation |
| `skills/setup-team/SKILL.md` | Source copy, kept in sync |
| `agents/core/pipeline-orchestrator.md` | Add write to recommended-plugins.json in Phase 0 routing |
| `plugins/sdlc-team-common/agents/pipeline-orchestrator.md` | Plugin copy, kept in sync |

## Relationship to team-config.json

`.sdlc/team-config.json` records the **setup-time snapshot**: what project type was selected, what formation, what was installed. It's written once at setup.

`.sdlc/recommended-plugins.json` records the **evolving tool catalogue**: everything the project has evaluated over its lifetime, from any source. It grows as the team discovers and adds tools.

Different lifecycle, different file. Both live in `.sdlc/`.

## Success Criteria

1. `.sdlc/recommended-plugins.json` created by setup-team after first setup
2. Pipeline-orchestrator appends to it during discovery
3. Duplicate entries prevented (match on name)
4. `last_updated` reflects the most recent write
5. File is human-readable and editable

## What This Does NOT Do

- Create a dedicated skill for managing the library — writes are event-driven
- Enforce installation — `installed: false` entries are recommendations, not requirements
- Sync across machines — the file is project-local, committed to git
- Replace team-config.json — different purpose, different lifecycle
