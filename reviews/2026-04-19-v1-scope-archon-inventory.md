# Archon v0.3.6 Capability Inventory

**Date**: 2026-04-19  
**Source**: `~/.archon-install/` (git ref `bed36ca`, complete checkout)  
**Compiled binary**: `~/.archon-bin/archon`  
**Analyst**: repository-knowledge-distiller (read-only analysis)  
**Purpose**: Evidence base for sdlc-workflows v1 scope review

---

## 1. Capability Inventory

### 1.1 Workflow Discovery

| Capability | Surface | File:line | Input / Output | Gotchas |
|---|---|---|---|---|
| Discover workflows from cwd | CLI / REST | `packages/workflows/src/workflow-discovery.ts:136` | `cwd: string` → `WorkflowLoadResult` (array of `WorkflowWithSource`) | Reads `.archon/workflows/` relative to cwd; recursively loads subdirs |
| Override bundled with project file | Internal | `workflow-discovery.ts:226-239` | filename-exact match | A repo file with the same filename as a bundled default overrides it; `source` stays `'bundled'` if it matches the bundled defaults subdir |
| Bundled defaults (binary build) | Internal | `workflow-discovery.ts:104-125` | Embedded map `BUNDLED_WORKFLOWS` (key: name, value: YAML string) | Generated at build time by `scripts/generate-bundled-defaults.ts`; 13 workflows bundled into the binary |
| Config-aware discovery | CLI / REST | `workflow-discovery.ts:291-307` | Reads `.archon/config.yaml`; `defaults.loadDefaultWorkflows: false` opts out of bundled | Config load failure falls back to `loadDefaults=true` |
| List workflows via REST | REST GET | `api.ts:158-172, 1667-1700` | `GET /api/workflows?cwd=<path>` → `{workflows:[{workflow,source}]}` | `cwd` must match a registered codebase path or be omitted (falls back to first registered codebase); no `cwd` + no registered codebases → empty list |

### 1.2 Workflow Execution

