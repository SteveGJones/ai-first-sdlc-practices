# Architecture Design: `sdlc-simple-orchestration` — cross-vendor delegation orchestrator with pluggable backend adapters

**Issue:** #232 · **Branch:** `feature/external-agent-delegation` · **Status:** Repositioning design v1 (Fable-tier), for implementation · **Date:** 2026-07-24
**Supersedes (in part):** `2026-07-23-external-agent-delegation-design.md` §7 (plugin shape) and its two-hardcoded-runner framing. **Marks superseded:** `2026-07-24-codex-mode-b-design.md` (entire; §6.3 for what survives). **Preserves as authoritative:** main spec §4.2 (unified return contract), §9.1 (portable daemonizer), §9.2 (submit-then-poll), §9.8 (per-handle mutex), §9.10 (pinned posture), §9.14–§9.16 (agy `--gemini_dir` findings) — these become the **direct-CLI adapter engine**, behavior unchanged.

**Ground truth (2026-07-24, this machine):** all three suites green (codex 67, agy 104, supervisor 14 = **185**, mock-only). `plugins/sdlc-agent-delegation` is **absent** from `marketplace.json`, `CLAUDE.md`, `AGENT-INDEX.md` — never released/registered, so the rename is a first-time registration (no alias/deprecation). Installed-plugin truth lives at `~/.claude/plugins/installed_plugins.json` (`{"version":2,"plugins":{"<name>@<marketplace>":[…]}}`) + cache tree `~/.claude/plugins/cache/<mkt>/<plugin>/<ver>/`. `codex-plugin-cc` and `opencode` are **not installed** here → detection is a runtime probe; OpenCode adapter flags are all probe-gated. `extdel.sh` (1766 ln) has a clean seam: generic core vs per-CLI functions (codex ln 352–583; agy ln 587–943) — the adapter refactor is a mechanical extraction along it.

---

## 1. Overview & positioning

Per-vendor delegation plugins already exist and do the per-vendor job better than we would: **`openai/codex-plugin-cc`** (official — `/codex:review|adversarial-review|rescue|transfer|status|result|cancel`, one-shot/background, resume; its "approval" is a *review gate*, not per-action permissions) and **`yuting0624/antigravity-for-claude-code`** (community agy; writes need blanket `--yolo`). We reposition as a **cross-vendor delegation orchestrator** whose value is what no per-vendor plugin gives:

1. **Unified delegation contract** (§4.2) across heterogeneous backends.
2. **Cross-model fan-out / compare / synthesize** — same task → N backends under one contract.
3. **Graded permission postures** enforced uniformly — incl. the agy `--gemini_dir` mechanism the community plugin lacks (yolo-or-nothing).
4. **Context isolation** — Haiku wrappers + `./tmp` log/slice; peer transcripts never enter the caller's context.
5. **Extensibility** — a new backend (OpenCode…) is one adapter directory, no core change.

**Name `sdlc-simple-orchestration`** — "simple" distinguishes it from `sdlc-workflows`: *in-session, uncontainerised, single-machine* delegation to locally-installed peer CLIs — no Archon, no Docker, no DAG. Every registration entry must carry that one-line distinction.

**Binding decisions designed-to:** rename → `sdlc-simple-orchestration`; keep codex Mode A as the **codex direct-CLI adapter** ("prefer codex-plugin-cc" = routing/hand-off, §3.3); keep agy `--gemini_dir` adapter (the anti-`--yolo` value-add); cut codex Mode B (§6.3); repurpose `extdel.sh`+`turn-supervisor.pl` as the reusable engine.

