# Retrospective: EPIC #96 — Containerised Claude Code Workers

**Branch**: `feature/96-sdlc-workflows`
**Date**: 2026-04-18
**EPIC**: #96
**Phases delivered**: 1-5 (all)
**Scope**: three-tier Docker image model, team manifests with per-container enforcement, Archon DAG orchestration via bash-node preprocessing, three-tier credential resolver, production hardening, full documentation suite

## Context

Prior to this EPIC, delegation from Claude Code to sub-agents had no filesystem-level enforcement of team composition, no credential isolation between workflow runs, no clean way to run multiple specialist teams from the same machine, and no DAG orchestration layer. Skills could *declare* "use only these agents" but any agent installed on the host remained loadable — enforcement was prompt-level only.

The EPIC delivered a containerised execution model: team manifests declare plugins/agents/skills, an image builder produces a team-scoped Docker image that contains only the declared components (read-only, enforced by filesystem permissions), and an Archon DAG dispatches nodes to containers via a thin bash-node preprocessor. Credentials are staged at runtime and wiped on exit. The work was phased into five branches-on-a-branch across a single long-lived feature branch: containerised delegation design (phase 1), three-tier image model + team manifest schema (phase 2), workforce management and coaching (phase 3), Archon orchestration (phase 4), production hardening (phase 5).

## Metrics

- **87 commits** on `feature/96-sdlc-workflows` (measured via `git log --oneline main..HEAD | wc -l`)
- **133 files changed, +18,450 / -28** (measured via `git diff --stat main..HEAD`)
- **27 commits prefixed `fix(...)`** against **6 commits prefixed `test(...)`** — a 4.5:1 fix-to-test commit ratio, called out below as a process signal
- **5 phase specs + 5 phase plans** archived under `docs/superpowers/specs/` and `docs/superpowers/plans/`
- **7 pre-PR multi-dimensional reviews** archived under `reviews/2026-04-17-*.md` (security-architect, solution-architect, devops-specialist, code-review-specialist, documentation-architect, agile-coach, swot-synthesis)

## What Went Well

- **Bash-node preprocessing over executor patching was the right architectural call.** When Phase 4 started, the natural-looking path was to extend Archon's executor to understand `image:` fields and dispatch to Docker directly. Instead, the preprocessor walks the workflow YAML and rewrites any `image:` node into an equivalent `bash:` node running `docker run <flags> <image> <command>`. Archon sees only `bash:` nodes — a stable contract. This keeps the coupling to Archon internals paper-thin, survives Archon's upstream reshape risks, and let us ship parallel DAG execution without owning the executor.

- **Team manifest schema as the single declarative source worked.** `.archon/teams/<name>.yaml` with `schema_version: "1.0"`, `plugins[]`, `agent_descriptions{}`, `skill_descriptions{}`, optional `base_image` and `team_extend[]`, plus `image_built` and `updated` timestamps for staleness detection. One file per team; all of the build-pipeline inputs and all of the runtime discovery metadata in one place; validated by `validate_team_manifest.py`. Schema-versioned from day one so future v1.1/v2.0 changes can be detected cleanly rather than ambiguously diffed.

- **Three-tier image model (base → full → team) with `COPY --from=full`.** `sdlc-worker:base` is the immutable toolchain layer (Ubuntu + pinned Node + pinned Claude Code CLI + pinned Ralph + Archon cloned at build time). `sdlc-worker:full` is base + every host plugin — it's a *source* layer, not a runtime image. `sdlc-worker:team-<name>` is base + additive `COPY --from=full` of only the manifest-listed plugins, agents, and skills. No pruning at runtime; enforcement is achieved by never copying in what isn't declared. Reproducible, cache-friendly, and the team image is identical whether rebuilt on Apple Silicon or Linux (pinned base).

