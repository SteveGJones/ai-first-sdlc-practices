#!/usr/bin/env bash
# Lint the stage-4 instruction artifacts (commands, agents, the council-policy
# skill): valid frontmatter, required keys, the orchestration-policy →
# council-policy reframe is complete, and every ${CLAUDE_PLUGIN_ROOT}/… path a
# command or agent references actually exists on disk. Cheap guard against
# broken references before the repo-wide check-broken-references.py at stage 7.
#
# Run: bash plugins/sdlc-model-council/tests/test-council-artifacts.sh
set -u

THIS_DIR="$(cd "$(dirname "$0")" && pwd -P)"
PLUGIN_ROOT="$(cd "$THIS_DIR/.." && pwd -P)"
cd "$PLUGIN_ROOT" || exit 1

PASS=0; FAIL=0
pass() { PASS=$((PASS + 1)); printf 'PASS: %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf 'FAIL: %s\n' "$1"; }

has_frontmatter() { [ "$(head -1 "$1")" = "---" ]; }
fm_key() { awk 'NR==1&&$0=="---"{f=1;next} f&&$0=="---"{exit} f&&$0~("^"k":")' k="$2" "$1" | head -1; }

# --- commands: frontmatter + description --------------------------------------
for f in commands/*.md; do
  [ -f "$f" ] || continue
  if has_frontmatter "$f"; then pass "frontmatter: $f"; else fail "frontmatter: $f"; fi
  if [ -n "$(fm_key "$f" description)" ]; then pass "description: $f"; else fail "description: $f"; fi
done

# --- agents: frontmatter + name + model ---------------------------------------
for f in agents/*.md; do
  [ -f "$f" ] || continue
  if has_frontmatter "$f"; then pass "frontmatter: $f"; else fail "frontmatter: $f"; fi
  if [ -n "$(fm_key "$f" name)" ]; then pass "name: $f"; else fail "name: $f"; fi
  if [ -n "$(fm_key "$f" model)" ]; then pass "model: $f"; else fail "model: $f"; fi
done

# --- the council-policy skill exists and is renamed ---------------------------
if [ -f "skills/council-policy/SKILL.md" ]; then
  pass "council-policy skill exists"
else
  fail "council-policy skill exists (skills/council-policy/SKILL.md)"
fi
if [ ! -d "skills/orchestration-policy" ]; then
  pass "old orchestration-policy skill dir removed"
else
  fail "old orchestration-policy skill dir removed"
fi
NAME_LINE="$(fm_key skills/council-policy/SKILL.md name 2>/dev/null)"
case "$NAME_LINE" in
  *council-policy*) pass "skill frontmatter name is council-policy" ;;
  *) fail "skill frontmatter name is council-policy (got: $NAME_LINE)" ;;
esac

# --- no stale orchestration-policy references anywhere in the plugin ----------
STALE="$(grep -rl 'orchestration-policy' . --include='*.md' 2>/dev/null | grep -v '/tmp/' || true)"
if [ -z "$STALE" ]; then
  pass "no stale 'orchestration-policy' references remain"
else
  fail "stale 'orchestration-policy' references in: $STALE"
fi

# --- every ${CLAUDE_PLUGIN_ROOT}/… reference in commands/agents resolves ------
# Extract paths, strip trailing markdown/quote punctuation, check existence.
MISSING=0
REFS="$(grep -rhoE '\$\{CLAUDE_PLUGIN_ROOT\}/[A-Za-z0-9._/-]+' commands agents 2>/dev/null \
  | sed -E 's#\$\{CLAUDE_PLUGIN_ROOT\}/##' | sort -u)"
for rel in $REFS; do
  rel="${rel%.}"     # strip a trailing dot from prose
  if [ -e "$PLUGIN_ROOT/$rel" ]; then
    :
  else
    fail "referenced path missing: \${CLAUDE_PLUGIN_ROOT}/$rel"
    MISSING=$((MISSING + 1))
  fi
done
[ "$MISSING" -eq 0 ] && pass "all \${CLAUDE_PLUGIN_ROOT} script references resolve"

# --- the 5 council commands exist --------------------------------------------
for c in council-commission council-assess council-roster council-run council-estimate; do
  if [ -f "commands/$c.md" ]; then pass "command present: $c"; else fail "command present: $c"; fi
done

echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
