# sdlc-team-pm

Project management, agile coaching, and delivery tracking agents for the AI-First SDLC framework.

## Quick start

```bash
/plugin install sdlc-team-pm@ai-first-sdlc
```

Requires `sdlc-core` to be installed first.

## Agents

| Agent | Purpose |
|-------|---------|
| **agile-coach** | Guides teams through agile adoption and process diagnosis, covering Scrum, Kanban, SAFe, and scaled frameworks, with expertise in sprint planning, retrospective facilitation, DORA/SPACE metrics, team dysfunction resolution (Lencioni model), and AI-augmented velocity recalibration. |
| **delivery-manager** | Orchestrates software delivery from development through production, handling release planning, cross-team dependency management, risk mitigation (ROAM classification), stakeholder communication, go/no-go decisions, and Monte Carlo delivery forecasting. |
| **project-plan-tracker** | Monitors project execution against established plans using earned value management (SPI/CPI), detects schedule slippage through leading indicators, analyses dependency cascades, and generates data-driven status reports with confidence-interval completion forecasts. |
| **retrospective-miner** | Extracts actionable insights from project retrospectives across the organisation, identifies recurring patterns and challenges, quantifies pattern frequency, and proposes concrete framework improvements ranked by impact. |
| **team-progress-tracker** | Measures team performance and health using DORA metrics, SPACE framework, and flow metrics, tracks practice adoption curves (Rogers' model), monitors compliance trends, and generates privacy-respecting team-level health reports. |

## When to use this plugin

Install `sdlc-team-pm` when your project needs:

- **Sprint planning and execution** -- capacity-based planning, velocity
  forecasting, sprint goal focus, scope management, and estimation approach
  selection (story points, t-shirt sizing, no-estimates)
- **Delivery tracking and coordination** -- multi-team release orchestration,
  dependency mapping, critical path analysis, and deployment strategy design
  (canary, blue-green, feature flags)
- **Agile methodology guidance** -- framework selection (Scrum vs Kanban vs
  SAFe vs LeSS), ceremony design, team maturity assessment, and
  transformation roadmaps
- **Retrospective analysis** -- cross-project pattern mining, failure mode
  extraction, anti-pattern identification, and framework improvement proposals
- **Team health measurement** -- DORA metrics, psychological safety assessment,
  Spotify health checks, adoption curve tracking, and balanced scorecards
- **Stakeholder reporting** -- executive dashboards with RAG indicators,
  delivery confidence assessments, risk heat maps, and remediation burndowns
- **Risk management** -- ROAM-classified risk registers, probability-impact
  matrices, contingency planning, and proactive escalation
- **Process improvement** -- measuring improvement velocity, tracking
  retrospective action completion, and identifying systemic delivery bottlenecks

## Agent collaboration

The agents in this plugin work together and with agents from other plugins:

- **agile-coach** diagnoses process problems; **delivery-manager** owns
  execution decisions and stakeholder communication
- **project-plan-tracker** provides objective progress data;
  **delivery-manager** decides corrective actions based on that data
- **retrospective-miner** extracts learning from past work; feeds
  improvements back to **agile-coach** for adoption coaching
- **team-progress-tracker** measures team health and performance; hands
  off to **agile-coach** for coaching interventions when issues are detected
- **delivery-manager** collaborates with `sdlc-team-common` agents
  (solution-architect) for architectural feasibility of delivery strategies
- **delivery-manager** collaborates with `sdlc-team-fullstack` agents
  (devops-specialist) for CI/CD pipeline and deployment coordination
- **team-progress-tracker** collaborates with `sdlc-team-security` agents
  (enforcement-strategy-advisor) on adoption strategies informed by tracking data

## Plugin family

This plugin is part of the AI-First SDLC plugin family. See the
[marketplace](../../.claude-plugin/marketplace.json) for the full list of
available plugins.
