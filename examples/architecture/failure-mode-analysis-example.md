# Failure Mode and Effects Analysis (FMEA) - E-Commerce Checkout System

**Project:** FastCart Checkout System
**Version:** 1.0
**Last Updated:** 2024-07-25
**Risk Assessment Team:** Architecture, Security, Operations

## Overview
This FMEA identifies potential failure modes in the checkout system, evaluates their risk using Risk Priority Numbers (RPN), and defines mitigation strategies.

## Risk Priority Number (RPN) Calculation
**RPN = Severity × Occurrence × Detection**

### Rating Scales

| Score | Severity | Occurrence | Detection |
|-------|----------|------------|-----------|
| 1 | No impact | < 0.01% | Always detected |
| 2 | Minor inconvenience | 0.01-0.1% | Usually detected |
| 3 | Customer irritation | 0.1-1% | Sometimes detected |
| 4 | Lost sale | 1-5% | Rarely detected |
| 5 | Multiple lost sales | 5-10% | Very rarely detected |
| 6 | Customer data exposed | 10-20% | Hard to detect |
| 7 | Financial loss | 20-30% | Very hard to detect |
| 8 | Compliance violation | 30-40% | Extremely hard |
| 9 | Major data breach | 40-50% | Nearly impossible |
| 10 | Business ending | > 50% | Undetectable |

## Critical Failure Modes (RPN > 100)

### Payment Processing Failures

| Failure Mode | Failure Effect | Severity | Occurrence | Detection | RPN | Priority |
|--------------|----------------|----------|------------|-----------|-----|----------|
| Payment gateway complete outage | No orders can be processed | 9 | 2 | 1 | **18** | High |
| Double charging customer | Customer charged twice for same order | 8 | 3 | 3 | **72** | High |
| Payment succeeds but order fails to record | Customer charged without order | 9 | 2 | 4 | **72** | High |
| Credit card data exposed in logs | PCI violation, data breach | 10 | 2 | 6 | **120** | Critical |
| Payment webhook not received | Order stuck in pending state | 6 | 4 | 3 | **72** | High |

#### Mitigation Strategies
1. **Payment Gateway Outage**
   - Current: Single payment provider
   - Mitigation: Implement PayPal as backup
   - New RPN: 9 × 2 × 1 = 18 (Acceptable)

2. **Double Charging**
   - Current: No idempotency
   - Mitigation: Implement idempotency keys
   - New RPN: 8 × 1 × 2 = 16 (Acceptable)

3. **Credit Card in Logs**
   - Current: No log scanning
   - Mitigation: PII scanner, log sanitization
   - New RPN: 10 × 1 × 2 = 20 (Acceptable)

### Data Integrity Failures

| Failure Mode | Failure Effect | Severity | Occurrence | Detection | RPN | Priority |
|--------------|----------------|----------|------------|-----------|-----|----------|
| Inventory oversold | Ship items we don't have | 7 | 4 | 3 | **84** | High |
| Price changes during checkout | Customer charged wrong amount | 6 | 3 | 2 | **36** | Medium |
| Tax calculation error | Legal compliance issue | 8 | 2 | 4 | **64** | High |
| Shopping cart data loss | Customer loses items | 4 | 5 | 2 | **40** | Medium |
| Order data corruption | Wrong items shipped | 7 | 2 | 5 | **70** | High |

#### Mitigation Strategies
1. **Inventory Oversold**
   - Current: Optimistic locking
   - Mitigation: Pessimistic locking, real-time sync
   - New RPN: 7 × 2 × 2 = 28 (Acceptable)

2. **Order Data Corruption**
   - Current: No checksums
   - Mitigation: Data integrity checks, audit trail
   - New RPN: 7 × 1 × 2 = 14 (Acceptable)

### Performance and Availability Failures

| Failure Mode | Failure Effect | Severity | Occurrence | Detection | RPN | Priority |
|--------------|----------------|----------|------------|-----------|-----|----------|
| Database connection pool exhausted | Checkout hangs | 7 | 4 | 2 | **56** | High |
| Memory leak in payment service | Service crash | 8 | 3 | 3 | **72** | High |
| DDoS attack on checkout | Site unavailable | 8 | 3 | 2 | **48** | Medium |
| Cache stampede on Black Friday | System overload | 9 | 4 | 3 | **108** | Critical |
| API rate limits hit | Integrations fail | 6 | 4 | 2 | **48** | Medium |

#### Mitigation Strategies
1. **Cache Stampede**
   - Current: Simple caching
   - Mitigation: Cache warming, queue system
   - New RPN: 9 × 2 × 2 = 36 (Acceptable)

2. **Memory Leak**
   - Current: No monitoring
   - Mitigation: Memory profiling, auto-restart
   - New RPN: 8 × 2 × 1 = 16 (Acceptable)

### Security Failures

