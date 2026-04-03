#!/bin/bash
# SDLC Core — Session Start Banner
# Displays installed team plugins and formation status

TEAM_CONFIG=".claude/team-config.json"

echo "--- AI-First SDLC ---"

# Show core version
CORE_VERSION=$(python3 -c "
import json, os
p = os.path.join(os.environ.get('CLAUDE_PLUGIN_ROOT', '.'), '.claude-plugin', 'plugin.json')
if os.path.exists(p):
    print(json.load(open(p))['version'])
else:
    print('unknown')
" 2>/dev/null || echo "unknown")
echo "sdlc-core v${CORE_VERSION}"

# Show team formation if configured
if [ -f "$TEAM_CONFIG" ]; then
    FORMATION=$(python3 -c "import json; print(json.load(open('$TEAM_CONFIG')).get('formation', 'none'))" 2>/dev/null)
    PROJECT_TYPE=$(python3 -c "import json; print(json.load(open('$TEAM_CONFIG')).get('project_type', 'unknown'))" 2>/dev/null)
    echo "Formation: ${FORMATION} (${PROJECT_TYPE})"
else
    echo "No team configured. Run /sdlc-core:setup-team to set up."
fi

echo "---"
