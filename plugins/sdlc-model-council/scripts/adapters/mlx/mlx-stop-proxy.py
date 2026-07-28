#!/usr/bin/env python3
"""mlx-stop-proxy — transparent OpenAI-compatible reverse proxy in front of a
local ``mlx_lm.server``, for Path A (OpenCode -> proxy -> mlx_lm.server).

Why this exists: OpenCode's own request bodies carry no ``stop`` sequence, and
mlx_lm.server (>=0.31.3) can leak the chat stop token into message content
(ml-explore/mlx-lm #973/#875). This proxy injects ``stop`` into any
``/v1/chat/completions`` request that's missing it, then forwards unchanged.
It is otherwise a dumb byte-for-byte relay for every other path.

Panic breadcrumbs: unlike Path B's mlx-chat client, this proxy sees OpenCode's
full agentic request (system prompt + tool schema + the actual item text
somewhere in the message history), so it cannot label a request by item id.
What it CAN do — and the whole reason it exists as a committed script rather
than an ad hoc one-off — is bracket every upstream call with a durable,
fsync'd breadcrumb: REQUEST_START before forwarding, REQUEST_WAITING every
~5s while blocked on mlx_lm.server, REQUEST_DONE/REQUEST_ERROR after. Each
record includes a content fingerprint (first/last N chars of the last user
message) so a post-mortem grep can usually still identify which stack item
was in flight when the machine panicked. Default breadcrumb location matches
mlx-chat's: ~/.sdlc/model-council/mlx-stop-proxy-panic-breadcrumb.jsonl
(override with $MLX_CHAT_BREADCRUMB, empty to disable — same env var as
mlx-chat so both paths' breadcrumbs land in one file by default).

Usage:
  mlx-stop-proxy.py [--listen-port 8081] [--upstream http://127.0.0.1:8082] \\
                     [--stop TOK ...]

Stdlib only. Runs in the foreground; Ctrl-C or SIGTERM to stop.
"""

import argparse
import datetime
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit

DEFAULT_LISTEN_PORT = 8081
DEFAULT_UPSTREAM = "http://127.0.0.1:8082"
DEFAULT_STOP = ["<|im_end|>"]
HEARTBEAT_S = 5


def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _breadcrumb_path():
    if "MLX_CHAT_BREADCRUMB" in os.environ:
        return os.environ["MLX_CHAT_BREADCRUMB"]
    base = os.path.expanduser("~/.sdlc/model-council")
    try:
        os.makedirs(base, exist_ok=True)
    except OSError:
        return ""  # breadcrumbs are diagnostics-only; disable rather than fail a turn
    return os.path.join(base, "mlx-stop-proxy-panic-breadcrumb.jsonl")


def _breadcrumb(path, record):
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, separators=(",", ":")) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
    except OSError:
        pass  # diagnostics must never break a real turn


def _forward_url(upstream, raw_path):
    """Build the upstream request URL without ever letting the incoming
    request line control the scheme/host (CWE-918 partial-SSRF): a client
    could send a proxy-style absolute-URI request line
    (``GET http://evil.example/x HTTP/1.1``), which `http.server` hands back
    verbatim as `self.path`. Only the path+query are taken from it; the
    scheme/host always come from `upstream`, fixed once at startup from the
    CLI arg, never from a request.
    """
    incoming = urlsplit(raw_path)
    up = urlsplit(upstream)
    safe_path = incoming.path or "/"
    if not safe_path.startswith("/"):
        safe_path = "/" + safe_path
    return urlunsplit((up.scheme, up.netloc, safe_path, incoming.query, ""))


def _fingerprint_messages(payload):
    """Best-effort identifying snippet: head+tail of the last user message."""
    try:
        messages = payload.get("messages", [])
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, list):  # some clients send content blocks
                    content = " ".join(
                        b.get("text", "") for b in content if isinstance(b, dict)
                    )
                content = str(content)
                if len(content) <= 300:
                    return content
                return content[:150] + " ... " + content[-150:]
    except Exception:
        pass  # best-effort fingerprint only; never let this break forwarding
    return ""


