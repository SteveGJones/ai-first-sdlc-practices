# Research Line 1: Regulated-Industry Traceability Standards
## Final Research Output — Stage 2

---

## Section 1: Executive Summary

**DO-178C (Civil Aviation).** DO-178C mandates end-to-end bidirectional traceability from system requirements through high-level and low-level software requirements, source code, and test verification across all software levels (A–D), with depth scaled to criticality; Level A requires traceability to object code, while Level D requires minimal documentation. [1][2] The FAA's AC 20-115D provides regulator-published guidance on acceptable evidence forms. [3] The standard specifies objectives but remains tool-neutral; compliance does not mandate specific tooling, only that traceability evidence exists and is verifiable. [4]

**IEC 62304 (Medical Devices).** IEC 62304 requires traceability between system requirements, software requirements, design, implementation, and verification activities, scaled by software safety class (A, B, C). [5] Unlike DO-178C's explicit bidirectionality requirement, IEC 62304 permits unidirectional traceability links (risk→requirement→test) but does not forbid bidirectionality; practitioners frequently implement bidirectional traces to satisfy audit expectations. [6][7] Class C (highest risk) demands more rigorous traceability and configuration control than Class A; change-impact assessment is mandatory before any software update. [8]

**ISO 26262 (Automotive).** ISO 26262:2018 demands bidirectional traceability across the entire development lifecycle, from hazard analysis through functional safety requirements, technical requirements, hardware and software implementation, and verification—with the chain intact at all ASIL levels (A–D). [9][10] Part 6 (software) mandates traceability at requirement granularity, with verification and validation (V&V) links explicitly required; the standard is tool-neutral and does not specify evidence formats. [11]

**IEC 61508 (Generic Industrial Safety).** IEC 61508-3 specifies bidirectional traceability as an explicit development objective in Annex A.1, ensuring all outline requirements are addressed and detailed requirements trace to outlines, with no spurious code. [12] Like ISO 26262, IEC 61508 is tool-neutral; conformance is evidenced by the ability to regenerate traceability links from artefacts, not by any specific tooling choice. [13]

**FDA 21 CFR Part 820 (US Medical Devices).** 21 CFR §820.30(g) requires design validation including software validation, and §820.70(i) mandates verification of software used in production. [14] The FDA's "General Principles of Software Validation" guidance emphasizes traceability from requirements through design, implementation, and verification, with links demonstrated in design-history-file documentation. [15] Re-validation is required whenever a design change could affect safety or effectiveness; impact assessment is a mandatory control gate. [16]

**Comparative Positioning.** Across all five standards, bidirectional traceability is the common demand (DO-178C, ISO 26262, IEC 61508) or at minimum unidirectional with backward confirmation (IEC 62304, FDA guidance). The strictest standard is **ISO 26262**, which requires ASIL-scaled rigor and does not permit unidirectional-only approaches at higher ASIL levels. The most permissive is **IEC 62304**, which allows unidirectional traces and scales requirements by class. All five standards are tool-neutral and silent on specific evidence export formats; all treat traceability as a verifiable property of the engineering process, not a property of the tooling. Change-impact obligation is universal but most explicitly detailed in IEC 62304 and FDA guidance, least explicit in DO-178C (where change control appears in the Software Configuration Management Plan objective, not a distinct traceability clause).

---

## Section 2: Comparison Matrix

| Standard | Traceability Mandate | Bidirectionality | Granularity | Acceptable Evidence | Change-Impact Obligation | Tooling Neutrality | Process vs Artefact |
|----------|---------------------|------------------|-------------|---------------------|--------------------------|--------------------|-------------------|
| **DO-178C** | High-level → low-level → source code → tests required; scaled by level (Level D: minimal, Level A: to object code). [1][2] | Bidirectional: requirement ↔ code. [2][4] | Requirements and tests at minimum; Level A requires source-to-object traceability. [1] | Traceability matrices, test logs, configuration baselines accepted; FAA AC 20-115D does not prescribe format. [3] | Implicit in Software Configuration Management Plan objective; change control via problem reporting. [1] | Yes—standard specifies objectives only; tool choice unrestricted. [4] | Both: process (configuration management, change control, independence in review) and artefact (traceability data, requirements baseline). [1] |
| **IEC 62304** | Traceability required between hazards, system requirements, software requirements, design, code, verification; scaled by class. [5] | Unidirectional (forward: req→design→code) permitted; bidirectional backward links (code→req) not mandated but not forbidden. [6][7] | Requirement-level, with design and code implementation traced to requirements; module-level when decomposed. [7] | Traceability matrices, design history files, verification records; IEC 62304:2015 explicitly permits any format demonstrating the trace. [6] | Mandatory: every change requires impact assessment against original hazard analysis and risk classification. [8] | Yes—standard is method-agnostic; tool qualification is not discussed (implies tool choice is outside scope). [7] | Both: process (configuration management per clause 8, risk assessment review before change implementation) and artefact (traceability documentation, change records). [8] |
| **ISO 26262** | End-to-end bidirectional traceability from hazard analysis through functional safety requirements, technical requirements, implementation, and V&V across all ASIL levels. [9][10] | Bidirectional required: each element traceable forward and backward (req→design→code and code→design→req). [9][10] | Requirement-level for functional and technical safety requirements; ASIL D demands finest granularity with proof of no spurious code. [9] | Traceability matrices, design documents, V&V records; no format specified. ISO 26262-8 clause 11 permits tool-neutral qualification approach. [11] | Design-change procedure required; re-verification of changed and related requirements mandatory if ASIL ≥ C. [9] | Yes—tool-neutral; Part 8 clause 11 specifies tool qualification only if tool can inject errors into safety-related work products; otherwise qualification not required. [11] | Both: process (design review, change control, independence in verification by ASIL level) and artefact (traceability links, V&V protocols, change records). [9] |
| **IEC 61508** | Bidirectional traceability from safety requirements specification through design, code, and verification; specified as explicit objective in Annex A.1. [12] | Bidirectional: all outline requirements addressed; all detailed requirements trace to outlines; spurious code detection. [12] | Requirements and code; module-level under decomposed architectures; SIL-dependent depth. [12] | Traceability documentation, verification protocols, test results; no specific format mandated. [12] | Implicit in change control and re-verification objectives; SIL-dependent review rigor. [12] | Yes—standard does not specify tools; conformance is evidenced by regenerability of traceability from artefacts. [13] | Both: process (safety requirements review, development and verification independence by SIL) and artefact (traceability records, safety case documentation). [12] |
| **FDA 21 CFR Part 820** | Design validation (§820.30(g)) and software verification (§820.70(i)) require documented traceability from requirements through design, implementation, and verification. [14] | Unidirectional required (requirements forward to implementation and tests); backward confirmation via design history file. [15] | Requirement-level; validation scope depends on software's role in device safety/effectiveness. [15] | Design history file (DHF), requirements traceability matrix, test reports, design review records; "General Principles" guidance accepts any format supporting traceability reconstruction. [15] | Re-validation required if design change could affect safety/effectiveness; impact assessment is gating control. [16] | Yes—regulation silent on tools; FDA guidance emphasizes documentation and verification evidence, not tooling. [15] | Both: process (design control stages: input, output, review, verification, validation, transfer, change notification) and artefact (DHF contents, design inputs/outputs, traceability matrix). [16] |

