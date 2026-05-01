# Programme Bundle Review (Phase D) -- Independent Critical Review

**Reviewer:** Claude (independent review agent)
**Date:** 2026-04-29
**Bundle:** `plugins/sdlc-programme/` v0.1.0
**Scope:** Phase D deliverable of EPIC #178

---

## 1. Constitution overlay soundness

**Verdict: AGREE-WITH-CONCERNS**

Articles 12-14 are well-bounded and internally consistent with articles 1-11. They extend without contradicting: Article 12 adds phase-gate discipline on top of Article 5's validation pipeline; Article 13 adds cross-phase reference integrity (a stricter form of Article 10's "documentation must match code"); Article 14 adds mandatory review (complementing Article 9's self-review with human-in-the-loop structured review).

**Concern 1 -- Article 12 ambiguity on "incomplete"**: Article 12 states "Code may not be committed for a feature whose phase artefacts are incomplete." The word "incomplete" is not explicitly defined. The article does say "Each phase artefact has mandatory sections declared by its template" and "Missing mandatory sections block the corresponding phase-gate validator," which partially addresses this -- incompleteness means missing mandatory sections. However, what counts as a "non-empty" mandatory section is left to the validator implementation. A section containing only whitespace or a single placeholder word could pass if the validator only checks for section existence. This is a minor gap rather than a blocking issue; the validator implementation (spec_parser.py) currently does not check for non-empty sections at all -- it only checks for feature-id and declared IDs. The constitution promises more than the validator delivers.

**Concern 2 -- Article 14 review record validity**: Article 14 specifies that review records live at `docs/specs/<feature-id>/reviews/<phase>-review-<reviewer>.md` and that "phase-gate validators check that a review record exists before they pass for design-spec and test-spec phases." However, the article does not define what makes a review record *valid* beyond its file path. There is no required schema (e.g., must contain a Verdict section). The SKILL.md for phase-review does specify the output format (Reviewer, Coverage assessment, Soundness assessment, Completeness assessment, Out-of-scope concerns, Verdict sections), but this is guidance to the agent, not a validated contract. A zero-byte file at the right path would satisfy the gate. More critically, **the gate validators in `gates.py` do not actually check for review records at all** -- `design_gate` and `test_gate` have no code looking for files in the `reviews/` directory. This is a clear gap between what the constitution promises and what the implementation enforces.

## 2. Phase artefact templates fitness

**Verdict: AGREE**

The three templates produce artefacts that the gates can validate. Specifically:

- **Feature-id substitution**: `phase-init` runs `sed "s/<feature-id>/$FEATURE_ID/g"` on the template. The requirements-spec template has `**Feature-id:** <feature-id>` which becomes `**Feature-id:** oauth-flow` after substitution. The `_FEATURE_ID_RE` regex in spec_parser.py matches `^\*\*Feature-id:\*\*\s+([a-z0-9][a-z0-9-]*)\s*$` which correctly matches the substituted output. The integration test (`test_phase_init_creates_artefact_from_template`) confirms this works.

- **REQ-ID headings**: The template has `### REQ-<feature-id>-001` which after substitution becomes `### REQ-oauth-flow-001`. The `_HEADING_ID_RE` regex `^###\s+(?P<id>(?:REQ|DES|TEST)-[a-z0-9][a-z0-9-]*-\d+)\b` matches this. Confirmed by test.

- **Satisfies lines**: The design-spec template has `**satisfies:** REQ-<feature-id>-001` which after substitution produces `**satisfies:** REQ-oauth-flow-001`. The `_SATISFIES_RE` and `_REF_ID_RE` regexes handle this correctly. The test-spec template uses `**satisfies:** REQ-<feature-id>-001 via DES-<feature-id>-001` -- the "via" word is treated as non-matching text between two IDs, and both REQ and DES IDs are extracted correctly by `_REF_ID_RE`.

- **No special-casing needed**: The templates produce exactly the format the parser expects. The sample fixture confirms end-to-end validity.

One note: the design-spec template includes an example with `**satisfies:** REQ-<feature-id>-002, REQ-<feature-id>-003` (comma-separated multi-REQ). The `_REF_ID_RE.findall()` call correctly extracts all IDs from the comma-separated list. No special-casing required.

## 3. Gate validator robustness

**Verdict: AGREE-WITH-CONCERNS**

The validators are well-structured and handle the core cases correctly. Specific answers to the posed questions:

- **design_gate with a DES referencing a non-existent REQ**: Yes, this is caught. Lines 112-119 of gates.py iterate over `des_parsed.references` and check each REQ-prefixed reference against `req_parsed.declared_ids`. A DES declaring `**satisfies:** REQ-X-999` where REQ-X-999 does not exist will produce an error. Test `test_design_gate_fails_on_broken_satisfies_reference` confirms this.

- **test_gate with satisfies lines like "REQ-X-001, REQ-X-002 via DES-X-001, DES-X-002"**: Yes, this works. The `_REF_ID_RE` regex (`\b((?:REQ|DES)-[a-z0-9][a-z0-9-]*-\d+)\b`) uses `findall()` which extracts all matching IDs from the line regardless of commas or "via" separators. Each extracted REQ-ID is checked against `req_parsed.declared_ids` and each DES-ID against `des_parsed.declared_ids`. The spec_parser test `test_parse_test_spec_extracts_test_ids_and_both_prior_phase_references` confirms the multi-ID extraction works.

- **code_gate with multiple `# implements:` annotations**: Yes, this works. The `_TEST_ID_REF_RE` regex uses `finditer()` over the entire `code_text` string, finding all `# implements:` lines. Each line's TEST-IDs are accumulated into `cited_test_ids`. Multiple annotations in different functions within the same file (or across multiple files concatenated by the phase-gate skill) are all collected.

**Concern -- false positives on quoted/code-block content**: The spec_parser correctly skips fenced code blocks (``` delimiters) for both declared IDs and satisfies references. This is confirmed by test `test_parse_spec_ignores_ids_in_code_blocks`. However, the parser does NOT skip:
  - Blockquotes (`>` lines containing IDs)
  - Inline code (backtick-wrapped IDs like `` `REQ-feature-001` ``)
  - HTML comments (`<!-- REQ-feature-001 -->`)

In practice, blockquoted or inline-code REQ-IDs in spec documents are likely rare and probably intentional references, so this is a minor concern. The code_gate's `_TEST_ID_REF_RE` only matches `# implements:` lines (comment-style annotations), which is a tighter pattern unlikely to false-positive.

**Concern -- no "coverage completeness" check**: The gates check that cited references resolve, but they do NOT check that all REQ-IDs are covered by at least one DES-ID, or that all DES-IDs are covered by at least one TEST-ID. Orphan REQs with no design coverage pass the design-gate. This is arguably correct for Method 1 (Method 2/Assured adds coverage validators), but the traceability-export does surface orphans, so a team would discover them there. The gap is acknowledged in METHODS.md as an Assured-level concern.

## 4. Phase-review skill realism

**Verdict: AGREE-WITH-CONCERNS**

The architectural choices are reasonable for the happy path:
- `sdlc-team-common:solution-architect` for design-spec review is appropriate -- solution architects are the right reviewers for design decisions.
- `sdlc-team-fullstack:backend-architect` for test-spec review is a somewhat odd choice. The feature proposal (line 91) mentions `sdlc-team-fullstack:test-architect` but notes this agent doesn't exist as named. The fallback to `backend-architect` is pragmatic but semantically imprecise -- a backend architect is not specifically qualified to review test specifications.

**Concern -- missing fallback for absent plugins**: The skill hardcodes specific agent paths (`sdlc-team-common:solution-architect`, `sdlc-team-fullstack:backend-architect`). If a project does not have the `sdlc-team-fullstack` plugin installed, the test-phase review will fail at agent dispatch time. Similarly, if `sdlc-team-common` is not installed, design-phase review fails. The skill has no fallback mechanism -- no graceful degradation to a generic review prompt, no check for agent availability before dispatch, no error message suggesting which plugin to install.

The `depends_on: [sdlc-core]` in manifest.yaml does not declare dependencies on `sdlc-team-common` or `sdlc-team-fullstack`. A team commissioning to Programme and installing only `sdlc-core` + `sdlc-programme` would have a broken `phase-review` skill for both phases.

**Recommendation**: Either (a) add `sdlc-team-common` to `depends_on` and document `sdlc-team-fullstack` as optional with a fallback, or (b) implement a fallback that uses the `superpowers:requesting-code-review` pattern (which exists without plugin dependencies) when the preferred agent is unavailable.

## 5. Bundle layout vs Phase C contract

**Verdict: AGREE**

The layout matches the Phase C contract with no violations:

- **manifest.yaml required fields**: All present and correct:
  - `schema_version: 1` -- correct
  - `name: programme` -- correct
  - `version: 0.1.0` -- correct semver
  - `supported_levels: [production, enterprise]` -- correct (Programme excludes prototype per design)
  - `description:` -- present and descriptive
  - `constitution: CONSTITUTION.md` -- correct, points to the file that exists at bundle root

- **File layout**: Matches the contract specification:
  - `.claude-plugin/plugin.json` -- present
  - `manifest.yaml` -- present
  - `README.md` -- present
  - `CONSTITUTION.md` -- present
  - `pyproject.toml` -- present (optional, but needed for Python helpers)
  - `scripts/` -- present with Python implementation helpers
  - `skills/` -- present with 5 skill subdirectories
  - `templates/` -- present with 3 template files
  - No `validators/` directory -- correct (Phase C contract explicitly dropped this)
  - No `agents/` directory -- the contract lists it as part of the layout, but the manifest declares `agents: []` which is consistent; the directory's absence is acceptable for a bundle with no agents in v0.1.0

- **Reserved Phase E fields**: None of the reserved fields (`decomposition_support`, `id_format`, `paths_split_supported`, `known_violations_field`, `anaemic_context_opt_out`) appear in manifest.yaml. Correct for a Method 1 bundle.

- **Validator configuration**: Present in manifest.yaml with bundle-defined identifiers including Programme-specific gates (`requirements_gate`, `design_gate`, `test_gate`, `code_gate`) in the `pre_push` list. This follows the contract's pattern of bundle-defined identifiers.

---

## Summary

The Programme bundle is a solid Method 1 substrate that is **good enough to ship as v0.1.0** with two issues that should be addressed before or shortly after shipping:

1. **Review record enforcement gap (Article 14)**: The constitution promises that gate validators check for review records, but `gates.py` does not implement this check. This is the most significant gap -- it means Article 14's mandatory review is enforceable only by skill discipline, not by the automated gate. For v0.1.0 this is acceptable if documented as a known limitation; for v0.2.0 it must be implemented.

2. **Agent dependency gap (phase-review)**: The phase-review skill dispatches agents from plugins not listed in `depends_on`. Teams installing only `sdlc-core` + `sdlc-programme` will hit a runtime failure. A fallback or explicit dependency declaration is needed.

**Phase E (Assured bundle) can build on top of this substrate without retrofit.** The architecture is clean: spec_parser.py's ID extraction, gates.py's validation pattern, and traceability.py's matrix construction are all extensible. Assured needs to add coverage validators (orphan detection), decomposition support, and KB-for-code indexing -- none of which require changes to the existing Method 1 code. The ID format (`REQ-<feature>-NNN`, `DES-<feature>-NNN`, `TEST-<feature>-NNN`) is consistent with Method 2's identifier system. The `_REF_ID_RE` regex patterns would need extension for Method 2's positional namespace IDs (`P1.SP2.M3.REQ-007`), but that extension is additive, not a retrofit.

The 27 tests provide good coverage of the core validation logic and integration flows. The code-block skipping in spec_parser.py is well-tested. Edge cases around blockquotes and inline code are minor and can be addressed incrementally.

**Overall assessment**: Ship v0.1.0 with the review-record enforcement gap documented. Address both gaps in v0.2.0.
