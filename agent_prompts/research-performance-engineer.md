# Deep Research Prompt: Performance Engineer Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Performance Engineer. This agent will design and execute
performance testing strategies, conduct capacity planning, identify and
resolve performance bottlenecks, optimize system throughput and latency,
and ensure applications meet performance SLAs and SLOs.

The resulting agent should be able to design load testing strategies,
interpret performance profiles, recommend optimization techniques,
create capacity models, and establish performance budgets when engaged
by the development team.

## Context

This agent is needed because performance engineering has evolved significantly
with cloud-native architectures, microservices, and modern observability tools.
The existing agent has basic performance testing and optimization knowledge but
lacks depth on modern profiling tools, cloud-specific performance patterns,
AI-driven performance optimization, and comprehensive capacity planning
methodologies. The sre-specialist handles production reliability, but this
agent owns performance testing, profiling, and optimization.

## Research Areas

### 1. Performance Testing Methodologies (2025-2026)
- What are the current best practices for load testing, stress testing, and soak testing?
- How have performance testing tools evolved (k6, Gatling, Locust, Artillery)?
- What are the latest patterns for performance testing in CI/CD pipelines?
- How should organizations approach performance testing for microservices?
- What are current best practices for API performance testing and benchmarking?

### 2. Application Profiling & Bottleneck Analysis
- What are the current best practices for CPU, memory, and I/O profiling?
- How do modern profiling tools work (async-profiler, py-spy, perf, eBPF)?
- What are current patterns for distributed tracing-based performance analysis?
- How should engineers analyze garbage collection and memory management?
- What are the latest techniques for database query performance analysis?

### 3. Web Performance Optimization (Current State)
- What are the current Core Web Vitals metrics and targets?
- How have browser rendering optimization techniques evolved?
- What are the latest patterns for image, font, and asset optimization?
- How should organizations implement edge computing for performance?
- What are current best practices for progressive web app performance?

### 4. Backend & Database Performance
- What are current patterns for query optimization across SQL and NoSQL databases?
- How should engineers optimize connection pooling, caching, and serialization?
- What are the latest patterns for async processing and non-blocking I/O?
- How do modern message queue and event streaming systems impact performance?
- What are current best practices for N+1 query detection and resolution?

### 5. Cloud-Native Performance Patterns
- How should organizations optimize performance in containerized environments?
- What are current patterns for Kubernetes resource management and autoscaling?
- How do serverless cold starts impact performance and how to mitigate them?
- What are the latest patterns for multi-region and edge performance optimization?
- How should teams approach cloud cost vs performance trade-offs?

### 6. Capacity Planning & Performance Modeling
- What are current methodologies for capacity planning (analytical modeling, simulation)?
- How should organizations model performance for growth projections?
- What tools exist for capacity planning and performance prediction?
- How do teams establish performance budgets and enforce them?
- What are current patterns for auto-scaling based on predictive models?

### 7. Performance Observability & Monitoring
- What are current best practices for performance monitoring in production?
- How should teams set up performance dashboards and alerting?
- What are the latest patterns for Real User Monitoring (RUM)?
- How do synthetic monitoring and continuous performance validation work?
- What are current best practices for performance regression detection?

### 8. AI-Driven Performance Optimization (Emerging)
- How is AI/ML being used for performance anomaly detection?
- What are current patterns for AI-assisted capacity planning?
- How do AI tools help with automated performance tuning?
- What are the implications of LLM workloads on performance engineering?
- How should organizations performance-test AI/ML inference systems?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Performance testing methodologies, profiling techniques, optimization patterns, capacity planning models the agent must know
2. **Decision Frameworks**: "When facing [performance issue type] in [system type], investigate [approach] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common performance mistakes (premature optimization, testing in non-production environments, ignoring P99, over-caching, N+1 queries)
4. **Tool & Technology Map**: Current performance tools (testing, profiling, monitoring, analysis) with selection criteria
5. **Interaction Scripts**: How to respond to "our API is slow", "plan for 10x traffic growth", "set up performance testing", "optimize our database queries"

## Agent Integration Points

This agent should:
- **Complement**: sre-specialist by owning pre-production performance (SRE owns production reliability)
- **Hand off to**: database-architect for deep database optimization, backend-architect for system design changes
- **Receive from**: solution-architect for performance requirements and SLA targets
- **Collaborate with**: devops-specialist on performance testing in CI/CD pipelines
- **Never overlap with**: observability-specialist on monitoring infrastructure setup
