---
feature_id: auth
module: P1.SP1.M1
---

# Design Specification: Authentication

## Design elements

### DES-auth-001
Use PKCE (RFC 7636) for OAuth authorisation code flow.

**satisfies:** REQ-auth-001
**Module:** P1.SP1.M1

### DES-auth-002
Store session expiry as absolute UTC timestamp; check on every request.

**satisfies:** REQ-auth-002
**Module:** P1.SP1.M1
