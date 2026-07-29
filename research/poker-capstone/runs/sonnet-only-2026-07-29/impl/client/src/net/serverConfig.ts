/**
 * Resolves the game server's address from the browser's own location.
 *
 * Both containers (client on host-mapped port from container port 80,
 * server on host-mapped port from container port 8000) are reached by a
 * real browser on the host machine. We never hardcode "localhost" — the
 * server is assumed reachable at the browser's own hostname on a fixed
 * port 8000, so this works whether the page was loaded via 127.0.0.1,
 * a LAN IP, or a real hostname.
 */

const SERVER_PORT = 8000;

export function getServerHttpBaseUrl(): string {
  const { protocol, hostname } = window.location;
  const httpProtocol = protocol === "https:" ? "https:" : "http:";
  return `${httpProtocol}//${hostname}:${SERVER_PORT}`;
}

export function getServerWsUrl(path = "/ws"): string {
  const { protocol, hostname } = window.location;
  const wsProtocol = protocol === "https:" ? "wss:" : "ws:";
  return `${wsProtocol}//${hostname}:${SERVER_PORT}${path}`;
}
