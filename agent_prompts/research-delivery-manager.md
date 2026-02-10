# Deep Research Prompt: Delivery Manager Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Delivery Manager. This agent will manage project timelines,
track deliverables, coordinate releases, manage risks, communicate status
to stakeholders, and ensure projects ship on time and within scope.

The resulting agent should be able to create delivery plans, track milestones,
manage dependencies, assess delivery risks, and communicate progress to
stakeholders when engaged by the development team.

## Research Areas

### 1. Software Delivery Management (2025-2026)
- What are current best practices for software delivery management?
- How have delivery management practices evolved with continuous delivery?
- What are the latest patterns for release planning and coordination?
- How should delivery managers handle competing priorities and scope?
- What are current patterns for delivery cadence optimization?

### 2. Risk & Dependency Management
- What are current best practices for delivery risk identification and mitigation?
- How should cross-team dependencies be tracked and managed?
- What are the latest patterns for risk registers and risk scoring?
- How do delivery managers handle technical debt as a delivery risk?
- What are current patterns for go/no-go decision frameworks?

### 3. Stakeholder Communication
- What are current best practices for delivery status reporting?
- How should progress be communicated to different audiences (exec, team, customers)?
- What are the latest patterns for delivery dashboards and visibility?
- How should delivery managers handle bad news and delays?
- What are current patterns for stakeholder expectation management?

### 4. Release Management
- What are current best practices for release management in continuous delivery?
- How should release trains and feature freezes be managed?
- What are the latest patterns for release coordination across teams?
- How do feature flags change release management practices?
- What are current patterns for release readiness and deployment checklists?

### 5. Capacity & Resource Planning
- What are current best practices for team capacity planning?
- How should delivery managers account for AI-augmented developer productivity?
- What are the latest patterns for resource allocation across projects?
- How do teams handle unplanned work within delivery commitments?
- What are current patterns for predictive delivery forecasting?

### 6. Delivery Metrics & Forecasting
- What are current best practices for delivery predictability metrics?
- How do Monte Carlo simulations support delivery forecasting?
- What are the latest patterns for lead time and cycle time tracking?
- How should organizations measure delivery health?
- What are current patterns for delivery retrospectives and improvement?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Delivery practices, risk management, release coordination, metrics the agent must know
2. **Decision Frameworks**: "When delivery faces [risk/constraint], take [action] because [reason]"
3. **Anti-Patterns Catalog**: Common delivery mistakes (overcommitting, hiding delays, scope creep, no dependency tracking)
4. **Tool & Technology Map**: Current delivery management tools with selection criteria
5. **Interaction Scripts**: How to respond to "plan our release", "track our delivery", "manage delivery risks"

## Agent Integration Points

This agent should:
- **Complement**: agile-coach by handling delivery execution (coach handles team practices)
- **Hand off to**: agile-coach for team dynamics and process improvement
- **Receive from**: project-plan-tracker for progress data and milestone tracking
- **Collaborate with**: solution-architect on technical delivery risks
- **Never overlap with**: agile-coach on team ceremonies and agile practices
