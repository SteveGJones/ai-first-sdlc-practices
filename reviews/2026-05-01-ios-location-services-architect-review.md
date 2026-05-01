# iOS / Location Services Architect Review — EPIC #178 Phase G Meta-Retrospective

**Date:** 2026-05-01
**Reviewer:** iOS Platform and Location-Based Services Architect
**Branch:** `feature/sdlc-programme-assured-bundles`
**Primary input:** `research/phase-g-session-meta-retrospective.md`
**Corroborating samples:** `research/phase-f-dogfood-findings.md`, `retrospectives/178-programme-assured-bundles-epic.md`, `docs/traceability/do-178c-rtm.md`, sampled Phase F requirements specs, and selected Assured implementation files.
**Review type:** Independent architecture and assurance-readiness review

---

## Executive Summary

The retrospective is unusually candid and broadly consistent with the supporting artefacts I sampled. The team has built a meaningful v0.1.0 substrate for Programme and Assured workflows, and the recursive dogfood phase did what a good dogfood phase should do: it found failures that unit tests and in-session reviews would not have found.

My verdict is **ship as an experimental / internal dogfoodable v0.1.0 only if the PR explicitly narrows the claims**. I would not support positioning the Assured bundle as audit-ready, regulated-industry-ready, or suitable for safety-significant mobile/location systems without substantial follow-up. The current system is a promising traceability scaffold, not yet a trustworthy assurance mechanism.

From an iOS and location-services perspective, the most important issue is that the assurance model is still heavily shaped around Python files and markdown artefacts. Real iOS location systems spread safety, privacy, and operational behaviour across Swift/Objective-C source, SwiftUI/UIKit lifecycle code, `Info.plist`, entitlements, Xcode project settings, background modes, app extensions, permissions copy, and test plans. A toolchain that misses markdown annotations today will almost certainly miss Xcode and Apple-platform configuration evidence tomorrow unless file-format support is designed deliberately rather than added one regex at a time.

---

## Verdict

**Conditional ship for v0.1.0.**

Required before merge or PR review completion:

1. The PR must state that Method 2 / Assured v0.1.0 is **not audit-ready** and that its traceability exports are smoke-test outputs, not compliance evidence.
2. The PR must include a review walking tour that decomposes the 236-file / 34k-line change into phase-level review paths.
3. The v0.2.0 backlog must explicitly track the three assurance blockers: multi-format annotation support, REQ-vs-DES granularity semantics, and real dependency extraction for visibility enforcement.
4. The team should manually review the eight Phase E `SKILL.md` files and a sample of Phase F M2 requirements before treating the retrospective as complete.

I do not see evidence that the whole EPIC should be stopped. I do see evidence that the merge must be framed honestly.

---

## Major Findings

### 1. The generated RTM is structurally useful but not assurance-grade

The DO-178C RTM sample has 43 HLR rows, all with populated LLR and test-case columns, but 28 rows have an empty source-code column. That is a 65.1% implementation-evidence gap. The Phase F findings correctly call this out as F-009.

This is not a cosmetic weakness. For regulated or safety-significant work, an RTM with a mostly empty source column creates a false sense of completeness: the document looks formal while failing the central evidence obligation. The exporter currently emits placeholders rather than distinguishing between "not implemented", "implemented by non-source artefact", "implemented by source but not indexed", and "not applicable with justification."

For iOS location-based services this distinction is critical. A requirement may be satisfied by:

- Swift or Objective-C source code
- `Info.plist` usage descriptions such as location permission purpose strings
- Background mode entitlement configuration
- Xcode project capabilities
- Privacy manifest entries
- App Store privacy disclosures
- Manual verification against device permission state transitions
- Field-test evidence for background delivery, region monitoring, or degraded GPS conditions

A single generic "Source code" column is too narrow for Apple-platform assurance. v0.2.0 should generalise this to **implementation evidence** with typed artefacts, rather than assuming every requirement maps cleanly to code.

**Recommendation:** keep the DO-178C export, but add an explicit "evidence status" concept before claiming compliance usefulness: `linked`, `missing`, `not_applicable`, `manual_evidence_required`, and `configuration_artifact`.

### 2. The annotation model is under-specified for real platform ecosystems

F-001 is valid and important: the parser recognises only Python-style `# implements:` comments. The retrospective's claim that markdown needs first-class support is correct. However, the underlying problem is broader than markdown.