---

## Section 3: Per-Standard Deep Dive

### DO-178C (Software Considerations in Airborne Systems and Equipment Certification)

**Traceability Mandate.** DO-178C requires end-to-end traceability from system requirements allocated to software, through high-level software requirements and low-level software requirements, to source code, and from requirements through test cases and test results. [1][2] The standard specifies this in its objectives structure across Sections 6.3.1 (requirements development) and 6.4.2 (verification). The depth of traceability scales with software level: Level D software requires minimal documentation and no traceability to object code; Level C adds traceability to low-level requirements and source code; Level B requires the same with independence in verification; Level A requires traceability extended to object code, where compiler-generated object code that is not directly traceable to source code must undergo additional verification. [1] The FAA's AC 20-115D confirms this tiered approach and notes that "traceability analysis is used to ensure that each requirement is fulfilled by the source code, that each functional requirement is verified by test, and that each line of source code has a purpose (is connected to a requirement)." [3]

**Bidirectional vs Unidirectional.** DO-178C mandates bidirectional traceability. [2][4] Forward traceability (requirement→low-level requirement→code) ensures all requirements are implemented; backward traceability (code→test→requirement) ensures all code has a justification and all tests connect to requirements. [1][4] The standard defines this as "the ability to describe and follow the life of a requirement in both a forwards and backwards direction (i.e., from its origins, through its development and specification, to its subsequent deployment and use, and through periods of on-going refinement and iteration)." [4]

**Granularity.** The minimum unit of traceability is the individual requirement and, for Level A systems, the individual source-code statement and object-code instruction. [1] For Level B and C, traceability to source code at the statement or function level is typical. Level D permits file-level or higher. [1] The standard does not prescribe module-level rollup; practitioners typically maintain requirement-level traceability matrices and aggregate them for reporting.

**Acceptable Evidence Forms.** The standard does not prescribe specific tools or document formats. [4] Practitioners commonly produce requirements-traceability matrices (spreadsheets, tables in design documents, or database exports), test-case matrices linking tests to requirements, source-code comments or annotations linking code to requirements (e.g., "implements REQ-005"), and configuration-management baselines proving which versions of which artefacts were verified together. [2][3] AC 20-115D states that traceability evidence must be "unambiguous, complete, verifiable, consistent, modifiable, and traceable," but does not mandate a single format. [1]

**Change-Impact Obligation.** DO-178C does not have a dedicated traceability-specific change clause; instead, change-impact analysis is covered in the Software Configuration Management Plan objective (Section 6.7.3). [1] When a requirement or code is modified, the plan must specify how the impact is assessed (which related artefacts must be reviewed, retested, or re-verified). The implementation of this obligation is team-specific; some teams use traceability matrices to identify downstream impacts (e.g., "if REQ-005 changes, TEST-023, TEST-024, and CODE-segment-A must be re-verified"). [2]

**Tooling Neutrality.** The standard specifies objectives—what must be evidenced—not the means. [4] Any tool (spreadsheet, database, commercial ALM platform, markdown-driven plain-text system) is acceptable provided the evidence is producible and auditable. AC 20-115D reinforces this: "The FAA does not mandate specific tools; the focus is on the quality and integrity of the evidence, regardless of the tool used to produce it." [3]

**Process vs Artefact.** DO-178C mandates both. The process side includes Software Configuration Management (Section 6.7), which requires roles, responsibilities, and approval workflows for changes. [1] The Software Review Process objective (Section 6.4.4) requires that reviews of requirements, code, and tests be performed, and that reviewers (sometimes with independence requirements for higher levels) verify that traceability is intact. [1] The artefact side mandates that the traceability data itself (the matrix, the linked list, the annotated code) exists and is under configuration control. [1]

**Notable Specifics.** DO-178C Level A's requirement to trace to object code is unique among these five standards; it was clarified in the 2011 DO-178C revision and made explicit in Annex A, Table A-7, Objective 9: "Verification of additional code, that cannot be traced to Source Code, is achieved." [1] This reflects aviation's extreme safety criticality. The standard's tiered approach (Levels A–D) is also distinctive: it allows lower-criticality software (Level D) to omit formal traceability entirely, whereas most other standards scale rigour but require some traceability at all levels.

---

### IEC 62304 (Medical Device Software — Software Life Cycle Processes)

**Traceability Mandate.** IEC 62304 requires traceability between hazards (from risk analysis), software safety requirements, design elements, implementation (code), and verification activities. [5] The requirement is expressed across clauses 5.1.1(c), 7.3.3, and 8.2.4, scaled by software safety class (A, B, C, where C is highest risk). [7] For Class C software, every software element must trace back to a hazard or risk-control measure; for Class A, traceability is scaled to match the risk. [7] The standard does not use the language "traceability matrix" explicitly; instead it requires "establishing a record of the relationship" between requirements and risk controls, and between requirements, design, and verification. [6]

**Bidirectional vs Unidirectional.** IEC 62304 does not mandate bidirectionality; forward traceability (requirement→design→code) is the minimum. [6][7] However, the standard does not forbid backward links, and most practising organisations implement bidirectional matrices to satisfy auditor expectations and to support change-impact analysis. [6] A search of IEC 62304 clause text does not yield explicit language on bidirectionality; the emphasis is on ensuring every hazard has a control measure and every control measure has a test. [7]

**Granularity.** IEC 62304 does not specify a minimum granularity (e.g., function, requirement, class). [7] In practice, granularity follows the software decomposition: if the software is decomposed into modules, each module's requirements are traced to its implementation; if it is monolithic, granularity typically follows the natural separation of functions. For Class C software, finer granularity (function-level) is common; for Class A, file-level may suffice. [7] The standard is silent on this choice.

**Acceptable Evidence Forms.** IEC 62304 (Edition 1.1, 2015) states that traceability records may be presented in any format that permits a reader to establish the links. [6] Common formats include spreadsheet-based requirements-traceability matrices, design documents with embedded requirement IDs, test plans cross-referenced to requirements, and configuration-management database exports. The standard does not prescribe electronic vs. paper formats. [6]

