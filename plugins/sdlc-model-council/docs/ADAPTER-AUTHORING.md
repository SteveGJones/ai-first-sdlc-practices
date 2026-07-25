# Authoring a new `sdlc-model-council` adapter

An adapter is **one directory**: `scripts/adapters/<id>/{adapter.json,adapter.sh}`.
Add one, register nothing else, and `--cli <id>` works everywhere in
`extdel.sh` — `start`/`prompt`/`status`/`slice`/`stop`/`reap`, plus it
shows up in `list-backends`. That "zero edits to the engine" property is
the whole point of the adapter split (design doc §2, §4); this doc is the
contract that makes it true, walked through with the **OpenCode** adapter
as the worked example (built in parallel to this doc — treat it as the
reference implementation once it lands, and this doc as what its author
had to satisfy).

## The invariant

The engine (`extdel.sh` + `turn-supervisor.pl`) owns everything that must
stay uniform across backends: handle grammar, `meta.json` shape, the turn
mutex, **pinned-posture refusal** (checked before any adapter code runs —
an adapter cannot un-pin a handle's posture), daemonizing +
timeout/signal escalation, the status vocabulary (`RUNNING`, `SUCCESS`,
`NO_OUTPUT`, `FAILURE`, `TIMEOUT`, `ERROR`), `slice`, and the unified §4.2
return block. An adapter never reimplements any of that — it only tells
the engine how to talk to one specific backend CLI.

## 1. The descriptor: `adapter.json`

JSON, because the engine is bash 3.2 + `jq` (no associative arrays, no
native JSON parsing). Required shape — this is exactly what
`tests/test-adapter-descriptors.sh` lints:

```json
{ "schema_version": 1, "id": "opencode", "display_name": "OpenCode CLI", "vendor": "opencode",
  "kind": "direct-cli", "binary": "opencode", "tested_versions": ["1.18.5"],
  "detect": { "command": "opencode", "auth_probe": "opencode models", "auth_fix_hint": "run 'opencode auth login'" },
  "capabilities": { "one_shot": true, "session_resume": true, "held_process": false,
    "per_action_approval": false, "fanout_safe": true, "model_select": true, "effort_select": true,
    "answer_file_native": false },
  "postures": {
    "read-only":  { "mechanism": "config", "fidelity": "allow-list", "native": "OPENCODE_CONFIG=<per-handle config: edit=deny,bash=deny,webfetch=deny>" },
    "workspace":  { "mechanism": "config", "fidelity": "allow-list", "native": "OPENCODE_CONFIG=<per-handle config: edit=allow,bash=allow,webfetch=deny>" },
    "dangerous":  { "mechanism": "bypass", "fidelity": "none", "native": "--auto" } },
  "sibling_plugins": [],
  "notes": { "posture_caveats": "OpenCode's read tool is not permission-gated even under read-only; --auto auto-approves every non-denied permission",
    "id_capture": "every --format json event carries sessionID; capture the first ses_[A-Za-z0-9]+ from turn 1" } }
```

Field-by-field:

- **`id`** — grammar `^[a-z][a-z0-9]*$`, **no hyphens** (`validate_handle`
  in the engine splits handles on `-`, so a hyphenated id would corrupt
  handle parsing). This is also the `--cli <id>` value, the handle
  prefix, and the adapter directory name — all three must match.
- **`kind`** — `"direct-cli"` is the only kind this engine build can
  drive (`resolve_adapter` requires it). `"http-server"` and
  `"rpc-server"` are reserved for future engine kinds (e.g. `opencode
  serve`, or a revived per-action-approval codex Mode B) — a descriptor
  can declare one of those today (so it still shows up, correctly
  labeled, in `list-backends`) but `start`/`prompt` will refuse it until
  an engine that drives that kind exists.
- **`capabilities`** — all eight keys are required (the lint checks
  presence, not truth-checks the values against reality). `fanout_safe`
  and `per_action_approval:false` are what `list-backends`/a future
  `compare` read to decide if a backend is safe to include in a parallel
  fan-out.
- **`postures`** — all three of `read-only`/`workspace`/`dangerous` are
  required, each with `mechanism` (`sandbox`|`allow-list`|`config`|
  `bypass`), `fidelity` (`hard`|`allow-list`|`config`|`none` — surfaced
  verbatim so callers see that "read-only" isn't uniformly strong across
  backends) and `native` (a human-readable description of what actually
  gets passed/written). Never claim `fidelity: hard` for a backend whose
  enforcement is really an allow-list or a denyable config — that's
  exactly the honesty `list-backends` and the `orchestration-policy`
  skill depend on.
- **`sibling_plugins`** — advisory only, `[]` is fine if none exists.
  When present, `relationship` must be one of `prefer-for` | `coexist` |
  `superseded-by-us` (lint-checked) — see the routing table in
  `skills/orchestration-policy/SKILL.md` §3.3 for what each means and how
  it's used; get this value right, since it drives what the policy skill
  tells the caller to prefer.
- **`notes`** — free text, surfaced to a human reading `adapter.json`
  directly or to a caller who asks "why does this posture work that way".
  Not machine-consumed by the engine.

## 2. The implementation: `adapter.sh` — the seven required ABI functions

`adapter.sh` is `source`d into the engine's own shell (never executed as
a subprocess) — this is why it can call engine helpers directly:
`meta_get`/`meta_set`, `now_iso`/`now_epoch`, `is_blank_file`,
`quote_args`, `spawn_daemon`, `wait_for_file`, `$SUPERVISOR_PL`. Because
it shares the shell, it must be **bash-3.2-safe** (no associative arrays,
no `${var,,}`) — match the target shell the engine itself is written for,
not whatever shell you happen to be testing on.