Apple-platform systems need traceability across Swift, Objective-C, plist XML, entitlements, `.xcodeproj` / `.pbxproj`, `.xcconfig`, test plans, localized strings, privacy manifests, and sometimes generated files. If v0.2.0 merely adds `<!-- implements: ... -->`, it will solve the current dogfood failure but not the platform-general issue.

The `code-annotate` requirement already names Python, JavaScript/TypeScript, Go, and Rust comment syntax. That is a good start, but it still treats annotation as line-oriented source comments. Location services projects routinely encode user-visible and compliance-relevant behaviour outside ordinary source comments.

**Recommendation:** define an `EvidenceIndexEntry` abstraction instead of expanding `CodeIndexEntry` indefinitely. It should support:

- source-code annotations
- markdown HTML comments
- YAML / JSON / plist paths
- Xcode capability and entitlement keys
- externally attached evidence files such as test reports or field-run logs
- explicit "satisfies by existence" records for governance documents

This would also resolve much of F-003 without creating a special case that only applies to constitutions.

### 3. `granularity_match` currently creates warning fatigue

The retrospective asks reviewers to challenge the "F-001/F-008/F-009 single root cause" claim. My assessment: the cluster is real, but the root cause is not singular.

F-001 is a parser coverage problem. F-008 is a traceability-semantics problem. F-009 is an export-evidence completeness problem. They reinforce each other, but a parser fix alone will not make the RTM audit-ready.

`granularity_match` warns on all 43 REQs because the implementation convention is DES-level annotation while the validator expects REQ-level annotation. The warning rate is therefore 100% noise in the dogfood scenario. In safety-critical engineering, noisy warnings are dangerous because teams learn to ignore the channel.

**Recommendation:** choose the semantic model before extending the tooling:

- If annotations target REQs, require direct REQ annotations and update the team convention.
- If annotations target DES, treat a REQ as implementation-covered when at least one satisfying DES has evidence.
- If both are supported, make the module's declared granularity explicit and validate against that mode.

For v0.1.0, I would document DES-level annotation as the active convention and mark `granularity_match` as advisory / known noisy for current dogfood artefacts.

### 4. Decomposition visibility is specified but not operationally enforced

F-007 is more serious than its MINOR severity suggests. `visibility_rule_enforcement` cannot run on real code because no import graph extractor exists. That means the decomposition boundary model is partially aspirational.

For iOS systems, dependency extraction is harder than Python imports. Important architectural coupling may appear in:

- Swift imports and module boundaries
- target membership in Xcode projects
- app extensions and shared frameworks
- delegate callbacks and notification-driven flows
- dependency injection registrations
- generated Swift package dependencies
- background task and CoreLocation delegate ownership

This does not mean v0.1.0 must solve iOS extraction. It does mean the architecture should stop describing visibility validation as if it is enforced in real projects.

**Recommendation:** raise F-007 to IMPORTANT for any claim about architectural boundary enforcement. Add a language/platform extractor interface and ship Python as the first implementation. Then Swift/Xcode extraction can be added without changing the validator contract.

### 5. Some Phase F requirements are still implementation-shaped

The retrospective worries that REQ quality may drift toward "function X exists." My sampling supports that concern.

Examples:

- `REQ-assured-decomposition-validators-001` begins with the function name `req_has_module_assignment` and describes its output.
- `REQ-assured-traceability-validators-003` begins with `index_regenerability` and describes byte-for-byte behaviour.
- `REQ-assured-skills-001` is closer to user-observable behaviour, but still mixes workflow outcome with implementation details such as scanning headings and incrementing max IDs.

This is not fatal for an internal tooling EPIC, but it matters for the Method 2 promise. If requirements become function contracts, the process can prove that functions satisfy themselves while missing user, safety, privacy, or operational obligations.

For an iOS location product, requirements need to express user and system guarantees such as:

- the app behaves correctly across `notDetermined`, denied, approximate, precise, foreground-only, and always-authorized states
- background location use degrades safely when authorization or system policy changes
- location data retention and transmission are constrained by privacy rules
- user-facing permission copy matches actual collection behaviour
- tests cover simulator and physical-device behaviours where CoreLocation differs

**Recommendation:** add a REQ-quality review gate with examples of unacceptable function-shaped SHALLs. Do not rely on validators alone to enforce this; it needs human review until the pattern matures.

### 6. The retrospective is honest about review drift, and that drift should be treated as a process defect

The controller's admission that review intensity degraded over time is credible. The highest-risk part is not simply that some reviews were short. It is that the process accepted implementer deviations repeatedly and batched eight skill files into one review pass.

For a 236-file PR, that creates two risks:

