# Deep Research Prompt: Team Progress Tracker Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Team Progress Tracker. This agent will track team-level
adoption metrics, monitor SDLC compliance progress, assess team readiness
for advancement, and maintain visibility into team health across development
practices.

The resulting agent should be able to track adoption metrics, measure
compliance trends, assess level-up readiness, generate team health reports,
and identify coaching opportunities when engaged by the development team.

## Research Areas

### 1. Team Performance Measurement (2025-2026)
- What are current best practices for measuring developer team performance?
- How do DORA metrics (deployment frequency, lead time, MTTR, change failure rate) apply?
- What are the SPACE framework dimensions and how to measure them?
- How should teams track flow metrics (flow efficiency, flow time, flow load)?
- What are current patterns for balanced performance measurement?

### 2. Adoption & Maturity Tracking
- What are current best practices for technology adoption tracking?
- How should organizations measure practice adoption across teams?
- What are the latest patterns for maturity model assessment?
- How do adoption curves inform coaching strategies?
- What are current patterns for self-assessment vs external assessment?

### 3. Compliance Monitoring
- What are current best practices for development process compliance?
- How should compliance be measured without creating bureaucracy?
- What are the latest patterns for automated compliance checking?
- How do teams track compliance trends over time?
- What are current patterns for compliance gamification?

### 4. Team Health Assessment
- What are current best practices for team health checks (Spotify model)?
- How should psychological safety be measured and tracked?
- What are the latest patterns for team satisfaction surveys?
- How do retrospective insights feed into team health metrics?
- What are current patterns for predicting team burnout?

### 5. Reporting & Visualization
- What are current best practices for team metrics dashboards?
- How should team progress be visualized for different audiences?
- What are the latest patterns for trend analysis and forecasting?
- How do organizations benchmark teams against each other fairly?
- What are current patterns for privacy-respecting team metrics?

### 6. Continuous Improvement Tracking
- How should improvement actions from retrospectives be tracked?
- What are current patterns for experiment tracking in teams?
- How do improvement velocity metrics work?
- What are the latest patterns for tracking coaching effectiveness?
- What are current patterns for team learning metrics?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Team metrics, adoption tracking, health assessment, compliance monitoring the agent must know
2. **Decision Frameworks**: "When team metric shows [value], recommend [action] because [reason]"
3. **Anti-Patterns Catalog**: Common tracking mistakes (surveillance metrics, gameable measures, vanity dashboards)
4. **Tool & Technology Map**: Current team analytics tools with selection criteria
5. **Interaction Scripts**: How to respond to "assess our team health", "track adoption progress", "measure team performance"

## Agent Integration Points

This agent should:
- **Complement**: project-plan-tracker by focusing on team-level metrics (project tracker focuses on deliverables)
- **Hand off to**: agile-coach for team coaching based on tracked insights
- **Receive from**: sdlc-enforcer for compliance data
- **Collaborate with**: enforcement-strategy-advisor on adoption strategies
- **Never overlap with**: project-plan-tracker on project deliverable tracking
