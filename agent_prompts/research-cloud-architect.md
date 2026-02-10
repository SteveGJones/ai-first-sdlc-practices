# Deep Research Prompt: Cloud Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Cloud Architect. This agent will design scalable, cost-effective,
and secure cloud infrastructure across AWS, Azure, and GCP, provide objective
multi-cloud guidance, implement Infrastructure as Code patterns, and establish
FinOps practices for cost optimization.

The resulting agent should be able to compare cloud services across providers,
design IaC module structures, implement cost optimization strategies, plan
disaster recovery architectures, and guide cloud migration decisions when
engaged by the development team.

## Context

This agent is needed because cloud architecture decisions directly impact cost,
security, performance, and operational complexity. The existing agent catalog
has devops-specialist for CI/CD and deployment automation, but lacks a dedicated
cloud architect who can make strategic multi-cloud decisions, optimize costs
across providers, and design resilient cloud-native architectures.

## Research Areas

### 1. Multi-Cloud Service Landscape (2025-2026)
- What are the latest AWS, Azure, and GCP service launches relevant to architecture decisions?
- How have serverless offerings evolved (Lambda SnapStart, Azure Flex, Cloud Run gen2)?
- What are the current managed Kubernetes offerings comparison (EKS, AKS, GKE)?
- How do cloud-native database services compare (Aurora, Cosmos DB, AlloyDB, Spanner)?
- What are the current multi-cloud abstraction approaches and their trade-offs?

### 2. Infrastructure as Code (Current State)
- What is the current state of Terraform (OpenTofu fork implications, Terraform CDK)?
- How has Pulumi evolved as a code-first IaC alternative?
- What are the current best practices for IaC module structure and state management?
- How should IaC testing be done (Terratest, Checkov, OPA/Conftest)?
- What are the current drift detection and remediation patterns?

### 3. FinOps and Cost Optimization (2025-2026)
- What are the current FinOps Foundation best practices and maturity model?
- How should organizations implement showback/chargeback for cloud costs?
- What are the current Savings Plans, Reserved Instances, and committed use patterns?
- How should spot/preemptible instances be used effectively?
- What tools exist for cloud cost anomaly detection and optimization (Infracost, Kubecost)?

### 4. Cloud Security (Current Best Practices)
- What are the current cloud IAM best practices (short-lived credentials, workload identity)?
- How should network security be designed in cloud environments (VPC, private endpoints)?
- What are the current CSPM (Cloud Security Posture Management) tools and approaches?
- How should cloud compliance be automated (Config Rules, Azure Policy, SCC)?
- What are the current patterns for securing multi-cloud environments?

### 5. Serverless Architecture (Production Patterns)
- What are the current serverless architecture patterns beyond simple functions?
- How should cold starts be managed across different providers?
- What are the current patterns for serverless workflow orchestration (Step Functions, Durable Functions)?
- How should serverless observability be implemented?
- What are the current cost models and break-even points vs containers?

### 6. Disaster Recovery and Resilience
- What are the current multi-region and multi-AZ architecture patterns?
- How should RTO/RPO targets be translated into infrastructure designs?
- What are the current chaos engineering practices for cloud infrastructure?
- How should backup and restore be automated across cloud services?
- What are the current patterns for active-active multi-region deployments?

### 7. Cloud Migration (Current Frameworks)
- What migration tools exist for each cloud provider (AWS MGN, Azure Migrate, Google Cloud Migrate)?
- What are the current patterns for database migration with minimal downtime?
- How should legacy application modernization be approached?
- What are the current container migration patterns (App2Container, Azure Containerize)?
- How should migration progress be tracked and validated?

### 8. Sustainability and Green Cloud
- What are the current cloud sustainability tools and dashboards?
- How should regions be selected for carbon efficiency?
- What architectural patterns reduce energy consumption?
- How do the providers compare on sustainability commitments?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Cloud service mappings, IaC patterns, cost optimization techniques, security controls, and DR strategies
2. **Decision Frameworks**: "When [requirements], choose [cloud service/pattern] because [reason]" structured guidance with multi-cloud perspective
3. **Anti-Patterns Catalog**: Common cloud architecture mistakes (over-provisioning, no tagging, single-AZ, manual configuration)
4. **Tool & Technology Map**: IaC tools, cost management tools, security scanners, and monitoring solutions with selection criteria
5. **Interaction Scripts**: How to respond to "which cloud should we use", "our cloud bill is too high", "design our DR strategy"

## Agent Integration Points

This agent should:
- **Complement**: devops-specialist by providing strategic cloud decisions while devops handles pipeline automation
- **Hand off to**: container-platform-specialist for Kubernetes-specific architecture decisions
- **Receive from**: solution-architect when system design needs cloud infrastructure mapping
- **Collaborate with**: security-architect on cloud security controls and sre-specialist on reliability
- **Never overlap with**: devops-specialist on CI/CD pipeline configuration or container-platform-specialist on Kubernetes internals
