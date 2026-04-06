FROM node:22-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv git curl ca-certificates xz-utils && \
    rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/bin/python3 /usr/bin/python

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Install Ralph orchestrator
RUN npm install -g @ralph-orchestrator/ralph-cli

# Copy entrypoint script (as root, before USER switch)
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

# Create a non-root user for runtime.
# Claude Code's --dangerously-skip-permissions (used by ralph-orchestrator)
# refuses to run as root for security reasons.
# UID 1001 because node:22-slim already has a 'node' user at UID 1000.
RUN useradd -m -s /bin/bash -u 1001 sdlc && \
    mkdir -p /workspace /home/sdlc/.claude && \
    chown -R sdlc:sdlc /workspace /home/sdlc/.claude

USER sdlc
WORKDIR /workspace

ENTRYPOINT ["/opt/entrypoint.sh"]
