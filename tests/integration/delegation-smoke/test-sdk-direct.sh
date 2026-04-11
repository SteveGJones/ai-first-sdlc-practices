#!/bin/bash
# Test: Force x86_64 platform to avoid Bun ARM64 segfault.
# Bun 1.3.11 on Linux ARM64 crashes with SIGSEGV when Claude Agent SDK
# spawns a subprocess. x86_64 under Rosetta may work.
set -e

echo "=== Test: Archon on x86_64 (Rosetta emulation) ==="
echo "Building x86_64 image..."
cd "$(dirname "$0")/../../plugins/sdlc-workflows/docker"
docker build --platform linux/amd64 -t sdlc-worker:amd64 . 2>&1 | tail -5

echo ""
echo "Running Archon chat test..."
docker run --rm \
    --platform linux/amd64 \
    -v sdlc-smoke-claude-creds:/home/sdlc/.claude \
    --entrypoint /bin/bash \
    sdlc-worker:amd64 \
    -c '
        BACKUP=$(ls -t /home/sdlc/.claude/backups/.claude.json.backup.* 2>/dev/null | head -1)
        [ -n "$BACKUP" ] && cp "$BACKUP" /home/sdlc/.claude.json && echo "Restored .claude.json"

        cd /tmp && git init -q testdir && cd testdir
        git config user.email "t@t.com"
        git config user.name "T"
        git commit -q --allow-empty -m "init"

        echo "Starting Archon (x86_64)..."
        timeout 90 archon chat "Say exactly ARCHON_OK and nothing else" --no-worktree 2>&1 | tail -15
        echo "EXIT: $?"
    '

echo "=== Test Complete ==="
