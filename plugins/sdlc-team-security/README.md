# sdlc-team-security

Security, compliance, and privacy specialist agents for the AI-First SDLC framework.

## Quick start

```bash
/plugin install sdlc-team-security@ai-first-sdlc
```

Requires `sdlc-core` to be installed first.

## Agents

| Agent | Purpose |
|-------|---------|
| **security-architect** | Designs secure systems, conducts threat modelling (STRIDE, PASTA), implements zero-trust architectures, and provides strategic security guidance across cloud, supply chain, AI/ML, and post-quantum cryptography domains. |
| **compliance-auditor** | Evaluates projects against compliance frameworks (SOC 2, ISO 27001, PCI DSS, GDPR, EU AI Act, DORA, NIS2), conducts gap analysis, validates evidence, and produces prioritised remediation plans. |
| **compliance-report-generator** | Transforms raw compliance data into audience-tailored reports (team, executive, auditor), creates remediation tracking dashboards with RAG indicators, and generates audit-ready documentation packages. |
| **data-privacy-officer** | Ensures compliance with global data protection regulations (GDPR, CCPA/CPRA, LGPD, PIPL), conducts privacy impact assessments (DPIAs), designs consent management systems, and implements privacy-by-design architecture. |
| **enforcement-strategy-advisor** | Applies behavioural psychology and change management to SDLC adoption, designs enforcement strategies that reduce resistance, plans staged rollouts, coaches teams through standards adoption, and measures effectiveness. |

## When to use this plugin

Install `sdlc-team-security` when your project involves:

- **Sensitive data handling** -- personal data, financial records, health
  information, or credentials that require protection controls
- **Compliance certification** -- preparing for SOC 2 Type II, ISO 27001,
  PCI DSS v4.0, HIPAA, or similar audits and gap analysis
- **Regulatory requirements** -- GDPR, CCPA, EU AI Act, DORA, NIS2, or
  other data protection and operational resilience regulations
- **Security architecture review** -- threat modelling, zero-trust design,
  cloud security posture, Kubernetes security, or supply chain integrity
- **Privacy-by-design** -- consent management, data subject rights (DSARs),
  data minimisation, pseudonymisation, and cross-border transfer mechanisms
- **AI/ML security** -- LLM application security (OWASP Top 10 for LLMs),
  model integrity, prompt injection prevention, and AI governance
- **Standards rollout** -- introducing security or compliance practices
  across multiple teams with behavioural change management support
- **Audit reporting** -- generating executive compliance dashboards,
  remediation tracking reports, or evidence packages for external auditors

## Agent collaboration

The agents in this plugin work together and with agents from other plugins:

- **security-architect** defines what to protect and how; hands off to
  **data-privacy-officer** for privacy-specific requirements and regulations
- **compliance-auditor** identifies compliance gaps; **compliance-report-generator**
  communicates findings to the appropriate audience
- **enforcement-strategy-advisor** designs the behavioural strategy for
  adopting standards that the other agents define
- **security-architect** collaborates with `sdlc-team-fullstack` agents
  (devops-specialist, api-architect) for security control implementation
- **compliance-auditor** collaborates with `sdlc-team-common` agents
  (solution-architect) when remediation requires architectural changes
- **data-privacy-officer** collaborates with `sdlc-team-common` agents
  (database-architect) for pseudonymisation patterns and retention design

## Plugin family

This plugin is part of the AI-First SDLC plugin family. See the
[marketplace](../../.claude-plugin/marketplace.json) for the full list of
available plugins.
