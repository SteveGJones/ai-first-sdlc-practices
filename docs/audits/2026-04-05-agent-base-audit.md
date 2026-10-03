# Agent Base Audit Report

**Date**: 2026-04-05
**Agents audited**: 62
**Alternatives found**: 46 agents with at least one alternative
**Frontmatter updated**: 46

## Summary

| Category | Agents | Alternatives Found | Frontmatter Updated |
|----------|--------|-------------------|-------------------|
| core | 30 | 18 | 18 |
| ai-development | 9 | 9 | 9 |
| ai-builders | 5 | 4 | 4 |
| testing | 4 | 4 | 4 |
| documentation | 2 | 2 | 2 |
| project-management | 4 | 4 | 4 |
| sdlc | 8 | 5 | 5 |
| **Total** | **62** | **46** | **46** |

## Key Findings

1. **46 of 62 agents (74%) have at least one 1st-party alternative** -- the MCP ecosystem has matured rapidly through 2025-2026, with major vendors (GitHub, AWS, Google, MongoDB, Grafana, Snyk, PagerDuty, Anthropic) publishing official MCP servers.

2. **No agent is fully replaceable** -- All 62 agents provide strategic, architectural, or advisory value beyond what MCP servers and vendor tools offer. MCP servers handle operational execution (queries, API access, scanning); agents handle design decisions, trade-off analysis, and methodology.

3. **github-integration-specialist has the most overlap** -- GitHub's official MCP Server (51 tools) covers nearly all described capabilities. This is the only agent flagged for Review in the core batch.

4. **junior-ai-solution-architect flagged for Review** -- Overlaps heavily with ai-solution-architect and lacks the specificity and decision frameworks of the senior version. Teams should consider consolidation.

5. **Framework-specific agents have zero overlap** -- 16 agents have no alternatives at all: agent-builder, backend-architect, compliance-auditor, compliance-report-generator, critical-goal-reviewer, deep-research-agent, enforcement-strategy-advisor, pipeline-orchestrator, repo-knowledge-distiller, sdlc-coach, sdlc-enforcer, solution-architect, verification-enforcer, ai-team-transformer, ai-first-kick-starter, framework-validator, sdlc-knowledge-curator. These are unique to the AI-First SDLC framework.

6. **Cloud/infrastructure agents have the richest alternative landscape** -- cloud-architect (3 alternatives: AWS 66 servers, Azure 40+, GCP), devops-specialist (3: GitHub, Terraform, Pulumi), and observability-specialist (3: Grafana, Datadog, Sentry) each have multiple well-maintained vendor MCP servers.

7. **AI-development agents universally have alternatives but remain valuable** -- All 9 ai-development agents have alternatives (SDKs, frameworks, observability tools), but each provides architectural reasoning and framework selection guidance that raw tooling does not.

8. **The MCP ecosystem has grown to 12,870+ servers** -- AWS alone has 66 official MCP servers; Docker Hub catalogs 100+; PulseMCP lists 12,870+ total servers.

## Findings by Agent

### Core Agents (30)

#### agent-builder
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Agent construction is a meta-capability specific to this framework. Anthropic's Claude Agent SDK provides building blocks but not an opinionated agent-building pipeline. No direct 1st-party alternative exists.

#### api-architect
- **Category**: core
- **Alternatives found**: 2
  - Apollo MCP Server (mcp-server) -- https://github.com/apollographql/graphql -- GraphQL schema introspection and operation tools -- Maintained: Yes
  - OpenAPI/Zuplo MCP (mcp-server) -- https://zuplo.com/blog/mcp-server-graphql -- Converts OpenAPI specs into MCP tools -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: Apollo MCP covers GraphQL operations. The agent adds value for API design strategy, versioning, and cross-paradigm comparisons (REST vs GraphQL vs gRPC) that MCP servers do not address.

#### backend-architect
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Backend architecture is a strategic design discipline. No vendor publishes an MCP server for microservices design, saga patterns, or architectural trade-off analysis.

#### cloud-architect
- **Category**: core
- **Alternatives found**: 3
  - AWS MCP Servers (mcp-server) -- https://github.com/awslabs/mcp -- 66 official AWS MCP servers for API access, documentation, infrastructure -- Maintained: Yes
  - Azure MCP Server (mcp-server) -- https://github.com/microsoft/mcp -- 40+ tools spanning Azure services -- Maintained: Yes
  - Google Cloud MCP Servers (mcp-server) -- https://github.com/google/mcp -- GCP services including compute, databases, security -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: Cloud vendor MCP servers provide direct API access and documentation. The agent adds value for multi-cloud strategy, cost optimization, Well-Architected reviews, and vendor-neutral decision frameworks.

#### compliance-auditor
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Compliance auditing (SOC 2, ISO 27001, PCI DSS, GDPR gap analysis) is a specialized advisory function. No vendor offers an MCP server for compliance framework assessment. DPO2U covers GDPR-specific compliance but not multi-framework auditing.

