# Deep Research Prompt: Compliance Report Generator Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Compliance Report Generator. This agent will create actionable
SDLC compliance reports tailored to different audiences (team, executive,
technical), generate compliance dashboards, track remediation progress, and
produce audit-ready documentation.

## Research Areas

### 1. Compliance Reporting Best Practices (2025-2026)
- What are current best practices for compliance report design and structure?
- How should reports be tailored for different audiences (executive, team, auditor)?
- What are the latest patterns for automated compliance report generation?
- How do GRC platforms generate compliance reports?
- What are current patterns for real-time compliance dashboards?

### 2. SDLC Compliance Metrics
- What metrics best indicate SDLC process compliance?
- How should code quality, testing, and deployment metrics feed into compliance?
- What are the latest patterns for developer workflow compliance tracking?
- How do organizations track feature proposal and retrospective compliance?
- What are current patterns for branch protection and PR compliance metrics?

### 3. Report Visualization & Communication
- What are current best practices for compliance data visualization?
- How should RAG (Red/Amber/Green) status indicators be designed?
- What are the latest patterns for trend analysis in compliance reporting?
- How should risk scores and compliance gaps be communicated visually?
- What are current patterns for executive summary generation?

### 4. Remediation Tracking
- What are current best practices for tracking compliance remediation?
- How should remediation priorities be assigned and communicated?
- What are the latest patterns for automated remediation workflows?
- How do organizations track time-to-remediation metrics?
- What are current patterns for remediation verification?

### 5. Audit-Ready Documentation
- What makes documentation audit-ready for SOC 2, ISO 27001?
- How should evidence be organized for compliance audits?
- What are the latest patterns for continuous audit readiness?
- How do organizations maintain compliance documentation over time?
- What are current patterns for compliance documentation automation?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Report structures, metrics, visualization, remediation tracking the agent must know
2. **Decision Frameworks**: "When generating report for [audience], include [content] because [reason]"
3. **Anti-Patterns Catalog**: Common reporting mistakes (data overload, vanity metrics, no actionable items, stale reports)
4. **Tool & Technology Map**: Current compliance reporting tools with selection criteria
5. **Interaction Scripts**: How to respond to "generate compliance report", "create executive dashboard", "track our remediation"

## Agent Integration Points

This agent should:
- **Complement**: compliance-auditor by generating reports from audit data
- **Receive from**: compliance-auditor for audit findings and data
- **Collaborate with**: sdlc-enforcer on compliance metrics collection
- **Never overlap with**: compliance-auditor on conducting actual audits
