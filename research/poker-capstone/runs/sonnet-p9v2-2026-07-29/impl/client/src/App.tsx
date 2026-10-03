import { useMemo, useState } from "react";
import { ApiError, postAction, postStart } from "./api";
import { ActionPanel } from "./components/ActionPanel";
import { CommunityCards } from "./components/CommunityCards";
import { Pots } from "./components/Pots";
import { Seat } from "./components/Seat";
import { TableMirror } from "./components/TableMirror";
import type { ShowdownEntry } from "./types";
import { useTablePolling } from "./useTablePolling";

function parseDeepLink(): { table: string | null; seat: number | null } {
  const params = new URLSearchParams(window.location.search);
  const table = params.get("table");
  const seatRaw = params.get("seat");
  const seat = seatRaw !== null && seatRaw !== "" ? Number(seatRaw) : null;
  return { table, seat: seat !== null && !Number.isNaN(seat) ? seat : null };
}

// docs/CLIENT-TEST-CONTRACT.md "URL contract": loading `/?table={id}&seat={n}`
// must take the browser straight to that table's view for that seat. A
// lobby/landing page may still exist for humans (below, when the params
// are absent) but the driver never uses it.
function LandingForm() {
  const [tableId, setTableId] = useState("");
  const [seat, setSeat] = useState("0");

  const go = () => {
    const url = new URL(window.location.href);
    url.searchParams.set("table", tableId.trim());
    url.searchParams.set("seat", seat.trim());
    window.location.href = url.toString();
  };

  return (
    <div className="landing">
      <h1>Poker Capstone Client</h1>
      <p>
        Enter a table ID and seat to view an already-created table (tables and
        seats are created via the server&apos;s REST API — this page does not
        create them).
      </p>
      <label>
        Table ID
        <input value={tableId} onChange={(e) => setTableId(e.target.value)} />
      </label>
      <label>
        Seat
        <input value={seat} onChange={(e) => setSeat(e.target.value)} type="number" min={0} />
      </label>
      <button type="button" onClick={go} disabled={!tableId.trim()}>
        View table
      </button>
    </div>
  );
}

function TableView({ tableId, seat }: { tableId: string; seat: number }) {
  const { state, status, lastError, refresh } = useTablePolling(tableId, seat);
  const [pending, setPending] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const myPlayer = useMemo(
    () => state?.players.find((p) => p.seat === seat),
    [state, seat],
  );

  const showdownBySeat = useMemo(() => {
    const map = new Map<number, ShowdownEntry>();
    state?.last_showdown.forEach((entry) => map.set(entry.seat, entry));
    return map;
  }, [state]);

  const runAction = async (fn: () => Promise<unknown>) => {
    setPending(true);
    setActionError(null);
    try {
      await fn();
      await refresh();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.detail : String(err));
    } finally {
      setPending(false);
    }
  };

  if (!state) {
    return (
      <div className="loading" data-testid="loading">
        {status === "error" ? `Failed to load table: ${lastError}` : "Loading table…"}
      </div>
    );
  }

  return (
    <div className="table-view">
      <header className="table-view__header">
        <h1>Table {state.table_id}</h1>
        <span className={`connection-status connection-status--${status}`}>{status}</span>
        <span>
          Blinds {state.small_blind}/{state.big_blind}
        </span>
        <span>Street: {state.betting_round ?? "—"}</span>
      </header>

      <TableMirror state={state}>
        <CommunityCards cards={state.community_cards} />
        <Pots pots={state.pots} />
        <div className="seats">
          {state.players.map((p) => (
            <Seat
              key={p.seat}
              player={p}
              isMe={p.seat === seat}
              isButton={p.seat === state.button_seat}
              isActing={p.seat === state.current_actor}
              showdownEntry={showdownBySeat.get(p.seat)}
            />
          ))}
        </div>
        <div className="action-log">
          <h2>Log</h2>
          <ul>
            {state.last_action_log.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </div>
      </TableMirror>

      <ActionPanel
        state={state}
        mySeat={seat}
        myPlayer={myPlayer}
        pending={pending}
        errorMessage={actionError}
        onFold={() => runAction(() => postAction(tableId, { seat, action: "fold" }))}
        onCheckCall={() => {
          const toCall = myPlayer ? Math.max(0, state.current_bet - myPlayer.current_bet) : 0;
          const action = toCall > 0 ? "call" : "check";
          return runAction(() => postAction(tableId, { seat, action }));
        }}
        onBetRaise={(amount) => {
          const action = state.current_bet > 0 ? "raise" : "bet";
          return runAction(() => postAction(tableId, { seat, action, amount }));
        }}
        onStartHand={() => runAction(() => postStart(tableId))}
      />
    </div>
  );
}

export function App() {
  const { table, seat } = parseDeepLink();

  if (table === null || seat === null) {
    return <LandingForm />;
  }

  return <TableView tableId={table} seat={seat} />;
}
