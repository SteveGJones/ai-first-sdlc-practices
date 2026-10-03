// ============================================================================
// State Management
// ============================================================================

let currentState = null;
let tableId = null;
let seatNumber = null;
let socket = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;
const RECONNECT_DELAY_MS = 1000;
let actionInFlight = false;

// Get API base URL - the client is served on port 80, server is on 8000
// Both are on the same host by default in the harness
const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`;

// ============================================================================
// URL Parsing & Deep Linking
// ============================================================================

function getUrlParams() {
  const params = new URLSearchParams(window.location.search);
  return {
    tableId: params.get('table'),
    seatNumber: params.get('seat') ? parseInt(params.get('seat'), 10) : null
  };
}

async function handleDeepLink() {
  const { tableId: paramTableId, seatNumber: paramSeatNumber } = getUrlParams();
  if (paramTableId && paramSeatNumber !== null) {
    tableId = paramTableId;
    seatNumber = paramSeatNumber;
    showTableView();
    await loadTableState();
    subscribeToUpdates();
    return true;
  }
  return false;
}

// ============================================================================
// Rendering & DOM Updates
// ============================================================================

function showLobbyView() {
  document.getElementById('lobby-view').classList.add('active');
  document.getElementById('table-view').classList.remove('active');
}

function showTableView() {
  document.getElementById('lobby-view').classList.remove('active');
  document.getElementById('table-view').classList.add('active');
}

/**
 * Render the complete table state to the DOM
 * Updates all data-* attributes per CLIENT-TEST-CONTRACT.md
 */
function renderTableState(state) {
  if (!state) return;

  // ========== TABLE-LEVEL STATE MIRROR ==========
  const tableMirror = document.getElementById('table-state-mirror');
  if (tableMirror) {
    tableMirror.setAttribute('data-hand-in-progress', state.hand_in_progress ? 'true' : 'false');
    tableMirror.setAttribute('data-current-actor', state.current_actor !== null ? String(state.current_actor) : '');
    tableMirror.setAttribute('data-current-bet', String(state.current_bet));
    tableMirror.setAttribute('data-button-seat', state.button_seat !== null ? String(state.button_seat) : '');
  }

  // ========== PER-SEAT STATE MIRRORS & HOLE CARDS ==========
  state.players.forEach(player => {
    const seatEl = document.getElementById(`seat-${player.seat}`);
    if (seatEl) {
      // Update per-seat state attributes
      seatEl.setAttribute('data-seat', String(player.seat));
      seatEl.setAttribute('data-status', player.status);
      seatEl.setAttribute('data-stack', String(player.stack));
      seatEl.setAttribute('data-current-bet', String(player.current_bet));
      seatEl.setAttribute('data-total-committed', String(player.total_committed));

      // Update hole cards for this seat
      for (let i = 0; i < 2; i++) {
        const holeCardEl = document.querySelector(`[data-testid="seat-${player.seat}-hole-card-${i}"]`);
        if (holeCardEl) {
          // Card is hidden unless it's this client's seat or it's showdown
          const isHidden = player.hole_cards === null ||
                          (player.seat !== seatNumber && state.betting_round !== 'showdown');
          holeCardEl.setAttribute('data-hidden', isHidden ? 'true' : 'false');

          if (!isHidden && player.hole_cards && player.hole_cards[i]) {
            const card = player.hole_cards[i];
            holeCardEl.setAttribute('data-rank', String(card.rank));
            holeCardEl.setAttribute('data-suit', card.suit);
          } else {
            holeCardEl.setAttribute('data-rank', '0');
            holeCardEl.setAttribute('data-suit', '');
          }
        }
      }

      // Update visual rendering
      const playerNameEl = seatEl.querySelector('.player-name');
      if (playerNameEl) {
        playerNameEl.textContent = player.name || '(empty)';
      }
      const playerStackEl = seatEl.querySelector('.player-stack');
      if (playerStackEl) {
        playerStackEl.textContent = `$${player.stack}`;
      }

      // Status indicator
      const statusEl = seatEl.querySelector('.seat-status-indicator');
      if (statusEl) {
        statusEl.textContent = player.status === 'active' ? '' : player.status;
      }

      // Dealer button
      const dealerEl = seatEl.querySelector('.dealer-button');
      if (dealerEl) {
        dealerEl.style.display = player.seat === state.button_seat ? 'block' : 'none';
      }

      // Highlight current actor's seat
      seatEl.classList.toggle('current-actor', player.seat === state.current_actor);

      // Render hole cards visually
      const cardsContainer = seatEl.querySelector('.hole-cards');
      if (cardsContainer) {
        cardsContainer.innerHTML = '';
        if (player.hole_cards && player.hole_cards.length === 2) {
          player.hole_cards.forEach((card, idx) => {
            const cardEl = document.createElement('div');
            cardEl.className = 'card';
            cardEl.textContent = formatCard(card);
            cardsContainer.appendChild(cardEl);
          });
        }
      }
    }
  });

  // ========== COMMUNITY CARDS ==========
  const communityCardsContainer = document.getElementById('community-cards');
  if (communityCardsContainer) {
    communityCardsContainer.innerHTML = '';
    state.community_cards.forEach((card, idx) => {
      const cardEl = document.createElement('div');
      cardEl.setAttribute('data-testid', `community-card-${idx}`);
      cardEl.setAttribute('data-rank', String(card.rank));
      cardEl.setAttribute('data-suit', card.suit);
      cardEl.className = 'community-card';
      cardEl.textContent = formatCard(card);
      communityCardsContainer.appendChild(cardEl);
    });
  }

  // ========== POTS ==========
  const potsContainer = document.getElementById('pots-display');
  if (potsContainer) {
    potsContainer.innerHTML = '';
    state.pots.forEach((pot, idx) => {
      const potEl = document.createElement('div');
      potEl.setAttribute('data-testid', `pot-${idx}`);
      potEl.setAttribute('data-amount', String(pot.amount));
      potEl.className = 'pot-display';
      potEl.textContent = `Pot: $${pot.amount}`;
      potsContainer.appendChild(potEl);
    });
  }

  // ========== ACTION LOG ==========
  const actionLogEl = document.getElementById('action-log');
  if (actionLogEl && state.last_action_log && state.last_action_log.length > 0) {
    const recentAction = state.last_action_log[state.last_action_log.length - 1];
    actionLogEl.textContent = recentAction;
  }

  // ========== GAME STATUS ==========
  const gameStatusEl = document.getElementById('game-status');
  if (gameStatusEl) {
    let status = '';
    if (!state.hand_in_progress) {
      status = 'Waiting for hand to start...';
    } else if (state.current_actor === seatNumber) {
      status = 'Your turn!';
    } else if (state.current_actor !== null) {
      const currentActorPlayer = state.players.find(p => p.seat === state.current_actor);
      status = `${currentActorPlayer?.name || 'Player'} is acting...`;
    } else {
      status = `Betting round: ${state.betting_round}`;
    }
    gameStatusEl.textContent = status;
  }

  // ========== UPDATE ACTION BUTTONS ==========
  updateActionButtons(state);
}

function formatCard(card) {
  const ranks = ['?', '?', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
  const suitSymbols = { s: '♠', h: '♥', d: '♦', c: '♣' };
  return `${ranks[card.rank]}${suitSymbols[card.suit] || '?'}`;
}

function updateActionButtons(state) {
  const isMyTurn = state.current_actor === seatNumber;
  const handInProgress = state.hand_in_progress;

  document.getElementById('start-hand-btn').disabled = handInProgress;
  document.getElementById('fold-btn').disabled = !isMyTurn;
  document.getElementById('check-call-btn').disabled = !isMyTurn;
  document.getElementById('bet-raise-btn').disabled = !isMyTurn;
  document.getElementById('bet-amount-input').disabled = !isMyTurn;

  // Update label for check/call button and bet/raise button
  const checkCallBtn = document.getElementById('check-call-btn');
  checkCallBtn.textContent = state.current_bet > 0 ? 'Call' : 'Check';

  const betRaiseBtn = document.getElementById('bet-raise-btn');
  betRaiseBtn.textContent = state.current_bet > 0 ? 'Raise' : 'Bet';

  // Update bet/raise constraints
  if (isMyTurn) {
    const playerStack = state.players.find(p => p.seat === seatNumber)?.stack || 0;
    const minAmount = state.current_bet > 0
      ? state.current_bet + state.min_raise
      : state.min_raise;
    document.getElementById('bet-amount-input').min = String(minAmount);
    document.getElementById('bet-amount-input').max = String(playerStack);
  }
}

// ============================================================================
// State Sync: REST & WebSocket
// ============================================================================

async function loadTableState() {
  try {
    const response = await fetch(`${API_BASE}/tables/${tableId}/state?seat=${seatNumber}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch state: ${response.status}`);
    }
    const state = await response.json();
    currentState = state;
    renderTableState(state);
    return state;
  } catch (err) {
    console.error('Error loading table state:', err);
    showConnectionStatus(`Error: ${err.message}`, 'error');
  }
}

function subscribeToUpdates() {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.hostname}:8000/tables/${tableId}/ws?seat=${seatNumber}`;

  socket = new WebSocket(wsUrl);

  socket.addEventListener('open', () => {
    console.log('WebSocket connected');
    reconnectAttempts = 0;
    showConnectionStatus('Connected', 'connected');
  });

  socket.addEventListener('message', (event) => {
    try {
      const state = JSON.parse(event.data);
      currentState = state;
      renderTableState(state);
      showConnectionStatus('Connected', 'connected');
    } catch (err) {
      console.error('Error parsing WebSocket message:', err);
    }
  });

  socket.addEventListener('close', () => {
    console.log('WebSocket closed');
    showConnectionStatus('Reconnecting...', 'reconnecting');
    scheduleReconnect();
  });

  socket.addEventListener('error', (err) => {
    console.error('WebSocket error:', err);
    showConnectionStatus('Connection error', 'error');
  });
}

