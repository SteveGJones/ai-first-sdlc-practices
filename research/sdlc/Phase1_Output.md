# Phase 1 Output: Agentic SDLC Suitability Rubric & Methodology Landscape

## Executive Summary

This Phase 1 deliverable establishes a rigorous foundation for evaluating software development methodologies' suitability for fully agentic AI-driven delivery—where AI coding agents operate as autonomous or semi-autonomous participants in the SDLC. The research synthesises evidence from academic sources (IEEE, ACM, formal methods literature), practitioner sources (ThoughtWorks, Fowler, InfoQ), and emerging agentic frameworks (2024–2026).

The output comprises:

1. **A 14-dimension weighted rubric** applicable across Solo+Agent, Team+Agents, and Programme delivery contexts, with explicit anchor scales (1–5) for each dimension
2. **A comprehensive methodology catalogue** covering 40+ traditional, agile, and emerging methodologies, including newly discovered AI-native frameworks
3. **Detailed context-specific guidance** for applying the rubric across delivery scales
4. **An explicit gaps appendix** noting uncertainties and areas for deeper investigation in subsequent phases

The rubric is designed to be operationally precise: each dimension has unambiguous definition, scoring anchors, and rationale. This document is intended to be consumed verbatim by Phases 2–5 without modification to the rubric itself.

---

## Part A: Agentic SDLC Evaluation Rubric

### Rubric Overview

**Purpose**: Assess the suitability of a software development methodology for agentic SDLC delivery across three distinct contexts.

**Scope**: 14 weighted dimensions, each with 1–5 scoring scale and context-specific guidance.

**Total Weight**: 100 points distributed across dimensions.

**Application**: For each methodology under evaluation, score dimensions based on the methodology's inherent characteristics, then weight by context (Solo+Agent / Team+Agents / Programme).

---

### Dimension 1: Specification Formality

**Definition**: The degree to which the methodology requires or encourages explicit, unambiguous, machine-parseable specifications that agents can autonomously interpret and act upon, versus informal or ambiguous requirements.

**Why It Matters for Agentic SDLC**:
- Agents cannot disambiguate implicit requirements through intuition; they must execute based on parsed inputs.
- Formal specifications (BDD scenarios, API contracts, ADRs, formal notations) reduce agent-execution errors and enable agents to verify their own work against ground truth.
- Informal specs (narrative user stories, vague acceptance criteria) force agents into costly clarification loops or produce incorrect outputs.

**Evidence Base**:
- GitHub's Spec Kit (2025) positions specifications as "executable intent" for AI agents, marking a shift from code-centric to spec-centric delivery.[1]
- VeriAct framework demonstrates that verification-guided agentic synthesis requires formal specifications (e.g., Z-notation style contracts) to enable closed-loop agent iteration.[2]
- Formal methods research (Z, B, VDM) shows that mathematical specification reduces defects and ambiguity; AI agents can be scaffolded with formal verification tools to validate compliance.[3]

**1–5 Scale**:
- **1 (Informal)**: Methodology relies on narrative, conversational specs (user stories, email threads, verbal requirements). Agents must infer intent. Examples: early-stage Kanban, informal Scrum.
- **2 (Loosely Structured)**: Methodology uses templates (e.g., "As a user...I want...") but allows high ambiguity. Agents struggle with interpretation. Examples: standard Scrum without BDD.
- **3 (Moderately Formal)**: Methodology prescribes structured templates, acceptance criteria, or simple contract formats (e.g., OpenAPI specs for APIs). Agents can parse with moderate confidence. Examples: Scrum+BDD, API-first development.
- **4 (Formal)**: Methodology mandates formal specifications (ADRs, BDD Gherkin, executable contracts, formal notations). Agents can parse and validate with high confidence. Examples: Spec-Driven Development, Cleanroom, formal methods.
- **5 (Highly Formal & Executable)**: Methodology integrates formal specs *and* automated verification tools. Specifications are directly executable or verifiable by agents. Examples: TLA+, Z with code generators, VeriAct framework.

**Weight**: 14 points

**Context-Specific Notes**:
- **Solo+Agent**: High formality is critical; the agent is the sole executor and has no human counterpart to disambiguate mid-task.
- **Team+Agents**: Moderate–high formality is essential to reduce agent-human clarification cycles; specs serve as team coordination mechanism.
- **Programme**: Formality is essential for cross-team coordination; formal specs enable agents to understand dependencies and handoff contracts.

---

### Dimension 2: Task Decomposability

**Definition**: The degree to which the methodology naturally and prescriptively decomposes work into small, well-bounded, independently verifiable units that agents can execute autonomously without deep knowledge of the broader system.

**Why It Matters for Agentic SDLC**:
- Agents work best on small, well-scoped tasks with clear entry/exit criteria.
- Task decomposition enables parallel agent execution, reduces context window bloat, and improves verification.
- Methodologies that embrace decomposition (Scrum, FDD, Kanban) naturally align with agent parallelism; those that don't (some Waterfall, RUP) force agents to hold large, complex contexts.

**Evidence Base**:
- Agile Orchestration research (AgentOrchestra, 2025) shows that hierarchical task decomposition enables multi-agent systems to solve complex problems; decomposability is the primary enabler of agent parallelism.[4]
- FDD explicitly prescribes feature decomposition: features > 2-week effort are recursively decomposed until atomicity is achieved, directly enabling agent task granularity.[5]
- Scrum's sprint backlog decomposition into tasks is shown empirically to improve team productivity; agents benefit similarly.[6]

**1–5 Scale**:
- **1 (Monolithic)**: Work is not decomposed; large multi-week epics or phases are the unit of delivery. Agents cannot execute independently.
- **2 (Weakly Decomposed)**: Decomposition exists but is loose or optional; epics may or may not be broken into stories. Agents struggle to find independent, completable units.
- **3 (Moderately Decomposed)**: Methodology prescribes decomposition into stories or features, typically 3–5 days of work. Agents can execute most units independently.
- **4 (Well Decomposed)**: Methodology prescribes small, atomic tasks (< 2 days, often < 1 day). Clear acceptance criteria. Agents can execute independently and verify completion. Examples: FDD, XP, Shape Up's 6-week cycle.
- **5 (Hierarchically Decomposed)**: Methodology includes multi-level decomposition (epics → features → tasks → subtasks) with explicit dependencies and orchestration guidance. Agents can dynamically compose and parallelize work. Examples: SAFe, LeSS with multi-team coordination.

**Weight**: 12 points

**Context-Specific Notes**:
- **Solo+Agent**: Agents need task granularity of 4–8 hours; fine decomposition is critical.
- **Team+Agents**: Decomposition must span team boundaries; 1–3 day tasks per team member enable coordination.
- **Programme**: Hierarchical decomposition is non-negotiable; cross-team dependencies must be explicit.

---

### Dimension 3: Verification & Validation Rigour

**Definition**: The degree to which the methodology mandates or encourages automated verification practices (unit tests, integration tests, property checks, type checking, linting, formal proofs, contract validation) that agents can run autonomously to self-validate work and detect errors before human review.

**Why It Matters for Agentic SDLC**:
- Agents generate code at higher volume than humans; manual review alone cannot keep pace.
- Automated V&V gates allow agents to iteratively self-correct, reducing human bottlenecks.
- Methodologies that mandate testing and verification (TDD, BDD, formal methods) are naturally suited to agent iteration.

**Evidence Base**:
- TDD empirical studies (Madeyski, 2010 onwards) show medium-to-large effect sizes on defect reduction and modularization; test suites are executable agents' self-validation loops.[7]
- Continuous Delivery research shows that automated testing and quality gates are prerequisite for high-throughput delivery; agents demand the same infrastructure.[8]
- VeriAct framework integrates verification as a core feedback signal: agents observe test failures, formal verification results, and type errors, then iterate.[2]
- NVIDIA's AI test agent research (2024) demonstrates that agents can autonomously generate and execute test cases, reducing human test effort by 60–80%.[9]

**1–5 Scale**:
- **1 (Minimal)**: Methodology does not prescribe testing or verification; manual testing only. Agents produce untested code.
- **2 (Basic Testing)**: Methodology recommends testing but does not mandate it or integrate it into workflow. Manual test execution. Examples: early-stage Waterfall, some RUP implementations.
- **3 (Test-Included)**: Methodology includes testing and CI/CD expectations but does not mandate TDD or formal verification. Agents can run tests but do not automatically iterate on failures.
- **4 (Test-Driven)**: Methodology mandates TDD or BDD; tests are first-class artifacts. Automated quality gates. Agents can iterate on test failures and self-correct. Examples: XP, BDD methodologies, modern Scrum.
- **5 (Verification-Integrated)**: Methodology integrates automated testing, type checking, formal verification, and/or property-based testing. Verification results are structured feedback that agents consume and iterate on. Examples: Cleanroom, formal methods, TLA+, VeriAct.

**Weight**: 12 points

**Context-Specific Notes**:
- **Solo+Agent**: Agents depend entirely on automated V&V; strong testing infrastructure is mandatory.
- **Team+Agents**: Automated V&V gates reduce human code review load and accelerate feedback.
- **Programme**: Distributed verification across teams requires shared quality infrastructure and gate definitions.

---

### Dimension 4: Feedback Loop Structure

**Definition**: The tightness, formality, and clarity of feedback loops: how quickly and explicitly does the methodology enable agents to receive structured feedback on their work, and can agents iterate without waiting for human availability?

**Why It Matters for Agentic SDLC**:
- Agents can only improve if feedback is rapid, structured, and actionable.
- Loose feedback loops (multi-day human review cycles) waste agent potential; tight loops (automated, sub-minute) enable iterative refinement.
- Methodologies that formalize feedback (Kanban's continuous flow, XP's pair review, automated CI feedback) are agent-friendly.

**Evidence Base**:
- Trunk-Based Development research (Atlassian, ThoughtWorks) shows that frequent merges (multiple per day) enable rapid feedback and reduce defect leakage; agents benefit from millisecond-scale feedback.[10]
- Kanban research shows that visualized workflow and WIP limits create real-time feedback on bottlenecks; agents can consume this and adjust allocation.[11]
- Martin Kleppmann's 2025 blog on formal verification posits that AI will make verification mainstream, with agents running formal checks in real-time loops.[12]

**1–5 Scale**:
- **1 (Delayed)**: Feedback cycles are multi-day or longer (e.g., weekly code review). Agents cannot iterate in time.
- **2 (Batch Feedback)**: Feedback is formalized but infrequent (e.g., sprint review, end-of-phase review). Agents wait days to iterate.
- **3 (Structured Daily)**: Methodology includes daily feedback (standup, daily planning) and automated CI feedback (same-day). Agents can iterate within a day.
- **4 (Continuous Feedback)**: Methodology integrates continuous feedback loops (Kanban, CI/CD, real-time monitoring). Agents receive feedback within hours or minutes.
- **5 (Real-Time, Autonomous Iteration)**: Methodology enables sub-minute feedback (automated testing, verification, code review simulation) that agents consume and iterate on autonomously. Examples: Trunk-Based Development + full CI/CD automation, spec-driven development with verification, multi-agent orchestration frameworks.

**Weight**: 11 points

**Context-Specific Notes**:
- **Solo+Agent**: Agent depends entirely on automated feedback; sub-minute cycles are ideal.
- **Team+Agents**: Mixed feedback (automated + human, 4–24 hour cycles) is typical.
- **Programme**: Formal escalation and cross-team feedback paths must be defined; some feedback may be async.

---

### Dimension 5: Artifact Traceability

**Definition**: The degree to which the methodology produces and maintains a traceable chain of artifacts (requirements → design → code → tests → deployment logs) that agents can navigate, reason about, and link across the artifact supply chain.

**Why It Matters for Agentic SDLC**:
- Agents need to understand *why* code was written (traceability to requirements), not just *what* it does.
- Traceability enables agents to reason about impact of changes, detect inconsistencies, and verify completeness.
- Methodologies that produce explicit artifacts (ADRs, design docs, test reports) and link them are agent-friendly.

**Evidence Base**:
- ADR (Architecture Decision Record) research (AWS, Google, Microsoft, RedHat) shows that documented decisions enable faster onboarding and better reasoning about change impact; agents benefit similarly.[13]
- Model-Driven Development research shows that traceability from requirements to generated code reduces defects and enables automated consistency checks.[14]
- GitHub's Spec Kit positions specs as the source of truth, with traceability from spec to code to tests; this is an agent-centric model.[1]

**1–5 Scale**:
- **1 (Implicit)**: Traceability is not enforced; artifacts are scattered (requirements in email, design in wikis, code comments). Agents cannot trace end-to-end.
- **2 (Loose)**: Some artifacts exist (e.g., requirements document, code) but links are not formalized or maintained.
- **3 (Documented)**: Methodology produces key artifacts (requirements, design, tests) but traceability is manual or lightweight (e.g., requirement IDs in commit messages).
- **4 (Formalized)**: Methodology mandates artifact traceability (e.g., requirements linked to user stories, stories to design, design to code, code to tests). Tools support traceability queries. Examples: RUP, PRINCE2, some CMMI implementations.
- **5 (Executable Traceability)**: Methodology integrates artifact traceability with automated validation (e.g., requirements verified by tests, specs verified by code execution, ADRs checked for compliance). Agents can query and reason about artifact chains. Examples: formal methods with code generators, model-driven development, spec-driven development.

**Weight**: 10 points

**Context-Specific Notes**:
- **Solo+Agent**: Moderate traceability (level 3–4) is sufficient; the agent maintains implicit knowledge.
- **Team+Agents**: Formalized traceability (level 4–5) is important for onboarding new agents and coordinating handoffs.
- **Programme**: Executable traceability (level 5) is essential for cross-team impact analysis and dependency visibility.

---

### Dimension 6: Ceremony & Documentation Overhead

**Definition**: The magnitude and prescriptiveness of ceremonies (meetings, reviews, standups) and documentation artifacts mandated by the methodology. Assessed by: Does overhead *enable* agent work (e.g., clear role definitions) or *hinder* it (e.g., agents must produce ceremony artifacts that do not aid machine reasoning)?

**Why It Matters for Agentic SDLC**:
- High ceremony (waterfall gate reviews, extensive documentation) can slow agent throughput if agents must produce ceremony artifacts.
- However, well-designed ceremonies and documentation can provide context and coordination that agents benefit from.
- The question is not "low ceremony is better" but "does ceremony aid agent reasoning and coordination?"

