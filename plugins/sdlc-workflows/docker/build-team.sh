#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -z "$1" ]; then
    echo "Usage: build-team.sh <team-name> [--image <tag>]"
    echo ""
    echo "Builds a team Docker image from .archon/teams/<team-name>.yaml"
    echo ""
    echo "Prerequisites:"
    echo "  - sdlc-worker:base and sdlc-worker:full images must exist"
    echo "  - Team CLAUDE.md must be pre-generated in .archon/teams/.generated/"
    exit 1
fi

TEAM_NAME="$1"
IMAGE_TAG="sdlc-worker:$TEAM_NAME"
if [ "$2" = "--image" ] && [ -n "$3" ]; then
    IMAGE_TAG="$3"
fi
MANIFEST=".archon/teams/${TEAM_NAME}.yaml"
GENERATED_DIR=".archon/teams/.generated"
PLUGINS_JSON="${CLAUDE_PLUGINS_DIR:-$HOME/.claude/plugins}/installed_plugins.json"

if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: Team manifest not found: $MANIFEST"
    exit 1
fi

# Ensure base and full images exist
for img in sdlc-worker:base sdlc-worker:full; do
    if ! docker image inspect "$img" >/dev/null 2>&1; then
        echo "ERROR: Required image $img not found."
        echo "Run: bash $SCRIPT_DIR/build-base.sh && bash $SCRIPT_DIR/build-full.sh"
        exit 1
    fi
done

mkdir -p "$GENERATED_DIR"

# Generate team CLAUDE.md from manifest
echo "Generating team CLAUDE.md for $TEAM_NAME..."
python3 "$PLUGIN_DIR/scripts/generate_team_claude_md.py" \
    "$MANIFEST" \
    --output "$GENERATED_DIR/${TEAM_NAME}-CLAUDE.md"

echo "Generating team Dockerfile for $TEAM_NAME..."
python3 "$PLUGIN_DIR/scripts/generate_team_dockerfile.py" \
    "$MANIFEST" \
    --installed-plugins "$PLUGINS_JSON" \
    --team-claude-md "$GENERATED_DIR/${TEAM_NAME}-CLAUDE.md" \
    --output "$GENERATED_DIR/${TEAM_NAME}.Dockerfile"

echo "Building $IMAGE_TAG..."
docker build -t "$IMAGE_TAG" \
    -f "$GENERATED_DIR/${TEAM_NAME}.Dockerfile" \
    .

echo ""
echo "Done. Image: $IMAGE_TAG"