#### compliance-report-generator
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Compliance reporting is framework-specific to this SDLC. No general-purpose compliance report generation MCP servers exist.

#### container-platform-specialist
- **Category**: core
- **Alternatives found**: 2
  - Kubernetes MCP Server (mcp-server) -- https://github.com/containers/kubernetes-mcp-server -- Native Go implementation for Kubernetes/OpenShift cluster management -- Maintained: Yes
  - Docker MCP Catalog (mcp-server) -- https://hub.docker.com/u/mcp -- 100+ containerized MCP servers via Docker Desktop -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: The Kubernetes MCP server handles cluster operations. The agent adds value for architecture design decisions (Helm chart design, service mesh selection, Pod Security Standards, platform engineering patterns).

#### critical-goal-reviewer
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Requirements verification and goal alignment validation is a meta-process capability. No vendor offers automated requirements traceability via MCP.

#### data-architect
- **Category**: core
- **Alternatives found**: 1
  - dbt MCP Server (mcp-server) -- https://docs.getdbt.com/docs/dbt-versions/2025-release-notes -- Data transformation, lineage, metrics, and quality via dbt projects -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: dbt MCP Server covers data transformation and governance. The agent adds value for data platform architecture, lakehouse design, data mesh strategy, and technology selection beyond dbt.

#### data-privacy-officer
- **Category**: core
- **Alternatives found**: 1
  - DPO2U MCP Server (mcp-server) -- https://skywork.ai/skypage/en/dpo2u-mcp-server-ai-engineer-gdpr-compliance/1981675405810135040 -- GDPR/LGPD compliance orchestration -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: DPO2U covers GDPR/LGPD process compliance. The agent adds value for multi-jurisdiction privacy strategy (CCPA/CPRA, PIPL), privacy-by-design architecture, and data subject rights implementation patterns.

#### database-architect
- **Category**: core
- **Alternatives found**: 2
  - MongoDB MCP Server (mcp-server) -- https://github.com/mongodb-js/mongodb-mcp-server -- Official MongoDB/Atlas query, schema inspection, index management -- Maintained: Yes
  - PostgreSQL MCP Server (mcp-server) -- https://github.com/modelcontextprotocol/servers -- Anthropic reference PostgreSQL MCP server -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: Database MCP servers provide query execution and schema access. The agent adds value for database technology selection, schema design strategy, query optimization methodology, and HA/DR architecture.

#### deep-research-agent
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Systematic web research with source evaluation (CRAAP) is a meta-capability of this framework's agent pipeline. Claude's built-in web search is a tool, not a structured research methodology.

#### devops-specialist
- **Category**: core
- **Alternatives found**: 3
  - GitHub MCP Server (mcp-server) -- https://github.com/github/github-mcp-server -- 51 tools: repos, issues, PRs, Actions, code security, notifications -- Maintained: Yes
  - Terraform MCP Server (mcp-server) -- https://developer.hashicorp.com/terraform/mcp-server -- Terraform Registry APIs, workspace management, run triggers -- Maintained: Yes
  - Pulumi MCP Server (mcp-server) -- https://www.pulumi.com/docs/ai/mcp-server/ -- IaC in multiple languages, stack management, resource queries -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: MCP servers handle CI/CD execution and IaC provisioning. The agent adds value for pipeline architecture design, GitOps strategy, progressive delivery patterns, and DevSecOps supply chain security design.

#### enforcement-strategy-advisor
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Behavioral psychology for software teams and change management strategy is a unique advisory function. No vendor offers AI tools for enforcement strategy design.

#### example-security-architect
- **Category**: core
- **Alternatives found**: 2
  - Snyk MCP Server (mcp-server) -- https://github.com/snyk/agent-scan -- 11 tools: SAST, SCA, IaC scanning, container scanning, SBOM, AIBOM -- Maintained: Yes
  - Semgrep MCP (mcp-server) -- https://www.pulsemcp.com/servers/semgrep -- Real-time code security scanning with AI reasoning -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: Security scanning MCP servers handle vulnerability detection. The agent (example template) adds value for threat modeling methodology, security architecture review, and secure design patterns. Note: this is the example/template version of security-architect.

#### frontend-architect
- **Category**: core
- **Alternatives found**: 2
  - Next.js DevTools MCP (mcp-server) -- https://github.com/vercel/next-devtools-mcp -- Error detection, live state queries, Next.js application debugging -- Maintained: Yes
  - Storybook MCP Server (mcp-server) -- https://storybook.js.org/docs/ai/mcp/overview -- Component metadata, design tokens, test execution, story generation -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: Framework-specific MCP servers handle development tooling. The agent adds value for component architecture patterns, state management strategy, performance optimization, and rendering strategy selection.

#### frontend-security-specialist
- **Category**: core
- **Alternatives found**: 1
  - Snyk MCP Server (mcp-server) -- https://github.com/snyk/agent-scan -- SAST scanning includes frontend vulnerability detection -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Snyk covers general vulnerability scanning but does not address frontend-specific threats (CSP configuration, XSS prevention patterns, OAuth/OIDC flows, SRI, Trusted Types). The agent's specialized domain knowledge is not replicated by any MCP server.