class ProxyHandler(BaseHTTPRequestHandler):
    upstream = DEFAULT_UPSTREAM
    stop_tokens = DEFAULT_STOP
    breadcrumb_path = ""

    def log_message(self, fmt, *args):
        sys.stderr.write(
            "mlx-stop-proxy: %s - %s\n" % (self.address_string(), fmt % args)
        )

    def _forward(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""

        is_chat = self.path.rstrip("/").endswith("/chat/completions")
        model = ""
        req_id = "%d-%d" % (os.getpid(), int(time.time() * 1000))
        fingerprint = ""
        if is_chat and raw:
            try:
                payload = json.loads(raw)
                if "stop" not in payload or not payload.get("stop"):
                    payload["stop"] = list(self.stop_tokens)
                    raw = json.dumps(payload).encode("utf-8")
                model = payload.get("model", "")
                fingerprint = _fingerprint_messages(payload)
            except (ValueError, TypeError):
                pass  # forward whatever we got, unmodified

        bc_base = {
            "req_id": req_id,
            "pid": os.getpid(),
            "path": self.path,
            "model": model,
            "client": self.client_address[0],
            "fingerprint": fingerprint,
        }
        _breadcrumb(
            self.breadcrumb_path,
            dict(
                bc_base,
                ts=_now_iso(),
                event="REQUEST_START",
                bytes_in=len(raw),
            ),
        )

        stop_heartbeat = threading.Event()

        def _heartbeat():
            waited = 0
            while not stop_heartbeat.wait(HEARTBEAT_S):
                waited += HEARTBEAT_S
                _breadcrumb(
                    self.breadcrumb_path,
                    dict(
                        bc_base,
                        ts=_now_iso(),
                        event="REQUEST_WAITING",
                        waited_s=waited,
                    ),
                )

        hb = threading.Thread(target=_heartbeat, daemon=True)
        hb.start()
        t0 = time.time()
        try:
            fwd_headers = {
                k: v
                for k, v in self.headers.items()
                if k.lower() not in ("host", "content-length")
            }
            fwd_headers["Content-Length"] = str(len(raw))
            req = urlrequest.Request(
                _forward_url(self.upstream, self.path),
                data=raw if raw else None,
                headers=fwd_headers,
                method=self.command,
            )
            with urlrequest.urlopen(req, timeout=1800) as resp:
                body = resp.read()
                status = resp.status
                resp_headers = resp.getheaders()
        except HTTPError as exc:
            body = exc.read() if hasattr(exc, "read") else b""
            status = exc.code
            resp_headers = list(exc.headers.items()) if exc.headers else []
            _breadcrumb(
                self.breadcrumb_path,
                dict(
                    bc_base,
                    ts=_now_iso(),
                    event="REQUEST_HTTP_ERROR",
                    elapsed_s=round(time.time() - t0, 1),
                    http_status=status,
                ),
            )
        except URLError as exc:
            stop_heartbeat.set()
            _breadcrumb(
                self.breadcrumb_path,
                dict(
                    bc_base,
                    ts=_now_iso(),
                    event="REQUEST_UNREACHABLE",
                    elapsed_s=round(time.time() - t0, 1),
                    detail=str(exc),
                ),
            )
            self.send_response(502)
            self.end_headers()
            self.wfile.write(b"mlx-stop-proxy: upstream unreachable")
            return
        finally:
            stop_heartbeat.set()

        _breadcrumb(
            self.breadcrumb_path,
            dict(
                bc_base,
                ts=_now_iso(),
                event="REQUEST_DONE",
                elapsed_s=round(time.time() - t0, 1),
                http_status=status,
                bytes_out=len(body),
            ),
        )

        self.send_response(status)
        for k, v in resp_headers:
            if k.lower() in ("transfer-encoding", "connection"):
                continue
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._forward()

    def do_POST(self):
        self._forward()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--listen-port", type=int, default=DEFAULT_LISTEN_PORT)
    ap.add_argument("--upstream", default=DEFAULT_UPSTREAM)
    ap.add_argument("--stop", action="append", default=None)
    args = ap.parse_args(argv)

    ProxyHandler.upstream = args.upstream.rstrip("/")
    ProxyHandler.stop_tokens = args.stop or list(DEFAULT_STOP)
    ProxyHandler.breadcrumb_path = _breadcrumb_path()

    srv = ThreadingHTTPServer(("127.0.0.1", args.listen_port), ProxyHandler)
    print(
        "mlx-stop-proxy: 127.0.0.1:%d -> %s  stop=%s  breadcrumb=%s"
        % (
            args.listen_port,
            ProxyHandler.upstream,
            ProxyHandler.stop_tokens,
            ProxyHandler.breadcrumb_path or "(disabled)",
        )
    )
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
