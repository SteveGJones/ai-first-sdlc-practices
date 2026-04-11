FROM sdlc-worker:latest

# Copy smoke test fixtures and Archon configs
USER root
COPY fixtures/miniproject/ /workspace/
COPY workflows/ /home/sdlc/.archon/workflows/
COPY commands/ /home/sdlc/.archon/commands/
COPY PROMPT.md /workspace/PROMPT.md
COPY ralph.yml /workspace/ralph.yml
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh && \
    chown -R sdlc:sdlc /workspace /home/sdlc/.archon
USER sdlc
WORKDIR /workspace

ENTRYPOINT ["/opt/entrypoint.sh"]