#### github-integration-specialist
- **Category**: core
- **Alternatives found**: 1
  - GitHub MCP Server (mcp-server) -- https://github.com/github/github-mcp-server -- 51 tools: repos, issues, PRs, Actions, code security, Copilot, notifications -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Review
- **Rationale**: The official GitHub MCP Server covers most operational tasks this agent describes (branch protection, Actions workflows, Advanced Security, PR automation). The agent may have limited residual value for GitHub organization governance strategy and complex workflow design patterns.

#### mobile-architect
- **Category**: core
- **Alternatives found**: 2
  - Expo MCP Server (mcp-server) -- https://docs.expo.dev/eas/ai/mcp/ -- React Native/Expo SDK context, simulator control, DevTools -- Maintained: Yes
  - iOS Simulator MCP (mcp-server) -- https://www.npmjs.com/package/ios-simulator-mcp -- iOS simulator control, UI inspection, screenshots -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: MCP servers handle runtime tooling. The agent adds value for cross-platform framework selection, mobile architecture patterns, performance optimization strategy, and platform guideline compliance.

#### observability-specialist
- **Category**: core
- **Alternatives found**: 3
  - Grafana MCP Server (mcp-server) -- https://github.com/grafana/mcp-grafana -- Dashboards, datasource queries, alerting, incident management, OnCall -- Maintained: Yes
  - Datadog MCP Server (mcp-server) -- https://docs.datadoghq.com/bits_ai/mcp_server/ -- Observability data bridge for monitoring and analysis -- Maintained: Yes
  - Sentry MCP Server (mcp-server) -- https://github.com/getsentry/sentry-mcp-stdio -- Error tracking, issue access, Seer analysis -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: Observability vendor MCP servers provide data access and querying. The agent adds value for OpenTelemetry instrumentation strategy, SLO/SLI framework design, alerting strategy, and observability architecture.

#### pipeline-orchestrator
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: The pipeline orchestrator coordinates the agent creation pipeline (discovery, research, building). This is a meta-capability specific to this framework with no external equivalent.

#### repo-knowledge-distiller
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Repository analysis for agent construction via RELIC evaluation is a unique capability of this framework's pipeline. No vendor offers structured codebase knowledge extraction for agent creation.

#### sdlc-coach
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: SDLC coaching and process improvement is specific to this framework's methodology. No vendor offers AI-First SDLC coaching tools.

#### sdlc-enforcer
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: SDLC enforcement is specific to this framework's CONSTITUTION.md rules and validation pipeline. No external equivalent exists.

#### security-architect
- **Category**: core
- **Alternatives found**: 2
  - Snyk MCP Server (mcp-server) -- https://github.com/snyk/agent-scan -- 11 tools: SAST, SCA, IaC scanning, container scanning, SBOM -- Maintained: Yes
  - Semgrep MCP (mcp-server) -- https://www.pulsemcp.com/servers/semgrep -- Real-time SAST with AI multimodal reasoning -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: Security scanning MCP servers handle automated vulnerability detection. The agent adds value for threat modeling methodology (STRIDE, PASTA), security architecture design, and security strategy that scanning tools cannot provide.

#### solution-architect
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Solution architecture (TOGAF, C4, ATAM) is a strategic design discipline. No vendor offers architecture framework methodology via MCP. Cloud MCP servers provide infrastructure access but not architectural decision-making.

#### sre-specialist
- **Category**: core
- **Alternatives found**: 2
  - PagerDuty MCP Server (mcp-server) -- https://www.pagerduty.com/newsroom/pagerduty-expands-ai-ecosystem-to-supercharge-ai-agents/ -- 60+ tools: incidents, on-call, escalation, event orchestration, status pages -- Maintained: Yes
  - Grafana MCP Server (mcp-server) -- https://github.com/grafana/mcp-grafana -- Incident management, OnCall integration, alerting -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: Incident management MCP servers handle operational tasks. The agent adds value for SLO framework design, chaos engineering methodology, error budget policy, and operational excellence strategy.

#### test-manager
- **Category**: core
- **Alternatives found**: 1
  - Playwright MCP Server (mcp-server) -- https://github.com/microsoft/playwright-mcp -- Browser automation via accessibility tree, navigation, form filling, screenshots -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: Playwright MCP handles browser test automation. The agent adds value for test strategy design, coverage planning, risk-based testing, and quality metrics management across all test types.

#### ux-ui-architect
- **Category**: core
- **Alternatives found**: 2
  - Figma MCP Server (mcp-server) -- https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server -- Design data access, component properties, auto-layout, design tokens -- Maintained: Yes
  - Storybook MCP Server (mcp-server) -- https://storybook.js.org/docs/ai/mcp/overview -- Component manifests, design system context, test execution -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: Design tool MCP servers provide design data access. The agent adds value for WCAG accessibility strategy, user research methodology, information architecture, and design system governance.

