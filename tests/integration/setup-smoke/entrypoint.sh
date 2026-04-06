#!/bin/bash
set -e

echo "=== SDLC Setup Smoke Test ==="
echo ""

# Step 1: Copy auth from read-only mounts to writable locations
if [ -d /host-claude ]; then
    echo "Copying Claude credentials from host..."
    cp -r /host-claude /root/.claude
else
    echo "WARNING: /host-claude not mounted. Auth may fail."
    mkdir -p /root/.claude
fi

if [ -f /host-claude.json ]; then
    cp /host-claude.json /root/.claude.json
else
    echo "WARNING: /host-claude.json not mounted. OAuth session may be missing."
fi

# Step 2: Ensure no API key set (use Max subscription)
unset ANTHROPIC_API_KEY

# Step 3: Verify Claude Code is available
echo "Claude Code version: $(claude --version 2>/dev/null || echo 'NOT FOUND')"
echo "Ralph version: $(ralph --version 2>/dev/null || echo 'NOT FOUND')"
echo "Python version: $(python --version 2>/dev/null || echo 'NOT FOUND')"
echo ""

# Step 4: Initialize git repo (Ralph needs a git repo)
if [ ! -d .git ]; then
    git init
    git config user.email "smoke-test@example.com"
    git config user.name "Smoke Test"
    git add -A
    git commit -m "initial" --allow-empty
fi

# Step 5: Run the smoke test via Ralph
echo "Starting Ralph loop..."
ralph run

echo ""
echo "=== Smoke Test Complete ==="

# Step 6: Report results
if [ -f .sdlc/team-config.json ]; then
    echo "PASS: .sdlc/team-config.json exists"
    echo "Contents:"
    cat .sdlc/team-config.json | python -m json.tool
else
    echo "FAIL: .sdlc/team-config.json not found"
    exit 1
fi

echo ""

if [ -f .sdlc/recommended-plugins.json ]; then
    echo "PASS: .sdlc/recommended-plugins.json exists"
    echo "Plugins found: $(python -c "import json; d=json.load(open('.sdlc/recommended-plugins.json')); print(len(d.get('plugins',[])))")"
else
    echo "FAIL: .sdlc/recommended-plugins.json not found"
    exit 1
fi
