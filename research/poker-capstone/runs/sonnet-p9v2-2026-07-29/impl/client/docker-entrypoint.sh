#!/bin/sh
# Regenerates env.js from the API_BASE env var (if set) at container start,
# so the client image doesn't need to be rebuilt to point at a different
# server host:port. See src/api.ts (getApiBase) for the resolution order.
set -eu

ENV_JS=/usr/share/nginx/html/env.js

if [ -n "${API_BASE:-}" ]; then
  printf 'window.__POKER_API_BASE__ = "%s";\n' "$API_BASE" > "$ENV_JS"
else
  printf 'window.__POKER_API_BASE__ = undefined;\n' > "$ENV_JS"
fi

exec nginx -g 'daemon off;'