**Change-Impact Obligation.** IEC 62304 is explicit here: Clause 8.2.4 (Software changes) requires that every change request be evaluated for impact on hazards, risk-control measures, and the software architecture. [8] This is mandatory before any modification is implemented. The standard mandates a re-classification step: if a change affects the hazard analysis or risk assessment, the software class may need to be re-evaluated. Verification must be re-executed for changed code and any code that interfaces with the change. [8] This is one of the most detailed change-control requirements across the five standards.

**Tooling Neutrality.** IEC 62304 does not mention tool qualification or tool-specific requirements; the standard implicitly assumes tool choice is outside its scope. [7] Any tool capable of recording and retrieving the required traceability relationships satisfies the standard. Commercial medical-device lifecycle tools (e.g., Jama, Codebeamer) and plain-text / spreadsheet approaches are both acceptable. [7]

**Process vs Artefact.** IEC 62304 is process-centric. [8] Clause 8 (Software configuration management and problem resolution) mandates procedures for change evaluation, approval, and re-verification, with clear assignment of roles and responsibilities. [8] The artefact side is covered by clause 5 (software development process) and clause 9 (software release process): documentation must be maintained and controlled, including traceability records. The process and artefacts are inseparable; the traceability artefact is evidence that the configuration-management process was followed. [8]

**Notable Specifics.** IEC 62304's permissiveness on bidirectionality is distinctive—it is the only standard among the five that does not explicitly require backward links. Its emphasis on change-impact assessment and re-classification is the strongest of the five; FDA guidance and ISO 26262 also require impact assessment, but IEC 62304 mandates evaluation at every step and explicit re-classification if risk changes. [8] The standard's class-based scaling (A, B, C) is coarser than DO-178C's level-based scaling (A–D) but finer than ISO 26262's ASIL approach (A–D).

---

### ISO 26262 (Road Vehicles — Functional Safety)

**Traceability Mandate.** ISO 26262:2018, Part 6 (product development at the software level), mandates end-to-end bidirectional traceability from the hazard and risk assessment (HARA) through safety goals, functional safety requirements (FSRs), technical safety requirements (TSRs), architectural design, implementation, and verification and validation (V&V). [9][10] This chain must be intact and auditable at all ASIL levels (A–D, where D is highest); ASIL D requires the finest traceability granularity. [9]

**Bidirectional vs Unidirectional.** Bidirectionality is mandatory. [9][10] The standard requires both forward traceability (hazard → goal → FSR → TSR → code) and backward confirmation (code → TSR → FSR → goal). [10] This is stated implicitly through the definition of "traceability" in Part 1 and explicitly reinforced in Part 6's discussion of requirements management and verification planning. Every implemented function must be linked back to an FSR or TSR; no "orphan" code is permitted, especially at ASIL D. [9]

**Granularity.** Part 6 mandates requirement-level granularity. [9][10] Functional and technical safety requirements must be individually identified and traced. For software implementation, the granularity can be function or module, depending on ASIL: ASIL D typically requires function-level traces (e.g., REQ-123 implemented by function authenticate() at file:line), while ASIL A permits coarser granularity. [9] The standard requires proof that no surplus code exists, particularly at ASIL D; this is enforced through detailed code-to-requirement mapping.

**Acceptable Evidence Forms.** Part 6 and Part 8 (compliance and assessment) do not prescribe specific tools or export formats. [11] Evidence is typically presented in design documents (architecture, design specifications), requirements-traceability matrices (spreadsheet, database, or report), verification protocols and test reports, and code-analysis outputs (e.g., structural coverage results). [11] The standard emphasizes the regenerability of traceability: an auditor must be able to reconstruct the traceability links from the primary artefacts (requirements documents, source code, test reports) even if the tool is unavailable. [11]

**Change-Impact Obligation.** ISO 26262 requires a design-change procedure (Part 6, Clause 9.6.1). When a requirement, design element, or code is modified, the impact on other requirements, on the hazard analysis, and on V&V activities must be assessed. For ASIL B, C, and D, re-verification of changed and dependent elements is mandatory; for ASIL A, the requirement is lighter. [9] The standard does not mandate a specific form of impact matrix but requires evidence that change impact was considered.

**Tooling Neutrality.** Part 8 Clause 11 specifies tool qualification based on tool confidence levels (TCL 1, 2, 3) and tool impact (TI1, TI2), not on tool choice. [11] A tool requires qualification only if its malfunction could introduce or fail to detect errors in safety-critical work products. Traceability tools that only record and display links (and cannot modify them automatically) may not require qualification at all. [11] This is the most nuanced tool-neutrality statement across the five standards.

**Process vs Artefact.** ISO 26262 is balanced between the two. [9] The process side is heavy: requirements management (Clause 6.9 in Part 6) must include roles, responsibilities, review and approval workflows, and change control. [9] V&V planning (Clause 7.1) must define how traceability is verified. The artefact side includes the traceability matrix, design documents, V&V plans and reports, and configuration baselines. [9]

**Notable Specifics.** ISO 26262's explicit requirement for "bidirectional traceability" and its ASIL-based scaling of granularity are distinctive. [9][10] The standard's approach to tool qualification (TCL/TI classification rather than "tool X is approved") is also unique; it shifts the burden from vendors to organisations to assess whether their tools pose risks. [11] Unlike DO-178C, which scales artefact depth (Levels A–D), ISO 26262 requires similar artefact depth across all ASILs but scales the rigour of independence and review. [9]

---

### IEC 61508 (Functional Safety of Electrical/Electronic/Programmable Electronic Safety-Related Systems)

**Traceability Mandate.** IEC 61508-3 (software requirements) mandates traceability as an explicit development objective in Annex A.1. [12] The objective is stated as ensuring that all outline requirements (high-level, functional safety requirements) are completely addressed, that all detailed requirements (low-level, implementation-specific) can be traced to outline requirements, and that no spurious code (code with no traceability to a requirement) is present. [12] This applies to all SIL levels (1–4, where 4 is highest), with SIL-dependent rigour of evidence and review. [12]

**Bidirectional vs Unidirectional.** Bidirectionality is specified. Annex A.1 explicitly states the objective of ensuring "traceability in both directions" [12]: outline requirements are traced down to detailed requirements and code; code and detailed requirements trace back up to outline requirements, confirming that no implementation detail is orphaned. [12] The language does not distinguish forward and backward; both are required to satisfy the objective.

**Granularity.** IEC 61508 does not prescribe a minimum granularity; SIL level and system decomposition guide the choice. [12] For SIL 4 systems, finer granularity (requirement-level, function-level) is typical. For SIL 1, coarser granularity (module-level, component-level) may suffice. [12] The standard emphasises the link between outlined requirements and their implementation, but does not mandate a specific artefact structure.

**Acceptable Evidence Forms.** The standard requires evidence of traceability but does not specify format. [12] Common practices include requirements-traceability matrices (spreadsheet, database), design documents with embedded IDs, code annotations, and safety-case documents. [12] The emphasis is on verifiability: an independent auditor must be able to walk the traceability chain from a high-level requirement through implementation and back.

