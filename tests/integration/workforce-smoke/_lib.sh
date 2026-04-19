#!/bin/bash
# Shared helpers for workforce-smoke integration harnesses.
#
# These functions centralise the backup/restore of the repo's .archon/
# teams + agents directories so individual run-*.sh scripts don't
# duplicate ~15 lines of bookkeeping each.
#
# Usage (from run-acceptance.sh / run-e2e.sh):
#
#     # shellcheck disable=SC1091
#     source "$(dirname "$0")/_lib.sh"
#
#     archon_backup_setup "e2e"          # prefix is used in mktemp names
#     trap archon_backup_cleanup EXIT
#
#     # ... drop miniproject manifests/agents into $TEAMS_DIR / $AGENTS_DIR ...
#     # ... run the test body ...
#
# Exported after archon_backup_setup:
#   TEAMS_DIR      — absolute path to $REPO_ROOT/.archon/teams
#   AGENTS_DIR     — absolute path to $REPO_ROOT/.archon/agents
#   BACKUP_DIR     — tempdir holding copies of pre-existing files
#
# archon_backup_cleanup:
#   1. Removes miniproject artefacts from TEAMS_DIR and AGENTS_DIR
#   2. Restores anything that was backed up
#   3. Wipes BACKUP_DIR
#
# Callers are responsible for extra cleanup (docker rmi, mktemp -d workspaces,
# etc.) in their own trap handlers — chain them with archon_backup_cleanup.

# Require REPO_ROOT to be set by the caller.
if [ -z "${REPO_ROOT:-}" ]; then
    echo "_lib.sh: REPO_ROOT must be set before sourcing" >&2
    return 1 2>/dev/null || exit 1
fi

archon_backup_setup() {
    local prefix="${1:-archon-smoke}"
    TEAMS_DIR="$REPO_ROOT/.archon/teams"
    AGENTS_DIR="$REPO_ROOT/.archon/agents"
    BACKUP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/${prefix}-backup.XXXXXX")
    mkdir -p "$TEAMS_DIR" "$AGENTS_DIR" "$BACKUP_DIR/teams" "$BACKUP_DIR/agents"
    if ls "$TEAMS_DIR"/*.yaml >/dev/null 2>&1; then
        cp "$TEAMS_DIR"/*.yaml "$BACKUP_DIR/teams/" 2>/dev/null || true
    fi
    if ls "$AGENTS_DIR"/*.md >/dev/null 2>&1; then
        cp "$AGENTS_DIR"/*.md "$BACKUP_DIR/agents/" 2>/dev/null || true
    fi
    export TEAMS_DIR AGENTS_DIR BACKUP_DIR
}

archon_backup_cleanup() {
    # Safe to call even if setup never ran.
    [ -z "${TEAMS_DIR:-}" ] && return 0
    [ -z "${BACKUP_DIR:-}" ] && return 0

    # Drop the miniproject artefacts by name — the backup restore below
    # puts the originals back if they existed.  Callers can override the
    # default team/agent lists by exporting ARCHON_SMOKE_TEAMS /
    # ARCHON_SMOKE_AGENTS before sourcing (space-separated names).  The
    # defaults match the original run-e2e.sh / run-acceptance.sh teams
    # so existing harnesses keep working without modification.
    local teams="${ARCHON_SMOKE_TEAMS:-dev-team review-team}"
    local agents="${ARCHON_SMOKE_AGENTS:-project-context}"
    local team_name agent_name
    for team_name in $teams; do
        rm -f "$TEAMS_DIR/${team_name}.yaml"
        rm -rf "$TEAMS_DIR/.generated/${team_name}"*
    done
    for agent_name in $agents; do
        rm -f "$AGENTS_DIR/${agent_name}.md"
    done

    if ls "$BACKUP_DIR/teams/"*.yaml >/dev/null 2>&1; then
        cp "$BACKUP_DIR/teams/"*.yaml "$TEAMS_DIR/" 2>/dev/null || true
    fi
    if ls "$BACKUP_DIR/agents/"*.md >/dev/null 2>&1; then
        cp "$BACKUP_DIR/agents/"*.md "$AGENTS_DIR/" 2>/dev/null || true
    fi
    rm -rf "$BACKUP_DIR"
}
