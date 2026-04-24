# Retrospective: Cross-Library KB Query — Phase A Foundation

**Issue:** #167 (sub-1 of EPIC #164)
**Branch:** `feature/164-cross-library-kb-query`
**Status:** Implementation complete (2026-04-24)

## What went well

- TDD flow caught bugs early across multiple tasks: a conftest registration gap caught in Task 2 before any downstream test tried to use the new fixtures, regex edge cases in the priming bundle caught in Task 5 review, and the fail-open paths in the attribution tokenizer caught in Task 6 review. All bugs were found before integration, not after.
- Per-source attribution checking (validating each source's output separately before merging) turned out to be a justified improvement over the plan's joined-output approach. The tokenizer's between-block dropping behaviour would have been masked had we only validated the concatenated result.
- Subagent-driven code reviews consistently found real issues rather than style nits — three tasks had substantive fix-up commits driven by reviewer findings. This is the expected ROI when reviews are scoped to security-sensitive modules.
- The scripts package infrastructure (Task 1) and conftest fixture setup (Task 2) paid forward quickly: every subsequent test file was wired cleanly with no fixture boilerplate.

## What was harder than expected

- The attribution tokenizer rewrite (Task 6) required a complete rewrite from regex-based block extraction to a line-wise state-machine tokenizer. Four separate fail-open paths existed in the original regex design — none obvious until a reviewer mapped the markdown grammar corner cases systematically. The rewrite took more effort than the original implementation.
- The priming bundle regex also had three edge-case bugs (empty `## Knowledge Bases` section leaking the next section header, non-line-anchored term matching, empty terms line causing incorrect extraction) that all required post-review fix commits. Regex-based plan code should be treated as pseudocode until proven against a real markdown corpus.
- Plugin-directory sync drift accumulated across Tasks 1–13 as source files were added to `plugins/sdlc-knowledge-base/scripts/` one by one. A catch-up Task 14 was needed. Running `release-plugin` between tasks would have prevented this from becoming a block.

## What surprised us

- How many findings from code reviews in Tasks 2, 3, 5, and 6 were bugs in the PLAN itself rather than implementer errors. The plan was written with care but still contained regex patterns, algorithm sketches, and boundary assumptions that did not survive contact with real-world inputs. This is a systemic finding: plan-level code deserves adversarial review before implementation begins.
- The format version parser (Task 7) was the simplest module in the plan but produced zero review findings — validating that straightforward parsers with clear contracts are easy to get right the first time.
- The orchestrator integration test (Task 13) fell out naturally from the unit tests; there was no integration surprise because the module boundaries had been designed cleanly throughout phase A.

## What we'd do differently next time

- Write adversarial tests earlier for security-critical or parsing modules — especially anything in `attribution.py` that touches untrusted LLM output. A fuzzing-style test suite at design time would have surfaced the fail-open paths before implementation began.
- Run `release-plugin` (or at minimum `check-plugin-packaging.py`) between tasks, not only at the end. One-task drift is trivial to fix; thirteen-task drift requires a dedicated catch-up commit.
- Validate regex-based plan code against a real markdown corpus before handing it to an implementer. If plan code can't be easily unit-tested, it should be written as pseudocode with explicit "verify this against real inputs" annotations.
- Consider running `--pre-push` validation at task boundaries (e.g., every 3-4 tasks) rather than only at the end of a phase. The pre-commit binary absence would have been caught immediately rather than deferred to the final task.

## Metrics

- Implementation time: 1 session (2026-04-24)
- Tests added: 52 unit tests across 5 test files (test_kb_registry, test_kb_priming, test_kb_attribution, test_kb_format_version, test_kb_orchestrator) — all passing
- Commits on branch for this sub-feature: 22 (17 task implementation commits + 5 fix commits from code reviews), plus 1 design spec and 1 implementation plan = 23 total ahead of main
- Validation pipeline: 9/10 checks PASS (syntax, technical debt, architecture, type safety, security, logging compliance, static analysis, plugin packaging, unit tests); pre-commit hook check fails due to `pre-commit` binary absent from this environment — pre-existing environment limitation, not a phase A regression

## Decisions worth capturing in memory

- Per-source attribution check (versus joined-output check) is essential when the tokenizer may drop content between blocks. Always validate source outputs individually before merging.
- The librarian prompt must explicitly forbid `---` (horizontal rule) inside findings sections — the tokenizer uses `---` as the source-block delimiter and the separator cannot appear inside a block.
- A line-wise state-machine tokenizer beats regex for markdown block boundaries. Regex cannot reliably handle nested constructs (fenced code with `#` headings, `---` inside code blocks, multi-paragraph findings).
- User-scope JSON registry at `~/.sdlc/` is the correct home for corporate library paths. Project-scope activation (`.sdlc-kb-libraries.json`) references registry entries by name only — paths never appear in the project repo.