#### verification-enforcer
- **Category**: core
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Documentation-code fidelity verification, test execution gating, and runtime proof are framework-specific enforcement capabilities. No vendor offers this combination as an MCP server.

---

### AI-Development Agents (9)

#### a2a-architect
- **Category**: ai-development
- **Alternatives found**: 3
  - Google Agent Development Kit / ADK (SDK/Framework) -- https://github.com/google/adk-python -- Official Google open-source agent framework with native A2A protocol support, auto-generated Agent Cards, Python/TypeScript/Java/Go SDKs, A2A v0.3 with gRPC support and security card signing -- Maintained: Yes
  - A2A Protocol Specification & SDK (Protocol/SDK) -- https://github.com/a2aproject/A2A -- Official A2A protocol spec (now Linux Foundation), Python SDK with client-side support, HTTP/SSE/JSON-RPC transport, enterprise-grade auth parity with OpenAPI -- Maintained: Yes
  - Google ADK Docs -- A2A Integration (Documentation) -- https://google.github.io/adk-docs/a2a/ -- Official A2A integration guide, deployment on Agent Engine, Cloud Run, and GKE, purchasing concierge codelabs -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: The a2a-architect agent provides architectural guidance and pattern selection that the raw SDKs do not. However, architects using this agent should reference the now-stable Google ADK + A2A spec; the agent's body text notes "Confidence: GAP - requires 2026 verification" for A2A, which should be updated since A2A is now stable.

#### agent-developer
- **Category**: ai-development
- **Alternatives found**: 2
  - Anthropic Claude Agent SDK -- Python (SDK) -- https://github.com/anthropics/claude-agent-sdk-python -- Official SDK for building autonomous Claude agents; same agent loop/tool execution as Claude Code; composable MCP-based tool system; subagent orchestration; lifecycle hooks; v0.1.48 as of March 2026 -- Maintained: Yes
  - Anthropic Claude Agent SDK -- TypeScript (SDK) -- https://github.com/anthropics/claude-agent-sdk-typescript -- TypeScript counterpart to the Python Agent SDK; identical capabilities; v0.2.71 as of March 2026 -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: The agent-developer agent covers architectural patterns (ReAct, Plan-Execute, Reflection), persona design, guardrails, and evaluation frameworks -- design concerns the SDKs themselves do not address. The SDKs are referenced as implementation tools the agent's output would target.

#### ai-solution-architect
- **Category**: ai-development
- **Alternatives found**: 3
  - Google Vertex AI (Platform) -- https://cloud.google.com/vertex-ai -- End-to-end managed MLOps platform; model serving, pipelines (Kubeflow-based), Model Registry, evaluation, agent builder; deep Google/Gemini integration -- Maintained: Yes
  - AWS SageMaker (Platform) -- https://aws.amazon.com/sagemaker/ -- Comprehensive enterprise MLOps platform; SageMaker Pipelines CI/CD, Model Monitor, Feature Store, JumpStart foundation model hub; deepest AWS ecosystem integration -- Maintained: Yes
  - Azure Machine Learning (Platform) -- https://azure.microsoft.com/en-us/products/machine-learning -- Microsoft's MLOps platform; multi-role support, automated ML, Responsible AI dashboard, integration with Azure OpenAI Service -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Platforms provide infrastructure; the ai-solution-architect provides cross-platform architectural reasoning, model selection trade-offs, RAG system design, and system-level multi-agent orchestration patterns that no single platform encompasses.

#### junior-ai-solution-architect
- **Category**: ai-development
- **Alternatives found**: 3
  - Google Vertex AI (Platform) -- https://cloud.google.com/vertex-ai -- Same as ai-solution-architect; relevant for junior reviews of MLOps practices and cloud-native AI deployments -- Maintained: Yes
  - AWS SageMaker (Platform) -- https://aws.amazon.com/sagemaker/ -- Same as ai-solution-architect; relevant for junior reviews -- Maintained: Yes
  - Azure Machine Learning (Platform) -- https://azure.microsoft.com/en-us/products/machine-learning -- Same as ai-solution-architect; Responsible AI dashboard directly addresses ethical AI considerations this agent covers -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Review
- **Rationale**: The junior-ai-solution-architect overlaps heavily with ai-solution-architect and lacks the specificity and decision frameworks of the senior version. Teams should consider whether this agent is needed alongside the senior variant, or whether it is better repositioned as a "review checklist" agent with explicit references to the official platform tooling.

