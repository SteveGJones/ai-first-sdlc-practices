#!/bin/bash
# Test: Archon with SDK subprocess forced to Node.js (not Bun).
# Archon runs on Bun, but the Claude Agent SDK subprocess uses Node.js
# to avoid the Bun ARM64 segfault (oven-sh/bun#26979).
set -e

echo "=== Test: Archon chat (Bun + Node.js subprocess) ==="
docker run --rm \
    -v sdlc-smoke-claude-creds:/home/sdlc/.claude \
    --entrypoint /bin/bash \
    sdlc-worker:latest \
    -c '
        BACKUP=$(ls -t /home/sdlc/.claude/backups/.claude.json.backup.* 2>/dev/null | head -1)
        [ -n "$BACKUP" ] && cp "$BACKUP" /home/sdlc/.claude.json && echo "Restored .claude.json"

        cd /tmp
        git init -q testdir && cd testdir
        git config user.email "t@t.com"
        git config user.name "T"
        git commit -q --allow-empty -m "init"

        echo "Bun: $(bun --version), Node: $(node --version)"
        echo "Patch check: $(grep -c "executable.*node" /opt/archon/packages/core/src/clients/claude.ts) occurrence(s)"
        echo ""
        echo "Starting Archon chat..."
        timeout 90 archon chat "Say exactly ARCHON_OK and nothing else" --no-worktree 2>&1
        EXIT=$?
        echo ""
        echo "EXIT: $EXIT"
        [ $EXIT -eq 0 ] && echo "RESULT: SUCCESS" || echo "RESULT: FAILED (exit $EXIT)"
    '
