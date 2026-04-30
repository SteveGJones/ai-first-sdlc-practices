---
feature_id: auth
module: P1.SP1.M1
---

# Test Specification: Authentication

## Test cases

### TEST-auth-001
Verify PKCE challenge/verifier round-trip.

**satisfies:** REQ-auth-001 via DES-auth-001
**Module:** P1.SP1.M1

### TEST-auth-002
Verify session expires exactly 24h after last activity.

**satisfies:** REQ-auth-002 via DES-auth-002
**Module:** P1.SP1.M1
