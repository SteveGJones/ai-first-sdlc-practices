# Deep Research Prompt: DevOps Specialist Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a DevOps Specialist. This agent will design CI/CD pipelines,
implement infrastructure as code, automate deployment workflows, establish
monitoring and alerting, and drive DevOps culture and practices for projects
of all sizes.

The resulting agent should be able to design end-to-end CI/CD pipelines,
implement GitOps workflows, select and configure IaC tools, establish
deployment strategies (blue-green, canary, rolling), and integrate quality
gates when engaged by the development team.

## Context

This agent is needed because DevOps practices are rapidly evolving with
platform engineering, GitOps, and AI-augmented operations becoming standard.
The existing agent has basic CI/CD and containerization knowledge but lacks
depth on modern platform engineering, supply chain security in pipelines,
cost optimization, and emerging DevOps patterns. The cloud-architect covers
infrastructure, but this agent owns the delivery pipeline and operational
automation.

## Research Areas

### 1. CI/CD Pipeline Design (2025-2026 Best Practices)
- What are the current best practices for CI/CD pipeline architecture?
- How have GitHub Actions, GitLab CI, and other platforms evolved?
- What are the latest patterns for pipeline-as-code and reusable workflows?
- How should pipelines handle monorepos vs polyrepos?
- What are current best practices for pipeline security (secrets, SLSA, provenance)?

### 2. Infrastructure as Code (Current State)
- What are the latest Terraform patterns and best practices (modules, workspaces, state management)?
- How has Pulumi evolved as a programming-language-based IaC alternative?
- What are current patterns for Crossplane and Kubernetes-native IaC?
- How should organizations manage IaC at scale (drift detection, policy-as-code)?
- What are the latest patterns for environment provisioning and management?

### 3. Platform Engineering & Internal Developer Platforms
- What is the current state of platform engineering in 2025-2026?
- How are organizations building internal developer platforms (IDPs)?
- What tools power modern IDPs (Backstage, Port, Humanitec)?
- What are current patterns for developer self-service and golden paths?
- How do platform teams measure developer experience and productivity?

### 4. GitOps & Deployment Strategies
- What are the current best practices for GitOps (ArgoCD, Flux)?
- How should organizations implement progressive delivery (canary, blue-green, feature flags)?
- What are current patterns for multi-environment promotion pipelines?
- How do rollback strategies work in GitOps-driven deployments?
- What are current best practices for database schema migrations in CI/CD?

### 5. DevSecOps & Supply Chain Security
- How should security be integrated into CI/CD pipelines (shift-left)?
- What are current best practices for container image scanning and signing?
- How should organizations implement SBOM generation and verification in pipelines?
- What are the latest SLSA framework requirements for build provenance?
- How do dependency scanning tools compare (Dependabot, Renovate, Snyk)?

### 6. Observability-Driven Development & AIOps
- How are AIOps tools transforming DevOps operations in 2025-2026?
- What are current patterns for observability-driven development?
- How should DevOps teams implement SLO-based alerting?
- What are the latest patterns for incident management automation?
- How do chaos engineering practices integrate with CI/CD?

### 7. Cost Optimization & FinOps for DevOps
- What are current best practices for CI/CD cost optimization?
- How should organizations implement FinOps practices in DevOps?
- What are patterns for right-sizing infrastructure through automation?
- How do spot/preemptible instances integrate into CI/CD pipelines?
- What tools help track and optimize cloud spending from pipelines?

### 8. AI in DevOps (Emerging Patterns)
- How is AI being used in CI/CD pipeline optimization?
- What are current patterns for AI-assisted incident detection and remediation?
- How are LLMs being used for infrastructure troubleshooting?
- What are the implications of AI code generation for CI/CD pipelines?
- How do AI agents interact with DevOps toolchains?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: CI/CD patterns, IaC best practices, deployment strategies, platform engineering principles the agent must know
2. **Decision Frameworks**: "When setting up [pipeline type] for [project size/type], use [tool/pattern] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common DevOps mistakes (snowflake servers, manual deployments, environment drift, alert fatigue, pipeline sprawl)
4. **Tool & Technology Map**: Current DevOps tools across CI/CD, IaC, monitoring, security with selection criteria and comparison matrices
5. **Interaction Scripts**: How to respond to "set up our CI/CD pipeline", "migrate to GitOps", "implement infrastructure as code", "optimize our deployment process"

## Agent Integration Points

This agent should:
- **Complement**: cloud-architect by owning the delivery pipeline (cloud-architect owns infrastructure design, devops-specialist owns automation)
- **Hand off to**: sre-specialist for production operations and incident response
- **Receive from**: solution-architect for deployment requirements and constraints
- **Collaborate with**: security-architect on DevSecOps pipeline integration
- **Never overlap with**: container-platform-specialist on Kubernetes cluster management details
