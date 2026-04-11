#!/bin/bash
# Diagnostic test: Can Archon's SDK spawn a Claude session inside Docker?
# Tests with .claude.json restored from backup (the SDK may need it).
set -e

echo "=== Test: Archon chat with .claude.json restored ==="
docker run --rm \
    -v sdlc-smoke-claude-creds:/home/sdlc/.claude \
    --entrypoint /bin/bash \
    sdlc-worker:latest \
    -c '
        # Restore .claude.json from backup if missing
        if [ ! -f /home/sdlc/.claude.json ]; then
            BACKUP=$(ls -t /home/sdlc/.claude/backups/.claude.json.backup.* 2>/dev/null | head -1)
            if [ -n "$BACKUP" ]; then
                cp "$BACKUP" /home/sdlc/.claude.json
                echo "Restored .claude.json from backup: $BACKUP"
            else
                echo "WARNING: No .claude.json and no backup found"
            fi
        fi

        cd /tmp
        git init -q testdir && cd testdir
        git config user.email "t@t.com"
        git config user.name "T"
        git commit -q --allow-empty -m "init"

        echo "Starting Archon chat..."
        timeout 90 archon chat "Say exactly ARCHON_OK and nothing else" --no-worktree 2>&1 | tail -10
        echo "EXIT: $?"
    '

echo "=== Test Complete ==="
