# Architecture Design: `agent-delegation` — Haiku wrapper agents for external agentic CLIs (codex, agy)

**Issue:** #232 · **Repo:** `ai-first-sdlc-practices` · **Pattern family:** `command-delegation` (full transcript to durable `./tmp/` log; compact slice back to caller) · **Status:** Design (Fable-tier spike, pending review) · **Date:** 2026-07-23

> Provenance: produced by a Fable-tier architecture spike that probed both CLIs' read-only `--help`/state surfaces on the target machine (codex v0.145.0, agy v1.1.5). A separate Fable-tier adversarial review of this document precedes implementation.

## 1. Overview

Two Haiku subagents — `codex-runner` and `agy-runner` — let a Claude Code session delegate prompts to locally installed external agentic CLIs (OpenAI Codex CLI v0.145.0, Antigravity CLI v1.1.5). Expensive reasoning happens inside the external CLI; the Haiku wrapper only orchestrates, extracts, and reports. Both agents present **one identical caller-facing contract** across two continuity modes:

- **Mode A `resume`** — stateless between calls; each turn is a fresh CLI invocation resuming a saved session id.
- **Mode B `persistent`** — one long-lived external process held open for the subagent's life, fed successive prompts.

**Core design decision:** all process plumbing (spawn, FIFO feed, framing detection, teardown, reaping) lives in a **deterministic shell helper shipped with the plugin** (`${CLAUDE_PLUGIN_ROOT}/scripts/extdel.sh` with subcommands `start | prompt | status | stop | reap | recover`). The Haiku agent never composes FIFO/JSON-RPC plumbing ad hoc — it calls the script and interprets its structured output. Haiku is cheap and fallible; the mechanism must not depend on it improvising `mkfifo` incantations correctly.

