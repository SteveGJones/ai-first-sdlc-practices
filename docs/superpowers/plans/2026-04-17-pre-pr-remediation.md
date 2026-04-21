# EPIC #96 — Pre-PR Remediation Plan (Full Billy Wright)

**Branch**: `feature/96-sdlc-workflows`
**Date**: 2026-04-17
**Intent**: Resolve **every** finding across the six dimensional reviews before PR to main. Nothing deferred as "follow-up only" unless it is genuinely out-of-scope for the EPIC itself (e.g., CI/CD automation for Docker images — a separate EPIC per the Phase 5 spec).
**Source reviews**: `reviews/2026-04-17-{security-architect,solution-architect,devops-specialist,code-review-specialist,documentation-architect,agile-coach,swot-synthesis}.md`

## Principles

- **No `--no-verify` commits, no skipped checks.** Every commit must pass pre-push validation.
- **No TODOs or `# type: ignore` introduced.** Every existing one gets a written justification or is removed.
- **Each session ends green**: all 10 pre-push checks pass before ending a session.
- **One commit per coherent change.** The final PR will be readable phase-by-phase AND theme-by-theme.
- **Tests before fixes** for the behavioural gaps (model:, parallel merge, signal cleanup). Write the failing test, then make it pass.

Total items: **73 distinct findings** across 6 reviewers after cross-review deduplication.

---

## Session 1 — Constitutional compliance & lint unblock (CI-green session)

Goal: this branch must satisfy the repo's own rules before it asks others to. By end of session: feature proposal, retrospective, Phase 1-3 specs committed; plugin packaging fixed; mechanical lint violations cleared; `--pre-push` green.

### 1.1 SDLC artifacts (Agile CRITICAL)

