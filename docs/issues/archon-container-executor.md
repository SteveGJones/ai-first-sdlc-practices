# GitHub Issue Draft: coleam00/Archon

## Title

Feature request: native container executor for workflow nodes

## Description

Archon's `command:` nodes run Claude directly on the host. For teams
that need per-node container isolation (different plugins, agents, and
credentials per node), there is no native execution primitive -- the
only option is to use `bash:` nodes with `docker run`, which loses
Archon's rich node rendering, `idle_timeout`, and SSE event stream.

We propose a native `image:` or `container:` field on nodes that
tells Archon to execute the node's Claude session inside a specified
Docker container:

```yaml
nodes:
  - id: security-review
    command: sdlc-security-review
    image: sdlc-worker:security-team    # Archon runs this in a container
    timeout: 600000
```

## What this would enable

1. **Per-node container isolation** -- different Docker images per node,
   each with a scoped set of plugins and agents
2. **Rich UI labels** -- Archon renders the node id and command name
   instead of "BASH Shell"
3. **`idle_timeout` support** -- silence-based kill works because Archon
   manages the Claude process inside the container
4. **SSE event stream** -- container nodes emit proper start/complete
   events like command nodes
5. **Credential injection** -- Archon could accept a `credentials_mount:`
   field to bind-mount credentials into the container

## Current workaround

We preprocess workflow YAML before Archon sees it: a Python script
rewrites every `image:` node into a `bash: docker run ...` node with
security flags (`--cap-drop ALL`, `--no-new-privileges`, resource
limits). This works functionally but:

- Graph shows "BASH Shell" on every node (no semantic labels)
- `idle_timeout` (silence detection) is unavailable
- We implement our own three-tier termination (budget cap, inner
  timeout, outer timeout) to compensate
- The preprocessor is ~600 LOC that would be unnecessary with native
  container support

## Reference implementation

Our preprocessor (`preprocess_workflow.py::_build_docker_run`) is
essentially what the native executor would do:

```python
docker run --rm
  --cap-drop ALL
  --security-opt no-new-privileges
  --memory=4g --cpus=2
  -v {workspace}:/workspace
  -v {credentials}:/home/sdlc/.claude-creds/:ro
  -e "CLAUDE_PROMPT=$PROMPT"
  -e CLAUDE_TIMEOUT={inner_timeout}
  -e CLAUDE_MAX_BUDGET={budget}
  {image}
```

## Versions

- Archon v0.3.6
- Earlier ContainerProvider proposal: coleam00/Archon#1197 (different
  approach -- that was a provider-level patch; this is a node-level
  executor type)
