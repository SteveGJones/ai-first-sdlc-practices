import type { ActionRequest, TableState } from "./types";

// The server is a separately-packaged container (docs/HARNESS-CONTRACT.md:
// service named `server`, container port 8000). This client doesn't own
// that compose wiring, so the base URL is resolved at *runtime* in the
// browser, in priority order:
//   1. `?api=` query param on the page URL (explicit override, e.g. for a
//      driver pointing at a specific host)
//   2. `window.__POKER_API_BASE__`, settable via an injected env.js file
//      (see Dockerfile) without rebuilding the client image
//   3. same-origin default: `${protocol}//${hostname}:8000`, which matches
//      how docker-compose typically publishes sibling service ports to the
//      host the browser runs on.
declare global {
  interface Window {
    __POKER_API_BASE__?: string;
  }
}

export function getApiBase(): string {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("api");
  if (fromQuery) return fromQuery.replace(/\/$/, "");

  if (window.__POKER_API_BASE__) {
    return window.__POKER_API_BASE__.replace(/\/$/, "");
  }

  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function parseErrorBody(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return body.detail ?? body.error ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

export async function fetchState(
  tableId: string,
  seat: number,
): Promise<TableState> {
  const url = `${getApiBase()}/tables/${encodeURIComponent(tableId)}/state?seat=${seat}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorBody(res));
  }
  return (await res.json()) as TableState;
}

export async function postStart(tableId: string): Promise<TableState> {
  const url = `${getApiBase()}/tables/${encodeURIComponent(tableId)}/start`;
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorBody(res));
  }
  return (await res.json()) as TableState;
}

export async function postAction(
  tableId: string,
  body: ActionRequest,
): Promise<TableState> {
  const url = `${getApiBase()}/tables/${encodeURIComponent(tableId)}/actions`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new ApiError(res.status, await parseErrorBody(res));
  }
  return (await res.json()) as TableState;
}