#### langchain-architect
- **Category**: ai-development
- **Alternatives found**: 4
  - LangGraph (Framework) -- https://github.com/langchain-ai/langgraph -- Official LangChain state-machine orchestration framework for resilient multi-agent systems; checkpointers, human-in-the-loop interrupts, subgraph composition -- Maintained: Yes
  - LangChain MCP Adapters (Library) -- https://github.com/langchain-ai/langchain-mcp-adapters -- Official library converting MCP tools into LangChain/LangGraph compatible tools; multi-server support -- Maintained: Yes
  - LangSmith (Observability Platform) -- https://www.langchain.com/langsmith -- Official LangChain tracing, evaluation, prompt management, and production monitoring; native LCEL integration; now supports MCP endpoint via Agent Server -- Maintained: Yes
  - LangChain Deep Agents / Agent Server (Framework) -- https://github.com/langchain-ai/deepagents -- Official agent harness with planning tool, filesystem backend, subagent spawning, and MCP via langchain-mcp-adapters -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: The langchain-architect agent is a strong domain expert for LCEL composition, RAG patterns, memory strategies, and LangServe deployment decisions. The official tools (LangGraph, LangSmith, MCP Adapters) are implementation infrastructure that this agent helps teams select and configure correctly.

#### mcp-quality-assurance
- **Category**: ai-development
- **Alternatives found**: 2
  - MCP Inspector (Tool) -- https://github.com/modelcontextprotocol/inspector -- Official visual testing and debugging tool from the MCP team; validates protocol handshake, inspects tool schemas, tests transports; runs via npx; React UI + Node.js proxy -- Maintained: Yes
  - MCP Conformance Tests (Test Suite) -- https://github.com/modelcontextprotocol/conformance -- Official conformance test suite from the modelcontextprotocol org; automated verification that servers/clients/SDKs correctly implement the spec; strategic roadmap priority for 2026 -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: The mcp-quality-assurance agent provides the six-dimensional review methodology (spec compliance, security, code quality, performance, production readiness, statistical validation) and issue classification (blocking/important/suggestion) that automated tools do not. The official tools are referenced as evidence-gathering mechanisms within the agent's review process.

#### mcp-server-architect
- **Category**: ai-development
- **Alternatives found**: 3
  - MCP Python SDK / `mcp` package (SDK) -- https://github.com/modelcontextprotocol/python-sdk -- Official Anthropic-backed Python SDK for MCP servers; asyncio-based, stdio and SSE transports, FastMCP for rapid prototyping -- Maintained: Yes
  - MCP TypeScript SDK / `@modelcontextprotocol/sdk` (SDK) -- https://github.com/modelcontextprotocol/typescript-sdk -- Official TypeScript/JavaScript SDK; most mature, best documented, Node.js support, Microsoft C# partnership announced -- Maintained: Yes
  - MCP Inspector (Tool) -- https://modelcontextprotocol.io/docs/tools/inspector -- Official debugging tool referenced in mcp-server-architect body; validates protocol compliance during development -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: The official SDKs provide implementation scaffolding; the mcp-server-architect provides architectural decisions around transport selection, tool hierarchy design, resource patterns, security architecture, and production deployment strategy that the SDKs do not prescribe.

#### mcp-test-agent
- **Category**: ai-development
- **Alternatives found**: 2
  - MCP Inspector (Tool) -- https://github.com/modelcontextprotocol/inspector -- Official visual testing and debugging tool; validates protocol handshake, tool schemas, transport configurations; CLI mode for scripting and automation -- Maintained: Yes
  - MCP Conformance Tests (Test Suite) -- https://github.com/modelcontextprotocol/conformance -- Official conformance test suite; automated spec compliance verification for servers and clients; supports npx-based test runner -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: The mcp-test-agent provides AI-client-perspective testing methodology: capability discovery simulation, statistical reliability validation (50-100 runs with variance thresholds), AI usability testing (tool disambiguation), and 6-personality AI behaviour testing. These test strategies are absent from the official tooling.

#### prompt-engineer
- **Category**: ai-development
- **Alternatives found**: 3
  - Anthropic Console -- Prompt Generator (Tool) -- https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-generator -- Official console tool generating production-ready prompts from descriptions using advanced PE techniques -- Maintained: Yes
  - Anthropic Console -- Prompt Improver & Evaluator (Tool) -- https://www.anthropic.com/news/prompt-improver -- Official console tools for refining existing prompts, running evaluations with ideal outputs, and sharing/standardising prompts across teams -- Maintained: Yes
  - Anthropic Console -- Workbench (Tool) -- https://www.anthropic.com/news/upgraded-anthropic-console -- Interactive environment for testing API calls, managing few-shot examples, and iterating on system prompts with structured input/output pairs -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: The prompt-engineer agent covers multi-model expertise (Claude, GPT, Gemini, Llama), advanced techniques (CoT, Tree-of-Thought, ReAct, self-consistency), token economics, security patterns (prompt injection prevention), and cross-model optimisation trade-offs. The Anthropic Console tools are Claude-only and GUI-based; this agent provides model-agnostic, code-first prompt engineering guidance.

---

### AI-Builders Agents (5)