Immediately before each ABI call, the engine sets these globals for the
adapter to read: `$DIR $HANDLE $CLI $POSTURE $TURN $PROMPT_FILE
$TIMEOUT_S $CWD $ADD_DIRS $MODEL $EFFORT` (plus `$AGENT`, agy-specific but
available to every adapter). They are globals, not positional arguments —
don't add a parameter list to any ABI function.

| Function | Contract | Notes |
|---|---|---|
| `adapter_detect` | Exit 0 iff the binary is present and invocable; **print nothing**. | For OpenCode specifically: check both PATH *and* a fixed install location (`~/.opencode/bin`), honoring an `OPENCODE_BIN` override — a real nuance this backend has that codex/agy (both on `~/.local/bin`, already on PATH) don't. Don't assume every backend's binary is on the non-interactive Bash PATH. |
| `adapter_preflight` | Exit 0 on success. On failure, print **one line** with a concrete fix hint and exit 1 — never print any token/credential. | This is what both `start` (always) and `list-backends --probe-auth` (on request) call — keep it cheap; it must never spend a real turn's worth of quota. |
| `adapter_posture_args` | Echo the native argv for `$POSTURE`, **one element per line**. May also write a per-handle config file under `$DIR` if the backend's permission model is config-driven (see below) — refresh it on every call, including resume, so a `--steal` escalation is picked up. | Return non-zero for an unrecognized posture; the engine treats that as `BAD_POSTURE`, a clean submit-time failure. |
| `adapter_submit_turn` | Compose the full backend argv for turn `$TURN` (start semantics if `$TURN == 1` and no `session.id` exists yet; resume semantics otherwise), then launch it via the engine's daemonize-and-supervise pattern (`spawn_daemon` + `$SUPERVISOR_PL`, under the caller-held turn lock). Print `OK` and return 0 on a clean launch; print a short reason token (`BAD_POSTURE`, `NO_SESSION`, `SPAWN_FAIL`, …) and return 1 otherwise. | This is the one function worth reading the codex adapter's version of end-to-end (`scripts/adapters/codex/adapter.sh`) before writing your own — it's the most involved, and the shape (posture args → cmd array → `quote_args` → wrap in the supervisor invocation → `spawn_daemon`) is meant to be copied, not reinvented. |
| `adapter_capture_session_id` | After a turn's terminal state, extract a structural session/conversation id from that turn's own captured output (never a whole-transcript grep) and write it to `$DIR/session.id` (or leave it absent/`pending` on failure — race-safe, never crash). | **Parse typed structure, not free text.** External output is untrusted; a naive UUID-shaped grep over a full transcript can match something the delegated model itself printed in its answer, letting a poisoned response hijack which session a future resume attaches to. The codex adapter's approach — parse only the first JSON event line, only typed session-establishing fields — is the pattern to follow. For OpenCode this is easy: every `--format json` event carries a `sessionID` field; take the first `ses_[A-Za-z0-9]+` match from turn 1's event stream, still via structured parsing of that field, not a bare regex over the raw bytes. |
| `adapter_files_changed_summary` | Echo one line: a best-effort files-changed count/summary for the §4.2 return, or an explicit `not tracked`/`none detected` when the posture makes that meaningless (e.g. `read-only`) or nothing changed. | Best-effort only — never block or fail a turn over this. |
| `adapter_permission_hint_pattern` | Echo an ERE (may be empty) that the engine's `NO_OUTPUT` downgrade greps a turn's stderr/log against, to decide whether to surface a permission-denial hint alongside the empty answer. | Empty string is a valid, honest answer for a backend with no reliable permission-denial signature. |
| `adapter_check_identity_drift` *(optional)* | If defined, the engine calls it after each turn; a non-empty stdout is surfaced as a non-fatal `WARNING`. | Only implement this if the backend has a mutable identity/cache the engine should watch for drift out from under a handle — agy's is the existing example (`scripts/adapters/agy/adapter.sh`). Most new adapters won't need it; omit it rather than stubbing it. |

`tests/test-adapter-descriptors.sh` checks that every one of the first
seven functions is defined (by `type -t`, after sourcing the file) — it
does not execute any of them. Behavioral coverage is your adapter's own
test file, next.

