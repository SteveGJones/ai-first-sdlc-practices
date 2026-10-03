"use strict";

/*
 * Poker client — no framework, no build step.
 *
 * The client holds no game logic. It renders whatever state the server
 * last sent, and submits action requests. The server is the source of
 * truth; a rejected action just re-renders from the last known-good
 * state with an error shown (see design-client.md "Action submission").
 *
 * API base is derived from the browser's own hostname (never a
 * hardcoded localhost), port 8000, per the harness contract.
 */

const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`;
const WS_BASE = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.hostname}:8000`;

const SUIT_SYMBOL = { s: "♠", h: "♥", d: "♦", c: "♣" };
const RANK_LABEL = { 11: "J", 12: "Q", 13: "K", 14: "A" };

function rankLabel(rank) {
  return RANK_LABEL[rank] || String(rank);
}

// ---------------------------------------------------------------------
// DOM handles
// ---------------------------------------------------------------------

const el = {
  lobbyView: document.getElementById("lobby-view"),
  tableView: document.getElementById("table-view"),

  createForm: document.getElementById("create-table-form"),
  createSmallBlind: document.getElementById("create-small-blind"),
  createBigBlind: document.getElementById("create-big-blind"),
  createResult: document.getElementById("create-table-result"),

  joinForm: document.getElementById("join-table-form"),
  joinTableId: document.getElementById("join-table-id"),
  joinName: document.getElementById("join-name"),
  joinBuyin: document.getElementById("join-buyin"),
  joinResult: document.getElementById("join-table-result"),

  gotoForm: document.getElementById("goto-form"),
  gotoTableId: document.getElementById("goto-table-id"),
  gotoSeat: document.getElementById("goto-seat"),

  backToLobby: document.getElementById("back-to-lobby"),
  tableIdDisplay: document.getElementById("table-id-display"),
  mySeatDisplay: document.getElementById("my-seat-display"),
  connectionStatus: document.getElementById("connection-status"),

  tableMirror: document.getElementById("table-state-mirror"),
  communityCards: document.getElementById("community-cards"),
  pots: document.getElementById("pots"),
  seats: document.getElementById("seats"),
  lastActionLog: document.getElementById("last-action-log"),
  errorToast: document.getElementById("error-toast"),

  startHandBtn: document.getElementById("start-hand"),
  foldBtn: document.getElementById("action-fold"),
  checkCallBtn: document.getElementById("action-check-call"),
  betRaiseBtn: document.getElementById("action-bet-raise"),
  betAmountInput: document.getElementById("bet-amount-input"),
};

// ---------------------------------------------------------------------
// Application state (single source of truth for both visible UI and
// the data-attribute mirror — one render pass drives both, so they
// cannot drift from each other).
// ---------------------------------------------------------------------

const ctx = {
  tableId: null,
  seat: null,
  state: null, // last full state from the server (GET/POST response or WS push)
  prevState: null, // previous state, used only to infer a human-readable action log line
  ws: null,
  wsRetryMs: 1000,
  actionInFlight: false,
  reconnecting: false,
};

// ---------------------------------------------------------------------
// Routing: lobby vs. deep-linked table view
// ---------------------------------------------------------------------

function parseQuery() {
  const params = new URLSearchParams(window.location.search);
  const table = params.get("table");
  const seat = params.get("seat");
  if (table !== null && seat !== null && seat !== "") {
    return { table, seat: Number(seat) };
  }
  return null;
}

function showLobby() {
  el.lobbyView.hidden = false;
  el.tableView.hidden = true;
  closeSocket();
}

function showTable() {
  el.lobbyView.hidden = true;
  el.tableView.hidden = false;
}

function navigateToTable(tableId, seat) {
  const url = new URL(window.location.href);
  url.searchParams.set("table", tableId);
  url.searchParams.set("seat", String(seat));
  window.history.pushState({}, "", url);
  enterTable(tableId, seat);
}

// ---------------------------------------------------------------------
// Lobby handlers (free-form, never used by the test driver)
// ---------------------------------------------------------------------

el.createForm.addEventListener("submit", async (evt) => {
  evt.preventDefault();
  el.createResult.textContent = "Creating…";
  try {
    const res = await fetch(`${API_BASE}/tables`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        small_blind: Number(el.createSmallBlind.value),
        big_blind: Number(el.createBigBlind.value),
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || data.detail || "create failed");
    el.createResult.textContent = `Table created: ${data.table_id}`;
    el.joinTableId.value = data.table_id;
    el.gotoTableId.value = data.table_id;
  } catch (err) {
    el.createResult.textContent = `Error: ${err.message}`;
  }
});

