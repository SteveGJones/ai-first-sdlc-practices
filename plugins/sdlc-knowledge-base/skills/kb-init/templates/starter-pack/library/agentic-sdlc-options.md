---
title: "Four SDLC Options for Agentic Software Delivery"
domain: sdlc, agentic-development, methodology, process
status: active
tags: [sdlc, agentic, scrum, safe, formal-methods, solo-development, multi-team, assured]
source: research/sdlc/Agentic_SDLC_Options.md (ai-first-sdlc-practices repo)
cross_references:
  - library/agent-suitability-rubric.md
  - library/specification-formality-and-agent-performance.md
---

## Key Question

What software development lifecycle should a project adopt when AI coding agents operate as primary or semi-autonomous members of the delivery team?

## Core Findings

1. **No single SDLC fits all agentic projects.** A practitioner-facing taxonomy identifies four distinct options positioned at different points on the scale, assurance, and regulatory spectrum: SpecFlow Solo (1-2 humans), Agile-Native SDLC (3-10 humans, default), SAFe-Lite Agentic (multi-team programmes), Assured Agentic (regulated/safety-critical). Source: Agentic SDLC research programme, Phase 5 synthesis (2026).

2. **Start at the default and move from there.** The decision matrix recommends starting with Option 2 (Agile-Native SDLC) and shifting based on context: down to Option 1 for solo or exploratory work, up to Option 3 when multi-team coordination dominates, sideways to Option 4 whenever assurance or regulation dominates regardless of team size.

3. **One trigger forces the assured option.** If any of three conditions is true — (a) a defect could cause physical harm, (b) a regulator requires auditable evidence of correctness, (c) the cost of a single production failure exceeds the cost of the entire project — jump directly to Option 4 (Assured Agentic) regardless of size or cost. No middle-ground compromise.

4. **Evidence quality varies by option.** All four options compose proven building blocks (TDD, BDD, Trunk-Based Development, Continuous Delivery, ADRs, Scrum, SAFe, Cleanroom, Formal Methods) with emerging agent-specific practices (machine-readable specs, agent RACI, escalation protocols, prompt libraries). The proven building blocks carry high confidence (decades of evidence); the agent-specific augmentations carry low-to-moderate confidence (1-2 years field evidence at time of writing).

5. **Migration paths are well-defined but mostly one-directional.** Common path: Option 1 → Option 2 as a project matures from prototype to product team. Less common but important: Option 2 → Option 3 when a single product grows into a platform with multiple consuming teams. Option 2 or 3 → Option 4 is invasive and triggered by regulatory entry or near-miss incidents. Moving *down* the ladder is rare and usually unwise once regulatory obligations exist.

## Frameworks Reviewed

| Framework | Evidence base | Limitations |
|---|---|---|
| SpecFlow Solo (Option 1) | Composes TDD/BDD/TBD/ADRs, all high-evidence | Doesn't scale beyond 1-2 humans; provides no governance surface |
| Agile-Native SDLC (Option 2) | Built on Scrum + BDD + TDD + TBD, decades of empirical support | Multi-team coordination requires Option 3; not for regulated work |
| SAFe-Lite Agentic (Option 3) | Built on SAFe Essentials + Specification-Driven Development | Requires architectural maturity; under-investment degrades to "SAFe + chaos" |
| Assured Agentic (Option 4) | Built on Cleanroom + Formal Methods + CMMI traceability, 40+ years of evidence | Slow and expensive; requires scarce formal methods skills |

## Actionable Thresholds

| Metric | Threshold | Source | Signal |
|---|---|---|---|
| Team size for SpecFlow Solo | 1-2 humans | Agentic SDLC Phase 5 | Above this, switch to Option 2 |
| Team size for Agile-Native default | 3-10 humans, single team | Agentic SDLC Phase 5 | Above this with cross-team work, consider Option 3 |
| Programme scale for SAFe-Lite | 3-20 teams, 50-200+ humans | Agentic SDLC Phase 5 | Below 3 teams, Option 2 is sufficient |
| Trigger for Assured (any one) | Physical harm risk OR regulator audit OR catastrophic failure cost | Agentic SDLC Phase 5 quick selection heuristic | Mandatory jump to Option 4 |

## Design Principles

- **Common foundations are non-negotiable across all four options.** Version-controlled machine-readable specifications, automated verification as default, trunk-based branching, ADRs, agent RACI, prompt/model registry, observability of agent actions, definition of done with agent artefacts. These are the floor; each option adds its own ceremonies on top.
- **Be explicit about proven vs emerging components.** Each option mixes high-confidence proven practices (Scrum, TDD, formal methods) with low-confidence emerging ones (agent RACI, prompt libraries, escalation protocols). Document which parts are which so teams can calibrate trust.
- **Optimise for fitness, not score.** The research's 14-dimension rubric scores top compositions at 68-71/100. Even the "best" agentic SDLC is mediocre by the rubric — pursue the right fit for context, not the highest number.
- **Migration is a discrete decision, not a runtime toggle.** Switching options should be deliberate, planned, and documented as a project event with its own retrospective.

## Key References

1. *Four SDLC Options for Agentic Software Delivery* — Practitioner guide derived from the five-phase Agentic SDLC research programme (2026). `research/sdlc/Agentic_SDLC_Options.md`
2. Phase 5 Final Report — Software Development Methodologies for Agentic SDLC: A Comparative Evaluation. April 2026. `research/sdlc/Phase5_Final_Report.md`
3. Schwaber, K., Sutherland, J. (2020). *The Scrum Guide.* Scrum.org.
4. Humble, J., Farley, D. (2010). *Continuous Delivery.* Addison-Wesley.
5. Linger, R. C., Pleszkoch, M. G., Prowell, S. B. (2003). *Cleanroom Software Engineering for Critical Systems.* SEI/CMU.
6. Leffingwell, D. (2021). *SAFe 5.0 Reference Guide.* Addison-Wesley.

## Programme Relevance

This file maps to EPIC #97 (Multi-Option Commissioned SDLC) in the ai-first-sdlc-practices framework. The four options are the basis for the framework's commissioning model — at project setup time, the framework picks one option and installs a complete bundle (constitution + agents + skills + templates + validators). See the EPIC for the implementation roadmap.

For projects using this knowledge base from outside the framework: this file is example content shipped with `sdlc-knowledge-base`. Replace it with library files relevant to your own problem space, or extend it with your project's specific findings about which option you've adopted and why.