- **Credential three-tier fallback (Keychain → volume → config) is zero-config on Mac and extensible elsewhere.** The default Mac developer path extracts from the system Keychain (service `"Claude Code-credentials"`) into an ephemeral temp file per run, with a cleanup entry that the caller uses. The Docker-volume path (`sdlc-claude-credentials`, seeded by `login.sh`) is for Linux/headless/CI. The explicit-config path (`.archon/credentials.yaml` → `credential_path:`) is the escape hatch. All three converge on the same mount point (`/home/sdlc/.claude-creds/.credentials.json`) so the entrypoint has one contract regardless of tier.

- **Credential staging pattern (mount → `.claude-creds/` → entrypoint copies to `~/.claude/`) avoided the tmpfs shadowing bug.** Mounting directly to `/home/sdlc/.claude/.credentials.json` failed because the tmpfs on `~/.claude/` shadowed the bind mount. The fix — mount to `.claude-creds/` (a path outside the tmpfs), have the entrypoint copy at startup, trap on SIGTERM/SIGINT/EXIT to wipe — is now the documented pattern and the thing a new team member would copy without hesitation.

- **Security hardening stack is complete and layered.** `--cap-drop ALL` on every generated `docker run`, `no-new-privileges` implicit, non-root user `sdlc` (UID 1001), read-only bind for credential staging, `chmod -R a-w` on the plugins directory at build time (plugin enforcement via filesystem permissions, not a `--read-only` flag which broke Claude Code's writable `~/.claude/`), HEALTHCHECK, configurable `CLAUDE_TIMEOUT`, signal-handling trap. Each layer is cheap and the composition means a single layer failing does not compromise the containment.

- **Phase-indexed design specs and plans gave every session a spec to work against.** Each phase had a design spec authored before implementation started and a phase plan authored alongside. Reviewers could diff the specs to see the scope trajectory; implementers could re-ground after a context reset. The seven pre-PR specialist reviews could be written against the specs plus the code and converge on consistent findings because the intent was written down.

- **Phase 3 miniproject discipline produced high-quality coaching and fleet-visibility features.** Phase 3 adopted a full SDLC for its sub-scope — task tracker with CLAUDE.md, CONSTITUTION.md, src, tests, local agent — rather than free-styling within the larger branch. The result was strong coverage (155 unit tests + 8/8 Phase 3 smoke + 16/16 container smoke) and a manage-teams coaching skill and teams-status fleet visibility skill that both have a cohesive design.

- **Seven-dimension pre-PR review caught the contradictions the authors had normalised.** The SWOT synthesis surfaced that the branch was genuinely go-with-conditions: `model:` field loss in preprocessing (solution-architect CRITICAL), parallel-branch merge gap (solution-architect CRITICAL), feature proposal / retrospective / phase specs missing from the branch (agile-coach CRITICAL), release-mapping.yaml incomplete (documentation-architect blockers), 63 logging-compliance violations (code-review-specialist). Without the seven parallel reviewer agents we would have shipped with at least three of these untouched.

## What Went Badly

- **`--read-only` attempted twice and reversed twice.** Two separate phases tried to layer `--read-only` on the generated `docker run`. It broke Claude Code both times: the CLI needs a writable `~/.claude/` for plugin metadata, session state, and backups. Plugin *enforcement* was the actual goal; `--read-only` was the wrong mechanism. The correct mechanism — `chmod -R a-w` on `~/.claude/plugins/` at build time — achieves filesystem-level enforcement without breaking the CLI. The lesson: "read-only filesystem" is not a substitute for "read-only directory under a read-write filesystem" when the application needs to write elsewhere under the same parent. The second reversal was especially embarrassing because the first one was already documented. Documented explicitly in `CLAUDE-CONTEXT-workflows.md` so a third attempt doesn't happen.

- **Tmpfs/mount ordering bug cost a full session to diagnose.** Mounting credentials directly to `/home/sdlc/.claude/.credentials.json` failed silently because the tmpfs on `/home/sdlc/.claude/` was mounted *after* the bind. The symptom (credentials missing inside the container) looked like a Keychain extraction bug for several hours. The fix required an intermediate staging path (`.claude-creds/`) and an entrypoint copy step. The lesson: when two mount mechanisms target overlapping paths, verify with `mount` inside the container before assuming the application is at fault.

- **Phase 5 integration test coverage is thin relative to the scope of the hardening changes.** Phase 5 added cap-drop, signal handling, timeout, healthcheck, and credential staging — five interacting surfaces. The unit tests cover each in isolation; the 16/16 container smoke test runs end-to-end with defaults; the 7/7 acceptance test validates the happy-path with real Claude Code. There is no integration test that deliberately kills a container mid-run to prove the signal-trap credential cleanup fires, no test that drives the timeout to expiry to prove the forced exit cleans credentials, no test that runs with a deliberately corrupted credential file to prove the resolver falls through. This is documented as a known gap in the Phase 5 design spec and is flagged for follow-on work.

- **Fix-to-test commit ratio of 4.5:1 signals the test suite was following the fixes, not driving them.** 27 `fix(...)` commits vs. 6 `test(...)` commits over the life of the branch. Some of this is legitimate (tests were landed in bigger chunks under `feat:` commits, not separate `test:` commits) but the qualitative feel — that we were frequently pushing fixes in response to integration-test failures rather than landing a test first and then the implementation — is real. Phase 3's miniproject discipline was the counter-example: it had a task tracker and a clean TDD rhythm. Phases 1, 2, 4, 5 did not.

- **Branch length (87 commits, ~18,450 lines, 133 files) makes the PR genuinely hard to review.** Even with phase-indexed commit ranges and per-dimension reviews archived under `reviews/`, a reviewer is being asked to evaluate five phases of work in one merge. The pre-PR remediation plan explicitly documents the commit ranges and the SWOT synthesis bounds the risk, but this is an EPIC-size PR by any honest measure. Splitting into multiple PRs was considered and rejected (the phases are genuinely interdependent and splitting would require temporary scaffolding that would also need to be reviewed) — so the chosen mitigation is review-depth (seven specialists) rather than PR-size. Flagged as a decision to revisit at the framework level.

- **Feature proposal and retrospective were written after implementation rather than before.** The feature proposal (`docs/feature-proposals/96-containerised-workers.md`) and this retrospective were both authored on 2026-04-18 as part of the pre-PR remediation, not at the start of the branch. The phase specs *were* written before each phase's implementation started, so the intent was captured — but it was captured at phase granularity, not EPIC granularity. A proper EPIC-level proposal at the top would have been a better anchor for the pre-PR review cycle and would have made the seven specialist reviews converge faster.

- **Plugin-vs-repo-root skill drift was silently possible for four skills.** The author-workflow, deploy-team, manage-teams, and teams-status skills were authored directly under `plugins/sdlc-workflows/skills/` — breaking the framework convention that skills are authored at repo-root `skills/` and released into plugins via `release-mapping.yaml` + `check-plugin-packaging.py`. The packaging checker caught it as a missing release-mapping entry, but only at pre-PR time. The lesson: `release-mapping.yaml` should be updated as part of the same commit that introduces a new skill, not retroactively.

- **The host → image → container path rewrite for `installed_plugins.json` was fragile and took two iterations.** The first version attempted to mount the host's `installed_plugins.json` directly. That leaked host paths into the container's plugin discovery. The second version rewrites the paths at image build time. The right version is the second, but the first shipped briefly and produced hard-to-interpret "plugin not found" errors. Documented in the Phase 2 retrospective (inline within this branch) so the pattern is reusable.

## Surprises

- **Bun segfault on ARM64 host under x86_64 emulation.** Phase 1's first build ran fine on Linux-x86_64 and failed on Apple Silicon with an unhelpful Bun segfault. Root cause: the image's Bun binary was an x86_64 build being run under Rosetta; some code path was non-Rosetta-compatible. Fix: build the base image multi-arch (`linux/amd64,linux/arm64`) and pin Bun to a version with published ARM64 binaries. Cost: about half a session to diagnose, because the error surface ("segfault") said nothing about architecture.

- **Archon bug #1126 manifests as an infinite loop with no error.** A race between Archon's file-watching and the workflow-dispatch path causes certain workflows to re-enter the first node forever. It doesn't crash, doesn't log an error, and doesn't surface in any Archon health check — the user just sees the same container log line repeating. We could not fix this upstream on the branch's timeline, so `entrypoint.sh` ships a detector (`detect-loop-bug.sh`) and a workaround (`loop-workaround.sh`) guarded by a skip marker. The workaround is ugly; the alternative was to block the EPIC on Archon. Documented in the Phase 4 design spec and in the production troubleshooting doc with a link to the upstream issue.

- **macOS Keychain extraction fails under Docker's tmpfs default.** The first credential-resolver implementation wrote the extracted Keychain payload to `/tmp` and mounted it. On some Docker Desktop configurations `/tmp` is a tmpfs with a size smaller than the payload (rare but real), and on others the tmpfs lifetime didn't align with the container lifetime, causing the bind mount to disappear mid-run. Fix: write to a per-run directory under the workspace (not `/tmp`), clean up explicitly in the `cleanup` field returned by the resolver. Entire class of bugs: don't lean on the host's default temp location when you need the path to outlive the resolver invocation.

## Decisions To Revisit

- **EPIC-size PR strategy.** Even with the mitigations above (phase-indexed review, seven-dimension pre-PR specialist reviews, traceability table, archived reviews under `reviews/`), a single ~90-commit / ~18.5k-line PR is on the outer edge of what's reviewable. The framework-level question: should EPICs of this scale *require* a multi-PR merge train (with temporary scaffolding tolerated), or is "one feature branch, one PR, seven specialists" acceptable? The current EPIC made a case-specific answer (interdependent phases rejected the split); the framework-level answer is open. File as a follow-up process issue.

- **`--dangerously-skip-permissions` is a placeholder that must be replaced.** The entrypoint currently invokes Claude Code with `--dangerously-skip-permissions` because a proper settings-based allowlist was not designed in time for Phase 5. The flag is documented as a deferral in the feature proposal. The right long-term answer is a per-team allowlist baked into the image at build time. Separate issue.

- **`team_extend` runtime contract is only statically validated.** The manifest schema accepts `team_extend[]` and the validator checks the referenced team exists, but the runtime contract (how an extending team's container actually loads the extended team's agents/skills) is not yet designed. In v1.0 this is prompt-level only. Separate issue before a v1.1 schema.

- **Legacy `.claude-auth` shim should be removed.** The entrypoint retains a compatibility shim for an earlier credential-path scheme. No team manifest in this branch uses it. Keeping it around costs documentation surface and one more path for an attacker to probe. Remove in a follow-up after confirming zero external users.

- **CI/CD for Docker image build + Trivy scan + SBOM + cosign signing is explicitly deferred.** The EPIC ships the images as local-build only. A GitHub Actions pipeline that builds on tag, scans with Trivy, generates an SBOM, and signs with cosign is the obvious next step. Already noted as a separate issue in the feature proposal's Explicit Deferrals section.

- **Fix-to-test ratio instrumentation.** Phase 3 had a clean TDD rhythm and the other phases did not. The framework doesn't currently measure fix-to-test ratio per branch. A pre-push hook (or a CI check) that warns when a branch's `fix(...)` commits outnumber its `test(...)` commits by more than 2:1 would have prompted the correction mid-branch rather than at retrospective time. File as a framework-level ergonomic improvement.

## Test-count Reconciliation

The headline "158 unit tests + all integration layers" hides a provenance question: how many of the 158 tests were added by this EPIC versus how many pre-existed in the repository at the start of the branch?

- **Pre-existing tests on `main` at branch cut**: approximately 30 unit tests in `tests/` covering framework scaffolding (validation tooling, release mapping, template scaffolding).
- **Tests added by this EPIC**: approximately 128 unit tests across 12 new test files (`tests/test_coaching_signals.py`, `tests/test_container_installed_json.py`, `tests/test_override_logger.py`, `tests/test_preprocess_workflow.py`, `tests/test_resolve_credentials.py`, `tests/test_team_claudemd_generator.py`, `tests/test_team_extend_validation.py`, `tests/test_team_inventory.py`, `tests/test_teams_status_report.py`, `tests/test_workflow_team_validation.py`, and two smaller files for script-level helpers).
- **Integration suites added by this EPIC**: `tests/integration/workforce-smoke/` (7/7 pass for Phase 2), `tests/integration/team-smoke/` (8/8 pass for Phase 3), container smoke 16/16, acceptance 7/7, sequential E2E 6/6, parallel E2E 8/8.

The 128-tests-added figure is approximate — it counts every `def test_*` discovered by `pytest --collect-only` in the 12 new files. Exact count is auditable via `pytest --collect-only tests/test_*.py` on the branch tip.

## Lessons Learned

1. **Prefer a thin preprocessing shim over an executor patch when integrating with an upstream DAG engine.** The preprocessor treats Archon's `bash:` node as the stable contract. Archon can reshape its executor freely and our integration keeps working. Executor patching would have coupled us to Archon's internals and the upstream-reshape risk register would have been much longer.

2. **Filesystem-level enforcement beats prompt-level guidance, every time.** Team manifests could have been "declared intent" that the launcher shellscript enforced at dispatch time. Instead the team image *cannot contain* anything not declared, and the plugins directory *cannot be written* at runtime. A compromised agent inside the container has no agents it wasn't given; a well-meaning agent cannot `/plugin install` its way into privilege creep. This is the core value proposition of the EPIC and the choice that justifies the Docker complexity.

3. **A "source layer" image (`full`) consumed via `COPY --from=` is cleaner than a prune step.** Prune steps are subtractive and fragile: the team image starts from "everything" and deletes down to "declared". The `COPY --from` pattern is additive: the team image starts from `base` (nothing declared) and copies in only what's declared. Easier to audit, faster to build (layer cache), and impossible to get wrong by forgetting to prune something.

4. **A two-step credential mount (staging path → entrypoint copy) beats a direct mount when the destination lives under a tmpfs.** The tmpfs-shadowing bug is the canonical example. Generalise: when the container's runtime will mount other filesystems over the target path, stage outside the target tree and copy in from the entrypoint.

5. **Build the pre-PR multi-dimensional review into the EPIC's definition-of-done.** Dispatching seven specialist reviewers in parallel and synthesising via SWOT surfaced contradictions and gaps that the authors had normalised. The cost (one session) is cheap relative to the cost of shipping those gaps. Make it standard for any EPIC that spans >2 phases or >50 commits.

6. **Phase specs are cheaper than you think and more valuable than you expect.** Each phase had a design spec authored before implementation. The specs took roughly half a session each to write. They paid for themselves the first time a phase needed a context reset and the first time a reviewer asked "what was the intent here?". EPICs without phase specs would have been much harder to review and much easier to drift in.

7. **Mandate `release-mapping.yaml` updates in the same commit as new plugin-shipped files.** The four-skills-authored-in-plugin drift was invisible until pre-PR. A pre-commit hook that runs `check-plugin-packaging.py` in `--dry-run` mode against the staged files would have caught it at authoring time.

8. **If a test integration gap is documented in a design spec and deferred, it is a debt, not a decision.** Phase 5's thin integration coverage was "documented as a known gap" — which is honest, but the documentation doesn't make the gap less costly. File an explicit follow-up issue and size it; don't leave it as a passive deferral.

## Constitutional Compliance

The pre-PR remediation plan (`docs/superpowers/plans/2026-04-17-pre-pr-remediation.md`) captures all 73 findings from the seven reviews and maps them to eight sessions through to PR-ready state. Session 1 (this session) resolved the constitutional-compliance blockers: feature proposal, retrospective, phase specs copied to the branch, lint violations unblocked. Sessions 2-8 address the remaining findings from solution-architect (preprocessor fixes), documentation-architect (release-mapping completeness, quickstart, troubleshooting), code-review-specialist (logging violations, shlex, import shim), security-architect (remaining hardenings), devops-specialist (build-pipeline robustness), agile-coach (process debt), and final integration / PR packaging.