| Capability | Surface | File:line | Input / Output | Gotchas |
|---|---|---|---|---|
| CLI run | CLI | `packages/cli/src/commands/workflow.ts` | `archon workflow run <name>` | Discovers from `discoverWorkflowsWithConfig(cwd, config)`; DAG executor runs in-process on host |
| REST-triggered run | REST POST | `api.ts:541-561, 1703-1743` | `POST /api/workflows/{name}/run` body `{conversationId, message}` | Dispatches via `dispatchToOrchestrator`; requires pre-existing conversation; fires-and-forgets into background worker conversation |
| DAG topological execution | Library | `dag-executor.ts:405-445` | Kahn's algorithm; parallel layers via `Promise.allSettled` | Independent nodes in the same layer run concurrently; runtime cycle detection added as safety net after load-time check |
| Node types | Library | `schemas/dag-node.ts:284-291` | `CommandNode`, `PromptNode`, `BashNode`, `LoopNode`, `ApprovalNode`, `CancelNode`, `ScriptNode` | All discriminated by which field is present; validated via `dagNodeSchema` |
| Prompt node (inline) | Library | `dag-node.ts:161-173` | `prompt: string` | Inline prompt text, no file |
| Command node (file-backed) | Library | `dag-node.ts:147-159` | `command: string` | Loads `.archon/commands/<name>.md` at runtime |
| Bash node | Library | `dag-executor.ts:1035-1099` | `bash: string` → stdout captured as node output | `bash -c` subprocess; default 2-minute timeout configurable via `timeout: ms`; no AI session |
| Script node | Library | `dag-node.ts:199-214` | `script: string`, `runtime: 'bun'|'uv'`, `deps: string[]` | TypeScript or Python via bun/uv; AI-specific fields ignored |
| Loop node | Library | `dag-executor.ts` (loop handling); `schemas/loop.ts` | `loop: {prompt, until, max_iterations, fresh_context, until_bash?, interactive?, gate_message?}` | Completion detected by string match in output OR `until_bash` exit-0; interactive variant pauses for `/workflow approve` |
| Approval node | Library | `dag-node.ts:247-263` | `approval: {message, capture_response?, on_reject?}` | Pauses workflow; REST approve/reject endpoints resume it |
| Cancel node | Library | `dag-node.ts:269-280` | `cancel: string` (reason) | Terminates the run with the reason string |
| Resume failed run | CLI / REST | `executor.ts:322-448` | Auto-detects prior failed run for same workflow + cwd; skips completed nodes | Resume loads prior `node_completed` events from DB; `--resume` flag on CLI; REST `POST /api/workflows/runs/{id}/resume` just signals "ready" — next invocation auto-resumes |
| Per-node output references | Library | `dag-executor.ts:198-231` | `$node_id.output` or `$node_id.output.field` in prompts | Field access tries JSON parse; unavailable ref → empty string (with warn log) |
| Variable substitution | Library | `executor-shared.ts` (referenced) | `$RUN_ID`, `$USER_MESSAGE`, `$ARTIFACTS_DIR`, `$BASE_BRANCH`, `$DOCS_DIR`, `$CONTEXT` | `$BASE_BRANCH` throws at substitution time if absent and referenced |
| Per-node provider/model override | Library | `dag-executor.ts:245-361` | `provider:`, `model:` per node | Node-level overrides take precedence; provider inferred from model name when not set |
| Structured output (JSON schema) | Library | `dag-node.ts:121` | `output_format: {…json schema…}` | Provider-specific; warns user if provider doesn't return structured output |
| Effort/thinking control | Library | `dag-node.ts:132-133` | `effort: low|medium|high|max`, `thinking: adaptive|enabled|disabled` | Provider capability checked; silently ignored with warning if unsupported |
| MCP per node | Library | `dag-node.ts:127` | `mcp: string` (path) | Provider capability checked |
| Skills per node | Library | `dag-node.ts:128-131` | `skills: string[]` | Provider capability checked |
| Hooks per node | Library | `dag-node.ts:126` | `hooks: …` | Provider capability checked |
| Idle timeout | Library | `dag-executor.ts:585, 1027` | `idle_timeout: ms` per node; global default `STEP_IDLE_TIMEOUT_MS` | Node aborted if no output for idle period; logs warning to user |
| Retry | Library | `dag-node.ts:125`; `schemas/retry.ts` | `retry: {max_attempts, delay_ms?, on_error?: 'transient'|'all'}` | Default 2 retries on transient errors; not allowed on loop nodes |
| Cost cap | Library | `dag-executor.ts:757-766` | `maxBudgetUsd: number` per node | Throws if exceeded; `error_max_budget_usd` subtype |
| Sandbox | Library | `dag-node.ts:71-107` | `sandbox: {enabled, filesystem, network, …}` | Provider capability checked |
| Cancellation | REST POST | `api.ts:1789-1805` | `POST /api/workflows/runs/{runId}/cancel` | Sets DB status `cancelled`; executor polls DB every 10s and aborts |
| Approve/reject paused run | REST POST | `api.ts:1849-1957` | `POST /api/workflows/runs/{runId}/approve` body `{comment?}` | Writes `node_completed` event or signals interactive loop state |
| Workflow validation without saving | REST POST | `api.ts:174-193, 2081-2107` | `POST /api/workflows/validate` body `{definition}` | Returns validation errors; does not persist |
| Save/update workflow (REST) | REST PUT | `api.ts:215-233, 2191-2244` | `PUT /api/workflows/{name}?cwd=<path>` body `{definition}` | Serialises to YAML, writes to `<cwd>/.archon/workflows/<name>.yaml`; validates before writing |
| Delete workflow (REST) | REST DELETE | `api.ts:235-253, 2247-2285` | `DELETE /api/workflows/{name}?cwd=<path>` | Refuses to delete bundled defaults |

### 1.3 Worktree / Isolation Management

| Capability | Surface | File:line | Input / Output | Gotchas |
|---|---|---|---|---|
| Worktree creation | Internal / CLI | `packages/isolation/src/factory.ts`, `providers/` | Per-request isolation; types: `issue`, `pr`, `review`, `thread`, `task` | Provider type field exists for `container`, `vm`, `remote` but only `worktree` is implemented |
| Worktree list | CLI | `archon isolation list` | Lists tracked worktrees | Read from `remote_agent_isolation_environments` table |
| Worktree cleanup | CLI | `archon isolation cleanup` | Destroys stale/merged worktrees | Best-effort; returns `DestroyResult` with per-step success flags |
| Continue on branch | CLI | `archon continue <branch>` | `packages/cli/src/commands/continue.ts` | Resumes work in existing worktree with prior context |
| Complete branch lifecycle | CLI | `archon complete <branch>` | Full teardown | |
| Path lock guard | Library | `executor.ts:485-566` | Prevents concurrent runs on same `working_path` | 5-minute stale-pending window clears orphaned lock tokens |