### Architecture at a glance
```
caller (main Claude session)
  ├── skills/orchestration-policy → routing (§3.3): sibling-plugin hand-off vs our dispatch
  ├── commands/delegate → Agent(delegation-runner, backend=X)         1 task → 1 backend
  ├── commands/compare  → Agent(delegation-runner)×N parallel → synthesize/vote (§5)
  └── agents/delegation-runner (Haiku; Bash/Read/Grep/Glob)
        └── scripts/extdel.sh  = THE ENGINE (start|prompt|status|slice|stop|reap|list-backends)
              ├── generic core: handles, meta, mutex, pinned posture, spawn_daemon,
              │   turn-supervisor.pl, submit-then-poll, unified §4.2 return
              └── sources ONE adapter/invocation:
                    scripts/adapters/{codex,agy,opencode}/{adapter.json,adapter.sh}
                    $EXTDEL_ADAPTER_PATH/…  (third-party, no core change)
```

---

## 2. Adapter interface

An adapter is **one directory**: a JSON descriptor (identity + capabilities; JSON because the engine is bash 3.2 + `jq`) and a shell implementation (the ABI the engine calls).

### 2.1 Descriptor `scripts/adapters/<id>/adapter.json` (codex shown)
```json
{ "schema_version":1, "id":"codex", "display_name":"OpenAI Codex CLI", "vendor":"openai",
  "kind":"direct-cli", "binary":"codex", "tested_versions":["0.145.0"],
  "detect":{"command":"codex","auth_probe":"codex login status","auth_fix_hint":"run 'codex login'"},
  "capabilities":{"one_shot":true,"session_resume":true,"held_process":false,
    "per_action_approval":false,"fanout_safe":true,"model_select":true,"effort_select":true,
    "answer_file_native":true},
  "postures":{
    "read-only":{"mechanism":"sandbox","fidelity":"hard","native":"-s read-only"},
    "workspace":{"mechanism":"sandbox","fidelity":"hard","native":"-s workspace-write"},
    "dangerous":{"mechanism":"bypass","fidelity":"none","native":"--dangerously-bypass-approvals-and-sandbox"}},
  "sibling_plugins":[{"plugin_match":"codex-plugin-cc@","relationship":"prefer-for",
    "prefer_for":["review of Claude's own work","adversarial review gate","rescue","persistent codex threads"],
    "commands":["/codex:review","/codex:adversarial-review","/codex:rescue","/codex:transfer","/codex:status","/codex:result","/codex:cancel"],
    "interop_note":"session-id hand-off is a probe-gated fast-follow (§3.4)"}],
  "notes":{"posture_caveats":"read-only is a real OS sandbox; blocks writes+network not reads",
    "id_capture":"--json event stream, fallback ~/.codex/sessions scan (spec §9.3)"}}
```
Semantics: **`id`** = `--cli <id>`, handle prefix, adapter dir name — grammar `[a-z][a-z0-9]*` (NO hyphens; `validate_handle` splits on `-`). **`kind`** = which engine drives it; v0.1.0 defines `direct-cli` only; reserved `http-server` (future `opencode serve`), `rpc-server` (future revived Mode B); unknown → `ERROR`. **`capabilities`** consumed by `list-backends`/`compare`/policy; `per_action_approval:false` for all v0.1.0 adapters (place for the cut Mode B to return). **`postures.*.fidelity`** ∈ `hard`|`allow-list`|`config`|`none`, surfaced verbatim so callers see "read-only" isn't uniformly strong. **`sibling_plugins.relationship`** ∈ `prefer-for`|`coexist`|`superseded-by-us` (agy lists `antigravity-for-claude-code@` as `superseded-by-us`: "requires blanket --yolo; ours is graded").

### 2.2 Implementation `adapter.sh` — the function ABI
Engine `source`s one adapter/invocation (from `--cli` at start, from `meta.json.cli` after) and asserts each function exists. For `kind:direct-cli`, each is a direct extraction of an existing extdel.sh function:

