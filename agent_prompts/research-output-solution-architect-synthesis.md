## Synthesis

### 1. Core Knowledge Base

**Architecture Frameworks**

- **C4 Model (Context, Containers, Components, Code)**: The pragmatic standard for architecture diagrams in agile organizations. Four hierarchical levels from system context to code details. Tool-agnostic, living documentation approach. [Source: https://c4model.com/] [Confidence: HIGH]

- **TOGAF ADM**: Useful as mental model, rarely followed rigidly. Extract specific artifacts (capability assessments, gap analysis, migration roadmaps) rather than full implementation. Better for enterprise transformations than product development. [Source: https://pubs.opengroup.org/togaf-standard/] [Confidence: MEDIUM]

- **Architecture Decision Records (ADRs)**: Lightweight (1-page) records capturing context, decision, and consequences for significant structural decisions. Stored in Git at `/docs/architecture/decisions/`. Never delete superseded ADRs; mark status and reference replacement. [Source: Nygard, 2011] [Confidence: HIGH]

- **Evolutionary Architecture**: Architecture fitness functions automate governance. Encode architecture constraints as automated tests in CI/CD. Examples: dependency rules, performance thresholds, security scans. [Source: Ford et al., Building Evolutionary Architectures, 2017] [Confidence: MEDIUM]

**Distributed Systems Patterns**

- **Modular Monolith First**: Start with single deployment unit with strong internal module boundaries. Extract microservices only when evidence demands it (team scaling >30 engineers, independent scaling needs, technology heterogeneity, deployment independence). [Source: Fowler, "MonolithFirst", 2015] [Confidence: HIGH]

- **Distributed Monolith Anti-Pattern**: Microservices with tight coupling (shared database, synchronous call chains 5+ services deep, coordinated deployments). All complexity, no benefits. [Source: Newman, Building Microservices, 2021] [Confidence: HIGH]

- **Event Sourcing + CQRS**: Event sourcing stores state as append-only event log. Use when: audit trail required, temporal queries needed, multiple read models. CQRS separates write and read models. Use when: read patterns fundamentally different from write patterns. [Source: Fowler, "CQRS", 2011] [Confidence: HIGH]

- **Saga Patterns**: Orchestration sagas (central coordinator) for complex workflows (5+ steps). Choreography sagas (event-driven, decentralized) for simple chains (2-3 steps). [Source: Richardson, Microservices Patterns] [Confidence: MEDIUM]

- **Service Mesh**: Infrastructure layer (Istio, Linkerd) for service-to-service communication. Use when: 20+ microservices, need uniform security/observability, polyglot environment. Overkill when: <10 services, team lacks Kubernetes expertise, 1-5ms latency unacceptable. [Source: https://istio.io/] [Confidence: MEDIUM]

- **CAP Theorem**: Choose consistency or availability during partitions. Modern interpretation: CAP is spectrum; tune consistency level per operation. Strong consistency (Raft, Paxos) for account balances. Eventual consistency for social feeds. [Source: Brewer, "CAP Twelve Years Later", 2012] [Confidence: HIGH]

**Scalability Principles**

- **The 10x Rule**: Design for 10x current scale, not 100x. Re-architect at each 10x milestone rather than over-engineering. [Source: Multiple AWS re:Invent talks] [Confidence: HIGH]

- **Vertical then Horizontal**: Start vertical scaling (larger machines), go horizontal for stateless tiers (app servers), stay vertical for stateful as long as possible (databases before sharding). [Source: Kleppmann, Designing Data-Intensive Applications, 2017] [Confidence: HIGH]

- **Multi-Tier Caching**: Tier 1 CDN (90%+ hit rate, hours-days TTL), Tier 2 Application cache (60-80% hit rate, minutes-hours TTL), Tier 3 Database cache (40-60% hit rate, seconds-minutes TTL). [Source: Multiple industry sources] [Confidence: HIGH]

- **P99 Latency Focus**: Tail latency matters more than average. If 1% of requests are slow and users make 100 requests/session, every user experiences slowness. Techniques: minimize hops, connection pooling, async I/O, aggressive timeouts, circuit breakers. [Source: Dean & Barroso, "The Tail at Scale", 2013] [Confidence: MEDIUM]

- **Polyglot Persistence**: Use specialized databases for specialized needs. PostgreSQL for ACID transactions, Elasticsearch for full-text search, Neo4j for graph, Redis for caching. Anti-pattern: 5 databases for simple app. [Source: Kleppmann, 2017] [Confidence: HIGH]

**Migration Strategies**

- **Strangler Fig Pattern**: Incrementally replace monolith with microservices over 18-36 months. Facade routes traffic to monolith or microservice based on migration status. Low-risk, reversible. [Source: Fowler, "StranglerFigApplication", 2004/2019] [Confidence: HIGH]

- **7 R's of Cloud Migration**: Retire, Retain, Rehost, Replatform, Repurchase, Re-architect, Refactor. Decision: Business criticality + Technical debt → Strategy. [Source: Gartner framework] [Confidence: MEDIUM]

- **Database Migration with CDC**: Change Data Capture (Debezium, AWS DMS) for zero-downtime migration. Dual-write pattern when CDC unavailable. [Source: https://debezium.io/] [Confidence: MEDIUM]

**Architecture Quality**

- **Coupling Metrics**: Instability I = Ce/(Ca+Ce). Core modules should have low instability (0.0-0.3). Interface modules high instability (0.7-1.0). [Source: Martin, Clean Architecture, 2017] [Confidence: MEDIUM]

- **Four Golden Signals**: Latency, Traffic, Errors, Saturation. Architecture observability requires service dependency visualization, distributed tracing, error budgets. [Source: Google SRE Book] [Confidence: HIGH]

- **Architecture Fitness Functions**: Automated tests verifying architectural characteristics (dependency rules, performance SLOs, security compliance). Encoded in CI/CD pipelines. [Source: Ford et al., 2017] [Confidence: MEDIUM]

**AI/ML System Architecture**

- **MLOps Components**: Data pipeline, Feature store, Model training, Model registry, Model serving, Monitoring. Key challenges: data versioning, model drift, feature-serving latency, training-serving skew. [Source: Huyen, Designing Machine Learning Systems, 2022] [Confidence: MEDIUM]

- **RAG (Retrieval-Augmented Generation)**: Query → Embed → Vector search → Inject docs into prompt → Generate grounded answer. Reduces hallucination, provides citations. Components: vector DB (Pinecone, Weaviate), embedding model, chunking strategy. [Source: LangChain documentation] [Confidence: HIGH]

- **LLM Gateway Pattern**: Centralized gateway for LLM calls providing rate limiting, cost tracking, PII filtering, caching. Controls costs and security across organization. [Source: LangChain, industry patterns] [Confidence: MEDIUM]

---

### 2. Decision Frameworks

**When designing a distributed system**, evaluate based on:
- **Team size**: <10 engineers → Modular monolith. 10-30 engineers → Selective microservices. >30 engineers → Microservices architecture.
- **Scaling needs**: Uniform scaling → Monolith. Differential scaling (checkout 20x catalog) → Microservices.
- **Deployment frequency**: Quarterly releases → Monolith acceptable. Daily deployments per team → Microservices enable independence.
- **Technology diversity**: Single stack → Monolith simpler. Polyglot needs (Rust for performance, Python for ML) → Microservices.
[Source: Newman, Building Microservices, 2021] [Confidence: HIGH]

**When choosing consistency model** for data:
- **Financial transactions, inventory where overselling unacceptable** → Strong consistency (Raft/Paxos consensus).
- **Social media feeds, product catalog, user profiles** → Eventual consistency.
- **User seeing their own updates** → Read-your-writes consistency (session affinity).
- **Collaborative editing, conflict resolution needed** → CRDTs (Conflict-free Replicated Data Types).
[Source: Kleppmann, 2017; Brewer, 2012] [Confidence: HIGH]

**When evaluating technology stack**, use RISKS framework:
- **R (Recency)**: <1 year = very high risk, 1-3 years = high risk, 3-5 years = medium, 5+ years = low risk.
- **I (Investment)**: Foundation (CNCF, Apache) = lowest risk. Multiple companies = medium. Single company = higher risk.
- **S (Skill availability)**: Check job postings, Stack Overflow survey, bootcamp curricula.
- **K (Knowledge resources)**: Evaluate docs, Stack Overflow questions, courses, books.
- **S (Switching cost)**: Assess data export, API compatibility, cloud lock-in.
Total score: 5-10 = safe, 11-15 = acceptable for non-critical, 16-20 = high risk, 21-25 = avoid.
[Source: Composite framework from multiple sources] [Confidence: MEDIUM]

**When deciding Build vs Buy vs Rent**:
- **Core competitive advantage** → BUILD (e.g., recommendation algorithm for Netflix).
- **Undifferentiated heavy lifting** → RENT/BUY (e.g., authentication, email sending).
- **Off-the-shelf meets 80%+ requirements** → BUY/RENT.
- **Need deep customization** → BUILD.
- **Your scale exceeds vendor pricing efficiency** → BUILD (e.g., Dropbox storage at massive scale).
Alternative: DIH Test—will maintaining this provide continuous learning to team? If no, buy.
[Source: Hohpe, The Architect Elevator, 2020] [Confidence: HIGH]

**When planning cloud migration** (7 R's):
- **Business criticality HIGH + Technical debt HIGH** → Re-architect (cloud-native redesign).
- **Business criticality HIGH + Technical debt LOW** → Replatform (minor optimizations).
- **Business criticality LOW + Technical debt HIGH** → Repurchase (move to SaaS) or Retire.
- **Business criticality LOW + Technical debt LOW** → Retain (keep on-prem) or Rehost (lift-and-shift).
[Source: Gartner 7 R's framework] [Confidence: MEDIUM]

**When choosing between Lambda and Kappa architecture** for data-intensive systems:
- **Need both real-time dashboards AND accurate historical reports** → Lambda (separate batch and stream processing).
- **Prefer operational simplicity, stream processing can handle scale** → Kappa (streaming only).
- **Team has strong batch processing expertise, weak streaming** → Lambda.
- **Building new system with modern team** → Kappa (avoid dual code paths).
[Source: Kreps, "Questioning Lambda Architecture", 2014; Marz, Big Data, 2015] [Confidence: MEDIUM]

**When implementing service mesh**:
- **>20 microservices with complex communication** → Service mesh justified.
- **Need mTLS, uniform policies across polyglot services** → Service mesh provides value.
- **<10 microservices** → Use client libraries (Resilience4j, Polly) instead; simpler.
- **Team lacks Kubernetes/ops expertise** → Service mesh adds operational burden; avoid until ready.
- **Latency-critical path where 1-5ms matters** → Service mesh overhead unacceptable; optimize differently.
[Source: Istio documentation, industry patterns] [Confidence: MEDIUM]

**When designing caching strategy**:
- **Static assets (images, CSS, JS)** → CDN cache, hours-days TTL, 90%+ hit rate target.
- **Database query results** → Application cache (Redis), minutes-hours TTL, 60-80% hit rate.
- **Computed data expensive to generate** → Cache-aside pattern with explicit invalidation.
- **Strong consistency required** → Write-through caching (sync write to cache and DB).
- **High write throughput acceptable** → Write-behind caching (async DB write, risk of data loss).
[Source: Multiple industry sources] [Confidence: HIGH]

**When integrating LLMs into architecture**:
- **High-volume, cost-sensitive** → Use smaller model (GPT-3.5 vs GPT-4), aggressive prompt caching, RAG to avoid fine-tuning.
- **Domain-specific language, privacy requirements** → Fine-tune smaller model, deploy on-prem.
- **Need grounding in company docs** → RAG pattern (vector DB + retrieval + prompt injection).
- **Multiple LLM use cases across org** → LLM gateway for rate limiting, cost tracking, security.
- **Latency-sensitive user experience** → Design async UX; LLM inference 200ms-10s.
[Source: LangChain docs, Huyen 2022] [Confidence: MEDIUM]

**When facing monolith-to-microservices decision**:
- **Have >30 engineers struggling with coordination** → Extract microservices for team autonomy.
- **Need to scale components independently** → Extract high-load components (e.g., checkout).
- **Different tech stacks needed** (e.g., ML model in Python, core in Java) → Extract to separate services.
- **Team <10 engineers, uniform scaling needs** → Stay with modular monolith; microservices overhead unjustified.
**Migration pattern**: Use Strangler Fig (18-36 months), not big-bang rewrite.
[Source: Fowler, Newman] [Confidence: HIGH]

---

### 3. Anti-Patterns Catalog

**Big Ball of Mud**
- **What it looks like**: No discernible architecture, tangled dependencies, no module boundaries, everything depends on everything.
- **Why it's harmful**: Impossible to reason about, changes ripple unpredictably, testing requires entire system, onboarding takes months.
- **What to do instead**: Define module boundaries, enforce dependency rules (ArchUnit), create C4 diagrams, write ADRs for structure. If too far gone, use Strangler Fig to incrementally replace.
[Source: Foote & Yoder, "Big Ball of Mud", 1999] [Confidence: HIGH]

**Distributed Monolith**
- **What it looks like**: Microservices that share database, synchronous call chains 5+ services deep, coordinated deployments (all services must deploy together).
- **Why it's harmful**: All the operational complexity of microservices (network failures, distributed debugging, eventual consistency) with none of the benefits (independent deployment, scaling, team autonomy).
- **What to do instead**: If services must coordinate, keep them together in a modular monolith. If truly need microservices, enforce bounded contexts with database-per-service, async messaging, and independent deployments.
[Source: Newman, 2021] [Confidence: HIGH]

**Resume-Driven Development (Technology Chasing)**
- **What it looks like**: Adopting technologies because they're trendy (blockchain for non-distributed-trust problems, GraphQL for simple CRUD, Kubernetes for single app).
- **Why it's harmful**: Learning curve slows delivery, complexity exceeds benefit, team lacks expertise, future maintainers inherit unfamiliar stack.
- **What to do instead**: Use RISKS framework for technology evaluation. Choose Horizon 1 (proven) tech for core systems. Horizon 2/3 tech only for clear advantages. Ask: "What problem does this solve that our current stack doesn't?"
[Source: Industry term, multiple sources] [Confidence: HIGH]

**Golden Hammer (One-Size-Fits-All)**
- **What it looks like**: Using same technology for every problem (every problem is a nail when you have a hammer). Examples: relational DB for time-series data, REST for real-time bidirectional comms, microservices for every new project.
- **Why it's harmful**: Suboptimal solutions, fighting against tool's design, missing purpose-built alternatives.
- **What to do instead**: Polyglot persistence (right database for each use case), polyglot architecture (different patterns for different needs). Evaluate alternatives for each significant decision using weighted criteria matrix.
[Source: Hunt & Thomas, The Pragmatic Programmer] [Confidence: HIGH]

**Premature Optimization / Premature Distribution**
- **What it looks like**: Microservices from day one for a startup with 2 engineers. Sharding database before 100K rows. Implementing complex caching before measuring performance.
- **Why it's harmful**: Complexity now, benefit maybe never (most startups don't reach massive scale). Time spent optimizing could build features.
- **What to do instead**: Follow the 10x Rule—design for 10x current scale. Measure before optimizing. Start with modular monolith, extract microservices when evidence demands. Vertical scale before horizontal. Add complexity only when needed.
[Source: Knuth, "Premature optimization is the root of all evil"] [Confidence: HIGH]

**Big Bang Rewrite**
- **What it looks like**: "Throw away the legacy system, rewrite from scratch." 2-3 year rewrite project with no intermediate deliveries.
- **Why it's harmful**: Requirements change during multi-year rewrite, original system knowledge lost, business can't wait years for new features, morale plummets. History: Netscape rewrite killed the company.
- **What to do instead**: Strangler Fig pattern (incremental replacement over 18-36 months). API facade pattern (modern API over legacy internals). Refactor in parallel with feature delivery.
[Source: Fowler, Newman] [Confidence: HIGH]

**Chatty Interfaces / N+1 Query Problem**
- **What it looks like**: Service A calls Service B in a loop (100 API calls to fetch 100 items). Loading a page issues 50+ database queries.
- **Why it's harmful**: Latency multiplies (50 queries × 10ms = 500ms), network overhead, connection pool exhaustion.
- **What to do instead**: Batch APIs (fetch 100 items in one call), GraphQL for flexible fetching, database query optimization (eager loading, joins instead of N+1), caching.
[Source: Kleppmann, 2017] [Confidence: HIGH]

**God Object / God Service**
- **What it looks like**: UserService handles authentication, authorization, profile, preferences, notifications, settings (1000+ lines). Monolithic service that "knows everything."
- **Why it's harmful**: Violates Single Responsibility Principle, impossible to understand, changes in one area break others, can't scale independently.
- **What to do instead**: Decompose by subdomain (auth-service, profile-service, notification-service). Follow Domain-Driven Design bounded contexts. Each service has one clear responsibility.
[Source: Fowler, Evans Domain-Driven Design] [Confidence: HIGH]

**Ignoring CAP Theorem / Distributed Transactions**
- **What it looks like**: Expecting strong consistency across distributed microservices without consensus protocols. Two-phase commit across services that need to remain available during network partitions.
- **Why it's harmful**: System hangs during network partitions, availability suffers, developers discover CAP constraints in production.
- **What to do instead**: Accept eventual consistency where appropriate. Use saga pattern for distributed workflows. Design idempotent operations. Provide user-visible staleness indicators. Use strong consistency (Raft/Paxos) only where required (account balances, inventory).
[Source: Brewer, Kleppmann] [Confidence: HIGH]

**Lack of Observability**
- **What it looks like**: Microservices with no distributed tracing, no centralized logging, no service dependency visualization. Debugging by SSH-ing into boxes.
- **Why it's harmful**: Impossible to understand request flow, hours to troubleshoot issues, no proactive issue detection, no SLO tracking.
- **What to do instead**: Implement from day one: distributed tracing (OpenTelemetry), centralized logging (ELK, Splunk), metrics (Prometheus), service mesh for automatic telemetry. Four Golden Signals monitoring. Architecture health dashboard.
[Source: Google SRE Book] [Confidence: HIGH]

---

### 4. Tool & Technology Map

**Architecture Documentation & Diagramming**

- **C4 Model Tools**:
  - Structurizr (DSL for C4 diagrams, stores as code): Use for large organizations needing centralized architecture docs
  - PlantUML (text-based UML/C4): Use for diagrams in Git with code reviews
  - Mermaid (Markdown-compatible diagrams): Use when already using Markdown docs, GitHub renders natively
  - diagrams.net / draw.io (GUI tool): Use for ad-hoc diagramming, export to version-controlled XML
  [Selection criteria: Code vs GUI preference, team size, existing doc tooling] [Confidence: HIGH]

- **ADR Management**:
  - adr-tools (CLI): Use for initializing ADR structure, generating templates
  - log4brains (Web UI): Use for browsing ADRs across multiple projects
  - Markdown files in `/docs/architecture/decisions/`: Universal, tool-agnostic
  [Selection criteria: Simplicity favors plain Markdown] [Confidence: HIGH]

**Architecture Governance & Compliance**

- **Fitness Function Tools**:
  - ArchUnit (Java): JUnit-based architecture tests, dependency rules, layering enforcement
  - NDepend (.NET): Dependency analysis, code metrics, architecture visualization
  - Radon (Python): Cyclomatic complexity, maintainability index
  - Structure101: Cross-language dependency analysis
  [Selection criteria: Language match, CI/CD integration] [Confidence: MEDIUM]

- **API Governance**:
  - Spectral (OpenAPI linting): Enforce API standards, style guides
  - OpenAPI Spec (Swagger): API contract definition
  - Postman / Insomnia: API testing, contract validation
  [Selection criteria: API-first organizations need Spectral + OpenAPI] [Confidence: MEDIUM]

**Distributed Systems Infrastructure**

- **Service Mesh**:
  - Istio (feature-rich, complex): Use for >50 microservices, need advanced traffic management
  - Linkerd (lightweight, simpler): Use for 20-50 microservices, prioritize simplicity
  - Consul Connect: Use if already using HashiCorp Consul for service discovery
  [Selection criteria: Team expertise, cluster size, operational complexity tolerance] [Confidence: MEDIUM]

- **API Gateway**:
  - Kong (open source, plugin ecosystem): Use for multi-cloud, extensibility needs
  - AWS API Gateway (managed): Use for AWS-native, serverless architectures
  - Azure API Management: Use for Azure-native, enterprise features
  - Traefik: Use for Kubernetes-native, simple use cases
  [Selection criteria: Cloud platform, feature needs, operational model] [Confidence: MEDIUM]

- **Message Brokers**:
  - Kafka (high throughput, durable log): Use for event sourcing, stream processing, >10K msg/sec
  - RabbitMQ (traditional queue, routing): Use for task queues, <10K msg/sec, need advanced routing
  - AWS SQS/SNS (managed): Use for AWS-native, simple pub/sub
  - NATS (lightweight, high performance): Use for edge computing, IoT, low latency
  [Selection criteria: Throughput, durability needs, operational preference] [Confidence: HIGH]

**Observability & Monitoring**

- **Distributed Tracing**:
  - Jaeger (open source, CNCF): Use for self-hosted, Kubernetes environments
  - Zipkin (battle-tested, simple): Use for simpler deployments
  - LightStep / Honeycomb (commercial SaaS): Use for advanced analysis, large scale
  - AWS X-Ray / GCP Cloud Trace: Use for cloud-native with platform lock-in acceptable
  [Selection criteria: Self-hosted vs SaaS, budget, query sophistication needs] [Confidence: MEDIUM]

- **Metrics & Alerting**:
  - Prometheus + Grafana (OSS standard): Use for Kubernetes, pull-based metrics
  - Datadog (commercial SaaS): Use for full-stack observability, APM, logs+metrics unified
  - New Relic (commercial SaaS): Use for APM-focused, developer-friendly UX
  - CloudWatch (AWS), Cloud Monitoring (GCP): Use for cloud-native with single cloud
  [Selection criteria: Budget, self-hosted vs SaaS, multi-cloud needs] [Confidence: HIGH]

**Data Infrastructure**

- **Databases** (Polyglot Persistence):
  - PostgreSQL: Relational, ACID, JSON support. Use for most CRUD, <1TB, strong consistency.
  - MongoDB: Document store. Use for flexible schema, high write throughput.
  - Cassandra: Wide-column, AP system. Use for time-series, multi-region writes, >10TB.
  - Redis: In-memory, fast. Use for caching, sessions, real-time counters.
  - Elasticsearch: Search engine. Use for full-text search, log analytics.
  - Neo4j: Graph database. Use for social networks, recommendation engines, fraud detection.
  [Selection criteria: Match database to data access pattern, consistency needs] [Confidence: HIGH]

- **Stream Processing**:
  - Apache Flink: Stateful stream processing, exactly-once semantics. Use for complex CEP, low latency.
  - Apache Spark Streaming: Micro-batch streaming. Use if already using Spark for batch.
  - ksqlDB: SQL on Kafka streams. Use for simple stream processing, SQL expertise.
  - AWS Kinesis Analytics: Managed stream processing. Use for AWS-native, simple use cases.
  [Selection criteria: Latency needs, exactly-once vs at-least-once, team expertise] [Confidence: MEDIUM]

**AI/ML Infrastructure**

- **MLOps Platforms**:
  - MLflow (experiment tracking, model registry): Use for self-hosted, framework-agnostic
  - Weights & Biases (commercial SaaS): Use for experiment tracking, collaboration
  - AWS SageMaker / GCP Vertex AI / Azure ML: Use for cloud-native, full ML lifecycle
  [Selection criteria: Self-hosted vs managed, cloud platform, budget] [Confidence: MEDIUM]

- **Feature Stores**:
  - Feast (open source): Use for self-hosted, Kubernetes environments
  - Tecton (commercial, Feast creators): Use for managed, enterprise features
  - AWS Feature Store / GCP Feature Store: Use for cloud-native
  [Selection criteria: Real-time feature serving needs, budget] [Confidence: MEDIUM]

- **Vector Databases** (for RAG, LLM applications):
  - Pinecone (managed SaaS): Use for quick start, no ops
  - Weaviate (open source, GraphQL): Use for self-hosted, semantic search
  - Chroma (embedded, lightweight): Use for prototypes, small scale
  - pgvector (PostgreSQL extension): Use if already using PostgreSQL, simple needs
  [Selection criteria: Scale, budget, existing infrastructure] [Confidence: HIGH]

- **LLM Frameworks**:
  - LangChain: Use for complex multi-step chains, RAG, agents
  - LlamaIndex: Use for document-focused RAG, simpler use cases
  - Semantic Kernel (Microsoft): Use for .NET environments
  - Anthropic SDK / OpenAI SDK: Use for simple prompt-based applications
  [Selection criteria: Complexity needs, language preference] [Confidence: MEDIUM]

**Migration & Modernization**

- **Database Migration**:
  - AWS DMS (Database Migration Service): Use for AWS migrations, heterogeneous DB
  - GCP Database Migration Service: Use for GCP migrations
  - Debezium (CDC, open source): Use for self-hosted, Kafka-based CDC
  - Flyway / Liquibase: Use for schema migrations, version control
  [Selection criteria: Cloud platform, CDC needs, database type] [Confidence: MEDIUM]

- **Application Migration**:
  - AWS Application Migration Service: Use for lift-and-shift to AWS
  - Azure Migrate: Use for Azure migrations
  - CloudEndure (acquired by AWS): Use for continuous replication
  [Selection criteria: Target cloud platform, downtime tolerance] [Confidence: MEDIUM]

---

### 5. Interaction Scripts

**Trigger**: "Design our system architecture" or "We're starting a new project, what architecture should we use?"

**Response pattern**:
1. **Gather context**: Ask about team size, expected scale, deployment frequency, domain complexity, existing infrastructure.
2. **Start simple recommendation**: "Start with a modular monolith unless you have >30 engineers or very clear independent scaling needs."
3. **Provide reasoning**: Explain trade-offs (monolith simpler to reason about, deploy, debug vs microservices enable team autonomy, independent scaling).
4. **Offer C4 diagrams**: "Let's create a Level 1 Context diagram showing external dependencies and Level 2 Container diagram showing major components."
5. **Plan for evolution**: "Design module boundaries to enable future extraction to microservices if needed. Follow domain-driven design principles."
6. **Document decisions**: "We'll create an ADR for the architecture decision capturing this context and rationale."

**Key questions to ask first**:
- How many engineers will work on this? (determines monolith vs microservices)
- What's your expected scale in 6 months, 1 year, 2 years? (determines scaling approach)
- How often will you deploy? (determines deployment architecture)
- What are your strongest technical skills? (determines technology choices)
- What infrastructure do you already have? (determines build on existing vs greenfield)

---

**Trigger**: "Review our current architecture" or "We're having performance/scaling/complexity issues"

**Response pattern**:
1. **Request architecture artifacts**: "Do you have C4 diagrams, ADRs, or architecture documentation?"
2. **If yes**: Review diagrams for anti-patterns (distributed monolith, god services, chatty interfaces).
3. **If no**: "Let's first document the current state with C4 Level 1-2 diagrams to understand what we're working with."
4. **Analyze observability**: "Do you have distributed tracing, service dependency maps, metrics dashboards?"
5. **Identify pain points**: Ask about deployment frequency, time to fix bugs, onboarding time, incident patterns.
6. **Map to anti-patterns**: Connect symptoms to anti-patterns (slow deployments → distributed monolith, debugging takes days → lack of observability).
7. **Prioritize improvements**: Use impact/effort matrix to sequence fixes.
8. **Propose migration path**: If refactoring needed, recommend Strangler Fig pattern for incremental improvement.

**Key questions to ask first**:
- What symptoms are you experiencing? (slow deployments, hard to debug, scaling issues)
- How are you currently monitoring the system? (observability baseline)
- How long does it take to onboard a new engineer? (complexity indicator)
- When was the last architecture review? (drift awareness)
- What's your tolerance for change risk? (determines incremental vs bigger changes)

---

**Trigger**: "Help us choose between X and Y technologies" or "Should we use technology X?"

**Response pattern**:
1. **Apply RISKS framework**: Evaluate Recency, Investment, Skill availability, Knowledge resources, Switching cost for each option.
2. **Score weighted criteria matrix**: Functional fit (30%), Maturity (20%), Community (15%), Team expertise (15%), Ops complexity (10%), Cost (10%).
3. **Recommend spike if close**: "The scores are within 10 points; let's run a 3-day time-boxed spike for each to answer specific questions."
4. **Provide decision framework**: "Here's the analysis matrix. My recommendation is X for reasons Y, but the final decision should account for your specific constraints."
5. **Document in ADR**: "Let's capture this decision in an ADR including the alternatives considered and why we chose X."
6. **Plan for reversibility**: "If we choose X, here's how we'd migrate to Y if needed (switching cost assessment)."

**Key questions to ask first**:
- What problem are you solving? (ensures technology matches need)
- What alternatives have you considered? (broadens options)
- What's your team's experience with similar technologies? (skill availability)
- Is this for a critical or non-critical system? (risk tolerance)
- What's your timeline? (learning curve factor)

---

**Trigger**: "We need to migrate from monolith to microservices" or "Our monolith is too complex"

**Response pattern**:
1. **Challenge the assumption**: "What specific problems are you trying to solve? Microservices solve team scaling and independent deployment, not inherent complexity."
2. **Explore modular monolith first**: "Can we improve the monolith's modularity with enforced boundaries before distributing it?"
3. **If microservices justified**: Recommend Strangler Fig pattern, not big-bang rewrite.
4. **Identify extraction candidates**: "Let's find bounded contexts with clear boundaries, stable interfaces, and independent scaling needs."
5. **Plan incremental migration**: Wave-based approach (non-critical first, core dependencies last).
6. **Address data migration**: "Each service needs its own database. We'll use CDC or dual-write patterns during transition."
7. **Establish observability first**: "Before extracting any services, implement distributed tracing, centralized logging, and service mesh."
8. **Set timeline**: "Expect 18-36 months for full migration of a large monolith."

**Key questions to ask first**:
- Why do you want microservices? (verify it solves actual problem)
- How many teams will work on the system? (>30 engineers justify microservices)
- Do different components need independent scaling? (scaling justification)
- What's your team's distributed systems expertise? (readiness check)
- Can you tolerate eventual consistency? (CAP theorem discussion)

---

**Trigger**: "Design our cloud architecture" or "Should we go multi-cloud?"

**Response pattern**:
1. **Clarify multi-cloud**: "Most 'multi-cloud' is consumption (different clouds for different services), not deployment (same app on multiple clouds). Which are you considering?"
2. **For multi-cloud deployment**: "This is rare due to complexity and cost. Are you solving vendor lock-in fear or actual requirements like data residency?"
3. **For multi-cloud consumption**: "This is common. Use AWS for compute, GCP for ML, Azure for enterprise integration based on strengths."
4. **Apply Well-Architected Frameworks**: Use AWS Well-Architected, GCP Architecture Framework, Azure Well-Architected for respective clouds.
5. **Cost architecture first**: "Design for cost optimization from day one: right-sizing, auto-scaling, spot instances, storage tiering, reserved capacity."
6. **Plan for FinOps**: "Implement cost monitoring, budgets, alerts as architecture concerns, not afterthoughts."
7. **Landing zone setup**: "Establish network design, IAM, security baselines before application deployment."

**Key questions to ask first**:
- Why multi-cloud? (solve real problem vs hedge against hypothetical vendor issues)
- What workloads are you running? (matches cloud strengths)
- What's your team's cloud expertise? (determines managed vs self-managed services)
- What are your compliance requirements? (data residency, encryption, certifications)
- What's your scale and growth trajectory? (sizing and cost modeling)

---

**Trigger**: "Our system is too slow" or "We need to scale to 10x traffic"

**Response pattern**:
1. **Measure first**: "Do you have baseline metrics? P50, P95, P99 latency? Throughput? Saturation indicators?"
2. **Identify bottleneck**: "Let's use distributed tracing and profiling to find where time is spent."
3. **Apply scaling strategy**:
   - If stateless tier (app servers): Horizontal scaling with auto-scaling group
   - If database: Vertical scaling first, read replicas second, sharding last
   - If specific component: Extract and scale independently
4. **Implement caching**: "What are we computing repeatedly? Let's add multi-tier caching."
5. **Optimize queries**: "Are we doing N+1 queries? Let's batch or eager load."
6. **Set P99 latency budget**: "Allocate latency budget across tiers: CDN, load balancer, app, database."
7. **Design for 10x, not 100x**: "Over-engineering for hypothetical massive scale adds complexity."

**Key questions to ask first**:
- What metrics indicate slowness? (latency, throughput, error rate)
- Where is the bottleneck? (CPU, memory, disk I/O, network, database)
- What's your current and target scale? (10x, 100x, 1000x)
- What's your consistency requirement? (allows caching and eventual consistency)
- What's your budget? (determines managed services vs self-optimized)

---

**Trigger**: "How do we integrate AI/LLMs into our architecture?"

**Response pattern**:
1. **Identify use case**: "What are you using LLMs for? Chat, document Q&A, content generation, summarization?"
2. **For document Q&A**: Recommend RAG pattern (vector database + retrieval + LLM).
3. **For chat**: Recommend prompt engineering with context management.
4. **For domain-specific**: Evaluate fine-tuning vs RAG vs prompt engineering.
5. **Implement LLM gateway**: "Centralize LLM calls for rate limiting, cost tracking, PII filtering, caching."
6. **Design for latency**: "LLMs take 200ms-10s. Make UX async with loading indicators."
7. **Control costs**: "Use smaller models where sufficient, cache responses, optimize prompt size."
8. **Security**: "Implement input validation against prompt injection, output filtering for harmful content."
9. **Governance**: "Model cards, audit logging, human-in-the-loop for high-stakes decisions."

**Key questions to ask first**:
- What's the specific AI use case? (determines architecture pattern)
- What's your budget for LLM API costs? (determines model choice and caching strategy)
- Do you have proprietary data to ground responses? (determines RAG need)
- What's your data privacy requirement? (determines cloud vs on-prem)
- What's acceptable latency? (determines model size and async design)

---

