# Deep Research Prompt: Agile Coach Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an Agile Coach. This agent will guide teams on agile practices,
facilitate retrospectives, improve sprint processes, coach on Scrum/Kanban,
and help teams continuously improve their development workflows.

The resulting agent should be able to assess agile maturity, recommend
process improvements, facilitate ceremonies, diagnose team dysfunction,
and implement scaled agile practices when engaged by the development team.

## Research Areas

### 1. Modern Agile Practices (2025-2026)
- What are current best practices for agile software development?
- How have Scrum, Kanban, and hybrid approaches evolved?
- What are the latest patterns for agile in remote/distributed teams?
- How do modern agile practices integrate with AI-assisted development?
- What are current patterns for measuring agile team effectiveness?

### 2. Sprint & Iteration Management
- What are current best practices for sprint planning and estimation?
- How do story points, t-shirt sizing, and no-estimates approaches compare?
- What are the latest patterns for sprint retrospectives that drive improvement?
- How should teams handle sprint scope changes and interruptions?
- What are current patterns for definition of done and acceptance criteria?

### 3. Team Dynamics & Coaching
- What are current best practices for coaching agile teams?
- How should coaches identify and address team dysfunction (Lencioni model)?
- What are the latest patterns for building psychological safety in teams?
- How do servant leadership principles apply in modern agile coaching?
- What are current patterns for coaching teams through transformation?

### 4. Scaled Agile
- What are current best practices for scaling agile (SAFe, LeSS, Nexus)?
- How should organizations coordinate across multiple agile teams?
- What are the latest patterns for portfolio-level agile planning?
- How do dependencies between teams get managed in scaled agile?
- What are current patterns for organizational agile transformation?

### 5. Metrics & Continuous Improvement
- What are the DORA and SPACE metrics and how should they be applied?
- How should teams use flow metrics (cycle time, throughput, WIP)?
- What are the latest patterns for data-driven agile coaching?
- How do teams implement effective continuous improvement loops?
- What are current patterns for OKR integration with agile planning?

### 6. AI-Augmented Agile
- How is AI changing agile practices in 2025-2026?
- What are current patterns for AI-assisted sprint planning and estimation?
- How should agile processes adapt for AI-first development teams?
- What are the latest patterns for AI-generated retrospective insights?
- How do AI coding assistants change team velocity and capacity planning?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Agile methodologies, coaching techniques, metrics, scaled patterns the agent must know
2. **Decision Frameworks**: "When team exhibits [symptom], diagnose [root cause] and recommend [practice] because [reason]"
3. **Anti-Patterns Catalog**: Common agile mistakes (cargo cult Scrum, estimation theater, retrospective fatigue, waterfall-in-disguise)
4. **Tool & Technology Map**: Current agile tools (Jira, Linear, Shortcut, metrics platforms) with selection criteria
5. **Interaction Scripts**: How to respond to "improve our sprint process", "coach our team on agile", "scale agile across teams"

## Agent Integration Points

This agent should:
- **Complement**: delivery-manager by focusing on team practices (delivery-manager handles project execution)
- **Hand off to**: delivery-manager for project timeline and milestone management
- **Receive from**: team-progress-tracker for team performance data
- **Collaborate with**: ai-team-transformer on AI-augmented team practices
- **Never overlap with**: delivery-manager on project timeline and milestone tracking
