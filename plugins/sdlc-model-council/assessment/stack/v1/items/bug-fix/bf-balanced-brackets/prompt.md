# Bug fix: balanced brackets

The module below is named `parens.py`. Its docstring promises that `is_balanced`
correctly matches and nests three bracket kinds: `()`, `[]`, `{}`. The current
implementation only tracks nesting *depth* with a counter, so it wrongly accepts
strings where brackets are mismatched in *type* (for example `"(]"` or `"([)]"`).

Fix the bug so `is_balanced` returns `True` only when every closing bracket
matches the most recently opened bracket of the same kind, and every opened
bracket is eventually closed — matching the docstring's contract exactly.

```python
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
```

Return the complete, corrected file, named exactly `parens.py`.

Respond with ONLY ```file:NAME``` fenced code blocks, one per file you change; no prose.