**No container isolation.** `IsolationProviderType` includes `'container'` and `'vm'` in `isolation/src/types.ts:13` but only `worktree` is instantiated. The `IIsolationProvider` interface defines `create/destroy/get/list` but no container implementation is wired.

### 1.4 Conversation Management

| Capability | Surface | File:line | Input / Output | Gotchas |
|---|---|---|---|---|
| Create conversation | REST POST | `api.ts:275-..., 1070-1132` | `POST /api/conversations` body `{platformType, platformConversationId, …}` | Confirmed working in live probe |
| List conversations | REST GET | `api.ts:275, 1036` | `GET /api/conversations` | |
| Send message | REST POST | `api.ts:1199` | `POST /api/conversations/{id}/messages` | Routes to orchestrator |
| Dispatch (run workflow) | REST POST | `api.ts:541-561, 1703` | `POST /api/workflows/{name}/run` | Creates a hidden worker conversation; workflow runs in it |

### 1.5 Credential Handling

| Capability | Surface | File:line | Input / Output | Gotchas |
|---|---|---|---|---|
| Setup wizard | CLI | `packages/cli/src/commands/setup.ts` | Interactive; writes `~/.archon/config.yaml` | Single-tier: API key → config file |
| Per-codebase env vars (REST) | REST | `api.ts:1595-1635` | `GET/POST/DELETE /api/codebases/{id}/env-vars` | Merged into `Options.env` on Claude SDK calls; encrypted-at-rest not mentioned in source |
| Config env var injection | Library | `executor.ts:250-251` | `codebaseId` → `getCodebaseEnvVars` → merged into `WorkflowConfig.envVars` | Available in workflow nodes via `env:` injection |
| `.env` file | Server startup | `server/src/index.ts:13-35` | Reads `~/.archon/.env` and repo-root `.env` | CWD env stripping applied first (`strip-cwd-env-boot`) |

### 1.6 Status / Observability

| Capability | Surface | File:line | Input / Output | Gotchas |
|---|---|---|---|---|
| Active runs | CLI | `archon workflow status` | Lists pending/running runs | Source: DB query |
| Dashboard runs (REST) | REST GET | `api.ts:563-576, 1747-1786` | `GET /api/dashboard/runs?status=&codebaseId=&search=&after=&before=&limit=&offset=` | Paginated; max 200 per page; joined run + enrichment data |
| Workflow run list | REST GET | `api.ts:594-607, 1981-2016` | `GET /api/workflows/runs` | |
| Single run detail | REST GET | `api.ts:2032-2079` | `GET /api/workflows/runs/{runId}` | |
| Run by worker platform ID | REST GET | `api.ts:578-592, 2017-2031` | `GET /api/workflows/runs/by-worker/{platformId}` | Looks up by worker conversation platform ID |
| Artifacts | REST GET | `api.ts:2356` | `GET /api/artifacts/{runId}/*` | Serves files from run artifacts directory |
| Health | REST GET | `api.ts:2528` | `GET /api/health` | |
| Update check | REST GET | `api.ts:2554` | `GET /api/update-check` | |
| File logs | Library | `logger.ts` (referenced) | Written to `<logDir>/` per run | `logNodeStart`, `logNodeComplete`, `logNodeError`, `logAssistant`, `logTool`, `logWorkflowComplete`, `logWorkflowError` |

### 1.7 Event Streaming (SSE)

| Capability | Surface | File:line | Input / Output | Gotchas |
|---|---|---|---|---|
| Dashboard SSE | REST GET | `api.ts:1374-1407` | `GET /api/stream/__dashboard__` | Heartbeat every 30s; multiplexed across all workflow runs |
| Conversation SSE | REST GET | `api.ts:1410-1449` | `GET /api/stream/:conversationId` | Per-conversation stream; heartbeat every 30s |
| Events emitted to SSE | Library | `executor.ts:617-623; dag-executor.ts:491-496` | `workflow_started`, `workflow_failed`, `node_started`, `node_completed`, `node_failed`, `tool_started`, `tool_completed`, `workflow_dispatch` | Events flow via `WorkflowEventEmitter` → `WebAdapter` → SSE streams |