### The per-handle config-injection pattern (for any config-driven backend)

agy's `--gemini_dir` mechanism and OpenCode's `OPENCODE_CONFIG` env var
are the same pattern generalized: when a backend's permission model is
"point me at a config file", write a **fresh per-handle config** under
`$DIR` from inside `adapter_posture_args` (or a helper it calls), keyed
to `$POSTURE`, and point the backend at it via whatever mechanism it
reads config from (a flag, an env var). Refresh it on every call — start
*and* every resume — so a posture `--steal` is picked up automatically
rather than needing special-case handling. This is the mechanism to reach
for whenever a new backend's headless mode auto-denies or under-specifies
permissions the way agy's and OpenCode's both do; it beats trying to map
posture onto an interactive-only flag that turns out not to gate anything
headless (the mistake the design doc's §9.15 live-probe caught for agy's
`--mode`/`--sandbox`, before the current design already fixed it — worth
reading before assuming any interactive-looking flag actually gates
non-interactive/headless invocation).

## 3. The mock-CLI test pattern

Every adapter ships a mock binary + a test file, so its behavioral tests
never spend real API quota and never depend on what's actually installed
on the machine running the suite. Follow `tests/fixtures/mock-bin/codex`
and `tests/test-extdel-codex-resume.sh` as the template:

1. **Mock binary** (`tests/fixtures/mock-bin/<id>`) — a small shell script
   that understands just enough of the real CLI's flag surface to
   round-trip a turn: recognize `--version`/an auth-probe invocation,
   recognize start vs. resume, read the prompt (stdin or a positional
   arg, whichever the real CLI uses), emit the same *shape* of output the
   real CLI produces (JSON events for OpenCode's `--format json`, an
   answer file for codex's `-o`, plain stdout for agy), and honor a small
   set of `MOCK_<ID>_*` env knobs so tests can force failure modes:
   induced failure, induced sleep (for timeout tests), and — critically —
   an **exit-0-but-empty** mode (`MOCK_<ID>_EMPTY`), since every backend's
   `NO_OUTPUT` path needs a test that proves an exit-0 turn with a blank
   answer is never reported as `SUCCESS`.
2. **Test file** (`tests/test-extdel-<id>-resume.sh`) — puts
   `tests/fixtures/mock-bin` first on `PATH`, drives `extdel.sh start` /
   `prompt` / `status` / `slice` / `stop` against the mock, and asserts:
   a fresh `start` reaches `SUCCESS` with the mock's answer captured; a
   `prompt` resume reuses the captured session id; a posture mismatch on
   `prompt` (without `--steal`) is refused; the `MOCK_<ID>_EMPTY` case
   reports `NO_OUTPUT`, not `SUCCESS`; `stop` cleans up. Bash-3.2-safe,
   same constraint as the engine itself. Use `./tmp/...` scratch roots
   (never `/tmp`) per this repo's rule, with a `trap 'rm -rf "$TESTROOT"'
   EXIT`.
3. **`tests/test-adapter-descriptors.sh`** needs no changes — it already
   iterates every directory under `scripts/adapters/*`, so a new adapter
   is linted automatically the moment its directory exists.

## 4. `tested_versions` and going live

Don't add a real version string to `tested_versions` in `adapter.json`
until you've actually run the adapter against that real, installed
backend binary at least once (a `--probe-auth` pass via `list-backends`,
plus one live turn if you can spend the quota) — `"tested_versions":
["0.0.0-mock"]` or similar is an honest placeholder for "mock-only, not
yet verified against the real CLI", not something to backfill with a
number you haven't actually run. This mirrors how the codex and agy
adapters record their own tested versions — pin what you've verified, not
what you expect to work.

## 5. Checklist

- [ ] `scripts/adapters/<id>/adapter.json` — passes
      `tests/test-adapter-descriptors.sh`'s descriptor lint.
- [ ] `scripts/adapters/<id>/adapter.sh` — defines all seven required ABI
      functions (`adapter_check_identity_drift` only if genuinely needed);
      passes `bash -n`.
- [ ] `tests/fixtures/mock-bin/<id>` — mock CLI, including an
      exit-0-but-empty (`NO_OUTPUT`) mode.
- [ ] `tests/test-extdel-<id>-resume.sh` — behavioral coverage against the
      mock.
- [ ] `<id>` appears correctly in `extdel.sh list-backends` (installed,
      auth, postures/fidelity, sibling columns all sane).
- [ ] **Zero edits** anywhere else — the engine, other adapters, the
      runner, and the policy skill (beyond the routing table's own
      `sibling_plugins.relationship`-driven prose) shouldn't need to
      change for a new backend to work. If you found yourself editing
      `extdel.sh` itself, something about the new backend genuinely
      doesn't fit the `direct-cli` ABI — that's a signal to reserve a new
      `kind`, not to special-case the engine.