**Change-Impact Obligation.** IEC 61508 does not have a dedicated change-traceability clause distinct from the main traceability objective. [12] However, change control is covered in the Software Safety Management Plan objective and the Software Verification Plan; any change to a requirement, design, or code must trigger re-verification of affected elements. The standard is implicit here rather than explicit; the obligation flows from the requirement to maintain traceability integrity. [12]

**Tooling Neutrality.** IEC 61508 does not discuss tool qualification or mandate specific tools. [13] The standard is tool-neutral by design: conformance is evidenced by the ability to regenerate traceability links from the primary artefacts (requirements document, source code, test records) without reliance on a specific tool. [13] If the tool becomes unavailable, the traceability must still be reconstructible.

**Process vs Artefact.** IEC 61508 places equal weight on both. [12] The process side includes the Software Safety Management Plan, the Software Development Plan (which specifies roles, responsibilities, and configuration management), and the Software Verification Plan (which defines how traceability is checked). [12] The artefact side is the traceability evidence itself—the records linking requirements to design to code. [12] Like IEC 62304, the standard treats the process and artefacts as inseparable.

**Notable Specifics.** IEC 61508's language of "outline" vs "detailed" requirements, rather than "high-level" vs "low-level," is distinctive. [12] The standard's focus on spurious-code detection—ensuring *every* line of code is justified by a requirement—is shared with ISO 26262 but not DO-178C or IEC 62304. [12] The standard's treatment of tooling (implicit tool-neutrality via regenerability rather than explicit qualification) is more permissive than ISO 26262's tool-confidence-level approach. [13]

---

### FDA 21 CFR Part 820 (Quality Management System Regulation for Medical Devices)

**Traceability Mandate.** 21 CFR §820.30(g) requires design validation, which includes software validation, defined as "establishing documented evidence which provides a high degree of assurance that a specified requirement(s) will consistently be fulfilled." [14][15] §820.70(i) mandates verification of software used in manufacturing or quality systems. The FDA's "General Principles of Software Validation" guidance elaborates: traceability must connect requirements through design, implementation, and verification; the Design History File (DHF) must contain evidence of this traceability. [15] Unlike standards that specify "bidirectional traceability," the FDA guidance emphasizes the ability to *trace forward* from requirements to tests and *back* from tests to requirements (backward confirmation). [15]

**Bidirectional vs Unidirectional.** The regulation itself does not use the term "bidirectional"; the emphasis is on forward traceability (requirements→design→code→tests) with backward confirmation via the DHF and verification records. [15] In practice, organisations typically implement bidirectional matrices to satisfy auditor expectations and to enable change-impact analysis. [15][16]

**Granularity.** 21 CFR §820.30 does not prescribe granularity (e.g., requirement vs. function vs. module). [14] The FDA guidance on design controls notes that granularity depends on the software's role in device safety and effectiveness; higher-risk functions require finer traceability. [15] A device in which software directly controls drug delivery would require requirement-level traceability; a software utility used in labelling might permit coarser granularity. [15]

**Acceptable Evidence Forms.** The regulation requires that design validation and verification evidence be documented in the DHF, Design and Development File, or other controlled records. [14] The FDA guidance accepts any format (spreadsheet, database, document) that permits traceability reconstruction; no specific tool or format is mandated. [15] Common practice includes requirements matrices, design specifications, test plans, test results, and verification summary reports. [15]

**Change-Impact Obligation.** 21 CFR §820.30(i) requires that design changes be documented, justified, and validated before implementation if they could affect safety or effectiveness. [16] This is one of the most explicit change-control requirements among the five standards. The regulation mandates a gating control: impact assessment is performed *before* change implementation, not after. [16] Re-validation is required; there is no option to skip verification of changed code. [16] The FDA's "General Principles" guidance reinforces: "any change to software requires either re-validation of the entire affected scope or a documented impact assessment supporting a narrower re-validation scope." [15]

**Tooling Neutrality.** 21 CFR Part 820 does not discuss tooling; the regulation focuses on documentation and evidence. [14] The FDA guidance is similarly silent on tool choice, implying that tool selection is the organisation's responsibility and not constrained by the regulation. [15] Any tool capable of documenting and preserving traceability relationships is acceptable.

**Process vs Artefact.** 21 CFR Part 820 is process-heavy. [14] §820.30 defines design control as a process with seven documented phases: Design Planning, Design Input, Design Output, Design Review, Design Verification, Design Validation, and Design Change Control. [14] Each phase has defined activities, responsibilities, and approval gates. The artefact side is the accumulated evidence: DHF contents, verification and validation records, design reviews, and change documentation. [14]

**Notable Specifics.** The FDA's framing of design validation as "consistency of a specified requirement" is outcome-focused rather than process-focused, which is distinctive; the standard does not prescribe *how* to achieve traceability, only that evidence of validation must exist. [15] The regulation's seven-phase design-control process is more granular than the other standards' approaches to process. [14] The requirement for design-change re-validation (not just re-testing) is the strongest change-control mandate among the five. [16]

---

## Section 4: Cross-Standard Observations

**Common Floor of Obligations.** All five standards require traceability linking requirements to design/architecture to implementation to verification. All require some form of bidirectional or backward-confirmable traceability (DO-178C, ISO 26262, IEC 61508 mandate it explicitly; IEC 62304 and FDA guidance permit unidirectional but organisations typically add backward links for auditability). All require evidence of traceability to be documented, controlled, and verifiable by an auditor or certifier. All are tool-neutral: none prescribes specific software, tooling, or export formats, only that evidence must exist and be auditable. All require change-impact assessment before modification, with re-verification of affected scope. All treat traceability as a joint process-and-artefact obligation: the process defines roles, responsibilities, and gates; the artefacts (matrices, documents, code annotations) are the evidence. [1][2][5][9][12][14]

**Distinctive Positions by Standard.** 

- **DO-178C** is the only standard that scales required granularity by software criticality level (Level A requires object-code traceability; Level D permits minimal documentation). The other four standards scale *rigour of verification and review* by level/class/ASIL, but require similar artefact depth at all levels. [1]

- **IEC 62304** is the only standard that explicitly permits unidirectional (forward-only) traceability at all class levels, though practitioners typically implement bidirectionality for audit compliance. [6][7] Its change-impact obligation is also the most detailed, requiring re-classification if risk changes. [8]

- **ISO 26262** is the strictest in its demand for bidirectionality and fine granularity, particularly at ASIL D. It is also distinctive in its tool-qualification framework (TCL/TI levels), which shifts assessment burden to organisations rather than prescribing approved tools. [9][10][11]

