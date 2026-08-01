// Poker capstone exemplar client. No framework, no build step — see
// docs/design-client.md. Holds no game logic: every render is a direct
// reflection of the last state the server sent; every action is a REST
// call the server may accept or reject.

const params = new URLSearchParams(window.location.search);
const apiPort = params.get("api_port") || "8000";
const API_BASE = `${window.location.protocol}//${window.location.hostname}:${apiPort}`;
const WS_BASE = `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.hostname}:${apiPort}`;

let tableId = null;
let mySeat = null;
let socket = null;
let lastState = null;
let actionInFlight = false;

const $ = (id) => document.getElementById(id);

function suitSymbol(suit) {
  return { s: "♠", h: "♥", d: "♦", c: "♣" }[suit] || suit;
}

function rankLabel(rank) {
  return { 11: "J", 12: "Q", 13: "K", 14: "A" }[rank] || String(rank);
}

function cardEl(card) {
  const span = document.createElement("span");
  span.className = "card" + (card.suit === "h" || card.suit === "d" ? " red" : "");
  span.textContent = `${rankLabel(card.rank)}${suitSymbol(card.suit)}`;
  return span;
}

// ---- Lobby ----

$("create-table-btn").addEventListener("click", async () => {
  const sb = Number($("sb").value);
  const bb = Number($("bb").value);
  const res = await fetch(`${API_BASE}/tables`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ small_blind: sb, big_blind: bb }),
  });
  const body = await res.json();
  $("create-result").textContent = res.ok
    ? `Created table_id=${body.table_id}`
    : `Error: ${body.detail}`;
});

$("join-btn").addEventListener("click", async () => {
  const id = $("join-table-id").value.trim();
  const res = await fetch(`${API_BASE}/tables/${id}/players`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: $("join-name").value,
      buy_in: Number($("join-buyin").value),
    }),
  });
  const body = await res.json();
  $("join-result").textContent = res.ok
    ? `Seated at seat=${body.seat}`
    : `Error: ${body.detail}`;
});

$("enter-btn").addEventListener("click", () => {
  tableId = $("enter-table-id").value.trim();
  mySeat = Number($("enter-seat").value);
  $("lobby").classList.add("hidden");
  $("table-view").classList.remove("hidden");
  connect();
});

// ---- Table view ----

function connect() {
  fetchState();
  const url = `${WS_BASE}/tables/${tableId}/ws?seat=${mySeat}`;
  socket = new WebSocket(url);
  socket.onmessage = (evt) => render(JSON.parse(evt.data));
  socket.onclose = () => {
    appendLog("disconnected, retrying in 2s...");
    setTimeout(connect, 2000);
  };
}

async function fetchState() {
  const res = await fetch(`${API_BASE}/tables/${tableId}/state?seat=${mySeat}`);
  if (res.ok) render(await res.json());
}

function appendLog(line) {
  const log = $("log");
  log.textContent += line + "\n";
  log.scrollTop = log.scrollHeight;
}

function render(state) {
  lastState = state;

  $("community-cards").replaceChildren();
  state.community_cards.forEach((c) => $("community-cards").appendChild(cardEl(c)));

  $("pots").textContent = state.pots.length
    ? state.pots.map((p, i) => `Pot ${i + 1}: ${p.amount}`).join("  |  ")
    : "";

  const seatsDiv = $("seats");
  seatsDiv.replaceChildren();
  const n = state.players.length;
  state.players.forEach((p, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2;
    const cx = 50 + 42 * Math.cos(angle);
    const cy = 50 + 42 * Math.sin(angle);
    const el = document.createElement("div");
    el.className =
      "seat" +
      (p.seat === state.current_actor ? " current-actor" : "") +
      (p.status === "folded" ? " folded" : "");
    el.style.left = `calc(${cx}% - 70px)`;
    el.style.top = `calc(${cy}% - 40px)`;

    const holeCards = p.hole_cards
      ? p.hole_cards.map((c) => `${rankLabel(c.rank)}${suitSymbol(c.suit)}`).join(" ")
      : p.status === "folded"
      ? "folded"
      : "??";

    // p.name is a player-supplied string (POST /tables/{id}/players), never
    // trusted as markup — built with textContent, not innerHTML, so a seat
    // name can't inject HTML/JS into every other player's browser.
    const nameLine = document.createElement("div");
    if (p.seat === state.button_seat) {
      const marker = document.createElement("span");
      marker.className = "button-marker";
      marker.textContent = "D";
      nameLine.appendChild(marker);
      nameLine.appendChild(document.createTextNode(" "));
    }
    const strong = document.createElement("strong");
    strong.textContent = p.name;
    nameLine.appendChild(strong);
    nameLine.appendChild(document.createTextNode(` (seat ${p.seat})`));
    el.appendChild(nameLine);

    for (const text of [`stack: ${p.stack}`, `bet: ${p.current_bet}`, holeCards, p.status]) {
      const div = document.createElement("div");
      div.textContent = text;
      el.appendChild(div);
    }
    seatsDiv.appendChild(el);
  });

  const myTurn = state.current_actor === mySeat;
  const me = state.players.find((p) => p.seat === mySeat);
  const toCall = me ? state.current_bet - me.current_bet : 0;

  $("start-hand-btn").disabled = state.hand_in_progress;
  $("fold-btn").disabled = !myTurn;
  $("check-call-btn").disabled = !myTurn;
  $("check-call-btn").textContent = toCall > 0 ? `Call ${toCall}` : "Check";
  $("bet-raise-btn").disabled = !myTurn;
  $("bet-raise-btn").textContent = state.current_bet > 0 ? "Raise to" : "Bet";

  if (state.last_action_log && state.last_action_log.length) {
    $("log").textContent = state.last_action_log.join("\n");
    $("log").scrollTop = $("log").scrollHeight;
  }
}

async function submitAction(action, amount) {
  if (actionInFlight) return;
  actionInFlight = true;
  $("action-error").textContent = "";
  try {
    const res = await fetch(`${API_BASE}/tables/${tableId}/actions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seat: mySeat, action, amount }),
    });
    const body = await res.json();
    if (!res.ok) {
      $("action-error").textContent = body.detail || "action rejected";
      return;
    }
    render(body);
  } finally {
    actionInFlight = false;
  }
}

$("start-hand-btn").addEventListener("click", async () => {
  const res = await fetch(`${API_BASE}/tables/${tableId}/start`, { method: "POST" });
  const body = await res.json();
  if (!res.ok) {
    $("action-error").textContent = body.detail;
  } else {
    render(body);
  }
});

$("fold-btn").addEventListener("click", () => submitAction("fold"));
$("check-call-btn").addEventListener("click", () => {
  const me = lastState.players.find((p) => p.seat === mySeat);
  const toCall = lastState.current_bet - me.current_bet;
  submitAction(toCall > 0 ? "call" : "check");
});
$("bet-raise-btn").addEventListener("click", () => {
  const amount = Number($("bet-amount").value);
  const action = lastState.current_bet > 0 ? "raise" : "bet";
  submitAction(action, amount);
});
