# Four SDLC Options for Agentic Software Delivery

*A practitioner's guide derived from the five-phase Agentic SDLC research programme (Phases 1–5).*

---

## Executive Summary

This document defines four distinct Software Development Lifecycle (SDLC) options for projects where AI coding agents (Claude Code, Devin, Cursor, Copilot Workspace, and equivalents) operate as autonomous or semi-autonomous members of the delivery team. The four options are not competing philosophies — they are deliberately positioned at different points on the scale, assurance, and regulatory spectrum so that a team can select the right option for its context rather than forcing one methodology onto every project.

The four options are:

1. **SpecFlow Solo** — a lightweight, single-practitioner agentic SDLC for solo developers, prototypes, and small discovery efforts.
2. **Agile-Native SDLC** — the default option for a single team of 3–10 humans with their own agents, balancing ceremony, feedback speed and governance.
3. **SAFe-Lite Agentic** — a programme-scale option for multi-team, dependency-heavy delivery where cross-team coordination and architectural integrity matter.
4. **Assured Agentic** — a high-assurance option for regulated, safety-critical or security-sensitive work where auditability and formal correctness dominate velocity.

### Decision Matrix

Use the matrix below to select an option. Start at **Option 2 (Agile-Native SDLC)** as the default; move *down* to Option 1 for solo or exploratory work, *up* to Option 3 when multi-team coordination dominates, and *sideways* to Option 4 whenever assurance or regulation dominates — regardless of team size.

| Decision Factor | Option 1: SpecFlow Solo | Option 2: Agile-Native SDLC | Option 3: SAFe-Lite Agentic | Option 4: Assured Agentic |
|---|---|---|---|---|
| **Team size** | 1–2 humans | 3–10 humans, one team | Multiple teams, 20–200+ humans | Any size |
| **Programme complexity** | Single workstream | Single product/service | Multi-team, interdependent workstreams | Any, typically critical subsystem |
| **Regulatory burden** | None / low | Low–moderate | Moderate–high | High (finance, health, safety, defence, gov) |
| **Assurance requirements** | Good-enough | Production-grade | Production-grade + programme audit | Formal evidence of correctness |
| **Blast radius of a defect** | Low (prototype, internal tool) | Moderate (customer-facing) | High (revenue / reputational) | Severe (life, money, national security) |
| **Requirement volatility** | High (discovery) | Moderate–high | Moderate | Low (contract-stable) |
| **Specification maturity** | Emergent, written as you go | Mix of emergent and contract | Contract-first, API-driven | Formal, sometimes mathematical |
| **Cross-team dependencies** | None | Few | Many | Varies |
| **Human review bandwidth vs. agent output** | Human can review all | Sampling + automated gates | Mostly automated gates | Mandatory human + formal gates |
| **Time-to-market pressure** | Very high | High | Moderate | Low |
| **Evidence tolerance (per Phase 5)** | Leans on newer practices (lower confidence) | Proven Agile core + newer spec practices | Proven SAFe core + newer AI-native practices | Anchored in 40+ years of formal/traditional evidence (highest confidence) |
| **Typical use case** | Side projects, R&D, PoCs, internal tooling | SaaS features, product teams, typical digital delivery | Enterprise transformations, platforms, large product portfolios | Medical devices, avionics, payments core, defence, regulated public services |
| **Relative cost** | £ | ££ | £££ | ££££ |
| **Relative speed** | Fastest | Fast | Moderate | Slowest |

### Quick Selection Heuristic

If any **one** of the following is true, jump directly to **Option 4 (Assured Agentic)** regardless of size or cost: (a) a defect could cause physical harm, (b) you face a regulator who requires auditable evidence of correctness, (c) the cost of a single production failure exceeds the cost of the entire project. Otherwise, use team size and dependency density to choose between Options 1, 2 and 3.

### Caveat on Evidence Quality

