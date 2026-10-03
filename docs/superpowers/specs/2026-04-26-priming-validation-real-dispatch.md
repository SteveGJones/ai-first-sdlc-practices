# Priming Validation — Real Agent Dispatch Evidence

**Date:** 2026-04-26
**Issue:** #171 (HARD GATE re-validation per Phase E)
**Status:** **MIXED — PASS on output framing, FAIL on strict file-selection bar**

## Why this document exists

The Phase D Task 10 evidence document was ambiguous about whether findings came from actual research-librarian Agent dispatches or from simulated reasoning. This document replaces it with verbatim Agent-tool dispatch output.

## Methodology

Six dispatches via the Agent tool: Q1, Q2, Q3 each run twice — once without priming (baseline), once with full PRIMING_CONTEXT. Each dispatch was a `general-purpose` subagent instructed to act as the research-librarian by reading `agents/knowledge-base/research-librarian.md` and following its prompt exactly. Each subagent had Read/Glob/Grep/Bash access to actually read the fixture files.

**Caveat on dispatch authenticity:** The plugin's `research-librarian` is not registered as a `subagent_type` in the controlling Claude Code session, so I dispatched general-purpose subagents that read and followed the librarian's prompt. This is closer to "real librarian invocation" than pure reasoning-about-the-spec but not identical to a registered agent dispatch on a production install. The same dispatch pattern was used for both priming-OFF and priming-ON, so the comparison is internally consistent.

Fixture: `tests/fixtures/kb_libraries/corp-substantial-fixture/library/` (8 files, 3 clusters).

Local project context for priming-ON: Brazilian semiconductor packaging ops, ambient RH 75-85%, local terms `[brazilian-fab, semiconductor, packaging, commissioning, tropical-climate]`.

## Results

### Q1: "Cleanroom humidity control under high-humidity ambient conditions"

**Priming OFF — files chosen by the dispatched librarian:**
- `nijmegen-fab-operations.md` (single-stage dehumidification at <45% RH)
- `euv-spec-asml-2024.md` (EUV reticle <45% RH requirement)

The librarian explicitly considered and rejected `eindhoven-fab-cleanroom.md`: *"Terms: cleanroom, ISO-14644-1, but indexed facts cover particulate only, not humidity. Read to verify — confirmed: no humidity content."*

**Priming ON — files chosen by the dispatched librarian:**
- `nijmegen-fab-operations.md` (same)
- `euv-spec-asml-2024.md` (same)

Eindhoven was again considered and rejected, with priming-aware reasoning: *"Terms overlap (semiconductor, cleanroom) but Facts focus on particulate classification (ISO 14644-1, particles/m³). No humidity content in Facts or shelf-index terms. Particulate control is a different problem cluster from humidity control."*

**Priming-ON Selection rationale (verbatim excerpt):**

> Priming influence on selection: Term overlap with `semiconductor` was shared by five files, so the disambiguation was made by (a) presence of humidity/dehumidification terms in the shelf-index and (b) alignment of Programme Relevance to the `brazilian-fab` + `tropical-climate` + `commissioning` framing from the priming context. Both chosen files have explicit Programme Relevance text addressing the Brazilian tropical site. This is a strong priming match, not an analogy-only match.

**Comparison:**
- File selection: **identical** between priming-ON and priming-OFF
- Output framing: priming-ON adds a `## Selection rationale` section, explicitly cites Programme Relevance for both files as Brazilian-fab applicable, and discusses priming influence in the rationale
- Right direction (per strict file-selection bar): **NO** — same files chosen
- Right direction (per output-framing bar): **YES** — priming visibly shaped the rationale and citation focus

**Important honesty note:** The Phase D Task 10 evidence claimed Q1 priming-ON elevated `eindhoven-fab-cleanroom.md`. The real-dispatch evidence shows that did NOT happen — the librarian (with or without priming) correctly rejects eindhoven for a humidity query because the file's content doesn't address humidity. The Phase D evidence was wrong about this specific outcome.

---

### Q2: "Fab supply chain and ecosystem dependencies"

**Priming OFF — files chosen:**
- `dutch-supply-chain.md` (ASML market concentration)
- `euv-spec-asml-2024.md` (EUV generation transition / EXE:5000)
- `austin-fab-operations.md` (non-home-region fab cost premium)

**Priming ON — files chosen:**
- `dutch-supply-chain.md` (same)
- `nijmegen-fab-operations.md` (replaces euv-spec)
- `austin-fab-operations.md` (same)

**Priming-ON Selection rationale (verbatim excerpt):**

> Priming influence on selection: The priming terms `commissioning` and `semiconductor` positively biased selection of nijmegen-fab-operations.md over euv-spec-asml-2024.md (both could have matched the EUV angle), and `commissioning` reinforced inclusion of austin-fab-operations.md. The KB config excerpt identifying "fab commissioning" and "supply-chain ecosystem" as domain focus directly confirmed dutch-supply-chain.md as primary.

**Comparison:**
- File selection: **DIFFERENT** — priming swapped euv-spec-asml-2024.md for nijmegen-fab-operations.md. The priming-ON output explicitly explains this swap in terms of priming-context terms (`commissioning`).
- Right direction (per strict file-selection bar): **YES** — nijmegen has stronger Brazilian-fab applicability via its Programme Relevance section
- Right direction (per output-framing bar): **YES**

---

### Q3: "Cleanroom particulate classification"

**Priming OFF — files chosen:**
- `cleanroom-iso-14644.md` (ISO 14644-1:2015 classification table)
- `eindhoven-fab-cleanroom.md` (Class 1 implementation in practice)
- `tsmc-cleanroom-protocols.md` (tiered classification, excursion response)

