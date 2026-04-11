FROM oven/bun:1.3.11-slim AS archon-deps

# Install Archon from source (not the compiled binary).
# The compiled Bun binary has a $bunfs extraction issue that prevents
# the Claude Agent SDK from spawning child processes as a non-root user.
# Running from source with bun matches Archon's own Docker setup.
WORKDIR /opt/archon
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 https://github.com/coleam00/Archon.git . && \
    bun install --frozen-lockfile --linker=hoisted

# ---------------------------------------------------------------------------
FROM node:22-slim

# System dependencies (matching tests/integration/setup-smoke/Dockerfile)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv git curl ca-certificates xz-utils && \
    rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/bin/python3 /usr/bin/python

# Install Bun runtime (needed to run Archon from source)
RUN curl -fsSL https://bun.sh/install | bash && \
    ln -sf /root/.bun/bin/bun /usr/local/bin/bun && \
    ln -sf /root/.bun/bin/bunx /usr/local/bin/bunx

# Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Copy Archon from source build stage
COPY --from=archon-deps /opt/archon /opt/archon

# Create archon wrapper script that runs from source
RUN printf '#!/bin/bash\nexec bun run /opt/archon/packages/cli/src/index.ts "$@"\n' > /usr/local/bin/archon && \
    chmod +x /usr/local/bin/archon

# Ralph orchestrator (used by smoke tests and autonomous loops)
RUN npm install -g @ralph-orchestrator/ralph-cli

# Build-time plugin installation (optional, for production images)
ARG INSTALL_PLUGINS_AT_BUILD=false

# Non-root user (UID 1001, matching smoke test convention — node:22-slim
# already has a 'node' user at UID 1000)
RUN useradd -m -s /bin/bash -u 1001 sdlc && \
    mkdir -p /workspace /home/sdlc/.claude /home/sdlc/.archon && \
    chown -R sdlc:sdlc /workspace /home/sdlc/.claude /home/sdlc/.archon /opt/archon

# Copy entrypoint (as root, before USER switch)
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

# If build-time plugin install is enabled, install as sdlc user
# This bakes plugins into the image for faster startup
RUN if [ "$INSTALL_PLUGINS_AT_BUILD" = "true" ]; then \
      su - sdlc -c "claude --bare -p 'run: /plugin marketplace add SteveGJones/ai-first-sdlc-practices && /plugin install sdlc-core@ai-first-sdlc'" || true; \
    fi

USER sdlc
WORKDIR /workspace

ENTRYPOINT ["/opt/entrypoint.sh"]