el.joinForm.addEventListener("submit", async (evt) => {
  evt.preventDefault();
  el.joinResult.textContent = "Joining…";
  const tableId = el.joinTableId.value.trim();
  try {
    const res = await fetch(`${API_BASE}/tables/${encodeURIComponent(tableId)}/players`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: el.joinName.value,
        buy_in: Number(el.joinBuyin.value),
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || data.detail || "join failed");
    el.joinResult.textContent = `Seated at seat ${data.seat}`;
    navigateToTable(tableId, data.seat);
  } catch (err) {
    el.joinResult.textContent = `Error: ${err.message}`;
  }
});

el.gotoForm.addEventListener("submit", (evt) => {
  evt.preventDefault();
  navigateToTable(el.gotoTableId.value.trim(), Number(el.gotoSeat.value));
});

el.backToLobby.addEventListener("click", () => {
  const url = new URL(window.location.href);
  url.searchParams.delete("table");
  url.searchParams.delete("seat");
  window.history.pushState({}, "", url);
  showLobby();
});

// ---------------------------------------------------------------------
// Table view: entry, state sync (REST bootstrap + WebSocket push)
// ---------------------------------------------------------------------

function enterTable(tableId, seat) {
  ctx.tableId = tableId;
  ctx.seat = seat;
  ctx.state = null;
  ctx.prevState = null;
  el.tableIdDisplay.textContent = tableId;
  el.mySeatDisplay.textContent = String(seat);
  showTable();
  setConnectionStatus("connecting");
  fetchState()
    .then(() => openSocket())
    .catch((err) => {
      showError(`Failed to load table: ${err.message}`);
    });
}

async function fetchState() {
  const res = await fetch(
    `${API_BASE}/tables/${encodeURIComponent(ctx.tableId)}/state?seat=${ctx.seat}`
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || data.detail || "failed to fetch state");
  applyState(data);
}

function openSocket() {
  closeSocket();
  const ws = new WebSocket(
    `${WS_BASE}/tables/${encodeURIComponent(ctx.tableId)}/ws?seat=${ctx.seat}`
  );
  ctx.ws = ws;

  ws.onopen = () => {
    ctx.wsRetryMs = 1000;
    ctx.reconnecting = false;
    setConnectionStatus("connected");
  };

  ws.onmessage = (evt) => {
    try {
      const data = JSON.parse(evt.data);
      applyState(data);
    } catch (err) {
      // Malformed push — ignore, keep last known-good state.
      console.error("Bad WS message", err);
    }
  };

  ws.onclose = () => {
    if (ctx.ws !== ws) return; // superseded by a newer socket
    setConnectionStatus("reconnecting");
    scheduleReconnect();
  };

  ws.onerror = () => {
    ws.close();
  };
}

function closeSocket() {
  if (ctx.ws) {
    const old = ctx.ws;
    ctx.ws = null;
    old.onclose = null;
    old.close();
  }
}

function scheduleReconnect() {
  if (ctx.reconnecting) return;
  ctx.reconnecting = true;
  setTimeout(async () => {
    ctx.reconnecting = false;
    if (el.tableView.hidden) return; // navigated away
    try {
      // Re-fetch full state before resubscribing — covers whatever
      // happened while disconnected (design-client.md "State sync").
      await fetchState();
      openSocket();
    } catch (err) {
      ctx.wsRetryMs = Math.min(ctx.wsRetryMs * 2, 15000);
      scheduleReconnect();
    }
  }, ctx.wsRetryMs);
}

function setConnectionStatus(state) {
  el.connectionStatus.dataset.state = state;
  el.connectionStatus.textContent =
    state === "connected" ? "live" : state === "connecting" ? "connecting…" : "reconnecting…";
}

// ---------------------------------------------------------------------
// Applying a new state: every message wholesale-replaces local state
// (never diffed/merged), then a single render pass draws both the
// visible UI and the data-attribute mirror from it.
// ---------------------------------------------------------------------

function applyState(newState) {
  ctx.prevState = ctx.state;
  ctx.state = newState;
  logInferredAction(ctx.prevState, ctx.state);
  render();
}