| ABI function | Contract | Today (line) |
|---|---|---|
| `adapter_detect` | exit 0 iff binary present; no output | inline `command -v` |
| `adapter_preflight` | exit 0, or print one-line reason + exit 1 (auth/init); NO tokens | `preflight_codex`(352), `preflight_agy`(587) |
| `adapter_posture_args` | echo native argv for `$POSTURE`; MAY write per-handle config under `$DIR` (agy `--gemini_dir` write lives here, refreshed each turn) | `codex_sandbox_args`(364), `agy_posture_args`(603)+`agy_write_gemini_config`(624) |
| `adapter_submit_turn` | compose full backend argv for turn `$TURN` (start if 1 & no session.id, else resume); launch via engine `engine_spawn_turn` (wraps spawn_daemon+turn-supervisor.pl + lock) | `submit_codex_turn`(483), `submit_agy_turn`(805) |
| `adapter_capture_session_id` | after turn 1 terminal, write id to `$DIR/session.id` or `pending`; race-safe | `capture_session_id`(375), `capture_agy_session_id`(736) |
| `adapter_files_changed_summary` | echo files-changed line for §4.2 | `files_changed_summary`(442), `agy_files_changed_summary`(792) |
| `adapter_permission_hint_pattern` | echo the ERE the NO_OUTPUT downgrade greps (may be empty) | `permission_denial_hint`(149) |
| `adapter_check_identity_drift` *(opt)* | engine calls iff defined; agy cache-tamper WARNING | `agy_check_identity_drift`(769) |

