# CLAUDE-CONTEXT-logging.md

Load when implementing logging or debugging production issues.

## 10 Mandatory Logging Points

### 1. Function Entry/Exit
```python
# GOOD - Context and timing
logger.info("Creating user", extra={
    "username": username,
    "email_domain": email.split('@')[1],
    "request_id": request.id
})
# ... function body ...
logger.info("User created", extra={
    "user_id": user.id,
    "duration_ms": elapsed
})

# BAD - No context
logger.info("start")
logger.info("done")
```

### 2. Error Handling
```python
# GOOD - Full context
except Exception as e:
    logger.error("User creation failed", extra={
        "username": username,
        "error": type(e).__name__,
        "message": str(e)
    }, exc_info=True)  # Include stack trace

# BAD - Lost context
except Exception:
    logger.error("Error")
```

### 3. External Calls
```python
# GOOD - Traceable
logger.info("Calling payment API", extra={
    "endpoint": "/charge",
    "amount": amount,
    "request_id": request_id
})
response = api.call()
logger.info("Payment API response", extra={
    "status": response.status,
    "duration_ms": elapsed,
    "request_id": request_id
})

# BAD - No correlation
response = api.call()
```

### 4. State Changes
```python
# GOOD - Audit trail
logger.info("Permission changed", extra={
    "user_id": user.id,
    "old_role": old_role,
    "new_role": new_role,
    "changed_by": admin.id,
    "reason": reason
})

# BAD - No audit trail
user.role = new_role
```

### 5. Security Events
```python
# GOOD - Security monitoring
logger.warning("Failed login", extra={
    "username": username,
    "ip": request.ip,
    "attempts": attempts,
    "user_agent": request.headers['User-Agent']
})

# BAD - Insufficient detail
logger.info("bad login")
```

### 6. Business Milestones & Transactions
```python
# GOOD - Business metrics
logger.info("Order milestone", extra={
    "order_id": order.id,
    "stage": "payment_complete",
    "amount": order.total,
    "items": len(order.items),
    "customer_lifetime_value": customer.ltv
})

# GOOD - Revenue events
logger.info("Revenue event", extra={
    "event_type": "subscription_upgraded",
    "customer_id": customer.id,
    "mrr_delta": 50.00,
    "new_mrr": 150.00
})

# BAD - No business value
logger.debug("processed")
```

### 7. Performance Anomalies
```python
# GOOD - Performance degradation
if response_time > EXPECTED_RESPONSE_TIME * 1.5:
    logger.warning("Performance degradation", extra={
        "operation": "user_search",
        "expected_ms": EXPECTED_RESPONSE_TIME,
        "actual_ms": response_time,
        "degradation_factor": response_time / EXPECTED_RESPONSE_TIME,
        "affected_users": result_count
    })

# GOOD - Slow query
logger.warning("Slow database query", extra={
    "query_type": "user_lookup",
    "duration_ms": query_time,
    "threshold_ms": 100,
    "query_hash": hash(query_text)  # Don't log actual query
})

# BAD - No actionable data
logger.warn("slow")
```

### 8. Configuration Changes
```python
# GOOD - Config update audit
logger.info("Configuration updated", extra={
    "config_key": "rate_limit",
    "old_value": old_limit,
    "new_value": new_limit,
    "updated_by": admin.id,
    "reason": update_reason,
    "effective_at": effective_timestamp
})

# GOOD - Feature flag change
logger.info("Feature flag toggled", extra={
    "flag": "new_checkout_flow",
    "enabled": True,
    "percentage": 25,
    "updated_by": admin.id
})

# BAD - No audit trail
config["limit"] = 100
```

### 9. Data Validation Failures
```python
# GOOD - Validation failure details
logger.warning("Data validation failed", extra={
    "entity": "order",
    "field": "total_amount",
    "constraint": "range_check",
    "expected": "0.01-10000.00",
    "actual": order.total,
    "action": "rejected",
    "request_id": request.id
})

# GOOD - Input sanitization
logger.info("Input sanitized", extra={
    "field": "username",
    "original_length": len(raw_input),
    "sanitized_length": len(clean_input),
    "removed_chars": ["<", ">", "script"]
})

# BAD - No context
logger.error("validation failed")
```

### 10. Resource Utilization Events
```python
# GOOD - Rate limit approaching
logger.warning("Approaching rate limit", extra={
    "resource": "api_calls",
    "current_usage": 950,
    "limit": 1000,
    "percentage_used": 95,
    "reset_time": reset_timestamp,
    "consumer": api_key_hash
})

# GOOD - Connection pool warning
logger.warning("Connection pool pressure", extra={
    "pool": "database_primary",
    "active_connections": 45,
    "max_connections": 50,
    "wait_queue_size": 12,
    "avg_wait_time_ms": 230
})

# BAD - Missing critical data
logger.info("high usage")
```

## Log Levels

- **ERROR**: System failures requiring immediate attention
- **WARN**: Degraded performance, security concerns, recoverable errors
- **INFO**: Business events, state changes, integration points
- **DEBUG**: Detailed flow (NEVER in production)

## Security Rules