- defects hide in apparently "content-only" files that are actually executable agent behaviour
- reviewers cannot reconstruct which deviations were intentional design evolution versus expedient acceptance

Skills are product surface. For this repo, a `SKILL.md` file is closer to executable workflow code than ordinary documentation. Batch review is therefore weaker than it appears.

**Recommendation:** before PR completion, produce a short deviation ledger: accepted deviation, rationale, affected file, reviewer confidence, and whether follow-up is required.

---

## Assessment of the Retrospective's Challenge List

I agree with most of the controller's proposed challenge list, with the following adjustments:

| Item | My assessment |
|------|---------------|
| 8 Phase E `SKILL.md` files | Must review. These are executable workflow contracts, not passive docs. |
| F-001/F-008/F-009 single root cause | Partially true, but too compressed. Treat as three related defects across parser, semantics, and evidence export. |
| Phase F M2 REQ quality | Must sample. Initial sample shows function-shaped requirements remain. |
| DO-178C RTM smoke output | Structurally valid table, but not compliance evidence. Needs typed evidence status. |
| Granularity of 9 findings | Findings could be grouped into 4 themes, but keeping 9 is useful if the backlog preserves causal links. |
| Timeout recovery commits | Worth reviewing, but lower priority than traceability semantics and skill correctness. |
| Phase F Task 9 annotation inside DES | Acceptable only if the convention says design documents can be implementation evidence; otherwise it blurs spec and implementation layers. |
| PR `Closes` line | Must verify against GitHub state before merge because the stale #142 recommendation shows this process is vulnerable to stale issue assumptions. |

---

## iOS / Location Services Readiness

If a mobile/location team attempted to use Assured v0.1.0 today, I would expect it to help with discipline and naming, but I would not trust it as an assurance system.

### What transfers well

- The REQ → DES → TEST chain maps well to mobile features that need explicit behavioural contracts.
- Decomposition by bounded context is appropriate for separating location acquisition, permission state, storage, networking, UI presentation, and policy enforcement.
- Change-impact annotation is a strong fit for privacy-sensitive code paths where small changes can alter collection behaviour.
- Module-scope rendering could help reviewers avoid massive mobile architecture documents.

### What is missing for Apple-platform work

- Swift / Objective-C annotation parsing
- `Info.plist`, entitlements, privacy manifest, and Xcode capability evidence
- test evidence distinction between unit, integration, simulator, and physical-device tests
- explicit privacy and user-consent requirement categories
- handling for background location, significant-change service, visits, region monitoring, and authorization transitions
- dependency extraction for Swift modules, targets, packages, and app extensions
- support for localized permission strings and App Store privacy declarations as traceable artefacts

### Practical guidance

Do not use v0.1.0 to claim that an iOS location system is compliant with an external safety or privacy standard. Use it to structure the evidence backlog, then add platform-specific evidence collectors.

---

## Recommended v0.2.0 Backlog Shape

1. **Evidence model generalisation**

   Rename or generalise code index concepts so evidence can be source code, markdown, config, entitlement, external test report, or governance document.

2. **Annotation syntax registry**

   Implement a registry by file type, not a single regex. Include Python, Markdown, Swift, Objective-C, plist/XML, YAML, JSON, and plain text.

3. **Granularity semantics**

   Decide direct REQ evidence vs DES-mediated evidence. Update `granularity_match`, docs, examples, and RTM export together.

4. **Evidence completeness checks**

   Add a validator that fails or warns when an export would contain placeholder implementation evidence without a justification.

5. **Dependency extractor interface**

   Add a platform-neutral extractor contract. Implement Python first, then Swift/Xcode as a separate plugin or language adapter.

6. **REQ-quality review**

   Add a human review checklist and later a lint rule for function-shaped requirements. The goal is user-visible, safety/privacy-relevant requirements.

7. **PR reviewability pack**

   For large EPICs, require a walking tour, phase summary, accepted-deviation ledger, and "areas safe to skim" list.

---

## Final Recommendation

The team should merge only with a conservative public claim: **Programme and Assured v0.1.0 establish the first working substrate and have been dogfooded; they do not yet provide audit-ready assurance evidence.**

The retrospective itself is a strong artefact. It does not try to hide the weak points, and that is a good sign. The next step is to convert the admissions into explicit PR constraints and v0.2.0 issues, especially around evidence completeness and platform/file-format coverage.

For iOS and location-based services, the architecture is promising but incomplete. The design direction is right; the evidence model is not yet broad enough for real Apple-platform assurance.
