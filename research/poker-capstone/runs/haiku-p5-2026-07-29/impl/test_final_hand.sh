#!/bin/bash

TABLE_ID="6c314062"
BASE_URL="http://localhost:8000"

echo "=== Completing hand to showdown ==="

# Play through remaining rounds with checks
for i in {1..15}; do
  STATE=$(curl -s "$BASE_URL/tables/$TABLE_ID/state?seat=0")
  HAND_IN_PROGRESS=$(echo "$STATE" | jq '.hand_in_progress')
  ACTOR=$(echo "$STATE" | jq '.current_actor')
  BETTING_ROUND=$(echo "$STATE" | jq '.betting_round')

  if [ "$HAND_IN_PROGRESS" = "false" ]; then
    echo "Iteration $i: Hand completed"
    break
  fi

  if [ "$ACTOR" = "null" ]; then
    echo "Iteration $i: No current actor"
    break
  fi

  echo "Iteration $i: Seat $ACTOR checking (round=$BETTING_ROUND)"

  STATE=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
    -H "Content-Type: application/json" \
    -d "{\"seat\": $ACTOR, \"action\": \"check\"}")
done

echo ""
echo "=== Final Hand State ==="
FINAL=$(curl -s "$BASE_URL/tables/$TABLE_ID/state?seat=0")

echo "Hand in progress: $(echo "$FINAL" | jq '.hand_in_progress')"
echo "Betting round: $(echo "$FINAL" | jq '.betting_round')"
echo ""
echo "Pots:"
echo "$FINAL" | jq '.pots'
echo ""
echo "Player stacks and totals:"
echo "$FINAL" | jq '.players[] | {seat, stack, status, total_committed}'
echo ""
TOTAL=$(echo "$FINAL" | jq '.players | map(.stack) | add')
echo "Total chips in play: $TOTAL (should be 150)"