Every option below composes practices with *proven* building blocks (TDD, BDD, Trunk-Based Development, Continuous Delivery, ADRs, Scrum, SAFe, Cleanroom, Formal Methods) augmented with *emerging* agent-specific practices (machine-readable specs, agent RACI, escalation protocols, prompt libraries). The proven building blocks carry high evidence confidence; the agent-specific augmentations carry low-to-moderate confidence (1–2 years of field evidence at the time of writing). Each option is explicit about which parts are proven versus emerging.

---

## Table of Contents

1. Executive Summary *(above)*
2. Common Foundations Across All Four Options
3. Option 1 — SpecFlow Solo
4. Option 2 — Agile-Native SDLC
5. Option 3 — SAFe-Lite Agentic
6. Option 4 — Assured Agentic
7. Migrating Between Options
8. Glossary

---

## Common Foundations Across All Four Options

Regardless of which option a team selects, the research identifies a core set of practices that are non-negotiable for any credible agentic SDLC. Every option below assumes these are in place.

- **Version-controlled, machine-readable specifications.** Whether Gherkin, OpenAPI, TLA+ or a lightweight intent document, the specification is the primary contract between human and agent. Ambiguous natural-language requirements produce unreliable agent behaviour.
- **Automated verification as the default.** Tests, type checks, linters, security scanners and contract checks run on every change. Agents use these as their feedback signal; humans use them as their gate.
- **Trunk-based branching with short-lived feature branches.** Long-lived branches amplify merge conflict and coordination overhead at agent speed.
- **Architectural Decision Records (ADRs).** An append-only, queryable log of why the architecture looks the way it does. Agents lose context between sessions; ADRs restore it.
- **An explicit agent RACI.** For every category of change, the team records which decisions the agent makes autonomously, which it recommends, which require human approval, and which are forbidden. This is the single most important governance artefact in an agentic SDLC.
- **Prompt, model and tool registry.** A tracked list of the prompts, models, model versions and tools in use, so that agent behaviour is reproducible and auditable.
- **Observability of agent actions.** A log of every agent action (prompts, diffs, tool calls, test results) retained long enough to debug incidents and satisfy audit.
- **A definition of done that includes agent artefacts.** Tests passing, spec updated, ADR written if architectural, documentation regenerated, agent log archived.

These foundations are the floor. Each option adds its own ceremonies, roles, cadences and gates on top.

---

## Option 1 — SpecFlow Solo

### When to Use

A single developer (or a pair) working with one or more agents on a prototype, research spike, internal tool, side project, or the earliest discovery phase of a larger product. The defining characteristic is that the human can personally review every change the agent produces and the blast radius of a defect is contained.

### Core Philosophy

Minimise every form of ceremony. Let the specification, the test suite and the trunk do all the coordination work. The human writes intent; the agent writes code; the tests adjudicate. Feedback loops are measured in seconds, not days.

### Lifecycle

The lifecycle is a tight continuous loop rather than a sequence of phases. A typical loop looks like this. The developer captures intent in a short Gherkin scenario or acceptance criterion and commits it. The agent reads the scenario, proposes an implementation plan (typically a short list of files and changes), writes failing tests, implements the change, runs the full test suite, and opens a pull request against trunk. The developer reviews the PR, runs it locally if needed, and either merges, requests changes, or reverts and reframes the intent. Between loops, any architectural decision that will outlive the current change is captured as a one-paragraph ADR.

### Artefacts

The artefact set is deliberately sparse: a specification file (Gherkin or equivalent) alongside each feature, a test suite, an ADR folder, a README that describes how to run the project, a CHANGELOG maintained automatically from merged PRs, and an agent session log. There is no backlog tool beyond a plain-text TODO file or lightweight issue tracker; there are no sprint artefacts.

### Roles

There are only two roles. The **Human Lead** owns intent, review, architecture and escalation. The **Agent** owns implementation, testing, refactoring inside approved boundaries, and documentation. If a second human joins, they share the Human Lead role; the option stops being Solo once the team exceeds two people or dependencies across workstreams appear.

### Ceremonies

None in the traditional sense. The daily rhythm is: write intent, run the loop, review, merge, repeat. There is a weekly personal retrospective of 15 minutes in which the developer reviews the agent session log, notes recurring failure modes, and refines the prompt library and the ADRs.

