# Critical Goal Review — EPIC #96 (Containerised Claude Code Workers)

**Date**: 2026-04-19
**Reviewer**: sdlc-core:critical-goal-reviewer
**Branch**: `feature/96-sdlc-workflows` (104 commits)
**Phase F task**: F.4 parallel specialist review

---

## Goal-Alignment Score

**HIGH** — The delivered scope directly fulfils the original goal's core promise: isolated, reproducible container workers orchestrated by a thin external scheduler, with skills that let a user dispatch work and recover merge-ready commits. Three of the four use cases named in the problem statement (parallel feature development, autonomous SDLC pipelines, secure sandboxed execution) have runnable infrastructure on this branch.

---

## Acceptance Criteria — 9-Check Smoke Test (Design Spec §6.3)

| # | Check | Status | Evidence |
|---|-------|--------|----------|
| 1 | Archon CLI installed and on PATH | Covered | `workflows-setup` SKILL.md steps 1-2; PATH-not-installed distinction explicit |
| 2 | `archon workflow list` shows `smoke-parallel-review` | Covered | `delegation-smoke/workflows/smoke-parallel-review.yaml` present; `workflows-run` step 2 checks workflow exists |
| 3 | SDLC plugins installed | Covered | `Dockerfile.base` + entrypoint install; validated by `setup-smoke` integration layer |
| 4 | Workflow starts without error | Covered | `delegation-smoke/run.sh` + `entrypoint.sh`; 6/6 sequential E2E + 8/8 parallel E2E proven |
| 5 | `review-structure` completes with output captured | Covered | `smoke-parallel-review.yaml` node def + `synthesise` uses `$review-structure.output` |
| 6 | `review-tests` completes with output captured | Covered | Same workflow; output passed to synthesis node |
| 7 | Both nodes ran concurrently (start times within 5 s) | **SOFT** | Parallel execution proven at E2E level; the 5-second wall-clock assertion from the spec is not encoded as a failing test. `delegation-smoke/README.md` lists "Nodes run concurrently" as a check but the `run.sh` does not assert timing. Pass/fail is visual inspection only. |
| 8 | `synthesise` produces valid JSON with all required fields | Covered | `smoke-parallel-review.yaml` `output_format` schema enforces required fields |
| 9 | Total duration < 10 minutes | Soft | No timeout assertion in `run.sh`; documented target only |

**Summary**: 7 of 9 checks are hard-verified. Checks 7 and 9 are documentarily present but rely on human observation rather than automated assertions. This is an honest limitation for a first-pass smoke test; it should be named explicitly in the PR body.

---

## Gaps That Are Real Blockers

### Blocker 1 — setup-team delegation detection is absent

The design spec (§5.1–5.3) commits to setup-team scanning for delegation signals (monorepo, large LOC, existing `.archon/`, Ralph configs) and presenting an explicit Archon recommendation prompt. The shipped setup-team SKILL.md (458 lines, fully read) contains zero references to Archon, archon, sdlc-workflows, delegation, or Ralph. A new user who runs `/sdlc-core:setup-team` on a large project gets no hint that delegated workflows exist. Discovery of the feature is entirely passive — the user must already know to look for `sdlc-workflows` in the marketplace.

This is a **blocker** because the design spec named this integration as the primary user entry point ("after plugin recommendations ... if delegation signals are present"). Without it, the user journey described in the original goal ("dispatch a team") has no guided on-ramp. The plugin itself is complete; only the discovery wiring is absent.

**Minimum fix**: Add a delegation signal check as a late step in setup-team (after step 12) that scans for `.archon/`, `ralph.yml`, `>3` independent package manifests, or `>50k LOC`, and if present, mentions `sdlc-workflows` and `/sdlc-workflows:workflows-setup` as an optional next step. This is additive and does not require re-architecting setup-team.

### Blocker 2 — No automated assertion that both parallel nodes actually ran concurrently

Check 7 of the 9-check smoke test is the only check that validates the unique value of this EPIC (parallelism). Every other check would pass even if Archon ran nodes sequentially. The current `delegation-smoke/run.sh` passes a single container through `docker run --rm`; parallel execution is validated indirectly through Phase 4 E2E tests but there is no timing assertion in the delegation smoke itself. If Archon regresses to sequential execution, the smoke passes.

