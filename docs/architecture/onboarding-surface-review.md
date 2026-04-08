# Onboarding Surface Design Review

**Scope**: discovery + install path
**Working theory**: process failure, not design failure
**Generalisation**: framework-wide rule
**Status**: Draft for review
**Date**: 2026-04-08
**Issue**: #128
**Authors**: Claude (AI Agent) and Steve Jones

---

## Executive summary

Between 2026-04-06 and 2026-04-08, four fixes landed on main touching the same onboarding surface. Each was a user-facing path bug that survived CI, PR review, and multi-week development cycles. Individually each fix was correct; the cumulative pattern is a design signal.

This review examines the pattern — not the individual fixes — and concludes that the root cause is **process, not code**. The design of discovery and the install path is fundamentally sound. The code after the four fixes is correct. The failure mode is that no one manually ran the documented user-facing path on a fresh client before any of the EPICs merged, because dogfooding happened via an internal dev path that bypassed the public install mechanism. CI tests file contents; CI does not exercise the user experience.

The prescriptive output of this review is a **framework-wide rule**: any skill, agent, plugin, or output-producing component whose primary consumer is a user must have its user-facing path manually verified on a fresh client environment before merge. Three enforcement layers implement the rule (CONTRIBUTING.md checklist, Constitution Article 12, automated test harness convention), and a concrete follow-on work list closes #128 cleanly.

---

## Part 1 — Pattern analysis

### 1.1 Opening framing

From 2026-04-06 to 2026-04-08, four fixes landed on main: #121, #123, #125, #130, closing issues #120, #122, #124, #129 respectively. All four touched the discovery and install path surface: either the marketplace configuration file, the `pipeline-orchestrator` agent's discovery output, or the `setup-team` skill's recommendation format. Each was caught by Steve manually testing the path after merge, not by CI, not by PR review, not by dogfooding during development. This part walks the four as a single pattern, because the individual fixes share a root cause that the individual retrospectives didn't fully surface.

### 1.2 The four fixes

#### Fix 1 — Issue #120 / PR #121: marketplace.json location

**What shipped wrong.** `/plugin marketplace add SteveGJones/ai-first-sdlc-practices` failed on a fresh install with `Error: Marketplace file not found at .../.claude-plugin/marketplace.json`. Claude Code clones the repo to `~/.claude/plugins/marketplaces/SteveGJones-ai-first-sdlc-practices/` and looks for `.claude-plugin/marketplace.json` at the cloned repo's root, but the file had been at `plugins/.claude-plugin/marketplace.json` since the plugin family launched.