**Gate**: SSE only receives events from runs executed via the serve process. CLI-launched runs (`archon workflow run`) never register with `WorkflowEventEmitter` in the serve process — they are separate OS processes.

### 1.8 Node Executor Model

All AI nodes call `deps.getAgentProvider(provider)` → provider's `sendQuery(prompt, cwd, sessionId, options)` and consume an async generator of typed messages (`assistant`, `tool`, `tool_result`, `result`, `system`, `rate_limit`).

**Key dispatch facts** (confirmed in source):

- Provider selected per-node via `resolveNodeProviderAndModel()` (`dag-executor.ts:245-361`). Each node can specify `provider:` and `model:` independently.
- This IS per-node provider dispatch. The claim "no per-node executor dispatch" was **imprecise** — there is per-node provider selection. What does NOT exist is per-node process/container dispatch; all nodes run in-process on the host.
- Session continuity: `context: 'shared'` passes `sessionId` forward; `context: 'fresh'` (or parallel nodes) always pass `resumeSessionId = undefined`. A fork (`shouldForkSession = resumeSessionId !== undefined`) leaves the source session untouched.

### 1.9 Credential Model (Config Hierarchy)

Four layers, later overrides earlier (`config-loader.ts:1-9`):

1. Built-in defaults (hardcoded in `getDefaults()`)
2. Global config (`~/.archon/config.yaml`)
3. Repository config (`.archon/config.yaml` relative to cwd)
4. Environment variables

Environment variables recognised by the config system:

| Env var | Effect | Source |
|---|---|---|
| `ARCHON_HOME` | Override `~/.archon` home dir | `archon-paths.ts:61` |
| `ARCHON_DOCKER=true` | Force Docker path mode | `archon-paths.ts:47` |
| `WORKSPACE_PATH` | Docker workspace path | `archon-paths.ts:45` |
| `PORT` | Override server port (default 3090) | `port-allocation.ts:38` |
| `DEFAULT_AI_ASSISTANT` | Override AI provider | `config-loader.ts:282` |
| `BOT_DISPLAY_NAME` | Bot display name | `config-loader.ts:276` |
| `TELEGRAM_STREAMING_MODE` | `stream` or `batch` | `config-loader.ts:296` |
| `DISCORD_STREAMING_MODE` | `stream` or `batch` | `config-loader.ts:301` |
| `SLACK_STREAMING_MODE` | `stream` or `batch` | `config-loader.ts:306` |
| `MAX_CONCURRENT_CONVERSATIONS` | Concurrency cap | `config-loader.ts:315` |
| `ARCHON_TELEMETRY_DISABLED=1` | Disable telemetry | `telemetry.ts:71` |
| `DO_NOT_TRACK=1` | Disable telemetry | `telemetry.ts:72` |
| `CLAUDE_API_KEY` | Claude API key | `server/src/index.ts:48` |
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude OAuth token | `server/src/index.ts:49` |
| `CLAUDE_USE_GLOBAL_AUTH` | Use global Claude auth | `server/src/index.ts:50-52` |

### 1.10 SQLite Schema

Database: `~/.archon/archon.db` (SQLite in standalone; PostgreSQL supported via same pool interface).

Canonical schema in `migrations/000_combined.sql`:

| Table | Columns (key ones) | Purpose |
|---|---|---|
| `remote_agent_codebases` | `id`, `name`, `repository_url`, `default_cwd`, `ai_assistant_type`, `commands` (JSONB) | Repository registry |
| `remote_agent_codebase_env_vars` | `codebase_id`, `key`, `value` | Per-project env var store |
| `remote_agent_conversations` | `id`, `platform_type`, `platform_conversation_id`, `codebase_id`, `cwd`, `isolation_env_id`, `hidden` | Chat session tracking |
| `remote_agent_sessions` | `conversation_id`, `assistant_session_id`, `active`, `parent_session_id` | AI session continuity |
| `remote_agent_isolation_environments` | `codebase_id`, `workflow_type`, `workflow_id`, `provider`, `working_path`, `branch_name`, `status` | Worktree lifecycle |
| `remote_agent_workflow_runs` | `workflow_name`, `conversation_id`, `codebase_id`, `status`, `user_message`, `metadata`, `working_path`, `parent_conversation_id` | Run state + resume data |
| `remote_agent_workflow_events` | `workflow_run_id`, `event_type`, `step_name`, `data` (JSONB) | Per-node event log |
| `remote_agent_messages` | `conversation_id`, `role`, `content`, `metadata` | Message history |

