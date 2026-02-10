# Deep Research Prompt: Backend Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Backend Architect. This agent will design scalable, resilient,
and maintainable backend systems, evaluate architectural trade-offs between
monolith and microservices, implement event-driven patterns, design caching
strategies, and guide database selection decisions.

The resulting agent should be able to evaluate monolith vs microservices
trade-offs for specific contexts, design event-driven systems with CQRS
and saga patterns, architect multi-layer caching strategies, and establish
resilience patterns when engaged by the development team.

## Context

This agent is needed because backend architecture decisions have long-lasting
consequences on system scalability, team productivity, and operational costs.
The existing agent catalog has solution-architect for high-level design and
database-architect for data layer specifics, but lacks a dedicated backend
architect who bridges the gap between system design and implementation
patterns for distributed services.

## Research Areas

### 1. Microservices vs Monolith (Current Industry Data)
- What does current industry data (2025-2026) say about microservices adoption and failures?
- What are the real-world costs of microservices (operational complexity, latency, debugging)?
- How are modular monoliths being adopted as a middle ground?
- What team size and organizational maturity thresholds justify microservices?
- What are the current patterns for migrating monolith to microservices (Strangler Fig)?

### 2. Event-Driven Architecture (Production Patterns)
- What are the current best practices for event sourcing in production systems?
- How should event schema evolution be managed (Avro, Protobuf, JSON Schema)?
- What are the current patterns for saga orchestration vs choreography?
- How should outbox pattern and transactional messaging be implemented?
- What are the current dead letter queue and poison message handling patterns?

### 3. Message Broker Selection (2025-2026)
- How do Kafka, RabbitMQ, NATS, and Pulsar compare for different workloads?
- What are the current best practices for Kafka topic design and partitioning?
- How should message ordering, deduplication, and exactly-once semantics be achieved?
- What are the current patterns for event streaming vs traditional queuing?
- How do cloud-native options (SQS/SNS, Azure Service Bus, GCP Pub/Sub) compare?

### 4. Caching Strategies (Current Best Practices)
- What are the current multi-layer caching patterns (CDN, application, database)?
- How should cache invalidation be handled in distributed systems?
- What are the current Redis vs Memcached vs embedded cache trade-offs?
- How should cache warming, stampede prevention, and write-behind patterns be implemented?
- What are the current patterns for caching in microservices with shared state?

### 5. Database Selection and Patterns
- How should polyglot persistence be approached in 2025-2026?
- What are the current best practices for database-per-service in microservices?
- How should distributed transactions be handled (Saga, 2PC, eventual consistency)?
- What are the current patterns for read replicas, sharding, and connection pooling?
- How do NewSQL databases (CockroachDB, TiDB, YugabyteDB) compare to traditional options?

### 6. Resilience and Reliability Patterns
- What are the current best practices for circuit breaker implementation (Resilience4j, Polly)?
- How should retry policies with exponential backoff and jitter be designed?
- What are the current bulkhead and rate limiting patterns for backend services?
- How should graceful degradation and feature flags be combined?
- What are the current chaos engineering practices for backend systems?

### 7. Backend Observability
- How should distributed tracing be implemented across microservices (OpenTelemetry)?
- What are the current structured logging best practices for backend services?
- How should health checks (liveness, readiness, startup) be designed?
- What are the current RED/USE method implementations for service monitoring?
- How should SLO/SLI be defined for backend services?

### 8. Scalability Patterns (Current Approaches)
- What are the current horizontal scaling patterns for stateless services?
- How should auto-scaling be configured for different workload types?
- What are the current connection pooling and resource management patterns?
- How should background job processing be architected (Celery, Bull, Temporal)?
- What are the current patterns for handling traffic spikes and load shedding?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Architectural patterns, event-driven design, caching strategies, database selection criteria, and resilience patterns
2. **Decision Frameworks**: "When [scale/team/requirements], choose [architecture] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common backend architecture mistakes (distributed monolith, shared database, chatty services)
4. **Tool & Technology Map**: Message brokers, caching solutions, databases, and resilience libraries with selection criteria
5. **Interaction Scripts**: How to respond to "should we use microservices", "design our caching strategy", "our system can't handle the load"

## Agent Integration Points

This agent should:
- **Complement**: api-architect by handling internal architecture while api-architect focuses on interface design
- **Hand off to**: database-architect for deep database schema optimization and query tuning
- **Receive from**: solution-architect for system-wide architectural constraints
- **Collaborate with**: devops-specialist on deployment architecture and sre-specialist on reliability
- **Never overlap with**: api-architect on API contract design or database-architect on query optimization
