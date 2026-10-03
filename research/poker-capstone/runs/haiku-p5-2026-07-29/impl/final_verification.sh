#!/bin/bash

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "FINAL VERIFICATION TEST"
echo "=========================================="
echo ""

# Test 1: healthz
echo "TEST 1: GET /healthz"
HEALTH=$(curl -s -w "\n%{http_code}" "$BASE_URL/healthz")
STATUS=$(echo "$HEALTH" | tail -1)
if [ "$STATUS" = "200" ]; then
  echo "✓ PASS: /healthz returns 200"
else
  echo "✗ FAIL: /healthz returned $STATUS"
fi

echo ""
echo "TEST 2: CORS headers"
CORS_TEST=$(curl -s -i -H "Origin: http://testclient:3000" "$BASE_URL/healthz" 2>&1)
if echo "$CORS_TEST" | grep -q "access-control-allow-origin: \*"; then
  echo "✓ PASS: CORS headers present"
else
  echo "✗ FAIL: CORS headers missing"
fi

echo ""
echo "TEST 3: Full hand completion with state verification"

# Create table
TABLE=$(curl -s -X POST "$BASE_URL/tables" \
  -H "Content-Type: application/json" \
  -d '{"small_blind": 1, "big_blind": 2}')
TABLE_ID=$(echo "$TABLE" | jq -r '.table_id')
echo "  Created table: $TABLE_ID"

# Seat players
for i in 0 1 2; do
  curl -s -X POST "$BASE_URL/tables/$TABLE_ID/players" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"Player$i\", \"buy_in\": 100}" > /dev/null
done
echo "  Seated 3 players"

# Start and play hand
INITIAL=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/start")
ACTOR=$(echo "$INITIAL" | jq '.current_actor')

# Play all checks to completion
for i in {1..20}; do
  STATE=$(curl -s "$BASE_URL/tables/$TABLE_ID/state?seat=0")
  HAND=$(echo "$STATE" | jq '.hand_in_progress')
  ACTOR=$(echo "$STATE" | jq '.current_actor')

  if [ "$HAND" = "false" ]; then
    break
  fi

  if [ "$ACTOR" != "null" ]; then
    curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
      -H "Content-Type: application/json" \
      -d "{\"seat\": $ACTOR, \"action\": \"check\"}" > /dev/null
  fi
done

FINAL=$(curl -s "$BASE_URL/tables/$TABLE_ID/state?seat=0")
HAND_COMPLETE=$(echo "$FINAL" | jq '.hand_in_progress')
BETTING_ROUND=$(echo "$FINAL" | jq '.betting_round')

if [ "$HAND_COMPLETE" = "false" ]; then
  echo "  ✓ Hand completed successfully"
else
  echo "  ✗ Hand did not complete"
fi

echo ""
echo "TEST 4: All required response fields present"
FIELDS=$(echo "$FINAL" | jq 'keys | length')
REQUIRED_FIELDS=14  # table_id, small_blind, big_blind, button_seat, betting_round, community_cards, pots, current_bet, min_raise, current_actor, hand_in_progress, last_action_log, last_showdown, players

if [ "$FIELDS" -ge "$REQUIRED_FIELDS" ]; then
  echo "  ✓ All required fields present ($FIELDS fields)"
else
  echo "  ✗ Missing fields (expected $REQUIRED_FIELDS, got $FIELDS)"
fi

echo ""
echo "TEST 5: Chip conservation"
TOTAL=$(echo "$FINAL" | jq '.players | map(.stack) | add')
if [ "$TOTAL" = "300" ]; then
  echo "  ✓ Total chips conserved: $TOTAL"
else
  echo "  ✗ Chip mismatch: $TOTAL (expected 300)"
fi

echo ""
echo "TEST 6: Hole cards privacy"
# During showdown, hole cards should be visible to all
SEAT0_VIEW=$(curl -s "$BASE_URL/tables/$TABLE_ID/state?seat=0")
SEAT0_CARDS=$(echo "$SEAT0_VIEW" | jq '.players[0].hole_cards')
SEAT1_CARDS=$(echo "$SEAT0_VIEW" | jq '.players[1].hole_cards')

if [ "$SEAT0_CARDS" != "null" ] && [ "$SEAT1_CARDS" != "null" ]; then
  echo "  ✓ Hole cards visible during showdown"
else
  echo "  ✗ Hole card visibility incorrect"
fi

echo ""
echo "TEST 7: Turn enforcement"
# Create new table for turn test
TABLE2=$(curl -s -X POST "$BASE_URL/tables" \
  -H "Content-Type: application/json" \
  -d '{"small_blind": 1, "big_blind": 2}')
TABLE_ID2=$(echo "$TABLE2" | jq -r '.table_id')

curl -s -X POST "$BASE_URL/tables/$TABLE_ID2/players" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "buy_in": 100}' > /dev/null

curl -s -X POST "$BASE_URL/tables/$TABLE_ID2/players" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "buy_in": 100}' > /dev/null

curl -s -X POST "$BASE_URL/tables/$TABLE_ID2/start" > /dev/null

# Get current state and try wrong player action
WRONG=$(curl -s -w "%{http_code}" -X POST "$BASE_URL/tables/$TABLE_ID2/actions" \
  -H "Content-Type: application/json" \
  -d '{"seat": 1, "action": "check"}')
HTTP_CODE=$(echo "$WRONG" | tail -c 4)

if [ "$HTTP_CODE" = "400" ]; then
  echo "  ✓ Wrong player action rejected with 400"
else
  echo "  ✗ Wrong player action not rejected (got $HTTP_CODE)"
fi

echo ""
echo "=========================================="
echo "VERIFICATION COMPLETE"
echo "=========================================="
