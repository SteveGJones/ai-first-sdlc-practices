---
description: List registered delegation backends, whether each is installed/authenticated, and any sibling plugin available for it.
argument-hint: "[--probe-auth]"
---

Report the current backend registry for `sdlc-model-council`.

Do this:

1. Run:
   `${CLAUDE_PLUGIN_ROOT}/scripts/extdel.sh list-backends $ARGUMENTS`
   (pass through `--probe-auth` if the caller asked for a live auth check;
   otherwise run it with no arguments — this is a pure read-only report,
   no handle is created and no external-provider tokens are spent unless
   `--probe-auth` is explicitly requested).
2. Show the table as-is: id, vendor, installed, auth, kind,
   postures(fidelity), sibling.
3. For any backend reported `installed: no`, add a one-line install hint
   for the underlying CLI (e.g. `codex`: see OpenAI's Codex CLI install
   docs; `agy`: see Antigravity's install docs) — this plugin only wraps
   an already-installed binary, it does not install one.
4. For any row whose `sibling` column is `installed`, mention the matching
   sibling plugin's own slash commands as an alternative worth
   considering for that backend (`codex` → `/codex:review`,
   `/codex:adversarial-review`, `/codex:rescue`, `/codex:transfer`,
   `/codex:status`, `/codex:result`, `/codex:cancel`, installable via
   `/plugin install codex@openai-codex`; `agy` → `/antigravity:delegate`,
   `/antigravity:review`, `/antigravity:research`,
   `/antigravity:cloud-run-debug`, `/antigravity:status`,
   `/antigravity:result`, `/antigravity:cancel`, installable via
   `/plugin install antigravity@antigravity-for-claude-code`) — point to
   the `orchestration-policy` skill's routing table for when to prefer
   the sibling plugin over `/…:delegate`.
5. For any row whose `sibling` column is `absent`, still name the
   sibling plugin and its `/plugin install` command as an FYI, in case the
   caller wants the vendor-native depth it offers alongside this
   plugin's cross-vendor uniformity.
