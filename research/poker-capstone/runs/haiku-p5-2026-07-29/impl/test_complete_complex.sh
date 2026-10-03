#!/bin/bash

TABLE_ID="150cdcd7"
BASE_URL="http://localhost:8000"

# Complete the hand by having players check through remaining rounds
STATE=$(curl -s "$BASE_URL/tables/$TABLE_ID/state?seat=0")
HAND_IN_PROGRESS=$(echo "$STATE" | jq '.hand_in_progress')
BETTING_ROUND=$(echo "$STATE" | jq '.betting_round')
ACTOR=$(echo "$STATE" | jq '.current_actor')

echo "Starting completion from: round=$BETTING_ROUND, actor=$ACTOR, hand_in_progress=$HAND_IN_PROGRESS"
echo ""

# Play through the hand with checks
for i in {1..20}; do
  if [ "$HAND_IN_PROGRESS" = "false" ]; then
    echo "Hand ended at iteration $i"
    break
  fi

  if [ "$ACTOR" = "null" ]; then
    echo "No current actor at iteration $i"
    break
  fi

  echo "Iteration $i: Seat $ACTOR checking (round=$BETTING_ROUND)"
  STATE=$(curl -s -X POST "$BASE_URL/tables/$TABLE_ID/actions" \
    -H "Content-Type: application/json" \
    -d "{\"seat\": $ACTOR, \"action\": \"check\"}")

  ACTOR=$(echo "$STATE" | jq '.current_actor')
  BETTING_ROUND=$(echo "$STATE" | jq '.betting_round')
  HAND_IN_PROGRESS=$(echo "$STATE" | jq '.hand_in_progress')
done

echo ""
echo "=== Hand Complete ==="
FINAL=$(curl -s "$BASE_URL/tables/$TABLE_ID/state?seat=0")

echo "Hand in progress: $(echo "$FINAL" | jq '.hand_in_progress')"
echo "Betting round: $(echo "$FINAL" | jq '.betting_round')"
echo ""
echo "Pots:"
echo "$FINAL" | jq '.pots'
echo ""
echo "Player stacks after:"
echo "$FINAL" | jq '.players[] | {seat, stack, status, total_committed}'
echo ""
TOTAL=$(echo "$FINAL" | jq '.players | map(.stack) | add')
echo "Total chips: $TOTAL (should be 150)"
