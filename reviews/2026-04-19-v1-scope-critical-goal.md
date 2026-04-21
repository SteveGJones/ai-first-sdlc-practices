# Critical Goal Review — sdlc-workflows v1 Scope

**Date**: 2026-04-19
**Reviewer**: critical-goal-reviewer
**Mandate**: User-first scope review. Authority to cut. "The point of v1 is to be helpful."

---

## 1. User Mental Model — Who Are We Building For?

### Persona A: Solo Developer on a Mac ("just got Archon, want to delegate a PR review")

**What they want in hour one:**
1. Run a parallel code review on their current branch without switching contexts.
2. See output committed back to git, ready to squash or cherry-pick.
3. Know the pipeline finished and roughly what it found.
4. Not have to write YAML from scratch.
5. Trust that what ran is isolated from their main Claude session.

**What they probably don't want:**
- To understand Docker image inheritance before their first run.
- To configure credentials on a machine where `claude` already works.
- A coaching dashboard for a fleet they don't have yet.

### Persona B: Team Lead Wiring Delegation Into a PR Workflow ("owns multiple repos, wants parallel specialist reviews")

**What they want in hour one:**
1. A security review and an architecture review running in parallel, not serially blocking their PR.
2. Different agents in each review node — security team vs. architecture team — without hacks.
3. A way to verify the right agents actually ran (not just "Claude said something").
4. To reuse the setup across repos with minimal per-repo configuration.
5. Results they can show in a PR comment.

**What they probably don't want:**
- Loop/cycle primitives — they want a one-shot review pipeline, not a designer-dev-review cycle.
- Fleet management tooling for a team of two.

### Persona C: Demo Repo Explorer ("evaluating this for their org, trying it in a throwaway repo")

**What they want in hour one:**
1. To see a real end-to-end run complete without deep domain knowledge.
2. To understand what the plugin actually does vs. what Archon does.
3. A working "hello world" pipeline that produces visible, reviewable output.
4. Clear failure messages if prerequisites are wrong.
5. Confidence this isn't a maintenance burden they're signing up for.

**What they probably don't want:**
- Being asked to choose between three credential tiers on install.
- Anything that says "future work" or "v2 item" in the user-facing path.

---

## 2. Goal-to-Capability Mapping

### Goal 1: Run a delegated workflow that produces git-committed output

**Does what we ship help?** Yes — this is the core value. `workflows-run` handles credential resolution, preprocessing, Archon invocation, workspace management, and cherry-pick back to the user's branch. The logic is non-trivial and genuinely useful.

**Does Archon alone help?** Partially. Archon runs workflows, but it cannot inject credentials into containers (has no container execution at all), cannot produce a workspace that gets cherry-picked back, and has no per-node team isolation.

**Does our addition move the needle measurably?** Yes. This is the feature. Without us, a user authoring container-based workflow nodes would have to write the preprocessing, credential staging, workspace isolation, and cherry-pick logic themselves.

**Verdict: KEEP.** This is the reason the plugin exists.

---

### Goal 2: See a parallel review with specialist teams (security + architecture)

**Does what we ship help?** Yes — the DAG engine is Archon's, but our three-tier image model and team manifests are what make "security review node uses only security agents" true enforcement, not prompt suggestion. The fan-out parallel execution is proven.

**Does Archon alone help?** No. Archon has no container execution. Two parallel nodes would run sequentially in-process on the host, sharing the full plugin installation.

**Does our addition move the needle measurably?** Yes. Manifest-scoped plugin enforcement at the filesystem level is a meaningful security and reproducibility guarantee.

**Verdict: KEEP.** The three-tier Docker model and team manifests are load-bearing.

---

### Goal 3: Know what happened (did it finish, what did it produce)

**Does what we ship help?** Partially. `workflows-status` (REST + SQLite fallback) is genuinely useful. The per-node stderr lines in the terminal are what most users will actually watch. The troubleshooting doc is helpful.

**Does Archon alone help?** Yes — `archon workflow status`, `archon serve` UI at :3090, and stderr progress lines are all native Archon. `docker logs -f` is native Docker.

**Does our addition move the needle measurably?** Only at the margins. `workflows-status` adds SQLite fallback (useful when `archon serve` is not running) and the `--recent / --run-id` UX. The SSE follower (`sse_stream_follow.py`) adds nothing for CLI-launched runs — SSE only fires for server-launched runs, which is disclosed but still confusing to ship.

**Verdict: KEEP `workflows-status` (SQLite fallback is real value). CUT `sse_stream_follow.py` (adds confusion, not value, for the CLI use case we actually have).**