// ---------------------------------------------------------------------
// Rendering — single source of truth (ctx.state) drives both the
// human-facing table and the required data-testid/data-* mirror in
// the same pass, so the two can never disagree.
// ---------------------------------------------------------------------

function render() {
  const state = ctx.state;
  if (!state) return;

  renderTableMirror(state);
  renderSeats(state);
  renderCommunityCards(state);
  renderPots(state);
  renderActionBar(state);
}

function renderTableMirror(state) {
  el.tableMirror.dataset.handInProgress = String(!!state.hand_in_progress);
  el.tableMirror.dataset.currentActor =
    state.current_actor === null || state.current_actor === undefined
      ? ""
      : String(state.current_actor);
  el.tableMirror.dataset.currentBet = String(state.current_bet);
  el.tableMirror.dataset.buttonSeat = String(state.button_seat);
}

function findShowdownCards(state, seat) {
  if (!Array.isArray(state.last_showdown)) return null;
  const entry = state.last_showdown.find((e) => e.seat === seat);
  return entry ? entry.hole_cards : null;
}

/**
 * Resolve the two hole cards to render for a seat, and whether they
 * should be shown as visible.
 *
 * The harness's redacted GET/WS state only ever includes a seat's own
 * hole cards on `players[n].hole_cards` (never another seat's, except
 * once the hand reaches showdown, per design-client.md and
 * HARNESS-CONTRACT.md's GET /state description). `last_showdown` is the
 * durable record for hands that reached showdown, so it's also checked
 * as a fallback once the hand has ended, until the next deal.
 */
function resolveHoleCards(state, player) {
  if (Array.isArray(player.hole_cards) && player.hole_cards.length === 2) {
    return { visible: true, cards: player.hole_cards };
  }
  const showdownCards = findShowdownCards(state, player.seat);
  if (Array.isArray(showdownCards) && showdownCards.length === 2) {
    return { visible: true, cards: showdownCards };
  }
  return { visible: false, cards: [null, null] };
}

function cardText(card) {
  if (!card) return "?";
  return `${rankLabel(card.rank)}${SUIT_SYMBOL[card.suit] || card.suit}`;
}

function cardSuitClass(card) {
  if (!card) return "";
  return card.suit === "h" || card.suit === "d" ? "red" : "black";
}

function buildHoleCardEl(seat, index, card, visible) {
  const div = document.createElement("div");
  div.className = "card hole-card" + (visible ? " " + cardSuitClass(card) : " face-down");
  div.dataset.testid = `seat-${seat}-hole-card-${index}`;
  div.dataset.hidden = visible ? "false" : "true";
  if (visible && card) {
    div.dataset.rank = String(card.rank);
    div.dataset.suit = card.suit;
    div.textContent = cardText(card);
  } else {
    delete div.dataset.rank;
    delete div.dataset.suit;
    div.textContent = "\u{1F0A0}"; // card back glyph
  }
  return div;
}

