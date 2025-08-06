# System Invariants - E-Commerce Checkout System

**Project:** FastCart Checkout System
**Version:** 1.0
**Last Updated:** 2024-07-25
**Owner:** Architecture Team

## Overview
These invariants represent conditions that must ALWAYS be true in our system. Violation of any invariant indicates a critical system fault requiring immediate intervention.

## Data Integrity Invariants

### Financial Invariants

- [ ] **INV-F001**: Order total MUST equal sum of (items + tax + shipping - discounts)
  - **Verification**: Database constraint, application validation
  - **Monitoring**: Reconciliation job every 5 minutes
  - **Recovery**: Halt orders, alert finance team

- [ ] **INV-F002**: Payment amount MUST equal order total (within $0.01 for rounding)
  - **Verification**: Payment service validation before processing
  - **Monitoring**: Payment/order mismatch alerts
  - **Recovery**: Refund overpayments, collect underpayments

- [ ] **INV-F003**: Refund amount MUST NOT exceed original payment amount
  - **Verification**: Refund service validation
  - **Monitoring**: Daily refund audit report
  - **Recovery**: Block refund, manual review required

- [ ] **INV-F004**: Account balance MUST NEVER be negative
  - **Verification**: Database constraint, application checks
  - **Monitoring**: Real-time balance monitoring
  - **Recovery**: Immediate freeze, investigation required

### Inventory Invariants

- [ ] **INV-I001**: Available inventory MUST be >= 0
  - **Verification**: Database constraint CHECK (available >= 0)
  - **Monitoring**: Inventory level alerts
  - **Recovery**: Block sales, investigate discrepancy

- [ ] **INV-I002**: Reserved inventory MUST NOT exceed physical inventory
  - **Verification**: Reservation service validation
  - **Monitoring**: Hourly reconciliation
  - **Recovery**: Release oldest reservations

- [ ] **INV-I003**: Sum of (available + reserved + sold) MUST equal total inventory
  - **Verification**: Inventory audit job
  - **Monitoring**: Real-time discrepancy alerts
  - **Recovery**: Inventory reconciliation process

### Order State Invariants

- [ ] **INV-O001**: Order status transitions MUST follow defined state machine
  - **Valid transitions**: pending → processing → shipped → delivered
  - **Invalid transitions**: shipped → pending, delivered → processing
  - **Verification**: State machine enforcement in code
  - **Monitoring**: Invalid transition alerts
  - **Recovery**: Manual status correction with audit trail

- [ ] **INV-O002**: Cancelled orders MUST NOT have shipments
  - **Verification**: Shipping service validation
  - **Monitoring**: Daily cancelled order audit
  - **Recovery**: Halt shipment, refund if needed

- [ ] **INV-O003**: Every completed order MUST have a payment record
  - **Verification**: Order completion validation
  - **Monitoring**: Orphaned order alerts
  - **Recovery**: Payment reconciliation process

## Security Invariants

### Authentication Invariants

- [ ] **INV-S001**: User sessions MUST expire after 30 minutes of inactivity
  - **Verification**: Session management service
  - **Monitoring**: Active session auditing
  - **Recovery**: Force logout all expired sessions

- [ ] **INV-S002**: Failed login attempts MUST lock account after 5 attempts
  - **Verification**: Authentication service
  - **Monitoring**: Brute force attack detection
  - **Recovery**: Account unlock after 15 minutes or manual reset

- [ ] **INV-S003**: API tokens MUST have expiration dates
  - **Verification**: Token generation service
  - **Monitoring**: Expired token usage alerts
  - **Recovery**: Revoke all non-expiring tokens

### Data Protection Invariants

- [ ] **INV-D001**: Credit card numbers MUST NEVER be stored in our database
  - **Verification**: Code review, database scans
  - **Monitoring**: PII detection scanning
  - **Recovery**: Immediate data purge, security incident process

- [ ] **INV-D002**: All PII MUST be encrypted at rest
  - **Verification**: Encryption validation checks
  - **Monitoring**: Unencrypted data scanning
  - **Recovery**: Emergency encryption, access review

