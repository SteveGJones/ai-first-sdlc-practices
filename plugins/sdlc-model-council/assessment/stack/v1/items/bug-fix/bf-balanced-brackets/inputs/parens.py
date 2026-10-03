"""Check whether brackets in a string are balanced and correctly nested."""

OPENERS = "([{"
CLOSERS = ")]}"


def is_balanced(text):
    """Return True if every bracket in `text` is properly matched and nested.

    Supports the three bracket kinds: () [] {}. A string is balanced only if
    every closing bracket matches the most recently opened bracket of the
    same kind, and every opened bracket is eventually closed.
    """
    depth = 0
    for ch in text:
        if ch in OPENERS:
            depth += 1
        elif ch in CLOSERS:
            depth -= 1
        if depth < 0:
            return False
    return depth == 0