### Quality Gates

A change may only merge when: tests pass on CI, lint and type checks pass, the specification file referenced by the change exists and has been updated, and the human has personally eyeballed the diff. There is no separate architecture review — architectural changes are captured as ADRs at merge time.

### Tooling Requirements

A coding agent (Claude Code or equivalent), a version control host with PR-based review, a CI pipeline that runs tests on every PR, a linter and type checker, a Gherkin or equivalent spec runner, and a local mechanism for recording ADRs. Nothing heavier is required.

### Metrics

Cycle time from intent to merged change, test coverage trend, number of human-requested revisions per PR (a proxy for agent prompt quality), and a weekly count of ADRs written (a proxy for architectural momentum). Velocity and story points are explicitly not used.

### Strengths

Feedback loops are as tight as technology allows. Ceremony overhead is effectively zero. The human retains full cognitive grip on the system. The approach is fully composed of proven building blocks and therefore carries high evidence confidence.

### Weaknesses

The approach does not scale beyond one or two humans. It provides no governance surface for regulators. If the developer becomes unavailable, continuity is fragile. It assumes the human has the discipline to write specifications and ADRs even when the agent could proceed without them.

### Proven vs. Emerging Elements

Proven: TDD/BDD, trunk-based development, PR-based review, ADRs. Emerging: treating a Gherkin file as the primary contract with an agent; using agent session logs as a retrospective artefact.

---

## Option 2 — Agile-Native SDLC

### When to Use

A single cross-functional team of three to ten humans, each with their own agents, building a product or service together. This is the default option and the one most teams adopting agentic delivery should start with.

### Core Philosophy

Keep the proven Agile core — iterative delivery, cross-functional team, product owner, tight customer feedback — but recalibrate the ceremonies, metrics, roles and artefacts for a world where agents dramatically increase code throughput and compress individual feedback loops. Machine-readable specifications replace narrative user stories as the primary contract; throughput and cycle time replace velocity; ceremonies are compressed rather than eliminated.

### Lifecycle

The lifecycle uses a weekly cadence rather than a two-week sprint. Each cycle begins with a 30-minute intent session in which the Product Owner walks the team through the week's priorities, expressed as executable specifications (Gherkin scenarios, OpenAPI contracts, example outputs). Work then flows continuously. Each team member pairs with their agent, picks a top-of-queue item, writes or refines the spec, lets the agent implement against it, runs the verification suite, and opens a PR. PRs are reviewed by another human (and optionally by a reviewing agent) and merged to trunk on green. Feature flags govern release to production, which happens continuously. At the end of the week there is a 30-minute review with stakeholders focused on the *behavioural* change delivered, followed by a 30-minute retrospective that explicitly includes agent-specific signals (prompt effectiveness, agent rework rate, specification ambiguity incidents).

### Artefacts

Backlog of intent items (not user stories but thin slices each linked to a spec), Gherkin or OpenAPI specifications as the canonical contract, ADR registry, test suites, a living architecture overview, a team-level RACI for agent autonomy, a prompt and tool registry, and an agent action log. The Definition of Done explicitly includes: specification updated, tests green, ADR added if architectural, human review complete, agent log archived.

### Roles

The **Product Owner** owns intent and priority. In an agent-native context this role evolves into a specification author as much as a backlog manager — precision of intent matters more than throughput of stories. A **Tech Lead / Architect** owns the ADR registry, the agent RACI and architectural coherence; this role becomes more critical than in a traditional Agile team because agents produce code faster than architectural drift can be spotted by osmosis. **Developers** become *developer-reviewers*: each human is responsible for their own agent's output, pair-reviews another developer's agent output, and retains accountability for merged changes. A lightweight **Scrum Master / Delivery Lead** facilitates ceremonies, maintains the prompt registry, and watches agent metrics for systemic issues. Agents themselves are registered team members with documented capabilities and limitations.

### Ceremonies

