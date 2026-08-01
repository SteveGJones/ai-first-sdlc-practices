import { useEffect, useState } from "react";
import { useTableConnection } from "./hooks/useTableConnection";
import { Table } from "./components/Table";

const DEFAULT_TABLE_ID = "table-1";

export default function App() {
  const [tableId, setTableId] = useState(DEFAULT_TABLE_ID);
  const { view, pendingTimedOut, join, sit, sitOut, sitIn, submitAction } =
    useTableConnection(tableId);

  useEffect(() => {
    join(tableId);
    // Only re-join if the operator explicitly changes tables.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tableId]);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Poker Capstone</h1>
        <label className="table-picker">
          Table
          <input value={tableId} onChange={(e) => setTableId(e.target.value)} />
        </label>
      </header>
      <Table
        view={view}
        pendingTimedOut={pendingTimedOut}
        onSubmitAction={submitAction}
        onSit={(seatNo, buyIn) => sit(tableId, seatNo, buyIn)}
        onSitOut={() => sitOut(tableId)}
        onSitIn={() => sitIn(tableId)}
      />
    </div>
  );
}
