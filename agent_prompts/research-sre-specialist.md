# Deep Research Prompt: SRE Specialist Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Site Reliability Engineer (SRE). This agent will design
reliability strategies, define SLOs/SLIs/error budgets, lead incident response,
implement chaos engineering, and ensure production systems maintain target
availability and performance levels.

The resulting agent should be able to define SLO frameworks, design incident
response runbooks, recommend reliability improvements, conduct postmortems,
and implement chaos engineering practices when engaged by the development team.

## Context

This agent is needed because site reliability engineering has matured significantly
with platform engineering, AI-driven operations, and formal SLO frameworks becoming
industry standard. The existing agent has basic monitoring and incident response
knowledge but lacks depth on modern SRE practices, error budget policies, chaos
engineering methodologies, and the Google/Netflix/Meta SRE frameworks. The
devops-specialist owns the delivery pipeline; this agent owns production reliability.

## Research Areas

### 1. SLO/SLI/Error Budget Frameworks (2025-2026)
- What are current best practices for defining SLOs and SLIs?
- How do organizations implement error budget policies effectively?
- What tools support SLO tracking and alerting (Nobl9, Sloth, Pyrra)?
- How should SLOs cascade from business objectives to technical metrics?
- What are common mistakes in SLO definition and how to avoid them?

### 2. Incident Management & Response
- What are current best practices for incident response frameworks?
- How have incident management tools evolved (PagerDuty, Opsgenie, Incident.io, Rootly)?
- What are the latest patterns for on-call rotation and escalation?
- How should organizations conduct blameless postmortems?
- What are current practices for incident severity classification and communication?

### 3. Chaos Engineering & Resilience Testing
- What is the current state of chaos engineering tools (Gremlin, Litmus, Chaos Monkey, Toxiproxy)?
- How should organizations start a chaos engineering practice safely?
- What are current patterns for game days and failure injection testing?
- How does chaos engineering integrate with CI/CD pipelines?
- What are the latest resilience testing patterns for distributed systems?

### 4. Production Monitoring & Alerting
- What are current best practices for monitoring strategy (USE, RED, golden signals)?
- How should organizations implement alert management to avoid fatigue?
- What are the latest patterns for synthetic monitoring and health checks?
- How do modern observability platforms support SRE workflows?
- What are current best practices for log aggregation and analysis?

### 5. Reliability Architecture Patterns
- What are current patterns for circuit breakers, retries, and timeouts in distributed systems?
- How should organizations implement graceful degradation and load shedding?
- What are the latest patterns for multi-region and active-active architectures?
- How do service mesh technologies improve reliability?
- What are current patterns for database reliability and failover?

### 6. Capacity Planning & Scaling
- What are current best practices for production capacity planning?
- How should organizations implement auto-scaling strategies (predictive vs reactive)?
- What are the latest patterns for traffic management and load balancing?
- How do organizations plan for organic growth vs burst traffic?
- What are current patterns for resource right-sizing and cost optimization?

### 7. Toil Reduction & Automation
- How do SRE teams measure and reduce toil in 2025-2026?
- What are current patterns for runbook automation and self-healing systems?
- How should organizations balance reliability work vs feature development?
- What tools support SRE automation (Ansible, Rundeck, StackStorm)?
- What are current best practices for infrastructure self-service?

### 8. AI-Augmented SRE (Emerging)
- How is AI being used for anomaly detection in production systems?
- What are current patterns for AI-assisted incident diagnosis?
- How do AIOps platforms support SRE workflows?
- What are the latest patterns for predictive alerting and auto-remediation?
- How should SRE teams leverage LLMs for operational tasks?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: SRE principles, SLO frameworks, incident response procedures, chaos engineering methodologies, reliability patterns the agent must know
2. **Decision Frameworks**: "When reliability target is [X] for [system type], implement [pattern] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common SRE mistakes (alert fatigue, hero culture, undefined SLOs, reactive-only operations, reliability theater)
4. **Tool & Technology Map**: Current SRE tools (monitoring, incident management, chaos engineering, SLO tracking) with selection criteria
5. **Interaction Scripts**: How to respond to "we need 99.99% uptime", "help with our incident response", "set up chaos engineering", "reduce operational toil"

## Agent Integration Points

This agent should:
- **Complement**: devops-specialist by owning production reliability (DevOps owns delivery pipeline, SRE owns production operations)
- **Hand off to**: performance-engineer for pre-production performance optimization
- **Receive from**: solution-architect for reliability requirements and SLA targets
- **Collaborate with**: observability-specialist on monitoring and alerting strategy
- **Never overlap with**: devops-specialist on CI/CD pipeline design and deployment automation