**Minimum fix**: Capture node start timestamps from Archon logs inside `entrypoint.sh` and assert the gap is under 10 seconds. Even a rough `awk`-based check is better than none. Alternatively, document this explicitly as a known gap with a follow-up issue filed.

---

## Gap Worth Tracking (not a blocker)

### The `--read-only` drop is undocumented at the user-facing level

The decision to drop `--read-only` (Phase 5) is correctly narrated in the commit history and CLAUDE.md. However `CLAUDE-CONTEXT-workflows.md` and `quickstart.md` do not explain the security trade-off to users who may wonder why the container is not read-only. This is not a blocker but should be in the "what we got wrong" PR section and in the troubleshooting doc.

---

## Over-Delivers Worth Naming in the PR Body

1. **`loop.stages:` multi-stage cycle primitive** — the original design committed to `loop:` with `until:` for the implement node only (single-stage retry). The delivered `loop.stages:` preprocessor extension handles multi-stage designer→dev→review cycles as a first-class primitive, including termination-signal detection (READY_TO_SHIP) and a soak test with smoke + real modes. This exceeds the spec.

2. **REST + SQLite dual-mode status with a standalone query helper** — the original spec said "Check running workflow" (a thin skill). The delivered `workflows-status` skill prefers a live REST API (`archon serve`) and falls back to direct SQLite reads with no Archon binary needed. This makes status observable in contexts where Archon is not on PATH, which is a common first-run scenario on macOS.

3. **Three-tier credential resolver with Keychain → volume → config fallback and cleanup traps** — the original design mentioned a named volume for credentials. The shipped resolver handles macOS Keychain extraction, Docker volume reuse, and config-file fallback with an `EXIT/INT/TERM` trap that removes staged credential files. The cleanup contract is more robust than the spec required.

---

## Recommended Reviewer Test Plan (10 minutes, no Claude API needed)

```bash
# Test 1 — Unit suite passes (1 minute)
python3 -m pytest tests/ -q
# Expected: 262 passed

# Test 2 — Preprocessor smoke: loop.stages generates correct bash (2 minutes)
cd tests/integration/workforce-smoke
bash run-loop-stages-soak.sh --smoke
# Expected: PASS — all stage assertions, terminates at iteration 3 not 5

# Test 3 — Credential resolver handles "no credentials" cleanly (30 seconds)
python3 plugins/sdlc-workflows/scripts/resolve_credentials.py \
    --project-dir /tmp --json
# Expected: JSON with tier=none and a human-readable error message, exit 0
# (Validates that the fail-safe path does not crash the skill)
```

These three commands require only Python, no Docker, no Archon, no Claude subscription. They validate the two most novel components (preprocessor, credential resolver) and the full unit coverage that protects everything else.

---

## Dogfood Evidence

The Phase F requirements spec (`docs/superpowers/specs/2026-04-19-phase-f-pr-open-requirements.md`) mandates four dogfood invocations (F.3) before the PR is opened:

1. `/sdlc-workflows:workflows-status --recent 5`
2. `/sdlc-workflows:workflows-status --run-id <any>`
3. `/sdlc-workflows:workflows-run` against an existing workflow
4. `sse_stream_follow.py` clean-fail + stream test

CLAUDE.md (worktree) reports "F.3 dogfood 1/4 done (workflows-status --recent 5 PASS)" in the session memory that shaped the branch. The security architect review (`reviews/2026-04-19-phase-f-security-architect.md`) is present, confirming F.4 was partially executed. No evidence in the branch that F.3 items 2–4 were completed or that the solution-architect and observability-specialist reviews were produced. These are pre-conditions of the Phase F acceptance criteria and should be verified before the PR is opened.

---

## Verdict

**APPROVE WITH CHANGES** — The core infrastructure is sound, well-tested at the unit level, and genuinely novel. Two items must be resolved before the PR opens: (1) file the setup-team delegation wiring as a tracked issue and reference it from the PR body as a named known gap (merging without this is acceptable only if the limitation is explicit), and (2) either add a timing assertion for parallel execution in the delegation smoke or document its absence as a filed issue. The over-delivers are real and strengthen the PR narrative.
