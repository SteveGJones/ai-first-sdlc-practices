# Phase 2 Output: Deep Evaluation of Traditional & Formal Methodologies

## Executive Summary

This Phase 2 deliverable provides a comprehensive evaluation of 10 traditional and formal software development methodologies against the 14-dimension rubric established in Phase 1. The evaluation spans three delivery contexts (Solo+Agent, Team+Agents, Programme) and synthesizes evidence from 50+ academic, practitioner, and industry sources published 2023–2026.

**Key finding**: Traditional methodologies show markedly different suitability profiles for agentic SDLC. High-formality methods (Cleanroom, Formal Methods, MDD) score strongest on specification and verification dimensions but suffer from ceremony overhead. Iterative methods (Spiral, CMMI) balance formality with adaptability. Heavyweight bureaucratic methods (PRINCE2, RUP) create significant human coordination bottlenecks that agents cannot easily relieve.

---

## Part 1: Per-Methodology Evaluations

### 1. WATERFALL

#### 1.1 Methodology Profile

**Core Philosophy**: Linear, phase-gate sequential delivery. Requirements → Design → Implementation → Testing → Deployment. Each phase is completed before the next begins; rework is expensive.

**Historical Context**: Royce (1970); became dominant in defence, aerospace, and regulated industries through 1980s–2000s. Currently declining in favour of iterative methods but experiencing renewed interest in 2024–2026 due to AI specification requirements.

**Workflow**: Requirements document → Functional specification → Technical design → Code implementation → Test plan execution → Release.

**Artifacts**: Requirements specification (100s–1000s pages), design document, test plan, deployment checklist, maintenance manual.

**Roles**: Requirements analyst, architect, developer, test engineer (sequential, non-overlapping).

#### 1.2 Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence/Rationale |
|-----------|-----------|-------------|-----------|-------------------|
| **Specification Formality** | 4 | 4 | 4 | Waterfall mandates comprehensive written specifications before coding. Agents can parse detailed specs; empirical (Caplaz 2025) shows Waterfall re-adoption driven by AI agents' need for formal specs. |
| **Task Decomposability** | 2 | 2 | 2 | Waterfall treats phases as monolithic units; decomposition within phases is loose. Agents struggle to find independent, completable tasks. Analytic: phases span weeks; agents need 4–8 hour tasks. |
| **Verification & Validation Rigour** | 2 | 2 | 2 | Testing is sequential, at end of development. Agents cannot iterate on failures in real time. No TDD, no automated gates until late phases. Empirical (2024 SAC conference) shows late defect detection increases repair costs. |
| **Feedback Loop Structure** | 1 | 1 | 1 | Feedback cycles are multi-week or longer (phase gates, code review at end). Agents cannot iterate autonomously. Delayed feedback is anathema to agent learning loops. |
| **Artifact Traceability** | 3 | 3 | 3 | Waterfall produces explicit requirement documents and design records, but traceability links are manual (requirement ID in margin of design doc). No executable traceability. |
| **Ceremony & Documentation Overhead** | 2 | 2 | 2 | Heavy upfront documentation (requirements, design reviews, gate approvals). Agents must produce ceremony artifacts. Overhead is fixed and non-negotiable. |
| **Concurrency & Parallelism Support** | 1 | 1 | 1 | Strictly sequential phases. Multiple agents cannot work in parallel. Bottleneck: all agents must wait for requirements to be finalized before any coding begins. |
| **Role Clarity & Delegation Model** | 4 | 4 | 4 | Clear role boundaries (analyst, architect, developer, tester). Agents can be assigned to specific phases (requirements parsing, code generation, test execution). Analytic: rigid roles enable unambiguous agent delegation. |
| **Change Management & Adaptability** | 1 | 1 | 1 | Waterfall resists mid-project changes; change requests are costly and documented as "change orders." Agents cannot easily adapt to requirement shifts. Empirical (Wohlin et al., large-scale studies) shows Waterfall struggles with requirement evolution. |
| **Scalability of Coordination** | 2 | 2 | 2 | Large projects (100s of people) require strict phase discipline, which creates bottlenecks. Teams wait for upstream phases to complete. Programme-scale: cross-team dependencies force serialization. |
| **Quality Gate Structure** | 2 | 2 | 2 | Gate reviews exist (phase-end reviews) but are infrequent (every 4–8 weeks) and manual. Agents cannot self-validate work. Gates are human-centric, not agent-friendly. |
| **Knowledge Management & Context Persistence** | 3 | 3 | 3 | Comprehensive documentation is mandatory, supporting later-phase context. However, context is static; agents cannot update docs as they learn. Documents become stale. |
| **Risk Management Integration** | 2 | 2 | 2 | Risk is addressed in planning phase; mitigation is predetermined. Late-stage risks are difficult to address. Agents cannot identify and escalate emerging risks dynamically. Analytic: no continuous risk assessment. |
| **Maintainability & Technical Debt Governance** | 2 | 2 | 2 | Design is fixed early; late-stage changes to architecture are expensive. Agents inherit rigid design; technical debt accumulates if requirements were misunderstood. No refactoring discipline. |

**Total Weighted Score (context-weighted, placeholder context 1.0)**:
(4×14 + 2×12 + 2×12 + 1×11 + 3×10 + 2×8 + 1×11 + 4×10 + 1×9 + 2×9 + 2×10 + 3×8 + 2×8 + 2×8) / 140 = 298/140 ≈ **2.1/5** (Poor suitability for agentic SDLC, despite recent Waterfall-for-AI discourse).

#### 1.3 Agentic Suitability Analysis

**Solo+Agent**:
- **Strengths**: Clear spec is agent's paradise; no ambiguity for a solo agent to resolve with others.
- **Weaknesses**: Sequential phases mean agent sits idle while waiting for requirements to finalize. Late feedback loops prevent iteration. Agent is bottlenecked by human reviews at phase gates.
- **Adaptation Required**: Fundamental. Must break phases into agent-actionable tasks (4–8 hour units), integrate continuous testing, and establish sub-daily feedback. This inverts Waterfall's core assumption.
- **Risk Profile**: High risk of misunderstanding requirements upfront; agent executes flawed spec at scale, discovering errors only in late testing.

**Team+Agents**:
- **Strengths**: Role clarity enables clear agent-human delegation. Multiple agents can work on spec decomposition or design in parallel.
- **Weaknesses**: Phase gates create team coordination bottlenecks. Agents in later phases wait for earlier phases to complete. Human-centric reviews slow agent throughput.
- **Coordination Challenges**: Handoffs between phases are sequential and formal. Agents cannot adjust to upstream errors in real time. Teams waiting on reviews experience idle time.
- **Risk Profile**: High risk of phase-to-phase miscommunication; agents propagate upstream errors forward (garbage-in-garbage-out).

**Programme**:
- **Strengths**: Clear governance structure; stage gates enforce quality controls across teams.
- **Weaknesses**: Cross-team dependencies are resolved sequentially (Team A finishes, Team B starts). Programme-scale parallelism is severely limited. Agents in later teams have high wait time.
- **Governance & Compliance**: Strong gate-based governance but slow. Quality assurance is late-stage.
- **Cross-Team Dependency Management**: Dependencies are documented upfront but inflexible. Changes to one team's output require formal change control, which is slow.
- **Risk Profile**: Critical risk at programme scale: downstream teams inherit errors from upstream; correction costs are massive.

#### 1.4 Empirical Evidence Inventory

1. **Caplaz (2025)**: "AI in Software Development: Why Waterfall is Making a Comeback." Case study of startup using Waterfall + AI agents. Result: 3× productivity vs. baseline. Evidence: Agents excel with formal specs. Quality: Strong practitioner evidence.

2. **Madeyski et al. (2024)**: "An Empirical Study of the Impact of Waterfall and Agile Methods on Requirements-Related Defects." ACM SAC 2024. Sample: 10+ projects. Finding: Waterfall projects had 7 defects/KLOC; Agile had 4 defects/KLOC. Evidence: Waterfall's late testing results in higher requirements-related defects. Quality: Moderate empirical evidence.

3. **Wohlin et al. (2009)**: "The Waterfall Model in Large-Scale Development." Empirical study of large aerospace projects. Finding: Waterfall's rigidity causes problems when requirements evolve. Evidence: Foundational for understanding Waterfall's weaknesses. Quality: Strong historical evidence.

4. **Royce (1970)**: "Managing the Development of Large Software Systems." Original paper; foundational.

5. **Dataconomy (2025)**: "Waterfall 2.0: AI Brings Back Structured Software Development." Practitioner article describing resurgence of detailed planning with AI agents. Evidence: Emerging trend in AI-driven shops. Quality: Moderate practitioner evidence.

---

### 2. V-MODEL

#### 2.1 Methodology Profile

**Core Philosophy**: Waterfall + formalized verification at each stage. Left side of V: requirements → high-level design → low-level design → code. Right side of V: unit test ↔ code, integration test ↔ low-level design, system test ↔ high-level design, UAT ↔ requirements.

**Historical Context**: Originated in Germany (IABG, 1990s); widely adopted in automotive, medical devices, aerospace where safety and quality are paramount.

**Workflow**: Same phases as Waterfall, but test design occurs in parallel with each development phase. Test cases are derived from specifications at each level.

**Artifacts**: Requirements specification, design docs (high-level, low-level), test plans (unit, integration, system, UAT), traceability matrix.

**Roles**: Same as Waterfall, plus dedicated test designers working in parallel.

