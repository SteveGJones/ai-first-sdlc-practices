# sdlc-team-common

Cross-cutting specialist agents for architecture, research, performance, and infrastructure.

## Quick start

```bash
/plugin install sdlc-team-common@ai-first-sdlc
```

Requires `sdlc-core` to be installed first.

## Agents

| Agent | Purpose |
|-------|---------|
| `solution-architect` | Designs end-to-end system architectures using TOGAF/C4 frameworks, evaluates distributed systems patterns, and produces architecture decision records for technology selection and migration strategies. |
| `database-architect` | Designs, optimizes, and secures the data layer -- covers database technology selection, schema modeling, query optimization, HA/DR architecture, and compliance implementation across relational, NoSQL, and vector databases. |
| `performance-engineer` | Specializes in load testing strategy, application profiling, bottleneck analysis, Core Web Vitals optimization, Kubernetes autoscaling, and capacity planning using tools like k6, Gatling, and async-profiler. |
| `observability-specialist` | Designs comprehensive observability solutions covering OpenTelemetry instrumentation, distributed tracing, log aggregation, metrics dashboards, SLO/SLI definitions, and alerting strategies with cost management. |
| `deep-research-agent` | Executes systematic web research campaigns from structured prompts, evaluates sources via the CRAAP framework, and produces synthesis documents for downstream agent creation. |
| `repo-knowledge-distiller` | Analyzes repositories and knowledge bases to produce synthesis documents for agent creation via RELIC evaluation and artifact discovery. |
| `agent-builder` | Builds production agents from research via a 6-phase pipeline, including archetype selection, knowledge distillation, and quality validation. |
| `pipeline-orchestrator` | Unified entry point for the agent creation pipeline -- routes web research or repo analysis, runs 1st-party tool discovery, then delegates to agent-builder for construction. |

## Agent details

### Architecture and data

The **solution-architect** provides strategic design authority spanning frontend, backend, data,
infrastructure, and integration layers. It applies TOGAF ADM, C4 model, and ATAM trade-off
analysis to translate business requirements into documented technical solutions with explicit
rationale and alternatives considered.

The **database-architect** covers the full spectrum of data technologies: PostgreSQL, MySQL,
Aurora, MongoDB, DynamoDB, Cassandra, InfluxDB, TimescaleDB, Neo4j, and vector databases
(pgvector, Pinecone, Milvus). It provides decision frameworks for technology selection, indexing
strategy, partitioning, connection pooling, caching, zero-downtime migrations, and compliance
controls for GDPR, HIPAA, and PCI-DSS.

### Performance and observability

The **performance-engineer** handles load testing design (k6, Gatling, Locust), CPU/memory/IO
profiling, database query optimization, Kubernetes autoscaling configuration (HPA, VPA,
Karpenter, KEDA), serverless cold start mitigation, and capacity planning using queueing
theory. It defines performance budgets and integrates testing into CI/CD.

The **observability-specialist** architects telemetry systems around the four pillars: metrics,
logs, traces, and continuous profiling. It covers the Grafana LGTM stack, SigNoz, SLO tooling
(Sloth, Pyrra, Nobl9), multi-window burn-rate alerting, eBPF-based observability (Beyla, Pixie),
and observability cost management including cardinality analysis and FinOps practices.

### Agent creation pipeline

The **pipeline-orchestrator**, **deep-research-agent**, **repo-knowledge-distiller**, and
**agent-builder** form the agent creation pipeline. The orchestrator coordinates end-to-end:
it discovers official 1st-party tools, routes to web research or repository analysis, and
delegates construction to the agent-builder. The deep-research-agent runs systematic CRAAP-scored
web research campaigns. The repo-knowledge-distiller extracts knowledge from codebases using
RELIC evaluation. The agent-builder constructs production agents from synthesis documents using
a 6-phase pipeline with archetype selection and anti-pattern detection.

## When to use this plugin

This plugin is recommended for nearly all projects. It provides foundational capabilities
that other team plugins depend on:

- **Solution architect** for end-to-end system design, technology evaluation, and migration planning.
- **Database architect** for data layer design across PostgreSQL, MongoDB, DynamoDB, vector databases, and more.
- **Performance engineer** for load testing, profiling, capacity planning, and performance SLO compliance.
- **Observability specialist** for telemetry strategy, SLO frameworks, and monitoring platform selection.
- **Deep research agent** and **repo knowledge distiller** for systematic knowledge gathering that feeds the agent creation pipeline.
- **Agent builder** and **pipeline orchestrator** for constructing new specialist agents from research.

Install this plugin whenever any team plugin leaves architectural, performance, or research
gaps. It complements every domain-specific team plugin in the family.

## Universal default

`sdlc-team-common` is a star universal default in the `setup-team` recommendations. When the
setup-team discovery identifies gaps in Section C (areas where custom agents would add value),
this plugin is required because it provides the agent creation pipeline needed to fill those
gaps. It is also recommended whenever cross-cutting architectural or research expertise is
needed alongside domain-specific team plugins.