Engine exports to adapters: `$DIR $HANDLE $CLI $POSTURE $TURN $PROMPT_FILE $TIMEOUT_S $CWD $ADD_DIRS $MODEL $EFFORT` + helpers `meta_get/meta_set now_iso/now_epoch is_blank_file engine_spawn_turn`. **Engine-owned, adapter-forbidden** (the uniformity invariants): handle grammar + `validate_handle`; `meta.json` schema; turn mutex; **pinned-posture refusal** (checked in `cmd_prompt` before any adapter code — adapters can't un-pin); `spawn_daemon`+`turn-supervisor.pl`; status vocabulary + NO_OUTPUT; `slice`; `stop`/`reap`; §4.2 emission.

Not a rewrite: `extdel.sh` keeps its name, subcommands, flag grammar, state layout, and byte-for-byte behavior where tests assert it; per-CLI bodies move to adapters; `case "$CLI"` → source-then-call. The 185 tests prove the extraction changed nothing.

---

## 3. "Delegate to an existing plugin" vs direct CLI — resolved honestly

**Mechanics:** (1) installed plugins' slash commands surface as invocable skills in the MAIN thread (observable in this repo). (2) Our runner subagents (Haiku; Bash/Read/Grep/Glob, no Skill/Agent tool) **cannot** invoke another plugin's command — and granting it would break isolation + be unreliable. (3) Even in the main thread, `/codex:review` yields codex-plugin-cc's output shape + its own background lifecycle, not our contract; wrapping it = scraping another plugin's conversational output (fragile, double-spends context).

**Resolution — option (a):** the codex adapter **is** the extdel.sh direct-CLI path (`codex exec`/`exec resume`), always. "Prefer codex-plugin-cc when installed" is **routing/hand-off at the policy layer, not call-through.** Stated plainly in README + policy skill — no pretending inter-plugin RPC exists.

**Detection** (`detect_sibling_plugins <id>`): primary = `jq` over `~/.claude/plugins/installed_plugins.json` (guard `.version==2`); fallback = cache-tree scan; any parse/shape failure → `sibling: unknown` (never "not installed" from a failed probe). Advisory-only — the direct adapter never depends on it. The main-thread policy skill additionally prefers the harness-truth signal of whether `/codex:*` appears in its own available-skills listing.

**Routing table** (`skills/orchestration-policy`, main thread, before dispatch):
| Task shape | codex-plugin-cc installed | Route |
|---|---|---|
| review my diff / adversarial gate / rescue stuck task / persistent codex thread | yes | **Hand off** to `/codex:*` in main thread; do NOT also dispatch runner |
| same | no | Dispatch `delegation-runner backend=codex`; note the official plugin exists (`/plugin install` hint) |
| cross-model compare/fan-out, unified-contract collection, isolated 2nd opinion, posture-graded write delegation | either | **Always our adapter** (work the official plugin doesn't do) |
| anything agy | either | **Always our agy adapter** (`superseded-by-us`: community needs `--yolo`; ours is graded) |

**§3.4 probe-gated interop:** both codex-plugin-cc threads and our handles persist in `~/.codex/sessions`. If `/codex:transfer` thread ids are codex session uuids (token-free probe), genuine state hand-off exists without any inter-plugin call: `start --cli codex --session-id <uuid>` (new flag: pre-seed session.id, first turn resumes) and vice-versa. Fast-follow, capability-flagged `session_id_interop`.

---

## 4. Registry & discovery

**Model:** static descriptor set + runtime probes, no registry file. Registry = `${CLAUDE_PLUGIN_ROOT}/scripts/adapters/*/adapter.json` ∪ each dir in `EXTDEL_ADAPTER_PATH` (colon-sep; local overrides shipped, first `id` wins). `cmd_start` resolves `--cli <id>` → dir → validates descriptor (`jq -e '.schema_version==1 and .id and .kind'`) → sources → asserts ABI; `meta.json` records `adapter_dir`+`adapter_schema_version`.

**`extdel.sh list-backends [--json]`** — per descriptor: `adapter_detect` (ms), optional `adapter_preflight` under `--probe-auth` (token-free), `detect_sibling_plugins`. Emits a table (id, vendor, installed, auth, kind, postures+fidelity, sibling plugin). Pure read-only; no handle/state/tokens.

**Adding a backend = one directory** (the invariant): `adapters/<newid>/{adapter.json,adapter.sh}` + mock fixture + test → `--cli <newid>` works everywhere + shows in `list-backends`, **zero edits** to engine/supervisor/runner/other adapters. Shipped `docs/ADAPTER-AUTHORING.md`; `tests/test-adapter-descriptors.sh` lints every descriptor.

**OpenCode worked example (fast-follow; all ⚠ = implementation-time probe):** descriptor `kind:direct-cli`, postures via a per-handle config file `$DIR/opencode-cfg/opencode.json` (`permission:{edit,bash,webfetch}=allow|ask|deny`) pointed to by `OPENCODE_CONFIG` ⚠P-OC3 — **the agy `--gemini_dir` pattern generalized** (per-handle config injection is the graded-permission mechanism for any config-driven backend). Turn 1 `opencode run "<prompt>"` ⚠P-OC4; turn N `opencode run --session <id> "<prompt>"` ⚠P-OC5 (never bare `--continue` — last-session fan-out race). id capture ⚠P-OC5b (run output / `session list` / storage dir; assert format, `pending` on failure). `auth list` ⚠P-OC1; `ask`-headless-auto-deny ⚠P-OC2. Held mode `opencode serve` (HTTP/OpenAPI) → reserved `kind:http-server`, out of scope. Deliverables: 2 files + mock + test + probes run + `tested_versions` pinned, **zero core edits** = the architecture's acceptance test.

**OpenCode probe results — CONFIRMED LIVE (opencode 1.18.5, 2026-07-24), resolving P-OC1..5b:**
- **Install/detect:** binary at `~/.opencode/bin/opencode`, **NOT on the non-interactive Bash PATH**. `adapter_detect` must check PATH *and* `~/.opencode/bin` (and honor an `OPENCODE_BIN` override). This is a real detection nuance the codex/agy adapters (on `~/.local/bin`, which IS on PATH) don't have.
- **Auth (P-OC1):** `opencode models` returns a non-empty provider/model list when authed; several **free models exist** (`opencode/deepseek-v4-flash-free`, …) → the mock isn't the only zero-cost path; live adapter tests can use a `-free` model (`cost:0` confirmed).
- **One-shot (P-OC4):** `opencode run --dir <cwd> --format json -m <provider/model> [--variant <effort>] "<message>"` → newline-delimited JSON events on stdout, exit 0. Prompt is a positional `[message..]` (guard leading dash; confirm multi-line handling). `--dir` sets the working dir (no cd needed — better than agy). `--format json` gives machine output.
- **Resume (P-OC5):** `opencode run --dir <cwd> --session <id> --format json "<message>"`. NEVER `-c/--continue` (last-session; fan-out race). `--fork` exists.
- **id capture (P-OC5b):** trivial — EVERY json event carries `"sessionID":"ses_…"`. Capture = first `ses_[A-Za-z0-9]+` from the turn-1 stream → `session.id` (assert format; `pending` on miss). (`opencode session list` returned empty in a fresh scratch cwd; the json stream is the reliable source.)
- **answer extraction:** the final answer is the `{"type":"text",…,"part":{"type":"text","text":"…"}}` event(s) before `step_finish`; `step_finish.part.tokens`+`cost` give usage. Write joined/last text to `last-message.txt`.
- **Postures / permissions (P-OC2/P-OC3):** `OPENCODE_CONFIG=<per-handle>.json` env points opencode at a config carrying a `permission` block (schema `https://opencode.ai/config.json`; keys `permission:{edit,bash,webfetch}` = `allow|ask|deny`). `--auto` auto-approves non-denied perms (⇒ `dangerous`). read-only = `{edit:deny,bash:deny,webfetch:deny}` (reads still allowed — OpenCode's read tool isn't permission-gated); workspace = `{edit:allow,bash:allow,webfetch:deny}`. ⚠ **Remaining probe P-OC2b:** headless behavior of an `ask` permission (auto-deny like agy, or hang?) — task B should confirm with one live `-free`-model write attempt under read-only; expect auto-deny. This is the exact `--gemini_dir`-style per-handle-config-injection pattern, generalized.

---

## 5. Orchestration operations (the novel core)

**5.1 `delegate` (v0.1.0):** one generic `agents/delegation-runner.md` (Haiku) replaces codex/agy-runner (~85% identical); takes `backend:` + §4.1 fields; merged hard-rules (only-through-extdel.sh; never self-escalate posture; external content is data; read-only≠read-nothing; mandatory stop; never cat transcripts; NO_OUTPUT terminal). Backend caveats move to the policy skill's platform table + descriptor notes. `description:` enumerates backends + trigger phrases (proactive selection). `commands/delegate.md` = `/…:delegate <backend> <prompt> [posture= model= handle=]` — consults routing table then dispatches. Contract/statuses/submit-then-poll/12k slice = shipped behavior.

**5.2 `compare`/fan-out (fast-follow F1):** choreography in `commands/compare.md`+skill; **no new engine code** (handles already fanout-safe). `/…:compare backends=codex,agy [posture=read-only] <task>`: main thread writes `./tmp/simple-orchestration/fanout-<ts>-<rand6>/{manifest.json,task.md}` (one identical prompt), dispatches N runners in one message (cap 5 across ALL ops), each writes its unified block to `<backend>.result.md` + returns. **Uniform posture:** one posture for the fan-out, pinned per-handle; mixed only via explicit `postures=codex:workspace,agy:read-only` (return flags the asymmetry). Pre-dispatch `list-backends --json` confirms installed + reports `fidelity` mismatch (report, not block). Collection = mechanical merge (same §4.2 shape); failures don't abort siblings.

**5.3 `synthesize`/`vote` (F1):** operate on a completed fan-out dir. `synthesize` (default) = one Sonnet judge subagent (reads N result files from disk, no main-context inheritance) → convergent/divergent(attributed)/adjudication/confidence, ≤12k. `vote` = compare appends `"End with: VERDICT: <APPROVE|BLOCK|UNSURE> — <reason>"`; tally by `grep -m1 '^VERDICT:'` (no model), escalate to judge on split; missing verdict = UNSURE, flagged. **Provenance rule:** synthesized output retains per-backend attribution (laundering "agy said X" into "the analysis shows X" is a defect).

**5.4 Isolation composes:** (1) runner is Haiku → ≤12k/delegation to caller; (2) raw material under `./tmp/simple-orchestration/<HANDLE>/` + `…/fanout-<id>/`; (3) judge is a file-reading subagent → even N×12k needn't transit main context. Main conversation sees: routing decision, N status lines, one synthesis.

---

## 6. Keep / reframe / cut — current files → new roles

| Current | Disposition | New role |
|---|---|---|
| `scripts/extdel.sh` | KEEP+refactor | Engine: generic core stays; per-CLI fns (352–583, 587–943) → adapters; gains adapter resolution+ABI assert+`detect_sibling_plugins`+`cmd_list_backends`; state dir → `./tmp/simple-orchestration/` |
| `scripts/turn-supervisor.pl` | KEEP verbatim | Engine component (14 tests unchanged) |
| `agents/codex-runner.md` | MERGE | basis of `delegation-runner.md`; deleted after |
| `agents/agy-runner.md` | MERGE | agy specifics → policy skill + agy descriptor notes; deleted |
| `skills/agent-delegation-policy` | REFRAME | → `skills/orchestration-policy`: keep posture/read-only≠read-nothing/cost/cap; ADD §3.3 routing table, list-backends usage, compare/synthesize rules, sdlc-workflows distinction |
| `README.md` | REWRITE | orchestrator positioning; honest §3 mechanism; adapter architecture; both sibling plugins named |
| `.claude-plugin/plugin.json` | REWRITE | name `sdlc-simple-orchestration`, v0.1.0, keywords orchestration/cross-model/codex/agy/opencode |
| `tests/*codex*` (67), `*agy*` (104) | KEEP, retarget | path/state-dir sed only |
| `tests/*turn-supervisor*` (14) | KEEP unmodified | supervisor untouched |
| `tests/fixtures/*` | KEEP | mock-CLI pattern = documented adapter-test pattern |
| *(new)* | ADD | `adapters/{codex,agy}/{adapter.json,adapter.sh}`; `commands/{delegate,backends}.md`; `docs/ADAPTER-AUTHORING.md`; `tests/{test-adapter-descriptors,test-list-backends}.sh` |

**6.3 The cut (codex Mode B):** `2026-07-24-codex-mode-b-design.md` gets a SUPERSEDED banner. Survives as recorded knowledge: the app-server protocol facts + posture→(sandbox,approvalPolicy) table (future `rpc-server`); the approval-policy decision tables + deny-list (reusable per-action policy); the request-file-spool IPC. **Revival condition:** returns only as `per_action_approval:true`/`kind:rpc-server` for a backend natively exposing a typed approval protocol, where not redundant with that backend's sibling-plugin gating. No code deleted (Mode B branches were never built; `--mode persistent` already ERRORs). README/skill wording that promised "codex persistent (planned)" → "held-process modes are a possible future engine kind; no backend ships one today."

---

## 7. Migration & rename plan (ordered; tests green at each starred step)

0. **Doc supersession (no code):** banners on both specs; update feature-proposal + retrospective with pivot + new name.
1. ***Directory + identity rename:*** `git mv plugins/sdlc-agent-delegation plugins/sdlc-simple-orchestration`; plugin.json name/desc/keywords (version stays 0.1.0). Suites green from new path.
2. ***State-dir + string rename:*** sed `tmp/agent-delegation`→`tmp/simple-orchestration` and `sdlc-agent-delegation`→`sdlc-simple-orchestration` across scripts/tests/agents/skills/README; verify no stragglers. Suites green.
3. ***Adapter extraction (the refactor):*** create `adapters/{codex,agy}/`; move per-CLI bodies (352–583→codex, 587–943→agy) under ABI names; write both descriptors; replace `case "$CLI"` with `resolve_adapter && source && assert_adapter_abi`; record `adapter_dir` in meta; add `EXTDEL_ADAPTER_PATH`. **Acceptance: all 185 pass with zero test-file edits.**
4. ***list-backends + sibling detection:*** add `detect_sibling_plugins`+`cmd_list_backends`; `tests/test-list-backends.sh` (mock installed_plugins.json via HOME override: installed/absent/malformed→unknown) + `tests/test-adapter-descriptors.sh`.
5. ***Agent merge:*** `git mv codex-runner.md delegation-runner.md`; generalize (`backend:` field; agy rules → skill+descriptor); `git rm agy-runner.md`.
6. **Skill reframe:** `git mv skills/agent-delegation-policy skills/orchestration-policy`; rewrite per §6 (routing table = major add; keep posture/cost sections verbatim).
7. **Commands:** `commands/delegate.md` + `commands/backends.md`.
8. **README rewrite + `docs/ADAPTER-AUTHORING.md`** (incl. OpenCode walkthrough with probes marked).
9. **Registration (first-time, new name only):** marketplace.json entry; CLAUDE.md plugin table row (with sdlc-workflows distinction); AGENT-INDEX.md `delegation-runner` + count bumps. No removal/alias (old name never registered).
10. **Validation gate:** `local-validation.py --pre-push` + `check-broken-references.py`; full tests (185 + new) green.
11. **Release + retrospective:** `/sdlc-core:release-plugin`; complete retrospective.

---

## 8. v0.1.0 scope vs fast-follows

**v0.1.0 ("the orchestrator exists"):** the refactored engine (behavior-identical); two adapters (codex fallback + agy graded-posture); registry + `list-backends` + sibling detection; `delegate` (runner + `/…:delegate` + `/…:backends`); `orchestration-policy` skill incl. routing table (so "prefer codex-plugin-cc" ships as behavior day one); adapter-authoring doc; 185 preserved + descriptor-lint + list-backends tests; registration.

**F1:** `compare` + `synthesize`/`vote` (skill/command choreography over the shipped engine — highest novel-value/effort). **F2:** OpenCode adapter (runs P-OC1–5; proves "one dir, no core change" publicly; gives compare a 3rd model family). **F3:** codex session-id interop (§3.4; adds `--session-id`). **Unscheduled:** `http-server` kind (`opencode serve`); `rpc-server` + per-action-approval revival; cost-telemetry for external spend.

---

## 9. Honest risks (ranked)

1. **Without inter-plugin RPC, it's an orchestrator *beside* not *over* the plugins.** v0.1.0 can read as "a nicer multi-CLI wrapper + routing skill." Mitigation: README states the mechanism; novel value must be carried by shipping F1 fast + unique graded agy postures. **Biggest disappointment surface.**
2. **Heterogeneous posture semantics under one word** (codex hard sandbox vs agy allow-list vs opencode config; read-only≠read-nothing everywhere). Mitigation: `fidelity` flags in list-backends + compare; honesty text retained. Residual: callers over-trust the shared word.
3. **Upstream CLI drift** (agy undocumented cache = weak seam). Mitigation: blast-radius = one adapter dir; `tested_versions` + recorded `--version`; loud-ERROR-on-shape-change. Residual: agy update can break id capture until patched (degrades single-turn, never misattributes).
4. **Sibling detection rests on a Claude Code internal.** Mitigation: version-guard + cache fallback + degrade-to-unknown; advisory-only; skill's available-skills cross-check. Worst case: lost preference, not lost capability.
5. **No cost benchmark vs competitors' measured claims.** Mitigation: run one honest measured comparison before any cost claim; until then claim isolation+safety, not savings.
6. **One generic runner weakens proactive auto-delegation** vs vendor-named agents. Mitigation: trigger-rich description + routing skill; cheap fix = thin vendor-named alias agents that re-invoke the runner.
7. **Fan-out multiplies real external spend** (invisible per 5). Mitigation: cap 5; compare states spend up front.
8. **OpenCode adapter designed against uninstalled docs** (all probe-gated). Mitigation: fast-follow, probes required before `tested_versions`. Low.
9. **Naming collision with `sdlc-workflows`.** Mitigation: mandated one-line distinction everywhere. Minor.

**Order note:** step 3 (adapter extraction) is the only regression-risk step and is fully gated by the 185 assertions before any new surface; every later stage is independently testable with `bash extdel.sh …` / mock manifests before any agent/skill touches it.
