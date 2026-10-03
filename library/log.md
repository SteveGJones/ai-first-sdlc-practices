# Knowledge Base Log

Append-only chronological record of ingest, query, and lint events.
Format: `## [YYYY-MM-DD] <operation> | <subject>`

Parseable with simple unix tools:
```
grep "^## \[" log.md | tail -10   # last 10 entries
grep "^## \[" log.md | grep "ingest"   # ingests only
```

---

## [2026-04-10] kb-init | manual initialisation for EPIC #96 research

Mode: manual (plugin not installed as Claude Code plugin; KB structure created directly)
Reason: Need structured library for containerised worker research before plugin install

## [2026-04-10] ingest | archon-workflow-engine

Source: library/raw/archon-analysis-2026-04-10.md
Output: library/archon-workflow-engine.md
Method: Direct analysis of coleam00/Archon GitHub repository (source code inspection, README, Dockerfile, workflow definitions, isolation types, DAG executor)
Relevance: EPIC #96 (Containerised Claude Code Workers) — Archon is a workflow engine with parallel DAG execution, worktree isolation, and planned container provider support

## [2026-04-12] update | archon-workflow-engine — known bugs and workarounds

Two Archon bugs discovered during smoke testing:
1. ARM64 SDK subprocess hang: SDK defaults to bun for subprocess, hangs on ARM64 Docker. Fix: `executable: "node"` in SDK options. Conditional patch in Dockerfile.
2. Loop completion signal not detected: `until:` signal emitted but Archon reports max_iterations_reached. Reproduces consistently. No workaround yet.

Both confirmed across multiple test runs. Issue drafts at docs/issues/.

## [2026-04-10] update | archon-workflow-engine — integration model clarification

Updated library entry with key architectural insight: Archon and our SDLC plugins are different layers (process vs team). Archon orchestrates containers; each container runs a Claude Code session with our plugins installed. The Docker image is the integration point — no command-format bridge needed. Node prompts in Archon workflows reference our agents by name. This simplifies the integration model significantly.

## [2026-04-10] ingest | EPIC #96 research campaign outputs (R1-R5, S1-S3)

Source: agent_prompts/campaign-96-containerized-workers/research/
Output: 5 library files created
- claude-code-native-parallelism.md (from R1)
- multi-agent-framework-landscape.md (from R2)
- containerised-worker-economics.md (from R5 + S1 cost sections)
- task-delegation-and-merging.md (from R4)
- containerised-worker-recommendations.md (from S3)
Method: Systematic web research campaign (5 parallel research missions + 3 sequential syntheses)