| Failure Mode | Failure Effect | Severity | Occurrence | Detection | RPN | Priority |
|--------------|----------------|----------|------------|-----------|-----|----------|
| SQL injection in search | Database compromised | 10 | 3 | 5 | **150** | Critical |
| XSS in checkout form | Payment data stolen | 9 | 3 | 4 | **108** | Critical |
| Session hijacking | Account takeover | 8 | 3 | 5 | **120** | Critical |
| Weak password reset | Account compromise | 7 | 4 | 4 | **112** | Critical |
| API authentication bypass | Data breach | 10 | 2 | 6 | **120** | Critical |

#### Mitigation Strategies
1. **SQL Injection**
   - Current: Basic sanitization
   - Mitigation: Parameterized queries, WAF
   - New RPN: 10 × 1 × 2 = 20 (Acceptable)

2. **XSS Attacks**
   - Current: Output encoding
   - Mitigation: CSP headers, input validation
   - New RPN: 9 × 1 × 2 = 18 (Acceptable)

### Integration Failures

| Failure Mode | Failure Effect | Severity | Occurrence | Detection | RPN | Priority |
|--------------|----------------|----------|------------|-----------|-----|----------|
| Shipping API timeout | Can't calculate shipping | 5 | 6 | 2 | **60** | High |
| Tax service returns wrong rate | Compliance violation | 7 | 3 | 4 | **84** | High |
| Email service down | No order confirmations | 3 | 5 | 1 | **15** | Low |
| Inventory sync lag | Oversell products | 6 | 4 | 3 | **72** | High |
| Analytics tracking fails | Lost business insights | 2 | 6 | 2 | **24** | Low |

#### Mitigation Strategies
1. **Shipping API Timeout**
   - Current: No fallback
   - Mitigation: Cached rates, multiple providers
   - New RPN: 5 × 3 × 1 = 15 (Acceptable)

2. **Tax Service Errors**
   - Current: Direct API calls
   - Mitigation: Validation layer, audit trail
   - New RPN: 7 × 2 × 2 = 28 (Acceptable)

## Failure Mode Interaction Matrix

Some failures can trigger cascading effects:

| Primary Failure | Can Trigger | Combined RPN |
|-----------------|-------------|--------------|
| Database outage | Payment failures, inventory issues | 200+ |
| Payment gateway down | Cart abandonment, support overload | 150+ |
| Cache failure | Database overload, slow response | 180+ |
| Network partition | Split brain, data inconsistency | 160+ |

## Monitoring and Detection Improvements

### Early Warning Systems
```yaml
Synthetic Monitoring:
  - Checkout flow every 5 minutes
  - Payment test transactions hourly
  - Integration health checks

Real User Monitoring:
  - Checkout funnel analytics
  - Error rate by step
  - Performance metrics

Anomaly Detection:
  - Unusual traffic patterns
  - Abnormal error rates
  - Payment success rate drops
```

### Automated Response
```typescript
class FailureDetector {
  async detectAndRespond() {
    // Payment failure rate spike
    if (paymentFailureRate > 0.05) {
      await this.switchToBackupPaymentProvider();
      await this.alertOncall('Payment failures above 5%');
    }

    // Inventory discrepancy
    if (inventoryMismatchCount > 10) {
      await this.pauseCheckout();
      await this.triggerInventoryReconciliation();
    }

    // Performance degradation
    if (p95ResponseTime > 2000) {
      await this.enableCacheBoost();
      await this.scaleOutServices();
    }
  }
}
```

## Testing Requirements

### Failure Injection Testing
1. **Chaos Monkey**: Random service failures
2. **Latency Injection**: Slow network conditions
3. **Resource Exhaustion**: Memory/CPU limits
4. **Dependency Failures**: Third-party outages

### Security Testing
1. **Penetration Testing**: Quarterly
2. **Vulnerability Scanning**: Weekly
3. **Dependency Scanning**: Daily
4. **Code Security Review**: Every PR

## Recovery Time Objectives (RTO)

| Failure Type | Current RTO | Target RTO | Recovery Method |
|--------------|-------------|------------|-----------------|
| Payment gateway | 15 min | 2 min | Auto-failover |
| Database failure | 30 min | 5 min | Read replica promotion |
| Complete outage | 2 hours | 30 min | Full DR site |
| Data corruption | 4 hours | 1 hour | Point-in-time recovery |

## Lessons from Past Incidents

1. **Black Friday 2023**: Cache stampede caused 2-hour outage
   - Learning: Implement cache warming
   - Status: Implemented

2. **Payment Duplicate Bug**: 150 customers double-charged
   - Learning: Idempotency required
   - Status: In progress

3. **Inventory Sync Failure**: Oversold 500 items
   - Learning: Real-time inventory critical
   - Status: Planned for Q3

## Review and Update Schedule

- **Weekly**: Review high-priority failures
- **Monthly**: Update RPN scores based on new data
- **Quarterly**: Comprehensive FMEA review
- **After Incidents**: Update relevant failure modes

## Success Metrics

- Reduce Critical failures (RPN > 100) to zero
- Achieve < 0.1% transaction failure rate
- Maintain 99.99% availability
- Zero security incidents
- < 30 minute recovery for any failure