---

## 2. Extensibility Surfaces

### Config files Archon reads

- `~/.archon/config.yaml` — global: `defaultAssistant`, `botName`, `streaming`, `paths`, `concurrency`, `assistants` (`config-loader.ts:177`)
- `.archon/config.yaml` — per-repo: `assistant`, `commands.folder`, `defaults.loadDefaultWorkflows`, `env`, `worktree` (for isolation) (`config-loader.ts:206`)
- `.archon/workflows/*.yaml` — project-defined workflows (recursive subdirectory scan)
- `.archon/commands/*.md` — project-defined command prompts
- `~/.archon/.env` and repo-root `.env` — environment variables loaded at server startup

### Provider / Plugin patterns

Providers registered via `registerBuiltinProviders()` (`@archon/providers`). The registry pattern (`isRegisteredProvider`, `getRegisteredProviders`) suggests third-party providers could be registered, but no documented extension point or lifecycle hook is exposed in v0.3.6.

Isolation provider is instantiated via `getIsolationProvider()` returning the worktree implementation. The `IIsolationProvider` interface (`isolation/src/types.ts:168-187`) defines `create/destroy/get/list` — a container provider would implement this interface, but none is wired.

### Environment variables that change behaviour (complete list)

See Section 1.9 above.

### Hook / callback systems

No general-purpose hook or plugin registration system is exposed externally. The serve process uses an internal `WorkflowEventEmitter` to route events to SSE, but this is not a public extension point.

Workflow YAML supports `hooks:` per node (`dag-node.ts:126`) — these are passed to the Claude SDK (`nodeConfig.hooks`) and are provider-specific Claude Code hooks, not server hooks.

---

## 3. Known Limitations with Source Evidence

### 3.1 "No per-node executor dispatch" — REFUTED (partially)

**What is true**: There is no per-node *process* or *container* dispatch. All nodes run in-process on the host machine.

**What is false as stated**: Archon does support per-node *provider and model* selection. `resolveNodeProviderAndModel()` in `dag-executor.ts:245-361` reads `node.provider` and `node.model` and resolves the appropriate AI client. Each node can use a different AI provider (Claude vs Codex) and model.

**What we actually needed**: Container dispatch — routing a node to a Docker container. Archon has no mechanism for this. Our `preprocess_workflow.py` transforms `image:` nodes into `bash: docker run` nodes to fill this gap. That transformation is genuinely novel; it is not a re-implementation of something Archon provides.

### 3.2 "Serve doesn't register CLI-discovered workflows" — TRUE but imprecise

**True part**: `archon serve` uses the same `discoverWorkflowsWithConfig()` function (`api.ts:1689`), which reads `.archon/workflows/` from a registered codebase's `default_cwd`. So project-local YAMLs **do** appear in `GET /api/workflows` — IF the codebase is registered via the UI.

**The real gap confirmed live**: `POST /api/workflows/<cli-discovered-name>` returns 404 because there is no POST route — only `POST /api/workflows/{name}/run`. And `POST /api/workflows/{name}/run` dispatches via `dispatchToOrchestrator` which requires a pre-existing conversation, not a standalone run trigger.

**Why CLI-launched runs don't appear in the UI**: The CLI and serve are separate processes. The CLI's `executeWorkflow()` call writes to `~/.archon/archon.db` (which the serve process also reads), so run records eventually appear in `GET /api/workflows/runs`. But SSE events from CLI runs never reach the serve's `WorkflowEventEmitter` — they are emitted into the CLI process's in-memory emitter and go nowhere. The UI's "DAG graph" and "live SSE" views are effectively only useful for serve-initiated runs.

**Catalog loading code** (`api.ts:1689`):
```
const result = await discoverWorkflowsWithConfig(workingDir, loadConfig);
```
`workingDir` is derived from `cwd` query param (must match a registered codebase) or from the first registered codebase's `default_cwd`. There is no in-memory catalog; discovery is on-demand per request.

### 3.3 "SSE emits only for server-initiated runs" — TRUE

