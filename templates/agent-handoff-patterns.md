# Agent Handoff Patterns for Claude Context

> **Practical templates for seamless agent transitions in shared Claude sessions**
> Copy-paste these patterns for effective agent coordination

## Quick Reference: Handoff Commands

```bash
# Create agent memory block
python tools/automation/agent-context-coordinator.py create_memory \
  "security-architect" "API Authentication Review" "JWT token security analysis"

# Document agent transition
python tools/automation/agent-context-coordinator.py create_transition \
  "solution-architect" "security-architect" \
  "Authentication system designed, needs security review" \
  --requirements "Review JWT implementation" "Validate authorization patterns"

# Update agent memory with decision
python tools/automation/agent-context-coordinator.py update_memory \
  "security-architect" \
  --decision "JWT algorithm:Use RS256 for enhanced security" \
  --tag "security-critical" \
  --dependency "performance-engineer needs to verify JWT parsing performance"

# Generate status board
python tools/automation/agent-context-coordinator.py status_board
```

## Pattern 1: Architecture → Security Handoff

### Context Setup
```markdown
# 🏗️ SOLUTION-ARCHITECT → 🔒 SECURITY-ARCHITECT TRANSITION

## Architecture Decisions Completed
- **API Design**: RESTful endpoints for user management
- **Authentication**: JWT-based stateless authentication chosen
- **Data Flow**: User → Auth Service → Protected Resources
- **Integration Points**: LDAP for user directory, Redis for session data

## Security Review Required
**High Priority**:
- [ ] JWT token security (algorithm, expiration, storage)
- [ ] API endpoint authorization patterns
- [ ] LDAP integration security considerations
- [ ] Rate limiting and abuse prevention

**Medium Priority**:
- [ ] Error handling information disclosure
- [ ] Logging security (no sensitive data)
- [ ] Future SSO/MFA architecture compatibility

## Context Transfer Package
- **Business Requirement**: Secure user authentication with LDAP integration
- **Technical Constraint**: Must handle 1000+ concurrent users
- **Compliance Need**: SOC 2 Type II requirements
- **Timeline**: Security review needed by [DATE]

**→ HANDOFF TO security-architect**: Ready for security analysis and threat modeling
```

### Security Architect Response Pattern
```markdown
## 🔒 SECURITY-ARCHITECT ACKNOWLEDGMENT

**CONTEXT RECEIVED**: ✅ Authentication system design from solution-architect
**THREAT MODEL SCOPE**: JWT authentication + LDAP integration + API endpoints

### Initial Security Assessment
**Risk Level**: MEDIUM (mitigatable with proper controls)
**Primary Concerns**:
1. JWT token management and storage
2. LDAP injection vulnerabilities
3. API authorization bypass potential

### Security Decisions Made
- **JWT Algorithm**: RS256 (not HS256) for asymmetric key security
- **Token Expiration**: 15-minute access tokens + 7-day refresh tokens
- **Key Rotation**: Automated every 90 days via Kubernetes secrets

### Cross-Agent Dependencies Identified
- **performance-engineer**: Verify JWT parsing performance under load
- **devops-specialist**: Kubernetes secret management for key rotation
- **ai-test-engineer**: Security-focused test scenarios needed

**STATUS**: Security analysis 80% complete, performance validation needed
**→ NEXT HANDOFF**: performance-engineer for load testing validation
```

## Pattern 2: Security → Performance Handoff

### Security Completion Package
```markdown
# 🔒 SECURITY-ARCHITECT → ⚡ PERFORMANCE-ENGINEER TRANSITION

## Security Requirements Finalized
**Security Controls Implemented**:
- ✅ JWT RS256 with 15-minute expiration
- ✅ Rate limiting: 100 requests/minute/user
- ✅ HTTPS + HSTS headers enforced
- ✅ Input validation on all endpoints

## Performance Validation Needed
**Critical Performance Tests**:
- [ ] JWT parsing/validation latency under load
- [ ] Database connection pooling with LDAP queries
- [ ] Redis performance for refresh token storage
- [ ] API response times with security headers

**Performance Constraints from Security**:
- Rate limiting adds ~2ms per request overhead
- JWT validation requires cryptographic operations
- LDAP queries must complete within 500ms
- Security headers add ~200 bytes per response

## Specific Performance Targets
- **Authentication endpoint**: < 100ms for 95th percentile
- **Protected resource access**: < 200ms with JWT validation
- **Concurrent users**: Support 1000+ simultaneous sessions
- **LDAP integration**: < 500ms for user lookup

**Context Package**: Security implementation complete, now verify performance doesn't degrade user experience

**→ HANDOFF TO performance-engineer**: Performance validation and optimization
```

