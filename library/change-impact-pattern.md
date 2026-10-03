---
title: "Change-Impact Annotation Pattern — Structured, Upfront, Optionally Gated"
domain: sdlc-bundles, change-impact, traceability, regulated-industries, method-2, assured
status: active
tags: [change-impact, change-impact-annotate, change-impact-gate, iec-62304, fda-21-cfr-820, iso-26262, structured-annotation, method-2, assured-bundle, epic-97]
source: research/sdlc-bundles/synthesis/01-traceability-synthesis.md
cross_references:
  - library/regulatory-traceability-baseline.md
  - research/sdlc-bundles/synthesis/overall-scope-update.md
---

## Key Question

How should the Assured bundle support the change-impact-assessment obligation that all five major safety-critical standards require, without overreaching into automatic semantic analysis?

## Core Findings

1. **All five regulated standards require change-impact assessment, but formalisation varies.** IEC 62304 Clause 8.2.4 [8] and FDA 21 CFR §820.30(i) [16] treat it as a mandatory blocking gate (impact must be assessed before implementation). DO-178C, ISO 26262, and IEC 61508 require it in configuration-management/design-change procedures but less explicitly as a blocker. — synthesis/01 §2 finding "Change-Impact Obligations"; §3 Claim 5
2. **Practitioner research shows change-impact is post-hoc in practice.** Academic and practitioner literature documents teams performing impact analysis *after* code changes are committed, using it as justification for re-testing scope rather than as a blocking gate. This is the compliance-theatre pattern. — synthesis/01 §2 finding "Practical Limitations"; output-1.md [20]
3. **The pragmatic middle ground is structured annotation, not automatic detection.** When a requirement, design element, or code unit changes, the team annotates the change with impact scope (e.g., "REQ-005 changed; affected: DES-012, TEST-034, CODE-segment-B"). This is upfront and auditable; it remains human-decided, requires no AST analysis, and satisfies IEC 62304 / FDA gating obligations when paired with the optional gate validator. — synthesis/01 §3 Claim 2
4. **Optional `change-impact-gate` validator** blocks commits where code changes exist but no change-impact annotation is present. Default: disabled. Enabled at commissioning for IEC 62304 / FDA 21 CFR Part 820 / ISO 26262 ASIL C/D contexts. — synthesis/01 §3 Claim 5; overall-scope-update.md §1 Cross-Line Agreement 6
5. **Automatic semantic change-impact detection is explicitly rejected.** Detecting that "a code change to `authenticate()` impacts tests for login, permission checking, session management" requires call graphs, data-flow analysis, or AI-driven reasoning. METHODS.md §6 declares AST-level code intelligence out of scope; this is the consistent design boundary. — synthesis/01 §4 first rejection
6. **Cross-line agreement strengthens this pattern.** Lines 1 and 3 both converge: Line 1 establishes the regulatory need (IEC 62304 / FDA gate); Line 3 confirms that static annotation is the right pattern compared to automatic detection. — synthesis/overall §1 Cross-Line Agreement 6 (HIGH confidence)
7. **`change-impact-annotate` skill makes the obligation cheap to satisfy.** Guides teams through declaring impact scope when artefacts change. Reduces friction so teams actually do it upfront rather than retrofitting at audit time. — overall-scope-update.md §4 Change 5

## Frameworks Reviewed

| Standard | Change-impact obligation | Gate? | Method 2 support |
|---|---|---|---|
| **DO-178C** | Required in CM plan (Section 6.7.3) | Implicit | Annotation supported; gate optional |
| **IEC 62304** | Mandatory before implementation (Clause 8.2.4) | **Blocking** | Annotation + `change-impact-gate` enabled at commission |
| **ISO 26262** | Required in design-change procedure (Part 6 Clause 9.6.1) | Required for ASIL B/C/D | Annotation + gate enabled for ASIL B+ |
| **IEC 61508** | Implied via traceability integrity | No explicit gate | Annotation; gate optional |
| **FDA 21 CFR §820.30(i)** | Re-validation before implementation if safety-affecting | **Blocking** | Annotation + `change-impact-gate` enabled at commission |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Annotation completeness for changed artefact | 100% (when gate enabled) | synthesis/01 §3 Claim 5 | Block commit |
| Default gate state | Disabled | synthesis/01 §3 Claim 5 | Configurable at commissioning |
| IEC 62304 / FDA / ISO 26262 commissioning | Gate enabled by default | synthesis/01 §3 Claim 5 | Recommended; team can opt out with documented justification |
| Annotation format integrity | Validated by `kb-rebuild-indexes` | overall §4 Change 3 | Block on broken IDs in annotations |

## Design Principles

1. **Structured annotation, not automatic detection.** The framework records what humans declare; it does not infer impact via call graphs or AST analysis.
2. **Optional gating, not mandatory.** Default disabled to preserve flexibility for non-regulated contexts. Enabled at commissioning when regulatory context demands it.
3. **Annotations are first-class artefacts, not metadata.** Stored in markdown alongside the changed artefact (or in a `change-impact/<artefact-id>.md` file); referenced by stable IDs; queryable via the librarian.
4. **The gate fails loud and informative.** Error messages must tell the developer exactly which artefact changed, what change-impact annotation is missing, and how to add it via `change-impact-annotate <artifact-id>`.
5. **Annotation expires.** A change-impact annotation references a specific change (commit SHA or version); subsequent changes require new annotations. Old annotations are historical record, not perpetual coverage.

## Key References

1. `research/sdlc-bundles/synthesis/01-traceability-synthesis.md` §3 Claims 2, 5; §4 first rejection
2. `research/sdlc-bundles/synthesis/overall-scope-update.md` §1 Agreement 6 (cross-line); §4 Change 5
3. IEC 62304:2015 Clause 8.2.4 — Software changes. output-1.md (line 1) bibliography [8]
4. FDA 21 CFR §820.30(i) — Design changes. Bibliography [16]
5. ISO 26262 Part 6 Clause 9.6.1 — Design-change procedure. Bibliography [9]
6. Ketryx and Perforce practitioner reports on post-hoc change-impact. output-1.md bibliography [20]

## Programme Relevance

**EPIC #97 sub-feature #104 (Assured bundle)**:
- New skill `change-impact-annotate <artifact-id>` ships in the Assured bundle (METHODS.md §4 update)
- New optional validator `change-impact-gate` ships disabled by default
- Commissioning script (`commission-assured`) enables the gate when regulatory context is IEC 62304, FDA 21 CFR Part 820, or ISO 26262 ASIL C/D — these have explicit gating requirements
- The librarian queries the change-impact records the same way it queries other findings — no new agent needed
- Format of change-impact annotation is markdown with YAML frontmatter (consistent with other spec records); fields: `affects: [<id-1>, <id-2>, ...]`, `commit_sha:`, `decided_by:`, `decided_at:`

**Compliance theatre risk** (from L3 research): the gate enforces *that* annotation exists; it cannot enforce that the annotation is *meaningful*. Whether the listed affected items are actually affected is a human-review concern (`phase-review` skill catches this). The framework draws the syntactic-vs-semantic line consistently.