**Gate location** (`executor.ts:615-623`):
```typescript
const emitter = getWorkflowEventEmitter();
emitter.registerRun(workflowRun.id, conversationId);
emitter.emit({ type: 'workflow_started', ... });
```
`getWorkflowEventEmitter()` returns an in-process singleton. CLI processes have their own singleton that is never connected to the serve process's singleton. There is no inter-process event bridge. The `WebAdapter`'s `setupEventBridge()` (`orchestrator.ts:337`) bridges worker-conversation events to parent-conversation SSE — but both worker and parent are conversations within the same serve process.

### 3.4 "No POST endpoint for workflow registration" — TRUE

Confirmed from route table (`api.ts:158-253`):

```
GET  /api/workflows                     -- list (discovery on demand)
POST /api/workflows/validate            -- validate only, no persist
GET  /api/workflows/{name}              -- fetch single
PUT  /api/workflows/{name}              -- save/create to disk
DELETE /api/workflows/{name}            -- delete from disk
POST /api/workflows/{name}/run          -- run via orchestrator
```

There is a `PUT /api/workflows/{name}` which creates or updates a workflow YAML on disk (`api.ts:2191-2244`). This is a genuine REST save endpoint — not just a discovery endpoint. We missed this in our pre-review. A caller can `PUT` a YAML definition and immediately `POST /{name}/run` it. However, the PUT writes to `<cwd>/.archon/workflows/<name>.yaml` — it requires a registered codebase and a writable filesystem at that path.

### 3.5 `app_defaults_not_available` on every binary install — TRUE

**Why** (`archon-paths.ts:381-394`): `validateAppDefaultsPaths()` calls `getDefaultWorkflowsPath()` which returns:
```
{repo_root}/.archon/workflows/defaults
```
where `repo_root` is computed from `import.meta.dir` — the source file's location at build time. In a compiled binary, `import.meta.dir` is frozen to the GitHub Actions runner path (`/Users/runner/work/Archon/Archon/packages/paths/src`). That directory does not exist on any user machine.

**Why it is benign in binary mode**: `workflow-discovery.ts:147-154` branches on `isBinaryBuild()` and loads bundled workflows from the embedded `BUNDLED_WORKFLOWS` map instead of the filesystem. The warning fires before that branch executes, creating log noise that is not actionable.

### 3.6 Additional limitations found

**Port allocation for worktree paths** (`port-allocation.ts:37-61`): When the serve process's cwd is a worktree path (detected via `isWorktreePath()`), it allocates a deterministic hash-based port in range 3190-4089 instead of 3090. This means a containerised Archon instance run from within a worktree uses an unpredictable port — a user must set `PORT` explicitly to avoid this.

**Codebase registration required for REST workflow access** (`api.ts:1673-1686`): `GET /api/workflows` rejects unregistered cwd values. A fresh project whose codebase is not yet registered via the UI returns an empty workflow list even if `.archon/workflows/` contains valid YAMLs.

**No POST /api/workflows (bare)**: There is no route that accepts a raw workflow definition for in-memory-only registration. All saves go to disk. There is no concept of an ephemeral workflow.

**Approval-resume is indirect** (`api.ts:1808-1828`): `POST /api/workflows/runs/{id}/resume` does NOT restart execution — it returns a message telling the caller to "re-run the workflow to auto-resume." The actual resume happens when `executeWorkflow` detects a prior failed run via `store.findResumableRun()`. This is an internal auto-detect, not a direct API trigger.

---

## 4. Capabilities We Are Probably Re-implementing

### 4.1 `workflows_status_query.py` vs REST API

| Our code | Archon native |
|---|---|
| `scripts/workflows_status_query.py` | `GET /api/workflows/runs` (`api.ts:594-607`) |
| SQLite fallback when serve not running | No equivalent — REST only |
| `GET /api/workflows/runs/{runId}` for detail | `GET /api/workflows/runs/{runId}` (`api.ts:2032-2079`) — identical |

**Assessment**: The REST path is a genuine re-implementation of something Archon provides, but the SQLite fallback path is not — Archon does not expose historical runs when serve is not running. The value of our script is the SQLite fallback, not the REST call. The REST fetch could be replaced with a direct `curl` in the skill.

### 4.2 `sse_stream_follow.py` vs native CLI streaming

| Our code | Archon native |
|---|---|
| `scripts/sse_stream_follow.py` — connects to `/api/stream/__dashboard__` | CLI: `archon workflow run` streams to stderr directly |

