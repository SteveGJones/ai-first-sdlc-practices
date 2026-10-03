# Retrospective: Cross-Library KB Query — Phase C Synthesis

**Issue:** #169 (sub-3 of EPIC #164)
**Branch:** `feature/164-cross-library-kb-query`
**Status:** Complete

## What went well

- All Phase A scaffolding (`check_synthesis_attribution`, `valid_handles` parameter, librarian SOURCE_HANDLE) was usable as-is — Phase C was purely activation work with no structural changes to the Phase A foundation.
- Three new orchestrator helpers (`is_synthesis_query`, `format_synthesis_prompt`, `run_synthesis_query`) compose cleanly: each is independently testable, and `run_synthesis_query` just orchestrates them. The separation made both implementation and testing straightforward.
- Attribution post-check from Phase A caught bogus `[TODO]` / `[0]` handles in test cases — reuse of the validator with `valid_handles` whitelist gave synthesis-grade rigour for free, validating the Phase A investment.
- Plugin-dir vs root-source pattern: the lesson from Phases A/B was applied correctly, with no regression in Phase C.
- Phase C completed in 7 tasks, identical shape to Phase B, confirming the pattern is stable.
- 72/72 tests pass across the full Phase A+B+C test suite; 352 total tests across the project all pass.

## What was harder than expected

- `format_synthesis_prompt` required careful prompt engineering — the librarian needs explicit "no file reading", "tag every claim with `[HANDLE]`", and "name cross-library spans" instructions to produce attribution-clean synthesis output. Getting the prompt phrasing right to avoid hallucinated handles took iteration.
- Deciding the right behaviour for single-source-with-findings edge case: landed on a silent skip (`synthesis_attempted=False` with `fallback_reason`), not an error, because a single-source result is a valid retrieval outcome and synthesis adds no value there.

## What surprised us

- Phase C completed in 7 tasks — same as Phase B. The Phase A foundation paid off in spades: what looked like the hardest sub-feature (actual synthesis) was in practice activation + prompt engineering + 15 new tests.
- Synthesis dispatcher signature `Callable[[str], str]` is simpler than retrieval's `Callable[[DispatchRequest], str]` because synthesis is a single call with a pre-formatted prompt, with no per-source iteration needed.
- The `valid_handles` whitelist approach generalises cleanly: the same attribution validator used for retrieval correctness also enforces synthesis correctness — one code path, two guarantees.

## What we'd do differently next time

- Consider building adversarial tests for synthesis attribution in Phase A rather than Phase C — they would have caught the regex fail-open during Phase A, before Phases B and C built on it. The fix happened at the right point, but catching it earlier would have been cleaner.
- The implementation plan documents (stored in `docs/implementation-plans/`) were valuable scaffolding — continue the practice for all EPIC sub-features.

## Metrics

- Implementation time: 7 tasks (same cadence as Phase B)
- Tests added in Phase C: 15 (5 in T1 `is_synthesis_query`, 4 in T2 `format_synthesis_prompt`, 6 in T3 `run_synthesis_query`)
- Total tests in Phase A+B+C suite: 72 (21 registry + 7 priming + 14 attribution + 5 format_version + 25 orchestrator)
- Total project tests: 352 (all passing)
- Commits on branch for Phase C: 7 (1 plan + 5 feat + 1 retrospective scaffold) + this retrospective commit
- Total commits on branch (all three phases): 40
- Validation pipeline: 9/10 PASS (pre-commit hook absent from CI path — same known env issue as Phases A and B; all other checks pass)

## Decisions worth capturing in memory

- **Synthesis dispatcher shape**: takes a formatted prompt string `str`, not a `DispatchRequest` — different shape from retrieval because there is no per-source iteration; the prompt is assembled once and sent as a single call.
- **`valid_handles` for synthesis**: derived from the dispatch sources (the SOURCE_HANDLEs of libraries that returned findings). This is what makes `[TODO]` / `[0]` / un-whitelisted handles fail attribution post-check, giving synthesis the same correctness guarantee as retrieval.
- **Synthesis failure always preserves retrieval output**: when synthesis fails (attribution check, dispatcher error, or single-source skip), the retrieval output block is always preserved with an error/skip block appended — never silently downgrades to "no answer".
- **Phase D (RemoteAgentSource)** becomes a separate future EPIC. EPIC #164 v1 (foundation + priming + synthesis) is feature-complete on this branch.
