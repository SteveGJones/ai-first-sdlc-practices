FROM node:22-slim

# System dependencies (matching tests/integration/setup-smoke/Dockerfile)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv git curl ca-certificates xz-utils && \
    rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/bin/python3 /usr/bin/python

# Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Archon CLI
RUN curl -fsSL https://archon.diy/install | bash && \
    mv /root/.archon/bin/archon /usr/local/bin/archon || true

# Ralph orchestrator (used by smoke tests and autonomous loops)
RUN npm install -g @ralph-orchestrator/ralph-cli

# Build-time plugin installation (optional, for production images)
ARG INSTALL_PLUGINS_AT_BUILD=false

# Non-root user (UID 1001, matching smoke test convention — node:22-slim
# already has a 'node' user at UID 1000)
RUN useradd -m -s /bin/bash -u 1001 sdlc && \
    mkdir -p /workspace /home/sdlc/.claude /home/sdlc/.archon && \
    chown -R sdlc:sdlc /workspace /home/sdlc/.claude /home/sdlc/.archon

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