#### rag-system-designer
- **Category**: ai-builders
- **Alternatives found**: 4
  - `mcp-server-llamacloud` (MCP server) -- https://github.com/run-llama/mcp-server-llamacloud -- Connects to LlamaCloud managed RAG indexes; point-and-click RAG queries -- Maintained: Yes
  - `mcp-server-qdrant` (MCP server) -- https://github.com/qdrant/mcp-server-qdrant -- Official Qdrant MCP server for vector memory storage and retrieval -- Maintained: Yes
  - `mcp-server-weaviate` (MCP server) -- https://github.com/weaviate/mcp-server-weaviate -- Official Weaviate MCP server; connects to Weaviate collections as knowledge base -- Maintained: Yes
  - `llama-index-tools-mcp` (library) -- https://github.com/run-llama/llama_index/tree/main/llama-index-integrations/tools/llama-index-tools-mcp -- LlamaIndex Python package enabling agents to connect to MCP servers and consume RAG tools -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: Vector DB MCP servers (Qdrant, Weaviate) and LlamaCloud MCP give Claude direct query/index access, but they do not make architecture decisions. The rag-system-designer agent reasons about trade-offs (chunking strategies, embedding model selection, hybrid retrieval design, reranking), which remains valuable expert guidance not replicated by any of these tools.

#### orchestration-architect
- **Category**: ai-builders
- **Alternatives found**: 4
  - `langchain-mcp-adapters` (library/MCP adapter) -- https://github.com/langchain-ai/langchain-mcp-adapters -- Official LangChain wrapper making MCP tools compatible with LangGraph agents -- Maintained: Yes
  - `crewAI enterprise-mcp-server` (MCP server) -- https://github.com/crewaiinc/enterprise-mcp-server -- Official CrewAI MCP server for kicking off and inspecting deployed Crew deployments -- Maintained: Yes
  - `microsoft/autogen` (framework with MCP support) -- https://github.com/microsoft/autogen -- Microsoft AutoGen 0.4 with native MCP workbench integration (merging into Microsoft Agent Framework) -- Maintained: Yes
  - `mcpdoc` (MCP server) -- https://github.com/langchain-ai/mcpdoc -- Official LangChain MCP docs server exposing llms.txt for LangGraph/LangChain documentation -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: LangGraph, AutoGen, and CrewAI are well-maintained frameworks with their own MCP server integrations. The orchestration-architect agent is still valuable for selecting the right framework, designing state machine topology, designing handoff protocols, and fault-tolerance patterns -- decisions none of the official tools make for you.

#### context-engineer
- **Category**: ai-builders
- **Alternatives found**: 2
  - `anthropic-sdk context-management beta` (official SDK feature) -- https://github.com/anthropics/anthropic-sdk-python -- Anthropic's official context-management-2025-06-27 beta with memory_20250818 tool; provides server-side context editing, clearing old thinking blocks, and token usage management -- Maintained: Yes
  - `claude-cookbooks memory_cookbook` (official reference) -- https://github.com/anthropics/claude-cookbooks/blob/main/tool_use/memory_cookbook.ipynb -- Anthropic-authored memory cookbook demonstrating context management and memory tool patterns -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Anthropic's context-management beta covers server-side context manipulation for a single session. The context-engineer agent covers broader architectural concerns: multi-agent context coordination, vector DB memory tiers, session state persistence, and token budget allocation across systems -- none of which are addressed by the SDK beta.

#### ai-devops-engineer
- **Category**: ai-builders
- **Alternatives found**: 3
  - `wandb-mcp-server` (MCP server) -- https://github.com/wandb/wandb-mcp-server -- Official W&B Models and Weave MCP server; query experiments, runs, models, and docs via natural language -- Maintained: Yes
  - `wandb/skills` (agent skills) -- https://github.com/wandb/skills -- Official W&B agent skills for Models and Weave -- Maintained: Yes
  - `mlflow` built-in MCP server (MCP server) -- https://github.com/mlflow/mlflow -- MLflow v3.5.1+ ships a built-in MCP server (`pip install mlflow[mcp]`) exposing experiment tracking, model registry, and AI commands as MCP prompts -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Reposition
- **Rationale**: W&B and MLflow MCP servers give Claude read/query access to experiment and model registry data; the ai-devops-engineer agent provides higher-level infrastructure architecture, LLM serving platform selection, GPU orchestration design, AI cost management strategy, and CI/CD pipeline design that the observability tools do not cover.

#### ai-team-transformer
- **Category**: ai-builders
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: AI team transformation is a strategic and organizational coaching domain. No vendor offers AI tools for change management methodology (ADKAR, Kotter), developer coaching for AI adoption, team maturity assessments, or resistance management.

---

### Testing Agents (4)

#### ai-test-engineer
- **Category**: testing
- **Alternatives found**: 2
  - promptfoo (OSS tool, now OpenAI-owned) -- https://github.com/promptfoo/promptfoo -- LLM/agent/RAG evaluation, red-teaming, CI/CD integration; used by OpenAI and Anthropic -- Maintained: Yes
  - DeepEval by Confident AI (SaaS + OSS) -- https://deepeval.com -- 50+ research-backed LLM evaluation metrics (faithfulness, hallucination, relevance, bias, toxicity), pytest-compatible CI gating -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent covers classical test pyramid + automation frameworks. promptfoo and DeepEval cover the AI/LLM evaluation layer specifically -- complementary, not replacements.

