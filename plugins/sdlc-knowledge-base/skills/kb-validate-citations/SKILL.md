---
name: kb-validate-citations
description: Spot-check citations in library files for obvious hallucinations. Resolves DOIs against the DOI registry, validates arXiv IDs, checks the format of journal references. Soft-fails on transient lookup failures rather than blocking. Recommended after kb-ingest and as part of periodic library hygiene.
disable-model-invocation: false
argument-hint: "[<file-path-or-glob>]"
---

# Validate Knowledge Base Citations

Catch obvious citation hallucinations in library files. Deep research engines occasionally fabricate DOIs, attribute findings to the wrong author, or invent journal names. Manual spot-checking 10-20% of citations remains necessary; this skill automates the obvious failure cases so manual review can focus on subtler issues.

## Argument

Optional file path or glob to scope validation. Default: all library files in `library/**/*.md` excluding the index files.

Examples:
- `library/dora-metrics.md` — single file
- `library/dora-*.md` — files matching a pattern
- (no argument) — all library files

## Preflight

- Verify the knowledge base is configured.
- Verify network access (DOI resolution requires HTTPS to https://doi.org).

## Steps

### 1. Discover library files

Use Glob to find files matching the scope. Exclude:
- `library/_shelf-index.md`
- `library/_index.md`
- `library/log.md`
- `library/raw/**`

### 2. Extract citations from each file

For each library file, parse the `## Key References` section and the inline citations in `## Core Findings`. Identify three citation types:

**DOI citations** — strings matching the DOI regex: `10\.\d{4,9}/[-._;()/:A-Z0-9]+` (case-insensitive). DOIs are the strongest signal because they're machine-resolvable.

**arXiv IDs** — strings matching `arXiv:\d{4}\.\d{4,5}` or `arxiv\.org/abs/\d{4}\.\d{4,5}`.

**Journal references** — anything matching the pattern `<authors>. (<year>). "<title>." <Journal Name>, <volume>(<issue>), <pages>.` or similar bibliographic format. Best-effort extraction; not all citations follow a standard format.

### 3. Validate each citation type

#### DOI resolution

For each DOI, attempt to resolve it via:

```bash
curl -sLI "https://doi.org/<doi>" -o /dev/null -w "%{http_code}"
```

Expected: HTTP 302 or 200 (redirected to the publisher landing page).
Failure: HTTP 404 (DOI does not exist) or 500 (DOI registry error).

Classify each result:
- **OK**: 200/302
- **NOT FOUND**: 404 — flag as likely hallucinated
- **TRANSIENT**: 500/timeout/network failure — soft-fail with "could not verify"

Rate limit: pause 100ms between DOI lookups to avoid hammering doi.org. If rate-limited (429), back off and retry once with a longer pause.

#### arXiv ID validation

For each arXiv ID:

1. Validate format: must be `YYMM.NNNNN` (4-5 digit suffix, 2007 or later)
2. Optionally verify existence:
   ```bash
   curl -sI "https://arxiv.org/abs/<id>" -o /dev/null -w "%{http_code}"
   ```
3. Expected: HTTP 200
4. NOT FOUND: HTTP 404 — flag as likely hallucinated

#### Journal reference format

For each journal reference, perform structural checks only (do not attempt to verify the journal exists in any registry — too many legitimate journals to maintain a list):

- Year is in the past or current year (no 2099 typos)
- Volume and issue, when present, are integers
- Page numbers, when present, follow `<start>-<end>` format
- Author list looks plausible (not a single word, not all caps unless it's an organisation)

These are weak checks — they catch obvious typos but not real hallucinations. The strong signals are DOI and arXiv resolution.

### 4. Produce the report

Output format:

```markdown
# Citation Validation Report

**Date:** YYYY-MM-DD
**Scope:** all files (or pattern)
**Files scanned:** N
**Citations checked:** M

## Summary

| Result | Count |
|---|---|
| OK (resolved) | A |
| NOT FOUND (likely hallucinated) | B |
| TRANSIENT (could not verify) | C |
| Format issues | D |

**Total issues:** B + D (transient failures are not counted as issues — they're informational)

---

## NOT FOUND citations

### library/dora-metrics.md

- DOI 10.1109/TSE.2010.99999 — DOI registry returned 404
  Context: "Madeyski (2010) reports defect reduction of..."
  Recommendation: verify the citation manually; consider whether the DOI was hallucinated

(repeat for each NOT FOUND)

## TRANSIENT failures (informational)

### library/dora-metrics.md

- DOI 10.1109/TSE.2010.5544067 — registry timeout, not validated
  Recommendation: re-run kb-validate-citations later; do not act on this

(repeat for each TRANSIENT)

## Format issues

### library/dora-metrics.md

- "Forsgren (3024)" — year appears to be a typo
  Recommendation: check the original source

(repeat)

---

## Recommended actions

1. Manually verify B citations marked NOT FOUND — these are the highest-confidence hallucination candidates
2. Re-run validation once C transient failures should have cleared
3. Fix D format issues
```

### 5. Append to log.md (if present)

```markdown
## [YYYY-MM-DD] validate-citations | <scope>

Files scanned: N
Citations checked: M
NOT FOUND: B
TRANSIENT: C
Format issues: D
```

### 6. Exit code

- Exit 0 if no NOT FOUND results AND no format issues (transient failures don't count)
- Exit 1 if any hard failures (NOT FOUND or format issues)

This lets the skill be wired into pre-push validation as an opt-in gate.

## What this skill does NOT do

- It does not verify that the cited paper actually says what the library file claims it says (LLM hallucination of *content*, not metadata — beyond automated reach; manual spot-checking remains necessary)
- It does not modify library files to fix issues
- It does not block on transient failures — soft-fail and report
- It does not validate non-academic citations (blog posts, GitHub repos, white papers without DOIs)

## Errors

- **No knowledge base configured** — run `/sdlc-knowledge-base:kb-init` first
- **No network access** — fail with explanation; the skill cannot work offline
- **DOI registry persistently down** — soft-fail all DOIs as TRANSIENT and recommend re-running later
- **Rate limited persistently** — back off, then partial-fail with a "ran out of attempts" note for unresolved DOIs

## Example

```
/sdlc-knowledge-base:kb-validate-citations

# Citation Validation Report
**Date:** 2026-04-08
**Scope:** all files
**Files scanned:** 22
**Citations checked:** 187

## Summary
| Result | Count |
|---|---|
| OK | 178 |
| NOT FOUND | 2 |
| TRANSIENT | 5 |
| Format issues | 2 |

Total issues: 4

(report continues...)
```
