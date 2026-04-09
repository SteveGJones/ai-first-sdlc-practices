---
name: kb-init
description: Initialise a project for knowledge base use. Appends the [Knowledge Base] section to the project's CLAUDE.md, creates the library/ directory structure, optionally seeds with three example library files from the Agentic SDLC research, and reports next steps. Run once after installing sdlc-knowledge-base.
disable-model-invocation: true
argument-hint: "[--with-starter-pack | --empty]"
---

# Initialise Knowledge Base

Set up a project to use the `sdlc-knowledge-base` plugin. This skill is idempotent — safe to run multiple times. It checks for existing setup before making changes.

## Arguments

- `--with-starter-pack` (default) — Seed `library/` with three example library files synthesised from the Agentic SDLC research programme: `agentic-sdlc-options.md`, `agent-suitability-rubric.md`, `specification-formality-and-agent-performance.md`. New users get a queryable library on first install and can see the format end-to-end. The starter content is example only and meant to be replaced or extended.
- `--empty` — Create the library directory structure but skip the starter pack. Use when you want a completely empty library to populate from scratch.

## Steps

### 1. Verify the plugin is installed

Check that the `sdlc-knowledge-base` plugin is available. If not, report:

```
sdlc-knowledge-base plugin is not installed. Run:
  /plugin install sdlc-knowledge-base@ai-first-sdlc
Then re-run this skill.
```

### 2. Check for existing CLAUDE.md

The schema section gets appended to the project's `CLAUDE.md`. If `CLAUDE.md` does not exist, report:

```
CLAUDE.md not found in the project root. Create it first (even an empty file is fine), then re-run this skill.
```

### 3. Check for existing knowledge base section

Read `CLAUDE.md` and look for an existing `## Knowledge Base` heading. If present, report:

```
[Knowledge Base] section already exists in CLAUDE.md. Skipping append.
If you want to reset the section, remove it manually and re-run this skill.
```

Then proceed to step 5 (directory creation) — it's still useful even if the section already exists.

### 4. Append the schema section template

Read the template from `templates/claude-md-section.md` (relative to this skill's directory; in plugin install this resolves to `${CLAUDE_PLUGIN_ROOT}/skills/kb-init/templates/claude-md-section.md`).

Strip the HTML comment block at the top of the template (the `<!-- ... -->` block explaining what the template is for).

Append the remaining content to `CLAUDE.md` with one blank line of separation.

Report what was added:

```
Appended [Knowledge Base] section to CLAUDE.md (XX lines).
```

### 5. Create the library directory structure

Check whether `library/` exists. If it does, skip the directory creation step (the starter pack copy in step 6 is still useful and safe).

If it does not, create:

```
library/
library/raw/
```

Plus a placeholder `library/.gitkeep` so git tracks the empty directory.

Report:

```
Created library/, library/raw/
```

### 6. Optionally seed with the starter pack

Default mode (`--with-starter-pack` or no argument): copy the starter pack from the plugin install directory into the project's `library/`. The starter pack files live at `${CLAUDE_PLUGIN_ROOT}/skills/kb-init/templates/starter-pack/library/`:

- `agentic-sdlc-options.md`
- `agent-suitability-rubric.md`
- `specification-formality-and-agent-performance.md`
- `_shelf-index.md` (with placeholder hashes)
- `log.md` (with starter header and install entry)

For each file, check whether the destination already exists in `library/`. If yes, skip (don't overwrite). If no, copy.

Report:

```
Seeded library/ with starter pack:
  Copied: agentic-sdlc-options.md
  Copied: agent-suitability-rubric.md
  Copied: specification-formality-and-agent-performance.md
  Copied: _shelf-index.md (placeholder hashes — run kb-rebuild-indexes to regenerate)
  Copied: log.md
```

After copying, recommend the user run `/sdlc-knowledge-base:kb-rebuild-indexes` to replace the placeholder hashes in the shelf-index with real ones based on the actual file contents.

`--empty` mode: skip the copy entirely. Create only the directory structure plus an empty `log.md` with the starter header:

```markdown
# Knowledge Base Log

Append-only chronological record of ingest, query, and lint events.
Format: `## [YYYY-MM-DD] <operation> | <subject>`
```

Report:

```
Created empty library structure (no starter pack).
Add raw sources to library/raw/ and run kb-ingest to populate.
```

### 7. Report next steps

Print a summary of what to do next.

For `--with-starter-pack` (default):

```
Knowledge base initialised with starter pack.

Next steps:
  1. Run /sdlc-knowledge-base:kb-rebuild-indexes to replace placeholder hashes with real ones
  2. Try a query: /sdlc-knowledge-base:kb-query "What does our research say about specification formality?"
  3. Review the example library files in library/ — replace or extend with content for your problem space
  4. Add your own raw sources to library/raw/ and run /sdlc-knowledge-base:kb-ingest <source> to integrate
  5. Read CLAUDE.md's new [Knowledge Base] section for the full conventions and workflow

For the format and design rationale, see:
  - The plugin README at plugins/sdlc-knowledge-base/README.md
  - The pattern document at docs/architecture/knowledge-base-pattern.md (in the framework repo)
```

For `--empty`:

```
Knowledge base initialised (empty).

Next steps:
  1. Add raw sources to library/raw/ (papers, articles, reports, conversation excerpts)
  2. Run /sdlc-knowledge-base:kb-ingest <source> to integrate them into structured library files
  3. After your first few library files exist, run /sdlc-knowledge-base:kb-rebuild-indexes to build the shelf-index
  4. Query the library with /sdlc-knowledge-base:kb-query "your question"
  5. Read CLAUDE.md's new [Knowledge Base] section for the full conventions and workflow

For the format and design rationale, see:
  - The plugin README at plugins/sdlc-knowledge-base/README.md
  - The pattern document at docs/architecture/knowledge-base-pattern.md (in the framework repo)
```

## What this skill does NOT do

- It does not write any library files. The user adds raw sources; `kb-ingest` produces library files from them.
- It does not build the shelf-index. `kb-rebuild-indexes` does that, after library files exist.
- It does not modify any agents or skills — they're shipped by the plugin install.
- It does not configure environment validation integration. That's an explicit opt-in the user adds to CLAUDE.md after reviewing the schema section.

## Idempotency

This skill is safe to run multiple times. On second invocation:
- Existing `[Knowledge Base]` section in CLAUDE.md is detected and not duplicated
- Existing `library/` directory is detected and not recreated
- The summary is still printed so the user knows where they are

## Error handling

- **CLAUDE.md missing** → preflight failure with guidance (step 2)
- **Plugin not installed** → preflight failure with install command (step 1)
- **Template file unreadable** → fail with explicit path so the user can check the install
- **Permission denied creating library/** → report the error and stop; do not continue with partial setup
