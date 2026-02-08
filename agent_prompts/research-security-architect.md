# Deep Research Prompt: Security Architect Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Security Architect. This agent will design secure system
architectures, conduct threat modeling, implement zero-trust principles, and
ensure security is embedded throughout the software development lifecycle for
projects of all sizes and compliance requirements.

The resulting agent should be able to perform threat modeling using STRIDE/DREAD,
design zero-trust architectures, recommend compliance controls for frameworks
like SOC 2/ISO 27001/GDPR/HIPAA, and integrate security gates into CI/CD
pipelines when engaged by the development team.

## Context

This agent is needed because security architecture requires specialized strategic
thinking that goes beyond vulnerability scanning or penetration testing. The
existing agent catalog has compliance-auditor for audit reporting and
frontend-security-specialist for client-side security, but lacks a dedicated
security architect who designs defense-in-depth systems and translates compliance
requirements into practical engineering controls.

## Research Areas

### 1. Threat Modeling Methodologies
- What are the current best practices for STRIDE threat modeling in 2025-2026?
- How has DREAD scoring evolved and what alternatives exist (CVSS, risk matrices)?
- What tools support automated threat modeling (Microsoft Threat Modeling Tool, OWASP Threat Dragon, IriusRisk)?
- How should threat models be maintained as systems evolve?
- What is the recommended frequency and scope for threat modeling sessions?

### 2. Zero-Trust Architecture (Current State)
- What are the latest NIST SP 800-207 recommendations for zero-trust?
- How are organizations implementing zero-trust in practice (not just theory)?
- What are the common failure patterns when adopting zero-trust?
- How do service mesh technologies (Istio, Linkerd) enable zero-trust networking?
- What role do Software-Defined Perimeters (SDP) play in modern zero-trust?

### 3. Cloud Security Patterns (2025-2026)
- What are the current cloud-native security best practices across AWS, Azure, GCP?
- How are Cloud Security Posture Management (CSPM) tools evolving?
- What are the latest patterns for securing serverless, container, and Kubernetes workloads?
- How should organizations implement Cloud Workload Protection Platforms (CWPP)?
- What are the current best practices for cloud IAM and cross-account security?

### 4. Supply Chain Security
- What are the current SLSA (Supply-chain Levels for Software Artifacts) framework requirements?
- How should organizations implement SBOM (Software Bill of Materials) generation and validation?
- What are the latest sigstore/cosign practices for container image signing?
- How do dependency confusion and typosquatting attacks work and how to prevent them?
- What tools exist for software supply chain verification (Dependabot, Snyk, Socket)?

### 5. Compliance Frameworks (Practical Implementation)
- What are the practical engineering controls for SOC 2 Type II compliance?
- How does ISO 27001:2022 differ from previous versions and what are the implementation gaps?
- What are the technical requirements for GDPR data protection by design?
- How should HIPAA security rules be translated into cloud infrastructure controls?
- What is the current PCI DSS v4.0 impact on application architecture?

### 6. Application Security (OWASP 2025)
- What are the current OWASP Top 10 for 2025 and how have they changed?
- What are the latest API security threats (OWASP API Security Top 10)?
- How should organizations implement security headers and Content Security Policy?
- What are current best practices for secrets management (HashiCorp Vault, cloud-native)?
- How are AI/ML-specific security threats emerging and how to mitigate them?

### 7. Security Testing and DevSecOps
- What are the current best-in-class SAST tools and how do they compare (Semgrep, SonarQube, CodeQL)?
- How should DAST be integrated into CI/CD pipelines (OWASP ZAP, Burp Suite)?
- What is the current state of IAST (Interactive Application Security Testing)?
- How should security scanning be prioritized to avoid alert fatigue?
- What are the current best practices for security champions programs?

### 8. Encryption and Key Management (Current Standards)
- What is the current status of post-quantum cryptography adoption?
- How should organizations prepare for quantum computing threats?
- What are the latest TLS 1.3 deployment best practices?
- How should key rotation and management be automated in cloud environments?
- What are the current certificate management best practices (ACME, cert-manager)?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Threat modeling methodologies, zero-trust principles, compliance control mappings, and encryption standards that the agent must recommend accurately
2. **Decision Frameworks**: "When designing security for [system type], prioritize [controls] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common security architecture mistakes with specific examples of insecure vs. secure designs
4. **Tool & Technology Map**: Current security tools (SAST/DAST/CSPM/CWPP), frameworks, and libraries with selection criteria
5. **Interaction Scripts**: How to respond to "review our security architecture", "help us prepare for SOC 2", "design zero-trust for our microservices"

## Agent Integration Points

This agent should:
- **Complement**: compliance-auditor by providing architectural security design (auditor tracks compliance, architect designs controls)
- **Hand off to**: frontend-security-specialist for client-side security implementation details
- **Receive from**: solution-architect when system designs need security review
- **Collaborate with**: devops-specialist on DevSecOps pipeline integration
- **Never overlap with**: compliance-auditor on audit reporting and evidence collection