- [ ] **1.1.1** Write `docs/feature-proposals/96-containerised-workers.md`. Must document the four original Phase 2 problems, the 5-phase delivery approach, final scope delivered, and the explicit deferrals (CI job, SBOM, image signing). *(AC-C-1)*
- [ ] **1.1.2** Write `retrospectives/96-containerised-workers.md`. Include: went-well list, went-badly list (`--read-only` reversal, tmpfs/mount ordering, Phase 5 thin integration coverage), surprises (Bun ARM64 segfault, Archon bug #1126, Keychain-under-tmpfs), metrics (87 commits, 4.5:1 fix-to-test ratio, 27 explicit `fix(...)` commits), decisions-to-revisit (EPIC-size PR strategy). *(AC-C-2)*
- [ ] **1.1.3** Commit the Phase 1, 2, 3 design specs currently untracked. Verify presence in `docs/superpowers/specs/` and that all phase specs are coherent with as-shipped code. *(AC-C-3)*
- [ ] **1.1.4** Add test-count reconciliation subsection to the retrospective: of the reported 158 unit tests, ~30 pre-existed; call out "tests added by this EPIC". *(AC-M-15)*

### 1.2 Plugin packaging (Documentation CRITICAL)

- [ ] **1.2.1** Update `release-mapping.yaml` for `sdlc-workflows` to include: all 7 skills (`author-workflow`, `deploy-team`, `manage-teams`, `teams-status`, `workflows-setup`, `workflows-run`, `workflows-status`), all 14 scripts in `plugins/sdlc-workflows/scripts/` (Python + shell), the full `docker/` tree (Dockerfiles, entrypoint, compose, build-*.sh, apply-patches.sh), `docs/quickstart.md`, `docs/troubleshooting.md`. *(DOC-C-1)*
- [ ] **1.2.2** Decide source-of-truth for new skills. Either (a) create repo-root `skills/{author-workflow,deploy-team,manage-teams,teams-status}/` with the current plugin files as copies OR (b) update `tools/validation/check-plugin-packaging.py` to accept plugin-only skills for `sdlc-workflows` and document the new convention. Preference: **(a)** — keep the existing source→plugin convention. *(DOC-C-2)*
- [ ] **1.2.3** Run `python tools/validation/check-plugin-packaging.py` — must pass cleanly. *(DOC-C-1 verification)*

### 1.3 Mechanical lint fixes (Code Review IMPORTANT + MINOR)

- [ ] **1.3.1** Remove unused `shlex` import at `preprocess_workflow.py:19` OR apply `shlex.quote` (the proper fix — see 4.1.1, deferred to session 4 because it has design consequences). Decision: keep the import, implement in 4.1.1. For session 1, add `# noqa` is NOT acceptable — leave the import and ensure 4.1.1 lands before `--pre-push`. *(SA-I-1 / CR-I-2 / S-I-6)*
- [ ] **1.3.2** Remove duplicate `import tempfile` at `resolve_credentials.py:163`. *(CR-M-2)*
- [ ] **1.3.3** Remove 6 unused `pytest` imports across test files — identify via `ruff check`. *(CR-M-3)*
- [ ] **1.3.4** De-duplicate "No secrets in images" bullet at `CLAUDE-CONTEXT-workflows.md:193-194`. *(SA-M-2 ≡ DOC-M-12)*

### 1.4 Session exit criteria

- [ ] `python tools/validation/local-validation.py --pre-push` green on all 10 checks
- [ ] `python tools/validation/check-plugin-packaging.py` green
- [ ] `git log --oneline main..HEAD` shows session-1 commits are atomic and properly labelled (`docs:`, `fix:`, `chore:`)

---

## Session 2 — Logging compliance & package layout

Goal: close the 63-violation logging gap properly (not by exempting the checker), and retire the import shim.

### 2.1 Logging compliance (Code Review IMPORTANT)

- [ ] **2.1.1** Add `logging` module usage across the 14 new scripts. Instrument Article 7's 10 mandatory points in the scripts where they apply. For CLI-entrypoint scripts, that means: start-of-run, input validation, external call (e.g., subprocess, docker), error, completion. *(CR-I-1)*
- [ ] **2.1.2** Add security-event logging specifically at `resolve_credentials.py:129` (credential selection) and `generate_team_dockerfile.py:255` (team image generation). These are the audit-trail-critical points. *(CR-I-1 detail)*
- [ ] **2.1.3** Ensure no secret, token, or PII is logged. Grep `resolve_credentials.py` and related files post-change for `cred`, `token`, `key`, `secret`, `password` appearing in log strings. *(Article 7 hard rule)*
- [ ] **2.1.4** Run `python tools/validation/check-logging-compliance.py plugins/sdlc-workflows --threshold 0` — must pass.

### 2.2 Import shim retirement (Code Review IMPORTANT)

- [ ] **2.2.1** Create `plugins/sdlc-workflows/pyproject.toml` declaring `sdlc_workflows_scripts` as a package with entry points. *(CR-I-3)*
- [ ] **2.2.2** Reorganise `plugins/sdlc-workflows/scripts/` into a proper package (`__init__.py`, module layout).
- [ ] **2.2.3** Install in editable mode for dev (`pip install -e plugins/sdlc-workflows/`). Update `requirements-dev.txt` or equivalent.
- [ ] **2.2.4** Delete `plugins_sdlc_workflows_scripts.py` from repo root.
- [ ] **2.2.5** Remove `sys.path.insert` + `# noqa: E402` workarounds (3 sites per review).
- [ ] **2.2.6** Update any CI or test harness that depended on the shim.

### 2.3 Session exit criteria

- [ ] All 14 scripts use `logging` module
- [ ] `check-logging-compliance.py --threshold 0` green
- [ ] Import shim and all workarounds removed
- [ ] Full unit test suite passes: `pytest tests/`
- [ ] `--pre-push` green

---

## Session 3 — Design correctness (CRITICAL semantics)

Goal: close the two CRITICAL items where shipped code silently diverges from stated behaviour. Test-first.

### 3.1 `model:` field passthrough (Solution CRITICAL)

- [ ] **3.1.1** Write failing test in `tests/test_preprocess_workflow.py`: a node with `image:` and `model: claude-opus-4-6[1m]` should produce `docker run -e CLAUDE_MODEL=claude-opus-4-6[1m] ...`. *(SA-C-1, TDD)*
- [ ] **3.1.2** Add `model` to `_PRESERVED_FIELDS` in `preprocess_workflow.py:24`.
- [ ] **3.1.3** Wire `-e CLAUDE_MODEL=<value>` in `_build_docker_run`.
- [ ] **3.1.4** Update `entrypoint.sh:92` to pass `--model "$CLAUDE_MODEL"` when set.
- [ ] **3.1.5** Verify the 4 shipped workflow templates (`sdlc-feature-development.yaml`, `sdlc-bulk-refactor.yaml`, `sdlc-commissioned-pipeline.yaml`, plus the fourth) behave correctly with the new behaviour — spot-check by running one E2E.
- [ ] **3.1.6** Document the `model:` field in `CLAUDE-CONTEXT-workflows.md` schema section.

### 3.2 Parallel branch-merge workspace isolation (Solution CRITICAL)

- [ ] **3.2.1** Write failing test: two parallel nodes writing to `output.txt` should not clobber each other. Current behaviour: they share workspace and the last writer wins. *(SA-C-2, TDD)*
- [ ] **3.2.2** Implement pre-fork bash node injection in `preprocess_workflow.py`'s `transform_workflow` — create branch-scoped workspace directories before a parallel fan-out.
- [ ] **3.2.3** Implement post-merge bash node injection — reconcile or merge branch workspaces on join.
- [ ] **3.2.4** Topology analysis: detect fan-out/fan-in patterns. Cover: simple parallel, parallel with conditional, nested parallel (out of scope → error), `trigger_rule: any` vs `all`.
- [ ] **3.2.5** E2E parallel test must continue to pass AND the new test must pass.
- [ ] **3.2.6** Document the isolation contract in `CLAUDE-CONTEXT-workflows.md` AND Phase 4 design spec.

### 3.3 Source-vs-generated workflow reconciliation (Documentation CRITICAL)

- [ ] **3.3.1** Align `quickstart.md:126` and `workflows-run/SKILL.md:73` to use `.archon/workflows/.generated/<name>.yaml`. Source YAML must never be overwritten. *(DOC-C-3)*
- [ ] **3.3.2** Verify idempotency: `workflows-run <name>` twice in a row must succeed without manual cleanup.

### 3.4 `team_extend` schema visibility (Solution IMPORTANT)

- [ ] **3.4.1** Add `team_extend` to `CLAUDE-CONTEXT-workflows.md` schema with a clear note: "validated statically but no runtime effect in v1.0; runtime injection mechanism deferred to a future phase. Currently results in silent no-op at runtime." *(SA-I-2)*
- [ ] **3.4.2** Emit a warning in `validate_team_manifest.py` when `team_extend` is non-empty, pointing at the documentation.

### 3.5 Credential temp-file cleanup in workflows-run (Solution IMPORTANT)

- [ ] **3.5.1** In `workflows-run/SKILL.md` step 5, extract the `cleanup` path from `resolve_credentials.py` JSON result and `rm -f` it after the workflow run. Use a `trap` so it fires on failure too. *(SA-I-3 + DOC-M-16)*
- [ ] **3.5.2** Unit test for cleanup-on-error path.

### 3.6 Session exit criteria

- [ ] New unit tests for model passthrough, parallel isolation, credential cleanup — all pass
- [ ] E2E parallel test still passes
- [ ] `--pre-push` green

---

## Session 4 — Security hardening (close every IMPORTANT)

Goal: close every IMPORTANT item from the security review except those explicitly deferred by Phase 5 scope (SBOM, image signing, Trivy — those become follow-up issues with file references).

### 4.1 Shell-escape hygiene (Security / Code Review / Solution)

- [ ] **4.1.1** Apply `shlex.quote()` to `image`, `workspace`, `cred_mount`, `command_name`, `prompt_text` in `preprocess_workflow.py._build_docker_run`. *(S-I-6 ≡ CR-I-2 ≡ SA-I-1)*
- [ ] **4.1.2** Replace fixed heredoc sentinel `SDLC_PROMPT_EOF` with a per-invocation nonce (e.g., `SDLC_PROMPT_EOF_$(openssl rand -hex 8)`), OR reject prompts containing the literal sentinel. Preference: nonce. *(CR-I-2, S-M-9)*
- [ ] **4.1.3** Adversarial test: a prompt containing the literal `SDLC_PROMPT_EOF` must not break generation. *(CR-M-5)*
- [ ] **4.1.4** Adversarial test: workspace path with spaces must generate a valid `docker run` command. *(SA-I-1 validation)*

### 4.2 Container capability tightening (Security)

- [ ] **4.2.1** Add `chmod -R a-w /home/sdlc/.claude/agents/` and `/home/sdlc/.claude/skills/` in `generate_team_dockerfile.py:393-394`. Extends the Phase 2 recommendation #2 from plugins to agents + skills. *(S-I-2)*
- [ ] **4.2.2** Add `--security-opt no-new-privileges` in `preprocess_workflow.py._build_docker_run`. *(S-M-1)*
- [ ] **4.2.3** Add `--memory=4g --cpus=2` defaults to the generated `docker run` command. Configurable via manifest or env. *(D-M-7)*
- [ ] **4.2.4** Container smoke test: `touch /home/sdlc/.claude/agents/evil.md` must fail. *(S-M-3)*
- [ ] **4.2.5** Container smoke test: send SIGTERM, assert `.credentials.json` absent on subsequent filesystem inspection. *(S-M-4)*

### 4.3 Generated CLAUDE.md sanitisation (Security)

- [ ] **4.3.1** Apply the manifest-description sanitisation logic at `generate_team_claude_md.py:20-46` to `agent_descriptions` and `skill_descriptions` (lines 129-132, 143-146). *(S-I-3 / PI-2 residual)*
- [ ] **4.3.2** Second-pass prompt-injection detection for cross-model markers (`<|im_start|>`, `[INST]`, `<|system|>`, etc.). *(S-M-7)*
- [ ] **4.3.3** Emit SHA-256 of the generated team CLAUDE.md in `build-team.sh` output for audit. *(S-M-5)*
- [ ] **4.3.4** Expand the file-sanitisation test (`test_team_claudemd_generator.py:69-78`) into a dedicated security test suite with ≥5 injection vectors. *(AC-I-11)*

### 4.4 Credential surface narrowing (Security)

- [ ] **4.4.1** Narrow `entrypoint.sh:28-33` legacy `.claude-auth` shim: copy only `.credentials.json`, not `*`. *(S-I-7)*
- [ ] **4.4.2** Credential-freshness probe in entrypoint: if expiry is readable and imminent, emit a specific diagnostic before Claude even starts. *(S-M-6 / AC-I-8)*
- [ ] **4.4.3** Stale-credential detection in `resolve_credentials.py` with a specific error message (not the generic `authentication_error`). *(AC-I-8)*

### 4.5 Supply-chain pinning (Security / DevOps)

- [ ] **4.5.1** Pin Archon clone to a specific SHA in `Dockerfile.base:10`. Record the resolved SHA as a Docker LABEL at build time (`docker inspect` visibility). Document the upgrade process. *(S-I-4 ≡ D-I-1 ≡ AC-I-9)*
- [ ] **4.5.2** Digest-pin `node:22-slim` in `Dockerfile.base:14`. *(S-I-5)*
- [ ] **4.5.3** Pin `oven/bun:latest` to a specific tag. *(D-M-6)*
- [ ] **4.5.4** Verify `sed -i` patches in `apply-patches.sh` land — add post-sed grep that fails the build if the edit didn't apply and the skip-marker is absent. *(D-M-1)*

### 4.6 Path-traversal hardening (Code Review)

- [ ] **4.6.1** Add path-traversal normalisation in `validate_team_manifest.py` for `local:` references: `Path(p).resolve()` + ancestry check against `project_root`. *(CR-M-1)*
- [ ] **4.6.2** Adversarial test: `local: ../../etc/passwd` must be rejected. *(CR-M-5)*

### 4.7 Phase 5 design-spec reconciliation (Security / DevOps)

- [ ] **4.7.1** Update `docs/superpowers/specs/2026-04-17-phase5-production-hardening-design.md` to reflect that `--read-only` was intentionally dropped. Cite: Claude Code needs writable `~/.claude/` for plugin runtime state. Note the compensating controls (`--cap-drop ALL`, `chmod -R a-w` on plugins/agents/skills). *(S-I-1 ≡ D-I-3)*
- [ ] **4.7.2** Retarget `troubleshooting.md:43-55` "read-only file system" section to `chmod -R a-w` enforcement (or remove). *(DOC-I-10)*

### 4.8 Session exit criteria

- [ ] New security tests (evil.md, SIGTERM wipe, heredoc nonce, path traversal, cross-model PI, SHA-256) all pass
- [ ] Phase 5 spec + troubleshooting aligned with shipped code
- [ ] Supply-chain pins in place and documented
- [ ] `--pre-push` green

---

## Session 5 — Test coverage of Phase 5 & beyond

Goal: convert the hourglass test pyramid into a proper pyramid. Cover every Phase 5 surface the Agile review flagged.

### 5.1 Phase 5 integration coverage (Agile CRITICAL)

- [ ] **5.1.1** Add to `tests/integration/workforce-smoke/run-containers.sh`:
  - **SIGTERM exit time**: start container, `kill -TERM`, assert exit within 5s *(AC-C-4 / S-M-4)*
  - **Credential-wipe on exit**: verify `.credentials.json` absent on inspected container filesystem *(AC-C-4 / S-M-4)*
  - **Healthcheck transitions**: `docker inspect --format='{{.State.Health.Status}}'` reports `healthy` after startup; `unhealthy` when Claude binary is missing (mock scenario) *(AC-C-4)*
  - **Concurrent team instances**: two containers from the same team image run simultaneously without cross-contamination
  - **Stale base-image detection**: team manifest `updated` > image `image_built` triggers a rebuild warning

### 5.2 Adversarial & negative tests (cross-review)

- [ ] **5.2.1** Heredoc termination adversarial test (from 4.1.3) — live in `tests/test_preprocess_workflow.py`.
- [ ] **5.2.2** Path-traversal test (from 4.6.2) — live in `tests/test_team_manifest_validation.py`.
- [ ] **5.2.3** Concurrent append test for `override_logger.log_override` — document whether the log is serialisable or racy-by-design. *(CR-M-4)*

### 5.3 Test infrastructure (Agile IMPORTANT / MINOR)

- [ ] **5.3.1** Introduce `pytest` markers: `@pytest.mark.docker`, `@pytest.mark.credentials`, `@pytest.mark.slow`, `@pytest.mark.e2e`. Apply to relevant tests. *(AC-I-10)*
- [ ] **5.3.2** Add `pytest-cov` configuration; publish baseline coverage percentage in the retrospective. *(AC-I-6)*
- [ ] **5.3.3** Create `tests/integration/run-all.sh` with a common reporter. Support `--no-acceptance`, `--no-e2e`, `--no-docker` flags for fast-feedback loops. *(AC-I-7)*
- [ ] **5.3.4** Extract common bash backup/restore/cleanup logic from `run-e2e.sh` and `run-acceptance.sh` into `tests/integration/workforce-smoke/_lib.sh`. *(AC-M-13)*
- [ ] **5.3.5** Rename `tests/integration/workforce-smoke/run.sh` → `run-python-integration.sh` for accuracy. *(AC-M-12)*
- [ ] **5.3.6** Move or namespace `test_ai_friendliness.py`, `test_framework_validation.py`, `test_setup_smart_e2e.py` — they pre-exist the EPIC and inflate the headline count. Either `tests/framework/` subdir OR explicit exclusion from the EPIC-scope count. *(AC-M-14)*

### 5.4 Retrofit legacy test harnesses (Security MINOR)

- [ ] **5.4.1** Apply `--cap-drop ALL` to any Phase 1/2 test harnesses that `docker run` directly, OR document why they intentionally don't. *(S-M-2)*

### 5.5 Session exit criteria

- [ ] All new tests pass
- [ ] Coverage baseline recorded in retrospective
- [ ] `tests/integration/run-all.sh` functional
- [ ] `--pre-push` green

---

## Session 6 — Documentation & Claude-Code-readiness

Goal: every documentation IMPORTANT and MINOR resolved. The primary consumer is Claude Code, per `feedback_docs_for_claude.md` — every doc must be navigable from Claude's standard entry points.

### 6.1 Cross-linking & discoverability (Documentation CRITICAL / IMPORTANT)

- [ ] **6.1.1** Add "Skills" and "Further reading" sections to `CLAUDE-CONTEXT-workflows.md` — pointers to all 7 skills, quickstart, troubleshooting, Phase 4/5 design specs. *(DOC-C-4)*
- [ ] **6.1.2** Expand `CLAUDE.md` skill table (lines 102-104) to include `/sdlc-workflows:author-workflow`, `/sdlc-workflows:deploy-team`, etc. in logical order. *(DOC-I-5)*
- [ ] **6.1.3** Add sdlc-workflows entries to `AGENT-INDEX.md` — `delegation-coordinator` agent + reference to the plugin skill catalog. *(DOC-I-6)*
- [ ] **6.1.4** Rewrite `plugins/sdlc-workflows/README.md` to reflect the 7-skill surface, link to quickstart + troubleshooting, reference Phase 5 spec. *(DOC-I-7)*
- [ ] **6.1.5** Update CLAUDE-CORE.md context-loading table to include `CLAUDE-CONTEXT-workflows.md` with its trigger conditions.

### 6.2 author-workflow skill hardening (Documentation IMPORTANT)

- [ ] **6.2.1** Step 0: explicit `Read` of `CLAUDE-CONTEXT-workflows.md` — don't rely on Claude remembering. *(DOC-I-8a)*
- [ ] **6.2.2** Step 4: inline a literal 10-line workflow YAML template. *(DOC-I-8b)*
- [ ] **6.2.3** Step 6: name-collision check across existing workflows + invoke `tools/validation/check_workflow_teams.py` if present. *(DOC-I-8c)*
- [ ] **6.2.4** Step 8: offer `/sdlc-workflows:workflows-run <name>` as the "what's next" pointer. *(DOC-I-8d)*
- [ ] **6.2.5** Add `author-workflow` entry to the `plan-task` output in `manage-teams/SKILL.md`. *(DOC-M-17)*

### 6.3 Schema & reference consistency (Documentation IMPORTANT)

- [ ] **6.3.1** Resolve team manifest schema drift between Phase 5 spec (`base_image`, `team_extend`) and `CLAUDE-CONTEXT-workflows.md`. Pick the spec as source of truth; update context doc. *(DOC-I-9)*
- [ ] **6.3.2** Add troubleshooting sections for: stale team image, `unhealthy` container from Phase 5 healthcheck, credential staging copy failure (tmpfs-shadow symptom). *(DOC-I-11)*
- [ ] **6.3.3** Footer in `troubleshooting.md` linking back to context module + quickstart. *(DOC-M-13)*
- [ ] **6.3.4** Add "Reference implementation" pointer in quickstart to `tests/integration/workforce-smoke/run-e2e.sh`. *(DOC-M-14)*
- [ ] **6.3.5** Fix step-numbering in `workflows-setup/SKILL.md` (9h between 9e and 9g). *(DOC-M-15)*
- [ ] **6.3.6** Standardise `archon workflow run` (not `archon run`) throughout `workflows-run/SKILL.md`. *(SA-M-3)*
- [ ] **6.3.7** Use `${CLAUDE_PLUGINS_DIR:-$HOME/.claude/plugins}/installed_plugins.json` in `deploy-team` and `manage-teams` skill commands. *(SA-M-1)*
- [ ] **6.3.8** "Can Claude Code author a workflow from this?" walkthrough — manually simulate it once after all doc changes.

### 6.4 Session exit criteria

- [ ] Every doc item in the reviews closed or explicitly filed as a tracked issue with a note
- [ ] Internal link integrity check (`python tools/validation/check-broken-references.py`) green
- [ ] `--pre-push` green

---

## Session 7 — Infrastructure polish & residual MINORs

Goal: every remaining infrastructure MINOR item addressed. Nothing left on the cutting-room floor.

### 7.1 Docker build context

- [ ] **7.1.1** Add project-root `.dockerignore` excluding `.git`, `.worktrees`, `retrospectives`, `reviews`, `node_modules`, `__pycache__`, `tests` (where appropriate). *(D-I-2)*
- [ ] **7.1.2** Add plugin-level `.dockerignore` for `build-base.sh` to exclude `agents/`, `commands/`, `docs/`, `skills/`, `workflows/` from the base build context. *(D-M-2)*

### 7.2 Entrypoint hygiene

- [ ] **7.2.1** Add comment at `entrypoint.sh:10` explaining `kill -- -$$` is intentionally process-group-wide. *(D-M-3)*
- [ ] **7.2.2** Document `ARCHON_ARGS` env var behaviour at `entrypoint.sh:89` (single-string vs array). Decide array if multi-token args are real. *(D-M-4)*
- [ ] **7.2.3** Upgrade HEALTHCHECK to `claude --version`. *(S-M-8)*

### 7.3 Residual schema & reporting

- [ ] **7.3.1** Add `group:` reserved field to manifest schema with forward-compat note (Phase 2 recommendation, still outstanding). *(SA-M-4)*
- [ ] **7.3.2** Track CLAUDE.md mtime as staleness signal in `teams_status_report.py`. *(SA-M-5)*

### 7.4 Session exit criteria

- [ ] All MINORs closed or filed as tracked issues with reasoning
- [ ] `--pre-push` green
- [ ] Full test suite green

---

## Session 8 — Final validation & PR

Goal: open a PR that reviewers can actually review, with full traceability back to every finding.

### 8.1 Final pass

- [ ] **8.1.1** Clean `git log main..HEAD`. Commits should be atomic, conventional-commits style, phase-prefixed.
- [ ] **8.1.2** Run `python tools/validation/local-validation.py --pre-push`. All 10 checks must pass.
- [ ] **8.1.3** Run `python tools/validation/check-plugin-packaging.py`. Green.
- [ ] **8.1.4** Run the full integration suite: `tests/integration/run-all.sh`. All layers pass.
- [ ] **8.1.5** Do a final diff review: `git diff --stat main..HEAD` — expect 133+ files (plus this session's additions); sanity-check the count.

### 8.2 PR body (Agile CRITICAL)

- [ ] **8.2.1** Draft phase-indexed PR body with commit ranges per phase (Phase 1: `<sha>..<sha>`, etc.). *(AC-C-5)*
- [ ] **8.2.2** For each phase: link its spec, plan, representative unit tests, and integration test. *(AC-C-5 detail)*
- [ ] **8.2.3** "Security — Deferred to Follow-up" section listing SBOM, image signing, Trivy scan, plugin allowlist, `--dangerously-skip-permissions` replacement, CI build/scan workflow. Each with a filed issue number. *(S-I-8 / D-I-4)*
- [ ] **8.2.4** "Addressed / Deferred / Filed as issue" traceability table: one row per review finding, status + commit SHA or issue link.
- [ ] **8.2.5** Rollback strategy section: if the EPIC needs to be reverted, what's the procedure? (Likely: revert the merge commit; team images are rebuildable from base.)

### 8.3 Follow-up issues to file before PR (for visibility)

- [ ] **8.3.1** "CI workflow: build and scan Docker images" — includes Trivy/grype scan, image size budget, PR gate for `docker build`. *(D-I-4)*
- [ ] **8.3.2** "Archon ContainerProvider upstream integration tracking" — tracks coleam00/Archon#1197 + local patches. *(existing debt)*
- [ ] **8.3.3** "`team_extend` runtime injection mechanism design" — decide hard-enforcement vs prompt-injection trade-off; design the injection contract. *(SA-I-2 residual)*
- [ ] **8.3.4** "Remove legacy `.claude-auth` shim" — with migration plan for any existing deployments. *(S-I-7 residual)*
- [ ] **8.3.5** "Replace `--dangerously-skip-permissions` with settings-based allowlist" — closes BV-3/LP-1. *(security follow-up)*
- [ ] **8.3.6** "SBOM generation + image signing (cosign) + Trivy in CI" — supply-chain trio. *(S-I-8 detail)*
- [ ] **8.3.7** "EPIC-size PR retrospective and process change" — decide whether to keep single-PR-per-EPIC or move to phase-PRs. *(AC process)*

### 8.4 Open PR

- [ ] **8.4.1** `gh pr create` with the drafted body. Target: `main`. Title under 70 chars.
- [ ] **8.4.2** Self-assign. Request reviews from the 6 review dimensions (or their human proxies).
- [ ] **8.4.3** Announce in any relevant channel with the phase-by-phase changelog link.

---

## Cross-reference table — every review finding to its session

| Finding | Source | Session | Item |
|---|---|---|---|
| Feature proposal missing | Agile C1 | 1 | 1.1.1 |
| Retrospective missing | Agile C2 | 1 | 1.1.2 |
| Phase 1/2/3 specs untracked | Agile C3 | 1 | 1.1.3 |
| Phase 5 signal/cred/healthcheck tests | Agile C4 | 5 | 5.1.1 |
| PR body phase-indexed | Agile C5 | 8 | 8.2.1 |
| Coverage measurement | Agile I6 | 5 | 5.3.2 |
| Consolidated integration runner | Agile I7 | 5 | 5.3.3 |
| Stale-credential detection | Agile I8 | 4 | 4.4.3 |
| Archon pin | Agile I9 ≡ Sec I4 ≡ DevOps I1 | 4 | 4.5.1 |
| pytest markers | Agile I10 | 5 | 5.3.1 |
| Security test suite split | Agile I11 | 4 | 4.3.4 |
| Rename run.sh | Agile M12 | 5 | 5.3.5 |
| Extract _lib.sh | Agile M13 | 5 | 5.3.4 |
| Move pre-existing tests | Agile M14 | 5 | 5.3.6 |
| Test-count reconciliation | Agile M15 | 1 | 1.1.4 |
| release-mapping.yaml | Doc C1 | 1 | 1.2.1 |
| Skills source-of-truth | Doc C2 | 1 | 1.2.2 |
| quickstart vs workflows-run path | Doc C3 | 3 | 3.3.1 |
| Cross-links in CLAUDE-CONTEXT | Doc C4 | 6 | 6.1.1 |
| CLAUDE.md skill table | Doc I5 | 6 | 6.1.2 |
| AGENT-INDEX.md | Doc I6 | 6 | 6.1.3 |
| Plugin README | Doc I7 | 6 | 6.1.4 |
| author-workflow skill | Doc I8 | 6 | 6.2.1-4 |
| Manifest schema drift | Doc I9 | 6 | 6.3.1 |
| troubleshooting --read-only | Doc I10 | 4 | 4.7.2 |
| Troubleshooting sections | Doc I11 | 6 | 6.3.2 |
| Dedupe sentence | Doc M12 ≡ Sol M2 | 1 | 1.3.4 |
| Troubleshooting footer | Doc M13 | 6 | 6.3.3 |
| Quickstart ref impl pointer | Doc M14 | 6 | 6.3.4 |
| Step numbering | Doc M15 | 6 | 6.3.5 |
| Workspace cleanup trap | Doc M16 ≡ Sol I3 | 3 | 3.5.1 |
| author-workflow in plan-task | Doc M17 | 6 | 6.2.5 |
| Logging compliance | Code I1 | 2 | 2.1.1-4 |
| shlex + heredoc | Code I2 ≡ Sec I6 ≡ Sol I1 | 1,4 | 1.3.1, 4.1.1-4 |
| Import shim | Code I3 | 2 | 2.2.1-6 |
| Path traversal | Code M4 | 4 | 4.6.1-2 |
| Duplicate import tempfile | Code M5 | 1 | 1.3.2 |
| Unused pytest imports | Code M6 | 1 | 1.3.3 |
| Concurrent append test | Code M7 | 5 | 5.2.3 |
| Heredoc/traversal tests | Code M8 | 4,5 | 4.1.3, 4.6.2, 5.2.1-2 |
| Archon clone pin | DevOps I1 | 4 | 4.5.1 |
| .dockerignore root | DevOps I2 | 7 | 7.1.1 |
| Phase 5 spec | DevOps I3 ≡ Sec I1 | 4 | 4.7.1 |
| CI Docker job | DevOps I4 | 8 | 8.3.1 (follow-up) |
| sed post-check | DevOps M1 | 4 | 4.5.4 |
| Plugin .dockerignore | DevOps M2 | 7 | 7.1.2 |
| kill -- -$$ comment | DevOps M3 | 7 | 7.2.1 |
| ARCHON_ARGS doc | DevOps M4 | 7 | 7.2.2 |
| npm multi-stage | DevOps M5 | — | deferred (not worth now) |
| bun tag pin | DevOps M6 | 4 | 4.5.3 |
| memory/cpu defaults | DevOps M7 | 4 | 4.2.3 |
| Phase 5 spec update | Sec I1 ≡ DevOps I3 | 4 | 4.7.1 |
| chmod agents/skills | Sec I2 | 4 | 4.2.1 |
| Sanitise agent/skill descriptions | Sec I3 | 4 | 4.3.1 |
| Archon SHA pin | Sec I4 | 4 | 4.5.1 |
| node digest pin | Sec I5 | 4 | 4.5.2 |
| shlex.quote | Sec I6 | 4 | 4.1.1 |
| .claude-auth narrow | Sec I7 | 4 | 4.4.1 |
| Deferred supply chain in PR | Sec I8 | 8 | 8.2.3 |
| no-new-privileges | Sec M1 | 4 | 4.2.2 |
| --cap-drop legacy | Sec M2 | 5 | 5.4.1 |
| Evil.md smoke | Sec M3 | 4 | 4.2.4 |
| SIGTERM wipe smoke | Sec M4 | 4/5 | 4.2.5, 5.1.1 |
| SHA-256 CLAUDE.md | Sec M5 | 4 | 4.3.3 |
| Cred freshness | Sec M6 | 4 | 4.4.2 |
| Cross-model PI | Sec M7 | 4 | 4.3.2 |
| Healthcheck claude --version | Sec M8 | 7 | 7.2.3 |
| Randomise heredoc sentinel | Sec M9 | 4 | 4.1.2 |
| model: field | Sol C1 | 3 | 3.1.1-6 |
| Parallel merge | Sol C2 | 3 | 3.2.1-6 |
| shlex unused | Sol I1 | 1,4 | 1.3.1, 4.1.1 |
| team_extend schema | Sol I2 | 3 | 3.4.1-2 |
| Keychain cleanup | Sol I3 | 3 | 3.5.1-2 |
| CLAUDE_PLUGINS_DIR | Sol M1 | 6 | 6.3.7 |
| Duplicate sentence | Sol M2 ≡ Doc M12 | 1 | 1.3.4 |
| archon workflow run | Sol M3 | 6 | 6.3.6 |
| group: reserved | Sol M4 | 7 | 7.3.1 |
| CLAUDE.md mtime | Sol M5 | 7 | 7.3.2 |

**Total unique findings: 73. Session-assigned: 73. Deferred (post-PR follow-up issues): 7 (session 8.3).**

---

## Risk register

1. **Session 3 parallel branch-merge (3.2)** is the most complex change. If the topology analysis proves harder than expected, fall back to option (b) from the Solution review: document the shared-workspace limitation and ship. Document explicitly; don't silently ship.
2. **Session 2 pyproject.toml migration (2.2)** may break CI paths that depend on the import shim. Keep the shim present but deprecated until CI confirms green, then delete.
3. **Session 4 heredoc nonce (4.1.2)** is a behavioural change to generated bash. E2E parallel must re-run and pass.
4. **The retrospective (1.1.2)** must be honest. If we cannot explain a decision cleanly, the decision was wrong — surface it, don't hide it.

## Definition of Done

- All 73 items in the table above either completed and committed, or filed as a post-PR issue with explicit reasoning in the PR body
- `python tools/validation/local-validation.py --pre-push` — all 10 checks green
- `python tools/validation/check-plugin-packaging.py` — green
- `python tools/validation/check-logging-compliance.py plugins/sdlc-workflows --threshold 0` — green
- `python tools/validation/check-technical-debt.py --threshold 0` — green
- `tests/integration/run-all.sh` — every layer green
- PR body contains the traceability table from session 8.2.4
- Follow-up issues filed and linked (section 8.3)
- The EPIC ships as a complete, defensible unit
