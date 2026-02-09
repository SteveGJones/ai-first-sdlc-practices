# Deep Research Prompt: Compliance Auditor Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Compliance Auditor. This agent will conduct compliance
assessments, track remediation progress, generate audit reports, implement
compliance-as-code, and ensure projects adhere to regulatory requirements,
industry standards, and organizational policies.

The resulting agent should be able to perform compliance gap analysis,
design audit frameworks, create compliance dashboards, implement automated
compliance checking, and prepare organizations for external audits when
engaged by the development team.

## Context

This agent is needed because compliance requirements are expanding rapidly
with new regulations (EU AI Act, DORA, NIS2) and evolving standards (SOC 2,
ISO 27001:2022, PCI DSS v4.0). The existing agent has solid compliance
auditing structure but lacks depth on modern compliance-as-code patterns,
automated evidence collection, continuous compliance monitoring, and
AI-specific regulations. The security-architect designs security controls;
this agent verifies and reports on their effectiveness.

## Research Areas

### 1. Modern Compliance Frameworks (2025-2026)
- What are the current major compliance frameworks (SOC 2, ISO 27001, PCI DSS, HIPAA, GDPR)?
- How has SOC 2 Type II evolved and what are common control gaps?
- What are the requirements of ISO 27001:2022 and how to transition?
- What is PCI DSS v4.0 and its impact on software development?
- How do GDPR and CCPA/CPRA enforcement trends affect technical requirements?

### 2. Emerging Regulations & AI Compliance
- What are the key requirements of the EU AI Act and its implementation timeline?
- How does DORA (Digital Operational Resilience Act) affect software organizations?
- What are the NIS2 Directive requirements for software security?
- How should organizations prepare for AI governance and ethics regulations?
- What are current best practices for AI model audit trails and explainability?

### 3. Compliance-as-Code & Automation
- What are current best practices for implementing compliance-as-code?
- How do tools like Open Policy Agent (OPA), Rego, and Sentinel work?
- What are the latest patterns for automated evidence collection?
- How should organizations implement policy-as-code in CI/CD pipelines?
- What tools support continuous compliance monitoring (Vanta, Drata, Secureframe)?

### 4. Audit Methodology & Process
- What are current best practices for conducting software compliance audits?
- How should organizations structure internal audit programs?
- What are the latest patterns for risk-based audit approaches?
- How do continuous auditing and continuous monitoring differ?
- What are current practices for audit reporting and stakeholder communication?

### 5. Evidence Collection & Documentation
- What are current best practices for compliance evidence management?
- How should organizations automate evidence collection for audits?
- What are the latest patterns for compliance documentation (policies, procedures, records)?
- How do GRC (Governance, Risk, Compliance) platforms support evidence management?
- What are current practices for audit trail and log management?

### 6. Software Development Compliance
- What are current best practices for secure SDLC compliance?
- How should organizations enforce coding standards and code quality compliance?
- What are the latest patterns for license compliance and open-source governance?
- How do SBOM requirements affect compliance programs?
- What are current practices for change management and release compliance?

### 7. Cross-Framework Compliance Mapping
- How should organizations map controls across multiple frameworks?
- What are current patterns for unified compliance frameworks?
- How do common control frameworks (CCM, NIST CSF) simplify multi-standard compliance?
- What tools support cross-framework compliance mapping?
- How should organizations prioritize when frameworks conflict?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Compliance frameworks, audit methodologies, evidence requirements, regulatory landscape the agent must know
2. **Decision Frameworks**: "When auditing [project type] for [framework], check [controls] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common compliance mistakes (checkbox compliance, audit-only culture, manual evidence collection, siloed compliance)
4. **Tool & Technology Map**: Current compliance tools (GRC platforms, policy-as-code, evidence collection, audit management) with selection criteria
5. **Interaction Scripts**: How to respond to "audit our compliance", "prepare for SOC 2 audit", "implement compliance-as-code", "map our controls across frameworks"

## Agent Integration Points

This agent should:
- **Complement**: security-architect by verifying control effectiveness (architect designs controls, auditor verifies and reports)
- **Hand off to**: security-architect for control remediation design
- **Receive from**: sdlc-enforcer for process compliance data
- **Collaborate with**: github-integration-specialist on repository compliance checks
- **Never overlap with**: security-architect on security control design and implementation
