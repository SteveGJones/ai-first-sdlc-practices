"""Sample OAuth login implementation for the assured fixture."""


def login_with_pkce(code: str, verifier: str) -> str:
    # implements: REQ-auth-001, DES-auth-001
    return f"session-for-{code}"


def is_session_active(last_activity_seconds_ago: int) -> bool:
    # implements: REQ-auth-002, DES-auth-002
    return last_activity_seconds_ago < 24 * 60 * 60
