// Placeholder for local `vite dev`/`vite preview` runs. The Docker image
// overwrites this file at container start (see docker-entrypoint.sh) with
// the API_BASE env var, if set, so the browser can be pointed at whatever
// host:port the server container is actually published on without
// rebuilding the client image. Leaving this unset falls back to
// src/api.ts's same-origin-port-8000 default.
window.__POKER_API_BASE__ = undefined;