function renderSeats(state) {
  el.seats.innerHTML = "";
  const players = Array.isArray(state.players) ? state.players : [];
  const total = players.length;
  const sorted = [...players].sort((a, b) => a.seat - b.seat);

  sorted.forEach((player, idx) => {
    const seatEl = document.createElement("div");
    seatEl.className = "seat";
    seatEl.dataset.testid = `seat-${player.seat}`;
    seatEl.dataset.seat = String(player.seat);
    seatEl.dataset.status = player.status;
    seatEl.dataset.stack = String(player.stack);
    seatEl.dataset.currentBet = String(player.current_bet);
    seatEl.dataset.totalCommitted = String(player.total_committed);

    if (player.seat === state.button_seat) seatEl.classList.add("is-button");
    if (state.hand_in_progress && player.seat === state.current_actor) {
      seatEl.classList.add("is-current-actor");
    }
    if (player.seat === ctx.seat) seatEl.classList.add("is-me");
    if (player.status === "folded") seatEl.classList.add("is-folded");
    if (player.status === "all_in") seatEl.classList.add("is-all-in");

    const angle = total > 0 ? (idx / total) * 360 : 0;
    seatEl.style.setProperty("--seat-angle", `${angle}deg`);

    const nameEl = document.createElement("div");
    nameEl.className = "seat-name";
    nameEl.textContent = `Seat ${player.seat}${player.seat === ctx.seat ? " (you)" : ""}`;
    seatEl.appendChild(nameEl);

    if (player.seat === state.button_seat) {
      const buttonMarker = document.createElement("div");
      buttonMarker.className = "dealer-button";
      buttonMarker.textContent = "D";
      seatEl.appendChild(buttonMarker);
    }

    const stackEl = document.createElement("div");
    stackEl.className = "seat-stack";
    stackEl.textContent = `Stack: ${player.stack}`;
    seatEl.appendChild(stackEl);

    const betEl = document.createElement("div");
    betEl.className = "seat-bet";
    betEl.textContent = `Bet: ${player.current_bet}`;
    seatEl.appendChild(betEl);

    const statusEl = document.createElement("div");
    statusEl.className = "seat-status-label";
    statusEl.textContent = player.status;
    seatEl.appendChild(statusEl);

    const holeWrap = document.createElement("div");
    holeWrap.className = "hole-cards";
    const { visible, cards } = resolveHoleCards(state, player);
    holeWrap.appendChild(buildHoleCardEl(player.seat, 0, cards[0], visible));
    holeWrap.appendChild(buildHoleCardEl(player.seat, 1, cards[1], visible));
    seatEl.appendChild(holeWrap);

    el.seats.appendChild(seatEl);
  });
}

function renderCommunityCards(state) {
  el.communityCards.innerHTML = "";
  const cards = Array.isArray(state.community_cards) ? state.community_cards : [];
  cards.forEach((card, i) => {
    const div = document.createElement("div");
    div.className = "card community-card " + cardSuitClass(card);
    div.dataset.testid = `community-card-${i}`;
    div.dataset.rank = String(card.rank);
    div.dataset.suit = card.suit;
    div.textContent = cardText(card);
    el.communityCards.appendChild(div);
  });
}

function renderPots(state) {
  el.pots.innerHTML = "";
  const pots = Array.isArray(state.pots) ? state.pots : [];
  pots.forEach((pot, i) => {
    const div = document.createElement("div");
    div.className = "pot";
    div.dataset.testid = `pot-${i}`;
    div.dataset.amount = String(pot.amount);
    div.textContent = i === 0 ? `Pot: ${pot.amount}` : `Side pot ${i}: ${pot.amount}`;
    el.pots.appendChild(div);
  });
}

function myPlayer(state) {
  return (state.players || []).find((p) => p.seat === ctx.seat) || null;
}

function renderActionBar(state) {
  const players = Array.isArray(state.players) ? state.players : [];
  const me = myPlayer(state);
  const isMyTurn =
    !!state.hand_in_progress &&
    state.current_actor === ctx.seat &&
    !!me &&
    me.status === "active";
  const disableAll = ctx.actionInFlight || !isMyTurn;

  el.startHandBtn.disabled = ctx.actionInFlight || !!state.hand_in_progress || players.length < 2;
  el.foldBtn.disabled = disableAll;

  const owesCall = me ? state.current_bet > me.current_bet : false;
  el.checkCallBtn.disabled = disableAll;
  el.checkCallBtn.textContent = owesCall ? `Call ${state.current_bet - (me ? me.current_bet : 0)}` : "Check";
  el.checkCallBtn.dataset.action = owesCall ? "call" : "check";

  el.betRaiseBtn.disabled = disableAll;
  el.betAmountInput.disabled = disableAll;

  const isRaise = state.current_bet > 0;
  el.betRaiseBtn.textContent = isRaise ? "Raise" : "Bet";
  el.betRaiseBtn.dataset.action = isRaise ? "raise" : "bet";

  if (me) {
    // Best-effort UI floor/ceiling for the total-this-round amount.
    // `min_raise` / `big_blind` aren't part of the fixed state response
    // (HARNESS-CONTRACT.md), so this is a helpful default only — the
    // server remains authoritative and a too-low amount is rejected
    // with a 409, handled like any other illegal action (see
    // design-client.md "Action submission").
    const floor = isRaise ? state.current_bet + 1 : 1;
    const ceiling = me.current_bet + me.stack;
    el.betAmountInput.min = String(Math.min(floor, ceiling));
    el.betAmountInput.max = String(ceiling);
    if (!el.betAmountInput.value || Number(el.betAmountInput.value) < floor) {
      el.betAmountInput.value = String(Math.min(floor, ceiling));
    }
  }
}

