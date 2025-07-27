# CLAUDE-CONTEXT-logging.md

Load when implementing logging or debugging production issues.

## Mandatory Logging Points

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

### 6. Business Milestones
```python
# GOOD - Business metrics
logger.info("Order milestone", extra={
    "order_id": order.id,
    "stage": "payment_complete",
    "amount": order.total,
    "items": len(order.items)
})

# BAD - No business value
logger.debug("processed")
```

## Log Levels

- **ERROR**: System failures requiring immediate attention
- **WARN**: Degraded performance, security concerns, recoverable errors
- **INFO**: Business events, state changes, integration points
- **DEBUG**: Detailed flow (NEVER in production)

## Security Rules

### NEVER Log:
- Passwords, API keys, tokens
- Full credit card numbers
- Social Security Numbers
- Personal health information
- Full email addresses in bulk
- Session cookies
- Private keys/certificates

### Safe Patterns:
```python
# Sanitize sensitive data
logger.info("User registered", extra={
    "username": username,
    "email_domain": email.split('@')[1],  # Not full email
    "card_last4": card_number[-4:],       # Not full card
})

# NEVER do this
logger.info(f"Login: {username}/{password}")  # SECURITY BREACH!
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