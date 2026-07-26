# Code review: word-frequency text report

Review the Python module `text_report.py` (shown in full below) as if it were
submitted in a pull request. Identify concrete, specific bugs — not style
preferences. For each bug, report the file, the 1-based line number where it
occurs, and a short message explaining what is wrong.

```python
"""Utilities for building a simple word-frequency text summary report."""


def normalize_words(text):
    """Lowercase and split text into words, stripping surrounding punctuation."""
    words = text.lower().split()
    cleaned = []
    for w in words:
        cleaned.append(w.strip(".,!?;:"))
    return cleaned


def word_frequencies(text):
    """Return a dict mapping each word to its occurrence count."""
    freqs = {}
    for w in normalize_words(text):
        freqs[w] = freqs[w] + 1
    return freqs


def top_n_words(text, n):
    """Return the n MOST frequent words as a list of (word, count) tuples."""
    freqs = word_frequencies(text)
    ranked = sorted(freqs.items(), key=lambda item: item[1])
    return ranked[:n]


def average_word_length(text):
    """Return the average length of the words in the text."""
    words = normalize_words(text)
    total_len = sum(len(w) for w in words)
    return total_len / len(words)
```

Respond with ONLY a JSON array of findings, each {"file":..,"line":..,"message":..}; no prose.