Weekly intent/planning (30 min), continuous flow with async standups through CI and chat (no daily synchronous standup), weekly stakeholder review (30 min), weekly retrospective (30 min) with explicit agent-failure review, and an ad-hoc architectural council triggered whenever an ADR is proposed. Total ceremony overhead is deliberately kept under two hours per person per week.

### Quality Gates

A PR may only merge when: tests, lint, type checks and security scans all pass; the related specification is updated; at least one human reviewer has approved; the change conforms to the agent RACI (i.e. the agent had the authority to make the change without further escalation). Architectural changes additionally require an ADR and a Tech Lead sign-off. Release to production is gated by feature flag and by the automated deployment pipeline.

### Tooling Requirements

Coding agents for every team member, a shared version control host, CI/CD with feature-flag support, a spec runner (Cucumber, Playwright, Postman/OpenAPI validator or equivalent), a linter, type checker and security scanner, an ADR tool, a prompt and tool registry, an agent action log store, and observability on production. A lightweight issue tracker remains useful for intent capture.

### Metrics

Throughput (items completed per week), cycle time distribution and P85 forecast, change-failure rate, mean time to restore, defect escape rate, specification-ambiguity incidents (how often did an agent misinterpret an intent?), and agent rework ratio (percentage of agent PRs that required more than one round of human-requested changes). Velocity in story points is not used.

### Strengths

Preserves the proven Agile core, which carries high evidence confidence, while systematically recalibrating each piece for agent participation. Ceremonies are light enough to keep pace with agent throughput but rich enough to retain human judgement where it matters. Scales naturally to the size of a single cross-functional team, which is the unit most organisations actually deliver in.

### Weaknesses

Does not address multi-team coordination; teams doing interdependent work will feel the strain as soon as two teams must agree on a contract. Assumes a disciplined Product Owner who can author specifications — not every organisation has this today. Some of the agent-specific augmentations (RACI, prompt registry, agent rework ratio) are emerging practices with limited longitudinal evidence.

### Proven vs. Emerging Elements

Proven: Scrum skeleton, trunk-based development, CI/CD, feature flags, TDD/BDD, ADRs, product ownership. Emerging: weekly cadence replacing two-week sprints for agentic teams, throughput-and-cycle-time replacing velocity, agent RACI, agent rework ratio as a quality signal, specification-as-contract with agents.

---

## Option 3 — SAFe-Lite Agentic

### When to Use

A programme of multiple interdependent teams — typically between three and twenty teams — delivering components of a shared product, platform or portfolio. The defining characteristics are cross-team dependencies, a need for architectural integrity across the estate, and a level of audit visible to executives or external stakeholders.

### Core Philosophy

Retain the minimum SAFe Essentials structure required for multi-team alignment (Agile Release Trains, PI planning, System Demos, architectural runway) while aggressively stripping heavy ceremony. Inside each team, the Agile-Native SDLC (Option 2) runs unchanged. Across teams, contracts and specifications — not meetings — are the primary coordination mechanism. Specification-Driven Development becomes the backbone: every cross-team interface is an OpenAPI, AsyncAPI or equivalent contract that is version-controlled, reviewed and tested.

### Lifecycle

The lifecycle has two cadences. The **team cadence** is identical to Option 2 (weekly intent, continuous flow, weekly review and retro). The **programme cadence** is a six-to-eight week Programme Increment. At the start of each PI, representatives from every team, the System Architect, the Product Management function and a lightweight Release Train Engineer run a compressed PI planning event of one day (not the traditional two). The inputs are the intent backlog for each team and the set of proposed cross-team contracts; the output is an agreed set of commitments expressed as specifications rather than dates. Throughout the PI, each team delivers continuously to trunk. Every two weeks there is a System Demo in which the programme-level behaviour is exercised end-to-end against its specifications. At the end of the PI there is an Inspect & Adapt event focused on programme-level agent signals: dependency violations, contract drift, architectural runway consumption and cross-team rework.

### Artefacts

