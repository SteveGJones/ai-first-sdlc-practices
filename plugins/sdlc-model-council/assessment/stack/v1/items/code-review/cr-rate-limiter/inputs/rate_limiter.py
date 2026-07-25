"""Simple in-memory rate limiter keyed by an arbitrary string."""

import time


class RateLimiter:
    """Allow at most `limit` calls per `window` seconds per key."""

    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.calls = {}

    def allow(self, key):
        """Return True if the call for `key` should be allowed right now."""
        now = time.time()
        history = self.calls.get(key, [])
        history = [t for t in history if now - t < self.window]
        if len(history) < self.limit:
            history.append(now)
            self.calls[key] = history
            return True
        self.calls[key] = history
        return False

    def reset(self, key):
        """Forget all recorded calls for a key, so it starts fresh."""
        del self.calls[key]

    def prune(self):
        """Drop empty per-key histories to bound memory growth over time."""
        for key in self.calls:
            if not self.calls[key]:
                del self.calls[key]


def retry_after_seconds(limiter, key):
    """Seconds until the next call for `key` is allowed again."""
    history = limiter.calls.get(key, [])
    oldest = min(history)
    return max(0, limiter.window - (time.time() - oldest))
