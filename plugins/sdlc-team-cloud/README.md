# sdlc-team-cloud

Cloud infrastructure, container, and SRE specialists.

## Quick start

```bash
/plugin install sdlc-team-cloud@ai-first-sdlc
```

Requires `sdlc-core` to be installed first.

## Agents

| Agent | Purpose |
|-------|---------|
| `cloud-architect` | Designs and governs cloud infrastructure across AWS, Azure, and GCP -- covers multi-cloud strategy, service selection, Infrastructure as Code (Terraform, Pulumi, CloudFormation), cost optimization and FinOps, serverless and event-driven patterns, disaster recovery, and Well-Architected Framework compliance. |
| `container-platform-specialist` | Provides deep expertise in Docker, Kubernetes, Helm, container security, service mesh (Istio, Linkerd, Cilium), GitOps workflows (ArgoCD, Flux), and platform engineering for scalable containerized applications. |
| `sre-specialist` | Designs reliability frameworks covering SLO/SLI/error budget systems, incident response and blameless postmortems, chaos engineering, production monitoring and alerting strategy, capacity planning, and toil reduction through automation. |

## Agent details

### Cloud architect

The cloud-architect provides vendor-neutral guidance across AWS, Azure, and GCP. Key
capabilities include:

- **Multi-cloud service mapping** with equivalence tables across all three providers for
  compute, storage, databases, networking, messaging, AI/ML, and security services.
- **Infrastructure as Code** patterns for Terraform, OpenTofu, Pulumi, Crossplane, Terragrunt,
  CloudFormation, and Bicep -- including module structure, state management, and drift detection.
- **Cost optimization and FinOps** using the FOCUS specification for multi-cloud cost
  normalization, shift-left tools (Infracost, OpenCost, Karpenter), and the four pillars of
  cloud cost optimization.
- **Cloud security architecture** covering defense in depth, workload identity federation,
  CSPM/CNAPP platforms (Wiz, Prisma Cloud), supply chain security (SLSA, Sigstore, SBOM),
  and data sovereignty controls.
- **Migration strategies** using the 7Rs framework with provider-specific migration tools.

### Container platform specialist

The container-platform-specialist covers the full container and orchestration stack:

- **Docker** multi-stage builds, image optimization, Chainguard/distroless base images,
  BuildKit features, and supply chain security with Sigstore/Cosign.
- **Kubernetes** workload patterns, Gateway API (successor to Ingress), Pod Security Admission,
  ValidatingAdmissionPolicy with CEL, and native sidecar containers.
- **Service mesh** selection across Istio (sidecar and ambient modes), Cilium (eBPF-based),
  and Linkerd -- with a decision framework based on workload requirements.
- **GitOps** with ArgoCD and Flux, progressive delivery via Argo Rollouts and Flagger, and
  secrets management with External Secrets Operator.
- **Platform engineering** including Backstage developer portals, Crossplane Compositions,
  and multi-tenancy with vCluster and Capsule.
- **Autoscaling** with HPA, VPA, Karpenter (AWS), KEDA (event-driven), and cost tooling
  (OpenCost, Kubecost, Goldilocks).

### SRE specialist

The sre-specialist ensures production reliability through data-driven operational practices:

- **SLO/SLI/error budget** framework design with multi-window multi-burn-rate alerting
  and tooling selection (Nobl9, Sloth, Pyrra, Datadog SLOs).
- **Incident management** with severity classification (SEV0-SEV4), on-call rotation design,
  runbook creation, blameless postmortem methodology, and platform selection (PagerDuty,
  Incident.io, Rootly).
- **Chaos engineering** following a safe adoption roadmap from staging through continuous
  production chaos, using Gremlin, Chaos Mesh, Litmus, AWS FIS, or Azure Chaos Studio.
- **Reliability patterns** including circuit breakers (Resilience4j, Polly), retry strategies
  with exponential backoff and jitter, timeout configuration, load shedding, and multi-region
  active-active architectures.
- **Toil reduction** targeting the Google SRE 50% engineering time benchmark through runbook
  automation, self-healing systems, and operational work measurement.

## When to use this plugin

Install `sdlc-team-cloud` when your project involves:

- **Cloud-native applications** -- designing infrastructure on AWS, Azure, or GCP with managed
  services, serverless compute, or multi-cloud strategies.
- **Container deployments** -- building and deploying with Docker and Kubernetes, implementing
  service mesh, GitOps, or platform engineering practices.
- **SRE concerns** -- defining SLOs and error budgets, setting up incident response frameworks,
  running chaos engineering experiments, or reducing operational toil.
- **Multi-cloud or hybrid architectures** -- evaluating services across providers, planning
  migrations using the 7Rs framework, or implementing disaster recovery across regions.
- **Cost optimization** -- conducting FinOps reviews, right-sizing infrastructure, implementing
  tagging strategies, or evaluating reserved capacity versus spot instances.
- **Infrastructure as Code** -- choosing between Terraform, OpenTofu, Pulumi, Crossplane, or
  cloud-native IaC tools and establishing module patterns.

The three agents in this plugin work together: the cloud architect designs the infrastructure,
the container platform specialist implements the container and orchestration layer, and the
SRE specialist ensures production reliability and operational excellence.