At programme level: a portfolio backlog of intent, a programme-level architectural runway document, a central contract registry (OpenAPI/AsyncAPI specs), a programme-wide ADR registry, a cross-team dependency map, a programme agent RACI, a programme prompt and model registry, and a consolidated agent action log for audit. Each team maintains the Option 2 artefact set.

### Roles

**Release Train Engineer (RTE)** — orchestrates the programme cadence, watches cross-team dependencies and escalates drift. Typically a single RTE per 5–10 teams. **System Architect** — owns the architectural runway and the contract registry, with authority to reject contracts that violate runway decisions. **Product Management** — curates the portfolio intent and prioritises cross-team work. **Team-level roles** are as in Option 2. **Agent Governance Lead** is a new role unique to this option: a single person (typically reporting to the CTO or Head of Engineering) who owns the programme agent RACI, the prompt and model registry, the agent audit log, and the incident response process for agent-caused failures.

### Ceremonies

Team ceremonies are identical to Option 2. Programme ceremonies add: a one-day PI planning event every six to eight weeks, a two-weekly System Demo of 60 minutes, a weekly cross-team Scrum-of-Scrums of 30 minutes focused *only* on dependency risk, and a PI-closing Inspect & Adapt of two hours. Total programme overhead is deliberately bounded at under five per cent of capacity.

### Quality Gates

Team-level gates are as in Option 2. Additional programme-level gates: every cross-team interface change requires an updated contract in the registry and a contract test in both the producer and consumer; every architectural change requires an ADR approved by the System Architect; every new agent capability or model version must be registered in the programme registry before use; every PI closes with a consolidated audit report summarising agent action logs, incidents and RACI compliance.

### Tooling Requirements

Everything in Option 2, plus: a centralised contract registry (e.g. a Git-hosted OpenAPI repository with automated linting and breaking-change detection), a programme-wide ADR tool, a dependency-tracking tool (even a well-maintained spreadsheet suffices), a centralised prompt and model registry, a centralised agent action log store with audit-grade retention, and programme-level observability.

### Metrics

Programme throughput (features completed per PI), cross-team dependency defect rate, contract drift rate (producer/consumer mismatch), architectural runway consumption, mean time to detect agent-caused regressions across teams, and audit compliance (percentage of agent actions with complete traceability). Team metrics are as in Option 2.

### Strengths

Preserves the well-evidenced SAFe coordination backbone for multi-team delivery while removing the ceremony overhead that makes classical SAFe painful. Specification-Driven Development is a natural fit for agent participation. The explicit Agent Governance Lead role gives executives a single point of accountability for agent behaviour across the programme — which is usually what satisfies auditors and regulators who cannot cope with distributed accountability.

### Weaknesses

Requires organisational maturity: a functioning architectural community, a product management function that can write contracts, and an executive sponsor who understands why agent governance needs a dedicated role. Under-investing in the Agent Governance Lead role or the contract registry causes this option to degrade rapidly into classical SAFe-plus-chaos. Some of the evidence base (multi-team agentic coordination at scale) is thin — this option extrapolates from proven SAFe practice rather than resting on direct agentic-SAFe studies.

### Proven vs. Emerging Elements

Proven: SAFe Essentials structure, PI planning, System Demos, architectural runway, Specification-Driven Development with OpenAPI, contract testing. Emerging: the Agent Governance Lead role, the programme prompt and model registry, audit-grade agent action logs, and the compression of PI planning to a single day on the back of agent throughput.

---

## Option 4 — Assured Agentic

### When to Use

Projects where a single production defect could cause physical harm, material financial loss, regulatory sanction, or national-security impact. Typical domains include medical devices, avionics and flight software, payments core systems, railway signalling, defence, critical national infrastructure and regulated public services. Use this option regardless of team size whenever assurance dominates velocity.

### Core Philosophy

Anchor the SDLC in the 40+ years of evidence behind Cleanroom Software Engineering, Formal Methods and CMMI-style traceability. Agents are permitted — and valuable — but only inside a bounded authority envelope and only where their output can be checked by independent, preferably formal, verification. Speed is explicitly de-prioritised in favour of demonstrable correctness, auditability and defensibility. The guiding question is not *"how fast did we ship?"* but *"can we prove, to a sceptical regulator, that this system does what it should and nothing else?"*

