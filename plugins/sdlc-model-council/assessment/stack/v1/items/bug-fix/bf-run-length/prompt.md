# Bug fix: run-length decode

The module below is named `run_length.py`. `encode` is correct: it turns a
string into a list of `(char, count)` run-length pairs. `decode` is supposed to
be its exact inverse (`decode(encode(s)) == s` for any string `s`), but it
currently drops one instance of every character.

Fix the bug in `decode` so it is the exact inverse of `encode`.

```python
"""Run-length encoding and decoding utilities."""


def encode(text):
    """Encode `text` as a list of (char, count) run-length pairs."""
    if not text:
        return []
    runs = []
    current = text[0]
    count = 1
    for ch in text[1:]:
        if ch == current:
            count += 1
        else:
            runs.append((current, count))
            current = ch
            count = 1
    runs.append((current, count))
    return runs


def decode(runs):
    """Decode a list of (char, count) pairs back into the original string."""
    parts = []
    for char, count in runs:
        parts.append(char * (count - 1))
    return "".join(parts)
```

Return the complete, corrected file, named exactly `run_length.py`.

Respond with ONLY ```file:NAME``` fenced code blocks, one per file you change; no prose.