#### code-review-specialist
- **Category**: testing
- **Alternatives found**: 2
  - GitHub Copilot Code Review (1st-party GitHub) -- https://docs.github.com/en/copilot/concepts/agents/code-review -- Agentic PR review with tool-calling architecture; 60M+ reviews completed; GA for all Copilot plans as of March 2026 -- Maintained: Yes
  - CodeRabbit (SaaS) -- https://www.coderabbit.ai/ -- AI PR reviews + issue planning, 40+ integrated SAST/linting tools, 2M+ repos, GitHub/GitLab/Azure DevOps/Bitbucket support -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent provides educational, consultative review logic. GitHub Copilot Code Review and CodeRabbit are automated tooling alternatives that complement rather than replace a reasoning specialist.

#### integration-orchestrator
- **Category**: testing
- **Alternatives found**: 1
  - PactFlow (SaaS + OSS) -- https://pactflow.io/ -- Consumer-driven contract testing platform with MCP server, Pact Broker, bi-directional contract verification, CI-native validation; MCP server for VS Code/Cursor/Claude Code -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent coordinates cross-team integration strategy and WireMock/Mountebank decisions. PactFlow is the canonical platform for contract testing specifically and now has direct IDE/MCP integration.

#### performance-engineer
- **Category**: testing
- **Alternatives found**: 1
  - Grafana k6 (OSS + Cloud SaaS) -- https://k6.io/ -- Load/stress/soak/spike/browser testing, JavaScript/TypeScript scripts, CI/CD integration, Grafana Cloud hosted option -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent covers strategy, profiling, capacity planning, and optimization across the full performance lifecycle. k6 is the canonical open-source load testing tool referenced in the agent body but not yet in the frontmatter.

---

### Documentation Agents (2)

#### documentation-architect
- **Category**: documentation
- **Alternatives found**: 3
  - Mintlify (SaaS) -- https://www.mintlify.com -- Developer documentation platform with Git-based workflow, AI-ready features, interactive API playgrounds, Workflows automation for doc updates on code ship -- Maintained: Yes
  - ReadMe (SaaS) -- https://readme.com -- Interactive developer hub: API reference, guides, changelog, forums, GitHub sync, branching for versioned content, real-time API usage analytics -- Maintained: Yes
  - Docusaurus (OSS, Meta) -- https://docusaurus.io -- React-based static site generator maintained by Meta, active development team, large community -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent provides documentation strategy, information architecture, and governance design. Mintlify, ReadMe, and Docusaurus are platforms the agent should recommend; having them in frontmatter improves discoverability and agent context.

#### technical-writer
- **Category**: documentation
- **Alternatives found**: 2
  - Vale (OSS) -- https://vale.sh -- Cross-platform prose linter (Go-based), enforces style guides programmatically, supports Markdown/HTML/RST/AsciiDoc/DITA/XML, used by Grafana, Datadog, Contentsquare -- Maintained: Yes
  - Mintlify Writer (SaaS AI) -- https://www.mintlify.com -- AI-assisted technical writing integrated into the documentation platform; best-practice defaults and LLM-ready output -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent handles all writing craft, accessibility, and content design. Vale is the canonical prose linter already referenced in the agent body. Both tools are direct workflow accelerators for this agent's outputs.

---

### Project-Management Agents (4)

#### agile-coach
- **Category**: project-management
- **Alternatives found**: 2
  - Atlassian Rovo (SaaS, enterprise) -- https://www.atlassian.com/software/rovo -- AI agent suite for Jira/Confluence: sprint planning, backlog refinement, NLP-to-JQL, automated issue creation from meeting notes, readiness checking; auto-enabled for Premium/Enterprise as of April 2026 -- Maintained: Yes
  - Parabol (OSS + SaaS) -- https://www.parabol.co -- Open-source agile meeting tool (retrospectives, standups, planning) with AI meeting summaries posted to Slack; used by Netflix and GitHub -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent provides contextual coaching, diagnosis, and framework selection. Rovo automates routine Jira-based agile operations; Parabol handles meeting facilitation. Neither replaces the strategic coaching role.

#### delivery-manager
- **Category**: project-management
- **Alternatives found**: 2
  - Linear (SaaS) -- https://linear.app -- AI-powered product development platform with MCP server (Feb 2026), Linear Agent (April 2026 beta), auto-categorization, and deep coding agent integrations for project milestone tracking -- Maintained: Yes
  - Atlassian Rovo (SaaS, enterprise) -- https://www.atlassian.com/software/rovo -- AI agent capabilities for Jira release management, cross-team coordination, and delivery tracking -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent orchestrates multi-team releases, go/no-go decisions, and risk management. Linear and Rovo are delivery platform tooling; the agent provides the reasoning, contingency planning, and communication layer.