### Lifecycle

The lifecycle retains recognisable phases but runs them as short iterations inside a phase gate. Each iteration begins with a **formal intent** phase in which a requirement is captured in a mathematically precise form — TLA+, Z, Event-B, Alloy, or at minimum BDD scenarios plus a contract — and signed off by a Requirements Authority. An **architecture and formal specification** phase follows in which the change is modelled, invariants are stated and, for the most critical modules, a formal proof obligation is written. The agent then participates in the **implementation** phase under tight constraint: it proposes code that satisfies the specification, generates tests (including property-based and adversarial tests), runs static analysis, and presents a candidate. A mandatory **independent verification** phase follows in which a human reviewer (and, where the regime requires it, a second independent reviewer) checks the diff, the tests, the formal proofs and the agent action log. A **qualification and audit** phase closes each change with an update to the traceability matrix linking requirement → spec → model → code → test → proof → evidence. Releases are gated by a formal release board that reviews the accumulated evidence.

### Artefacts

A controlled requirements specification, formal models (TLA+ / Z / Event-B / Alloy) for critical subsystems, a behavioural specification (BDD/Gherkin) for less critical surfaces, a complete traceability matrix from requirement to evidence, ADRs, proof artefacts, test suites including property-based and mutation tests, static analysis reports, security analysis reports, configuration-managed builds, a release evidence package, a full agent action log retained for the regulatory minimum period, and a documented agent RACI that is deliberately narrower than in Options 1–3.

### Roles

**Requirements Authority** owns the controlled specification and signs off intent. **Formal Methods Engineer** owns the formal models and proofs for critical subsystems. **Architect** owns the ADR registry and architectural integrity. **Independent Verifier / V&V Engineer** reviews every change; in regimes that require it, a second independent verifier reviews high-criticality changes. **Developers** author specifications and supervise agents; they are explicitly *not* authorised to merge their own agent's output without independent review. **Quality / Safety / Security Assurance Lead** owns the release evidence package and the interface with regulators. **Agent Governance Lead** (as in Option 3) owns the agent RACI, the prompt and model registry, and the agent action log. **Configuration Manager** owns baselines and controlled change. Agents operate under the narrowest authority of any option: they may propose, implement and test, but never approve, never release, never modify safety-critical modules without human-plus-formal verification.

### Ceremonies

Ceremonies are deliberately heavier than in Options 1–3 because assurance requires visible decisions. A weekly requirements review, a weekly architecture and ADR review, a per-change independent verification session, a periodic (typically monthly) formal methods review for critical modules, a per-release release board, and a quarterly programme audit. In addition, a monthly agent behaviour review in which the Agent Governance Lead presents the agent action log, incident list, RACI compliance and any proposed changes to agent authority.

### Quality Gates

A change may only merge when: the requirement is in the controlled specification; the behavioural or formal spec is updated and, for critical modules, proof obligations are discharged; all tests (unit, property-based, mutation, integration, system) pass; static analysis and security scans are clean; at least one independent human verifier has approved; the traceability matrix is complete; and the change complies with the agent RACI. A release may only occur when: all merged changes meet the merge gates, the release evidence package is complete, the safety / security assurance lead has signed off, the release board has approved, and the configuration baseline is frozen and archived.

### Tooling Requirements

Everything in Option 2, plus: a formal methods toolchain (TLA+ Toolbox, Isabelle, Coq, Event-B/Rodin, Alloy, as appropriate), property-based and mutation testing frameworks, a controlled requirements management tool, a traceability tool capable of generating evidence packages, a configuration management system with full baseline control, audit-grade agent action logging with tamper-evident retention, a hardened prompt and model registry with change control, and an independent CI environment that cannot be influenced by the agent.

### Metrics

Defect escape rate to production (target: effectively zero), residual risk score, formal proof coverage for critical modules, traceability completeness (target: 100 per cent), independent verification findings per change, time-to-evidence for release packages, agent RACI compliance (target: 100 per cent), and audit finding counts. Throughput and cycle time are tracked but explicitly subordinate to assurance metrics.

