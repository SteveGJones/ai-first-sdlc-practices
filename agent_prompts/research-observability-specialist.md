# Deep Research Prompt: Observability Specialist Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an Observability Specialist. This agent will design comprehensive
observability solutions using OpenTelemetry, implement distributed tracing and
log aggregation, define SLO/SLI frameworks, create intelligent alerting strategies,
and manage observability costs for distributed systems.

The resulting agent should be able to instrument applications with OpenTelemetry,
design trace sampling strategies, establish SLO/SLI aligned with business goals,
reduce alert fatigue through intelligent alerting, and optimize observability
costs when engaged by the development team.

## Context

This agent is needed because modern distributed systems require correlated
observability across metrics, logs, and traces. The existing agent catalog has
sre-specialist for reliability engineering and devops-specialist for infrastructure,
but lacks a dedicated observability expert who understands instrumentation
strategies, telemetry pipeline design, and the economics of observability data.

## Research Areas

### 1. OpenTelemetry (Current State 2025-2026)
- What is the current OTel specification status for traces, metrics, and logs?
- How have OTel SDKs evolved across languages (auto-instrumentation maturity)?
- What are the current OTel Collector deployment patterns (agent vs gateway)?
- How should OTel sampling strategies be configured (head-based, tail-based, adaptive)?
- What are the current OTel semantic conventions and their adoption?

### 2. Distributed Tracing (Production Patterns)
- What are the current tracing backend options (Jaeger, Tempo, Honeycomb, Lightstep)?
- How should context propagation work across async boundaries (message queues, events)?
- What are the current trace sampling strategies and their cost/visibility trade-offs?
- How should service dependency maps be generated from trace data?
- What are the current patterns for business-context enrichment of traces?

### 3. Log Aggregation (2025-2026 Landscape)
- How has Grafana Loki evolved compared to Elasticsearch/OpenSearch?
- What are the current structured logging best practices across languages?
- How should log correlation with traces be implemented (trace ID injection)?
- What are the current log processing pipeline patterns (Fluent Bit, Vector, Logstash)?
- How should log volume and cost be managed in high-throughput systems?

### 4. Metrics and Dashboards (Current Best Practices)
- What is the current Prometheus ecosystem (Mimir, Thanos, VictoriaMetrics)?
- How should metric cardinality be managed to control costs?
- What are the current Grafana dashboard design best practices?
- How should custom metrics be designed (histograms vs summaries, label strategies)?
- What are the current PromQL/LogQL query optimization techniques?

### 5. SLO/SLI Definition (Practical Implementation)
- How are organizations implementing SLOs in practice (not just theory)?
- What tools exist for SLO tracking (Sloth, OpenSLO, Nobl9, Dynatrace)?
- How should error budgets be calculated and used for decision-making?
- What are the current approaches to multi-signal SLOs (combining latency + error rate)?
- How should SLOs be communicated to non-technical stakeholders?

### 6. Alerting Strategy (Noise Reduction)
- What are the current best practices for alert design (symptom vs cause)?
- How should alert correlation and suppression be implemented?
- What tools support intelligent alert grouping (PagerDuty AIOps, Opsgenie)?
- How should on-call rotations be designed to minimize burnout?
- What metrics should be tracked for alert effectiveness (MTTA, MTTR, false positive rate)?

### 7. Observability Cost Management
- What are the current observability vendor pricing models and hidden costs?
- How should intelligent sampling reduce costs while maintaining visibility?
- What are the current approaches to data tiering (hot/warm/cold storage)?
- How do open-source observability stacks compare to commercial tools on TCO?
- What tools exist for observability cost tracking and optimization?

### 8. Incident Response Integration
- How should observability data be pre-populated in incident channels?
- What are the current patterns for automated incident detection from telemetry?
- How should post-incident reviews leverage observability data for timelines?
- What are the current patterns for synthetic monitoring and proactive detection?
- How should runbooks be linked to alerts and dashboards?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: OTel instrumentation patterns, tracing architecture, SLO/SLI frameworks, and alerting strategies
2. **Decision Frameworks**: "When monitoring [system type], use [approach] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common observability mistakes (high cardinality metrics, alert fatigue, unsampled traces, uncorrelated logs)
4. **Tool & Technology Map**: Tracing backends, log aggregators, metrics stores, and alerting platforms with selection criteria
5. **Interaction Scripts**: How to respond to "we can't find the bottleneck", "too many alerts", "observability costs too much"

## Agent Integration Points

This agent should:
- **Complement**: sre-specialist by providing observability implementation while SRE focuses on reliability practices and incident response
- **Hand off to**: performance-engineer for application-level performance tuning based on observability data
- **Receive from**: backend-architect when system designs need observability architecture
- **Collaborate with**: devops-specialist on observability tooling deployment and cloud-architect on cloud monitoring
- **Never overlap with**: sre-specialist on incident management processes or on-call scheduling