**Assessment**: For CLI-launched runs (which is how `workflows-run` fires Archon), the CLI already streams node output to stderr in real time. `sse_stream_follow.py` targets the serve SSE endpoint which does NOT receive events from CLI-launched runs (see §3.3). The script has no effect in our current integration shape. This is a candidate for removal.

### 4.3 Workflow YAML authoring vs `PUT /api/workflows/{name}`

| Our code | Archon native |
|---|---|
| `author-workflow` skill — conversational YAML generator | `PUT /api/workflows/{name}` writes YAML to disk; UI has a visual DAG builder |

**Assessment**: The UI's DAG builder is visual; `author-workflow` is conversational/text-based and can run without the serve process. These serve different audiences. Not a re-implementation — complementary shapes.

### 4.4 `workflows-setup` skill vs `archon setup`

| Our code | Archon native |
|---|---|
| `workflows-setup` — installs archon, builds Docker images, scaffolds `.archon/` | `archon setup` — interactive wizard for `~/.archon/config.yaml` only |

**Assessment**: `archon setup` covers only credential configuration. Our skill additionally builds Docker images and scaffolds the `.archon/workflows/` and `.archon/commands/` directories. The scaffold portion partially overlaps with what `archon setup` could be extended to do, but currently does not. Not a meaningful re-implementation.

### 4.5 `workflows-status` skill vs `archon workflow status`

| Our code | Archon native |
|---|---|
| `workflows-status` skill — human-readable summary, optionally forwards to `workflows_status_query.py` | `archon workflow status` — lists active runs; `GET /api/workflows/runs` via serve |

**Assessment**: `archon workflow status` shows only active (pending/running) runs with no history. Our skill adds historical runs (via REST or SQLite fallback). The skill wrapper around a REST call is thin overhead.

### 4.6 Loop node vs `loop.stages:` primitive

| Our code | Archon native |
|---|---|
| `loop.stages:` in our bundled YAMLs — a structured multi-stage schema that drives a sequence of `archon workflow run` invocations | Archon's `loop:` node — AI prompt in a loop until completion signal |

**Assessment**: Completely different concepts. Archon's loop is an AI loop within one workflow run. Our `loop.stages:` is a multi-workflow-run cycle (designer → dev → review → repeat). No overlap.

### 4.7 `resolve_credentials.py` vs Archon credential model

| Our code | Archon native |
|---|---|
| 3-tier fallback: macOS Keychain → Docker volume → `~/.archon/config.yaml` | `archon setup` writes `~/.archon/config.yaml` (1 tier) |

**Assessment**: Our resolver handles the containerised use case where credentials must be injected into Docker containers without exposing them in environment variables. Archon's model has no container-aware credential path. Not a re-implementation.

---

## Summary of Confirmed Findings vs Pre-Review Hypotheses

| Hypothesis | Verdict | Evidence |
|---|---|---|
| "No per-node executor dispatch" | REFUTED (per-node provider/model: yes; per-node process/container: no) | `dag-executor.ts:245-361` |
| "Serve doesn't register CLI-discovered workflows" | TRUE for SSE; FALSE for REST if codebase registered | `api.ts:1689`; SSE gate `executor.ts:615-623` |
| "SSE emits only for server-initiated runs" | TRUE | In-process `WorkflowEventEmitter`; no IPC bridge |
| "No POST endpoint for workflow registration" | TRUE for in-memory; FALSE: PUT exists for disk-based save | `api.ts:215-233, 2191-2244` |
| "app_defaults_not_available fires because hardcoded path" | TRUE | `archon-paths.ts:183-198`; `import.meta.dir` frozen at build time |
| "POST /api/workflows returns 404" | TRUE (bare POST); `POST /api/workflows/{name}/run` exists | Route table `api.ts:541-561` |

**Newly discovered** (not in pre-review brief):

- `PUT /api/workflows/{name}` exists and saves YAML to disk — we did not know about this endpoint
- Port auto-allocation based on cwd hash (3190-4089 range for worktrees) — `PORT` env var required for predictable port in containers
- Codebase registration required before REST workflow discovery will return results
- `POST /api/workflows/runs/{id}/resume` is informational only — actual resume is triggered by re-running the workflow, not by this endpoint
- `sse_stream_follow.py` likely has no effect in CLI-launch integration shape — CLI runs do not emit to serve's SSE