### Performance Engineer Response Pattern
```markdown
## ⚡ PERFORMANCE-ENGINEER ACKNOWLEDGMENT

**CONTEXT RECEIVED**: ✅ Security-hardened authentication system
**PERFORMANCE SCOPE**: JWT + LDAP + API endpoints under load

### Performance Analysis Started
**Baseline Measurements**:
- JWT parsing: 15ms average (within acceptable range)
- LDAP queries: 350ms average (needs optimization)
- Redis operations: 2ms average (excellent)

### Performance Optimizations Identified
1. **LDAP Connection Pooling**: Reduce query time to <200ms
2. **JWT Caching**: Cache public keys to reduce crypto operations
3. **Database Indexes**: Optimize user lookup queries

### Load Testing Plan
- **Gradual Ramp**: 100 → 500 → 1000 concurrent users
- **Stress Testing**: 1500 users to find breaking point
- **Security Integration**: Test with all security controls enabled

**STATUS**: Performance analysis in progress
**→ NEXT HANDOFF**: ai-test-engineer for comprehensive test scenarios
```

## Pattern 3: Multi-Agent Collaborative Decision

### Decision Documentation Template
```markdown
# 🧠 COLLABORATIVE DECISION: Authentication Strategy Selection

**Decision ID**: decision_20250108_143000
**Participants**: solution-architect, security-architect, performance-engineer, devops-specialist
**Context**: Choose authentication approach for microservices architecture

## Agent Perspectives

**🏗️ solution-architect**:
- Stateless preferred for microservices scalability
- JWT enables distributed authorization without central auth server
- Concern: Token revocation complexity

**🔒 security-architect**:
- JWT acceptable if properly implemented (RS256, short expiration)
- Refresh token rotation essential for security
- Concern: Distributed key management complexity

**⚡ performance-engineer**:
- JWT parsing adds computational overhead but eliminates database lookups
- Caching public keys can reduce crypto operations
- Concern: Large JWT payloads affecting network performance

**🚀 devops-specialist**:
- Kubernetes secrets can handle key rotation
- Istio can inject JWT validation at service mesh level
- Concern: Complexity of distributed key distribution

## Consensus Decision
**SELECTED APPROACH**: JWT with refresh token rotation
- **Access Tokens**: 15-minute expiration, RS256 algorithm
- **Refresh Tokens**: 7-day expiration, stored in Redis with rotation
- **Key Management**: Kubernetes secrets with 90-day rotation
- **Validation**: Service mesh level JWT validation where possible

**Implementation Owner**: solution-architect (overall coordination)
**Security Implementation**: security-architect
**Performance Validation**: performance-engineer
**Infrastructure Setup**: devops-specialist

**Review Checkpoint**: After initial implementation, before production deployment

---
**IMPLEMENTATION IMPACT**:
- Code: JWT middleware + refresh token handling
- Infrastructure: K8s secrets + service mesh configuration
- Monitoring: Token rotation success rates + JWT validation latency
- Testing: Security + performance + infrastructure scenarios
```

## Pattern 4: Critical Issue Escalation

