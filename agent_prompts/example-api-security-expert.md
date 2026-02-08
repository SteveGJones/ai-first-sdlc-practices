# Deep Research Prompt: API Security Expert Agent

## Objective

Research and compile the domain knowledge required to build an AI sub-agent
that acts as an API Security Expert. This agent will identify security
vulnerabilities in API designs, recommend hardening strategies, and enforce
security best practices for projects involving REST, GraphQL, and gRPC APIs.

The resulting agent should be able to review API endpoint designs for security
flaws, recommend authentication/authorization patterns, and detect common
API attack vectors when engaged by the development team.

## Context

This agent is needed because API security requires specialized knowledge that
spans authentication protocols, authorization models, input validation, rate
limiting, and transport security. The existing agent catalog has a general
security agent but lacks API-specific security depth. The closest existing
agents are solution-architect and backend-engineer, but they lack dedicated
security threat modeling for API surfaces.

## Research Areas

### 1. API Authentication & Authorization Patterns
- What are the current best practices for API authentication (OAuth 2.0, API keys, JWT, mTLS)?
- How do authorization models (RBAC, ABAC, ReBAC) apply to API design?
- What are the security implications of different token strategies (opaque vs. self-contained)?
- How should API keys be scoped, rotated, and revoked?
- What are the trade-offs between session-based and stateless authentication for APIs?

### 2. OWASP API Security Top 10
- What are the current OWASP API Security Top 10 vulnerabilities?
- For each vulnerability, what are concrete detection patterns in code?
- What are the recommended mitigations for each vulnerability category?
- How do these vulnerabilities differ between REST, GraphQL, and gRPC?

### 3. Input Validation & Injection Prevention
- What input validation strategies are specific to API endpoints?
- How should request bodies, query parameters, headers, and path parameters be validated?
- What serialization/deserialization vulnerabilities exist (e.g., prototype pollution, XML external entities)?
- How should file uploads be secured in API contexts?

### 4. Rate Limiting & Abuse Prevention
- What rate limiting algorithms are used in production APIs (token bucket, sliding window, fixed window)?
- How should rate limits be configured for different endpoint types?
- What are effective bot detection and abuse prevention strategies?
- How do API gateways and WAFs complement application-level security?

### 5. Transport Security & Data Protection
- What TLS configuration best practices apply to APIs?
- How should sensitive data be handled in request/response bodies?
- What are the security considerations for API versioning and deprecation?
- How should CORS be configured for API endpoints?

### 6. API-Specific Threat Modeling
- What threat modeling frameworks apply to API architectures (STRIDE, PASTA)?
- How should API attack surfaces be enumerated?
- What are common API-specific attack patterns (BOLA, BFLA, mass assignment)?
- How should security testing be integrated into API development workflows?

### 7. Logging, Monitoring & Incident Response
- What API security events should be logged?
- How should anomalous API usage patterns be detected?
- What information should be available for incident response?
- How should API abuse be investigated and mitigated?

## Synthesis Requirements

After completing the research, synthesize findings into:

1. **Core Knowledge Base**: Authentication patterns, authorization models, validation rules, and security headers that the agent must recommend accurately
2. **Decision Frameworks**: "When building [API type], use [auth pattern] because [reason]" structured guidance
3. **Anti-Patterns Catalog**: Common API security mistakes with code-level examples of vulnerable vs. secure implementations
4. **Tool & Technology Map**: Security testing tools (Burp Suite, OWASP ZAP, Postman security tests), libraries (helmet.js, rate-limit), and frameworks
5. **Interaction Scripts**: How to respond to "review my API for security", "recommend auth for this API", "help me implement rate limiting"

## Agent Integration Points

This agent should:
- **Complement**: solution-architect by providing security-specific API design review
- **Hand off to**: backend-engineer when implementation details are decided
- **Receive from**: api-architect when API designs need security review
- **Never overlap with**: general security-specialist on non-API security topics
