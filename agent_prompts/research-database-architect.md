# Deep Research Prompt: Database Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Database Architect. This agent will design data models, select
appropriate database technologies, optimize query performance, plan data
migration strategies, implement data governance, and ensure data reliability
and integrity for projects of all sizes and complexity levels.

The resulting agent should be able to design relational and NoSQL schemas,
evaluate database technology trade-offs (SQL vs NoSQL vs NewSQL), create
indexing and partitioning strategies, plan database migrations, and implement
data security controls when engaged by the development team.

## Context

This agent is needed because the database landscape has evolved dramatically
with cloud-native databases, serverless data platforms, vector databases for AI,
and new approaches to data modeling. The existing agent has a good competency
list but reads more like a resume than a decision-making expert. It lacks
deep methodology, specific decision frameworks, and current best practices
for modern database technologies. The backend-architect covers application
architecture, but this agent owns the data layer end-to-end.

## Research Areas

### 1. Modern Database Technology Landscape (2025-2026)
- What is the current state of database technology? (PostgreSQL, MySQL, SQL Server, Oracle)
- How have cloud-native databases evolved (Aurora, CockroachDB, PlanetScale, Neon)?
- What are the latest developments in NewSQL databases (TiDB, YugabyteDB, CockroachDB)?
- How have vector databases evolved for AI workloads (Pinecone, Weaviate, pgvector, Milvus)?
- What is the current state of serverless database platforms?

### 2. Data Modeling Best Practices
- What are current best practices for relational data modeling (normalization vs denormalization trade-offs)?
- How should architects design document models for MongoDB, DynamoDB?
- What are the latest patterns for graph data modeling (Neo4j, Neptune)?
- How should time-series data be modeled (InfluxDB, TimescaleDB)?
- What are current patterns for data vault and dimensional modeling for analytics?

### 3. Database Performance Optimization
- What are the current best practices for query optimization and execution plan analysis?
- How should architects design indexing strategies (B-tree, hash, GiST, GIN, partial, covering)?
- What are current patterns for database partitioning and sharding?
- How do connection pooling solutions compare (PgBouncer, ProxySQL, cloud-native)?
- What are the latest patterns for caching architectures (Redis, Memcached, application-level)?

### 4. High Availability & Disaster Recovery
- What are current best practices for database replication (synchronous vs async, multi-primary)?
- How should organizations design for zero-downtime database migrations?
- What are the latest patterns for cross-region database deployment?
- How do managed database services handle HA (RDS Multi-AZ, Cloud SQL HA, Aurora Global)?
- What are current RPO/RTO targets and how to achieve them?

### 5. Database Security & Compliance
- What are current best practices for database encryption (at rest, in transit, application-level)?
- How should organizations implement row-level security and dynamic data masking?
- What are the latest patterns for database audit logging and compliance?
- How do GDPR, CCPA, and other privacy regulations impact database design?
- What are current best practices for database access control and privilege management?

### 6. Data Migration & Schema Evolution
- What are the current best practices for schema migration tools (Flyway, Liquibase, Atlas)?
- How should organizations plan large-scale data migrations between database platforms?
- What are current patterns for zero-downtime schema changes?
- How do blue-green database deployments work?
- What are the latest patterns for dual-write and change data capture (Debezium)?

### 7. Cloud Database Patterns
- How should architects choose between managed vs self-managed databases?
- What are the latest patterns for multi-cloud database strategies?
- How do serverless databases (Aurora Serverless, Neon, PlanetScale) work and when to use them?
- What are current patterns for database cost optimization in the cloud?
- How should database architects leverage cloud-specific features (read replicas, global tables)?

### 8. AI/ML Database Patterns (Emerging)
- How are vector databases being used for RAG and semantic search?
- What are current patterns for feature stores and ML data pipelines?
- How should databases handle embeddings and vector similarity search?
- What are the implications of AI workloads on database architecture?
- How do graph databases support knowledge graphs for AI systems?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Database technologies, data modeling patterns, performance optimization techniques, HA/DR strategies the agent must know
2. **Decision Frameworks**: "When designing data storage for [workload type] with [requirements], recommend [technology/pattern] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common database mistakes (using a single database for everything, premature denormalization, missing indexes, unbounded queries, N+1 patterns, god tables)
4. **Tool & Technology Map**: Current database technologies, management tools, migration tools, monitoring solutions with selection criteria
5. **Interaction Scripts**: How to respond to "design our database schema", "should we use SQL or NoSQL?", "our queries are slow", "plan a database migration"

## Agent Integration Points

This agent should:
- **Complement**: backend-architect by owning the data layer (backend-architect owns application architecture patterns)
- **Hand off to**: security-architect for comprehensive data security policies
- **Receive from**: solution-architect for data requirements and constraints
- **Collaborate with**: performance-engineer on query optimization and load testing
- **Never overlap with**: backend-architect on application-level data access patterns (ORM, repository layer)