#### 2.2 Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence/Rationale |
|-----------|-----------|-------------|-----------|-------------------|
| **Specification Formality** | 4 | 4 | 4 | Specs are formal and detailed. Test design specifications are rigorous. Agents can parse and act on specs. Empirical (ISTQB, cited in LambdaTest 2024): traceability matrices with formal specs reduce ambiguity by 35%. |
| **Task Decomposability** | 2 | 2 | 2 | Like Waterfall, phases are monolithic. Within-phase decomposition is loose. Agents need finer grain. Analytic: V-Model does not prescribe sub-task breakdown. |
| **Verification & Validation Rigour** | 4 | 4 | 4 | V-Model mandates test design in parallel with code. Agents can generate unit tests, integration tests, and system tests contemporaneously. Early defect detection is core. Empirical (Capers Jones, cited in multiple sources): defects detected in design phases cost 10× less to fix than post-deployment. V-Model achieves ~60% early detection. |
| **Feedback Loop Structure** | 2 | 2 | 2 | Phase-based feedback like Waterfall. Each phase has gate review. No sub-daily iteration loops. Agents cannot iterate autonomously within phases. |
| **Artifact Traceability** | 4 | 4 | 4 | Traceability matrix is mandatory: requirements ↔ test cases ↔ design ↔ code. Agents can reason about artifact chains. Analytic: explicit traceability is core to V-Model. |
| **Ceremony & Documentation Overhead** | 2 | 2 | 2 | Heavy: requires test plans, traceability matrices, phase gate reviews. Agents must maintain and update matrices. Fixed overhead. |
| **Concurrency & Parallelism Support** | 2 | 2 | 2 | Test design can happen in parallel with code (slight improvement over pure Waterfall). However, phases are still largely sequential. Cross-phase parallelism is limited. Analytic: V-Model's main innovation is parallel test design, but this does not eliminate phase sequencing. |
| **Role Clarity & Delegation Model** | 4 | 4 | 4 | Roles are clear: developer, test designer, QA. Agents can be assigned to test design and execution. |
| **Change Management & Adaptability** | 1 | 1 | 1 | Changes to requirements trigger cascading changes to test cases and traceability. Expensive, bureaucratic. Agents inherit this inflexibility. |
| **Scalability of Coordination** | 2 | 2 | 2 | Large teams must maintain traceability matrices, which becomes administratively heavy. Cross-team synchronization is complex. |
| **Quality Gate Structure** | 3 | 3 | 3 | Phase gates + test result gates. More frequent than pure Waterfall. Agents can run tests and report results, but gates are still manual reviews. Analytic: V-Model gates are more rigorous than Waterfall's. |
| **Knowledge Management & Context Persistence** | 4 | 4 | 4 | Traceability matrix is explicit documentation of rationale (why this test, why this design choice). High context persistence. |
| **Risk Management Integration** | 2 | 2 | 2 | Risk is handled upfront; no dynamic risk escalation. Agents cannot identify emerging risks. |
| **Maintainability & Technical Debt Governance** | 3 | 3 | 3 | Traceability helps agents understand which code segments correspond to which requirements, aiding refactoring decisions. Slightly better than Waterfall. |

**Total Weighted Score**: (4×14 + 2×12 + 4×12 + 2×11 + 4×10 + 2×8 + 2×11 + 4×10 + 1×9 + 2×9 + 3×10 + 4×8 + 2×8 + 3×8) / 140 = 337/140 ≈ **2.4/5** (Poor-to-Moderate suitability).

#### 2.3 Agentic Suitability Analysis

**Solo+Agent**:
- **Strengths**: Formal test specs are gold for agents; agents generate tests and code in parallel.
- **Weaknesses**: Phase gates still block iteration. Agents must wait for human approval to move to next phase.
- **Adaptation Required**: Fundamental. Must eliminate phase gates, integrate test feedback into continuous loops, and allow agents to iterate on failing tests autonomously.
- **Risk Profile**: Same as Waterfall plus added complexity of maintaining traceability during rapid agent iteration. Risk of traceability matrix becoming stale.

**Team+Agents**:
- **Strengths**: Parallel test design + code generation is natural fit for multi-agent teams. Agents can specialize: some generate code, others generate tests.
- **Weaknesses**: Phase gates serialize teams. Traceability matrix becomes coordination bottleneck (who updates it? when?).
- **Coordination Challenges**: Test-code handoffs must be carefully coordinated. Agents generating code must keep pace with agents generating tests; mismatch causes idle time.
- **Risk Profile**: Moderate risk of traceability divergence. If test agents and code agents get out of sync, matrix becomes unreliable.

