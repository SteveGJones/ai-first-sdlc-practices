"""E1 fixture: source intentionally has no # implements: TEST-fxe1-001 annotation."""


def do_operation() -> int:  # implements: DES-fxe1-001
    return 42