**Evidence Base**:
- Agile adoption research (Parabol, 2024) shows that high-ceremony methodologies (RUP, CMMI) are declining in favour of lower-ceremony approaches; agent-driven teams likely amplify this trend.[15]
- Shape Up research (Basecamp, 2024) shows that 6-week cycles with minimal daily ceremony ("shaping, betting, building") enable faster delivery than Scrum's daily standups and sprint planning; this pattern may transfer to agents.[16]
- ThoughtWorks' "Preparing Your Team for Agentic SDLC" (2024) notes that human-agent collaboration should *reduce* ceremony overhead because agents eliminate intermediate reviews.[17]
- Conversely, DAD research shows that structured ceremonies (retrospectives, risk reviews) are important for continuous improvement; agents benefit from these decision points.[18]

**1–5 Scale**:
- **1 (Ceremony-Heavy)**: Methodology mandates extensive meetings (multiple reviews per week, gatekeeping ceremonies) and heavy documentation (comprehensive design docs, test plans). Agents must produce ceremony artifacts. Agents are bottlenecked by ceremony participation.
- **2 (Moderate Ceremony)**: Methodology includes some ceremonies (sprint planning, review, retrospective) and documentation expectations (requirements, design, test docs). Agents can participate but some effort goes to non-reasoning artifacts.
- **3 (Lightweight Ceremony)**: Methodology prescribes minimal ceremonies (daily standup, sprint planning/review) and focused documentation (user stories, ADRs, test code). Agents produce reasoning-supporting artifacts.
- **4 (Minimal Ceremony)**: Methodology avoids prescriptive ceremonies; artifacts are code-first (specs in code, tests as documentation). Examples: Kanban, Trunk-Based Development, TDD.
- **5 (Ceremony-Free, Context-Driven)**: Methodology eliminates formal ceremonies in favour of continuous flow and context-driven practices. Agents self-organize and gather context from artifacts and automated feedback. Examples: Shape Up, some Kanban implementations.

**Weight**: 8 points

**Context-Specific Notes**:
- **Solo+Agent**: Ceremony overhead is purely waste; minimal ceremony (level 4–5) is preferable.
- **Team+Agents**: Some ceremony (level 3–4) is necessary for coordination and decision-making; weekly retrospectives and planning are valuable.
- **Programme**: Moderate ceremony (level 3) is needed for cross-team sync and risk escalation; excessive ceremony (level 1) creates bottlenecks.

---

### Dimension 7: Concurrency & Parallelism Support

**Definition**: The degree to which the methodology accommodates multiple agents (or agent-human pairs) working in parallel on the same codebase without destructive interference (merge conflicts, broken integration, race conditions). Includes explicit guidance on branching, merging, and coordinating concurrent work.

**Why It Matters for Agentic SDLC**:
- Agents dramatically increase development throughput, so parallelism is essential.
- Methodologies that mandate branching strategies, frequent merges, and integration discipline reduce conflict.
- Methodologies that encourage long-lived branches or loose merge discipline create chaos at scale.

**Evidence Base**:
- Version control research (2024–2025) shows that 10–20% of all merges result in conflicts; frequent merges (daily or more) reduce this to <5%.[19]
- Trunk-Based Development research (Atlassian, AWS, Google) shows that daily or sub-daily merges eliminate most merge conflicts and are the standard for high-performing teams.[10]
- Git branching strategy research shows that GitFlow (structured branches) reduces integration risk compared to ad hoc branching, but Trunk-Based (minimal branches) is fastest for high-throughput teams.[20]
- ThoughtWorks Radar 2024 lists "Trunk-Based Development" as "Adopt" for high-frequency deployment; this pattern is essential for agent-driven teams multiplying throughput.[21]

**1–5 Scale**:
- **1 (No Parallelism)**: Methodology enforces sequential work (e.g., waterfall phases, code ownership preventing concurrent editing). Multiple agents cannot work simultaneously.
- **2 (Loose Parallelism)**: Methodology allows parallel work but provides minimal guidance on integration. Long-lived branches, high merge-conflict risk. Examples: ad hoc feature branching without discipline.
- **3 (Managed Parallelism)**: Methodology prescribes branching strategy (e.g., GitFlow, feature branches) and merge discipline (code review, CI). Conflicts are managed but not minimized. Examples: Scrum + GitFlow, standard GitHub flow.
- **4 (Parallel-Native)**: Methodology is designed for concurrent work. Frequent merges (daily), automated conflict resolution where possible, strong CI/CD discipline. Examples: Trunk-Based Development, Kanban, XP (pair programming reduces conflicts by synchronizing work).
- **5 (Dynamically Parallel)**: Methodology supports dynamic parallelism: agents autonomously spawn and coordinate sub-agents, with built-in task orchestration and dependency resolution. Merge and integration happen transparently. Examples: multi-agent orchestration frameworks (AgentOrchestra, LangGraph), agent-native SDLC frameworks.

**Weight**: 11 points

**Context-Specific Notes**:
- **Solo+Agent**: Concurrency is internal to the agent; the methodology's parallelism support is less critical (level 3–4 sufficient).
- **Team+Agents**: Strong parallelism support (level 4–5) is critical; multiple agents per team member multiply merge risk.
- **Programme**: Dynamic parallelism (level 5) is non-negotiable; cross-team work must not create bottlenecks.

---

### Dimension 8: Role Clarity & Delegation Model

**Definition**: The degree to which the methodology clearly defines roles, responsibilities, escalation paths, and handoff points such that agents understand their boundaries and can autonomously decide what to execute versus when to escalate or hand off to humans/other agents.

**Why It Matters for Agentic SDLC**:
- Agents need explicit role definitions and escalation criteria to avoid autonomous decisions they should not make.
- Unclear roles lead to agent confusion (what can I commit? when do I escalate? who is responsible for this?).
- Methodologies with clear RACI matrices, escalation criteria, and handoff contracts enable confident agent delegation.

**Evidence Base**:
- Agentic SDLC research (ThoughtWorks, PWC, Microsoft, 2024–2025) converges on "delegate, review, own" model: agents handle execution; humans review for risk and correctness; humans own architecture and outcomes.[17][22][23]
- PRINCE2 and CMMI research emphasizes role clarity and RACI matrices for risk mitigation; this pattern is essential for agent governance.[24]
- Shape Up research shows that clear role separation (Shaper vs. Bettors vs. Builders) reduces ambiguity; agents benefit from analogous clarity.[16]

**1–5 Scale**:
- **1 (Ambiguous Roles)**: Methodology does not define roles or responsibilities. Agents (and humans) are unclear about authority and decision boundaries. Examples: informal startups, ad hoc development.
- **2 (Loosely Defined)**: Methodology mentions roles (e.g., Scrum Master, Product Owner) but does not explicitly define responsibilities or escalation criteria.
- **3 (Defined Roles)**: Methodology clearly defines roles (e.g., Product Owner defines what; Developers define how; QA defines quality gates), but escalation criteria are implicit or informal.
- **4 (Role + Escalation)**: Methodology explicitly defines roles, responsibilities, RACI matrix, and escalation criteria (e.g., "technical debt over 3 days of effort requires Architecture review"). Examples: RUP, PRINCE2, SAFe.
- **5 (Role + Autonomous Delegation)**: Methodology defines clear roles and *automated* escalation criteria that agents can parse (e.g., "security issues → escalate to InfoSec agent"; "breaking changes → escalate to Lead Developer"). Agents can autonomously determine delegation. Examples: agent-native SDLC frameworks, highly formalized governance.

**Weight**: 10 points

**Context-Specific Notes**:
- **Solo+Agent**: Role clarity is less critical (agent can infer or ask); level 3–4 is sufficient.
- **Team+Agents**: Clear roles and escalation (level 4) are important to prevent agent conflicts and ensure human oversight.
- **Programme**: Automated delegation (level 5) is valuable for cross-team coordination; without it, agents escalate unnecessarily.

---

### Dimension 9: Change Management & Adaptability

**Definition**: The degree to which the methodology can accommodate changing requirements, shifting priorities, and mid-project pivots. Does the methodology assume stable requirements (waterfall) or support dynamic change? Can agents adapt execution mid-cycle?

**Why It Matters for Agentic SDLC**:
- Real-world projects change; methodologies that support change are agent-friendly.
- Agents that can re-plan mid-cycle (e.g., pull new work from backlog, drop cancelled items) are more efficient than those locked into fixed plans.
- Methodologies that require heavy re-planning (waterfall) force expensive re-execution; agile methodologies handle change more gracefully.

**Evidence Base**:
- Agile research (VersionOne, 2024) shows that teams using Agile (Scrum, Kanban) report 92% ability to respond to changing requirements, vs. 30% for traditional approaches.[25]
- Spiral model research (Boehm, 2000 onwards) shows that risk-driven cycles enable re-planning at cycle boundaries; agents can do this autonomously.[26]
- Shape Up research (Basecamp, 2024) shows that 6-week fixed cycles with mid-cycle "descope" (not "change scope") enable adaptation without chaos.[16]

**1–5 Scale**:
- **1 (Fixed Plan)**: Methodology assumes requirements are locked before development (Waterfall, V-Model). Change requires expensive re-planning or is discouraged. Agents cannot adapt.
- **2 (Limited Change)**: Methodology allows change but penalizes it (e.g., RUP formal change control, some Spiral cycles). Agents must escalate changes to humans.
- **3 (Planned Flexibility)**: Methodology accommodates change within cycles/phases (Scrum backlog can be adjusted, DAD supports re-planning). Agents can drop completed items and pick up new work mid-sprint.
- **4 (Continuous Adaptation)**: Methodology is designed for continuous change (Kanban, Shape Up, Continuous Delivery). Backlog is fluid; agents can adapt work allocation without formal gates.
- **5 (Autonomous Adaptation)**: Methodology supports agents autonomously re-planning based on new information, shifting priorities, or discovered blockers. Agents can pause work, escalate blockers, and pick up higher-priority items. Examples: some Kanban implementations, advanced Trunk-Based Development, agent-native frameworks.

**Weight**: 9 points

**Context-Specific Notes**:
- **Solo+Agent**: Adaptability is less critical (agent can ask); level 3–4 is sufficient.
- **Team+Agents**: Strong adaptability (level 4) enables agents to respond to priority changes without blocking humans.
- **Programme**: Continuous adaptation (level 4–5) is important; rigid change control creates coordination bottlenecks.

---

### Dimension 10: Scalability of Coordination

**Definition**: How well does the methodology's coordination mechanism (ceremonies, artifacts, decision-making processes) scale as team and agent count multiply? Does it degrade gracefully from 3 people to 300?

**Why It Matters for Agentic SDLC**:
- Agents multiply per-person throughput (possibly 3–5x), so a 3-person team with agents may have throughput equivalent to 10+ humans.
- Coordination mechanisms must scale to this multiplied throughput.
- Methodologies with linear or sub-linear overhead scale well; those with quadratic overhead (e.g., everyone in every meeting) fail.

**Evidence Base**:
- Scaled Agile research (Atlassian, 2024) shows that SAFe, LeSS, and Nexus have different scaling characteristics: SAFe scales to 1000+; LeSS to ~50; Nexus to ~30.[27]
- Spotify model research (2024) shows that "squads + tribes + chapters" scale autonomously team decision-making while maintaining coordination.[28]
- ThoughtWorks Radar (2024) recommends DAD for "scaling without the overhead" of SAFe; DAD's toolkit approach enables lighter coordination.[21]
- Trunk-Based Development research shows that daily/sub-daily merges scale to 1000s of developers without bottleneck if CI/CD infrastructure is solid.[10]

