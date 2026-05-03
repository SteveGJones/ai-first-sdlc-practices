# CLAUDE-CONTEXT-knowledge-base.md

Knowledge base operations reference. Load this when working with kb-* skills, debugging KB issues, or designing new KB features.

## Agent-Only Rule (Critical)

**kb-query and kb-ingest operations MUST be dispatched to the `research-librarian` or `agent-knowledge-updater` agents via the Agent tool. Never run these operations inline in the main session.**

### Why this rule exists

KB query and ingest operations read multiple library files (400–2000 tokens each) plus the shelf-index and produce structured output — all of which fills the main session context window. Running 5–6 queries inline degrades context quality for everything that follows.

Root cause: In the Amkor AI Strategy engagement (2026-04), inline kb-query calls caused visible context degradation after ~5 queries. The `research-librarian` and `agent-knowledge-updater` agents isolate KB work into a sub-session that terminates after the operation completes, preserving the main session for everything else.

### Operation routing table

| Skill | How to invoke | Reason |
|---|---|---|
| `kb-query` | Agent tool → `research-librarian` | Reads 2–4 library files + shelf-index |
| `kb-ingest` | Agent tool → `agent-knowledge-updater` | Reads raw source + library files + writes |
| `kb-lint` | Agent tool → `research-librarian` | Reads all library files for consistency check |
| `kb-validate-citations` | Agent tool → `research-librarian` | Reads all library files + external checks |
| `kb-promote-answer-to-library` | Agent tool → `agent-knowledge-updater` | Writes to library — agent write-access only |
| `kb-rebuild-indexes` | Bash (script) | Pure Python, no library file content loaded into session |
| `kb-stats` | Bash (reads shelf-index header only) | Lightweight — timestamps + counts only |
| `kb-staleness-check` | Bash (reads timestamps) | Lightweight — no library file content read |
| `kb-audit-query` | Bash (reads audit.log) | Lightweight — small append-only log |
| `kb-init` | Inline OK | Writes CLAUDE.md section + empty dirs — no library content read |
| `kb-register-library` | Inline OK | Updates `~/.sdlc/global-libraries.json` — no library content read |

### Correct dispatch pattern

```
# Correct — dispatches to sub-session
Use the Agent tool: dispatch research-librarian with prompt:
"SCOPE: library/  SOURCE_HANDLE: local  Question: What does our research say about cycle time?"

# Wrong — fills main context
/sdlc-knowledge-base:kb-query "What does our research say about cycle time?"
```

The skill files begin with a guardrail reminding you of this rule.

## Shelf-Index Format

The shelf-index (`library/_shelf-index.md`) structure:

```markdown
<!-- format_version: 1 -->
<!-- last_rebuilt: 2026-05-03T10:00:00Z -->
<!-- library_handle: local -->
<!-- library_description: Local project library -->
# Knowledge Base Shelf-Index
...
## 1. agent-suitability-rubric.md

**Hash:** <sha256-hex-64chars>
**Terms:** rubric, dora, evaluation, sdlc, bdd, tdd, ...
**Facts:**
- Elite teams have cycle time <1 hour (DORA 2024)
- 14-dimension rubric, top 4 dimensions account for 35% of weight
**Links:** library/agentic-sdlc-options.md, library/specification-formality-and-agent-performance.md
```

Fields:
- `format_version` — shelf-index schema version (currently 1)
- `last_rebuilt` — ISO 8601 UTC when `kb-rebuild-indexes` last ran; consumed by staleness-check
- `library_handle` — handle in `~/.sdlc/global-libraries.json` (empty for local-only libraries)
- `library_description` — human-readable note, preserved across rebuilds
- `**Hash:**` — SHA-256 of raw file bytes; triggers re-extraction on change
- `**Terms:**` — comma-separated keywords; consumed by `priming.py` for cross-library biasing
- `**Facts:**` — up to 5 key findings; guides librarian's initial file selection
- `**Links:**` — cross-references to other library files and project artifacts

## Key Files

| File | Purpose |
|---|---|
| `library/_shelf-index.md` | Fast-scan catalogue — librarian reads this on every query |
| `library/log.md` | Chronological ingest and rebuild history |
| `library/audit.log` | Attribution and synthesis events (JSON lines) |
| `.sdlc/libraries.json` | Project-level activation of external libraries |
| `~/.sdlc/global-libraries.json` | User-scope registry of named external libraries |

## Rebuild Frequency

Run `/sdlc-knowledge-base:kb-rebuild-indexes` after:
- Adding or ingesting new library files
- Editing existing library files
- Deleting library files

The rebuild script (`build_shelf_index.py`) is pure Python with no LLM invocation — <1s for 500 files. Run it freely.