---

### Goal 4: Set up without having to understand the full system

**Does what we ship help?** The `workflows-setup` skill is genuinely thorough. But "thorough" and "simple" are not the same. The skill's health check (9 components, ARM64 patch status, loop workaround status, per-team staleness) is designed for a returning expert, not a first-time installer.

**Does Archon alone help?** `archon setup` covers its own credential configuration. We are the only path for the Docker/image part.

**Does our addition move the needle measurably?** Yes — the Archon PATH-vs-missing distinction, Docker availability detection, and the diagnostic step 9 are genuinely helpful first-time guidance. But the ARM64 patch status and loop workaround items in the health check expose internal mechanics that a v1 user has no context for.

**Verdict: KEEP the skill. REWORK health check to hide internal state (ARM64 patch, loop workaround) unless `--verbose` is passed. A user who gets a green health check should see 5 lines, not 9.**

---

### Goal 5: Author a new workflow without reading the YAML schema by hand

**Does what we ship help?** `author-workflow` is interactive and guides DAG design. It's the right idea.

**Does Archon alone help?** Archon has bundled templates. Ours add SDLC-specific prompts and team-aware structure.

**Does our addition move the needle measurably?** The tool exists and is correct. The question is whether a first-time user reaches for it. There is no mention of `author-workflow` in the quickstart's "Step 3" — the quickstart shows hand-written YAML. This is a documentation gap, not a capability gap.

**Verdict: KEEP. Fix quickstart to lead with `/sdlc-workflows:author-workflow` before showing the raw YAML.**

---

## 3. Goals NOT Served

These are things a realistic v1 user wants that we do not address well:

**3.1 Discovery: "I don't know this feature exists"**
The prior critical goal review (Phase F) already named this as Blocker 1: `setup-team` does not surface `sdlc-workflows` to users who would benefit from it. A solo dev on a monorepo gets zero guided path to this feature. This is not a v2 problem — it is a v1 problem because a feature no one discovers has zero user value.

**3.2 First-run happy path without YAML**
The quickstart's Step 3 drops the user into hand-written YAML before they've seen a single successful run. The `author-workflow` skill exists precisely to avoid this, but the quickstart doesn't use it. A user who encounters YAML first will bounce. The right v1 flow is: setup, run a bundled example, see it work, THEN author something custom.

**3.3 "What did the agents actually do?" post-run**
The cherry-pick brings commits back, but there is no skill or summary that reads those commits and explains what changed, what was reviewed, what the agents recommended. The user is left to read raw git log. For the "demo repo" persona especially, seeing a clean summary of what delegation produced would be the high-value moment.

**3.4 Cost transparency**
`author-workflow` warns about token costs for long cyclical runs. `workflows-run` does not warn at all. A first-time user dispatching `sdlc-feature-development` (a multi-hour pipeline on Opus) has no idea what it will cost until the bill arrives. This is a user-trust issue.

**3.5 Linux credential setup**
The three-tier resolver is macOS-first. Tier 2 (Docker volume via `login.sh`) exists but is not surfaced in setup or the quickstart's main path. A Linux user or a team lead on a non-Mac machine will hit "credential tier: none" with no guided recovery.

---

## 4. Capabilities WITHOUT Goals

These are things we ship that do not correspond to a top-ranked v1 user goal. They are candidates for cuts.

**4.1 `sse_stream_follow.py`**
SSE streaming only works for server-launched runs. CLI-launched runs (which is everything `workflows-run` does) write to SQLite and do not appear in the SSE stream. We ship a helper that follows a stream that is categorically empty for the use case we support. The PR body discloses this, but the script is still in the plugin. A user who finds it and runs it will see nothing, and wonder why.

Cut justification: zero user-visible value for CLI workflows. The disclosure in `CLAUDE-CONTEXT-workflows.md` is the right approach; the script is not needed alongside the disclosure.

**4.2 `teams-status` coaching signals for a user with zero teams**
The coaching infrastructure — tiered signals, `overrides.jsonl` tracking, fleet reporting — is designed for a team with multiple teams, multiple workflows, and weeks of operational history. A first-time user who installs the plugin has none of these. The skill's "no teams configured" path works, but the skill itself is invisible friction until the user has at least two teams and one workflow.

Not a cut — but this skill should not be in the "next steps" list shown after `workflows-setup`. It belongs in a "once you have teams" section.

