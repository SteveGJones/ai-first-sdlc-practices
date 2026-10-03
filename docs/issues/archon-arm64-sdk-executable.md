# GitHub Issue Draft: coleam00/Archon

**Title**: Claude SDK subprocess hangs on ARM64 Docker — needs `executable: "node"` in client options

**Labels**: bug, docker, arm64

---

### Environment

- Archon v0.3.5 running from source (`bun run`)
- Docker Desktop on Apple Silicon (ARM64 Linux containers)
- `oven/bun:latest` (1.3.12) for build, `node:22-slim` for production
- Claude Agent SDK `@anthropic-ai/claude-agent-sdk` (bundled)
- Non-root user (UID 1001)

### Problem

When running Archon in Docker on ARM64 (Apple Silicon), any operation that spawns a Claude session (`archon chat`, `archon workflow run`) hangs silently. Logs show `using_global_auth` and `starting_new_session`, then no further output — no response, no error. The session never produces output and eventually times out.

### Root Cause

The Claude Agent SDK auto-detects runtime and uses `bun` to spawn `cli.js` when running under Bun:

```javascript
// In SDK source (sdk.mjs)
executable: Q.executable ?? (T6() ? "bun" : "node")
```

Archon's Claude client (`packages/core/src/clients/claude.ts`) does not pass an `executable` option, so the SDK defaults to `bun`. On ARM64 Linux, Bun's `child_process` stdin pipe handling doesn't flush correctly when writing to the subprocess in `stream-json` mode. The subprocess never receives its input and hangs indefinitely.

**Key diagnostic evidence:**

| Test | Result |
|------|--------|
| `node cli.js --print -p "say OK"` (direct) | Works — returns "OK" |
| `spawn("node", ["cli.js", ...], {stdio: ["pipe","pipe","pipe"]})` | Hangs |
| `spawn("node", ["cli.js", ...], {stdio: ["ignore","pipe","pipe"]})` | Works |
| SDK `query()` without `executable` (defaults to `bun`) | Hangs |
| SDK `query()` with `executable: "node"` | **Works** — returns response in 2.4s |

The issue is Bun-as-parent reading/writing pipes to child processes on ARM64. When the SDK subprocess is forced to run on Node.js, the pipes work correctly.

### Proposed Fix

Add `executable: "node"` to the SDK options in `packages/core/src/clients/claude.ts`:

```diff
      const options: Options = {
        cwd,
        pathToClaudeCodeExecutable: cliPath,
+       executable: "node",
        env: requestOptions?.env
```

Node.js is already present in Docker images (Archon's own Dockerfile uses `node:22-slim` as the production base). Since `cli.js` is standard JavaScript, it runs identically on Node.js. This keeps Archon itself on Bun (for `bun:sqlite`, `.md` imports, etc.) while the SDK subprocess uses the stable Node.js runtime.

**Alternative approaches** (in order of preference):

1. Always use `executable: "node"` — simplest, no downside since cli.js is JS
2. Add a config option: `claude.executable` in `config.yaml` — lets users choose
3. Auto-detect: use `"node"` when running in Docker (check `/.dockerenv`) or on ARM64
4. Fix the pipe handling in Bun — upstream issue, not in Archon's control

### Workaround

Patch at Docker build time:
```dockerfile
RUN sed -i 's/pathToClaudeCodeExecutable: cliPath,/pathToClaudeCodeExecutable: cliPath,\n        executable: "node",/' \
    /opt/archon/packages/core/src/clients/claude.ts
```

### Verification

With the patch applied, full Archon workflow lifecycle works on ARM64 Docker:
- `archon chat` returns responses in ~2.4s
- `archon workflow run` executes parallel DAG nodes (true concurrency — 0ms delta between node starts)
- Fix-review loops complete autonomously
- 11/11 smoke test checks pass