### Strengths

Rests on the highest-confidence evidence base in the research — Cleanroom, Formal Methods and CMMI all have decades of empirical support including in regulated domains. Provides the audit surface that regulators actually require. Narrow agent authority contains the blast radius of agent errors. The option is defensible in a post-incident investigation in a way that Options 1–3 are not.

### Weaknesses

Slow and expensive relative to the other options. Requires scarce skills (formal methods engineers are not abundant). Ceremony overhead is high by design. The option will frustrate teams used to continuous delivery — it is explicitly not optimised for speed. The augmentations for agent participation (RACI, action log, governance role) are proven in principle but have limited field evidence specifically inside formally assured programmes; expect to invest in tailoring the approach to the specific regulatory regime.

### Proven vs. Emerging Elements

Proven: Cleanroom Software Engineering, Formal Methods (Z, B, VDM, TLA+), CMMI-style traceability, independent V&V, configuration management, controlled requirements, release evidence packages. Emerging: narrow agent authority envelopes inside formally assured programmes, tamper-evident agent action logs as regulatory evidence, and the integration of coding agents with property-based and mutation testing as a reinforced verification layer.

---

## Migrating Between Options

The four options are not silos. A project may legitimately move between options as it matures or as its context changes.

A typical path is **Option 1 → Option 2**: a solo developer validates an idea, hires or joins a team, and the project gains a Product Owner, a weekly cadence and more structured artefacts. The specifications, ADRs and agent logs carry forward and become the seed of the team's canonical context.

A less common but important path is **Option 2 → Option 3** when a single product grows into a platform with multiple teams depending on it. The trigger is usually the first cross-team contract dispute. Migration involves standing up the contract registry, the programme ADR registry, the Agent Governance Lead role and the PI cadence.

The path **Option 2 → Option 4** or **Option 3 → Option 4** is triggered by a change in regulatory scope, a near-miss incident, or entry into a regulated market. Migration here is invasive and should be planned as a project in its own right; formal methods skills must be acquired, the traceability matrix must be back-filled, and the agent RACI must be narrowed.

Moving *down* the ladder is rare and usually unwise: once a regulatory obligation exists it does not go away, and a programme that has invested in SAFe-Lite structure loses more than it gains by dropping back to single-team Agile-Native.

---

## Glossary

**ADR (Architectural Decision Record).** A short, append-only document recording a single architectural decision, its context and its consequences.

**Agent RACI.** A table listing categories of change and, for each, which are Responsible / Accountable / Consulted / Informed between human and agent; extended in an agentic SDLC to cover what the agent may do autonomously, what it may recommend, what requires human approval, and what is forbidden.

**BDD (Behaviour-Driven Development).** A practice in which system behaviour is described in structured natural language (typically Gherkin: Given / When / Then) that is both human-readable and machine-executable.

**Contract Registry.** A central, version-controlled store of interface specifications (OpenAPI, AsyncAPI, protobuf, etc.) governing how components or teams interact.

**Formal Methods.** Mathematically rigorous techniques (Z, B, VDM, TLA+, Event-B, Alloy, Isabelle, Coq, and related) for specifying and verifying software.

**PI (Programme Increment).** A time-boxed planning and delivery cadence used in SAFe; typically 8–12 weeks in classical SAFe and compressed to 6–8 weeks in SAFe-Lite Agentic.

**Prompt and Model Registry.** A tracked list of the prompts, models, model versions and tools used by agents, enabling reproducibility and audit.

**Specification-Driven Development.** A family of practices (API-first, Contract-first, Design-by-Contract) in which a machine-readable specification is the primary artefact and the source from which code and tests flow.

**Trunk-Based Development.** A branching practice in which developers integrate small changes into a single shared main branch many times per day, relying on feature flags and tests to govern release.

---

*Derived from the five-phase Agentic SDLC research programme (Phases 1–5) held in this workspace.*