### NEVER Log:
- Passwords, API keys, tokens (including JWT, OAuth, refresh tokens)
- Full credit card numbers, bank accounts, routing numbers, IBAN
- Social Security Numbers, driver's license, passport numbers
- Personal health information, patient IDs, prescriptions
- Full email addresses in bulk operations
- Session cookies, authentication artifacts
- Private keys, certificates, cryptographic material
- Biometric data (fingerprints, facial data, voice prints)
- IP addresses (can be PII under GDPR)
- Device identifiers (MAC addresses, IMEI, device IDs)
- Geolocation data (GPS coordinates, physical addresses)
- Phone numbers (use area code only)
- Date of birth (age range okay)
- Government IDs, national identification numbers

### Safe Patterns:
```python
# Sanitize sensitive data
logger.info("User registered", extra={
    "username": username,
    "email_domain": email.split('@')[1],  # Not full email
    "card_last4": card_number[-4:],       # Not full card
    "phone_area": phone[:3],              # Area code only
    "age_range": "25-34",                 # Not exact DOB
    "country": address.country,           # Not full address
})

# Hash for correlation without exposing data
logger.info("User lookup", extra={
    "user_hash": hashlib.sha256(user_id.encode()).hexdigest()[:8],
    "ip_hash": hashlib.sha256(ip_address.encode()).hexdigest()[:8],
})

# NEVER do this
logger.info(f"Login: {username}/{password}")  # SECURITY BREACH!
logger.debug(f"Token: {jwt_token}")           # EXPOSES AUTH!
logger.error(f"SSN validation failed: {ssn}") # PII LEAK!
```

## Structured Logging

### Required Fields:
```json
{
  "timestamp": "ISO-8601",
  "level": "INFO",
  "logger": "ComponentName",
  "method": "functionName",
  "request_id": "correlation-id",
  "message": "Human readable",
  "duration_ms": 123  // If >100ms
}
```

### Python Example:
```python
import structlog
import time

logger = structlog.get_logger()

def create_user(username: str, email: str):
    start = time.time()
    request_id = get_request_id()

    log = logger.bind(
        method="create_user",
        request_id=request_id
    )

    log.info("Creating user",
        username=username,
        email_domain=email.split('@')[1]
    )

    try:
        user = db.create_user(username, email)

        duration = (time.time() - start) * 1000
        log.info("User created",
            user_id=user.id,
            duration_ms=duration
        )

        return user

    except Exception as e:
        duration = (time.time() - start) * 1000
        log.error("User creation failed",
            error_type=type(e).__name__,
            error_message=str(e),
            duration_ms=duration,
            exc_info=True
        )
        raise
```

### JavaScript/TypeScript Example:
```typescript
import winston from 'winston';
import { v4 as uuidv4 } from 'uuid';

const logger = winston.createLogger({
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'app.log' })
  ]
});

async function createUser(username: string, email: string) {
  const start = Date.now();
  const requestId = uuidv4();

  const log = logger.child({
    method: 'createUser',
    requestId
  });

  log.info('Creating user', {
    username,
    emailDomain: email.split('@')[1]
  });

  try {
    const user = await db.createUser(username, email);

    log.info('User created', {
      userId: user.id,
      durationMs: Date.now() - start
    });

    return user;

  } catch (error) {
    log.error('User creation failed', {
      errorType: error.constructor.name,
      errorMessage: error.message,
      durationMs: Date.now() - start,
      stack: error.stack
    });
    throw error;
  }
}
```

## Performance Guidelines

### Skip Logging For:
- Simple getters/setters
- Pure mathematical functions
- High-frequency loops (>1000/sec)

### Use Sampling For:
```python
# Log only 1% of high-frequency events
import random

if random.random() < 0.01:
    logger.info("High frequency event", extra={...})
```

### Async Logging:
```python
# Use async handlers for file output
import logging.handlers
import queue

queue = queue.Queue(-1)
handler = logging.handlers.QueueHandler(queue)
logger.addHandler(handler)
```

## Configuration Examples

### Python logging.yaml:
```yaml
version: 1
formatters:
  json:
    class: pythonjsonlogger.jsonlogger.JsonFormatter
    format: '%(timestamp)s %(level)s %(name)s %(message)s'

handlers:
  file:
    class: logging.handlers.RotatingFileHandler
    filename: app.log
    maxBytes: 104857600  # 100MB
    backupCount: 30
    formatter: json

  console:
    class: logging.StreamHandler
    formatter: json

loggers:
  '':
    level: INFO
    handlers: [console, file]
```

### Validation

After implementation, run:
```bash
python tools/validation/check-logging-compliance.py --threshold 0
```

This ensures:
- All mandatory points have logs
- Log quality meets standards
- No sensitive data in logs
- Performance guidelines followed

## Common Mistakes

1. **Logging in wrong thread**: Always log from main execution path
2. **Over-logging in loops**: Use sampling or aggregate
3. **Under-logging errors**: Always include stack traces
4. **Missing correlation IDs**: Every log needs request_id
5. **Wrong log levels**: Don't use INFO for errors
6. **Synchronous file I/O**: Use async handlers

Remember: Logs are your lifeline in production. Make them count!