# Knowledge Base Log

Append-only chronological record of ingest, query, and lint events.
Format: `## [YYYY-MM-DD] <operation> | <subject>`

Parseable with simple unix tools:
```
grep "^## \[" log.md | tail -10   # last 10 entries
grep "^## \[" log.md | grep "ingest"   # ingests only
```

---

## [2026-04-08] starter-pack | initial install

Mode: starter-pack-install
Files seeded: 3
- agentic-sdlc-options.md
- agent-suitability-rubric.md
- specification-formality-and-agent-performance.md
Index: shipped pre-built (placeholder hashes; will be replaced on first kb-rebuild-indexes)

This is example content shipped with the sdlc-knowledge-base plugin.
Replace or extend with library files relevant to your own problem space.
After editing, run `/sdlc-core:kb-rebuild-indexes` to regenerate the
shelf-index with real content hashes.