function scheduleReconnect() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    showConnectionStatus('Max reconnect attempts reached', 'error');
    return;
  }
  reconnectAttempts++;
  const delay = RECONNECT_DELAY_MS * Math.pow(2, Math.min(reconnectAttempts - 1, 4));
  setTimeout(async () => {
    console.log(`Reconnecting... attempt ${reconnectAttempts}`);
    // Re-fetch state and resubscribe
    await loadTableState();
    subscribeToUpdates();
  }, delay);
}

function showConnectionStatus(message, status) {
  const el = document.getElementById('connection-status');
  if (el) {
    el.textContent = message;
    el.className = `connection-status ${status}`;
  }
}

// ============================================================================
// Action Submission
// ============================================================================

async function submitAction(action, amount = null) {
  if (actionInFlight) return;
  if (seatNumber === null || tableId === null) return;

  actionInFlight = true;
  updateActionButtons(currentState || {});

  try {
    const body = {
      seat: seatNumber,
      action: action
    };
    if (amount !== null) {
      body.amount = amount;
    }

    const response = await fetch(`${API_BASE}/tables/${tableId}/actions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    if (response.ok) {
      const newState = await response.json();
      currentState = newState;
      renderTableState(newState);
    } else {
      const error = await response.json();
      const message = error.error || error.detail || 'Action rejected';
      showConnectionStatus(`Error: ${message}`, 'error');
      // Leave UI as-is, don't clear or update
    }
  } catch (err) {
    console.error('Error submitting action:', err);
    showConnectionStatus(`Error: ${err.message}`, 'error');
  } finally {
    actionInFlight = false;
    if (currentState) {
      updateActionButtons(currentState);
    }
  }
}

async function startHand() {
  if (tableId === null) return;

  try {
    const response = await fetch(`${API_BASE}/tables/${tableId}/start`, {
      method: 'POST'
    });

    if (response.ok) {
      const newState = await response.json();
      currentState = newState;
      renderTableState(newState);
    } else {
      const error = await response.json();
      const message = error.error || error.detail || 'Failed to start hand';
      showConnectionStatus(`Error: ${message}`, 'error');
    }
  } catch (err) {
    console.error('Error starting hand:', err);
    showConnectionStatus(`Error: ${err.message}`, 'error');
  }
}

// ============================================================================
// Lobby Actions
// ============================================================================

async function createTable() {
  const smallBlind = parseInt(document.getElementById('create-small-blind').value, 10);
  const bigBlind = parseInt(document.getElementById('create-big-blind').value, 10);

  try {
    const response = await fetch(`${API_BASE}/tables`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ small_blind: smallBlind, big_blind: bigBlind })
    });

    if (response.ok) {
      const data = await response.json();
      tableId = data.table_id;
      // Redirect to join as first player
      window.location.href = `/?table=${tableId}&seat=0`;
    } else {
      const error = await response.json();
      alert(`Error creating table: ${error.error || error.detail}`);
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

async function joinTable() {
  const joinTableId = document.getElementById('join-table-id').value.trim();
  const playerName = document.getElementById('join-player-name').value.trim();
  const buyIn = parseInt(document.getElementById('join-buy-in').value, 10);

  if (!joinTableId || !playerName || !buyIn) {
    alert('Please fill in all fields');
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/tables/${joinTableId}/players`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: playerName, buy_in: buyIn })
    });

    if (response.ok) {
      const data = await response.json();
      const seat = data.seat;
      tableId = joinTableId;
      window.location.href = `/?table=${tableId}&seat=${seat}`;
    } else {
      const error = await response.json();
      alert(`Error joining table: ${error.error || error.detail}`);
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

function backToLobby() {
  if (socket) {
    socket.close();
  }
  tableId = null;
  seatNumber = null;
  currentState = null;
  showLobbyView();
}

// ============================================================================
// Event Listeners
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
  // Lobby buttons
  document.getElementById('create-table-btn').addEventListener('click', createTable);
  document.getElementById('join-table-btn').addEventListener('click', joinTable);

  // Table view buttons
  document.getElementById('start-hand-btn').addEventListener('click', startHand);
  document.getElementById('fold-btn').addEventListener('click', () => submitAction('fold'));
  document.getElementById('check-call-btn').addEventListener('click', () => {
    const action = currentState?.current_bet > 0 ? 'call' : 'check';
    submitAction(action);
  });
  document.getElementById('bet-raise-btn').addEventListener('click', () => {
    const amount = parseInt(document.getElementById('bet-amount-input').value, 10);
    if (!isNaN(amount) && amount > 0) {
      const action = currentState?.current_bet > 0 ? 'raise' : 'bet';
      submitAction(action, amount);
    }
  });
  document.getElementById('back-to-lobby-btn').addEventListener('click', backToLobby);

  // Try to deep-link to a table if URL params exist
  const deepLinked = await handleDeepLink();
  if (!deepLinked) {
    showLobbyView();
  }
});
