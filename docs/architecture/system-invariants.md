# System Invariants

**Project/Feature:** [Feature Name]  
**Date:** [YYYY-MM-DD]  
**Version:** 1.0  
**Maintainers:** [Team/Roles responsible]

---

## Overview

System invariants are conditions that MUST ALWAYS be true throughout the system's lifetime. These are non-negotiable constraints that, if violated, indicate a critical system failure. Every piece of code must respect these invariants.

---

## 🔒 Data Integrity Invariants

### User Data
- [ ] **INV-U001**: User email addresses are ALWAYS unique across the entire system
- [ ] **INV-U002**: User IDs are immutable once created
- [ ] **INV-U003**: Deleted user data is NEVER recoverable (GDPR compliance)
- [ ] **INV-U004**: Password hashes are NEVER stored in plain text
- [ ] **INV-U005**: [Add your invariant]

### Financial Data
- [ ] **INV-F001**: Account balances are NEVER negative
- [ ] **INV-F002**: Transaction amounts ALWAYS use decimal(19,4) precision
- [ ] **INV-F003**: Every debit has a corresponding credit (double-entry)
- [ ] **INV-F004**: Currency codes ALWAYS follow ISO 4217
- [ ] **INV-F005**: [Add your invariant]

### Audit & Compliance
- [ ] **INV-A001**: Audit logs are append-only and immutable
- [ ] **INV-A002**: Every data modification has an audit trail
- [ ] **INV-A003**: Timestamps ALWAYS use UTC with timezone info
- [ ] **INV-A004**: User actions ALWAYS include authentication context
- [ ] **INV-A005**: [Add your invariant]

---

## 🔐 Security Invariants

### Authentication & Authorization
- [ ] **INV-S001**: All API endpoints require authentication (except public list)
- [ ] **INV-S002**: JWT tokens expire within 24 hours
- [ ] **INV-S003**: Failed login attempts are rate-limited to 5 per 15 minutes
- [ ] **INV-S004**: Passwords require minimum 12 characters with complexity
- [ ] **INV-S005**: [Add your invariant]

### Data Protection
- [ ] **INV-D001**: PII is ALWAYS encrypted at rest (AES-256)
- [ ] **INV-D002**: PII is ALWAYS encrypted in transit (TLS 1.3+)
- [ ] **INV-D003**: Encryption keys are rotated every 90 days
- [ ] **INV-D004**: Sensitive data is NEVER logged
- [ ] **INV-D005**: [Add your invariant]

### Access Control
- [ ] **INV-AC001**: Users can ONLY access their own data (unless admin)
- [ ] **INV-AC002**: Admin actions require 2FA
- [ ] **INV-AC003**: Service accounts have minimal required permissions
- [ ] **INV-AC004**: Permissions are deny-by-default
- [ ] **INV-AC005**: [Add your invariant]

---

## 📊 Business Logic Invariants

### Order Processing
- [ ] **INV-O001**: Orders ALWAYS have at least one line item
- [ ] **INV-O002**: Order total equals sum of line items plus tax/shipping
- [ ] **INV-O003**: Cancelled orders CANNOT be modified
- [ ] **INV-O004**: Refunds NEVER exceed original payment amount
- [ ] **INV-O005**: [Add your invariant]

### Inventory Management
- [ ] **INV-I001**: Inventory count is NEVER negative
- [ ] **INV-I002**: Reserved inventory is released after 15 minutes
- [ ] **INV-I003**: Product prices are ALWAYS positive
- [ ] **INV-I004**: Discontinued products CANNOT be ordered
- [ ] **INV-I005**: [Add your invariant]

### Workflow States
- [ ] **INV-W001**: State transitions follow defined state machine
- [ ] **INV-W002**: Completed workflows CANNOT be restarted
- [ ] **INV-W003**: Every state change is logged with reason
- [ ] **INV-W004**: Timeout actions are idempotent
- [ ] **INV-W005**: [Add your invariant]

---

## ⚡ Performance Invariants

### Response Times
- [ ] **INV-P001**: API responses return within 200ms (p95)
- [ ] **INV-P002**: Database queries complete within 100ms
- [ ] **INV-P003**: Background jobs start within 5 seconds
- [ ] **INV-P004**: WebSocket connections timeout after 30s idle
- [ ] **INV-P005**: [Add your invariant]

### Resource Limits
- [ ] **INV-R001**: Request payload size NEVER exceeds 10MB
- [ ] **INV-R002**: Batch operations limited to 1000 items
- [ ] **INV-R003**: Concurrent user sessions limited to 5 per account
- [ ] **INV-R004**: API rate limit: 1000 requests per minute per user
- [ ] **INV-R005**: [Add your invariant]

### Scalability
- [ ] **INV-SC001**: System handles 10x current load without degradation
- [ ] **INV-SC002**: Database connections NEVER exceed pool size
- [ ] **INV-SC003**: Memory usage NEVER exceeds 80% of available
- [ ] **INV-SC004**: CPU usage NEVER sustained above 70%
- [ ] **INV-SC005**: [Add your invariant]