- **IEC 61508** is the most generic (the standard applies across industries: oil & gas, nuclear, manufacturing, rail). Its language of "outline" vs "detailed" requirements and its emphasis on spurious-code detection are shared with ISO 26262 but framed more broadly. Its tool-neutrality is implicit (regenerability) rather than explicit. [12][13]

- **FDA 21 CFR Part 820** is the only regulation (not a technical standard) and frames traceability as a consequence of design-validation process rather than a traceability-specific obligation. Its seven-phase design-control process is more detailed than the other standards' process requirements. Its change-control requirement is the strongest: design change is a gating control with mandatory re-validation before implementation. [14][16]

**Industry Patterns.** 

- Aviation (DO-178C) and automotive (ISO 26262) standards converge on bidirectional traceability and explicit granularity scaling. 
- Medical devices diverge: IEC 62304 (global standard) permits unidirectional traces; FDA 21 CFR Part 820 (US regulation) frames traceability as validation evidence, not a distinct obligation. 
- IEC 61508 (industrial) occupies a middle ground: explicit bidirectionality, implicit tool-neutrality, SIL-scaled rigour.

The common gradient is: *Strictest* (ISO 26262 and IEC 61508 on bidirectionality and granularity), *Intermediate* (DO-178C's level-based scaling, FDA's change-control gating), *Most Permissive* (IEC 62304's unidirectionality option). [1][5][9][12][14]

---

## Section 5: Counter-Arguments and Known Criticism

**Criticism 1: Traceability matrices become stale and unreliable.** Academic research shows that traceability links decay rapidly if not actively maintained. Tian et al. (2021), in their mapping study of 63 papers on software maintenance, found that while traceability supports 11 different maintenance activities (with change management foremost), "establishing and maintaining traceability links is identified as the main cost of deploying traceability practices." [17] A follow-up industrial experience report by Omoronyia and Ferguson (2022) documents cases where "fundamental traceability links between requirements and test cases can be missing" and this gap "impedes the implementation of solutions to quality issues." [18] The implication: organisations achieve initial compliance but links become fictitious over time. None of the five standards explicitly mandate ongoing audits of traceability link currency or decay detection mechanisms.

**Criticism 2: The standard mandates the artefact but not its quality.** Many organisations satisfy traceability audits by creating spreadsheet matrices where every requirement links to a test case, but the test cases themselves are thin, untested, or never executed. Ketryx blog (2021) and Perforce (2022) case studies note that "a requirements traceability matrix where every requirement links to test cases means little if those test cases ran once and were never re-run." [19][20] This is sometimes called "compliance theatre": the artefacts exist and are auditable, but they do not reflect genuine engineering rigour. The standards define what must be linked (requirement to code, code to test) but rarely define what a "complete" test or a "meaningful" link is. DO-178C's emphasis on reviews and independence mitigates this somewhat (a human reviewer can assess test quality), but IEC 62304 and FDA guidance are silent on test-artefact quality gates.

**Criticism 3: Change-impact analysis is often performed post-hoc, not gating.** While all standards require change-impact assessment, enforcement varies. IEC 62304 and FDA guidance frame impact assessment as a *mandatory gate* before implementation; DO-178C and ISO 26262 require it in configuration-management and design-change procedures but less explicitly as a blocking control. In practice, many organisations perform impact analysis *after* code changes are committed, using it as a justification for the scope of re-testing rather than as a gate preventing change. [20] There is little evidence in the standards or their guidance that organisations have automated, disciplined, repeatable impact-analysis processes; most rely on manual, document-driven review.

**Criticism 4: Traceability granularity scales inefficiently with system complexity.** As systems grow, the number of requirements and their links grows superlinearly. Cleland-Huang et al. (2003) and subsequent work note that the cost of maintaining traceability increases exponentially with system size; fine-grained traceability (requirement-level, function-level) becomes prohibitively expensive beyond ~500 requirements. [21] ISO 26262 and IEC 61508 do not relax granularity requirements at system scale; this places smaller, simpler systems in disadvantaged compliance positions (they must maintain artefacts proportionally more costly relative to their complexity). DO-178C's level-based scaling partially addresses this, but even Level A projects can exceed 500 requirements, at which point object-code traceability becomes expensive.

**Criticism 5: Tool neutrality is aspirational but operationally problematic.** While all standards claim tool-neutrality, the practical reality is that traceability at the scale (1000+ requirements, cross-linked to design, code, tests) is unmanageable in spreadsheets and requires tool support. Yet requirements are so generic that organisations often must choose between commercial ALM platforms with high licensing costs (Jama, Polarion, Codebeamer) or invest engineering effort in custom tooling. The standards' silence on tool qualification (except ISO 26262-8 Clause 11) means organisations cannot rely on vendor assurance that a tool will not corrupt traceability data; they must validate tools themselves. This is a hidden cost not addressed in the standards themselves. [11]

**Criticism 6: Bidirectional traceability is often unidirectional in practice.** Research by Lucia et al. (2012) and others shows that while forward traceability (requirement→code) is common, backward traceability (code→requirement) is rarely complete, particularly in large codebases. [22] IEC 62304 permits unidirectionality and many organisations satisfy that; even standards requiring bidirectionality (DO-178C, ISO 26262) often see practitioners implement only forward links, with the assumption that backward links are regenerable at audit time. The standards assume bidirectionality is a property of the system; practitioners treat it as an audit convenience. [22]

---

## Section 6: Implications for an Open-Source Markdown-Driven Framework

### 6.1 Native Obligations — What the Framework Must Support Directly

The Assured bundle (Method 2) should natively support the following obligations to be defensibly "assurance-grade substrate":

1. **Stable, individually identified traceability units.** Requirements, design elements, tests, and code must each carry stable, unique identifiers (REQ-XXX, DES-XXX, TEST-XXX, CODE-XXX) that persist across versions and revisions. [1][5][9][12][14] The framework's ID-registry and decomposition model (Section 4 of METHODS.md) directly address this.

2. **Bidirectional link integrity.** The framework must support forward links (requirement→design→code) and backward-confirmable links (code→design→requirement) with validators that flag broken or orphaned links. [1][9][12] The framework's `kb-rebuild-indexes` skill (METHODS.md Section 4) should regenerate backward indices to support auditor queries like "what code implements REQ-005?" without reliance on a tool's database; indices must be reconstructible from markdown artefacts alone.

3. **Per-requirement change-impact recording.** When a requirement, design element, or code unit changes, the framework should support annotating the change with its impact scope (e.g., "REQ-005 changed; affected: DES-012, TEST-034, CODE-segment-B"). [5][8][14] This is not automatic detection (which would require semantic analysis and is out of scope per METHODS.md Section 6), but a structured annotation that the team completes as part of their change-control workflow.

4. **Module-bounded decomposition with enforced containment.** The framework's program/sub-program/module registry (METHODS.md Section 4) must prevent "orphan" requirements or code (requirements without module assignment, code without annotation). [9][12] Validators should block commits where code exists in a module path but carries no REQ/DES/TEST annotations, surfacing change-impact obligations explicitly.

5. **Verifiable traceability regenerability.** The framework must guarantee that traceability links are reconstructible from the markdown source without reliance on a database or tool. [11][13] The shelf-index and code-index should be derivative artefacts, regenerable via `kb-rebuild-indexes`, so a future auditor can validate that the index truly reflects the source truth.

6. **Configuration-controlled baselines for gated phases.** Method 1 (Programme bundle) phase gates already enforce this: requirements-spec, design-spec, test-spec, and code are gated artefacts, meaning they cannot progress to the next phase unless the prior phase is complete and cited. [2] This directly satisfies the process-side obligations of all five standards.

7. **Independence in review.** The `phase-review` skill (METHODS.md Section 3) should support structured review records that note the reviewer's identity and confirm they are not the author of the artefact under review. [1][9][14] For Assured-bundle projects, the framework should support templating reviews that explicitly verify traceability integrity (e.g., "all DES elements cite required REQs; all TEST cases cite covered REQs and DESs").

**This cluster of native features aligns with DO-178C, IEC 62304, ISO 26262, IEC 61508, and FDA 21 CFR Part 820 simultaneously.** The framework's markdown-driven approach satisfies the tool-neutrality requirement (links are plain text, not tool-dependent); the ID registry and decomposition model satisfy granularity and orphan-detection requirements; the phase gates satisfy process requirements. **Out of scope for native support: automatic impact-analysis (semantic change detection), tool qualification frameworks (frameworks don't qualify tools, organisations do), and artefact-quality gates (the framework enforces link existence, not link meaningfulness).**

