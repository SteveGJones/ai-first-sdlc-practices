# Deep Research Prompt: Project Plan Tracker Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Project Plan Tracker. This agent will monitor project progress,
track deliverables against plans, identify schedule deviations, maintain
visibility into project health, and ensure teams stay on track with commitments.

The resulting agent should be able to create tracking dashboards, detect
schedule slippage early, analyze task dependencies, generate progress reports,
and recommend corrective actions when engaged by the development team.

## Research Areas

### 1. Project Tracking Best Practices (2025-2026)
- What are current best practices for software project tracking?
- How have project tracking methodologies adapted to agile environments?
- What are the latest patterns for tracking work across multiple tools?
- How should projects balance detailed tracking with team autonomy?
- What are current patterns for automated progress detection from commits/PRs?

### 2. Schedule & Milestone Management
- What are current best practices for milestone definition and tracking?
- How should critical path analysis work for software projects?
- What are the latest patterns for dependency tracking across teams?
- How do teams detect and respond to schedule slippage early?
- What are current patterns for schedule buffer management?

### 3. Progress Visualization & Dashboards
- What are current best practices for project progress dashboards?
- How should burndown/burnup charts be designed for maximum value?
- What are the latest patterns for cumulative flow diagrams?
- How do real-time project health indicators work?
- What are current patterns for multi-project portfolio dashboards?

### 4. Health Indicators & Early Warning
- What are current best practices for project health assessment?
- How should leading indicators predict delivery problems?
- What are the latest patterns for automated health scoring?
- How do AI-powered project analytics predict risks?
- What are current patterns for traffic light and RAG status systems?

### 5. Reporting & Communication
- What are current best practices for project status reports?
- How should progress be reported to different stakeholder levels?
- What are the latest patterns for automated report generation?
- How should deviations and risks be communicated?
- What are current patterns for project retrospective facilitation?

### 6. Tool Integration & Automation
- How should project tracking integrate with development tools (GitHub, Jira, Linear)?
- What are current patterns for automated task status updates?
- How do project tracking bots and AI assistants work?
- What are the latest patterns for cross-tool data aggregation?
- What are current patterns for project data export and analysis?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Tracking methods, health indicators, reporting patterns, tool integration the agent must know
2. **Decision Frameworks**: "When project shows [indicator], investigate [area] because [reason]"
3. **Anti-Patterns Catalog**: Common tracking mistakes (over-reporting, vanity metrics, manual-only tracking, no early warning)
4. **Tool & Technology Map**: Current project tracking tools with selection criteria
5. **Interaction Scripts**: How to respond to "track our project", "assess project health", "generate status report"

## Agent Integration Points

This agent should:
- **Complement**: delivery-manager by providing tracking data (delivery-manager makes decisions)
- **Hand off to**: delivery-manager for corrective action decisions
- **Receive from**: all team members for progress updates
- **Collaborate with**: team-progress-tracker on team-level metrics
- **Never overlap with**: delivery-manager on delivery decision-making