// ---------------------------------------------------------------------
// Action submission
// ---------------------------------------------------------------------

el.startHandBtn.addEventListener("click", () => submitStart());
el.foldBtn.addEventListener("click", () => submitAction("fold"));
el.checkCallBtn.addEventListener("click", () => submitAction(el.checkCallBtn.dataset.action));
el.betRaiseBtn.addEventListener("click", () =>
  submitAction(el.betRaiseBtn.dataset.action, Number(el.betAmountInput.value))
);

async function submitStart() {
  if (ctx.actionInFlight) return;
  setInFlight(true);
  try {
    const res = await fetch(`${API_BASE}/tables/${encodeURIComponent(ctx.tableId)}/start`, {
      method: "POST",
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || data.detail || "could not start hand");
    applyState(data);
  } catch (err) {
    showError(err.message);
  } finally {
    setInFlight(false);
  }
}

async function submitAction(action, amount) {
  if (ctx.actionInFlight) return;
  setInFlight(true);
  const body = { seat: ctx.seat, action };
  if (amount !== undefined && !Number.isNaN(amount)) body.amount = amount;
  try {
    const res = await fetch(`${API_BASE}/tables/${encodeURIComponent(ctx.tableId)}/actions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      // 409 (or other rejection): leave state exactly as it was,
      // just surface the server's reason (design-client.md).
      throw new Error(data.error || data.detail || "action rejected");
    }
    // Apply immediately — don't wait for the WS echo, which is
    // idempotent to apply again when it arrives.
    applyState(data);
  } catch (err) {
    showError(err.message);
  } finally {
    setInFlight(false);
  }
}

function setInFlight(value) {
  ctx.actionInFlight = value;
  if (ctx.state) renderActionBar(ctx.state);
}

// ---------------------------------------------------------------------
// Error toast + inferred action log
// ---------------------------------------------------------------------

let errorTimer = null;
function showError(message) {
  el.errorToast.textContent = message;
  el.errorToast.hidden = false;
  if (errorTimer) clearTimeout(errorTimer);
  errorTimer = setTimeout(() => {
    el.errorToast.hidden = true;
  }, 5000);
}

function logLine(text) {
  const line = document.createElement("div");
  line.className = "log-line";
  line.textContent = text;
  el.lastActionLog.prepend(line);
  while (el.lastActionLog.children.length > 20) {
    el.lastActionLog.removeChild(el.lastActionLog.lastChild);
  }
}

/**
 * There's no explicit "what just happened" field on the state
 * response (HARNESS-CONTRACT.md's response shape is state-only), so
 * the human-facing log/toast design-client.md calls for is inferred
 * by diffing the previous and new full-state snapshots. This is pure
 * presentation — it never feeds back into game logic or the mirror.
 */
function logInferredAction(prev, next) {
  if (!next) return;
  if (!prev) {
    logLine("Table state loaded.");
    return;
  }
  if (!prev.hand_in_progress && next.hand_in_progress) {
    logLine("New hand started.");
  }
  if (prev.hand_in_progress && !next.hand_in_progress) {
    logLine("Hand ended.");
  }
  if (next.community_cards.length > prev.community_cards.length) {
    const revealed = next.community_cards.slice(prev.community_cards.length);
    logLine(`Dealt: ${revealed.map(cardText).join(" ")}`);
  }
  const prevPlayers = new Map((prev.players || []).map((p) => [p.seat, p]));
  for (const p of next.players || []) {
    const before = prevPlayers.get(p.seat);
    if (!before) continue;
    if (before.status !== p.status && p.status === "folded") {
      logLine(`Seat ${p.seat} folded.`);
    } else if (before.status !== p.status && p.status === "all_in") {
      logLine(`Seat ${p.seat} is all-in.`);
    } else if (p.current_bet > before.current_bet) {
      logLine(`Seat ${p.seat} bet to ${p.current_bet}.`);
    } else if (p.stack !== before.stack && p.current_bet === before.current_bet) {
      logLine(`Seat ${p.seat}'s stack changed to ${p.stack}.`);
    }
  }
}

// ---------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------

(function init() {
  const deepLink = parseQuery();
  if (deepLink) {
    enterTable(deepLink.table, deepLink.seat);
  } else {
    showLobby();
  }
})();
