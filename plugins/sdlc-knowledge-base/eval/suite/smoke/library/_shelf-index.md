<!-- format_version: 1 -->
<!-- last_rebuilt: 2026-06-10T00:00:00Z -->
<!-- library_handle: local -->
<!-- library_description: Smoke eval fixture — 3 pages for kb-offline M1c runner tests -->
# Knowledge Base Shelf-Index

Smoke fixture for the kb-offline eval runner (#211). Three pages spanning the
evidence, development, and methodology layers. Used only by the eval suite.

---

## 1. dora.md

**Layer:** evidence
**Confidence:** high
**Terms:** dora, deploy, deployment frequency, lead time, change failure rate, elite teams
**Facts:**
- Elite performing teams deploy multiple times per day
- Lead time for changes is under one hour for elite teams
- Change failure rate stays at or below 15 percent for elite performers

## 2. review.md

**Layer:** development
**Confidence:** medium
**Terms:** code review, merge, correctness, tests, standards
**Facts:**
- Every change is reviewed before merge
- Reviews check correctness, tests, and adherence to the standards

## 3. testing.md

**Layer:** methodology
**Confidence:** high
**Terms:** testing, tdd, test-driven development, failing test, implementation
**Facts:**
- Tests are written before the implementation in test-driven development
- A failing test is written first, then the minimal code to make it pass