**Second core decision (the Mode B crux, resolved):** a Claude Code subagent's only durable state between Bash calls is the filesystem — a foreground child dies with each Bash shell. Therefore Mode B's held process is a **detached daemon** (spawned once via `nohup setsid`, disowned from the Bash shell's process group), addressed on every subsequent turn through **files under `./tmp/`**: a named FIFO for input, an append-only log for output, and pid files for lifecycle. For codex this daemon is `codex mcp-server` (stdio JSON-RPC, machine-framed). For agy, holding `agy -i` open is feasible only via a pty with heuristic completion detection — **we reject it as too fragile** and implement agy's `persistent` mode as *resume-under-the-hood* (same contract, documented behavior; see §3.2 for why this loses almost nothing).

### Ground truth verified in the spike (v0.145.0 / v1.1.5)

| Fact | Source |
|---|---|
| `codex exec [PROMPT]` with `--json` (JSONL events to stdout) and `-o/--output-last-message FILE` (final agent message written to a file) | `codex exec --help` |
| `codex exec resume [SESSION_ID] [PROMPT]` accepts UUID or thread name, plus `--last`, `--json`, `-o` | `codex exec resume --help` |
| `codex mcp-server` — "Start Codex as an MCP server (stdio)" — stable subcommand, `-c` overrides | `codex mcp-server --help` |
| `codex app-server` — experimental; `daemon start/stop/restart/version`, `proxy` (stdio→control socket), `--listen unix://PATH` | `codex app-server --help`, `daemon --help` |
| `codex exec-server` — EXPERIMENTAL, ws-first | `codex exec-server --help` |
| `codex login status` exists (read-only auth probe) | `codex login status --help` |
| Codex sessions persist at `~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl`; first line is `{"type":"session_meta","payload":{"id":"<uuid>",...,"cwd":...}}` | inspected on disk |
| `codex exec` sandbox: `-s read-only|workspace-write|danger-full-access`; `--dangerously-bypass-approvals-and-sandbox`; `-C/--cd`, `--add-dir`, `--ephemeral`, `--output-schema` | `codex exec --help` |
| `agy --print/-p`, `--continue/-c`, `--conversation <ID>`, `--prompt-interactive/-i`, `--print-timeout` (default 5m), `--agent`, `--model`, `--effort low|medium|high`, `--mode accept-edits|plan`, `--sandbox`, `--dangerously-skip-permissions`, `--add-dir`, `--new-project`, `--project`, `--log-file` | `agy help` |
| agy state at `~/.gemini/antigravity-cli/`: `cache/last_conversations.json` = **map of absolute cwd → most-recent conversation UUID**; `cache/conversation_metadata.json` = per-conversation `{ID, Preview, NumSteps, UpdatedAt, WorkspaceURIs, ProjectID}`; `conversations/<uuid>.db` | inspected on disk |
| `agy models` lists e.g. `gemini-3.1-pro-high`, `claude-opus-4-6-thinking`, `gpt-oss-120b-medium`; `agy agent` currently lists none | ran both |

**Not verified (implementation-time TODOs, cheap and token-free):** exact codex MCP tool names/schemas (expected: a `codex` tool starting a conversation and a `codex-reply`/continue tool taking `conversationId` — verify with an `initialize` + `tools/list` handshake, which costs no model tokens); whether `agy --print` auto-denies or hangs on permission requests in its default posture; whether agy prints the conversation id anywhere on stdout/stderr/log (we have the cache-file mechanism regardless).

---

## 2. Mode A — id-based resume (per CLI)

No process survives between the subagent's Bash calls; continuity lives entirely in the external CLI's own session store. Each turn = one fresh, self-terminating CLI invocation.

### 2.1 File layout (shared by both modes)

All state under the project-relative `./tmp/` (repo policy: never `/tmp`):

```
./tmp/agent-delegation/
  <HANDLE>/                      # HANDLE = <cli>-<mode>-<UTCts>-<rand6>, e.g. codex-resume-2026-07-23T21-04-11Z-a3f9c1
    meta.json                    # {handle, cli, mode, cwd, model, effort, posture, created, pid?, session_id?}
    session.id                   # external session/conversation UUID, written after turn 1
    turn-001.events.jsonl        # full JSONL / raw output for turn 1  (the durable "full log")
    turn-001.last-message.txt    # final answer only (codex -o target / agy stdout)
    turn-001.stderr.log
    turn-002.events.jsonl        # ... one triple per turn
    ...
    # Mode B extras (codex only): in.fifo, holder.pid, daemon.pid, watchdog.pid, out.jsonl, activity.touch
  .locks/                        # mkdir-based mutexes (see §5.2)
```

### 2.2 Mode A — codex

**Turn 1 (start):**
```bash
timeout "${TIMEOUT_S}" codex exec \
  --json -o "$DIR/turn-001.last-message.txt" \
  -C "$CWD" ${ADD_DIRS/#/--add-dir } \
  -s "$SANDBOX" ${MODEL:+-m "$MODEL"} \
  ${EFFORT:+-c model_reasoning_effort="\"$EFFORT\""} \
  --color never --skip-git-repo-check \
  - < "$DIR/turn-001.prompt.txt" \
  > "$DIR/turn-001.events.jsonl" 2> "$DIR/turn-001.stderr.log"
echo "EXIT_CODE=$?"
```
Prompt is passed via stdin (`-`) from a file the wrapper writes first — avoids all shell-quoting hazards with multi-line prompts.

**Session-id capture** (belt and braces, in order):
1. `grep -m1 -oE '"(session_id|thread_id|conversation_id)"\s*:\s*"[0-9a-f-]{36}"' turn-001.events.jsonl` — the `--json` event stream carries the id in its first events.
2. Fallback: newest `~/.codex/sessions/$(date -u +%Y/%m/%d)/rollout-*.jsonl` whose first-line `session_meta.payload.cwd == $CWD` and mtime ≥ turn start — the id is `payload.id` (and is embedded in the filename). Verified format on disk.

Write it to `$DIR/session.id` and `meta.json`.

**Turn N (resume):**
```bash
timeout "${TIMEOUT_S}" codex exec resume "$(cat "$DIR/session.id")" \
  --json -o "$DIR/turn-00N.last-message.txt" \
  -s "$SANDBOX" --color never --skip-git-repo-check \
  - < "$DIR/turn-00N.prompt.txt" \
  > "$DIR/turn-00N.events.jsonl" 2> "$DIR/turn-00N.stderr.log"
```
Never use `resume --last` — it races under fan-out (see §5).

**Note (macOS):** `timeout` is GNU coreutils (`gtimeout` if only Homebrew-installed). `extdel.sh` detects `timeout`/`gtimeout` and falls back to a `perl -e 'alarm ...'` wrapper — do not assume `timeout` exists on darwin.

### 2.3 Mode A — agy

**Turn 1 (start):**
```bash
T0=$(date +%s)
( cd "$CWD" && agy --print "$(cat "$DIR/turn-001.prompt.txt")" \
    ${MODEL:+--model "$MODEL"} ${EFFORT:+--effort "$EFFORT"} \
    ${AGENT:+--agent "$AGENT"} \
    $POSTURE_FLAGS \
    ${ADD_DIRS/#/--add-dir } \
    --print-timeout "${TIMEOUT_S}s" \
    --log-file "$DIR/turn-001.agy-cli.log" \
) > "$DIR/turn-001.last-message.txt" 2> "$DIR/turn-001.stderr.log"
echo "EXIT_CODE=$?"
```
agy runs *in* `$CWD` (agy has no `-C` flag; workspace = cwd). `--print-timeout` gives us a native timeout; we still wrap in `timeout $((TIMEOUT_S+30))` as a hard backstop. (If agy `--print` supports `-`/stdin, prefer that over argv to avoid quoting hazards — verify at implementation.)

**Conversation-id capture** (agy makes this non-obvious; solved via verified state files):
1. **Primary:** read `~/.gemini/antigravity-cli/cache/last_conversations.json` and take the value keyed by the absolute `$CWD`. Verified: this file is exactly `{ "<abs cwd>": "<conversation-uuid>", ... }`.
2. **Cross-check (mandatory under fan-out):** in `~/.gemini/antigravity-cli/cache/conversation_metadata.json`, confirm that conversation's `UpdatedAt` ≥ turn start time `T0` and `WorkspaceURIs` contains `file://$CWD`. If the cross-check fails (another session in the same cwd won the race), fall back to: newest conversation in the metadata file with matching `WorkspaceURIs` and `UpdatedAt ∈ [T0, now]` that is **not** already claimed by another handle (claimed ids are discoverable as `./tmp/agent-delegation/*/session.id`).
3. **Race prevention rather than cure:** first calls in the same cwd are serialized with a `mkdir` lock (§5.2), making 1+2 deterministic.

Write to `$DIR/session.id`.

**Turn N (resume):**
```bash
( cd "$CWD" && agy --conversation "$(cat "$DIR/session.id")" \
    --print "$(cat "$DIR/turn-00N.prompt.txt")" \
    $POSTURE_FLAGS --print-timeout "${TIMEOUT_S}s" \
    --log-file "$DIR/turn-00N.agy-cli.log" \
) > "$DIR/turn-00N.last-message.txt" 2> "$DIR/turn-00N.stderr.log"
```
Never use `--continue` — same fan-out race as codex `--last`.

---

## 3. Mode B — persistent long-lived process (per CLI)

### 3.0 The process-holding problem, stated precisely

The wrapper subagent's Bash tool gives it a fresh shell per call; any foreground child and any shell-job (`&`, `coproc`) tied to that shell's lifetime is gone by the next turn. The subagent's only durable state is the filesystem. Three candidate mechanisms were evaluated:

**(a) Detached daemon + named FIFO under `./tmp/` — FEASIBLE, chosen for codex.** A process started with `nohup setsid ... &` and redirected entirely to files is reparented to init/launchd and survives Bash-shell death. It is addressed on later turns purely through the filesystem: write to its FIFO stdin, poll its output file. The one classic trap — a FIFO delivers EOF to the reader when the *last writer* closes, which would terminate a stdio server after the first prompt — is defeated by a **holder process** that opens the FIFO for writing and never closes it (`sleep 2147483647 > in.fifo &`, detached the same way). Subsequent per-turn writers (`cat req.json > in.fifo`) come and go without ever dropping the writer count to zero.

**(b) codex `mcp-server`/`app-server`/`exec-server` — FEASIBLE; `mcp-server` chosen as the transport that daemon (a) speaks.** `codex mcp-server` is stdio JSON-RPC with newline-delimited framing and explicit request/response correlation — exactly what (a) needs for deterministic "response complete" detection. `app-server daemon` is attractive (codex manages its own daemon; short-lived `codex app-server proxy` per turn bridges stdio to the control socket, so *we* would hold nothing) but is flagged experimental, has a richer protocol surface (typed thread/turn API, TS bindings), and one shared daemon serving N fan-out sessions is a single point of failure. It is documented as the designated successor path, not v1. `exec-server` is EXPERIMENTAL and ws-first: rejected for v1.

**(c) `agy -i` via pty — FEASIBLE ONLY FRAGILELY, rejected.** `agy -i` is an interactive TUI session. Driving it detached requires a pty (`script -q ... agy -i` or a tiny Python `pty` shim), and — decisive — its output stream has **no machine framing**: response completion would be detected by ANSI-aware prompt-redraw heuristics or idle timers, both of which misfire on long tool-running silences and on streaming output pauses. Since agy conversations are resumable by id with server-side state (verified: `conversations/<uuid>.db` + id-addressable `--conversation`), a held local process buys only process-startup latency, not warm model state. **Verdict: agy `persistent` mode is implemented as resume-under-the-hood (§3.2), same contract.**

### 3.1 Mode B — codex (`codex mcp-server` daemon over FIFO)

#### Spawn & detach (turn 1, `extdel.sh start codex persistent`)

```bash
DIR=./tmp/agent-delegation/$HANDLE
mkdir -p "$DIR"; mkfifo "$DIR/in.fifo"

# 1. Holder: keeps a writer on the FIFO forever so the server never sees EOF.
nohup setsid sh -c "exec sleep 2147483647 > '$DIR/in.fifo'" \
  >/dev/null 2>&1 & echo $! > "$DIR/holder.pid"

# 2. Daemon: codex-as-MCP-server, stdin from FIFO, stdout appended to a regular file.
nohup setsid sh -c "exec codex mcp-server \
    -c sandbox_mode='\"$SANDBOX_MODE\"' ${MODEL:+-c model='\"$MODEL\"'} \
    < '$DIR/in.fifo' >> '$DIR/out.jsonl' 2>> '$DIR/stderr.log'" \
  >/dev/null 2>&1 & echo $! > "$DIR/daemon.pid"

# 3. Watchdog: reaps the daemon if no activity for IDLE_TIMEOUT (default 1800s) —
#    the safety net for a wrapper that dies without running `stop`.
touch "$DIR/activity.touch"
nohup setsid sh -c '
  while sleep 60; do
    kill -0 "$(cat "'"$DIR"'/daemon.pid")" 2>/dev/null || exit 0
    last=$(stat -f %m "'"$DIR"'/activity.touch"); now=$(date +%s)
    if [ $((now - last)) -gt '"$IDLE_TIMEOUT"' ]; then
      kill "$(cat "'"$DIR"'/daemon.pid")" "$(cat "'"$DIR"'/holder.pid")" 2>/dev/null
      exit 0
    fi
  done' >/dev/null 2>&1 & echo $! > "$DIR/watchdog.pid"
```
(macOS `stat -f %m`; Linux branch uses `stat -c %Y` — `extdel.sh` switches on `uname`.)

**Handshake (same turn):** write newline-delimited JSON-RPC to the FIFO — `initialize` (id 0), await response, then `notifications/initialized`, then `tools/list` (id 1) to *verify actual tool names* and record them in `meta.json` (`start_tool`, `reply_tool`). Expected per codex docs: `codex` (args incl. `prompt`, `cwd`, `sandbox`, `model`) and `codex-reply` (args incl. `prompt`, `conversationId`/`sessionId`); the handshake makes the wrapper robust to naming drift across codex versions.

**Where the handle lives:** everything is the `$DIR` path. A later Bash call — or in principle a different process entirely — needs only the HANDLE string to find fifo, pids, offsets, and session id.

#### Prompt write / response read (turn N, `extdel.sh prompt <HANDLE>`)

```
1. liveness:   kill -0 $(cat daemon.pid) || return status=DAEMON_DEAD
2. offset:     OFF=$(wc -c < out.jsonl)              # byte offset before this request
3. req id:     RID=turn-N (monotonic, from meta.json)
4. write:      jq -cn '{jsonrpc:"2.0",id:$rid,method:"tools/call",params:
                 {name:$tool, arguments:{prompt:$p, conversationId:$sid, cwd:$cwd, ...}}}' \
                 > turn-N.request.json
               cat turn-N.request.json > in.fifo     # single <64KB line (see §8 R5)
               touch activity.touch
5. poll loop (interval 2s, deadline TIMEOUT_S):
               tail -c +$((OFF+1)) out.jsonl | grep -q '"id":"'$RID'"' && break
   Every line arriving in [OFF..] stays on disk. Lines that are JSON-RPC *notifications*
   (codex/event: agent_message deltas, exec begin/end, token counts) are the "full transcript";
   the line bearing our request id and a "result" (or "error") member is the response — THIS
   is the completion signal. No heuristics.
6. extract:    RESP=$(tail -c +$((OFF+1)) out.jsonl | grep -m1 '"id":"'$RID'"')
               echo "$RESP" | jq -r '.result.content[]?.text // .result.structuredContent // .error.message' \
                 > turn-N.last-message.txt
               # first turn only: capture conversation/session id from the result
               #   fallback: ~/.codex/sessions scan as in §2.2 → session.id
7. slice:      compact return assembled per §4; full detail remains in out.jsonl
```

**Timeout mid-poll:** return `status: TIMEOUT` with the handle still live (the model may still finish; a follow-up `extdel.sh status <HANDLE>` re-polls from the recorded offset — offsets per request id are stored in `meta.json`).

#### Teardown (`extdel.sh stop <HANDLE>`)

```bash
for f in daemon.pid watchdog.pid holder.pid; do
  kill "$(cat "$DIR/$f" 2>/dev/null)" 2>/dev/null || true
done
rm -f "$DIR/in.fifo"
# mark meta.json: {closed: <ts>}; logs are retained for the caller
```
The wrapper agent's instructions make `stop` mandatory in its final turn (success and error paths). The watchdog (idle reap) and `extdel.sh reap` (§5.3) cover the cases where the wrapper never gets a final turn.

### 3.2 Mode B — agy (resume-under-the-hood)

Per §3.0(c), agy `persistent` mode holds **no OS process**. `extdel.sh start agy persistent` performs Mode A turn 1 (§2.3), records `mode: persistent` in `meta.json`, and every `prompt` call performs an id-resume `--conversation` invocation. The caller-facing contract is byte-identical: same input options, same handle, same return shape; `runtime.held_process: false` in the return's runtime block is the only visible difference. Rationale (documented decision, not accident): agy's continuity is server-side and id-addressable, so a pty-held TUI would add fragility (heuristic completion detection, ANSI parsing, orphaned ptys) for ~2–5s of process-startup latency per turn. If a future agy release ships a machine-framed server mode (the state dir contains `bin/agentapi`, suggesting one exists or is coming — §8 R3), it slots into the same `start/prompt/stop` script interface codex uses.

---

## 4. Unified contract (both CLIs, both modes)

### 4.1 Input — the delegation request

The caller passes one block to the subagent (via the Agent prompt or the `/delegate-*` skill args). All fields except `prompt` optional:

```yaml
prompt: <string, required>          # the task for the external CLI
cli: codex | agy                    # default: skill-specific (codex for /delegate-codex, …)
mode: resume | persistent           # default: resume
handle: <HANDLE string>             # continue an existing session; omit to start a new one
model: <string>                     # passed through: codex -m / agy --model (validate against `agy models`)
effort: low | medium | high         # agy --effort verbatim; codex -c model_reasoning_effort="<effort>"
agent: <string>                     # agy --agent only; ignored for codex
cwd: <abs path>                     # default: project root. codex -C <cwd>; agy runs in <cwd>
add_dirs: [<abs path>, ...]         # codex --add-dir; agy --add-dir
timeout_s: <int>                    # per-prompt-turn deadline. default 600
posture: read-only | workspace | dangerous    # default: read-only (see §6.3 mapping)
close: true | false                 # persistent mode: tear down after this prompt. default false;
                                    # the wrapper ALWAYS closes on its own final turn regardless
expect: <string>                    # optional relevance criteria — what to extract into the answer slice
```

### 4.2 Output — the compact return (MAX_RETURN_CHARS = 12000, per family convention)

```
## External Delegation
- CLI: codex | agy            Mode: resume | persistent
- Status: SUCCESS | FAILURE | TIMEOUT | ERROR | DAEMON_DEAD
- Handle: <HANDLE>                        # pass back to continue this session
- Session id: <external uuid | pending>
- Turn: <n>    Held process: yes|no    Duration: <s>
- Answer file: ./tmp/agent-delegation/<HANDLE>/turn-00N.last-message.txt
- Full log:    ./tmp/agent-delegation/<HANDLE>/turn-00N.events.jsonl   # or out.jsonl for codex persistent
- Files changed: <count + paths, or "none detected", or "not tracked (read-only posture)">

## Answer
<final agent message, verbatim, truncated to fit with "…[truncated — full text in answer file]">

## Errors            # only when Status != SUCCESS
<verbatim stderr tail / JSON-RPC error / auth guidance — see §6>
```

Status semantics: `SUCCESS` = external CLI completed the turn (its own task verdict is in the Answer — the wrapper does not re-judge it); `FAILURE` = CLI ran and exited non-zero / returned JSON-RPC error; `TIMEOUT` = deadline hit (handle may still be live in persistent mode); `ERROR` = could not invoke (missing binary, auth, bad handle, IO); `DAEMON_DEAD` = persistent daemon vanished mid-session (§6.5).

**Files-changed detection:** best-effort from the transcript, not from git: codex `--json` events include patch/exec events (grep `apply_patch`/`patch` event types from `events.jsonl`); agy under `accept-edits` — parse the `--log-file` for edit records; else report `not tracked`. The wrapper never runs `git diff` itself in someone else's cwd unless `expect` asks for it.

### 4.3 Contract invariants (what "IDENTICAL" means)

Same field names, same status vocabulary, same file layout, same handle grammar for: codex/resume, codex/persistent, agy/resume, agy/persistent. Per-CLI differences are confined to (a) which flags `extdel.sh` maps options onto, and (b) the `Held process` runtime flag. A caller script that fans out to both CLIs parses one shape.

---

## 5. Session handle & fan-out model

### 5.1 Handle grammar and lifetime

`HANDLE = <cli>-<mode>-<UTC yyyy-mm-ddThh-mm-ssZ>-<rand6 hex>` — collision-safe under concurrent dispatch by the rand6 (from `/dev/urandom`), human-sortable by timestamp, self-describing. The handle **is** the directory name; possession of the string is possession of the session. Lifetime = wrapper-subagent lifetime: created on `start`, closed on the wrapper's final turn (`stop`), directory retained (logs are the durable artifact; only pids/fifo are cleaned).

A caller that wants a *conversation* with one external session across multiple wrapper dispatches has two options: (1) keep one wrapper subagent alive and send it follow-up instructions (SendMessage / multi-turn Task) — preferred, matches "session lifetime = subagent lifetime"; (2) re-dispatch a new wrapper with `handle:` set — legal for `resume` mode (state is external), and for `persistent` the new wrapper adopts daemon ownership via the pid files (`meta.json` gains `adopted_by` for audit).

### 5.2 Fan-out: N subagents → N external sessions

- **codex, both modes:** zero shared mutable state between handles. N `codex exec` invocations or N `mcp-server` daemons are fully independent; codex's session store is keyed by uuid. No locks needed. Never use `resume --last`.
- **agy:** conversations are independent, but **first-call id capture** reads a cwd-keyed cache (§2.3), so two agy sessions starting concurrently *in the same cwd* race. Serialization: `mkdir ./tmp/agent-delegation/.locks/agy-first-$(echo -n "$CWD" | shasum | cut -c1-12).d` — `mkdir` is atomic; holder does first call + id capture, then `rmdir`. Waiters poll (2s, give up after `timeout_s`, stale lock older than 15 min is broken and noted). Subsequent turns (`--conversation <id>`) don't race. Never use `--continue`.
- **Concurrency cap:** policy default max 5 concurrent external sessions (matches kb-ingest-batch's parallel cap in this repo family); documented, not enforced by the script.

### 5.3 Orphan reaping (no leaked daemons)

Three independent layers, because any single one can be skipped by a crash:

1. **Wrapper's own final turn** runs `extdel.sh stop <HANDLE>` — the normal path, mandated by the agent instructions for every exit path.
2. **Per-daemon watchdog** (§3.1): kills its daemon after `IDLE_TIMEOUT` (default 1800s) without a prompt. Spawned *with* the daemon so it cannot be skipped; exits when the daemon dies so it never lingers.
3. **Sweep on entry:** `extdel.sh reap` runs at the start of every `start` (and as a manual command). For each `./tmp/agent-delegation/*/daemon.pid`: if the pid is dead → clean pid files/fifo, mark meta closed; if alive, verify `ps -o command= -p <pid>` contains `codex mcp-server` (pid-reuse guard) **and** meta is not marked closed **and** activity.touch is younger than `2×IDLE_TIMEOUT` — otherwise kill and clean. Bounds leakage to one idle window even if a whole Claude session is killed.

---

## 6. Failure modes & safety

### 6.1 Missing CLI
`command -v codex` / `command -v agy` at the top of every `start`. Absent → `Status: ERROR`, message `codex not found on PATH — install: npm i -g @openai/codex (or brew install codex)` / `agy not found on PATH — install per Antigravity docs`, no retry.

### 6.2 Auth not logged in (fast-fail, no token spend)
- **codex:** `codex login status` (verified to exist) as a pre-flight in `start`; non-zero/"not logged in" → `ERROR` with `run 'codex login' in a terminal`. Also pattern-match turn stderr for `login|unauthorized|401` as a runtime backstop.
- **agy:** no known status subcommand. Two-stage: pre-flight sanity that `~/.gemini/antigravity-cli/` exists (absence = never-initialized); then treat a first-turn failure whose stderr/CLI-log matches `(?i)auth|sign.?in|login|unauthorized|credential` as `ERROR (auth)` with `run 'agy' interactively once to sign in`, distinct from model-level `FAILURE`. Implementation-time TODO: re-check `agy help` for an auth/status verb in future versions.

### 6.3 Permission / sandbox posture (never auto-approve destructive actions by default)

| posture | codex mapping | agy mapping |
|---|---|---|
| `read-only` (**default**) | `-s read-only` | `--mode plan --sandbox` (plan mode: no edits; sandbox: terminal restrictions) |
| `workspace` | `-s workspace-write` | `--mode accept-edits --sandbox` |
| `dangerous` (explicit opt-in only) | `--dangerously-bypass-approvals-and-sandbox` | `--dangerously-skip-permissions` |

Rules: the wrapper **never** selects `dangerous` itself — it must arrive verbatim in the caller's request, and the wrapper echoes the posture in its return so the escalation is visible in the main transcript. Non-interactive runs (`exec`/`--print`) cannot surface approval prompts to a human, so anything the sandbox blocks under `read-only`/`workspace` simply fails inside the external CLI and shows up in the Answer/Errors — intended, not a bug to route around. `--skip-git-repo-check` is passed for codex (may target non-repo cwds); `--ephemeral` is **not** used (would break `resume`).

Open verification item: `agy --print` + a permission-requiring action in default posture may *hang* until `--print-timeout` rather than fail fast — the native `--print-timeout` plus our hard backstop `timeout` bounds the damage either way (worst case: `TIMEOUT` at `timeout_s`).

### 6.4 Timeouts
Per-turn `timeout_s` (default 600) enforced by: codex resume — `timeout`/`gtimeout`/perl-alarm wrapper (§2.2 note); codex persistent — poll-loop deadline (§3.1 step 5, process left alive, status `TIMEOUT`, re-pollable); agy — native `--print-timeout ${timeout_s}s` + hard backstop at `timeout_s+30`. Daemon-level: `IDLE_TIMEOUT` 1800s watchdog. All timeouts land in the return's runtime block.

### 6.5 Mode-B daemon dying mid-session
`prompt` step 1 (`kill -0`) catches death before a turn → `Status: DAEMON_DEAD`. Death *during* a turn surfaces as poll-deadline + dead pid → also `DAEMON_DEAD`, with stderr.log tail verbatim in Errors. Recovery is explicit in the wrapper's instructions and cheap because codex persists sessions on disk even when started via mcp-server: `extdel.sh recover <HANDLE>` = clean pids/fifo, then **continue the same conversation in resume mode** (`codex exec resume $(cat session.id) …`) or re-`start` a daemon and continue via the reply tool with the recorded conversationId. The return tells the caller which happened (`runtime.recovered: resume-fallback`). If no session id was captured before death, the session is lost — `ERROR`, with `out.jsonl` offered for post-mortem.

### 6.6 Log/answer hygiene
The wrapper never `cat`s a full events file into its own context (Haiku discipline, enforced by instructions mirroring command-runner's step 5: grep/tail/jq extraction only). Return capped at 12 000 chars; overflow lives in the answer file. Secrets: transcripts may contain env/command output from the external agent's tool calls — `./tmp/` is already gitignored in framework projects; the plugin README states logs are local-only and the reap/stop steps never upload anything.

---

## 7. Recommended defaults & plugin shape

**Defaults:** `mode: resume`; `posture: read-only`; `timeout_s: 600`; `IDLE_TIMEOUT: 1800`; model/effort unset (CLI defaults); fan-out cap 5; codex persistent transport `mcp-server` (not app-server/exec-server, both experimental).

**Plugin `sdlc-agent-delegation` (marketplace family: token-optimization, alongside `command-delegation`):**

```
sdlc-agent-delegation/
  .claude-plugin/plugin.json
  agents/
    codex-runner.md        # Haiku; tools: Bash, Read, Grep, Glob; embeds contract + procedure
    agy-runner.md          # Haiku; same shape
  commands/                # (skills/ in this repo's convention)
    delegate-codex.md      # /sdlc-agent-delegation:delegate-codex <prompt...>
    delegate-agy.md
    delegate-status.md     # inspect / reap handles: wraps `extdel.sh status|reap`
  scripts/
    extdel.sh              # start | prompt | status | stop | reap | recover  (all mechanism lives here)
  skills/
    agent-delegation-policy/SKILL.md   # when to delegate out vs run inline; posture escalation rules
```

Agent procedure (mirrors command-runner's numbered-steps style): 1 parse request → 2 pre-flight (`command -v`, auth, reap) → 3 `extdel.sh start|prompt` → 4 extract compact slice from files via grep/jq → 5 compose return → 6 (final turn) `extdel.sh stop`. The agent is forbidden from invoking `codex`/`agy` directly except through `extdel.sh`, and forbidden from ever passing a `dangerous` posture it wasn't given.

---

## 8. Open risks, ranked

1. **R1 — codex MCP tool names/schemas unverified in v0.145.0.** Design assumes `codex` + `codex-reply`-style tools with a conversation id in the result. Mitigated structurally (the `tools/list` handshake discovers actual names at `start`, `meta.json` records them); the argument schema must be confirmed with one token-free `initialize`+`tools/list` probe at implementation. If continuation-by-id is absent from the MCP surface, codex persistent falls back to §3.2 (resume-under-the-hood) — contract unchanged.
2. **R2 — agy conversation-id capture rests on undocumented cache files.** `cache/last_conversations.json` / `conversation_metadata.json` are internal to agy v1.1.5 and could change format on update. Mitigations: format assert with loud `ERROR` (never silent misattribution), first-call cwd lock shrinks the race window to zero in-plugin, and an implementation-time check of whether the id appears in the `--log-file` output. Residual: an agy upgrade breaks id capture until patched — resume degrades to single-turn (each call still works; continuity breaks), surfaced as `Session id: pending`.
3. **R3 — agy `persistent` is not a held process.** Honest divergence, documented in-contract (`Held process: no`). Risk is caller expectation, not correctness. Watch item: `~/.gemini/antigravity-cli/bin/agentapi` suggests a machine-drivable server; if exposed, it slots into `extdel.sh` behind the same verbs.
4. **R4 — orphaned daemons on hard kill.** If the whole Claude process tree is killed, layer 1 (stop) is skipped; layers 2–3 bound leakage to ≤ `2×IDLE_TIMEOUT` per daemon, pid-reuse guarded by command-line matching. Residual: reboot leaves stale pid files — `reap`'s dead-pid branch cleans them on next use. Low.
5. **R5 — FIFO write atomicity for large prompts.** PIPE_BUF guarantees atomic writes only ≤ 64 KiB; a >64 KiB JSON-RPC line is safe in practice because there is exactly one live per-turn writer (holder writes zero bytes) and turns are sequential — no concurrent writers. Documented so nobody "optimizes" into parallel prompt writes on one handle. Very low.
6. **R6 — CLI flag drift.** Both CLIs version fast. All flag composition centralized in `extdel.sh`, so drift is a one-file patch; `start` records CLI `--version` into `meta.json`.
7. **R7 — cost opacity.** Delegated turns spend OpenAI/Google credits invisible to Claude cost telemetry. Codex `--json` token-count events and agy CLI logs are retained; a later `cost-telemetry` integration can parse them. Accepted for v1; noted in the policy skill.

---

**Implementation-order note:** build `extdel.sh` + codex resume mode first (everything verified), then agy resume (one unverified seam: R2), then codex persistent (one probe: R1), then the two agent `.md` files and skills — each stage independently shippable and testable with `bash extdel.sh` directly before any Haiku agent touches it.
