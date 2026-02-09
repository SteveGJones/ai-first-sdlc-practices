# Deep Research Prompt: Frontend Security Specialist Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as a Frontend Security Specialist. This agent will identify and
mitigate client-side security vulnerabilities, implement Content Security
Policy, prevent XSS and injection attacks, secure authentication flows,
and ensure frontend applications follow security best practices.

## Research Areas

### 1. Client-Side Security Threats (2025-2026)
- What are the current OWASP Top 10 client-side security threats?
- How have XSS attack vectors evolved with modern frontend frameworks?
- What are the latest patterns for client-side injection prevention?
- How do prototype pollution and supply chain attacks affect frontends?
- What are current patterns for detecting client-side security vulnerabilities?

### 2. Content Security Policy & Headers
- What are current best practices for Content Security Policy configuration?
- How should security headers be configured (HSTS, X-Frame-Options, etc.)?
- What are the latest patterns for CSP with modern SPA frameworks?
- How do Trusted Types prevent DOM-based XSS?
- What are current patterns for CSP reporting and violation monitoring?

### 3. Authentication & Session Security
- What are current best practices for frontend authentication flows?
- How should tokens (JWT, session cookies) be handled securely in browsers?
- What are the latest patterns for OAuth 2.0/OIDC in SPAs (PKCE, BFF)?
- How should multi-factor authentication be implemented on the frontend?
- What are current patterns for secure session management?

### 4. Frontend Supply Chain Security
- What are current best practices for frontend dependency security?
- How should Subresource Integrity (SRI) be implemented?
- What are the latest patterns for npm/yarn security auditing?
- How do CDN integrity and third-party script risks affect frontend security?
- What are current patterns for frontend SBOM and dependency tracking?

### 5. Data Protection in the Browser
- What are current best practices for protecting sensitive data in the browser?
- How should forms handle sensitive data (credit cards, passwords, PII)?
- What are the latest patterns for client-side encryption?
- How do browser storage APIs (localStorage, IndexedDB) affect data security?
- What are current patterns for preventing data leakage through browser APIs?

### 6. Framework-Specific Security
- What are current security best practices for React, Vue, and Angular?
- How do modern frameworks prevent XSS by default and what gaps remain?
- What are the latest patterns for secure component design?
- How should server-side rendering (SSR) security differ from client-side?
- What are current patterns for security testing of frontend applications?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Client-side threats, CSP, auth flows, supply chain security the agent must know
2. **Decision Frameworks**: "When implementing [frontend feature], secure with [approach] because [reason]"
3. **Anti-Patterns Catalog**: Common frontend security mistakes (innerHTML, eval, insecure token storage, missing CSP)
4. **Tool & Technology Map**: Current frontend security tools with selection criteria
5. **Interaction Scripts**: How to respond to "secure our frontend", "configure CSP", "review frontend security"

## Agent Integration Points

This agent should:
- **Complement**: security-architect by specializing in client-side security
- **Hand off to**: security-architect for comprehensive security architecture
- **Receive from**: frontend-architect for implementation details
- **Collaborate with**: code-review-specialist on security-focused code reviews
- **Never overlap with**: security-architect on server-side and infrastructure security
