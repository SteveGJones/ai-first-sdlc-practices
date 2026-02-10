# Deep Research Prompt: Data Privacy Officer Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Data Privacy Officer. This agent will ensure data privacy
compliance, implement privacy-by-design, manage data subject rights, conduct
privacy impact assessments, and guide organizations on data protection
regulations across jurisdictions.

## Research Areas

### 1. Data Privacy Regulations (2025-2026)
- What are the current GDPR enforcement trends and key requirements?
- How have CCPA/CPRA evolved and what are the technical requirements?
- What are the emerging privacy regulations globally (Brazil LGPD, India DPDP, China PIPL)?
- How does the EU AI Act intersect with data privacy regulations?
- What are current patterns for multi-jurisdiction privacy compliance?

### 2. Privacy-by-Design Implementation
- What are current best practices for privacy-by-design in software development?
- How should data minimization principles be implemented technically?
- What are the latest patterns for purpose limitation in data processing?
- How should consent management systems be designed?
- What are current patterns for privacy architecture in microservices?

### 3. Data Subject Rights
- What are current best practices for implementing data subject access requests (DSARs)?
- How should right to deletion (right to be forgotten) be implemented technically?
- What are the latest patterns for data portability implementation?
- How should automated decision-making transparency be provided?
- What are current patterns for consent withdrawal and data processing cessation?

### 4. Privacy Impact Assessment
- What are current best practices for conducting privacy impact assessments (PIAs/DPIAs)?
- How should data flow mapping be conducted for privacy analysis?
- What are the latest patterns for risk assessment in data processing?
- How do privacy engineering tools support automated assessment?
- What are current patterns for ongoing privacy monitoring?

### 5. Technical Privacy Controls
- What are current best practices for data anonymization and pseudonymization?
- How do differential privacy and synthetic data techniques work?
- What are the latest patterns for data encryption for privacy?
- How should data retention and automatic deletion be implemented?
- What are current patterns for privacy-preserving analytics?

### 6. AI & Privacy
- How do AI systems create unique privacy challenges?
- What are current best practices for privacy in ML training data?
- What are the latest patterns for federated learning and privacy?
- How should AI model outputs be audited for privacy leakage?
- What are current patterns for responsible AI data governance?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Privacy regulations, PbD patterns, technical controls, assessment methods the agent must know
2. **Decision Frameworks**: "When processing [data type] for [purpose], implement [control] because [regulation]"
3. **Anti-Patterns Catalog**: Common privacy mistakes (over-collection, no retention policy, consent theater, ignoring data flows)
4. **Tool & Technology Map**: Current privacy tools (consent, anonymization, assessment) with selection criteria
5. **Interaction Scripts**: How to respond to "ensure GDPR compliance", "conduct privacy assessment", "implement data deletion"

## Agent Integration Points

This agent should:
- **Complement**: security-architect by focusing on privacy (security handles confidentiality/integrity/availability)
- **Hand off to**: security-architect for security control implementation
- **Receive from**: database-architect for data model privacy review
- **Collaborate with**: compliance-auditor on privacy audit requirements
- **Never overlap with**: security-architect on general security architecture
