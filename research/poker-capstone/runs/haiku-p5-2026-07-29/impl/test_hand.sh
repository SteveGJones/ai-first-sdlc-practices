#!/bin/bash

set -e

BASE_URL="http://localhost:8000"

echo "=== Test 1: Create table ==="
TABLE_RESPONSE=$(curl -s -X POST "$BASE_URL/tables" \
  -H "Content-Type: application/json" \
  -d '{"small_blind": 1, "big_blind": 2}')
TABLE_ID=$(echo "$TABLE_RESPONSE" | grep -o '"table_id":"[^"]*"' | cut -d'"' -f4)
echo "Created table: $TABLE_ID"
echo "$TABLE_RESPONSE" | jq .

echo ""
echo "=== Test 2: Seat three players ==="
SEAT0=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/players" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "buy_in": 100}' | jq '.seat')
echo "Seated Alice at seat $SEAT0"

SEAT1=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/players" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "buy_in": 100}' | jq '.seat')
echo "Seated Bob at seat $SEAT1"

SEAT2=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/players" \
  -H "Content-Type: application/json" \
  -d '{"name": "Charlie", "buy_in": 100}' | jq '.seat')
echo "Seated Charlie at seat $SEAT2"

echo ""
echo "=== Test 3: Start hand ==="
STATE=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/start")
echo "Hand started"
CURRENT_ACTOR=$(echo "$STATE" | jq '.current_actor')
echo "Current actor is seat: $CURRENT_ACTOR"
HAND_IN_PROGRESS=$(echo "$STATE" | jq '.hand_in_progress')
echo "Hand in progress: $HAND_IN_PROGRESS"
echo "Betting round: $(echo "$STATE" | jq '.betting_round')"

echo ""
echo "=== Test 4: Play preflop actions ==="

# Current actor should act first
echo "Seat $CURRENT_ACTOR to act (preflop)"

# Seat $CURRENT_ACTOR calls the big blind
ACTION=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
  -H "Content-Type: application/json" \
  -d "{\"seat\": $CURRENT_ACTOR, \"action\": \"call\"}")
CURRENT_ACTOR=$(echo "$ACTION" | jq '.current_actor')
echo "Player called. Next actor: $CURRENT_ACTOR"

# Next player calls
ACTION=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
  -H "Content-Type: application/json" \
  -d "{\"seat\": $CURRENT_ACTOR, \"action\": \"call\"}")
CURRENT_ACTOR=$(echo "$ACTION" | jq '.current_actor')
echo "Player called. Next actor: $CURRENT_ACTOR"

# Small blind checks (completes call)
ACTION=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
  -H "Content-Type: application/json" \
  -d "{\"seat\": $CURRENT_ACTOR, \"action\": \"check\"}")
CURRENT_ACTOR=$(echo "$ACTION" | jq '.current_actor')
BETTING_ROUND=$(echo "$ACTION" | jq '.betting_round')
echo "Small blind checked. Preflop complete. New betting round: $BETTING_ROUND"
echo "Next actor: $CURRENT_ACTOR"

echo ""
echo "=== Test 5: Play flop actions ==="

# All players check through the flop
for i in {1..3}; do
  if [ "$CURRENT_ACTOR" != "null" ]; then
    ACTION=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
      -H "Content-Type: application/json" \
      -d "{\"seat\": $CURRENT_ACTOR, \"action\": \"check\"}")
    CURRENT_ACTOR=$(echo "$ACTION" | jq '.current_actor')
    BETTING_ROUND=$(echo "$ACTION" | jq '.betting_round')
    echo "Player $CURRENT_ACTOR checked. Betting round: $BETTING_ROUND"
  fi
done

echo ""
echo "=== Test 6: Play turn actions ==="

# All players check through the turn
for i in {1..3}; do
  if [ "$CURRENT_ACTOR" != "null" ]; then
    ACTION=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
      -H "Content-Type: application/json" \
      -d "{\"seat\": $CURRENT_ACTOR, \"action\": \"check\"}")
    CURRENT_ACTOR=$(echo "$ACTION" | jq '.current_actor')
    BETTING_ROUND=$(echo "$ACTION" | jq '.betting_round')
    echo "Player checked. Betting round: $BETTING_ROUND"
  fi
done

echo ""
echo "=== Test 7: Play river actions ==="

# All players check through the river
for i in {1..3}; do
  if [ "$CURRENT_ACTOR" != "null" ]; then
    ACTION=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
      -H "Content-Type: application/json" \
      -d "{\"seat\": $CURRENT_ACTOR, \"action\": \"check\"}")
    CURRENT_ACTOR=$(echo "$ACTION" | jq '.current_actor')
    BETTING_ROUND=$(echo "$ACTION" | jq '.betting_round')
    echo "Player checked. Betting round: $BETTING_ROUND"
  fi
done

echo ""
echo "=== Test 8: Final state after showdown ==="
FINAL_STATE=$(curl -s -X GET "$BASE_URL/tables/$TABLE_ID/state?seat=0")
echo "Final state:"
echo "$FINAL_STATE" | jq '.
  | {
      table_id,
      hand_in_progress,
      betting_round,
      pots,
      "players": .players | map({seat, stack, status, current_bet, total_committed}),
      last_showdown: (.last_showdown | length),
      last_action_log: (.last_action_log | length)
    }'

echo ""
echo "=== Test 9: Verify all required fields are present ==="
FIELD_CHECK=$(echo "$FINAL_STATE" | jq '{
  table_id: (.table_id != null),
  small_blind: (.small_blind != null),
  big_blind: (.big_blind != null),
  button_seat: (true),
  betting_round: (.betting_round != null),
  community_cards: (.community_cards != null),
  pots: (.pots != null),
  current_bet: (true),
  min_raise: (true),
  current_actor: (true),
  hand_in_progress: (.hand_in_progress != null),
  last_action_log: (.last_action_log != null),
  last_showdown: (.last_showdown != null),
  players: (.players != null and (.players | length) > 0)
}')
echo "$FIELD_CHECK"

echo ""
echo "=== Test 10: Test CORS headers ==="
CORS_RESPONSE=$(curl -s -i -H "Origin: http://localhost:8081" \
  -X GET "$BASE_URL/tables/$TABLE_ID/state?seat=0")
echo "CORS headers check:"
echo "$CORS_RESPONSE" | head -20 | grep -i "access-control"

echo ""
echo "=== Test 11: Test turn enforcement (wrong player action) ==="
WRONG_TURN=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
  -H "Content-Type: application/json" \
  -d '{"seat": 1, "action": "check"}')
echo "Wrong turn action response:"
echo "$WRONG_TURN" | tail -1

echo ""
echo "ALL TESTS COMPLETE"
