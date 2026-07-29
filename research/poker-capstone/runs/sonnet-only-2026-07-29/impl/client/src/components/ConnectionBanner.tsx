import type { ConnectionStatus } from "../state/tableView";

export function ConnectionBanner({ status }: { status: ConnectionStatus }) {
  if (status === "CONNECTED") return null;
  const text =
    status === "RECONNECTING"
      ? "Reconnecting…"
      : "Out of sync — resyncing with the table…";
  return <div className="connection-banner">{text}</div>;
}