#### project-plan-tracker
- **Category**: project-management
- **Alternatives found**: 2
  - LinearB (SaaS, free DORA tier) -- https://linearb.io/platform/dora-metrics -- Engineering metrics platform with DORA dashboard (free for all team sizes), sprint tracking, PR workflow automation via gitStream -- Maintained: Yes
  - Linear (SaaS) -- https://linear.app -- MCP server integration enables AI agents to programmatically check and update project milestones and progress -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent reads git/markdown plan files and generates status reports. LinearB and Linear provide automated metrics collection; agent adds interpretation, EVM analysis, and stakeholder-ready reporting.

#### team-progress-tracker
- **Category**: project-management
- **Alternatives found**: 2
  - LinearB (SaaS, free DORA tier) -- https://linearb.io -- DORA metrics, engineering team health dashboards, sprint tracking, workflow automation -- Maintained: Yes
  - Sleuth (SaaS) -- https://www.sleuth.io -- Deploy-first DORA tracking platform connecting issues, commits, PRs, deployments, and incidents with pre-built PR hygiene automations -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent covers DORA, SPACE, Flow metrics, adoption curves, and maturity models. LinearB and Sleuth provide automated data collection for the metrics the agent interprets and contextualises.

---

### SDLC Agents (8)

#### ai-first-kick-starter
- **Category**: sdlc
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Agent is framework-specific (AI-First SDLC post-install advisor). No external tool replicates this role.

#### framework-validator
- **Category**: sdlc
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Agent enforces AI-First SDLC-specific rules (Zero Technical Debt, architecture docs, invariants). No generic tool replicates this framework-specific validation role.

#### language-go-expert
- **Category**: sdlc
- **Alternatives found**: 1
  - MCP Go SDK / gopls MCP (Official Anthropic/Google/Go team) -- https://github.com/modelcontextprotocol/go-sdk -- Official Go SDK for MCP servers and clients, maintained in collaboration with Google; gopls includes experimental built-in MCP server exposing language intelligence to AI assistants -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent provides expert Go guidance, architecture decisions, and idiomatic pattern advice. The official Go MCP SDK and gopls MCP integration are tooling surfaces the agent can recommend to teams building Go-based MCP servers or integrating Go tooling with AI assistants.

#### language-javascript-expert
- **Category**: sdlc
- **Alternatives found**: 1
  - MCP TypeScript SDK (Official Anthropic) -- https://github.com/modelcontextprotocol/typescript-sdk -- Official TypeScript/JavaScript SDK for MCP servers and clients (@modelcontextprotocol/sdk on npm); middleware packages for Express, Hono, Node.js Streamable HTTP -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent covers the full JS/TS ecosystem. The official TypeScript MCP SDK is the canonical reference for teams building MCP-enabled JavaScript tooling, directly relevant to the agent's Node.js and TypeScript guidance.

#### language-python-expert
- **Category**: sdlc
- **Alternatives found**: 1
  - MCP Python SDK (Official Anthropic) -- https://github.com/modelcontextprotocol/python-sdk -- Official Python SDK for MCP servers and clients (mcp on PyPI, v1.3.2); recommended with uv for project setup; official reference servers include Filesystem, Git, Memory, Sequential Thinking -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent covers Python 3.12+, FastAPI, type systems, and AI/ML patterns. The official Python MCP SDK is directly relevant as teams build Python-based MCP tooling, and aligns with the agent's uv/pyright toolchain guidance.

#### project-bootstrapper
- **Category**: sdlc
- **Alternatives found**: 1
  - Cookiecutter (OSS) -- https://github.com/cookiecutter/cookiecutter -- Cross-platform project templating from local or remote templates, pre/post-generate scripts, multi-language support; actively maintained -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent specialises in AI-First SDLC framework bootstrapping via setup-smart.py. Cookiecutter is the canonical generic scaffolding tool and a useful reference for teams building reusable project templates outside the framework.

#### retrospective-miner
- **Category**: sdlc
- **Alternatives found**: 2
  - TeamRetro (SaaS) -- https://www.teamretro.com -- AI-assisted retrospective platform with trend analysis, team health checks, cross-team analytics, SOC 2 Type 2 certified, AI action planning -- Maintained: Yes
  - Parabol (OSS + SaaS) -- https://www.parabol.co -- Open-source agile meeting platform with AI retrospective summaries; full codebase on GitHub -- Maintained: Yes
- **Action**: Added first_party_alternatives to frontmatter
- **Recommendation**: Keep
- **Rationale**: Agent mines retrospective documents to extract framework improvement patterns and build organisational knowledge. TeamRetro and Parabol handle facilitation; this agent provides the cross-project pattern mining and framework evolution layer.

#### sdlc-knowledge-curator
- **Category**: sdlc
- **Alternatives found**: None
- **Action**: No change
- **Recommendation**: Keep
- **Rationale**: Agent curates AI-First SDLC-specific pattern libraries, onboarding paths, and institutional memory. No generic tool replicates this framework-specific knowledge management role.