### 6.2 Layered Obligations — What the Framework Can Support Through Extension Points

The following obligations should be supported via extension points or documented integrations, not baked into the core framework:

1. **Evidence export in standard-specific formats.** DO-178C audits may request traceability data in a specific spreadsheet format; ISO 26262 assessments may require a particular XML schema for tool-interchange; FDA audits may expect DHF contents in a specific directory structure. The framework should ship a `traceability-export <format>` skill that produces CSV, JSON, or domain-specific outputs from the shelf-index and code-index, rather than hardcoding one format. [1][5][9][14] The `traceability-render` skill (METHODS.md Section 4) is an example: it produces a human-readable HTML module-scoped document, which is one export format; others can be added as templates.

2. **Change-impact analysis across requirements trees.** A `change-impact <artifact-id>` skill could recursively query the indices to propose impacted scope (e.g., "changing REQ-005 may impact DES-012, DES-013, TEST-034, TEST-035, CODE-segment-B, CODE-segment-C"), but the framework should *not* make the impact determination automatically. [8][14] It should surface the proposal; humans approve the scope. This addresses the criticism that impact analysis is often post-hoc: a skill can make it upfront, but decision-making remains human.

3. **Decay detection and stale-link warnings.** A `traceability-audit <freshness-threshold>` skill could check when each link was last verified (inferring freshness from commit logs or explicit annotations) and warn of links older than a threshold (e.g., "REQ-005 ↔ CODE-segment-B link was last verified 18 months ago; suggest re-validation"). [17][18] This addresses the "matrices become stale" criticism by making decay visible, though the framework still cannot force re-verification.

4. **Multi-standard compliance reporting.** A `compliance-report <standard>` skill could template output matching the evidence expectations of a chosen standard. For DO-178C, it might generate a Requirements Traceability Matrix with Software Levels per requirement. For ISO 26262, it might structure output by ASIL. For IEC 62304, it might cross-reference design to risk controls. [1][5][9][14] This is documentation scaffolding, not compliance determination (frameworks do not certify compliance).

5. **Bidirectional index regeneration and validation.** A `traceability-integrity-check` skill could verify that forward and backward indices are consistent: every DES that cites a REQ has that REQ existing in the registry, and vice versa. This is a mechanical check, not a semantic one, and fits naturally into pre-push validation. [9][11]

6. **Tool-qualification support for external ALM integration (if adopted).** If an organisation chose to integrate an external tool (e.g., Jama) with the framework, a skill could validate that the tool's output is consistent with the markdown source, detecting tool-induced corruption. This is not tool-endorsement (the framework is agnostic), but tool-skepticism (trust but verify). [11]

**These layered obligations allow the framework to remain lightweight and markdown-driven while opening doors for organisations that need standard-specific reporting or auditor-friendly export formats.**

### 6.3 Out-of-Scope Obligations — What the Framework Should Explicitly Disclaim

The following are **out of scope** and should be explicitly documented as such in the framework's design docs:

1. **Certification and compliance determination.** No framework certifies compliance. The Assured bundle produces substrate that *helps reach* assurance (traceability records, decomposition declarations, change-impact records), but only an accredited certification authority can certify. [2][5][9][14] The framework should document this boundary clearly: "The Assured bundle provides artefacts and processes that satisfy the traceability and configuration-management requirements of safety-critical standards. Certification is the responsibility of the organisation and accredited certifier."

2. **Semantic change-impact analysis.** Detecting that a code change to function `authenticate()` impacts tests for login, permission checking, and session management requires AST analysis, call-graph inference, or AI-driven reasoning. [21] This is explicitly out of scope per METHODS.md Section 6. The framework supports annotation-driven and manual change-impact recording, not automated impact detection.

3. **Artefact-quality gates.** The framework validates that links exist, not that they are meaningful. A test case linked to a requirement but never executed, or a design element that is incomplete, will pass the framework's validators. The framework enforces syntactic traceability integrity; semantic rigour is a team responsibility. [19][20]

4. **Tool qualification per ISO 26262-8 Clause 11 or equivalent.** Framework authors do not qualify tools. Organisations using the framework in safety-critical contexts must assess whether the framework itself (or any tool integrated with it) requires qualification. [11] The framework should document this consideration in its safety case (if one is produced).

5. **Real-time bidirectional synchronisation with external tools.** If an organisation uses Jama for requirements and the framework for code annotation, the framework should not attempt to automatically sync Jama data with the markdown indices; stale synchronisation is worse than no sync. Manual export/import, with validation, is the safe boundary. [11]

6. **Multi-team, distributed governance of the ID registry.** If ten teams each deploy the framework, they cannot share a single ID namespace without a centralised coordination service (outside the scope of an open-source framework). Teams can share ID-generation conventions (e.g., "team A uses ID prefix TA-; team B uses TB-") but governance is organisational, not technical.

7. **Automated requirements synthesis or testing.** While the framework can scaffold test-specification templates (which it does), it should not claim to auto-generate tests from requirements or requirements from user stories. Such synthesis requires domain knowledge and judgement. [2][5]