---

## 🔄 Consistency Invariants

### Distributed Systems
- [ ] **INV-DS001**: Eventually consistent within 5 seconds
- [ ] **INV-DS002**: Idempotency keys prevent duplicate processing
- [ ] **INV-DS003**: Distributed locks have automatic timeout
- [ ] **INV-DS004**: Message ordering preserved within partition
- [ ] **INV-DS005**: [Add your invariant]

### Data Synchronization
- [ ] **INV-SY001**: Cache invalidation happens within 1 second
- [ ] **INV-SY002**: Read-after-write consistency guaranteed
- [ ] **INV-SY003**: Replicas lag by maximum 100ms
- [ ] **INV-SY004**: Conflict resolution favors most recent write
- [ ] **INV-SY005**: [Add your invariant]

---

## 🚨 Operational Invariants

### Availability
- [ ] **INV-AV001**: System uptime >= 99.9% (monthly)
- [ ] **INV-AV002**: Planned maintenance < 4 hours/month
- [ ] **INV-AV003**: RTO (Recovery Time Objective) < 1 hour
- [ ] **INV-AV004**: RPO (Recovery Point Objective) < 5 minutes
- [ ] **INV-AV005**: [Add your invariant]

### Monitoring & Alerting
- [ ] **INV-M001**: All errors are logged with correlation ID
- [ ] **INV-M002**: Critical alerts fire within 1 minute
- [ ] **INV-M003**: Metrics retained for 90 days minimum
- [ ] **INV-M004**: Health checks run every 30 seconds
- [ ] **INV-M005**: [Add your invariant]

---

## 📝 Invariant Verification

### Automated Checks

```python
# Example invariant verification code
class InvariantChecker:
    def verify_user_email_unique(self):
        """INV-U001: User emails are unique"""
        duplicate_emails = db.query(
            "SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1"
        )
        assert len(duplicate_emails) == 0, "Duplicate emails found!"
    
    def verify_account_balance_positive(self):
        """INV-F001: Account balances never negative"""
        negative_balances = db.query(
            "SELECT * FROM accounts WHERE balance < 0"
        )
        assert len(negative_balances) == 0, "Negative balances found!"
```

### Verification Schedule
| Invariant Category | Check Frequency | Method |
|-------------------|-----------------|---------|
| Data Integrity | Every transaction | Inline validation |
| Security | Every request | Middleware |
| Business Logic | Every operation | Domain logic |
| Performance | Every minute | Metrics monitoring |
| Consistency | Every 5 minutes | Background job |

---

## 🛡️ Invariant Violation Response

### Severity Levels
1. **CRITICAL**: System halt required
2. **HIGH**: Immediate intervention needed
3. **MEDIUM**: Fix within current sprint
4. **LOW**: Track for future improvement

### Response Procedures
| Invariant | Severity | Detection | Response | Recovery |
|-----------|----------|-----------|----------|----------|
| INV-U001 | CRITICAL | Unique constraint | Block operation | Manual fix |
| INV-F001 | CRITICAL | Balance check | Halt transactions | Rollback |
| INV-S001 | HIGH | Auth middleware | Reject request | Log attempt |
| [Add more] | | | | |

---

## 📚 Implementation Guidelines

### For Developers
1. **ALWAYS** check invariants before state changes
2. **NEVER** bypass invariant checks, even temporarily
3. **ALWAYS** fail fast when invariant violated
4. **NEVER** catch and ignore invariant violations
5. **ALWAYS** log invariant violations with full context

### Code Example
```typescript
// GOOD: Explicit invariant checking
async function transferMoney(from: Account, to: Account, amount: number) {
    // Check invariants FIRST
    if (from.balance - amount < 0) {
        throw new InvariantViolation("INV-F001: Would create negative balance");
    }
    
    // Proceed with operation
    await db.transaction(async (tx) => {
        await tx.debit(from, amount);
        await tx.credit(to, amount);
        
        // Verify invariants still hold
        await verifyAccountInvariants(tx, [from.id, to.id]);
    });
}

// BAD: No invariant checking
async function transferMoney(from: Account, to: Account, amount: number) {
    // DON'T DO THIS - No invariant validation!
    from.balance -= amount;
    to.balance += amount;
    await db.save([from, to]);
}
```

---

## 🔍 Review and Maintenance

### Review Schedule
- **Weekly**: Review violation logs
- **Monthly**: Update invariant definitions
- **Quarterly**: Comprehensive invariant audit
- **Yearly**: Revisit all invariants for relevance

### Sign-offs
| Role | Name | Date | Signature |
|------|------|------|-----------|
| Tech Lead | | | |
| Architect | | | |
| Security Lead | | | |
| Product Owner | | | |

---

<!-- VALIDATION CHECKLIST
- [ ] All invariants are testable
- [ ] All invariants have verification code
- [ ] All invariants have violation procedures
- [ ] No contradicting invariants
- [ ] All edge cases covered
- [ ] Monitoring configured for each
-->