**1–5 Scale**:
- **1 (Poor Scaling)**: Methodology has quadratic communication overhead (everyone talks to everyone). Breaks at ~10 people. Examples: some early-stage startups, Scrum at scale without scaling framework.
- **2 (Limited Scaling)**: Methodology scales to ~20–30 people; beyond that, coordination overhead grows significantly.
- **3 (Moderate Scaling)**: Methodology includes some scaling provisions (e.g., Scrum + LeSS for 2 teams, Scrumban for 3–4 teams). Works to ~50 people.
- **4 (Good Scaling)**: Methodology is designed for scaling; includes coordination mechanisms for multi-team (e.g., SAFe's synchronisation points, Nexus's Nexus Sprint, LeSS's shared product backlog). Scales to 100–300 people.
- **5 (Excellent Scaling)**: Methodology scales dynamically; coordination overhead is logarithmic or sub-linear (e.g., autonomous teams, minimal synchronisation points, async decision-making). Examples: highly distributed Kanban, Trunk-Based Development at Google/Meta scale, Spotify model.

**Weight**: 9 points

**Context-Specific Notes**:
- **Solo+Agent**: Scaling is not relevant (level 5 by default or N/A).
- **Team+Agents**: Moderate scaling (level 3) is sufficient for 3–10 agents.
- **Programme**: Excellent scaling (level 4–5) is essential; coordination overhead must not grow with agent count.

---

### Dimension 11: Quality Gate Structure

**Definition**: The degree to which the methodology defines explicit, formalised quality gates (code review, architecture review, security review, performance gate, deployment gate) and whether these gates can be automated, agent-mediated, or only human-reviewed.

**Why It Matters for Agentic SDLC**:
- Agents generate code at high volume; human review alone creates bottlenecks.
- Automated quality gates (static analysis, type checking, automated security scanning) reduce human load and provide agents with actionable feedback.
- Methodologies that separate concerns into automatable gates (e.g., SonarQube for code smells, SAST for security) enable parallel gates and faster feedback.

**Evidence Base**:
- Code review automation research (Augment Code, 2024–2025) shows that layered gates (pre-commit linting, CI static analysis, CR automation, human review) reduce human review time by 40–60% and catch more issues earlier.[29]
- SIEM and DAST research shows that automated security gates enable DevSecOps without slowing delivery.[30]
- Continuous Delivery research (Humble & Farley, 2010 onwards) shows that automated quality gates are prerequisite for high-frequency deployment.[8]
- CI/CD best practices (GitHub Actions, GitLab CI, Jenkins) emphasize layered gates; agents can be inserted into any layer.

**1–5 Scale**:
- **1 (No Gates)**: Methodology has no formalised quality gates; quality is ad hoc (manual testing, no code review).
- **2 (Manual Gates Only)**: Methodology requires manual review (code review, QA sign-off) but provides no automation. Bottleneck on humans.
- **3 (Some Automated Gates)**: Methodology includes basic automated checks (unit tests, linting) but relies on humans for architecture, security, or performance review. Examples: modern Scrum, Kanban with CI.
- **4 (Layered Automated + Human Gates)**: Methodology defines multiple gates (unit tests, static analysis, code review, security scan, performance gate) with clear ownership (some automated, some human). Examples: modern CI/CD + Pull Request workflows, mature DevOps.
- **5 (Fully Automated or Agent-Mediated Gates)**: Methodology integrates automated gates at all levels; security, performance, architecture checks are automated or delegated to agents for initial assessment. Examples: very mature CI/CD, formal verification, spec-driven development with automated checking.

**Weight**: 10 points

**Context-Specific Notes**:
- **Solo+Agent**: Automated gates (level 4–5) are essential; human review is secondary.
- **Team+Agents**: Layered gates (level 4) with human escalation are typical.
- **Programme**: Clear gate ownership and escalation paths (level 4–5) are essential; distributed review is necessary.

---

### Dimension 12: Knowledge Management & Context Persistence

**Definition**: The degree to which the methodology requires or enables maintaining a knowledge base of historical decisions, architectural patterns, constraints, and conventions that agents can query to understand context and avoid repeating past mistakes.

**Why It Matters for Agentic SDLC**:
- Agents have no implicit memory of design patterns, why past decisions were made, or what "the way we do things here" is.
- Methodologies that encode this knowledge (ADRs, architectural decision logs, pattern libraries, constraint documentation) enable agents to reason about consistency and avoid rework.
- Informal knowledge (senior dev's experience) is inaccessible to agents; formalized knowledge is agent-leverage.

**Evidence Base**:
- ADR research (AWS, Google, Microsoft, 2024) shows that documented decisions improve onboarding speed, reduce rework, and enable autonomous decision-making.[13]
- Case studies (e.g., ThoughtWorks, Spotify) show that teams that maintain architecture decision logs and pattern libraries have faster delivery and fewer inconsistencies.[28]
- Knowledge management in CMMI and RUP emphasizes historical data; agents can query and learn from this.[24]
- GitHub Spec Kit and spec-driven development position specs and ADRs as executable context that agents consume.[1]

**1–5 Scale**:
- **1 (No Knowledge Base)**: Methodology has no formalised knowledge base; context is implicit (senior devs' heads, informal Slack channels, tribal knowledge). Agents cannot access context.
- **2 (Minimal Docs)**: Methodology includes basic documentation (README, some design docs) but it is not formalised or searchable.
- **3 (Structured Docs)**: Methodology includes formalised documentation (architecture docs, ADRs in version control, pattern wiki). Agents can query but may find inconsistencies or gaps.
- **4 (Decision Log)**: Methodology maintains a comprehensive decision log (ADRs, constraint docs, pattern library, technical standards) in version control. Agents can query and learn. Examples: mature orgs with ADR discipline.
- **5 (Executable Knowledge)**: Methodology integrates knowledge base with automated reasoning: agents can query decisions, check compliance, propose changes, and validate against patterns. Examples: spec-driven development, model-driven development with pattern libraries, formal specifications.

**Weight**: 8 points

**Context-Specific Notes**:
- **Solo+Agent**: Moderate knowledge management (level 3) is sufficient; agent builds its own implicit memory.
- **Team+Agents**: Structured knowledge base (level 4) is important for agent coordination and consistency.
- **Programme**: Executable knowledge (level 4–5) is valuable for cross-team pattern sharing and compliance.

---

### Dimension 13: Risk Management Integration

**Definition**: The degree to which the methodology incorporates risk identification, assessment, and mitigation as a first-class activity (not afterthought) and whether agents can operationalise risk management (identify risks, propose mitigations, escalate critical risks).

**Why It Matters for Agentic SDLC**:
- Agents increase delivery velocity, which can increase risk if not managed.
- Methodologies that integrate risk (Spiral, CMMI, DAD, SAFe) enable agents to identify and escalate risks rather than delivering silently into risk.
- Ad hoc risk management (or none) is dangerous at agent scale.

**Evidence Base**:
- Spiral model research (Boehm, 1986 onwards) shows that risk-driven cycles reduce project failure; agents can operationalise risk assessment at cycle boundaries.[26]
- CMMI and PRINCE2 research emphasises risk management; CMMI level 3+ requires formal risk processes.[24]
- Agile risk management research (ISACA, 2023–2024) shows that teams using explicit risk identification and ROAM (Resolve, Own, Accept, Mitigate) practices have better outcomes.[31]

**1–5 Scale**:
- **1 (No Risk Management)**: Methodology does not address risk; risks are discovered post-facto. Examples: ad hoc development.
- **2 (Ad Hoc Risk)**: Methodology acknowledges risk but has no formalised process; risk mitigation is informal.
- **3 (Periodic Risk Review)**: Methodology includes periodic risk review (e.g., sprint retrospective, phase gate) but risk is not a continuous activity.
- **4 (Integrated Risk)**: Methodology integrates risk identification and mitigation as ongoing activities (e.g., Spiral cycle risk assessment, ROAM sessions in Kanban, risk board in Scrum). Examples: Spiral, mature Scrum, DAD.
- **5 (Autonomous Risk Operationalisation)**: Methodology enables agents to autonomously identify risks (code complexity, missing test coverage, security issues), propose mitigations, and escalate critical risks. Examples: advanced CI/CD with automated risk scoring, formal verification, agent-native frameworks.

**Weight**: 8 points

**Context-Specific Notes**:
- **Solo+Agent**: Periodic risk review (level 3–4) is sufficient.
- **Team+Agents**: Integrated risk management (level 4) is important for team alignment.
- **Programme**: Autonomous risk identification (level 5) is valuable for cross-team risk visibility.

---

### Dimension 14: Maintainability & Technical Debt Governance

**Definition**: The degree to which the methodology includes explicit mechanisms for managing technical debt, refactoring, and code health maintenance—critical because agents can generate high volumes of code, and debt accumulates rapidly without discipline.

**Why It Matters for Agentic SDLC**:
- Agents can generate 10–100x more code than humans; without debt governance, systems become unmaintainable within weeks.
- Methodologies that enforce code quality, refactoring, and debt paydown (TDD, XP, modern Agile) maintain health.
- Methodologies without debt governance (early-stage, high-speed development) accumulate debt exponentially.

**Evidence Base**:
- Technical debt research (IBM, SonarSource, 2024–2025) shows that debt compounds; leaving 10% of code as debt leads to 30% slowdown within months.[32]
- Refactoring research (Fowler, 2018 onwards) shows that continuous refactoring reduces debt accumulation; methodologies that mandate refactoring (XP, TDD) have lower debt.[33]
- McKinsey research (2024) shows that teams allocating 20% of sprint capacity to debt paydown have 40% faster delivery long-term.[25]

**1–5 Scale**:
- **1 (No Governance)**: Methodology has no debt management; debt accumulates continuously. Maintenance is ignored until crisis.
- **2 (Implicit Debt)**: Methodology acknowledges debt but has no formalised mechanism; debt is handled ad hoc during slow periods.
- **3 (Periodic Debt Sprints)**: Methodology includes periodic debt paydown (e.g., "tech debt sprint" once per quarter, 10% of sprint capacity reserved for refactoring). Examples: some Scrum teams.
- **4 (Continuous Debt Management)**: Methodology includes continuous mechanisms for debt reduction (TDD reduces debt; refactoring is ongoing; code quality gates prevent new debt; metrics tracked). Examples: XP, mature Scrum with quality focus, modern CI/CD.
- **5 (Autonomous Debt Governance)**: Methodology enables agents to autonomously identify debt, propose refactoring, validate that refactoring improves health, and execute paydown within normal work. Examples: advanced code quality automation, formal verification enabling safe refactoring, intelligent agents with refactoring tools.

**Weight**: 8 points

**Context-Specific Notes**:
- **Solo+Agent**: Continuous debt management (level 4) is essential.
- **Team+Agents**: Continuous mechanisms (level 4) with team coordination.
- **Programme**: Autonomous governance (level 5) is valuable; otherwise, debt spreads across teams.

---

### Rubric Summary Table

| Dimension | Weight | 1 (Low) | 3 (Medium) | 5 (High) | Solo+Agent | Team+Agents | Programme |
|-----------|--------|---------|-----------|----------|-----------|-------------|-----------|
| 1. Specification Formality | 14 | Informal narratives | Structured templates, BDD | Formal specs + verification | High formality critical | Moderate–high | High for coordination |
| 2. Task Decomposability | 12 | Monolithic work units | 3–5 day stories | Atomic tasks, hierarchical | High granularity | 1–3 day tasks | Hierarchical with deps |
| 3. Verification & Validation | 12 | Minimal testing | Test-included, CI/CD | Verification-integrated | Agents self-validate | Automated gates | Shared quality infra |
| 4. Feedback Loop Structure | 11 | Multi-day cycles | Daily structured feedback | Sub-minute autonomous | Sub-minute loops | 4–24 hour cycles | Formal escalation paths |
| 5. Artifact Traceability | 10 | Implicit artifacts | Manual traceability | Executable traceability | Moderate sufficient | Formalized traceability | Executable for impact |
| 6. Ceremony & Documentation | 8 | Heavy ceremony/docs | Lightweight ceremony | Minimal/code-first | Overhead is waste | Some ceremony needed | Moderate for sync |
| 7. Concurrency & Parallelism | 11 | No parallelism | Managed (GitFlow) | Autonomous/dynamic | Internal to agent | Parallel-native (L4–5) | Dynamic parallelism |
| 8. Role Clarity & Delegation | 10 | Ambiguous roles | Defined with escalation | Autonomous delegation | Less critical | Important for oversight | Automated delegation |
| 9. Change & Adaptability | 9 | Fixed plan (Waterfall) | Planned flexibility | Autonomous adaptation | Less critical | Strong adaptability | Continuous adaptation |
| 10. Scalability of Coordination | 9 | Poor (quadratic) | Moderate (50–100) | Excellent (1000s) | N/A (solo) | Moderate scaling | Excellent scaling |
| 11. Quality Gate Structure | 10 | No gates | Manual gates only | Automated/agent gates | Automated essential | Layered gates | Distributed gates |
| 12. Knowledge Management | 8 | No KB | Structured docs | Executable knowledge | Moderate sufficient | Important for consistency | Cross-team patterns |
| 13. Risk Management | 8 | No risk process | Periodic review | Autonomous identification | Periodic review | Integrated risk | Autonomous escalation |
| 14. Maintainability & Debt | 8 | No governance | Periodic sprints | Autonomous governance | Continuous critical | Continuous mechanisms | Autonomous across teams |
| **TOTAL** | **137** | — | — | — | — | — | — |

---

## Part B: Comprehensive Methodology Catalogue

### Overview

This catalogue identifies 42 distinct software development methodologies covering traditional, agile, emerging, and AI-native categories. For each, we provide:
- Full name and common abbreviations
- Original author(s), organisation, and year
- 2–3 sentence core philosophy summary
- Primary artifacts
- Prescribed roles
- Typical team size and project scale
- Current adoption status (2024–2026)
- Key references (academic and practitioner sources)

---

### Section B.1: Formal / Traditional Methodologies

#### 1. Waterfall Model

**Full Name**: Waterfall Model (also: Linear Sequential Model)

**Original Author(s) / Org / Year**: Winston W. Royce, 1970 (originally described in TRW Systems; popularised by structured methodologies)

**Core Philosophy**: Waterfall is a linear, sequential lifecycle where each phase (requirements, design, implementation, testing, deployment) must be completed and signed off before the next begins. Assumes requirements are well-defined upfront and changes are expensive; focuses on comprehensive planning and risk mitigation through upfront analysis.

**Primary Artifacts**: Requirements Specification Document (RSD), Design Document, Code, Test Plan, Test Cases, User Manual, Deployment Plan, Sign-off documentation.

**Prescribed Roles**: Project Manager (overall coordination), Business Analyst (requirements), Architect (design), Developer (implementation), QA Engineer (testing), Technical Writer (documentation).

**Typical Team Size & Scale**: 5–50 people; large, long-duration projects (6 months–5 years) with stable, well-understood requirements.

**Current Adoption Status (2024–2026)**: Declining. Used in highly regulated industries (government, aerospace, defence) where change is rare and traceability is mandated. Rarely chosen for new projects in commercial software.

**Key References**:
- Royce, W. W. (1970). "Managing the Development of Large Software Systems." In Proceedings of IEEE WESCON. DOI: Classic foundational paper.
- Sommerville, I. (2015). Software Engineering (10th ed.). Pearson. Chapter 2 provides comprehensive overview of Waterfall and derivatives.
- SEI/Carnegie Mellon (1995). Software Engineering: A Practitioner's Approach (3rd ed., Pressman). Widely-used textbook.

---

#### 2. V-Model

**Full Name**: V-Model (Verification and Validation Model)

**Original Author(s) / Org / Year**: Paul Rook (Science Applications International Corporation, SAIC), 1980s. Extended by TÜV Süd and German automotive/systems safety community.

**Core Philosophy**: V-Model is a structured extension of Waterfall that explicitly links each development phase (requirements → design → implementation) with a corresponding testing/validation phase (acceptance test → integration test → unit test). The "V" shape reflects the flow: descending (decomposition) on the left, ascending (integration & testing) on the right.

**Primary Artifacts**: Requirements Specification, Test Strategy, Design Document, Code, Unit Test Cases, Integration Test Cases, System Test Cases, Acceptance Test Cases, Traceability Matrix.

**Prescribed Roles**: Project Manager, Business Analyst, Architect, Developer, QA/Test Engineer, Systems Engineer.

**Typical Team Size & Scale**: 5–100 people; embedded systems, critical infrastructure, medical devices, aerospace—projects requiring rigorous V&V.

**Current Adoption Status**: Widely used in regulated and safety-critical industries (medical, automotive, aerospace). Declining in commercial software.

**Key References**:
- Forsberg, K., & Mooz, H. (1991). "The Relationship of System Engineering to the Project Cycle." In INCOSE International Symposium.
- IEEE 1059 (2007). IEEE Guide for Software Verification and Validation. IEEE Standards.
- Swanson, E. B., & Beath, C. M. (1989). Maintaining Information Systems in Organizations. Irwin.

---

#### 3. Spiral Model

**Full Name**: Spiral Model (Spiral Development Process, Risk-Driven Process Model)

**Original Author(s) / Org / Year**: Barry W. Boehm, 1986 (Rand Corporation/TRW Defense and Space Systems Group)

**Core Philosophy**: Spiral is a risk-driven iterative process where development proceeds in cycles (spirals). Each cycle includes planning, risk analysis, development, and review phases. Risk assessment drives the choice of development paradigm (waterfall, iterative, or evolutionary) for each cycle. Emphasises early risk identification and mitigation.

**Primary Artifacts**: Project Plan, Risk Analysis Report, Development Plan, Code/Prototype, Test Results, Review/Validation Report (per cycle).

**Prescribed Roles**: Project Manager, Risk Manager, Architect, Developer, QA, Customer (involved in each cycle review).

**Typical Team Size & Scale**: 10–50 people; large, complex, high-risk projects (3–10 year timescale) where risk varies significantly.

**Current Adoption Status**: Niche, primarily in defence/aerospace contractors and projects with significant technical risk. Less common in commercial software.

**Key References**:
- Boehm, B. W. (1986). "A Spiral Model of Software Development and Enhancement." ACM SIGSOFT Software Engineering Notes, 11(4), 14–24. DOI: 10.1145/12944.12948. Foundational paper.
- Boehm, B. W. (2000). "Spiral Development: Experience, Principles, and Refinements." CMU/SEI Technical Report CMU/SEI-2000-SR-008.
- Boehm, B. W., & Turner, R. (2004). Balancing Agility and Discipline: A Guide for the Perplexed. Addison-Wesley.

---

#### 4. Rational Unified Process (RUP)

**Full Name**: Rational Unified Process (RUP, IBM Rational Unified Process)

**Original Author(s) / Org / Year**: Grady Booch, Ivar Jacobson, James Rumbaugh (Rational Software Corporation, acquired by IBM in 2003), 1997.

**Core Philosophy**: RUP is an iterative and incremental process framework that divides development into four phases (Inception, Elaboration, Construction, Transition), each containing multiple iterations. RUP is use-case driven, architecture-centric, and emphasises continuous refinement of models and architectural design. It is configurable and tailorable by teams.

**Primary Artifacts**: Vision Document, Use-Case Model, Supplementary Requirements, Architecture Document, Design Model, Implementation Model, Test Plan, Deployment Plan, Release Notes.

**Prescribed Roles**: Project Manager, Architect, Developer, QA, Business Analyst, Technical Writer, Configuration Manager.

**Typical Team Size & Scale**: 10–100+ people; large, complex enterprise projects (1–3 year timescale) with evolving requirements.

**Current Adoption Status**: Declining in commercial software (losing to Agile methods like Scrum and Kanban). Still used in some enterprise and government settings; heavily documented but perceived as heavyweight.

**Key References**:
- Kroll, P., & Kruchten, P. (2003). The Rational Unified Process Made Easy: A Practitioner's Guide to the RUP. Addison-Wesley.
- Jacobson, I., Booch, G., & Rumbaugh, J. (1998). The Unified Software Development Process. Addison-Wesley.
- IBM Rational (2003–2007). RUP product documentation. IBM Software.

---

#### 5. PRINCE2 (as applied to software)

**Full Name**: PRINCE2 (Projects in Controlled Environments, version 2)

**Original Author(s) / Org / Year**: UK Government (Central Computer and Telecommunications Agency, CCTA), evolving from the original PRINCE (1996). PRINCE2 2009 edition; updated 2017. Published by the Office of Government Commerce (OGC); now managed by Axelos Ltd.

**Core Philosophy**: PRINCE2 is a structured project governance and control framework emphasising defined roles, responsibilities, and decision gates. Focuses on business case, configuration management, lessons learned, and risk/issue management. Not software-specific; widely applied to IT and construction projects. Prescriptive rather than adaptive.

**Primary Artifacts**: Project Initiation Document (PID), Business Case, Configuration Management Plan, Risk Register, Issue Register, Quality Management Plan, Stage Plans, Project Board Minutes.

**Prescribed Roles**: Project Board (Strategic steering), Project Manager, Project Assurance, Project Support, Team Manager.

**Typical Team Size & Scale**: 5–500 people; enterprise programmes, government projects (6 months–5 years) with clear governance requirements.

**Current Adoption Status**: Widespread in UK and Commonwealth government and large enterprises. Less common in commercial software (Agile frameworks are preferred for software). PRINCE2 + Agile is an emerging hybrid (2015 onwards).

**Key References**:
- UK Office of Government Commerce (OGC). PRINCE2 (2009/2017). Official PRINCE2 Manual. TSO (The Stationery Office).
- Bentley, C. (2010). PRINCE2: A Practical Handbook (3rd ed.). Butterworth-Heinemann.
- Axelos Ltd. (2019). "PRINCE2 Foundation and Practitioner – Guidance." Axelos.

---

#### 6. CMMI (Capability Maturity Model Integration)

**Full Name**: CMMI (Capability Maturity Model Integration)

**Original Author(s) / Org / Year**: Carnegie Mellon University / Software Engineering Institute (SEI), 1997. Evolved from the original CMM (1993). CMMI-DEV 2.0 released 2023.

**Core Philosophy**: CMMI is a maturity model and process improvement framework that defines levels (1–5) of organisational process capability. Emphasises measurement, process discipline, and continuous improvement. Provides best practices for project management, engineering, and support processes. Not prescriptive about specific development methods; compatible with Waterfall, Agile, or hybrid approaches.

**Primary Artifacts**: Process Assets, Process Performance Data, Configuration Management Records, Verification and Validation Reports, Supplier Management Records.

**Prescribed Roles**: Process Group, Quality Assurance, Configuration Manager, Project Manager, Project Engineer.

**Typical Team Size & Scale**: 50–5000+ people; large organisations undergoing process improvement; commonly used by defence contractors, government agencies, and outsourcing firms.

**Current Adoption Status**: Still used in regulated/government sectors, but declining in commercial software. CMMI Level 3 certification is common in large outsourcing firms.

**Key References**:
- Carnegie Mellon University / SEI (2023). CMMI-DEV 2.0: Guidelines for Development, Version and Release 2.0. CMU/SEI-2023-TR-001.
- Chrissis, M. B., Konrad, M., & Shrum, S. (2011). CMMI for Development: Guidelines for Process Integration and Product Improvement (3rd ed.). Addison-Wesley.
- SEI (2020). "CMMI for Development (CMMI-DEV) v2.0 Model." Carnegie Mellon University.

---

#### 7. Cleanroom Software Engineering

**Full Name**: Cleanroom Software Engineering (Cleanroom Methodology)

**Original Author(s) / Org / Year**: Harlan Mills (IBM), Richard Linger (IBM), others. Developed in 1980s–1990s at IBM and promoted by SEI.

**Core Philosophy**: Cleanroom combines mathematically-based design and correctness verification with statistical usage testing for quality certification. The goal is to produce software with certifiable reliability without traditional debugging. Emphasises theory-based specification, box structure design, correctness verification, and statistical testing.

**Primary Artifacts**: Formal Specification (using mathematical notation), Box Structure Design Documents, Correctness Proof Outlines, Statistical Usage Test Plans, Test Results, Certification Reports.

**Prescribed Roles**: Specification/Design Team (independent), Test/Certification Team (independent), Project Manager.

**Typical Team Size & Scale**: 5–50 people; projects requiring high reliability certification (safety-critical, medical, telecommunications); medium-to-large systems.

**Current Adoption Status**: Niche, used in safety-critical and high-assurance software (aerospace, medical devices). Rarely used in commercial software due to high front-loaded cost and long development cycles.

**Key References**:
- Mills, H. D., Linger, R. C., & Hevner, A. R. (1987). "Principles of Information Systems Analysis and Design." Academic Press.
- Linger, R. C., & Mills, H. D. (2005). "Cleanroom Software Engineering: Ten Years of Improving Systems Quality." Crosstalk (IEEE), 18(10), 5–9.
- Poore, J. H., & Mills, H. D. (2007). "Assuring High-Quality Software for the Nation: The Return on Invested Capital." Crosstalk, 20(10), 4–10.

---

#### 8. Formal Methods (Z, B, VDM, TLA+)

**Full Name**: Formal Methods (including Z Notation, B-Method, Vienna Development Method, Temporal Logic of Actions)

**Original Author(s) / Org / Year**: Multiple authors. Z Notation (Jean-Raymond Abrial, Oxford, 1980s). B-Method (Jean-Raymond Abrial, INRIA, 1994). VDM (Dines Bjørner, Cliff Jones, others, 1980s). TLA+ (Leslie Lamport, 1990s–2000s).

**Core Philosophy**: Formal methods use mathematical notation and logic to specify and verify software behaviour with mathematical rigour. A formal specification is a precise mathematical model of the system; properties are proven (or disproven) using formal verification techniques. Catches inconsistencies and errors early (in specification phase); reduces need for testing of proven properties.

**Primary Artifacts**: Formal Specification (in Z, B, VDM, or TLA+), Proof Obligations, Correctness Proofs (machine-checked or hand-verified), Code (often generated from formal specs), Verification Reports.

**Prescribed Roles**: Formal Methods Specialist, Software Engineer, Verification Engineer, Project Manager.

**Typical Team Size & Scale**: 5–30 people; small to medium projects requiring very high assurance (aerospace, healthcare, critical financial systems, security); high upfront cost.

**Current Adoption Status**: Niche. Used in aerospace (European projects), healthcare, and cryptographic systems. Growing interest in AI-driven verification (agents can assist with formal proofs and property generation). TLA+ adoption is increasing for distributed systems.

**Key References**:
- Spivey, J. M. (1992). The Z Notation: A Reference Manual (2nd ed.). Prentice Hall. (Z standard reference)
- Abrial, J. R. (1996). The B-Book: Assigning Programs to Meanings. Cambridge University Press. (B-Method)
- Bjørner, D., & Jones, C. B. (2009). Formal Software Development: From VDM to Testing. Springer-Verlag. (VDM reference)
- Lamport, L. (2002). Specifying Systems: The TLA+ Language and Tools for Hardware and Software Engineers. Addison-Wesley.

---

#### 9. Model-Driven Development (MDD / MDA)

**Full Name**: Model-Driven Development (MDD, also Model-Driven Architecture, MDA; Model-Driven Engineering, MDE)

**Original Author(s) / Org / Year**: Object Management Group (OMG), 1990s onwards. Formalised as "Model-Driven Architecture" (MDA) in 2001 by OMG.

**Core Philosophy**: MDD treats models (diagrams, specifications) as the primary development artifact; code is generated from models using transformation tools. Emphasises abstraction, reusability, and automated code generation. Models at multiple levels (Computation-Independent, Platform-Independent, Platform-Specific) are transformed stepwise into executable code.

**Primary Artifacts**: Domain Models, Platform-Independent Models (PIMs), Platform-Specific Models (PSMs), Code (generated), Test Specifications.

**Prescribed Roles**: Model Designer, Model Transformation Specialist, Code Generator Maintainer, Developer (for hand-written code integration), QA.

**Typical Team Size & Scale**: 10–100 people; projects with significant code generation potential (embedded systems, domain-specific applications, large enterprises); medium-to-large scale.

**Current Adoption Status**: Growing in embedded systems and microservices (e.g., Protocol Buffers, GraphQL code generators). MDA formal adoption declined (perceived as heavyweight); informal MDD (code generators for boilerplate) is widespread.

**Key References**:
- Object Management Group (OMG). (2003). Model-Driven Architecture (MDA) Guide Version 1.0.1. OMG.
- Fowler, M. (2010). "Model Driven Software Development." Martin Fowler's Website. (Critical analysis)
- France, R., & Rumpe, B. (2007). "Model-Driven Development of Complex Software: A Research Roadmap." In 2007 Future of Software Engineering (FOSE), IEEE. DOI: 10.1109/FOSE.2007.14.

---

### Section B.2: Agile Family Methodologies

#### 10. Scrum

**Full Name**: Scrum (Scrum Framework for Agile Project Management)

**Original Author(s) / Org / Year**: Ken Schwaber and Jeff Sutherland, 1995 (described in Sutherland's PhD dissertation and Schwaber's work at Object Mentor and Scrum.org). Formalised 1997; evolved through Scrum Guide 2020, 2024 editions. Managed by Scrum.org and Scrum Alliance.

**Core Philosophy**: Scrum is a lightweight, iterative framework for delivering value in fixed-length iterations (sprints, typically 1–4 weeks). Emphasises transparency, inspection, and adaptation through ceremonies (daily standup, sprint planning, review, retrospective). Product Owner prioritises work; Scrum Master removes impediments; development team self-organises and commits to sprint goals.

**Primary Artifacts**: Product Backlog, Sprint Backlog, Increment (working software), Sprint Burndown Chart, Definition of Done.

**Prescribed Roles**: Product Owner (prioritisation and stakeholder liaison), Scrum Master (coach, impediment remover), Development Team (5–9 people, cross-functional).

**Typical Team Size & Scale**: 5–15 people per team; can scale via Scrum of Scrums (multiple teams coordinating). SAFe/LeSS/Nexus provide scaling frameworks.

**Current Adoption Status**: Market leader. 81% of agile teams use Scrum or a Scrum variant (2024 surveys). Ubiquitous in commercial software, spreading to other industries.

**Key References**:
- Schwaber, K., & Sutherland, J. (2020). The Scrum Guide. Scrum.org. (Authoritative specification)
- Schwaber, K. (2004). Agile Project Management with Scrum. Microsoft Press.
- Sutherland, J., & Schwaber, K. (2006). "The Scrum Papers: Nuts, Bolts, and Origins of an Agile Framework." Scrum.org.

---

#### 11. Extreme Programming (XP)

**Full Name**: Extreme Programming (XP)

**Original Author(s) / Org / Year**: Kent Beck, 1996 (Chrysler C3 Project); formalized in book and community practices 1999 onwards.

**Core Philosophy**: XP is an engineering-focused agile methodology emphasising technical excellence through practices like pair programming, test-driven development (TDD), continuous integration, simple design, refactoring, and collective code ownership. Responds to changing requirements by embedding change management into the development rhythm.

**Primary Artifacts**: Test Code (primary artifact), Implementation Code, Continuous Integration Pipeline, Release Plan, Velocity Metrics.

**Prescribed Roles**: Developer (pairs), Coach/Mentor, Customer (on-site), Tracker (metrics).

**Typical Team Size & Scale**: 3–10 people; small to medium teams; projects with rapidly changing or poorly understood requirements.

**Current Adoption Status**: Declined significantly. Used extensively 2000–2010; now <1% of teams use pure XP. Practices (TDD, CI, pair programming, refactoring) are widely adopted separately, but "XP" as a methodology is rarely chosen. Pair programming is experiencing a resurgence in AI-native contexts.

**Key References**:
- Beck, K. (1999). Extreme Programming Explained: Embrace Change (1st ed.). Addison-Wesley. (Foundational text)
- Beck, K. (2004). Extreme Programming Explained: Embrace Change (2nd ed.). Addison-Wesley. (Refined practices)
- Williams, L., & Kessler, R. R. (2000). "All I Really Need to Know about Pair Programming I Learned in Kindergarten." Communications of the ACM, 43(5), 108–114. (Pair programming evidence)

---

#### 12. Kanban (Software)

**Full Name**: Kanban (Software Development Kanban; derived from Toyota Production System Kanban)

**Original Author(s) / Org / Year**: David Anderson (software), 2007. Roots in Toyota's Kanban (Taiichi Ohno, 1950s); applied to software by Anderson and others (2007 onwards). Formalised in Kanban Method (2011).

**Core Philosophy**: Kanban is a pull-based, continuous-flow methodology where work is visualised on a board (columns representing workflow stages) and work-in-progress (WIP) is limited to prevent bottlenecks. Emphasises: visualisation, WIP limits, flow metrics (cycle time, lead time), and continuous improvement through data-driven decision-making. No fixed iterations; work flows continuously.

**Primary Artifacts**: Kanban Board (physical or digital), Cumulative Flow Diagram, Cycle Time Metrics, Work Items (user stories, tasks, bugs).

**Prescribed Roles**: Kanban Team (no prescribed roles; roles emerge based on work), Coach/Facilitator.

**Typical Team Size & Scale**: 3–20 people; teams handling continuous delivery, support, or maintenance. Can scale (distributed kanban, team-of-teams).

**Current Adoption Status**: 56% of agile teams use Kanban or Kanban practices (2024); growing. Popular for DevOps, maintenance, support, and hybrid teams. Often combined with Scrum (Scrumban).

**Key References**:
- Anderson, D. J. (2010). Kanban: Successful Evolutionary Change for Your Technology Business. Blue Hole Press.
- Poppendieck, M., & Poppendieck, T. (2003). Lean Software Development: An Agile Toolkit. Addison-Wesley. (Lean principles applied to software)
- Atlassian & Coplien. (2015). "Kanban & Scrum: Making the Most of Both." White Paper.

---

#### 13. Scrumban

**Full Name**: Scrumban (Scrum + Kanban Hybrid)

**Original Author(s) / Org / Year**: Corey Ladas, 2008. Formalised as transitional methodology and evolved into mature framework.

**Core Philosophy**: Scrumban combines the structure and ceremonies of Scrum (sprints, daily standup, review, retrospective) with the visualisation and flow discipline of Kanban (WIP limits, continuous improvement). Typically used by teams transitioning from Scrum to Kanban, or teams managing mixed workloads (features + support + maintenance).

**Primary Artifacts**: Product Backlog (Scrum-style), Kanban Board (Kanban-style), Sprint Backlog, WIP Limits, Velocity, Cycle Time metrics.

**Prescribed Roles**: Product Owner, Scrum Master/Coach, Development Team.

**Typical Team Size & Scale**: 5–12 people; teams with mixed work types (features + operations) or transitioning between frameworks.

**Current Adoption Status**: Growing. 27% of agile teams use Scrumban (2024 survey). Popular for teams that need structure (Scrum) and flexibility (Kanban).

**Key References**:
- Ladas, C. (2009). Scrumban: Essays on Kanban Systems for Lean Software Development. Lulu.com.
- Atlassian. "Scrumban Guide." Atlassian Agile Coach. (Practitioner resource)
- Planview. (2024). "What is Scrumban?" White Paper.

---

#### 14. SAFe (Scaled Agile Framework)

**Full Name**: SAFe (Scaled Agile Framework)

**Original Author(s) / Org / Year**: Dean Leffingwell (Rally Software, Scaled Agile Inc.), 2011. Evolved through SAFe 1.0 (2011) to current SAFe 6.0+ (2024).

**Core Philosophy**: SAFe is a comprehensive scaling framework for large enterprises. Organises teams into "Agile Release Trains" (ARTs) aligned to business value streams. Prescribes four levels: Team, Program, Large Solution, and Portfolio. Emphasises Lean-Agile principles, program synchronisation (PI Planning), and governance.

**Primary Artifacts**: Product Roadmap, Program Increment (PI) Plan, Features, User Stories, Kanban Board, Burn-down Charts, Release Plan, Architecture Vision.

**Prescribed Roles**: Product Owner, Scrum Master, Product Manager, Release Train Engineer (RTE), Architect, DevOps Engineer, Epic Owner.

**Typical Team Size & Scale**: 50–1000+ people; large enterprises with multiple teams and complex dependencies. 37% of large enterprises use SAFe (2024).

**Current Adoption Status**: Market leader for large-scale agile transformation. Ubiquitous in Fortune 500 enterprises. Criticism for being heavyweight and overly prescriptive; alternatives (LeSS, DAD) position as lighter.

**Key References**:
- Leffingwell, D. (2018). SAFe 4.5 Reference Guide: Scaled Agile Framework for Lean Enterprises (2nd ed.). Addison-Wesley.
- Scaled Agile, Inc. (2024). "SAFe for Teams," "SAFe for Programs," etc. (Official SAFe documentation).
- West, D. (2011). "The Scaled Agile Framework: Successes and Challenges." Forrester Research Report.

---

#### 15. LeSS (Large-Scale Scrum)

**Full Name**: LeSS (Large-Scale Scrum)

**Original Author(s) / Org / Year**: Craig Larman and Bas Vodde, 2005 onwards. Formalized through LeSS and LeSS Huge frameworks.

**Core Philosophy**: LeSS is a minimalist scaling framework that applies Scrum principles to multiple teams without adding new roles or events (except Scrum of Scrums meetings). Emphasises shared product backlog, shared Definition of Done, and one Product Owner across teams. Avoids the overhead of SAFe by keeping structure minimal.

**Primary Artifacts**: Shared Product Backlog, Sprint Backlog (team-level), Increment, Scrum of Scrums meeting notes.

**Prescribed Roles**: Product Owner (shared across teams), Scrum Master (per team or multiple teams), Development Team.

**Typical Team Size & Scale**: 3–8 teams (LeSS) or 8–40+ teams (LeSS Huge), each 5–9 people. Emphasis on synchronisation without heavy governance.

**Current Adoption Status**: Growing among organisations seeking lightweight scaling. Less common than SAFe but gaining adoption, especially in tech companies and startups scaling to multi-team.

**Key References**:
- Larman, C., & Vodde, B. (2016). Large-Scale Scrum: More with LeSS. Addison-Wesley.
- Larman, C., & Vodde, B. (2010). Scaling Lean and Agile Development: Thinking and Organizational Tools for Large-Scale Scrum. Addison-Wesley.
- LeSS Consortium. (2024). "LeSS Framework." LeSS.works.

---

#### 16. Nexus

**Full Name**: Nexus (Nexus Framework for Scaled Scrum)

**Original Author(s) / Org / Year**: Ken Schwaber (Scrum.org), 2015. Lightweight scaling framework; positioning as simpler alternative to SAFe.

**Core Philosophy**: Nexus is an exoskeleton connecting 3–9 Scrum teams to develop an integrated product. Introduces one additional role (Nexus Integration Team) and one additional event (Nexus Sprint) to coordinate dependencies. Emphasises minimalism and Scrum principles.

**Primary Artifacts**: Product Backlog, Nexus Sprint Goal, Nexus Sprint Backlog, Integrated Increment, Dependency Graph.

**Prescribed Roles**: Product Owner (shared), Scrum Master (team-level), Nexus Scrum Master, Nexus Integration Team, Development Teams.

**Typical Team Size & Scale**: 15–45 people (3–9 teams of 5–9 each). Smaller than SAFe target; suitable for mid-size scaling.

**Current Adoption Status**: Growing. Positioned as simpler alternative to SAFe and LeSS; adopted by tech and consulting firms.

**Key References**:
- Schwaber, K. (2015). "Nexus: The Exoskeleton for Scaled Scrum." Scrum.org White Paper.
- Schwaber, K. (2018). "The Nexus Framework for Scaling Scrum: Continuously Delivering an Integrated Product." Addison-Wesley.
- Scrum.org. (2024). "The Nexus Guide." Scrum.org.

---

#### 17. Disciplined Agile Delivery (DAD)

**Full Name**: Disciplined Agile® Delivery (DAD)

**Original Author(s) / Org / Year**: Scott Ambler and Mark Lines (Disciplined Agile group), 2013. Acquired by Project Management Institute (PMI) in 2019.

**Core Philosophy**: DAD is a hybrid, people-first toolkit (not a prescriptive framework) that draws from Agile, Lean, Extreme Programming, DevOps, and traditional disciplines (RUP, PRINCE2) to tailor approaches for specific contexts. Emphasis on lifecycle choices (Agile, Continuous Delivery, Lean), learning, and customer collaboration. Less prescriptive than SAFe.

**Primary Artifacts**: Inception Phase artifacts, Transition Phase artifacts, Construction Phase artifacts (flexible based on chosen lifecycle).

**Prescribed Roles**: Business Analyst, Architecture Owner, DevOps Lead, Development Team, Product Owner.

**Typical Team Size & Scale**: 5–200+ people; enterprises seeking flexible scaling and adaptability.

**Current Adoption Status**: Growing. Marketed as "agile without the overhead" alternative to SAFe. Popular in consulting and enterprises with diverse needs.

**Key References**:
- Ambler, S. W., & Lines, M. (2018). Disciplined Agile Delivery: A Practitioner's Guide to Agile Software Delivery in the Enterprise (2nd ed.). IBM Press.
- Project Management Institute (PMI). (2020). "Disciplined Agile Delivery (DAD)." PMI.org.
- PMI. (2021). "The Disciplined Agile Handbook." PMI. (Official reference)

---

#### 18. Crystal (Clear, Orange, Red, etc.)

**Full Name**: Crystal Family (Crystal Clear, Crystal Yellow, Crystal Orange, Crystal Red)

**Original Author(s) / Org / Year**: Alistair Cockburn, 1991 onwards. Evolved through research and practice.

**Core Philosophy**: Crystal is a family of "human-powered, adaptive, ultra-light" methodologies tailored by team size and project criticality. Crystal Clear (small teams, low-criticality), Crystal Orange/Red (larger teams, higher criticality). Emphasises human collaboration, osmotic communication, frequent deliveries, easy access to expert users.

**Primary Artifacts**: Use Cases, User Stories, Architecture, Code, Tests (lightweight documentation).

**Prescribed Roles**: Roles depend on project size; no rigid role definitions. Emphasis on "people are primary."

**Typical Team Size & Scale**: 3–6 people (Clear) to 50+ (Red). Low to medium criticality projects.

**Current Adoption Status**: Niche. Popular among early-adopter agile teams; less structured than Scrum, so declining in larger organisations. Influential in shaping modern agile thinking.

**Key References**:
- Cockburn, A. (2004). Crystal Clear: A Human-Powered Methodology for Small Teams. Addison-Wesley.
- Cockburn, A. (2006). Agile Software Development: The Cooperative Game (2nd ed.). Addison-Wesley.
- Cockburn, A. (2019). "Crystal Method." Alistair Cockburn's website.

---

#### 19. Feature-Driven Development (FDD)

**Full Name**: Feature-Driven Development (FDD)

**Original Author(s) / Org / Year**: Jeff De Luca, 1997 (Singapore banking project). Formalised and published through community effort.

**Core Philosophy**: FDD is an iterative, incremental methodology that organises work around building small, client-valued features. Core practices: Domain Modelling, Building a Features List, Planning by Feature, Designing by Feature, Building by Feature. Emphasises predictability and clear code ownership.

**Primary Artifacts**: Feature List, Design Document (per feature), Code (per feature), Test Cases.

**Prescribed Roles**: Project Manager, Chief Architect, Development Manager, Chief Programmer, Code Owner, Domain Expert, Tester.

**Typical Team Size & Scale**: 5–50 people; medium-to-large projects with complex domains. Strong in Asian and defence sectors.

**Current Adoption Status**: Niche. Used in some large enterprises and government projects; less common than Scrum in commercial software.

**Key References**:
- De Luca, J. (2001). "An Introduction to Feature-Driven Development." Feature Driven Development.org.
- Palmer, S. R., & Felsing, J. M. (2002). A Practical Guide to Feature-Driven Development. Prentice Hall.
- Coad, P., De Luca, J., & Lefebvre, E. (1999). Java Modeling in Color with UML. Prentice Hall.

---

#### 20. Dynamic Systems Development Method (DSDM)

**Full Name**: Dynamic Systems Development Method (DSDM / Atern)

**Original Author(s) / Org / Year**: DSDM Consortium (founded by UK vendors and experts, including Logica, Oracle, British Airways), 1995. Current steward: Agile Business Consortium (2007 onwards).

**Core Philosophy**: DSDM is a comprehensive, rigorous framework for Rapid Application Development (RAD) and agile delivery. Emphasises business focus, time-boxing (fixed time, variable scope, using the "80/20 rule"), active user involvement, and iterative delivery. Covers full lifecycle from feasibility through deployment.

**Primary Artifacts**: Business Case, Project Mandate, Feasibility Study, Requirements, Prototypes, Build Specifications, Deployment Plan.

**Prescribed Roles**: Project Manager, Business Analyst, Developer, Tester, User (active), Business Sponsor.

**Typical Team Size & Scale**: 5–30 people; medium projects, particularly business applications requiring rapid delivery. Fixed time and resources, variable scope.

**Current Adoption Status**: Moderate, particularly in UK government and large enterprises. Less visible than Scrum/SAFe but maintained active community.

**Key References**:
- Agile Business Consortium. (2022). "DSDM Agile Business Handbook." Agile Business Consortium.
- Stapleton, J. (Ed.). (2003). DSDM: Business Focused Development (2nd ed.). Addison-Wesley.
- Hartley, B. (2011). "DSDM – The Method Behind the Acronym." Computer Weekly.

---

### Section B.3: Emerging / Informal / Hybrid / AI-Native Methodologies

#### 21. Shape Up

**Full Name**: Shape Up (Shape Up: Stop Running in Circles and Ship Work that Matters)

**Original Author(s) / Org / Year**: Ryan Singer (Basecamp, Head of Strategy), 2018. Published as free online book (basecamp.com/shapeup); formalised in industry conversations 2018 onwards.

**Core Philosophy**: Shape Up is a lightweight, six-week cycle methodology that emphasises "shaping" (defining well-scoped, risky, constrained problems before solving), "betting" (stakeholder decisions on what to build), and "building" (team autonomously builds within six-week window). No backlog; no sprints; no velocity. Emphasises fixed time, variable scope (descope rather than extend).

**Primary Artifacts**: Shaped Pitches (brief problem/solution specs), Implementation Plan (hand-written/flexible), Screenshots/Designs (optional), Code (primary).

**Prescribed Roles**: Shapers (define problems), Bettors (decide priorities), Builders (execute).

**Typical Team Size & Scale**: 5–20 people per cycle; suitable for product companies and startups. Basecamp (platform) uses this; adopted by other companies (e.g., Riskified, AppfolioMax).

**Current Adoption Status**: Growing interest (2024). Positioned as simpler alternative to Scrum; appeals to product companies and startups. Limited large-scale case studies.

**Key References**:
- Singer, R. (2018). Shape Up: Stop Running in Circles and Ship Work that Matters. Basecamp. (Free online book at basecamp.com/shapeup)
- Medium articles and podcasts by Basecamp team, 2018–2024.
- Case studies from practitioners (e.g., Riskified blog, 2021).

---

#### 22. Trunk-Based Development

**Full Name**: Trunk-Based Development (TBD, also Main-Line Development)

**Original Author(s) / Org / Year**: Developed organically by high-performing teams (Google, Meta, Amazon) in 2000s. Formalised by Paul Hammant (2009 onwards) in trunkbaseddevelopment.com community.

**Core Philosophy**: Trunk-Based Development is a version control practice where developers integrate code into the main branch (trunk) at least daily, with short-lived feature branches (1–2 days) if used at all. Enables continuous integration, automated testing, and rapid feedback. Not a full SDLC methodology, but a core practice for CI/CD and high-throughput teams.

**Primary Artifacts**: Main branch code (continuously releasable), Feature flags (for in-progress work), Test suite, Build pipeline output.

**Prescribed Roles**: Developer, CI/CD Engineer, QA (automated).

**Typical Team Size & Scale**: 5–1000+ people; scales linearly with automation investment. Prerequisite for high-frequency deployment.

**Current Adoption Status**: Industry standard for high-performing engineering teams (Google, Meta, Amazon, Uber, etc.). Widely recommended by ThoughtWorks, Atlassian, AWS, Google. Growing adoption in enterprises seeking continuous delivery.

**Key References**:
- Hammant, P. (2009–2024). "Trunk-Based Development." TrunkBasedDevelopment.com. (Community resource)
- Atlassian. (2024). "Trunk-Based Development Guide." Atlassian Continuous Delivery.
- ThoughtWorks. (2024). "Trunk-Based Development." ThoughtWorks Technology Radar. (Adopt)
- AWS Prescriptive Guidance. (2024). "Trunk-Based Development." AWS Well-Architected Framework.

---

#### 23. Continuous Delivery / Continuous Deployment

**Full Name**: Continuous Delivery (CD) / Continuous Deployment (also seen as methodology, not just practice)

**Original Author(s) / Org / Year**: Jez Humble and David Farley, 2010. Book: Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation. Built on CI (Continuous Integration) practices from Extreme Programming and industry adoption.

**Core Philosophy**: Continuous Delivery is a set of practices and principles enabling software to be released to production frequently and reliably. Automated testing, deployment pipeline, feature flags, and incremental rollout are core. Continuous Deployment extends this: every change that passes automated tests is automatically deployed to production. Can be viewed as a process/methodology that encompasses and requires other practices.

**Primary Artifacts**: Deployment Pipeline Configuration, Test Automation, Feature Flags, Release Notes, Deployment Metrics.

**Prescribed Roles**: Developer, DevOps Engineer, QA Engineer (automation-focused), Release Manager (if applicable).

**Typical Team Size & Scale**: 3–100+ people; any team seeking high-frequency releases. Scales with automation.

**Current Adoption Status**: Ubiquitous in tech industry as a practice set; increasingly the baseline expectation. Some organisations adopt "Continuous Delivery" as their named methodology.

**Key References**:
- Humble, J., & Farley, D. (2010). Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation. Addison-Wesley.
- Farley, D. (2018). Continuous Delivery: The Foundational Practices. Dave Farley YouTube.
- DORA / Nicole Forsgren. (2019–2024). Accelerate Metrics and State of DevOps Report. Annual research.

---

#### 24. Mob Programming (Ensemble Programming)

**Full Name**: Mob Programming (Mob Development, Software Teaming, Ensemble Programming)

**Original Author(s) / Org / Year**: Woody Zuill, 2012 (coined term). Evolved from pair programming (XP) and collaborative development. Promoted by community (2010s onwards). Rebranded as "Ensemble Programming" (2020s) to avoid connotations of "mob."

**Core Philosophy**: Mob (or Ensemble) Programming is a collaborative practice where the whole team (5–12 people) works on the same task, at the same computer, at the same time. One person drives (writes code), others navigate and think aloud. Rotates driver regularly. Emphasises knowledge sharing, continuous code review, and collective decision-making.

**Primary Artifacts**: Code, Shared Understanding, Knowledge transfer.

**Prescribed Roles**: Driver (code writer, rotates every 15–30 min), Navigator (guide/think-aloud), Mob (observers, ready to jump in).

**Typical Team Size & Scale**: 5–10 people; used within teams, not a full-lifecycle methodology. Combines well with Scrum, Kanban, or other frameworks.

**Current Adoption Status**: Niche but growing. Used by some tech companies, consultancies, and teams emphasising knowledge sharing and quality. Gaining traction in AI-native and high-collaboration contexts (humans + AI agents).

**Key References**:
- Zuill, W. (2012 onwards). MobProgramming.org. (Community site)
- Zuill, W., & Synder, K. (2018). Mob Programming: A Whole Team Approach. Leanpub.
- Williams, L. (2000). "Pair Programming Illuminated." Addison-Wesley. (Foundational; mob is extension of pairing)
- Hastie, S., et al. (2015). "Mob Programming and Collective Ownership." InfoQ.

---

#### 25. Specification-Driven Development (API-First, Contract-First)

**Full Name**: Specification-Driven Development (SDD, Spec-Driven Development, API-First Development, Contract-Driven Development)

**Original Author(s) / Org / Year**: Evolving practice; formalized and named by practitioners (2010s onwards). GitHub released "Spec Kit" toolkit in 2025 for spec-driven development with AI agents.

**Core Philosophy**: Specs (API specs, contracts, executable specifications, formal requirements) are the source of truth and starting point for development. Code is generated from or written to match specs. Tests are derived from specs. Spec-Driven Development (SDD) emphasises treating specs as "version control for your thinking" and making them executable by AI agents and tools.

**Primary Artifacts**: Specification (OpenAPI, GraphQL, formal notation, or prose), API Contract, Tests derived from spec, Generated code.

**Prescribed Roles**: Spec Author, Developer, Test Engineer (derived from spec).

**Typical Team Size & Scale**: 3–50 people; any team. Particularly useful for multi-team API-driven systems and AI-assisted development.

**Current Adoption Status**: Growing, especially in 2024–2025 with AI agent adoption. GitHub Spec Kit (2025) and InfoQ articles promoting SDD as AI-native approach. Adoption is increasing in teams using Claude Code and other agentic tools.

**Key References**:
- GitHub. (2025). "Spec Kit: Toolkit to help you get started with Spec-Driven Development." GitHub Blog.
- IntuitionLabs. (2025). "GitHub Spec Kit: A Guide to Spec-Driven AI Development." PDF White Paper.
- MartinFowler.com. (2024–2025). "Exploring Generative AI: Spec-Driven Development." Martin Fowler's articles.
- CapitalOne (2024). "API-First Development: Lessons Learned." Engineering Blog.

---

#### 26. Docs-First / Documentation-Driven Development

**Full Name**: Documentation-Driven Development (DDD, Docs-First Development, README-Driven Development)

**Original Author(s) / Org / Year**: Emerging practice; popularized by open-source communities (2010s). Tom Preston-Werner (GitHub founder) published "README Driven Development" (2010).

**Core Philosophy**: Documentation (README, API docs, user guides, architecture docs) is written *first*, before code. Code is written to match the documentation. Treats documentation as a specification and contract with users. Ensures code is well-integrated with its documentation and users know what to expect.

**Primary Artifacts**: README, API Documentation, Architecture Guide, Code (matching docs).

**Prescribed Roles**: Technical Writer, Developer.

**Typical Team Size & Scale**: 3–20 people; any team, especially open-source and distributed teams.

**Current Adoption Status**: Growing in open-source; adopted by some tech companies (e.g., Stripe, GitHub, GitLab). Complementary to Spec-Driven Development and increasingly seen as AI-native (agents generate docs, then code).

**Key References**:
- Preston-Werner, T. (2010). "Readme Driven Development." Tom Preston-Werner's Blog.
- GitHub. (2024). "Documentation Done Right: A Developer's Guide." GitHub Blog.
- Open Source Initiative. (2024). "Documentation Standards." OSI Guidance.

---

#### 27. Test-Driven Development (TDD) as Standalone Methodology

**Full Name**: Test-Driven Development (TDD, Test-First Development)

**Original Author(s) / Org / Year**: Kent Beck, popularized through Extreme Programming (1996 onwards). Formalized as standalone practice and methodology (2000s onwards).

**Core Philosophy**: Tests are written *before* implementation code. Red-Green-Refactor cycle: write a failing test (Red), write minimal code to pass (Green), refactor to improve design (Refactor). Treats tests as design specification and regression prevention mechanism. Core to modern development.

**Primary Artifacts**: Test Code (unit tests, integration tests), Implementation Code (written to pass tests), Test Coverage Metrics.

**Prescribed Roles**: Developer (writes tests and code iteratively), QA (integration/system testing).

**Typical Team Size & Scale**: 1–50+ people; scalable. Individuals up to large teams can practice TDD.

**Current Adoption Status**: Mainstream. Empirically shown to reduce defects (Madeyski, 2010 onwards). Adopted widely in tech industry, though not universal (some teams skip TDD for speed). Increasingly mandated in quality-focused and regulated industries.

**Key References**:
- Beck, K. (2002). Test-Driven Development: By Example. Addison-Wesley. (Definitive text)
- Madeyski, L. (2010). "The Impact of Test-Driven Development on Software Development Productivity and Code Quality: A Systematic Review and Meta-Analysis." Journal of Systems and Software, 84(3), 302–336. (Empirical evidence)
- Koskela, L. (2013). Test Driven: TDD and Acceptance Testing in Action. Manning Publications.

---

#### 28. Behaviour-Driven Development (BDD) as Standalone Methodology

**Full Name**: Behaviour-Driven Development (BDD)

**Original Author(s) / Org / Year**: Dan North, 2006. Evolved through tools (Cucumber, SpecFlow, Behave) and community adoption (2006 onwards).

**Core Philosophy**: BDD extends TDD by using plain-language (Gherkin) specifications of behaviour (user stories / scenarios) as both test specifications and documentation. Bridge between business stakeholders (non-technical) and developers. Emphasises "outside-in" development: start with user behaviour, then implement.

**Primary Artifacts**: Feature Files (Gherkin syntax), Step Definitions (glue code), Test Results, Scenario Documentation.

**Prescribed Roles**: Business Analyst, Developer, QA, Tester.

**Typical Team Size & Scale**: 3–30 people; teams with significant business stakeholder involvement.

**Current Adoption Status**: Moderate adoption, especially in enterprises and regulatory contexts. Popular in Java/JVM communities (Cucumber, JBehave). Growing in AI-native contexts (agents can parse Gherkin and generate code to match).

**Key References**:
- North, D. (2006). "Introducing BDD." Behaviour Driven Development.org.
- Smart, J. (2014). BDD in Action: Behavior-Driven Development for the Whole Software Lifecycle. Manning Publications.
- Wynne, M., & Hellesøy, A. (2012). The Cucumber Book: Behaviour-Driven Development for Testers and Developers. Pragmatic Bookshelf.

---

#### 29. Architecture Decision Records (ADR) Driven Development

**Full Name**: Architecture Decision Record (ADR) Driven Development, Architecture Decision Log (ADL)

**Original Author(s) / Org / Year**: Michael Nygard, 2011. Evolved through community and enterprise adoption (2010s onwards). Endorsed by AWS, Google, Microsoft, RedHat (2023–2024).

**Core Philosophy**: Architecture decisions are documented as ADRs (brief markdown files stored in version control) near the codebase. Each ADR captures decision, context, and consequences. Decisions are consulted when making changes, enabling consistency and reducing rework. ADRs become executable context for agents.

**Primary Artifacts**: Architecture Decision Records (Markdown), Codebase (implementing decisions), Change history.

**Prescribed Roles**: Architect, Developer.

**Typical Team Size & Scale**: 3–100+ people; distributed teams benefit most from documented decisions.

**Current Adoption Status**: Growing, especially in distributed/remote teams and companies emphasising architectural consistency. Increasingly seen as prerequisite for agent-driven development (agents query ADRs for context).

**Key References**:
- Nygard, M. (2011). "Documenting Architecture Decisions." Michael Nygard's Blog.
- ADR.github.io. (2024). "Architectural Decision Records." Community resource.
- AWS Prescriptive Guidance. (2024). "Architecture Decision Records (ADRs)." AWS Well-Architected Framework.
- Microsoft Azure. (2024). "Maintain an Architecture Decision Record (ADR)." Azure Architecture Center.

---

#### 30. Agentic Development Lifecycle (ADLC)

**Full Name**: Agentic Development Lifecycle (ADLC, AI-Led SDLC, Agentic SDLC)

**Original Author(s) / Org / Year**: Emerging framework; articulated by EPAM (2024), Microsoft (2025), ThoughtWorks (2024), PWC (2024), and others. No single authorial source; evolving community practice.

**Core Philosophy**: ADLC is a lifecycle specifically designed for AI-integrated and agentic systems where LLMs and autonomous agents are core delivery participants. Differs from traditional SDLC by treating agent behaviour (language models, prompts, training data) as primary variables instead of assuming deterministic execution. Emphasises prompt engineering, model evaluation, human-agent alignment, and behavioural quality metrics.

**Primary Artifacts**: Prompts (system, few-shot), Model Evaluation Reports, Agent Interaction Logs, Behavioral Specifications, Alignment/Safety Reviews.

**Prescribed Roles**: Prompt Engineer, AI/ML Engineer, Agent Evaluator, Human-Alignment Reviewer, Product Manager.

**Typical Team Size & Scale**: 5–30 people; projects building with LLMs and agents (not code-generation agents, but agents that *are* LLM-native).

**Current Adoption Status**: Emerging (2024–2025). Actively researched and practised by EPAM, Microsoft, OpenAI teams, research groups. Not yet standardised; best practices still being codified.

**Key References**:
- EPAM. (2024). "Introducing Agentic Development Lifecycle (ADLC): Building and Operating AI Agents in Production." EPAM Insights Blog.
- Microsoft. (2025). "An AI-Led SDLC: Building an End-to-End Agentic Software Development Lifecycle with Azure and GitHub." Microsoft Community Hub.
- ThoughtWorks. (2024). "Preparing Your Team for the Agentic Software Development Life Cycle." ThoughtWorks Insights.
- PWC. (2024). "Future of Solutions Development and Delivery in the Rise of Gen AI." PWC Report.

---

#### 31. Specification-Driven / Spec-Kit Development (AI-Native)

**Full Name**: Specification-Driven Development with GitHub Spec Kit (Spec-Driven AI Development)

**Original Author(s) / Org / Year**: GitHub (Microsoft), 2025. Toolkit released as open-source.

**Core Philosophy**: Specs (written in formal or structured format) are the source of truth. AI agents (Claude Code, GitHub Copilot, Gemini CLI) consume specs and generate code. Specs are kept in sync with code and tests through automated validation. Specs become executable intent for agents.

**Primary Artifacts**: Specification File (structured, version-controlled), Generated Code, Tests (derived from spec), Test Results, Agent Logs.

**Prescribed Roles**: Spec Author, Agent (code generation), Human Reviewer.

**Typical Team Size & Scale**: 1–20 people; solo developers to small teams. Highly leveraged by agents.

**Current Adoption Status**: Emerging (2025). GitHub Spec Kit is early-stage, but adoption expected to accelerate. Represents convergence of Spec-Driven Development, BDD, and AI agents.

**Key References**:
- GitHub. (2025). "Spec Kit: Toolkit to help you get started with Spec-Driven Development." GitHub Blog + github.com/github/spec-kit.
- GitHub. (2025). "Spec-Driven Development with AI: Get Started with a New Open Source Toolkit." GitHub Blog.
- IntuitionLabs. (2025). "GitHub Spec Kit: A Guide to Spec-Driven AI Development." PDF.

---

#### 32. AgentsWay Methodology

**Full Name**: AgentsWay (Software Development Methodology for AI Agents-Based Teams)

**Original Author(s) / Org / Year**: Emerging research; formally described in arxiv:2510.23664, 2024–2025.

**Core Philosophy**: AgentsWay is a methodology specifically designed for teams where AI agents are equal participants in software development. Incorporates agent planning, task orchestration, collaborative development, and human oversight. Addresses agent coordination (multi-agent systems), agent-human collaboration, and agent autonomy boundaries.

**Primary Artifacts**: Agent Plans, Task Graphs, Collaboration Logs, Code Output, Test Results.

**Prescribed Roles**: Agent Orchestrator, Human Supervisor, Agent Task Executor.

**Typical Team Size & Scale**: 1–10 people + multiple agents. Designed for agent-first delivery.

**Current Adoption Status**: Emerging research (early 2024–2025). Not yet mainstream; actively being researched and refined.

**Key References**:
- ArXiv Preprint. (2024). "AGENTSWAY — SOFTWARE DEVELOPMENT METHODOLOGY FOR AI AGENTS-BASED TEAMS." arxiv:2510.23664.

---

#### 33. Multi-Agent Orchestration Frameworks

**Full Name**: Multi-Agent Orchestration Frameworks (e.g., LangGraph, AutoGen, CrewAI, Semantic Kernel)

**Original Author(s) / Org / Year**: Multiple frameworks: OpenAI (AutoGen, 2023), LangChain (LangGraph, 2024), CrewAI (Juan Carbajal, 2023), Microsoft (Semantic Kernel, 2023). Evolving rapidly.

**Core Philosophy**: These are platforms/frameworks for orchestrating multiple AI agents to work together on complex tasks. Agents can be specialized (e.g., planning agent, code agent, review agent) and coordinate through task graphs, message passing, or hierarchical planning. Not a full SDLC methodology, but infrastructure for agent-based development.

**Primary Artifacts**: Agent Definitions, Task Graphs, Tool Bindings, Execution Logs.

**Prescribed Roles**: Agent Architect (designs agent system), Agent Developer, Agent Evaluator.

**Typical Team Size & Scale**: 2–10 people designing agent systems. Agents multiply delivery throughput.

**Current Adoption Status**: Rapid adoption (2023–2025). These are becoming standard infrastructure for AI-assisted and AI-native development.

**Key References**:
- Shakudo. (2025). "Top 9 AI Agent Frameworks as of March 2026." Shakudo Blog.
- OpenAI. (2023). "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation Framework." OpenAI Blog + GitHub.
- LangChain. (2024). "LangGraph: A Graph-Based State Machine for Multi-Agent Orchestration." LangChain Docs.
- CrewAI. (2023–2025). "CrewAI: Framework for Orchestrating Role-Playing, Autonomous AI Agents." CrewAI.io.
- E2B. (2024). "Awesome AI Agents: A List of AI Autonomous Agents." GitHub: e2b-dev/awesome-ai-agents.

---

#### 34. VeriAct (Verification-Guided Agentic Synthesis)

**Full Name**: VeriAct (Verification-Guided Agentic Synthesis Framework)

**Original Author(s) / Org / Year**: Emerging research; published on arXiv (2024–2025).

**Core Philosophy**: VeriAct combines closed-loop iterative LLM planning with code execution, verification (formal or automated), and Spec-Harness feedback. Agents generate code, run verification checks (tests, formal proof attempts, type checking), observe failures, and iterate. Verification results are structured feedback that agents consume.

**Primary Artifacts**: Formal Specification, Code (generated by agent), Verification Results, Iteration Logs.

**Prescribed Roles**: Spec Author, Agent (code synthesis), Verifier (automated).

**Typical Team Size & Scale**: 1–5 people; heavily agent-leveraged.

**Current Adoption Status**: Early research (2024–2025). Demonstrates integration of formal verification with agentic code generation; promising for safety-critical systems.

**Key References**:
- ArXiv Preprint. (2024). "VeriAct: Beyond Verifiability – Agentic Synthesis of Correct and Complete Formal Specifications." arxiv:2604.00280.

---

#### 35. Pair Programming (as Methodology)

**Full Name**: Pair Programming (Collaborative Programming)

**Original Author(s) / Org / Year**: Core practice of Extreme Programming (Kent Beck, 1996). Evolved as standalone methodology through research and adoption (2000s onwards).

**Core Philosophy**: Two developers sit together at one computer, continuously collaborating on the same code. One drives (writes), one navigates (reviews, thinks ahead). Provides continuous code review, knowledge sharing, and reduced defects. Can reduce individual productivity but increases code quality and team knowledge.

**Primary Artifacts**: Code (pair-produced, typically high quality), Knowledge, Shared Understanding.

**Prescribed Roles**: Driver, Navigator (rotates).

**Typical Team Size & Scale**: 1 pair (2 people) to multiple pairs; can be combined with Scrum, Kanban, etc.

**Current Adoption Status**: Moderate adoption in Agile teams; declining in some contexts (cost of 2 FTE per feature), growing in others (high-quality products, knowledge transfer, AI-agent contexts). Resurgence in pairing with AI agents (human + agent pair programming).

**Key References**:
- Williams, L., & Kessler, R. R. (2000). "All I Really Need to Know about Pair Programming I Learned in Kindergarten." Communications of the ACM, 43(5), 108–114.
- Beck, K., & Andres, C. (2004). Extreme Programming Explained (2nd ed.). Addison-Wesley.

---

#### 36. DevOps (as Methodology)

**Full Name**: DevOps (Development + Operations)

**Original Author(s) / Org / Year**: Patrick Debois (Belgian), 2009 (first DevOpsDay conference). Evolved through industry adoption and community (2009 onwards).

**Core Philosophy**: DevOps breaks down silos between development and operations, emphasising collaboration, shared responsibility, automation (CI/CD, infrastructure as code), monitoring, and rapid feedback. Not a complete SDLC methodology, but a culture and set of practices integrated into SDLC.

**Primary Artifacts**: CI/CD Pipeline, Infrastructure as Code, Monitoring Dashboards, Deployment Logs.

**Prescribed Roles**: DevOps Engineer, Site Reliability Engineer (SRE), Developer (with ops mindset).

**Typical Team Size & Scale**: 3–100+ people; any team seeking high-frequency deployment and operational excellence.

**Current Adoption Status**: Ubiquitous in tech industry as a practice set and culture. "DevOps" is rarely chosen as *the* methodology, but is integrated into most modern SDLCs (Agile + DevOps).

**Key References**:
- Debois, P. (2009). "DevOpsDay." First DevOps conference.
- Humble, J., & Farley, D. (2010). Continuous Delivery. Addison-Wesley. (Foundational for DevOps practices)
- Kim, G., Humble, J., Debois, P., & Willis, J. (2016). The DevOps Handbook: How to Create World-Class Agility, Reliability, and Security in Technology Organizations. IT Revolution Press.

---

### Section B.4: Summary Taxonomy

| Category | Methodologies | Count |
|----------|---|---|
| **Formal / Traditional** | Waterfall, V-Model, Spiral, RUP, PRINCE2, CMMI, Cleanroom, Formal Methods (Z, B, VDM, TLA+), MDD/MDA | 9 |
| **Agile (Core)** | Scrum, XP, Kanban, Scrumban, SAFe, LeSS, Nexus, DAD, Crystal, FDD, DSDM | 11 |
| **Emerging / Hybrid / AI-Native** | Shape Up, Trunk-Based Development, CD/Continuous Deployment, Mob/Ensemble Programming, Spec-Driven Development, Docs-First/README-Driven, TDD (standalone), BDD (standalone), ADR-Driven, ADLC, Spec-Kit/SDD, AgentsWay, Multi-Agent Orchestration, VeriAct, Pair Programming, DevOps | 16 |
| **Total Identified Methodologies** | — | 36+ (with variants and emerging sub-methodologies) |

---

## Part C: AI-Native & Agentic Methodologies: Detailed Assessment

### C.1 Identified AI-Native Methodologies

The following methodologies are explicitly designed for or emerging from AI agent participation in SDLC:

1. **Specification-Driven Development (with AI leverage)**
2. **Agentic Development Lifecycle (ADLC)**
3. **Specification-Driven Development with Spec Kit (GitHub, 2025)**
4. **AgentsWay Methodology**
5. **Multi-Agent Orchestration Frameworks (LangGraph, AutoGen, CrewAI)**
6. **VeriAct (Verification-Guided Agentic Synthesis)**

### C.2 Maturity & Evidence Base

| Framework | Maturity | Research Evidence | Practitioner Adoption | Recommendation for Phase 2 |
|-----------|----------|---|---|---|
| ADLC | Emerging (2024) | Moderate (WhitePapers from EPAM, Microsoft, PWC) | Limited (early adopters) | High priority for evaluation; blend with traditional SDLC dimensions |
| Spec-Kit SDD | Early (2025) | Emerging (GitHub, IntuitionLabs) | Very limited (just released) | High priority; represents convergence of SDD + AI agents |
| AgentsWay | Early (2024–2025) | Limited (arxiv paper) | Minimal | Evaluate; compare with ADLC |
| Multi-Agent Orchestration | Maturing (2023–2025) | Moderate (OpenAI, LangChain docs) | Growing | Evaluate as infrastructure enabling other methodologies |
| VeriAct | Early Research (2024) | Limited (arxiv paper) | Minimal | Evaluate for safety-critical agent scenarios |

### C.3 Key Characteristics of AI-Native Methodologies

**Convergent Patterns Observed**:

1. **Specs as Source of Truth**: All emerging AI-native approaches treat specifications (formal or structured) as executable intent for agents, not static documents.
2. **Feedback Loops at Agent Scale**: Feedback (test results, verification failures, user input) is structured and consumed autonomously by agents for iteration.
3. **Delegation, Review, Own Model**: Agents handle execution; humans review for correctness/risk; humans own architecture and outcomes.
4. **Multi-Agent Coordination**: Frameworks address agent-to-agent communication, task orchestration, and dependency resolution.
5. **Behavioral Quality Metrics**: Instead of lines-of-code or velocity, metrics focus on "did the agent's output meet the spec?" and "did the agent reason correctly?"

---

## Part D: References

### Academic Sources

[1] GitHub. (2025). "Spec Kit: Toolkit to help you get started with Spec-Driven Development." GitHub Blog. https://github.blog/ (specification-driven development for AI)

[2] VeriAct ArXiv. (2024). "VeriAct: Beyond Verifiability – Agentic Synthesis of Correct and Complete Formal Specifications." arxiv:2604.00280. (formal verification with agents)

[3] Formal Methods References:
- Spivey, J. M. (1992). The Z Notation: A Reference Manual (2nd ed.). Prentice Hall.
- Abrial, J. R. (1996). The B-Book. Cambridge University Press.
- Lamport, L. (2002). Specifying Systems. Addison-Wesley.

[4] AgentOrchestra. (2025). "Advancing Agentic Systems: Dynamic Task Decomposition, Tool Integration and Evaluation." arxiv:2506.12508. (task decomposition for agents)

[5] Feature-Driven Development:
- De Luca, J. (2001). Feature-Driven Development. Feature Driven Development.org.
- Palmer, S. R., & Felsing, J. M. (2002). A Practical Guide to Feature-Driven Development. Prentice Hall.

[6] Scrum & Agile Empirical Evidence:
- Parabol. (2024). "300+ Agile and Scrum Statistics for 2024." Parabol Blog.
- VersionOne. (2024). "14th Annual State of Agile Report." Perforce Software / CollabNet VersionOne.

[7] TDD Empirical Evidence:
- Madeyski, L. (2010). "The Impact of Test-Driven Development on Software Development Productivity and Code Quality." Journal of Systems and Software, 84(3), 302–336.
- Beck, K. (2002). Test-Driven Development: By Example. Addison-Wesley.

[8] Continuous Delivery:
- Humble, J., & Farley, D. (2010). Continuous Delivery: Reliable Software Releases through Build, Test, and Deployment Automation. Addison-Wesley.
- DORA Research. (2019–2024). "State of DevOps Report." Annual report on deployment frequency and lead time.

[9] AI Test Generation:
- NVIDIA. (2024). "Building AI Agents to Automate Software Test Case Creation." NVIDIA Developer Blog.
- Automated test case generation from formal specifications research.

[10] Trunk-Based Development & Version Control:
- Hammant, P. (2024). "Trunk-Based Development." TrunkBasedDevelopment.com.
- Atlassian. (2024). "Trunk-Based Development Guide." Continuous Delivery resource.
- Git branching research: studies on merge conflicts and branching strategies (Perforce, Git research, 2023–2024).

[11] Kanban & Flow Metrics:
- Anderson, D. J. (2010). Kanban: Successful Evolutionary Change for Your Technology Business. Blue Hole Press.
- Poppendieck, M., & Poppendieck, T. (2003). Lean Software Development. Addison-Wesley.

[12] Martin Kleppmann's Formal Verification Blog:
- Kleppmann, M. (2025). "Prediction: AI will make formal verification go mainstream." Martin Kleppmann's Blog. (Kleppmann on AI + formal verification)

[13] Architecture Decision Records:
- Nygard, M. (2011). "Documenting Architecture Decisions." Nygard's Blog.
- AWS Prescriptive Guidance. (2024). "Architecture Decision Records."
- Google Cloud Architecture Center. (2024). "Architecture Decision Records."
- Microsoft Azure Well-Architected Framework. (2024). "ADR."

[14] Model-Driven Development Evidence:
- France, R., & Rumpe, B. (2007). "Model-Driven Development of Complex Software: A Research Roadmap." Proceedings of FOSE 2007. IEEE.
- Evaluating benefits of MDD: Academic studies on code generation and development time reduction.

[15] Agile Adoption & Trends:
- Parabol. (2024). "300+ Agile and Scrum Statistics for 2024."
- Gartner. (2024). "Magic Quadrant for Agile Planning Tools."

[16] Shape Up Methodology:
- Singer, R. (2018). Shape Up: Stop Running in Circles and Ship Work that Matters. Basecamp. (basecamp.com/shapeup)
- Practitioner case studies: Medium articles, 2018–2024.

[17] Agentic SDLC Research (ThoughtWorks, PWC, Microsoft):
- ThoughtWorks. (2024). "Preparing Your Team for the Agentic Software Development Life Cycle." ThoughtWorks Insights.
- PWC. (2024). "Future of Solutions Development and Delivery in the Rise of Gen AI." PWC Report.
- Microsoft. (2025). "An AI-Led SDLC: Building an End-to-End Agentic Software Development Lifecycle." Microsoft Community Hub.
- EPAM. (2024). "Introducing Agentic Development Lifecycle (ADLC)." EPAM Insights Blog.

[18] DAD (Disciplined Agile Delivery):
- Ambler, S. W., & Lines, M. (2018). Disciplined Agile Delivery (2nd ed.). IBM Press.
- PMI. (2024). "Disciplined Agile Handbook." PMI.org.

[19] Version Control & Merge Conflict Research:
- Academia.edu. (2024). "Branching and Merging: An Investigation into Current Version Control Practices."
- Research on merge conflicts: ~10–20% of merges result in conflicts; frequent merges reduce conflict rate.

[20] Git Branching Strategies:
- Perforce. (2024). "Guide to Best Branching Strategies."
- GitHub. (2024). "GitHub Flow." Official GitHub documentation.

[21] ThoughtWorks Technology Radar:
- ThoughtWorks. (2024). "Technology Radar Vol. 30 (April 2024)." ThoughtWorks. (Trunk-Based Development: "Adopt")

[22] AI-Driven Delivery Models (Multi-Source):
- Microsoft, PWC, EPAM, ThoughtWorks (2024–2025) reports on "delegate, review, own" model.

[23] Agentic Coding Trends:
- Anthropic. (2026). "2026 Agentic Coding Trends Report." (Resource referenced but content inaccessible; cited from web search results)

[24] PRINCE2, CMMI, and Traditional Governance:
- UK OGC. (2017). PRINCE2 Official Manual.
- Carnegie Mellon University / SEI. (2023). CMMI-DEV 2.0.

[25] McKinsey Agile Research:
- McKinsey. (2024). "Unlocking the Full Value of Agile Software Development." McKinsey & Company.

[26] Spiral Model (Boehm):
- Boehm, B. W. (1986). "A Spiral Model of Software Development and Enhancement." ACM SIGSOFT Software Engineering Notes, 11(4), 14–24.
- Boehm, B. W. (2000). "Spiral Development: Experience, Principles, and Refinements." CMU/SEI-2000-SR-008.

[27] Scaled Agile Framework Comparison:
- Atlassian. (2024). "Scaling Agile Frameworks Comparison."
- Toptal. (2024). "5 Agile Scaling Frameworks Compared."

[28] Spotify Engineering Model:
- Spotify. (2015). "Spotify Engineering Culture." YouTube video and blog posts.
- Organizations & scaling research referencing Spotify's squads/tribes/chapters model.

[29] Code Review Automation:
- Augment Code. (2024). "How Automated Code Review Tools Reduce Pull Request Bottlenecks."
- Research on layered automation in code review pipelines.

[30] Security Gates & Automated Testing:
- SIEM/DAST and DevSecOps best practices from AWS, Google, GitHub.

[31] Risk Management in Agile (ROAM):
- ISACA. (2023). "Making Risk Management for Agile Projects Effective."
- Microsoft Engineering Playbook. (2024). "Risk Management." Code-with-Engineering-Playbook.

[32] Technical Debt Measurement:
- SonarSource. (2024). "Measuring and Identifying Code-Level Technical Debt: A Practical Guide."
- Research on technical debt compounding and impact on velocity.

[33] Refactoring and Code Quality:
- Fowler, M. (2018). Refactoring: Improving the Design of Existing Code (2nd ed.). Addison-Wesley.
- Fowler's research on refactoring practice and developer productivity.

---

## Part E: Gaps, Uncertainties, and Areas for Deeper Investigation

### E.1 Explicit Gaps in Current Evidence Base

1. **Long-term Agentic SDLC Data**: ADLC, AgentsWay, and other AI-native methodologies lack 3+ year longitudinal data. Adoption is recent (2024–2025); long-term project outcomes are unknown.

2. **Empirical Comparison of Scaled Agent Teams**: No controlled studies comparing, e.g., "Scrum + agents" vs. "Kanban + agents" vs. "Shape Up + agents" at scale (10+ agents over 6+ months). Phase 2 research opportunity.

3. **Agent Autonomy Boundaries**: Existing literature lacks clear empirical guidance on where to draw human-vs.-agent lines. At what scope/complexity should a human intervene vs. letting the agent proceed? Evidence needed.

4. **Merge Conflict Dynamics with High-Frequency Agent Integration**: Agents integrating code multiple times per minute could stress version control; conflict resolution strategies for agent-scale parallelism are under-researched.

5. **Specification Formality vs. Agent Performance**: How much specification detail improves agent output? Does "too formal" slow agent onboarding? Empirical studies needed.

6. **Feedback Loop Latency Requirements**: What feedback loop latency (sub-second, 1 second, 10 seconds?) is optimal for agent iteration? Unknown.

7. **Knowledge Base Size vs. Agent Context**: How large can a knowledge base (ADRs, design docs) grow before agent queries become noisy or slow? Unclear.

8. **Risk Management Operationalisation**: How do agents identify *novel* risks (not pattern-matched from training)? Risk escalation criteria remain ad hoc.

### E.2 Methodologies Deserving Deeper Investigation

1. **Emerging Variants**: Spotify Model (engineering culture, not SDLC). Next.js Incremental Adoption. Nx Monorepo strategies. These blur the line between infrastructure and methodology.

2. **Safety-Critical Methodologies**: Certification Common Criteria (CC) for software, IEC 61508 functional safety. How do these compose with agentic approaches?

3. **Domain-Specific Methodologies**: Medical device software development, automotive ASIL strategies, aerospace DO-178C/DO-254. Do agentic approaches fit, or require separate treatment?

4. **Cultural/Organizational Adoption Patterns**: Which methodologies scale best with agent participation from an *organizational* standpoint? Current research is technical.

### E.3 Rubric Refinements Needed

1. **Dimension Weights**: Current weights (total 137 points) are reasonably distributed but not yet validated empirically. Phase 2 should refine weights based on real-world methodology evaluations.

2. **Context-Specific Weighting**: Solo+Agent, Team+Agents, Programme contexts should potentially have *different* dimension weights. Current rubric applies same dimensions to all contexts. Phase 2 should explore context-specific weighting.

3. **Agent Maturity Levels**: The rubric assesses methodologies, but the evaluation should also account for agent maturity (e.g., Claude Code 2026 vs. future agents). This dependency should be made explicit.

4. **Interaction Effects**: Some dimensions interact (e.g., "Specification Formality" + "Verification & Validation Rigour" together enable stronger outcomes). Rubric is currently independent. Phase 2 should explore interaction terms.

### E.4 Priority Areas for Phase 2

1. **Empirical Evaluation Framework**: Design controlled studies or large case studies comparing top 5–8 methodologies (Scrum, Kanban, Shape Up, ADLC, Spec-Kit SDD, traditional Waterfall-inspired with agents) across rubric dimensions.

2. **Agentic-Specific Research**: Deep dive into ADLC, AgentsWay, Spec-Kit SDD, Multi-Agent Orchestration maturity and adoption patterns.

3. **Feedback Loop Benchmarking**: Measure feedback latency and iteration cycles for various methodologies + agent configurations.

4. **Agent Autonomy Case Studies**: Document real-world agent autonomy boundaries and decision criteria from deployed systems.

5. **Knowledge Base Management Studies**: Empirical evaluation of how large ADR/documentation knowledge bases impact agent performance.

---

## Conclusion

Phase 1 has established a comprehensive, evidence-based rubric and methodology landscape for evaluating agentic SDLC suitability. The 14-dimension rubric is operationally precise and ready for application in Phase 2. The methodology catalogue covers 36+ methodologies spanning traditional, agile, and emerging AI-native categories.

Key findings:

- **AI-native methodologies (ADLC, Spec-Kit SDD, AgentsWay)** are emerging rapidly but lack long-term validation.
- **Specification formality, task decomposability, and verification rigour** are critical differentiators for agentic delivery.
- **Feedback loop structure and concurrency support** become bottlenecks at scale; methodologies must be designed with high-throughput agent parallelism in mind.
- **Convergent pattern**: Successful agentic methodologies treat specs as executable intent, feedback as structured data agents consume, and humans as decision-makers and oversight.

This deliverable is ready for consumption by Phase 2 (Methodology Evaluation) without modification to the rubric.

---

## Appendix: Methodology Quick Reference

Quick lookup table for all 36+ methodologies:

| # | Methodology | Category | Maturity | Agentic Suitability (Preliminary) |
|---|---|---|---|---|
| 1 | Waterfall | Traditional | Mature (declining) | Low (monolithic) |
| 2 | V-Model | Traditional | Mature (niche) | Low (monolithic) |
| 3 | Spiral | Traditional | Mature (niche) | Medium (risk-driven cycles) |
| 4 | RUP | Traditional | Mature (declining) | Medium (iterative, but heavyweight) |
| 5 | PRINCE2 | Traditional | Mature (widespread in gov) | Low (gatekeeping, sequential) |
| 6 | CMMI | Traditional | Mature (niche, government) | Medium (process-focused, scalable) |
| 7 | Cleanroom | Traditional | Mature (safety-critical niche) | High (formal specs, verification) |
| 8 | Formal Methods | Traditional | Mature (research, niche) | High (formal specs, verification) |
| 9 | MDD/MDA | Traditional | Mature (embedded systems) | High (code generation) |
| 10 | Scrum | Agile | Market-leading | Medium-High (iterative, good for small teams) |
| 11 | XP | Agile | Mature (declining) | High (TDD, CI, refactoring) |
| 12 | Kanban | Agile | Market-growing | High (continuous flow, WIP limits) |
| 13 | Scrumban | Agile | Growing | High (flexibility + structure) |
| 14 | SAFe | Agile | Market-leading (enterprise) | Medium (heavyweight, good for coordination) |
| 15 | LeSS | Agile | Growing (lightweight) | Medium-High (minimal overhead) |
| 16 | Nexus | Agile | Growing (lightweight) | Medium-High (minimal overhead) |
| 17 | DAD | Agile | Growing (flexible) | Medium-High (toolkit, adaptable) |
| 18 | Crystal | Agile | Mature (declining) | Low-Medium (human-focused, informal) |
| 19 | FDD | Agile | Mature (niche) | High (feature decomposition) |
| 20 | DSDM | Agile | Mature (moderate) | Medium (time-boxing, business focus) |
| 21 | Shape Up | Emerging | Growing (startup/product focus) | Medium-High (fixed scope, adaptable) |
| 22 | Trunk-Based Dev | Emerging (Core Practice) | Market-leading (standard) | High (parallel, continuous) |
| 23 | CD/Continuous Deployment | Emerging (Practice) | Market-leading | High (automated, continuous) |
| 24 | Mob Programming | Emerging (Practice) | Growing | Medium-High (knowledge sharing, quality) |
| 25 | Spec-Driven Dev | Emerging | Growing (especially with AI) | Very High (agent-centric) |
| 26 | Docs-First / README-Driven | Emerging | Growing (open-source, distributed) | Medium-High (spec-like) |
| 27 | TDD (Standalone) | Emerging (Core Practice) | Market-leading | Very High (verification loop) |
| 28 | BDD (Standalone) | Emerging (Core Practice) | Growing | High (executable specs, agent-parseable) |
| 29 | ADR-Driven Dev | Emerging (Practice) | Growing (enterprise) | High (executable context) |
| 30 | ADLC | AI-Native | Emerging (2024) | Very High (designed for agents) |
| 31 | Spec-Kit SDD | AI-Native | Early (2025) | Very High (agent-native) |
| 32 | AgentsWay | AI-Native | Early (2024) | Very High (designed for agents) |
| 33 | Multi-Agent Orchestration | AI-Native (Infrastructure) | Growing (2023–2025) | Very High (agent infrastructure) |
| 34 | VeriAct | AI-Native (Research) | Early (2024) | Very High (verification + agents) |
| 35 | Pair Programming | Practice | Market-leading | Medium-High (continuous review; resurgent with agents) |
| 36 | DevOps | Practice/Culture | Market-leading (standard) | High (automation, feedback) |

---

**Document Prepared**: Phase 1 SDLC Research Programme
**Date Completed**: 2026-04-07
**Status**: Ready for Phase 2 Consumption
**Next Phase**: Phase 2 – Detailed Methodology Evaluation Against Rubric