**4.3 `loop.stages:` with multi-stage cycle primitive**
Genuinely novel engineering. But the v1 user who wants to delegate work is running a one-shot review pipeline, not a designer-dev-review cycle. The cycle use case requires: a real task description, multiple team types, many minutes per node, willingness to run unsupervised. That is not a first-hour use case. It is a power feature that adds YAML schema complexity (the `stages:` block is non-trivial to reason about) and a preprocessing code path that affects every containerised run.

Not a cut from the code — it works and is tested — but it should not be in the quickstart or in the suggested "next steps" after setup. Defer it to "advanced patterns" in `CLAUDE-CONTEXT-workflows.md` only.

**4.4 `manage-teams --plan-task` and `.archon/tasks/` record**
The task-planning mode generates a YAML file in `.archon/tasks/`. No other skill reads this file. No workflow references it. It is a paper trail with no consumer. A user who plans a task this way and then runs the workflow does not get any benefit from the task record.

Cut justification: the output has no consumer, so the feature adds steps without value. The node-assignment recommendation is genuinely helpful; that part should be folded into `author-workflow` (which is already the "design a workflow" skill) and the task record dropped.

**4.5 `workflows-setup` steps 9d (ARM64 patch) and 9e (loop workaround) in health check output**
These expose internal implementation details (a patch to Archon's Node.js runtime, a workaround for Archon bug #1126). A user who runs `--health-check` and sees "Loop workaround: active (Archon #1126 not yet fixed)" has no context for what this means. If it's active, fine — it means things work. If it's needed and not active, the build would have failed anyway. Surfacing this in the health check adds noise for normal users and mild alarm for careful ones who then google a bug number in a dependency's issue tracker.

Rework justification: move to `--verbose` output only. The default health check should be green/not-green, not a tour of internal workarounds.

---

## 5. First-Hour Simulation

As Persona A (solo dev, Mac, fresh install):

**Minutes 0-2: Install**
`/plugin install sdlc-workflows@ai-first-sdlc` — this works.

**Minutes 2-5: Setup**
`/sdlc-workflows:workflows-setup` — runs 9 steps including Docker image build (3-5 min actual). The PATH-vs-not-installed distinction for Archon is excellent; a user who hit this would otherwise lose 20 minutes. Win.

**Minutes 5-15: Docker build**
Build takes 3-5 minutes. The user waits. Nothing goes wrong on a Mac with Docker Desktop running. At the end: "SDLC delegated workflows are configured and verified. Next steps: 1. Run a parallel review: `/sdlc-workflows:workflows-run sdlc-parallel-review`". Good.

**Minute 15: Try to run `sdlc-parallel-review`**
The skill runs. Immediately: `Workflow 'sdlc-parallel-review' not found. Available workflows: (empty)`. 

Why? Because `sdlc-parallel-review` references `image: sdlc-worker:dev-team` and `sdlc-worker:review-team`. Neither image exists. `workflows-setup` builds `base` and `full`, not team images. The user does not have `.archon/teams/` set up. The workflow can't run.

This is the bounce point. The user goes from "verified, ready" to "not found error" in one command. Setup told them to run this workflow. It fails. There is nothing in the error output that says "you need to deploy a team first".

**Minute 20: Try to recover**
The user reads the quickstart. Step 2 says "Create `.archon/teams/my-team.yaml`". Now they're writing YAML. This is 15 minutes after installing. The YAML requires them to know which agents they want. They don't know that yet.

**Minute 30: Give up or ask for help**
Either the user runs `author-workflow` (not mentioned in the quickstart until the end), or they write the YAML by hand (requires prior knowledge), or they stop.

**Where they win:**
- The Archon PATH detection is excellent.
- The Docker build works cleanly.
- The credential detection on macOS (Keychain tier) is zero-config — if they get to a run, credentials just work.

**Where they bounce:**
- Setup points to a workflow that requires teams that don't exist yet.
- The quickstart drops users into YAML before showing them a working run.
- There is no bundled "hello world" team that works with `sdlc-parallel-review` out of the box.

**What would fix the bounce:** `workflows-setup` should either (a) also build a bundled starter team (`sdlc-worker:general-purpose`) that `sdlc-parallel-review` uses by default, or (b) tell the user explicitly: "Next step: create your first team with `/sdlc-workflows:manage-teams --create`" and NOT point them at `workflows-run` until a team image exists.

---

## 6. Recommendations

### KEEP list (genuinely helpful, ship as-is)

1. **`workflows-run` skill** — the core value proposition. The preprocessing, workspace isolation, credential injection, and cherry-pick logic are not replaceable by Archon alone.
2. **Three-tier Docker image model** — the enforcement guarantee (filesystem-level, not prompt-level) is the key differentiator.
3. **Team manifests schema v1.0** — declarative, validated, and the right abstraction.
4. **`workflows-setup` skill** — the Archon PATH detection alone saves users 20 minutes. Keep. Fix health check verbosity.
5. **`workflows-status` skill (REST + SQLite fallback)** — the SQLite fallback is genuinely useful in the common case where `archon serve` is not running.
6. **`author-workflow` skill** — correct approach to authoring. Fix quickstart to lead with it.
7. **`deploy-team` skill** — necessary complement to manifest authoring. Keep.
8. **`manage-teams --create`** — the guided Q&A for team creation is the right first-run experience. Keep; surface it earlier.
9. **Credential resolver (three-tier)** — Keychain tier is zero-config on Mac. Keep.
10. **Security hardening** (`--cap-drop ALL`, signal traps, rsync excludes, credential cleanup) — these are not visible to the user but protect them silently. Keep.
11. **`quickstart.md` and `troubleshooting.md`** — necessary. The troubleshooting doc in particular has the specific PATH and credential-tier fixes users will need.

---

### CUT list (no corresponding user goal, ranked by impact)

**Cut 1 (High impact): `sse_stream_follow.py`**
The SSE stream does not carry CLI-launched runs. Shipping a helper that follows an empty stream is misleading. The disclosure in `CLAUDE-CONTEXT-workflows.md` is the right place for this explanation. The script adds confusion, not value. Delete from the plugin.

**Cut 2 (Medium impact): `manage-teams --plan-task` task record (`.archon/tasks/`)**
The workflow recommendation from `--plan-task` is useful. The persisted YAML record has no consumer. Remove the file-write step; deliver the recommendation inline and offer to invoke `author-workflow` or `workflows-run` directly. No user goal is served by a YAML file nobody reads.

**Cut 3 (Low impact): ARM64 patch status and loop workaround status from default health check output**
Steps 9d and 9e in `workflows-setup --health-check` expose internal workarounds. Move to `--verbose` only. Does not require code deletion, just a conditional.

---

### REWORK list (right goal, wrong shape)

**Rework 1 (Critical): Post-setup next-steps messaging**
Current: "Next steps: 1. Run a parallel review: `/sdlc-workflows:workflows-run sdlc-parallel-review`"
Problem: This command fails unless a team image exists. Users have no team image after setup.
New shape: After setup, check whether any team images exist. If none: "Your first step: create a team with `/sdlc-workflows:manage-teams --create`. Once your team image is built, run `/sdlc-workflows:workflows-run sdlc-parallel-review`." If team images exist: current message is fine.

**Rework 2 (High): Quickstart structure**
Current: Step 3 drops users into hand-written YAML.
New shape: Step 3 should be "Instead of writing YAML by hand, run `/sdlc-workflows:author-workflow`." Show the hand-written YAML in a collapsible "manual alternative" section, or after the skill has been used once. The skill exists — use it in the getting-started path.

**Rework 3 (High): Cost warning in `workflows-run`**
Current: No cost warning at dispatch time.
New shape: Before launching any multi-node workflow (more than 2 nodes, or any node with `timeout > 600`), emit a one-line warning: "Multi-node workflow. Depending on model and task length, this may consume significant tokens. Proceed? (y/n)". This is one conditional, high user-trust value.

**Rework 4 (Medium): `teams-status` and `manage-teams` placement in "next steps"**
Current: Both are mentioned in `workflows-setup` next steps for all users.
New shape: Surface these only after the user has at least one team image built. Gate the mention on `ls .archon/teams/*.yaml 2>/dev/null | wc -l`. Zero teams: "First, create a team." One team: "Once you have multiple teams, `/sdlc-workflows:teams-status` shows fleet health."

**Rework 5 (Medium): `loop.stages:` in user-facing docs**
Current: `CLAUDE-CONTEXT-workflows.md` schema presents `loop.stages:` at the same level as `image:` and `depends_on:`.
New shape: Move `loop.stages:` to an "Advanced Patterns" section. Do not remove it — it is working and tested — but a first-time user reading the schema should not encounter it in the primary flow.

---

### MISSING list (goals not served, ranked by user impact)

**Missing 1 (Critical): Bundled starter team or working end-to-end example**
The gap between "setup complete" and "first successful run" is unbridged. Either ship a bundled `general-purpose` team manifest that `workflows-setup` builds automatically, OR ensure `sdlc-parallel-review` references only `sdlc-worker:full` (which IS built by setup) as its default image. This is the single highest-impact gap. Without it, Persona A bounces within 10 minutes of install.

Options (in order of preference):
1. Add a `general-purpose.yaml` team manifest to the plugin. `workflows-setup` builds it automatically. `sdlc-parallel-review` uses `sdlc-worker:general-purpose` by default. User runs one command after setup and it works.
2. Rewrite `sdlc-parallel-review` to use `sdlc-worker:full` (already built by setup) as a fallback when no team image exists.
3. Document it explicitly: "The bundled workflows require team images. Run `/sdlc-workflows:manage-teams --create` before your first workflow run." This is the weakest option but better than the silent failure.

**Missing 2 (High): `setup-team` does not surface `sdlc-workflows`**
Already identified in the Phase F critical goal review as Blocker 1. Persona B (team lead) runs `setup-team` on their monorepo and gets zero hint that delegated workflows exist. This is a discovery problem that cannot be fixed by improving the plugin docs — it requires adding a delegation-signal check to `setup-team`.

**Missing 3 (High): Post-run summary skill**
The cherry-pick brings commits back but there is no "what did delegation produce?" summary. Persona C (demo explorer) needs a moment where they see: "The design node proposed X. The dev node implemented Y. The review node flagged Z." Reading raw git log requires domain knowledge they do not have yet. A one-screen summary of what each node committed would significantly increase the "I understand what just happened" moment.

This is a "ship and follow up" candidate — the workflow can complete and produce value without it — but it should be filed as a named follow-up issue, not silently deferred.

**Missing 4 (Medium): Linux credential setup in the first-run path**
The `login.sh` script exists but is not mentioned in `workflows-setup` output when Tier 1 (Keychain) is unavailable. A Linux user hits "Credential tier: NONE" and has to read the quickstart carefully to find the recovery path. `workflows-setup` step 9g already detects the tier — when tier is NONE, it should surface the `login.sh` command directly.

**Missing 5 (Low): Cost warning at dispatch**
Covered in Rework 3. Filed here for completeness as a missing user protection.

---

## Priority Summary

| Priority | Action | Category | Impact |
|---|---|---|---|
| 1 | Bundled starter team or `sdlc-worker:full` fallback for bundled workflows | Missing | Blocks first successful run |
| 2 | Fix post-setup next-steps to not point at commands that require team images | Rework | Prevents immediate bounce |
| 3 | Surface `sdlc-workflows` from `setup-team` delegation signal check | Missing | Feature discovery for main audience |
| 4 | Cut `sse_stream_follow.py` | Cut | Removes misleading artifact |
| 5 | Fix quickstart to lead with `author-workflow`, not raw YAML | Rework | Reduces 15-min barrier to first custom workflow |
| 6 | Cost warning in `workflows-run` before multi-node dispatch | Missing/Rework | User trust |
| 7 | Move `loop.stages:` to advanced-patterns section | Rework | Reduces schema complexity for first readers |
| 8 | Post-run summary skill (file as follow-up issue) | Missing | "Aha moment" for demo persona |
| 9 | Health check: move ARM64/loop workaround to `--verbose` | Rework | Reduces expert-noise in default output |
| 10 | Cut `manage-teams --plan-task` task record | Cut | Removes no-consumer artifact |

---

## Honest Disclosure Check Against `.pr-body-phase-f.md`

The PR body is largely accurate. Three items need adjustment:

**Overclaim:** "five minutes" setup in the quickstart header. The Docker build alone takes 3-5 minutes on first run. The user needs to build a team image before running any workflow. Realistic first-run time to a working pipeline: 15-20 minutes minimum.

**Under-disclosed:** The PR body describes `workflows-run` as the main skill, but does not disclose that the bundled workflow (`sdlc-parallel-review`) cannot run on a fresh install without a team image. A reviewer who reads the PR body will not know that the first suggested post-setup command fails.

**Archon coverage:** The PR body accurately discloses the SSE blindness for CLI-launched runs. The disclosure is good. The `sse_stream_follow.py` script contradicts it by existing as a shipped artifact.

---

## Verdict

The core infrastructure (container isolation, preprocessing, credential resolver, cherry-pick workspace) is sound and genuinely helpful. The plugin earns its existence.

The risk is that v1 users never get to the core because the path from "setup complete" to "first successful run" has a broken bridge: `workflows-setup` succeeds, `workflows-run sdlc-parallel-review` fails silently on missing team image, and the recovery path requires writing YAML.

Fix Missing 1 and Rework 1 before opening the PR. Everything else can ship as-is, as a named follow-up, or as a cut on next pass. These two changes take an hour and turn "helpfulness theory" into "helpfulness practice."
