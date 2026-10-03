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