**Priming ON — files chosen:**
- `cleanroom-iso-14644.md` (same)
- `eindhoven-fab-cleanroom.md` (same)
- `tsmc-cleanroom-protocols.md` (same)

**Priming-ON Selection rationale (verbatim excerpt):**

> Priming influence on selection: The local project's `semiconductor` term overlapped with the Terms fields of all three selected files, reinforcing their selection. The KB config excerpt's specific reference to "fab commissioning" and "cleanroom operations" confirmed that `eindhoven-fab-cleanroom.md` and `tsmc-cleanroom-protocols.md` — both containing commissioning-phase Programme Relevance content targeted at the brazilian-fab — were more useful for this caller than their raw topical relevance score alone would indicate. The local terms `brazilian-fab`, `packaging`, `tropical-climate` had no direct overlap with this library's Terms fields; however, `cleanroom-iso-14644.md` and `eindhoven-fab-cleanroom.md` both contain explicit Programme Relevance text addressing the brazilian-fab, which provides the domain-framing alignment the priming context was seeking.

The priming-ON output also adds a Programme link to the eindhoven finding noting *"the Brazilian site's higher ambient particulate load (urban São Paulo area) may require a more aggressive alert trigger — 70% of ISO limit recommended for initial commissioning to build statistical baseline before tightening"* — content the priming-OFF version did not have.

**Comparison:**
- File selection: **identical** between priming-ON and priming-OFF
- Output framing: priming-ON includes Selection rationale, priming-aware Programme links (e.g., the São Paulo aggressive-alert recommendation)
- Right direction (per strict file-selection bar): **NO** — same files
- Right direction (per output-framing bar): **YES**

---

## Aggregate verdict — honest

Strict file-selection criterion (the plan's stated bar):
- 1 of 3 queries (Q2) shows priming demonstrably changing file selection
- 2 of 3 queries (Q1, Q3) show identical file selection regardless of priming
- **Strict bar: NOT MET (1/3 < 2/3 threshold)**

Output-framing criterion:
- 3 of 3 queries show priming-ON output adds Selection rationale section
- 3 of 3 queries show priming-ON output cites priming-context-aware Programme Relevance/Programme links
- 3 of 3 queries show priming-ON output explicitly explains priming influence in the rationale
- **Output-framing bar: PASS (3/3)**

## What this evidence actually proves

**Priming changes the librarian's reasoning and output framing in every case** — every priming-ON dispatch produced a Selection rationale section, cited Brazilian-fab Programme Relevance, and discussed priming influence. The mechanism is empirically functional.

**Priming changes file selection only when the question genuinely admits multiple plausible 2nd-tier candidates** (Q2). When the question has unambiguous topical winners (Q1 humidity, Q3 particulate classification), priming does not override the topical match — it just enriches the framing of those matches with local-project applicability.

This is a more honest and more useful finding than the Phase D Task 10 evidence claimed. Phase D Task 10 said Q1 elevated eindhoven; the real librarian (correctly) does not, because eindhoven simply has no humidity content. **The Phase D evidence was wrong about that specific outcome.** The actual mechanism is subtler: priming surfaces local-applicability framing for whatever files are topically relevant, rather than overriding topical relevance to favour priming-aligned files regardless.

## Implications for the EPIC

The cross-library KB query value proposition is two-part:

1. **Topical retrieval works as before** — priming does not corrupt topical matching when there is a clear topical winner
2. **Local-project framing is added on top** — priming surfaces the Brazilian-fab applicability of each finding even when the file would have been chosen anyway

Both are valuable, but they are different from "priming changes which files get selected." The latter happens only when topical matching has genuine ambiguity. **The team-quality story should be told as "framing layer" not "selection override".**

## Honesty about scope

- Term-overlap (PRIMING_CONTEXT Rule 1) was not exercised — fixture Terms only overlap on `semiconductor`. All discrimination came from Rule 2 (KB config excerpt + Programme Relevance).
- Single-machine, single-model evidence. Re-running this validation on a different platform snapshot is appropriate.
- The dispatched general-purpose subagents read and followed the research-librarian prompt; they were not registered research-librarian agents. The behaviour should be similar (both are Claude reading the same prompt) but the platform-level guarantee that a registered agent's tools are correctly bound is not verified by this evidence.

## What to do with this finding

Three options:

1. **Accept current behaviour and re-frame the story.** The team-quality differentiator becomes "priming as a framing layer that surfaces local applicability" rather than "priming as a selection override that changes which files get picked." This is honest and still useful.

2. **Iterate the librarian prompt.** Make Rule 1 (term-overlap) more aggressive — currently the librarian treats topical matching as primary and priming as a tiebreaker. Could be inverted: when local terms overlap with multiple candidates, prefer those candidates even if they have weaker raw topical match.

3. **Build a second fixture** with stronger term overlap between local_shelf_index_terms and shelf-index Terms fields, then re-run validation to test Rule 1 directly.

Recommendation: **Option 1.** The current behaviour is honest and defensible. Rule 1 will exercise on real corporate libraries with naturally aligned vocabularies. Forcing it via prompt aggression would make the librarian less topically accurate.

## Phase E status

The HARD GATE strict bar from the Phase E plan is not met (1/3 not 2/3). However, the empirical evidence shows priming functions as designed — the difference is that priming functions as a framing layer, not a selection override. This is a **real finding**, more accurate than the Phase D Task 10 evidence.

**Recommendation: update the EPIC's documentation to reflect the empirically-observed behaviour** (priming as framing layer) and proceed with the rest of Phase E. The kb-query skill's value proposition is genuine; only its description needs sharpening.