**Root cause.** The original plugin migration design (#70) placed the marketplace manifest at `plugins/.claude-plugin/marketplace.json`, treating `plugins/` as the conceptual root of the plugin family. That was wrong against Claude Code's discovery convention. Four subsequent EPICs (#71, #82-83, #105) all touched the file without noticing, because none of them actually ran `/plugin marketplace add` against a fresh client.

**How it was discovered.** Steve ran the documented install command on two separate machines and got the identical failure. The public install path had never worked since day one.

#### Fix 2 — Issue #122 / PR #123: discovery output missing install instructions

**What shipped wrong.** Discovery produced a list of found tools with URLs and descriptions, but no installation instructions. The user had no guidance on how to install any of them, and different tool categories required different install paths (slash commands for plugins, `.mcp.json` snippets for MCP servers, workflow YAML for GitHub Actions, clone-and-run for standalone CLIs).

**Root cause.** The discovery report templates in `pipeline-orchestrator.md` and `skills/setup-team/SKILL.md` defined columns for tool metadata but had no Install column. A vague "(c) Provide installation instructions" step in the pipeline-orchestrator workflow was never actually produced, because the format wasn't specified and the agent had no reference for per-category install commands.

**How it was discovered.** Steve ran discovery after the plugin install path was fixed (PR #121) and found that the output was half-done — tools identified, nothing actionable.

#### Fix 3 — Issue #124 / PR #125: install field still skipped + tool categories mixed

**What shipped wrong.** After PR #123 added the install instructions category and format, verification showed two new problems: (a) the Install field was still not reliably produced — an agent following descriptive template language would skip it — and (b) project libraries (like `@modelcontextprotocol/sdk`, for building MCP servers in your own code) were mixed with Claude Code environment tools (like `@mongodb/mcp-server`, a pre-built server you install into Claude Code) in a single undifferentiated list.

**Root cause.** The #122 fix phrased the instructions as descriptive ("every tool gets an install instruction") rather than prescriptive ("Install field is MANDATORY, omit the entry if you cannot produce it"). And the seven-category taxonomy from #122 kept `library-framework` (Section B category) in the same output section as `mcp-server-npm` (Section A category), losing the distinction between "install into Claude Code" and "add to your project's `package.json`."

**How it was discovered.** Steve refreshed the marketplace after #123 and ran discovery again. He had to ask the agent explicitly for install instructions (the MANDATORY gap) and noticed that a library like `@modelcontextprotocol/sdk` was being recommended as if it were a Claude Code tool (the category mixing).

#### Fix 4 — Issue #129 / PR #130: coverage gaps not surfaced as custom agent options

**What shipped wrong.** After #125 split the output into Section A (Claude Code tools) and Section B (project libraries), the "build a custom agent for this topic" path was still buried as a vague whole-report "(c) Build custom" option at the end of the flow. The user couldn't see which specific topics warranted custom agents, what a custom agent would know, or how the research → build pipeline would work for each gap.

**Root cause.** The design had an implicit third case — topics where neither off-the-shelf tools nor libraries alone give the user what they need — but it was never surfaced as an explicit section in the output. The pipeline-orchestrator already had the full research → synthesis → agent-builder workflow; the gap was just that discovery wasn't presenting that capability as a per-topic option.

**How it was discovered.** Steve flagged it immediately after #125 merged: "there should be a section C which is then doing specific research to create project specific agents for those topics, which should be a choice the user can make."

### 1.3 Pattern statement

All four fixes share a single shape: each was a user-facing path bug where the observable defect was in output the user would see when running a documented command on a fresh client. CI passed on every one of them because CI tests file contents, schemas, and format conformance — it cannot run Claude Code commands against a live client. Each bug existed for at least one EPIC before being detected (and #120 existed for at least five EPICs). The common failure mode is not "the code was wrong." After each fix landed, the code was correct. The failure mode is that nobody ran the documented user-facing path on a fresh client before merge, so the gap between "what the file says" and "what the user experiences" was invisible to everyone involved.

### 1.4 Contributing factors

Five factors let the pattern persist undetected across four EPICs and multiple contributors:

- **Dogfooding bypassed the public install path.** `scripts/setup-dev-environment.sh` symlinks plugins directly from source into `.claude/skills/` and `.claude/agents/`. Contributors working on the framework had these symlinks in place, so they were always testing against their dev environment — never against `/plugin marketplace add`.
- **CI tests file contents, not user experience.** The pre-push and CI pipelines run validators, type checks, schema conformance, link checks, and format checks. They do not run Claude Code commands against a live client because Claude Code can't run inside GitHub Actions without interactive OAuth.
- **The Docker smoke test runs a different path.** `tests/integration/setup-smoke/` executes plugin install via `/plugin install --scope project` from a local clone of the repo, completely bypassing `/plugin marketplace add`. It validates that the plugin files *can* be installed, not that the documented marketplace add command actually works.
- **EPICs shipped without any owner running the public install path.** Five plugin-family EPICs (#70, #71, #82-83, #105) touched `marketplace.json` without anyone running `/plugin marketplace add SteveGJones/ai-first-sdlc-practices` on a fresh client. Each EPIC owner had their own dev environment already working and had no reason to test the path from scratch.
- **No individual contributor owned "what the first-time user sees."** Contributors each tested their own slice of the work via the dev environment. Nobody was responsible for the end-to-end user experience, so no one was checking whether the documented commands produced the documented outputs. The gap wasn't an individual's failure — it was an ownership gap.

---

## Part 2 — Framework-wide rule proposal

### 2.1 The rule

> **Any skill, agent, plugin, or output-producing component whose primary consumer is a human user or downstream agent must have its user-facing path manually verified on a fresh client environment before merge.**

Short, mandatory, unambiguous. Not hedged. Applies regardless of EPIC, contributor, or complexity.

### 2.2 What "user-facing path" means

A user-facing path is any command, invocation, or output that a human or downstream agent runs or reads as part of using the framework. Concrete examples and non-examples:

| Surface | User-facing? | Why |
|---|---|---|
| `/plugin marketplace add <repo>` + `/plugin install <plugin>@<marketplace>` | **Yes** | User runs these commands; output determines whether install succeeds |
| `/sdlc-core:setup-team` | **Yes** | Output is a recommendation the user acts on |
| `/sdlc-core:kb-query "what does research say about X"` | **Yes** | Output is evidence the user cites |
| `/sdlc-core:kb-init` with the starter pack | **Yes** | Creates files the user will edit and the `[Knowledge Base]` CLAUDE.md section the user reads |
| `@pipeline-orchestrator create a <topic> agent` | **Yes** | Output drives downstream agent creation the user decided to commission |
| `@research-librarian` query responses | **Yes** | Output drives user decisions |
| `python tools/validation/local-validation.py --pre-push` | **No** | Internal validator; output is pass/fail, not interpreted text |
| `release-plugin` skill (in-repo only) | **No** | Only invoked by maintainers; not part of any user path |
| CI workflow YAML files | **No** | Not user-facing; CI runs them, users don't |
| `tests/**` | **No** | Framework-internal |
| Documentation-only changes to README.md or CLAUDE.md when the text is explanatory (not instructions the user follows) | **No** | No executable path |
| Documentation changes to CLAUDE.md/CLAUDE-CORE.md instructions the user is expected to follow (e.g., install steps, commands) | **Yes** | If the user will run what's documented, the documented path is a user-facing path |

Tie-breaker: if you're unsure whether a change is user-facing, ask "will a user ever copy-paste something from this file, or read its output and act on it?" If yes, user-facing.

### 2.3 What "fresh client" means

"Fresh client" means an environment where none of the framework's prior state is cached or pre-wired. Specifically, either:

**Option A — Docker container** (preferred for reproducibility):
- Base image with Claude Code installed but no cached marketplaces, no enabled plugins, no pre-symlinked `.claude/` content
- The existing `tests/integration/setup-smoke/` Docker harness is the canonical fresh environment; future user-path tests extend it

**Option B — Local environment with explicit cache clear** (acceptable when Docker is impractical):
Before running the verification, clear the relevant state:
```bash
# Remove cached marketplace clone
rm -rf ~/.claude/plugins/marketplaces/<marketplace-name>

# Remove enabledPlugins entries from ~/.claude/settings.json for any sdlc-* plugins
# (manual edit; do not automate without confirmation)

# Remove any pre-symlinked dev content for the surface being tested
# (reversible via scripts/setup-dev-environment.sh later)
```

Neither "it works on my current machine" nor "I tested it in a different project where I already had things set up" counts as a fresh client. The point is to see what the first-time user sees.

### 2.4 Three enforcement layers

**(a) CONTRIBUTING.md checklist item — advisory, human-gated.**

Add a required section to any PR touching a trigger path (see 2.5). The PR description must include the user-path verification as a structured block:

```
## User-path verification

- **Surface touched**: <which user-facing path this PR affects>
- **Fresh client used**: <Docker container / local with cache cleared / N/A with exemption reason>
- **Commands run**: <list the exact commands, in order>
- **Output observed**: <summary of what appeared, or link to screenshot/transcript>
- **Result**: <pass / fail / known limitation with issue link>
```

The reviewer must confirm the verification was actually done before approving. An unfilled block is grounds to block the PR.

**(b) Constitution Article 12 proposal — mandatory for Production+.**

This review proposes adding a new article to `CONSTITUTION.md`. Draft wording (to be refined in the follow-on authoring issue):

> **Article 12: User-Facing Path Verification** [Production+]
>
> 12.1. Any change touching a user-facing path (skill output, agent response, plugin install flow, schema template the user edits, or documented command instructions) must be manually verified on a fresh client environment before merge.
>
> 12.2. Fresh client means either a Docker container with no cached framework state, or a local environment where cached marketplaces, enabled plugins, and pre-symlinked dev content have been explicitly cleared for the surface being tested.
>
> 12.3. The verification is documented in the PR description using the template from CONTRIBUTING.md section on user-path verification.
>
> 12.4. The reviewer must confirm the verification was actually performed, not just described, before approving the PR.
>
> 12.5. Exempt changes: emergency hotfixes where the fix IS the verification, typo-only changes in user-facing text, changes behind a feature flag that isn't enabled by default, PRs that touch only internal tests or CI config, and documentation that explains concepts rather than instructing the user to run commands. Each exemption must be justified explicitly in the PR description.

Actual authoring (integrating this into CONSTITUTION.md, firing the sync check, updating plugins/sdlc-core/skills/rules/constitution.md) is a follow-on issue, not in scope for this review.

**(c) Automated test harness convention — enforcement via tests.**

Establish a convention: every user-facing surface gets a test under `tests/user-path/<surface>/`. The test runs the real invocation (where feasible) and asserts on the output shape.

Directory layout:
```
tests/user-path/
  plugin-install/             # Docker: fresh client runs /plugin marketplace add + /plugin install
  setup-team-discovery/       # Mock tech stack: verifies Sections A/B/C are produced, Install fields populated
  kb-init/                    # Mock project: verifies [Knowledge Base] section appended to CLAUDE.md
  kb-query/                   # Against starter pack: verifies librarian returns structured evidence
  pipeline-orchestrator-discovery/  # Mock: verifies discovery report shape
  commission/                 # Mock: verifies commissioning questions + bundle installed (once EPIC #97 lands)
```

Each test's shape:
- **Preflight**: set up the fresh client state
- **Invoke**: run the user-facing command
- **Assert on output shape**: specific checks (e.g., "Section A heading present", "every tool has non-empty Install field", "no placeholder text like `{install snippet}` in output")
- **Teardown**: restore state if needed

The tests run in CI where possible (mocks and assertions) and manually in the Docker harness where Claude Code interaction is required.

### 2.5 Trigger conditions

Changes to files matching any of these paths trigger the user-path verification requirement:

- `.claude-plugin/marketplace.json`
- `plugins/**/.claude-plugin/plugin.json`
- `skills/setup-team/**`, `skills/kb-*/**`, `skills/commission*/**`, `skills/kb-init/**`, `skills/kb-query/**`, `skills/kb-lint/**`, `skills/kb-ingest/**`
- `agents/core/pipeline-orchestrator.md`, `agents/knowledge-base/**` (librarian, updater), any agent whose output is user-facing per the 2.2 table
- `CLAUDE.md`, `CLAUDE-CORE.md`, `CONSTITUTION.md` when touching text that the user reads or runs as commands
- Any file under `plugins/sdlc-*/` that mirrors a source file above (plugin copies)

A path-glob check in CI can detect whether a PR touches any of these and enforce the PR description template requirement (warning mode initially, blocking once the test harness is populated).

### 2.6 Exemptions

Explicit carve-outs to prevent the rule from being weaponised against legitimate changes:

- **Emergency hotfixes where the fix IS the verification.** If you're fixing a broken install path, running the install path IS the verification. Document the manual run in the PR description and proceed.
- **Typo-only changes in user-facing text.** A typo fix in the `[Knowledge Base]` template or a spelling error in a skill's output is exempt. Rule of thumb: if the change is < 10 characters and does not modify any instruction or command, it's a typo.
- **Feature-flagged changes.** If a change is behind a feature flag that is not enabled by default, the user-facing path is unchanged from the user's perspective. The verification is deferred until the flag is enabled.
- **Internal-only changes.** Tests, CI config, internal validators, release tooling. These affect the framework's own operations, not any user path.

Each exemption must be justified in the PR description ("exempt per Article 12.5 — typo-only fix in ... with the changed bytes shown"). Ungeneralised "I don't think this needs verification" is not an exemption; it's bypassing the rule.

---

## Part 3 — Follow-on inventory

### 3.1 Extensions to existing issues

- **#126 — Automated discovery output testing** — extend scope from "discovery output" to "every user-facing surface." The test harness grows to cover setup-team output, kb-query output, kb-rebuild-indexes output, any commissioning output once EPIC #97 lands. Acceptance criteria updated to reference the `tests/user-path/<surface>/` convention from Part 2 section 2.4(c). Comment the scope extension on #126 as an agreed change.
- **#127 — CONTRIBUTING.md PR review checklist** — extend scope from "discovery / setup-team / commissioning / install paths" to "all user-facing paths per the 2.2 table." The wording from Part 2 section 2.4(a) (the five-field PR template) supersedes whatever #127 originally specified. Comment the scope extension and update acceptance criteria.

### 3.2 New issues to file

**Issue A — Constitution Article 12 authoring.** Author the Article 12 text (using the draft in Part 2 section 2.4(b) as the starting point), add it to `CONSTITUTION.md`, verify the sync check to `plugins/sdlc-core/skills/rules/constitution.md` fires correctly, run `release-plugin` to sync the plugin copy, and verify CI passes. Blocked by #128 closure. Deliverable: a PR adding Article 12.

**Issue B — User-path test harness convention.** Document the `tests/user-path/<surface>/` convention as a first-class architecture concept: directory layout, test shape per surface type, Docker-vs-mock decision tree, how assertions work, how tests integrate into existing `pytest` / smoke test harness. Deliverable: convention doc at `docs/architecture/user-path-test-harness.md` plus one example test per surface type (plugin install via Docker, discovery output against a mock tech stack, knowledge base query against the starter pack). Related to but logically separate from #126 — #126 is implementation of specific tests; this is the convention they follow.

**Issue C — Path-glob CI check for user-path verification.** A GitHub Actions job that runs on every PR, checks whether any trigger paths from Part 2 section 2.5 were touched, and requires the PR description to include the user-path verification template from 2.4(a). Warning mode initially (not blocking) until the test harness is populated; then mandatory. Deliverable: a workflow file plus an optional bot check that parses PR descriptions for the required structured block.

### 3.3 Per-EPIC risk flags

Two existing EPICs need annotations (comments on their issues), not new issues:

- **#97 (Multi-Option Commissioned SDLC)** — commissioning produces user-facing output at multiple points: the commission skill's structured questions, the schema templates (per option), the per-option agent sets installed into the project, the `kb-init`-style project bootstrap. Every sub-feature that ships user-facing content needs user-path verification per the new rule. Comment on #97 flagging the dependency and noting that the test harness convention (new issue B above) should land before sub-features 6-7 (Programme, Assured) ship their user-facing surfaces — those sub-features will benefit most from having an established convention to follow.
- **#105 (sdlc-knowledge-base, merged)** — retroactive check. `kb-init`, `kb-query`, `kb-lint`, `kb-ingest` all produce user-facing output. The core branch merged without user-path tests per the new rule. Comment on #105 flagging this as a verification debt item: when `kb-init --with-starter-pack` is next run on a fresh client, document the output, verify it matches the schema template's intended format, and if there are gaps, file them as normal fix issues.

### 3.4 Optional future work

Not required for rule implementation, but worth considering while the context is fresh:

- A dedicated `onboarding-surface` GitHub label for tracking any PR or issue that touches the trigger paths from Part 2 section 2.5. Makes it easier to search for and audit user-facing path work.
- A standardised PR description template (auto-inserted via `.github/PULL_REQUEST_TEMPLATE.md`) with the user-path verification block pre-populated. Reduces forgetting.
- A "fresh client" Docker image published as a convenience base for manual verification runs, reducing the setup cost of running the rule for a one-off verification.

---

## Closing the review

This review's conclusion: **the discovery and install path design is correct.** The four session fixes produced code that correctly implements the design. What was wrong was the process — specifically, that no verification of the user-facing path on a fresh client was ever part of the merge criteria. The fix is not a code refactor; it is a rule (Part 2) plus the concrete work to implement and enforce that rule (Part 3).

Closing #128 involves: merging this review document to main, commenting the scope extensions on #126 and #127, filing the three new issues (A/B/C from section 3.2), annotating #97 and #105 with the risk flags from 3.3, and (optionally) adopting any of the items from 3.4. Once those actions are taken, #128 can close as completed.

If a fifth discovery fix arrives before Issues A, B, and C are done, that is a signal that the rule needs to be adopted more urgently than "as follow-on work." Until then, the framework-wide rule lives in this document and the three follow-on issues carry it forward.

---

## References

- Issue: #128
- Session fixes: #120/#121, #122/#123, #124/#125, #129/#130
- Related follow-ons: #126 (automated testing), #127 (PR checklist)
- Related EPICs at risk: #97 (commissioning), #105 (knowledge base, merged)
- Precedent review location: `docs/architecture/knowledge-base-pattern.md` (from EPIC #105)