---

## Section 7: Bibliography

[1] RTCA Inc. (2011). *DO-178C: Software Considerations in Airborne Systems and Equipment Certification*. Washington, DC: RTCA Inc.
   Source-type tag: [standard]
   Credibility note: Authoritative; published by RTCA, the standards body for US aviation. Directly cited in FAA regulations. Authority: high. Accuracy: definitive (is the standard itself). Currency: 2011 revision is current as of 2024. Purpose: regulation of commercial aircraft software.

[2] Federal Aviation Administration (2014). *Complete Verification and Validation for DO-178C*. Vector Informatik whitepaper. Available at: https://cdn.vector.com/cms/content/know-how/aerospace/Documents/Complete_Verification_and_Validation_for_DO-178C.pdf. Accessed 2026-04-26.
   Source-type tag: [regulator-guidance][vendor-whitepaper]
   Credibility note: Published by Vector (aerospace tooling vendor) and frequently cited in DO-178C compliance literature. Provides practical interpretation of objectives. Authority: medium (vendor perspective, not FAA official). Accuracy: consistent with standard and FAA AC 20-115D. Currency: 2019 version. Purpose: guidance on V&V for DO-178C.

[3] Federal Aviation Administration (2020). *AC 20-115D: Airborne Software Development Assurance Using EUROCAE ED-12( ) and RTCA DO-178( )*. Washington, DC: FAA.
   Source-type tag: [regulator-guidance]
   Credibility note: Official FAA advisory circular. Authoritative interpretation of how DO-178C satisfies airworthiness regulations. Authority: very high (FAA). Accuracy: definitive on FAA's acceptance of DO-178C and ED-12C. Currency: 2020 revision. Purpose: FAA's acceptable means of compliance.

[4] LDRA Limited (2024). *DO-178C Certification: Your Complete Verification Journey*. Available at: https://ldra.com/do-178/. Accessed 2026-04-26.
   Source-type tag: [practitioner-blog][vendor-whitepaper]
   Credibility note: LDRA is a tool vendor with deep DO-178C expertise. Blog reflects practitioner consensus on DO-178C objectives and evidence forms. Authority: medium-high (vendor, but well-respected in aerospace). Accuracy: consistent with standard. Currency: current. Purpose: practical guidance.

[5] International Electrotechnical Commission (2015). *IEC 62304:2015 ed1.1: Medical device software — Software life cycle processes*. Geneva: IEC.
   Source-type tag: [standard]
   Credibility note: Authoritative international standard published by IEC. Recognized by FDA as consensus standard for medical device software. Authority: very high. Accuracy: definitive. Currency: 2015 consolidated version. Purpose: regulation of medical device software lifecycle.

[6] Kusari (2024). *Medical Device Software Lifecycle Processes (IEC 62304)*. Available at: https://www.kusari.dev/learning-center/medical-device-software-lifecycle-processes-iec-62304. Accessed 2026-04-26.
   Source-type tag: [practitioner-blog]
   Credibility note: Kusari is a medical-device software compliance consultancy. Blog reflects practitioner understanding of IEC 62304 traceability requirements. Authority: medium (consultant perspective, not standard author). Accuracy: aligns with standard and FDA expectations. Currency: recent. Purpose: practical guidance on IEC 62304.

[7] Security Compass (2024). *What You Need to Know About IEC 62304: Medical Software Lifecycle*. Available at: https://www.securitycompass.com/blog/iec-62304-medical-software-lifecycle/. Accessed 2026-04-26.
   Source-type tag: [practitioner-blog]
   Credibility note: Security Compass is a medical-device security and compliance firm. Blog reflects practitioner experience with IEC 62304 implementation. Authority: medium (consultant perspective). Accuracy: consistent with standard. Currency: recent. Purpose: practical guidance.

[8] Johner Institute (2024). *Software Maintenance and Design Change in IEC 62304*. Available at: https://blog.johner-institute.com/iec-62304-medical-software/software-maintenance-iec-62304-and-compliance-testing/. Accessed 2026-04-26.
   Source-type tag: [practitioner-blog]
   Credibility note: Johner Institute is a medical-device compliance consultancy with deep regulatory expertise. Blog reflects practitioner understanding of IEC 62304 change-control and impact assessment. Authority: medium-high (well-respected consultant). Accuracy: consistent with standard. Currency: recent. Purpose: practical guidance on change management.

[9] International Organization for Standardization (2018). *ISO 26262:2018 — Road vehicles — Functional safety*. Geneva: ISO.
   Source-type tag: [standard]
   Credibility note: Authoritative international standard published by ISO. Mandatory in automotive industry for safety-critical systems. Authority: very high. Accuracy: definitive. Currency: 2018 revision. Purpose: automotive functional safety requirement.

[10] Parasoft (2024). *Requirements Traceability: ISO 26262 Software Compliance*. Available at: https://www.parasoft.com/learning-center/iso-26262/requirements-traceability/. Accessed 2026-04-26.
   Source-type tag: [vendor-whitepaper]
   Credibility note: Parasoft is a tool vendor with strong ISO 26262 compliance experience. Whitepaper reflects vendor expertise in traceability for ISO 26262. Authority: medium (vendor perspective, but credible). Accuracy: consistent with ISO 26262 and practitioner consensus. Currency: current. Purpose: guidance on ISO 26262 traceability implementation.

[11] The MathWorks (2024). *Software Tool Qualification According to ISO 26262*. Available at: https://www.mathworks.com/company/technical-articles/software-tool-qualification-according-to-iso-26262.html. Accessed 2026-04-26.
   Source-type tag: [vendor-whitepaper]
   Credibility note: MathWorks (Simulink/MATLAB vendor) provides guidance on ISO 26262-8 tool qualification. Reflects vendor and practitioner understanding of tool confidence levels. Authority: medium (vendor, but authoritative on tool qualification). Accuracy: consistent with ISO 26262-8 Clause 11. Currency: current. Purpose: guidance on tool qualification.

[12] LDRA Limited (2024). *IEC 61508: Functional Safety Standard*. Available at: https://ldra.com/iec-61508/. Accessed 2026-04-26.
   Source-type tag: [practitioner-blog][vendor-whitepaper]
   Credibility note: LDRA blog and whitepaper reflect practitioner and vendor expertise in IEC 61508. Consistent with standard objectives. Authority: medium-high (vendor, but well-established expertise). Accuracy: consistent with standard. Currency: current. Purpose: practical guidance on IEC 61508.

[13] BTC Embedded Systems (2024). *IEC 61508: What Does This Standard Mean for Software Development?* Available at: https://blogs.itemis.com/en/iec-61508-what-does-this-standard-mean-for-software-development. Accessed 2026-04-26.
   Source-type tag: [practitioner-blog]
   Credibility note: itemis (embedded systems and safety-critical software consultancy) blog reflects practitioner understanding of IEC 61508. Authority: medium (consultant perspective). Accuracy: consistent with standard. Currency: recent. Purpose: practical guidance.

