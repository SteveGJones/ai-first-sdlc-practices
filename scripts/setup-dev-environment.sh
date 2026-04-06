#!/bin/bash
# setup-dev-environment.sh
#
# Symlinks the skills and agents that we SHIP (per release-mapping.yaml) into
# .claude/skills/ and .claude/agents/ so the local Claude Code session uses
# the source code we are actively editing — not a stale published version.
#
# Skills/agents we DON'T ship (e.g., superpowers, claude-code-guide) remain
# globally installed and are unaffected.
#
# Run this once after cloning the repo, and again whenever release-mapping.yaml
# changes (new shipped skills/agents added).
#
# This script is safe to re-run. It removes existing symlinks before creating
# fresh ones, but never touches non-symlink files.

set -e

FORCE=0
if [ "$1" = "--force" ]; then
    FORCE=1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_DIR="$REPO_ROOT/.claude"
MAPPING="$REPO_ROOT/release-mapping.yaml"

if [ ! -f "$MAPPING" ]; then
    echo "ERROR: release-mapping.yaml not found at $MAPPING"
    exit 1
fi

mkdir -p "$CLAUDE_DIR/skills" "$CLAUDE_DIR/agents"

# ----------------------------------------------------------------------------
# Step 1: Remove existing symlinks (safe — never touches real files)
# ----------------------------------------------------------------------------
echo "Cleaning existing symlinks..."

find "$CLAUDE_DIR/skills" -maxdepth 1 -type l -delete 2>/dev/null || true
find "$CLAUDE_DIR/agents" -maxdepth 1 -type l -delete 2>/dev/null || true

# ----------------------------------------------------------------------------
# Step 2: Symlink shipped skills
# ----------------------------------------------------------------------------
echo ""
echo "Symlinking shipped skills..."

# Extract skill directory names from release-mapping.yaml
# Lines look like:  - source: skills/validate/SKILL.md
# We want the directory: skills/validate
# Using POSIX character classes for BSD sed compatibility (macOS).
SKILL_DIRS=$(grep -E "^[[:space:]]*-[[:space:]]*source:[[:space:]]*skills/" "$MAPPING" | \
    sed -E 's|^[[:space:]]*-[[:space:]]*source:[[:space:]]*||' | \
    awk -F/ '{print $2}' | \
    sort -u)

for skill in $SKILL_DIRS; do
    SOURCE="$REPO_ROOT/skills/$skill"
    TARGET="$CLAUDE_DIR/skills/$skill"

    if [ ! -d "$SOURCE" ]; then
        echo "  WARN: skill source not found: $SOURCE"
        continue
    fi

    if [ -e "$TARGET" ] && [ ! -L "$TARGET" ]; then
        if [ "$FORCE" -eq 1 ]; then
            rm -rf "$TARGET"
            echo "  removed pre-existing: $skill"
        else
            echo "  WARN: $TARGET exists and is not a symlink — skipping (use --force to replace)"
            continue
        fi
    fi

    ln -s "$SOURCE" "$TARGET"
    echo "  linked: $skill"
done

# ----------------------------------------------------------------------------
# Step 3: Symlink shipped agents
# ----------------------------------------------------------------------------
echo ""
echo "Symlinking shipped agents..."

# Extract agent file paths from release-mapping.yaml
# Lines look like:  - source: agents/core/sdlc-enforcer.md
AGENT_PATHS=$(grep -E "^[[:space:]]*-[[:space:]]*source:[[:space:]]*agents/" "$MAPPING" | \
    sed -E 's|^[[:space:]]*-[[:space:]]*source:[[:space:]]*||' | \
    sort -u)

for agent_path in $AGENT_PATHS; do
    SOURCE="$REPO_ROOT/$agent_path"
    AGENT_NAME=$(basename "$agent_path")
    TARGET="$CLAUDE_DIR/agents/$AGENT_NAME"

    if [ ! -f "$SOURCE" ]; then
        echo "  WARN: agent source not found: $SOURCE"
        continue
    fi

    if [ -e "$TARGET" ] && [ ! -L "$TARGET" ]; then
        if [ "$FORCE" -eq 1 ]; then
            rm -f "$TARGET"
            echo "  removed pre-existing: $AGENT_NAME"
        else
            echo "  WARN: $TARGET exists and is not a symlink — skipping (use --force to replace)"
            continue
        fi
    fi

    ln -s "$SOURCE" "$TARGET"
    echo "  linked: $AGENT_NAME"
done

# ----------------------------------------------------------------------------
# Step 4: Report
# ----------------------------------------------------------------------------
echo ""
echo "=== Dev Environment Setup Complete ==="
echo ""
echo "Symlinked skills (in .claude/skills/):"
ls -1 "$CLAUDE_DIR/skills/" | sed 's/^/  /'
echo ""
echo "Symlinked agents (in .claude/agents/): $(ls -1 "$CLAUDE_DIR/agents/" | wc -l | tr -d ' ') agents"
echo ""
echo "Restart Claude Code for the new symlinks to take effect."
echo ""
echo "Note: Non-shipped skills and agents (superpowers, claude-code-guide, etc.)"
echo "remain installed globally and are unaffected by this script."
