#!/bin/bash

BASE_URL="http://localhost:8000"

echo "=== Complex Hand Test: With Raises and Folds ==="

# Create table
TABLE_ID=$(curl -s -X POST "$BASE_URL/tables" \
  -H "Content-Type: application/json" \
  -d '{"small_blind": 1, "big_blind": 2}' | jq -r '.table_id')

echo "Table: $TABLE_ID"

# Seat 3 players with 50 chips each
curl -s -X POST "$BASE_URL/tables/$TABLE_ID/players" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "buy_in": 50}' > /dev/null

curl -s -X POST "$BASE_URL/tables/$TABLE_ID/players" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "buy_in": 50}' > /dev/null

curl -s -X POST "$BASE_URL/tables/$TABLE_ID/players" \
  -H "Content-Type: application/json" \
  -d '{"name": "Charlie", "buy_in": 50}' > /dev/null

# Start hand
STATE=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/start")
ACTOR=$(echo "$STATE" | jq '.current_actor')
echo "Hand started. UTG (current_actor): $ACTOR"

# Preflop: UTG raises to 6
echo ""
echo "UTG (seat $ACTOR) raises to 6"
STATE=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
  -H "Content-Type: application/json" \
  -d "{\"seat\": $ACTOR, \"action\": \"raise\", \"amount\": 6}")
ACTOR=$(echo "$STATE" | jq '.current_actor')
echo "Current bet: $(echo "$STATE" | jq '.current_bet')"
echo "Next actor: $ACTOR"

# Next player folds
echo ""
echo "Seat $ACTOR folds"
STATE=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
  -H "Content-Type: application/json" \
  -d "{\"seat\": $ACTOR, \"action\": \"fold\"}")
ACTOR=$(echo "$STATE" | jq '.current_actor')
echo "Next actor: $ACTOR"

# BB calls the raise
echo ""
echo "Seat $ACTOR calls"
STATE=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
  -H "Content-Type: application/json" \
  -d "{\"seat\": $ACTOR, \"action\": \"call\"}")
ACTOR=$(echo "$STATE" | jq '.current_actor')
BETTING_ROUND=$(echo "$STATE" | jq '.betting_round')
echo "Betting round: $BETTING_ROUND"
echo "Next actor: $ACTOR"

# Flop: UTG checks
if [ "$BETTING_ROUND" = "\"flop\"" ]; then
  echo ""
  echo "Flop dealt"
  COMMUNITY=$(echo "$STATE" | jq '.community_cards | length')
  echo "Community cards: $COMMUNITY"

  echo ""
  echo "Seat $ACTOR checks"
  STATE=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
    -H "Content-Type: application/json" \
    -d "{\"seat\": $ACTOR, \"action\": \"check\"}")
  ACTOR=$(echo "$STATE" | jq '.current_actor')

  echo "Seat $ACTOR checks"
  STATE=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
    -H "Content-Type: application/json" \
    -d "{\"seat\": $ACTOR, \"action\": \"check\"}")
  ACTOR=$(echo "$STATE" | jq '.current_actor')
  BETTING_ROUND=$(echo "$STATE" | jq '.betting_round')
  echo "Betting round: $BETTING_ROUND"
fi

echo ""
echo "=== Final State Summary ==="
FINAL=$(curl -s "$BASE_URL/tables/$TABLE_ID/state?seat=0")

echo "Hand in progress: $(echo "$FINAL" | jq '.hand_in_progress')"
echo "Betting round: $(echo "$FINAL" | jq '.betting_round')"
echo ""
echo "Pots:"
echo "$FINAL" | jq '.pots[] | {amount, eligible_seats}'
echo ""
echo "Player stacks:"
echo "$FINAL" | jq '.players[] | {seat, stack, status, total_committed}'
echo ""
echo "Total chips in play: $(echo "$FINAL" | jq '.players | map(.stack) | add')"

# Verify all required fields present
FIELDS=$(echo "$FINAL" | jq 'keys | sort | @csv')
echo ""
echo "Response fields: $FIELDS"