- [ ] **INV-D003**: Audit logs MUST be immutable
  - **Verification**: Write-only permissions
  - **Monitoring**: Log modification attempts
  - **Recovery**: Restore from backup, investigation

## Business Logic Invariants

### Pricing Invariants

- [ ] **INV-P001**: Discount percentage MUST be between 0 and 100
  - **Verification**: Discount service validation
  - **Monitoring**: Invalid discount alerts
  - **Recovery**: Cap at boundaries, log attempts

- [ ] **INV-P002**: Product price MUST be > 0
  - **Verification**: Product service validation
  - **Monitoring**: Zero/negative price alerts
  - **Recovery**: Block product, require manual update

- [ ] **INV-P003**: Shipping cost MUST be >= 0
  - **Verification**: Shipping calculator validation
  - **Monitoring**: Negative shipping alerts
  - **Recovery**: Default to standard shipping rate

### User Invariants

- [ ] **INV-U001**: Email addresses MUST be unique across accounts
  - **Verification**: Database unique constraint
  - **Monitoring**: Duplicate account detection
  - **Recovery**: Merge accounts process

- [ ] **INV-U002**: User MUST have valid email before checkout
  - **Verification**: Checkout service validation
  - **Monitoring**: Invalid email attempts
  - **Recovery**: Block checkout, require email

## Performance Invariants

### Response Time Invariants

- [ ] **INV-R001**: API response time MUST be < 5 seconds
  - **Verification**: API gateway timeout
  - **Monitoring**: Response time metrics
  - **Recovery**: Circuit breaker activation

- [ ] **INV-R002**: Database query time MUST be < 1 second
  - **Verification**: Query timeout settings
  - **Monitoring**: Slow query log
  - **Recovery**: Kill long-running queries

### Capacity Invariants

- [ ] **INV-C001**: Queue depth MUST NOT exceed 10,000 messages
  - **Verification**: Queue monitoring
  - **Monitoring**: Queue depth alerts
  - **Recovery**: Scale consumers, throttle producers

- [ ] **INV-C002**: Memory usage MUST NOT exceed 80% of available
  - **Verification**: Container limits
  - **Monitoring**: Memory alerts
  - **Recovery**: Automatic pod restart

## Consistency Invariants

### Data Consistency

- [ ] **INV-DC001**: Cart items MUST reference existing products
  - **Verification**: Foreign key constraints
  - **Monitoring**: Orphaned cart item detection
  - **Recovery**: Remove invalid items

- [ ] **INV-DC002**: Order addresses MUST have all required fields
  - **Verification**: Address validation service
  - **Monitoring**: Incomplete address detection
  - **Recovery**: Request address update

### Temporal Invariants

- [ ] **INV-T001**: Order creation date MUST be <= shipping date
  - **Verification**: Shipping service validation
  - **Monitoring**: Temporal anomaly detection
  - **Recovery**: Correct dates, investigate cause

- [ ] **INV-T002**: Payment timestamp MUST be within order session window
  - **Verification**: Payment service validation
  - **Monitoring**: Out-of-window payment alerts
  - **Recovery**: Manual payment verification

## Monitoring and Alerting

### Alert Priority Levels
- **P0 (Critical)**: Financial invariants, security invariants
- **P1 (High)**: Data integrity, business logic invariants
- **P2 (Medium)**: Performance invariants
- **P3 (Low)**: Non-critical consistency issues

### Verification Schedule
- **Real-time**: Financial and security invariants
- **Every 5 minutes**: Order and inventory invariants
- **Hourly**: Performance and consistency invariants
- **Daily**: Comprehensive invariant audit

## Testing Requirements

Each invariant MUST have:
1. Unit test verifying enforcement
2. Integration test validating detection
3. Chaos test confirming recovery
4. Load test ensuring performance

## Incident Response

When invariant violation detected:
1. **Immediate**: Alert on-call engineer
2. **Within 5 min**: Assess impact scope
3. **Within 15 min**: Implement recovery action
4. **Within 1 hour**: Root cause analysis
5. **Within 24 hours**: Post-mortem report

## Review and Updates

- Monthly review of invariant violations
- Quarterly update of invariant definitions
- Annual comprehensive invariant audit
- Add new invariants as system evolves