#!/bin/bash

BASE_URL="http://localhost:8000"

echo "=== Test: Wrong turn rejection with state preservation ==="

# Create table
TABLE_ID=$(curl -s -X POST "$BASE_URL/tables" \
  -H "Content-Type: application/json" \
  -d '{"small_blind": 1, "big_blind": 2}' | jq -r '.table_id')

# Seat players
curl -s -X POST "$BASE_URL/tables/$TABLE_ID/players" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "buy_in": 100}' > /dev/null

curl -s -X POST "$BASE_URL/tables/$TABLE_ID/players" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "buy_in": 100}' > /dev/null

# Start hand
curl -s -X POST "$BASE_URL/tables/$TABLE_ID/start" > /dev/null

# Get state before
BEFORE=$(curl -s "$BASE_URL/tables/$TABLE_ID/state?seat=0")
ACTOR_BEFORE=$(echo "$BEFORE" | jq '.current_actor')
STACKS_BEFORE=$(echo "$BEFORE" | jq '.players | map(.stack) | @csv')

echo "Before wrong action:"
echo "  Current actor: $ACTOR_BEFORE"
echo "  Stacks: $STACKS_BEFORE"

# Try wrong player action
echo ""
echo "Attempting action from wrong player (seat 1, but should be seat $ACTOR_BEFORE)..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
  -H "Content-Type: application/json" \
  -d '{"seat": 1, "action": "check"}')
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
ERROR_DETAIL=$(echo "$RESPONSE" | head -1 | jq '.detail // .error // "no error message"')

echo "Response status: $HTTP_CODE"
echo "Error: $ERROR_DETAIL"

# Get state after
AFTER=$(curl -s "$BASE_URL/tables/$TABLE_ID/state?seat=0")
ACTOR_AFTER=$(echo "$AFTER" | jq '.current_actor')
STACKS_AFTER=$(echo "$AFTER" | jq '.players | map(.stack) | @csv')

echo ""
echo "After wrong action (should be unchanged):"
echo "  Current actor: $ACTOR_AFTER"
echo "  Stacks: $STACKS_AFTER"

if [ "$ACTOR_BEFORE" = "$ACTOR_AFTER" ] && [ "$STACKS_BEFORE" = "$STACKS_AFTER" ]; then
  echo ""
  echo "✓ PASS: State correctly preserved on rejected action"
else
  echo ""
  echo "✗ FAIL: State was modified on rejected action!"
fi