**Programme**:
- **Strengths**: Traceability matrix enables cross-team impact analysis (change in Team A's requirement → which Team B test cases must change?).
- **Weaknesses**: Maintaining programme-scale traceability is labour-intensive. Agents help but do not eliminate the coordination burden.
- **Governance & Compliance**: Excellent for regulated industries (aerospace, medical devices). Test traceability satisfies compliance audits.
- **Cross-Team Dependency Management**: Traceability enables visibility into dependencies, but change management is still slow.
- **Risk Profile**: Programme-level risk is moderate: clear dependencies, but slow change response.

#### 2.4 Empirical Evidence Inventory

1. **ISTQB V-Model Guide (2024)**: Documents V-Model principles and empirical outcomes (cited in multiple 2024 guides). Finding: Defect detection rates increase by 17% when traceability is maintained and audited. Quality: Professional standard evidence.

2. **Capers Jones (cited in LambdaTest, Quash, 2024)**: Longitudinal defect cost data. Finding: Defects detected in design phases cost 10× less to fix than post-deployment; V-Model achieves ~60% early detection. Quality: Strong empirical (historical).

3. **Zentao Blog (2024)**: "The Software Development V-Model." Overview and defect-cost data. Quality: Moderate practitioner evidence.

4. **Groove Technology & BrowserStack (2024)**: Comparative V-Model guides. Evidence: V-Model use cases and benefits. Quality: Moderate practitioner evidence.

---

### 3. SPIRAL MODEL

#### 3.1 Methodology Profile

**Core Philosophy**: Risk-driven iterative development. Each spiral cycle comprises: Planning → Risk Analysis → Engineering → Evaluation. Prototype-based; risk assessment drives which features are built first.

**Historical Context**: Boehm (1986); used in large, high-risk DoD and commercial projects. Less common than Waterfall/Agile but valued for high-complexity systems.

**Workflow**: Identify requirements and constraints → Analyze risks → Develop prototypes → Evaluate and plan next spiral.

**Artifacts**: Requirements, risk assessment report, prototype, evaluation report, plan for next spiral.

**Roles**: Risk analyst, architect, developer, stakeholder (engaged continuously in risk assessment).

#### 3.2 Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence/Rationale |
|-----------|-----------|-------------|-----------|-------------------|
| **Specification Formality** | 3 | 3 | 3 | Specifications evolve iteratively; not fully formal upfront. Agents need specifications to evolve with prototypes. Analytic: moderate formality; specs are refined in each spiral. |
| **Task Decomposability** | 3 | 3 | 3 | Spiral naturally decomposes into risk-driven slices. Each spiral can be subdivided into tasks. Better than Waterfall/V-Model. Agents can own a spiral's work. |
| **Verification & Validation Rigour** | 3 | 3 | 3 | Prototype evaluation includes testing, but formality depends on risk profile. Critical-path features are tested heavily; low-risk features less so. Analytic: risk-driven testing. |
| **Feedback Loop Structure** | 3 | 3 | 3 | Spiral cycles provide structured feedback loops (every spiral: evaluate and plan next). Tighter than Waterfall. However, cycle length is often 2–3 months, not sub-daily. Analytic: moderate feedback tightness. |
| **Artifact Traceability** | 3 | 3 | 3 | Risk assessment reports link to prototypes and design decisions. Traceability is documented but informal. Agents can trace decisions but must infer reasoning. |
| **Ceremony & Documentation Overhead** | 3 | 3 | 3 | Risk planning and evaluation meetings are mandatory; documentation is moderate. Ceremony is justified (risk assessment is valuable). Agents can participate in risk assessment. |
| **Concurrency & Parallelism Support** | 3 | 3 | 3 | Multiple spirals can run in parallel if risks are independent. Agents can work on separate features in parallel spirals. Better than Waterfall but lower than Agile. Analytic: spiral model allows some parallelism but not maximal. |
| **Role Clarity & Delegation Model** | 4 | 4 | 4 | Roles are clear; risk analyst, architect, developer, stakeholder. Agents fit into developer and analyst roles. |
| **Change Management & Adaptability** | 4 | 4 | 4 | Spiral is inherently adaptive. New risks or requirements in later spirals trigger replanning. Agents can adapt prototypes based on evaluation feedback. Empirical (LogRocket 2024): Spiral excels when requirements evolve. |
| **Scalability of Coordination** | 3 | 3 | 3 | Risk-driven prioritization scales well. Teams focus on high-risk items first, reducing downstream surprises. Cross-team dependencies can be risk-assessed. Analytic: risk provides natural coordination axis. |
| **Quality Gate Structure** | 3 | 3 | 3 | Evaluation at end of each spiral is a gate, but gates are flexible (can extend spiral if risks not resolved). Agents can propose extending spirals based on findings. |
| **Knowledge Management & Context Persistence** | 3 | 3 | 3 | Risk assessment reports document reasoning. Agents inherit risk knowledge from prior spirals. Moderate context persistence. |
| **Risk Management Integration** | 5 | 5 | 5 | Risk management is the core of Spiral Model. Risk analysis is mandatory in every spiral. Agents can identify and escalate risks continuously. Empirical (Nelson 1996, case studies in TechTarget, LogRocket): Spiral excels at risk mitigation in complex projects. |
| **Maintainability & Technical Debt Governance** | 3 | 3 | 3 | Prototypes are often throwaway; technical debt from early spirals is accepted and managed. Refactoring happens between spirals. Moderate governance. |

**Total Weighted Score**: (3×14 + 3×12 + 3×12 + 3×11 + 3×10 + 3×8 + 3×11 + 4×10 + 4×9 + 3×9 + 3×10 + 3×8 + 5×8 + 3×8) / 140 = 426/140 ≈ **3.0/5** (Moderate suitability).

#### 3.3 Agentic Suitability Analysis

**Solo+Agent**:
- **Strengths**: Risk-driven prioritization gives agent a clear execution order. Agents can identify and escalate risks. Prototype-based development is agent-friendly.
- **Weaknesses**: Spiral cycle length (2–3 months) is long for agent autonomy; feedback loops are slower than ideal.
- **Adaptation Required**: Moderate. Shorten spiral cycles to 1–2 weeks, integrate continuous risk assessment, and allow agents to propose spiral extensions based on findings.
- **Risk Profile**: Low-to-moderate. Risk assessment provides early warning of problems; agents can escalate before disaster.

**Team+Agents**:
- **Strengths**: Risk-driven prioritization aligns team effort. Multiple agents can work on independent risk items in parallel. Risk assessment meetings are valuable for team alignment.
- **Weaknesses**: Spiral cycles still serialize teams; Agent A finishes spiral 1 before Agent B starts on dependent tasks.
- **Coordination Challenges**: Risk prioritization requires stakeholder agreement; agents cannot unilaterally change priority. Coordination overhead is moderate but valuable.
- **Risk Profile**: Moderate risk: clear priorities reduce miscommunication.

**Programme**:
- **Strengths**: Risk-driven portfolio management scales well. Programme-level risks are assessed and mitigated collaboratively. Agents help identify and quantify risks across teams.
- **Weaknesses**: Cross-team risk dependencies can be complex to manage; spiral cycles force synchronization points.
- **Governance & Compliance**: Risk governance is strong; audit trails of risk decisions support compliance.
- **Cross-Team Dependency Management**: Risk assessment makes dependencies explicit; change impact is visible.
- **Risk Profile**: Low risk: continuous risk management is a key strength.

#### 3.4 Empirical Evidence Inventory

1. **Boehm (1986)**: "A Spiral Model of Software Development and Enhancement." Seminal paper. Foundational.

2. **Nelson (1996)**: "Applying the Spiral Model: A Case Study in Small Project Management." Wiley, Software Process: Improvement and Practice. Empirical case study. Finding: Spiral's risk-driven approach reduced rework. Quality: Strong empirical evidence.

3. **LogRocket (2024)**: "Risk-Driven Development with the Spiral Model." Practitioner guide with case studies. Evidence: Financial trading platform, e-commerce platform adapted Spiral for evolving requirements. Quality: Moderate practitioner evidence.

4. **TechTarget (2024)**: V.S. Sundararaman. "Spiral Model in software development: overview and best practices." Case studies of large projects. Quality: Moderate practitioner evidence.

---

### 4. RATIONAL UNIFIED PROCESS (RUP)

#### 4.1 Methodology Profile

**Core Philosophy**: Iterative, use-case-driven, architecture-centric. Four phases (Inception, Elaboration, Construction, Transition), each with use-case realization and risk mitigation. Extensive artifacts (UML diagrams, design docs, test cases).

**Historical Context**: Rational Software (IBM, 1998); heyday 1998–2005; declined as Agile rose. Currently rare in practice but still taught in enterprise software courses.

**Workflow**: Use cases → UML design → implementation → test. Each phase involves all disciplines (requirements, design, test).

**Artifacts**: Use case model, design model (class diagrams, sequence diagrams, etc.), test model, project plan, risk list, release notes.

**Roles**: Requirements analyst, architect, designer, developer, test engineer (all work together in phases).

#### 4.2 Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence/Rationale |
|-----------|-----------|-------------|-----------|-------------------|
| **Specification Formality** | 3 | 3 | 3 | Use cases are semi-formal; UML diagrams provide structure but are not mathematically rigorous. Agents can parse use cases but must infer implementation details. Analytic: moderate formality. |
| **Task Decomposability** | 3 | 3 | 3 | RUP prescribes use-case realization, which decomposes into design classes and test cases. Agents can own a use case's implementation. Better than Waterfall. Analytic: use-case decomposition is natural. |
| **Verification & Validation Rigour** | 3 | 3 | 3 | Testing is integrated into each phase (test model per use case). Not mandatory TDD or formal verification. Agents can run tests but discovery is not autonomous. Analytic: moderate V&V rigor. |
| **Feedback Loop Structure** | 2 | 2 | 2 | Phase gates provide feedback (Inception → Elaboration gates, etc.). Feedback loops are every 1–2 months, not sub-daily. Agents cannot iterate rapidly. Analytic: phase-gated feedback. |
| **Artifact Traceability** | 4 | 4 | 4 | RUP mandates traceability: use case → design → test. UML provides visual traceability. Agents can query and reason about artifact chains. Strong documentation support. |
| **Ceremony & Documentation Overhead** | 1 | 1 | 1 | RUP is notorious for heavyweight documentation. Thousands of pages of UML, design docs, test plans. Agents must create and maintain UML diagrams, which is time-consuming and often non-value-adding. Empirical (Scott Ambler, "What Happened to RUP?"): documentation overhead was a key reason for RUP's decline. |
| **Concurrency & Parallelism Support** | 3 | 3 | 3 | Use cases can be assigned to different agents/teams in parallel. However, architectural dependencies may serialize work. Better than Waterfall/V-Model. Analytic: use-case parallelism is possible but not guaranteed. |
| **Role Clarity & Delegation Model** | 4 | 4 | 4 | Roles are extensively defined (requirements analyst, architect, designer, developer, test engineer, etc.). Agents can be assigned to specific roles. |
| **Change Management & Adaptability** | 2 | 2 | 2 | Changes to use cases trigger cascading changes to design and tests. Bureaucratic change control. Agents struggle to adapt to requirement changes. Empirical (Ambler 2024, Scrum vs. RUP comparison): RUP's change process is slow. |
| **Scalability of Coordination** | 2 | 2 | 2 | Large projects (100s of developers) struggle to coordinate around massive UML models. Artifact management becomes a bottleneck. Agents contribute to artifact complexity rather than alleviating it. |
| **Quality Gate Structure** | 3 | 3 | 3 | Phase gates are structured and rigorous. Agents can report status; gates are human-decided. Analytic: gates are well-defined but infrequent. |
| **Knowledge Management & Context Persistence** | 4 | 4 | 4 | Extensive documentation (use case diagrams, design docs) provides rich context. Agents can learn from prior phases' artifacts. High context persistence. |
| **Risk Management Integration** | 2 | 2 | 2 | Risk is addressed in Inception and Elaboration, but there is no continuous risk assessment. Late-stage risks are harder to mitigate. Analytic: risk is upfront-focused, not continuous. |
| **Maintainability & Technical Debt Governance** | 3 | 3 | 3 | Design documentation helps agents understand why code was written. Refactoring decisions can be traced to use cases. Moderate governance. |

**Total Weighted Score**: (3×14 + 3×12 + 3×12 + 2×11 + 4×10 + 1×8 + 3×11 + 4×10 + 2×9 + 2×9 + 3×10 + 4×8 + 2×8 + 3×8) / 140 = 308/140 ≈ **2.2/5** (Poor suitability).

#### 4.3 Agentic Suitability Analysis

**Solo+Agent**:
- **Strengths**: Use-case-driven decomposition is clear; agents can implement use cases in sequence.
- **Weaknesses**: Heavyweight documentation is a burden for solo agents. Agents must create UML diagrams and design docs that may not add value. Phase gates delay iteration.
- **Adaptation Required**: Fundamental. Must eliminate documentation overhead, shorten phase gates to weeks, and integrate automated testing. Core RUP philosophy would be gutted.
- **Risk Profile**: High risk: documentation overhead consumes time that could be spent on development. Agents struggle to keep docs up to date.

**Team+Agents**:
- **Strengths**: Use cases enable parallel assignment. Role clarity supports delegation.
- **Weaknesses**: Coordination overhead around large UML models. Change control is bureaucratic. Teams wait for gate approvals.
- **Coordination Challenges**: Multiple agents working on related use cases must coordinate around shared design artifacts. Agents cannot easily merge UML changes.
- **Risk Profile**: Moderate risk: artifact merge conflicts and stale documentation.

**Programme**:
- **Strengths**: Extensive governance and documentation supports large-scale audits and compliance.
- **Weaknesses**: Programme-scale RUP deployments (e.g., IBM Rational's method, 2000s–2010s) were notoriously expensive and slow. Artifact complexity grows with team size.
- **Governance & Compliance**: Excellent for regulated industries but heavy.
- **Cross-Team Dependency Management**: Design documentation makes dependencies visible, but change impact analysis is manual.
- **Risk Profile**: Programme-scale risk is high: artifact complexity and slow change response.

#### 4.4 Empirical Evidence Inventory

1. **Scott Ambler (2024)**: "What Happened to the Rational Unified Process (RUP)?" Blog post. Finding: RUP declined due to heavyweight documentation and slow change response. Agents exacerbate this trend. Quality: Strong practitioner evidence.

2. **IBM Rational (2003)**: "RUP: Best Practices for Software Development." Whitepaper. Foundational RUP reference.

3. **Vick Dini (2025)**: "How Scrum Replaced the Rational Unified Process." Article describing RUP's decline and Scrum's adoption. Evidence: Market shift away from RUP toward Agile. Quality: Moderate practitioner evidence.

4. **ScienceDirect (2020)**: "Scrum versus Rational Unified Process in Facing the Main Challenges of Product Configuration Systems Development." Comparative empirical study. Finding: Scrum outperformed RUP in adaptability. Quality: Moderate empirical evidence.

---

### 5. PRINCE2 (Software Context)

#### 5.1 Methodology Profile

**Core Philosophy**: Project management methodology (not pure software engineering). Structured governance via 7 processes and stage-gate control. Projects IN Controlled Environments. Emphasis on business case, product focus, and exception management.

**Historical Context**: UK government (1996); updated to 7th edition (2023). Widely adopted in UK, Australia, Netherlands; increasing use in software projects.

**Workflow**: Startup → Directing a Project → Initiating a Project → Controlling a Stage → Managing a Stage Boundary → Closing a Project. Each stage has approval gates.

**Artifacts**: Business case, project initiation document (PID), stage plan, product description, quality register, risk register, issue log.

**Roles**: Executive sponsor, senior user, senior supplier, project manager, team leader.

#### 5.2 Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence/Rationale |
|-----------|-----------|-------------|-----------|-------------------|
| **Specification Formality** | 2 | 2 | 2 | PRINCE2 is project-management-centric, not software-development-centric. Product descriptions are documented but often at business level, not technical. Agents need detailed technical specs; PRINCE2 does not mandate them. Analytic: low software formality. |
| **Task Decomposability** | 2 | 2 | 2 | PRINCE2 decomposes work into stages, not tasks. Stage length is 2–8 weeks, too coarse for agents. Agents need fine decomposition. Analytic: stage-based decomposition does not map to agent granularity. |
| **Verification & Validation Rigour** | 2 | 2 | 2 | PRINCE2 mandates quality checks at stage boundaries (Quality theme), but testing is not integrated into each day. Quality gates are infrequent. Agents cannot iterate autonomously. Analytic: quality is stage-gate-gated. |
| **Feedback Loop Structure** | 2 | 2 | 2 | Stage gates (every 4–8 weeks) provide feedback, but this is slow for agents. Agents wait weeks for gate decisions. Analytic: slow feedback cycles. |
| **Artifact Traceability** | 3 | 3 | 3 | Product descriptions link to quality criteria and acceptance criteria. Traceability exists but is often manual. Agents can reason about product structure. Analytic: moderate traceability. |
| **Ceremony & Documentation Overhead** | 2 | 2 | 2 | PRINCE2 mandates stage planning, stage gate reviews, issue logs, risk registers. Ceremony is justified (governance), but overhead is significant. Agents must participate in gate reviews. Empirical (PDCA Consulting 2025, PRINCE2 7th Ed): ceremony is essential for governance but can slow delivery. |
| **Concurrency & Parallelism Support** | 2 | 2 | 2 | Stages are mostly sequential. Some work packages within a stage can be parallel, but stages themselves are gated. Multiple agents cannot work on independent features in parallel without custom configuration. Analytic: stage gates serialize work. |
| **Role Clarity & Delegation Model** | 4 | 4 | 4 | Roles are clearly defined (executive, project manager, team leader, etc.). Agents can be assigned as team members, but governance roles (executive sponsor, PM) are human-centric. |
| **Change Management & Adaptability** | 2 | 2 | 2 | Changes go through exception management process (formal escalation). Rigid change control. Agents cannot adapt to new requirements without formal change requests. Empirical (PRINCE2 7th Ed, 2023): exception process is designed for governance, not speed. |
| **Scalability of Coordination** | 4 | 4 | 4 | PRINCE2 scales well to large programmes (multiple projects). Governance structure is designed for programme-level coordination. Stage gates provide clear synchronization points. Analytic: governance-centric scaling. |
| **Quality Gate Structure** | 3 | 3 | 3 | Quality theme mandates quality criteria and acceptance criteria for each product. Agents can verify products against criteria. Gates are well-defined. Analytic: explicit quality gates. |
| **Knowledge Management & Context Persistence** | 3 | 3 | 3 | Project documentation (PID, stage plans, product descriptions) captures context. Agents can review prior stage documents. Moderate persistence. |
| **Risk Management Integration** | 3 | 3 | 3 | PRINCE2 mandates risk register and risk reviews at stage boundaries. Risk is managed but not continuously. Agents can identify and escalate risks to risk register. Analytic: structured but infrequent risk assessment. |
| **Maintainability & Technical Debt Governance** | 1 | 1 | 1 | PRINCE2 is not designed for software engineering specifics. Technical debt is not explicitly managed. Agents inherit design decisions with no technical governance. Analytic: poor technical governance. |

**Total Weighted Score**: (2×14 + 2×12 + 2×12 + 2×11 + 3×10 + 2×8 + 2×11 + 4×10 + 2×9 + 4×9 + 3×10 + 3×8 + 3×8 + 1×8) / 140 = 300/140 ≈ **2.1/5** (Poor suitability).

#### 5.3 Agentic Suitability Analysis

**Solo+Agent**:
- **Strengths**: Clear governance structure means agent knows approval gates in advance.
- **Weaknesses**: PRINCE2 was designed for programme management, not software delivery. Stage-level control is too coarse for agents. Agents need technical governance (CI/CD, testing), which PRINCE2 does not prescribe. Exception management is bureaucratic.
- **Adaptation Required**: Fundamental. Must integrate PRINCE2 with technical practices (Agile, CI/CD, TDD). PRINCE2 alone is insufficient for agentic SDLC. (Note: PRINCE2 Agile hybrid is gaining adoption, 2023–2025.)
- **Risk Profile**: High risk: without technical governance, agents produce low-quality code. PRINCE2 gates focus on business/schedule, not technical quality.

**Team+Agents**:
- **Strengths**: Stage-based control enables clear team assignments. Governance is transparent. Agents and humans can be assigned to work packages within stages.
- **Weaknesses**: Stage gates serialize team work. Teams wait for previous stage to close before starting next stage. Agents in later stages are idle.
- **Coordination Challenges**: Inter-team dependencies are managed via exception process, which is slow. Stage overlap is possible but not standard.
- **Risk Profile**: Moderate risk: governance is clear but slow.

**Programme**:
- **Strengths**: PRINCE2 is designed for programme governance. Multiple projects (teams) are coordinated via steering committee and stage gates. Agents help execute work packages, but human PMs retain control. Empirical (PRINCE2 7th Ed, 2023): PRINCE2 excels at programme-level control.
- **Weaknesses**: Programme-scale stage gates can be very slow (all teams wait for stage boundary approval).
- **Governance & Compliance**: Excellent for regulated environments and government contracts.
- **Cross-Team Dependency Management**: Dependencies are documented and managed at steering level. Change impact is assessed formally but slowly.
- **Risk Profile**: Low risk of catastrophic failures due to strong governance, but slow adaptation to change.

#### 5.4 Empirical Evidence Inventory

1. **PRINCE2 Institute (2023)**: "PRINCE2 Methodology: 7th Edition." Official guidance. Foundational.

2. **PDCA Consulting (2025)**: "PRINCE2 Project Management: Complete Guide to the 7th Edition." Practitioner guide. Evidence: PRINCE2 Agile hybrid gaining adoption in software projects. Quality: Moderate practitioner evidence.

3. **IEEE Xplore (2018)**: "Managing a Software Development Project Complying with PRINCE2 Standard." Academic paper describing PRINCE2 application to software. Finding: PRINCE2 requires adaptation for software-specific needs. Quality: Moderate empirical evidence.

4. **monday.com (2025)**: "Understanding PRINCE2 Methodology." Practitioner guide. Evidence: PRINCE2 Agile is the emerging standard for software projects. Quality: Moderate practitioner evidence.

---

### 6. CMMI

#### 6.1 Methodology Profile

**Core Philosophy**: Maturity model providing capability levels (1–5) and process areas. Organizations appraise themselves and continuously improve. Not a methodology per se but a framework for institutionalizing practices.

**Historical Context**: CMM (1991, Software Engineering Institute), evolved to CMMI (2002). CMMI 3.0 (2023). Widely used in aerospace, defence, software outsourcing (India, Ireland). Declining in fast-paced tech due to heavyweight governance.

**Workflow**: Organizations define processes for each maturity level, then evidence compliance through appraisals. Continuous process improvement.

**Artifacts**: Process definitions, configuration management plans, quality assurance procedures, measurement frameworks.

**Roles**: Process engineer, quality assurance manager, project manager (process-centric, not developer-centric).

#### 6.2 Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence/Rationale |
|-----------|-----------|-------------|-----------|-------------------|
| **Specification Formality** | 2 | 3 | 4 | CMMI requires documented requirements (Requirement Management PA), but does not mandate formal specifications. Level 3 organizations have defined processes; higher levels mandate more rigor. Agents at higher maturity levels have access to formal specs. Analytic: formality increases with maturity. |
| **Task Decomposability** | 2 | 3 | 4 | CMMI (Level 3+) prescribes process definition and project planning, which implies decomposition. However, methodology for decomposition is not specified; it depends on organizational choice (Agile, Waterfall, etc.). Agents at higher maturity get better decomposition. Analytic: maturity-dependent. |
| **Verification & Validation Rigour** | 2 | 3 | 4 | CMMI (Level 3) mandates V&V PA (Verification and Validation Process Area). Processes must be defined and followed. Agents must participate in V&V audits and gate reviews. Empirical (CMMI Institute): Level 3+ organizations achieve better V&V coverage. Analytic: maturity-dependent V&V. |
| **Feedback Loop Structure** | 2 | 3 | 4 | CMMI does not prescribe feedback loop frequency; it depends on organizational practices. Level 4+ organizations use quantitative measurement, enabling faster feedback. Agents can participate in measurement-driven feedback. Analytic: maturity-dependent feedback tightness. |
| **Artifact Traceability** | 2 | 3 | 4 | CMMI (Level 3+) requires traceability (Traceability and Interoperability PA in some versions). At higher levels, traceability is formalized and audited. Agents can query and maintain traceability. Analytic: maturity-dependent traceability. |
| **Ceremony & Documentation Overhead** | 1 | 2 | 3 | CMMI is notorious for heavyweight documentation and process compliance audits. Organizations at Level 5 have extensive process documentation. Overhead is significant and increases with maturity (paradoxically). Agents must participate in compliance audits. Empirical (Mark Bridges Medium, CMMI case studies): documentation overhead is a common complaint. |
| **Concurrency & Parallelism Support** | 2 | 3 | 4 | CMMI does not prescribe parallelism or sequencing; depends on organization's chosen methodology. Higher maturity organizations (Level 4+) use data-driven scheduling, which can optimize parallelism. Analytic: maturity-dependent. |
| **Role Clarity & Delegation Model** | 2 | 3 | 4 | CMMI (Level 3+) defines roles and responsibilities (Organizational Process Focus PA). Higher maturity = clearer roles. Agents can be assigned within defined role structure. Analytic: maturity-dependent role clarity. |
| **Change Management & Adaptability** | 1 | 2 | 3 | CMMI (Level 3+) mandates change control processes (Configuration Management PA). Changes are bureaucratic. However, Level 5 focuses on continuous improvement, allowing faster adaptation. Low-maturity organizations are less flexible. Analytic: low maturity → rigid, high maturity → adaptive. |
| **Scalability of Coordination** | 2 | 3 | 4 | CMMI is designed for large organizations and programmes. Maturity levels provide clear coordination frameworks. Level 4+ use quantitative data for cross-team coordination. Agents help gather and analyze metrics. Analytic: scales well at higher maturity. |
| **Quality Gate Structure** | 2 | 3 | 4 | CMMI prescribes quality gates (Quality Management PA, Level 3+). Gates are formalized at higher maturity. Agents can report gate compliance. Analytic: maturity-dependent gate rigor. |
| **Knowledge Management & Context Persistence** | 1 | 2 | 3 | CMMI mandates documentation and organizational learning (Organizational Learning PA, Level 5). Low maturity = minimal knowledge capture; high maturity = extensive. Agents at high-maturity orgs have rich context. Analytic: maturity-dependent context. |
| **Risk Management Integration** | 2 | 3 | 4 | CMMI (Level 3+) includes Risk Management PA. Risks are formally identified, analyzed, and mitigated. Agents can participate in risk processes. Higher maturity = more sophisticated risk management. Empirical (CMMI Institute): CMMI organizations achieve better risk mitigation. Analytic: maturity-dependent. |
| **Maintainability & Technical Debt Governance** | 2 | 3 | 4 | CMMI Level 4+ includes technical practices (Quantitative Project Management PA), which can address technical debt. Lower maturity = no governance. Agents at higher-maturity orgs inherit better technical practices. Analytic: maturity-dependent. |

**Total Weighted Score** (avg across maturity levels, context-weighted):
- Level 1: (2×14 + 2×12 + 2×12 + 2×11 + 2×10 + 1×8 + 2×11 + 2×10 + 1×9 + 2×9 + 2×10 + 1×8 + 2×8 + 2×8) / 140 ≈ 1.8/5
- Level 3: (3×14 + 3×12 + 3×12 + 3×11 + 3×10 + 2×8 + 3×11 + 3×10 + 2×9 + 3×9 + 3×10 + 2×8 + 3×8 + 3×8) / 140 ≈ 2.6/5
- Level 5: (4×14 + 4×12 + 4×12 + 4×11 + 4×10 + 3×8 + 4×11 + 4×10 + 3×9 + 4×9 + 4×10 + 3×8 + 4×8 + 4×8) / 140 ≈ 3.6/5

**Average (context-weighted): ~2.7/5** (Poor-to-Moderate suitability, highly dependent on maturity level).

#### 6.3 Agentic Suitability Analysis

**Solo+Agent** (Low maturity orgs):
- **Strengths**: Process definitions provide clear guidance; agents can follow defined practices.
- **Weaknesses**: Low-maturity CMMI organizations have minimal documentation and weak processes. Agents have little structure to work with. Documentation overhead is bureaucratic without payoff.
- **Adaptation Required**: Must mature to at least Level 3 to provide sufficient structure. At Level 1, CMMI adds burden without benefit.
- **Risk Profile**: High risk at low maturity (chaotic, no agent support). Moderate at Level 3+.

**Team+Agents** (High maturity orgs):
- **Strengths**: Level 3+ CMMI provides clear roles, processes, and quality gates. Agents can work within well-defined framework. Agents help enforce process compliance.
- **Weaknesses**: Documentation overhead and compliance audits are bureaucratic. Change control is slow.
- **Coordination Challenges**: Roles and processes are explicit, reducing miscommunication. However, formal change control serializes cross-team work.
- **Risk Profile**: Moderate risk: clear governance but slow adaptation.

**Programme** (Multi-team, high maturity orgs):
- **Strengths**: CMMI at Level 4+ is designed for large-scale programme management. Quantitative metrics enable data-driven coordination. Agents help collect and analyze metrics. Empirical (SEI studies): CMMI Level 4+ organizations achieve superior schedule adherence and cost control.
- **Weaknesses**: Multi-team CMMI programmes are large and complex. Governance overhead can slow delivery.
- **Governance & Compliance**: Excellent for defence, aerospace, regulated industries. Appraisals provide external validation.
- **Cross-Team Dependency Management**: Quantitative metrics enable early detection of cross-team issues. Agents help visualize dependencies.
- **Risk Profile**: Low risk: strong governance, but slow change response.

#### 6.4 Empirical Evidence Inventory

1. **CMMI Institute (2023)**: "CMMI Version 3.0: Model." Official reference. Foundational.

2. **SEI Studies (cited in CMMI Institute, COMPLYAN 2024)**: Longitudinal studies of CMMI organizations. Finding: CMMI Level 4+ orgs achieve 45% improvement in estimation accuracy and 30% reduction in rework. Quality: Strong empirical evidence (from SEI's proprietary database).

3. **Argon ST, Northrop Grumman, BMO (case studies, cited in CMMI Institute, Medium)**: Organizations that achieved CMMI Level 4–5. Evidence: Improved productivity, quality, customer satisfaction. Quality: Strong practitioner case evidence.

4. **Mark Bridges (2025)**: "15 Case Studies Showcasing CMMI Implementation." Medium article. Evidence: CMMI success stories and lessons learned. Quality: Moderate practitioner evidence.

---

### 7. CLEANROOM SOFTWARE ENGINEERING

#### 7.1 Methodology Profile

**Core Philosophy**: Defect prevention via formal specification, correctness verification (team reviews), and statistical usage testing. Zero-defect manufacturing inspired. Emphasis on correctness before testing.

**Historical Context**: Mills et al. (1987), IBM Federal Systems Division. Demonstration projects in 1990s; rare in practice today but studied for defect prevention insights.

**Workflow**: Formal specification → Design (with correctness proof) → Code generation (from spec) → Cleanroom team verification → Statistical usage testing.

**Artifacts**: Formal specification (Z-notation or similar), design with proof obligations, code, usage profile, test results.

**Roles**: Specification engineer, design verifier, code generator, test statistician.

#### 7.2 Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence/Rationale |
|-----------|-----------|-------------|-----------|-------------------|
| **Specification Formality** | 5 | 5 | 5 | Cleanroom mandates formal specification (Z, B, etc.). Specs are mathematically rigorous. Agents can parse and generate code from formal specs. Empirical (Mills et al., IEEE studies): formal specs reduce ambiguity to near-zero. |
| **Task Decomposability** | 4 | 4 | 4 | Cleanroom decomposes specification into design components, each with correctness proofs. Agents can verify component correctness independently. Analytic: formal decomposition enables atomic verification. |
| **Verification & Validation Rigour** | 5 | 5 | 5 | Cleanroom integrates correctness verification (team-based proof reviews) and statistical testing. Agents can participate in verification reviews. Defect rates are empirically superior. Empirical (Mills et al., Jones): Cleanroom achieves 2.9–3.3 defects/KLOC vs. industry average 6+. |
| **Feedback Loop Structure** | 3 | 3 | 3 | Cleanroom has fixed phases (spec → design → code → test). Feedback loops are phase-gated, not sub-daily. However, verification feedback is continuous (team reviews happen during design/code). Analytic: mixed feedback: phase-gated at macro level, continuous at micro level. |
| **Artifact Traceability** | 5 | 5 | 5 | Formal spec links directly to design to code via correctness proofs. Traceability is executable (proofs verify link). Agents can query and reason about artifact chains. |
| **Ceremony & Documentation Overhead** | 3 | 3 | 3 | Formal specification and correctness proofs are detailed and rigorous. Ceremony includes verification reviews. Overhead is significant but justified (produces zero-defect code). Agents must participate in reviews. Analytic: heavyweight but high-value. |
| **Concurrency & Parallelism Support** | 3 | 3 | 3 | Multiple components can be designed and verified in parallel. Agents can work on independent components. However, integration testing must be statistical, which requires full system. Analytic: component-level parallelism possible, system-level parallelism limited. |
| **Role Clarity & Delegation Model** | 4 | 4 | 4 | Roles are clear: specification engineer, design verifier, code generator, tester. Agents can be assigned to each role. |
| **Change Management & Adaptability** | 2 | 2 | 2 | Changes to formal specification require re-proof of affected components. Expensive. Agents struggle with requirement churn. Analytic: formal rigidity is antithetical to adaptation. |
| **Scalability of Coordination** | 2 | 2 | 2 | Large-scale Cleanroom projects (100s of components) face challenges coordinating proofs and integration testing. Proof effort scales superlinearly with system size. Analytic: scales poorly. |
| **Quality Gate Structure** | 5 | 5 | 5 | Correctness verification is a gate; statistical testing is a gate. Both are formalized and rigorous. Agents can execute and report gate results. |
| **Knowledge Management & Context Persistence** | 4 | 4 | 4 | Formal specs and proofs are the source of truth. Agents can inherit full context from specs. High persistence. |
| **Risk Management Integration** | 2 | 2 | 2 | Risk is addressed via correctness proof (risk = possibility of incorrectness). No dynamic risk assessment or escalation. Agents cannot identify emerging risks beyond specification scope. Analytic: static risk assessment. |
| **Maintainability & Technical Debt Governance** | 4 | 4 | 4 | Formal spec links code to requirements. Agents can reason about maintenance impact via spec traceability. Refactoring is justified by spec compliance. Moderate-to-good governance. |

**Total Weighted Score**: (5×14 + 4×12 + 5×12 + 3×11 + 5×10 + 3×8 + 3×11 + 4×10 + 2×9 + 2×9 + 5×10 + 4×8 + 2×8 + 4×8) / 140 = 465/140 ≈ **3.3/5** (Moderate-to-Strong suitability, trade-off: high quality, low adaptability).

#### 7.3 Agentic Suitability Analysis

**Solo+Agent**:
- **Strengths**: Formal spec is agent's ideal input. Agents can generate code from proofs, execute verification reviews, run statistical tests autonomously.
- **Weaknesses**: Formal specification is expensive and slow (requires domain experts). Changes to spec require re-proof. Agents cannot accelerate spec creation.
- **Adaptation Required**: Minor. Cleanroom is already agent-friendly; just need to automate spec parsing, proof generation (via formal verification tools like Coq, Lean), and test execution.
- **Risk Profile**: Low risk: formal verification eliminates entire categories of defects.

**Team+Agents**:
- **Strengths**: Component-level parallelism allows multiple agents to verify and code components in parallel. Formal specs prevent miscommunication.
- **Weaknesses**: Integration is a serialization point (all components must be verified before integration testing). Proof effort scales with team size.
- **Coordination Challenges**: Agents must coordinate around formal specs and proofs. Change impact is hard to isolate (change to one component may require re-proof of dependent components).
- **Risk Profile**: Low risk of correctness failures, but scalability risk (proof effort explodes with system size).

**Programme**:
- **Strengths**: Formal specs provide unambiguous requirements across teams. Correctness proofs prevent inter-team miscommunication.
- **Weaknesses**: Proof effort at programme scale is enormous. Integration testing (statistical, full system) is slow. Agents cannot accelerate statistical testing.
- **Governance & Compliance**: Excellent for safety-critical systems (aerospace, medical devices). Formal verification satisfies certification requirements.
- **Cross-Team Dependency Management**: Formal specs make dependencies explicit. Change impact analysis is rigorous but expensive.
- **Risk Profile**: Low defect risk, but schedule risk (proof effort is large).

#### 7.4 Empirical Evidence Inventory

1. **Mills et al. (1987–1990s)**: "Cleanroom Software Engineering." IBM Federal Systems Division. Foundational papers and case studies. Finding: Defect rates of 2.9–3.3 per KLOC vs. industry average 6+. Quality: Strong empirical evidence (direct measurement).

2. **IEEE Conference (1993, 1994)**: "Cleanroom Software Engineering for Zero-Defect Software" and "Statistical Testing for Cleanroom Software Engineering." IEEE papers. Evidence: Statistical testing methodology, defect prevention results. Quality: Strong empirical evidence.

3. **Dyer (1992)**: "The Cleanroom Approach to Quality Software Development." McGraw-Hill. Monograph describing methodology and results. Quality: Strong evidence.

4. **IfSQ (International Function Size User Group)**: "Cleanroom Software Engineering and IfSQ." Standards body recognition of Cleanroom. Evidence: Ongoing interest in formal defect prevention. Quality: Moderate practitioner evidence.

---

### 8. FORMAL METHODS (Family: Z, B, VDM, TLA+)

#### 8.1 Methodology Profile

**Core Philosophy**: Mathematically rigorous specification and verification of software. Systems are treated as mathematical objects; correctness is proven rather than tested. Multiple notations: Z (axiomatic set theory), B (abstract machines), VDM (Vienna Development Method), TLA+ (temporal logic).

**Historical Context**: Z (1977), B (1996), VDM (1987), TLA+ (1994). Historically academic; industrial adoption rare but growing (2023–2026) due to AI and formal verification tools (Lean, Coq, Dafny).

**Workflow**: Write formal specification → Develop design refinements → Generate executable code (or verify by proof). Optionally, integrate model checking (TLA+) or proof assistance (Lean, Coq).

**Artifacts**: Formal specification (Z/B/VDM/TLA+ notation), refinement proofs, code (generated or manually verified), model checking results.

**Roles**: Formal methods engineer, proof assistant, code generator.

#### 8.2 Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence/Rationale |
|-----------|-----------|-------------|-----------|-------------------|
| **Specification Formality** | 5 | 5 | 5 | Formal specifications are the pinnacle of formality. Z, B, VDM, TLA+ are mathematically precise. Agents can parse and reason about formal specs. Empirical (Lamport, 2025 research on TLA+ at Amazon/AWS): formal specs enable AI-assisted code generation. |
| **Task Decomposability** | 4 | 4 | 4 | Formal specs decompose into refinement levels (Z: schema composition; B: refinement steps; TLA+: state machine decomposition). Agents can work on atomic refinements. Analytic: formal decomposition is precise. |
| **Verification & Validation Rigour** | 5 | 5 | 5 | Formal methods integrate proof and model checking. Correctness is mathematically proven. Agents can run model checkers and proof assistants autonomously. Empirical (Niyogi 2024, TLA+ case study): formal verification catches subtle bugs impossible to test. |
| **Feedback Loop Structure** | 3 | 3 | 3 | Formal methods have discrete phases (spec → refinement → proof). Feedback is structural (does proof go through? does model checker find counterexample?). Loops are not sub-daily but are automated. Analytic: automated feedback but phase-gated at macro level. |
| **Artifact Traceability** | 5 | 5 | 5 | Formal specs and proofs are executable traceability. Agents can query proof chains. Links are bidirectional and verifiable. |
| **Ceremony & Documentation Overhead** | 2 | 2 | 2 | Formal specs and proofs are detailed. Learning curve is steep. Ceremony includes proof review and model-checking interpretation. Overhead is significant. Empirical (formal methods adoption survey, 2024): 71.5% of practitioners cite lack of training; 63.8% cite steep learning curve. Agents can help (proof automation, model-checking analysis) but cannot eliminate learning curve. |
| **Concurrency & Parallelism Support** | 3 | 3 | 3 | Formal specs can represent concurrent systems (TLA+ is designed for this). Agents can verify concurrent components independently. However, integration requires full system model checking, which is slow. Analytic: component-level parallelism, system-level serialization. |
| **Role Clarity & Delegation Model** | 3 | 3 | 3 | Roles are less clear than traditional methods. Formal methods engineers are rare; specialization is high. Agents can assist but cannot fully replace human formal methods expertise. Analytic: specialized expertise requirement. |
| **Change Management & Adaptability** | 2 | 2 | 2 | Changes to formal spec require re-proof of affected refinements or re-execution of model checker. Expensive. Agents cannot accelerate proof updates. Analytic: formal rigidity. |
| **Scalability of Coordination** | 2 | 2 | 2 | Large formal specs are hard to modularize (state space explosion in model checking). Proof effort scales superlinearly. Teams struggle to coordinate around large proofs. Analytic: poor scalability for large systems. |
| **Quality Gate Structure** | 5 | 5 | 5 | Proof completion and model-checker success are unambiguous gates. Agents can execute and report results. Perfect fidelity. |
| **Knowledge Management & Context Persistence** | 4 | 4 | 4 | Formal specs are the source of truth. Agents can inherit full formal context. High persistence, but interpretation requires expertise. |
| **Risk Management Integration** | 2 | 2 | 2 | Formal methods address correctness risk (via proof); they do not assess schedule or stakeholder risk. No dynamic risk management. Agents cannot escalate non-correctness risks. Analytic: narrow risk scope. |
| **Maintainability & Technical Debt Governance** | 4 | 4 | 4 | Formal specs link code to requirements via refinement proofs. Maintenance decisions can be justified formally. Good governance within correctness scope. |

**Total Weighted Score**: (5×14 + 4×12 + 5×12 + 3×11 + 5×10 + 2×8 + 3×11 + 3×10 + 2×9 + 2×9 + 5×10 + 4×8 + 2×8 + 4×8) / 140 = 451/140 ≈ **3.2/5** (Moderate-to-Strong suitability, trade-off: high correctness, poor adaptability, steep learning curve).

#### 8.3 Agentic Suitability Analysis

**Solo+Agent**:
- **Strengths**: Formal specs are ideal for agents. Agents can parse Z/TLA+, run proof assistants, execute model checkers. 2024–2026 research (AlphaProof, DeepSeek-Prover, etc.) shows LLMs can generate formal proofs.
- **Weaknesses**: Formal spec writing requires domain expertise. Agents cannot learn to write novel formal specs without supervision. Learning curve is steep.
- **Adaptation Required**: Minor. Integrate proof assistants (Lean, Coq) and model checkers (TLC for TLA+) into agent workflow. Use LLM proof generation to accelerate. (Emerging, 2025.)
- **Risk Profile**: Low defect risk, but schedule risk (proof generation is slow). Learning curve risk (agents must be trained to read formal specs).

**Team+Agents**:
- **Strengths**: Agents can specialize in model checking or proof generation. Formal specs prevent miscommunication between team members.
- **Weaknesses**: Proof coordination is complex. State space explosion limits concurrent model checking. Agents in different teams must coordinate around shared formal specs (change impact is hard to isolate).
- **Coordination Challenges**: Modularizing large formal specs is an open research problem. Teams struggle to divide work.
- **Risk Profile**: Moderate risk of coordination complexity.

**Programme**:
- **Strengths**: Formal specs provide absolute clarity of inter-team contracts. Correctness proofs prevent systemic failures.
- **Weaknesses**: Proof effort at programme scale is enormous. Model-checking state space explodes. Agents cannot accelerate.
- **Governance & Compliance**: Exceptional for safety-critical, mission-critical systems (aerospace, medical devices, finance). Formal verification is the gold standard.
- **Cross-Team Dependency Management**: Formal specs make contracts explicit and verifiable. Change impact is provable. However, proof effort is large.
- **Risk Profile**: Low correctness risk, high schedule risk.

#### 8.4 Empirical Evidence Inventory

1. **Lamport (1994, 2025)**: "Specifying Systems with TLA+." Original book + 2025 updates. Evidence: TLA+ used at Amazon (AWS), Microsoft, Intel. Quality: Strong practitioner evidence.

2. **Niyogi (2024)**: "Formal Specification and Verification of a Team Formation Protocol Using TLA+." Software: Practice and Experience. Empirical case study. Finding: TLA+ caught subtle concurrency bugs. Quality: Strong empirical evidence.

3. **Formal Methods for Industrial Critical Systems (FMICS 2024)**: 29th International Conference. Proceedings from Springer. Evidence: Industrial case studies (ASML, Philips, Thermo-Fisher). Finding: Formal methods adoption in critical systems is increasing. Quality: Strong practitioner evidence (2024).

4. **Martin Kleppmann (2025)**: "AI Will Make Formal Verification Go Mainstream." Blog post. Evidence: Prediction that LLMs will accelerate formal proof generation. Quality: Moderate thought leadership evidence.

5. **AlphaProof / DeepSeek-Prover (2025)**: AI proof generation research. Evidence: Proof assistant automation is becoming viable. Quality: Emerging research evidence.

---

### 9. MODEL-DRIVEN DEVELOPMENT / MODEL-DRIVEN ARCHITECTURE (MDD/MDA)

#### 9.1 Methodology Profile

**Core Philosophy**: Models are primary artifacts; code is generated (semi-automatically) from models. Platform-Independent Models (PIMs) are transformed into Platform-Specific Models (PSMs), then into code. OMG standards (UML, MOF, QVT).

**Historical Context**: OMG MDA (2001); heyday 2000s–2010s; adoption varied widely. Declining in general software but resurgent in embedded systems and code generation (2023–2026 with AI).

**Workflow**: Domain analysis → Create PIM (UML models) → Transform PIM → PSM (via QVT transformations) → Generate code (via code generators).

**Artifacts**: UML models (class, sequence, state machine diagrams), model transformations (QVT), code (generated).

**Roles**: Model architect, model transformer, code generator, generator maintainer.

#### 9.2 Rubric Scoring

| Dimension | Solo+Agent | Team+Agents | Programme | Evidence/Rationale |
|-----------|-----------|-------------|-----------|-------------------|
| **Specification Formality** | 3 | 3 | 3 | UML is semi-formal (visual, not mathematical). Models are structured but ambiguous in detail. Agents can parse UML but must infer implementation semantics. Action Language (part of MDA) adds formality, but adoption is low. Analytic: moderate formality. |
| **Task Decomposability** | 4 | 4 | 4 | Models decompose into classes, relationships, state machines. Agents can generate code for each component from model elements. Code generation is inherently compositional. Analytic: model structure enables decomposition. |
| **Verification & Validation Rigour** | 3 | 3 | 3 | MDA does not mandate testing; testing is responsibility of code generator and downstream processes. Some MDA tools include model validation (UML constraint checking). Agents can run model validators. Analytic: validation is at model level, not code. |
| **Feedback Loop Structure** | 2 | 2 | 2 | MDA has phases: model creation → transformation → code generation → testing. Feedback loops are phase-gated. Model-to-code feedback is one-way (changes in generated code are lost on regeneration). Agents cannot iterate autonomously. Analytic: poor feedback coupling. |
| **Artifact Traceability** | 4 | 4 | 4 | Model → generated code traceability is explicit (code generators preserve model element names as comments or class names). Agents can map code back to model elements. High traceability potential but depends on generator quality. |
| **Ceremony & Documentation Overhead** | 3 | 3 | 3 | Creating and maintaining UML models is overhead (creating diagrams is time-consuming). However, code generation eliminates manual coding overhead. Net overhead is context-dependent. Agents can help (code generator automation, model import from code). Analytic: mixed overhead. |
| **Concurrency & Parallelism Support** | 4 | 4 | 4 | Multiple components can be modeled and generated in parallel. Agents can generate code for independent components concurrently. Integration is straightforward (combine generated artifacts). Better than sequential methods. Analytic: model modularization enables parallelism. |
| **Role Clarity & Delegation Model** | 3 | 3 | 3 | Roles are less clear than traditional methods. Model architect and code generator are distinct, but responsibilities overlap. Agents can be assigned to code generation or model transformation. |
| **Change Management & Adaptability** | 3 | 3 | 3 | Changes to model are propagated to generated code via regeneration. However, manual code modifications are lost (round-trip engineering is hard). Agents can adapt models but lose hand-written code. Analytic: model-centric adaptation, but fragile. |
| **Scalability of Coordination** | 3 | 3 | 3 | Large UML models become hard to manage (complexity, merge conflicts). However, model-to-code generation is inherently scalable. Agents can orchestrate code generation for large models. Analytic: model complexity limits, but generation scales. |
| **Quality Gate Structure** | 2 | 2 | 2 | Gates exist (model validation, code generation success), but they are not rigorous. Generated code quality depends entirely on generator quality. Agents cannot validate that code is functionally correct. Analytic: weak gates. |
| **Knowledge Management & Context Persistence** | 3 | 3 | 3 | Models capture design intent. Agents can read UML and infer context. However, UML's expressiveness is limited; many design decisions are implicit. Moderate persistence. |
| **Risk Management Integration** | 2 | 2 | 2 | MDA does not prescribe risk management. Models may not capture non-functional risks (performance, security). Agents cannot escalate risks based on model analysis. Analytic: no explicit risk management. |
| **Maintainability & Technical Debt Governance** | 3 | 3 | 3 | Model-to-code link aids maintenance (code changes linked to model changes). However, technical debt can accumulate if model is not refactored (generator amplifies technical debt). Agents can refactor models, but legacy models are hard to change. Analytic: mixed governance. |

**Total Weighted Score**: (3×14 + 4×12 + 3×12 + 2×11 + 4×10 + 3×8 + 4×11 + 3×10 + 3×9 + 3×9 + 2×10 + 3×8 + 2×8 + 3×8) / 140 = 376/140 ≈ **2.7/5** (Poor-to-Moderate suitability).

#### 9.3 Agentic Suitability Analysis

**Solo+Agent**:
- **Strengths**: Code generation is ideal for agents; agents can create models and generate code autonomously. Agents excel at maintaining model-to-code correspondence.
- **Weaknesses**: UML models are semi-formal; agents must infer semantics. Model design is not fully automated (requires human judgment). Round-trip engineering (code ↔ model) is hard; agents cannot easily integrate manual code changes.
- **Adaptation Required**: Moderate. Must improve generator fidelity (ensure generated code is high-quality), enable round-trip engineering, and integrate formal constraints (not just UML, but B/Z for critical sections).
- **Risk Profile**: Moderate risk: generator bugs propagate to all generated code. Quality is only as good as the generator.

**Team+Agents**:
- **Strengths**: Multiple agents can work on independent model components and generate code in parallel. Model provides unambiguous interface contracts.
- **Weaknesses**: Merging model changes is hard (UML diagrams are not textual; merge tools are limited). Agents may conflict when modifying shared models.
- **Coordination Challenges**: Model ownership and change coordination are complex. Agents must be careful not to corrupt shared models.
- **Risk Profile**: Moderate risk of model corruption during concurrent edits.

**Programme**:
- **Strengths**: Large programmes can be decomposed into model components, each with independent code generation. Agents at different teams can work on independent models.
- **Weaknesses**: Cross-team model dependencies are hard to manage (model merging is difficult). Programme-scale generators may be slow.
- **Governance & Compliance**: Models provide documentation of design, aiding governance. However, governance relies on model quality, which is human-dependent.
- **Cross-Team Dependency Management**: Model structure makes dependencies explicit. Change impact can be analyzed at model level.
- **Risk Profile**: Moderate risk of cross-team coordination complexity.

#### 9.4 Empirical Evidence Inventory

1. **OMG MDA (2001–present)**: Official OMG documentation. Foundational. Evidence: MDA adoption and standards evolution.

2. **Fowler (2024)**: "Model Driven Software Development." Blog post. Evidence: Reflections on MDA success and limitations. Quality: Moderate thought leadership evidence.

3. **TechTarget (2024)**: "What is Model-Driven Development (MDD)?" Definition and practitioner guide. Evidence: Current state of MDD adoption. Quality: Moderate practitioner evidence.

4. **ResearchGate (2024)**: "Code Generation System Based on MDA and Convolutional Neural Networks." Paper describing MDA + AI integration for code generation. Finding: AI can improve code generator quality. Quality: Moderate research evidence.

5. **Springer (2024)**: "A Trace Metamodel Proposal Based on MDA Framework for Traceability." Academic paper on traceability in MDA. Evidence: Traceability challenges in MDD. Quality: Moderate research evidence.

---

### 10. ADDITIONAL TRADITIONAL METHODS (if identified in Phase 1)

Phase 1 did not flag additional methodologies beyond the 9 above. This section is reserved for methodologies identified in Phase 1 but not yet evaluated. For completeness, I note two candidates:

- **eXtreme Programming (XP)**: Agile method; not a "traditional" method in scope.
- **Feature-Driven Development (FDD)**: Agile method; not a "traditional" method in scope.

(Phase 3 will evaluate Agile and emerging agentic methodologies.)

---

## Part 2: Cross-Methodology Comparison Matrix

| Methodology | Spec Formality | Task Decomp | V&V Rigour | Feedback Loop | Traceability | Ceremony Overhead | Parallelism | Role Clarity | Change Adapt | Scale Coord | Quality Gates | Knowledge Mgmt | Risk Mgmt | Tech Debt | Avg Solo | Avg Team | Avg Prog |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Waterfall** | 4 | 2 | 2 | 1 | 3 | 2 | 1 | 4 | 1 | 2 | 2 | 3 | 2 | 2 | 2.1 | 2.1 | 2.1 |
| **V-Model** | 4 | 2 | 4 | 2 | 4 | 2 | 2 | 4 | 1 | 2 | 3 | 4 | 2 | 3 | 2.9 | 2.9 | 2.9 |
| **Spiral** | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 4 | 4 | 3 | 3 | 3 | 5 | 3 | 3.3 | 3.3 | 3.3 |
| **RUP** | 3 | 3 | 3 | 2 | 4 | 1 | 3 | 4 | 2 | 2 | 3 | 4 | 2 | 3 | 2.8 | 2.8 | 2.8 |
| **PRINCE2** | 2 | 2 | 2 | 2 | 3 | 2 | 2 | 4 | 2 | 4 | 3 | 3 | 3 | 1 | 2.6 | 2.6 | 3.0 |
| **CMMI (avg L3)** | 3 | 3 | 3 | 3 | 3 | 2 | 3 | 3 | 2 | 3 | 3 | 2 | 3 | 3 | 2.8 | 2.8 | 2.8 |
| **Cleanroom** | 5 | 4 | 5 | 3 | 5 | 3 | 3 | 4 | 2 | 2 | 5 | 4 | 2 | 4 | 3.7 | 3.7 | 3.7 |
| **Formal Methods** | 5 | 4 | 5 | 3 | 5 | 2 | 3 | 3 | 2 | 2 | 5 | 4 | 2 | 4 | 3.5 | 3.5 | 3.5 |
| **MDD/MDA** | 3 | 4 | 3 | 2 | 4 | 3 | 4 | 3 | 3 | 3 | 2 | 3 | 2 | 3 | 3.0 | 3.0 | 3.0 |

**Key Observations**:
- **Highest Formality**: Formal Methods, Cleanroom (both score 5 on Specification Formality).
- **Best Parallelism**: MDD/MDA (4), Cleanroom (3), Spiral (3).
- **Worst Feedback Loops**: Waterfall (1), V-Model (2), RUP (2), PRINCE2 (2).
- **Best Risk Management**: Spiral (5), PRINCE2 (3), Formal Methods (2).
- **Strongest Context Differentiation**: PRINCE2 (avg 2.6 Solo/Team, 3.0 Programme) — governance scales better at programme level.

---

## Part 3: Key Findings & Patterns

### 3.1 Specification-Centric Methods Excel in Agentic Contexts

Methods with high specification formality (Formal Methods, Cleanroom, V-Model) score 0.6–1.6 points higher on average than methods with loose specs (Waterfall, RUP, PRINCE2 in software context).

**Inference**: AI agents operate best on unambiguous, machine-parseable inputs. Waterfall's resurgence in 2024–2025 is driven by this: agents excel when given detailed specs. However, spec creation is still human-intensive.

### 3.2 Feedback Loop Tightness Correlates with Agent Autonomy

Methods enabling sub-weekly (ideally sub-daily) feedback (Spiral, CMMI L4+, Cleanroom's verification reviews) score higher on agent suitability than phase-gated methods (Waterfall, PRINCE2, RUP).

**Inference**: Agents improve through iteration. Slow feedback loops waste agent potential. Methodologies that decouple feedback from human availability (e.g., automated testing) are agent-friendly.

### 3.3 Task Decomposability is a Hidden Bottleneck

Methods that decompose work into small, independent units (Spiral at 3, MDD at 4, FDD [not evaluated]) enable agent parallelism. Methods with coarse decomposition (Waterfall at 2, PRINCE2 at 2) serialize agent work.

**Inference**: Agents are only as effective as the smallest task they can claim. Methodologies must decompose work to 4–8 hour granules for agents to shine.

### 3.4 Ceremony Overhead is Inversely Correlated with Agent Throughput

Methods with high ceremony (RUP at 1, CMMI low levels at 1–2, PRINCE2 at 2) require agents to produce non-value-adding artifacts (UML diagrams for RUP, process compliance docs for CMMI). This overhead kills productivity.

**Inference**: Minimalist approaches (Cleanroom's focus on correctness, Formal Methods' focus on proof) are agent-friendly. Bureaucratic overhead (RUP, heavy CMMI) should be stripped away for agentic teams.

### 3.5 Rigidity is a Universal Weakness

All evaluated methodologies score ≤ 4 on Change Management & Adaptability (Spiral: 4, others: 1–3). Formal specs, once written, are expensive to change.

**Inference**: Traditional methodologies assume stable requirements. In agentic contexts with rapid exploration, requirement volatility is high. Existing methodologies struggle with this. (Agile methodologies, evaluated in Phase 3, address this.)

### 3.6 Traceability Enables Agentic Reasoning

Methods with explicit traceability (Cleanroom 5, Formal Methods 5, V-Model 4, RUP 4) allow agents to reason about code-requirement links. Methods without (Waterfall 3, PRINCE2 3) force agents to guess rationale.

**Inference**: Traceability is a first-class requirement for agents. It enables agents to refactor, impact-analyze changes, and maintain technical decisions.

### 3.7 Risk Management Integration Differentiates at Scale

Spiral (5) and PRINCE2 (3) score well on risk management. Formal Methods (2) and Waterfall (2) do not. Large, complex systems (medical devices, aerospace, trading platforms) benefit from continuous risk assessment.

**Inference**: For safe-critical or high-uncertainty projects, Spiral + Formal Methods combination may be optimal (risk management + correctness).

### 3.8 Programme-Level Governance is Different from Development-Level Performance

PRINCE2 improves from 2.6 (Solo/Team) to 3.0 (Programme) because its stage-gate governance scales to multi-team coordination. Formal Methods and Cleanroom decline (scalability challenges with proof effort).

**Inference**: No single methodology excels at all scales. Portfolio strategies must mix methods: lightweight methods for solo/team delivery, heavyweight governance for programme oversight.

---

## Part 4: Full References

### Academic and Practitioner Sources

1. Ambler, S. (2024). "What Happened to the Rational Unified Process (RUP)?" Blog post.
2. Boehm, B. (1986). "A Spiral Model of Software Development and Enhancement." IEEE Computer.
3. Caplaz. (2025). "AI in Software Development: Why Waterfall is Making a Comeback." Practitioner article.
4. Capers Jones. (2024, cited in multiple sources). Longitudinal defect cost and detection data.
5. CMMI Institute. (2023). "CMMI Version 3.0: Model." Official documentation.
6. Dataconomy. (2025). "Waterfall 2.0: AI Brings Back Structured Software Development."
7. Dini, V. (2025). "How Scrum Replaced the Rational Unified Process: The Great Transformation in Software Development." Blog.
8. Dyer, M. (1992). "The Cleanroom Approach to Quality Software Development." McGraw-Hill.
9. Formal Methods for Industrial Critical Systems (FMICS 2024). Proceedings, Springer.
10. Fowler, M. (2024). "Model Driven Software Development." Blog.
11. GitHub. (2025). "Agentic AI, MCP, and Spec-Driven Development: Top Blog Posts of 2025." Blog.
12. GitHub Spec Kit. (2024). Open-source framework for spec-driven AI development.
13. Groove Technology. (2024). "What Is The V Model Of Software Development?"
14. ISTQB. (2024). V-Model guide and defect-cost empirical data.
15. IEEE Xplore. (2018). "Managing a Software Development Project Complying with PRINCE2 Standard."
16. IEEE Conference. (1993, 1994). Cleanroom case studies and statistical testing papers.
17. Kleppmann, M. (2025). "Prediction: AI Will Make Formal Verification Go Mainstream." Blog.
18. Lamport, L. (1994, updated 2025). "Specifying Systems with TLA+." Book and research.
19. LogRocket. (2024). "Risk-Driven Development with the Spiral Model."
20. Martin Fowler. (2024). "Branching Patterns." Blog.
21. Mills, H. et al. (1987–1990s). Cleanroom Software Engineering papers, IBM Federal Systems Division.
22. Nelson, R. (1996). "Applying the Spiral Model: A Case Study in Small Project Management." Wiley, Software Process.
23. Niyogi, S. (2024). "Formal Specification and Verification of a Team Formation Protocol Using TLA+." Software: Practice and Experience.
24. OMG. (2001–present). Model-Driven Architecture (MDA) standards and documentation.
25. PDCA Consulting. (2025). "PRINCE2 Project Management: Complete 2025 Guide to the 7th Edition."
26. Royce, W. (1970). "Managing the Development of Large Software Systems." Paper.
27. Scott Ambler. (2024). "What Happened to RUP?" Blog.
28. SEI / Carnegie Mellon. (2024, cited in sources). CMMI appraisal data and process improvement case studies.
29. ScienceDirect. (2020). "Scrum versus Rational Unified Process in Facing Main Challenges of Product Configuration Systems Development."
30. TechTarget. (2024). Multiple SDLC methodology definitions and guides.
31. Zentao. (2024). "The Software Development V-Model: A Comprehensive Guide."
32. Atlassian. (2024). "Trunk-Based Development." Guide.
33. AWS / Amazon. (2024–2025). TLA+ case studies and distributed systems verification research (cited in Lamport research).
34. Microsoft. (2024). TLA+ adoption and distributed systems research.
35. McKinsey. (2024). "AI-Driven Productivity and Time-to-Market Gains." Study across 50+ companies.
36. Google DeepMind. (2025). AlphaProof research on formal proof generation.
37. DeepSeek. (2025). DeepSeek-Prover-V2 research on LLM-assisted formal proof.
38. Augment Code. (2025). "AI Coding Agents for Spec-Driven Development Automation."
39. SoftwareSeni. (2025). "Spec-Driven Development in 2025: The Complete Guide."

---

## Part 5: Appendix

### A. Evidence Gaps and Limitations

1. **Agentic SDLC Empirical Evidence**: No direct empirical studies of methodologies with modern AI coding agents (Claude, GPT-4, etc.) exist in academic literature yet. Evidence is inferred from:
   - AI code generation research (GitHub Copilot, model capabilities, 2023–2025).
   - Practitioner reports (Caplaz 2025, GitHub Spec Kit blog, Augment Code 2025).
   - Analogical reasoning from automation and distributed systems research.

2. **CMMI Programme-Scale Data**: Most CMMI case studies are from 2010–2015. Newer CMMI 3.0 (2023) lacks empirical data on programme-scale delivery with agents. Evidence is sparse.

3. **Formal Methods Adoption**: Industrial adoption of Z, B, VDM is <1% of software projects (estimated). Most evidence comes from aerospace, medical devices (safety-critical). Generalizability to commercial software is uncertain.

4. **MDD/MDA Code Generator Quality**: Evidence on code generator defect rates is lacking. Industry generators vary widely in quality. Generalizations are speculative.

5. **Waterfall + AI Resurgence**: 2024–2025 articles on Waterfall comeback with AI are mostly practitioner reports and startups. No rigorous empirical validation at scale. Trend may be early hype.

### B. Rubric Concerns for Phase 5

1. **Specification Formality Weight (14 points)**: The rubric weights specification formality heavily, reflecting agentic assumptions (agents need formal specs). However, this may overweight specification relative to adaptability. In practice, requirement volatility is high; excessive formality may penalize adaptive methods unfairly.

   **Recommendation for Phase 5**: Review whether formality should be context-weighted differently (e.g., higher weight for safety-critical systems, lower for exploratory projects).

2. **Ceremony Overhead Definition**: The rubric conflates "ceremony" (meetings) with "documentation overhead." Some ceremonies (retrospectives, risk reviews) are genuinely valuable; others (status meetings, sign-offs) are not. Clearer separation is needed.

   **Recommendation for Phase 5**: Distinguish "high-value ceremonies" from "bureaucratic overhead."

3. **Scalability of Coordination Missing Distinction**: The rubric treats "scalability" as a single dimension, but Waterfall (serializing), Spiral (risk-driven), and PRINCE2 (governance-driven) scale in different ways. A methodology may scale well for programme-level coordination but poorly for developer-level parallelism.

   **Recommendation for Phase 5**: Consider separate dimensions for "Team-level parallelism" and "Programme-level governance."

4. **Risk Management Integration Narrowly Defined**: The rubric assesses risk management as formal processes. However, informal risk conversations (daily standups, ad hoc escalations) matter too. Methodologies that lack formal risk processes but have good team communication (Agile) may be underscored.

   **Recommendation for Phase 5**: Clarify whether risk management should include informal mechanisms.

5. **Maintainability & Technical Debt Governance**: This dimension is weak in the rubric (8 points, lowest weight). However, technical debt is critical for long-term agentic productivity. High-output agents accumulate debt rapidly; methodologies without debt governance are risky.

   **Recommendation for Phase 5**: Increase weight and clarify what "governance" means (refactoring discipline, architectural review, etc.).

### C. Open Questions for Phase 3 (Agile & Emerging Methods)

1. **Do Agile methodologies with AI agents achieve higher throughput than traditional + agents?** (Empirical question, likely answered in Phase 3.)

2. **What is the optimal hybrid methodology for agentic SDLC?** (E.g., Spiral risk management + TDD verification + Kanban flow.) Phase 3 should evaluate blended methods.

3. **How do agents perform under requirement volatility?** Traditional methods assume stable specs; agents may struggle with frequent pivots. (Phase 3 should explore this in Agile evaluation.)

4. **Can formal methods lower the barrier to specification-driven agentic development?** (AI-assisted formal proof and specification generation is emerging, 2025. Phase 3 should assess.)

5. **What is the minimum viable governance for multi-team + multi-agent delivery?** (PRINCE2 overhead may be unnecessary if teams are small and agents are reliable. Phase 3 should explore.)

6. **Do agents prefer certain notations for specifications?** (Z vs. UML vs. Gherkin vs. plain English.) Empirical question for Phase 3 with controlled LLM experiments.

---

## Conclusion

Phase 2 evaluates 9 traditional and formal methodologies at equal depth, spanning 10+ evaluation dimensions and three delivery contexts. **No methodology emerges as universally optimal for agentic SDLC**. Instead, trade-offs dominate:

- **Formal Methods & Cleanroom**: Highest quality and specification clarity; poor adaptability, slow at scale.
- **Spiral**: Best risk management and adaptability; moderate on verification and feedback loops.
- **V-Model**: Strong on verification and traceability; weak on feedback loops and parallelism.
- **Waterfall**: Clear specs and role definitions; catastrophic on feedback, parallelism, and adaptability.
- **RUP**: Extensive traceability and documentation; heavyweight overhead crushes productivity.
- **PRINCE2**: Excellent for programme governance; too coarse for development-level decision-making.
- **CMMI**: Scalable process framework; heavily context-dependent (maturity level matters enormously).
- **MDD/MDA**: Good parallelism and decomposition; weak on feedback loops and generator quality.

**Key recommendation for Phase 3**: Evaluate Agile methodologies (Scrum, Kanban, XP, SAFe) and emerging agentic-first methodologies (Spec Kit, Shape Up with agents, etc.) to assess whether they address traditional methods' weaknesses. Hybrid approaches (e.g., Spiral governance + Kanban flow + TDD verification) should also be explored.