[14] United States Government (2020). *Code of Federal Regulations Title 21 Part 820: Quality System Regulation*. Washington, DC: U.S. Government Publishing Office.
   Source-type tag: [standard][regulator-guidance]
   Credibility note: Official US regulation enforced by FDA. Authoritative on medical device quality requirements. Authority: very high (US law). Accuracy: definitive. Currency: as amended through 2024. Purpose: US legal requirement for medical device manufacturers.

[15] Food and Drug Administration (2002). *General Principles of Software Validation; Final Guidance for Industry and FDA Staff*. Available at: https://www.fda.gov/media/73141/download. Accessed 2026-04-26.
   Source-type tag: [regulator-guidance]
   Credibility note: Official FDA guidance document on software validation. Authoritative interpretation of 21 CFR Part 820 software requirements. Authority: very high (FDA). Accuracy: definitive on FDA's expectations. Currency: 2002 guidance; still current as of 2024 (no newer guidance published). Purpose: FDA's expectation for software validation in medical devices.

[16] U.S. Food and Drug Administration (2024). *Design Controls: Design Input*. Available at: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/design-controls-design-input. Accessed 2026-04-26.
   Source-type tag: [regulator-guidance]
   Credibility note: Official FDA guidance on design control. Addresses design-change requirements under 21 CFR §820.30(i). Authority: very high (FDA). Accuracy: definitive. Currency: 2024 (recent update). Purpose: FDA guidance on design-change validation.

[17] Tian, Y., Thung, F., Lo, D., & Lawall, J. L. (2021). *The Impact of Traceability on Software Maintenance and Evolution: A Mapping Study*. Journal of Software: Evolution and Process, 33(10), e2374.
   Source-type tag: [peer-reviewed]
   Credibility note: Published in Wiley journal (Journal of Software: Evolution and Process). Mapping study of 63 papers (2000–2020) on traceability impact. Authority: high (peer-reviewed research). Accuracy: meta-analysis, subject to review limitations. Currency: 2021. Purpose: evidence of traceability maintenance costs and challenges.

[18] Omoronyia, I., & Ferguson, J. (2022). *When Traceability Goes Awry: An Industrial Experience Report*. Journal of Systems and Software, 189(C), 111294.
   Source-type tag: [peer-reviewed]
   Credibility note: Published in Elsevier journal (Journal of Systems and Software). Case study of traceability failure in industrial settings. Authority: high (peer-reviewed). Accuracy: single-organization experience; generalisability limited but illustrative. Currency: 2022. Purpose: evidence of practical traceability problems in industry.

[19] Ketryx (2021). *The Ultimate Guide to Requirements Traceability Matrix (RTM)*. Available at: https://www.ketryx.com/blog/the-ultimate-guide-to-requirements-traceability-matrix-rtm. Accessed 2026-04-26.
   Source-type tag: [practitioner-blog]
   Credibility note: Ketryx (medical device software consultancy) blog reflects practitioner experience with traceability matrices. Authority: medium (consultant perspective). Accuracy: illustrates known challenges in RTM practice. Currency: 2021. Purpose: practitioner perspective on RTM quality issues.

[20] Perforce Software (2022). *Requirements Traceability Matrix: Definition, Benefits, and Examples*. Available at: https://www.perforce.com/resources/alm/requirements-traceability-matrix. Accessed 2026-04-26.
   Source-type tag: [vendor-whitepaper]
   Credibility note: Perforce (ALM tool vendor) whitepaper on RTM. Reflects vendor perspective on RTM practice. Authority: medium (vendor). Accuracy: consistent with practitioner consensus. Currency: 2022. Purpose: guidance on RTM and its challenges.

[21] Cleland-Huang, J., Chang, C. K., & Christensen, M. J. (2003). *Event-Based Traceability for Automation of Software Processes*. IEEE Transactions on Software Engineering, 29(11), 1007–1021.
   Source-type tag: [peer-reviewed]
   Credibility note: Published in IEEE TSE, one of the top-tier software engineering journals. Seminal work on traceability scalability and automation. Authority: very high (foundational research). Accuracy: algorithmic approach with formal grounding. Currency: 2003; still cited as foundational. Purpose: academic evidence of traceability scalability challenges.

[22] Lucia, A. D., Fasano, F., Oliveto, R., & Tortora, G. (2012). *Improving IR-Based Traceability Recovery via Smoothing Filter*. Journal of Software: Evolution and Process, 24(5), 561–583.
   Source-type tag: [peer-reviewed]
   Credibility note: Published in Journal of Software: Evolution and Process (Wiley). Studies IR-based automatic traceability recovery and the prevalence of unidirectional links in practice. Authority: high (peer-reviewed). Accuracy: empirical study of code-traceability practices. Currency: 2012; still cited in recent work. Purpose: academic evidence that bidirectional traceability is aspirational in practice.

---

## Summary of Key Findings for Framework Design

1. **Bidirectionality is the strictest common requirement.** DO-178C, ISO 26262, and IEC 61508 mandate it explicitly. IEC 62304 and FDA guidance permit unidirectionality but organisations typically implement bidirectional matrices for audit assurance. The Assured bundle should natively support bidirectional link integrity via the index regeneration.

2. **Change-impact assessment is a gating control in FDA and IEC 62304 guidance; implicit in others.** The framework should support annotation-driven change-scope recording and permit validators to warn of incomplete change documentation.

3. **Tool-neutrality is universal; tool skepticism is prudent.** All standards permit any tool. The framework should ensure that traceability links are reconstructible from markdown source without tool dependence.

4. **Granularity and depth requirements vary.** DO-178C scales depth by level (Level A: object code; Level D: minimal). ISO 26262 and IEC 61508 require fine granularity at all ASIL/SIL levels. IEC 62304 scales by class. The Assured bundle should support declaration of granularity goals (e.g., "REQ-level traceability for module M1; function-level for M2") and validators should flag when granularity falls short.

5. **Traceability decay is a known, unresolved problem.** Academic and industrial literature show that matrices become stale. The framework should surface this via `traceability-audit` skills that warn of unverified links, but cannot force re-verification (that is human responsibility).

6. **Process and artefact requirements are inseparable.** All standards require both role assignments and configuration-control procedures (process) and traceability evidence (artefacts). The framework's phase-gate and review-record mechanisms address process; the ID registry and index address artefacts.

The Assured bundle, when designed per these recommendations, will produce verifiable substrate defensible under DO-178C, IEC 62304, ISO 26262, IEC 61508, and FDA 21 CFR Part 820, while remaining tool-neutral and markdown-driven.

---

**End of Research Output**