### Issue Escalation Template
```markdown
# 🚨 CRITICAL ISSUE ESCALATION: JWT Validation Performance Degradation

**Issue Detected By**: performance-engineer
**Severity**: HIGH (affecting production readiness)
**Timeline**: Immediate attention required

## Problem Description
JWT validation causing 500ms+ response times under load:
- Baseline: 15ms JWT validation
- Under 500 concurrent users: 500ms+ validation time
- CPU usage spiking to 90% during crypto operations

## Evidence Collected
- Load test results showing performance cliff at 400 concurrent users
- CPU profiling identifies RSA signature verification as bottleneck
- Memory usage stable, purely computational issue

## Cross-Agent Impact Assessment
**🏗️ solution-architect**: Architecture decision (JWT) causing performance issue
**🔒 security-architect**: Cannot compromise on RS256 algorithm for security
**🚀 devops-specialist**: Infrastructure scaling won't solve computational bottleneck
**🎯 critical-goal-reviewer**: Performance requirements not being met

## Escalation to Multi-Agent Resolution
**Required Participants**: solution-architect, security-architect, performance-engineer
**Decision Needed**: Architectural change vs. performance optimization vs. infrastructure scaling
**Timeline**: Resolution needed within 24 hours for production timeline

**Proposed Solutions to Evaluate**:
1. **JWT Caching**: Cache decoded tokens for repeat requests
2. **Async Validation**: Background JWT validation with temp access
3. **Hardware Scaling**: Dedicated crypto acceleration
4. **Hybrid Approach**: Session-based auth for high-frequency endpoints

**→ ESCALATION TO**: critical-goal-reviewer for solution prioritization
```

## Pattern 5: Context Validation Checkpoint

### Validation Checkpoint Template
```markdown
# ✅ CONTEXT VALIDATION CHECKPOINT

**Checkpoint Triggered By**: critical-goal-reviewer
**Validation Scope**: Authentication system implementation
**Timestamp**: 2025-01-08 14:45:00 UTC

## Agent Memory Validation
**🏗️ solution-architect**:
- ✅ Architecture decisions documented with rationale
- ✅ Implementation plan created and reviewed
- ✅ Cross-service integration patterns defined

**🔒 security-architect**:
- ✅ Threat model completed for authentication flow
- ✅ Security controls specified and justified
- ✅ Compliance requirements (SOC 2) addressed

**⚡ performance-engineer**:
- ✅ Performance requirements quantified (<200ms response time)
- ⚠️ ISSUE: Load testing shows 500ms under high concurrency
- ❌ Performance targets not currently met

**🚀 devops-specialist**:
- ⏳ PENDING: Infrastructure setup dependent on performance resolution
- ⏳ PENDING: Kubernetes secret management configuration

## Cross-Agent Consistency Check
- ✅ No conflicting technical decisions detected
- ✅ Security requirements aligned with performance goals
- ❌ **BLOCKER**: Performance issue requires resolution before infrastructure setup

## Context Integrity Assessment
- **Memory Coverage**: 95% (4/4 primary agents have documented decisions)
- **Handoff Quality**: 85% (3/4 handoffs properly documented)
- **Decision Conflicts**: 1 (performance vs. security trade-off unresolved)

## Required Actions
1. **IMMEDIATE**: Multi-agent session to resolve JWT performance issue
2. **NEXT**: Update implementation plan based on performance solution
3. **THEN**: Resume devops-specialist infrastructure work

**VERDICT**: Context integrity maintained, but critical performance blocker requires multi-agent resolution

**→ SCHEDULING**: Multi-agent collaboration session within 2 hours
```

## Usage Guidelines

### For Individual Agents
1. **Start Work**: Check for existing memory blocks from your agent type
2. **Document Decisions**: Use `update_memory` command after significant choices
3. **Prepare Handoffs**: Create transition documentation before switching agents
4. **Acknowledge Receipt**: Confirm handoff received and context understood

### For Teams
1. **Regular Checkpoints**: Validate context integrity every 2-4 hours of work
2. **Issue Escalation**: Use escalation pattern when single agent can't resolve
3. **Decision Documentation**: Record all multi-agent collaborative decisions
4. **Status Monitoring**: Generate status boards to track agent coordination

### For Context Health
```bash
# Check agent coordination health
python tools/automation/agent-context-coordinator.py validate

# Expected healthy metrics:
# - Health Score: > 0.8
# - Unacknowledged Handoffs: < 2
# - Decision Conflicts: 0
# - Recent Updates: > 80% of active agents
```

These patterns ensure that specialized knowledge is preserved, decisions are tracked, and handoffs are clear even within Claude's single-context architecture.
