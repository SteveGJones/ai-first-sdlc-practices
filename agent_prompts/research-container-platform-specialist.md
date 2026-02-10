# Deep Research Prompt: Container Platform Specialist Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Container Platform Specialist. This agent will architect
containerized application deployments, optimize Docker builds, design
Kubernetes workloads, implement Helm chart strategies, configure service mesh
and GitOps workflows, and establish platform engineering practices.

The resulting agent should be able to design Kubernetes deployment architectures,
optimize Docker images for security and size, implement GitOps with ArgoCD/Flux,
configure service mesh for microservices, and build internal developer platforms
when engaged by the development team.

## Context

This agent is needed because container platforms have become the foundation of
modern application deployment, requiring specialized knowledge in Docker
optimization, Kubernetes orchestration, and cloud-native tooling. The existing
agent catalog has devops-specialist for CI/CD pipelines and cloud-architect
for infrastructure strategy, but lacks a dedicated container platform expert
who understands Kubernetes internals, Helm chart design, and platform
engineering patterns.

## Research Areas

### 1. Docker and Container Runtime (2025-2026)
- What are the current Docker BuildKit features and optimization techniques?
- How have container runtimes evolved (containerd, CRI-O, gVisor, Kata)?
- What are the current distroless and minimal base image best practices?
- How should multi-architecture images be built and managed?
- What are the current container image supply chain security patterns (sigstore, Notary v2)?

### 2. Kubernetes Architecture (Current State)
- What are the latest Kubernetes features relevant to workload design (gateway API, CEL)?
- How have Kubernetes operators evolved and what are the current best practices?
- What are the current patterns for multi-tenant Kubernetes clusters?
- How should Kubernetes RBAC be designed for development teams?
- What are the current Kubernetes networking patterns (Cilium, Calico, Gateway API)?

### 3. Helm and Packaging (Current Best Practices)
- What are the current Helm 3 best practices for chart development?
- How should Helm values be structured for multi-environment deployments?
- What are the current alternatives to Helm (Kustomize, cdk8s, Timoni)?
- How should Helm chart testing and validation be automated?
- What are the current OCI-based Helm chart registry patterns?

### 4. Container Security (2025-2026)
- What are the current container image scanning tools and how do they compare (Trivy, Grype, Snyk)?
- How should Pod Security Standards be implemented in production?
- What are the current runtime security tools (Falco, KubeArmor, Tetragon)?
- How should admission controllers be configured for security (Kyverno vs OPA/Gatekeeper)?
- What are the current patterns for secrets management in Kubernetes (External Secrets, Sealed Secrets)?

### 5. Service Mesh (Current Landscape)
- What is the current state of Istio (ambient mesh mode)?
- How has Linkerd evolved and when should it be preferred over Istio?
- What are the current Cilium Service Mesh capabilities?
- How should service mesh be evaluated vs simpler alternatives (ingress + mTLS)?
- What are the current patterns for multi-cluster service mesh?

### 6. GitOps Workflows (Production Patterns)
- What are the current ArgoCD features and best practices (ApplicationSets, Autopilot)?
- How has Flux evolved and how does it compare to ArgoCD?
- What are the current GitOps repository structure patterns?
- How should GitOps handle secrets, progressive delivery, and multi-cluster?
- What are the current patterns for GitOps promotion across environments?

### 7. Platform Engineering (2025-2026)
- What are the current internal developer platform (IDP) patterns?
- How has Backstage evolved as a developer portal?
- What are the current self-service platform patterns for Kubernetes?
- How should golden paths and templates be designed for developer teams?
- What tools exist for platform engineering (Crossplane, Kratix, Port)?

### 8. Autoscaling and Resource Management
- What are the current HPA patterns including custom metrics scaling?
- How should KEDA be used for event-driven autoscaling?
- What are the current VPA recommendations and implementations?
- How should resource requests and limits be tuned in production?
- What tools exist for Kubernetes cost optimization (Kubecost, OpenCost)?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Docker optimization, Kubernetes workload patterns, Helm best practices, service mesh architecture, and GitOps workflows
2. **Decision Frameworks**: "When deploying [workload type], use [pattern] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common container platform mistakes (no resource limits, privileged containers, kubectl apply in CI, shared cluster without RBAC)
4. **Tool & Technology Map**: Container runtimes, Kubernetes distributions, service meshes, GitOps tools, and platform engineering tools with selection criteria
5. **Interaction Scripts**: How to respond to "deploy this to Kubernetes", "our Docker builds are slow", "set up GitOps for our team"

## Agent Integration Points

This agent should:
- **Complement**: devops-specialist by providing deep container platform expertise while devops handles broader CI/CD automation
- **Hand off to**: cloud-architect for cloud-specific infrastructure decisions (EKS vs AKS vs GKE)
- **Receive from**: backend-architect when applications need containerization strategy
- **Collaborate with**: security-architect on container security and observability-specialist on monitoring
- **Never overlap with**: cloud-architect on cloud service selection or devops-specialist on CI/CD pipeline design
