# GitHub Issue Draft: coleam00/Archon

## Title

Bash node graph labels show "BASH Shell" instead of node id

## Description

When a workflow uses `bash:` nodes, the web UI DAG graph renders every
node as "BASH Shell" regardless of the node's `id` field. This makes
the graph structurally correct but semantically useless -- you cannot
tell which node is which without counting positions.

The CLI correctly uses the `id` field:
```
[security-review] Started
[architecture-review] Completed (2m10s)
[synthesise] Completed (6m8s)
```

But the web UI shows:
```
BASH Shell 2.0m | BASH Shell 2.2m | BASH Shell 2.0m | ...
```

Screenshot attached (7 nodes, all showing "BASH Shell").

## Expected behaviour

The graph should render the node `id` (or a `name` / `label` field if
one were supported) as the display label. For example:

```
security-review 2.0m | architecture-review 2.2m | synthesise 5.6m
```

## Context

We build workflows that preprocess `image:` nodes into `bash: docker run ...`
nodes for container-isolated execution. Each node has a meaningful `id`
(e.g. `security-review`, `architecture-review`, `synthesise`) but the
graph only shows the node type.

We attempted to add a `name:` field to bash nodes, but Archon's schema
validation rejects unknown fields and the graph fails to render entirely.

## Suggested fix

In the web UI graph renderer, use `node.id` as the primary display label
for bash nodes, falling back to the type label ("Bash") only if `id` is
absent. Alternatively, support a `name:` or `label:` field on all node
types that the UI renders when present.

## Versions

- Archon v0.3.6 (Homebrew compiled binary)
- macOS, Docker Desktop, Apple Silicon
